import os
import base64
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class E2EESession:
    def __init__(self, role: str, private_key_b64: str | None = None):
        """
        role: "gateway" or "client"
        The role determines which directional key is used for encrypt vs decrypt.
        """
        self.role = role
        
        if private_key_b64:
            self._private_key = X25519PrivateKey.from_private_bytes(base64.b64decode(private_key_b64))
        else:
            self._private_key = X25519PrivateKey.generate()
            
        self.public_key_b64 = base64.b64encode(
            self._private_key.public_key().public_bytes_raw()
        ).decode()
        
        # We can export the private key if we need to persist it (e.g. gateway)
        self.private_key_b64 = base64.b64encode(
            self._private_key.private_bytes_raw()
        ).decode()
        
        self._c2s_key: bytes | None = None  # client → server
        self._s2c_key: bytes | None = None  # server → client
        self._msg_counter = 0
        self._last_seen_msg_id: int = 0  # For replay-attack prevention on decrypt

    def _derive_key(self, shared_secret: bytes, info: bytes) -> bytes:
        return HKDF(
            algorithm=hashes.SHA256(), length=32,
            salt=None, info=info
        ).derive(shared_secret)

    def derive_session_keys(self, peer_public_key_b64: str) -> None:
        """ECDH + HKDF → two direction-specific keys. No key crosses the wire."""
        peer_pub = X25519PublicKey.from_public_bytes(base64.b64decode(peer_public_key_b64))
        shared_secret = self._private_key.exchange(peer_pub)
        
        # Direction-specific keys prevent reflection attacks.
        # Attacker cannot replay a server→client ciphertext as a client→server command.
        self._c2s_key = self._derive_key(shared_secret, b"antimatter-v1:client-to-server")
        self._s2c_key = self._derive_key(shared_secret, b"antimatter-v1:server-to-client")

    @property
    def _encrypt_key(self) -> bytes:
        if not self._c2s_key or not self._s2c_key:
            raise ValueError("Session keys not derived yet.")
        return self._c2s_key if self.role == "client" else self._s2c_key

    @property
    def _decrypt_key(self) -> bytes:
        if not self._c2s_key or not self._s2c_key:
            raise ValueError("Session keys not derived yet.")
        return self._s2c_key if self.role == "client" else self._c2s_key

    def encrypt(self, plaintext: str, direction: str) -> dict:
        """
        direction: "cmd" (client→server) or "output" (server→client)
        AAD encodes direction + msg_id to block replay and swap attacks.
        """
        self._msg_counter += 1
        aad = f"{direction}:v1:msg_id:{self._msg_counter}".encode()
        nonce = os.urandom(12)
        ct = AESGCM(self._encrypt_key).encrypt(nonce, plaintext.encode(), aad)
        return {
            "iv":  base64.b64encode(nonce).decode(),
            "ct":  base64.b64encode(ct).decode(),
            "aad": aad.decode()  # sent in plaintext — authenticated but not encrypted
        }

    def decrypt(self, envelope: dict, expected_direction: str) -> str:
        """
        Verifies AAD prefix matches expected direction before decryption.
        Enforces monotonically increasing msg_id to prevent replay attacks.
        Raises ValueError if direction mismatch or replay detected.
        """
        aad = envelope["aad"].encode()
        if not aad.startswith(expected_direction.encode()):
            raise ValueError(f"AAD direction mismatch: expected prefix {expected_direction!r}, got {aad!r}")
        
        # Extract and validate msg_id from AAD (format: "direction:v1:msg_id:N")
        try:
            msg_id = int(aad.decode().split("msg_id:")[1])
            if msg_id <= self._last_seen_msg_id:
                raise ValueError(f"Replay attack detected: msg_id {msg_id} is not greater than last seen {self._last_seen_msg_id}")
            self._last_seen_msg_id = msg_id
        except (IndexError, ValueError) as e:
            if "Replay attack" in str(e):
                raise
            raise ValueError(f"Invalid AAD format — cannot extract msg_id: {aad!r}")
        
        nonce = base64.b64decode(envelope["iv"])
        ct    = base64.b64decode(envelope["ct"])
        
        # AES-GCM will raise InvalidTag if AAD is tampered with, even if prefix matched.
        return AESGCM(self._decrypt_key).decrypt(nonce, ct, aad).decode()
