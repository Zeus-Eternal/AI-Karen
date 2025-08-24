"""
Enhanced data models for production-ready conversation management.
Supports advanced features like branching, templates, folders, and search.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import uuid


class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"


class MessageType(str, Enum):
    """Message types for different content."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    CODE = "code"
    SYSTEM = "system"
    TEMPLATE = "template"


class ConversationStatus(str, Enum):
    """Conversation status states."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    TEMPLATE = "template"


class ChatMessage(BaseModel):
    """Enhanced chat message model with branching support."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    role: MessageRole
    content: str
    message_type: MessageType = MessageType.TEXT
    metadata: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    parent_message_id: Optional[str] = None  # For branching
    embedding: Optional[List[float]] = None
    
    # Advanced features
    edit_history: List[Dict[str, Any]] = Field(default_factory=list)
    reactions: Dict[str, int] = Field(default_factory=dict)  # emoji -> count
    is_pinned: bool = False
    confidence_score: Optional[float] = None
    processing_time_ms: Optional[int] = None


class ConversationSettings(BaseModel):
    """Conversation-specific settings."""
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    system_prompt: Optional[str] = None
    memory_enabled: bool = True
    streaming_enabled: bool = True
    auto_title: bool = True
    auto_summarize: bool = True
    context_window_size: int = 20
    enable_branching: bool = True
    enable_search: bool = True


class ConversationFolder(BaseModel):
    """Folder for organizing conversations."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: Optional[str] = None
    parent_folder_id: Optional[str] = None  # For nested folders
    color: Optional[str] = None
    icon: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationTemplate(BaseModel):
    """Template for creating conversations with predefined structure."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # None for system templates
    name: str
    description: Optional[str] = None
    category: str = "general"
    initial_messages: List[ChatMessage] = Field(default_factory=list)
    default_settings: ConversationSettings = Field(default_factory=ConversationSettings)
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False
    usage_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Conversation(BaseModel):
    """Enhanced conversation model with advanced features."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: Optional[str] = None
    status: ConversationStatus = ConversationStatus.ACTIVE
    
    # Organization
    folder_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_favorite: bool = False
    priority: int = 0  # 0=normal, 1=high, -1=low
    
    # Content
    message_count: int = 0
    last_message_at: Optional[datetime] = None
    summary: Optional[str] = None
    
    # Branching
    parent_conversation_id: Optional[str] = None  # For branches
    branch_point_message_id: Optional[str] = None
    child_branches: List[str] = Field(default_factory=list)
    
    # Template
    template_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    
    # Settings and metadata
    settings: ConversationSettings = Field(default_factory=ConversationSettings)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Analytics
    view_count: int = 0
    share_count: int = 0
    export_count: int = 0


class ConversationFilters(BaseModel):
    """Filters for conversation search and listing."""
    # Date filters
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    last_accessed_from: Optional[datetime] = None
    last_accessed_to: Optional[datetime] = None
    
    # Organization filters
    folder_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None
    status: Optional[ConversationStatus] = None
    priority: Optional[int] = None
    
    # Content filters
    has_attachments: Optional[bool] = None
    min_messages: Optional[int] = None
    max_messages: Optional[int] = None
    message_types: Optional[List[MessageType]] = None
    
    # Template filters
    template_id: Optional[str] = None
    created_from_template: Optional[bool] = None
    
    # Branching filters
    is_branch: Optional[bool] = None
    has_branches: Optional[bool] = None
    parent_conversation_id: Optional[str] = None


class ConversationSearchResult(BaseModel):
    """Search result for conversation queries."""
    conversation: Conversation
    relevance_score: float
    matched_messages: List[ChatMessage] = Field(default_factory=list)
    highlight_snippets: List[str] = Field(default_factory=list)
    search_metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationExportOptions(BaseModel):
    """Options for conversation export."""
    format: str = "json"  # json, markdown, pdf, html, csv
    include_metadata: bool = True
    include_attachments: bool = False
    include_system_messages: bool = False
    date_format: str = "iso"
    compress: bool = False
    encrypt: bool = False
    password: Optional[str] = None
    custom_template: Optional[str] = None


class ConversationImportOptions(BaseModel):
    """Options for conversation import."""
    source_format: str = "json"
    merge_strategy: str = "create_new"  # create_new, merge_existing, replace
    preserve_ids: bool = False
    validate_content: bool = True
    auto_detect_format: bool = True
    default_folder_id: Optional[str] = None
    default_tags: List[str] = Field(default_factory=list)


class ConversationBranch(BaseModel):
    """Information about a conversation branch."""
    id: str
    title: str
    branch_point_message_id: str
    created_at: datetime
    message_count: int
    last_message_at: Optional[datetime] = None
    is_active: bool = True


class ConversationStats(BaseModel):
    """Statistics for conversations."""
    total_conversations: int = 0
    active_conversations: int = 0
    archived_conversations: int = 0
    favorite_conversations: int = 0
    total_messages: int = 0
    avg_messages_per_conversation: float = 0.0
    conversations_by_folder: Dict[str, int] = Field(default_factory=dict)
    conversations_by_tag: Dict[str, int] = Field(default_factory=dict)
    conversations_by_template: Dict[str, int] = Field(default_factory=dict)
    recent_activity: Dict[str, int] = Field(default_factory=dict)  # date -> count


class QuickAction(BaseModel):
    """Quick action for conversations."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    action_type: str  # template, prompt, function
    action_data: Dict[str, Any] = Field(default_factory=dict)
    is_system: bool = False
    usage_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)