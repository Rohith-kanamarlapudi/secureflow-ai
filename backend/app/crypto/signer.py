from pathlib import Path

from app.core.config import settings
from app.crypto.signing import (
    generate_signing_key_pair,
    load_private_key,
)


def get_private_key():
    """
    Load the application's RSA private signing key.

    For development:
    - Generate the key automatically if it does not exist.
    - Reuse the same key afterwards.
    """

    path = Path(
        settings.SIGNING_PRIVATE_KEY_PATH
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not path.exists():

        private_pem, _ = (
            generate_signing_key_pair()
        )

        path.write_bytes(
            private_pem
        )

    return load_private_key(
        path.read_bytes()
    )