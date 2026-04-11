"""
Generated Import Registry for Karen Plugin System

This system auto-generates import maps from the plugin_repo directory
for Next.js bundler-safe dynamic loading.

Requirements: 3.2, 7.1, 7.2, 7.3, 34, 35
"""

import os
import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
import logging
from datetime import datetime

from .ui_installer import get_ui_service, UIInstallationState

logger = logging.getLogger(__name__)


@dataclass
class RegistryEntry:
    """Entry in the generated import registry."""
    plugin_id: str
    import_path: str
    component_name: str
    checksum: str
    size_bytes: int
    generated_at: datetime
    manifest_data: Dict[str, Any]


class GeneratedImportRegistry:
    """Registry that auto-generates import maps from plugin_repo."""

    def __init__(self,
                 plugins_repo_root: str = "ui_launchers/Karen-AI-Theme/src/plugin_repo",
                 output_file: str = "ui_launchers/Karen-AI-Theme/src/plugin-import-map.generated.ts"):
        self.plugins_repo_root = Path(plugins_repo_root)
        self.output_file = Path(output_file)
        self.ui_service = get_ui_service()
        
        # Ensure directories exist
        self.plugins_repo_root.mkdir(parents=True, exist_ok=True)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Track registry entries
        self.entries: Dict[str, RegistryEntry] = {}
        # Source of truth is the filesystem + ui_installer state; do not attempt
        # to parse the generated TypeScript module back into Python.

    def _load_registry(self) -> None:
        """Load existing registry from file."""
        return

    def _save_registry(self) -> None:
        """Save registry to file."""
        return

    def _generate_import_path(self, plugin_id: str) -> str:
        """Generate import path for a plugin."""
        return f"@/plugin_repo/{plugin_id}/{plugin_id}"

    def _generate_component_name(self, plugin_id: str) -> str:
        """Generate component name for a plugin."""
        return f"{plugin_id}Plugin"

    def _validate_plugin_package(self, plugin_id: str) -> bool:
        """Validate a plugin package in plugin_repo."""
        package_path = self.plugins_repo_root / plugin_id
        if not package_path.exists():
            return False

        # Check required files
        manifest_path = package_path / "manifest.json"
        entry_file = package_path / f"{plugin_id}.tsx"
        
        if not (manifest_path.exists() and entry_file.exists()):
            return False

        # Try to load manifest
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            # Validate required fields
            required_fields = ["id", "name", "version"]
            for field in required_fields:
                if field not in manifest_data:
                    logger.warning(f"Missing required field '{field}' in {plugin_id} manifest")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load manifest for {plugin_id}: {e}")
            return False

    def _calculate_checksum(self, plugin_id: str) -> str:
        """Calculate checksum for plugin package."""
        import hashlib
        
        package_path = self.plugins_repo_root / plugin_id
        if not package_path.exists():
            return ""
        
        hash_sha256 = hashlib.sha256()
        for root, dirs, files in os.walk(package_path):
            for file in files:
                file_path = Path(root) / file
                try:
                    with open(file_path, 'rb') as f:
                        hash_sha256.update(f.read())
                except (IOError, OSError):
                    continue
        
        return hash_sha256.hexdigest()

    def _get_package_size(self, plugin_id: str) -> int:
        """Get package size in bytes."""
        package_path = self.plugins_repo_root / plugin_id
        if not package_path.exists():
            return 0
        
        total_size = 0
        for root, dirs, files in os.walk(package_path):
            for file in files:
                file_path = Path(root) / file
                try:
                    total_size += file_path.stat().st_size
                except (IOError, OSError):
                    continue
        
        return total_size

    def _load_manifest_data(self, plugin_id: str) -> Dict[str, Any]:
        """Load manifest data for a plugin."""
        manifest_path = self.plugins_repo_root / plugin_id / "manifest.json"
        if not manifest_path.exists():
            return {}
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load manifest for {plugin_id}: {e}")
            return {}

    def generate_registry(self) -> Dict[str, Any]:
        """Generate the complete import registry."""
        logger.info("Generating import registry...")
        
        # Get current UI installations
        installed_ui = self.ui_service.list_installed_ui()
        
        # Clear existing entries
        self.entries.clear()
        
        # Process each installed UI
        for ui_info in installed_ui:
            plugin_id = ui_info['plugin_id']
            
            # Skip if not in valid state
            if ui_info.get('state') != UIInstallationState.INSTALLED.value:
                logger.warning(f"Skipping {plugin_id}: not in installed state")
                continue
            
            # Validate package
            if not self._validate_plugin_package(plugin_id):
                logger.warning(f"Skipping {plugin_id}: package validation failed")
                continue
            
            # Generate entry
            try:
                import_path = self._generate_import_path(plugin_id)
                component_name = self._generate_component_name(plugin_id)
                checksum = self._calculate_checksum(plugin_id)
                size_bytes = self._get_package_size(plugin_id)
                manifest_data = self._load_manifest_data(plugin_id)
                
                entry = RegistryEntry(
                    plugin_id=plugin_id,
                    import_path=import_path,
                    component_name=component_name,
                    checksum=checksum,
                    size_bytes=size_bytes,
                    generated_at=datetime.now(),
                    manifest_data=manifest_data
                )
                
                self.entries[plugin_id] = entry
                logger.info(f"Added {plugin_id} to registry")
                
            except Exception as e:
                logger.error(f"Failed to generate entry for {plugin_id}: {e}")
        
        # Generate TypeScript file
        self._generate_typescript_file()
        
        return {
            'total_entries': len(self.entries),
            'plugins': list(self.entries.keys()),
            'generated_at': datetime.now().isoformat(),
            'output_file': str(self.output_file)
        }

    def _generate_typescript_file(self) -> None:
        """Generate the TypeScript import map file (bundler-safe static module)."""
        try:
            lines: List[str] = []
            lines.append("/**")
            lines.append(" * Generated plugin import map (frontend).")
            lines.append(" *")
            lines.append(" * Single loading authority: `plugin_host/loader.ts` must import from here and")
            lines.append(" * resolve ONLY installed UI packages under `src/plugin_repo/<plugin-id>/`.")
            lines.append(" */")
            lines.append("import type React from 'react';")
            lines.append("")
            lines.append("export type PluginImporter = () => Promise<{")
            lines.append("  default: React.ComponentType<Record<string, unknown>>;")
            lines.append("}>;")
            lines.append("")
            lines.append("export type PluginImportMap = Record<string, PluginImporter>;")
            lines.append("")
            lines.append("export const PLUGIN_IMPORT_MAP: PluginImportMap = {")

            for plugin_id in sorted(self.entries.keys()):
                entry = self.entries[plugin_id]
                lines.append(
                    f"  {json.dumps(plugin_id)}: () => import({json.dumps(entry.import_path)}),"
                )

            lines.append("};")
            lines.append("")
            ts_content = "\n".join(lines)

            # Write to file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(ts_content)

            logger.info(f"Generated TypeScript file: {self.output_file}")

        except Exception as e:
            logger.error(f"Failed to generate TypeScript file: {e}")

    def get_import_map(self) -> Dict[str, str]:
        """Get the import map as a dictionary."""
        return {
            entry.plugin_id: entry.import_path
            for entry in self.entries.values()
        }

    def get_metadata(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a plugin."""
        if plugin_id not in self.entries:
            return None
        
        entry = self.entries[plugin_id]
        return {
            'plugin_id': entry.plugin_id,
            'component_name': entry.component_name,
            'checksum': entry.checksum,
            'size_bytes': entry.size_bytes,
            'manifest_data': entry.manifest_data,
            'generated_at': entry.generated_at.isoformat()
        }

    def get_plugin_list(self) -> List[str]:
        """Get list of all registered plugins."""
        return list(self.entries.keys())

    def is_plugin_registered(self, plugin_id: str) -> bool:
        """Check if a plugin is registered."""
        return plugin_id in self.entries

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_size = sum(entry.size_bytes for entry in self.entries.values())
        
        return {
            'total_plugins': len(self.entries),
            'total_size_bytes': total_size,
            'average_size_bytes': total_size / len(self.entries) if self.entries else 0,
            'registry_file': str(self.output_file),
            'last_generated': datetime.now().isoformat(),
            'plugins': list(self.entries.keys())
        }

    def remove_stale_entries(self) -> int:
        """Remove entries for plugins that no longer exist."""
        stale_count = 0
        
        # Check which entries are still valid
        valid_plugin_ids = set()
        for plugin_id in self.entries.keys():
            if self._validate_plugin_package(plugin_id):
                valid_plugin_ids.add(plugin_id)
            else:
                stale_count += 1
        
        # Remove stale entries
        stale_plugin_ids = set(self.entries.keys()) - valid_plugin_ids
        for plugin_id in stale_plugin_ids:
            del self.entries[plugin_id]
            logger.info(f"Removed stale entry for {plugin_id}")
        
        if stale_count > 0:
            self._save_registry()
            self._generate_typescript_file()
            logger.info(f"Removed {stale_count} stale entries from registry")
        
        return stale_count

    def refresh_registry(self) -> Dict[str, Any]:
        """Refresh the registry by removing stale entries and regenerating."""
        # Remove stale entries
        stale_count = self.remove_stale_entries()
        
        # Generate fresh registry
        result = self.generate_registry()
        
        return {
            **result,
            'stale_entries_removed': stale_count,
            'total_entries_after_refresh': len(self.entries)
        }


# Global registry instance
_registry: Optional[GeneratedImportRegistry] = None


def get_registry() -> GeneratedImportRegistry:
    """Get the global generated import registry instance."""
    global _registry
    if _registry is None:
        _registry = GeneratedImportRegistry()
    return _registry


def generate_registry() -> Dict[str, Any]:
    """Generate the import registry."""
    registry = get_registry()
    return registry.generate_registry()


def get_import_map() -> Dict[str, str]:
    """Get the import map."""
    registry = get_registry()
    return registry.get_import_map()


def get_plugin_metadata(plugin_id: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a plugin."""
    registry = get_registry()
    return registry.get_metadata(plugin_id)


def is_plugin_registered(plugin_id: str) -> bool:
    """Check if a plugin is registered."""
    registry = get_registry()
    return registry.is_plugin_registered(plugin_id)


def get_registry_stats() -> Dict[str, Any]:
    """Get registry statistics."""
    registry = get_registry()
    return registry.get_registry_stats()


def refresh_registry() -> Dict[str, Any]:
    """Refresh the registry."""
    registry = get_registry()
    return registry.refresh_registry()
