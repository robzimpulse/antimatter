import urllib.parse
import qrcode
import logging

logger = logging.getLogger(__name__)

def generate_qr_payload(
    cloudflare_url: str | None,
    pairing_token: str,
    gateway_x25519_pub: str,
    client_id: str | None = None,
    client_secret: str | None = None
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
    
    if client_id and client_secret:
        import hashlib
        import os
        import json
        import base64
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        key = hashlib.sha256(pairing_token.encode("utf-8")).digest()
        aesgcm = AESGCM(key)
        cf_payload = json.dumps({"id": client_id, "secret": client_secret}).encode("utf-8")
        
        iv = os.urandom(12)
        encrypted_data = aesgcm.encrypt(iv, cf_payload, None)
        ciphertext = encrypted_data[:-16]
        auth_tag = encrypted_data[-16:]
        
        params["cfenc"] = f"{base64.b64encode(iv).decode('utf-8')}:{base64.b64encode(auth_tag).decode('utf-8')}:{base64.b64encode(ciphertext).decode('utf-8')}"
    elif client_id:
        params["client_id"] = client_id
        
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
    
    # Server running check removed so users can generate QR codes anytime

    from antimatter_shared_config.config import load_config
    config = load_config()
    if not config.private_key_pem or not config.pairing_token:
        print("Error: Gateway not initialized. Please run 'antimatter-gateway start' first.")
        return
    
    tunnel_url = config.cloudflare_url

    from antimatter_crypto.auth import Ed25519Auth
    auth = Ed25519Auth(config.private_key_pem)
    import base64
    ed25519_pub_b64 = base64.b64encode(auth.public_key_raw).decode('utf-8')

    payload = generate_qr_payload(
        cloudflare_url=tunnel_url,
        pairing_token=config.pairing_token,
        gateway_x25519_pub=ed25519_pub_b64,
        client_id=config.cloudflare_client_id,
        client_secret=config.cloudflare_client_secret
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
