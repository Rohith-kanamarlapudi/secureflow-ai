from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes


def sign_hash(
    private_key: rsa.RSAPrivateKey,
    sha256_hex_digest: str,
) -> bytes:
    return private_key.sign(
        bytes.fromhex(sha256_hex_digest),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )