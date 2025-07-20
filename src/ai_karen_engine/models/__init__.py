"""
AI Karen Engine Models Package.

This package contains all data models and type definitions used throughout
the AI Karen engine, including shared types for frontend-backend consistency.
"""

from .shared_types import (
    # Enums
    MessageRole,
    MemoryDepth,
    PersonalityTone,
    PersonalityVerbosity,
    TemperatureUnit,
    WeatherServiceOption,
    FlowType,
    ToolType,
    
    # Core Models
    AiData,
    ChatMessage,
    NotificationPreferences,
    KarenSettings,
    HandleUserMessageResult,
    
    # Flow Models
    FlowInput,
    FlowOutput,
    DecideActionInput,
    DecideActionOutput,
    KarenEnhancedInput,
    KarenEnhancedOutput,
    
    # Tool and Plugin Models
    ToolInput,
    MemoryContext,
    PluginInfo,
)

__all__ = [
    # Enums
    "MessageRole",
    "MemoryDepth", 
    "PersonalityTone",
    "PersonalityVerbosity",
    "TemperatureUnit",
    "WeatherServiceOption",
    "FlowType",
    "ToolType",
    
    # Core Models
    "AiData",
    "ChatMessage",
    "NotificationPreferences", 
    "KarenSettings",
    "HandleUserMessageResult",
    
    # Flow Models
    "FlowInput",
    "FlowOutput",
    "DecideActionInput",
    "DecideActionOutput",
    "KarenEnhancedInput",
    "KarenEnhancedOutput",
    
    # Tool and Plugin Models
    "ToolInput",
    "MemoryContext",
    "PluginInfo",
]