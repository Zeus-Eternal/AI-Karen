"""
Content Type Detection and Classification System
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

# Import shared models
from .response_formatting_models import (
    ContentType, LayoutType, DisplayContext, LayoutHint
)

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
    """
    
    def __init__(self):
        """Initialize the content type detector."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._init_code_patterns()
        self._init_data_patterns()
        self._init_structure_patterns()
        self._init_language_patterns()
        self._detection_stats = {
            "total_detections": 0,
            "type_counts": {ct.value: 0 for ct in ContentType},
            "average_confidence": 0.0
        }
    
    def _init_code_patterns(self):
        self.code_patterns = {
            'python': [r'^\s*(def|class|import|from)\s+\w+', r'^\s*if\s+.*:\s*$', r'#.*$'],
            'javascript': [r'^\s*(function|const|let|var)\s+\w+', r'^\s*if\s*\(.*\)\s*\{', r'//.*$'],
            'json': [r'^\s*\{', r'^\s*\[', r'^\s*".*"\s*:'],
            'xml': [r'^\s*<\?xml', r'^\s*<[^/>]+>', r'^\s*</[^>]+>'],
            'yaml': [r'^\s*\w+\s*:', r'^\s*-\s+', r'^\s*#.*$'],
            'sql': [r'^\s*(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\s+', r'^\s*FROM\s+'],
            'html': [r'^\s*<!DOCTYPE\s+html>', r'^\s*<html', r'^\s*<div'],
            'css': [r'^\s*\.[\w-]+\s*\{', r'^\s*#[\w-]+\s*\{', r'^\s*\w+\s*:\s*.*;'],
        }
        self.generic_code_patterns = [r'^\s*\w+\s*\([^)]*\)\s*\{', r'^\s*[{}]\s*$', r'^\s*".*"$']
    
    def _init_data_patterns(self):
        self.data_patterns = {
            'table': [r'^\s*\|.*\|', r'^\s*\+[-+]+\+'],
            'list': [r'^\s*[-*+]\s+'],
            'menu': [r'^\s*\d+\.\s+', r'^\s*\[[^\]]+\]\s+'],
            'steps': [r'^\s*Step\s+\d+:', r'^\s*\d+\.\s+.*[:.]'],
            'comparison': [r'^\s*\w+\s*vs\s*\w+', r'Pros\s*:.*Cons\s*:'],
            'timeline': [r'^\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}:', r'^\s*\w+\s+\d{1,2},\s*\d{4}:'],
        }
    
    def _init_structure_patterns(self):
        self.structure_patterns = {
            'heading': [r'^#{1,6}\s+', r'^[A-Z][a-z\s]+:$'],
            'code_block': [r'^```', r'^\s{4,}'],
            'quote': [r'^\s*>', r'^\s*"'],
            'link': [r'\[.*\]\(.*\)', r'https?://[^\s]+'],
            'emphasis': [r'\*\*.*?\*\*', r'\*.*?\*', r'`.*?`'],
        }
    
    def _init_language_patterns(self):
        self.language_patterns = {
            'error': [r'\b(error|exception|failed|failure|traceback)\b'],
            'warning': [r'\b(warning|caution|alert|notice)\b'],
            'info': [r'\b(info|information|note|tip)\b'],
            'success': [r'\b(success|complete|done|finished)\b'],
        }
    
    async def detect_content_type(
        self,
        content: str,
        user_query: Optional[str] = None,
        context_hints: Optional[List[str]] = None,
        display_context: DisplayContext = DisplayContext.DESKTOP
    ) -> DetectionResult:
        try:
            normalized_content = content.strip()
            code_result = self._detect_code_type(normalized_content)
            data_result = self._detect_data_structure(normalized_content)
            language_result = self._detect_language_type(normalized_content)
            structure_result = self._detect_structure_type(normalized_content)
            
            combined_results = [code_result, data_result, language_result, structure_result]
            best_result = self._select_best_result(combined_results, user_query, context_hints, display_context)
            layout_hint = self._generate_layout_hint(best_result, display_context)
            self._update_detection_stats(best_result)
            
            return DetectionResult(
                content_type=best_result[0],
                confidence=best_result[1],
                layout_hint=layout_hint,
                metadata=best_result[2] if len(best_result) > 2 else {},
                alternative_types=[r[:2] for r in combined_results]
            )
        except Exception as e:
            logger.error(f"Error detecting content type: {e}")
            return DetectionResult(content_type=ContentType.TEXT, confidence=0.0)
    
    def _detect_code_type(self, content: str) -> Tuple[ContentType, float, Dict[str, Any]]:
        lines = content.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        if total_lines == 0: return ContentType.TEXT, 0.0, {}
        
        language_scores = {}
        for language, patterns in self.code_patterns.items():
            score = sum(1 for pattern in patterns for line in lines if re.search(pattern, line, re.IGNORECASE))
            language_scores[language] = score / max(total_lines, 1)
        
        best_lang = max(language_scores.items(), key=lambda x: x[1])
        if best_lang[1] > 0.3:
            content_type_map = {'python': ContentType.PYTHON, 'javascript': ContentType.JAVASCRIPT, 'json': ContentType.JSON,
                               'xml': ContentType.XML, 'yaml': ContentType.YAML, 'sql': ContentType.SQL, 'html': ContentType.HTML, 'css': ContentType.CSS}
            return content_type_map.get(best_lang[0], ContentType.CODE), best_lang[1], {'language': best_lang[0]}
        return ContentType.TEXT, 0.0, {}

    def _detect_data_structure(self, content: str) -> Tuple[ContentType, float, Dict[str, Any]]:
        lines = content.split('\n')
        total_lines = len([line for line in lines if line.strip()])
        if total_lines == 0: return ContentType.TEXT, 0.0, {}
        
        structure_scores = {}
        for structure, patterns in self.data_patterns.items():
            score = sum(1 for pattern in patterns for line in lines if re.search(pattern, line, re.IGNORECASE))
            structure_scores[structure] = score / max(total_lines, 1)
            
        best_struct = max(structure_scores.items(), key=lambda x: x[1])
        if best_struct[1] > 0.3:
            content_type_map = {'table': ContentType.DATA_TABLE, 'list': ContentType.LIST, 'menu': ContentType.MENU, 'steps': ContentType.STEPS}
            return content_type_map.get(best_struct[0], ContentType.TEXT), best_struct[1], {'structure': best_struct[0]}
        return ContentType.TEXT, 0.0, {}

    def _detect_language_type(self, content: str) -> Tuple[ContentType, float, Dict[str, Any]]:
        content_lower = content.lower()
        language_scores = {}
        for lang_type, patterns in self.language_patterns.items():
            score = sum(len(re.findall(pattern, content_lower)) for pattern in patterns)
            language_scores[lang_type] = min(score / max(len(content.split()), 1), 1.0)
            
        best = max(language_scores.items(), key=lambda x: x[1])
        if best[1] > 0.1:
            content_type_map = {'error': ContentType.ERROR, 'warning': ContentType.WARNING, 'info': ContentType.INFO, 'success': ContentType.SUCCESS}
            return content_type_map.get(best[0], ContentType.TEXT), best[1], {'language_type': best[0]}
        return ContentType.TEXT, 0.0, {}

    def _detect_structure_type(self, content: str) -> Tuple[ContentType, float, Dict[str, Any]]:
        lines = content.split('\n')
        counts = {s: sum(1 for p in ps for l in lines if re.search(p, l, re.IGNORECASE)) for s, ps in self.structure_patterns.items()}
        total = sum(counts.values()) or 1
        best = max(counts.items(), key=lambda x: x[1])
        if best[0] == 'code_block' and best[1]/total > 0.3: return ContentType.CODE, best[1]/total, counts
        if best[0] == 'heading' and best[1]/total > 0.2: return ContentType.MARKDOWN, best[1]/total, counts
        return ContentType.TEXT, best[1]/total, counts

    def _select_best_result(self, results, query, hints, display):
        valid = [r for r in results if r[1] > 0]
        if not valid: return ContentType.TEXT, 0.0, {}
        valid.sort(key=lambda x: x[1], reverse=True)
        return valid[0]

    def _generate_layout_hint(self, result, display):
        content_type, confidence, metadata = result
        layout_mapping = {ContentType.CODE: LayoutType.CODE_BLOCK, ContentType.DATA_TABLE: LayoutType.TABLE,
                         ContentType.LIST: LayoutType.BULLET_LIST, ContentType.MENU: LayoutType.MENU, ContentType.STEPS: LayoutType.STEPS}
        return LayoutHint(layout_type=layout_mapping.get(content_type, LayoutType.DEFAULT), confidence=confidence, parameters=metadata)

    def _update_detection_stats(self, result):
        self._detection_stats["total_detections"] += 1
        self._detection_stats["type_counts"][result[0].value] += 1

_content_detector_instance = None
def get_content_detector() -> ContentTypeDetector:
    global _content_detector_instance
    if _content_detector_instance is None: _content_detector_instance = ContentTypeDetector()
    return _content_detector_instance