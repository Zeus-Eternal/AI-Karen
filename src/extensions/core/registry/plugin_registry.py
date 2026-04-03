from typing import Dict, Any, List, Optional
import logging
from enum import Enum
from datetime import datetime

logger = logging.getLogger("kari.plugin_registry")

class PluginStatus(Enum):
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"

class PluginManifest:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.version = kwargs.get("version", "0.0.0")
        self.capabilities = kwargs.get("capabilities", {})
        self.display_name = kwargs.get("display_name")
        self.description = kwargs.get("description")
        self.category = kwargs.get("category")
        self.author = kwargs.get("author")
        self.provides_ui = kwargs.get("provides_ui", False)
        self.provides_api = kwargs.get("provides_api", False)
        self.provides_background_tasks = kwargs.get("provides_background_tasks", False)
        self.provides_webhooks = kwargs.get("provides_webhooks", False)

class PluginRecord:
    def __init__(self, manifest_data: Dict[str, Any]):
        # Default capabilities if missing
        if "capabilities" not in manifest_data:
            manifest_data["capabilities"] = {}
        self.manifest = PluginManifest(**manifest_data)
        self.status = PluginStatus.UNLOADED
        self.loaded_at: Optional[datetime] = None
        self.error_message: Optional[str] = None

class PluginRegistry:
    """
    Single source of truth for all Plugin Packages in Karen AI.
    Handles discovery, prompt-first manifest validation, and cataloging.
    """
    def __init__(self):
        self._plugins: Dict[str, PluginRecord] = {}

    def validate_manifest(self, manifest: Dict[str, Any]) -> bool:
        """
        Prompt-First Contract validation.
        Validates that a plugin provides the expected structure.
        """
        # A valid plugin MUST have a name, version, and prompt capability definition
        required_keys = {"name", "version", "capabilities"}
        return required_keys.issubset(manifest.keys())

    def register(self, plugin_id: str, manifest: Dict[str, Any]) -> bool:
        """
        Registers a plugin package after validating its manifest contract.
        """
        if not self.validate_manifest(manifest):
            logger.error(f"Plugin {plugin_id} failed prompt-first manifest validation. Rejected.")
            return False
            
        self._plugins[plugin_id] = manifest
        logger.debug(f"Registered plugin package {plugin_id}")
        return True

    def get_plugin(self, plugin_id: str) -> Optional[PluginRecord]:
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> List[str]:
        return list(self._plugins.keys())
        
    def list_extensions(self) -> List[PluginRecord]:
        return list(self._plugins.values())

    def get_all_manifests(self) -> Dict[str, PluginRecord]:
        return self._plugins.copy()

# Singleton registry instance
_registry_instance: Optional[PluginRegistry] = None

def get_registry() -> PluginRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = PluginRegistry()
    return _registry_instance
