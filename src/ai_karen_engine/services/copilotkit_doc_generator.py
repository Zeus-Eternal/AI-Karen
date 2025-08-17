"""
CopilotKit Documentation Generator Service

Enhances Karen's existing documentation system with CopilotKit-powered generation capabilities.
Integrates with the existing docs/ directory structure and provides AI-powered documentation
generation for code, APIs, and system components.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import re
import json
from datetime import datetime

from ai_karen_engine.llm_orchestrator import get_orchestrator
from ai_karen_engine.hooks.hook_mixin import HookMixin

logger = logging.getLogger(__name__)


class CopilotKitDocumentationGenerator(HookMixin):
    """CopilotKit-powered documentation generator with hook integration."""
    
    def __init__(self, docs_directory: Optional[Path] = None):
        super().__init__()
        self.name = "copilotkit_doc_generator"
        self.docs_directory = docs_directory or Path("docs")
        self.orchestrator = get_orchestrator()
        
        # Documentation templates and styles
        self.doc_styles = {
            "api": "API reference with detailed endpoint documentation",
            "tutorial": "Step-by-step tutorial with examples",
            "guide": "Comprehensive guide with best practices",
            "reference": "Technical reference documentation",
            "troubleshooting": "Problem-solving and troubleshooting guide"
        }
        
        # Register documentation hooks
        asyncio.create_task(self._register_doc_hooks())
    
    async def _register_doc_hooks(self):
        """Register documentation generation hooks."""
        try:
            # Pre-generation validation hook
            await self.register_hook(
                "validate_doc_request",
                self._validate_doc_request,
                priority=10,
                source_name="doc_generator_validation"
            )
            
            # Post-generation enhancement hook
            await self.register_hook(
                "enhance_generated_docs",
                self._enhance_generated_docs,
                priority=80,
                source_name="doc_generator_enhancement"
            )
            
            # Documentation storage hook
            await self.register_hook(
                "store_generated_docs",
                self._store_generated_docs,
                priority=90,
                source_name="doc_generator_storage"
            )
            
            logger.info("CopilotKit documentation generator hooks registered successfully")
            
        except Exception as e:
            logger.warning(f"Failed to register documentation generator hooks: {e}")
    
    async def _validate_doc_request(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate documentation generation request."""
        doc_type = context.get("doc_type", "guide")
        content = context.get("content", "")
        target_file = context.get("target_file", "")
        
        validation_result = {
            "valid": True,
            "warnings": [],
            "suggestions": []
        }
        
        # Validate documentation type
        if doc_type not in self.doc_styles:
            validation_result["warnings"].append(f"Unknown documentation type: {doc_type}")
            validation_result["suggestions"].append(f"Available types: {', '.join(self.doc_styles.keys())}")
        
        # Validate content
        if not content.strip():
            validation_result["valid"] = False
            validation_result["warnings"].append("No content provided for documentation generation")
            return validation_result
        
        # Validate target file path
        if target_file:
            target_path = Path(target_file)
            if not target_path.suffix == ".md":
                validation_result["warnings"].append("Target file should have .md extension")
                validation_result["suggestions"].append("Consider using .md extension for markdown documentation")
        
        return validation_result
    
    async def _enhance_generated_docs(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance generated documentation with additional features."""
        try:
            generated_content = context.get("generated_content", "")
            doc_type = context.get("doc_type", "guide")
            
            enhancements = []
            
            # Add table of contents for longer documents
            if len(generated_content.split('\n')) > 20:
                toc = self._generate_table_of_contents(generated_content)
                if toc:
                    enhancements.append(("table_of_contents", toc))
            
            # Add code syntax highlighting hints
            code_blocks = re.findall(r'```(\w+)?\n(.*?)\n```', generated_content, re.DOTALL)
            if code_blocks:
                enhancements.append(("code_blocks_found", len(code_blocks)))
            
            # Add cross-references to existing documentation
            cross_refs = await self._find_cross_references(generated_content)
            if cross_refs:
                enhancements.append(("cross_references", cross_refs))
            
            # Add metadata section
            metadata = {
                "generated_at": datetime.utcnow().isoformat(),
                "doc_type": doc_type,
                "generator": "copilotkit_doc_generator",
                "enhancements_applied": len(enhancements)
            }
            
            return {
                "enhanced": True,
                "enhancements": enhancements,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to enhance generated documentation: {e}")
            return {"enhanced": False, "error": str(e)}
    
    async def _store_generated_docs(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Store generated documentation to the docs directory."""
        try:
            generated_content = context.get("generated_content", "")
            target_file = context.get("target_file", "")
            doc_type = context.get("doc_type", "guide")
            
            if not target_file:
                # Generate filename based on content
                title = self._extract_title_from_content(generated_content)
                filename = self._sanitize_filename(title) + ".md"
                target_file = str(self.docs_directory / filename)
            
            # Ensure docs directory exists
            self.docs_directory.mkdir(parents=True, exist_ok=True)
            
            # Write documentation file
            target_path = Path(target_file)
            target_path.write_text(generated_content, encoding="utf-8")
            
            # Update documentation index if it exists
            await self._update_doc_index(target_path, doc_type)
            
            return {
                "stored": True,
                "file_path": str(target_path),
                "file_size": len(generated_content),
                "doc_type": doc_type
            }
            
        except Exception as e:
            logger.error(f"Failed to store generated documentation: {e}")
            return {"stored": False, "error": str(e)}
    
    def _generate_table_of_contents(self, content: str) -> Optional[str]:
        """Generate table of contents from markdown headers."""
        try:
            headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
            if len(headers) < 3:  # Only generate TOC for documents with multiple headers
                return None
            
            toc_lines = ["## Table of Contents\n"]
            
            for level, title in headers:
                indent = "  " * (len(level) - 1)
                anchor = title.lower().replace(" ", "-").replace(".", "").replace(",", "")
                toc_lines.append(f"{indent}- [{title}](#{anchor})")
            
            return "\n".join(toc_lines) + "\n"
            
        except Exception as e:
            logger.debug(f"Failed to generate table of contents: {e}")
            return None
    
    async def _find_cross_references(self, content: str) -> List[str]:
        """Find potential cross-references to existing documentation."""
        try:
            cross_refs = []
            
            # Check for references to existing docs
            if self.docs_directory.exists():
                existing_docs = list(self.docs_directory.glob("*.md"))
                
                for doc_file in existing_docs:
                    doc_name = doc_file.stem
                    if doc_name.lower() in content.lower():
                        cross_refs.append(f"[{doc_name}]({doc_file.name})")
            
            return cross_refs[:5]  # Limit to top 5 references
            
        except Exception as e:
            logger.debug(f"Failed to find cross-references: {e}")
            return []
    
    def _extract_title_from_content(self, content: str) -> str:
        """Extract title from generated content."""
        # Look for first H1 header
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1)
        
        # Look for first line that looks like a title
        lines = content.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and not line.startswith('#') and len(line) < 100:
                return line
        
        return "Generated Documentation"
    
    def _sanitize_filename(self, title: str) -> str:
        """Sanitize title for use as filename."""
        # Remove special characters and replace spaces with underscores
        sanitized = re.sub(r'[^\w\s-]', '', title)
        sanitized = re.sub(r'[-\s]+', '_', sanitized)
        return sanitized.lower()
    
    async def _update_doc_index(self, doc_path: Path, doc_type: str):
        """Update documentation index with new document."""
        try:
            index_file = self.docs_directory / "README.md"
            
            if not index_file.exists():
                # Create basic index
                index_content = "# Documentation Index\n\nThis directory contains system documentation.\n\n"
            else:
                index_content = index_file.read_text(encoding="utf-8")
            
            # Add entry if not already present
            doc_entry = f"- [{doc_path.stem}]({doc_path.name}) - {doc_type}"
            if doc_entry not in index_content:
                # Find or create section for doc type
                section_header = f"## {doc_type.title()} Documentation"
                if section_header not in index_content:
                    index_content += f"\n{section_header}\n\n{doc_entry}\n"
                else:
                    # Add to existing section
                    index_content = index_content.replace(
                        section_header,
                        f"{section_header}\n{doc_entry}"
                    )
                
                index_file.write_text(index_content, encoding="utf-8")
                
        except Exception as e:
            logger.debug(f"Failed to update documentation index: {e}")
    
    async def generate_code_documentation(
        self,
        code: str,
        language: str = "python",
        doc_style: str = "reference",
        include_examples: bool = True,
        target_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate documentation for code using CopilotKit.
        
        Args:
            code: Source code to document
            language: Programming language
            doc_style: Documentation style (api, tutorial, guide, reference, troubleshooting)
            include_examples: Whether to include usage examples
            target_file: Optional target file path
        
        Returns:
            Dictionary containing generation results
        """
        try:
            # Validate request
            validation_context = {
                "doc_type": doc_style,
                "content": code,
                "target_file": target_file or ""
            }
            
            validation_result = await self.trigger_hook_safe(
                "validate_doc_request",
                validation_context,
                {}
            )
            
            if not validation_result.get("valid", True):
                return {
                    "success": False,
                    "error": "Validation failed",
                    "warnings": validation_result.get("warnings", [])
                }
            
            # Generate documentation using CopilotKit
            documentation = await self.orchestrator.generate_documentation(
                code=code,
                language=language,
                style=doc_style
            )
            
            # Add examples if requested
            if include_examples and documentation:
                examples_prompt = f"Generate usage examples for this {language} code:\n\n```{language}\n{code}\n```"
                examples = await self.orchestrator.enhanced_route(examples_prompt)
                documentation += f"\n\n## Usage Examples\n\n{examples}"
            
            # Enhance documentation
            enhancement_context = {
                "generated_content": documentation,
                "doc_type": doc_style,
                "language": language
            }
            
            enhancement_result = await self.trigger_hook_safe(
                "enhance_generated_docs",
                enhancement_context,
                {}
            )
            
            # Store documentation if target file specified
            storage_result = {}
            if target_file:
                storage_context = {
                    "generated_content": documentation,
                    "target_file": target_file,
                    "doc_type": doc_style
                }
                
                storage_result = await self.trigger_hook_safe(
                    "store_generated_docs",
                    storage_context,
                    {}
                )
            
            return {
                "success": True,
                "documentation": documentation,
                "language": language,
                "doc_style": doc_style,
                "enhancement_info": enhancement_result,
                "storage_info": storage_result,
                "generator": "copilotkit_doc_generator"
            }
            
        except Exception as e:
            logger.error(f"Code documentation generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "generator": "copilotkit_doc_generator"
            }
    
    async def generate_api_documentation(
        self,
        api_spec: Union[str, Dict[str, Any]],
        format_type: str = "openapi",
        target_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate API documentation from specification.
        
        Args:
            api_spec: API specification (OpenAPI, JSON, etc.)
            format_type: Specification format (openapi, json, yaml)
            target_file: Optional target file path
        
        Returns:
            Dictionary containing generation results
        """
        try:
            # Convert spec to string if needed
            if isinstance(api_spec, dict):
                api_spec_str = json.dumps(api_spec, indent=2)
            else:
                api_spec_str = str(api_spec)
            
            # Generate API documentation
            api_doc_prompt = f"""Generate comprehensive API documentation from this {format_type} specification:

```{format_type}
{api_spec_str}
```

Include:
- Overview and authentication
- Endpoint descriptions with parameters
- Request/response examples
- Error codes and handling
- Rate limiting information"""
            
            documentation = await self.orchestrator.enhanced_route(api_doc_prompt)
            
            # Store documentation
            storage_result = {}
            if target_file:
                storage_context = {
                    "generated_content": documentation,
                    "target_file": target_file,
                    "doc_type": "api"
                }
                
                storage_result = await self.trigger_hook_safe(
                    "store_generated_docs",
                    storage_context,
                    {}
                )
            
            return {
                "success": True,
                "documentation": documentation,
                "format_type": format_type,
                "storage_info": storage_result,
                "generator": "copilotkit_doc_generator"
            }
            
        except Exception as e:
            logger.error(f"API documentation generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "generator": "copilotkit_doc_generator"
            }
    
    async def enhance_existing_documentation(
        self,
        doc_file: Union[str, Path],
        enhancement_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Enhance existing documentation with CopilotKit assistance.
        
        Args:
            doc_file: Path to existing documentation file
            enhancement_type: Type of enhancement (comprehensive, examples, troubleshooting)
        
        Returns:
            Dictionary containing enhancement results
        """
        try:
            doc_path = Path(doc_file)
            
            if not doc_path.exists():
                return {
                    "success": False,
                    "error": f"Documentation file not found: {doc_file}"
                }
            
            # Read existing content
            existing_content = doc_path.read_text(encoding="utf-8")
            
            # Generate enhancement based on type
            if enhancement_type == "examples":
                enhancement_prompt = f"Add practical examples to this documentation:\n\n{existing_content}"
            elif enhancement_type == "troubleshooting":
                enhancement_prompt = f"Add troubleshooting section to this documentation:\n\n{existing_content}"
            else:  # comprehensive
                enhancement_prompt = f"Enhance this documentation with better structure, examples, and clarity:\n\n{existing_content}"
            
            enhanced_content = await self.orchestrator.enhanced_route(enhancement_prompt)
            
            # Create backup of original
            backup_path = doc_path.with_suffix(f".backup{doc_path.suffix}")
            backup_path.write_text(existing_content, encoding="utf-8")
            
            # Write enhanced content
            doc_path.write_text(enhanced_content, encoding="utf-8")
            
            return {
                "success": True,
                "original_file": str(doc_path),
                "backup_file": str(backup_path),
                "enhancement_type": enhancement_type,
                "content_length_before": len(existing_content),
                "content_length_after": len(enhanced_content),
                "generator": "copilotkit_doc_generator"
            }
            
        except Exception as e:
            logger.error(f"Documentation enhancement failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "generator": "copilotkit_doc_generator"
            }


# Global instance
_doc_generator: Optional[CopilotKitDocumentationGenerator] = None

def get_doc_generator() -> CopilotKitDocumentationGenerator:
    """Get the global documentation generator instance."""
    global _doc_generator
    if _doc_generator is None:
        _doc_generator = CopilotKitDocumentationGenerator()
    return _doc_generator


__all__ = [
    "CopilotKitDocumentationGenerator",
    "get_doc_generator"
]