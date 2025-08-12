"""
Extension manifest validation and schema checking.
Enhanced with unified validation patterns from Phase 4.1.a.
"""

from __future__ import annotations

from typing import List, Tuple, Dict, Any, Optional, Union
from datetime import datetime
import re

from pydantic import ValidationError as PydanticValidationError

from ai_karen_engine.extensions.models import ExtensionManifest, NAME_PATTERN

# Import unified validation utilities
try:
    from ai_karen_engine.api_routes.unified_schemas import (
        ValidationUtils,
        FieldError
    )
    UNIFIED_VALIDATION_AVAILABLE = True
except ImportError:
    UNIFIED_VALIDATION_AVAILABLE = False


class ValidationError(Exception):
    """Extension validation error."""
    pass


class ExtensionValidator:
    """
    Validates extension manifests and ensures they meet requirements.
    """
    
    # Valid permissions
    VALID_DATA_PERMISSIONS = {'read', 'write', 'delete', 'admin'}
    VALID_PLUGIN_PERMISSIONS = {'execute', 'manage'}
    VALID_SYSTEM_PERMISSIONS = {'metrics', 'logs', 'config', 'admin'}
    VALID_NETWORK_PERMISSIONS = {'outbound_http', 'outbound_https', 'inbound', 'webhook'}
    
    def __init__(self):
        """Initialize the validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.field_errors: List[FieldError] = []
    
    def validate_manifest(self, manifest: Union[ExtensionManifest, Dict[str, Any]]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate an extension manifest.
        
        Args:
            manifest: Extension manifest to validate
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        self.field_errors = []

        try:
            manifest_model = (
                manifest
                if isinstance(manifest, ExtensionManifest)
                else ExtensionManifest(**manifest)
            )
        except PydanticValidationError as e:
            for err in e.errors():
                field_path = ".".join(str(p) for p in err["loc"])
                message = err["msg"]
                self.errors.append(f"{field_path}: {message}")
                if UNIFIED_VALIDATION_AVAILABLE:
                    self.field_errors.append(
                        FieldError(
                            field=field_path,
                            message=message,
                            code="invalid",
                            invalid_value=err.get("input"),
                        )
                    )
            return False, self.errors.copy(), self.warnings.copy()

        manifest = manifest_model
        
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
    
    # The basic field, version, name, and category validations are now handled
    # by the Pydantic ``ExtensionManifest`` model. The methods are kept for
    # backward compatibility but perform no actions.

    def _validate_basic_fields(self, manifest: ExtensionManifest) -> None:
        return

    def _validate_version(self, version: str) -> None:
        return

    def _validate_name(self, name: str) -> None:
        return

    def _validate_category(self, category: str) -> None:
        return
    
    def _validate_dependencies(self, manifest: ExtensionManifest) -> None:
        """Validate extension dependencies."""
        deps = manifest.dependencies or {}
        plugins = (deps.get("plugins") if isinstance(deps, dict) else deps.plugins) or []
        extensions = (deps.get("extensions") if isinstance(deps, dict) else deps.extensions) or []
        system_services = (deps.get("system_services") if isinstance(deps, dict) else deps.system_services) or []

        # Validate plugin dependencies
        for plugin in plugins:
            if not isinstance(plugin, str) or not plugin.strip():
                self.errors.append(f"Invalid plugin dependency: {plugin}")

        # Validate extension dependencies
        for ext_dep in extensions:
            if not isinstance(ext_dep, str) or not ext_dep.strip():
                self.errors.append(f"Invalid extension dependency: {ext_dep}")
                continue
            
            # Check version specification format
            if '@' in ext_dep:
                ext_name, version_spec = ext_dep.split('@', 1)
                if not re.match(NAME_PATTERN, ext_name):
                    self.errors.append(f"Invalid extension name in dependency: {ext_name}")
                
                # Basic version spec validation (could be enhanced)
                if not version_spec or version_spec.startswith('^') and len(version_spec) < 2:
                    self.errors.append(f"Invalid version specification: {version_spec}")
        
        # Validate system service dependencies
        valid_services = {'postgres', 'redis', 'elasticsearch', 'milvus'}
        for service in system_services:
            if service not in valid_services:
                self.warnings.append(f"Unknown system service dependency: {service}")
    
    def _validate_permissions(self, manifest: ExtensionManifest) -> None:
        """Validate extension permissions."""
        perms = manifest.permissions or {}
        data_access = perms.get("data_access") if isinstance(perms, dict) else perms.data_access
        plugin_access = perms.get("plugin_access") if isinstance(perms, dict) else perms.plugin_access
        system_access = perms.get("system_access") if isinstance(perms, dict) else perms.system_access
        network_access = perms.get("network_access") if isinstance(perms, dict) else perms.network_access

        for perm in data_access or []:
            if perm not in self.VALID_DATA_PERMISSIONS:
                self.errors.append(f"Invalid data access permission: {perm}")

        for perm in plugin_access or []:
            if perm not in self.VALID_PLUGIN_PERMISSIONS:
                self.errors.append(f"Invalid plugin access permission: {perm}")

        for perm in system_access or []:
            if perm not in self.VALID_SYSTEM_PERMISSIONS:
                self.errors.append(f"Invalid system access permission: {perm}")

        for perm in network_access or []:
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

    def _validate_with_unified_patterns(self, manifest: ExtensionManifest) -> None:
        """Validate using unified validation patterns from Phase 4.1.a."""
        if not UNIFIED_VALIDATION_AVAILABLE:
            return
        
        try:
            # Validate extension name using unified patterns
            if manifest.name:
                # Use unified validation for text content
                ValidationUtils.validate_text_content(manifest.name, min_length=1, max_length=50)
            
            # Validate description using unified patterns
            if manifest.description:
                ValidationUtils.validate_text_content(manifest.description, min_length=10, max_length=500)
            
            # Validate tags if present in manifest
            if hasattr(manifest, 'tags') and manifest.tags:
                ValidationUtils.validate_tags(manifest.tags)
                
        except ValueError as e:
            self.errors.append(f"Unified validation error: {str(e)}")
    
    def _validate_api_endpoint_compatibility(self, manifest: ExtensionManifest) -> None:
        """Validate API endpoint compatibility with new unified endpoints."""
        # Check if extension uses legacy API endpoints
        legacy_endpoints = [
            '/ag_ui/memory',
            '/memory_ag_ui',
            '/chat_memory',
            '/legacy'
        ]
        
        for endpoint in manifest.api.endpoints:
            if isinstance(endpoint, dict) and 'path' in endpoint:
                path = endpoint['path']
                for legacy_path in legacy_endpoints:
                    if legacy_path in path:
                        self.warnings.append(
                            f"Extension uses legacy API endpoint '{path}'. "
                            f"Consider updating to use unified endpoints: "
                            f"/copilot/assist, /memory/search, /memory/commit"
                        )
        
        # Check for recommended unified endpoint usage
        unified_endpoints = ['/copilot/assist', '/memory/search', '/memory/commit']
        uses_unified = False
        
        for endpoint in manifest.api.endpoints:
            if isinstance(endpoint, dict) and 'path' in endpoint:
                path = endpoint['path']
                if any(unified_path in path for unified_path in unified_endpoints):
                    uses_unified = True
                    break
        
        if not uses_unified and manifest.api.endpoints:
            self.warnings.append(
                "Extension does not use unified API endpoints. "
                "Consider integrating with /copilot/assist, /memory/search, /memory/commit for better compatibility."
            )
    
    def _validate_provider_integration(self, manifest: ExtensionManifest) -> None:
        """Validate provider integration compatibility."""
        # Check if extension declares provider capabilities
        if hasattr(manifest, 'capabilities') and manifest.capabilities:
            provider_capabilities = [
                'chat_assistance',
                'memory_integration', 
                'action_suggestions',
                'context_awareness',
                'real_time_streaming',
                'multi_tenant_support'
            ]
            
            declared_capabilities = getattr(manifest.capabilities, 'provides', [])
            if isinstance(declared_capabilities, list):
                for capability in declared_capabilities:
                    if capability in provider_capabilities:
                        # Extension provides provider-like capabilities
                        self.warnings.append(
                            f"Extension provides '{capability}' capability. "
                            f"Consider registering as a provider in the provider registry."
                        )
    
    def _validate_memory_system_integration(self, manifest: ExtensionManifest) -> None:
        """Validate memory system integration patterns."""
        # Check for memory-related permissions
        memory_permissions = ['memory:read', 'memory:write', 'memory:admin']
        extension_permissions = []
        
        # Collect all permissions from the manifest
        if manifest.permissions:
            extension_permissions.extend(manifest.permissions.data_access)
            extension_permissions.extend(manifest.permissions.system_access)
        
        uses_memory = any(perm in str(extension_permissions) for perm in ['memory', 'data'])
        
        if uses_memory:
            # Extension uses memory - validate it follows unified patterns
            self.warnings.append(
                "Extension uses memory functionality. "
                "Ensure it integrates with the unified memory service and follows "
                "tenant isolation patterns."
            )
            
            # Check for required memory dependencies
            required_services = ['postgres', 'milvus', 'redis']
            declared_services = manifest.dependencies.system_services
            
            missing_services = [svc for svc in required_services if svc not in declared_services]
            if missing_services:
                self.warnings.append(
                    f"Extension uses memory but doesn't declare dependencies on: {', '.join(missing_services)}. "
                    f"Consider adding these to system_services dependencies."
                )
    
    def validate_manifest_enhanced(self, manifest: Union[ExtensionManifest, Dict[str, Any]]) -> Tuple[bool, List[str], List[str], List[FieldError]]:
        """
        Enhanced validation with unified patterns and new API compatibility.
        
        Args:
            manifest: Extension manifest to validate
            
        Returns:
            Tuple of (is_valid, errors, warnings, field_errors)
        """
        # Run standard validation first
        is_valid, errors, warnings = self.validate_manifest(manifest)

        if not is_valid:
            return is_valid, errors, warnings, self.field_errors.copy()

        manifest_model = (
            manifest
            if isinstance(manifest, ExtensionManifest)
            else ExtensionManifest(**manifest)
        )

        # Run enhanced validations
        self._validate_with_unified_patterns(manifest_model)
        self._validate_api_endpoint_compatibility(manifest_model)
        self._validate_provider_integration(manifest_model)
        self._validate_memory_system_integration(manifest_model)
        
        # Update validity based on any new errors
        is_valid = len(self.errors) == 0
        
        return is_valid, self.errors.copy(), self.warnings.copy(), self.field_errors.copy()
    
    def get_validation_report(self, manifest: ExtensionManifest) -> Dict[str, Any]:
        """
        Get comprehensive validation report with recommendations.
        
        Args:
            manifest: Extension manifest to validate
            
        Returns:
            Dict containing validation results and recommendations
        """
        is_valid, errors, warnings, field_errors = self.validate_manifest_enhanced(manifest)
        
        # Generate recommendations based on validation results
        recommendations = []
        
        if not is_valid:
            recommendations.append("Fix validation errors before deploying extension")
        
        if warnings:
            recommendations.append("Review warnings for potential improvements")
        
        # API modernization recommendations
        if any("legacy" in warning.lower() for warning in warnings):
            recommendations.append("Update to use unified API endpoints for better performance and compatibility")
        
        # Provider integration recommendations
        if any("provider" in warning.lower() for warning in warnings):
            recommendations.append("Consider registering extension capabilities in the provider registry")
        
        # Memory system recommendations
        if any("memory" in warning.lower() for warning in warnings):
            recommendations.append("Ensure memory operations follow tenant isolation and RBAC patterns")
        
        return {
            "manifest_name": manifest.name,
            "manifest_version": manifest.version,
            "validation_timestamp": datetime.utcnow().isoformat(),
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "field_errors": [fe.dict() if hasattr(fe, 'dict') else str(fe) for fe in field_errors],
            "recommendations": recommendations,
            "compatibility": {
                "unified_api": not any("legacy" in warning.lower() for warning in warnings),
                "provider_registry": not any("provider" in warning.lower() for warning in warnings),
                "memory_system": not any("memory" in warning.lower() for warning in warnings),
                "rbac_ready": "admin" in str(manifest.permissions.system_access) if manifest.permissions else False
            },
            "summary": {
                "total_errors": len(errors),
                "total_warnings": len(warnings),
                "total_recommendations": len(recommendations),
                "overall_score": max(0, 100 - (len(errors) * 20) - (len(warnings) * 5))
            }
        }


def validate_extension_manifest(manifest: Union[ExtensionManifest, Dict[str, Any]]) -> Tuple[bool, List[str], List[str]]:
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