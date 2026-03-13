"""
File Upload Handler for Context Management

Handles multi-format file uploads with preprocessing, validation,
security scanning, and storage management.
"""

import hashlib
import logging
import mimetypes
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ai_karen_engine.context_management.models import (
    ContextFile,
    ContextFileType,
    ContextStatus,
)

logger = logging.getLogger(__name__)


class FileUploadHandler:
    """
    Comprehensive file upload handler with support for multiple file types,
    validation, security scanning, and preprocessing.
    """

    def __init__(
        self,
        storage_path: str = "/tmp/context_files",
        max_file_size_mb: int = 100,
        allowed_extensions: Optional[List[str]] = None,
        scan_for_malware: bool = True,
        extract_text: bool = True,
    ):
        """
        Initialize file upload handler.
        
        Args:
            storage_path: Base path for file storage
            max_file_size_mb: Maximum file size in MB
            allowed_extensions: List of allowed file extensions
            scan_for_malware: Whether to scan for malware
            extract_text: Whether to extract text content
        """
        self.storage_path = storage_path
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.scan_for_malware = scan_for_malware
        self.extract_text = extract_text
        
        # Default allowed extensions if not provided
        if allowed_extensions is None:
            self.allowed_extensions = [
                ext.value for ext in ContextFileType
            ]
        else:
            self.allowed_extensions = allowed_extensions
        
        # Ensure storage directory exists
        os.makedirs(storage_path, exist_ok=True)
        
        # Create subdirectories
        self.uploads_dir = os.path.join(storage_path, "uploads")
        self.processed_dir = os.path.join(storage_path, "processed")
        self.quarantine_dir = os.path.join(storage_path, "quarantine")
        
        for dir_path in [self.uploads_dir, self.processed_dir, self.quarantine_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        logger.info(f"FileUploadHandler initialized with storage path: {storage_path}")

    async def handle_upload(
        self,
        file_data: bytes,
        filename: str,
        context_id: str,
        user_id: str,
        mime_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[ContextFile], Optional[str]]:
        """
        Handle file upload with validation and processing.
        
        Args:
            file_data: Raw file data
            filename: Original filename
            context_id: Context ID to associate file with
            user_id: User ID uploading file
            mime_type: MIME type (detected if not provided)
            metadata: Additional metadata
            
        Returns:
            Tuple of (ContextFile, error_message)
        """
        try:
            # Validate file
            validation_result = await self._validate_file(file_data, filename, mime_type)
            if not validation_result[0]:
                return None, validation_result[1]
            
            # Detect file type
            file_type = self._detect_file_type(filename, mime_type)
            if not file_type:
                return None, "Unsupported file type"
            
            # Calculate checksum
            checksum = hashlib.sha256(file_data).hexdigest()
            
            # Check for duplicates
            existing_file = await self._find_duplicate_file(checksum, user_id)
            if existing_file:
                return existing_file, "File already exists"
            
            # Save file
            file_path, storage_path = await self._save_file(
                file_data, filename, checksum
            )
            
            # Create file record
            context_file = ContextFile(
                file_id=str(uuid.uuid4()),
                context_id=context_id,
                filename=filename,
                file_type=file_type,
                mime_type=mime_type or mimetypes.guess_type(filename)[0] or "application/octet-stream",
                size_bytes=len(file_data),
                storage_path=storage_path,
                checksum=checksum,
                metadata=metadata or {},
                status=ContextStatus.PROCESSING,
            )
            
            # Process file (extract text, metadata, etc.)
            if self.extract_text:
                await self._process_file(context_file, file_path)
            
            # Update status to active
            context_file.status = ContextStatus.ACTIVE
            context_file.processed_at = datetime.utcnow()
            
            logger.info(f"Successfully uploaded file {filename} for context {context_id}")
            return context_file, None
            
        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {e}")
            return None, str(e)

    async def get_file(
        self,
        file_id: str,
        user_id: str,
        check_access: bool = True,
    ) -> Optional[ContextFile]:
        """
        Retrieve file information by ID.
        
        Args:
            file_id: File ID to retrieve
            user_id: User ID requesting file
            check_access: Whether to check access permissions
            
        Returns:
            ContextFile if found and accessible, None otherwise
        """
        try:
            # In a real implementation, this would query the database
            # For now, we'll use a simple in-memory lookup
            # This would be replaced with actual database queries
            
            # This is a placeholder - in real implementation,
            # you would query your database for the file
            logger.warning("get_file() needs database implementation")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get file {file_id}: {e}")
            return None

    async def delete_file(
        self,
        file_id: str,
        user_id: str,
        permanent: bool = False,
    ) -> bool:
        """
        Delete a file (soft delete by default).
        
        Args:
            file_id: File ID to delete
            user_id: User ID requesting deletion
            permanent: Whether to permanently delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Get file information
            context_file = await self.get_file(file_id, user_id)
            if not context_file:
                return False
            
            if permanent:
                # Delete physical file
                if os.path.exists(context_file.storage_path):
                    os.remove(context_file.storage_path)
                
                # Delete from database (placeholder)
                logger.warning("delete_file() needs database implementation")
            else:
                # Soft delete
                context_file.status = ContextStatus.DELETED
                # Update in database (placeholder)
                logger.warning("delete_file() needs database implementation")
            
            logger.info(f"{'Permanently deleted' if permanent else 'Soft deleted'} file {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            return False

    async def _validate_file(
        self,
        file_data: bytes,
        filename: str,
        mime_type: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate file against security and size constraints.
        
        Args:
            file_data: Raw file data
            filename: Original filename
            mime_type: MIME type
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        if len(file_data) > self.max_file_size_bytes:
            return False, f"File too large. Maximum size is {self.max_file_size_bytes // (1024*1024)}MB"
        
        # Check if file is empty
        if len(file_data) == 0:
            return False, "File is empty"
        
        # Check file extension
        file_ext = Path(filename).suffix.lower().lstrip('.')
        if file_ext not in self.allowed_extensions:
            return False, f"File type '{file_ext}' not allowed"
        
        # Basic malware scan (simplified)
        if self.scan_for_malware:
            is_safe, error = await self._basic_malware_scan(file_data, filename)
            if not is_safe:
                return False, error
        
        return True, None

    def _detect_file_type(
        self,
        filename: str,
        mime_type: Optional[str] = None,
    ) -> Optional[ContextFileType]:
        """
        Detect file type from filename and MIME type.
        
        Args:
            filename: Original filename
            mime_type: MIME type
            
        Returns:
            Detected ContextFileType or None if unknown
        """
        # Get file extension
        file_ext = Path(filename).suffix.lower().lstrip('.')
        
        # Try to match by extension
        try:
            return ContextFileType(file_ext)
        except ValueError:
            pass
        
        # Try to match by MIME type
        if mime_type:
            mime_mapping = {
                "application/pdf": ContextFileType.PDF,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ContextFileType.DOCX,
                "text/plain": ContextFileType.TXT,
                "text/markdown": ContextFileType.MD,
                "application/json": ContextFileType.JSON,
                "text/csv": ContextFileType.CSV,
                "application/xml": ContextFileType.XML,
                "text/html": ContextFileType.HTML,
                "text/x-python": ContextFileType.PY,
                "application/javascript": ContextFileType.JS,
                "text/typescript": ContextFileType.TS,
                "text/x-java-source": ContextFileType.JAVA,
                "text/x-c++src": ContextFileType.CPP,
                "image/png": ContextFileType.PNG,
                "image/jpeg": ContextFileType.JPG,
                "image/gif": ContextFileType.GIF,
                "image/svg+xml": ContextFileType.SVG,
                "audio/mpeg": ContextFileType.MP3,
                "audio/wav": ContextFileType.WAV,
                "video/mp4": ContextFileType.MP4,
                "video/x-msvideo": ContextFileType.AVI,
                "video/quicktime": ContextFileType.MOV,
                "application/zip": ContextFileType.ZIP,
                "application/x-tar": ContextFileType.TAR,
                "application/gzip": ContextFileType.GZ,
            }
            
            return mime_mapping.get(mime_type)
        
        return None

    async def _save_file(
        self,
        file_data: bytes,
        filename: str,
        checksum: str,
    ) -> Tuple[str, str]:
        """
        Save file to storage with checksum-based path.
        
        Args:
            file_data: Raw file data
            filename: Original filename
            checksum: File checksum
            
        Returns:
            Tuple of (relative_path, full_path)
        """
        # Create checksum-based directory structure
        checksum_prefix = checksum[:2]
        checksum_dir = os.path.join(self.uploads_dir, checksum_prefix)
        os.makedirs(checksum_dir, exist_ok=True)
        
        # Create unique filename
        unique_filename = f"{checksum}_{filename}"
        file_path = os.path.join(checksum_dir, unique_filename)
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Return relative and full paths
        relative_path = os.path.join("uploads", checksum_prefix, unique_filename)
        full_path = os.path.abspath(file_path)
        
        return relative_path, full_path

    async def _process_file(self, context_file: ContextFile, file_path: str) -> None:
        """
        Process file to extract text and metadata.
        
        Args:
            context_file: ContextFile object to update
            file_path: Path to the file
        """
        try:
            # Extract text based on file type
            extracted_text = await self._extract_text_from_file(
                context_file.file_type, file_path
            )
            
            if extracted_text:
                context_file.extracted_text = extracted_text
            
            # Extract metadata based on file type
            extracted_metadata = await self._extract_metadata_from_file(
                context_file.file_type, file_path
            )
            
            if extracted_metadata:
                context_file.extracted_metadata.update(extracted_metadata)
            
        except Exception as e:
            logger.warning(f"Failed to process file {context_file.filename}: {e}")
            context_file.error_message = str(e)

    async def _extract_text_from_file(
        self,
        file_type: ContextFileType,
        file_path: str,
    ) -> Optional[str]:
        """
        Extract text content from file based on type.
        
        Args:
            file_type: Type of file
            file_path: Path to the file
            
        Returns:
            Extracted text or None if extraction failed
        """
        try:
            if file_type in [ContextFileType.TXT, ContextFileType.MD, ContextFileType.PY, 
                           ContextFileType.JS, ContextFileType.TS, ContextFileType.JAVA, 
                           ContextFileType.CPP, ContextFileType.HTML, ContextFileType.XML]:
                # Text files - read directly
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            
            elif file_type == ContextFileType.JSON:
                # JSON files - pretty print
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return json.dumps(data, indent=2)
            
            elif file_type == ContextFileType.CSV:
                # CSV files - read as text
                import csv
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    return '\n'.join([','.join(row) for row in rows])
            
            elif file_type == ContextFileType.PDF:
                # PDF files - extract text
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(file_path)
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    doc.close()
                    return text if text.strip() else None
                except ImportError:
                    logger.warning("PyMuPDF not installed for PDF text extraction")
                    return None
            
            elif file_type == ContextFileType.DOCX:
                # DOCX files - extract text
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text = ""
                    for paragraph in doc.paragraphs:
                        text += paragraph.text + "\n"
                    return text if text.strip() else None
                except ImportError:
                    logger.warning("python-docx not installed for DOCX text extraction")
                    return None
            
            # Image files - OCR (placeholder)
            elif file_type in [ContextFileType.PNG, ContextFileType.JPG, 
                              ContextFileType.JPEG, ContextFileType.GIF, ContextFileType.SVG]:
                # OCR would be implemented here
                logger.info(f"OCR extraction not implemented for {file_type}")
                return None
            
            # Audio/Video files - transcription (placeholder)
            elif file_type in [ContextFileType.MP3, ContextFileType.WAV, 
                              ContextFileType.MP4, ContextFileType.AVI, ContextFileType.MOV]:
                # Speech-to-text would be implemented here
                logger.info(f"Audio transcription not implemented for {file_type}")
                return None
            
            # Archive files - list contents (placeholder)
            elif file_type in [ContextFileType.ZIP, ContextFileType.TAR, ContextFileType.GZ]:
                # Archive listing would be implemented here
                logger.info(f"Archive listing not implemented for {file_type}")
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract text from {file_type}: {e}")
            return None

    async def _extract_metadata_from_file(
        self,
        file_type: ContextFileType,
        file_path: str,
    ) -> Dict[str, Any]:
        """
        Extract metadata from file based on type.
        
        Args:
            file_type: Type of file
            file_path: Path to the file
            
        Returns:
            Extracted metadata dictionary
        """
        metadata = {}
        
        try:
            # Basic file metadata
            stat = os.stat(file_path)
            metadata.update({
                "size_bytes": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            })
            
            # Type-specific metadata
            if file_type in [ContextFileType.PNG, ContextFileType.JPG, ContextFileType.JPEG]:
                # Image metadata
                try:
                    from PIL import Image
                    with Image.open(file_path) as img:
                        metadata.update({
                            "width": img.width,
                            "height": img.height,
                            "format": img.format,
                            "mode": img.mode,
                        })
                except ImportError:
                    logger.warning("PIL not installed for image metadata extraction")
            
            elif file_type in [ContextFileType.MP3, ContextFileType.WAV]:
                # Audio metadata
                try:
                    import mutagen
                    audio_file = mutagen.File(file_path)
                    if audio_file:
                        metadata.update({
                            "duration": getattr(audio_file.info, 'length', 0),
                            "bitrate": getattr(audio_file.info, 'bitrate', 0),
                            "sample_rate": getattr(audio_file.info, 'sample_rate', 0),
                        })
                except ImportError:
                    logger.warning("mutagen not installed for audio metadata extraction")
            
            elif file_type in [ContextFileType.MP4, ContextFileType.AVI, ContextFileType.MOV]:
                # Video metadata
                try:
                    import cv2
                    cap = cv2.VideoCapture(file_path)
                    if cap.isOpened():
                        metadata.update({
                            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                            "fps": cap.get(cv2.CAP_PROP_FPS),
                            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                        })
                        cap.release()
                except ImportError:
                    logger.warning("OpenCV not installed for video metadata extraction")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_type}: {e}")
            return {}

    async def _basic_malware_scan(
        self,
        file_data: bytes,
        filename: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Basic malware scan (placeholder implementation).
        
        Args:
            file_data: Raw file data
            filename: Original filename
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        # This is a very basic placeholder
        # In production, you would integrate with proper antivirus/antimalware solutions
        
        # Check for common executable signatures
        executable_signatures = [
            b'MZ',  # Windows PE
            b'\x7fELF',  # Linux ELF
            b'\xca\xfe\xba\xbe',  # Java class
            b'\xfe\xed\xfa\xce',  # Mach-O binary
        ]
        
        for signature in executable_signatures:
            if file_data.startswith(signature):
                return False, "Executable file detected"
        
        # Check for suspicious patterns
        suspicious_patterns = [
            b'eval(',
            b'exec(',
            b'system(',
            b'shell_exec(',
        ]
        
        for pattern in suspicious_patterns:
            if pattern in file_data:
                return False, "Suspicious code pattern detected"
        
        return True, None

    async def _find_duplicate_file(
        self,
        checksum: str,
        user_id: str,
    ) -> Optional[ContextFile]:
        """
        Find existing file by checksum.
        
        Args:
            checksum: File checksum
            user_id: User ID
            
        Returns:
            Existing ContextFile or None
        """
        # This would query the database for existing files
        # with the same checksum for the same user
        logger.warning("_find_duplicate_file() needs database implementation")
        return None

    def get_supported_file_types(self) -> List[Dict[str, str]]:
        """
        Get list of supported file types with descriptions.
        
        Returns:
            List of file type information
        """
        file_types = []
        
        for file_type in ContextFileType:
            file_types.append({
                "extension": file_type.value,
                "name": file_type.name,
                "description": self._get_file_type_description(file_type),
            })
        
        return file_types

    def _get_file_type_description(self, file_type: ContextFileType) -> str:
        """Get description for file type."""
        descriptions = {
            ContextFileType.PDF: "PDF Document",
            ContextFileType.DOCX: "Microsoft Word Document",
            ContextFileType.TXT: "Plain Text File",
            ContextFileType.MD: "Markdown Document",
            ContextFileType.JSON: "JSON Data File",
            ContextFileType.CSV: "CSV Data File",
            ContextFileType.XML: "XML Document",
            ContextFileType.HTML: "HTML Document",
            ContextFileType.PY: "Python Source Code",
            ContextFileType.JS: "JavaScript Source Code",
            ContextFileType.TS: "TypeScript Source Code",
            ContextFileType.JAVA: "Java Source Code",
            ContextFileType.CPP: "C++ Source Code",
            ContextFileType.PNG: "PNG Image",
            ContextFileType.JPG: "JPEG Image",
            ContextFileType.JPEG: "JPEG Image",
            ContextFileType.GIF: "GIF Image",
            ContextFileType.SVG: "SVG Vector Image",
            ContextFileType.MP3: "MP3 Audio",
            ContextFileType.WAV: "WAV Audio",
            ContextFileType.MP4: "MP4 Video",
            ContextFileType.AVI: "AVI Video",
            ContextFileType.MOV: "QuickTime Video",
            ContextFileType.ZIP: "ZIP Archive",
            ContextFileType.TAR: "TAR Archive",
            ContextFileType.GZ: "GZIP Archive",
        }
        
        return descriptions.get(file_type, "Unknown File Type")