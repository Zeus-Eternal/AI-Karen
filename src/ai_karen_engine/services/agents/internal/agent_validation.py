"""
Internal validation utilities for the agents domain.

This module provides validation functions and classes for agent data.
These are not part of the public API and should not be imported from outside the agents domain.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from .agent_schemas import (
    AgentSchema,
    AgentManifestSchema,
    AgentExecutionSchema,
    AgentCapability,
    AgentType,
    AgentStatus,
    TaskStatus,
)


class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


class AgentValidator:
    """Validator for agent data."""
    
    @staticmethod
    def validate_agent_id(agent_id: Union[str, UUID]) -> UUID:
        """Validate agent ID format."""
        if isinstance(agent_id, str):
            try:
                return UUID(agent_id)
            except ValueError:
                raise ValidationError(f"Invalid agent ID format: {agent_id}")
        elif isinstance(agent_id, UUID):
            return agent_id
        else:
            raise ValidationError(f"Invalid agent ID type: {type(agent_id)}")
    
    @staticmethod
    def validate_agent_name(name: str) -> str:
        """Validate agent name format."""
        if not name:
            raise ValidationError("Agent name cannot be empty")
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValidationError(f"Invalid agent name format: {name}")
        
        return name
    
    @staticmethod
    def validate_agent_version(version: str) -> str:
        """Validate agent version format."""
        if not version:
            raise ValidationError("Agent version cannot be empty")
        
        # Simple version format check (e.g., "1.0.0")
        if not re.match(r'^[0-9]+(\.[0-9]+)*$', version):
            raise ValidationError(f"Invalid agent version format: {version}")
        
        return version
    
    @staticmethod
    def validate_agent_type(agent_type: Union[str, AgentType]) -> AgentType:
        """Validate agent type."""
        if isinstance(agent_type, str):
            try:
                return AgentType(agent_type.lower())
            except ValueError:
                raise ValidationError(f"Invalid agent type: {agent_type}")
        elif isinstance(agent_type, AgentType):
            return agent_type
        else:
            raise ValidationError(f"Invalid agent type: {type(agent_type)}")
    
    @staticmethod
    def validate_agent_status(status: Union[str, AgentStatus]) -> AgentStatus:
        """Validate agent status."""
        if isinstance(status, str):
            try:
                return AgentStatus(status.lower())
            except ValueError:
                raise ValidationError(f"Invalid agent status: {status}")
        elif isinstance(status, AgentStatus):
            return status
        else:
            raise ValidationError(f"Invalid agent status type: {type(status)}")
    
    @staticmethod
    def validate_agent_capabilities(capabilities: List[Dict[str, Any]]) -> List[AgentCapability]:
        """Validate agent capabilities."""
        validated_capabilities = []
        
        for cap_data in capabilities:
            try:
                capability = AgentCapability(**cap_data)
                validated_capabilities.append(capability)
            except Exception as e:
                raise ValidationError(f"Invalid capability: {e}")
        
        # Check for duplicate capability names
        capability_names = [cap.name for cap in validated_capabilities]
        if len(capability_names) != len(set(capability_names)):
            raise ValidationError("Duplicate capability names found")
        
        return validated_capabilities
    
    @staticmethod
    def validate_agent_data(agent_data: Dict[str, Any]) -> AgentSchema:
        """Validate agent data."""
        try:
            return AgentSchema(**agent_data)
        except Exception as e:
            raise ValidationError(f"Invalid agent data: {e}")


class ManifestValidator:
    """Validator for agent manifest data."""
    
    @staticmethod
    def validate_manifest_file(manifest_path: Union[str, Path]) -> Dict[str, Any]:
        """Validate manifest file exists and is valid JSON."""
        manifest_path = Path(manifest_path)
        
        if not manifest_path.exists():
            raise ValidationError(f"Manifest file does not exist: {manifest_path}")
        
        if not manifest_path.is_file():
            raise ValidationError(f"Manifest path is not a file: {manifest_path}")
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in manifest file: {e}")
        except Exception as e:
            raise ValidationError(f"Error reading manifest file: {e}")
        
        return manifest_data
    
    @staticmethod
    def validate_manifest_data(manifest_data: Dict[str, Any]) -> AgentManifestSchema:
        """Validate manifest data."""
        try:
            return AgentManifestSchema(**manifest_data)
        except Exception as e:
            raise ValidationError(f"Invalid manifest data: {e}")
    
    @staticmethod
    def validate_entry_point(entry_point: str, base_path: Optional[Path] = None) -> Path:
        """Validate entry point file exists."""
        entry_point_path = Path(entry_point)
        
        # If base_path is provided, prepend it to the entry point
        if base_path:
            entry_point_path = base_path / entry_point_path
        
        # Resolve relative paths
        entry_point_path = entry_point_path.resolve()
        
        if not entry_point_path.exists():
            raise ValidationError(f"Entry point file does not exist: {entry_point_path}")
        
        if not entry_point_path.is_file():
            raise ValidationError(f"Entry point is not a file: {entry_point_path}")
        
        if not entry_point_path.suffix == '.py':
            raise ValidationError(f"Entry point is not a Python file: {entry_point_path}")
        
        return entry_point_path
    
    @staticmethod
    def validate_agent_directory(agent_dir: Union[str, Path]) -> Path:
        """Validate agent directory structure."""
        agent_dir = Path(agent_dir)
        
        if not agent_dir.exists():
            raise ValidationError(f"Agent directory does not exist: {agent_dir}")
        
        if not agent_dir.is_dir():
            raise ValidationError(f"Agent path is not a directory: {agent_dir}")
        
        # Check for required files
        manifest_path = agent_dir / "agent_manifest.json"
        if not manifest_path.exists():
            raise ValidationError(f"Agent manifest not found: {manifest_path}")
        
        # Validate entry point exists
        manifest_data = ManifestValidator.validate_manifest_file(manifest_path)
        entry_point = manifest_data.get("entry_point", "handler.py")
        entry_point_path = agent_dir / entry_point
        
        try:
            ManifestValidator.validate_entry_point(entry_point_path)
        except ValidationError as e:
            raise ValidationError(f"Invalid entry point in agent directory: {e}")
        
        return agent_dir


class ExecutionValidator:
    """Validator for agent execution data."""
    
    @staticmethod
    def validate_task_id(task_id: Union[str, UUID]) -> UUID:
        """Validate task ID format."""
        if isinstance(task_id, str):
            try:
                return UUID(task_id)
            except ValueError:
                raise ValidationError(f"Invalid task ID format: {task_id}")
        elif isinstance(task_id, UUID):
            return task_id
        else:
            raise ValidationError(f"Invalid task ID type: {type(task_id)}")
    
    @staticmethod
    def validate_task_status(status: Union[str, TaskStatus]) -> TaskStatus:
        """Validate task status."""
        if isinstance(status, str):
            try:
                return TaskStatus(status.lower())
            except ValueError:
                raise ValidationError(f"Invalid task status: {status}")
        elif isinstance(status, TaskStatus):
            return status
        else:
            raise ValidationError(f"Invalid task status type: {type(status)}")
    
    @staticmethod
    def validate_execution_data(execution_data: Dict[str, Any]) -> AgentExecutionSchema:
        """Validate execution data."""
        try:
            return AgentExecutionSchema(**execution_data)
        except Exception as e:
            raise ValidationError(f"Invalid execution data: {e}")
    
    @staticmethod
    def validate_input_data(input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data."""
        if not isinstance(input_data, dict):
            raise ValidationError(f"Input data must be a dictionary: {type(input_data)}")
        
        # Check for circular references
        try:
            json.dumps(input_data)
        except TypeError as e:
            raise ValidationError(f"Invalid input data (not JSON serializable): {e}")
        
        return input_data
    
    @staticmethod
    def validate_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters."""
        if not isinstance(parameters, dict):
            raise ValidationError(f"Parameters must be a dictionary: {type(parameters)}")
        
        # Check for circular references
        try:
            json.dumps(parameters)
        except TypeError as e:
            raise ValidationError(f"Invalid parameters (not JSON serializable): {e}")
        
        return parameters
    
    @staticmethod
    def validate_context(context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate context."""
        if not isinstance(context, dict):
            raise ValidationError(f"Context must be a dictionary: {type(context)}")
        
        # Check for circular references
        try:
            json.dumps(context)
        except TypeError as e:
            raise ValidationError(f"Invalid context (not JSON serializable): {e}")
        
        return context