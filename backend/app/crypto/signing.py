from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidSignature


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


def verify_signature(
    public_key,
    signature: bytes,
    sha256_hex_digest: str,
) -> bool:
    try:
        public_key.verify(
            signature,
            bytes.fromhex(sha256_hex_digest),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )

        return True

    except InvalidSignature:
        return False