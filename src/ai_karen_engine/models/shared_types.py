"""
Shared type definitions for AI Karen Engine.

This module provides Python equivalents of TypeScript types used in the web UI,
ensuring type consistency across the entire system. These models use Pydantic
for runtime validation and serialization.
"""

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum
import uuid


class MessageRole(str, Enum):
    """Enum for message roles in conversations."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MemoryDepth(str, Enum):
    """Enum for memory depth settings."""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class PersonalityTone(str, Enum):
    """Enum for personality tone settings."""
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    HUMOROUS = "humorous"


class PersonalityVerbosity(str, Enum):
    """Enum for personality verbosity settings."""
    CONCISE = "concise"
    BALANCED = "balanced"
    DETAILED = "detailed"


class TemperatureUnit(str, Enum):
    """Enum for temperature unit preferences."""
    CELSIUS = "C"
    FAHRENHEIT = "F"


class WeatherServiceOption(str, Enum):
    """Enum for weather service options."""
    WTTR_IN = "wttr_in"
    OPENWEATHER = "openweather"
    CUSTOM_API = "custom_api"


class AiData(BaseModel):
    """AI-generated metadata and insights."""
    keywords: Optional[List[str]] = Field(None, description="Extracted keywords from the content")
    knowledge_graph_insights: Optional[str] = Field(None, description="Insights from the knowledge graph")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score for the AI response")
    reasoning: Optional[str] = Field(None, description="AI reasoning process explanation")


class ChatMessage(BaseModel):
    """Represents a single message in a conversation."""
    id: str = Field(description="Unique identifier for the message")
    role: MessageRole = Field(description="Role of the message sender")
    content: str = Field(description="Content of the message")
    timestamp: datetime = Field(description="When the message was created")
    ai_data: Optional[AiData] = Field(None, description="AI-generated metadata for the message")
    should_auto_play: Optional[bool] = Field(None, description="Whether the message should auto-play (for TTS)")


class NotificationPreferences(BaseModel):
    """User notification preferences."""
    enabled: bool = Field(True, description="Whether notifications are enabled")
    alert_on_new_insights: bool = Field(True, description="Alert when new insights are available")
    alert_on_summary_ready: bool = Field(True, description="Alert when conversation summary is ready")


class KarenSettings(BaseModel):
    """User settings for Karen AI behavior and preferences."""
    memory_depth: MemoryDepth = Field(MemoryDepth.MEDIUM, description="Preferred memory depth for context")
    personality_tone: PersonalityTone = Field(PersonalityTone.FRIENDLY, description="Preferred personality tone")
    personality_verbosity: PersonalityVerbosity = Field(PersonalityVerbosity.BALANCED, description="Preferred response verbosity")
    personal_facts: List[str] = Field(default_factory=list, description="Personal facts for Karen to remember")
    notifications: NotificationPreferences = Field(default_factory=NotificationPreferences, description="Notification preferences")
    tts_voice_uri: Optional[str] = Field(None, description="Text-to-speech voice URI")
    custom_persona_instructions: str = Field("", description="Custom instructions for AI persona")
    temperature_unit: TemperatureUnit = Field(TemperatureUnit.CELSIUS, description="Preferred temperature unit")
    weather_service: WeatherServiceOption = Field(WeatherServiceOption.WTTR_IN, description="Preferred weather service")
    weather_api_key: Optional[str] = Field(None, description="API key for weather service")
    default_weather_location: Optional[str] = Field(None, description="Default location for weather queries")
    active_listen_mode: bool = Field(False, description="Whether active listening mode is enabled")


class HandleUserMessageResult(BaseModel):
    """Result of processing a user message."""
    acknowledgement: Optional[str] = Field(None, description="Initial acknowledgement message")
    final_response: str = Field(description="Final response to the user")
    ai_data_for_final_response: Optional[AiData] = Field(None, description="AI metadata for the final response")
    suggested_new_facts: Optional[List[str]] = Field(None, description="New facts suggested for remembering")
    proactive_suggestion: Optional[str] = Field(None, description="Proactive suggestion for the user")
    summary_was_generated: Optional[bool] = Field(None, description="Whether a conversation summary was generated")


class FlowType(str, Enum):
    """Types of AI flows available."""
    DECIDE_ACTION = "decide_action"
    CONVERSATION_PROCESSING = "conversation_processing"
    CONVERSATION_SUMMARY = "conversation_summary"
    GENERATE_FINAL_RESPONSE = "generate_final_response"


class ToolType(str, Enum):
    """Available tool types."""
    GET_CURRENT_DATE = "getCurrentDate"
    GET_CURRENT_TIME = "getCurrentTime"
    GET_WEATHER = "getWeather"
    QUERY_BOOK_DATABASE = "queryBookDatabase"
    CHECK_GMAIL_UNREAD = "checkGmailUnread"
    COMPOSE_GMAIL = "composeGmail"
    NONE = "none"


class ToolInput(BaseModel):
    """Input parameters for tool execution."""
    location: Optional[str] = Field(None, description="Location for weather or time queries")
    book_title: Optional[str] = Field(None, description="Book title for database queries")
    gmail_recipient: Optional[str] = Field(None, description="Email recipient address")
    gmail_subject: Optional[str] = Field(None, description="Email subject line")
    gmail_body: Optional[str] = Field(None, description="Email body content")


class MemoryContext(BaseModel):
    """Memory context from AI Karen backend."""
    content: str = Field(description="Memory content")
    similarity_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Similarity score")
    tags: Optional[List[str]] = Field(None, description="Memory tags")
    timestamp: Optional[int] = Field(None, description="Unix timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PluginInfo(BaseModel):
    """Information about an available plugin."""
    name: str = Field(description="Plugin name")
    description: str = Field(description="Plugin description")
    category: str = Field(description="Plugin category")
    enabled: bool = Field(description="Whether the plugin is enabled")


class FlowInput(BaseModel):
    """Input for AI flow processing."""
    prompt: str = Field(description="User input prompt")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Recent conversation history")
    user_settings: Dict[str, Any] = Field(default_factory=dict, description="User settings and preferences")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context information")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    # Memory and context
    short_term_memory: Optional[str] = Field(None, description="Short-term memory as string")
    long_term_memory: Optional[str] = Field(None, description="Long-term memory as string")
    keywords: Optional[List[str]] = Field(None, description="Extracted keywords")
    knowledge_graph_insights: Optional[str] = Field(None, description="Knowledge graph insights")
    
    # User preferences
    memory_depth: Optional[MemoryDepth] = Field(None, description="Memory depth preference")
    personality_tone: Optional[PersonalityTone] = Field(None, description="Personality tone preference")
    personality_verbosity: Optional[PersonalityVerbosity] = Field(None, description="Verbosity preference")
    personal_facts: Optional[List[str]] = Field(None, description="Personal facts to remember")
    custom_persona_instructions: Optional[str] = Field(None, description="Custom persona instructions")
    
    # Backend context
    context_from_memory: Optional[List[MemoryContext]] = Field(None, description="Relevant memories from backend")
    available_plugins: Optional[List[PluginInfo]] = Field(None, description="Available plugins")


class FlowOutput(BaseModel):
    """Output from AI flow processing."""
    response: str = Field(description="Main response to the user")
    requires_plugin: bool = Field(False, description="Whether plugin execution is required")
    plugin_to_execute: Optional[str] = Field(None, description="Plugin name to execute")
    plugin_parameters: Optional[Dict[str, Any]] = Field(None, description="Parameters for plugin execution")
    memory_to_store: Optional[Dict[str, Any]] = Field(None, description="Memory data to store")
    suggested_actions: Optional[List[str]] = Field(None, description="Suggested actions for the user")
    ai_data: Optional[AiData] = Field(None, description="AI metadata for the response")
    proactive_suggestion: Optional[str] = Field(None, description="Proactive suggestion")
    
    # Tool-related outputs
    tool_to_call: Optional[ToolType] = Field(None, description="Tool to call")
    tool_input: Optional[ToolInput] = Field(None, description="Input for tool execution")
    
    # Additional metadata
    intermediate_response: Optional[str] = Field(None, description="Intermediate response before tool execution")
    suggested_new_facts: Optional[List[str]] = Field(None, description="New facts to remember")
    summary_was_generated: Optional[bool] = Field(None, description="Whether summary was generated")


class DecideActionInput(BaseModel):
    """Input for the decide action flow."""
    prompt: str = Field(description="User input prompt")
    short_term_memory: Optional[str] = Field(None, description="Short-term memory")
    long_term_memory: Optional[str] = Field(None, description="Long-term memory")
    keywords: Optional[List[str]] = Field(None, description="Extracted keywords")
    knowledge_graph_insights: Optional[str] = Field(None, description="Knowledge graph insights")
    memory_depth: Optional[MemoryDepth] = Field(None, description="Memory depth preference")
    personality_tone: Optional[PersonalityTone] = Field(None, description="Personality tone preference")
    personality_verbosity: Optional[PersonalityVerbosity] = Field(None, description="Verbosity preference")
    personal_facts: Optional[List[str]] = Field(None, description="Personal facts")
    custom_persona_instructions: Optional[str] = Field(None, description="Custom persona instructions")


class DecideActionOutput(BaseModel):
    """Output from the decide action flow."""
    intermediate_response: str = Field(description="Initial response or acknowledgement")
    tool_to_call: ToolType = Field(ToolType.NONE, description="Tool to call")
    tool_input: Optional[ToolInput] = Field(None, description="Tool input parameters")
    suggested_new_facts: Optional[List[str]] = Field(None, description="Suggested new facts")
    proactive_suggestion: Optional[str] = Field(None, description="Proactive suggestion")


class KarenEnhancedInput(BaseModel):
    """Enhanced input for Karen AI flows."""
    prompt: str = Field(description="User input prompt")
    conversation_history: Optional[str] = Field(None, description="Recent conversation history")
    user_id: Optional[str] = Field(None, description="User ID for personalization")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    settings: Optional[KarenSettings] = Field(None, description="User settings")
    context_from_memory: Optional[List[MemoryContext]] = Field(None, description="Relevant memories")
    available_plugins: Optional[List[PluginInfo]] = Field(None, description="Available plugins")


class KarenEnhancedOutput(BaseModel):
    """Enhanced output from Karen AI flows."""
    response: str = Field(description="Main response to the user")
    requires_plugin: bool = Field(False, description="Whether plugin execution is required")
    plugin_to_execute: Optional[str] = Field(None, description="Plugin to execute")
    plugin_parameters: Optional[Dict[str, Any]] = Field(None, description="Plugin parameters")
    memory_to_store: Optional[Dict[str, Any]] = Field(None, description="Memory to store")
    ai_data: Optional[AiData] = Field(None, description="AI metadata")
    proactive_suggestion: Optional[str] = Field(None, description="Proactive suggestion")
    suggested_new_facts: Optional[List[str]] = Field(None, description="Suggested new facts")