"""
Agent Response Composer Service

This service is responsible for composing responses from agents,
including formatting, templating, and response customization.
"""

from typing import Dict, List, Any, Optional, Union, Callable
import logging
from dataclasses import dataclass
from enum import Enum
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class ResponseFormat(Enum):
    """Enumeration of response formats."""
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    XML = "xml"
    CUSTOM = "custom"


class ResponseStyle(Enum):
    """Enumeration of response styles."""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    CONCISE = "concise"
    DETAILED = "detailed"


@dataclass
class ResponseTemplate:
    """Represents a response template."""
    id: str
    name: str
    description: str
    template: str
    format: ResponseFormat
    style: ResponseStyle
    variables: List[str]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ResponseComposition:
    """Represents a response composition."""
    id: str
    agent_id: str
    template_id: Optional[str]
    content: Dict[str, Any]
    format: ResponseFormat
    style: ResponseStyle
    variables: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ComposedResponse:
    """Represents a composed response."""
    id: str
    composition_id: str
    content: str
    format: ResponseFormat
    style: ResponseStyle
    metadata: Optional[Dict[str, Any]] = None


class AgentResponseComposer:
    """
    Composes responses from agents.
    
    This class is responsible for:
    - Managing response templates
    - Composing responses from agent output
    - Formatting responses according to specifications
    - Customizing response style and content
    """
    
    def __init__(self):
        self._templates: Dict[str, ResponseTemplate] = {}
        self._compositions: Dict[str, ResponseComposition] = {}
        self._composed_responses: Dict[str, ComposedResponse] = {}
        
        # Initialize default templates
        self._initialize_default_templates()
        
        # Callbacks for composition events
        self._on_composition_start: Optional[Callable[[ResponseComposition], None]] = None
        self._on_composition_complete: Optional[Callable[[ComposedResponse], None]] = None
        self._on_composition_error: Optional[Callable[[ResponseComposition, str], None]] = None
    
    def register_template(self, template: ResponseTemplate) -> None:
        """Register a response template."""
        self._templates[template.id] = template
        logger.info(f"Registered response template: {template.id} ({template.name})")
    
    def unregister_template(self, template_id: str) -> bool:
        """Unregister a response template."""
        if template_id in self._templates:
            del self._templates[template_id]
            logger.info(f"Unregistered response template: {template_id}")
            return True
        else:
            logger.warning(f"Attempted to unregister non-existent template: {template_id}")
            return False
    
    def get_template(self, template_id: str) -> Optional[ResponseTemplate]:
        """Get a response template by ID."""
        return self._templates.get(template_id)
    
    def get_all_templates(self) -> Dict[str, ResponseTemplate]:
        """Get all response templates."""
        return self._templates.copy()
    
    def get_templates_by_format(self, format: ResponseFormat) -> List[ResponseTemplate]:
        """Get all templates with a specific format."""
        return [template for template in self._templates.values() if template.format == format]
    
    def get_templates_by_style(self, style: ResponseStyle) -> List[ResponseTemplate]:
        """Get all templates with a specific style."""
        return [template for template in self._templates.values() if template.style == style]
    
    def search_templates(self, query: str) -> List[ResponseTemplate]:
        """Search for templates by name or description."""
        query_lower = query.lower()
        matching_templates = []
        
        for template in self._templates.values():
            if (query_lower in template.name.lower() or
                query_lower in template.description.lower()):
                matching_templates.append(template)
        
        return matching_templates
    
    def create_composition(
        self,
        agent_id: str,
        content: Dict[str, Any],
        format: ResponseFormat,
        style: ResponseStyle,
        template_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a response composition.
        
        Args:
            agent_id: ID of agent
            content: Content to compose
            format: Response format
            style: Response style
            template_id: Optional template ID to use
            variables: Variables for template substitution
            metadata: Additional metadata
            
        Returns:
            Composition ID
        """
        import uuid
        composition_id = str(uuid.uuid4())
        
        # Create composition
        composition = ResponseComposition(
            id=composition_id,
            agent_id=agent_id,
            template_id=template_id,
            content=content,
            format=format,
            style=style,
            variables=variables or {},
            metadata=metadata or {}
        )
        
        # Store composition
        self._compositions[composition_id] = composition
        
        logger.info(f"Created response composition: {composition_id}")
        return composition_id
    
    def compose_response(self, composition_id: str) -> ComposedResponse:
        """
        Compose a response from a composition.
        
        Args:
            composition_id: ID of composition
            
        Returns:
            Composed response
        """
        # Get composition
        composition = self._compositions.get(composition_id)
        if not composition:
            raise ValueError(f"Composition not found: {composition_id}")
        
        # Call start callback if set
        if self._on_composition_start:
            self._on_composition_start(composition)
        
        try:
            # Get template if specified
            template = None
            if composition.template_id:
                template = self._templates.get(composition.template_id)
                if not template:
                    logger.warning(f"Template not found: {composition.template_id}")
            
            # Compose response
            if template:
                response_content = self._compose_from_template(composition, template)
            else:
                response_content = self._compose_without_template(composition)
            
            # Create composed response
            response = ComposedResponse(
                id=f"response_{composition_id}",
                composition_id=composition_id,
                content=response_content,
                format=composition.format,
                style=composition.style,
                metadata=composition.metadata
            )
            
            # Store response
            self._composed_responses[response.id] = response
            
            # Call completion callback if set
            if self._on_composition_complete:
                self._on_composition_complete(response)
            
            logger.info(f"Composed response: {response.id}")
            return response
            
        except Exception as e:
            error_msg = str(e)
            
            # Call error callback if set
            if self._on_composition_error:
                self._on_composition_error(composition, error_msg)
            
            logger.error(f"Failed to compose response for composition {composition_id}: {error_msg}")
            raise
    
    def compose_response_sync(
        self,
        agent_id: str,
        content: Dict[str, Any],
        format: ResponseFormat,
        style: ResponseStyle,
        template_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ComposedResponse:
        """
        Create and compose a response synchronously.
        
        Args:
            agent_id: ID of agent
            content: Content to compose
            format: Response format
            style: Response style
            template_id: Optional template ID to use
            variables: Variables for template substitution
            metadata: Additional metadata
            
        Returns:
            Composed response
        """
        composition_id = self.create_composition(
            agent_id=agent_id,
            content=content,
            format=format,
            style=style,
            template_id=template_id,
            variables=variables,
            metadata=metadata
        )
        
        return self.compose_response(composition_id)
    
    def get_composition(self, composition_id: str) -> Optional[ResponseComposition]:
        """Get a response composition by ID."""
        return self._compositions.get(composition_id)
    
    def get_composed_response(self, response_id: str) -> Optional[ComposedResponse]:
        """Get a composed response by ID."""
        return self._composed_responses.get(response_id)
    
    def get_compositions_for_agent(self, agent_id: str) -> List[ResponseComposition]:
        """Get all compositions for an agent."""
        return [comp for comp in self._compositions.values() if comp.agent_id == agent_id]
    
    def get_responses_for_agent(self, agent_id: str) -> List[ComposedResponse]:
        """Get all composed responses for an agent."""
        default_composition = ResponseComposition(
            id="",
            agent_id="",
            template_id=None,
            content={},
            format=ResponseFormat.PLAIN_TEXT,
            style=ResponseStyle.FORMAL,
            variables={},
            metadata={}
        )
        
        return [
            resp for resp in self._composed_responses.values()
            if self._compositions.get(resp.composition_id, default_composition).agent_id == agent_id
        ]
    
    def update_composition(
        self,
        composition_id: str,
        content: Optional[Dict[str, Any]] = None,
        format: Optional[ResponseFormat] = None,
        style: Optional[ResponseStyle] = None,
        variables: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a response composition.
        
        Args:
            composition_id: ID of composition to update
            content: New content
            format: New format
            style: New style
            variables: New variables
            metadata: New metadata
            
        Returns:
            True if composition was updated, False if not found
        """
        composition = self._compositions.get(composition_id)
        if composition:
            if content is not None:
                composition.content = content
            if format is not None:
                composition.format = format
            if style is not None:
                composition.style = style
            if variables is not None:
                composition.variables = variables
            if metadata is not None:
                composition.metadata = metadata
            
            logger.info(f"Updated response composition: {composition_id}")
            return True
        else:
            logger.warning(f"Attempted to update non-existent composition: {composition_id}")
            return False
    
    def delete_composition(self, composition_id: str) -> bool:
        """
        Delete a response composition.
        
        Args:
            composition_id: ID of composition to delete
            
        Returns:
            True if composition was deleted, False if not found
        """
        if composition_id in self._compositions:
            del self._compositions[composition_id]
            
            # Also delete any composed responses for this composition
            response_ids = [rid for rid, resp in self._composed_responses.items() if resp.composition_id == composition_id]
            for rid in response_ids:
                del self._composed_responses[rid]
            
            logger.info(f"Deleted response composition: {composition_id}")
            return True
        else:
            logger.warning(f"Attempted to delete non-existent composition: {composition_id}")
            return False
    
    def set_composition_callbacks(
        self,
        on_start: Optional[Callable[[ResponseComposition], None]] = None,
        on_complete: Optional[Callable[[ComposedResponse], None]] = None,
        on_error: Optional[Callable[[ResponseComposition, str], None]] = None
    ) -> None:
        """Set callbacks for composition events."""
        self._on_composition_start = on_start
        self._on_composition_complete = on_complete
        self._on_composition_error = on_error
    
    def get_composition_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about compositions and responses.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_compositions": len(self._compositions),
            "total_responses": len(self._composed_responses),
            "templates_by_format": {},
            "templates_by_style": {},
            "compositions_by_agent": {},
            "responses_by_format": {},
            "responses_by_style": {}
        }
        
        # Count templates by format
        for format in ResponseFormat:
            stats["templates_by_format"][format.value] = len(self.get_templates_by_format(format))
        
        # Count templates by style
        for style in ResponseStyle:
            stats["templates_by_style"][style.value] = len(self.get_templates_by_style(style))
        
        # Count compositions by agent
        for comp in self._compositions.values():
            if comp.agent_id not in stats["compositions_by_agent"]:
                stats["compositions_by_agent"][comp.agent_id] = 0
            stats["compositions_by_agent"][comp.agent_id] += 1
        
        # Count responses by format
        for resp in self._composed_responses.values():
            if resp.format.value not in stats["responses_by_format"]:
                stats["responses_by_format"][resp.format.value] = 0
            stats["responses_by_format"][resp.format.value] += 1
        
        # Count responses by style
        for resp in self._composed_responses.values():
            if resp.style.value not in stats["responses_by_style"]:
                stats["responses_by_style"][resp.style.value] = 0
            stats["responses_by_style"][resp.style.value] += 1
        
        return stats
    
    def _initialize_default_templates(self) -> None:
        """Initialize default response templates."""
        # Plain text templates
        plain_template = ResponseTemplate(
            id="plain_text_default",
            name="Plain Text Default",
            description="Default plain text response template",
            template="{content}",
            format=ResponseFormat.PLAIN_TEXT,
            style=ResponseStyle.FORMAL,
            variables=["content"]
        )
        self.register_template(plain_template)
        
        # Markdown templates
        markdown_template = ResponseTemplate(
            id="markdown_default",
            name="Markdown Default",
            description="Default markdown response template",
            template="# Response\n\n{content}",
            format=ResponseFormat.MARKDOWN,
            style=ResponseStyle.FORMAL,
            variables=["content"]
        )
        self.register_template(markdown_template)
        
        # JSON templates
        json_template = ResponseTemplate(
            id="json_default",
            name="JSON Default",
            description="Default JSON response template",
            template="{\n  \"response\": \"{content}\"\n}",
            format=ResponseFormat.JSON,
            style=ResponseStyle.TECHNICAL,
            variables=["content"]
        )
        self.register_template(json_template)
        
        # Formal templates
        formal_template = ResponseTemplate(
            id="formal_response",
            name="Formal Response",
            description="Formal response template",
            template="Dear User,\n\n{content}\n\nSincerely,\nAI Assistant",
            format=ResponseFormat.PLAIN_TEXT,
            style=ResponseStyle.FORMAL,
            variables=["content"]
        )
        self.register_template(formal_template)
        
        # Casual templates
        casual_template = ResponseTemplate(
            id="casual_response",
            name="Casual Response",
            description="Casual response template",
            template="Hey there!\n\n{content}\n\nCheers,\nAI Assistant",
            format=ResponseFormat.PLAIN_TEXT,
            style=ResponseStyle.CASUAL,
            variables=["content"]
        )
        self.register_template(casual_template)
    
    def _compose_from_template(self, composition: ResponseComposition, template: ResponseTemplate) -> str:
        """Compose a response using a template."""
        # Prepare variables
        variables = composition.variables.copy()
        variables["content"] = self._format_content(composition.content, composition.format)
        
        # Substitute variables in template
        response = template.template
        for var_name, var_value in variables.items():
            if var_name in template.variables:
                response = response.replace(f"{{{var_name}}}", str(var_value))
        
        # Apply style formatting
        response = self._apply_style(response, composition.style)
        
        return response
    
    def _compose_without_template(self, composition: ResponseComposition) -> str:
        """Compose a response without a template."""
        # Format content
        content = self._format_content(composition.content, composition.format)
        
        # Apply style formatting
        response = self._apply_style(content, composition.style)
        
        return response
    
    def _format_content(self, content: Dict[str, Any], format: ResponseFormat) -> str:
        """Format content according to specified format."""
        if format == ResponseFormat.PLAIN_TEXT:
            return self._format_as_plain_text(content)
        elif format == ResponseFormat.MARKDOWN:
            return self._format_as_markdown(content)
        elif format == ResponseFormat.HTML:
            return self._format_as_html(content)
        elif format == ResponseFormat.JSON:
            return self._format_as_json(content)
        elif format == ResponseFormat.XML:
            return self._format_as_xml(content)
        else:
            # Default to plain text
            return self._format_as_plain_text(content)
    
    def _apply_style(self, content: str, style: ResponseStyle) -> str:
        """Apply style formatting to content."""
        if style == ResponseStyle.FORMAL:
            return self._apply_formal_style(content)
        elif style == ResponseStyle.CASUAL:
            return self._apply_casual_style(content)
        elif style == ResponseStyle.TECHNICAL:
            return self._apply_technical_style(content)
        elif style == ResponseStyle.FRIENDLY:
            return self._apply_friendly_style(content)
        elif style == ResponseStyle.PROFESSIONAL:
            return self._apply_professional_style(content)
        elif style == ResponseStyle.CONCISE:
            return self._apply_concise_style(content)
        elif style == ResponseStyle.DETAILED:
            return self._apply_detailed_style(content)
        else:
            # Default to formal style
            return self._apply_formal_style(content)
    
    def _format_as_plain_text(self, content: Dict[str, Any]) -> str:
        """Format content as plain text."""
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            result = []
            for key, value in content.items():
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, indent=2)
                result.append(f"{key}: {value}")
            return "\n".join(result)
        else:
            return str(content)
    
    def _format_as_markdown(self, content: Dict[str, Any]) -> str:
        """Format content as markdown."""
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            result = []
            for key, value in content.items():
                if isinstance(value, (list, dict)):
                    value = "```json\n" + json.dumps(value, indent=2) + "\n```"
                result.append(f"**{key}**: {value}")
            return "\n\n".join(result)
        else:
            return str(content)
    
    def _format_as_html(self, content: Dict[str, Any]) -> str:
        """Format content as HTML."""
        if isinstance(content, str):
            return f"<p>{content}</p>"
        elif isinstance(content, dict):
            result = ["<div>"]
            for key, value in content.items():
                if isinstance(value, (list, dict)):
                    value = "<pre><code>" + json.dumps(value, indent=2) + "</code></pre>"
                result.append(f"<p><strong>{key}:</strong> {value}</p>")
            result.append("</div>")
            return "\n".join(result)
        else:
            return f"<p>{str(content)}</p>"
    
    def _format_as_json(self, content: Dict[str, Any]) -> str:
        """Format content as JSON."""
        return json.dumps(content, indent=2)
    
    def _format_as_xml(self, content: Dict[str, Any]) -> str:
        """Format content as XML."""
        if isinstance(content, str):
            return f"<content>{content}</content>"
        elif isinstance(content, dict):
            result = ["<response>"]
            for key, value in content.items():
                if isinstance(value, (list, dict)):
                    value = json.dumps(value)
                result.append(f"<{key}>{value}</{key}>")
            result.append("</response>")
            return "\n".join(result)
        else:
            return f"<content>{str(content)}</content>"
    
    def _apply_formal_style(self, content: str) -> str:
        """Apply formal style to content."""
        # Add formal greeting and closing if not already present
        if not content.startswith(("Dear", "Hello", "To whom it may concern")):
            content = "Dear User,\n\n" + content
        
        if not content.endswith(("\nSincerely,", "\nBest regards,", "\nYours truly,")):
            content = content + "\n\nSincerely,\nAI Assistant"
        
        return content
    
    def _apply_casual_style(self, content: str) -> str:
        """Apply casual style to content."""
        # Add casual greeting and closing if not already present
        if not content.startswith(("Hey", "Hi", "Hello")):
            content = "Hey there!\n\n" + content
        
        if not content.endswith(("\nCheers,", "\nBest,", "\nLater,")):
            content = content + "\n\nCheers,\nAI Assistant"
        
        return content
    
    def _apply_technical_style(self, content: str) -> str:
        """Apply technical style to content."""
        # Ensure technical precision and detail
        if not re.search(r'\b(technical|specification|implementation|algorithm)\b', content, re.IGNORECASE):
            content = "Technical Analysis:\n\n" + content
        
        return content
    
    def _apply_friendly_style(self, content: str) -> str:
        """Apply friendly style to content."""
        # Add friendly tone
        content = re.sub(r'\b(you should|you must|you need to)\b', 'you might want to', content, flags=re.IGNORECASE)
        
        # Add friendly greeting and closing if not already present
        if not content.startswith(("Hi", "Hello", "Hey")):
            content = "Hi there!\n\n" + content
        
        if not content.endswith(("\nHave a great day!", "\nTake care!", "\nBest wishes!")):
            content = content + "\n\nHave a great day!"
        
        return content
    
    def _apply_professional_style(self, content: str) -> str:
        """Apply professional style to content."""
        # Add professional greeting and closing if not already present
        if not content.startswith(("Dear", "Hello", "Good morning/afternoon/evening")):
            content = "Dear User,\n\n" + content
        
        if not content.endswith(("\nBest regards,", "\nSincerely,", "\nRespectfully,")):
            content = content + "\n\nBest regards,\nAI Assistant"
        
        return content
    
    def _apply_concise_style(self, content: str) -> str:
        """Apply concise style to content."""
        # Remove redundant words and phrases
        content = re.sub(r'\b(in order to|for the purpose of|due to the fact that)\b', 'to', content, flags=re.IGNORECASE)
        content = re.sub(r'\b(it is important to note that|it should be noted that)\b', '', content, flags=re.IGNORECASE)
        
        return content.strip()
    
    def _apply_detailed_style(self, content: str) -> str:
        """Apply detailed style to content."""
        # Add detail indicators if not already present
        if not re.search(r'\b(detailed|comprehensive|in-depth|thorough)\b', content, re.IGNORECASE):
            content = "Detailed Analysis:\n\n" + content
        
        return content