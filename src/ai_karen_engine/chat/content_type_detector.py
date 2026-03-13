"""
Content Type Detection and Classification System

This module provides intelligent content type detection and classification
for the CoPilot response formatting system.
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    from .response_formatting_models import (
        ContentType, LayoutType, DisplayContext, LayoutHint
    )
except ImportError:
    # Fallback imports for circular dependency
    from enum import Enum
    
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
    
    class DisplayContext(Enum):
        DESKTOP = "desktop"
        MOBILE = "mobile"
        TABLET = "tablet"
        TERMINAL = "terminal"
        API = "api"
        PRINT = "print"
        EMBEDDED = "embedded"
        VOICE = "voice"
    
    class LayoutHint:
        def __init__(self, layout_type, confidence=1.0, parameters=None, content_type=None, display_context=None):
            self.layout_type = layout_type
            self.confidence = confidence
            self.parameters = parameters or {}
            self.content_type = content_type
            self.display_context = display_context

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Result of content type detection."""
    content_type: ContentType
    confidence: float
    layout_hint: Optional[LayoutHint] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    alternative_types: List[Tuple[ContentType, float]] = field(default_factory=list)
    


class ContentTypeDetector:
    """
    Advanced content type detection system with multiple detection strategies.
    
    This class provides intelligent content type detection using:
    - Pattern matching
    - Statistical analysis
    - Contextual analysis
    - Language detection
    - Structure analysis
    """
    
    def __init__(self):
        """Initialize the content type detector."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize detection patterns
        self._init_code_patterns()
        self._init_data_patterns()
        self._init_structure_patterns()
        self._init_language_patterns()
        
        # Detection statistics
        self._detection_stats = {
            "total_detections": 0,
            "type_counts": {ct.value: 0 for ct in ContentType},
            "average_confidence": 0.0
        }
    
    def _init_code_patterns(self):
        """Initialize code detection patterns."""
        self.code_patterns = {
            'python': [
                r'^\s*(def|class|import|from)\s+\w+',
                r'^\s*if\s+.*:\s*$',
                r'^\s*for\s+.*\s+in\s+.*:\s*$',
                r'^\s*while\s+.*:\s*$',
                r'^\s*try\s*:\s*$',
                r'^\s*except\s+.*:\s*$',
                r'#.*$',  # Comments
                r'""".*?"""',  # Docstrings
                r"'''.*?'''",
            ],
            'javascript': [
                r'^\s*(function|const|let|var)\s+\w+',
                r'^\s*if\s*\(.*\)\s*\{',
                r'^\s*for\s*\(.*\)\s*\{',
                r'^\s*while\s*\(.*\)\s*\{',
                r'^\s*//.*$',  # Comments
                r'/\*.*?\*/',  # Block comments
                r'console\.log\(.*\)',
                r'require\s*\(',
                r'import\s+.*\s+from',
            ],
            'json': [
                r'^\s*\{',  # Object start
                r'^\s*\[',  # Array start
                r'^\s*".*"\s*:',  # Key-value pair
                r'^\s*\d+,?\s*$',  # Array element
                r'^\s*\}\s*$',  # Object end
                r'^\s*\]\s*$',  # Array end
            ],
            'xml': [
                r'^\s*<\?xml',  # XML declaration
                r'^\s*<[^/>]+>',  # Opening tag
                r'^\s*</[^>]+>',  # Closing tag
                r'^\s*<[^/>]+/>',  # Self-closing tag
            ],
            'yaml': [
                r'^\s*\w+\s*:',  # Key-value
                r'^\s*-\s+',  # List item
                r'^\s*#.*$',  # Comment
                r'^\s*\|',  # Multiline string
            ],
            'sql': [
                r'^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\s+',
                r'^\s*FROM\s+',
                r'^\s*WHERE\s+',
                r'^\s*ORDER\s+BY\s+',
                r'^\s*GROUP\s+BY\s+',
                r'^\s*JOIN\s+',
            ],
            'html': [
                r'^\s*<!DOCTYPE\s+html>',
                r'^\s*<html',
                r'^\s*<head>',
                r'^\s*<body>',
                r'^\s*<div',
                r'^\s*<p>',
                r'^\s*<script',
                r'^\s*<style',
            ],
            'css': [
                r'^\s*\.[\w-]+\s*\{',  # Class selector
                r'^\s*#[\w-]+\s*\{',  # ID selector
                r'^\s*@\w+',  # At-rules
                r'^\s*\w+\s*:\s*.*;',  # Property
            ],
        }
        
        # Generic code patterns
        self.generic_code_patterns = [
            r'^\s*\w+\s*\([^)]*\)\s*\{',  # Function definition
            r'^\s*\w+\s*:\s*\w+',  # Key-value
            r'^\s*[{}]\s*$',  # Braces
            r'^\s*\[[^\]]*\]\s*$',  # Brackets
            r'^\s*".*"$',  # Quoted strings
            r'^\s*\'.*\'',  # Single quoted
            r'^\s*\d+\s*[,;)\}]',  # Numbers
        ]
    
    def _init_data_patterns(self):
        """Initialize data structure detection patterns."""
        self.data_patterns = {
            'table': [
                r'^\s*\|.*\|.*\|',  # Markdown table
                r'^\s*\+[-+]+\+',  # Table separator
                r'^\s*\w+\s*\|\s*\w+\s*\|\s*\w+',  # Simple table
                r'^\s*-+\s*-+\s*-+',  # Dashed table
            ],
            'list': [
                r'^\s*[-*+]\s+',  # Bullet list
                r'^\s*\d+\.\s+',  # Numbered list
                r'^\s*[a-zA-Z]\.\s+',  # Lettered list
                r'^\s*\(\d+\)\s+',  # Parenthesized list
            ],
            'menu': [
                r'^\s*\d+\.\s+.*\(\w+\)',  # Numbered with shortcut
                r'^\s*[A-Z][a-z]*:\s+',  # Labeled options
                r'^\s*\[[^\]]+\]\s+',  # Bracketed options
            ],
            'steps': [
                r'^\s*Step\s+\d+:',  # Explicit steps
                r'^\s*\d+\.\s+.*[:.]',  # Numbered with description
                r'^\s*[Ff]irst\s*,\s*[Nn]ext',  # First/Next
                r'^\s*[Bb]egin\s*,\s*[Cc]ontinue',  # Begin/Continue
            ],
            'comparison': [
                r'^\s*\w+\s*vs\s*\w+',  # vs comparison
                r'^\s*\w+\s*versus\s*\w+',  # versus comparison
                r'^\s*Pros\s*:.*Cons\s*:',  # Pros/Cons
                r'^\s*Advantages\s*:.*Disadvantages\s*:',  # Advantages/Disadvantages
            ],
            'timeline': [
                r'^\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}:',  # Date-based
                r'^\s*\w+\s+\d{1,2},\s*\d{4}:',  # Month Day, Year
                r'^\s*Q[1-4]\s*\d{4}:',  # Quarter
                r'^\s*\[\d{4}\]:',  # Bracketed year
            ],
        }
    
    def _init_structure_patterns(self):
        """Initialize structure detection patterns."""
        self.structure_patterns = {
            'heading': [
                r'^#{1,6}\s+',  # Markdown headings
                r'^[A-Z][A-Z0-9\s\/&\-\(\)]+:$',  # Title case with colon
                r'^[A-Z][a-z\s]+:$',  # Capitalized with colon
            ],
            'code_block': [
                r'^```',  # Markdown code block
                r'^\s{4,}',  # Indented code
                r'^\t',  # Tab-indented
            ],
            'quote': [
                r'^\s*>',  # Blockquote
                r'^\s*"',  # Quoted text
            ],
            'link': [
                r'\[.*\]\(.*\)',  # Markdown link
                r'https?://[^\s]+',  # URL
                r'www\.[^\s]+',  # WWW link
            ],
            'emphasis': [
                r'\*\*.*?\*\*',  # Bold
                r'\*.*?\*',  # Italic
                r'_.*?_',  # Italic underscore
                r'`.*?`',  # Code
            ],
        }
    
    def _init_language_patterns(self):
        """Initialize language detection patterns."""
        self.language_patterns = {
            'error': [
                r'\b(error|exception|failed|failure|traceback)\b',
                r'\b(file|line)\s+\d+',
                r'\b(stack\s*trace|call\s*stack)\b',
            ],
            'warning': [
                r'\b(warning|caution|alert|notice)\b',
                r'\b(deprecated|obsolete|outdated)\b',
            ],
            'info': [
                r'\b(info|information|note|tip)\b',
                r'\b(reminder|hint|suggestion)\b',
            ],
            'success': [
                r'\b(success|complete|done|finished)\b',
                r'\b(passed|ok|ready)\b',
            ],
        }
    
    async def detect_content_type(
        self,
        content: str,
        user_query: Optional[str] = None,
        context_hints: Optional[List[str]] = None,
        display_context: DisplayContext = DisplayContext.DESKTOP
    ) -> DetectionResult:
        """
        Detect content type using multiple detection strategies.
        
        Args:
            content: Content to analyze
            user_query: Original user query for context
            context_hints: Additional context hints
            display_context: Display context for formatting
            
        Returns:
            DetectionResult with content type and confidence
        """
        try:
            self.logger.debug(f"Detecting content type for {len(content)} characters")
            
            # Normalize content
            normalized_content = self._normalize_content(content)
            
            # Apply detection strategies
            code_result = self._detect_code_type(normalized_content)
            data_result = self._detect_data_structure(normalized_content)
            language_result = self._detect_language_type(normalized_content)
            structure_result = self._detect_structure_type(normalized_content)
            
            # Combine results
            combined_results = [
                code_result,
                data_result,
                language_result,
                structure_result
            ]
            
            # Select best result
            best_result = self._select_best_result(
                combined_results, 
                user_query, 
                context_hints,
                display_context
            )
            
            # Generate layout hint
            layout_hint = self._generate_layout_hint(best_result, display_context)
            
            # Update statistics
            self._update_detection_stats(best_result)
            
            result = DetectionResult(
                content_type=best_result[0],
                confidence=best_result[1],
                layout_hint=layout_hint,
                metadata=best_result[2] if len(best_result) > 2 else {},
                alternative_types=[r[:2] for r in combined_results[1:4]]  # Top 3 alternatives
            )
            
            self.logger.debug(
                f"Content type detected: {result.content_type.value} "
                f"with confidence {result.confidence:.2f}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error detecting content type: {e}")
            # Return default result on error
            return DetectionResult(
                content_type=ContentType.TEXT,
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    def _normalize_content(self, content: str) -> str:
        """Normalize content for analysis."""
        if not content:
            return ""
        
        # Remove excessive whitespace
        normalized = re.sub(r'\s+', ' ', content.strip())
        
        # Normalize line endings
        normalized = normalized.replace('\r\n', '\n').replace('\r', '\n')
        
        return normalized
    
    def _detect_code_type(self, content: str) -> Tuple[ContentType, float, Dict[str, Any]]:
        """Detect if content is code and determine language."""
        lines = content.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        
        if total_lines == 0:
            return ContentType.TEXT, 0.0, {}
        
        # Score each language
        language_scores = {}
        
        for language, patterns in self.code_patterns.items():
            score = 0
            matches = 0
            
            for pattern in patterns:
                for line in lines:
                    if re.search(pattern, line, re.IGNORECASE | re.MULTILINE):
                        matches += 1
                        score += 1
            
            # Normalize by total lines
            confidence = score / max(total_lines, 1)
            language_scores[language] = {
                'confidence': confidence,
                'matches': matches,
                'score': score
            }
        
        # Check generic code patterns
        generic_score = 0
        for pattern in self.generic_code_patterns:
            for line in lines:
                if re.search(pattern, line, re.IGNORECASE | re.MULTILINE):
                    generic_score += 1
        
        generic_confidence = generic_score / max(total_lines, 1)
        
        # Find best language
        if language_scores:
            best_language = max(language_scores.items(), key=lambda x: x[1]['confidence'])
            best_confidence = best_language[1]['confidence']
            
            # Combine with generic confidence
            combined_confidence = (best_confidence + generic_confidence) / 2
            
            if combined_confidence > 0.3:  # Threshold for code detection
                content_type_map = {
                    'python': ContentType.PYTHON,
                    'javascript': ContentType.JAVASCRIPT,
                    'json': ContentType.JSON,
                    'xml': ContentType.XML,
                    'yaml': ContentType.YAML,
                    'sql': ContentType.SQL,
                    'html': ContentType.HTML,
                    'css': ContentType.CSS,
                }
                
                detected_type = content_type_map.get(best_language[0], ContentType.CODE)
                
                return detected_type, combined_confidence, {
                    'language': best_language[0],
                    'matches': best_language[1]['matches'],
                    'generic_score': generic_score
                }
        
        return ContentType.TEXT, 0.0, {}
    
    def _detect_data_structure(self, content: str) -> Tuple[ContentType, float, Dict[str, Any]]:
        """Detect data structures like tables, lists, etc."""
        lines = content.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        
        if total_lines == 0:
            return ContentType.TEXT, 0.0, {}
        
        structure_scores = {}
        
        for structure, patterns in self.data_patterns.items():
            score = 0
            matches = 0
            
            for pattern in patterns:
                for line in lines:
                    if re.search(pattern, line, re.IGNORECASE | re.MULTILINE):
                        matches += 1
                        score += 1
            
            confidence = score / max(total_lines, 1)
            structure_scores[structure] = {
                'confidence': confidence,
                'matches': matches,
                'score': score
            }
        
        if structure_scores:
            best_structure = max(structure_scores.items(), key=lambda x: x[1]['confidence'])
            best_confidence = best_structure[1]['confidence']
            
            if best_confidence > 0.3:  # Threshold for structure detection
                content_type_map = {
                    'table': ContentType.DATA_TABLE,
                    'list': ContentType.LIST,
                    'menu': ContentType.MENU,
                    'steps': ContentType.STEPS,
                    'comparison': ContentType.TEXT,  # Special case
                    'timeline': ContentType.TEXT,  # Special case
                }
                
                detected_type = content_type_map.get(best_structure[0], ContentType.TEXT)
                
                return detected_type, best_confidence, {
                    'structure': best_structure[0],
                    'matches': best_structure[1]['matches'],
                    'all_scores': structure_scores
                }
        
        return ContentType.TEXT, 0.0, {}
    
    def _detect_language_type(self, content: str) -> Tuple[ContentType, float, Dict[str, Any]]:
        """Detect language type (error, warning, info, etc.)."""
        content_lower = content.lower()
        
        language_scores = {}
        
        for lang_type, patterns in self.language_patterns.items():
            score = 0
            matches = 0
            
            for pattern in patterns:
                matches += len(re.findall(pattern, content_lower))
                score += len(re.findall(pattern, content_lower))
            
            confidence = min(score / max(len(content.split()), 1), 1.0)
            language_scores[lang_type] = {
                'confidence': confidence,
                'matches': matches,
                'score': score
            }
        
        if language_scores:
            best_language = max(language_scores.items(), key=lambda x: x[1]['confidence'])
            best_confidence = best_language[1]['confidence']
            
            if best_confidence > 0.1:  # Lower threshold for language detection
                content_type_map = {
                    'error': ContentType.ERROR,
                    'warning': ContentType.WARNING,
                    'info': ContentType.INFO,
                    'success': ContentType.SUCCESS,
                }
                
                detected_type = content_type_map.get(best_language[0], ContentType.TEXT)
                
                return detected_type, best_confidence, {
                    'language_type': best_language[0],
                    'matches': best_language[1]['matches'],
                    'all_scores': language_scores
                }
        
        return ContentType.TEXT, 0.0, {}
    
    def _detect_structure_type(self, content: str) -> Tuple[ContentType, float, Dict[str, Any]]:
        """Detect structural elements like headings, code blocks, etc."""
        lines = content.split('\n')
        
        # Count structural elements
        structure_counts = {
            'headings': 0,
            'code_blocks': 0,
            'quotes': 0,
            'links': 0,
            'emphasis': 0,
        }
        
        for line in lines:
            for structure, patterns in self.structure_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE | re.MULTILINE):
                        structure_counts[structure] += 1
        
        total_elements = sum(structure_counts.values())
        
        if total_elements == 0:
            return ContentType.TEXT, 0.0, {}
        
        # Determine dominant structure
        dominant_structure = max(structure_counts.items(), key=lambda x: x[1])
        confidence = dominant_structure[1] / total_elements
        
        # Map to content types
        if dominant_structure[0] == 'code_blocks' and confidence > 0.3:
            return ContentType.CODE, confidence, structure_counts
        elif dominant_structure[0] == 'headings' and confidence > 0.2:
            return ContentType.MARKDOWN, confidence, structure_counts
        
        return ContentType.TEXT, confidence, structure_counts
    
    def _select_best_result(
        self,
        results: List[Tuple[ContentType, float, Dict[str, Any]]],
        user_query: Optional[str],
        context_hints: Optional[List[str]],
        display_context: DisplayContext
    ) -> Tuple[ContentType, float, Dict[str, Any]]:
        """Select the best detection result based on multiple factors."""
        # Filter out results with zero confidence
        valid_results = [r for r in results if r[1] > 0]
        
        if not valid_results:
            return ContentType.TEXT, 0.0, {}
        
        # Sort by confidence
        valid_results.sort(key=lambda x: x[1], reverse=True)
        
        # Apply context hints if available
        if context_hints:
            for hint in context_hints:
                for result in valid_results:
                    if hint.lower() in result[0].value.lower():
                        # Boost confidence for hinted types
                        boosted_confidence = min(result[1] * 1.2, 1.0)
                        result = (result[0], boosted_confidence, result[2])
                        valid_results[valid_results.index(result)] = result
                        break
        
        # Consider user query context
        if user_query:
            query_lower = user_query.lower()
            for result in valid_results:
                if any(keyword in query_lower for keyword in ['code', 'example', 'function', 'class']):
                    if result[0] in [ContentType.CODE, ContentType.PYTHON, ContentType.JAVASCRIPT]:
                        # Boost code-related types for code queries
                        boosted_confidence = min(result[1] * 1.1, 1.0)
                        result = (result[0], boosted_confidence, result[2])
                        valid_results[valid_results.index(result)] = result
        
        # Return highest confidence result
        return valid_results[0]
    
    def _generate_layout_hint(
        self,
        detection_result: Tuple[ContentType, float, Dict[str, Any]],
        display_context: DisplayContext
    ) -> Optional[LayoutHint]:
        """Generate layout hint based on detection result."""
        content_type, confidence, metadata = detection_result
        
        # Map content types to layout types
        layout_mapping = {
            ContentType.CODE: LayoutType.CODE_BLOCK,
            ContentType.DATA_TABLE: LayoutType.TABLE,
            ContentType.LIST: LayoutType.BULLET_LIST,
            ContentType.MENU: LayoutType.MENU,
            ContentType.STEPS: LayoutType.STEPS,
            ContentType.ERROR: LayoutType.SYSTEM_STATUS,
            ContentType.WARNING: LayoutType.SYSTEM_STATUS,
            ContentType.INFO: LayoutType.SYSTEM_STATUS,
            ContentType.SUCCESS: LayoutType.SYSTEM_STATUS,
        }
        
        layout_type = layout_mapping.get(content_type, LayoutType.DEFAULT)
        
        # Adjust for display context
        if display_context == DisplayContext.MOBILE:
            # Simplify layouts for mobile
            if layout_type == LayoutType.TABLE:
                layout_type = LayoutType.BULLET_LIST
            elif layout_type == LayoutType.GRID:
                layout_type = LayoutType.BULLET_LIST
        
        return LayoutHint(
            layout_type=layout_type,
            confidence=confidence,
            parameters=metadata,
            content_type=content_type,
            display_context=display_context
        )
    
    def _update_detection_stats(self, result: Tuple[ContentType, float, Dict[str, Any]]):
        """Update detection statistics."""
        self._detection_stats["total_detections"] += 1
        self._detection_stats["type_counts"][result[0].value] += 1
        
        # Update average confidence
        total = self._detection_stats["total_detections"]
        current_avg = self._detection_stats["average_confidence"]
        new_confidence = result[1]
        self._detection_stats["average_confidence"] = (
            (current_avg * (total - 1) + new_confidence) / total
        )
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return self._detection_stats.copy()
    
    def reset_statistics(self):
        """Reset detection statistics."""
        self._detection_stats = {
            "total_detections": 0,
            "type_counts": {ct.value: 0 for ct in ContentType},
            "average_confidence": 0.0
        }


# Global detector instance
_content_detector_instance: Optional[ContentTypeDetector] = None


def get_content_detector() -> ContentTypeDetector:
    """Get global content detector instance."""
    global _content_detector_instance
    if _content_detector_instance is None:
        _content_detector_instance = ContentTypeDetector()
    return _content_detector_instance