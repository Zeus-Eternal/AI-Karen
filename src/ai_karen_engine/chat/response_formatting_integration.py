"""
Response Formatting Integration Module

This module provides integration points for the response formatting system
with the existing chat runtime and agent systems in the CoPilot architecture.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class ResponseFormattingIntegration:
    """
    Integration layer for response formatting with chat and agent systems.
    
    This class provides methods to integrate the enhanced response formatting
    capabilities with the existing chat runtime, agent services, and other
    components of the CoPilot system.
    """
    
    def __init__(self):
        """Initialize the response formatting integration."""
        self.formatting_enabled = True
        self.default_profile = "pretty"
        self.cache_enabled = True
        self.performance_monitoring = True
        
        # Import formatting components
        try:
            from .enhanced_response_formatter import EnhancedResponseFormatter
            from .content_type_detector import ContentTypeDetector
            from .syntax_highlighter import SyntaxHighlighter
            from .responsive_formatter import ResponsiveFormatter
            from .response_formatting_models import (
                FormattingConfiguration, ResponseContext, OutputProfile,
                LayoutType, ContentType, DisplayContext, ThemeMode, AccessibilityLevel
            )
            
            self.formatter = EnhancedResponseFormatter()
            self.content_detector = ContentTypeDetector()
            self.syntax_highlighter = SyntaxHighlighter()
            self.responsive_formatter = ResponsiveFormatter()
            
            # Model classes
            self.FormattingConfiguration = FormattingConfiguration
            self.ResponseContext = ResponseContext
            self.OutputProfile = OutputProfile
            self.LayoutType = LayoutType
            self.ContentType = ContentType
            self.DisplayContext = DisplayContext
            self.ThemeMode = ThemeMode
            self.AccessibilityLevel = AccessibilityLevel
            
            logger.info("Response formatting integration initialized successfully")
            
        except ImportError as e:
            logger.warning(f"Could not import formatting components: {e}")
            self.formatter = None
            self.content_detector = None
            self.syntax_highlighter = None
            self.responsive_formatter = None
    
    def format_agent_response(
        self,
        content: str,
        agent_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[Dict[str, Any]] = None,
        formatting_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format an agent response using the enhanced response formatting system.
        
        This method integrates with the agent system to provide formatted responses
        with content type detection, syntax highlighting, responsive formatting,
        and user preference handling.
        
        Args:
            content: The raw agent response content
            agent_id: ID of the agent generating the response
            user_context: User context and preferences
            conversation_context: Conversation history and context
            formatting_preferences: Specific formatting preferences
            
        Returns:
            Dictionary containing formatted response and metadata
        """
        if not self.formatting_enabled or not self.formatter:
            return {
                "content": content,
                "formatted": False,
                "metadata": {"reason": "formatting_disabled_or_unavailable"}
            }
        
        try:
            logger.info(f"Formatting response for agent {agent_id or 'unknown'}")
            
            # Extract formatting preferences
            preferences = formatting_preferences or {}
            if user_context:
                preferences.update(user_context.get("formatting_preferences", {}))
            
            # Create response context
            response_context = self._create_response_context(
                content=content,
                agent_id=agent_id,
                user_context=user_context,
                conversation_context=conversation_context,
                preferences=preferences
            )
            
            # Create formatting configuration
            config = self._create_formatting_configuration(preferences)
            
            # Format the response
            formatted_result = self.formatter.format_response(
                content=content,
                config=config,
                context=response_context
            )
            
            # Add integration metadata
            formatted_result.metadata.update({
                "agent_id": agent_id,
                "integration_timestamp": datetime.utcnow().isoformat(),
                "formatting_version": "1.0.0"
            })
            
            logger.info(f"Agent response formatted successfully")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error formatting agent response: {e}")
            return {
                "content": content,
                "formatted": False,
                "metadata": {"error": str(e), "fallback": True}
            }
    
    def format_streaming_chunk(
        self,
        chunk: str,
        chunk_id: int,
        is_final: bool = False,
        formatting_context: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format a streaming chunk from an agent response.
        
        This method handles real-time formatting of streaming responses
        while maintaining consistency across chunks.
        
        Args:
            chunk: The content chunk to format
            chunk_id: Sequential ID of the chunk
            is_final: Whether this is the final chunk
            formatting_context: Context for formatting consistency
            agent_id: ID of the agent generating the response
            
        Returns:
            Dictionary containing formatted chunk and metadata
        """
        if not self.formatting_enabled or not self.formatter:
            return {
                "content": chunk,
                "chunk_id": chunk_id,
                "formatted": False,
                "metadata": {"reason": "formatting_disabled_or_unavailable"}
            }
        
        try:
            logger.debug(f"Formatting streaming chunk {chunk_id} for agent {agent_id or 'unknown'}")
            
            # Create streaming context
            context = formatting_context or {}
            context.update({
                "chunk_id": chunk_id,
                "is_final": is_final,
                "agent_id": agent_id
            })
            
            # Format the chunk
            formatted_chunk = self.formatter.format_streaming_chunk(
                content=chunk,
                chunk_id=chunk_id,
                is_final=is_final,
                context=context
            )
            
            logger.debug(f"Streaming chunk {chunk_id} formatted successfully")
            return formatted_chunk
            
        except Exception as e:
            logger.error(f"Error formatting streaming chunk {chunk_id}: {e}")
            return {
                "content": chunk,
                "chunk_id": chunk_id,
                "formatted": False,
                "metadata": {"error": str(e), "fallback": True}
            }
    
    def detect_content_type(
        self,
        content: str,
        context_hints: Optional[List[str]] = None,
        user_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect the content type of agent response content.
        
        This method provides content type detection for the agent system
        to enable appropriate handling and formatting.
        
        Args:
            content: The content to analyze
            context_hints: Hints about the content context
            user_query: The original user query for context
            
        Returns:
            Dictionary containing detected content type and metadata
        """
        if not self.content_detector:
            return {
                "detected_type": "text",
                "confidence": 0.5,
                "metadata": {"reason": "detector_unavailable"}
            }
        
        try:
            logger.debug("Detecting content type for agent response")
            
            # Detect content type
            detection_result = self.content_detector.detect_content_type(
                content=content,
                context_hints=context_hints or [],
                user_query=user_query
            )
            
            logger.debug(f"Content type detected: {detection_result.detected_type}")
            return detection_result
            
        except Exception as e:
            logger.error(f"Error detecting content type: {e}")
            return {
                "detected_type": "text",
                "confidence": 0.5,
                "metadata": {"error": str(e), "fallback": True}
            }
    
    def get_formatting_preferences(
        self,
        user_id: str,
        agent_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get formatting preferences for a user in a specific context.
        
        This method retrieves user formatting preferences, considering
        agent-specific and conversation-specific settings.
        
        Args:
            user_id: ID of the user
            agent_id: ID of the agent (for agent-specific preferences)
            conversation_id: ID of the conversation (for conversation-specific preferences)
            
        Returns:
            Dictionary containing formatting preferences
        """
        try:
            logger.debug(f"Getting formatting preferences for user {user_id}")
            
            # Default preferences
            preferences = {
                "output_profile": self.default_profile,
                "theme_mode": "auto",
                "accessibility_level": "basic",
                "enable_syntax_highlighting": True,
                "enable_responsive_formatting": True,
                "enable_interactive_elements": True,
                "language": "en"
            }
            
            # In a real implementation, this would fetch from user preferences database
            # For now, return default preferences
            
            logger.debug(f"Retrieved formatting preferences for user {user_id}")
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting formatting preferences: {e}")
            return {
                "output_profile": self.default_profile,
                "error": str(e)
            }
    
    def _create_response_context(
        self,
        content: str,
        agent_id: Optional[str],
        user_context: Optional[Dict[str, Any]],
        conversation_context: Optional[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> Any:
        """Create a response context object for formatting."""
        if not hasattr(self, 'ResponseContext'):
            return None
        
        try:
            # Detect display context
            display_context = self.DisplayContext.DESKTOP
            if user_context and "device_type" in user_context:
                device_type = user_context["device_type"].lower()
                if device_type == "mobile":
                    display_context = self.DisplayContext.MOBILE
                elif device_type == "tablet":
                    display_context = self.DisplayContext.TABLET
            
            # Detect theme mode
            theme_mode = self.ThemeMode.AUTO
            if preferences.get("theme_mode"):
                theme_str = preferences["theme_mode"].lower()
                if theme_str == "light":
                    theme_mode = self.ThemeMode.LIGHT
                elif theme_str == "dark":
                    theme_mode = self.ThemeMode.DARK
                elif theme_str == "high_contrast":
                    theme_mode = self.ThemeMode.HIGH_CONTRAST
            
            # Detect accessibility level
            accessibility_level = self.AccessibilityLevel.BASIC
            if preferences.get("accessibility_level"):
                access_str = preferences["accessibility_level"].lower()
                if access_str == "enhanced":
                    accessibility_level = self.AccessibilityLevel.ENHANCED
                elif access_str == "full":
                    accessibility_level = self.AccessibilityLevel.FULL
                elif access_str == "screen_reader":
                    accessibility_level = self.AccessibilityLevel.SCREEN_READER
            
            # Create response context
            return self.ResponseContext(
                user_id=user_context.get("user_id") if user_context else None,
                session_id=user_context.get("session_id") if user_context else None,
                conversation_id=conversation_context.get("conversation_id") if conversation_context else None,
                agent_id=agent_id,
                request_id=conversation_context.get("request_id") if conversation_context else None,
                timestamp=datetime.utcnow(),
                display_context=display_context,
                theme_mode=theme_mode,
                accessibility_level=accessibility_level,
                user_agent=user_context.get("user_agent") if user_context else None,
                screen_resolution=user_context.get("screen_resolution") if user_context else None,
                language=preferences.get("language", "en"),
                timezone=user_context.get("timezone") if user_context else None,
                custom_data=preferences.get("custom_data", {})
            )
            
        except Exception as e:
            logger.error(f"Error creating response context: {e}")
            return None
    
    def _create_formatting_configuration(self, preferences: Dict[str, Any]) -> Any:
        """Create a formatting configuration object."""
        if not hasattr(self, 'FormattingConfiguration'):
            return None
        
        try:
            # Get output profile
            output_profile = self.OutputProfile.PRETTY
            if preferences.get("output_profile"):
                profile_str = preferences["output_profile"].upper()
                try:
                    output_profile = self.OutputProfile[profile_str]
                except KeyError:
                    logger.warning(f"Unknown output profile: {profile_str}")
            
            # Get layout type
            layout_type = self.LayoutType.DEFAULT
            if preferences.get("layout_type"):
                layout_str = preferences["layout_type"].upper()
                try:
                    layout_type = self.LayoutType[layout_str]
                except KeyError:
                    logger.warning(f"Unknown layout type: {layout_str}")
            
            # Create formatting configuration
            return self.FormattingConfiguration(
                output_profile=output_profile,
                layout_type=layout_type,
                enable_syntax_highlighting=preferences.get("enable_syntax_highlighting", True),
                enable_responsive_formatting=preferences.get("enable_responsive_formatting", True),
                enable_interactive_elements=preferences.get("enable_interactive_elements", True),
                enable_accessibility_features=preferences.get("enable_accessibility_features", True),
                custom_css_classes=preferences.get("custom_css_classes", []),
                custom_attributes=preferences.get("custom_attributes", {}),
                cache_enabled=self.cache_enabled,
                performance_monitoring=self.performance_monitoring
            )
            
        except Exception as e:
            logger.error(f"Error creating formatting configuration: {e}")
            return None


# Global integration instance
_response_formatting_integration = None


def get_response_formatting_integration() -> ResponseFormattingIntegration:
    """Get the global response formatting integration instance."""
    global _response_formatting_integration
    if _response_formatting_integration is None:
        _response_formatting_integration = ResponseFormattingIntegration()
    return _response_formatting_integration


# Convenience functions for easy integration
def format_agent_response(
    content: str,
    agent_id: Optional[str] = None,
    user_context: Optional[Dict[str, Any]] = None,
    conversation_context: Optional[Dict[str, Any]] = None,
    formatting_preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Format an agent response using the enhanced response formatting system."""
    integration = get_response_formatting_integration()
    return integration.format_agent_response(
        content=content,
        agent_id=agent_id,
        user_context=user_context,
        conversation_context=conversation_context,
        formatting_preferences=formatting_preferences
    )


def format_streaming_chunk(
    chunk: str,
    chunk_id: int,
    is_final: bool = False,
    formatting_context: Optional[Dict[str, Any]] = None,
    agent_id: Optional[str] = None
) -> Dict[str, Any]:
    """Format a streaming chunk from an agent response."""
    integration = get_response_formatting_integration()
    return integration.format_streaming_chunk(
        chunk=chunk,
        chunk_id=chunk_id,
        is_final=is_final,
        formatting_context=formatting_context,
        agent_id=agent_id
    )


def detect_content_type(
    content: str,
    context_hints: Optional[List[str]] = None,
    user_query: Optional[str] = None
) -> Dict[str, Any]:
    """Detect the content type of agent response content."""
    integration = get_response_formatting_integration()
    return integration.detect_content_type(
        content=content,
        context_hints=context_hints,
        user_query=user_query
    )