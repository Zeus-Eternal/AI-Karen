"""
Tool integration service for chat system.

This module provides a comprehensive tool integration framework for
custom tools, plugins, and external service integrations.
"""

from __future__ import annotations

import asyncio
import logging
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Type
import uuid

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

logger = logging.getLogger(__name__)


class ToolType(str, Enum):
    """Types of tools."""
    BUILTIN = "builtin"
    PLUGIN = "plugin"
    EXTERNAL_API = "external_api"
    CODE_EXECUTION = "code_execution"
    WEBHOOK = "webhook"


class ToolStatus(str, Enum):
    """Tool status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPRECATED = "deprecated"


class ParameterType(str, Enum):
    """Parameter types for tools."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: ParameterType
    description: str
    required: bool = True
    default_value: Any = None
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    examples: List[Any] = field(default_factory=list)


@dataclass
class ToolMetadata:
    """Tool metadata information."""
    name: str
    display_name: str
    description: str
    version: str
    author: str
    category: str
    tags: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    icon_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class ToolExecutionContext(BaseModel):
    """Context for tool execution."""
    user_id: str = Field(..., description="User ID")
    conversation_id: str = Field(..., description="Conversation ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Execution ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ToolExecutionResult(BaseModel):
    """Result of tool execution."""
    success: bool = Field(..., description="Whether execution was successful")
    result: Any = Field(None, description="Tool execution result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    execution_time: float = Field(..., description="Execution time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional result metadata")
    artifacts: List[Dict[str, Any]] = Field(default_factory=list, description="Generated artifacts")


class BaseTool(ABC):
    """Base class for all tools."""
    
    def __init__(self, metadata: ToolMetadata, parameters: List[ToolParameter]):
        self.metadata = metadata
        self.parameters = {param.name: param for param in parameters}
        self.status = ToolStatus.ACTIVE
        self._execution_count = 0
        self._last_execution: Optional[datetime] = None
    
    @abstractmethod
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolExecutionResult:
        """Execute the tool with given parameters."""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate tool parameters."""
        errors = []
        
        # Check required parameters
        for param_name, param_def in self.parameters.items():
            if param_def.required and param_name not in parameters:
                errors.append(f"Required parameter '{param_name}' is missing")
                continue
            
            if param_name in parameters:
                value = parameters[param_name]
                
                # Type validation
                if not self._validate_parameter_type(value, param_def.type):
                    errors.append(f"Parameter '{param_name}' has invalid type")
                
                # Custom validation rules
                if param_def.validation_rules:
                    validation_errors = self._apply_validation_rules(
                        param_name, value, param_def.validation_rules
                    )
                    errors.extend(validation_errors)
        
        return len(errors) == 0, errors
    
    def _validate_parameter_type(self, value: Any, param_type: ParameterType) -> bool:
        """Validate parameter type."""
        if param_type == ParameterType.STRING:
            return isinstance(value, str)
        elif param_type == ParameterType.INTEGER:
            return isinstance(value, int)
        elif param_type == ParameterType.FLOAT:
            return isinstance(value, (int, float))
        elif param_type == ParameterType.BOOLEAN:
            return isinstance(value, bool)
        elif param_type == ParameterType.ARRAY:
            return isinstance(value, list)
        elif param_type == ParameterType.OBJECT:
            return isinstance(value, dict)
        elif param_type == ParameterType.FILE:
            return isinstance(value, str)  # File ID or path
        else:
            return True
    
    def _apply_validation_rules(
        self,
        param_name: str,
        value: Any,
        rules: Dict[str, Any]
    ) -> List[str]:
        """Apply custom validation rules."""
        errors = []
        
        # Min/max length for strings and arrays
        if "min_length" in rules and hasattr(value, "__len__"):
            if len(value) < rules["min_length"]:
                errors.append(f"Parameter '{param_name}' is too short")
        
        if "max_length" in rules and hasattr(value, "__len__"):
            if len(value) > rules["max_length"]:
                errors.append(f"Parameter '{param_name}' is too long")
        
        # Min/max value for numbers
        if "min_value" in rules and isinstance(value, (int, float)):
            if value < rules["min_value"]:
                errors.append(f"Parameter '{param_name}' is too small")
        
        if "max_value" in rules and isinstance(value, (int, float)):
            if value > rules["max_value"]:
                errors.append(f"Parameter '{param_name}' is too large")
        
        # Pattern matching for strings
        if "pattern" in rules and isinstance(value, str):
            import re
            if not re.match(rules["pattern"], value):
                errors.append(f"Parameter '{param_name}' doesn't match required pattern")
        
        # Allowed values
        if "allowed_values" in rules:
            if value not in rules["allowed_values"]:
                errors.append(f"Parameter '{param_name}' has invalid value")
        
        return errors
    
    def get_info(self) -> Dict[str, Any]:
        """Get tool information."""
        return {
            "metadata": {
                "name": self.metadata.name,
                "display_name": self.metadata.display_name,
                "description": self.metadata.description,
                "version": self.metadata.version,
                "author": self.metadata.author,
                "category": self.metadata.category,
                "tags": self.metadata.tags,
                "documentation_url": self.metadata.documentation_url,
                "icon_url": self.metadata.icon_url
            },
            "parameters": [
                {
                    "name": param.name,
                    "type": param.type.value,
                    "description": param.description,
                    "required": param.required,
                    "default_value": param.default_value,
                    "validation_rules": param.validation_rules,
                    "examples": param.examples
                }
                for param in self.parameters.values()
            ],
            "status": self.status.value,
            "execution_count": self._execution_count,
            "last_execution": self._last_execution.isoformat() if self._last_execution else None
        }


class BuiltinTool(BaseTool):
    """Built-in tool implementation."""
    
    def __init__(
        self,
        metadata: ToolMetadata,
        parameters: List[ToolParameter],
        execution_function: Callable
    ):
        super().__init__(metadata, parameters)
        self.execution_function = execution_function
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolExecutionResult:
        """Execute built-in tool."""
        import time
        start_time = time.time()
        
        try:
            # Validate parameters
            is_valid, errors = self.validate_parameters(parameters)
            if not is_valid:
                return ToolExecutionResult(
                    success=False,
                    error_message=f"Parameter validation failed: {', '.join(errors)}",
                    execution_time=time.time() - start_time
                )
            
            # Execute function
            if asyncio.iscoroutinefunction(self.execution_function):
                result = await self.execution_function(parameters, context)
            else:
                result = self.execution_function(parameters, context)
            
            self._execution_count += 1
            self._last_execution = datetime.utcnow()
            
            return ToolExecutionResult(
                success=True,
                result=result,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Built-in tool execution failed: {e}", exc_info=True)
            return ToolExecutionResult(
                success=False,
                error_message=str(e),
                execution_time=time.time() - start_time
            )


class ExternalAPITool(BaseTool):
    """External API tool implementation."""
    
    def __init__(
        self,
        metadata: ToolMetadata,
        parameters: List[ToolParameter],
        api_config: Dict[str, Any]
    ):
        super().__init__(metadata, parameters)
        self.api_config = api_config
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolExecutionResult:
        """Execute external API tool."""
        import time
        import aiohttp
        
        start_time = time.time()
        
        try:
            # Validate parameters
            is_valid, errors = self.validate_parameters(parameters)
            if not is_valid:
                return ToolExecutionResult(
                    success=False,
                    error_message=f"Parameter validation failed: {', '.join(errors)}",
                    execution_time=time.time() - start_time
                )
            
            # Prepare API request
            url = self.api_config["url"]
            method = self.api_config.get("method", "POST")
            headers = self.api_config.get("headers", {})
            timeout = self.api_config.get("timeout", 30)
            
            # Build request data
            request_data = self._build_api_request(parameters)
            
            # Make API call
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    json=request_data if method in ["POST", "PUT", "PATCH"] else None,
                    params=request_data if method == "GET" else None,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        self._execution_count += 1
                        self._last_execution = datetime.utcnow()
                        
                        return ToolExecutionResult(
                            success=True,
                            result=result,
                            execution_time=time.time() - start_time,
                            metadata={"status_code": response.status}
                        )
                    else:
                        error_text = await response.text()
                        return ToolExecutionResult(
                            success=False,
                            error_message=f"API call failed with status {response.status}: {error_text}",
                            execution_time=time.time() - start_time,
                            metadata={"status_code": response.status}
                        )
            
        except Exception as e:
            logger.error(f"External API tool execution failed: {e}", exc_info=True)
            return ToolExecutionResult(
                success=False,
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def _build_api_request(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Build API request from parameters."""
        # Apply parameter mapping if configured
        mapping = self.api_config.get("parameter_mapping", {})
        
        request_data = {}
        for param_name, param_value in parameters.items():
            api_param_name = mapping.get(param_name, param_name)
            request_data[api_param_name] = param_value
        
        # Add static parameters if configured
        static_params = self.api_config.get("static_parameters", {})
        request_data.update(static_params)
        
        return request_data


class ToolIntegrationService:
    """
    Service for managing tool integrations in the chat system.
    
    Features:
    - Tool registration and management
    - Parameter validation and execution
    - Built-in and external tool support
    - Tool discovery and documentation
    - Execution history and analytics
    """
    
    def __init__(self):
        self._registered_tools: Dict[str, BaseTool] = {}
        self._tool_categories: Dict[str, List[str]] = {}
        self._execution_history: List[Dict[str, Any]] = []
        
        # Initialize built-in tools
        self._register_builtin_tools()
        
        logger.info("ToolIntegrationService initialized")
    
    def _register_builtin_tools(self):
        """Register built-in tools."""
        # Calculator tool
        calculator_metadata = ToolMetadata(
            name="calculator",
            display_name="Calculator",
            description="Perform mathematical calculations",
            version="1.0.0",
            author="System",
            category="math"
        )
        
        calculator_params = [
            ToolParameter(
                name="expression",
                type=ParameterType.STRING,
                description="Mathematical expression to evaluate",
                examples=["2 + 2", "sqrt(16)", "sin(pi/2)"]
            )
        ]
        
        calculator_tool = BuiltinTool(
            calculator_metadata,
            calculator_params,
            self._calculator_function
        )
        
        self.register_tool(calculator_tool)
        
        # Text analyzer tool
        text_analyzer_metadata = ToolMetadata(
            name="text_analyzer",
            display_name="Text Analyzer",
            description="Analyze text for various properties",
            version="1.0.0",
            author="System",
            category="text"
        )
        
        text_analyzer_params = [
            ToolParameter(
                name="text",
                type=ParameterType.STRING,
                description="Text to analyze",
                validation_rules={"min_length": 1, "max_length": 10000}
            ),
            ToolParameter(
                name="analysis_type",
                type=ParameterType.STRING,
                description="Type of analysis to perform",
                default_value="basic",
                validation_rules={"allowed_values": ["basic", "sentiment", "keywords", "readability"]}
            )
        ]
        
        text_analyzer_tool = BuiltinTool(
            text_analyzer_metadata,
            text_analyzer_params,
            self._text_analyzer_function
        )
        
        self.register_tool(text_analyzer_tool)
        
        # URL shortener tool (external API example)
        url_shortener_metadata = ToolMetadata(
            name="url_shortener",
            display_name="URL Shortener",
            description="Shorten long URLs",
            version="1.0.0",
            author="System",
            category="utility"
        )
        
        url_shortener_params = [
            ToolParameter(
                name="url",
                type=ParameterType.STRING,
                description="URL to shorten",
                validation_rules={"pattern": r"^https?://.*"}
            )
        ]
        
        url_shortener_config = {
            "url": "https://api.example.com/shorten",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "parameter_mapping": {"url": "long_url"},
            "timeout": 10
        }
        
        url_shortener_tool = ExternalAPITool(
            url_shortener_metadata,
            url_shortener_params,
            url_shortener_config
        )
        
        # Note: Not registering this as it requires a real API
        # self.register_tool(url_shortener_tool)
    
    def _calculator_function(self, parameters: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        """Built-in calculator function."""
        import math
        import re
        
        expression = parameters["expression"]
        
        # Security: Only allow safe mathematical operations
        allowed_names = {
            "abs", "acos", "asin", "atan", "atan2", "ceil", "cos", "cosh",
            "degrees", "e", "exp", "fabs", "floor", "fmod", "frexp", "hypot",
            "ldexp", "log", "log10", "modf", "pi", "pow", "radians", "sin",
            "sinh", "sqrt", "tan", "tanh"
        }
        
        # Remove any non-mathematical characters
        safe_expression = re.sub(r'[^0-9+\-*/().\s]', '', expression)
        
        # Replace mathematical functions
        for name in allowed_names:
            if name in expression:
                safe_expression = expression.replace(name, f"math.{name}")
        
        try:
            # Evaluate safely
            result = eval(safe_expression, {"__builtins__": {}, "math": math})
            
            return {
                "expression": expression,
                "result": result,
                "type": type(result).__name__
            }
            
        except Exception as e:
            raise ValueError(f"Invalid mathematical expression: {str(e)}")
    
    def _text_analyzer_function(self, parameters: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        """Built-in text analyzer function."""
        text = parameters["text"]
        analysis_type = parameters.get("analysis_type", "basic")
        
        result = {
            "text_length": len(text),
            "word_count": len(text.split()),
            "character_count": len(text),
            "line_count": len(text.split('\n'))
        }
        
        if analysis_type == "basic":
            result.update({
                "sentence_count": len([s for s in text.split('.') if s.strip()]),
                "paragraph_count": len([p for p in text.split('\n\n') if p.strip()])
            })
        
        elif analysis_type == "sentiment":
            # Simple sentiment analysis (placeholder)
            positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic"]
            negative_words = ["bad", "terrible", "awful", "horrible", "disappointing"]
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                sentiment = "positive"
            elif negative_count > positive_count:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            
            result.update({
                "sentiment": sentiment,
                "positive_indicators": positive_count,
                "negative_indicators": negative_count
            })
        
        elif analysis_type == "keywords":
            # Simple keyword extraction
            words = text.lower().split()
            word_freq = {}
            
            for word in words:
                # Remove punctuation
                clean_word = ''.join(c for c in word if c.isalnum())
                if len(clean_word) > 3:  # Only words longer than 3 characters
                    word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
            
            # Get top keywords
            keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            result.update({
                "keywords": [{"word": word, "frequency": freq} for word, freq in keywords],
                "unique_words": len(word_freq)
            })
        
        elif analysis_type == "readability":
            # Simple readability metrics
            sentences = len([s for s in text.split('.') if s.strip()])
            words = len(text.split())
            syllables = sum(max(1, len([c for c in word if c.lower() in 'aeiou'])) for word in text.split())
            
            # Flesch Reading Ease (simplified)
            if sentences > 0 and words > 0:
                flesch_score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
                flesch_score = max(0, min(100, flesch_score))  # Clamp to 0-100
            else:
                flesch_score = 0
            
            result.update({
                "flesch_reading_ease": round(flesch_score, 2),
                "avg_words_per_sentence": round(words / sentences, 2) if sentences > 0 else 0,
                "avg_syllables_per_word": round(syllables / words, 2) if words > 0 else 0
            })
        
        return result
    
    def register_tool(self, tool: BaseTool) -> bool:
        """Register a tool."""
        try:
            self._registered_tools[tool.metadata.name] = tool
            
            # Update category index
            category = tool.metadata.category
            if category not in self._tool_categories:
                self._tool_categories[category] = []
            
            if tool.metadata.name not in self._tool_categories[category]:
                self._tool_categories[category].append(tool.metadata.name)
            
            logger.info(f"Tool '{tool.metadata.name}' registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register tool '{tool.metadata.name}': {e}")
            return False
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool."""
        try:
            if tool_name in self._registered_tools:
                tool = self._registered_tools[tool_name]
                
                # Remove from category index
                category = tool.metadata.category
                if category in self._tool_categories:
                    if tool_name in self._tool_categories[category]:
                        self._tool_categories[category].remove(tool_name)
                    
                    # Remove empty categories
                    if not self._tool_categories[category]:
                        del self._tool_categories[category]
                
                # Remove tool
                del self._registered_tools[tool_name]
                
                logger.info(f"Tool '{tool_name}' unregistered successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to unregister tool '{tool_name}': {e}")
            return False
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolExecutionResult:
        """Execute a tool."""
        try:
            if tool_name not in self._registered_tools:
                return ToolExecutionResult(
                    success=False,
                    error_message=f"Tool '{tool_name}' not found",
                    execution_time=0.0
                )
            
            tool = self._registered_tools[tool_name]
            
            # Check tool status
            if tool.status != ToolStatus.ACTIVE:
                return ToolExecutionResult(
                    success=False,
                    error_message=f"Tool '{tool_name}' is not active (status: {tool.status.value})",
                    execution_time=0.0
                )
            
            # Execute tool
            result = await tool.execute(parameters, context)
            
            # Record execution history
            self._execution_history.append({
                "tool_name": tool_name,
                "execution_id": context.execution_id,
                "user_id": context.user_id,
                "conversation_id": context.conversation_id,
                "timestamp": context.timestamp.isoformat(),
                "success": result.success,
                "execution_time": result.execution_time,
                "error_message": result.error_message
            })
            
            # Keep history limited
            if len(self._execution_history) > 1000:
                self._execution_history = self._execution_history[-1000:]
            
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return ToolExecutionResult(
                success=False,
                error_message=f"Tool execution failed: {str(e)}",
                execution_time=0.0
            )
    
    def get_available_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        tools = []
        
        for tool_name, tool in self._registered_tools.items():
            if category and tool.metadata.category != category:
                continue
            
            tools.append(tool.get_info())
        
        return tools
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific tool."""
        if tool_name in self._registered_tools:
            return self._registered_tools[tool_name].get_info()
        return None
    
    def get_categories(self) -> Dict[str, List[str]]:
        """Get tool categories and their tools."""
        return self._tool_categories.copy()
    
    def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """Search tools by name, description, or tags."""
        query_lower = query.lower()
        matching_tools = []
        
        for tool in self._registered_tools.values():
            # Search in name, display name, description, and tags
            searchable_text = " ".join([
                tool.metadata.name,
                tool.metadata.display_name,
                tool.metadata.description,
                " ".join(tool.metadata.tags)
            ]).lower()
            
            if query_lower in searchable_text:
                matching_tools.append(tool.get_info())
        
        return matching_tools
    
    def get_execution_history(
        self,
        user_id: Optional[str] = None,
        tool_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get execution history with optional filtering."""
        history = self._execution_history.copy()
        
        # Apply filters
        if user_id:
            history = [h for h in history if h["user_id"] == user_id]
        
        if tool_name:
            history = [h for h in history if h["tool_name"] == tool_name]
        
        # Sort by timestamp (newest first) and limit
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        return history[:limit]
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        total_tools = len(self._registered_tools)
        active_tools = sum(1 for tool in self._registered_tools.values() if tool.status == ToolStatus.ACTIVE)
        total_executions = len(self._execution_history)
        successful_executions = sum(1 for h in self._execution_history if h["success"])
        
        # Tool usage statistics
        tool_usage = {}
        for history_item in self._execution_history:
            tool_name = history_item["tool_name"]
            tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
        
        return {
            "total_tools": total_tools,
            "active_tools": active_tools,
            "categories": len(self._tool_categories),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0.0,
            "most_used_tools": sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:10],
            "tool_categories": list(self._tool_categories.keys())
        }