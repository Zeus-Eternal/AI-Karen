"""
Advanced Formatting and Structure Optimization Engine

This module provides intelligent formatting and structure optimization for responses,
including automatic format selection, hierarchical organization, syntax highlighting,
navigation aids, accessibility support, and responsive formatting.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class FormatType(Enum):
    """Available formatting types for content."""
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    HTML = "html"
    CODE_BLOCK = "code_block"
    LIST = "list"
    TABLE = "table"
    STRUCTURED = "structured"
    INTERACTIVE = "interactive"


class ContentType(Enum):
    """Types of content that can be formatted."""
    TEXT = "text"
    CODE = "code"
    DATA = "data"
    MIXED = "mixed"
    TECHNICAL = "technical"
    NARRATIVE = "narrative"
    INSTRUCTIONAL = "instructional"


class AccessibilityLevel(Enum):
    """Accessibility support levels."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    FULL = "full"


class DisplayContext(Enum):
    """Different display contexts for responsive formatting."""
    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"
    TERMINAL = "terminal"
    API = "api"
    PRINT = "print"


@dataclass
class ContentSection:
    """Represents a section of content with formatting metadata."""
    content: str
    section_type: ContentType
    priority: int = 1
    format_hint: Optional[FormatType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    accessibility_text: Optional[str] = None
    navigation_id: Optional[str] = None


@dataclass
class FormattingContext:
    """Context information for formatting decisions."""
    display_context: DisplayContext = DisplayContext.DESKTOP
    accessibility_level: AccessibilityLevel = AccessibilityLevel.BASIC
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    content_length: int = 0
    technical_level: str = "intermediate"
    language: str = "en"


@dataclass
class NavigationAid:
    """Navigation aid for long responses."""
    type: str  # "toc", "summary", "index", "breadcrumb"
    content: str
    links: List[Dict[str, str]] = field(default_factory=list)
    position: str = "top"  # "top", "bottom", "sidebar"


@dataclass
class FormattedResponse:
    """Complete formatted response with all optimizations applied."""
    content: str
    format_type: FormatType
    sections: List[ContentSection]
    navigation_aids: List[NavigationAid]
    accessibility_features: Dict[str, Any]
    metadata: Dict[str, Any]
    estimated_reading_time: Optional[int] = None


class AdvancedFormattingEngine:
    """
    Advanced formatting and structure optimization engine that provides
    intelligent formatting, hierarchical organization, and accessibility support.
    """
    
    def __init__(self):
        self.code_languages = {
            'python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'csharp',
            'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'r',
            'sql', 'html', 'css', 'xml', 'json', 'yaml', 'bash', 'shell'
        }
        
        self.format_patterns = {
            'code_block': re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL),
            'inline_code': re.compile(r'`([^`]+)`'),
            'list_item': re.compile(r'^[\s]*[-*+]\s+(.+)$', re.MULTILINE),
            'numbered_list': re.compile(r'^[\s]*\d+\.\s+(.+)$', re.MULTILINE),
            'table_row': re.compile(r'\|(.+)\|'),
            'heading': re.compile(r'^#+\s+(.+)$', re.MULTILINE),
            'url': re.compile(r'https?://[^\s]+'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        }
        
        self.syntax_highlighters = self._initialize_syntax_highlighters()
    
    def _initialize_syntax_highlighters(self) -> Dict[str, Any]:
        """Initialize syntax highlighting configurations."""
        return {
            'python': {
                'keywords': ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'import', 'from', 'return'],
                'builtins': ['print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple'],
                'operators': ['=', '+', '-', '*', '/', '//', '%', '**', '==', '!=', '<', '>', '<=', '>='],
                'delimiters': ['(', ')', '[', ']', '{', '}', ',', ':', ';']
            },
            'javascript': {
                'keywords': ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'return', 'class', 'extends'],
                'builtins': ['console', 'document', 'window', 'Array', 'Object', 'String', 'Number'],
                'operators': ['=', '+', '-', '*', '/', '%', '==', '===', '!=', '!==', '<', '>', '<=', '>='],
                'delimiters': ['(', ')', '[', ']', '{', '}', ',', ';', '.']
            }
        }
    
    async def analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """Analyze content structure to determine optimal formatting approach."""
        try:
            analysis = {
                'content_type': self._detect_content_type(content),
                'complexity': self._assess_complexity(content),
                'sections': self._identify_sections(content),
                'code_blocks': self._extract_code_blocks(content),
                'data_structures': self._identify_data_structures(content),
                'length': len(content),
                'reading_time': self._estimate_reading_time(content),
                'technical_density': self._calculate_technical_density(content)
            }
            
            logger.info(f"Content analysis completed: {analysis['content_type']} with {len(analysis['sections'])} sections")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing content structure: {e}")
            return {
                'content_type': ContentType.TEXT,
                'complexity': 'simple',
                'sections': [],
                'code_blocks': [],
                'data_structures': [],
                'length': len(content),
                'reading_time': 1,
                'technical_density': 0.0
            }
    
    def _detect_content_type(self, content: str) -> ContentType:
        """Detect the primary type of content."""
        code_indicators = len(self.format_patterns['code_block'].findall(content))
        inline_code_indicators = len(self.format_patterns['inline_code'].findall(content))
        list_indicators = len(self.format_patterns['list_item'].findall(content))
        table_indicators = len(self.format_patterns['table_row'].findall(content))
        
        # Technical keywords
        technical_keywords = ['function', 'class', 'method', 'algorithm', 'implementation', 'API', 'database']
        technical_count = sum(1 for keyword in technical_keywords if keyword.lower() in content.lower())
        
        if code_indicators > 2 or inline_code_indicators > 5:
            return ContentType.CODE
        elif technical_count > 3 or (code_indicators > 0 and technical_count > 1):
            return ContentType.TECHNICAL
        elif list_indicators > 3 or table_indicators > 2:
            return ContentType.DATA
        elif code_indicators > 0 or inline_code_indicators > 0 or technical_count > 0:
            return ContentType.MIXED
        elif any(word in content.lower() for word in ['step', 'first', 'then', 'next', 'finally', 'how to']):
            return ContentType.INSTRUCTIONAL
        else:
            return ContentType.NARRATIVE
    
    def _assess_complexity(self, content: str) -> str:
        """Assess the complexity level of content."""
        word_count = len(content.split())
        sentence_count = len([s for s in content.split('.') if s.strip()])
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        code_blocks = len(self.format_patterns['code_block'].findall(content))
        headings = len(self.format_patterns['heading'].findall(content))
        
        complexity_score = 0
        if avg_sentence_length > 20:
            complexity_score += 1
        if word_count > 500:
            complexity_score += 1
        if code_blocks > 2:
            complexity_score += 1
        if headings > 3:
            complexity_score += 1
        
        if complexity_score >= 3:
            return 'complex'
        elif complexity_score >= 1:
            return 'moderate'
        else:
            return 'simple'
    
    def _identify_sections(self, content: str) -> List[Dict[str, Any]]:
        """Identify logical sections in the content."""
        sections = []
        lines = content.split('\n')
        current_section = {'content': '', 'type': 'text', 'start_line': 0}
        
        for i, line in enumerate(lines):
            # Check for headings
            heading_match = self.format_patterns['heading'].match(line)
            if heading_match:
                if current_section['content'].strip():
                    sections.append(current_section)
                current_section = {
                    'content': line + '\n',
                    'type': 'heading',
                    'level': len(line) - len(line.lstrip('#')),
                    'start_line': i
                }
            # Check for code blocks
            elif line.strip().startswith('```'):
                if current_section['content'].strip():
                    sections.append(current_section)
                # Find the end of code block
                code_content = [line]
                for j in range(i + 1, len(lines)):
                    code_content.append(lines[j])
                    if lines[j].strip().startswith('```'):
                        break
                current_section = {
                    'content': '\n'.join(code_content),
                    'type': 'code',
                    'language': line.strip()[3:] if len(line.strip()) > 3 else 'text',
                    'start_line': i
                }
            else:
                current_section['content'] += line + '\n'
        
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _extract_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Extract and analyze code blocks."""
        code_blocks = []
        matches = self.format_patterns['code_block'].findall(content)
        
        for language, code in matches:
            code_blocks.append({
                'language': language or 'text',
                'code': code.strip(),
                'lines': len(code.strip().split('\n')),
                'complexity': self._assess_code_complexity(code)
            })
        
        return code_blocks
    
    def _assess_code_complexity(self, code: str) -> str:
        """Assess the complexity of a code block."""
        lines = len(code.split('\n'))
        functions = len(re.findall(r'\bdef\b|\bfunction\b|\bclass\b', code, re.IGNORECASE))
        loops = len(re.findall(r'\bfor\b|\bwhile\b', code, re.IGNORECASE))
        conditionals = len(re.findall(r'\bif\b|\belse\b|\belif\b', code, re.IGNORECASE))
        
        complexity_score = functions * 2 + loops * 1.5 + conditionals * 1 + lines * 0.1
        
        if complexity_score > 20:
            return 'high'
        elif complexity_score > 10:
            return 'medium'
        else:
            return 'low'
    
    def _identify_data_structures(self, content: str) -> List[Dict[str, Any]]:
        """Identify data structures that could be formatted as tables or lists."""
        data_structures = []
        
        # Look for table-like structures
        table_matches = self.format_patterns['table_row'].findall(content)
        if len(table_matches) > 1:
            data_structures.append({
                'type': 'table',
                'rows': len(table_matches),
                'estimated_columns': len(table_matches[0].split('|')) if table_matches else 0
            })
        
        # Look for list structures
        list_matches = self.format_patterns['list_item'].findall(content)
        if len(list_matches) > 2:
            data_structures.append({
                'type': 'list',
                'items': len(list_matches),
                'style': 'unordered'
            })
        
        numbered_matches = self.format_patterns['numbered_list'].findall(content)
        if len(numbered_matches) > 2:
            data_structures.append({
                'type': 'list',
                'items': len(numbered_matches),
                'style': 'ordered'
            })
        
        return data_structures
    
    def _estimate_reading_time(self, content: str) -> int:
        """Estimate reading time in minutes."""
        word_count = len(content.split())
        # Average reading speed: 200-250 words per minute
        return max(1, round(word_count / 225))
    
    def _calculate_technical_density(self, content: str) -> float:
        """Calculate the density of technical content."""
        total_words = len(content.split())
        if total_words == 0:
            return 0.0
        
        technical_indicators = [
            len(self.format_patterns['code_block'].findall(content)),
            len(self.format_patterns['inline_code'].findall(content)),
            content.lower().count('api'),
            content.lower().count('function'),
            content.lower().count('method'),
            content.lower().count('class'),
            content.lower().count('algorithm'),
            content.lower().count('implementation')
        ]
        
        return sum(technical_indicators) / total_words
    
    async def select_optimal_format(self, content: str, context: FormattingContext) -> FormatType:
        """Select the optimal format type based on content analysis and context."""
        try:
            analysis = await self.analyze_content_structure(content)
            
            # Consider display context
            if context.display_context == DisplayContext.TERMINAL:
                return FormatType.PLAIN_TEXT
            elif context.display_context == DisplayContext.API:
                return FormatType.STRUCTURED
            
            # Consider content type
            content_type = analysis['content_type']
            if content_type == ContentType.CODE:
                return FormatType.CODE_BLOCK
            elif content_type == ContentType.DATA and len(analysis['data_structures']) > 0:
                # Check if table format would be appropriate
                for ds in analysis['data_structures']:
                    if ds['type'] == 'table':
                        return FormatType.TABLE
                return FormatType.LIST
            elif content_type == ContentType.TECHNICAL:
                return FormatType.MARKDOWN
            elif analysis['complexity'] == 'complex':
                return FormatType.STRUCTURED
            else:
                return FormatType.MARKDOWN
                
        except Exception as e:
            logger.error(f"Error selecting optimal format: {e}")
            return FormatType.MARKDOWN
    
    async def organize_content_hierarchically(self, content: str) -> List[ContentSection]:
        """Organize content into hierarchical sections."""
        try:
            analysis = await self.analyze_content_structure(content)
            sections = []
            
            for i, section_data in enumerate(analysis['sections']):
                section = ContentSection(
                    content=section_data['content'],
                    section_type=self._map_section_type(section_data['type']),
                    priority=self._calculate_section_priority(section_data, i),
                    format_hint=self._suggest_section_format(section_data),
                    metadata={
                        'original_type': section_data['type'],
                        'start_line': section_data.get('start_line', 0),
                        'level': section_data.get('level', 1)
                    },
                    navigation_id=f"section_{i}" if section_data['type'] == 'heading' else None
                )
                sections.append(section)
            
            # Sort by priority (higher priority first)
            sections.sort(key=lambda x: x.priority, reverse=True)
            
            logger.info(f"Organized content into {len(sections)} hierarchical sections")
            return sections
            
        except Exception as e:
            logger.error(f"Error organizing content hierarchically: {e}")
            return [ContentSection(content=content, section_type=ContentType.TEXT)]
    
    def _map_section_type(self, section_type: str) -> ContentType:
        """Map section type to ContentType enum."""
        mapping = {
            'heading': ContentType.TEXT,
            'code': ContentType.CODE,
            'text': ContentType.TEXT,
            'list': ContentType.DATA,
            'table': ContentType.DATA
        }
        return mapping.get(section_type, ContentType.TEXT)
    
    def _calculate_section_priority(self, section_data: Dict[str, Any], index: int) -> int:
        """Calculate priority for a section."""
        priority = 5  # Base priority
        
        # Headings get higher priority
        if section_data['type'] == 'heading':
            level = section_data.get('level', 3)
            priority += (4 - level) * 2  # H1 gets +6, H2 gets +4, etc.
        
        # Code blocks get medium-high priority
        elif section_data['type'] == 'code':
            priority += 3
        
        # Earlier sections get slight priority boost
        priority += max(0, 10 - index)
        
        return priority
    
    def _suggest_section_format(self, section_data: Dict[str, Any]) -> FormatType:
        """Suggest optimal format for a section."""
        section_type = section_data['type']
        
        if section_type == 'code':
            return FormatType.CODE_BLOCK
        elif section_type == 'heading':
            return FormatType.MARKDOWN
        elif section_type == 'list':
            return FormatType.LIST
        elif section_type == 'table':
            return FormatType.TABLE
        else:
            return FormatType.MARKDOWN
    
    async def apply_syntax_highlighting(self, code: str, language: str) -> str:
        """Apply syntax highlighting to code blocks."""
        try:
            if language not in self.syntax_highlighters:
                return code  # Return as-is if language not supported
            
            highlighter = self.syntax_highlighters[language]
            highlighted_code = code
            
            # Apply keyword highlighting
            for keyword in highlighter['keywords']:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                highlighted_code = re.sub(
                    pattern, 
                    f'<span class="keyword">{keyword}</span>', 
                    highlighted_code
                )
            
            # Apply builtin highlighting
            for builtin in highlighter['builtins']:
                pattern = r'\b' + re.escape(builtin) + r'\b'
                highlighted_code = re.sub(
                    pattern, 
                    f'<span class="builtin">{builtin}</span>', 
                    highlighted_code
                )
            
            # Apply string highlighting
            string_pattern = r'(["\'])(?:(?=(\\?))\2.)*?\1'
            highlighted_code = re.sub(
                string_pattern, 
                r'<span class="string">\g<0></span>', 
                highlighted_code
            )
            
            # Apply comment highlighting
            if language == 'python':
                comment_pattern = r'#.*$'
            elif language == 'javascript':
                comment_pattern = r'//.*$'
            else:
                comment_pattern = r'#.*$'  # Default to hash comments
            
            highlighted_code = re.sub(
                comment_pattern, 
                r'<span class="comment">\g<0></span>', 
                highlighted_code, 
                flags=re.MULTILINE
            )
            
            return highlighted_code
            
        except Exception as e:
            logger.error(f"Error applying syntax highlighting: {e}")
            return code
    
    async def create_navigation_aids(self, sections: List[ContentSection], context: FormattingContext) -> List[NavigationAid]:
        """Create navigation aids for long responses."""
        try:
            navigation_aids = []
            
            # Create table of contents for long content
            headings = [s for s in sections if s.navigation_id]
            if len(headings) > 2:
                toc_content = self._generate_table_of_contents(headings)
                navigation_aids.append(NavigationAid(
                    type="toc",
                    content=toc_content,
                    links=[{
                        "text": self._extract_heading_text(h.content),
                        "id": h.navigation_id
                    } for h in headings],
                    position="top"
                ))
            
            # Create summary for very long content
            total_content_length = sum(len(s.content) for s in sections)
            if total_content_length > 2000:
                summary = self._generate_content_summary(sections)
                navigation_aids.append(NavigationAid(
                    type="summary",
                    content=summary,
                    position="top"
                ))
            
            # Create index for technical content
            code_sections = [s for s in sections if s.section_type == ContentType.CODE]
            if len(code_sections) > 2:
                index_content = self._generate_code_index(code_sections)
                navigation_aids.append(NavigationAid(
                    type="index",
                    content=index_content,
                    position="sidebar"
                ))
            
            logger.info(f"Created {len(navigation_aids)} navigation aids")
            return navigation_aids
            
        except Exception as e:
            logger.error(f"Error creating navigation aids: {e}")
            return []
    
    def _generate_table_of_contents(self, headings: List[ContentSection]) -> str:
        """Generate a table of contents from headings."""
        toc_lines = ["## Table of Contents\n"]
        
        for heading in headings:
            heading_text = self._extract_heading_text(heading.content)
            level = heading.metadata.get('level', 1)
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}- [{heading_text}](#{heading.navigation_id})")
        
        return "\n".join(toc_lines)
    
    def _extract_heading_text(self, heading_content: str) -> str:
        """Extract clean text from a heading."""
        # Remove markdown heading markers
        text = re.sub(r'^#+\s*', '', heading_content.strip())
        return text.split('\n')[0]  # Take only the first line
    
    def _generate_content_summary(self, sections: List[ContentSection]) -> str:
        """Generate a summary of the content."""
        summary_parts = ["## Summary\n"]
        
        # Count different types of content
        text_sections = len([s for s in sections if s.section_type == ContentType.TEXT])
        code_sections = len([s for s in sections if s.section_type == ContentType.CODE])
        data_sections = len([s for s in sections if s.section_type == ContentType.DATA])
        
        if text_sections > 0:
            summary_parts.append(f"- {text_sections} explanatory sections")
        if code_sections > 0:
            summary_parts.append(f"- {code_sections} code examples")
        if data_sections > 0:
            summary_parts.append(f"- {data_sections} data structures")
        
        # Estimate reading time
        total_words = sum(len(s.content.split()) for s in sections)
        reading_time = max(1, round(total_words / 225))
        summary_parts.append(f"- Estimated reading time: {reading_time} minute{'s' if reading_time != 1 else ''}")
        
        return "\n".join(summary_parts)
    
    def _generate_code_index(self, code_sections: List[ContentSection]) -> str:
        """Generate an index of code sections."""
        index_lines = ["## Code Index\n"]
        
        for i, section in enumerate(code_sections):
            language = section.metadata.get('language', 'text')
            lines = len(section.content.split('\n'))
            index_lines.append(f"- Code Block {i+1} ({language}, {lines} lines)")
        
        return "\n".join(index_lines)
    
    async def add_accessibility_features(self, response: FormattedResponse, context: FormattingContext) -> Dict[str, Any]:
        """Add accessibility features to the formatted response."""
        try:
            accessibility_features = {}
            
            if context.accessibility_level in [AccessibilityLevel.ENHANCED, AccessibilityLevel.FULL]:
                # Add alt text for code blocks
                accessibility_features['code_descriptions'] = []
                for section in response.sections:
                    if section.section_type == ContentType.CODE:
                        description = self._generate_code_description(section.content)
                        accessibility_features['code_descriptions'].append({
                            'section_id': section.navigation_id,
                            'description': description
                        })
                
                # Add reading level information
                accessibility_features['reading_level'] = self._assess_reading_level(response.content)
                
                # Add content warnings for complex technical content
                if response.metadata.get('technical_density', 0) > 0.3:
                    accessibility_features['content_warning'] = "This response contains technical content that may require programming knowledge."
            
            if context.accessibility_level == AccessibilityLevel.FULL:
                # Add screen reader optimized version
                accessibility_features['screen_reader_text'] = self._generate_screen_reader_text(response)
                
                # Add keyboard navigation hints
                accessibility_features['keyboard_navigation'] = self._generate_keyboard_navigation_hints(response)
            
            logger.info(f"Added accessibility features: {list(accessibility_features.keys())}")
            return accessibility_features
            
        except Exception as e:
            logger.error(f"Error adding accessibility features: {e}")
            return {}
    
    def _generate_code_description(self, code_content: str) -> str:
        """Generate a description of code content for accessibility."""
        lines = len(code_content.split('\n'))
        
        # Identify key programming constructs
        functions = len(re.findall(r'\bdef\b|\bfunction\b', code_content, re.IGNORECASE))
        classes = len(re.findall(r'\bclass\b', code_content, re.IGNORECASE))
        loops = len(re.findall(r'\bfor\b|\bwhile\b', code_content, re.IGNORECASE))
        conditionals = len(re.findall(r'\bif\b', code_content, re.IGNORECASE))
        
        description_parts = [f"Code block with {lines} lines"]
        
        if functions > 0:
            description_parts.append(f"{functions} function{'s' if functions != 1 else ''}")
        if classes > 0:
            description_parts.append(f"{classes} class{'es' if classes != 1 else ''}")
        if loops > 0:
            description_parts.append(f"{loops} loop{'s' if loops != 1 else ''}")
        if conditionals > 0:
            description_parts.append(f"{conditionals} conditional{'s' if conditionals != 1 else ''}")
        
        return ", ".join(description_parts)
    
    def _assess_reading_level(self, content: str) -> str:
        """Assess the reading level of content."""
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        if not sentences:
            return "basic"
        
        words = content.split()
        avg_sentence_length = len(words) / len(sentences)
        
        # Simple heuristic based on sentence length and technical terms
        technical_terms = ['implementation', 'algorithm', 'optimization', 'configuration', 'architecture']
        technical_count = sum(1 for term in technical_terms if term in content.lower())
        
        if avg_sentence_length > 25 or technical_count > 5:
            return "advanced"
        elif avg_sentence_length > 15 or technical_count > 2:
            return "intermediate"
        else:
            return "basic"
    
    def _generate_screen_reader_text(self, response: FormattedResponse) -> str:
        """Generate optimized text for screen readers."""
        screen_reader_parts = []
        
        # Add content overview
        screen_reader_parts.append(f"Response with {len(response.sections)} sections.")
        
        # Add navigation information
        if response.navigation_aids:
            nav_types = [aid.type for aid in response.navigation_aids]
            screen_reader_parts.append(f"Navigation aids available: {', '.join(nav_types)}.")
        
        # Add reading time
        if response.estimated_reading_time:
            screen_reader_parts.append(f"Estimated reading time: {response.estimated_reading_time} minutes.")
        
        return " ".join(screen_reader_parts)
    
    def _generate_keyboard_navigation_hints(self, response: FormattedResponse) -> List[str]:
        """Generate keyboard navigation hints."""
        hints = []
        
        if any(s.section_type == ContentType.CODE for s in response.sections):
            hints.append("Use Tab to navigate between code blocks")
        
        if response.navigation_aids:
            hints.append("Use arrow keys to navigate table of contents")
        
        if len(response.sections) > 5:
            hints.append("Use Ctrl+F to search within the response")
        
        return hints
    
    async def apply_responsive_formatting(self, response: FormattedResponse, context: FormattingContext) -> str:
        """Apply responsive formatting based on display context."""
        try:
            if context.display_context == DisplayContext.MOBILE:
                return self._format_for_mobile(response)
            elif context.display_context == DisplayContext.TABLET:
                return self._format_for_tablet(response)
            elif context.display_context == DisplayContext.TERMINAL:
                return self._format_for_terminal(response)
            elif context.display_context == DisplayContext.PRINT:
                return self._format_for_print(response)
            elif context.display_context == DisplayContext.API:
                return self._format_for_api(response)
            else:  # Desktop
                return self._format_for_desktop(response)
                
        except Exception as e:
            logger.error(f"Error applying responsive formatting: {e}")
            return response.content
    
    def _format_for_mobile(self, response: FormattedResponse) -> str:
        """Format response for mobile display."""
        formatted_parts = []
        
        # Add compact navigation for mobile
        if response.navigation_aids:
            formatted_parts.append("📋 **Quick Navigation**")
            for aid in response.navigation_aids:
                if aid.type == "toc":
                    # Simplified TOC for mobile
                    formatted_parts.append("• " + "\n• ".join([link["text"] for link in aid.links[:5]]))
                    if len(aid.links) > 5:
                        formatted_parts.append(f"... and {len(aid.links) - 5} more sections")
            formatted_parts.append("")
        
        # Format sections with mobile-friendly spacing
        for section in response.sections:
            if section.section_type == ContentType.CODE:
                # Wrap long code lines for mobile
                formatted_parts.append("```" + section.metadata.get('language', ''))
                code_lines = section.content.split('\n')
                for line in code_lines:
                    if len(line) > 60:  # Wrap long lines
                        formatted_parts.append(line[:60] + "...")
                    else:
                        formatted_parts.append(line)
                formatted_parts.append("```")
            else:
                # Add extra spacing for readability on mobile
                formatted_parts.append(section.content)
            formatted_parts.append("")  # Extra spacing between sections
        
        return "\n".join(formatted_parts)
    
    def _format_for_tablet(self, response: FormattedResponse) -> str:
        """Format response for tablet display."""
        # Similar to desktop but with slightly more compact formatting
        return self._format_for_desktop(response)
    
    def _format_for_terminal(self, response: FormattedResponse) -> str:
        """Format response for terminal display."""
        formatted_parts = []
        
        # Use ASCII art for headers
        formatted_parts.append("=" * 60)
        formatted_parts.append("RESPONSE")
        formatted_parts.append("=" * 60)
        
        # Simple text formatting without HTML/Markdown
        for section in response.sections:
            if section.navigation_id:
                # Header sections
                formatted_parts.append("")
                formatted_parts.append("-" * 40)
                formatted_parts.append(section.content.strip())
                formatted_parts.append("-" * 40)
            elif section.section_type == ContentType.CODE:
                # Code blocks with simple borders
                formatted_parts.append("")
                formatted_parts.append("┌" + "─" * 58 + "┐")
                for line in section.content.split('\n'):
                    formatted_parts.append(f"│ {line:<56} │")
                formatted_parts.append("└" + "─" * 58 + "┘")
            else:
                # Regular text with word wrapping
                words = section.content.split()
                line = ""
                for word in words:
                    if len(line + word) > 70:
                        formatted_parts.append(line.strip())
                        line = word + " "
                    else:
                        line += word + " "
                if line.strip():
                    formatted_parts.append(line.strip())
        
        formatted_parts.append("")
        formatted_parts.append("=" * 60)
        
        return "\n".join(formatted_parts)
    
    def _format_for_print(self, response: FormattedResponse) -> str:
        """Format response for print display."""
        formatted_parts = []
        
        # Add print header with timestamp
        formatted_parts.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        formatted_parts.append("=" * 80)
        formatted_parts.append("")
        
        # Add table of contents for print
        if response.navigation_aids:
            for aid in response.navigation_aids:
                if aid.type == "toc":
                    formatted_parts.append("TABLE OF CONTENTS")
                    formatted_parts.append("-" * 20)
                    for i, link in enumerate(aid.links, 1):
                        formatted_parts.append(f"{i:2d}. {link['text']}")
                    formatted_parts.append("")
                    break
        
        # Format content with page-friendly layout
        for section in response.sections:
            formatted_parts.append(section.content)
            formatted_parts.append("")  # Space between sections
        
        # Add footer
        formatted_parts.append("=" * 80)
        if response.estimated_reading_time:
            formatted_parts.append(f"Estimated reading time: {response.estimated_reading_time} minutes")
        
        return "\n".join(formatted_parts)
    
    def _format_for_api(self, response: FormattedResponse) -> str:
        """Format response for API consumption (structured JSON)."""
        api_response = {
            "content": response.content,
            "format_type": response.format_type.value,
            "sections": [
                {
                    "content": section.content,
                    "type": section.section_type.value,
                    "priority": section.priority,
                    "metadata": section.metadata,
                    "navigation_id": section.navigation_id
                }
                for section in response.sections
            ],
            "navigation_aids": [
                {
                    "type": aid.type,
                    "content": aid.content,
                    "links": aid.links,
                    "position": aid.position
                }
                for aid in response.navigation_aids
            ],
            "accessibility_features": response.accessibility_features,
            "metadata": response.metadata,
            "estimated_reading_time": response.estimated_reading_time
        }
        
        return json.dumps(api_response, indent=2)
    
    def _format_for_desktop(self, response: FormattedResponse) -> str:
        """Format response for desktop display."""
        formatted_parts = []
        
        # Add navigation aids at the top
        for aid in response.navigation_aids:
            if aid.position == "top":
                formatted_parts.append(aid.content)
                formatted_parts.append("")
        
        # Format main content
        for section in response.sections:
            formatted_parts.append(section.content)
            formatted_parts.append("")
        
        # Add bottom navigation aids
        for aid in response.navigation_aids:
            if aid.position == "bottom":
                formatted_parts.append(aid.content)
                formatted_parts.append("")
        
        return "\n".join(formatted_parts)
    
    async def format_response(self, content: str, context: FormattingContext) -> FormattedResponse:
        """Main method to format a response with all optimizations applied."""
        try:
            logger.info(f"Starting advanced formatting for {len(content)} characters")
            
            # Analyze content structure
            analysis = await self.analyze_content_structure(content)
            
            # Select optimal format
            format_type = await self.select_optimal_format(content, context)
            
            # Organize content hierarchically
            sections = await self.organize_content_hierarchically(content)
            
            # Apply syntax highlighting to code sections
            for section in sections:
                if section.section_type == ContentType.CODE:
                    language = section.metadata.get('language', 'text')
                    section.content = await self.apply_syntax_highlighting(section.content, language)
            
            # Create navigation aids
            navigation_aids = await self.create_navigation_aids(sections, context)
            
            # Create initial formatted response
            formatted_response = FormattedResponse(
                content=content,
                format_type=format_type,
                sections=sections,
                navigation_aids=navigation_aids,
                accessibility_features={},
                metadata=analysis,
                estimated_reading_time=analysis.get('reading_time', 1)
            )
            
            # Add accessibility features
            accessibility_features = await self.add_accessibility_features(formatted_response, context)
            formatted_response.accessibility_features = accessibility_features
            
            # Apply responsive formatting
            final_content = await self.apply_responsive_formatting(formatted_response, context)
            formatted_response.content = final_content
            
            logger.info(f"Advanced formatting completed: {format_type.value} with {len(sections)} sections")
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error in format_response: {e}")
            # Return basic formatted response on error
            return FormattedResponse(
                content=content,
                format_type=FormatType.PLAIN_TEXT,
                sections=[ContentSection(content=content, section_type=ContentType.TEXT)],
                navigation_aids=[],
                accessibility_features={},
                metadata={}
            )