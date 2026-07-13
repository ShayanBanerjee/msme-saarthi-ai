"""Authenticated field encryption, blind indexes, passwords, and session secrets."""

import base64
import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class DataCipher:
    """AES-256-GCM envelope with domain-bound associated data."""

    def __init__(self, *, key_base64: str, key_version: str) -> None:
        try:
            key = base64.b64decode(key_base64, validate=True)
        except ValueError as error:
            raise ValueError("data encryption key must be valid base64") from error
        if len(key) != 32:
            raise ValueError("data encryption key must decode to exactly 32 bytes")
        self._key = key
        self._key_version = key_version
        self._aes = AESGCM(key)

    def encrypt(self, value: str, *, field: str) -> str:
        nonce = secrets.token_bytes(12)
        ciphertext = self._aes.encrypt(nonce, value.encode(), field.encode())
        payload = base64.urlsafe_b64encode(nonce + ciphertext).decode()
        return f"{self._key_version}:{payload}"

    def decrypt(self, value: str, *, field: str) -> str:
        version, payload = value.split(":", 1)
        if version != self._key_version:
            raise ValueError(f"unsupported encryption key version: {version}")
        raw = base64.urlsafe_b64decode(payload)
        return self._aes.decrypt(raw[:12], raw[12:], field.encode()).decode()

    def blind_index(self, value: str, *, field: str) -> str:
        return hmac.new(self._key, f"{field}:{value}".encode(), hashlib.sha256).hexdigest()


class CredentialProtector:
    """Argon2id passwords and SHA-256 opaque-session token hashes."""

    def __init__(self) -> None:
        self._passwords = PasswordHasher(time_cost=3, memory_cost=65_536, parallelism=4)
        self._dummy_hash = self._passwords.hash("timing-equalization-only-not-a-credential")

    def hash_password(self, password: str) -> str:
        return self._passwords.hash(password)

    def verify_password(self, password_hash: str | None, password: str) -> bool:
        candidate = password_hash or self._dummy_hash
        try:
            valid: bool = self._passwords.verify(candidate, password)
        except (InvalidHashError, VerifyMismatchError):
            valid = False
        return valid and password_hash is not None

    @staticmethod
    def new_session_secret() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_session_secret(secret: str) -> str:
        return hashlib.sha256(secret.encode()).hexdigest()
