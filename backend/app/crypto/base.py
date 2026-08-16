from dataclasses import dataclass


@dataclass
class EncryptedBlob:
    ciphertext: bytes
    nonce: bytes
    tag: bytes
    wrapped_key: bytes
    key_version: str