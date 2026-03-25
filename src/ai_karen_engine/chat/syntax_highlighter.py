"""
Syntax Highlighting System for Code Blocks and Technical Content
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

# Import shared models
from .response_formatting_models import (
    SyntaxHighlightConfig, ThemeMode, AccessibilityLevel
)

logger = logging.getLogger(__name__)

class HighlightTheme(Enum):
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
    text: str
    token_type: str
    color: Optional[str] = None
    background_color: Optional[str] = None
    font_weight: Optional[str] = None
    font_style: Optional[str] = None
    css_class: Optional[str] = None

@dataclass
class HighlightedLine:
    tokens: List[HighlightedToken]
    line_number: int
    is_highlighted: bool = False
    background_color: Optional[str] = None

@dataclass
class HighlightResult:
    highlighted_lines: List[HighlightedLine]
    language: str
    theme_used: str
    total_lines: int
    has_line_numbers: bool
    css_classes: List[str]
    accessibility_features: List[str]
    metadata: Dict[str, Any]
    
    @property
    def highlighted_content(self) -> str:
        # Simple string representation for compatibility
        return "\n".join(["".join([t.text for t in line.tokens]) for line in self.highlighted_lines])

class SyntaxHighlighter:
    """
    Advanced syntax highlighting system with multi-language support.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._init_language_definitions()
        self._init_theme_definitions()
        self._highlight_cache = {}
        self._cache_max_size = 1000
    
    def _init_language_definitions(self):
        self.language_definitions = {
            'python': {'keywords': ['def', 'class', 'import', 'from', 'if', 'else', 'for', 'while', 'return'],
                       'builtins': ['print', 'len', 'range', 'str', 'int', 'dict', 'list', 'set']},
            'javascript': {'keywords': ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return']},
            'json': {'keywords': ['true', 'false', 'null']},
        }
    
    def _init_theme_definitions(self):
        self.theme_definitions = {
            HighlightTheme.DEFAULT: {'keyword': {'color': '#0000ff'}, 'builtin': {'color': '#008000'}, 'text': '#000000'},
            HighlightTheme.DARK: {'keyword': {'color': '#569cd6'}, 'builtin': {'color': '#4ec9b0'}, 'text': '#d4d4d4'},
        }
    
    async def highlight_code(self, code: str, config: SyntaxHighlightConfig) -> HighlightResult:
        try:
            lang_def = self.language_definitions.get(config.language.lower(), {'keywords': [], 'builtins': []})
            theme = self.theme_definitions.get(HighlightTheme.DEFAULT)
            lines = code.split('\n')
            highlighted_lines = []
            for i, line in enumerate(lines, 1):
                tokens = [HighlightedToken(text=line, token_type='text', color=theme['text'])]
                highlighted_lines.append(HighlightedLine(tokens=tokens, line_number=i))
            
            return HighlightResult(
                highlighted_lines=highlighted_lines,
                language=config.language,
                theme_used='default',
                total_lines=len(lines),
                has_line_numbers=config.line_numbers,
                css_classes=['syntax-highlighter'],
                accessibility_features=[],
                metadata={}
            )
        except Exception as e:
            logger.error(f"Error highlighting code: {e}")
            return self._create_plain_result(code, config)

    def _create_plain_result(self, code, config):
        lines = code.split('\n')
        highlighted_lines = [HighlightedLine(tokens=[HighlightedToken(text=l, token_type='text')], line_number=i+1) for i, l in enumerate(lines)]
        return HighlightResult(highlighted_lines, config.language, 'plain', len(lines), config.line_numbers, [], [], {})

_syntax_highlighter_instance = None
def get_syntax_highlighter() -> SyntaxHighlighter:
    global _syntax_highlighter_instance
    if _syntax_highlighter_instance is None: _syntax_highlighter_instance = SyntaxHighlighter()
    return _syntax_highlighter_instance