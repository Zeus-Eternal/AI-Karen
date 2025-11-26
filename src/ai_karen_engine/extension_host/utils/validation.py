"""
Validation utilities for extension manifests and configuration.

This module provides validation functions for extension manifests and related
configuration data structures.
"""

import json
from typing import Any, Dict, List, Optional
import logging
from jsonschema import validate, ValidationError

from ..errors import ExtensionValidationError

logger = logging.getLogger(__name__)

# Schema for extension manifests
EXTENSION_MANIFEST_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_\\.]*[a-z0-9]$",
            "description": "Unique identifier for the extension"
        },
        "name": {
            "type": "string",
            "minLength": 1,
            "description": "Human-readable name of the extension"
        },
        "version": {
            "type": "string",
            "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(-[a-z0-9]+)?$",
            "description": "Semantic version of the extension"
        },
        "entrypoint": {
            "type": "string",
            "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*:[a-zA-Z_][a-zA-Z0-9_]*$",
            "description": "Module and class name for the extension entrypoint"
        },
        "description": {
            "type": "string",
            "minLength": 1,
            "description": "Description of what the extension does"
        },
        "hook_points": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "pre_intent_detection",
                    "pre_memory_retrieval", 
                    "post_memory_retrieval",
                    "pre_llm_prompt",
                    "post_llm_result",
                    "post_response"
                ]
            },
            "minItems": 1,
            "description": "List of hook points this extension implements"
        },
        "prompt_files": {
            "type": "object",
            "properties": {
                "system": {
                    "type": "string",
                    "description": "Path to system prompt file"
                },
                "user": {
                    "type": "string", 
                    "description": "Path to user prompt file"
                },
                "assistant": {
                    "type": "string",
                    "description": "Path to assistant prompt file"
                }
            },
            "additionalProperties": False,
            "description": "Mapping of prompt types to file paths"
        },
        "config_schema": {
            "type": "object",
            "description": "JSON Schema for extension configuration"
        },
        "permissions": {
            "type": "object",
            "properties": {
                "memory_read": {
                    "type": "boolean"
                },
                "memory_write": {
                    "type": "boolean"
                },
                "tools": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "additionalProperties": False,
            "description": "Permissions required by this extension"
        },
        "rbac": {
            "type": "object",
            "properties": {
                "allowed_roles": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 1
                },
                "default_enabled": {
                    "type": "boolean"
                }
            },
            "required": ["allowed_roles"],
            "additionalProperties": False,
            "description": "Role-based access control settings"
        },
        "dependencies": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Other extensions this one depends on"
        },
        "author": {
            "type": "string",
            "description": "Author of the extension"
        },
        "homepage": {
            "type": "string",
            "format": "uri",
            "description": "URL for the extension's homepage"
        }
    },
    "required": [
        "id",
        "name", 
        "version",
        "entrypoint",
        "description",
        "hook_points"
    ],
    "additionalProperties": False
}


def validate_manifest(manifest_data: Dict[str, Any]) -> None:
    """
    Validate an extension manifest against the schema.
    
    Args:
        manifest_data: Dictionary containing the manifest data
        
    Raises:
        ExtensionValidationError: If the manifest is invalid
    """
    try:
        validate(instance=manifest_data, schema=EXTENSION_MANIFEST_SCHEMA)
    except ValidationError as e:
        error_msg = f"Manifest validation failed: {e.message}"
        if e.path:
            error_msg += f" at {'.'.join(str(p) for p in e.path)}"
        
        logger.error(error_msg)
        raise ExtensionValidationError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error validating manifest: {str(e)}"
        logger.error(error_msg)
        raise ExtensionValidationError(error_msg) from e


def validate_extension_config(config_data: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """
    Validate extension configuration against a schema.
    
    Args:
        config_data: Dictionary containing the configuration data
        schema: JSON Schema to validate against
        
    Raises:
        ExtensionValidationError: If the configuration is invalid
    """
    try:
        if schema:
            validate(instance=config_data, schema=schema)
    except ValidationError as e:
        error_msg = f"Configuration validation failed: {e.message}"
        if e.path:
            error_msg += f" at {'.'.join(str(p) for p in e.path)}"
        
        logger.error(error_msg)
        raise ExtensionValidationError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error validating configuration: {str(e)}"
        logger.error(error_msg)
        raise ExtensionValidationError(error_msg) from e


def validate_extension_name(name: str) -> bool:
    """
    Validate that an extension name follows the naming conventions.
    
    Extension names should use the format: <category>_<capability>
    
    Args:
        name: The extension name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False
    
    # Check that it contains exactly one underscore
    if name.count('_') != 1:
        return False
    
    # Split into category and capability
    parts = name.split('_')
    category, capability = parts
    
    # Check that both parts are valid
    if not category or not capability:
        return False
    
    # Check that both parts contain only lowercase letters and numbers
    if not (category.islower() and capability.islower()):
        return False
    
    # Check that both parts start with a letter
    if not (category[0].isalpha() and capability[0].isalpha()):
        return False
    
    return True


def validate_hook_point(hook_point: str) -> bool:
    """
    Validate that a hook point name is valid.
    
    Args:
        hook_point: The hook point name to validate
        
    Returns:
        True if valid, False otherwise
    """
    valid_hook_points = [
        "pre_intent_detection",
        "pre_memory_retrieval", 
        "post_memory_retrieval",
        "pre_llm_prompt",
        "post_llm_result",
        "post_response"
    ]
    
    return hook_point in valid_hook_points


def validate_permissions(permissions: Dict[str, Any]) -> List[str]:
    """
    Validate extension permissions and return a list of any issues.
    
    Args:
        permissions: Dictionary containing the permissions
        
    Returns:
        List of validation issues (empty if valid)
    """
    issues = []
    
    if not isinstance(permissions, dict):
        issues.append("Permissions must be a dictionary")
        return issues
    
    # Check for unknown permission types
    valid_permission_types = ["memory_read", "memory_write", "tools"]
    for perm_type in permissions:
        if perm_type not in valid_permission_types:
            issues.append(f"Unknown permission type: {perm_type}")
    
    # Check tools permission type
    if "tools" in permissions and not isinstance(permissions["tools"], list):
        issues.append("Tools permission must be a list")
    
    return issues