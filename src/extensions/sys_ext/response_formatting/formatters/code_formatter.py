"""
Code Response Formatter Plugin

This formatter provides intelligent formatting for code-related responses,
including syntax highlighting, step-by-step instructions, and code explanations.
Integrates with the existing theme manager for consistent styling.
"""

import logging
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Import from parent directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from base import ResponseFormatter, ResponseContext, FormattedResponse, ContentType, FormattingError

logger = logging.getLogger(__name__)


@dataclass
class CodeBlock:
    """Data structure for code block information."""
    language: str
    code: str
    line_numbers: bool = True
    filename: Optional[str] = None
    description: Optional[str] = None


@dataclass
class CodeInfo:
    """Data structure for code-related information."""
    title: Optional[str] = None
    description: Optional[str] = None
    code_blocks: List[CodeBlock] = None
    steps: List[str] = None
    language: Optional[str] = None
    complexity: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.code_blocks is None:
            self.code_blocks = []
        if self.steps is None:
            self.steps = []
        if self.tags is None:
            self.tags = []


class CodeResponseFormatter(ResponseFormatter):
    """
    Formatter for code-related responses.
    
    This formatter detects code information in responses and formats them
    with syntax highlighting, step-by-step instructions, and explanations.
    """
    
    def __init__(self):
        super().__init__("code", "1.0.0")
        
        # Language detection patterns
        self._language_patterns = {
            'python': [
                r'def\s+\w+\s*\(',
                r'import\s+\w+',
                r'from\s+\w+\s+import',
                r'if\s+__name__\s*==\s*["\']__main__["\']',
                r'print\s*\(',
                r'class\s+\w+\s*\(',
                r'\.py\b'
            ],
            'javascript': [
                r'function\s+\w+\s*\(',
                r'const\s+\w+\s*=',
                r'let\s+\w+\s*=',
                r'var\s+\w+\s*=',
                r'console\.log\s*\(',
                r'\.js\b',
                r'=>\s*{',
                r'require\s*\(',
                r'module\.exports',
                r'function\s*\(',
                r'return\s+`',
                r'`[^`]*\$\{[^}]*\}[^`]*`'  # Template literals
            ],
            'java': [
                r'public\s+class\s+\w+',
                r'public\s+static\s+void\s+main',
                r'System\.out\.println',
                r'import\s+java\.',
                r'\.java\b',
                r'@Override',
                r'extends\s+\w+',
                r'implements\s+\w+'
            ],
            'cpp': [
                r'#include\s*<\w+>',
                r'int\s+main\s*\(',
                r'std::\w+',
                r'cout\s*<<',
                r'cin\s*>>',
                r'\.cpp\b',
                r'\.h\b',
                r'using\s+namespace'
            ],
            'c': [
                r'#include\s*<\w+\.h>',
                r'int\s+main\s*\(',
                r'printf\s*\(',
                r'scanf\s*\(',
                r'\.c\b',
                r'malloc\s*\(',
                r'free\s*\('
            ],
            'html': [
                r'<html>',
                r'<head>',
                r'<body>',
                r'<div\s+class=',
                r'<script>',
                r'<style>',
                r'\.html\b',
                r'<!DOCTYPE'
            ],
            'css': [
                r'\.\w+\s*{',
                r'#\w+\s*{',
                r'@media\s*\(',
                r'font-family\s*:',
                r'background-color\s*:',
                r'\.css\b',
                r'@import'
            ],
            'sql': [
                r'SELECT\s+.*\s+FROM',
                r'INSERT\s+INTO',
                r'UPDATE\s+.*\s+SET',
                r'DELETE\s+FROM',
                r'CREATE\s+TABLE',
                r'ALTER\s+TABLE',
                r'\.sql\b'
            ],
            'bash': [
                r'#!/bin/bash',
                r'#!/bin/sh',
                r'\$\w+',
                r'echo\s+',
                r'grep\s+',
                r'awk\s+',
                r'sed\s+',
                r'\.sh\b'
            ],
            'json': [
                r'^\s*{',
                r'^\s*\[',
                r'"\w+"\s*:',
                r'\.json\b'
            ],
            'yaml': [
                r'^\w+\s*:',
                r'^\s*-\s+\w+',
                r'\.yaml\b',
                r'\.yml\b'
            ],
            'xml': [
                r'<\?xml',
                r'<\w+>.*</\w+>',
                r'\.xml\b'
            ]
        }
        
        # Code block patterns
        self._code_block_patterns = [
            r'```(\w+)?\n(.*?)\n```',  # Markdown code blocks
            r'`([^`]+)`',  # Inline code
            r'<code>(.*?)</code>',  # HTML code tags
            r'<pre>(.*?)</pre>',  # HTML pre tags
        ]
        
        # Step patterns
        self._step_patterns = [
            r'(?:Step\s+\d+|^\d+\.)\s*[:\-]?\s*(.+)',
            r'(?:First|Second|Third|Fourth|Fifth|Next|Then|Finally)[,:]?\s*(.+)',
            r'^\s*[-*]\s*(.+)',  # Bullet points
        ]
    
    def can_format(self, content: str, context: ResponseContext) -> bool:
        """
        Determine if this formatter can handle code-related content.
        
        Args:
            content: The response content to check
            context: Additional context information
            
        Returns:
            True if content appears to be code-related
        """
        if not self.validate_content(content, context):
            return False
        
        # Check if content type is already detected as code
        if context.detected_content_type == ContentType.CODE:
            return True
        
        # Look for code-related keywords and patterns
        content_lower = content.lower()
        code_keywords = [
            'code', 'programming', 'function', 'variable', 'class', 'method',
            'algorithm', 'debug', 'error', 'syntax', 'compile', 'execute',
            'script', 'python', 'javascript', 'java', 'html', 'css', 'sql',
            'api', 'database', 'framework', 'library', 'import', 'return'
        ]
        
        keyword_count = sum(1 for keyword in code_keywords if keyword in content_lower)
        
        # Check for code blocks
        code_block_count = sum(1 for pattern in self._code_block_patterns 
                              if re.search(pattern, content, re.DOTALL | re.IGNORECASE))
        
        # Check for programming language patterns
        language_matches = 0
        for lang, patterns in self._language_patterns.items():
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                language_matches += 1
        
        # Require code blocks or strong language indicators
        if code_block_count >= 1:
            return True
        elif language_matches >= 2 and keyword_count >= 2:
            return True
        elif keyword_count >= 3 and language_matches >= 1:
            return True
        elif keyword_count >= 2:  # More lenient for programming content
            return True
        
        return False
    
    def format_response(self, content: str, context: ResponseContext) -> FormattedResponse:
        """
        Format code-related content with syntax highlighting and explanations.
        
        Args:
            content: The response content to format
            context: Additional context information
            
        Returns:
            FormattedResponse with code formatting
            
        Raises:
            FormattingError: If formatting fails
        """
        try:
            if not self.can_format(content, context):
                raise FormattingError("Content is not code-related", self.name)
            
            # Extract code information from content
            code_info = self._extract_code_info(content)
            
            # Generate formatted HTML
            formatted_html = self._generate_code_html(code_info, context)
            
            # Determine CSS classes based on theme
            css_classes = self._get_css_classes(context)
            
            return FormattedResponse(
                content=formatted_html,
                content_type=ContentType.CODE,
                theme_requirements=self.get_theme_requirements(),
                metadata={
                    "formatter": self.name,
                    "title": code_info.title,
                    "language": code_info.language,
                    "code_blocks_count": len(code_info.code_blocks),
                    "steps_count": len(code_info.steps),
                    "complexity": code_info.complexity,
                    "tags": code_info.tags
                },
                css_classes=css_classes,
                has_images=False,
                has_interactive_elements=True  # Code blocks are interactive
            )
            
        except Exception as e:
            self.logger.error(f"Code formatting failed: {e}")
            raise FormattingError(f"Failed to format code content: {e}", self.name, e)
    
    def get_theme_requirements(self) -> List[str]:
        """
        Get theme requirements for code formatting.
        
        Returns:
            List of required theme components
        """
        return [
            "typography",
            "spacing",
            "colors",
            "code_blocks",
            "syntax_highlighting",
            "buttons",
            "cards"
        ]
    
    def get_supported_content_types(self) -> List[ContentType]:
        """
        Get supported content types.
        
        Returns:
            List containing CODE content type
        """
        return [ContentType.CODE]
    
    def get_confidence_score(self, content: str, context: ResponseContext) -> float:
        """
        Get confidence score for code content formatting.
        
        Args:
            content: The response content
            context: Additional context information
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not self.can_format(content, context):
            return 0.0
        
        score = 0.0
        content_lower = content.lower()
        
        # High confidence indicators
        if context.detected_content_type == ContentType.CODE:
            score += 0.4
        
        # Code block patterns
        code_block_matches = sum(1 for pattern in self._code_block_patterns 
                               if re.search(pattern, content, re.DOTALL | re.IGNORECASE))
        score += min(code_block_matches * 0.2, 0.4)
        
        # Programming language patterns
        language_matches = 0
        for lang, patterns in self._language_patterns.items():
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in patterns):
                language_matches += 1
        score += min(language_matches * 0.1, 0.3)
        
        # Code keywords
        code_keywords = ['code', 'function', 'variable', 'class', 'method', 'algorithm']
        keyword_matches = sum(1 for keyword in code_keywords if keyword in content_lower)
        score += min(keyword_matches * 0.05, 0.2)
        
        return min(score, 1.0)
    
    def _extract_code_info(self, content: str) -> CodeInfo:
        """
        Extract code information from response content.
        
        Args:
            content: The response content
            
        Returns:
            CodeInfo object with extracted data
        """
        code_info = CodeInfo()
        
        # Extract title (look for headings or first line)
        title_patterns = [
            r'^#\s*(.+)',  # Markdown heading
            r'^(.+)\n[=\-]{3,}',  # Underlined heading
            r'(?i)^(?:how to|tutorial|guide|example)[:\-]?\s*(.+)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                code_info.title = match.group(1).strip()
                break
        
        if not code_info.title:
            # Generate title from content
            if 'function' in content.lower():
                code_info.title = "Function Implementation"
            elif 'class' in content.lower():
                code_info.title = "Class Definition"
            elif 'algorithm' in content.lower():
                code_info.title = "Algorithm Implementation"
            else:
                code_info.title = "Code Example"
        
        # Extract code blocks
        code_info.code_blocks = self._extract_code_blocks(content)
        
        # Detect primary language
        code_info.language = self._detect_primary_language(content)
        
        # Extract steps/instructions
        code_info.steps = self._extract_steps(content)
        
        # Extract description
        code_info.description = self._extract_description(content)
        
        # Determine complexity
        code_info.complexity = self._determine_complexity(content, code_info)
        
        # Extract tags
        code_info.tags = self._extract_tags(content, code_info)
        
        return code_info
    
    def _extract_code_blocks(self, content: str) -> List[CodeBlock]:
        """
        Extract code blocks from content.
        
        Args:
            content: The response content
            
        Returns:
            List of CodeBlock objects
        """
        code_blocks = []
        
        # Extract markdown code blocks
        markdown_pattern = r'```(\w+)?\n(.*?)\n```'
        for match in re.finditer(markdown_pattern, content, re.DOTALL):
            language = match.group(1) or self._detect_language_from_code(match.group(2))
            code = match.group(2).strip()
            if code:
                code_blocks.append(CodeBlock(
                    language=language,
                    code=code,
                    line_numbers=len(code.split('\n')) > 3
                ))
        
        # Extract inline code if no blocks found
        if not code_blocks:
            inline_pattern = r'`([^`]+)`'
            inline_matches = re.findall(inline_pattern, content)
            for code in inline_matches:
                if len(code.strip()) > 15:  # Only longer inline code
                    language = self._detect_language_from_code(code)
                    code_blocks.append(CodeBlock(
                        language=language,
                        code=code.strip(),
                        line_numbers=False
                    ))
        
        # If still no code blocks, try to extract from plain text
        if not code_blocks:
            code_blocks.extend(self._extract_plain_text_code(content))
        
        return code_blocks
    
    def _extract_plain_text_code(self, content: str) -> List[CodeBlock]:
        """
        Extract code from plain text content.
        
        Args:
            content: The response content
            
        Returns:
            List of CodeBlock objects
        """
        code_blocks = []
        lines = content.split('\n')
        
        # Look for indented code blocks
        current_block = []
        in_code_block = False
        
        for line in lines:
            if line.strip() and (line.startswith('    ') or line.startswith('\t')):
                # Indented line - likely code
                current_block.append(line)
                in_code_block = True
            elif in_code_block and not line.strip():
                # Empty line in code block
                current_block.append(line)
            else:
                # End of code block
                if current_block and len(current_block) >= 2:
                    code = '\n'.join(current_block).strip()
                    language = self._detect_language_from_code(code)
                    code_blocks.append(CodeBlock(
                        language=language,
                        code=code,
                        line_numbers=len(current_block) > 3
                    ))
                current_block = []
                in_code_block = False
        
        # Handle final block
        if current_block and len(current_block) >= 2:
            code = '\n'.join(current_block).strip()
            language = self._detect_language_from_code(code)
            code_blocks.append(CodeBlock(
                language=language,
                code=code,
                line_numbers=len(current_block) > 3
            ))
        
        return code_blocks
    
    def _detect_language_from_code(self, code: str) -> str:
        """
        Detect programming language from code content.
        
        Args:
            code: Code content
            
        Returns:
            Detected language name
        """
        code_lower = code.lower()
        
        # Score each language
        language_scores = {}
        for lang, patterns in self._language_patterns.items():
            score = sum(1 for pattern in patterns if re.search(pattern, code, re.IGNORECASE))
            if score > 0:
                language_scores[lang] = score
        
        if language_scores:
            best_lang = max(language_scores, key=language_scores.get)
            # Only return detected language if we have a reasonable confidence
            if language_scores[best_lang] >= 1:
                return best_lang
        
        return 'text'
    
    def _detect_primary_language(self, content: str) -> Optional[str]:
        """
        Detect the primary programming language in the content.
        
        Args:
            content: The response content
            
        Returns:
            Primary language name or None
        """
        language_scores = {}
        
        for lang, patterns in self._language_patterns.items():
            score = sum(1 for pattern in patterns if re.search(pattern, content, re.IGNORECASE))
            if score > 0:
                language_scores[lang] = score
        
        if language_scores:
            return max(language_scores, key=language_scores.get)
        
        return None
    
    def _extract_steps(self, content: str) -> List[str]:
        """
        Extract step-by-step instructions from content.
        
        Args:
            content: The response content
            
        Returns:
            List of step descriptions
        """
        steps = []
        
        for pattern in self._step_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                step = match.strip()
                if len(step) > 10 and step not in steps:  # Avoid duplicates and short steps
                    steps.append(step)
        
        return steps[:10]  # Limit to 10 steps
    
    def _extract_description(self, content: str) -> Optional[str]:
        """
        Extract description from content.
        
        Args:
            content: The response content
            
        Returns:
            Description text or None
        """
        # Look for description patterns
        desc_patterns = [
            r'(?i)description[:\-]?\s*(.+?)(?:\n\n|\n#|\n```)',
            r'(?i)this\s+(?:code|function|class|script)\s+(.+?)(?:\n\n|\n#|\n```)',
            r'(?i)explanation[:\-]?\s*(.+?)(?:\n\n|\n#|\n```)',
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                desc = match.group(1).strip()
                if len(desc) > 20:
                    return desc[:200] + ('...' if len(desc) > 200 else '')
        
        # Fallback: use first paragraph
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if len(para) > 30 and not re.search(r'^```|^#|^\d+\.', para):
                return para[:200] + ('...' if len(para) > 200 else '')
        
        return None
    
    def _determine_complexity(self, content: str, code_info: CodeInfo) -> str:
        """
        Determine code complexity level.
        
        Args:
            content: The response content
            code_info: Extracted code information
            
        Returns:
            Complexity level (Beginner, Intermediate, Advanced)
        """
        complexity_score = 0
        
        # Check for advanced patterns
        advanced_patterns = [
            r'class\s+\w+.*:',  # Classes
            r'async\s+def',  # Async functions
            r'try\s*:.*except',  # Exception handling
            r'import\s+\w+\.\w+',  # Complex imports
            r'@\w+',  # Decorators
            r'lambda\s+',  # Lambda functions
            r'yield\s+',  # Generators
            r'with\s+\w+.*:',  # Context managers
        ]
        
        for pattern in advanced_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                complexity_score += 2
        
        # Check for intermediate patterns
        intermediate_patterns = [
            r'def\s+\w+.*:',  # Functions
            r'for\s+\w+\s+in',  # Loops
            r'if\s+.*:',  # Conditionals
            r'while\s+.*:',  # While loops
            r'import\s+\w+',  # Imports
        ]
        
        for pattern in intermediate_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                complexity_score += 1
        
        # Consider code length
        total_code_lines = sum(len(block.code.split('\n')) for block in code_info.code_blocks)
        if total_code_lines > 50:
            complexity_score += 2
        elif total_code_lines > 20:
            complexity_score += 1
        
        # Determine level
        if complexity_score >= 6:
            return "Advanced"
        elif complexity_score >= 3:
            return "Intermediate"
        else:
            return "Beginner"
    
    def _extract_tags(self, content: str, code_info: CodeInfo) -> List[str]:
        """
        Extract relevant tags from content.
        
        Args:
            content: The response content
            code_info: Extracted code information
            
        Returns:
            List of tags
        """
        tags = []
        
        # Add language tag
        if code_info.language:
            tags.append(code_info.language)
        
        # Add complexity tag
        if code_info.complexity:
            tags.append(code_info.complexity.lower())
        
        # Add concept tags
        concept_patterns = {
            'algorithm': r'\balgorithm\b',
            'data-structure': r'\b(?:array|list|dict|tree|graph|stack|queue|data.structure)\b',
            'web-development': r'\b(?:html|css|javascript|react|vue|angular)\b',
            'database': r'\b(?:sql|database|query|table)\b',
            'api': r'\b(?:api|rest|endpoint|request|response)\b',
            'testing': r'\b(?:test|testing|unittest|pytest)\b',
            'debugging': r'\b(?:debug|error|exception|bug)\b',
            'optimization': r'\b(?:optimize|performance|efficient)\b',
        }
        
        content_lower = content.lower()
        for tag, pattern in concept_patterns.items():
            if re.search(pattern, content_lower):
                tags.append(tag)
        
        return tags[:5]  # Limit to 5 tags
    
    def _generate_code_html(self, code_info: CodeInfo, context: ResponseContext) -> str:
        """
        Generate HTML for code display.
        
        Args:
            code_info: Extracted code information
            context: Response context for theming
            
        Returns:
            Formatted HTML string
        """
        # Get theme context
        theme_name = context.theme_context.get('current_theme', 'light')
        
        # Build code response HTML
        html_parts = []
        
        # Container
        html_parts.append('<div class="code-response response-card">')
        
        # Header
        html_parts.append('<div class="code-header">')
        html_parts.append(f'<h2 class="code-title">{self._escape_html(code_info.title)}</h2>')
        
        # Tags
        if code_info.tags:
            html_parts.append('<div class="code-tags">')
            for tag in code_info.tags:
                html_parts.append(f'<span class="code-tag">{self._escape_html(tag)}</span>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        # Description
        if code_info.description:
            html_parts.append('<div class="code-description">')
            html_parts.append(f'<p>{self._escape_html(code_info.description)}</p>')
            html_parts.append('</div>')
        
        # Steps (if any)
        if code_info.steps:
            html_parts.append('<div class="code-steps">')
            html_parts.append('<h3 class="steps-title">Steps:</h3>')
            html_parts.append('<ol class="steps-list">')
            for step in code_info.steps:
                html_parts.append(f'<li class="step-item">{self._escape_html(step)}</li>')
            html_parts.append('</ol>')
            html_parts.append('</div>')
        
        # Code blocks
        if code_info.code_blocks:
            html_parts.append('<div class="code-blocks">')
            for i, block in enumerate(code_info.code_blocks):
                html_parts.append(self._generate_code_block_html(block, i, theme_name))
            html_parts.append('</div>')
        
        # Metadata
        html_parts.append('<div class="code-metadata">')
        if code_info.language:
            html_parts.append(f'<span class="metadata-item">Language: <strong>{code_info.language}</strong></span>')
        if code_info.complexity:
            html_parts.append(f'<span class="metadata-item">Complexity: <strong>{code_info.complexity}</strong></span>')
        html_parts.append('</div>')
        
        # Add theme-specific styling
        html_parts.append(self._generate_theme_styles(theme_name))
        
        # Add JavaScript for copy functionality
        html_parts.append(self._generate_copy_script())
        
        html_parts.append('</div>')  # Close code-response
        
        return '\n'.join(html_parts)
    
    def _generate_code_block_html(self, block: CodeBlock, index: int, theme_name: str) -> str:
        """
        Generate HTML for a single code block.
        
        Args:
            block: CodeBlock object
            index: Block index
            theme_name: Current theme name
            
        Returns:
            HTML for code block
        """
        html_parts = []
        
        # Code block container
        html_parts.append(f'<div class="code-block" data-language="{block.language}">')
        
        # Header with language and copy button
        html_parts.append('<div class="code-block-header">')
        html_parts.append(f'<span class="code-language">{block.language}</span>')
        if block.filename:
            html_parts.append(f'<span class="code-filename">{self._escape_html(block.filename)}</span>')
        html_parts.append(f'<Button class="copy-button" onclick="copyCodeToClipboard(this, {index})">Copy</Button>')
        html_parts.append('</div>')
        
        # Code content
        html_parts.append('<div class="code-content">')
        if block.line_numbers:
            html_parts.append(self._generate_code_with_line_numbers(block.code))
        else:
            html_parts.append(f'<pre class="code-pre"><code class="language-{block.language}">{self._escape_html(block.code)}</code></pre>')
        html_parts.append('</div>')
        
        # Description
        if block.description:
            html_parts.append('<div class="code-block-description">')
            html_parts.append(f'<p>{self._escape_html(block.description)}</p>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')  # Close code-block
        
        return '\n'.join(html_parts)
    
    def _generate_code_with_line_numbers(self, code: str) -> str:
        """
        Generate code HTML with line numbers.
        
        Args:
            code: Code content
            
        Returns:
            HTML with line numbers
        """
        lines = code.split('\n')
        html_parts = []
        
        html_parts.append('<div class="code-with-lines">')
        html_parts.append('<div class="line-numbers">')
        for i in range(1, len(lines) + 1):
            html_parts.append(f'<span class="line-number">{i}</span>')
        html_parts.append('</div>')
        
        html_parts.append('<div class="code-lines">')
        for line in lines:
            html_parts.append(f'<div class="code-line">{self._escape_html(line)}</div>')
        html_parts.append('</div>')
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _get_css_classes(self, context: ResponseContext) -> List[str]:
        """
        Get CSS classes based on theme context.
        
        Args:
            context: Response context
            
        Returns:
            List of CSS classes
        """
        base_classes = [
            "response-formatted",
            "code-response",
            "themed-content"
        ]
        
        # Add theme-specific classes
        theme_name = context.theme_context.get('current_theme', 'light')
        base_classes.append(f"theme-{theme_name}")
        
        return base_classes
    
    def _generate_theme_styles(self, theme_name: str) -> str:
        """
        Generate theme-specific CSS styles.
        
        Args:
            theme_name: Name of the current theme
            
        Returns:
            CSS style block
        """
        # Import design tokens
        try:
            from ui_logic.themes.design_tokens import COLORS, SPACING, FONTS
            
            colors = COLORS.get(theme_name, COLORS['light'])
            
            css = f"""
            <style>
            .code-response {{
                background: {colors['surface']};
                border: 1px solid {colors.get('border', '#e0e0e0')};
                border-radius: 12px;
                padding: {SPACING['lg']};
                margin: {SPACING['md']} 0;
                font-family: {FONTS['base']};
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                max-width: 800px;
            }}
            
            .code-header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: {SPACING['md']};
                border-bottom: 2px solid {colors['accent']};
                padding-bottom: {SPACING['sm']};
            }}
            
            .code-title {{
                color: {colors.get('text', '#333')};
                margin: 0;
                font-size: 1.5em;
                font-weight: 600;
            }}
            
            .code-tags {{
                display: flex;
                gap: {SPACING['xs']};
                flex-wrap: wrap;
            }}
            
            .code-tag {{
                background: {colors['accent']};
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.8em;
                font-weight: 500;
            }}
            
            .code-description {{
                background: {colors.get('background', '#fff')};
                border-radius: 8px;
                padding: {SPACING['md']};
                margin-bottom: {SPACING['md']};
                border-left: 4px solid {colors['accent']};
            }}
            
            .code-description p {{
                color: {colors.get('text', '#333')};
                margin: 0;
                line-height: 1.6;
            }}
            
            .code-steps {{
                margin-bottom: {SPACING['md']};
            }}
            
            .steps-title {{
                color: {colors['accent']};
                margin: 0 0 {SPACING['sm']} 0;
                font-size: 1.2em;
                font-weight: 600;
            }}
            
            .steps-list {{
                margin: 0;
                padding-left: {SPACING['lg']};
            }}
            
            .step-item {{
                color: {colors.get('text', '#333')};
                margin-bottom: {SPACING['xs']};
                line-height: 1.5;
            }}
            
            .code-blocks {{
                margin-bottom: {SPACING['md']};
            }}
            
            .code-block {{
                background: {colors.get('code_background', '#f8f9fa')};
                border: 1px solid {colors.get('border', '#e0e0e0')};
                border-radius: 8px;
                margin-bottom: {SPACING['md']};
                overflow: hidden;
            }}
            
            .code-block-header {{
                background: {colors.get('code_header_bg', '#f1f3f4')};
                padding: {SPACING['sm']} {SPACING['md']};
                display: flex;
                align-items: center;
                justify-content: space-between;
                border-bottom: 1px solid {colors.get('border', '#e0e0e0')};
            }}
            
            .code-language {{
                font-weight: 600;
                color: {colors['accent']};
                text-transform: uppercase;
                font-size: 0.9em;
            }}
            
            .code-filename {{
                color: {colors.get('text_secondary', '#666')};
                font-family: {FONTS.get('mono', 'monospace')};
                font-size: 0.9em;
            }}
            
            .copy-button {{
                background: {colors['accent']};
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.8em;
                font-weight: 500;
            }}
            
            .copy-button:hover {{
                opacity: 0.8;
            }}
            
            .code-content {{
                padding: {SPACING['md']};
                overflow-x: auto;
            }}
            
            .code-pre {{
                margin: 0;
                font-family: {FONTS.get('mono', 'monospace')};
                font-size: 0.9em;
                line-height: 1.5;
                color: {colors.get('text', '#333')};
                background: transparent;
            }}
            
            .code-with-lines {{
                display: flex;
                font-family: {FONTS.get('mono', 'monospace')};
                font-size: 0.9em;
                line-height: 1.5;
            }}
            
            .line-numbers {{
                background: {colors.get('line_numbers_bg', '#f0f0f0')};
                padding: 0 {SPACING['sm']};
                border-right: 1px solid {colors.get('border', '#e0e0e0')};
                color: {colors.get('text_secondary', '#666')};
                text-align: right;
                user-select: none;
                min-width: 40px;
            }}
            
            .line-number {{
                display: block;
            }}
            
            .code-lines {{
                flex: 1;
                padding: 0 {SPACING['md']};
                overflow-x: auto;
            }}
            
            .code-line {{
                color: {colors.get('text', '#333')};
                white-space: pre;
            }}
            
            .code-metadata {{
                display: flex;
                gap: {SPACING['md']};
                padding-top: {SPACING['sm']};
                border-top: 1px solid {colors.get('border', '#e0e0e0')};
                font-size: 0.9em;
            }}
            
            .metadata-item {{
                color: {colors.get('text_secondary', '#666')};
            }}
            
            .metadata-item strong {{
                color: {colors['accent']};
            }}
            
            .theme-dark .code-response {{
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }}
            
            .theme-dark .code-block {{
                background: #1e1e1e;
                border-color: #333;
            }}
            
            .theme-dark .code-block-header {{
                background: #2d2d2d;
                border-color: #333;
            }}
            
            .theme-dark .line-numbers {{
                background: #2d2d2d;
                border-color: #333;
            }}
            
            .theme-enterprise .code-response {{
                border-color: {colors.get('border', '#d0d0d0')};
            }}
            </style>
            
            <script>
            function copyCode(index) {{
                const codeBlocks = document.querySelectorAll('.code-block');
                const codeBlock = codeBlocks[index];
                const codeContent = codeBlock.querySelector('.code-pre code, .code-lines');
                
                if (codeContent) {{
                    const text = codeContent.textContent || codeContent.innerText;
                    navigator.clipboard.writeText(text).then(() => {{
                        const button = codeBlock.querySelector('.copy-button');
                        const originalText = button.textContent;
                        button.textContent = 'Copied!';
                        setTimeout(() => {{
                            button.textContent = originalText;
                        }}, 2000);
                    }});
                }}
            }}
            </script>
            """
            
            return css
            
        except ImportError:
            # Fallback styles if design tokens not available
            return """
            <style>
            .code-response {
                background: #fff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 16px;
                margin: 12px 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                max-width: 800px;
            }
            .code-title { color: #333; margin: 0; font-size: 1.5em; font-weight: 600; }
            .code-tag { background: #1e88e5; color: white; padding: 4px 8px; border-radius: 4px; }
            .code-block { background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; }
            .code-pre { font-family: monospace; }
            .copy-button { background: #1e88e5; color: white; border: none; padding: 4px 12px; border-radius: 4px; cursor: pointer; }
            </style>
            
            <script>
            function copyCode(index) {
                const codeBlocks = document.querySelectorAll('.code-block');
                const codeBlock = codeBlocks[index];
                const codeContent = codeBlock.querySelector('.code-pre code, .code-lines');
                
                if (codeContent) {
                    const text = codeContent.textContent || codeContent.innerText;
                    navigator.clipboard.writeText(text).then(() => {
                        const button = codeBlock.querySelector('.copy-button');
                        const originalText = button.textContent;
                        button.textContent = 'Copied!';
                        setTimeout(() => {
                            button.textContent = originalText;
                        }, 2000);
                    });
                }
            }
            </script>
            """
    
    def _generate_copy_script(self) -> str:
        """
        Generate JavaScript for copy functionality.
        
        Returns:
            JavaScript code for copy functionality
        """
        return """
        <script>
        function copyCodeToClipboard(button, blockIndex) {
            // Find the code block
            const codeBlock = button.closest('.code-block');
            if (!codeBlock) return;
            
            // Get the code content
            let codeText = '';
            const codeLines = codeBlock.querySelectorAll('.code-line');
            if (codeLines.length > 0) {
                // Code with line numbers
                codeText = Array.from(codeLines).map(line => line.textContent).join('\\n');
            } else {
                // Regular code block
                const codeElement = codeBlock.querySelector('code');
                if (codeElement) {
                    codeText = codeElement.textContent;
                }
            }
            
            // Copy to clipboard
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(codeText).then(() => {
                    showCopyFeedback(button, 'Copied!');
                }).catch(() => {
                    fallbackCopyTextToClipboard(codeText, button);
                });
            } else {
                fallbackCopyTextToClipboard(codeText, button);
            }
        }
        
        function fallbackCopyTextToClipboard(text, button) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                document.execCommand('copy');
                showCopyFeedback(button, 'Copied!');
            } catch (err) {
                showCopyFeedback(button, 'Copy failed');
            }
            
            document.body.removeChild(textArea);
        }
        
        function showCopyFeedback(button, message) {
            const originalText = button.textContent;
            button.textContent = message;
            button.disabled = true;
            
            setTimeout(() => {
                button.textContent = originalText;
                button.disabled = false;
            }, 2000);
        }
        </script>
        """
    
    def _escape_html(self, text: str) -> str:
        """
        Escape HTML characters in text.
        
        Args:
            text: Text to escape
            
        Returns:
            HTML-escaped text
        """
        if not text:
            return ""
        
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))