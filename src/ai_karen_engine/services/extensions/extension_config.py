"""
Extension Config Service

This service provides configuration management capabilities for extensions,
including settings, permissions, and environment variables.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import logging
import uuid
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path

from .extension_registry import Extension, ExtensionConfig

logger = logging.getLogger(__name__)


class ConfigScope(Enum):
    """Enumeration of configuration scopes."""
    GLOBAL = "global"
    EXTENSION = "extension"
    USER = "user"
    SESSION = "session"


class ConfigType(Enum):
    """Enumeration of configuration types."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


class ConfigPermission(Enum):
    """Enumeration of configuration permissions."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


@dataclass
class ConfigSchema:
    """Schema for a configuration setting."""
    key: str
    type: ConfigType
    default: Any
    required: bool = False
    description: str = ""
    options: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    permissions: List[ConfigPermission] = field(default_factory=lambda: [ConfigPermission.READ])


@dataclass
class ConfigValue:
    """A configuration value."""
    key: str
    value: Any
    scope: ConfigScope
    extension_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigChange:
    """A change to a configuration value."""
    id: str
    key: str
    old_value: Any
    new_value: Any
    scope: ConfigScope
    extension_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExtensionConfigManager:
    """
    Provides configuration management capabilities for extensions.
    
    This class is responsible for:
    - Managing configuration schemas
    - Storing and retrieving configuration values
    - Handling configuration changes
    - Validating configuration values
    - Managing configuration permissions
    """
    
    def __init__(self, config_dir: str = "config"):
        self._config_dir = Path(config_dir)
        self._schemas: Dict[str, ConfigSchema] = {}
        self._values: Dict[str, List[ConfigValue]] = {}
        self._changes: List[ConfigChange] = []
        self._scope_index: Dict[ConfigScope, Set[str]] = {s: set() for s in ConfigScope}
        self._extension_index: Dict[str, Set[str]] = {}
        self._user_index: Dict[str, Set[str]] = {}
        self._session_index: Dict[str, Set[str]] = {}
        
        # Callbacks for config events
        self._on_config_changed: Optional[Callable[[ConfigChange], None]] = None
        self._on_config_validated: Optional[Callable[[str, Any, bool], None]] = None
        self._on_config_loaded: Optional[Callable[[str, Any], None]] = None
    
    def initialize(self) -> None:
        """Initialize the extension config manager."""
        # Create config directory if it doesn't exist
        self._config_dir.mkdir(exist_ok=True)
        
        # Load configurations
        self._load_configurations()
        
        logger.info(f"Initialized extension config manager with {len(self._schemas)} schemas")
    
    def register_schema(self, schema: ConfigSchema) -> str:
        """
        Register a configuration schema.
        
        Args:
            schema: Configuration schema
            
        Returns:
            Key of the schema
        """
        # Check if schema already exists
        if schema.key in self._schemas:
            logger.warning(f"Schema already exists: {schema.key}")
            return schema.key
        
        # Add schema
        self._schemas[schema.key] = schema
        
        # Save schema
        self._save_schema(schema)
        
        logger.info(f"Registered configuration schema: {schema.key}")
        return schema.key
    
    def get_schema(self, key: str) -> Optional[ConfigSchema]:
        """Get a configuration schema by key."""
        return self._schemas.get(key)
    
    def get_schemas(self, extension_id: Optional[str] = None) -> List[ConfigSchema]:
        """
        Get configuration schemas, optionally filtered by extension ID.
        
        Args:
            extension_id: ID of extension
            
        Returns:
            List of configuration schemas
        """
        schemas = list(self._schemas.values())
        
        # Filter by extension ID
        if extension_id:
            schemas = [s for s in schemas if s.key.startswith(f"{extension_id}.")]
        
        return schemas
    
    def unregister_schema(self, key: str) -> bool:
        """
        Unregister a configuration schema.
        
        Args:
            key: Key of the schema
            
        Returns:
            True if schema was unregistered, False if not found
        """
        if key not in self._schemas:
            logger.warning(f"Schema not found: {key}")
            return False
        
        # Remove schema
        del self._schemas[key]
        
        # Remove schema file
        schema_file = self._config_dir / f"{key}.json"
        if schema_file.exists():
            schema_file.unlink()
        
        logger.info(f"Unregistered configuration schema: {key}")
        return True
    
    def set_config_value(
        self,
        key: str,
        value: Any,
        scope: ConfigScope = ConfigScope.GLOBAL,
        extension_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Key of the configuration
            value: Value of the configuration
            scope: Scope of the configuration
            extension_id: ID of the extension
            user_id: ID of the user
            session_id: ID of the session
            metadata: Metadata for the configuration
            
        Returns:
            True if value was set, False otherwise
        """
        # Get schema
        schema = self._schemas.get(key)
        if not schema:
            logger.error(f"Schema not found: {key}")
            return False
        
        # Validate value
        validation_result = self._validate_value(schema, value)
        if not validation_result["valid"]:
            logger.error(f"Invalid value for {key}: {validation_result['error']}")
            
            # Call config validated callback if set
            if self._on_config_validated:
                self._on_config_validated(key, value, False)
            
            return False
        
        # Get old value
        old_value = self.get_config_value(key, scope, extension_id, user_id, session_id)
        
        # Create config value
        config_value = ConfigValue(
            key=key,
            value=value,
            scope=scope,
            extension_id=extension_id,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        # Store value
        if key not in self._values:
            self._values[key] = []
        
        # Remove existing values with same scope and identifiers
        self._values[key] = [
            v for v in self._values[key]
            if not (
                v.scope == scope and
                v.extension_id == extension_id and
                v.user_id == user_id and
                v.session_id == session_id
            )
        ]
        
        # Add new value
        self._values[key].append(config_value)
        
        # Update indexes
        self._scope_index[scope].add(key)
        if extension_id:
            if extension_id not in self._extension_index:
                self._extension_index[extension_id] = set()
            self._extension_index[extension_id].add(key)
        if user_id:
            if user_id not in self._user_index:
                self._user_index[user_id] = set()
            self._user_index[user_id].add(key)
        if session_id:
            if session_id not in self._session_index:
                self._session_index[session_id] = set()
            self._session_index[session_id].add(key)
        
        # Save configuration
        self._save_configuration(key)
        
        # Record change
        if old_value != value:
            change = ConfigChange(
                id=str(uuid.uuid4()),
                key=key,
                old_value=old_value,
                new_value=value,
                scope=scope,
                extension_id=extension_id,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {}
            )
            
            self._changes.append(change)
            
            # Call config changed callback if set
            if self._on_config_changed:
                self._on_config_changed(change)
        
        # Call config validated callback if set
        if self._on_config_validated:
            self._on_config_validated(key, value, True)
        
        logger.info(f"Set configuration value: {key} = {value}")
        return True
    
    def get_config_value(
        self,
        key: str,
        scope: Optional[ConfigScope] = None,
        extension_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Key of the configuration
            scope: Scope of the configuration
            extension_id: ID of the extension
            user_id: ID of the user
            session_id: ID of the session
            
        Returns:
            Configuration value or default value
        """
        # Get schema
        schema = self._schemas.get(key)
        if not schema:
            logger.error(f"Schema not found: {key}")
            return None
        
        # Get values for key
        values = self._values.get(key, [])
        
        # Filter by scope and identifiers
        filtered_values = []
        
        for value in values:
            # Check scope
            if scope and value.scope != scope:
                continue
            
            # Check extension ID
            if extension_id and value.extension_id != extension_id:
                continue
            
            # Check user ID
            if user_id and value.user_id != user_id:
                continue
            
            # Check session ID
            if session_id and value.session_id != session_id:
                continue
            
            filtered_values.append(value)
        
        # Sort by scope priority (session > user > extension > global)
        scope_priority = {
            ConfigScope.SESSION: 4,
            ConfigScope.USER: 3,
            ConfigScope.EXTENSION: 2,
            ConfigScope.GLOBAL: 1
        }
        
        filtered_values.sort(key=lambda v: scope_priority[v.scope], reverse=True)
        
        # Return first value or default
        if filtered_values:
            # Call config loaded callback if set
            if self._on_config_loaded:
                self._on_config_loaded(key, filtered_values[0].value)
            
            return filtered_values[0].value
        else:
            # Call config loaded callback if set
            if self._on_config_loaded:
                self._on_config_loaded(key, schema.default)
            
            return schema.default
    
    def get_config_values(
        self,
        extension_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all configuration values for a given context.
        
        Args:
            extension_id: ID of the extension
            user_id: ID of the user
            session_id: ID of the session
            
        Returns:
            Dictionary of configuration values
        """
        values = {}
        
        for key in self._schemas:
            values[key] = self.get_config_value(
                key,
                extension_id=extension_id,
                user_id=user_id,
                session_id=session_id
            )
        
        return values
    
    def delete_config_value(
        self,
        key: str,
        scope: ConfigScope,
        extension_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Delete a configuration value.
        
        Args:
            key: Key of the configuration
            scope: Scope of the configuration
            extension_id: ID of the extension
            user_id: ID of the user
            session_id: ID of the session
            
        Returns:
            True if value was deleted, False otherwise
        """
        # Get values for key
        if key not in self._values:
            logger.warning(f"No values found for key: {key}")
            return False
        
        # Get old value
        old_value = self.get_config_value(key, scope, extension_id, user_id, session_id)
        
        # Remove values with matching scope and identifiers
        original_count = len(self._values[key])
        self._values[key] = [
            v for v in self._values[key]
            if not (
                v.scope == scope and
                v.extension_id == extension_id and
                v.user_id == user_id and
                v.session_id == session_id
            )
        ]
        
        # Check if any values were removed
        if len(self._values[key]) == original_count:
            logger.warning(f"No matching values found for key: {key}")
            return False
        
        # Save configuration
        self._save_configuration(key)
        
        # Record change
        change = ConfigChange(
            id=str(uuid.uuid4()),
            key=key,
            old_value=old_value,
            new_value=None,
            scope=scope,
            extension_id=extension_id,
            user_id=user_id,
            session_id=session_id
        )
        
        self._changes.append(change)
        
        # Call config changed callback if set
        if self._on_config_changed:
            self._on_config_changed(change)
        
        logger.info(f"Deleted configuration value: {key}")
        return True
    
    def get_changes(
        self,
        key: Optional[str] = None,
        extension_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ConfigChange]:
        """
        Get configuration changes.
        
        Args:
            key: Key of the configuration
            extension_id: ID of the extension
            user_id: ID of the user
            session_id: ID of the session
            limit: Maximum number of changes to return
            
        Returns:
            List of configuration changes
        """
        changes = self._changes
        
        # Filter by key
        if key:
            changes = [c for c in changes if c.key == key]
        
        # Filter by extension ID
        if extension_id:
            changes = [c for c in changes if c.extension_id == extension_id]
        
        # Filter by user ID
        if user_id:
            changes = [c for c in changes if c.user_id == user_id]
        
        # Filter by session ID
        if session_id:
            changes = [c for c in changes if c.session_id == session_id]
        
        # Sort by timestamp (newest first)
        changes.sort(key=lambda c: c.timestamp, reverse=True)
        
        # Apply limit
        return changes[:limit]
    
    def set_config_callbacks(
        self,
        on_config_changed: Optional[Callable[[ConfigChange], None]] = None,
        on_config_validated: Optional[Callable[[str, Any, bool], None]] = None,
        on_config_loaded: Optional[Callable[[str, Any], None]] = None
    ) -> None:
        """Set callbacks for configuration events."""
        self._on_config_changed = on_config_changed
        self._on_config_validated = on_config_validated
        self._on_config_loaded = on_config_loaded
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about configuration.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_schemas": len(self._schemas),
            "total_values": sum(len(values) for values in self._values.values()),
            "total_changes": len(self._changes),
            "schemas_by_type": {},
            "values_by_scope": {},
            "values_by_extension": {},
            "values_by_user": {},
            "values_by_session": {},
            "changes_by_scope": {}
        }
        
        # Count schemas by type
        for schema in self._schemas.values():
            config_type = schema.type.value
            if config_type not in stats["schemas_by_type"]:
                stats["schemas_by_type"][config_type] = 0
            stats["schemas_by_type"][config_type] += 1
        
        # Count values by scope
        for scope, keys in self._scope_index.items():
            stats["values_by_scope"][scope.value] = len(keys)
        
        # Count values by extension
        for extension_id, keys in self._extension_index.items():
            stats["values_by_extension"][extension_id] = len(keys)
        
        # Count values by user
        for user_id, keys in self._user_index.items():
            stats["values_by_user"][user_id] = len(keys)
        
        # Count values by session
        for session_id, keys in self._session_index.items():
            stats["values_by_session"][session_id] = len(keys)
        
        # Count changes by scope
        for change in self._changes:
            scope = change.scope.value
            if scope not in stats["changes_by_scope"]:
                stats["changes_by_scope"][scope] = 0
            stats["changes_by_scope"][scope] += 1
        
        return stats
    
    def _load_configurations(self) -> None:
        """Load configurations from disk."""
        # Load schemas
        for schema_file in self._config_dir.glob("*.schema.json"):
            try:
                with open(schema_file, "r") as f:
                    schema_data = json.load(f)
                
                schema = ConfigSchema(
                    key=schema_data["key"],
                    type=ConfigType(schema_data["type"]),
                    default=schema_data["default"],
                    required=schema_data.get("required", False),
                    description=schema_data.get("description", ""),
                    options=schema_data.get("options"),
                    min_value=schema_data.get("min_value"),
                    max_value=schema_data.get("max_value"),
                    pattern=schema_data.get("pattern"),
                    permissions=[ConfigPermission(p) for p in schema_data.get("permissions", ["read"])]
                )
                
                self._schemas[schema.key] = schema
                
                logger.debug(f"Loaded configuration schema: {schema.key}")
                
            except Exception as e:
                logger.error(f"Failed to load schema from {schema_file}: {str(e)}")
        
        # Load values
        for config_file in self._config_dir.glob("*.config.json"):
            try:
                with open(config_file, "r") as f:
                    config_data = json.load(f)
                
                key = config_file.stem
                
                if key not in self._values:
                    self._values[key] = []
                
                for value_data in config_data.get("values", []):
                    config_value = ConfigValue(
                        key=key,
                        value=value_data["value"],
                        scope=ConfigScope(value_data["scope"]),
                        extension_id=value_data.get("extension_id"),
                        user_id=value_data.get("user_id"),
                        session_id=value_data.get("session_id"),
                        timestamp=datetime.fromisoformat(value_data["timestamp"]),
                        metadata=value_data.get("metadata", {})
                    )
                    
                    self._values[key].append(config_value)
                    
                    # Update indexes
                    self._scope_index[config_value.scope].add(key)
                    if config_value.extension_id:
                        if config_value.extension_id not in self._extension_index:
                            self._extension_index[config_value.extension_id] = set()
                        self._extension_index[config_value.extension_id].add(key)
                    if config_value.user_id:
                        if config_value.user_id not in self._user_index:
                            self._user_index[config_value.user_id] = set()
                        self._user_index[config_value.user_id].add(key)
                    if config_value.session_id:
                        if config_value.session_id not in self._session_index:
                            self._session_index[config_value.session_id] = set()
                        self._session_index[config_value.session_id].add(key)
                
                logger.debug(f"Loaded configuration values: {key}")
                
            except Exception as e:
                logger.error(f"Failed to load config from {config_file}: {str(e)}")
    
    def _save_schema(self, schema: ConfigSchema) -> None:
        """Save a schema to disk."""
        schema_file = self._config_dir / f"{schema.key}.schema.json"
        
        schema_data = {
            "key": schema.key,
            "type": schema.type.value,
            "default": schema.default,
            "required": schema.required,
            "description": schema.description,
            "options": schema.options,
            "min_value": schema.min_value,
            "max_value": schema.max_value,
            "pattern": schema.pattern,
            "permissions": [p.value for p in schema.permissions]
        }
        
        with open(schema_file, "w") as f:
            json.dump(schema_data, f, indent=2)
    
    def _save_configuration(self, key: str) -> None:
        """Save configuration values to disk."""
        config_file = self._config_dir / f"{key}.config.json"
        
        config_data = {
            "key": key,
            "values": [
                {
                    "value": v.value,
                    "scope": v.scope.value,
                    "extension_id": v.extension_id,
                    "user_id": v.user_id,
                    "session_id": v.session_id,
                    "timestamp": v.timestamp.isoformat(),
                    "metadata": v.metadata
                }
                for v in self._values.get(key, [])
            ]
        }
        
        with open(config_file, "w") as f:
            json.dump(config_data, f, indent=2)
    
    def _validate_value(self, schema: ConfigSchema, value: Any) -> Dict[str, Any]:
        """Validate a value against a schema."""
        result = {
            "valid": True,
            "error": None
        }
        
        # Check type
        if schema.type == ConfigType.STRING:
            if not isinstance(value, str):
                result["valid"] = False
                result["error"] = f"Expected string, got {type(value).__name__}"
                return result
        
        elif schema.type == ConfigType.NUMBER:
            if not isinstance(value, (int, float)):
                result["valid"] = False
                result["error"] = f"Expected number, got {type(value).__name__}"
                return result
            
            # Check min/max
            if schema.min_value is not None and value < schema.min_value:
                result["valid"] = False
                result["error"] = f"Value {value} is less than minimum {schema.min_value}"
                return result
            
            if schema.max_value is not None and value > schema.max_value:
                result["valid"] = False
                result["error"] = f"Value {value} is greater than maximum {schema.max_value}"
                return result
        
        elif schema.type == ConfigType.BOOLEAN:
            if not isinstance(value, bool):
                result["valid"] = False
                result["error"] = f"Expected boolean, got {type(value).__name__}"
                return result
        
        elif schema.type == ConfigType.OBJECT:
            if not isinstance(value, dict):
                result["valid"] = False
                result["error"] = f"Expected object, got {type(value).__name__}"
                return result
        
        elif schema.type == ConfigType.ARRAY:
            if not isinstance(value, list):
                result["valid"] = False
                result["error"] = f"Expected array, got {type(value).__name__}"
                return result
        
        # Check options
        if schema.options is not None and value not in schema.options:
            result["valid"] = False
            result["error"] = f"Value {value} is not in allowed options: {schema.options}"
            return result
        
        # Check pattern
        if schema.pattern is not None and isinstance(value, str):
            import re
            if not re.match(schema.pattern, value):
                result["valid"] = False
                result["error"] = f"Value {value} does not match pattern: {schema.pattern}"
                return result
        
        return result