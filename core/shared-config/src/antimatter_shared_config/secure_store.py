import os
import json
import getpass
from pathlib import Path
import keyring
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SECRETS_FILE = Path(os.path.expanduser("~/.antimatter_daemon/secrets.enc"))

def is_keyring_secure() -> bool:
    """Detects if a secure, hardware/OS-backed keyring is available."""
    if os.environ.get("ANTIMATTER_FORCE_HEADLESS") == "1":
        return False
    try:
        kr = keyring.get_keyring()
        # Secure backends (macOS Keychain, KWallet, Windows) have priority >= 1
        # Fallbacks (fail, plaintext) have priority < 1
        return getattr(kr, 'priority', 0) >= 1
    except Exception:
        return False

class HeadlessVault:
    """AES-GCM encrypted vault for headless Linux servers without DBus."""
    def __init__(self):
        self._key: bytes | None = None
        self._salt_file = SECRETS_FILE.with_suffix('.salt')
        self._secrets: dict[str, str] = {}
        
    def _get_or_create_salt(self) -> bytes:
        if self._salt_file.exists():
            return self._salt_file.read_bytes()
        salt = os.urandom(16)
        # Ensure directory exists
        self._salt_file.parent.mkdir(parents=True, exist_ok=True)
        self._salt_file.write_bytes(salt)
        os.chmod(self._salt_file, 0o600)
        return salt
        
    def _derive_key(self, password: str) -> bytes:
        salt = self._get_or_create_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600_000,  # OWASP 2023 minimum for PBKDF2-HMAC-SHA256
        )
        return kdf.derive(password.encode('utf-8'))
        
    def _unlock(self) -> None:
        if self._key is not None:
            return
            
        password = os.environ.get("ANTIMATTER_MASTER_PASSWORD")
        if not password:
            print("\n[Antimatter] 🔒 Headless Server Mode Detected. OS Keyring unavailable.")
            password = getpass.getpass("Enter Master Password for Antimatter Vault: ")
            
        self._key = self._derive_key(password)
        
        if SECRETS_FILE.exists():
            try:
                data = SECRETS_FILE.read_bytes()
                nonce, ct = data[:12], data[12:]
                aesgcm = AESGCM(self._key)
                pt = aesgcm.decrypt(nonce, ct, None)
                self._secrets = json.loads(pt.decode('utf-8'))
            except Exception:
                # Reset key so they can try again if called programmatically
                self._key = None
                raise ValueError("Invalid Master Password or corrupted vault.")
                
    def _save(self) -> None:
        if self._key is None:
            return
        aesgcm = AESGCM(self._key)
        nonce = os.urandom(12)
        pt = json.dumps(self._secrets).encode('utf-8')
        ct = aesgcm.encrypt(nonce, pt, None)
        
        temp_path = SECRETS_FILE.with_suffix('.tmp')
        temp_path.write_bytes(nonce + ct)
        os.chmod(temp_path, 0o600)
        temp_path.rename(SECRETS_FILE)
        
    def get_secret(self, service: str, username: str) -> str | None:
        self._unlock()
        return self._secrets.get(f"{service}::{username}")
        
    def set_secret(self, service: str, username: str, password: str) -> None:
        self._unlock()
        self._secrets[f"{service}::{username}"] = password
        self._save()

_headless_vault = HeadlessVault()
_use_keyring = is_keyring_secure()

def get_secret(key: str) -> str | None:
    """Retrieve a secret from the most secure available store."""
    if _use_keyring:
        try:
            return keyring.get_password("antimatter_gateway", key)
        except Exception:
            pass
    return _headless_vault.get_secret("antimatter_gateway", key)

def set_secret(key: str, value: str) -> None:
    """Save a secret to the most secure available store."""
    if value is None:
        return
    if _use_keyring:
        try:
            keyring.set_password("antimatter_gateway", key, value)
            return
        except Exception:
            pass
    _headless_vault.set_secret("antimatter_gateway", key, value)
