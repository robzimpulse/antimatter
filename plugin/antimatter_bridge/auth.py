import os
import json
import base64
import secrets
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

CONFIG_FILE = Path.home() / ".antimatter_daemon" / "config.json"

class AuthHandler:
    def __init__(self):
        self.pairing_token = None
        self.private_key = None
        self.public_key_raw_base64 = None
        self.load_or_generate_keys()

    def load_or_generate_keys(self):
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        config = {}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)

        if "pairing_token" in config:
            self.pairing_token = config["pairing_token"]
        else:
            self.pairing_token = secrets.token_urlsafe(32)
            config["pairing_token"] = self.pairing_token

        if "private_key_pem" in config:
            self.private_key = serialization.load_pem_private_key(
                config["private_key_pem"].encode("utf-8"),
                password=None
            )
        else:
            self.private_key = ed25519.Ed25519PrivateKey.generate()
            config["private_key_pem"] = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode("utf-8")

        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        # VULN-V3-001: Restrict config file to owner read/write only (chmod 600)
        # Prevents other users on multi-user systems from reading credentials
        import stat
        os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)

        # Extract raw 32-byte public key
        pub_der = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.public_key_raw_base64 = base64.b64encode(pub_der[12:]).decode("utf-8")

        self.cloudflare_url = config.get("cloudflare_url")
        self.cloudflare_client_id = config.get("cloudflare_client_id")
        self.cloudflare_client_secret = config.get("cloudflare_client_secret")

    def get_qr_payload(self) -> str:
        import urllib.parse
        
        # The Android app expects a deep link URI:
        # https://your-domain.com/connect?url=...&token=...&pubkey=...
        
        # Default to localhost if no cloudflare URL is set (for completeness)
        ws_url = self.cloudflare_url if self.cloudflare_url else "ws://127.0.0.1:8765"
        
        params = {
            "url": ws_url,
            "token": self.pairing_token,
            "pubkey": self.public_key_raw_base64
        }
        
        if self.cloudflare_client_id:
            params["cfid"] = self.cloudflare_client_id
        if self.cloudflare_client_secret:
            params["cfsec"] = self.cloudflare_client_secret
            
        query_string = urllib.parse.urlencode(params)
        return f"https://your-domain.com/connect?{query_string}"

    def verify_token(self, provided_token: str) -> bool:
        if not provided_token or not self.pairing_token:
            return False
        return secrets.compare_digest(provided_token, self.pairing_token)

    def sign_challenge(self, challenge_base64: str) -> str:
        nonce = base64.b64decode(challenge_base64)
        signature = self.private_key.sign(nonce)
        return base64.b64encode(signature).decode("utf-8")
