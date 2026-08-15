from pathlib import Path

from app.storage.base import StorageService


class LocalStorage(StorageService):

    def __init__(self, base_path: str = "./storage"):
        self.base_path = Path(base_path)

        self.base_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def put(
        self,
        key: str,
        data: bytes,
        content_type: str,
    ) -> None:

        file_path = self.base_path / key

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path.write_bytes(data)

    def get(
        self,
        key: str,
    ) -> bytes:

        file_path = self.base_path / key

        if not file_path.exists():
            raise FileNotFoundError(
                f"Object not found: {key}"
            )

        return file_path.read_bytes()

    def delete(
        self,
        key: str,
    ) -> None:

        file_path = self.base_path / key

        if file_path.exists():
            file_path.unlink()