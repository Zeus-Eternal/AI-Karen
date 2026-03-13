"""
Enhanced Response Formatter with Pretty Output Layer

This module provides comprehensive response formatting with support for:
- Multiple output profiles
- Content type detection
- Syntax highlighting
- Responsive formatting
- Theme-aware formatting
- Accessibility features
- Streaming support
- Metadata formatting
- Custom profiles and user preferences
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime

try:
    from .response_formatting_models import (
        OutputProfile, LayoutType, ContentType, DisplayContext, ThemeMode,
        AccessibilityLevel, ResponseContext, FormattingConfig, ResponseMetadata,
        StreamingChunk, FormattingPreferences
    )
    from .content_type_detector import get_content_detector, DetectionResult
    from .syntax_highlighter import get_syntax_highlighter, SyntaxHighlightConfig
    from .responsive_formatter import get_responsive_formatter, ResponsiveConfig
except ImportError:
    # Fallback imports for circular dependency
    from enum import Enum
    
    class OutputProfile(Enum):
        PLAIN = "plain"
        PRETTY = "pretty"
        DEV_DOC = "dev_doc"
        MINIMAL = "minimal"
        VERBOSE = "verbose"
        ACCESSIBLE = "accessible"
        TECHNICAL = "technical"
        CONVERSATIONAL = "conversational"
    
    class LayoutType(Enum):
        DEFAULT = "default"
        MENU = "menu"
        MOVIE_LIST = "movie_list"
        BULLET_LIST = "bullet_list"
        SYSTEM_STATUS = "system_status"
        CODE_BLOCK = "code_block"
        TABLE = "table"
        STEPS = "steps"
        COMPARISON = "comparison"
        TIMELINE = "timeline"
        TREE = "tree"
        GRID = "grid"
        ACCORDION = "accordion"
        TABS = "tabs"
    
    class ContentType(Enum):
        TEXT = "text"
        CODE = "code"
        MARKDOWN = "markdown"
        JSON = "json"
        XML = "xml"
        YAML = "yaml"
        SQL = "sql"
        HTML = "html"
        CSS = "css"
        JAVASCRIPT = "javascript"
        PYTHON = "python"
        DATA_TABLE = "data_table"
        LIST = "list"
        MENU = "menu"
        STEPS = "steps"
        ERROR = "error"
        WARNING = "warning"
        INFO = "info"
        SUCCESS = "success"
    
    class DisplayContext(Enum):
        DESKTOP = "desktop"
        MOBILE = "mobile"
        TABLET = "tablet"
        TERMINAL = "terminal"
        API = "api"
        PRINT = "print"
        EMBEDDED = "embedded"
        VOICE = "voice"
    
    class ThemeMode(Enum):
        LIGHT = "light"
        DARK = "dark"
        AUTO = "auto"
        HIGH_CONTRAST = "high_contrast"
    
    class AccessibilityLevel(Enum):
        BASIC = "basic"
        ENHANCED = "enhanced"
        FULL = "full"
        SCREEN_READER = "screen_reader"
    
    class ResponseContext:
        def __init__(self, user_query, response_content, user_preferences=None, 
                     session_data=None, theme_context=None, detected_content_type=None,
                     confidence_score=0.0, display_context=DisplayContext.DESKTOP,
                     accessibility_level=AccessibilityLevel.BASIC, theme_mode=ThemeMode.AUTO,
                     language="en", is_streaming=False, stream_chunk_id=None,
                     metadata=None):
            self.user_query = user_query
            self.response_content = response_content
            self.user_preferences = user_preferences or {}
            self.session_data = session_data or {}
            self.theme_context = theme_context or {}
            self.detected_content_type = detected_content_type
            self.confidence_score = confidence_score
            self.display_context = display_context
            self.accessibility_level = accessibility_level
            self.theme_mode = theme_mode
            self.language = language
            self.is_streaming = is_streaming
            self.stream_chunk_id = stream_chunk_id
            self.metadata = metadata
    
    class FormattingConfig:
        def __init__(self, output_profile=OutputProfile.PRETTY, default_layout=LayoutType.DEFAULT,
                     enable_markdown=True, enable_sections=True, enable_highlights=True,
                     enable_syntax_highlighting=True, enable_interactive_elements=True,
                     enable_responsive_formatting=True, enable_accessibility_features=True,
                     enable_theme_support=True, max_content_length=10000, safe_mode=True,
                     cache_enabled=True, performance_monitoring=True, custom_formatters=None,
                     theme_configurations=None, accessibility_configurations=None):
            self.output_profile = output_profile
            self.default_layout = default_layout
            self.enable_markdown = enable_markdown
            self.enable_sections = enable_sections
            self.enable_highlights = enable_highlights
            self.enable_syntax_highlighting = enable_syntax_highlighting
            self.enable_interactive_elements = enable_interactive_elements
            self.enable_responsive_formatting = enable_responsive_formatting
            self.enable_accessibility_features = enable_accessibility_features
            self.enable_theme_support = enable_theme_support
            self.max_content_length = max_content_length
            self.safe_mode = safe_mode
            self.cache_enabled = cache_enabled
            self.performance_monitoring = performance_monitoring
            self.custom_formatters = custom_formatters or {}
            self.theme_configurations = theme_configurations or {}
            self.accessibility_configurations = accessibility_configurations or {}
    
    class ResponseMetadata:
        def __init__(self, timestamp=None, processing_time=0.0, content_length=0,
                     original_length=0, confidence_score=0.0, sources=None, model_used=None,
                     user_id=None, session_id=None, formatting_applied=True,
                     layout_confidence=0.0, content_type_detected=None,
                     language_detected=None, theme_used=None,
                     accessibility_features=None, interactive_elements=None,
                     custom_metadata=None):
            self.timestamp = timestamp or datetime.utcnow()
            self.processing_time = processing_time
            self.content_length = content_length
            self.original_length = original_length
            self.confidence_score = confidence_score
            self.sources = sources or []
            self.model_used = model_used
            self.user_id = user_id
            self.session_id = session_id
            self.formatting_applied = formatting_applied
            self.layout_confidence = layout_confidence
            self.content_type_detected = content_type_detected
            self.language_detected = language_detected
            self.theme_used = theme_used
            self.accessibility_features = accessibility_features or []
            self.interactive_elements = interactive_elements or []
            self.custom_metadata = custom_metadata or {}
    
    class StreamingChunk:
        def __init__(self, chunk_id, content, state, metadata=None, layout_hint=None,
                     formatting_applied=False, is_final_chunk=False, error_message=None,
                     progress=0.0):
            self.chunk_id = chunk_id
            self.content = content
            self.state = state
            self.metadata = metadata or ResponseMetadata()
            self.layout_hint = layout_hint
            self.formatting_applied = formatting_applied
            self.is_final_chunk = is_final_chunk
            self.error_message = error_message
            self.progress = progress
    
    class FormattingPreferences:
        def __init__(self, output_profile=OutputProfile.PRETTY, theme_mode=ThemeMode.AUTO,
                     accessibility_level=AccessibilityLevel.BASIC, display_context=DisplayContext.DESKTOP,
                     language="en", timezone="UTC", date_format="%Y-%m-%d %H:%M:%S",
                     enable_syntax_highlighting=True, enable_interactive_elements=True,
                     enable_animations=True, max_content_length=10000, custom_css_classes=None,
                     custom_settings=None):
            self.output_profile = output_profile
            self.theme_mode = theme_mode
            self.accessibility_level = accessibility_level
            self.display_context = display_context
            self.language = language
            self.timezone = timezone
            self.date_format = date_format
            self.enable_syntax_highlighting = enable_syntax_highlighting
            self.enable_interactive_elements = enable_interactive_elements
            self.enable_animations = enable_animations
            self.max_content_length = max_content_length
            self.custom_css_classes = custom_css_classes or []
            self.custom_settings = custom_settings or {}

logger = logging.getLogger(__name__)


@dataclass
class FormattingResult:
    """Result of response formatting operation."""
    formatted_content: str
    content_type: ContentType
    layout_type: LayoutType
    output_profile: OutputProfile
    metadata: ResponseMetadata
    css_classes: List[str] = field(default_factory=list)
    accessibility_features: List[str] = field(default_factory=list)
    interactive_elements: List[str] = field(default_factory=list)
    theme_requirements: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    confidence_score: float = 0.0


class EnhancedResponseFormatter:
    """
    Enhanced response formatter with comprehensive formatting capabilities.
    
    This class integrates:
    - Content type detection
    - Syntax highlighting
    - Responsive formatting
    - Theme-aware formatting
    - Accessibility features
    - Streaming support
    - Metadata formatting
    - Custom profiles and user preferences
    """
    
    def __init__(self, config: Optional[FormattingConfig] = None):
        """Initialize the enhanced response formatter."""
        self.config = config or FormattingConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize subsystems
        self.content_detector = None
        self.syntax_highlighter = None
        self.responsive_formatter = None
        
        # Performance metrics
        self._performance_metrics = {
            "total_formatting": 0,
            "content_detections": 0,
            "syntax_highlights": 0,
            "responsive_adaptations": 0,
            "theme_applications": 0,
            "accessibility_enhancements": 0,
            "streaming_chunks": 0,
            "average_processing_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Simple cache for formatted content
        self._format_cache = {}
        self._cache_max_size = 500
        
        self.logger.info(f"EnhancedResponseFormatter initialized with profile: {self.config.output_profile.value}")
    
    async def format_response(
        self,
        content: str,
        context: ResponseContext
    ) -> FormattingResult:
        """
        Format a response using the enhanced formatting system.
        
        Args:
            content: The content to format
            context: Response context with preferences and metadata
            
        Returns:
            FormattingResult with formatted content and metadata
        """
        start_time = time.time()
        self._performance_metrics["total_formatting"] += 1
        
        try:
            self.logger.debug(f"Formatting response: {len(content)} characters")
            
            # Initialize subsystems if needed
            if not self.content_detector:
                try:
                    from .content_type_detector import get_content_detector
                    self.content_detector = get_content_detector()
                except ImportError:
                    self.content_detector = None
                self.content_detector = get_content_detector()
            
            if not self.syntax_highlighter:
                try:
                    from .syntax_highlighter import get_syntax_highlighter
                    self.syntax_highlighter = get_syntax_highlighter()
                except ImportError:
                    self.syntax_highlighter = None
                self.syntax_highlighter = get_syntax_highlighter()
            
            if not self.responsive_formatter:
                try:
                    from .responsive_formatter import get_responsive_formatter
                    self.responsive_formatter = get_responsive_formatter()
                except ImportError:
                    self.responsive_formatter = None
                self.responsive_formatter = get_responsive_formatter()
            
            # Check cache first
            cache_key = self._generate_cache_key(content, context)
            if cache_key in self._format_cache:
                self._performance_metrics["cache_hits"] += 1
                cached_result = self._format_cache[cache_key]
                self.logger.debug("Using cached formatting result")
                return cached_result
            
            self._performance_metrics["cache_misses"] += 1
            
            # Step 1: Detect content type
            detection_result = await self.content_detector.detect_content_type(
                content,
                user_query=context.user_query,
                context_hints=context.session_data.get('context_hints', []),
                display_context=context.display_context
            )
            self._performance_metrics["content_detections"] += 1
            
            # Update context with detected content type
            context.detected_content_type = detection_result.content_type
            context.confidence_score = detection_result.confidence
            
            # Step 2: Apply syntax highlighting if enabled and content is code
            highlighted_content = content
            if (self.config.enable_syntax_highlighting and 
                detection_result.content_type in [ContentType.CODE, ContentType.PYTHON, 
                                            ContentType.JAVASCRIPT, ContentType.JSON, 
                                            ContentType.SQL, ContentType.HTML, ContentType.CSS]):
                
                highlight_config = SyntaxHighlightConfig(
                    language=self._map_content_type_to_language(detection_result.content_type),
                    theme=self._get_theme_for_context(context),
                    line_numbers=context.user_preferences.get('line_numbers', True)
                )
                
                highlight_result = await self.syntax_highlighter.highlight_code(
                    content, highlight_config
                )
                highlighted_content = self._convert_highlighted_to_text(highlight_result)
                self._performance_metrics["syntax_highlights"] += 1
            else:
                highlighted_content = content
            
            # Step 3: Apply responsive formatting if enabled
            if self.config.enable_responsive_formatting:
                responsive_config = ResponsiveConfig(
                    display_context=context.display_context,
                    screen_width=context.session_data.get('screen_width'),
                    screen_height=context.session_data.get('screen_height'),
                    touch_enabled=context.session_data.get('touch_enabled', False),
                    high_dpi=context.session_data.get('high_dpi', False),
                    prefers_reduced_motion=context.session_data.get('prefers_reduced_motion', False),
                    prefers_dark_theme=context.theme_mode == ThemeMode.DARK
                )
                
                layout_type = (detection_result.layout_hint.layout_type 
                              if detection_result.layout_hint 
                              else self.config.default_layout)
                
                responsive_result = await self.responsive_formatter.format_responsive(
                    highlighted_content, responsive_config, layout_type
                )
                
                formatted_content = responsive_result['content']
                self._performance_metrics["responsive_adaptations"] += 1
                
                # Update CSS classes and features
                css_classes = responsive_result.get('css_classes', [])
                accessibility_features = responsive_result.get('accessibility_adaptations', [])
            else:
                formatted_content = highlighted_content
                css_classes = []
                accessibility_features = []
            
            # Step 4: Apply theme-aware formatting if enabled
            if self.config.enable_theme_support:
                formatted_content = self._apply_theme_formatting(
                    formatted_content, context
                )
                self._performance_metrics["theme_applications"] += 1
            
            # Step 5: Apply accessibility features if enabled
            if self.config.enable_accessibility_features:
                formatted_content = self._apply_accessibility_features(
                    formatted_content, context
                )
                self._performance_metrics["accessibility_enhancements"] += 1
                accessibility_features.extend(self._get_accessibility_features_for_context(context))
            
            # Step 6: Apply profile-specific formatting
            formatted_content = await self._apply_profile_formatting(
                formatted_content, context
            )
            
            # Step 7: Apply safe mode if enabled
            if self.config.safe_mode:
                formatted_content = self._apply_safe_mode_formatting(formatted_content)
            
            # Step 8: Truncate if needed
            original_length = len(content)
            if original_length > self.config.max_content_length:
                formatted_content = formatted_content[:self.config.max_content_length] + "... [truncated]"
            
            # Create metadata
            metadata = ResponseMetadata(
                timestamp=datetime.utcnow(),
                processing_time=time.time() - start_time,
                content_length=len(formatted_content),
                original_length=original_length,
                confidence_score=context.confidence_score,
                sources=context.session_data.get('sources', []),
                model_used=context.session_data.get('model_used'),
                user_id=context.session_data.get('user_id'),
                session_id=context.session_data.get('session_id'),
                formatting_applied=True,
                layout_confidence=detection_result.confidence,
                content_type_detected=detection_result.content_type.value,
                language_detected=detection_result.metadata.get('language'),
                theme_used=context.theme_mode.value,
                accessibility_features=accessibility_features,
                interactive_elements=self._get_interactive_elements_for_context(context),
                custom_metadata={
                    'detection_metadata': detection_result.metadata,
                    'responsive_metadata': responsive_result.get('responsive_metadata', {}) if self.config.enable_responsive_formatting else {},
                    'theme_metadata': self._get_theme_metadata(context) if self.config.enable_theme_support else {}
                }
            )
            
            # Create result
            result = FormattingResult(
                formatted_content=formatted_content,
                content_type=detection_result.content_type,
                layout_type=(detection_result.layout_hint.layout_type 
                            if detection_result.layout_hint 
                            else self.config.default_layout),
                output_profile=self.config.output_profile,
                metadata=metadata,
                css_classes=css_classes,
                accessibility_features=accessibility_features,
                interactive_elements=self._get_interactive_elements_for_context(context),
                theme_requirements=self._get_theme_requirements(context),
                processing_time=time.time() - start_time,
                confidence_score=context.confidence_score
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            # Update performance metrics
            self._update_performance_metrics(time.time() - start_time)
            
            self.logger.debug(
                f"Response formatted with {detection_result.content_type.value} "
                f"in {time.time() - start_time:.4f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error formatting response: {e}")
            # Return basic result on error
            return FormattingResult(
                formatted_content=content,
                content_type=ContentType.TEXT,
                layout_type=LayoutType.DEFAULT,
                output_profile=self.config.output_profile,
                metadata=ResponseMetadata(
                    processing_time=time.time() - start_time,
                    error=str(e)
                ),
                processing_time=time.time() - start_time
            )
    
    async def format_streaming_chunk(
        self,
        chunk: StreamingChunk,
        context: ResponseContext
    ) -> StreamingChunk:
        """
        Format a streaming chunk with enhanced formatting.
        
        Args:
            chunk: Streaming chunk to format
            context: Response context
            
        Returns:
            Formatted streaming chunk
        """
        try:
            self.logger.debug(f"Formatting streaming chunk {chunk.chunk_id}")
            self._performance_metrics["streaming_chunks"] += 1
            
            # Apply basic formatting to chunk content
            chunk_context = ResponseContext(
                user_query=context.user_query,
                response_content=chunk.content,
                user_preferences=context.user_preferences,
                session_data=context.session_data,
                theme_context=context.theme_context,
                display_context=context.display_context,
                accessibility_level=context.accessibility_level,
                theme_mode=context.theme_mode,
                language=context.language,
                is_streaming=True,
                stream_chunk_id=chunk.chunk_id
            )
            
            # Format the chunk content
            result = await self.format_response(chunk.content, chunk_context)
            
            # Update chunk with formatting information
            formatted_chunk = StreamingChunk(
                chunk_id=chunk.chunk_id,
                content=result.formatted_content,
                state=chunk.state,
                metadata=result.metadata,
                layout_hint=chunk.layout_hint,
                formatting_applied=True,
                is_final_chunk=chunk.is_final_chunk,
                error_message=chunk.error_message,
                progress=chunk.progress
            )
            
            return formatted_chunk
            
        except Exception as e:
            self.logger.error(f"Error formatting streaming chunk: {e}")
            # Return original chunk on error
            return chunk
    
    async def _apply_profile_formatting(self, content: str, context: ResponseContext) -> str:
        """Apply profile-specific formatting to content."""
        profile = self.config.output_profile
        
        if profile == OutputProfile.PLAIN:
            return self._apply_plain_profile(content, context)
        elif profile == OutputProfile.PRETTY:
            return self._apply_pretty_profile(content, context)
        elif profile == OutputProfile.DEV_DOC:
            return self._apply_dev_doc_profile(content, context)
        elif profile == OutputProfile.MINIMAL:
            return self._apply_minimal_profile(content, context)
        elif profile == OutputProfile.VERBOSE:
            return self._apply_verbose_profile(content, context)
        elif profile == OutputProfile.ACCESSIBLE:
            return self._apply_accessible_profile(content, context)
        elif profile == OutputProfile.TECHNICAL:
            return self._apply_technical_profile(content, context)
        elif profile == OutputProfile.CONVERSATIONAL:
            return self._apply_conversational_profile(content, context)
        else:
            return content
    
    def _apply_plain_profile(self, content: str, context: ResponseContext) -> str:
        """Apply plain profile formatting (minimal formatting)."""
        # Remove markdown formatting
        import re
        content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*(.+?)\*', r'\1', content)    # Italic
        content = re.sub(r'`(.+?)`', r'\1', content)      # Code
        content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)  # Headings
        
        # Clean up extra whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    def _apply_pretty_profile(self, content: str, context: ResponseContext) -> str:
        """Apply pretty profile formatting (enhanced formatting)."""
        # Apply basic markdown formatting
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Format headings
            if re.search(r'^#{1,6}\s+', line):
                formatted_lines.append(f"## {line.lstrip('#').strip()}")
            # Format lists
            elif re.search(r'^\s*[-*+]\s+', line):
                formatted_lines.append(f"• {line.lstrip('-*+').strip()}")
            # Format code blocks
            elif line.strip().startswith('```'):
                formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _apply_dev_doc_profile(self, content: str, context: ResponseContext) -> str:
        """Apply developer documentation profile formatting."""
        # Enhance code blocks with line numbers and syntax highlighting hints
        lines = content.split('\n')
        formatted_lines = []
        in_code_block = False
        line_number = 1
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                formatted_lines.append(line)
            elif in_code_block:
                # Add line numbers for code blocks
                formatted_lines.append(f"{line_number:4d} {line}")
                line_number += 1
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _apply_minimal_profile(self, content: str, context: ResponseContext) -> str:
        """Apply minimal profile formatting."""
        # Remove all formatting, keep only basic structure
        import re
        content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)  # Remove bold
        content = re.sub(r'\*(.+?)\*', r'\1', content)    # Remove italic
        content = re.sub(r'`(.+?)`', r'\1', content)      # Remove code formatting
        content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)  # Remove headings
        content = re.sub(r'^\s*[-*+]\s+', '- ', content, flags=re.MULTILINE)  # Simplify lists
        
        # Collapse multiple newlines
        content = re.sub(r'\n{2,}', '\n', content)
        
        return content.strip()
    
    def _apply_verbose_profile(self, content: str, context: ResponseContext) -> str:
        """Apply verbose profile formatting (detailed formatting)."""
        # Add detailed metadata and structure
        lines = content.split('\n')
        formatted_lines = []
        
        # Add section headers
        formatted_lines.append("## Response Details")
        formatted_lines.append(f"**Generated at:** {datetime.utcnow().isoformat()}")
        formatted_lines.append(f"**Content type:** {context.detected_content_type.value if context.detected_content_type else 'Unknown'}")
        formatted_lines.append(f"**Confidence score:** {context.confidence_score:.2f}")
        formatted_lines.append("")
        formatted_lines.append("## Content")
        formatted_lines.extend(lines)
        
        return '\n'.join(formatted_lines)
    
    def _apply_accessible_profile(self, content: str, context: ResponseContext) -> str:
        """Apply accessible profile formatting."""
        # Add accessibility features
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Add ARIA labels for interactive elements
            if '[button:' in line:
                formatted_lines.append(f'<button aria-label="{line.split("[button:")[1].split("]")[0]}">{line.split("[button:")[1].split("]")[1]}</button>')
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _apply_technical_profile(self, content: str, context: ResponseContext) -> str:
        """Apply technical profile formatting."""
        # Enhance technical content with proper formatting
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Format technical terms
            if any(term in line.lower() for term in ['api', 'endpoint', 'function', 'method', 'parameter']):
                formatted_lines.append(f"`{line}`")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _apply_conversational_profile(self, content: str, context: ResponseContext) -> str:
        """Apply conversational profile formatting."""
        # Make content more conversational and friendly
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Add conversational elements
            if '?' in line and len(line) < 100:
                formatted_lines.append(f"💬 {line}")
            elif any(greeting in line.lower() for greeting in ['hello', 'hi', 'hey']):
                formatted_lines.append(f"👋 {line}")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _apply_theme_formatting(self, content: str, context: ResponseContext) -> str:
        """Apply theme-aware formatting to content."""
        # Apply theme-specific CSS classes or styling
        if context.theme_mode == ThemeMode.DARK:
            return f'<div class="dark-theme">{content}</div>'
        elif context.theme_mode == ThemeMode.HIGH_CONTRAST:
            return f'<div class="high-contrast">{content}</div>'
        else:
            return content
    
    def _apply_accessibility_features(self, content: str, context: ResponseContext) -> str:
        """Apply accessibility features to content."""
        # Add accessibility enhancements based on level
        if context.accessibility_level == AccessibilityLevel.FULL:
            # Add comprehensive accessibility features
            content = f'<div role="region" aria-label="Content">{content}</div>'
            content += '\n<div class="accessibility-controls">'
            content += '<button onclick="increaseFontSize()">A+</button>'
            content += '<button onclick="decreaseFontSize()">A-</button>'
            content += '<button onclick="toggleHighContrast()">High Contrast</button>'
            content += '</div>'
        elif context.accessibility_level == AccessibilityLevel.ENHANCED:
            # Add enhanced accessibility features
            content = f'<div class="enhanced-accessibility">{content}</div>'
        
        return content
    
    def _apply_safe_mode_formatting(self, content: str) -> str:
        """Apply safe mode formatting to content."""
        import re
        # Remove potentially dangerous HTML/JS
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'<iframe[^>]*>.*?</iframe>', '', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
        content = re.sub(r'on\w+\s*=', '', content, flags=re.IGNORECASE)
        
        return content
    
    def _map_content_type_to_language(self, content_type: ContentType) -> str:
        """Map content type to syntax highlighting language."""
        mapping = {
            ContentType.PYTHON: 'python',
            ContentType.JAVASCRIPT: 'javascript',
            ContentType.JSON: 'json',
            ContentType.XML: 'xml',
            ContentType.YAML: 'yaml',
            ContentType.SQL: 'sql',
            ContentType.HTML: 'html',
            ContentType.CSS: 'css',
            ContentType.CODE: 'text'  # Generic code
        }
        return mapping.get(content_type, 'text')
    
    def _get_theme_for_context(self, context: ResponseContext) -> str:
        """Get theme name for context."""
        theme_mapping = {
            ThemeMode.LIGHT: 'light',
            ThemeMode.DARK: 'dark',
            ThemeMode.AUTO: 'default',
            ThemeMode.HIGH_CONTRAST: 'high_contrast'
        }
        return theme_mapping.get(context.theme_mode, 'default')
    
    def _convert_highlighted_to_text(self, highlight_result) -> str:
        """Convert syntax highlighting result to plain text."""
        if not hasattr(highlight_result, 'highlighted_lines'):
            return str(highlight_result)
        
        lines = []
        for line in highlight_result.highlighted_lines:
            line_text = ''.join(token.text for token in line.tokens)
            lines.append(line_text)
        
        return '\n'.join(lines)
    
    def _get_interactive_elements_for_context(self, context: ResponseContext) -> List[str]:
        """Get interactive elements for context."""
        elements = []
        
        if context.user_preferences.get('enable_interactive_elements', True):
            if context.detected_content_type == ContentType.CODE:
                elements.extend(['copy-button', 'line-numbers', 'syntax-highlighting'])
            elif context.detected_content_type == ContentType.DATA_TABLE:
                elements.extend(['sortable-columns', 'filterable-rows'])
            elif context.detected_content_type == ContentType.MENU:
                elements.extend(['interactive-menu', 'keyboard-navigation'])
        
        return elements
    
    def _get_accessibility_features_for_context(self, context: ResponseContext) -> List[str]:
        """Get accessibility features for context."""
        features = []
        
        if context.accessibility_level == AccessibilityLevel.BASIC:
            features = ['screen-reader-compatible', 'keyboard-navigable']
        elif context.accessibility_level == AccessibilityLevel.ENHANCED:
            features = ['screen-reader-compatible', 'keyboard-navigable', 'high-contrast', 'large-text']
        elif context.accessibility_level == AccessibilityLevel.FULL:
            features = ['screen-reader-compatible', 'keyboard-navigable', 'high-contrast', 'large-text', 'voice-control']
        elif context.accessibility_level == AccessibilityLevel.SCREEN_READER:
            features = ['screen-reader-optimized', 'structured-markup', 'descriptive-labels']
        
        return features
    
    def _get_theme_requirements(self, context: ResponseContext) -> List[str]:
        """Get theme requirements for context."""
        requirements = []
        
        if context.theme_mode == ThemeMode.DARK:
            requirements.extend(['dark-variables', 'light-text-on-dark'])
        elif context.theme_mode == ThemeMode.HIGH_CONTRAST:
            requirements.extend(['high-contrast-colors', 'clear-borders'])
        
        return requirements
    
    def _get_theme_metadata(self, context: ResponseContext) -> Dict[str, Any]:
        """Get theme metadata for context."""
        metadata = {
            'theme_mode': context.theme_mode.value,
            'auto_detect': context.theme_mode == ThemeMode.AUTO
        }
        
        if context.theme_mode == ThemeMode.AUTO:
            metadata['system_preference'] = context.theme_context.get('prefers_dark_theme', False)
        
        return metadata
    
    def _generate_cache_key(self, content: str, context: ResponseContext) -> str:
        """Generate cache key for formatting result."""
        import hashlib
        key_data = f"{content}:{getattr(context, 'output_profile', 'pretty')}:{getattr(context, 'display_context', DisplayContext.DESKTOP).value}:{getattr(context, 'theme_mode', ThemeMode.AUTO).value}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _cache_result(self, cache_key: str, result: FormattingResult):
        """Cache formatting result."""
        if len(self._format_cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._format_cache))
            del self._format_cache[oldest_key]
        
        self._format_cache[cache_key] = result
    
    def _update_performance_metrics(self, processing_time: float):
        """Update performance metrics."""
        # Update average processing time
        total = self._performance_metrics["total_formatting"]
        current_avg = self._performance_metrics["average_processing_time"]
        self._performance_metrics["average_processing_time"] = (
            (current_avg * (total - 1) + processing_time) / total
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self._performance_metrics.copy()
    
    def reset_performance_metrics(self):
        """Reset performance metrics."""
        self._performance_metrics = {
            "total_formatting": 0,
            "content_detections": 0,
            "syntax_highlights": 0,
            "responsive_adaptations": 0,
            "theme_applications": 0,
            "accessibility_enhancements": 0,
            "streaming_chunks": 0,
            "average_processing_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def clear_cache(self):
        """Clear formatting cache."""
        self._format_cache.clear()
        self.logger.info("Response formatting cache cleared")
    
    def set_output_profile(self, profile: OutputProfile) -> None:
        """Set the output profile for formatting."""
        self.config.output_profile = profile
        self.logger.info(f"Output profile changed to {profile.value}")
    
    def get_output_profile(self) -> OutputProfile:
        """Get the current output profile."""
        return self.config.output_profile


# Global formatter instance
_enhanced_formatter_instance: Optional[EnhancedResponseFormatter] = None


def get_enhanced_response_formatter(config: Optional[FormattingConfig] = None) -> EnhancedResponseFormatter:
    """Get global enhanced response formatter instance."""
    global _enhanced_formatter_instance
    if _enhanced_formatter_instance is None:
        _enhanced_formatter_instance = EnhancedResponseFormatter(config)
    return _enhanced_formatter_instance