"""
Agent Validation module for the agent system.

This module implements validation logic for the agent system, including validation of
agent capabilities, tasks, messages, tool access, permissions, configurations,
sessions, and safety checks.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from datetime import datetime
from uuid import uuid4

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

from .agent_schemas import (
    AgentDefinition, AgentTask, AgentMessage, AgentMemory, AgentTool,
    AgentResponse, AgentSession, AgentPermission, AgentCapability,
    AgentStatus, TaskStatus, MessageStatus, PermissionLevel
)

logger = logging.getLogger(__name__)


class AgentValidation(BaseService):
    """
    Agent Validation service for validating agent system components.
    
    This service provides validation logic for all components of the agent system,
    ensuring data integrity and enforcing business rules.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="agent_validation"))
        self._initialized = False
        self._validation_rules: Dict[str, Any] = {}
        self._blacklisted_agents: Set[str] = set()
        self._blacklisted_tools: Set[str] = set()
        self._blacklisted_permissions: Set[str] = set()
    
    async def initialize(self) -> None:
        """Initialize the agent validation service."""
        if self._initialized:
            return
            
        self._validation_rules = {
            "agent_id_pattern": r"^[a-zA-Z0-9_-]{3,50}$",
            "task_id_pattern": r"^[a-zA-Z0-9_-]{3,50}$",
            "message_id_pattern": r"^[a-zA-Z0-9_-]{3,50}$",
            "memory_id_pattern": r"^[a-zA-Z0-9_-]{3,50}$",
            "tool_id_pattern": r"^[a-zA-Z0-9_-]{3,50}$",
            "session_id_pattern": r"^[a-zA-Z0-9_-]{3,50}$",
            "permission_id_pattern": r"^[a-zA-Z0-9_-]{3,50}$",
            "max_agent_capabilities": 100,
            "max_task_retries": 5,
            "max_message_size": 1024 * 1024,  # 1MB
            "max_memory_size": 10 * 1024 * 1024,  # 10MB
            "max_session_duration": 24 * 60 * 60,  # 24 hours
            "max_permission_duration": 30 * 24 * 60 * 60,  # 30 days
            "forbidden_agent_names": ["system", "admin", "root"],
            "forbidden_tool_names": ["system", "admin", "root"],
            "required_agent_fields": ["agent_id", "name", "agent_type"],
            "required_task_fields": ["task_id", "agent_id", "task_type"],
            "required_message_fields": ["message_id", "sender_id", "recipient_id", "message_type", "content"],
            "required_memory_fields": ["memory_id", "agent_id", "content"],
            "required_tool_fields": ["tool_id", "name"],
            "required_session_fields": ["session_id", "agent_id"],
            "required_permission_fields": ["permission_id", "agent_id", "resource", "level"],
        }
        
        self._initialized = True
        logger.info("Agent validation service initialized successfully")
    
    async def validate_agent_capability(self, capability: AgentCapability) -> Tuple[bool, List[str]]:
        """
        Validate an agent capability.
        
        Args:
            capability: The agent capability to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate name
        if not capability.name or not isinstance(capability.name, str):
            errors.append("Capability name is required and must be a string")
        elif len(capability.name) < 3 or len(capability.name) > 50:
            errors.append("Capability name must be between 3 and 50 characters")
        
        # Validate version
        if not capability.version or not isinstance(capability.version, str):
            errors.append("Capability version is required and must be a string")
        
        # Validate parameters
        if not isinstance(capability.parameters, dict):
            errors.append("Capability parameters must be a dictionary")
        
        # Validate dependencies
        if not isinstance(capability.dependencies, list):
            errors.append("Capability dependencies must be a list")
        
        return len(errors) == 0, errors
    
    async def validate_agent_definition(self, agent: AgentDefinition) -> Tuple[bool, List[str]]:
        """
        Validate an agent definition.
        
        Args:
            agent: The agent definition to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate required fields
        for field in self._validation_rules["required_agent_fields"]:
            if not getattr(agent, field, None):
                errors.append(f"Required field '{field}' is missing")
        
        # Validate agent_id
        if agent.agent_id:
            if not re.match(self._validation_rules["agent_id_pattern"], agent.agent_id):
                errors.append("Agent ID must be 3-50 characters and contain only letters, numbers, hyphens, and underscores")
            
            if agent.agent_id.lower() in self._validation_rules["forbidden_agent_names"]:
                errors.append(f"Agent name '{agent.agent_id}' is not allowed")
            
            if agent.agent_id in self._blacklisted_agents:
                errors.append(f"Agent ID '{agent.agent_id}' is blacklisted")
        
        # Validate name
        if agent.name and (len(agent.name) < 3 or len(agent.name) > 100):
            errors.append("Agent name must be between 3 and 100 characters")
        
        # Validate agent_type
        if agent.agent_type and (len(agent.agent_type) < 3 or len(agent.agent_type) > 50):
            errors.append("Agent type must be between 3 and 50 characters")
        
        # Validate capabilities
        if not isinstance(agent.capabilities, list):
            errors.append("Agent capabilities must be a list")
        elif len(agent.capabilities) > self._validation_rules["max_agent_capabilities"]:
            errors.append(f"Agent cannot have more than {self._validation_rules['max_agent_capabilities']} capabilities")
        else:
            for capability in agent.capabilities:
                is_valid, cap_errors = await self.validate_agent_capability(capability)
                if not is_valid:
                    errors.extend([f"Capability error: {error}" for error in cap_errors])
        
        # Validate status
        if agent.status not in AgentStatus:
            errors.append(f"Invalid agent status: {agent.status}")
        
        return len(errors) == 0, errors
    
    async def validate_agent_task(self, task: AgentTask) -> Tuple[bool, List[str]]:
        """
        Validate an agent task.
        
        Args:
            task: The agent task to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate required fields
        for field in self._validation_rules["required_task_fields"]:
            if not getattr(task, field, None):
                errors.append(f"Required field '{field}' is missing")
        
        # Validate task_id
        if task.task_id and not re.match(self._validation_rules["task_id_pattern"], task.task_id):
            errors.append("Task ID must be 3-50 characters and contain only letters, numbers, hyphens, and underscores")
        
        # Validate priority
        if not isinstance(task.priority, int) or task.priority < 0:
            errors.append("Task priority must be a non-negative integer")
        
        # Validate progress
        if not isinstance(task.progress, (int, float)) or task.progress < 0 or task.progress > 1:
            errors.append("Task progress must be a number between 0.0 and 1.0")
        
        # Validate retry count
        if not isinstance(task.retry_count, int) or task.retry_count < 0:
            errors.append("Task retry count must be a non-negative integer")
        
        # Validate max retries
        if not isinstance(task.max_retries, int) or task.max_retries < 0:
            errors.append("Task max retries must be a non-negative integer")
        elif task.max_retries > self._validation_rules["max_task_retries"]:
            errors.append(f"Task max retries cannot exceed {self._validation_rules['max_task_retries']}")
        
        # Validate timeout
        if task.timeout_seconds is not None and (not isinstance(task.timeout_seconds, int) or task.timeout_seconds <= 0):
            errors.append("Task timeout must be a positive integer")
        
        # Validate status
        if task.status not in TaskStatus:
            errors.append(f"Invalid task status: {task.status}")
        
        # Validate timestamps
        if task.started_at and task.started_at < task.created_at:
            errors.append("Task start time cannot be before creation time")
        
        if task.completed_at and task.started_at and task.completed_at < task.started_at:
            errors.append("Task completion time cannot be before start time")
        
        return len(errors) == 0, errors
    
    async def validate_agent_message(self, message: AgentMessage) -> Tuple[bool, List[str]]:
        """
        Validate an agent message.
        
        Args:
            message: The agent message to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate required fields
        for field in self._validation_rules["required_message_fields"]:
            if not getattr(message, field, None):
                errors.append(f"Required field '{field}' is missing")
        
        # Validate message_id
        if message.message_id and not re.match(self._validation_rules["message_id_pattern"], message.message_id):
            errors.append("Message ID must be 3-50 characters and contain only letters, numbers, hyphens, and underscores")
        
        # Validate sender and recipient
        if message.sender_id == message.recipient_id:
            errors.append("Message sender and recipient cannot be the same")
        
        # Validate content
        if not isinstance(message.content, dict):
            errors.append("Message content must be a dictionary")
        
        # Check message size
        content_size = len(str(message.content).encode('utf-8'))
        if content_size > self._validation_rules["max_message_size"]:
            errors.append(f"Message content exceeds maximum size of {self._validation_rules['max_message_size']} bytes")
        
        # Validate priority
        if not isinstance(message.priority, int) or message.priority < 0:
            errors.append("Message priority must be a non-negative integer")
        
        # Validate status
        if message.status not in MessageStatus:
            errors.append(f"Invalid message status: {message.status}")
        
        # Validate timestamps
        if message.delivered_at and message.delivered_at < message.created_at:
            errors.append("Message delivery time cannot be before creation time")
        
        if message.read_at and message.delivered_at and message.read_at < message.delivered_at:
            errors.append("Message read time cannot be before delivery time")
        
        if message.processed_at and message.read_at and message.processed_at < message.read_at:
            errors.append("Message processed time cannot be before read time")
        
        return len(errors) == 0, errors
    
    async def validate_agent_tool_access(self, agent_id: str, tool_id: str, 
                                        permissions: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate agent tool access.
        
        Args:
            agent_id: ID of the agent requesting access
            tool_id: ID of the tool being accessed
            permissions: List of permissions the agent has
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if agent is blacklisted
        if agent_id in self._blacklisted_agents:
            errors.append(f"Agent '{agent_id}' is blacklisted")
        
        # Check if tool is blacklisted
        if tool_id in self._blacklisted_tools:
            errors.append(f"Tool '{tool_id}' is blacklisted")
        
        # Check if agent has required permissions
        if "tool_access" not in permissions:
            errors.append("Agent does not have tool access permission")
        
        return len(errors) == 0, errors
    
    async def validate_agent_permission(self, permission: AgentPermission) -> Tuple[bool, List[str]]:
        """
        Validate an agent permission.
        
        Args:
            permission: The agent permission to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate required fields
        for field in self._validation_rules["required_permission_fields"]:
            if not getattr(permission, field, None):
                errors.append(f"Required field '{field}' is missing")
        
        # Validate permission_id
        if permission.permission_id and not re.match(self._validation_rules["permission_id_pattern"], permission.permission_id):
            errors.append("Permission ID must be 3-50 characters and contain only letters, numbers, hyphens, and underscores")
        
        # Validate level
        if permission.level not in PermissionLevel:
            errors.append(f"Invalid permission level: {permission.level}")
        
        # Validate resource
        if not permission.resource or len(permission.resource) < 3:
            errors.append("Permission resource must be at least 3 characters")
        
        # Check if permission is blacklisted
        if permission.permission_id in self._blacklisted_permissions:
            errors.append(f"Permission '{permission.permission_id}' is blacklisted")
        
        # Validate timestamps
        if permission.expires_at and permission.expires_at < permission.granted_at:
            errors.append("Permission expiration time cannot be before grant time")
        
        return len(errors) == 0, errors
    
    async def validate_agent_configuration(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate agent configuration.
        
        Args:
            config: The agent configuration to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate config is a dictionary
        if not isinstance(config, dict):
            errors.append("Configuration must be a dictionary")
            return False, errors
        
        # Validate required configuration keys
        required_keys = ["name", "agent_type"]
        for key in required_keys:
            if key not in config:
                errors.append(f"Required configuration key '{key}' is missing")
        
        # Validate name
        if "name" in config:
            name = config["name"]
            if not isinstance(name, str) or len(name) < 3 or len(name) > 100:
                errors.append("Agent name must be a string between 3 and 100 characters")
            elif name.lower() in self._validation_rules["forbidden_agent_names"]:
                errors.append(f"Agent name '{name}' is not allowed")
        
        # Validate agent_type
        if "agent_type" in config:
            agent_type = config["agent_type"]
            if not isinstance(agent_type, str) or len(agent_type) < 3 or len(agent_type) > 50:
                errors.append("Agent type must be a string between 3 and 50 characters")
        
        # Validate capabilities if present
        if "capabilities" in config:
            capabilities = config["capabilities"]
            if not isinstance(capabilities, list):
                errors.append("Capabilities must be a list")
            elif len(capabilities) > self._validation_rules["max_agent_capabilities"]:
                errors.append(f"Cannot have more than {self._validation_rules['max_agent_capabilities']} capabilities")
        
        return len(errors) == 0, errors
    
    async def validate_agent_session(self, session: AgentSession) -> Tuple[bool, List[str]]:
        """
        Validate an agent session.
        
        Args:
            session: The agent session to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate required fields
        for field in self._validation_rules["required_session_fields"]:
            if not getattr(session, field, None):
                errors.append(f"Required field '{field}' is missing")
        
        # Validate session_id
        if session.session_id and not re.match(self._validation_rules["session_id_pattern"], session.session_id):
            errors.append("Session ID must be 3-50 characters and contain only letters, numbers, hyphens, and underscores")
        
        # Validate context
        if not isinstance(session.context, dict):
            errors.append("Session context must be a dictionary")
        
        # Validate status
        valid_statuses = ["active", "inactive", "expired", "terminated"]
        if session.status not in valid_statuses:
            errors.append(f"Invalid session status: {session.status}")
        
        # Validate session duration
        if session.expires_at:
            duration = (session.expires_at - session.created_at).total_seconds()
            if duration > self._validation_rules["max_session_duration"]:
                errors.append(f"Session duration cannot exceed {self._validation_rules['max_session_duration']} seconds")
        
        # Validate timestamps
        if session.last_activity < session.created_at:
            errors.append("Last activity time cannot be before creation time")
        
        return len(errors) == 0, errors
    
    async def validate_agent_safety(self, agent_id: str, action: str, 
                                   data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate agent safety for an action.
        
        Args:
            agent_id: ID of the agent performing the action
            action: Action being performed
            data: Data associated with the action
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if agent is blacklisted
        if agent_id in self._blacklisted_agents:
            errors.append(f"Agent '{agent_id}' is blacklisted")
        
        # Validate action
        if not action or not isinstance(action, str):
            errors.append("Action must be a non-empty string")
        
        # Validate data
        if not isinstance(data, dict):
            errors.append("Action data must be a dictionary")
        
        # Check for potentially dangerous actions
        dangerous_actions = ["system", "admin", "root", "delete_all", "format"]
        for dangerous in dangerous_actions:
            if dangerous.lower() in action.lower():
                errors.append(f"Action '{action}' contains potentially dangerous keyword '{dangerous}'")
        
        # Check for sensitive data patterns
        sensitive_patterns = [
            r"password\s*[:=]\s*[^\s]+",
            r"api_key\s*[:=]\s*[^\s]+",
            r"token\s*[:=]\s*[^\s]+",
            r"secret\s*[:=]\s*[^\s]+"
        ]
        
        data_str = str(data)
        for pattern in sensitive_patterns:
            if re.search(pattern, data_str, re.IGNORECASE):
                errors.append(f"Action data contains potentially sensitive information")
                break
        
        return len(errors) == 0, errors
    
    async def health_check(self) -> bool:
        """Check the health of the agent validation service."""
        return self._initialized
    
    def add_blacklisted_agent(self, agent_id: str) -> None:
        """Add an agent to the blacklist."""
        self._blacklisted_agents.add(agent_id)
        logger.info(f"Added agent '{agent_id}' to blacklist")
    
    def remove_blacklisted_agent(self, agent_id: str) -> None:
        """Remove an agent from the blacklist."""
        if agent_id in self._blacklisted_agents:
            self._blacklisted_agents.remove(agent_id)
            logger.info(f"Removed agent '{agent_id}' from blacklist")
    
    def add_blacklisted_tool(self, tool_id: str) -> None:
        """Add a tool to the blacklist."""
        self._blacklisted_tools.add(tool_id)
        logger.info(f"Added tool '{tool_id}' to blacklist")
    
    def remove_blacklisted_tool(self, tool_id: str) -> None:
        """Remove a tool from the blacklist."""
        if tool_id in self._blacklisted_tools:
            self._blacklisted_tools.remove(tool_id)
            logger.info(f"Removed tool '{tool_id}' from blacklist")
    
    def add_blacklisted_permission(self, permission_id: str) -> None:
        """Add a permission to the blacklist."""
        self._blacklisted_permissions.add(permission_id)
        logger.info(f"Added permission '{permission_id}' to blacklist")
    
    def remove_blacklisted_permission(self, permission_id: str) -> None:
        """Remove a permission from the blacklist."""
        if permission_id in self._blacklisted_permissions:
            self._blacklisted_permissions.remove(permission_id)
            logger.info(f"Removed permission '{permission_id}' from blacklist")
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get the current validation rules."""
        return self._validation_rules.copy()
    
    def update_validation_rules(self, rules: Dict[str, Any]) -> None:
        """Update the validation rules."""
        self._validation_rules.update(rules)
        logger.info("Updated validation rules")
    
    async def start(self) -> None:
        """Start the agent validation service."""
        logger.info("Agent validation service started")
    
    async def stop(self) -> None:
        """Stop the agent validation service."""
        logger.info("Agent validation service stopped")