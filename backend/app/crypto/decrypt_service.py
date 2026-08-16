from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.crypto.base import EncryptedBlob


def decrypt_file(
    blob: EncryptedBlob,
    master_key: bytes,
) -> bytes:
    """
    Unwrap the per-file data key and decrypt the file.
    """

    # First 12 bytes are the wrapping nonce
    wrap_nonce = blob.wrapped_key[:12]

    # Remaining bytes are wrapped data key + GCM tag
    wrapped = blob.wrapped_key[12:]

    # Recover per-file AES-256 key
    data_key = AESGCM(master_key).decrypt(
        wrap_nonce,
        wrapped,
        None,
    )

    # Reconstruct ciphertext + authentication tag
    encrypted = blob.ciphertext + blob.tag

    # Decrypt original file
    plaintext = AESGCM(data_key).decrypt(
        blob.nonce,
        encrypted,
        None,
    )

    return plaintext