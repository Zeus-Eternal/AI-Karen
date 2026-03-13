"""
Pretty Output Layer (Global Response Formatter) for Karen's AI system.

This module provides configurable formatting for AI responses with support for
different output profiles and layout types. It integrates with existing
response formatting systems while maintaining a headless/API-first design.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
import logging
import re
import time
import traceback

logger = logging.getLogger(__name__)


class OutputProfile(Enum):
    """Output profile enumeration."""
    PLAIN = "plain"
    PRETTY = "pretty"
    DEV_DOC = "dev_doc"


class LayoutType(Enum):
    """Layout type enumeration."""
    DEFAULT = "default"
    MENU = "menu"
    MOVIE_LIST = "movie_list"
    BULLET_LIST = "bullet_list"
    SYSTEM_STATUS = "system_status"


@dataclass
class LayoutHint:
    """Layout hint for formatting decisions."""
    layout_type: LayoutType
    confidence: float = 1.0
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponseContext:
    """Context information for response formatting."""
    user_query: str
    response_content: str
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    session_data: Dict[str, Any] = field(default_factory=dict)
    theme_context: Dict[str, Any] = field(default_factory=dict)
    detected_content_type: Optional[str] = None
    confidence_score: float = 0.0


@dataclass
class FormattingConfig:
    """Configuration for response formatting."""
    output_profile: OutputProfile = OutputProfile.PRETTY
    default_layout: LayoutType = LayoutType.DEFAULT
    enable_markdown: bool = True
    enable_sections: bool = True
    enable_highlights: bool = True
    max_content_length: int = 10000
    safe_mode: bool = True


class PrettyOutputLayer:
    """
    Pretty Output Layer for formatting AI responses.
    
    This class provides configurable formatting for AI responses with support for
    different output profiles and layout types. It integrates with existing
    response formatting systems while maintaining a headless/API-first design.
    """
    
    def __init__(self, config: Optional[FormattingConfig] = None):
        """
        Initialize the Pretty Output Layer.
        
        Args:
            config: Configuration for formatting behavior
        """
        try:
            self.config = config or FormattingConfig()
            self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
            
            # Performance metrics
            self._performance_metrics = {
                "format_calls": 0,
                "layout_detection_time": 0.0,
                "formatting_time": 0.0,
                "errors": 0
            }
            
            # Initialize layout detectors
            self._layout_detectors = {
                LayoutType.MENU: self._detect_menu_layout,
                LayoutType.MOVIE_LIST: self._detect_movie_list_layout,
                LayoutType.BULLET_LIST: self._detect_bullet_list_layout,
                LayoutType.SYSTEM_STATUS: self._detect_system_status_layout,
            }
            
            # Initialize layout formatters
            self._layout_formatters = {
                LayoutType.DEFAULT: self._format_default_layout,
                LayoutType.MENU: self._format_menu_layout,
                LayoutType.MOVIE_LIST: self._format_movie_list_layout,
                LayoutType.BULLET_LIST: self._format_bullet_list_layout,
                LayoutType.SYSTEM_STATUS: self._format_system_status_layout,
            }
            
            # Initialize profile formatters
            self._profile_formatters = {
                OutputProfile.PLAIN: self._apply_plain_profile,
                OutputProfile.PRETTY: self._apply_pretty_profile,
                OutputProfile.DEV_DOC: self._apply_dev_doc_profile,
            }
            
            # Initialize interactive elements (disabled by default)
            self._interactive_elements_enabled = False
            
            self.logger.info(f"PrettyOutputLayer initialized with profile: {self.config.output_profile.value}")
            
        except Exception as e:
            self.logger.error(f"Error initializing PrettyOutputLayer: {e}")
            self.logger.debug(traceback.format_exc())
            raise
    
    def set_output_profile(self, profile: OutputProfile) -> None:
        """
        Set the output profile for formatting.
        
        Args:
            profile: The output profile to use
        """
        if not isinstance(profile, OutputProfile):
            raise ValueError(f"Invalid output profile: {profile}")
        
        old_profile = self.config.output_profile.value
        self.config.output_profile = profile
        
        self.logger.info(f"Output profile changed from {old_profile} to {profile.value}")
    
    def get_output_profile(self) -> OutputProfile:
        """
        Get the current output profile.
        
        Returns:
            The current output profile
        """
        return self.config.output_profile
    
    def force_layout_type(self, layout_type: LayoutType) -> None:
        """
        Force the use of a specific layout type.
        
        Args:
            layout_type: The layout type to force
        """
        if not isinstance(layout_type, LayoutType):
            raise ValueError(f"Invalid layout type: {layout_type}")
        
        self.config.default_layout = layout_type
        self.logger.info(f"Layout type forced to: {layout_type.value}")
    
    def reset_layout_detection(self) -> None:
        """
        Reset to automatic layout detection.
        """
        self.config.default_layout = LayoutType.DEFAULT
        self.logger.info("Layout detection reset to automatic")
    
    def enable_interactive_elements(self, enabled: bool = True) -> None:
        """
        Enable or disable interactive elements in formatted output.
        
        Args:
            enabled: Whether to enable interactive elements
        """
        try:
            # Add interactive elements configuration to the class
            self._interactive_elements_enabled = enabled
            self.logger.info(f"Interactive elements {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            self.logger.error(f"Error setting interactive elements: {e}")
            self.logger.debug(traceback.format_exc())
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the Pretty Output Layer.
        
        Returns:
            Dictionary containing performance metrics
        """
        try:
            avg_layout_time = (
                self._performance_metrics["layout_detection_time"] /
                max(self._performance_metrics["format_calls"], 1)
            )
            avg_format_time = (
                self._performance_metrics["formatting_time"] /
                max(self._performance_metrics["format_calls"], 1)
            )
            
            return {
                "format_calls": self._performance_metrics["format_calls"],
                "total_layout_detection_time": self._performance_metrics["layout_detection_time"],
                "total_formatting_time": self._performance_metrics["formatting_time"],
                "average_layout_detection_time": avg_layout_time,
                "average_formatting_time": avg_format_time,
                "errors": self._performance_metrics["errors"],
                "error_rate": (
                    self._performance_metrics["errors"] /
                    max(self._performance_metrics["format_calls"], 1)
                )
            }
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}
    
    def reset_performance_metrics(self) -> None:
        """
        Reset performance metrics.
        """
        try:
            self._performance_metrics = {
                "format_calls": 0,
                "layout_detection_time": 0.0,
                "formatting_time": 0.0,
                "errors": 0
            }
            self.logger.info("Performance metrics reset")
        except Exception as e:
            self.logger.error(f"Error resetting performance metrics: {e}")
    
    def add_interactive_element(self, element_type: str, content: str, **kwargs) -> str:
        """
        Add an interactive element to the content.
        
        Args:
            element_type: Type of interactive element (button, link, etc.)
            content: Content for the element
            **kwargs: Additional parameters for the element
            
        Returns:
            Formatted interactive element
        """
        try:
            if not getattr(self, '_interactive_elements_enabled', False):
                self.logger.debug("Interactive elements disabled, returning content as-is")
                return content
            
            self.logger.debug(f"Adding interactive element of type: {element_type}")
            
            # Format based on element type
            if element_type == "button":
                action = kwargs.get("action", "")
                formatted = f"[{content}]({action})"
                self.logger.debug(f"Formatted button element: {formatted}")
                return formatted
            elif element_type == "link":
                url = kwargs.get("url", "")
                formatted = f"[{content}]({url})"
                self.logger.debug(f"Formatted link element: {formatted}")
                return formatted
            elif element_type == "menu":
                options = kwargs.get("options", [])
                formatted_options = "\n".join([f"• {option}" for option in options])
                formatted = f"{content}\n{formatted_options}"
                self.logger.debug(f"Formatted menu element with {len(options)} options")
                return formatted
            else:
                # Unknown element type, return as-is
                self.logger.warning(f"Unknown interactive element type: {element_type}")
                return content
                
        except Exception as e:
            self.logger.error(f"Error adding interactive element: {e}")
            self.logger.debug(traceback.format_exc())
            # Return original content on error
            return content
    
    def format_response(
        self,
        response_content: str,
        context: ResponseContext
    ) -> Dict[str, Any]:
        """
        Format a response using the configured output profile and detected layout.
        
        Args:
            response_content: The raw response content to format
            context: Context information for formatting
            
        Returns:
            Dictionary containing formatted response and metadata
        """
        start_time = time.time()
        self._performance_metrics["format_calls"] += 1
        
        try:
            # Log input details
            self.logger.debug(
                f"Formatting response: content_length={len(response_content)}, "
                f"profile={self.config.output_profile.value}, "
                f"safe_mode={self.config.safe_mode}"
            )
            
            # Apply safety checks
            if self.config.safe_mode:
                try:
                    response_content = self._sanitize_content(response_content)
                except Exception as e:
                    self.logger.warning(f"Error during content sanitization: {e}")
                    # Continue with original content if sanitization fails
            
            # Truncate if needed
            original_length = len(response_content)
            if original_length > self.config.max_content_length:
                response_content = response_content[:self.config.max_content_length] + "... [truncated]"
                self.logger.info(f"Content truncated from {original_length} to {len(response_content)} characters")
            
            # Detect layout with timing
            layout_start = time.time()
            try:
                layout_hint = self._detect_layout(response_content, context)
                layout_time = time.time() - layout_start
                self._performance_metrics["layout_detection_time"] += layout_time
                self.logger.debug(f"Layout detection completed in {layout_time:.4f}s: {layout_hint.layout_type.value}")
            except Exception as e:
                self.logger.error(f"Error during layout detection: {e}")
                self.logger.debug(traceback.format_exc())
                # Use default layout as fallback
                layout_hint = LayoutHint(layout_type=LayoutType.DEFAULT, confidence=0.0)
            
            # Format based on layout with timing
            format_start = time.time()
            try:
                formatted_content = self._format_by_layout(
                    response_content, layout_hint, context
                )
                format_time = time.time() - format_start
                self._performance_metrics["formatting_time"] += format_time
                self.logger.debug(f"Layout formatting completed in {format_time:.4f}s")
            except Exception as e:
                self.logger.error(f"Error during layout formatting: {e}")
                self.logger.debug(traceback.format_exc())
                formatted_content = response_content  # Use original content as fallback
            
            # Apply profile formatting with timing
            profile_start = time.time()
            try:
                formatted_content = self._apply_profile_formatting(
                    formatted_content, context
                )
                profile_time = time.time() - profile_start
                self.logger.debug(f"Profile formatting completed in {profile_time:.4f}s")
            except Exception as e:
                self.logger.error(f"Error during profile formatting: {e}")
                self.logger.debug(traceback.format_exc())
                # Continue with content as-is if profile formatting fails
            
            # Build response
            total_time = time.time() - start_time
            response = {
                "content": formatted_content,
                "layout_type": layout_hint.layout_type.value,
                "output_profile": self.config.output_profile.value,
                "metadata": {
                    "layout_confidence": layout_hint.confidence,
                    "layout_parameters": layout_hint.parameters,
                    "content_length": len(response_content),
                    "original_length": original_length,
                    "formatting_applied": True,
                    "processing_time": total_time,
                }
            }
            
            self.logger.info(
                f"Formatted response with layout: {layout_hint.layout_type.value}, "
                f"profile: {self.config.output_profile.value} in {total_time:.4f}s"
            )
            
            return response
            
        except Exception as e:
            self._performance_metrics["errors"] += 1
            total_time = time.time() - start_time
            self.logger.error(f"Error formatting response: {e}")
            self.logger.debug(traceback.format_exc())
            
            # Return basic formatted response on error
            return {
                "content": response_content,
                "layout_type": LayoutType.DEFAULT.value,
                "output_profile": OutputProfile.PLAIN.value,
                "metadata": {
                    "layout_confidence": 0.0,
                    "layout_parameters": {},
                    "content_length": len(response_content),
                    "formatting_applied": False,
                    "error": str(e),
                    "processing_time": total_time,
                }
            }
    
    def _detect_layout(self, content: str, context: ResponseContext) -> LayoutHint:
        """
        Detect the most appropriate layout for the content.
        
        Args:
            content: The content to analyze
            context: Context information
            
        Returns:
            LayoutHint with detected layout type and confidence
        """
        try:
            # Log input details
            lines_count = len(content.split('\n'))
            self.logger.debug(
                f"Detecting layout for content: length={len(content)}, "
                f"lines={lines_count}"
            )
            
            # If a specific layout is forced, use it
            if self.config.default_layout != LayoutType.DEFAULT:
                self.logger.debug(f"Using forced layout: {self.config.default_layout.value}")
                return LayoutHint(
                    layout_type=self.config.default_layout,
                    confidence=1.0,
                    parameters={"forced": True}
                )
            
            best_layout = LayoutType.DEFAULT
            best_confidence = 0.0
            best_parameters = {}
            detector_errors = []
            
            # Try each layout detector
            for layout_type, detector in self._layout_detectors.items():
                try:
                    self.logger.debug(f"Running {layout_type.value} detector")
                    hint = detector(content, context)
                    
                    if hint.confidence > best_confidence:
                        best_layout = layout_type
                        best_confidence = hint.confidence
                        best_parameters = hint.parameters
                        self.logger.debug(
                            f"New best layout: {layout_type.value} with confidence {hint.confidence}"
                        )
                except Exception as e:
                    error_msg = f"Error in layout detector for {layout_type.value}: {e}"
                    self.logger.warning(error_msg)
                    detector_errors.append(error_msg)
                    self.logger.debug(traceback.format_exc())
            
            # Log detector errors if any
            if detector_errors:
                self.logger.warning(f"Layout detector errors: {'; '.join(detector_errors)}")
            
            # Use default layout if confidence is too low
            if best_confidence < 0.3:
                self.logger.debug(f"Confidence too low ({best_confidence}), using default layout")
                best_layout = LayoutType.DEFAULT
                best_confidence = 0.5
                best_parameters = {}
            
            result = LayoutHint(
                layout_type=best_layout,
                confidence=best_confidence,
                parameters=best_parameters
            )
            
            self.logger.debug(
                f"Layout detection result: {best_layout.value} with confidence {best_confidence}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in layout detection: {e}")
            self.logger.debug(traceback.format_exc())
            # Return default layout as fallback
            return LayoutHint(
                layout_type=LayoutType.DEFAULT,
                confidence=0.0,
                parameters={"error": str(e)}
            )
    
    def _format_by_layout(
        self,
        content: str,
        layout_hint: LayoutHint,
        context: ResponseContext
    ) -> str:
        """
        Format content based on the detected layout.
        
        Args:
            content: The content to format
            layout_hint: Layout detection result
            context: Context information
            
        Returns:
            Content formatted according to the layout
        """
        try:
            self.logger.debug(
                f"Formatting by layout: {layout_hint.layout_type.value}, "
                f"confidence: {layout_hint.confidence}"
            )
            
            formatter = self._layout_formatters.get(layout_hint.layout_type)
            if not formatter:
                self.logger.warning(f"No formatter for layout: {layout_hint.layout_type.value}")
                return content
            
            try:
                formatted_content = formatter(content, layout_hint.parameters, context)
                self.logger.debug(
                    f"Successfully formatted content with {layout_hint.layout_type.value} layout"
                )
                return formatted_content
            except Exception as e:
                self.logger.error(f"Error formatting with {layout_hint.layout_type.value}: {e}")
                self.logger.debug(traceback.format_exc())
                return content
                
        except Exception as e:
            self.logger.error(f"Unexpected error in _format_by_layout: {e}")
            self.logger.debug(traceback.format_exc())
            return content
    
    def _apply_profile_formatting(self, content: str, context: ResponseContext) -> str:
        """
        Apply output profile formatting to the content.
        
        Args:
            content: The content to format
            context: Context information
            
        Returns:
            Content formatted according to the output profile
        """
        try:
            self.logger.debug(f"Applying profile formatting: {self.config.output_profile.value}")
            
            formatter = self._profile_formatters.get(self.config.output_profile)
            if not formatter:
                self.logger.warning(f"No formatter for profile: {self.config.output_profile.value}")
                return content
            
            try:
                formatted_content = formatter(content, context)
                self.logger.debug(
                    f"Successfully applied {self.config.output_profile.value} profile formatting"
                )
                return formatted_content
            except Exception as e:
                self.logger.error(f"Error applying profile {self.config.output_profile.value}: {e}")
                self.logger.debug(traceback.format_exc())
                return content
                
        except Exception as e:
            self.logger.error(f"Unexpected error in _apply_profile_formatting: {e}")
            self.logger.debug(traceback.format_exc())
            return content
    
    def _sanitize_content(self, content: str) -> str:
        """
        Sanitize content for safe rendering.
        
        Args:
            content: The content to sanitize
            
        Returns:
            Sanitized content
        """
        try:
            if not content:
                return ""
                
            original_length = len(content)
            self.logger.debug(f"Sanitizing content of length {original_length}")
            
            # Basic HTML tag removal
            content = re.sub(r'<[^>]+>', '', content)
            
            # Normalize excessive whitespace
            content = re.sub(r'\n{3,}', '\n\n', content)
            content = re.sub(r' {2,}', ' ', content)
            
            sanitized_content = content.strip()
            
            if len(sanitized_content) != original_length:
                self.logger.debug(
                    f"Content sanitized: {original_length} -> {len(sanitized_content)} characters"
                )
            
            return sanitized_content
            
        except Exception as e:
            self.logger.error(f"Error sanitizing content: {e}")
            self.logger.debug(traceback.format_exc())
            # Return original content if sanitization fails
            return content if content else ""
    
    # Layout Detectors
    
    def _detect_menu_layout(self, content: str, context: ResponseContext) -> LayoutHint:
        """Detect if content should be formatted as a menu."""
        try:
            # Look for option patterns
            option_patterns = [
                r'^\s*\d+\.\s+.+',  # Numbered options
                r'^\s*[-*+]\s+.+',  # Bullet options
                r'^\s*[A-Z][a-z]*:\s+.+',  # Labeled options
            ]
            
            lines = content.split('\n')
            option_count = 0
            
            for line in lines:
                for pattern in option_patterns:
                    if re.match(pattern, line, re.MULTILINE):
                        option_count += 1
                        break
            
            # Calculate confidence based on option density
            total_lines = len([line for line in lines if line.strip()])
            confidence = min(option_count / max(total_lines, 1), 1.0)
            
            self.logger.debug(
                f"Menu layout detection: {option_count} options in {total_lines} lines, "
                f"confidence: {confidence}"
            )
            
            # Consider it a menu if at least 30% of lines are options
            if confidence >= 0.3:
                return LayoutHint(
                    layout_type=LayoutType.MENU,
                    confidence=confidence,
                    parameters={"option_count": option_count}
                )
            
            return LayoutHint(layout_type=LayoutType.MENU, confidence=0.0)
            
        except Exception as e:
            self.logger.error(f"Error in menu layout detection: {e}")
            self.logger.debug(traceback.format_exc())
            return LayoutHint(layout_type=LayoutType.MENU, confidence=0.0)
    
    def _detect_movie_list_layout(self, content: str, context: ResponseContext) -> LayoutHint:
        """Detect if content should be formatted as a movie list."""
        try:
            # Look for movie-related keywords
            movie_keywords = [
                'movie', 'film', 'director', 'starring', 'genre', 'rating',
                'release date', 'duration', 'watch', 'cinema'
            ]
            
            # Check for movie patterns
            movie_patterns = [
                r'.*\(\d{4}\).*',  # Year in parentheses
                r'.*\*\*.*\*\*.*',  # Bold titles
                r'.*Director:.*',
                r'.*Starring:.*',
            ]
            
            content_lower = content.lower()
            keyword_score = sum(1 for keyword in movie_keywords if keyword in content_lower)
            pattern_score = sum(1 for pattern in movie_patterns if re.search(pattern, content, re.IGNORECASE))
            
            # Calculate confidence
            max_score = len(movie_keywords) + len(movie_patterns)
            confidence = min((keyword_score + pattern_score) / max(max_score, 1), 1.0)
            
            self.logger.debug(
                f"Movie list layout detection: keyword_score={keyword_score}, "
                f"pattern_score={pattern_score}, confidence={confidence}"
            )
            
            # Consider it a movie list if confidence is at least 0.4
            if confidence >= 0.4:
                return LayoutHint(
                    layout_type=LayoutType.MOVIE_LIST,
                    confidence=confidence,
                    parameters={"keyword_score": keyword_score, "pattern_score": pattern_score}
                )
            
            return LayoutHint(layout_type=LayoutType.MOVIE_LIST, confidence=0.0)
            
        except Exception as e:
            self.logger.error(f"Error in movie list layout detection: {e}")
            self.logger.debug(traceback.format_exc())
            return LayoutHint(layout_type=LayoutType.MOVIE_LIST, confidence=0.0)
    
    def _detect_bullet_list_layout(self, content: str, context: ResponseContext) -> LayoutHint:
        """Detect if content should be formatted as a bullet list."""
        try:
            lines = content.split('\n')
            bullet_count = 0
            
            # Count bullet points
            for line in lines:
                if re.match(r'^\s*[-*+]\s+', line):
                    bullet_count += 1
            
            # Calculate confidence based on bullet density
            total_lines = len([line for line in lines if line.strip()])
            confidence = min(bullet_count / max(total_lines, 1), 1.0)
            
            self.logger.debug(
                f"Bullet list layout detection: {bullet_count} bullets in {total_lines} lines, "
                f"confidence: {confidence}"
            )
            
            # Consider it a bullet list if at least 40% of lines are bullets
            if confidence >= 0.4:
                return LayoutHint(
                    layout_type=LayoutType.BULLET_LIST,
                    confidence=confidence,
                    parameters={"bullet_count": bullet_count}
                )
            
            return LayoutHint(layout_type=LayoutType.BULLET_LIST, confidence=0.0)
            
        except Exception as e:
            self.logger.error(f"Error in bullet list layout detection: {e}")
            self.logger.debug(traceback.format_exc())
            return LayoutHint(layout_type=LayoutType.BULLET_LIST, confidence=0.0)
    
    def _detect_system_status_layout(self, content: str, context: ResponseContext) -> LayoutHint:
        """Detect if content should be formatted as system status."""
        try:
            # Look for system status keywords
            status_keywords = [
                'status', 'system', 'service', 'online', 'offline', 'error',
                'warning', 'critical', 'healthy', 'unhealthy', 'running', 'stopped'
            ]
            
            # Look for status patterns
            status_patterns = [
                r'.*Status:.*',
                r'.*Service:.*',
                r'.*State:.*',
                r'.*\[.*\].*',  # Status in brackets
            ]
            
            content_lower = content.lower()
            keyword_score = sum(1 for keyword in status_keywords if keyword in content_lower)
            pattern_score = sum(1 for pattern in status_patterns if re.search(pattern, content, re.IGNORECASE))
            
            # Calculate confidence
            max_score = len(status_keywords) + len(status_patterns)
            confidence = min((keyword_score + pattern_score) / max(max_score, 1), 1.0)
            
            self.logger.debug(
                f"System status layout detection: keyword_score={keyword_score}, "
                f"pattern_score={pattern_score}, confidence={confidence}"
            )
            
            # Consider it system status if confidence is at least 0.3
            if confidence >= 0.3:
                return LayoutHint(
                    layout_type=LayoutType.SYSTEM_STATUS,
                    confidence=confidence,
                    parameters={"keyword_score": keyword_score, "pattern_score": pattern_score}
                )
            
            return LayoutHint(layout_type=LayoutType.SYSTEM_STATUS, confidence=0.0)
            
        except Exception as e:
            self.logger.error(f"Error in system status layout detection: {e}")
            self.logger.debug(traceback.format_exc())
            return LayoutHint(layout_type=LayoutType.SYSTEM_STATUS, confidence=0.0)
    
    # Layout Formatters
    
    def _format_default_layout(self, content: str, parameters: Dict[str, Any], context: ResponseContext) -> str:
        """Format content using the default layout."""
        if not self.config.enable_markdown:
            return content
        
        # Apply basic markdown formatting
        formatted = self._format_paragraphs(content)
        formatted = self._format_headings(formatted)
        formatted = self._format_code_blocks(formatted)
        
        return formatted
    
    def _format_menu_layout(self, content: str, parameters: Dict[str, Any], context: ResponseContext) -> str:
        """Format content as a menu."""
        if not self.config.enable_markdown:
            return content
        
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
            
            # Format options
            if re.match(r'^\d+\.\s+', line):
                # Numbered option
                formatted_lines.append(f"**{line}**")
            elif re.match(r'^[-*+]\s+', line):
                # Bullet option
                formatted_lines.append(f"• {line[1:].strip()}")
            elif re.match(r'^[A-Z][a-z]*:\s+', line):
                # Labeled option
                formatted_lines.append(f"**{line}**")
            else:
                # Regular content
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_movie_list_layout(self, content: str, parameters: Dict[str, Any], context: ResponseContext) -> str:
        """Format content as a movie list."""
        if not self.config.enable_markdown:
            return content
        
        # Extract movie entries (simplified approach)
        entries = re.split(r'\n\s*\n', content)
        formatted_entries = []
        
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            
            # Try to extract title, year, and description
            title_match = re.search(r'^\*\*(.+?)\*\*', entry)
            if title_match:
                title = title_match.group(1)
                rest = entry[title_match.end():].strip()
                
                # Try to extract year
                year_match = re.search(r'\((\d{4})\)', rest)
                year = year_match.group(1) if year_match else ''
                
                # Format as a movie card
                formatted_entry = f"**{title}** {year}\n\n{rest}"
                formatted_entries.append(formatted_entry)
            else:
                # Keep as-is if no clear structure
                formatted_entries.append(entry)
        
        return '\n\n---\n\n'.join(formatted_entries)
    
    def _format_bullet_list_layout(self, content: str, parameters: Dict[str, Any], context: ResponseContext) -> str:
        """Format content as a bullet list."""
        if not self.config.enable_markdown:
            return content
        
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
            
            # Format bullets
            if re.match(r'^[-*+]\s+', line):
                formatted_lines.append(f"• {line[1:].strip()}")
            elif re.match(r'^\d+\.\s+', line):
                # Convert numbered lists to bullets for consistency
                formatted_lines.append(f"• {line.split('.', 1)[1].strip()}")
            else:
                # Regular content
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_system_status_layout(self, content: str, parameters: Dict[str, Any], context: ResponseContext) -> str:
        """Format content as system status."""
        if not self.config.enable_markdown:
            return content
        
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
            
            # Look for status indicators
            if any(keyword in line.lower() for keyword in ['online', 'healthy', 'running', 'ok']):
                formatted_lines.append(f"✅ {line}")
            elif any(keyword in line.lower() for keyword in ['offline', 'unhealthy', 'stopped', 'error']):
                formatted_lines.append(f"❌ {line}")
            elif any(keyword in line.lower() for keyword in ['warning', 'caution']):
                formatted_lines.append(f"⚠️ {line}")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    # Profile Formatters
    
    def _apply_plain_profile(self, content: str, context: ResponseContext) -> str:
        """Apply plain profile formatting (minimal formatting)."""
        # Remove markdown formatting
        content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)  # Bold
        content = re.sub(r'`(.+?)`', r'\1', content)  # Code
        content = re.sub(r'#{1,6}\s*', '', content)  # Headings
        
        # Clean up extra whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    def _apply_pretty_profile(self, content: str, context: ResponseContext) -> str:
        """Apply pretty profile formatting (enhanced formatting)."""
        if not self.config.enable_markdown:
            return content
        
        # Apply enhanced formatting
        content = self._format_paragraphs(content)
        content = self._format_headings(content)
        content = self._format_code_blocks(content)
        content = self._format_highlights(content)
        
        if self.config.enable_sections:
            content = self._format_sections(content)
        
        return content
    
    def _apply_dev_doc_profile(self, content: str, context: ResponseContext) -> str:
        """Apply developer documentation profile formatting."""
        if not self.config.enable_markdown:
            return content
        
        # Apply developer-specific formatting
        content = self._format_paragraphs(content)
        content = self._format_headings(content)
        content = self._format_code_blocks(content)
        content = self._format_code_blocks_enhanced(content)
        content = self._format_highlights(content)
        
        if self.config.enable_sections:
            content = self._format_sections(content)
        
        # Add developer-specific elements
        content = self._add_code_annotations(content)
        content = self._add_api_references(content)
        
        return content
    
    # Helper Methods
    
    def _format_paragraphs(self, content: str) -> str:
        """Format paragraphs with proper spacing."""
        # Split into paragraphs
        paragraphs = re.split(r'\n\s*\n', content)
        
        # Format each paragraph
        formatted_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para:
                formatted_paragraphs.append(para)
        
        # Join with double line breaks
        return '\n\n'.join(formatted_paragraphs)
    
    def _format_headings(self, content: str) -> str:
        """Format headings consistently."""
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Convert various heading formats to markdown
            if re.match(r'^[A-Z][A-Z0-9\s\/&\-\(\)]+:$', line.strip()):
                # Title case with colon
                formatted_lines.append(f"## {line.strip()}")
            elif re.match(r'^#+\s+', line):
                # Already markdown heading
                formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _format_code_blocks(self, content: str) -> str:
        """Format code blocks."""
        # Simple code block formatting
        # More advanced formatting would be in the dev_doc profile
        return content
    
    def _format_code_blocks_enhanced(self, content: str) -> str:
        """Format code blocks with enhanced features."""
        # Add line numbers if not present
        # Add syntax highlighting hints
        # Add copy button hints
        return content
    
    def _format_highlights(self, content: str) -> str:
        """Format highlighted content."""
        # Convert **bold** to markdown bold
        # Convert *italic* to markdown italic
        # Convert `code` to markdown code
        return content
    
    def _format_sections(self, content: str) -> str:
        """Format content sections."""
        # Add horizontal rules between sections
        # Add section anchors
        return content
    
    def _add_code_annotations(self, content: str) -> str:
        """Add code annotations for developer profile."""
        # Add TODO comments
        # Add FIXME comments
        # Add NOTE comments
        return content
    
    def _add_api_references(self, content: str) -> str:
        """Add API references for developer profile."""
        # Link API methods
        # Link class names
        # Link parameters
        return content