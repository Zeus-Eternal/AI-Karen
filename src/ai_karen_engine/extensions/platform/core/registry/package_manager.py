"""
Plugin Package Manager - Handles download, extraction, and file system operations for plugins.
"""

import asyncio
import hashlib
import logging
import os
import shutil
import tempfile
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse
import aiohttp
from datetime import datetime

from ai_karen_engine.extensions.platform.core.manifest import ExtensionManifest
from ai_karen_engine.extensions.platform.core.registry.database_service import get_database_service

logger = logging.getLogger("kari.plugin_package_manager")


class PluginPackageManager:
    """
    Handles all file system operations for plugin management including:
    - Downloading plugins from URLs
    - Extracting plugin packages
    - Installing plugins to filesystem
    - Removing plugins from filesystem
    - Creating and restoring backups
    - Validating plugin packages
    """

    def __init__(self, extensions_dir: str = "src/extensions"):
        self.extensions_dir = Path(extensions_dir)
        self.temp_dir = Path(tempfile.gettempdir()) / "kari_plugins"
        self.temp_dir.mkdir(exist_ok=True)
        self.database_service = get_database_service()

        # Supported archive formats
        self.supported_formats = {".tar.gz", ".tgz", ".zip", ".tar"}

    async def download_plugin_package(
        self, package_url: str, target_path: Optional[Path] = None, timeout: int = 300
    ) -> Path:
        """
        Download a plugin package from a URL.

        Args:
            package_url: URL to download plugin package from
            target_path: Target path for download (temp dir if None)
            timeout: Download timeout in seconds

        Returns:
            Path to downloaded file

        Raises:
            Exception if download fails or validation fails
        """
        logger.info(f"Downloading plugin package from: {package_url}")

        if target_path is None:
            target_path = self.temp_dir / f"plugin_{datetime.now().timestamp()}"

        try:
            # Create async HTTP client session
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as session:
                async with session.get(package_url) as response:
                    if response.status != 200:
                        raise Exception(
                            f"Download failed with status {response.status}"
                        )

                    # Get content length for progress logging
                    content_length = response.headers.get("content-length")
                    total_size = int(content_length) if content_length else None

                    # Download file
                    downloaded_path = target_path.with_suffix(".download")
                    downloaded_bytes = 0

                    with open(downloaded_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded_bytes += len(chunk)

                            # Log progress for large downloads
                            if (
                                total_size and downloaded_bytes % (1024 * 1024) == 0
                            ):  # Every MB
                                progress = (downloaded_bytes / total_size) * 100
                                logger.info(f"Download progress: {progress:.1f}%")

                    # Rename to final file
                    final_path = target_path.with_suffix(
                        self._get_extension_from_url(package_url)
                    )
                    downloaded_path.rename(final_path)

                    logger.info(f"Plugin package downloaded to: {final_path}")
                    return final_path

        except Exception as e:
            logger.error(f"Failed to download plugin package: {e}")
            # Clean up partial download
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            raise

    def _get_extension_from_url(self, url: str) -> str:
        """Extract file extension from URL."""
        parsed = urlparse(url)
        path = parsed.path
        for ext in self.supported_formats:
            if path.endswith(ext):
                return ext
        return ".zip"  # Default to zip

    async def extract_plugin_package(
        self, package_path: Path, extract_to: Optional[Path] = None
    ) -> Path:
        """
        Extract a plugin package to a directory.

        Args:
            package_path: Path to plugin package
            extract_to: Target extraction directory (temp dir if None)

        Returns:
            Path to extracted directory

        Raises:
            Exception if extraction fails
        """
        logger.info(f"Extracting plugin package: {package_path}")

        if extract_to is None:
            extract_to = self.temp_dir / f"extracted_{datetime.now().timestamp()}"

        extract_to.mkdir(parents=True, exist_ok=True)

        try:
            if package_path.suffix in [".zip", ".zip"]:
                # Handle ZIP files
                with zipfile.ZipFile(package_path, "r") as zip_ref:
                    zip_ref.extractall(extract_to)

            elif package_path.suffix in [".tar.gz", ".tgz", ".tar"]:
                # Handle TAR files
                with tarfile.open(package_path, "r:*") as tar_ref:
                    tar_ref.extractall(extract_to)
            else:
                raise Exception(f"Unsupported package format: {package_path.suffix}")

            logger.info(f"Plugin package extracted to: {extract_to}")
            return extract_to

        except Exception as e:
            logger.error(f"Failed to extract plugin package: {e}")
            # Clean up partial extraction
            if extract_to.exists():
                shutil.rmtree(extract_to, ignore_errors=True)
            raise

    async def validate_plugin_package(
        self, extracted_dir: Path
    ) -> Tuple[bool, List[str], Optional[ExtensionManifest]]:
        """
        Validate a plugin package structure and manifest.

        Args:
            extracted_dir: Path to extracted plugin directory

        Returns:
            Tuple of (is_valid, validation_errors, manifest)
        """
        logger.info(f"Validating plugin package: {extracted_dir}")

        validation_errors = []
        manifest = None

        try:
            # Check if manifest exists
            manifest_path = extracted_dir / "manifest.json"
            if not manifest_path.exists():
                validation_errors.append("manifest.json not found")
                return False, validation_errors, None

            # Load and parse manifest
            import json

            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)

            # Create ExtensionManifest object
            manifest = ExtensionManifest.from_dict(manifest_data)

            # Validate manifest structure
            if not manifest.name:
                validation_errors.append("Plugin name is required")

            if not manifest.version:
                validation_errors.append("Plugin version is required")

            if not manifest.display_name:
                validation_errors.append("Plugin display name is required")

            # Check for required files based on capabilities
            if manifest.capabilities.provides_ui:
                ui_files = ["ui.html", "ui.js", "ui.css"]
                for ui_file in ui_files:
                    ui_path = extracted_dir / ui_file
                    if not ui_path.exists():
                        logger.warning(f"Optional UI file not found: {ui_file}")

            # Check for entry point if specified
            if manifest.module:
                module_path = extracted_dir / manifest.module.replace(".", "/") + ".py"
                if not module_path.exists():
                    validation_errors.append(
                        f"Module file not found: {manifest.module}"
                    )

            # Calculate package hash for security
            package_hash = await self._calculate_package_hash(extracted_dir)
            logger.info(f"Package hash: {package_hash}")

            is_valid = len(validation_errors) == 0

            return is_valid, validation_errors, manifest

        except Exception as e:
            validation_errors.append(f"Validation error: {str(e)}")
            return False, validation_errors, None

    async def _calculate_package_hash(self, package_dir: Path) -> str:
        """Calculate SHA256 hash of plugin package for security validation."""
        hash_sha256 = hashlib.sha256()

        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in [".py", ".json", ".html", ".js", ".css", ".md"]:
                    with open(file_path, "rb") as f:
                        hash_sha256.update(f.read())

        return hash_sha256.hexdigest()

    async def install_plugin_to_filesystem(
        self,
        extracted_dir: Path,
        manifest: ExtensionManifest,
        target_extensions_dir: Optional[Path] = None,
    ) -> Path:
        """
        Install a validated plugin to the extensions directory.

        Args:
            extracted_dir: Path to extracted plugin directory
            manifest: Plugin manifest
            target_extensions_dir: Target extensions directory (default if None)

        Returns:
            Path to installed plugin directory

        Raises:
            Exception if installation fails
        """
        if target_extensions_dir is None:
            target_extensions_dir = self.extensions_dir

        target_plugin_dir = target_extensions_dir / manifest.name

        logger.info(f"Installing plugin to: {target_plugin_dir}")

        try:
            # Remove existing installation if it exists
            if target_plugin_dir.exists():
                logger.info(f"Removing existing installation: {target_plugin_dir}")
                shutil.rmtree(target_plugin_dir, ignore_errors=True)

            # Copy plugin files
            shutil.copytree(extracted_dir, target_plugin_dir)

            # Ensure proper permissions
            for root, dirs, files in os.walk(target_plugin_dir):
                for file in files:
                    file_path = Path(root) / file
                    file_path.chmod(0o644)  # Read/write for owner, read for others

                for dir in dirs:
                    dir_path = Path(root) / dir
                    dir_path.chmod(
                        0o755
                    )  # Read/write/execute for owner, read/execute for others

            logger.info(f"Plugin installed successfully to: {target_plugin_dir}")
            return target_plugin_dir

        except Exception as e:
            logger.error(f"Failed to install plugin: {e}")
            # Clean up partial installation
            if target_plugin_dir.exists():
                shutil.rmtree(target_plugin_dir, ignore_errors=True)
            raise

    async def create_plugin_backup(
        self, plugin_name: str, backup_dir: Optional[Path] = None
    ) -> Path:
        """
        Create a backup of an installed plugin.

        Args:
            plugin_name: Name of plugin to backup
            backup_dir: Directory to store backup (default if None)

        Returns:
            Path to backup file

        Raises:
            Exception if backup creation fails
        """
        if backup_dir is None:
            backup_dir = self.extensions_dir / "backups"

        backup_dir.mkdir(parents=True, exist_ok=True)

        plugin_dir = self.extensions_dir / plugin_name
        if not plugin_dir.exists():
            raise Exception(f"Plugin directory not found: {plugin_dir}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"{plugin_name}_{timestamp}.tar.gz"

        logger.info(f"Creating backup: {backup_file}")

        try:
            # Create tar.gz backup
            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(plugin_dir, arcname=plugin_name)

            logger.info(f"Backup created successfully: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            # Clean up partial backup
            if backup_file.exists():
                backup_file.unlink(missing_ok=True)
            raise

    async def restore_plugin_from_backup(
        self,
        backup_file: Path,
        target_plugin_name: Optional[str] = None,
        target_extensions_dir: Optional[Path] = None,
    ) -> Path:
        """
        Restore a plugin from a backup file.

        Args:
            backup_file: Path to backup file
            target_plugin_name: Target plugin name (extract from backup if None)
            target_extensions_dir: Target extensions directory (default if None)

        Returns:
            Path to restored plugin directory

        Raises:
            Exception if restoration fails
        """
        if target_extensions_dir is None:
            target_extensions_dir = self.extensions_dir

        logger.info(f"Restoring plugin from backup: {backup_file}")

        try:
            # Extract backup to temp directory
            temp_extract = self.temp_dir / f"restore_{datetime.now().timestamp()}"
            await self.extract_plugin_package(backup_file, temp_extract)

            # Find plugin directory in backup
            plugin_dirs = [d for d in temp_extract.iterdir() if d.is_dir()]
            if not plugin_dirs:
                raise Exception("No plugin directory found in backup")

            source_plugin_dir = plugin_dirs[0]  # Use first directory found

            # Determine target plugin name
            if target_plugin_name is None:
                target_plugin_name = source_plugin_dir.name

            target_plugin_dir = target_extensions_dir / target_plugin_name

            # Remove existing installation
            if target_plugin_dir.exists():
                shutil.rmtree(target_plugin_dir, ignore_errors=True)

            # Copy plugin files
            shutil.copytree(source_plugin_dir, target_plugin_dir)

            # Clean up temp directory
            shutil.rmtree(temp_extract, ignore_errors=True)

            logger.info(f"Plugin restored successfully to: {target_plugin_dir}")
            return target_plugin_dir

        except Exception as e:
            logger.error(f"Failed to restore plugin: {e}")
            raise

    async def remove_plugin_from_filesystem(
        self,
        plugin_name: str,
        create_backup: bool = True,
        backup_dir: Optional[Path] = None,
    ) -> bool:
        """
        Remove a plugin from the filesystem.

        Args:
            plugin_name: Name of plugin to remove
            create_backup: Create backup before removal
            backup_dir: Directory for backup (default if None)

        Returns:
            True if removal was successful

        Raises:
            Exception if removal fails
        """
        plugin_dir = self.extensions_dir / plugin_name

        logger.info(f"Removing plugin from filesystem: {plugin_dir}")

        try:
            if not plugin_dir.exists():
                logger.warning(f"Plugin directory not found: {plugin_dir}")
                return True

            # Create backup if requested
            backup_file = None
            if create_backup:
                try:
                    backup_file = await self.create_plugin_backup(
                        plugin_name, backup_dir
                    )
                    logger.info(f"Backup created before removal: {backup_file}")
                except Exception as e:
                    logger.warning(f"Failed to create backup: {e}")

            # Remove plugin directory
            shutil.rmtree(plugin_dir, ignore_errors=True)

            logger.info(f"Plugin removed successfully: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove plugin: {e}")
            raise

    async def cleanup_temp_files(self):
        """Clean up temporary files and directories."""
        logger.info("Cleaning up temporary files")

        try:
            # Clean temp directory
            if self.temp_dir.exists():
                for item in self.temp_dir.iterdir():
                    if item.is_file():
                        item.unlink(missing_ok=True)
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)

            logger.info("Temporary files cleaned up")

        except Exception as e:
            logger.warning(f"Failed to cleanup temp files: {e}")

    async def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get information about an installed plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            Dictionary with plugin information
        """
        plugin_dir = self.extensions_dir / plugin_name

        if not plugin_dir.exists():
            return {"exists": False}

        try:
            # Load manifest
            manifest_path = plugin_dir / "manifest.json"
            manifest_data = {}

            if manifest_path.exists():
                import json

                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)

            # Get directory info
            files = []
            total_size = 0

            for root, dirs, file_names in os.walk(plugin_dir):
                for file_name in file_names:
                    file_path = Path(root) / file_name
                    rel_path = file_path.relative_to(plugin_dir)
                    files.append(
                        {
                            "path": str(rel_path),
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat(),
                        }
                    )
                    total_size += file_path.stat().st_size

            return {
                "exists": True,
                "directory": str(plugin_dir),
                "manifest": manifest_data,
                "file_count": len(files),
                "total_size_bytes": total_size,
                "files": files,
                "created": datetime.fromtimestamp(
                    plugin_dir.stat().st_ctime
                ).isoformat(),
                "modified": datetime.fromtimestamp(
                    plugin_dir.stat().st_mtime
                ).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get plugin info: {e}")
            return {"exists": True, "error": str(e)}


# Singleton instance
_package_manager: Optional[PluginPackageManager] = None


def get_package_manager(extensions_dir: str = "src/extensions") -> PluginPackageManager:
    """Get the singleton plugin package manager instance."""
    global _package_manager
    if _package_manager is None:
        _package_manager = PluginPackageManager(extensions_dir=extensions_dir)
    return _package_manager
