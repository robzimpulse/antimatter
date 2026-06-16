import asyncio
import json
import logging
import time
import websockets
from websockets.exceptions import ConnectionClosed

from antimatter_shared_config.config import load_config, save_config, AntimatterConfig
from antimatter_crypto.auth import Ed25519Auth
from antimatter_crypto.e2ee import E2EESession
from .qr import generate_qr_payload, print_qr_to_terminal
from .tunnel import CloudflaredManager
from .router import MessageRouter

logger = logging.getLogger(__name__)

# Rate Limiting
_ip_failure_counts: dict[str, dict] = {}
RATE_LIMIT_MAX_FAILURES = 5
RATE_LIMIT_WINDOW = 60

def _record_failure(ip: str):
    now = time.monotonic()
    data = _ip_failure_counts.get(ip, {"count": 0, "reset_at": 0.0})
    if now >= data["reset_at"]:
        data = {"count": 0, "reset_at": now + RATE_LIMIT_WINDOW}
    data["count"] += 1
    _ip_failure_counts[ip] = data

class GatewayServer:
    def __init__(self):
        self.config = load_config()
        self.auth = Ed25519Auth(self.config.private_key_pem)
        self.router = MessageRouter(gateway=self)
        
        # Initialize E2EE Gateway Session
        self.e2ee = E2EESession(role="gateway", private_key_b64=self.config.gateway_priv_x25519)
        
        # Persist keys if newly generated
        needs_save = False
        if not self.config.private_key_pem:
            self.config.private_key_pem = self.auth.private_key_base64
            self.config.pairing_token = self.auth.pairing_token
            needs_save = True
        
        if not self.config.gateway_priv_x25519:
            self.config.gateway_priv_x25519 = self.e2ee.private_key_b64
            needs_save = True
            
        if needs_save:
            save_config(self.config)

    async def handler(self, websocket):
        ip = getattr(websocket, "remote_address", ("unknown",))[0]
        now = time.monotonic()
        
        # 1. Rate Limiting Check
        rate_data = _ip_failure_counts.get(ip)
        if rate_data and rate_data["count"] >= RATE_LIMIT_MAX_FAILURES and now < rate_data["reset_at"]:
            logger.warning(f"Rate limited connection rejected: {ip}")
            await websocket.close(1008, "Rate Limited")
            return

        # 2. Origin Validation
        # In a real setup, we check req.headers.origin against cloudflareaccess.com
        # For simplicity in python websockets, we handle it natively or trust localhost.

        authenticated = False
        e2ee_established = False

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                except Exception:
                    continue
                
                msg_type = data.get("type")

                msg_type = data.get("type")

                # Adapter Registration (Local IPC)
                if msg_type == "REGISTER_ADAPTER":
                    agent_id = data.get("id")
                    agent_name = data.get("name")
                    workspace_root = data.get("workspaceRoot")
                    if agent_id and agent_name:
                        logger.info(f"Adapter registered: {agent_name} ({agent_id})")
                        await self.router.register_adapter(agent_id, agent_name, websocket, workspace_root)
                        # We break out of the auth loop into a dedicated adapter loop
                        await self._adapter_loop(websocket, agent_id)
                        return
                    else:
                        await websocket.close(1008, "Missing adapter id/name")
                        return

                # State 1: Legacy Ed25519 Auth Challenge (Client)
                if msg_type == "AUTH_CHALLENGE":
                    challenge = data.get("challenge")
                    if not challenge:
                        await websocket.close(1008, "Missing challenge")
                        return
                    
                    sig = self.auth.sign_challenge(challenge)
                    await websocket.send(json.dumps({"type": "AUTH_RESPONSE", "signature": sig}))
                    authenticated = True
                    logger.info(f"Client {ip} authenticated successfully.")
                    
                    # Add client to router once authenticated
                    self.router.add_client(websocket)
                    continue
                
                if not authenticated:
                    _record_failure(ip)
                    await websocket.close(1008, "Unauthorized")
                    return

                # State 2: E2EE Handshake
                if msg_type == "HELLO":
                    client_pubkey = data.get("pubkey")
                    if not client_pubkey:
                        await websocket.close(1008, "Missing X25519 pubkey")
                        return
                    
                    self.e2ee.derive_session_keys(client_pubkey)
                    e2ee_established = True
                    logger.info("E2EE Session established (ECDH + HKDF).")
                    
                    # Notify adapters
                    await self.router.broadcast_system_state()
                    continue
                
                if not e2ee_established:
                    await websocket.send(json.dumps({"type": "ERROR", "message": "E2EE Handshake required."}))
                    continue

                # State 3: E2EE Encrypted Payload Routing
                if "iv" in data and "ct" in data and "aad" in data:
                    try:
                        # Decrypt client->server command
                        plaintext = self.e2ee.decrypt(data, expected_direction="cmd:")
                        parsed_cmd = json.loads(plaintext)
                        
                        # Route to local adapter via IPC
                        await self.router.route_to_adapter(parsed_cmd, self.e2ee, websocket)
                    except ValueError as e:
                        logger.error(f"E2EE Decryption/AAD failed: {e}")
                        await websocket.close(1008, "Encryption Error")
                        return
                else:
                    logger.warning("Unencrypted message received post-handshake. Dropping.")

        except ConnectionClosed:
            logger.info(f"Connection closed: {ip}")
        finally:
            self.router.remove_client(websocket)

    async def _adapter_loop(self, websocket, agent_id: str):
        """
        Dedicated loop for listening to incoming messages from a local adapter.
        When an adapter sends a message, it needs to be broadcast or routed to clients.
        """
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                except Exception:
                    continue
                
                # Currently we only have one e2ee session and one client.
                # If we have multiple clients, we need to map adapter messages to clients.
                # For now, we broadcast to all connected, authenticated clients.
                await self.router.broadcast_to_clients(data, self.e2ee)
                
        except ConnectionClosed:
            logger.info(f"Adapter connection closed: {agent_id}")
        finally:
            await self.router.unregister_adapter(agent_id)

    async def start(self):
        logger.info("Starting Gateway WebSocket server on ws://127.0.0.1:8765")
        
        # Start Tunnel if configured
        tunnel_url = self.config.cloudflare_url
        self.cf_manager = None
        
        if not tunnel_url:
            logger.info("Starting Cloudflare Quick Tunnel...")
            self.cf_manager = CloudflaredManager(8765)
            if await self.cf_manager.start():
                try:
                    await asyncio.wait_for(self.cf_manager.ready_event.wait(), timeout=15.0)
                    tunnel_url = self.cf_manager.url
                except asyncio.TimeoutError:
                    logger.warning("Quick tunnel timeout.")
        
        payload = generate_qr_payload(
            cloudflare_url=tunnel_url,
            pairing_token=self.auth.pairing_token,
            gateway_x25519_pub=self.e2ee.public_key_b64,
            client_id=self.config.cloudflare_client_id
        )
        
        print("\n" + "="*50)
        print("ANTIMATTER E2EE GATEWAY SECURE PAIRING")
        print("="*50)
        if tunnel_url:
            print(f"\nTunnel: {tunnel_url}")
        
        print("\nScan this QR Code with the Antimatter App:\n")
        print_qr_to_terminal(payload)
        print("="*50)

        async with websockets.serve(self.handler, "127.0.0.1", self.port):
            await asyncio.Future()

async def main_async(port: int = 8765):
    server = GatewayServer()
    server.port = port
    await server.start()

def main():
    import argparse
    from antimatter_shared_config.config import load_config, save_config

    parser = argparse.ArgumentParser(prog="antimatter", description="Antimatter E2EE Gateway")
    parser.add_argument("--port", type=int, default=8765, help="Port to run the Gateway on")
    
    subparsers = parser.add_subparsers(dest="command")
    
    config_parser = subparsers.add_parser("config", help="Manage gateway configuration")
    config_sub = config_parser.add_subparsers(dest="config_command")
    
    set_parser = config_sub.add_parser("set", help="Set a configuration key")
    set_parser.add_argument("key", help="Configuration key to set")
    set_parser.add_argument("value", help="Value to set")
    
    args = parser.parse_args()
    
    if args.command == "config":
        if args.config_command == "set":
            config = load_config()
            if hasattr(config, args.key):
                setattr(config, args.key, args.value)
                save_config(config)
                print(f"✅ Successfully set '{args.key}'")
            else:
                print(f"❌ Unknown config key: {args.key}")
        return

    # Otherwise, start the server
    asyncio.run(main_async(args.port))

if __name__ == "__main__":
    main()
