"""
Syntax Highlighting System for Code Blocks and Technical Content

This module provides comprehensive syntax highlighting for multiple programming languages
and technical content types with support for different themes and accessibility.
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from .response_formatting_models import (
        SyntaxHighlightConfig, ThemeMode, AccessibilityLevel
    )
except ImportError:
    # Fallback imports for circular dependency
    from enum import Enum
    
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
    
    class SyntaxHighlightConfig:
        def __init__(self, language, theme="default", line_numbers=True,
                     highlight_lines=None, wrap_lines=True, tab_size=4,
                     show_whitespace=False, show_line_endings=False):
            self.language = language
            self.theme = theme
            self.line_numbers = line_numbers
            self.highlight_lines = highlight_lines or []
            self.wrap_lines = wrap_lines
            self.tab_size = tab_size
            self.show_whitespace = show_whitespace
            self.show_line_endings = show_line_endings

logger = logging.getLogger(__name__)


class HighlightTheme(Enum):
    """Syntax highlighting themes."""
    DEFAULT = "default"
    DARK = "dark"
    LIGHT = "light"
    HIGH_CONTRAST = "high_contrast"
    MONOCHROME = "monochrome"
    COLORBLIND_FRIENDLY = "colorblind_friendly"
    GITHUB = "github"
    VS_CODE = "vs_code"
    PYGMENTS_DEFAULT = "pygments_default"


@dataclass
class HighlightedToken:
    """A highlighted token with styling information."""
    text: str
    token_type: str
    color: Optional[str] = None
    background_color: Optional[str] = None
    font_weight: Optional[str] = None
    font_style: Optional[str] = None  # italic, underline, etc.
    css_class: Optional[str] = None


@dataclass
class HighlightedLine:
    """A line of highlighted code."""
    tokens: List[HighlightedToken]
    line_number: int
    is_highlighted: bool = False
    background_color: Optional[str] = None


@dataclass
class HighlightResult:
    """Result of syntax highlighting operation."""
    highlighted_lines: List[HighlightedLine]
    language: str
    theme_used: str
    total_lines: int
    has_line_numbers: bool
    css_classes: List[str]
    accessibility_features: List[str]
    metadata: Dict[str, Any]


class SyntaxHighlighter:
    """
    Advanced syntax highlighting system with multi-language support.
    
    This class provides:
    - Multi-language syntax highlighting
    - Theme support (light, dark, high contrast, etc.)
    - Accessibility features
    - Line numbering
    - Custom highlighting rules
    - Performance optimization
    """
    
    def __init__(self):
        """Initialize the syntax highlighter."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize language definitions
        self._init_language_definitions()
        
        # Initialize theme definitions
        self._init_theme_definitions()
        
        # Initialize accessibility features
        self._init_accessibility_features()
        
        # Performance metrics
        self._performance_metrics = {
            "total_highlights": 0,
            "total_lines_processed": 0,
            "average_time_per_line": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # Simple cache for highlighted content
        self._highlight_cache = {}
        self._cache_max_size = 1000
        
        self.logger.info("SyntaxHighlighter initialized")
    
    def _init_language_definitions(self):
        """Initialize language syntax definitions."""
        self.language_definitions = {
            'python': {
                'keywords': [
                    'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
                    'del', 'elif', 'else', 'except', 'finally', 'for', 'from',
                    'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal',
                    'not', 'or', 'pass', 'raise', 'return', 'try', 'while',
                    'with', 'yield', 'async', 'await'
                ],
                'builtins': [
                    'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes',
                    'callable', 'chr', 'classmethod', 'compile', 'complex',
                    'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval',
                    'exec', 'filter', 'float', 'format', 'frozenset',
                    'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex',
                    'id', 'input', 'int', 'isinstance', 'issubclass', 'iter',
                    'len', 'list', 'locals', 'map', 'max', 'memoryview',
                    'min', 'next', 'object', 'oct', 'open', 'ord', 'pow',
                    'print', 'property', 'range', 'repr', 'reversed', 'round',
                    'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str',
                    'sum', 'super', 'tuple', 'type', 'vars', 'zip'
                ],
                'operators': [
                    r'\+', r'-', r'\*', r'/', r'%', r'\*\*', r'//', r'=',
                    r'==', r'!=', r'<', r'>', r'<=', r'>=', r'&', r'\|', r'\^',
                    r'<<', r'>>', r'\+=', r'-=', r'\*=', r'/=', r'%='
                ],
                'delimiters': [r'\(', r'\)', r'\[', r'\]', r'\{', r'\}', r':', r','],
                'strings': [
                    r'""".*?"""',  # Triple quotes
                    r"'''.*?'''",  # Triple single quotes
                    r'".*?"',  # Double quotes
                    r"'.*?'",  # Single quotes
                    r'r".*?"',  # Raw strings
                    r"r'.*?'",  # Raw single quotes
                ],
                'comments': [r'#.*$', r'#.*$'],
                'numbers': [r'\b\d+\.?\d*\b', r'\b0x[0-9a-fA-F]+\b'],
                'functions': [r'\b[a-zA-Z_][a-zA-Z0-9_]*(?=\s*\()'],
            },
            'javascript': {
                'keywords': [
                    'break', 'case', 'catch', 'class', 'const', 'continue',
                    'debugger', 'default', 'delete', 'do', 'else', 'export',
                    'extends', 'finally', 'for', 'function', 'if', 'import',
                    'in', 'instanceof', 'let', 'new', 'return', 'super',
                    'switch', 'this', 'throw', 'try', 'typeof', 'var',
                    'void', 'while', 'with', 'yield', 'async', 'await'
                ],
                'builtins': [
                    'Array', 'Boolean', 'Date', 'Error', 'Function', 'JSON',
                    'Math', 'Number', 'Object', 'RegExp', 'String',
                    'console', 'document', 'window', 'setTimeout', 'setInterval'
                ],
                'operators': [
                    r'\+', r'-', r'\*', r'/', r'%', r'\*\*', r'=',
                    r'==', r'===', r'!=', r'!==', r'<', r'>', r'<=', r'>=',
                    r'&&', r'\|\|', r'!', r'\+\+', r'--', r'\+=', r'-='
                ],
                'delimiters': [r'\(', r'\)', r'\[', r'\]', r'\{', r'\}', r':', r',', r';'],
                'strings': [
                    r'`.*?`',  # Template literals
                    r'".*?"',  # Double quotes
                    r"'.*?'",  # Single quotes
                ],
                'comments': [r'//.*$', r'/\*.*?\*/'],
                'numbers': [r'\b\d+\.?\d*\b', r'\b0x[0-9a-fA-F]+\b'],
                'functions': [r'\b[a-zA-Z_$][a-zA-Z0-9_$]*(?=\s*\()'],
            },
            'json': {
                'keywords': ['true', 'false', 'null'],
                'operators': [r':', r','],
                'delimiters': [r'\{', r'\}', r'\[', r'\]'],
                'strings': [r'".*?"', r"'.*?'"],
                'numbers': [r'\b-?\d+\.?\d*\b'],
                'comments': [],  # JSON doesn't support comments
                'functions': [],
            },
            'sql': {
                'keywords': [
                    'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE',
                    'CREATE', 'DROP', 'ALTER', 'TABLE', 'INDEX', 'VIEW',
                    'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER',
                    'GROUP', 'BY', 'ORDER', 'HAVING', 'LIMIT', 'OFFSET',
                    'UNION', 'DISTINCT', 'AS', 'ON', 'AND', 'OR', 'NOT',
                    'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'IS', 'NULL'
                ],
                'builtins': ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'CONCAT'],
                'operators': [r'=', r'\(', r'\)', r'<', r'>', r'=', r'!=', r'LIKE'],
                'delimiters': [r',', r';'],
                'strings': [r"'.*?'", r'".*?"'],
                'comments': [r'--.*$', r'/\*.*?\*/'],
                'numbers': [r'\b\d+\.?\d*\b'],
                'functions': [r'\b[a-zA-Z_][a-zA-Z0-9_]*(?=\s*\()'],
            },
            'html': {
                'keywords': [],
                'builtins': [],
                'operators': [],
                'delimiters': [r'<', r'>', r'=', r'/'],
                'strings': [r'".*?"', r"'.*?'"],
                'comments': [r'<!--.*?-->'],
                'numbers': [],
                'functions': [],
                'tags': [
                    r'</?[a-zA-Z][a-zA-Z0-9]*',  # HTML tags
                    r'[a-zA-Z-]+(?=\s*=)',  # Attributes
                ]
            },
            'css': {
                'keywords': [
                    'important', 'inherit', 'initial', 'unset', 'revert',
                    'auto', 'none', 'hidden', 'visible', 'absolute', 'relative',
                    'fixed', 'static', 'block', 'inline', 'flex', 'grid'
                ],
                'builtins': [
                    'color', 'background', 'border', 'margin', 'padding',
                    'width', 'height', 'font', 'text', 'display'
                ],
                'operators': [r':', r';', r'{', r'}', r','],
                'delimiters': [r'\{', r'\}', r':', r';'],
                'strings': [r'".*?"', r"'.*?'"],
                'comments': [r'/\*.*?\*/'],
                'numbers': [r'\b\d+\.?\d*(px|em|rem|%|vh|vw|deg|s|ms)\b'],
                'functions': [r'[a-zA-Z-]+(?=\s*\()'],
            }
        }
    
    def _init_theme_definitions(self):
        """Initialize theme definitions for syntax highlighting."""
        self.theme_definitions = {
            HighlightTheme.DEFAULT: {
                'keyword': {'color': '#0000ff', 'font_weight': 'bold'},
                'builtin': {'color': '#008000'},
                'string': {'color': '#008000'},
                'comment': {'color': '#808080', 'font_style': 'italic'},
                'number': {'color': '#000080'},
                'operator': {'color': '#666666'},
                'function': {'color': '#000080', 'font_weight': 'bold'},
                'delimiter': {'color': '#000000'},
                'tag': {'color': '#0000ff', 'font_weight': 'bold'},
                'attribute': {'color': '#ff0000'},
                'background': '#ffffff',
                'text': '#000000',
                'line_number': {'color': '#999999', 'background_color': '#f5f5f5'},
                'highlight': {'background_color': '#ffff00'},
            },
            HighlightTheme.DARK: {
                'keyword': {'color': '#569cd6', 'font_weight': 'bold'},
                'builtin': {'color': '#4ec9b0'},
                'string': {'color': '#ce9178'},
                'comment': {'color': '#6a9955', 'font_style': 'italic'},
                'number': {'color': '#b5cea8'},
                'operator': {'color': '#d4d4d4'},
                'function': {'color': '#dcdcaa', 'font_weight': 'bold'},
                'delimiter': {'color': '#d4d4d4'},
                'tag': {'color': '#569cd6', 'font_weight': 'bold'},
                'attribute': {'color': '#9cdcfe'},
                'background': '#1e1e1e',
                'text': '#d4d4d4',
                'line_number': {'color': '#858585', 'background_color': '#2d2d30'},
                'highlight': {'background_color': '#264f78'},
            },
            HighlightTheme.HIGH_CONTRAST: {
                'keyword': {'color': '#0000ff', 'font_weight': 'bold'},
                'builtin': {'color': '#008000', 'font_weight': 'bold'},
                'string': {'color': '#ff0000'},
                'comment': {'color': '#008080', 'font_style': 'italic'},
                'number': {'color': '#000080', 'font_weight': 'bold'},
                'operator': {'color': '#000000'},
                'function': {'color': '#800080', 'font_weight': 'bold'},
                'delimiter': {'color': '#000000'},
                'tag': {'color': '#0000ff', 'font_weight': 'bold'},
                'attribute': {'color': '#ff0000'},
                'background': '#ffffff',
                'text': '#000000',
                'line_number': {'color': '#000000', 'background_color': '#cccccc'},
                'highlight': {'background_color': '#ffff00', 'color': '#000000'},
            },
            HighlightTheme.COLORBLIND_FRIENDLY: {
                'keyword': {'color': '#0066cc', 'font_weight': 'bold'},
                'builtin': {'color': '#006600'},
                'string': {'color': '#cc6600'},
                'comment': {'color': '#666666', 'font_style': 'italic'},
                'number': {'color': '#006666'},
                'operator': {'color': '#333333'},
                'function': {'color': '#006666', 'font_weight': 'bold'},
                'delimiter': {'color': '#333333'},
                'tag': {'color': '#0066cc', 'font_weight': 'bold'},
                'attribute': {'color': '#cc6600'},
                'background': '#ffffff',
                'text': '#000000',
                'line_number': {'color': '#666666', 'background_color': '#f0f0f0'},
                'highlight': {'background_color': '#cccc00'},
            }
        }
    
    def _init_accessibility_features(self):
        """Initialize accessibility features for syntax highlighting."""
        self.accessibility_features = {
            AccessibilityLevel.BASIC: {
                'high_contrast': False,
                'large_text': False,
                'screen_reader_optimized': False,
                'focus_indicators': True,
                'color_blind_friendly': False
            },
            AccessibilityLevel.ENHANCED: {
                'high_contrast': True,
                'large_text': False,
                'screen_reader_optimized': False,
                'focus_indicators': True,
                'color_blind_friendly': True
            },
            AccessibilityLevel.FULL: {
                'high_contrast': True,
                'large_text': True,
                'screen_reader_optimized': True,
                'focus_indicators': True,
                'color_blind_friendly': True
            },
            AccessibilityLevel.SCREEN_READER: {
                'high_contrast': True,
                'large_text': True,
                'screen_reader_optimized': True,
                'focus_indicators': True,
                'color_blind_friendly': False,
                'minimal_styling': True
            }
        }
    
    async def highlight_code(
        self,
        code: str,
        config: SyntaxHighlightConfig
    ) -> HighlightResult:
        """
        Highlight code syntax with specified configuration.
        
        Args:
            code: Code to highlight
            config: Syntax highlighting configuration
            
        Returns:
            HighlightResult with highlighted lines and metadata
        """
        import time
        start_time = time.time()
        
        try:
            self.logger.debug(f"Highlighting {len(code)} characters of {config.language} code")
            
            # Check cache first
            cache_key = self._generate_cache_key(code, config)
            if cache_key in self._highlight_cache:
                self._performance_metrics["cache_hits"] += 1
                cached_result = self._highlight_cache[cache_key]
                self.logger.debug("Using cached highlighting result")
                return cached_result
            
            self._performance_metrics["cache_misses"] += 1
            
            # Get language definition
            lang_def = self.language_definitions.get(config.language.lower())
            if not lang_def:
                self.logger.warning(f"Language {config.language} not supported, using plain text")
                return self._create_plain_result(code, config)
            
            # Get theme definition
            theme = self._get_theme_for_config(config)
            
            # Split code into lines
            lines = code.split('\n')
            
            # Highlight each line
            highlighted_lines = []
            for i, line in enumerate(lines, 1):
                highlighted_line = await self._highlight_line(
                    line, i, lang_def, theme, config
                )
                highlighted_lines.append(highlighted_line)
            
            # Generate CSS classes
            css_classes = self._generate_css_classes(config.language, theme)
            
            # Generate accessibility features
            accessibility_features = self._get_accessibility_features_for_level(
                getattr(config, 'accessibility_level', AccessibilityLevel.BASIC)
            )
            
            # Create result
            result = HighlightResult(
                highlighted_lines=highlighted_lines,
                language=config.language,
                theme_used=theme.get('name', 'default'),
                total_lines=len(lines),
                has_line_numbers=config.line_numbers,
                css_classes=css_classes,
                accessibility_features=accessibility_features,
                metadata={
                    'processing_time': time.time() - start_time,
                    'cache_used': False,
                    'language_detected': True,
                    'theme_adapted': True
                }
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            # Update performance metrics
            self._update_performance_metrics(len(lines), time.time() - start_time)
            
            self.logger.debug(
                f"Highlighted {len(lines)} lines in {time.time() - start_time:.4f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error highlighting code: {e}")
            # Return plain result on error
            return self._create_plain_result(code, config, error=str(e))
    
    async def _highlight_line(
        self,
        line: str,
        line_number: int,
        lang_def: Dict[str, Any],
        theme: Dict[str, Any],
        config: SyntaxHighlightConfig
    ) -> HighlightedLine:
        """Highlight a single line of code."""
        tokens = []
        remaining_text = line
        position = 0
        
        # Check if line should be highlighted
        is_highlighted = line_number in config.highlight_lines
        
        while position < len(remaining_text):
            # Find next token
            token, token_type, advance = await self._find_next_token(
                remaining_text[position:], lang_def
            )
            
            if token:
                # Get styling for token type
                styling = theme.get(token_type, {})
                
                # Create highlighted token
                highlighted_token = HighlightedToken(
                    text=token,
                    token_type=token_type,
                    color=styling.get('color'),
                    background_color=styling.get('background_color'),
                    font_weight=styling.get('font_weight'),
                    font_style=styling.get('font_style'),
                    css_class=f"token-{token_type}"
                )
                tokens.append(highlighted_token)
                
                position += advance
            else:
                # No more tokens, add remaining text as plain
                if remaining_text[position:]:
                    tokens.append(HighlightedToken(
                        text=remaining_text[position:],
                        token_type='text',
                        color=theme.get('text'),
                        css_class='token-text'
                    ))
                break
        
        # Determine background color for highlighted lines
        background_color = None
        if is_highlighted:
            background_color = theme.get('highlight', {}).get('background_color')
        
        return HighlightedLine(
            tokens=tokens,
            line_number=line_number,
            is_highlighted=is_highlighted,
            background_color=background_color
        )
    
    async def _find_next_token(
        self,
        text: str,
        lang_def: Dict[str, Any]
    ) -> Tuple[str, str, int]:
        """Find the next token in text based on language definition."""
        # Define token priorities (higher number = higher priority)
        token_priorities = {
            'comment': 10,
            'string': 9,
            'keyword': 8,
            'builtin': 7,
            'function': 6,
            'number': 5,
            'operator': 4,
            'delimiter': 3,
            'tag': 2,
            'attribute': 1,
            'text': 0
        }
        
        best_match = None
        best_priority = -1
        best_length = 0
        
        # Check each token type
        for token_type, patterns in lang_def.items():
            if not patterns:
                continue
                
            priority = token_priorities.get(token_type, 0)
            
            # Skip if lower priority than current best
            if priority < best_priority:
                continue
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and match.start() == 0:
                    match_length = len(match.group())
                    
                    # Prefer longer matches for same priority
                    if priority > best_priority or (
                        priority == best_priority and match_length > best_length
                    ):
                        best_match = (match.group(), token_type, match_length)
                        best_priority = priority
                        best_length = match_length
        
        return best_match if best_match else (text[0], 'text', 1)
    
    def _get_theme_for_config(self, config: SyntaxHighlightConfig) -> Dict[str, Any]:
        """Get theme definition based on configuration."""
        theme_name = config.theme.lower()
        
        # Map theme mode to theme definition
        theme_mapping = {
            'default': HighlightTheme.DEFAULT,
            'dark': HighlightTheme.DARK,
            'light': HighlightTheme.DEFAULT,
            'high_contrast': HighlightTheme.HIGH_CONTRAST,
            'monochrome': HighlightTheme.HIGH_CONTRAST,
            'colorblind_friendly': HighlightTheme.COLORBLIND_FRIENDLY,
            'github': HighlightTheme.DEFAULT,
            'vs_code': HighlightTheme.DARK,
            'pygments_default': HighlightTheme.DEFAULT
        }
        
        theme_enum = theme_mapping.get(theme_name, HighlightTheme.DEFAULT)
        theme_def = self.theme_definitions.get(theme_enum, self.theme_definitions[HighlightTheme.DEFAULT])
        theme_def['name'] = theme_name
        
        return theme_def
    
    def _generate_css_classes(self, language: str, theme: Dict[str, Any]) -> List[str]:
        """Generate CSS classes for syntax highlighting."""
        base_classes = [
            f"syntax-highlighter",
            f"language-{language.lower()}",
            f"theme-{theme.get('name', 'default')}"
        ]
        
        token_classes = []
        for token_type in theme.keys():
            if token_type not in ['background', 'text']:
                token_classes.append(f"token-{token_type}")
        
        return base_classes + token_classes
    
    def _get_accessibility_features_for_level(
        self, level: AccessibilityLevel
    ) -> List[str]:
        """Get accessibility features for the specified level."""
        features = self.accessibility_features.get(level, {})
        return [feature for feature, enabled in features.items() if enabled]
    
    def _create_plain_result(
        self,
        code: str,
        config: SyntaxHighlightConfig,
        error: Optional[str] = None
    ) -> HighlightResult:
        """Create a plain (unhighlighted) result."""
        lines = code.split('\n')
        highlighted_lines = []
        
        for i, line in enumerate(lines, 1):
            # Create plain token for entire line
            token = HighlightedToken(
                text=line,
                token_type='text',
                css_class='token-text'
            )
            
            highlighted_line = HighlightedLine(
                tokens=[token],
                line_number=i,
                is_highlighted=i in config.highlight_lines,
                background_color='#ffff00' if i in config.highlight_lines else None
            )
            highlighted_lines.append(highlighted_line)
        
        return HighlightResult(
            highlighted_lines=highlighted_lines,
            language=config.language,
            theme_used='plain',
            total_lines=len(lines),
            has_line_numbers=config.line_numbers,
            css_classes=['syntax-highlighter', 'language-plain'],
            accessibility_features=[],
            metadata={
                'error': error,
                'language_detected': False,
                'theme_adapted': False
            }
        )
    
    def _generate_cache_key(self, code: str, config: SyntaxHighlightConfig) -> str:
        """Generate cache key for highlighting result."""
        import hashlib
        key_data = f"{code}:{config.language}:{config.theme}:{config.line_numbers}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _cache_result(self, cache_key: str, result: HighlightResult):
        """Cache highlighting result."""
        if len(self._highlight_cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._highlight_cache))
            del self._highlight_cache[oldest_key]
        
        self._highlight_cache[cache_key] = result
    
    def _update_performance_metrics(self, lines_processed: int, processing_time: float):
        """Update performance metrics."""
        self._performance_metrics["total_highlights"] += 1
        self._performance_metrics["total_lines_processed"] += lines_processed
        
        # Update average time per line
        total_lines = self._performance_metrics["total_lines_processed"]
        current_avg = self._performance_metrics["average_time_per_line"]
        self._performance_metrics["average_time_per_line"] = (
            (current_avg * (total_lines - lines_processed) + processing_time) / total_lines
        )
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.language_definitions.keys())
    
    def get_supported_themes(self) -> List[str]:
        """Get list of supported themes."""
        return [theme.value for theme in HighlightTheme]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self._performance_metrics.copy()
    
    def reset_performance_metrics(self):
        """Reset performance metrics."""
        self._performance_metrics = {
            "total_highlights": 0,
            "total_lines_processed": 0,
            "average_time_per_line": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def clear_cache(self):
        """Clear the highlighting cache."""
        self._highlight_cache.clear()
        self.logger.info("Syntax highlighting cache cleared")
    
    def add_custom_language(
        self,
        name: str,
        definition: Dict[str, Any]
    ):
        """Add a custom language definition."""
        self.language_definitions[name.lower()] = definition
        self.logger.info(f"Added custom language definition: {name}")
    
    def add_custom_theme(
        self,
        name: str,
        definition: Dict[str, Any]
    ):
        """Add a custom theme definition."""
        # Convert string theme name to enum if it matches
        try:
            theme_enum = HighlightTheme(name.upper())
            self.theme_definitions[theme_enum] = definition
            self.logger.info(f"Added custom theme: {name}")
        except ValueError:
            self.logger.warning(f"Invalid theme name: {name}")


# Global highlighter instance
_syntax_highlighter_instance: Optional[SyntaxHighlighter] = None


def get_syntax_highlighter() -> SyntaxHighlighter:
    """Get global syntax highlighter instance."""
    global _syntax_highlighter_instance
    if _syntax_highlighter_instance is None:
        _syntax_highlighter_instance = SyntaxHighlighter()
    return _syntax_highlighter_instance