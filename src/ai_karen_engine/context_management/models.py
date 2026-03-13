"""
Context Management data models and types.

Defines the core data structures for context persistence, file uploads,
versioning, sharing, and access control.
"""

import enum
import hashlib
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import numpy as np


class ContextType(str, enum.Enum):
    """Types of context entries."""
    CONVERSATION = "conversation"
    DOCUMENT = "document"
    CODE = "code"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    WEB_PAGE = "web_page"
    NOTE = "note"
    TASK = "task"
    MEMORY = "memory"
    CUSTOM = "custom"


class ContextFileType(str, enum.Enum):
    """Supported file types for context uploads."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    HTML = "html"
    PY = "py"
    JS = "js"
    TS = "ts"
    JAVA = "java"
    CPP = "cpp"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    GIF = "gif"
    SVG = "svg"
    MP3 = "mp3"
    WAV = "wav"
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    ZIP = "zip"
    TAR = "tar"
    GZ = "gz"


class ContextAccessLevel(str, enum.Enum):
    """Access levels for context entries."""
    PRIVATE = "private"      # Only owner can access
    SHARED = "shared"        # Owner and specified users can access
    TEAM = "team"           # All team members can access
    ORGANIZATION = "organization"  # All organization members can access
    PUBLIC = "public"       # Anyone can access


class ContextStatus(str, enum.Enum):
    """Status of context entries."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    PROCESSING = "processing"
    ERROR = "error"


@dataclass
class ContextFile:
    """Represents a file uploaded as context."""
    file_id: str
    context_id: str
    filename: str
    file_type: ContextFileType
    mime_type: str
    size_bytes: int
    storage_path: str
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_text: Optional[str] = None
    extracted_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    status: ContextStatus = ContextStatus.PROCESSING
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if not self.file_id:
            self.file_id = str(uuid.uuid4())
    
    @property
    def is_processed(self) -> bool:
        """Check if file has been processed."""
        return self.status in [ContextStatus.ACTIVE, ContextStatus.ARCHIVED]
    
    @property
    def processing_duration(self) -> Optional[timedelta]:
        """Get processing duration if processed."""
        if self.processed_at and self.created_at:
            return self.processed_at - self.created_at
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "file_id": self.file_id,
            "context_id": self.context_id,
            "filename": self.filename,
            "file_type": self.file_type.value,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "storage_path": self.storage_path,
            "checksum": self.checksum,
            "metadata": self.metadata,
            "extracted_text": self.extracted_text,
            "extracted_metadata": self.extracted_metadata,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "status": self.status.value,
            "error_message": self.error_message,
            "is_processed": self.is_processed,
            "processing_duration_seconds": self.processing_duration.total_seconds() if self.processing_duration else None,
        }


@dataclass
class ContextEntry:
    """Main context entry with full metadata and content."""
    id: str
    user_id: str
    org_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    title: str = ""
    content: str = ""
    context_type: ContextType = ContextType.CUSTOM
    access_level: ContextAccessLevel = ContextAccessLevel.PRIVATE
    status: ContextStatus = ContextStatus.ACTIVE
    
    # Content analysis
    embedding: Optional[np.ndarray] = None
    summary: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Relevance and scoring
    relevance_score: float = 0.0
    importance_score: float = 5.0  # 1-10 scale
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    # Versioning and history
    version: int = 1
    parent_context_id: Optional[str] = None
    child_context_ids: List[str] = field(default_factory=list)
    
    # Metadata and timestamps
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # File associations
    file_ids: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize default values."""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        # Set default expiration if not provided (30 days)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(days=30)
    
    @property
    def is_expired(self) -> bool:
        """Check if context has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_active(self) -> bool:
        """Check if context is active."""
        return self.status == ContextStatus.ACTIVE and not self.is_expired
    
    @property
    def age_days(self) -> float:
        """Get age in days."""
        return (datetime.utcnow() - self.created_at).total_seconds() / 86400
    
    def increment_access(self) -> None:
        """Increment access count and update last accessed."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_content(self, new_content: str, create_version: bool = True) -> 'ContextEntry':
        """Update content and optionally create new version."""
        if create_version:
            # Create new version
            new_context = ContextEntry(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                org_id=self.org_id,
                session_id=self.session_id,
                conversation_id=self.conversation_id,
                title=self.title,
                content=new_content,
                context_type=self.context_type,
                access_level=self.access_level,
                status=self.status,
                importance_score=self.importance_score,
                metadata=self.metadata.copy(),
                tags=self.tags.copy(),
                file_ids=self.file_ids.copy(),
                version=self.version + 1,
                parent_context_id=self.id,
            )
            
            # Update this entry's children
            self.child_context_ids.append(new_context.id)
            self.updated_at = datetime.utcnow()
            
            return new_context
        else:
            # Update in place
            self.content = new_content
            self.updated_at = datetime.utcnow()
            return self
    
    def add_tag(self, tag: str) -> None:
        """Add a tag if not already present."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag if present."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_embedding: bool = False) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "org_id": self.org_id,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "title": self.title,
            "content": self.content,
            "context_type": self.context_type.value,
            "access_level": self.access_level.value,
            "status": self.status.value,
            "summary": self.summary,
            "keywords": self.keywords,
            "entities": self.entities,
            "relevance_score": self.relevance_score,
            "importance_score": self.importance_score,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "version": self.version,
            "parent_context_id": self.parent_context_id,
            "child_context_ids": self.child_context_ids,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "file_ids": self.file_ids,
            "is_expired": self.is_expired,
            "is_active": self.is_active,
            "age_days": self.age_days,
        }
        
        if include_embedding and self.embedding is not None:
            result["embedding"] = self.embedding.tolist()
        
        return result


@dataclass
class ContextQuery:
    """Query parameters for context search and retrieval."""
    query_text: str = ""
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    
    # Filters
    context_types: List[ContextType] = field(default_factory=list)
    access_levels: List[ContextAccessLevel] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    status: List[ContextStatus] = field(default_factory=list)
    
    # Time-based filters
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    
    # Search parameters
    top_k: int = 10
    similarity_threshold: float = 0.7
    include_content: bool = True
    include_files: bool = False
    include_embedding: bool = False
    
    # Sorting
    sort_by: str = "relevance"  # relevance, created_at, updated_at, access_count, importance
    sort_order: str = "desc"   # asc, desc
    
    # Metadata filters
    metadata_filter: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query_text": self.query_text,
            "user_id": self.user_id,
            "org_id": self.org_id,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "context_types": [ct.value for ct in self.context_types],
            "access_levels": [al.value for al in self.access_levels],
            "tags": self.tags,
            "keywords": self.keywords,
            "status": [s.value for s in self.status],
            "created_after": self.created_after.isoformat() if self.created_after else None,
            "created_before": self.created_before.isoformat() if self.created_before else None,
            "updated_after": self.updated_after.isoformat() if self.updated_after else None,
            "updated_before": self.updated_before.isoformat() if self.updated_before else None,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "include_content": self.include_content,
            "include_files": self.include_files,
            "include_embedding": self.include_embedding,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "metadata_filter": self.metadata_filter,
        }


@dataclass
class ContextSearchResult:
    """Result from context search with scoring information."""
    context: ContextEntry
    similarity_score: float
    relevance_score: float
    match_highlights: List[str] = field(default_factory=list)
    explanation: Optional[str] = None
    
    def to_dict(self, include_embedding: bool = False) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "context": self.context.to_dict(include_embedding=include_embedding),
            "similarity_score": self.similarity_score,
            "relevance_score": self.relevance_score,
            "match_highlights": self.match_highlights,
            "explanation": self.explanation,
        }


@dataclass
class ContextVersion:
    """Version information for context entries."""
    version_id: str
    context_id: str
    version_number: int
    content: str
    title: str
    created_by: str
    change_summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "version_id": self.version_id,
            "context_id": self.context_id,
            "version_number": self.version_number,
            "content": self.content,
            "title": self.title,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "change_summary": self.change_summary,
        }


@dataclass
class ContextShare:
    """Sharing configuration for context entries."""
    share_id: str
    context_id: str
    shared_by: str
    shared_with: Optional[str] = None  # None means public/team/org
    access_level: ContextAccessLevel = ContextAccessLevel.SHARED
    permissions: List[str] = field(default_factory=list)  # read, write, share, delete
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    
    def __post_init__(self):
        """Initialize default values."""
        if not self.share_id:
            self.share_id = str(uuid.uuid4())
    
    @property
    def is_expired(self) -> bool:
        """Check if share has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_active(self) -> bool:
        """Check if share is active."""
        return not self.is_expired
    
    def increment_access(self) -> None:
        """Increment access count and update last accessed."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "share_id": self.share_id,
            "context_id": self.context_id,
            "shared_by": self.shared_by,
            "shared_with": self.shared_with,
            "access_level": self.access_level.value,
            "permissions": self.permissions,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count,
            "is_expired": self.is_expired,
            "is_active": self.is_active,
        }


@dataclass
class ContextAccessLog:
    """Access log entry for context entries."""
    log_id: str
    context_id: str
    user_id: str
    action: str  # read, write, share, delete, search
    access_level: ContextAccessLevel
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Initialize default values."""
        if not self.log_id:
            self.log_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "log_id": self.log_id,
            "context_id": self.context_id,
            "user_id": self.user_id,
            "action": self.action,
            "access_level": self.access_level.value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "error_message": self.error_message,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }