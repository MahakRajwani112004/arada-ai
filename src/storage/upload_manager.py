"""Chunked upload manager for resumable file uploads.

Supports:
- Initializing uploads with metadata
- Uploading chunks individually
- Tracking upload progress in Redis
- Resuming failed uploads
- Automatic cleanup of abandoned uploads
"""

import hashlib
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from src.config.logging import get_logger
from src.storage.object_storage import get_storage
from src.storage.redis_client import RedisCache

logger = get_logger(__name__)

# Upload configuration
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB per chunk
UPLOAD_TTL = 24 * 60 * 60  # 24 hours TTL for upload sessions
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB max file size


class UploadStatus(str, Enum):
    """Upload session status."""
    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class UploadSession:
    """Represents an upload session."""
    upload_id: str
    knowledge_base_id: str
    filename: str
    file_size: int
    total_chunks: int
    chunk_size: int
    content_type: str
    status: UploadStatus
    received_chunks: set = field(default_factory=set)
    created_at: str = ""
    updated_at: str = ""
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    storage_key: Optional[str] = None
    checksum: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "upload_id": self.upload_id,
            "knowledge_base_id": self.knowledge_base_id,
            "filename": self.filename,
            "file_size": str(self.file_size),
            "total_chunks": str(self.total_chunks),
            "chunk_size": str(self.chunk_size),
            "content_type": self.content_type,
            "status": self.status.value,
            "received_chunks": ",".join(str(c) for c in sorted(self.received_chunks)),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at or "",
            "error_message": self.error_message or "",
            "storage_key": self.storage_key or "",
            "checksum": self.checksum or "",
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UploadSession":
        """Create from dictionary."""
        received = data.get("received_chunks", "")
        received_set = set(int(c) for c in received.split(",") if c)

        return cls(
            upload_id=data["upload_id"],
            knowledge_base_id=data["knowledge_base_id"],
            filename=data["filename"],
            file_size=int(data["file_size"]),
            total_chunks=int(data["total_chunks"]),
            chunk_size=int(data["chunk_size"]),
            content_type=data["content_type"],
            status=UploadStatus(data["status"]),
            received_chunks=received_set,
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            completed_at=data.get("completed_at") or None,
            error_message=data.get("error_message") or None,
            storage_key=data.get("storage_key") or None,
            checksum=data.get("checksum") or None,
        )


class UploadManager:
    """Manages chunked file uploads with Redis-backed state."""

    def __init__(self):
        self.cache = RedisCache(prefix="magone:upload")
        self.temp_dir = tempfile.gettempdir()

    def _session_key(self, upload_id: str) -> str:
        """Get Redis key for upload session."""
        return f"session:{upload_id}"

    def _chunk_key(self, upload_id: str, chunk_num: int) -> str:
        """Get temp file path for chunk."""
        return os.path.join(self.temp_dir, f"upload_{upload_id}_chunk_{chunk_num}")

    async def init_upload(
        self,
        knowledge_base_id: str,
        filename: str,
        file_size: int,
        content_type: str,
        chunk_size: int = CHUNK_SIZE,
    ) -> UploadSession:
        """Initialize a new upload session.

        Args:
            knowledge_base_id: Target knowledge base ID
            filename: Original filename
            file_size: Total file size in bytes
            content_type: MIME type
            chunk_size: Size of each chunk (default 5MB)

        Returns:
            UploadSession with upload_id and chunk info
        """
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum of {MAX_FILE_SIZE} bytes")

        upload_id = uuid4().hex[:16]
        total_chunks = (file_size + chunk_size - 1) // chunk_size  # Ceiling division
        now = datetime.now(timezone.utc).isoformat()

        session = UploadSession(
            upload_id=upload_id,
            knowledge_base_id=knowledge_base_id,
            filename=filename,
            file_size=file_size,
            total_chunks=total_chunks,
            chunk_size=chunk_size,
            content_type=content_type,
            status=UploadStatus.INITIALIZED,
            created_at=now,
            updated_at=now,
        )

        # Store in Redis with TTL
        await self._save_session(session)

        logger.info(
            "upload_initialized",
            upload_id=upload_id,
            filename=filename,
            file_size=file_size,
            total_chunks=total_chunks,
        )

        return session

    async def upload_chunk(
        self,
        upload_id: str,
        chunk_num: int,
        data: bytes,
    ) -> UploadSession:
        """Upload a single chunk.

        Args:
            upload_id: Upload session ID
            chunk_num: Chunk number (0-indexed)
            data: Chunk data

        Returns:
            Updated UploadSession
        """
        session = await self.get_session(upload_id)
        if not session:
            raise ValueError(f"Upload session not found: {upload_id}")

        if session.status in (UploadStatus.COMPLETED, UploadStatus.FAILED):
            raise ValueError(f"Upload session is {session.status.value}")

        if chunk_num < 0 or chunk_num >= session.total_chunks:
            raise ValueError(f"Invalid chunk number: {chunk_num}")

        # Write chunk to temp file
        chunk_path = self._chunk_key(upload_id, chunk_num)
        with open(chunk_path, "wb") as f:
            f.write(data)

        # Update session
        session.received_chunks.add(chunk_num)
        session.status = UploadStatus.IN_PROGRESS
        session.updated_at = datetime.now(timezone.utc).isoformat()

        await self._save_session(session)

        logger.debug(
            "chunk_uploaded",
            upload_id=upload_id,
            chunk_num=chunk_num,
            received=len(session.received_chunks),
            total=session.total_chunks,
        )

        return session

    async def complete_upload(self, upload_id: str) -> UploadSession:
        """Complete the upload by assembling chunks and storing in MinIO.

        Args:
            upload_id: Upload session ID

        Returns:
            Completed UploadSession with storage_key
        """
        session = await self.get_session(upload_id)
        if not session:
            raise ValueError(f"Upload session not found: {upload_id}")

        # Verify all chunks received
        expected = set(range(session.total_chunks))
        if session.received_chunks != expected:
            missing = expected - session.received_chunks
            raise ValueError(f"Missing chunks: {sorted(missing)}")

        session.status = UploadStatus.COMPLETING
        await self._save_session(session)

        try:
            # Assemble file from chunks
            hasher = hashlib.sha256()
            assembled_data = bytearray()

            for chunk_num in range(session.total_chunks):
                chunk_path = self._chunk_key(upload_id, chunk_num)
                with open(chunk_path, "rb") as f:
                    chunk_data = f.read()
                    hasher.update(chunk_data)
                    assembled_data.extend(chunk_data)

            # Verify size
            if len(assembled_data) != session.file_size:
                raise ValueError(
                    f"Size mismatch: expected {session.file_size}, got {len(assembled_data)}"
                )

            # Upload to MinIO
            storage = get_storage()
            file_id = uuid4().hex[:12]
            storage_key = f"{session.knowledge_base_id}/{file_id}_{session.filename}"

            await storage.upload(
                key=storage_key,
                data=bytes(assembled_data),
                content_type=session.content_type,
            )

            # Update session
            session.status = UploadStatus.COMPLETED
            session.completed_at = datetime.now(timezone.utc).isoformat()
            session.storage_key = storage_key
            session.checksum = hasher.hexdigest()
            session.updated_at = session.completed_at

            await self._save_session(session)

            # Cleanup temp files
            await self._cleanup_chunks(upload_id, session.total_chunks)

            logger.info(
                "upload_completed",
                upload_id=upload_id,
                storage_key=storage_key,
                checksum=session.checksum,
            )

            return session

        except Exception as e:
            session.status = UploadStatus.FAILED
            session.error_message = str(e)
            session.updated_at = datetime.now(timezone.utc).isoformat()
            await self._save_session(session)

            logger.error("upload_failed", upload_id=upload_id, error=str(e))
            raise

    async def get_session(self, upload_id: str) -> Optional[UploadSession]:
        """Get upload session by ID."""
        data = await self.cache.hgetall(self._session_key(upload_id))
        if not data:
            return None
        return UploadSession.from_dict(data)

    async def cancel_upload(self, upload_id: str) -> bool:
        """Cancel an upload and cleanup resources."""
        session = await self.get_session(upload_id)
        if not session:
            return False

        # Cleanup temp files
        await self._cleanup_chunks(upload_id, session.total_chunks)

        # Delete Redis key
        await self.cache.delete(self._session_key(upload_id))

        logger.info("upload_cancelled", upload_id=upload_id)
        return True

    async def _save_session(self, session: UploadSession) -> None:
        """Save session to Redis."""
        key = self._session_key(session.upload_id)
        for field, value in session.to_dict().items():
            await self.cache.hset(key, field, value)
        await self.cache.expire(key, UPLOAD_TTL)

    async def _cleanup_chunks(self, upload_id: str, total_chunks: int) -> None:
        """Remove temporary chunk files."""
        for chunk_num in range(total_chunks):
            chunk_path = self._chunk_key(upload_id, chunk_num)
            try:
                if os.path.exists(chunk_path):
                    os.remove(chunk_path)
            except Exception as e:
                logger.warning(
                    "chunk_cleanup_failed",
                    upload_id=upload_id,
                    chunk_num=chunk_num,
                    error=str(e),
                )


# Global upload manager instance
_upload_manager: Optional[UploadManager] = None


def get_upload_manager() -> UploadManager:
    """Get upload manager singleton."""
    global _upload_manager
    if _upload_manager is None:
        _upload_manager = UploadManager()
    return _upload_manager
