"""
UI Materialization Pipeline - Auto-generates UI artifacts from plugin canonical source.

This service:
- Scans plugin manifests for UI declarations
- Discovers UI components and icons from plugin directories
- Generates registration artifacts for the frontend
- Manages artifact lifecycle and cleanup
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib

from ai_karen_engine.extensions.platform.core.manifest import ExtensionManifest
from ai_karen_engine.extensions.platform.core.registry.plugin_registry import get_registry
from ai_karen_engine.extensions.platform.core.registry.database_service import get_database_service

logger = logging.getLogger("kari.ui_materialization")


class UIArtifact:
    """Represents a generated UI artifact."""

    def __init__(
        self,
        artifact_type: str,
        plugin_id: str,
        source_path: Path,
        target_path: Path,
        content_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.artifact_type = artifact_type
        self.plugin_id = plugin_id
        self.source_path = source_path
        self.target_path = target_path
        self.content_hash = content_hash
        self.metadata = metadata or {}
        self.generated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "plugin_id": self.plugin_id,
            "source_path": str(self.source_path),
            "target_path": str(self.target_path),
            "content_hash": self.content_hash,
            "metadata": self.metadata,
            "generated_at": self.generated_at.isoformat(),
        }


class UIMaterializationPipeline:
    """
    Pipeline for materializing UI artifacts from plugin canonical source.

    Artifact Types:
    - icon: Plugin icons following naming convention
    - component: React components for plugin UI
    - manifest_entry: Registration entries for frontend loader
    - menu_config: Menu placement configurations
    """

    # Supported icon naming convention: <plugin-id>---<placement>--<subplacement>_<NN>.<ext>
    ICON_PATTERN = r"^(.+?)---([a-z]+?)(?:--([a-z]+?))?_(\d{2})\.(svg|png|jpg|jpeg)$"

    SUPPORTED_ARTIFACT_TYPES = [
        "icon",
        "component",
        "manifest_entry",
        "menu_config",
    ]

    def __init__(
        self,
        extensions_dir: str = "src/ai_karen_engine/extensions/plugins",
        artifacts_dir: Optional[str] = None,
        plugins_ui_dir: Optional[str] = None,
    ):
        self.extensions_dir = Path(extensions_dir)
        self.artifacts_dir = (
            Path(artifacts_dir) if artifacts_dir else self.extensions_dir / ".artifacts"
        )
        self.plugins_ui_dir = (
            Path(plugins_ui_dir)
            if plugins_ui_dir
            else Path("src/ui_launchers/Karen-AI-Theme/src/plugin_repo")
        )
        self.registry = None
        self.database_service = None
        self._artifact_cache: Dict[str, UIArtifact] = {}

        # Ensure directories exist
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.plugins_ui_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"UIMaterializationPipeline initialized")
        logger.info(f"  Extensions dir: {self.extensions_dir}")
        logger.info(f"  Artifacts dir: {self.artifacts_dir}")
        logger.info(f"  Plugins UI dir: {self.plugins_ui_dir}")

    def _get_registry(self):
        """Lazily get registry, handling the case where it's not initialized."""
        if self.registry is None:
            try:
                self.registry = get_registry()
            except Exception as e:
                logger.warning(f"Registry not available: {e}")
                # Return None to indicate registry is not available
                return None
        return self.registry

    def _get_database_service(self):
        """Lazily get database service, handling the case where it's not initialized."""
        if self.database_service is None:
            try:
                self.database_service = get_database_service()
            except ValueError as e:
                logger.warning(f"Database service not available: {e}")
                # Return None to indicate database service is not available
                return None
        return self.database_service

    async def discover_ui_plugins(self) -> List[Dict[str, Any]]:
        """
        Discover all plugins that declare UI capabilities.

        Returns:
            List of plugin UI metadata
        """
        # First, try to get plugins from registry if available
        registry = self._get_registry()
        if registry is not None:
            try:
                plugins = await registry.list_all_extensions()
                if plugins:
                    return await self._process_registry_plugins(plugins)
            except Exception as e:
                logger.warning(f"Failed to get extensions from registry: {e}")

        # Fallback: Direct filesystem discovery
        logger.info("Registry not available, using filesystem discovery")
        return await self._discover_plugins_filesystem()

        ui_plugins = []

        for plugin in plugins:
            if not plugin.capabilities or not plugin.capabilities.get(
                "provides_ui", False
            ):
                continue

            plugin_dir = self.extensions_dir / plugin.name
            if not plugin_dir.exists():
                logger.warning(f"Plugin directory not found: {plugin_dir}")
                continue

            # Load manifest to get UI configuration
            manifest_path = plugin_dir / "plugin_manifest.json"
            if not manifest_path.exists():
                manifest_path = plugin_dir / "manifest.json"

            if not manifest_path.exists():
                continue

            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)

                ui_config = manifest_data.get("ui", {})
                if not ui_config:
                    continue

                # Check for UI component
                ui_component_dir = plugin_dir / "ui"
                if not ui_component_dir.exists():
                    # Fallback to checking source_path from config
                    source_path = ui_config.get("source_path")
                    if source_path:
                        ui_component_dir = plugin_dir / source_path

                # Resolve entry file
                entry_file_name = ui_config.get("entry_file", "PluginPage.tsx")
                entry_file_path = plugin_dir / entry_file_name
                if not entry_file_path.exists():
                    # Try relative to ui_component_dir
                    entry_file_path = ui_component_dir / Path(entry_file_name).name
                
                has_component = entry_file_path.exists()

                # Check for icons
                icons = self._discover_plugin_icons(plugin_dir, plugin.name)

                plugin_ui_data = {
                    "plugin_id": plugin.name,
                    "display_name": plugin.display_name,
                    "version": plugin.version,
                    "status": plugin.status.value,
                    "has_component": has_component
                    or ui_config.get("has_component", False),
                    "component_path": str(entry_file_path)
                    if has_component
                    else None,
                    "menu_config": ui_config.get("menu", []),
                    "icons": icons,
                    "ui_config": ui_config,
                }

                ui_plugins.append(plugin_ui_data)

            except Exception as e:
                logger.error(f"Failed to load UI config for {plugin.name}: {e}")

        logger.info(f"Discovered {len(ui_plugins)} UI-capable plugins")
        return ui_plugins

    def _discover_plugin_icons(
        self, plugin_dir: Path, plugin_id: str
    ) -> List[Dict[str, Any]]:
        """
        Discover icons following the naming convention.

        Convention: <plugin-id>---<placement>--<subplacement>_<NN>.<ext>
        Example: weather-query---sidebar--main_00.svg
        """
        import re

        icons = []
        pattern = re.compile(self.ICON_PATTERN)

        # Search in plugin directory
        for file_path in plugin_dir.rglob("*"):
            if not file_path.is_file():
                continue

            match = pattern.match(file_path.name)
            if match:
                icon_data = {
                    "filename": file_path.name,
                    "path": str(file_path),
                    "plugin_id": match.group(1),
                    "placement": match.group(2),
                    "subplacement": match.group(3),
                    "order": int(match.group(4)),
                    "extension": match.group(5),
                    "relative_path": str(file_path.relative_to(plugin_dir)),
                }
                icons.append(icon_data)

        return icons

    async def _process_registry_plugins(self, plugins) -> List[Dict[str, Any]]:
        """Process plugins obtained from registry."""
        ui_plugins = []

        for plugin in plugins:
            if not hasattr(plugin, "capabilities") or not plugin.capabilities.get(
                "provides_ui", False
            ):
                continue

            plugin_dir = self.extensions_dir / plugin.name
            if not plugin_dir.exists():
                logger.warning(f"Plugin directory not found: {plugin_dir}")
                continue

            # Load manifest to get UI configuration
            manifest_path = plugin_dir / "plugin_manifest.json"
            if not manifest_path.exists():
                manifest_path = plugin_dir / "manifest.json"

            if not manifest_path.exists():
                continue

            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)

                ui_config = manifest_data.get("ui", {})
                if not ui_config:
                    continue

                # Check for UI component
                ui_component_dir = plugin_dir / "ui"
                has_component = ui_component_dir.exists() and any(
                    f.suffix == ".tsx" or f.suffix == ".jsx"
                    for f in ui_component_dir.iterdir()
                    if f.is_file()
                )

                # Check for icons
                icons = self._discover_plugin_icons(plugin_dir, plugin.name)

                plugin_ui_data = {
                    "plugin_id": plugin.name,
                    "display_name": plugin.display_name,
                    "version": plugin.version,
                    "status": plugin.status.value
                    if hasattr(plugin, "status")
                    else "active",
                    "has_component": has_component
                    or ui_config.get("has_component", False),
                    "component_path": str(ui_component_dir / "PluginPage.tsx")
                    if has_component
                    else None,
                    "menu_config": ui_config.get("menu", []),
                    "icons": icons,
                    "ui_config": ui_config,
                }

                ui_plugins.append(plugin_ui_data)

            except Exception as e:
                logger.error(f"Failed to load UI config for {plugin.name}: {e}")

        logger.info(f"Discovered {len(ui_plugins)} UI-capable plugins from registry")
        return ui_plugins

    async def _discover_plugins_filesystem(self) -> List[Dict[str, Any]]:
        """Discover plugins directly from filesystem when registry is not available."""
        ui_plugins = []

        # Scan extensions directory for plugin manifests
        for extension_dir in self.extensions_dir.iterdir():
            if not extension_dir.is_dir():
                continue

            # Skip if it's a system directory
            if extension_dir.name.startswith(".") or extension_dir.name in [
                "core",
                "api_routes",
                "channels",
                "__pycache__",
            ]:
                continue

            # Look for manifest files
            manifest_path = extension_dir / "plugin_manifest.json"
            if not manifest_path.exists():
                manifest_path = extension_dir / "manifest.json"

            if not manifest_path.exists():
                continue

            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)

                # Check if plugin has UI capabilities
                ui_config = manifest_data.get("ui", {})
                if not ui_config and not manifest_data.get("capabilities", {}).get(
                    "provides_ui", False
                ):
                    continue

                # Get plugin info
                plugin_id = manifest_data.get("name", extension_dir.name)
                display_name = manifest_data.get("display_name", plugin_id)
                version = manifest_data.get("version", "1.0.0")

                # Check for UI component
                ui_component_dir = extension_dir / "ui"
                has_component = ui_component_dir.exists() and any(
                    f.suffix == ".tsx" or f.suffix == ".jsx"
                    for f in ui_component_dir.iterdir()
                    if f.is_file()
                )

                # Check for icons
                icons = self._discover_plugin_icons(extension_dir, plugin_id)

                plugin_ui_data = {
                    "plugin_id": plugin_id,
                    "display_name": display_name,
                    "version": version,
                    "status": "active",  # Assume active when discovered from filesystem
                    "has_component": has_component
                    or ui_config.get("has_component", False),
                    "component_path": str(ui_component_dir / "PluginPage.tsx")
                    if has_component
                    else None,
                    "menu_config": ui_config.get("menu", []),
                    "icons": icons,
                    "ui_config": ui_config,
                }

                ui_plugins.append(plugin_ui_data)

            except Exception as e:
                logger.error(f"Failed to load UI config for {extension_dir.name}: {e}")

        logger.info(f"Discovered {len(ui_plugins)} UI-capable plugins from filesystem")
        return ui_plugins

    async def materialize_all(self) -> Dict[str, Any]:
        """
        Materialize UI artifacts for all plugins.

        Returns:
            Materialization result summary
        """
        logger.info("Starting full UI materialization")

        ui_plugins = await self.discover_ui_plugins()
        artifacts_generated = []
        artifacts_updated = []
        artifacts_removed = []
        errors = []

        for plugin_ui in ui_plugins:
            try:
                result = await self.materialize_plugin(plugin_ui)
                artifacts_generated.extend(result["generated"])
                artifacts_updated.extend(result["updated"])
                artifacts_removed.extend(result["removed"])

            except Exception as e:
                logger.error(f"Failed to materialize {plugin_ui['plugin_id']}: {e}")
                errors.append(
                    {
                        "plugin_id": plugin_ui["plugin_id"],
                        "error": str(e),
                    }
                )

        # Clean up stale artifacts
        stale = await self.cleanup_stale_artifacts(ui_plugins)
        artifacts_removed.extend(stale)

        # Generate import map
        import_map = await self.generate_import_map(ui_plugins)

        result = {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "plugins_processed": len(ui_plugins),
            "artifacts_generated": len(artifacts_generated),
            "artifacts_updated": len(artifacts_updated),
            "artifacts_removed": len(artifacts_removed),
            "errors": errors,
            "import_map": import_map,
        }

        logger.info(f"UI materialization complete: {result}")
        return result

    async def materialize_plugin(self, plugin_ui: Dict[str, Any]) -> Dict[str, Any]:
        """
        Materialize UI artifacts for a single plugin.

        Args:
            plugin_ui: Plugin UI metadata from discover_ui_plugins()

        Returns:
            Materialization result for this plugin
        """
        plugin_id = plugin_ui["plugin_id"]
        logger.info(f"Materializing UI for plugin: {plugin_id}")

        generated = []
        updated = []
        removed = []

        # Materialize icons
        if plugin_ui.get("icons"):
            icon_results = await self._materialize_icons(plugin_ui)
            generated.extend(icon_results["generated"])
            updated.extend(icon_results["updated"])

        # Materialize component registration
        if plugin_ui.get("has_component") and plugin_ui.get("component_path"):
            # First, ensure UI source files are copied to plugin_repo
            await self._materialize_ui_source(plugin_ui)
            
            component_result = await self._materialize_component(plugin_ui)
            if component_result:
                if component_result["action"] == "generated":
                    generated.append(component_result["artifact"])
                elif component_result["action"] == "updated":
                    updated.append(component_result["artifact"])

        # Materialize menu configuration
        if plugin_ui.get("menu_config"):
            menu_result = await self._materialize_menu_config(plugin_ui)
            if menu_result:
                generated.append(menu_result["artifact"])

        return {
            "plugin_id": plugin_id,
            "generated": generated,
            "updated": updated,
            "removed": removed,
        }

    async def _materialize_icons(
        self, plugin_ui: Dict[str, Any]
    ) -> Dict[str, List[Any]]:
        """Materialize icon artifacts."""
        generated = []
        updated = []

        plugin_id = plugin_ui["plugin_id"]
        icons = plugin_ui.get("icons", [])

        # Create icon output directory
        icon_output_dir = self.artifacts_dir / "icons" / plugin_id
        icon_output_dir.mkdir(parents=True, exist_ok=True)

        for icon in icons:
            source_path = Path(icon["path"])

            if not source_path.exists():
                logger.warning(f"Icon source not found: {source_path}")
                continue

            # Calculate content hash
            content_hash = self._calculate_file_hash(source_path)

            # Target path
            target_path = icon_output_dir / icon["filename"]

            # Check if artifact needs update
            existing_hash = None
            if target_path.exists():
                existing_hash = self._calculate_file_hash(target_path)

            # Copy icon if new or updated
            if existing_hash != content_hash:
                shutil.copy2(source_path, target_path)

                artifact = UIArtifact(
                    artifact_type="icon",
                    plugin_id=plugin_id,
                    source_path=source_path,
                    target_path=target_path,
                    content_hash=content_hash,
                    metadata=icon,
                )

                if existing_hash is None:
                    generated.append(artifact.to_dict())
                    logger.debug(f"Generated icon artifact: {target_path}")
                else:
                    updated.append(artifact.to_dict())
                    logger.debug(f"Updated icon artifact: {target_path}")

                self._artifact_cache[str(target_path)] = artifact

        return {"generated": generated, "updated": updated}

    async def _materialize_component(
        self, plugin_ui: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Materialize component registration artifact."""
        plugin_id = plugin_ui["plugin_id"]
        component_path = Path(plugin_ui["component_path"])

        if not component_path.exists():
            logger.warning(f"Component source not found: {component_path}")
            return None

        # Calculate content hash
        content_hash = self._calculate_file_hash(component_path)

        # Target path for registration
        target_path = self.artifacts_dir / "components" / f"{plugin_id}.json"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if artifact needs update
        existing_hash = None
        if target_path.exists():
            existing_hash = self._calculate_file_hash(target_path)

        if existing_hash != content_hash:
            # Create component registration artifact
            artifact_data = {
                "plugin_id": plugin_id,
                "component_path": str(component_path),
                "display_name": plugin_ui.get("display_name", plugin_id),
                "version": plugin_ui.get("version", "1.0.0"),
                "status": plugin_ui.get("status", "active"),
                "generated_at": datetime.utcnow().isoformat(),
                "content_hash": content_hash,
            }

            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(artifact_data, f, indent=2)

            artifact = UIArtifact(
                artifact_type="component",
                plugin_id=plugin_id,
                source_path=component_path,
                target_path=target_path,
                content_hash=content_hash,
                metadata=artifact_data,
            )

            action = "generated" if existing_hash is None else "updated"
            self._artifact_cache[str(target_path)] = artifact

            logger.debug(f"{action.capitalize()} component artifact: {target_path}")
            return {"action": action, "artifact": artifact.to_dict()}

        return None

    async def _materialize_ui_source(self, plugin_ui: Dict[str, Any]) -> bool:
        """Copy UI source files from plugin directory to plugin_repo."""
        plugin_id = plugin_ui["plugin_id"]
        ui_config = plugin_ui.get("ui_config", {})
        
        # Source directory for UI files
        plugin_dir = self.extensions_dir / plugin_id
        source_path_rel = ui_config.get("source_path", "ui")
        source_dir = plugin_dir / source_path_rel
        
        if not source_dir.exists():
            # If no 'ui' or configured subdir, use root as source for TSX files
            source_dir = plugin_dir
            
        # Target directory in plugin_repo
        target_dir = self.plugins_ui_dir / plugin_id.replace("_", "-")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 1. Copy all UI related files
            for file_path in source_dir.rglob("*"):
                if file_path.suffix in [".tsx", ".jsx", ".css", ".svg"]:
                    # Compute relative target path
                    rel_path = file_path.relative_to(source_dir)
                    dest_path = target_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy if changed
                    if not dest_path.exists() or self._calculate_file_hash(file_path) != self._calculate_file_hash(dest_path):
                        shutil.copy2(file_path, dest_path)
                        logger.debug(f"Materialized UI file: {dest_path}")
            
            # 2. Copy/Create GUI manifest in target
            gui_manifest_source = plugin_dir / "manifest.json"
            if not gui_manifest_source.exists():
                gui_manifest_source = plugin_dir / plugin_id / "manifest.json"
                
            dest_manifest = target_dir / "manifest.json"
            if gui_manifest_source.exists():
                if not dest_manifest.exists() or self._calculate_file_hash(gui_manifest_source) != self._calculate_file_hash(dest_manifest):
                    shutil.copy2(gui_manifest_source, dest_manifest)
            
            return True
        except Exception as e:
            logger.error(f"Failed to materialize UI source for {plugin_id}: {e}")
            return False

    async def _materialize_menu_config(
        self, plugin_ui: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Materialize menu configuration artifact."""
        plugin_id = plugin_ui["plugin_id"]
        menu_config = plugin_ui.get("menu_config", [])

        if not menu_config:
            return None

        # Target path for menu configuration
        target_path = self.artifacts_dir / "menus" / f"{plugin_id}.json"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Create menu configuration artifact
        artifact_data = {
            "plugin_id": plugin_id,
            "display_name": plugin_ui.get("display_name", plugin_id),
            "menus": menu_config,
            "icons": plugin_ui.get("icons", []),
            "generated_at": datetime.utcnow().isoformat(),
        }

        # Convert to JSON string for hashing
        content_str = json.dumps(artifact_data, sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()

        # Check if artifact needs update
        existing_hash = None
        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as f:
                existing_content = json.load(f)
            existing_str = json.dumps(existing_content, sort_keys=True)
            existing_hash = hashlib.sha256(existing_str.encode()).hexdigest()

        if existing_hash != content_hash:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(artifact_data, f, indent=2)

            artifact = UIArtifact(
                artifact_type="menu_config",
                plugin_id=plugin_id,
                source_path=self.extensions_dir / plugin_id / "plugin_manifest.json",
                target_path=target_path,
                content_hash=content_hash,
                metadata=artifact_data,
            )

            self._artifact_cache[str(target_path)] = artifact
            logger.debug(f"Generated menu artifact: {target_path}")

            return {"artifact": artifact.to_dict()}

        return None

    async def generate_import_map(
        self, ui_plugins: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Generate the PLUGIN_IMPORT_MAP for the frontend.

        Args:
            ui_plugins: List of UI plugin metadata

        Returns:
            Dictionary mapping plugin IDs to import paths
        """
        import_map = {}

        for plugin in ui_plugins:
            if not plugin.get("has_component"):
                continue

            plugin_id = plugin["plugin_id"]
            component_path = plugin.get("component_path")

            if not component_path:
                continue

            # Normalize plugin ID
            normalized_id = plugin_id.lower().replace("_", "-")

            # Convert filesystem path to frontend import path
            # Example: src/ai_karen_engine/extensions/plugins/time_query/ui/DateTimePluginPage.tsx
            # becomes: @/plugin_repo/time-query/DateTimePluginPage
            component_path_obj = Path(component_path)
            
            # Find the index of the 'plugins' directory to extract the plugin folder name
            parts = component_path_obj.parts
            plugin_idx = None
            for idx, part in enumerate(parts):
                if part == "plugins":
                    plugin_idx = idx
                    break
            
            if plugin_idx is not None and plugin_idx + 1 < len(parts):
                # The folder name in extensions/plugins/ (e.g., 'time_query')
                plugin_folder_name = parts[plugin_idx + 1]
                # Normalize folder name for frontend (hyphens)
                normalized_plugin_id = plugin_folder_name.lower().replace("_", "-")
                
                # The filename without extension
                component_name = component_path_obj.stem
                
                # Check if it was in a 'ui' folder
                if "ui" in parts:
                    import_path = f"@/plugin_repo/{normalized_plugin_id}/ui/{component_name}"
                else:
                    import_path = f"@/plugin_repo/{normalized_plugin_id}/{component_name}"
                    
                import_map[normalized_id] = import_path
                import_map[plugin_id] = import_path

        logger.info(f"Generated import map with {len(import_map)} entries")
        return import_map

    async def cleanup_stale_artifacts(
        self, active_plugins: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove artifacts for plugins that no longer exist or don't declare UI.

        Args:
            active_plugins: List of currently active UI plugins

        Returns:
            List of removed artifacts
        """
        removed = []
        active_plugin_ids = {p["plugin_id"] for p in active_plugins}

        # Check each artifact directory
        for artifact_type_dir in ["icons", "components", "menus"]:
            type_dir = self.artifacts_dir / artifact_type_dir
            if not type_dir.exists():
                continue

            for plugin_dir in type_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue

                plugin_id = plugin_dir.name

                # Remove if plugin no longer active
                if plugin_id not in active_plugin_ids:
                    logger.info(
                        f"Removing stale artifacts for inactive plugin: {plugin_id}"
                    )

                    for artifact_file in plugin_dir.rglob("*"):
                        if artifact_file.is_file():
                            removed.append(
                                {
                                    "artifact_type": artifact_type_dir,
                                    "plugin_id": plugin_id,
                                    "path": str(artifact_file),
                                    "action": "removed",
                                }
                            )

                    shutil.rmtree(plugin_dir, ignore_errors=True)

        return removed

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        hash_sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_sha256.update(chunk)

        return hash_sha256.hexdigest()

    async def get_artifact_status(self) -> Dict[str, Any]:
        """
        Get status of all generated artifacts.

        Returns:
            Artifact status summary
        """
        status = {
            "artifacts_dir": str(self.artifacts_dir),
            "artifact_types": {},
            "total_artifacts": 0,
        }

        for artifact_type in self.SUPPORTED_ARTIFACT_TYPES:
            type_dir = self.artifacts_dir / artifact_type
            if not type_dir.exists():
                status["artifact_types"][artifact_type] = {"count": 0}
                continue

            artifacts = []
            for plugin_dir in type_dir.rglob("*"):
                if plugin_dir.is_file():
                    artifacts.append(str(plugin_dir))

            status["artifact_types"][artifact_type] = {
                "count": len(artifacts),
                "artifacts": artifacts[:10],  # Limit to 10 for readability
            }
            status["total_artifacts"] += len(artifacts)

        return status


# Singleton instance
_pipeline_instance: Optional[UIMaterializationPipeline] = None


def get_ui_pipeline(
    extensions_dir: str = "src/ai_karen_engine/extensions/plugins",
    artifacts_dir: Optional[str] = None,
    plugins_ui_dir: Optional[str] = None,
) -> UIMaterializationPipeline:
    """Get the singleton UI materialization pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = UIMaterializationPipeline(
            extensions_dir=extensions_dir,
            artifacts_dir=artifacts_dir,
            plugins_ui_dir=plugins_ui_dir,
        )
    return _pipeline_instance
