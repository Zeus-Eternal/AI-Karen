"""
File attachment and multimedia support service for chat system.

This module provides comprehensive file upload, processing, and multimedia
integration capabilities for the chat system.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import mimetypes
import os
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO
import json

from sqlalchemy import select

from ai_karen_engine.database import get_postgres_session
from ai_karen_engine.database.models import File as FileModel
from ai_karen_engine.services.webhook_service import dispatch_webhook

try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

logger = logging.getLogger(__name__)


class FileType(str, Enum):
    """Supported file types."""
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """File processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    QUARANTINED = "quarantined"


class SecurityScanResult(str, Enum):
    """Security scan results."""
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    SCAN_FAILED = "scan_failed"


@dataclass
class FileMetadata:
    """File metadata information."""
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    file_type: FileType
    file_hash: str
    upload_timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    security_scan_result: SecurityScanResult = SecurityScanResult.SAFE
    extracted_content: Optional[str] = None
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    thumbnail_path: Optional[str] = None
    preview_available: bool = False


class FileUploadRequest(BaseModel):
    """Request for file upload."""
    conversation_id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., description="File size in bytes")
    description: Optional[str] = Field(None, description="File description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class FileUploadResponse(BaseModel):
    """Response for file upload."""
    file_id: str = Field(..., description="Unique file identifier")
    upload_url: Optional[str] = Field(None, description="Upload URL for large files")
    processing_status: ProcessingStatus = Field(..., description="Processing status")
    metadata: FileMetadata = Field(..., description="File metadata")
    success: bool = Field(..., description="Upload success status")
    message: str = Field(..., description="Status message")


class FileProcessingResult(BaseModel):
    """Result of file processing."""
    file_id: str = Field(..., description="File identifier")
    processing_status: ProcessingStatus = Field(..., description="Processing status")
    extracted_content: Optional[str] = Field(None, description="Extracted text content")
    analysis_results: Dict[str, Any] = Field(default_factory=dict, description="Analysis results")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    preview_url: Optional[str] = Field(None, description="Preview URL")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class FileAttachmentService:
    """
    Service for handling file attachments and multimedia content in chat.
    
    Features:
    - File upload and storage management
    - Document analysis and content extraction
    - Image recognition and processing
    - Security scanning and validation
    - Thumbnail and preview generation
    """
    
    def __init__(
        self,
        storage_path: str = "data/attachments",
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        allowed_extensions: Optional[List[str]] = None,
        enable_security_scan: bool = True,
        enable_content_extraction: bool = True,
        enable_image_analysis: bool = True
    ):
        self.storage_path = Path(storage_path)
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions or self._get_default_extensions()
        self.enable_security_scan = enable_security_scan
        self.enable_content_extraction = enable_content_extraction
        self.enable_image_analysis = enable_image_analysis
        
        # Create storage directories
        self.storage_path.mkdir(parents=True, exist_ok=True)
        (self.storage_path / "files").mkdir(exist_ok=True)
        (self.storage_path / "thumbnails").mkdir(exist_ok=True)
        (self.storage_path / "previews").mkdir(exist_ok=True)
        (self.storage_path / "quarantine").mkdir(exist_ok=True)
        
        # File metadata storage
        self._file_metadata: Dict[str, FileMetadata] = {}

        logger.info(f"FileAttachmentService initialized with storage: {self.storage_path}")

    async def list_files(self) -> Dict[str, FileMetadata]:
        """Return stored file metadata, including database entries."""
        files: Dict[str, FileMetadata] = dict(self._file_metadata)

        try:
            async with get_postgres_session() as session:
                result = await session.execute(select(FileModel))
                for db_file in result.scalars():
                    if db_file.file_id in files:
                        continue
                    meta = db_file.metadata or {}
                    files[db_file.file_id] = FileMetadata(
                        filename=Path(db_file.storage_uri).name if db_file.storage_uri else db_file.name,
                        original_filename=db_file.name,
                        file_size=db_file.bytes or 0,
                        mime_type=db_file.mime_type or "application/octet-stream",
                        file_type=self._determine_file_type(db_file.name, db_file.mime_type or ""),
                        file_hash=db_file.sha256,
                        upload_timestamp=db_file.created_at or datetime.utcnow(),
                        processing_status=ProcessingStatus(
                            meta.get("processing_status", ProcessingStatus.PENDING.value)
                        ),
                        security_scan_result=SecurityScanResult(
                            meta.get("security_scan_result", SecurityScanResult.SAFE.value)
                        ),
                        extracted_content=meta.get("extracted_content"),
                        analysis_results=meta.get("analysis_results", {}),
                        thumbnail_path=meta.get("thumbnail_path"),
                        preview_available=meta.get("preview_available", False),
                    )
        except Exception as e:  # pragma: no cover - database optional
            logger.warning("Failed to load files from database: %s", e)

        return files

    async def get_metadata(self, file_id: str) -> Optional[FileMetadata]:
        """Retrieve metadata for a single file."""
        if file_id in self._file_metadata:
            return self._file_metadata[file_id]

        try:
            async with get_postgres_session() as session:
                db_file = await session.get(FileModel, file_id)
                if not db_file:
                    return None
                meta = db_file.metadata or {}
                return FileMetadata(
                    filename=Path(db_file.storage_uri).name if db_file.storage_uri else db_file.name,
                    original_filename=db_file.name,
                    file_size=db_file.bytes or 0,
                    mime_type=db_file.mime_type or "application/octet-stream",
                    file_type=self._determine_file_type(db_file.name, db_file.mime_type or ""),
                    file_hash=db_file.sha256,
                    upload_timestamp=db_file.created_at or datetime.utcnow(),
                    processing_status=ProcessingStatus(
                        meta.get("processing_status", ProcessingStatus.PENDING.value)
                    ),
                    security_scan_result=SecurityScanResult(
                        meta.get("security_scan_result", SecurityScanResult.SAFE.value)
                    ),
                    extracted_content=meta.get("extracted_content"),
                    analysis_results=meta.get("analysis_results", {}),
                    thumbnail_path=meta.get("thumbnail_path"),
                    preview_available=meta.get("preview_available", False),
                )
        except Exception as e:  # pragma: no cover - database optional
            logger.warning("Failed to fetch file metadata from database: %s", e)
            return None
    
    def _get_default_extensions(self) -> List[str]:
        """Get default allowed file extensions."""
        return [
            # Documents
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
            '.xls', '.xlsx', '.ppt', '.pptx', '.csv',
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
            # Audio
            '.mp3', '.wav', '.ogg', '.m4a', '.flac',
            # Video
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
            # Code
            '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
            '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs',
            # Archives
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'
        ]
    
    def _determine_file_type(self, filename: str, mime_type: str) -> FileType:
        """Determine file type from filename and MIME type."""
        extension = Path(filename).suffix.lower()
        
        if mime_type.startswith('image/'):
            return FileType.IMAGE
        elif mime_type.startswith('audio/'):
            return FileType.AUDIO
        elif mime_type.startswith('video/'):
            return FileType.VIDEO
        elif extension in ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx', '.csv']:
            return FileType.DOCUMENT
        elif extension in ['.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs']:
            return FileType.CODE
        elif extension in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']:
            return FileType.ARCHIVE
        else:
            return FileType.UNKNOWN
    
    def _calculate_file_hash(self, file_handle: BinaryIO) -> str:
        """Calculate SHA-256 hash of file content from a file-like object."""
        file_handle.seek(0)
        hasher = hashlib.sha256()
        for chunk in iter(lambda: file_handle.read(8192), b""):
            hasher.update(chunk)
        file_handle.seek(0)
        return hasher.hexdigest()
    
    def _validate_file(self, filename: str, file_size: int, mime_type: str) -> tuple[bool, str]:
        """Validate file before upload."""
        # Check file size
        if file_size > self.max_file_size:
            return False, f"File size {file_size} exceeds maximum allowed size {self.max_file_size}"
        
        # Check file extension
        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            return False, f"File extension {extension} is not allowed"
        
        # Check for suspicious filenames
        suspicious_patterns = ['..', '/', '\\', '<', '>', '|', ':', '*', '?', '"']
        if any(pattern in filename for pattern in suspicious_patterns):
            return False, f"Filename contains suspicious characters"
        
        return True, "File validation passed"
    
    async def upload_file(
        self,
        request: FileUploadRequest,
        file_handle: BinaryIO
    ) -> FileUploadResponse:
        """Upload and process a file attachment."""
        try:
            # Validate file
            is_valid, validation_message = self._validate_file(
                request.filename, request.file_size, request.content_type
            )

            if not is_valid:
                return FileUploadResponse(
                    file_id="",
                    processing_status=ProcessingStatus.FAILED,
                    metadata=FileMetadata(
                        filename="",
                        original_filename=request.filename,
                        file_size=request.file_size,
                        mime_type=request.content_type,
                        file_type=FileType.UNKNOWN,
                        file_hash="",
                        processing_status=ProcessingStatus.FAILED
                    ),
                    success=False,
                    message=validation_message
                )

            # Generate unique file ID and filename
            file_id = str(uuid.uuid4())
            file_hash = self._calculate_file_hash(file_handle)
            file_extension = Path(request.filename).suffix
            stored_filename = f"{file_id}{file_extension}"
            file_path = self.storage_path / "files" / stored_filename

            # Create file metadata
            file_type = self._determine_file_type(request.filename, request.content_type)
            metadata = FileMetadata(
                filename=stored_filename,
                original_filename=request.filename,
                file_size=request.file_size,
                mime_type=request.content_type,
                file_type=file_type,
                file_hash=file_hash,
                processing_status=ProcessingStatus.PROCESSING
            )

            # Store file
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file_handle, f)

            # Store metadata in memory
            self._file_metadata[file_id] = metadata

            # Persist metadata to database
            try:
                async with get_postgres_session() as session:
                    db_file = FileModel(
                        file_id=file_id,
                        owner_user_id=request.user_id,
                        name=request.filename,
                        mime_type=request.content_type,
                        bytes=request.file_size,
                        storage_uri=str(file_path),
                        sha256=file_hash,
                        metadata={
                            "description": request.description,
                            "tags": request.metadata.get("tags", []),
                            "processing_status": metadata.processing_status.value,
                        },
                    )
                    session.add(db_file)
                    await session.commit()
            except Exception as db_exc:  # pragma: no cover - database optional
                logger.warning("Failed to persist file metadata: %s", db_exc)

            # Dispatch webhook asynchronously
            asyncio.create_task(
                dispatch_webhook(
                    "file.uploaded", {"file_id": file_id, "user_id": request.user_id}
                )
            )

            # Start background processing
            asyncio.create_task(self._process_file(file_id, file_path, metadata))

            return FileUploadResponse(
                file_id=file_id,
                processing_status=ProcessingStatus.PROCESSING,
                metadata=metadata,
                success=True,
                message="File uploaded successfully and processing started"
            )

        except Exception as e:
            logger.error(f"File upload failed: {e}", exc_info=True)
            return FileUploadResponse(
                file_id="",
                processing_status=ProcessingStatus.FAILED,
                metadata=FileMetadata(
                    filename="",
                    original_filename=request.filename,
                    file_size=request.file_size,
                    mime_type=request.content_type,
                    file_type=FileType.UNKNOWN,
                    file_hash="",
                    processing_status=ProcessingStatus.FAILED
                ),
                success=False,
                message=f"File upload failed: {str(e)}"
            )
    
    async def _process_file(
        self,
        file_id: str,
        file_path: Path,
        metadata: FileMetadata
    ) -> None:
        """Process uploaded file in background."""
        try:
            logger.info(f"Starting processing for file {file_id}")

            # Security scan
            if self.enable_security_scan:
                scan_result = await self._security_scan(file_path)
                metadata.security_scan_result = scan_result

                if scan_result == SecurityScanResult.MALICIOUS:
                    await self._quarantine_file(file_id, file_path, "Malicious file detected")
                    return

            # Content extraction
            if self.enable_content_extraction:
                extracted_content = await self._extract_content(file_path, metadata.file_type)
                metadata.extracted_content = extracted_content

            # Image analysis
            if self.enable_image_analysis and metadata.file_type == FileType.IMAGE:
                analysis_results = await self._analyze_image(file_path)
                metadata.analysis_results.update(analysis_results)

            # Generate thumbnail
            thumbnail_path = await self._generate_thumbnail(file_path, metadata.file_type)
            if thumbnail_path:
                metadata.thumbnail_path = str(thumbnail_path)
                metadata.preview_available = True

            # Update processing status
            metadata.processing_status = ProcessingStatus.COMPLETED
            logger.info(f"File processing completed for {file_id}")

        except Exception as e:
            logger.error(f"File processing failed for {file_id}: {e}", exc_info=True)
            metadata.processing_status = ProcessingStatus.FAILED
            metadata.analysis_results["error"] = str(e)

        finally:
            self._file_metadata[file_id] = metadata
            try:
                async with get_postgres_session() as session:
                    db_file = await session.get(FileModel, file_id)
                    if db_file:
                        db_meta = db_file.metadata or {}
                        db_meta.update(
                            {
                                "processing_status": metadata.processing_status.value,
                                "security_scan_result": metadata.security_scan_result.value,
                                "extracted_content": metadata.extracted_content,
                                "analysis_results": metadata.analysis_results,
                                "thumbnail_path": metadata.thumbnail_path,
                                "preview_available": metadata.preview_available,
                            }
                        )
                        db_file.metadata = db_meta
                        session.add(db_file)
                        await session.commit()
            except Exception as db_exc:  # pragma: no cover - optional DB
                logger.warning("Failed to update file metadata: %s", db_exc)
    
    async def _security_scan(self, file_path: Path) -> SecurityScanResult:
        """Perform security scan on uploaded file."""
        try:
            # Basic security checks
            file_size = file_path.stat().st_size
            
            # Check for suspicious file patterns
            with open(file_path, 'rb') as f:
                content = f.read(1024)  # Read first 1KB
                
                # Check for executable signatures
                executable_signatures = [
                    b'\x4d\x5a',  # PE executable
                    b'\x7f\x45\x4c\x46',  # ELF executable
                    b'\xfe\xed\xfa',  # Mach-O executable
                ]
                
                for signature in executable_signatures:
                    if content.startswith(signature):
                        return SecurityScanResult.SUSPICIOUS
                
                # Check for script patterns
                script_patterns = [
                    b'<script',
                    b'javascript:',
                    b'eval(',
                    b'exec(',
                ]
                
                for pattern in script_patterns:
                    if pattern in content.lower():
                        return SecurityScanResult.SUSPICIOUS
            
            return SecurityScanResult.SAFE
            
        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            return SecurityScanResult.SCAN_FAILED
    
    async def _extract_content(self, file_path: Path, file_type: FileType) -> Optional[str]:
        """Extract text content from file."""
        try:
            if file_type == FileType.DOCUMENT:
                return await self._extract_document_content(file_path)
            elif file_type == FileType.CODE:
                return await self._extract_code_content(file_path)
            elif file_type == FileType.IMAGE:
                return await self._extract_image_text(file_path)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Content extraction failed: {e}")
            return None
    
    async def _extract_document_content(self, file_path: Path) -> Optional[str]:
        """Extract content from document files."""
        try:
            extension = file_path.suffix.lower()
            
            if extension == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            elif extension == '.pdf':
                # PDF extraction would require PyPDF2 or similar
                # For now, return placeholder
                return f"[PDF Document: {file_path.name}]"
            
            elif extension in ['.doc', '.docx']:
                # Word document extraction would require python-docx
                return f"[Word Document: {file_path.name}]"
            
            elif extension == '.csv':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    return f"[CSV Data]\n{content[:1000]}..."  # First 1000 chars
            
            else:
                return f"[Document: {file_path.name}]"
                
        except Exception as e:
            logger.error(f"Document content extraction failed: {e}")
            return None
    
    async def _extract_code_content(self, file_path: Path) -> Optional[str]:
        """Extract content from code files."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Limit content size
                if len(content) > 10000:
                    content = content[:10000] + "\n... [Content truncated]"
                
                return content
                
        except Exception as e:
            logger.error(f"Code content extraction failed: {e}")
            return None
    
    async def _extract_image_text(self, file_path: Path) -> Optional[str]:
        """Extract text from images using OCR."""
        try:
            # OCR would require pytesseract or similar
            # For now, return image metadata
            from PIL import Image
            
            with Image.open(file_path) as img:
                return f"[Image: {img.format}, {img.size[0]}x{img.size[1]}]"
                
        except Exception as e:
            logger.error(f"Image text extraction failed: {e}")
            return f"[Image: {file_path.name}]"
    
    async def _analyze_image(self, file_path: Path) -> Dict[str, Any]:
        """Analyze image content and properties."""
        try:
            from PIL import Image
            
            analysis = {}
            
            with Image.open(file_path) as img:
                analysis.update({
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                })
                
                # Basic color analysis
                if img.mode == 'RGB':
                    # Get dominant colors (simplified)
                    colors = img.getcolors(maxcolors=256*256*256)
                    if colors:
                        dominant_color = max(colors, key=lambda x: x[0])[1]
                        analysis["dominant_color"] = dominant_color
            
            return analysis
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {"error": str(e)}
    
    async def _generate_thumbnail(self, file_path: Path, file_type: FileType) -> Optional[Path]:
        """Generate thumbnail for file."""
        try:
            if file_type == FileType.IMAGE:
                return await self._generate_image_thumbnail(file_path)
            elif file_type == FileType.VIDEO:
                return await self._generate_video_thumbnail(file_path)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return None
    
    async def _generate_image_thumbnail(self, file_path: Path) -> Optional[Path]:
        """Generate thumbnail for image file."""
        try:
            from PIL import Image
            
            thumbnail_path = self.storage_path / "thumbnails" / f"{file_path.stem}_thumb.jpg"
            
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Generate thumbnail
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, "JPEG", quality=85)
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Image thumbnail generation failed: {e}")
            return None
    
    async def _generate_video_thumbnail(self, file_path: Path) -> Optional[Path]:
        """Generate thumbnail for video file."""
        try:
            # Video thumbnail generation would require ffmpeg or similar
            # For now, return placeholder
            thumbnail_path = self.storage_path / "thumbnails" / f"{file_path.stem}_thumb.jpg"
            
            # Create a simple placeholder thumbnail
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.new('RGB', (200, 150), color='lightgray')
            draw = ImageDraw.Draw(img)
            
            try:
                # Try to use default font
                font = ImageFont.load_default()
            except:
                font = None
            
            text = "VIDEO"
            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width, text_height = 50, 20
            
            x = (200 - text_width) // 2
            y = (150 - text_height) // 2
            draw.text((x, y), text, fill='black', font=font)
            
            img.save(thumbnail_path, "JPEG")
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Video thumbnail generation failed: {e}")
            return None
    
    async def _quarantine_file(self, file_id: str, file_path: Path, reason: str) -> None:
        """Move file to quarantine."""
        try:
            quarantine_path = self.storage_path / "quarantine" / file_path.name
            file_path.rename(quarantine_path)

            # Update metadata
            if file_id in self._file_metadata:
                self._file_metadata[file_id].processing_status = ProcessingStatus.QUARANTINED
                self._file_metadata[file_id].analysis_results["quarantine_reason"] = reason

            try:
                async with get_postgres_session() as session:
                    db_file = await session.get(FileModel, file_id)
                    if db_file:
                        db_meta = db_file.metadata or {}
                        db_meta.update(
                            {
                                "processing_status": ProcessingStatus.QUARANTINED.value,
                                "analysis_results": {
                                    **db_meta.get("analysis_results", {}),
                                    "quarantine_reason": reason,
                                },
                            }
                        )
                        db_file.metadata = db_meta
                        session.add(db_file)
                        await session.commit()
            except Exception as db_exc:  # pragma: no cover - optional DB
                logger.warning("Failed to update quarantined file metadata: %s", db_exc)
            
            logger.warning(f"File {file_id} quarantined: {reason}")
            
        except Exception as e:
            logger.error(f"Failed to quarantine file {file_id}: {e}")
    
    async def get_file_info(self, file_id: str) -> Optional[FileProcessingResult]:
        """Get file processing information."""
        metadata = await self.get_metadata(file_id)
        if not metadata:
            return None

        return FileProcessingResult(
            file_id=file_id,
            processing_status=metadata.processing_status,
            extracted_content=metadata.extracted_content,
            analysis_results=metadata.analysis_results,
            thumbnail_url=f"/api/files/{file_id}/thumbnail" if metadata.thumbnail_path else None,
            preview_url=f"/api/files/{file_id}/preview" if metadata.preview_available else None,
            error_message=metadata.analysis_results.get("error")
        )

    async def get_file_content(self, file_id: str) -> Optional[bytes]:
        """Get file content by ID."""
        metadata = await self.get_metadata(file_id)
        if not metadata:
            return None

        file_path = self.storage_path / "files" / metadata.filename

        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_id}: {e}")
            return None

    async def get_thumbnail(self, file_id: str) -> Optional[bytes]:
        """Get file thumbnail by ID."""
        metadata = await self.get_metadata(file_id)
        if not metadata or not metadata.thumbnail_path:
            return None

        try:
            with open(metadata.thumbnail_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read thumbnail for {file_id}: {e}")
            return None

    async def delete_file(self, file_id: str) -> bool:
        """Delete file and associated data."""
        metadata = await self.get_metadata(file_id)
        if not metadata:
            return False

        try:
            # Delete main file
            file_path = self.storage_path / "files" / metadata.filename
            if file_path.exists():
                file_path.unlink()

            # Delete thumbnail
            if metadata.thumbnail_path:
                thumbnail_path = Path(metadata.thumbnail_path)
                if thumbnail_path.exists():
                    thumbnail_path.unlink()

            if file_id in self._file_metadata:
                del self._file_metadata[file_id]

            try:
                async with get_postgres_session() as session:
                    db_file = await session.get(FileModel, file_id)
                    if db_file:
                        await session.delete(db_file)
                        await session.commit()
            except Exception as db_exc:  # pragma: no cover - optional DB
                logger.warning("Failed to remove file %s from database: %s", file_id, db_exc)

            logger.info(f"File {file_id} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            files = await self.list_files()
            total_files = len(files)
            total_size = sum(metadata.file_size for metadata in files.values())

            files_by_type: Dict[str, int] = {}
            files_by_status: Dict[str, int] = {}

            for metadata in files.values():
                file_type = metadata.file_type.value
                files_by_type[file_type] = files_by_type.get(file_type, 0) + 1

                status = metadata.processing_status.value
                files_by_status[status] = files_by_status.get(status, 0) + 1

            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "files_by_type": files_by_type,
                "files_by_status": files_by_status,
                "storage_path": str(self.storage_path),
                "max_file_size_mb": round(self.max_file_size / (1024 * 1024), 2)
            }

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}