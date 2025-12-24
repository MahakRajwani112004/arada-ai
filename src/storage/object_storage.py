"""Object storage abstraction for document storage.

Supports MinIO (default for air-gapped) and can be extended to S3.
"""
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO
from typing import Optional

from miniopy_async import Minio

from src.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class StorageConfig:
    """Configuration for object storage."""

    endpoint: str = "localhost:9000"
    access_key: str = "magure"
    secret_key: str = "magure_minio_secret"
    bucket_name: str = "knowledge-documents"
    secure: bool = False  # Use HTTPS


class ObjectStorage(ABC):
    """Abstract base class for object storage backends."""

    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload data and return the storage key."""
        pass

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Download data by key."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete object by key."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if object exists."""
        pass

    @abstractmethod
    async def get_url(self, key: str, expires_seconds: int = 3600) -> str:
        """Get a presigned URL for the object."""
        pass


class MinIOStorage(ObjectStorage):
    """MinIO object storage backend (S3-compatible)."""

    def __init__(self, config: Optional[StorageConfig] = None):
        """Initialize MinIO client."""
        self.config = config or StorageConfig()
        self._client: Optional[Minio] = None
        self._bucket_ensured = False

    async def _get_client(self) -> Minio:
        """Get or create MinIO client."""
        if self._client is None:
            self._client = Minio(
                self.config.endpoint,
                access_key=self.config.access_key,
                secret_key=self.config.secret_key,
                secure=self.config.secure,
            )
        return self._client

    async def _ensure_bucket(self) -> None:
        """Ensure the bucket exists."""
        if self._bucket_ensured:
            return

        client = await self._get_client()
        bucket_exists = await client.bucket_exists(self.config.bucket_name)

        if not bucket_exists:
            await client.make_bucket(self.config.bucket_name)
            logger.info("minio_bucket_created", bucket=self.config.bucket_name)

        self._bucket_ensured = True

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload data to MinIO."""
        await self._ensure_bucket()
        client = await self._get_client()

        data_stream = BytesIO(data)
        data_length = len(data)

        await client.put_object(
            bucket_name=self.config.bucket_name,
            object_name=key,
            data=data_stream,
            length=data_length,
            content_type=content_type,
        )

        logger.info("minio_upload_success", key=key, size=data_length)
        return key

    async def download(self, key: str) -> bytes:
        """Download data from MinIO."""
        client = await self._get_client()

        response = await client.get_object(
            bucket_name=self.config.bucket_name,
            object_name=key,
        )

        try:
            data = await response.read()
            logger.info("minio_download_success", key=key, size=len(data))
            return data
        finally:
            response.close()
            await response.release()

    async def delete(self, key: str) -> bool:
        """Delete object from MinIO."""
        client = await self._get_client()

        try:
            await client.remove_object(
                bucket_name=self.config.bucket_name,
                object_name=key,
            )
            logger.info("minio_delete_success", key=key)
            return True
        except Exception as e:
            logger.error("minio_delete_failed", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """Check if object exists in MinIO."""
        client = await self._get_client()

        try:
            await client.stat_object(
                bucket_name=self.config.bucket_name,
                object_name=key,
            )
            return True
        except Exception:
            return False

    async def get_url(self, key: str, expires_seconds: int = 3600) -> str:
        """Get presigned URL for object."""
        from datetime import timedelta

        client = await self._get_client()

        url = await client.presigned_get_object(
            bucket_name=self.config.bucket_name,
            object_name=key,
            expires=timedelta(seconds=expires_seconds),
        )
        return url


# Factory function to get storage backend
_storage_instance: Optional[ObjectStorage] = None


def get_storage_config() -> StorageConfig:
    """Get storage config from environment."""
    return StorageConfig(
        endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "magure"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "magure_minio_secret"),
        bucket_name=os.getenv("MINIO_BUCKET", "knowledge-documents"),
        secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
    )


def get_storage() -> ObjectStorage:
    """Get the storage backend singleton."""
    global _storage_instance
    if _storage_instance is None:
        config = get_storage_config()
        _storage_instance = MinIOStorage(config)
    return _storage_instance
