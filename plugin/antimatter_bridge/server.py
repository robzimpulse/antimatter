import asyncio
import json
import logging
import websockets
from pathlib import Path
from websockets.exceptions import ConnectionClosed
from .auth import AuthHandler
from .agent_bridge import AgentBridge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

auth_handler = AuthHandler()

import os
CONFIG_FILE = os.path.expanduser("~/.antimatter_daemon/config.json")
try:
    with open(CONFIG_FILE, 'r') as f:
        daemon_config = json.load(f)
        if "gemini_api_key" in daemon_config and daemon_config["gemini_api_key"]:
            os.environ["GEMINI_API_KEY"] = daemon_config["gemini_api_key"]
except Exception as e:
    logger.warning(f"Failed to load daemon config: {e}")

APP_DATA_DIR = Path(os.environ.get("AGY_APP_DATA_DIR", os.path.expanduser("~/.gemini/antigravity")))

def get_latest_conversation_id(app_data_dir: Path) -> str:
    brain_dir = app_data_dir / "brain"
    if not brain_dir.exists():
        return "default"
    
    conv_dirs = [d.name for d in brain_dir.iterdir() if d.is_dir() and (brain_dir / d / ".system_generated").exists()]
    if not conv_dirs:
        return "default"
        
    conv_dirs.sort(key=lambda d: (brain_dir / d).stat().st_mtime, reverse=True)
    return conv_dirs[0]

# VULN-V3-002: IP-based rate limiting state
# Maps remote_addr -> {"count": int, "reset_at": float}
_ip_failure_counts: dict[str, dict] = {}
_RATE_LIMIT_MAX_FAILURES = 5
_RATE_LIMIT_WINDOW_SECONDS = 60

def _record_auth_failure(remote_addr: str) -> None:
    """Record a failed authentication attempt for rate limiting."""
    import time
    now = time.monotonic()
    data = _ip_failure_counts.get(remote_addr, {"count": 0, "reset_at": 0.0})
    if now >= data["reset_at"]:
        data = {"count": 0, "reset_at": now + _RATE_LIMIT_WINDOW_SECONDS}
    data["count"] += 1
    _ip_failure_counts[remote_addr] = data
    if data["count"] >= _RATE_LIMIT_MAX_FAILURES:
        logger.warning(f"IP {remote_addr} has {data['count']} auth failures — rate limiting active for {_RATE_LIMIT_WINDOW_SECONDS}s")

# BUG-004: Do NOT evaluate conversation ID at module import time — look it up fresh per-connection
# (CURRENT_CONVERSATION_ID removed; each handler call invokes get_latest_conversation_id directly)

def get_default_workspace() -> str:
    # If AGY_WORKSPACE_DIR is explicitly set, use it.
    if "AGY_WORKSPACE_DIR" in os.environ:
        return os.environ["AGY_WORKSPACE_DIR"]
    
    # Try to find the root by looking for .git folder upwards from the current file
    try:
        current = Path(__file__).resolve().parent
        while current != current.parent:
            if (current / ".git").exists():
                return str(current)
            current = current.parent
    except Exception:
        pass
        
    return os.getcwd()

async def handler(websocket, path=None):
    logger.info("New connection attempt...")

    # VULN-V3-002: Check IP-based rate limit before any auth processing
    import time
    remote_addr = getattr(websocket, "remote_address", ("unknown",))[0]
    now = time.monotonic()
    rate_data = _ip_failure_counts.get(remote_addr)
    if rate_data and rate_data["count"] >= _RATE_LIMIT_MAX_FAILURES and now < rate_data["reset_at"]:
        logger.warning(f"Rate-limited connection from {remote_addr}")
        await websocket.close()
        return

    # BUG-004: Look up the latest conversation ID fresh on every new connection
    # instead of using a stale module-level constant captured at startup.
    convo_id = os.environ.get("AGY_CONVERSATION_ID") or get_latest_conversation_id(APP_DATA_DIR)
    bridge = AgentBridge(websocket, str(APP_DATA_DIR), convo_id)

    # Try authenticating via URL token parameter
    authenticated = False
    try:
        import urllib.parse
        path = getattr(websocket, "path", None)
        if path is None and hasattr(websocket, "request"):
            path = websocket.request.path
        if path:
            query = urllib.parse.urlparse(path).query
            params = urllib.parse.parse_qs(query)
            if "token" in params and auth_handler.verify_token(params["token"][0]):
                authenticated = True
                logger.info("Client authenticated successfully via URL token parameter.")
                # Send initial state
                await websocket.send(json.dumps({
                    "type": "SESSION_STATE",
                    "conversationId": bridge.conversation_id,
                    "model": "gemini-2.5-pro",
                    "stepCount": bridge.step_index,
                    "cloudflareUrl": None,
                    "environment": "2.0"
                }))
            else:
                # VULN-V3-002: Record URL-token auth failure for rate limiting
                _record_auth_failure(remote_addr)
    except Exception as e:
        logger.warning(f"Error parsing URL params: {e}")

    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "AUTH_CHALLENGE":
                    challenge = data.get("challenge")
                    if not challenge:
                        await websocket.send(json.dumps({"type": "ERROR", "message": "Missing challenge payload"}))
                        return
                    
                    signature = auth_handler.sign_challenge(challenge)
                    await websocket.send(json.dumps({
                        "type": "AUTH_RESPONSE",
                        "signature": signature
                    }))
                    authenticated = True
                    logger.info("Client authenticated successfully via AUTH_CHALLENGE.")
                    
                    # Send SESSION_STATE with environment: "2.0"
                    await websocket.send(json.dumps({
                        "type": "SESSION_STATE",
                        "conversationId": bridge.conversation_id,
                        "model": "gemini-2.5-pro",
                        "stepCount": bridge.step_index,
                        "cloudflareUrl": None,
                        "environment": "2.0"
                    }))
                    
                elif not authenticated:
                    logger.warning("Message received before authentication.")
                    await websocket.send(json.dumps({"type": "ERROR", "message": "Unauthorized"}))
                    return
                    
                elif msg_type == "SUBSCRIBE_CONVERSATION":
                    if bridge.conversation_id:
                        await bridge.send_transcript(bridge.conversation_id)
                        await bridge.send_artifacts(bridge.conversation_id)
                    asyncio.create_task(bridge.poll_transcript())
                    await bridge.send_workspace(get_default_workspace())

                elif msg_type == "NEW_CONVERSATION":
                    await websocket.send(json.dumps({
                        "type": "ERROR",
                        "message": "Antimatter Bridge daemon currently locks to a single active IDE session."
                    }))

                elif msg_type == "GET_HISTORY":
                    await bridge.send_history()

                elif msg_type == "GET_ARTIFACTS":
                    cid = data.get("conversationId", bridge.conversation_id)
                    if cid:
                        await bridge.send_artifacts(cid)

                elif msg_type == "GET_FILES":
                    await bridge.send_workspace(get_default_workspace())
                    
                elif msg_type == "READ_FILE":
                    path = data.get("path")
                    if path:
                        await bridge.read_file(path)
                    
                elif msg_type == "SEND_MESSAGE":
                    text = data.get("text", "")
                    asyncio.create_task(bridge.process_message(text))
                    
                elif msg_type == "EXECUTE_COMMAND":
                    await websocket.send(json.dumps({
                        "type": "ERROR",
                        "message": "Terminal not supported in Antigravity 2.0"
                    }))
                    
                elif msg_type == "PING":
                    await websocket.send(json.dumps({"type": "PONG"}))
                    
            except json.JSONDecodeError:
                pass
                
    except ConnectionClosed:
        logger.info("Connection closed.")
    finally:
        await bridge.cleanup()

import qrcode
from .tunnel_manager import CloudflaredManager

async def main():
    logger.info("Starting Antigravity 2.0 Bridge daemon on ws://localhost:8765...")
    server = websockets.serve(handler, "localhost", 8765)
    
    tunnel_url = auth_handler.cloudflare_url
    cf_manager = None
    
    if not tunnel_url:
        print("\nStarting Cloudflare Quick Tunnel (TryCloudflare)...")
        cf_manager = CloudflaredManager(8765)
        success = await cf_manager.start()
        
        if success:
            try:
                await asyncio.wait_for(cf_manager.ready_event.wait(), timeout=15.0)
                tunnel_url = cf_manager.url
                auth_handler.cloudflare_url = tunnel_url
            except asyncio.TimeoutError:
                print("Timeout waiting for Cloudflare Quick Tunnel.")
    
    payload = auth_handler.get_qr_payload()
    
    print("\n" + "="*50)
    print("ANTIMATTER BRIDGE SECURE PAIRING")
    print("="*50)
    
    if tunnel_url:
        print(f"\nCloudflare Tunnel: {tunnel_url}")
        if auth_handler.cloudflare_client_id:
            print("Zero Trust Security: ENABLED")
        else:
            print("Zero Trust Security: NOT CONFIGURED (Public Quick Tunnel)")
    else:
        print("\nConnection: Local Network (Cloudflare Quick Tunnel failed or not used)")

    print("\nScan this QR Code with the Antimatter Android App:\n")
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(payload)
    
    # Attempt terminal print
    try:
        qr.print_ascii(invert=True)
    except Exception:
        print("Failed to print QR code in terminal. Raw pairing token below:")
    
    print("\n" + "="*50)
    print("MANUAL PAIRING TOKENS")
    print("="*50)
    logger.info(f"Pairing Token: {auth_handler.pairing_token}")
    logger.info(f"Public Key (Base64): {auth_handler.public_key_raw_base64}")
    
    try:
        async with server:
            await asyncio.Future()  # run forever
    finally:
        if cf_manager:
            await cf_manager.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDaemon shut down gracefully.")
