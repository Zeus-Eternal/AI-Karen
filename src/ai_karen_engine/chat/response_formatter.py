"""
Pretty Output Layer (Global Response Formatter) for Karen's AI system.

This module provides comprehensive, production-grade response formatting with support for:
- Multiple output profiles (Plain, Pretty, Dev Doc, Minimal, Verbose, etc.)
- Content type detection integration
- Syntax highlighting integration
- Responsive formatting adaptation
- Theme-aware formatting
- Accessibility features
- Streaming support
- Metadata enrichment
- Pydantic models for API integration
"""

import logging
import time
import re
import json
import traceback
import hashlib
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, field

# Import shared models
from .response_formatting_models import (
    OutputProfile, LayoutType, ContentType, DisplayContext, ThemeMode,
    AccessibilityLevel, StreamingState, LayoutHint, ResponseMetadata,
    FormattingPreferences, ResponseContext, StreamingChunk, FormattingResult,
    BaseModel, Field, validator, SyntaxHighlightConfig
)

logger = logging.getLogger(__name__)

# --- Configuration & Specialized Models ---

@dataclass
class FormattingConfig:
    """Configuration for response formatting."""
    output_profile: OutputProfile = OutputProfile.PRETTY
    default_layout: LayoutType = LayoutType.DEFAULT
    enable_markdown: bool = True
    enable_sections: bool = True
    enable_highlights: bool = True
    enable_syntax_highlighting: bool = True
    enable_responsive_formatting: bool = True
    enable_accessibility_features: bool = True
    enable_theme_support: bool = True
    max_content_length: int = 20000
    safe_mode: bool = True
    cache_enabled: bool = True
    performance_monitoring: bool = True


# --- Pydantic Models for API ---

class FormattingRequest(BaseModel):
    """Request model for formatting API."""
    content: str
    output_profile: Optional[str] = None
    layout_type: Optional[str] = None
    display_context: Optional[str] = "desktop"
    theme_mode: Optional[str] = "auto"
    accessibility_level: Optional[str] = "basic"
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    session_data: Dict[str, Any] = Field(default_factory=dict)

class FormattingResponse(BaseModel):
    """Response model for formatting API."""
    formatted_content: str
    content_type: str
    layout_type: str
    output_profile: str
    metadata: Dict[str, Any]
    accessibility_features: List[str] = Field(default_factory=list)
    interactive_elements: List[str] = Field(default_factory=list)
    theme_requirements: List[str] = Field(default_factory=list)
    css_classes: List[str] = Field(default_factory=list)
    processing_time: float
    confidence_score: float

class StreamingFormattingResponse(BaseModel):
    """Response model for streaming formatting API."""
    chunk_id: int
    formatted_content: str
    state: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_final: bool = False
    progress: float = 0.0

# --- Core Formatter ---

class PrettyOutputLayer:
    """
    Unified Pretty Output Layer for formatting AI responses.
    Consolidates legacy PrettyOutputLayer and EnhancedResponseFormatter.
    """
    
    def __init__(self, config: Optional[FormattingConfig] = None):
        self.config = config or FormattingConfig()
        self._interactive_elements_enabled = True
        
        # Subsystems (lazy initialized)
        self.content_detector = None
        self.syntax_highlighter = None
        self.responsive_formatter = None
        
        # Performance metrics
        self._performance_metrics = {
            "format_calls": 0,
            "layout_detection_time": 0.0,
            "formatting_time": 0.0,
            "errors": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Cache for formatted results
        self._format_cache = {}
        self._cache_max_size = 500
        
        # Layout Detectors & Formatters
        self._init_layout_registry()
        self._init_profile_registry()
        
        logger.info(f"PrettyOutputLayer consolidated instance initialized with profile: {self.config.output_profile.value}")

    def _init_layout_registry(self):
        """Initialize registry of layout-specific detectors and formatters."""
        self._layout_detectors = {
            LayoutType.MENU: self._detect_menu_layout,
            LayoutType.MOVIE_LIST: self._detect_movie_list_layout,
            LayoutType.BULLET_LIST: self._detect_bullet_list_layout,
            LayoutType.SYSTEM_STATUS: self._detect_system_status_layout,
        }
        self._layout_formatters = {
            LayoutType.DEFAULT: self._format_default_layout,
            LayoutType.MENU: self._format_menu_layout,
            LayoutType.MOVIE_LIST: self._format_movie_list_layout,
            LayoutType.BULLET_LIST: self._format_bullet_list_layout,
            LayoutType.SYSTEM_STATUS: self._format_system_status_layout,
            LayoutType.CODE_BLOCK: self._format_code_block_layout,
            LayoutType.TABLE: self._format_table_layout,
            LayoutType.STEPS: self._format_steps_layout,
        }

    def _init_profile_registry(self):
        """Initialize registry of profile-specific formatters."""
        self._profile_formatters = {
            OutputProfile.PLAIN: self._apply_plain_profile,
            OutputProfile.PRETTY: self._apply_pretty_profile,
            OutputProfile.DEV_DOC: self._apply_dev_doc_profile,
            OutputProfile.MINIMAL: self._apply_minimal_profile,
            OutputProfile.VERBOSE: self._apply_verbose_profile,
            OutputProfile.ACCESSIBLE: self._apply_accessible_profile,
            OutputProfile.TECHNICAL: self._apply_technical_profile,
            OutputProfile.CONVERSATIONAL: self._apply_conversational_profile,
        }

    async def _ensure_subsystems(self):
        """Lazy load and initialize subsystems."""
        if not self.content_detector:
            try:
                from .content_type_detector import get_content_detector
                self.content_detector = get_content_detector()
            except Exception as e:
                logger.warning(f"Could not load content_detector: {e}")
        
        if not self.syntax_highlighter:
            try:
                from .syntax_highlighter import get_syntax_highlighter
                self.syntax_highlighter = get_syntax_highlighter()
            except Exception as e:
                logger.warning(f"Could not load syntax_highlighter: {e}")
                
        if not self.responsive_formatter:
            try:
                from .responsive_formatter import get_responsive_formatter
                self.responsive_formatter = get_responsive_formatter()
            except Exception as e:
                logger.warning(f"Could not load responsive_formatter: {e}")

    # --- Public API ---

    async def format_response(
        self,
        response_content: str,
        context: ResponseContext
    ) -> Dict[str, Any]:
        """Primary entry point for formatting a response."""
        start_time = time.time()
        self._performance_metrics["format_calls"] += 1
        
        try:
            await self._ensure_subsystems()
            
            # Check Cache
            cache_key = self._generate_cache_key(response_content, context)
            if self.config.cache_enabled and cache_key in self._format_cache:
                self._performance_metrics["cache_hits"] += 1
                return self._format_cache[cache_key]
            
            self._performance_metrics["cache_misses"] += 1

            # 1. Sanitize & Truncate
            if self.config.safe_mode:
                response_content = self._sanitize_content(response_content)
            
            original_length = len(response_content)
            if original_length > self.config.max_content_length:
                response_content = response_content[:self.config.max_content_length] + "... [truncated]"

            # 2. Content Type Detection
            detected_type = ContentType.TEXT
            confidence = 0.5
            layout_hint = LayoutHint(layout_type=self.config.default_layout)
            
            if self.content_detector:
                detection = await self.content_detector.detect_content_type(
                    response_content,
                    user_query=context.user_query
                )
                detected_type = self._map_to_content_type_enum(detection.content_type)
                confidence = detection.confidence
                if hasattr(detection, 'layout_hint') and detection.layout_hint:
                    layout_hint = LayoutHint(
                        layout_type=self._map_to_layout_type_enum(detection.layout_hint.layout_type),
                        confidence=detection.layout_hint.confidence,
                        parameters=detection.layout_hint.parameters if hasattr(detection.layout_hint, 'parameters') else {}
                    )

            # 3. Layout Detection (Fallback)
            if layout_hint.layout_type == LayoutType.DEFAULT:
                layout_hint = self._detect_layout(response_content, context)

            # 4. Preliminary Layout Formatting
            formatted_content = self._format_by_layout(response_content, layout_hint, context)

            # 5. Syntax Highlighting
            if (self.config.enable_syntax_highlighting and self.syntax_highlighter and 
                detected_type in [ContentType.CODE, ContentType.PYTHON, ContentType.JAVASCRIPT]):
                try:
                    highlight_result = await self.syntax_highlighter.highlight_code(
                        formatted_content, 
                        SyntaxHighlightConfig(language=detected_type.value)
                    )
                    formatted_content = getattr(highlight_result, 'highlighted_content', formatted_content)
                except Exception as e:
                    logger.warning(f"Highlighting failed: {e}")

            # 6. Responsive Formatting
            css_classes = []
            accessibility_features = []
            if self.config.enable_responsive_formatting and self.responsive_formatter:
                try:
                    from .responsive_formatter import ResponsiveConfig
                    resp_result = await self.responsive_formatter.format_responsive(
                        formatted_content, 
                        ResponsiveConfig(display_context=context.display_context),
                        layout_hint.layout_type
                    )
                    formatted_content = resp_result.get('content', formatted_content)
                    css_classes = resp_result.get('css_classes', [])
                    accessibility_features = resp_result.get('accessibility_adaptations', [])
                except Exception as e:
                    logger.warning(f"Responsive formatting failed: {e}")

            # 7. Profile Specific Formatting
            formatted_content = await self._apply_profile_formatting(formatted_content, context)

            # 8. Theme and Accessibility Wrappers
            if self.config.enable_theme_support:
                formatted_content = self._apply_theme_wrappers(formatted_content, context)
            if self.config.enable_accessibility_features:
                formatted_content = self._apply_accessibility_wrappers(formatted_content, context)

            # Build Result
            proc_time = time.time() - start_time
            final_output = {
                "content": formatted_content,
                "layout_type": layout_hint.layout_type.value,
                "output_profile": self.config.output_profile.value,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "processing_time": proc_time,
                    "content_length": len(formatted_content),
                    "original_length": original_length,
                    "confidence_score": confidence,
                    "layout_confidence": layout_hint.confidence,
                    "content_type_detected": detected_type.value,
                    "theme_used": context.theme_mode.value,
                    "accessibility_features": accessibility_features,
                    "formatting_applied": True
                }
            }
            
            if self.config.cache_enabled:
                self._cache_result(cache_key, final_output)
            
            return final_output

        except Exception as e:
            self._performance_metrics["errors"] += 1
            logger.error(f"Formatting failed: {e}\n{traceback.format_exc()}")
            return {
                "content": response_content,
                "layout_type": LayoutType.DEFAULT.value,
                "output_profile": self.config.output_profile.value,
                "metadata": {"error": str(e), "formatting_applied": False, "processing_time": time.time() - start_time}
            }

    async def format_streaming_chunk(
        self,
        chunk: StreamingChunk,
        context: ResponseContext
    ) -> StreamingChunk:
        """Format a single chunk in a stream."""
        try:
            chunk_content = chunk.content
            if self.config.output_profile == OutputProfile.PLAIN:
                chunk_content = self._sanitize_content(chunk_content)
            
            chunk.content = chunk_content
            chunk.formatting_applied = True
            return chunk
        except Exception as e:
            logger.warning(f"Streaming chunk formatting failed: {e}")
            return chunk

    # --- Helper Logic ---

    def _sanitize_content(self, content: str) -> str:
        if not content: return ""
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        content = re.sub(r'on\w+\s*=', '', content, flags=re.IGNORECASE)
        return content.strip()

    def _detect_layout(self, content: str, context: ResponseContext) -> LayoutHint:
        best_layout = LayoutType.DEFAULT
        best_confidence = 0.0
        for l_type, detector in self._layout_detectors.items():
            hint = detector(content, context)
            if hint.confidence > best_confidence:
                best_layout = l_type
                best_confidence = hint.confidence
        return LayoutHint(layout_type=best_layout, confidence=best_confidence) if best_confidence > 0.3 else LayoutHint(layout_type=LayoutType.DEFAULT)

    def _format_by_layout(self, content: str, hint: LayoutHint, context: ResponseContext) -> str:
        formatter = self._layout_formatters.get(hint.layout_type, self._format_default_layout)
        return formatter(content, hint.parameters, context)

    async def _apply_profile_formatting(self, content: str, context: ResponseContext) -> str:
        formatter = self._profile_formatters.get(self.config.output_profile, self._apply_pretty_profile)
        return formatter(content, context)

    # --- Layout Implementations ---
    def _detect_menu_layout(self, content: str, context: ResponseContext) -> LayoutHint:
        # Menus often have numbered options with trailing dots or parentheses
        count = len(re.findall(r'^\s*\d+\.\s+', content, re.MULTILINE))
        lines = len([l for l in content.split('\n') if l.strip()])
        confidence = count/max(lines, 1) if lines > 0 else 0
        return LayoutHint(LayoutType.MENU, confidence)

    def _detect_movie_list_layout(self, content: str, context: ResponseContext) -> LayoutHint:
        k = ['director', 'starring', 'genre', 'rating', 'release', 'film']
        s = sum(1 for kw in k if kw in content.lower())
        return LayoutHint(LayoutType.MOVIE_LIST, min(s/len(k), 1.0))

    def _detect_bullet_list_layout(self, content: str, context: ResponseContext) -> LayoutHint:
        c = len(re.findall(r'^\s*[-*+]\s+', content, re.MULTILINE))
        l = len(content.split('\n'))
        return LayoutHint(LayoutType.BULLET_LIST, min(c/max(l,1), 1.0))

    def _detect_system_status_layout(self, content: str, context: ResponseContext) -> LayoutHint:
        k = ['status', 'online', 'active', 'cpu', 'memory', 'disk']
        s = sum(1 for kw in k if kw in content.lower())
        return LayoutHint(LayoutType.SYSTEM_STATUS, min(s/len(k),1.0))

    def _format_default_layout(self, content: str, params: dict, context: ResponseContext) -> str: return content
    def _format_menu_layout(self, content: str, params: dict, context: ResponseContext) -> str: return f'<div class="ui-menu">\n{content}\n</div>'
    def _format_movie_list_layout(self, content: str, params: dict, context: ResponseContext) -> str: return f'<div class="ui-movie-list">\n{content}\n</div>'
    def _format_bullet_list_layout(self, content: str, params: dict, context: ResponseContext) -> str: return content
    def _format_system_status_layout(self, content: str, params: dict, context: ResponseContext) -> str: return f'<div class="ui-system-status">\n{content}\n</div>'
    
    def _format_code_block_layout(self, content: str, params: dict, context: ResponseContext) -> str:
        """Format content as a code block, adding markdown triple backticks if missing."""
        if '```' in content:
            return content
            
        language = params.get('language', 'text')
        
        # Map specific types to markdown language identifiers
        lang_map = {
            ContentType.HTML: 'html',
            ContentType.PYTHON: 'python',
            ContentType.JAVASCRIPT: 'javascript',
            ContentType.JSON: 'json',
            ContentType.XML: 'xml',
            ContentType.CSS: 'css',
            ContentType.SQL: 'sql',
            ContentType.YAML: 'yaml',
            'html': 'html',
            'python': 'python',
            'javascript': 'javascript',
            'js': 'javascript',
            'json': 'json',
            'xml': 'xml',
            'yaml': 'yaml',
            'css': 'css',
            'sql': 'sql'
        }
        
        # Determine the language identifier for backticks
        lang_id = lang_map.get(language, 'text')
        if not isinstance(lang_id, str):
            # Fallback if it's an enum but not in map (shouldn't happen with updated map)
            lang_id = getattr(language, 'value', str(language))
        
        return f"```{lang_id}\n{content.strip()}\n```"

    def _format_table_layout(self, content: str, params: dict, context: ResponseContext) -> str:
        return f'<div class="ui-table-container">\n{content}\n</div>'

    def _format_steps_layout(self, content: str, params: dict, context: ResponseContext) -> str:
        return f'<div class="ui-steps-container">\n{content}\n</div>'

    # --- Profile Implementations ---
    def _apply_plain_profile(self, content: str, context: ResponseContext) -> str:
        content = re.sub(r'#{1,6}\s*', '', content)
        content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
        content = re.sub(r'\*(.+?)\*', r'\1', content)
        return content.strip()

    def _apply_pretty_profile(self, content: str, context: ResponseContext) -> str: return content
    def _apply_dev_doc_profile(self, content: str, context: ResponseContext) -> str: return f"### Technical Response\n{content}"
    def _apply_minimal_profile(self, content: str, context: ResponseContext) -> str: return content.replace('\n\n', '\n').strip()
    def _apply_verbose_profile(self, content: str, context: ResponseContext) -> str: return f"Detailed Response:\n{content}\n[Words: {len(content.split())}]"
    def _apply_accessible_profile(self, content: str, context: ResponseContext) -> str: return f'<section aria-label="AI response">{content}</section>'
    def _apply_technical_profile(self, content: str, context: ResponseContext) -> str: return f"```technical\n{content}\n```"
    def _apply_conversational_profile(self, content: str, context: ResponseContext) -> str: return f"Here's what I found: {content}"

    # --- Wrappers ---
    def _apply_theme_wrappers(self, content: str, context: ResponseContext) -> str:
        if context.theme_mode == ThemeMode.DARK: return f'<div class="theme-dark">{content}</div>'
        return content
    def _apply_accessibility_wrappers(self, content: str, context: ResponseContext) -> str:
        if context.accessibility_level != AccessibilityLevel.BASIC:
            return f'<div role="article" class="acc-{context.accessibility_level.value}">{content}</div>'
        return content

    # --- Utilities ---
    def _generate_cache_key(self, content: str, context: ResponseContext) -> str:
        key_data = f"{content}:{context.user_query}:{self.config.output_profile.value}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _cache_result(self, key: str, result: Any):
        if len(self._format_cache) > self._cache_max_size:
            self._format_cache.pop(next(iter(self._format_cache)))
        self._format_cache[key] = result

    def _map_to_content_type_enum(self, value: Any) -> ContentType:
        if isinstance(value, ContentType): return value
        try: return ContentType(str(value).lower())
        except: return ContentType.TEXT

    def _map_to_layout_type_enum(self, value: Any) -> LayoutType:
        if isinstance(value, LayoutType): return value
        try: return LayoutType(str(value).lower())
        except: return LayoutType.DEFAULT

    # Compatibility methods
    def set_output_profile(self, profile: Union[OutputProfile, str]) -> None:
        if isinstance(profile, str): profile = OutputProfile(profile.lower())
        self.config.output_profile = profile
    def get_output_profile(self) -> OutputProfile: return self.config.output_profile
    def force_layout_type(self, layout_type: Union[LayoutType, str]) -> None:
        if isinstance(layout_type, str): layout_type = LayoutType(layout_type.lower())
        self.config.default_layout = layout_type
    def reset_layout_detection(self) -> None: self.config.default_layout = LayoutType.DEFAULT
    def enable_interactive_elements(self, enabled: bool = True) -> None: self._interactive_elements_enabled = enabled
    def get_performance_metrics(self) -> Dict[str, Any]: return self._performance_metrics
