"""
Extension manifest validation and schema checking.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from ai_karen_engine.extensions.models import ExtensionManifest


class ValidationError(Exception):
    """Extension validation error."""
    pass


class ExtensionValidator:
    """
    Validates extension manifests and ensures they meet requirements.
    """
    
    # Semantic version regex pattern
    SEMVER_PATTERN = re.compile(
        r'^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)'
        r'(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
        r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
        r'(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
    )
    
    # Valid extension name pattern (kebab-case)
    NAME_PATTERN = re.compile(r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$')
    
    # Valid categories
    VALID_CATEGORIES = {
        'analytics', 'automation', 'communication', 'data', 'development',
        'finance', 'integration', 'iot', 'marketing', 'productivity',
        'security', 'social', 'utilities', 'example', 'test'
    }
    
    # Valid permissions
    VALID_DATA_PERMISSIONS = {'read', 'write', 'delete', 'admin'}
    VALID_PLUGIN_PERMISSIONS = {'execute', 'manage'}
    VALID_SYSTEM_PERMISSIONS = {'metrics', 'logs', 'config', 'admin'}
    VALID_NETWORK_PERMISSIONS = {'outbound_http', 'outbound_https', 'inbound', 'webhook'}
    
    def __init__(self):
        """Initialize the validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_manifest(self, manifest: ExtensionManifest) -> Tuple[bool, List[str], List[str]]:
        """
        Validate an extension manifest.
        
        Args:
            manifest: Extension manifest to validate
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Basic field validation
        self._validate_basic_fields(manifest)
        
        # Version validation
        self._validate_version(manifest.version)
        self._validate_version(manifest.kari_min_version)
        
        # Name validation
        self._validate_name(manifest.name)
        
        # Category validation
        self._validate_category(manifest.category)
        
        # Dependencies validation
        self._validate_dependencies(manifest)
        
        # Permissions validation
        self._validate_permissions(manifest)
        
        # Resources validation
        self._validate_resources(manifest)
        
        # UI configuration validation
        self._validate_ui_config(manifest)
        
        # API configuration validation
        self._validate_api_config(manifest)
        
        # Background tasks validation
        self._validate_background_tasks(manifest)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors.copy(), self.warnings.copy()
    
    def _validate_basic_fields(self, manifest: ExtensionManifest) -> None:
        """Validate basic required fields."""
        required_fields = [
            ('name', manifest.name),
            ('version', manifest.version),
            ('display_name', manifest.display_name),
            ('description', manifest.description),
            ('author', manifest.author),
            ('license', manifest.license),
            ('category', manifest.category)
        ]
        
        for field_name, field_value in required_fields:
            if not field_value or not isinstance(field_value, str) or not field_value.strip():
                self.errors.append(f"Required field '{field_name}' is missing or empty")
    
    def _validate_version(self, version: str) -> None:
        """Validate semantic version format."""
        if not version:
            return  # Will be caught by basic field validation
        
        if not self.SEMVER_PATTERN.match(version):
            self.errors.append(f"Invalid semantic version format: {version}")
    
    def _validate_name(self, name: str) -> None:
        """Validate extension name format."""
        if not name:
            return  # Will be caught by basic field validation
        
        if not self.NAME_PATTERN.match(name):
            self.errors.append(
                f"Extension name '{name}' must be lowercase kebab-case (e.g., 'my-extension')"
            )
        
        if len(name) > 50:
            self.errors.append(f"Extension name '{name}' is too long (max 50 characters)")
    
    def _validate_category(self, category: str) -> None:
        """Validate extension category."""
        if not category:
            return  # Will be caught by basic field validation
        
        if category not in self.VALID_CATEGORIES:
            self.warnings.append(
                f"Category '{category}' is not in recommended categories: "
                f"{', '.join(sorted(self.VALID_CATEGORIES))}"
            )
    
    def _validate_dependencies(self, manifest: ExtensionManifest) -> None:
        """Validate extension dependencies."""
        # Validate plugin dependencies
        for plugin in manifest.dependencies.plugins:
            if not isinstance(plugin, str) or not plugin.strip():
                self.errors.append(f"Invalid plugin dependency: {plugin}")
        
        # Validate extension dependencies
        for ext_dep in manifest.dependencies.extensions:
            if not isinstance(ext_dep, str) or not ext_dep.strip():
                self.errors.append(f"Invalid extension dependency: {ext_dep}")
                continue
            
            # Check version specification format
            if '@' in ext_dep:
                ext_name, version_spec = ext_dep.split('@', 1)
                if not self.NAME_PATTERN.match(ext_name):
                    self.errors.append(f"Invalid extension name in dependency: {ext_name}")
                
                # Basic version spec validation (could be enhanced)
                if not version_spec or version_spec.startswith('^') and len(version_spec) < 2:
                    self.errors.append(f"Invalid version specification: {version_spec}")
        
        # Validate system service dependencies
        valid_services = {'postgres', 'redis', 'elasticsearch', 'milvus'}
        for service in manifest.dependencies.system_services:
            if service not in valid_services:
                self.warnings.append(f"Unknown system service dependency: {service}")
    
    def _validate_permissions(self, manifest: ExtensionManifest) -> None:
        """Validate extension permissions."""
        # Data access permissions
        for perm in manifest.permissions.data_access:
            if perm not in self.VALID_DATA_PERMISSIONS:
                self.errors.append(f"Invalid data access permission: {perm}")
        
        # Plugin access permissions
        for perm in manifest.permissions.plugin_access:
            if perm not in self.VALID_PLUGIN_PERMISSIONS:
                self.errors.append(f"Invalid plugin access permission: {perm}")
        
        # System access permissions
        for perm in manifest.permissions.system_access:
            if perm not in self.VALID_SYSTEM_PERMISSIONS:
                self.errors.append(f"Invalid system access permission: {perm}")
        
        # Network access permissions
        for perm in manifest.permissions.network_access:
            if perm not in self.VALID_NETWORK_PERMISSIONS:
                self.errors.append(f"Invalid network access permission: {perm}")
    
    def _validate_resources(self, manifest: ExtensionManifest) -> None:
        """Validate resource limits."""
        resources = manifest.resources
        
        # Memory limits
        if resources.max_memory_mb <= 0:
            self.errors.append("Memory limit must be positive")
        elif resources.max_memory_mb > 4096:  # 4GB limit
            self.warnings.append(f"Memory limit {resources.max_memory_mb}MB is very high")
        
        # CPU limits
        if resources.max_cpu_percent <= 0 or resources.max_cpu_percent > 100:
            self.errors.append("CPU limit must be between 1 and 100 percent")
        elif resources.max_cpu_percent > 50:
            self.warnings.append(f"CPU limit {resources.max_cpu_percent}% is very high")
        
        # Disk limits
        if resources.max_disk_mb <= 0:
            self.errors.append("Disk limit must be positive")
        elif resources.max_disk_mb > 10240:  # 10GB limit
            self.warnings.append(f"Disk limit {resources.max_disk_mb}MB is very high")
    
    def _validate_ui_config(self, manifest: ExtensionManifest) -> None:
        """Validate UI configuration."""
        # Control Room pages
        for page in manifest.ui.control_room_pages:
            if not isinstance(page, dict):
                self.errors.append("Control Room page configuration must be a dictionary")
                continue
            
            required_page_fields = ['name', 'path']
            for field in required_page_fields:
                if field not in page or not page[field]:
                    self.errors.append(f"Control Room page missing required field: {field}")
            
            # Validate path format
            if 'path' in page and page['path']:
                path = page['path']
                if not path.startswith('/'):
                    self.errors.append(f"Control Room page path must start with '/': {path}")
        
        # Streamlit pages
        for page in manifest.ui.streamlit_pages:
            if not isinstance(page, dict):
                self.errors.append("Streamlit page configuration must be a dictionary")
                continue
            
            required_page_fields = ['name', 'module']
            for field in required_page_fields:
                if field not in page or not page[field]:
                    self.errors.append(f"Streamlit page missing required field: {field}")
    
    def _validate_api_config(self, manifest: ExtensionManifest) -> None:
        """Validate API configuration."""
        for endpoint in manifest.api.endpoints:
            if not isinstance(endpoint, dict):
                self.errors.append("API endpoint configuration must be a dictionary")
                continue
            
            # Required fields
            required_fields = ['path', 'methods']
            for field in required_fields:
                if field not in endpoint or not endpoint[field]:
                    self.errors.append(f"API endpoint missing required field: {field}")
            
            # Validate path
            if 'path' in endpoint and endpoint['path']:
                path = endpoint['path']
                if not path.startswith('/'):
                    self.errors.append(f"API endpoint path must start with '/': {path}")
            
            # Validate methods
            if 'methods' in endpoint and endpoint['methods']:
                valid_methods = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}
                methods = endpoint['methods']
                if isinstance(methods, list):
                    for method in methods:
                        if method not in valid_methods:
                            self.errors.append(f"Invalid HTTP method: {method}")
                else:
                    self.errors.append("API endpoint methods must be a list")
    
    def _validate_background_tasks(self, manifest: ExtensionManifest) -> None:
        """Validate background task configuration."""
        for task in manifest.background_tasks:
            # Validate cron schedule format (basic validation)
            schedule = task.schedule
            if schedule:
                # Basic cron validation - should have 5 parts
                parts = schedule.split()
                if len(parts) != 5:
                    self.errors.append(f"Invalid cron schedule format: {schedule}")
            
            # Validate function reference
            function = task.function
            if function and '.' not in function:
                self.warnings.append(f"Background task function should include module path: {function}")


def validate_extension_manifest(manifest: ExtensionManifest) -> Tuple[bool, List[str], List[str]]:
    """
    Convenience function to validate an extension manifest.
    
    Args:
        manifest: Extension manifest to validate
        
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    validator = ExtensionValidator()
    return validator.validate_manifest(manifest)


__all__ = ["ExtensionValidator", "ValidationError", "validate_extension_manifest"]
