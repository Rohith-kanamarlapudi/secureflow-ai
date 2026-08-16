from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.crypto.base import EncryptedBlob


def decrypt_file(
    blob: EncryptedBlob,
    master_key: bytes,
) -> bytes:
    """
    Decrypt a file using envelope encryption.

    Steps:
    1. Extract the wrapping nonce.
    2. Unwrap/decrypt the per-file data key using the master key.
    3. Decrypt the file ciphertext using the recovered data key.
    """

    # ---------------------------------------------------------
    # 1. Extract wrapping nonce and wrapped data key
    # ---------------------------------------------------------
    wrap_nonce = blob.wrapped_key[:12]
    wrapped = blob.wrapped_key[12:]

    # ---------------------------------------------------------
    # 2. Recover the per-file AES-256 data key
    # ---------------------------------------------------------
    data_key = AESGCM(master_key).decrypt(
        wrap_nonce,
        wrapped,
        None,
    )

    # ---------------------------------------------------------
    # 3. Reconstruct ciphertext + authentication tag
    # ---------------------------------------------------------
    encrypted = blob.ciphertext + blob.tag

    # ---------------------------------------------------------
    # 4. Decrypt the file
    # ---------------------------------------------------------
    plaintext = AESGCM(data_key).decrypt(
        blob.nonce,
        encrypted,
        None,
    )

    return plaintext