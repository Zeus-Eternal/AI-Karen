"""
Integration layer for Pretty Output Layer with existing response formatting systems.

This module provides integration between the new Pretty Output Layer and the
existing extensions response formatting system, allowing them to work together
seamlessly.
"""

import logging
from typing import Dict, Any, Optional, List

from .response_formatter import (
    PrettyOutputLayer,
    OutputProfile,
    LayoutType,
    ResponseContext as PrettyResponseContext,
    FormattingConfig
)

# Try to import from extensions response formatting system
try:
    from extensions.response_formatting.base import (
        ResponseContext as ExtensionResponseContext,
        FormattedResponse,
        ContentType,
        ResponseFormatter
    )
    from extensions.response_formatting.registry import get_formatter_registry
    from extensions.response_formatting.integration import get_response_formatting_integration
    EXTENSIONS_AVAILABLE = True
except ImportError:
    EXTENSIONS_AVAILABLE = False
    # Create placeholder classes if extensions are not available
    class ContentType:
        DEFAULT = "default"
    
    class FormattedResponse:
        def __init__(self, content: str, **kwargs):
            self.content = content
            self.metadata = kwargs.get("metadata", {})
    
    class ExtensionResponseContext:
        def __init__(self, user_query: str, response_content: str, **kwargs):
            self.user_query = user_query
            self.response_content = response_content
            self.detected_content_type = kwargs.get("detected_content_type", None)
            self.confidence_score = kwargs.get("confidence_score", 0.0)

logger = logging.getLogger(__name__)


class ResponseFormatterAdapter:
    """
    Adapter class that integrates Pretty Output Layer with extensions response formatting.
    
    This class provides a unified interface that can use either the new
    Pretty Output Layer or the existing extensions response formatting system
    depending on availability and configuration.
    """
    
    def __init__(
        self,
        use_extensions: bool = True,
        pretty_config: Optional[FormattingConfig] = None
    ):
        """
        Initialize the response formatter adapter.
        
        Args:
            use_extensions: Whether to use extensions formatting system if available
            pretty_config: Configuration for the Pretty Output Layer
        """
        self.use_extensions = use_extensions and EXTENSIONS_AVAILABLE
        self.pretty_output_layer = PrettyOutputLayer(pretty_config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        if self.use_extensions:
            try:
                self.extensions_integration = get_response_formatting_integration()  # type: ignore
                self.formatter_registry = get_formatter_registry()  # type: ignore
                self.logger.info("Using extensions response formatting system")
            except Exception as e:
                self.logger.warning(f"Failed to initialize extensions integration: {e}")
                self.use_extensions = False
        
        if not self.use_extensions:
            self.logger.info("Using Pretty Output Layer for response formatting")
    
    async def format_response(
        self,
        user_query: str,
        response_content: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        theme_context: Optional[Dict[str, Any]] = None,
        session_data: Optional[Dict[str, Any]] = None,
        output_profile: Optional[OutputProfile] = None,
        force_layout: Optional[LayoutType] = None
    ) -> Dict[str, Any]:
        """
        Format a response using the appropriate formatting system.
        
        Args:
            user_query: The original user query
            response_content: The AI response content to format
            user_preferences: User formatting preferences
            theme_context: Current theme context
            session_data: Session-specific data
            output_profile: Output profile to use (overrides default)
            force_layout: Layout type to force (overrides detection)
            
        Returns:
            Dictionary containing formatted response and metadata
        """
        if self.use_extensions:
            try:
                return await self._format_with_extensions(
                    user_query=user_query,
                    response_content=response_content,
                    user_preferences=user_preferences,
                    theme_context=theme_context,
                    session_data=session_data,
                    output_profile=output_profile,
                    force_layout=force_layout
                )
            except Exception as e:
                self.logger.error(f"Extensions formatting failed: {e}")
                # Fall back to Pretty Output Layer
                self.use_extensions = False
        
        # Use Pretty Output Layer
        return self._format_with_pretty_output(
            user_query=user_query,
            response_content=response_content,
            user_preferences=user_preferences,
            theme_context=theme_context,
            session_data=session_data,
            output_profile=output_profile,
            force_layout=force_layout
        )
    
    async def _format_with_extensions(
        self,
        user_query: str,
        response_content: str,
        user_preferences: Optional[Dict[str, Any]],
        theme_context: Optional[Dict[str, Any]],
        session_data: Optional[Dict[str, Any]],
        output_profile: Optional[OutputProfile],
        force_layout: Optional[LayoutType]
    ) -> Dict[str, Any]:
        """
        Format response using extensions response formatting system.
        
        Args:
            user_query: The original user query
            response_content: The AI response content to format
            user_preferences: User formatting preferences
            theme_context: Current theme context
            session_data: Session-specific data
            output_profile: Output profile to use
            force_layout: Layout type to force
            
        Returns:
            Dictionary containing formatted response and metadata
        """
        # First, try to detect content type using extensions system
        try:
            detection_result = await self.extensions_integration.detect_content_type(
                user_query, response_content
            )
            
            # Create context for extensions system
            ext_context = ExtensionResponseContext(
                user_query=user_query,
                response_content=response_content,
                user_preferences=user_preferences or {},
                theme_context=theme_context or {},
                session_data=session_data or {},
                detected_content_type=detection_result.content_type,
                confidence_score=detection_result.confidence
            )
            
            # Format using extensions system
            formatted_response = await self.extensions_integration.format_response(
                user_query=user_query,
                response_content=response_content,
                user_preferences=user_preferences,
                theme_context=theme_context,
                session_data=session_data
            )
            
            # Apply Pretty Output Layer enhancements if specified
            if output_profile or force_layout:
                pretty_context = PrettyResponseContext(
                    user_query=user_query,
                    response_content=formatted_response.content,
                    user_preferences=user_preferences or {},
                    theme_context=theme_context or {},
                    session_data=session_data or {},
                    detected_content_type=detection_result.content_type.value if detection_result.content_type else None,
                    confidence_score=detection_result.confidence
                )
                
                # Set output profile if specified
                if output_profile:
                    self.pretty_output_layer.set_output_profile(output_profile)
                
                # Force layout if specified
                if force_layout:
                    self.pretty_output_layer.force_layout_type(force_layout)
                
                # Apply Pretty Output Layer formatting
                pretty_result = self.pretty_output_layer.format_response(
                    pretty_context.response_content, pretty_context
                )
                
                # Merge metadata
                merged_metadata = {
                    **formatted_response.metadata,
                    **pretty_result["metadata"],
                    "extensions_used": True,
                    "pretty_output_enhancements": True
                }
                
                return {
                    "content": pretty_result["content"],
                    "content_type": detection_result.content_type.value if detection_result.content_type else "default",
                    "layout_type": pretty_result["layout_type"],
                    "output_profile": pretty_result["output_profile"],
                    "metadata": merged_metadata,
                    "theme_requirements": getattr(formatted_response, 'theme_requirements', []),
                    "css_classes": getattr(formatted_response, 'css_classes', []),
                    "has_images": getattr(formatted_response, 'has_images', False),
                    "has_interactive_elements": getattr(formatted_response, 'has_interactive_elements', False)
                }
            
            # Return extensions formatting result as-is
            return {
                "content": formatted_response.content,
                "content_type": detection_result.content_type.value if detection_result.content_type else "default",
                "layout_type": "default",
                "output_profile": "extensions",
                "metadata": {
                    **formatted_response.metadata,
                    "extensions_used": True,
                    "pretty_output_enhancements": False
                },
                "theme_requirements": getattr(formatted_response, 'theme_requirements', []),
                "css_classes": getattr(formatted_response, 'css_classes', []),
                "has_images": getattr(formatted_response, 'has_images', False),
                "has_interactive_elements": getattr(formatted_response, 'has_interactive_elements', False)
            }
            
        except Exception as e:
            self.logger.error(f"Extensions formatting failed: {e}")
            raise
    
    def _format_with_pretty_output(
        self,
        user_query: str,
        response_content: str,
        user_preferences: Optional[Dict[str, Any]],
        theme_context: Optional[Dict[str, Any]],
        session_data: Optional[Dict[str, Any]],
        output_profile: Optional[OutputProfile],
        force_layout: Optional[LayoutType]
    ) -> Dict[str, Any]:
        """
        Format response using Pretty Output Layer.
        
        Args:
            user_query: The original user query
            response_content: The AI response content to format
            user_preferences: User formatting preferences
            theme_context: Current theme context
            session_data: Session-specific data
            output_profile: Output profile to use
            force_layout: Layout type to force
            
        Returns:
            Dictionary containing formatted response and metadata
        """
        # Create context for Pretty Output Layer
        context = PrettyResponseContext(
            user_query=user_query,
            response_content=response_content,
            user_preferences=user_preferences or {},
            theme_context=theme_context or {},
            session_data=session_data or {}
        )
        
        # Set output profile if specified
        if output_profile:
            self.pretty_output_layer.set_output_profile(output_profile)
        
        # Force layout if specified
        if force_layout:
            self.pretty_output_layer.force_layout_type(force_layout)
        
        # Format using Pretty Output Layer
        result = self.pretty_output_layer.format_response(
            context.response_content, context
        )
        
        # Add metadata to indicate Pretty Output Layer was used
        result["metadata"]["extensions_used"] = False
        result["metadata"]["pretty_output_enhancements"] = True
        
        return result
    
    def set_output_profile(self, profile: OutputProfile) -> None:
        """
        Set the output profile for formatting.
        
        Args:
            profile: The output profile to use
        """
        self.pretty_output_layer.set_output_profile(profile)
    
    def get_output_profile(self) -> OutputProfile:
        """
        Get the current output profile.
        
        Returns:
            The current output profile
        """
        return self.pretty_output_layer.get_output_profile()
    
    def force_layout_type(self, layout_type: LayoutType) -> None:
        """
        Force the use of a specific layout type.
        
        Args:
            layout_type: The layout type to force
        """
        self.pretty_output_layer.force_layout_type(layout_type)
    
    def reset_layout_detection(self) -> None:
        """
        Reset layout detection to automatic.
        """
        self.pretty_output_layer.reset_layout_detection()
    
    def enable_interactive_elements(self, enabled: bool = True) -> None:
        """
        Enable or disable interactive elements in formatted output.
        
        Args:
            enabled: Whether to enable interactive elements
        """
        self.pretty_output_layer.enable_interactive_elements(enabled)
    
    def get_available_formatters(self) -> List[Dict[str, Any]]:
        """
        Get information about available formatters.
        
        Returns:
            List of formatter metadata dictionaries
        """
        if self.use_extensions:
            try:
                return self.extensions_integration.get_available_formatters()
            except Exception as e:
                self.logger.error(f"Failed to get available formatters: {e}")
        
        # Return Pretty Output Layer formatters
        return [
            {
                "name": "Pretty Output Layer",
                "version": "1.0.0",
                "supported_content_types": ["default", "menu", "movie_list", "bullet_list", "system_status"],
                "theme_requirements": ["typography", "spacing", "colors"]
            }
        ]
    
    def get_supported_content_types(self) -> List[str]:
        """
        Get all supported content types.
        
        Returns:
            List of content type names
        """
        if self.use_extensions:
            try:
                return self.extensions_integration.get_supported_content_types()
            except Exception as e:
                self.logger.error(f"Failed to get supported content types: {e}")
        
        # Return Pretty Output Layer content types
        return ["default", "menu", "movie_list", "bullet_list", "system_status"]
    
    def get_integration_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the formatting integration.
        
        Returns:
            Dictionary with integration metrics
        """
        metrics = {
            "using_extensions": self.use_extensions,
            "extensions_available": EXTENSIONS_AVAILABLE
        }
        
        if self.use_extensions:
            try:
                metrics["extensions_metrics"] = self.extensions_integration.get_integration_metrics()
            except Exception as e:
                self.logger.error(f"Failed to get extensions metrics: {e}")
                metrics["extensions_metrics"] = {"error": str(e)}  # type: ignore
        
        return metrics