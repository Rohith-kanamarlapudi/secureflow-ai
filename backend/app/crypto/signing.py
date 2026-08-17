import base64

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import (
    padding,
    rsa,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
    load_pem_public_key,
)


def generate_signing_key_pair():
    """
    Generate a 2048-bit RSA signing key pair.
    """

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )

    public_pem = public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo,
    )

    return private_pem, public_pem


def load_private_key(
    private_pem: bytes,
):
    return load_pem_private_key(
        private_pem,
        password=None,
    )


def load_public_key(
    public_pem: bytes,
):
    return load_pem_public_key(
        public_pem,
    )


def sign_hash(
    private_key,
    sha256_hex_digest: str,
) -> bytes:
    """
    Sign a SHA-256 hexadecimal digest using RSA-PSS.
    """

    return private_key.sign(
        bytes.fromhex(sha256_hex_digest),
        padding.PSS(
            mgf=padding.MGF1(
                hashes.SHA256()
            ),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )


def verify_signature(
    public_key,
    signature: bytes,
    sha256_hex_digest: str,
) -> bool:
    """
    Verify an RSA-PSS signature against a SHA-256 digest.
    """

    try:
        public_key.verify(
            signature,
            bytes.fromhex(sha256_hex_digest),
            padding.PSS(
                mgf=padding.MGF1(
                    hashes.SHA256()
                ),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )

        return True

    except InvalidSignature:
        return False


def encode_signature(
    signature: bytes,
) -> str:
    return base64.b64encode(
        signature
    ).decode("utf-8")


def decode_signature(
    signature: str,
) -> bytes:
    return base64.b64decode(
        signature
    )


def encode_public_key(
    public_key_pem: bytes,
) -> str:
    return base64.b64encode(
        public_key_pem
    ).decode("utf-8")


def decode_public_key(
    public_key: str,
) -> bytes:
    return base64.b64decode(
        public_key
    )