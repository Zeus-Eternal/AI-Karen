"""Unified extension host manager."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ai_karen_engine.extensions.platform.core.host.loader import ExtensionLoader
from ai_karen_engine.extensions.platform.core.host.models import ExtensionRecord, ExtensionStatus
from ai_karen_engine.extensions.platform.core.registry.plugin_registry import get_registry


class ExtensionManager:
    """Minimal runtime manager coordinating discovery and loading."""

    def __init__(
        self,
        extension_root: Path | str = "src/ai_karen_engine/extensions/plugins",
        plugin_router: Any = None,
        db_session: Any = None,
        app_instance: Any = None,
        use_new_architecture: bool = True,
    ) -> None:
        self.extension_root = Path(extension_root)
        self.plugin_router = plugin_router
        self.db_session = db_session
        self.app_instance = app_instance
        self.use_new_architecture = use_new_architecture
        self.loader = ExtensionLoader(str(self.extension_root))
        self.registry = get_registry()

    def get_extension_by_name(self, name: str) -> Optional[ExtensionRecord]:
        """Get an extension record by its name."""
        return self.registry.get_extension(name)

    async def discover_extensions(self) -> Dict[str, Any]:
        await self.registry.refresh()
        manifests: Dict[str, Any] = {}
        for extension_id in self.registry.list_discovered():
            metadata = self.registry.get_metadata(extension_id)
            if metadata and hasattr(metadata, "manifest_path"):
                manifests[extension_id] = self.loader.load_manifest(extension_id)
        return manifests

    async def load_extension(self, extension_name: str) -> Optional[ExtensionRecord]:
        instance = self.loader.load_extension(extension_name)
        record = ExtensionRecord(
            manifest=instance.manifest,
            instance=instance,
            status=ExtensionStatus.ACTIVE,
            directory=self.extension_root / extension_name,
            loaded_at=datetime.now(),
        )
        self.registry.register_loaded_instance(record)
        return record

    async def unload_extension(self, extension_name: str) -> bool:
        loaded = self.loader.get_loaded_extensions()
        instance = loaded.get(extension_name)
        if instance and hasattr(instance, "_shutdown"):
            await instance._shutdown()
        self.loader._loaded_extensions.pop(extension_name, None)
        self.registry._extensions.pop(extension_name, None)
        return True
