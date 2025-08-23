"""
Base Connector - Abstract base class for knowledge connectors

This module defines the base interface and common functionality
for all knowledge connectors in the ingestion pipeline.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json

try:
    from llama_index.core import Document
except ImportError:
    Document = None


class ConnectorType(Enum):
    """Types of knowledge connectors."""
    FILE = "file"
    GIT = "git"
    DATABASE = "database"
    DOCUMENTATION = "documentation"
    API = "api"
    LOG = "log"


class ChangeType(Enum):
    """Types of changes detected."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class ChangeDetection:
    """Represents a detected change in a source."""
    source_path: str
    change_type: ChangeType
    timestamp: datetime
    old_checksum: Optional[str] = None
    new_checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestionResult:
    """Result of an ingestion operation."""
    connector_type: ConnectorType
    source_id: str
    success: bool
    
    # Documents processed
    documents_created: int = 0
    documents_updated: int = 0
    documents_deleted: int = 0
    
    # Processing details
    processing_time_ms: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Change detection
    changes_detected: List[ChangeDetection] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "connector_type": self.connector_type.value,
            "source_id": self.source_id,
            "success": self.success,
            "documents_created": self.documents_created,
            "documents_updated": self.documents_updated,
            "documents_deleted": self.documents_deleted,
            "processing_time_ms": self.processing_time_ms,
            "errors": self.errors,
            "warnings": self.warnings,
            "changes_count": len(self.changes_detected),
            "metadata": self.metadata
        }


class BaseConnector(ABC):
    """
    Abstract base class for all knowledge connectors.
    Provides common functionality for change detection, incremental updates,
    and document processing.
    """
    
    def __init__(
        self,
        connector_id: str,
        connector_type: ConnectorType,
        config: Dict[str, Any]
    ):
        self.connector_id = connector_id
        self.connector_type = connector_type
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{connector_id}")
        
        # Change detection state
        self.last_scan_time: Optional[datetime] = None
        self.source_checksums: Dict[str, str] = {}
        self.source_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.incremental_updates = config.get("incremental_updates", True)
        self.change_detection_enabled = config.get("change_detection", True)
        self.batch_size = config.get("batch_size", 100)
        self.max_file_size = config.get("max_file_size", 10 * 1024 * 1024)  # 10MB
        
        # Filters and patterns
        self.include_patterns = config.get("include_patterns", [])
        self.exclude_patterns = config.get("exclude_patterns", [])
        self.file_extensions = config.get("file_extensions", [])
        
        # Processing state
        self.is_scanning = False
        self.last_error: Optional[str] = None
    
    @abstractmethod
    async def scan_sources(self) -> AsyncGenerator[Document, None]:
        """
        Scan sources and yield documents for ingestion.
        Must be implemented by concrete connectors.
        """
        pass
    
    @abstractmethod
    async def detect_changes(self) -> List[ChangeDetection]:
        """
        Detect changes since last scan.
        Must be implemented by concrete connectors.
        """
        pass
    
    @abstractmethod
    async def get_source_metadata(self, source_path: str) -> Dict[str, Any]:
        """
        Get metadata for a specific source.
        Must be implemented by concrete connectors.
        """
        pass
    
    async def ingest_incremental(self) -> IngestionResult:
        """
        Perform incremental ingestion based on detected changes.
        """
        start_time = datetime.utcnow()
        result = IngestionResult(
            connector_type=self.connector_type,
            source_id=self.connector_id,
            success=False
        )
        
        try:
            self.is_scanning = True
            
            # Detect changes if enabled
            if self.change_detection_enabled:
                changes = await self.detect_changes()
                result.changes_detected = changes
                
                if not changes:
                    result.success = True
                    result.metadata["message"] = "No changes detected"
                    return result
            
            # Process changes or full scan
            documents_processed = 0
            
            async for document in self.scan_sources():
                if document:
                    # Process document based on change type
                    await self._process_document(document, result)
                    documents_processed += 1
                    
                    # Batch processing
                    if documents_processed % self.batch_size == 0:
                        await asyncio.sleep(0.01)  # Yield control
            
            # Update scan time
            self.last_scan_time = datetime.utcnow()
            result.success = True
            
        except Exception as e:
            error_msg = f"Ingestion failed: {str(e)}"
            result.errors.append(error_msg)
            self.last_error = error_msg
            self.logger.error(error_msg)
        
        finally:
            self.is_scanning = False
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.processing_time_ms = int(processing_time)
        
        return result
    
    async def _process_document(self, document: Document, result: IngestionResult):
        """Process a single document and update result statistics."""
        try:
            # Extract source path from document metadata
            source_path = document.metadata.get("source_path", "unknown")
            
            # Calculate checksum for change detection
            content_checksum = self._calculate_checksum(document.text)
            old_checksum = self.source_checksums.get(source_path)
            
            if old_checksum is None:
                # New document
                result.documents_created += 1
                self.source_checksums[source_path] = content_checksum
            elif old_checksum != content_checksum:
                # Modified document
                result.documents_updated += 1
                self.source_checksums[source_path] = content_checksum
            
            # Store metadata
            self.source_metadata[source_path] = document.metadata
            
        except Exception as e:
            result.errors.append(f"Error processing document {source_path}: {str(e)}")
    
    def _calculate_checksum(self, content: str) -> str:
        """Calculate MD5 checksum of content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _matches_patterns(self, path: str) -> bool:
        """Check if path matches include/exclude patterns."""
        import fnmatch
        
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(path, pattern):
                return False
        
        # If no include patterns, include by default
        if not self.include_patterns:
            return True
        
        # Check include patterns
        for pattern in self.include_patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        
        return False
    
    def _matches_extensions(self, path: str) -> bool:
        """Check if file extension is in allowed list."""
        if not self.file_extensions:
            return True
        
        import os
        _, ext = os.path.splitext(path)
        return ext.lower() in [e.lower() for e in self.file_extensions]
    
    def _should_process_file(self, file_path: str, file_size: int = 0) -> bool:
        """Determine if file should be processed based on filters."""
        # Check file size
        if file_size > self.max_file_size:
            return False
        
        # Check patterns
        if not self._matches_patterns(file_path):
            return False
        
        # Check extensions
        if not self._matches_extensions(file_path):
            return False
        
        return True
    
    async def validate_configuration(self) -> List[str]:
        """Validate connector configuration and return any errors."""
        errors = []
        
        # Check required configuration
        if not self.connector_id:
            errors.append("Connector ID is required")
        
        # Check batch size
        if self.batch_size <= 0:
            errors.append("Batch size must be positive")
        
        # Check max file size
        if self.max_file_size <= 0:
            errors.append("Max file size must be positive")
        
        return errors
    
    async def get_connector_status(self) -> Dict[str, Any]:
        """Get current status of the connector."""
        return {
            "connector_id": self.connector_id,
            "connector_type": self.connector_type.value,
            "is_scanning": self.is_scanning,
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
            "sources_tracked": len(self.source_checksums),
            "last_error": self.last_error,
            "configuration": {
                "incremental_updates": self.incremental_updates,
                "change_detection_enabled": self.change_detection_enabled,
                "batch_size": self.batch_size,
                "max_file_size": self.max_file_size,
                "include_patterns": self.include_patterns,
                "exclude_patterns": self.exclude_patterns,
                "file_extensions": self.file_extensions
            }
        }
    
    async def reset_state(self):
        """Reset connector state (checksums, metadata, etc.)."""
        self.source_checksums.clear()
        self.source_metadata.clear()
        self.last_scan_time = None
        self.last_error = None
        self.logger.info(f"Reset state for connector {self.connector_id}")
    
    def _create_document(
        self,
        content: str,
        source_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Create a LlamaIndex document with proper metadata."""
        if not Document:
            # Fallback for when LlamaIndex is not available
            return type('Document', (), {
                'text': content,
                'metadata': metadata or {}
            })()
        
        doc_metadata = {
            "source_path": source_path,
            "connector_id": self.connector_id,
            "connector_type": self.connector_type.value,
            "ingestion_time": datetime.utcnow().isoformat(),
            "checksum": self._calculate_checksum(content)
        }
        
        if metadata:
            doc_metadata.update(metadata)
        
        return Document(
            text=content,
            metadata=doc_metadata
        )
    
    async def cleanup_deleted_sources(self, existing_sources: Set[str]) -> int:
        """Clean up tracking data for sources that no longer exist."""
        deleted_count = 0
        
        # Find sources that are tracked but no longer exist
        tracked_sources = set(self.source_checksums.keys())
        deleted_sources = tracked_sources - existing_sources
        
        for source_path in deleted_sources:
            if source_path in self.source_checksums:
                del self.source_checksums[source_path]
            if source_path in self.source_metadata:
                del self.source_metadata[source_path]
            deleted_count += 1
        
        if deleted_count > 0:
            self.logger.info(f"Cleaned up {deleted_count} deleted sources")
        
        return deleted_count