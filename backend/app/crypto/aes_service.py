import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.crypto.base import EncryptedBlob


def encrypt_file(
    plaintext: bytes,
    master_key: bytes,
    key_version: str,
) -> EncryptedBlob:
    """
    Encrypt a file using envelope encryption.

    A random AES-256 data key is generated for every file.
    The data key is then wrapped using the master key.
    """

    # Random per-file AES-256 key
    data_key = AESGCM.generate_key(bit_length=256)

    # Random 12-byte GCM nonce
    nonce = os.urandom(12)

    # Encrypt file
    aesgcm = AESGCM(data_key)

    encrypted = aesgcm.encrypt(
        nonce,
        plaintext,
        None,
    )

    # AES-GCM returns ciphertext + 16-byte authentication tag
    ciphertext = encrypted[:-16]
    tag = encrypted[-16:]

    # Wrap the per-file data key using master key
    wrapper = AESGCM(master_key)

    wrap_nonce = os.urandom(12)

    wrapped_data_key = wrapper.encrypt(
        wrap_nonce,
        data_key,
        None,
    )

    # Store wrap nonce + wrapped key
    wrapped_key = wrap_nonce + wrapped_data_key

    return EncryptedBlob(
        ciphertext=ciphertext,
        nonce=nonce,
        tag=tag,
        wrapped_key=wrapped_key,
        key_version=key_version,
    )