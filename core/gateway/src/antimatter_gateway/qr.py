import urllib.parse
import qrcode
import logging

logger = logging.getLogger(__name__)

def generate_qr_payload(
    cloudflare_url: str | None,
    pairing_token: str,
    gateway_x25519_pub: str,
    client_id: str | None = None
) -> str:
    """
    Generates the canonical Deep Link payload for Android pairing.
    Includes the X25519 public key for the E2EE ECDH handshake.
    """
    # For now, default to local dev if cloudflare is off
    base_url = "https://antimatter.saifmukhtar.dev/connect"
    
    params = {
        "url": cloudflare_url or "ws://127.0.0.1:8765",
        "token": pairing_token,
        "x25519_pub": gateway_x25519_pub
    }
    
    if client_id:
        params["cid"] = client_id
        
    query = urllib.parse.urlencode(params)
    return f"{base_url}?{query}"

def print_qr_to_terminal(payload: str) -> None:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(payload)
    
    try:
        qr.print_ascii(invert=True)
    except Exception:
        logger.warning("Failed to print ASCII QR. Terminal might not support it.")

def main():
    import socket
    import sys
    
    # Check if the gateway is running locally
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect(("127.0.0.1", 8765))
        s.close()
    except (socket.timeout, ConnectionRefusedError):
        print("\n[ERROR] The Antimatter Gateway is not running!")
        print("Please start it first by running: uv run antimatter\n")
        sys.exit(1)

    from antimatter_shared_config.config import load_config
    config = load_config()
    if not config.gateway_priv_x25519 or not config.pairing_token:
        print("Error: Gateway not initialized. Please run 'antimatter-gateway' first.")
        return

    # Actually, E2EESession handles derivation.
    from antimatter_crypto.e2ee import E2EESession
    e2ee = E2EESession(role="gateway", private_key_b64=config.gateway_priv_x25519)
    
    tunnel_url = config.cloudflare_url
    if not tunnel_url:
        import os
        from pathlib import Path
        ephemeral = Path(os.path.expanduser("~/.antimatter_daemon/ephemeral_tunnel.txt"))
        if ephemeral.exists():
            tunnel_url = ephemeral.read_text().strip()

    payload = generate_qr_payload(
        cloudflare_url=tunnel_url,
        pairing_token=config.pairing_token,
        gateway_x25519_pub=e2ee.public_key_b64,
        client_id=config.cloudflare_client_id
    )
    
    print("\n" + "="*50)
    print("ANTIMATTER E2EE GATEWAY SECURE PAIRING")
    print("="*50)
    if tunnel_url:
        print(f"\nTunnel: {tunnel_url}")
    
    print("\nScan this QR Code with the Antimatter App:\n")
    print_qr_to_terminal(payload)
    print("="*50)

if __name__ == "__main__":
    main()
