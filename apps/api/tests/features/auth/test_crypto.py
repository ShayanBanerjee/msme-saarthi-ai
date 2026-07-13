"""Cryptographic boundary tests."""

import pytest
from cryptography.exceptions import InvalidTag

from app.features.auth.crypto import CredentialProtector, DataCipher

KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


def test_sensitive_fields_are_authenticated_and_not_stored_as_plaintext() -> None:
    cipher = DataCipher(key_base64=KEY, key_version="v1")
    encrypted = cipher.encrypt("founder@example.test", field="email")

    assert "founder@example.test" not in encrypted
    assert cipher.decrypt(encrypted, field="email") == "founder@example.test"
    with pytest.raises(InvalidTag):
        cipher.decrypt(encrypted, field="business_name")


def test_blind_indexes_are_stable_and_domain_separated() -> None:
    cipher = DataCipher(key_base64=KEY, key_version="v1")
    first = cipher.blind_index("founder@example.test", field="email_lookup")
    assert first == cipher.blind_index("founder@example.test", field="email_lookup")
    assert first != cipher.blind_index("founder@example.test", field="other")


def test_passwords_use_argon2_and_session_secrets_are_only_hashable() -> None:
    protector = CredentialProtector()
    password_hash = protector.hash_password("a-strong-test-password")
    secret = protector.new_session_secret()

    assert password_hash.startswith("$argon2id$")
    assert protector.verify_password(password_hash, "a-strong-test-password")
    assert not protector.verify_password(password_hash, "wrong-password")
    assert secret not in protector.hash_session_secret(secret)
