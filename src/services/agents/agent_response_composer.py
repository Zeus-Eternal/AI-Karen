"""
Agent Response Composer service for generating and formatting agent responses.

This service provides capabilities for agents to compose, format, and structure
their responses in various formats suitable for different contexts.
"""

import asyncio
import logging
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

logger = logging.getLogger(__name__)


class AgentResponseComposer(BaseService):
    """
    Agent Response Composer service for generating and formatting agent responses.
    
    This service provides capabilities for agents to compose, format, and structure
    their responses in various formats suitable for different contexts.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="agent_response_composer"))
        self._initialized = False
        self._templates: Dict[str, Dict[str, Any]] = {}
        self._response_formats: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the agent response composer."""
        if self._initialized:
            return
            
        # Initialize with default response formats
        self._response_formats = {
            "text": {
                "content_type": "text/plain",
                "description": "Plain text response format"
            },
            "markdown": {
                "content_type": "text/markdown",
                "description": "Markdown formatted response"
            },
            "html": {
                "content_type": "text/html",
                "description": "HTML formatted response"
            },
            "json": {
                "content_type": "application/json",
                "description": "JSON structured response"
            },
            "xml": {
                "content_type": "application/xml",
                "description": "XML formatted response"
            }
        }
        
        # Initialize with default templates
        self._templates = {
            "default": {
                "template": "{content}",
                "description": "Default response template"
            },
            "structured": {
                "template": "{{\n  \"response\": \"{content}\",\n  \"timestamp\": \"{timestamp}\",\n  \"agent_id\": \"{agent_id}\"\n}}",
                "description": "Structured JSON response template"
            },
            "chat": {
                "template": "[{agent_id}] {content}",
                "description": "Chat message format template"
            }
        }
        
        self._initialized = True
        logger.info("Agent response composer initialized successfully")
    
    async def start(self) -> None:
        """Start the agent response composer."""
        logger.info("Agent response composer started")
    
    async def stop(self) -> None:
        """Stop the agent response composer."""
        logger.info("Agent response composer stopped")
    
    async def health_check(self) -> bool:
        """Check health of the agent response composer."""
        return self._initialized
    
    async def compose_response(
        self, 
        agent_id: str, 
        content: str,
        format_type: str = "text",
        template_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compose a response in the specified format.
        
        Args:
            agent_id: Identifier of the agent
            content: Content of the response
            format_type: Type of format to use (text, markdown, html, json, xml)
            template_name: Optional name of template to use
            metadata: Optional metadata to include in response
            
        Returns:
            Composed response
        """
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            # Check if format is supported
            if format_type not in self._response_formats:
                return {
                    "status": "error",
                    "message": f"Unsupported format type: {format_type}",
                    "supported_formats": list(self._response_formats.keys())
                }
            
            # Get format info
            format_info = self._response_formats[format_type]
            
            # Apply template if specified
            if template_name and template_name in self._templates:
                template = self._templates[template_name]["template"]
                
                # Format template with content and metadata
                template_vars = {
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_id": agent_id
                }
                
                if metadata:
                    template_vars.update(metadata)
                
                try:
                    formatted_content = template.format(**template_vars)
                except KeyError as e:
                    logger.warning(f"Template variable missing: {e}")
                    formatted_content = content
            else:
                formatted_content = content
            
            # Format response based on type
            if format_type == "json":
                try:
                    # If content is already JSON, use it as is
                    if content.strip().startswith("{") and content.strip().endswith("}"):
                        response_content = json.loads(content)
                    else:
                        # Otherwise, create a JSON structure
                        response_content = {
                            "response": formatted_content,
                            "timestamp": datetime.utcnow().isoformat(),
                            "agent_id": agent_id
                        }
                        if metadata:
                            response_content.update(metadata)
                        
                    formatted_content = json.dumps(response_content, indent=2)
                except json.JSONDecodeError:
                    # Fallback to simple JSON structure
                    response_content = {
                        "response": formatted_content,
                        "timestamp": datetime.utcnow().isoformat(),
                        "agent_id": agent_id
                    }
                    if metadata:
                        response_content.update(metadata)
                    
                    formatted_content = json.dumps(response_content, indent=2)
            
            elif format_type == "xml":
                # Simple XML formatting
                xml_content = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
                xml_content += f"<response>\n"
                xml_content += f"  <agent_id>{agent_id}</agent_id>\n"
                xml_content += f"  <timestamp>{datetime.utcnow().isoformat()}</timestamp>\n"
                xml_content += f"  <content>{formatted_content}</content>\n"
                
                if metadata:
                    xml_content += f"  <metadata>\n"
                    for key, value in metadata.items():
                        xml_content += f"    <{key}>{value}</{key}>\n"
                    xml_content += f"  </metadata>\n"
                
                xml_content += f"</response>"
                formatted_content = xml_content
            
            elif format_type == "html":
                # Simple HTML formatting
                html_content = f"<!DOCTYPE html>\n<html>\n<head>\n"
                html_content += f"<title>Agent Response</title>\n"
                html_content += f"<meta charset=\"UTF-8\">\n"
                html_content += f"</head>\n<body>\n"
                html_content += f"<div class=\"agent-response\">\n"
                html_content += f"<div class=\"agent-id\">Agent: {agent_id}</div>\n"
                html_content += f"<div class=\"timestamp\">{datetime.utcnow().isoformat()}</div>\n"
                html_content += f"<div class=\"content\">{formatted_content}</div>\n"
                
                if metadata:
                    html_content += f"<div class=\"metadata\">\n"
                    for key, value in metadata.items():
                        html_content += f"<div class=\"{key}\">{key}: {value}</div>\n"
                    html_content += f"</div>\n"
                
                html_content += f"</div>\n</body>\n</html>"
                formatted_content = html_content
            
            # Create response object
            response = {
                "status": "success",
                "content": formatted_content,
                "format_type": format_type,
                "content_type": format_info["content_type"],
                "agent_id": agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "template_used": template_name
            }
            
            if metadata:
                response["metadata"] = metadata
            
            return response
    
    async def register_template(
        self, 
        template_name: str, 
        template: str,
        description: str
    ) -> bool:
        """
        Register a new response template.
        
        Args:
            template_name: Name of the template
            template: Template string with placeholders
            description: Description of the template
            
        Returns:
            True if registration was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            self._templates[template_name] = {
                "template": template,
                "description": description
            }
            logger.info(f"Registered template: {template_name}")
            return True
    
    async def unregister_template(self, template_name: str) -> bool:
        """
        Unregister a response template.
        
        Args:
            template_name: Name of the template to unregister
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            if template_name in self._templates:
                del self._templates[template_name]
                logger.info(f"Unregistered template: {template_name}")
                return True
            return False
    
    async def list_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available templates.
        
        Returns:
            Dictionary of template information
        """
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            return self._templates.copy()
    
    async def list_formats(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available response formats.
        
        Returns:
            Dictionary of format information
        """
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            return self._response_formats.copy()
    
    async def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template information if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            if template_name in self._templates:
                return self._templates[template_name].copy()
            return None
    
    async def get_format(self, format_type: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific response format.
        
        Args:
            format_type: Type of format
            
        Returns:
            Format information if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        async with self._lock:
            if format_type in self._response_formats:
                return self._response_formats[format_type].copy()
            return None