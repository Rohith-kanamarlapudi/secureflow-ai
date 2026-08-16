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
    The data key is then encrypted using the master key.
    """

    # ---------------------------------------------------------
    # 1. Generate a random AES-256 key for this file
    # ---------------------------------------------------------
    data_key = AESGCM.generate_key(bit_length=256)

    # ---------------------------------------------------------
    # 2. Encrypt the file using AES-256-GCM
    # ---------------------------------------------------------
    nonce = os.urandom(12)

    aesgcm = AESGCM(data_key)

    # AESGCM.encrypt() returns ciphertext + 16-byte authentication tag
    encrypted = aesgcm.encrypt(
        nonce,
        plaintext,
        None,
    )

    # Separate ciphertext and authentication tag
    ciphertext = encrypted[:-16]
    tag = encrypted[-16:]

    # ---------------------------------------------------------
    # 3. Wrap/encrypt the per-file data key using master key
    # ---------------------------------------------------------
    wrapper = AESGCM(master_key)

    wrap_nonce = os.urandom(12)

    wrapped_data_key = wrapper.encrypt(
        wrap_nonce,
        data_key,
        None,
    )

    # Store the nonce together with the wrapped key
    wrapped_key = wrap_nonce + wrapped_data_key

    # ---------------------------------------------------------
    # 4. Return encryption metadata
    # ---------------------------------------------------------
    return EncryptedBlob(
        ciphertext=ciphertext,
        nonce=nonce,
        tag=tag,
        wrapped_key=wrapped_key,
        key_version=key_version,
    )