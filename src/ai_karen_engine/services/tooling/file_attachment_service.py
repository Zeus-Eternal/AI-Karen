"""
File Attachment Service Compatibility Layer.

This module provides a simplified compatibility layer for file attachment functionality
that was previously in the chat directory. Since the original services were removed during
demolition, this provides basic functionality with warnings.
"""

import logging
import uuid
import os
import shutil
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


class FileType(str, Enum):
    """Supported file types."""

    IMAGE = "image"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    CODE = "code"
    OTHER = "other"


class ProcessingStatus(str, Enum):
    """File processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class FileUploadRequest:
    """File upload request."""

    conversation_id: str
    user_id: str
    filename: str
    content_type: str
    file_size: int
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileUploadResponse:
    """File upload response."""

    success: bool
    file_id: Optional[str] = None
    message: Optional[str] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    processing_status: Optional[ProcessingStatus] = None
    created_at: Optional[datetime] = None


@dataclass
class FileProcessingResult:
    """File processing result."""

    file_id: str
    processing_status: ProcessingStatus
    extracted_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


@dataclass
class FileMetadata:
    """File metadata."""

    file_id: str
    filename: str
    original_filename: str
    file_type: FileType
    mime_type: str
    file_size: int
    upload_timestamp: datetime
    processing_status: ProcessingStatus
    storage_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    preview_available: bool = False
    extracted_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class FileAttachmentService:
    """File attachment service for managing uploaded files."""

    def __init__(self, storage_path: str = "./data/attachments"):
        self.logger = logging.getLogger(__name__)
        self.storage_path = Path(storage_path)
        self.max_file_size = 100 * 1024 * 1024  # 100MB default
        
        # In-memory metadata storage (simplified for this layer)
        self._files_metadata: Dict[str, FileMetadata] = {}
        
        # Ensure storage directories exist
        self._setup_storage()

    def _setup_storage(self):
        """Setup storage directories."""
        (self.storage_path / "files").mkdir(parents=True, exist_ok=True)
        (self.storage_path / "thumbnails").mkdir(parents=True, exist_ok=True)
        (self.storage_path / "previews").mkdir(parents=True, exist_ok=True)

    async def upload_file(self, request: FileUploadRequest, file_content: Any) -> FileUploadResponse:
        """Upload a file from a file-like object."""
        try:
            file_id = str(uuid.uuid4())
            
            # Determine file type
            file_type = self._detect_file_type(request.filename, request.content_type)
            
            # Save file content
            storage_filename = f"{file_id}_{request.filename}"
            file_path = self.storage_path / "files" / storage_filename
            
            with open(file_path, "wb") as f:
                if hasattr(file_content, "read"):
                    # Handle file-like objects (e.g. SpooledTemporaryFile)
                    shutil.copyfileobj(file_content, f)
                else:
                    # Handle bytes
                    f.write(file_content)
            
            # Create metadata
            metadata = FileMetadata(
                file_id=file_id,
                filename=storage_filename,
                original_filename=request.filename,
                file_type=file_type,
                mime_type=request.content_type,
                file_size=request.file_size,
                upload_timestamp=datetime.now(),
                processing_status=ProcessingStatus.COMPLETED,
                storage_path=str(file_path),
                metadata=request.metadata
            )
            
            self._files_metadata[file_id] = metadata
            
            self.logger.info(f"Successfully uploaded file: {request.filename} (ID: {file_id})")
            
            return FileUploadResponse(
                success=True,
                file_id=file_id,
                file_name=request.filename,
                file_url=f"/api/files/{file_id}/download",
                file_size=request.file_size,
                processing_status=ProcessingStatus.COMPLETED,
                created_at=metadata.upload_timestamp
            )
        except Exception as e:
            self.logger.error(f"File upload failed: {e}")
            return FileUploadResponse(
                success=False,
                message=str(e)
            )

    async def get_file_info(self, file_id: str) -> Optional[FileProcessingResult]:
        """Get file processing information."""
        metadata = self._files_metadata.get(file_id)
        if not metadata:
            return None
            
        return FileProcessingResult(
            file_id=file_id,
            processing_status=metadata.processing_status,
            extracted_text=metadata.extracted_content,
            metadata=metadata.metadata,
            filename=metadata.original_filename,
            file_size=metadata.file_size,
            mime_type=metadata.mime_type
        )

    async def get_file_content(self, file_id: str) -> Optional[bytes]:
        """Get the raw content of a file."""
        metadata = self._files_metadata.get(file_id)
        if not metadata or not metadata.storage_path:
            return None
            
        try:
            with open(metadata.storage_path, "rb") as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read file content: {e}")
            return None

    async def get_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """Get file metadata."""
        return self._files_metadata.get(file_id)

    async def get_thumbnail(self, file_id: str) -> Optional[bytes]:
        """Get file thumbnail if available."""
        metadata = self._files_metadata.get(file_id)
        if not metadata or not metadata.thumbnail_path:
            return None
            
        try:
            with open(metadata.thumbnail_path, "rb") as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Failed to read thumbnail: {e}")
            return None

    async def list_files(self) -> Dict[str, FileMetadata]:
        """List all uploaded files."""
        return self._files_metadata

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file and its metadata."""
        metadata = self._files_metadata.get(file_id)
        if not metadata:
            return False
            
        try:
            if metadata.storage_path and os.path.exists(metadata.storage_path):
                os.remove(metadata.storage_path)
            if metadata.thumbnail_path and os.path.exists(metadata.thumbnail_path):
                os.remove(metadata.thumbnail_path)
            
            del self._files_metadata[file_id]
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete file {file_id}: {e}")
            return False

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        total_size = sum(m.file_size for m in self._files_metadata.values())
        return {
            "total_files": len(self._files_metadata),
            "total_size_bytes": total_size,
            "storage_path": str(self.storage_path)
        }

    def _detect_file_type(self, filename: str, content_type: str) -> FileType:
        """Detect the file type category."""
        if "image" in content_type:
            return FileType.IMAGE
        if "video" in content_type:
            return FileType.VIDEO
        if "audio" in content_type:
            return FileType.AUDIO
        
        ext = os.path.splitext(filename)[1].lower()
        if ext in [".txt", ".pdf", ".doc", ".docx", ".md"]:
            return FileType.DOCUMENT
        if ext in [".py", ".js", ".ts", ".html", ".css", ".json"]:
            return FileType.CODE
            
        return FileType.OTHER


# Global service instance
_service: Optional[FileAttachmentService] = None


def get_file_attachment_service() -> FileAttachmentService:
    """Get the file attachment service instance."""
    global _service
    if _service is None:
        _service = FileAttachmentService()
    return _service


# Multimedia service compatibility
class MediaType(str, Enum):
    """Supported media types."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


@dataclass
class MediaProcessingRequest:
    """Media processing request."""

    file_id: str
    media_type: MediaType
    capabilities: List["ProcessingCapability"]
    options: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1


@dataclass
class MediaProcessingResponse:
    """Media processing response."""

    file_id: str
    processing_status: ProcessingStatus
    processed_files: List[str]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingCapability:
    """Media processing capability."""

    media_type: MediaType
    operations: List[str]
    available: bool = True


class MultimediaService:
    """Multimedia service for processing media files."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def process_media(
        self, request: MediaProcessingRequest, file_path: Union[str, Path]
    ) -> MediaProcessingResponse:
        """Process media files (stub implementation)."""
        self.logger.info(f"Processing media: {request.file_id} type: {request.media_type}")

        # In a real implementation, this would use ffmpeg, PIL, etc.
        return MediaProcessingResponse(
            file_id=request.file_id,
            processing_status=ProcessingStatus.COMPLETED,
            processed_files=[str(file_path)],
            metadata={"mode": "simulated", "processed_at": datetime.now().isoformat()}
        )

    def get_available_capabilities(self) -> List[MediaType]:
        """Get available processing capabilities."""
        return [MediaType.IMAGE, MediaType.VIDEO, MediaType.AUDIO]

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get multimedia processing statistics."""
        return {
            "queue_depth": 0,
            "processed_count": 0,
            "failed_count": 0,
            "active_workers": 0
        }


# Global multimedia service instance
_multimedia_service: Optional[MultimediaService] = None


def get_multimedia_service() -> MultimediaService:
    """Get the multimedia service instance."""
    global _multimedia_service
    if _multimedia_service is None:
        _multimedia_service = MultimediaService()
    return _multimedia_service


# Hook enabled file service compatibility
class HookEnabledFileService:
    """Service for processing files with external hooks."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def process_file_with_hooks(
        self, file_id: str, hooks: List[str]
    ) -> Dict[str, Any]:
        """Process file with hooks (simplified implementation)."""
        self.logger.info(f"Processing file with hooks: {file_id}")

        return {
            "file_id": file_id,
            "hooks_applied": hooks,
            "status": "completed",
            "mode": "compatibility",
        }


# Global hook enabled file service instance
_hook_enabled_service: Optional[HookEnabledFileService] = None


def get_hook_enabled_file_service() -> HookEnabledFileService:
    """Get the hook enabled file service instance."""
    global _hook_enabled_service
    if _hook_enabled_service is None:
        _hook_enabled_service = HookEnabledFileService()
    return _hook_enabled_service
