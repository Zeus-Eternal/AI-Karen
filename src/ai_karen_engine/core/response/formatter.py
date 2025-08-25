"""
DRY Formatter with CopilotKit hooks for consistent response formatting.

This module implements the DRYFormatter class that provides consistent output
structure (headings, code blocks, bullets) with optional CopilotKit enhancements
as purely additive features. Ensures graceful degradation when CopilotKit is
unavailable.
"""

import re
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from .protocols import ResponseFormatter
from .config import PipelineConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class FormattingOptions:
    """Options for response formatting."""
    
    enable_copilotkit: bool = True
    enable_code_highlighting: bool = True
    enable_structured_sections: bool = True
    enable_onboarding_format: bool = True
    max_code_block_lines: int = 50
    bullet_style: str = "•"  # Unicode bullet
    heading_style: str = "##"  # Markdown heading level
    
    # CopilotKit specific options
    copilotkit_complexity_graphs: bool = True
    copilotkit_inline_suggestions: bool = True
    copilotkit_ui_hints: bool = True


@dataclass
class FormattedResponse:
    """Structured response with formatting metadata."""
    
    content: str
    sections: Dict[str, str] = field(default_factory=dict)
    code_blocks: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    copilotkit_enhancements: Optional[Dict[str, Any]] = None


class DRYFormatter:
    """
    DRY (Don't Repeat Yourself) Formatter with CopilotKit hooks.
    
    Provides consistent output structure with optional CopilotKit enhancements
    that are purely additive and gracefully degrade when unavailable.
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the DRY formatter.
        
        Args:
            config: Pipeline configuration, uses default if None
        """
        self.config = config or DEFAULT_CONFIG
        self.options = FormattingOptions(
            enable_copilotkit=self.config.enable_copilotkit
        )
        self._copilotkit_available = self._check_copilotkit_availability()
    
    def format_response(
        self, 
        raw_response: str, 
        intent: str, 
        persona: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Format raw LLM response into structured output.
        
        Args:
            raw_response: Raw response from LLM
            intent: User intent
            persona: Selected persona
            **kwargs: Additional formatting options
            
        Returns:
            Formatted response dictionary
        """
        try:
            # Update options from kwargs
            options = self._merge_options(kwargs)
            
            # Parse and structure the response
            structured = self._parse_response_structure(raw_response)
            
            # Apply consistent formatting
            formatted_content = self._apply_consistent_formatting(
                structured, intent, persona, options
            )
            
            # Add CopilotKit enhancements if available and enabled
            copilotkit_enhancements = None
            if options.enable_copilotkit and self._copilotkit_available:
                copilotkit_enhancements = self._add_copilotkit_enhancements(
                    formatted_content, intent, persona, options
                )
            
            # Build final response
            response = {
                "content": formatted_content.content,
                "sections": formatted_content.sections,
                "code_blocks": formatted_content.code_blocks,
                "metadata": {
                    "intent": intent,
                    "persona": persona,
                    "formatter_version": "1.0",
                    "copilotkit_enabled": options.enable_copilotkit and self._copilotkit_available,
                    "formatting_applied": True,
                    **formatted_content.metadata
                }
            }
            
            # Add CopilotKit enhancements to response if available
            if copilotkit_enhancements:
                response["copilotkit"] = copilotkit_enhancements
            
            return response
            
        except Exception as e:
            logger.warning(f"Formatting failed, returning raw response: {e}")
            # Graceful degradation - return raw response
            return {
                "content": raw_response,
                "sections": {},
                "code_blocks": [],
                "metadata": {
                    "intent": intent,
                    "persona": persona,
                    "formatter_version": "1.0",
                    "copilotkit_enabled": False,
                    "formatting_applied": False,
                    "error": str(e)
                }
            }
    
    def _merge_options(self, kwargs: Dict[str, Any]) -> FormattingOptions:
        """Merge kwargs into formatting options."""
        options = FormattingOptions(
            enable_copilotkit=self.config.enable_copilotkit
        )
        
        # Override with kwargs
        for key, value in kwargs.items():
            if hasattr(options, key):
                setattr(options, key, value)
        
        return options
    
    def _parse_response_structure(self, raw_response: str) -> FormattedResponse:
        """Parse raw response into structured components."""
        sections = {}
        code_blocks = []
        metadata = {}
        
        # Extract code blocks first
        code_pattern = r'```(\w+)?\n(.*?)\n```'
        code_matches = re.findall(code_pattern, raw_response, re.DOTALL)
        
        for i, (language, code) in enumerate(code_matches):
            code_blocks.append({
                "id": f"code_block_{i}",
                "language": language or "text",
                "code": code.strip(),
                "line_count": len(code.strip().split('\n'))
            })
        
        # Remove code blocks from content for section parsing
        content_without_code = re.sub(code_pattern, f'[CODE_BLOCK_PLACEHOLDER]', raw_response, flags=re.DOTALL)
        
        # Extract sections based on common patterns
        sections = self._extract_sections(content_without_code)
        
        # Restore code blocks in content
        final_content = raw_response
        
        return FormattedResponse(
            content=final_content,
            sections=sections,
            code_blocks=code_blocks,
            metadata=metadata
        )
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract structured sections from content."""
        sections = {}
        
        # Split content into lines and process section by section
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Check if this line is a section header
            section_match = None
            if re.match(r'^##?\s*(?:Quick Plan|Plan)(?:\s*:)?\s*$', line, re.IGNORECASE):
                section_match = 'quick_plan'
            elif re.match(r'^##?\s*(?:Next Action|Next Step)(?:\s*:)?\s*$', line, re.IGNORECASE):
                section_match = 'next_action'
            elif re.match(r'^##?\s*(?:Optional Boost|Boost|Enhancement)(?:\s*:)?\s*$', line, re.IGNORECASE):
                section_match = 'optional_boost'
            elif re.match(r'^##?\s*(?:Summary|Overview)(?:\s*:)?\s*$', line, re.IGNORECASE):
                section_match = 'summary'
            elif re.match(r'^##?\s*(?:Details|Explanation)(?:\s*:)?\s*$', line, re.IGNORECASE):
                section_match = 'details'
            
            if section_match:
                # Save previous section if exists
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                current_section = section_match
                current_content = []
            elif current_section:
                # Add content to current section
                if line:  # Skip empty lines at start of section
                    current_content.append(line)
                elif current_content:  # Keep empty lines within content
                    current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _apply_consistent_formatting(
        self, 
        structured: FormattedResponse, 
        intent: str, 
        persona: str, 
        options: FormattingOptions
    ) -> FormattedResponse:
        """Apply consistent formatting rules."""
        content = structured.content
        
        # Apply heading formatting
        if options.enable_structured_sections:
            content = self._format_headings(content, options)
        
        # Apply bullet point formatting
        content = self._format_bullets(content, options)
        
        # Apply code block formatting
        if options.enable_code_highlighting:
            content = self._format_code_blocks(content, structured.code_blocks, options)
        
        # Apply onboarding format if needed
        if options.enable_onboarding_format and self._needs_onboarding_format(intent, structured.sections):
            content = self._apply_onboarding_format(content, structured.sections, options)
        
        # Update metadata
        structured.metadata.update({
            "headings_formatted": options.enable_structured_sections,
            "bullets_formatted": True,
            "code_highlighted": options.enable_code_highlighting,
            "onboarding_applied": options.enable_onboarding_format
        })
        
        return FormattedResponse(
            content=content,
            sections=structured.sections,
            code_blocks=structured.code_blocks,
            metadata=structured.metadata
        )
    
    def _format_headings(self, content: str, options: FormattingOptions) -> str:
        """Apply consistent heading formatting."""
        # Normalize heading levels
        heading_patterns = [
            (r'^(#{1,6})\s*(.+)$', lambda m: f"{options.heading_style} {m.group(2)}"),
            (r'^([A-Z][A-Za-z\s]+):?\s*$', lambda m: f"{options.heading_style} {m.group(1)}")
        ]
        
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            formatted_line = line
            for pattern, replacement in heading_patterns:
                if re.match(pattern, line.strip()):
                    if callable(replacement):
                        formatted_line = replacement(re.match(pattern, line.strip()))
                    else:
                        formatted_line = re.sub(pattern, replacement, line.strip())
                    break
            formatted_lines.append(formatted_line)
        
        return '\n'.join(formatted_lines)
    
    def _format_bullets(self, content: str, options: FormattingOptions) -> str:
        """Apply consistent bullet point formatting."""
        # Normalize bullet points
        bullet_patterns = [
            (r'^[\s]*[-*+]\s+(.+)$', f'{options.bullet_style} \\1'),
            (r'^[\s]*\d+\.\s+(.+)$', f'{options.bullet_style} \\1'),  # Convert numbered to bullets
        ]
        
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            formatted_line = line
            for pattern, replacement in bullet_patterns:
                if re.match(pattern, line):
                    formatted_line = re.sub(pattern, replacement, line)
                    break
            formatted_lines.append(formatted_line)
        
        return '\n'.join(formatted_lines)
    
    def _format_code_blocks(
        self, 
        content: str, 
        code_blocks: List[Dict[str, str]], 
        options: FormattingOptions
    ) -> str:
        """Apply consistent code block formatting."""
        # Process each code block and apply truncation if needed
        formatted_content = content
        
        for i, block in enumerate(code_blocks):
            language = block.get('language', 'text')
            code = block.get('code', '')
            original_pattern = f'```{language}?\n{re.escape(code)}\n```'
            
            # Truncate very long code blocks
            if block.get('line_count', 0) > options.max_code_block_lines:
                lines = code.split('\n')
                truncated_code = '\n'.join(lines[:options.max_code_block_lines])
                truncated_code += f'\n... ({block["line_count"] - options.max_code_block_lines} more lines)'
                
                # Replace the original code block with truncated version
                truncated_block = f'```{language}\n{truncated_code}\n```'
                
                # Find and replace the specific code block
                original_block_pattern = f'```{language}?\n.*?\n```'
                if re.search(original_block_pattern, formatted_content, re.DOTALL):
                    formatted_content = re.sub(
                        original_block_pattern, 
                        truncated_block, 
                        formatted_content, 
                        count=1, 
                        flags=re.DOTALL
                    )
        
        return formatted_content
    
    def _needs_onboarding_format(self, intent: str, sections: Dict[str, str]) -> bool:
        """Determine if onboarding format should be applied."""
        onboarding_intents = ['general_assist', 'setup_help', 'getting_started']
        has_onboarding_sections = any(key in sections for key in ['quick_plan', 'next_action'])
        
        return intent in onboarding_intents or has_onboarding_sections
    
    def _apply_onboarding_format(
        self, 
        content: str, 
        sections: Dict[str, str], 
        options: FormattingOptions
    ) -> str:
        """Apply structured onboarding format."""
        if not sections:
            return content
        
        # Build structured onboarding response
        onboarding_parts = []
        
        if 'quick_plan' in sections:
            onboarding_parts.append(f"{options.heading_style} Quick Plan\n{sections['quick_plan']}")
        
        if 'next_action' in sections:
            onboarding_parts.append(f"{options.heading_style} Next Action\n{sections['next_action']}")
        
        if 'optional_boost' in sections:
            onboarding_parts.append(f"{options.heading_style} Optional Boost\n{sections['optional_boost']}")
        
        # If we have onboarding sections, restructure the content
        if onboarding_parts:
            # Remove the sections from original content and add structured version
            structured_content = '\n\n'.join(onboarding_parts)
            
            # Add any remaining content that's not in sections
            remaining_content = content
            for section_content in sections.values():
                remaining_content = remaining_content.replace(section_content, '').strip()
            
            if remaining_content and remaining_content != content:
                structured_content = f"{remaining_content}\n\n{structured_content}"
            
            return structured_content
        
        return content
    
    def _check_copilotkit_availability(self) -> bool:
        """Check if CopilotKit is available and functional."""
        try:
            # Try to import CopilotKit related modules
            # This is a placeholder - actual implementation would check for CopilotKit
            # For now, we'll assume it's available if enabled in config
            return self.config.enable_copilotkit
        except ImportError:
            logger.debug("CopilotKit not available, disabling enhancements")
            return False
        except Exception as e:
            logger.warning(f"CopilotKit availability check failed: {e}")
            return False
    
    def _add_copilotkit_enhancements(
        self, 
        formatted_response: FormattedResponse, 
        intent: str, 
        persona: str, 
        options: FormattingOptions
    ) -> Optional[Dict[str, Any]]:
        """Add CopilotKit enhancements to the response."""
        if not self._copilotkit_available:
            return None
        
        try:
            enhancements = {}
            
            # Add complexity graphs for code-related responses
            if options.copilotkit_complexity_graphs and self._has_code_content(formatted_response):
                enhancements['complexity_graph'] = self._generate_complexity_graph(formatted_response)
            
            # Add inline suggestions
            if options.copilotkit_inline_suggestions:
                enhancements['inline_suggestions'] = self._generate_inline_suggestions(
                    formatted_response, intent, persona
                )
            
            # Add UI hints
            if options.copilotkit_ui_hints:
                enhancements['ui_hints'] = self._generate_ui_hints(formatted_response, intent)
            
            # Add performance metrics
            enhancements['performance_metrics'] = {
                'code_blocks_count': len(formatted_response.code_blocks),
                'sections_count': len(formatted_response.sections),
                'estimated_complexity': self._estimate_complexity(formatted_response),
                'suggested_next_actions': self._suggest_next_actions(intent, persona)
            }
            
            return enhancements
            
        except Exception as e:
            logger.warning(f"CopilotKit enhancement failed, continuing without: {e}")
            return None
    
    def _has_code_content(self, response: FormattedResponse) -> bool:
        """Check if response contains code content."""
        return len(response.code_blocks) > 0
    
    def _generate_complexity_graph(self, response: FormattedResponse) -> Dict[str, Any]:
        """Generate complexity graph data for CopilotKit."""
        complexity_data = {
            'type': 'complexity_graph',
            'data': {
                'nodes': [],
                'edges': [],
                'metrics': {}
            }
        }
        
        # Analyze code blocks for complexity
        for i, block in enumerate(response.code_blocks):
            language = block.get('language', 'text')
            code = block.get('code', '')
            line_count = block.get('line_count', 0)
            
            # Simple complexity estimation
            complexity_score = min(line_count * 0.1, 10.0)  # Cap at 10
            
            complexity_data['data']['nodes'].append({
                'id': f'code_block_{i}',
                'label': f'{language.title()} Block',
                'complexity': complexity_score,
                'lines': line_count
            })
        
        return complexity_data
    
    def _generate_inline_suggestions(
        self, 
        response: FormattedResponse, 
        intent: str, 
        persona: str
    ) -> List[Dict[str, Any]]:
        """Generate inline suggestions for CopilotKit."""
        suggestions = []
        
        # Intent-based suggestions
        intent_suggestions = {
            'optimize_code': [
                {'type': 'optimization', 'text': 'Consider performance profiling'},
                {'type': 'refactor', 'text': 'Look for code duplication opportunities'}
            ],
            'debug_error': [
                {'type': 'debugging', 'text': 'Add logging statements'},
                {'type': 'testing', 'text': 'Write unit tests to isolate the issue'}
            ],
            'documentation': [
                {'type': 'docs', 'text': 'Add code examples'},
                {'type': 'docs', 'text': 'Include usage scenarios'}
            ]
        }
        
        suggestions.extend(intent_suggestions.get(intent, []))
        
        # Code-based suggestions
        if self._has_code_content(response):
            suggestions.extend([
                {'type': 'code_review', 'text': 'Review for security vulnerabilities'},
                {'type': 'testing', 'text': 'Add comprehensive test coverage'}
            ])
        
        return suggestions
    
    def _generate_ui_hints(self, response: FormattedResponse, intent: str) -> Dict[str, Any]:
        """Generate UI hints for CopilotKit."""
        hints = {
            'suggested_actions': [],
            'ui_components': [],
            'interaction_hints': []
        }
        
        # Intent-based UI hints
        if intent == 'optimize_code':
            hints['suggested_actions'].append('Show performance metrics')
            hints['ui_components'].append('performance_dashboard')
        
        if intent == 'debug_error':
            hints['suggested_actions'].append('Enable debug mode')
            hints['ui_components'].append('debug_console')
        
        # Code-based UI hints
        if self._has_code_content(response):
            hints['suggested_actions'].extend([
                'Syntax highlighting',
                'Copy to clipboard',
                'Run in sandbox'
            ])
            hints['ui_components'].append('code_editor')
        
        return hints
    
    def _estimate_complexity(self, response: FormattedResponse) -> str:
        """Estimate overall response complexity."""
        score = 0
        
        # Factor in code blocks
        score += len(response.code_blocks) * 2
        
        # Factor in sections
        score += len(response.sections)
        
        # Factor in content length
        content_length = len(response.content)
        if content_length > 1000:
            score += 2
        elif content_length > 500:
            score += 1
        
        if score >= 8:
            return 'high'
        elif score >= 4:
            return 'medium'
        else:
            return 'low'
    
    def _suggest_next_actions(self, intent: str, persona: str) -> List[str]:
        """Suggest next actions based on intent and persona."""
        actions = []
        
        intent_actions = {
            'optimize_code': ['Profile performance', 'Run benchmarks', 'Review architecture'],
            'debug_error': ['Add logging', 'Write tests', 'Check dependencies'],
            'documentation': ['Add examples', 'Review clarity', 'Update references'],
            'general_assist': ['Clarify requirements', 'Break down tasks', 'Set priorities']
        }
        
        actions.extend(intent_actions.get(intent, ['Continue conversation', 'Ask follow-up questions']))
        
        return actions[:3]  # Limit to 3 suggestions


# Factory function for easy instantiation
def create_formatter(config: Optional[PipelineConfig] = None) -> DRYFormatter:
    """Create a DRY formatter instance.
    
    Args:
        config: Pipeline configuration, uses default if None
        
    Returns:
        DRYFormatter instance
    """
    return DRYFormatter(config)


# Export the main classes and functions
__all__ = [
    'DRYFormatter',
    'FormattingOptions', 
    'FormattedResponse',
    'create_formatter'
]