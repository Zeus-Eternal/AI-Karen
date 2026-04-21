"""
File Attachment Service Compatibility Layer.

This module provides a simplified compatibility layer for file attachment functionality
that was previously in the chat directory. Since the original services were removed during
demolition, this provides basic functionality with warnings.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

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

    file_name: str
    file_type: FileType
    file_size: int
    content_type: str
    user_id: str
    conversation_id: Optional[str] = None


@dataclass
class FileUploadResponse:
    """File upload response."""

    file_id: str
    file_name: str
    file_url: str
    file_size: int
    processing_status: ProcessingStatus
    created_at: datetime
    error_message: Optional[str] = None


@dataclass
class FileProcessingResult:
    """File processing result."""

    file_id: str
    processing_status: ProcessingStatus
    extracted_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class FileAttachmentService:
    """Simplified file attachment service for compatibility."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.warning(
            "Using compatibility FileAttachmentService - full functionality not available"
        )

    async def upload_file(self, request: FileUploadRequest) -> FileUploadResponse:
        """Upload a file (simplified implementation)."""
        file_id = str(uuid.uuid4())

        # Simulate file processing
        self.logger.info(f"Processing file upload: {request.file_name}")

        return FileUploadResponse(
            file_id=file_id,
            file_name=request.file_name,
            file_url=f"/api/files/{file_id}",
            file_size=request.file_size,
            processing_status=ProcessingStatus.COMPLETED,
            created_at=datetime.now(),
        )

    async def process_file(self, file_id: str) -> FileProcessingResult:
        """Process a file (simplified implementation)."""
        self.logger.info(f"Processing file: {file_id}")

        return FileProcessingResult(
            file_id=file_id,
            processing_status=ProcessingStatus.COMPLETED,
            extracted_text="File content extraction not available in compatibility mode",
            metadata={"mode": "compatibility"},
        )

    async def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file information (simplified implementation)."""
        return {
            "file_id": file_id,
            "file_url": f"/api/files/{file_id}",
            "available": True,
        }


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
    operations: List[str]


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
    """Simplified multimedia service for compatibility."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.warning(
            "Using compatibility MultimediaService - full functionality not available"
        )

    async def process_media(
        self, request: MediaProcessingRequest
    ) -> MediaProcessingResponse:
        """Process media files (simplified implementation)."""
        self.logger.info(f"Processing media: {request.file_id}")

        return MediaProcessingResponse(
            file_id=request.file_id,
            processing_status=ProcessingStatus.COMPLETED,
            processed_files=[request.file_id],
            metadata={"mode": "compatibility"},
        )

    def get_capabilities(self) -> List[ProcessingCapability]:
        """Get available processing capabilities."""
        return [
            ProcessingCapability(MediaType.IMAGE, ["resize", "compress"]),
            ProcessingCapability(MediaType.VIDEO, ["transcode", "compress"]),
            ProcessingCapability(MediaType.AUDIO, ["convert", "compress"]),
        ]


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
    """Simplified hook enabled file service for compatibility."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.warning(
            "Using compatibility HookEnabledFileService - full functionality not available"
        )

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
