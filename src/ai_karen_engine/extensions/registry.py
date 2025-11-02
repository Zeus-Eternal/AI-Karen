"""
Extension registry for tracking installed extensions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ai_karen_engine.extensions.models import ExtensionManifest, ExtensionRecord, ExtensionStatus


class ExtensionRegistry:
    """
    Registry for tracking installed and loaded extensions.
    
    This class maintains the state of all extensions in the system,
    including their manifests, status, and runtime information.
    """
    
    def __init__(
        self,
        plugin_registry: Optional[Any] = None,
        service_registry: Optional[Any] = None,
    ):
        """Initialize the extension registry.

        Args:
            plugin_registry: Optional pre-configured plugin registry instance.
            service_registry: Optional pre-configured service registry instance.
        """
        self.extensions: Dict[str, ExtensionRecord] = {}
        self.logger = logging.getLogger("extension.registry")
        self._plugin_registry = plugin_registry
        self._service_registry = service_registry
    
    def register_extension(
        self, 
        manifest: ExtensionManifest,
        instance: Any,
        directory: str
    ) -> ExtensionRecord:
        """
        Register a new extension in the registry.
        
        Args:
            manifest: Extension manifest
            instance: Extension instance
            directory: Extension directory path
            
        Returns:
            ExtensionRecord for the registered extension
        """
        from pathlib import Path
        
        record = ExtensionRecord(
            manifest=manifest,
            instance=instance,
            status=ExtensionStatus.LOADING,
            directory=Path(directory),
            loaded_at=datetime.now(timezone.utc),
        )
        
        self.extensions[manifest.name] = record
        self.logger.info(f"Registered extension {manifest.name} v{manifest.version}")
        
        return record
    
    def unregister_extension(self, name: str) -> bool:
        """
        Unregister an extension from the registry.
        
        Args:
            name: Extension name
            
        Returns:
            True if extension was unregistered, False if not found
        """
        if name in self.extensions:
            del self.extensions[name]
            self.logger.info(f"Unregistered extension {name}")
            return True
        return False
    
    def get_extension(self, name: str) -> Optional[ExtensionRecord]:
        """
        Get extension record by name.
        
        Args:
            name: Extension name
            
        Returns:
            ExtensionRecord if found, None otherwise
        """
        return self.extensions.get(name)
    
    def list_extensions(
        self, 
        status_filter: Optional[ExtensionStatus] = None
    ) -> List[ExtensionRecord]:
        """
        List all registered extensions.
        
        Args:
            status_filter: Optional status filter
            
        Returns:
            List of ExtensionRecord instances
        """
        extensions = list(self.extensions.values())
        
        if status_filter:
            extensions = [ext for ext in extensions if ext.status == status_filter]
        
        return extensions
    
    def update_status(self, name: str, status: ExtensionStatus, error_message: Optional[str] = None) -> bool:
        """
        Update extension status.
        
        Args:
            name: Extension name
            status: New status
            error_message: Optional error message
            
        Returns:
            True if status was updated, False if extension not found
        """
        if name in self.extensions:
            self.extensions[name].status = status
            self.extensions[name].error_message = error_message
            self.logger.info(
                f"Updated extension {name} status to {status.value}"
            )
            return True
        return False
    
    def get_active_extensions(self) -> List[ExtensionRecord]:
        """Get all active extensions."""
        return self.list_extensions(ExtensionStatus.ACTIVE)
    
    def get_extension_count(self) -> int:
        """Get total number of registered extensions."""
        return len(self.extensions)
    
    def get_status_summary(self) -> Dict[str, int]:
        """
        Get summary of extension statuses.
        
        Returns:
            Dictionary with status counts
        """
        summary = {}
        for status in ExtensionStatus:
            summary[status.value] = 0
        
        for extension in self.extensions.values():
            summary[extension.status.value] += 1
        
        return summary
    
    def find_extensions_by_category(self, category: str) -> List[ExtensionRecord]:
        """
        Find extensions by category.
        
        Args:
            category: Extension category
            
        Returns:
            List of matching ExtensionRecord instances
        """
        return [
            ext for ext in self.extensions.values()
            if ext.manifest.category == category
        ]
    
    def find_extensions_by_tag(self, tag: str) -> List[ExtensionRecord]:
        """
        Find extensions by tag.
        
        Args:
            tag: Extension tag
            
        Returns:
            List of matching ExtensionRecord instances
        """
        return [
            ext for ext in self.extensions.values()
            if tag in ext.manifest.tags
        ]
    
    def check_dependencies(self, manifest: ExtensionManifest) -> Dict[str, bool]:
        """
        Check if extension dependencies are satisfied.
        
        Args:
            manifest: Extension manifest to check
            
        Returns:
            Dictionary mapping dependency names to availability status
        """
        dependency_status: Dict[str, bool] = {}

        # Check extension dependencies
        for dep in manifest.dependencies.extensions:
            dep_name, version_spec = self._parse_dependency_spec(dep)
            dep_extension = self.get_extension(dep_name)
            is_available = False

            if dep_extension and dep_extension.status in {
                ExtensionStatus.ACTIVE,
                ExtensionStatus.LOADING,
            }:
                if version_spec:
                    is_available = self._is_version_compatible(
                        dep_extension.manifest.version,
                        version_spec,
                    )
                else:
                    is_available = True

            dependency_status[f"extension:{dep}"] = is_available

        # Check plugin dependencies
        plugin_registry = self._get_plugin_registry()
        if manifest.dependencies.plugins:
            for dep in manifest.dependencies.plugins:
                dep_name, version_spec = self._parse_dependency_spec(dep)
                is_available = False

                if plugin_registry is not None:
                    plugin_meta = getattr(plugin_registry, "get_plugin", lambda *_: None)(
                        dep_name
                    )

                    if plugin_meta is not None:
                        plugin_status = getattr(plugin_meta, "status", None)
                        try:
                            from ai_karen_engine.services.plugin_registry import PluginStatus

                            allowed_statuses = {
                                PluginStatus.ACTIVE,
                                PluginStatus.LOADED,
                                PluginStatus.REGISTERED,
                                PluginStatus.VALIDATED,
                            }
                            status_allows_use = plugin_status in allowed_statuses
                        except ImportError:  # pragma: no cover - defensive fallback
                            status_allows_use = str(plugin_status).lower() not in {
                                "error",
                                "disabled",
                            }

                        if status_allows_use:
                            plugin_version = getattr(
                                plugin_meta.manifest,
                                "version",
                                None,
                            )
                            if version_spec and plugin_version:
                                is_available = self._is_version_compatible(
                                    plugin_version,
                                    version_spec,
                                )
                            else:
                                is_available = True

                dependency_status[f"plugin:{dep}"] = is_available

        # Check system service dependencies
        service_registry = self._get_service_registry()
        if manifest.dependencies.system_services:
            for service_name in manifest.dependencies.system_services:
                is_available = False

                if service_registry is not None:
                    service_info = getattr(
                        service_registry,
                        "get_service_info",
                        lambda *_: None,
                    )(service_name)

                    if service_info is not None:
                        service_status = getattr(service_info, "status", None)
                        try:
                            from ai_karen_engine.core.service_registry import ServiceStatus

                            is_available = service_status in {
                                ServiceStatus.READY,
                                ServiceStatus.DEGRADED,
                            }
                        except ImportError:  # pragma: no cover - defensive fallback
                            is_available = str(service_status).lower() in {
                                "ready",
                                "degraded",
                            }

                dependency_status[f"service:{service_name}"] = is_available

        return dependency_status

    def _parse_dependency_spec(self, dependency: str) -> Tuple[str, Optional[str]]:
        """Split a dependency specification into name and version component."""
        if "@" in dependency:
            dep_name, version_spec = dependency.split("@", 1)
            return dep_name.strip(), version_spec.strip() or None
        return dependency.strip(), None

    def _is_version_compatible(self, available_version: str, required_spec: str) -> bool:
        """Evaluate whether an available version satisfies a version constraint."""
        required_spec = required_spec.strip()
        if not required_spec:
            return True

        caret_prefix = required_spec.startswith("^")
        tilde_prefix = required_spec.startswith("~")

        if caret_prefix or tilde_prefix:
            version_text = required_spec[1:]
            return self._compare_caret_tilde_versions(
                available_version,
                version_text,
                caret_prefix,
            )

        try:  # Prefer packaging when available for rich spec support
            from packaging.specifiers import SpecifierSet
            from packaging.version import InvalidVersion, Version

            try:
                spec_set = SpecifierSet(required_spec)
            except Exception:  # pragma: no cover - invalid spec fallback
                return available_version == required_spec

            try:
                return Version(available_version) in spec_set
            except InvalidVersion:
                return False
        except ImportError:  # pragma: no cover - packaging not installed
            return available_version == required_spec

    def _compare_caret_tilde_versions(
        self,
        available_version: str,
        required_version: str,
        is_caret: bool,
    ) -> bool:
        """Fallback comparison for caret/tilde semantic requirements."""
        def _parse(version: str) -> List[int]:
            parts = [int(part) for part in version.split(".") if part.isdigit()]
            while len(parts) < 3:
                parts.append(0)
            return parts[:3]

        try:
            available_parts = _parse(available_version)
            required_parts = _parse(required_version)
        except ValueError:
            return False

        if is_caret:
            return (
                available_parts[0] == required_parts[0]
                and available_parts >= required_parts
            )

        return (
            available_parts[0] == required_parts[0]
            and available_parts[1] == required_parts[1]
            and available_parts[2] >= required_parts[2]
        )

    def _get_plugin_registry(self) -> Optional[Any]:
        """Resolve the plugin registry instance if available."""
        if self._plugin_registry is not None:
            return self._plugin_registry

        try:
            from ai_karen_engine.services.plugin_registry import get_plugin_registry

            self._plugin_registry = get_plugin_registry()
        except Exception:  # pragma: no cover - plugin system optional
            self._plugin_registry = None

        return self._plugin_registry

    def _get_service_registry(self) -> Optional[Any]:
        """Resolve the service registry instance if available."""
        if self._service_registry is not None:
            return self._service_registry

        try:
            from ai_karen_engine.core.service_registry import get_service_registry

            self._service_registry = get_service_registry()
        except Exception:  # pragma: no cover - service registry optional
            self._service_registry = None

        return self._service_registry
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert registry to dictionary for serialization.
        
        Returns:
            Dictionary representation of the registry
        """
        return {
            "extensions": {
                name: record.to_dict() 
                for name, record in self.extensions.items()
            },
            "summary": self.get_status_summary(),
            "total_count": self.get_extension_count()
        }


__all__ = ["ExtensionRegistry"]