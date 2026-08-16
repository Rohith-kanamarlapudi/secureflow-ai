# backend/tests/test_crypto.py

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.crypto.aes_service import encrypt_file
from app.crypto.decrypt_service import decrypt_file


def test_encrypt_decrypt_roundtrip():
    plaintext = b"SecureFlow test payload" * 1000

    key = AESGCM.generate_key(bit_length=256)

    blob = encrypt_file(
        plaintext,
        key,
        "v1",
    )

    decrypted = decrypt_file(
        blob,
        key,
    )

    assert decrypted == plaintext


def test_tampered_ciphertext_fails():
    key = AESGCM.generate_key(bit_length=256)

    blob = encrypt_file(
        b"data",
        key,
        "v1",
    )

    # Modify one byte of the ciphertext.
    blob.ciphertext = (
        blob.ciphertext[:-1]
        + bytes([blob.ciphertext[-1] ^ 0xFF])
    )

    with pytest.raises(Exception):
        decrypt_file(
            blob,
            key,
        )