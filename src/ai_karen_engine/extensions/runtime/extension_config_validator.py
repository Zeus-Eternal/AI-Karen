"""
Extension Configuration Validator service for validating extension configurations.

This service provides capabilities for validating extension configurations,
including schema validation, dependency checking, and security validation.
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import asyncio
import logging
import json
import re
from datetime import datetime

from ai_karen_engine.core.services.base import BaseService, ServiceConfig, ServiceStatus, ServiceHealth


class ExtensionConfigValidator(BaseService):
    """
    Extension Configuration Validator service for validating extension configurations.
    
    This service provides capabilities for validating extension configurations,
    including schema validation, dependency checking, and security validation.
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        super().__init__(config or ServiceConfig(name="extension_config_validator"))
        self._initialized = False
        self._validation_schemas: Dict[str, Dict[str, Any]] = {}  # schema_name -> schema_definition
        self._validation_rules: Dict[str, List[Dict[str, Any]]] = {}  # extension_type -> validation_rules
        self._security_policies: Dict[str, Dict[str, Any]] = {}  # policy_name -> policy_definition
        self._validation_results: Dict[str, Dict[str, Any]] = {}  # extension_id -> validation_result
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize the Extension Configuration Validator service."""
        if self._initialized:
            return
            
        try:
            self.logger.info("Initializing Extension Configuration Validator service")
            
            # Initialize validation schemas
            self._validation_schemas = {}
            self._validation_rules = {}
            self._security_policies = {}
            self._validation_results = {}
            
            # Create default validation schemas
            self._validation_schemas["extension_manifest"] = {
                "type": "object",
                "required": ["name", "version", "description", "entrypoint"],
                "properties": {
                    "name": {
                        "type": "string",
                        "pattern": "^[a-z][a-z0-9-]*[a-z0-9]$",
                        "minLength": 3,
                        "maxLength": 50
                    },
                    "version": {
                        "type": "string",
                        "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"
                    },
                    "description": {
                        "type": "string",
                        "minLength": 10,
                        "maxLength": 500
                    },
                    "entrypoint": {
                        "type": "string",
                        "pattern": "^[a-zA-Z0-9_/\\-]+\\.py$"
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "pattern": "^[a-z][a-z0-9-]*[a-z0-9]$"
                        }
                    },
                    "permissions": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["read", "write", "execute", "network", "storage"]
                        }
                    },
                    "resources": {
                        "type": "object",
                        "properties": {
                            "cpu": {"type": "string"},
                            "memory": {"type": "string"},
                            "storage": {"type": "string"}
                        }
                    }
                }
            }
            
            # Create default validation rules
            self._validation_rules["python"] = [
                {
                    "name": "valid_python_version",
                    "description": "Check if Python version is supported",
                    "check": lambda config: "python_version" not in config or config["python_version"] in ["3.9", "3.10", "3.11"]
                },
                {
                    "name": "valid_dependencies",
                    "description": "Check if dependencies are valid",
                    "check": lambda config: "dependencies" not in config or all(
                        isinstance(dep, str) and re.match(r"^[a-z][a-z0-9\-_\.]*[a-z0-9]$", dep)
                        for dep in config.get("dependencies", [])
                    )
                }
            ]
            
            # Create default security policies
            self._security_policies["default"] = {
                "allowed_permissions": ["read", "write"],
                "restricted_permissions": ["network", "storage"],
                "max_resources": {
                    "cpu": "2",
                    "memory": "4Gi",
                    "storage": "10Gi"
                },
                "allowed_dependencies": [
                    "numpy", "pandas", "requests", "aiofiles", "pydantic"
                ],
                "restricted_dependencies": [
                    "os", "subprocess", "sys", "eval", "exec"
                ]
            }
            
            self._initialized = True
            self._status = ServiceStatus.RUNNING
            self.logger.info("Extension Configuration Validator service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Extension Configuration Validator service: {str(e)}")
            self._status = ServiceStatus.ERROR
            raise
            
    async def register_schema(self, schema_name: str, schema: Dict[str, Any]) -> None:
        """Register a validation schema."""
        async with self._lock:
            self._validation_schemas[schema_name] = schema
            
        self.logger.info(f"Registered validation schema: {schema_name}")
        
    async def get_schema(self, schema_name: str) -> Dict[str, Any]:
        """Get a validation schema."""
        async with self._lock:
            if schema_name not in self._validation_schemas:
                raise ValueError(f"Validation schema '{schema_name}' not found")
                
            return self._validation_schemas[schema_name].copy()
            
    async def list_schemas(self) -> List[str]:
        """List all validation schema names."""
        async with self._lock:
            return list(self._validation_schemas.keys())
            
    async def register_validation_rules(self, extension_type: str, rules: List[Dict[str, Any]]) -> None:
        """Register validation rules for an extension type."""
        async with self._lock:
            self._validation_rules[extension_type] = rules
            
        self.logger.info(f"Registered validation rules for extension type: {extension_type}")
        
    async def get_validation_rules(self, extension_type: str) -> List[Dict[str, Any]]:
        """Get validation rules for an extension type."""
        async with self._lock:
            return self._validation_rules.get(extension_type, []).copy()
            
    async def register_security_policy(self, policy_name: str, policy: Dict[str, Any]) -> None:
        """Register a security policy."""
        async with self._lock:
            self._security_policies[policy_name] = policy
            
        self.logger.info(f"Registered security policy: {policy_name}")
        
    async def get_security_policy(self, policy_name: str) -> Dict[str, Any]:
        """Get a security policy."""
        async with self._lock:
            if policy_name not in self._security_policies:
                raise ValueError(f"Security policy '{policy_name}' not found")
                
            return self._security_policies[policy_name].copy()
            
    async def validate_configuration(self, extension_id: str, config: Dict[str, Any], 
                                   schema_name: str = "extension_manifest", 
                                   extension_type: Optional[str] = None,
                                   security_policy: Optional[str] = None) -> Dict[str, Any]:
        """Validate an extension configuration."""
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Validate schema
        try:
            schema = await self.get_schema(schema_name)
            schema_errors = self._validate_schema(config, schema)
            if schema_errors:
                result["valid"] = False
                result["errors"].extend(schema_errors)
        except ValueError as e:
            result["valid"] = False
            result["errors"].append(str(e))
            
        # Validate rules
        if extension_type:
            try:
                rules = await self.get_validation_rules(extension_type)
                for rule in rules:
                    try:
                        if not rule["check"](config):
                            result["warnings"].append(rule.get("description", "Validation rule failed"))
                    except Exception as e:
                        result["errors"].append(f"Error in validation rule '{rule.get('name', 'unknown')}': {str(e)}")
                        result["valid"] = False
            except ValueError as e:
                result["warnings"].append(str(e))
                
        # Validate security policy
        if security_policy:
            try:
                policy = await self.get_security_policy(security_policy)
                security_errors = self._validate_security(config, policy)
                if security_errors:
                    result["valid"] = False
                    result["errors"].extend(security_errors)
            except ValueError as e:
                result["errors"].append(str(e))
                result["valid"] = False
                
        # Store validation result
        async with self._lock:
            self._validation_results[extension_id] = result
            
        self.logger.info(f"Validated configuration for extension {extension_id}: {'valid' if result['valid'] else 'invalid'}")
        return result
        
    async def get_validation_result(self, extension_id: str) -> Dict[str, Any]:
        """Get the validation result for an extension."""
        async with self._lock:
            if extension_id not in self._validation_results:
                raise ValueError(f"Validation result for extension '{extension_id}' not found")
                
            return self._validation_results[extension_id].copy()
            
    def _validate_schema(self, config: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate a configuration against a schema."""
        errors = []
        
        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in config:
                errors.append(f"Required field '{field}' is missing")
                
        # Check field types and patterns
        properties = schema.get("properties", {})
        for field, value in config.items():
            if field in properties:
                field_schema = properties[field]
                
                # Check type
                expected_type = field_schema.get("type")
                if expected_type and not self._check_type(value, expected_type):
                    errors.append(f"Field '{field}' has incorrect type. Expected {expected_type}, got {type(value).__name__}")
                    
                # Check pattern
                pattern = field_schema.get("pattern")
                if pattern and isinstance(value, str) and not re.match(pattern, value):
                    errors.append(f"Field '{field}' does not match required pattern")
                    
                # Check min/max length
                if isinstance(value, str):
                    min_length = field_schema.get("minLength")
                    max_length = field_schema.get("maxLength")
                    
                    if min_length and len(value) < min_length:
                        errors.append(f"Field '{field}' is too short. Minimum length: {min_length}")
                        
                    if max_length and len(value) > max_length:
                        errors.append(f"Field '{field}' is too long. Maximum length: {max_length}")
                        
                # Check array items
                if isinstance(value, list) and "items" in field_schema:
                    item_schema = field_schema["items"]
                    for i, item in enumerate(value):
                        if not self._check_type(item, item_schema.get("type")):
                            errors.append(f"Item {i} in field '{field}' has incorrect type. Expected {item_schema.get('type')}, got {type(item).__name__}")
                            
                # Check object properties
                if isinstance(value, dict) and "properties" in field_schema:
                    nested_errors = self._validate_schema(value, field_schema)
                    errors.extend([f"In field '{field}': {error}" for error in nested_errors])
                    
        return errors
        
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if a value matches an expected type."""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        if expected_type not in type_mapping:
            return False
            
        expected_python_type = type_mapping[expected_type]
        return isinstance(value, expected_python_type)
        
    def _validate_security(self, config: Dict[str, Any], policy: Dict[str, Any]) -> List[str]:
        """Validate a configuration against a security policy."""
        errors = []
        
        # Check permissions
        allowed_permissions = set(policy.get("allowed_permissions", []))
        restricted_permissions = set(policy.get("restricted_permissions", []))
        
        for permission in config.get("permissions", []):
            if permission in restricted_permissions:
                errors.append(f"Permission '{permission}' is restricted by security policy")
            elif permission not in allowed_permissions:
                errors.append(f"Permission '{permission}' is not allowed by security policy")
                
        # Check resources
        max_resources = policy.get("max_resources", {})
        resources = config.get("resources", {})
        
        for resource, max_value in max_resources.items():
            if resource in resources:
                # Simple string comparison for resource limits
                # In a real implementation, this would parse and compare numeric values
                if resources[resource] > max_value:
                    errors.append(f"Resource limit exceeded for '{resource}'. Maximum: {max_value}")
                    
        # Check dependencies
        allowed_dependencies = set(policy.get("allowed_dependencies", []))
        restricted_dependencies = set(policy.get("restricted_dependencies", []))
        
        for dependency in config.get("dependencies", []):
            if dependency in restricted_dependencies:
                errors.append(f"Dependency '{dependency}' is restricted by security policy")
            elif dependency not in allowed_dependencies:
                errors.append(f"Dependency '{dependency}' is not allowed by security policy")
                
        return errors
        
    async def health_check(self) -> ServiceHealth:
        """Perform a health check of the service."""
        status = ServiceStatus.RUNNING if self._initialized else ServiceStatus.INITIALIZING
        
        return ServiceHealth(
            status=status,
            last_check=datetime.now(),
            details={
                "validation_schemas": len(self._validation_schemas),
                "validation_rules": len(self._validation_rules),
                "security_policies": len(self._security_policies),
                "validation_results": len(self._validation_results)
            }
        )
        
    async def shutdown(self) -> None:
        """Shutdown the service."""
        self.logger.info("Shutting down Extension Configuration Validator service")
        
        self._validation_schemas.clear()
        self._validation_rules.clear()
        self._security_policies.clear()
        self._validation_results.clear()
        
        self._initialized = False
        self._status = ServiceStatus.SHUTDOWN
        self.logger.info("Extension Configuration Validator service shutdown complete")