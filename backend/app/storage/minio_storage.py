import io

from minio import Minio

from app.storage.base import StorageService


class MinioStorage(StorageService):

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
    ):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False,
        )

        self.bucket = bucket

        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def put(
        self,
        key: str,
        data: bytes,
        content_type: str,
    ) -> None:
        self.client.put_object(
            self.bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    def get(
        self,
        key: str,
    ) -> bytes:
        response = self.client.get_object(
            self.bucket,
            key,
        )

        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(
        self,
        key: str,
    ) -> None:
        self.client.remove_object(
            self.bucket,
            key,
        )