"""
Production chat system for AI-Karen.

This module provides a comprehensive chat infrastructure with:
- Multi-LLM provider support (OpenAI, Anthropic, Gemini, Local)
- Real-time streaming capabilities
- Database persistence with PostgreSQL
- RESTful API endpoints
- WebSocket streaming support
- Provider fallback mechanisms
"""

from .models import (
    ChatConversation, ChatMessage, ChatProviderConfiguration,
    ChatSession, MessageAttachment
)

from .schemas import (
    # Base schemas
    BaseSchema, MessageMetadata, ConversationMetadata, ProviderConfig,
    SessionMetadata, AttachmentMetadata,
    
    # Request schemas
    CreateConversationRequest, SendMessageRequest, UpdateConversationRequest,
    ConfigureProviderRequest, StreamMessageRequest,
    
    # Response schemas
    MessageResponse, ConversationResponse, ProviderResponse,
    SessionResponse, AttachmentResponse, StreamChunkResponse,
    StreamResponse,
    
    # List and pagination schemas
    ConversationListResponse, MessageListResponse, ProviderListResponse,
    
    # Error and success schemas
    ErrorResponse, ValidationErrorResponse, SuccessResponse,
    
    # Health check schemas
    HealthCheckResponse,
    
    # Configuration schemas
    ChatSettings, UserPreferences,
    
    # Search and filtering schemas
    SearchRequest, SearchResponse,
    
    # Enums
    MessageRole, ProviderType, StreamingStatus
)

from .services import ChatService

from .providers import (
    BaseLLMProvider, OpenAIProvider, AnthropicProvider,
    GeminiProvider, LocalModelProvider,
    ProviderFeatures, ProviderStatus, ValidationResult,
    AIRequest, AIResponse, AIStreamChunk
)

__version__ = "1.0.0"
__all__ = [
    # Models
    "ChatConversation",
    "ChatMessage", 
    "ChatProviderConfiguration",
    "ChatSession",
    "MessageAttachment",
    
    # Schemas
    "BaseSchema",
    "MessageMetadata",
    "ConversationMetadata", 
    "ProviderConfig",
    "SessionMetadata",
    "AttachmentMetadata",
    "CreateConversationRequest",
    "SendMessageRequest",
    "UpdateConversationRequest",
    "ConfigureProviderRequest",
    "StreamMessageRequest",
    "MessageResponse",
    "ConversationResponse",
    "ProviderResponse",
    "SessionResponse",
    "AttachmentResponse",
    "StreamChunkResponse",
    "StreamResponse",
    "ConversationListResponse",
    "MessageListResponse",
    "ProviderListResponse",
    "ErrorResponse",
    "ValidationErrorResponse",
    "SuccessResponse",
    "HealthCheckResponse",
    "ChatSettings",
    "UserPreferences",
    "SearchRequest",
    "SearchResponse",
    "MessageRole",
    "ProviderType",
    "StreamingStatus",
    
    # Services
    "ChatService",
    
    # Providers
    "BaseLLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
    "LocalModelProvider",
    "FallbackManager",
    "ProviderFeatures",
    "ProviderStatus",
    "ValidationResult",
    "AIRequest",
    "AIResponse",
    "AIStreamChunk",
]