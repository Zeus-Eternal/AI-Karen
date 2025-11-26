"""
Internal validation utilities for the extensions domain.

This module provides validation functions and classes for extension data.
These are not part of the public API and should not be imported from outside the extensions domain.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from .extension_schemas import (
    ExtensionSchema,
    ExtensionManifestSchema,
    ExtensionExecutionSchema,
    ExtensionConfigSchema,
    ExtensionAuthSchema,
    ExtensionPermissionSchema,
    ExtensionCapability,
    ExtensionType,
    ExtensionStatus,
    ExecutionStatus,
    PermissionType,
)


class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


class ExtensionValidator:
    """Validator for extension data."""
    
    @staticmethod
    def validate_extension_id(extension_id: Union[str, UUID]) -> UUID:
        """Validate extension ID format."""
        if isinstance(extension_id, str):
            try:
                return UUID(extension_id)
            except ValueError:
                raise ValidationError(f"Invalid extension ID format: {extension_id}")
        elif isinstance(extension_id, UUID):
            return extension_id
        else:
            raise ValidationError(f"Invalid extension ID type: {type(extension_id)}")
    
    @staticmethod
    def validate_extension_name(name: str) -> str:
        """Validate extension name format."""
        if not name:
            raise ValidationError("Extension name cannot be empty")
        
        # Check for valid characters (alphanumeric, hyphens, underscores, periods)
        if not re.match(r'^[a-zA-Z0-9_.-]+$', name):
            raise ValidationError(f"Invalid extension name format: {name}")
        
        return name
    
    @staticmethod
    def validate_extension_version(version: str) -> str:
        """Validate extension version format."""
        if not version:
            raise ValidationError("Extension version cannot be empty")
        
        # Simple version format check (e.g., "1.0.0")
        if not re.match(r'^[0-9]+(\.[0-9]+)*$', version):
            raise ValidationError(f"Invalid extension version format: {version}")
        
        return version
    
    @staticmethod
    def validate_extension_type(extension_type: Union[str, ExtensionType]) -> ExtensionType:
        """Validate extension type."""
        if isinstance(extension_type, str):
            try:
                return ExtensionType(extension_type.lower())
            except ValueError:
                raise ValidationError(f"Invalid extension type: {extension_type}")
        elif isinstance(extension_type, ExtensionType):
            return extension_type
        else:
            raise ValidationError(f"Invalid extension type: {type(extension_type)}")
    
    @staticmethod
    def validate_extension_status(status: Union[str, ExtensionStatus]) -> ExtensionStatus:
        """Validate extension status."""
        if isinstance(status, str):
            try:
                return ExtensionStatus(status.lower())
            except ValueError:
                raise ValidationError(f"Invalid extension status: {status}")
        elif isinstance(status, ExtensionStatus):
            return status
        else:
            raise ValidationError(f"Invalid extension status type: {type(status)}")
    
    @staticmethod
    def validate_extension_capabilities(capabilities: List[Dict[str, Any]]) -> List[ExtensionCapability]:
        """Validate extension capabilities."""
        validated_capabilities = []
        
        for cap_data in capabilities:
            try:
                capability = ExtensionCapability(**cap_data)
                validated_capabilities.append(capability)
            except Exception as e:
                raise ValidationError(f"Invalid capability: {e}")
        
        # Check for duplicate capability names
        capability_names = [cap.name for cap in validated_capabilities]
        if len(capability_names) != len(set(capability_names)):
            raise ValidationError("Duplicate capability names found")
        
        return validated_capabilities
    
    @staticmethod
    def validate_extension_data(extension_data: Dict[str, Any]) -> ExtensionSchema:
        """Validate extension data."""
        try:
            return ExtensionSchema(**extension_data)
        except Exception as e:
            raise ValidationError(f"Invalid extension data: {e}")


class ManifestValidator:
    """Validator for extension manifest data."""
    
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
    def validate_manifest_data(manifest_data: Dict[str, Any]) -> ExtensionManifestSchema:
        """Validate manifest data."""
        try:
            return ExtensionManifestSchema(**manifest_data)
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
    def validate_extension_directory(extension_dir: Union[str, Path]) -> Path:
        """Validate extension directory structure."""
        extension_dir = Path(extension_dir)
        
        if not extension_dir.exists():
            raise ValidationError(f"Extension directory does not exist: {extension_dir}")
        
        if not extension_dir.is_dir():
            raise ValidationError(f"Extension path is not a directory: {extension_dir}")
        
        # Check for required files
        manifest_path = extension_dir / "extension_manifest.json"
        if not manifest_path.exists():
            raise ValidationError(f"Extension manifest not found: {manifest_path}")
        
        # Validate entry point exists
        manifest_data = ManifestValidator.validate_manifest_file(manifest_path)
        entry_point = manifest_data.get("entry_point", "main.py")
        entry_point_path = extension_dir / entry_point
        
        try:
            ManifestValidator.validate_entry_point(entry_point_path)
        except ValidationError as e:
            raise ValidationError(f"Invalid entry point in extension directory: {e}")
        
        return extension_dir


class ExecutionValidator:
    """Validator for extension execution data."""
    
    @staticmethod
    def validate_execution_id(execution_id: Union[str, UUID]) -> UUID:
        """Validate execution ID format."""
        if isinstance(execution_id, str):
            try:
                return UUID(execution_id)
            except ValueError:
                raise ValidationError(f"Invalid execution ID format: {execution_id}")
        elif isinstance(execution_id, UUID):
            return execution_id
        else:
            raise ValidationError(f"Invalid execution ID type: {type(execution_id)}")
    
    @staticmethod
    def validate_execution_status(status: Union[str, ExecutionStatus]) -> ExecutionStatus:
        """Validate execution status."""
        if isinstance(status, str):
            try:
                return ExecutionStatus(status.lower())
            except ValueError:
                raise ValidationError(f"Invalid execution status: {status}")
        elif isinstance(status, ExecutionStatus):
            return status
        else:
            raise ValidationError(f"Invalid execution status type: {type(status)}")
    
    @staticmethod
    def validate_execution_data(execution_data: Dict[str, Any]) -> ExtensionExecutionSchema:
        """Validate execution data."""
        try:
            return ExtensionExecutionSchema(**execution_data)
        except Exception as e:
            raise ValidationError(f"Invalid execution data: {e}")
    
    @staticmethod
    def validate_request_data(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate request data."""
        if not isinstance(request_data, dict):
            raise ValidationError(f"Request data must be a dictionary: {type(request_data)}")
        
        # Check for circular references
        try:
            json.dumps(request_data)
        except TypeError as e:
            raise ValidationError(f"Invalid request data (not JSON serializable): {e}")
        
        return request_data
    
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
    
    @staticmethod
    def validate_auth(auth: Dict[str, Any]) -> Dict[str, Any]:
        """Validate auth data."""
        if not isinstance(auth, dict):
            raise ValidationError(f"Auth data must be a dictionary: {type(auth)}")
        
        # Check for circular references
        try:
            json.dumps(auth)
        except TypeError as e:
            raise ValidationError(f"Invalid auth data (not JSON serializable): {e}")
        
        return auth


class ConfigValidator:
    """Validator for extension configuration data."""
    
    @staticmethod
    def validate_config_key(config_key: str) -> str:
        """Validate configuration key."""
        if not config_key:
            raise ValidationError("Configuration key cannot be empty")
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', config_key):
            raise ValidationError(f"Invalid configuration key format: {config_key}")
        
        return config_key
    
    @staticmethod
    def validate_config_value(config_value: Any, config_type: str) -> Any:
        """Validate configuration value based on type."""
        try:
            if config_type == 'string':
                return str(config_value)
            elif config_type == 'integer':
                return int(config_value)
            elif config_type == 'float':
                return float(config_value)
            elif config_type == 'boolean':
                if isinstance(config_value, str):
                    return config_value.lower() in ('true', '1', 'yes', 'on')
                return bool(config_value)
            elif config_type == 'list':
                if isinstance(config_value, str):
                    try:
                        return json.loads(config_value)
                    except json.JSONDecodeError:
                        return [config_value]
                return list(config_value)
            elif config_type == 'dict':
                if isinstance(config_value, str):
                    try:
                        return json.loads(config_value)
                    except json.JSONDecodeError:
                        raise ValidationError(f"Invalid dict configuration value: {config_value}")
                return dict(config_value)
            elif config_type == 'json':
                if isinstance(config_value, str):
                    try:
                        return json.loads(config_value)
                    except json.JSONDecodeError:
                        raise ValidationError(f"Invalid JSON configuration value: {config_value}")
                return config_value
            else:
                raise ValidationError(f"Invalid configuration type: {config_type}")
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid configuration value for type {config_type}: {e}")
    
    @staticmethod
    def validate_config_data(config_data: Dict[str, Any]) -> ExtensionConfigSchema:
        """Validate configuration data."""
        try:
            return ExtensionConfigSchema(**config_data)
        except Exception as e:
            raise ValidationError(f"Invalid configuration data: {e}")


class AuthValidator:
    """Validator for extension authentication data."""
    
    @staticmethod
    def validate_auth_type(auth_type: str) -> str:
        """Validate authentication type."""
        allowed_types = ['token', 'api_key', 'oauth', 'jwt', 'basic', 'certificate']
        if auth_type not in allowed_types:
            raise ValidationError(f"Invalid authentication type: {auth_type}")
        return auth_type
    
    @staticmethod
    def validate_auth_data(auth_data: Dict[str, Any], auth_type: str) -> Dict[str, Any]:
        """Validate authentication data based on type."""
        if not isinstance(auth_data, dict):
            raise ValidationError(f"Authentication data must be a dictionary: {type(auth_data)}")
        
        # Type-specific validation
        if auth_type == 'token':
            if 'token' not in auth_data:
                raise ValidationError("Token authentication requires 'token' field")
        elif auth_type == 'api_key':
            if 'api_key' not in auth_data:
                raise ValidationError("API key authentication requires 'api_key' field")
        elif auth_type == 'oauth':
            if 'access_token' not in auth_data:
                raise ValidationError("OAuth authentication requires 'access_token' field")
        elif auth_type == 'jwt':
            if 'jwt_token' not in auth_data:
                raise ValidationError("JWT authentication requires 'jwt_token' field")
        elif auth_type == 'basic':
            if 'username' not in auth_data or 'password' not in auth_data:
                raise ValidationError("Basic authentication requires 'username' and 'password' fields")
        elif auth_type == 'certificate':
            if 'certificate' not in auth_data:
                raise ValidationError("Certificate authentication requires 'certificate' field")
        
        return auth_data
    
    @staticmethod
    def validate_auth_schema(auth_data: Dict[str, Any]) -> ExtensionAuthSchema:
        """Validate authentication schema."""
        try:
            return ExtensionAuthSchema(**auth_data)
        except Exception as e:
            raise ValidationError(f"Invalid authentication data: {e}")