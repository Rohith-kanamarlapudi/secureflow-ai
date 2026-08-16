import hashlib

from app.core.config import settings


def get_master_key() -> bytes:
    """
    Derive a deterministic 32-byte AES-256 master key
    from the configured encryption secret.

    In production, this should come from a proper KMS/
    secret-management system.
    """

    return hashlib.sha256(
        settings.ENCRYPTION_MASTER_KEY.encode("utf-8")
    ).digest()