"""
Extension manager for discovery, loading, lifecycle, hooks, health, and marketplace ops.
Production-hardened: strict logging, safe hooks, dependency resolution, resource monitoring.
"""

from __future__ import annotations

import asyncio
import importlib.util
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from ai_karen_engine.plugins.router import PluginRouter

from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.hooks.hook_mixin import HookMixin
from ai_karen_engine.hooks.hook_types import HookTypes
from ai_karen_engine.extensions.models import (
    ExtensionContext,
    ExtensionManifest,
    ExtensionRecord,
    ExtensionStatus,
)
from ai_karen_engine.extensions.registry import ExtensionRegistry
from ai_karen_engine.extensions.validator import ExtensionValidator
from ai_karen_engine.extensions.dependency_resolver import (
    DependencyResolver,
    DependencyError,
)
from ai_karen_engine.extensions.resource_monitor import (
    ResourceMonitor,
    ExtensionHealthChecker,
    HealthStatus,
)
from ai_karen_engine.event_bus import get_event_bus
from ai_karen_engine.extensions.marketplace_client import MarketplaceClient
from ai_karen_engine.database.client import get_db_session_context
from ai_karen_engine.services.usage_service import UsageService
from ai_karen_engine.database.models import (
    Extension,
    InstalledExtension,
    MarketplaceExtension,
)
from pydantic import ValidationError as PydanticValidationError


class ExtensionManager(HookMixin):
    """
    Manages extension discovery, loading, lifecycle, hooks, health, and installation.
    """

    def __init__(
        self,
        extension_root: Path,
        plugin_router: PluginRouter,
        db_session: Any = None,
        app_instance: Any = None,
        marketplace_client: Optional[MarketplaceClient] = None,
    ):
        """
        Initialize the extension manager.

        Args:
            extension_root: Root directory containing extensions (flat or categorized).
            plugin_router: Plugin router instance for orchestration.
            db_session: Optional DB session.
            app_instance: Optional FastAPI app instance for API injection.
            marketplace_client: Optional marketplace client for remote installs.
        """
        super().__init__()
        self.extension_root = Path(extension_root)
        self.plugin_router = plugin_router
        self.db_session = db_session
        self.app_instance = app_instance
        self.marketplace_client = marketplace_client or MarketplaceClient()
        self.name = "extension_manager"

        self.registry = ExtensionRegistry()
        self.validator = ExtensionValidator()
        self.dependency_resolver = DependencyResolver()
        self.resource_monitor = ResourceMonitor()
        self.health_checker = ExtensionHealthChecker(self.resource_monitor)
        self.logger = logging.getLogger("extension.manager")

        # Ensure extension root exists
        self.extension_root.mkdir(parents=True, exist_ok=True)
        self.logger.info("Extension manager initialized at %s", self.extension_root)

    # -------------------------
    # Discovery
    # -------------------------
    async def discover_extensions(self) -> Dict[str, ExtensionManifest]:
        """
        Scan extension directory and load manifests from all categories.

        Returns:
            Dict[str, ExtensionManifest]: mapping extension name -> manifest
        """
        manifests: Dict[str, ExtensionManifest] = {}
        self.logger.info("Discovering extensions in %s", self.extension_root)
        try:
            await self._scan_directory_for_extensions(self.extension_root, manifests)
        except Exception as e:
            self.logger.error("Failed to scan extension directory: %s", e, exc_info=True)

        self.logger.info("Discovered %d extensions", len(manifests))
        return manifests

    async def _scan_directory_for_extensions(
        self, directory: Path, manifests: Dict[str, ExtensionManifest]
    ) -> None:
        """
        Recursively scan a directory for extensions (flat or categorized layouts).
        """
        try:
            for item in directory.iterdir():
                if not item.is_dir():
                    continue
                # Skip metadata dirs
                if item.name.startswith("__") or item.name.startswith("."):
                    continue

                manifest_path = item / "extension.json"
                if manifest_path.exists():
                    await self._load_extension_manifest(item, manifest_path, manifests)
                else:
                    # Dive deeper (category)
                    await self._scan_directory_for_extensions(item, manifests)
        except Exception as e:
            self.logger.error("Failed to scan directory %s: %s", directory, e, exc_info=True)

    async def _load_extension_manifest(
        self, extension_dir: Path, manifest_path: Path, manifests: Dict[str, ExtensionManifest]
    ) -> None:
        """
        Load and validate a manifest, populate in `manifests` if valid.
        """
        try:
            manifest = ExtensionManifest.from_file(manifest_path)
        except PydanticValidationError as e:
            errors = [".".join(str(p) for p in err["loc"]) + ": " + err["msg"] for err in e.errors()]
            self.logger.error(
                "Invalid manifest for %s: %s", extension_dir.name, "; ".join(errors)
            )
            return
        except Exception as e:
            self.logger.error(
                "Failed to load manifest from %s: %s", manifest_path, e, exc_info=True
            )
            return

        # Use enhanced validation with unified patterns and new API compatibility
        is_valid, errors, warnings, field_errors = self.validator.validate_manifest_enhanced(manifest)

        if not is_valid:
            self.logger.error(
                "Invalid manifest for %s: %s", extension_dir.name, "; ".join(errors)
            )
            return

        if warnings:
            self.logger.warning(
                "Manifest warnings for %s: %s", extension_dir.name, "; ".join(warnings)
            )

        if field_errors:
            self.logger.warning(
                "Manifest field errors for %s: %s",
                extension_dir.name,
                "; ".join(str(fe.dict() if hasattr(fe, 'dict') else str(fe)) for fe in field_errors)
            )
            
        # Log validation report for comprehensive feedback
        validation_report = self.validator.get_validation_report(manifest)
        if validation_report.get("recommendations"):
            self.logger.info(
                "Extension %s recommendations: %s",
                extension_dir.name,
                "; ".join(validation_report["recommendations"])
            )
        
        # Check endpoint compatibility with unified API
        try:
            from ai_karen_engine.extensions.endpoint_adapter import ExtensionEndpointAdapter
            endpoint_adapter = ExtensionEndpointAdapter()
            compatibility = endpoint_adapter.validate_endpoint_compatibility(manifest)
            
            if not compatibility["is_compatible"]:
                self.logger.warning(
                    "Extension %s has API compatibility issues: %s",
                    extension_dir.name,
                    "; ".join(compatibility["issues"])
                )
            
            if compatibility["warnings"]:
                self.logger.info(
                    "Extension %s API warnings: %s",
                    extension_dir.name,
                    "; ".join(compatibility["warnings"])
                )
                
        except ImportError:
            # Endpoint adapter not available - skip compatibility check
            pass

        manifests[manifest.name] = manifest
        self.logger.info(
            "Discovered extension: %s v%s at %s",
            manifest.name,
            manifest.version,
            extension_dir,
        )

    # -------------------------
    # Loading / Unloading
    # -------------------------
    async def load_extension(self, name: str) -> ExtensionRecord:
        """
        Load and initialize an extension by name.
        """
        self.logger.info("Loading extension: %s", name)
        try:
            extension_dir = await self._find_extension_directory(name)
            if not extension_dir:
                raise RuntimeError(f"Extension directory not found for: {name}")

            manifest_path = extension_dir / "extension.json"
            if not manifest_path.exists():
                raise RuntimeError(f"Extension manifest not found: {manifest_path}")

            manifest = ExtensionManifest.from_file(manifest_path)

            dependency_status = self.registry.check_dependencies(manifest)
            missing = [dep for dep, ok in dependency_status.items() if not ok]
            if missing:
                raise RuntimeError(f"Missing dependencies: {missing}")

            extension_instance = await self._load_extension_module(extension_dir, manifest)
            record = self.registry.register_extension(manifest, extension_instance, str(extension_dir))

            # Build a context (extensions can read it on initialize)
            _ = ExtensionContext(
                plugin_router=self.plugin_router,
                db_session=self.db_session,
                app_instance=self.app_instance,
            )

            try:
                await extension_instance.initialize()
                self.registry.update_status(name, ExtensionStatus.ACTIVE)

                # Monitoring
                self.resource_monitor.register_extension(record)

                # Hooks: loaded
                await self.trigger_hook_safe(
                    HookTypes.EXTENSION_LOADED,
                    {
                        "extension_name": name,
                        "extension_version": manifest.version,
                        "extension_manifest": manifest.dict(),
                        "extension_directory": str(extension_dir),
                        "extension_category": getattr(manifest, "category", None),
                        "extension_capabilities": getattr(manifest, "capabilities", None)
                        and manifest.capabilities.dict(),
                        "resource_usage": self.resource_monitor.get_extension_usage(name),
                    },
                )

                # Hooks: activated
                await self.trigger_hook_safe(
                    HookTypes.EXTENSION_ACTIVATED,
                    {
                        "extension_name": name,
                        "extension_version": manifest.version,
                        "extension_instance": extension_instance,
                        "extension_manifest": manifest.dict(),
                        "activation_timestamp": record.loaded_at.isoformat()
                        if record.loaded_at
                        else None,
                        "has_mcp_server": bool(
                            hasattr(extension_instance, "_mcp_server")
                            and extension_instance._mcp_server is not None
                        ),
                        "has_api_router": bool(
                            hasattr(extension_instance, "_api_router")
                            and extension_instance._api_router is not None
                        ),
                    },
                )

                # Event bus
                try:
                    bus = get_event_bus()
                    bus.publish(
                        "extensions",
                        "loaded",
                        {"name": name, "version": manifest.version},
                        roles=["admin"],
                    )
                except Exception as exc:  # pragma: no cover - optional
                    self.logger.debug("Event publish failed: %s", exc)

                self.logger.info("Extension %s loaded and initialized", name)

                # Persist extension metadata
                try:
                    with get_db_session_context() as session:
                        caps = getattr(manifest, "capabilities", None)
                        caps_dict = caps.dict() if hasattr(caps, "dict") else caps
                        session.merge(
                            Extension(
                                name=manifest.name,
                                version=manifest.version,
                                category=getattr(manifest, "category", None),
                                capabilities=caps_dict,
                                directory=str(extension_dir),
                                status=record.status.value,
                                error_msg=record.error_message,
                                loaded_at=datetime.utcnow(),
                                updated_at=datetime.utcnow(),
                            )
                        )
                        session.commit()
                except Exception as db_error:
                    self.logger.debug(
                        "Failed to persist extension %s: %s", name, db_error
                    )

            except Exception as e:
                self.registry.update_status(name, ExtensionStatus.ERROR, str(e))
                raise RuntimeError(f"Extension initialization failed: {e}") from e

            return record

        except Exception as e:
            self.logger.error("Failed to load extension %s: %s", name, e, exc_info=True)
            # If partially registered, mark error
            try:
                self.registry.update_status(name, ExtensionStatus.ERROR, str(e))
            except Exception:
                pass
            raise

    async def unload_extension(self, name: str) -> None:
        """
        Safely unload an extension and cleanup resources.
        """
        self.logger.info("Unloading extension: %s", name)
        try:
            record = self.registry.get_extension(name)
            if not record:
                raise RuntimeError(f"Extension {name} not found in registry")

            self.registry.update_status(name, ExtensionStatus.UNLOADING)

            # Hook: deactivated
            await self.trigger_hook_safe(
                HookTypes.EXTENSION_DEACTIVATED,
                {
                    "extension_name": name,
                    "extension_version": record.manifest.version,
                    "extension_instance": record.instance,
                    "extension_manifest": record.manifest.dict(),
                    "deactivation_reason": "manual_unload",
                    "resource_usage_final": self.resource_monitor.get_extension_usage(name),
                    "uptime_seconds": 0,  # record.loaded_at can be used to compute uptime if needed
                },
            )

            # Graceful shutdown
            if record.instance and hasattr(record.instance, "shutdown"):
                try:
                    await record.instance.shutdown()
                except Exception as e:
                    self.logger.error("Error during extension shutdown: %s", e, exc_info=True)

            # Stop monitoring
            self.resource_monitor.unregister_extension(name)

            # Hook: unloaded
            await self.trigger_hook_safe(
                HookTypes.EXTENSION_UNLOADED,
                {
                    "extension_name": name,
                    "extension_version": record.manifest.version,
                    "extension_directory": str(record.directory),
                    "extension_manifest": record.manifest.dict(),
                    "unload_timestamp": record.loaded_at.isoformat() if record.loaded_at else None,
                    "cleanup_successful": True,
                },
            )

            # Unregister
            self.registry.unregister_extension(name)

            # Event bus
            try:
                bus = get_event_bus()
                bus.publish("extensions", "unloaded", {"name": name}, roles=["admin"])
            except Exception as exc:  # pragma: no cover - optional
                self.logger.debug("Event publish failed: %s", exc)

            self.logger.info("Extension %s unloaded", name)

            # Update persistence
            try:
                with get_db_session_context() as session:
                    ext = session.get(Extension, name)
                    if ext:
                        ext.status = ExtensionStatus.INACTIVE.value
                        ext.error_msg = None
                        ext.updated_at = datetime.utcnow()
                        session.commit()
            except Exception as db_error:
                self.logger.debug(
                    "Failed to update extension %s: %s", name, db_error
                )

        except Exception as e:
            self.logger.error("Failed to unload extension %s: %s", name, e, exc_info=True)
            self.registry.update_status(name, ExtensionStatus.ERROR, str(e))
            raise

    async def reload_extension(self, name: str) -> ExtensionRecord:
        """
        Reload an extension (dev-time convenience).
        """
        self.logger.info("Reloading extension: %s", name)
        if self.registry.get_extension(name):
            await self.unload_extension(name)
        record = await self.load_extension(name)
        try:
            bus = get_event_bus()
            bus.publish("extensions", "reloaded", {"name": name}, roles=["admin"])
        except Exception as exc:  # pragma: no cover - optional
            self.logger.debug("Event publish failed: %s", exc)
        return record

    # -------------------------
    # Status / Health / Usage
    # -------------------------
    def get_extension_status(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get current status and health of an extension.
        """
        record = self.registry.get_extension(name)
        if not record:
            return None

        status: Dict[str, Any] = {
            "name": record.manifest.name,
            "version": record.manifest.version,
            "status": record.status.value,
            "loaded_at": record.loaded_at,
            "error_message": record.error_message,
            "directory": str(record.directory),
        }

        if record.instance and hasattr(record.instance, "get_status"):
            try:
                instance_status = record.instance.get_status()
                if isinstance(instance_status, dict):
                    status.update(instance_status)
            except Exception as e:
                self.logger.error("Failed to get instance status for %s: %s", name, e)

        return status

    async def load_all_extensions(self) -> Dict[str, ExtensionRecord]:
        """
        Discover and load all available extensions with dependency resolution.
        """
        self.logger.info("Loading all extensions")
        manifests = await self.discover_extensions()
        if not manifests:
            self.logger.info("No extensions found to load")
            return {}

        loaded: Dict[str, ExtensionRecord] = {}

        try:
            loading_order = self.dependency_resolver.resolve_loading_order(manifests)

            compatibility_warnings = self.dependency_resolver.check_version_compatibility(
                manifests
            )
            for warning in compatibility_warnings:
                self.logger.warning("Version compatibility: %s", warning)

            for idx, name in enumerate(loading_order, start=1):
                if name not in manifests:
                    self.logger.warning(
                        "Extension %s in loading order but not discovered", name
                    )
                    continue
                try:
                    self.logger.info(
                        "Loading extension %s (%d/%d)", name, idx, len(manifests)
                    )
                    record = await self.load_extension(name)
                    loaded[name] = record
                except Exception as e:
                    self.logger.error("Failed to load extension %s: %s", name, e, exc_info=True)
                    continue

        except DependencyError as e:
            self.logger.error("Dependency resolution failed: %s", e, exc_info=True)
            self.logger.info("Attempting best-effort load without resolution")
            for name in manifests:
                if name in loaded:
                    continue
                try:
                    record = await self.load_extension(name)
                    loaded[name] = record
                except Exception as load_error:
                    self.logger.error(
                        "Failed to load extension %s: %s", name, load_error, exc_info=True
                    )
                    continue

        self.logger.info("Loaded %d of %d discovered extensions", len(loaded), len(manifests))
        return loaded

    async def _load_extension_module(
        self, extension_dir: Path, manifest: ExtensionManifest
    ) -> BaseExtension:
        """
        Load the extension Python module and create instance.
        """
        try:
            init_file = extension_dir / "__init__.py"
            if not init_file.exists():
                raise RuntimeError(f"Extension __init__.py not found: {init_file}")

            module_name = f"extension_{manifest.name}"
            spec = importlib.util.spec_from_file_location(module_name, init_file)
            if not spec or not spec.loader:
                raise RuntimeError(f"Failed to create module spec for {init_file}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)  # type: ignore[attr-defined]

            class_name = self._get_extension_class_name(manifest.name)
            if hasattr(module, class_name):
                extension_class = getattr(module, class_name)
            else:
                # Fallback: first subclass of BaseExtension
                candidates = [
                    getattr(module, attr)
                    for attr in dir(module)
                    if isinstance(getattr(module, attr), type)
                    and issubclass(getattr(module, attr), BaseExtension)
                    and getattr(module, attr) != BaseExtension
                ]
                if not candidates:
                    raise RuntimeError(f"No extension class found in {init_file}")
                extension_class = candidates[0]

            context = ExtensionContext(
                plugin_router=self.plugin_router,
                db_session=self.db_session,
                app_instance=self.app_instance,
            )

            instance = extension_class(manifest, context)
            if not isinstance(instance, BaseExtension):
                raise RuntimeError(
                    f"Loaded extension instance does not inherit BaseExtension: {manifest.name}"
                )
            return instance

        except Exception as e:
            self.logger.error("Failed to load extension module: %s", e, exc_info=True)
            raise RuntimeError(f"Module loading failed: {e}") from e

    def _get_extension_class_name(self, extension_name: str) -> str:
        """
        Convert kebab/underscore to PascalCase + 'Extension' suffix.
        """
        words = extension_name.replace("-", "_").split("_")
        base_name = "".join(word.capitalize() for word in words)
        if base_name.lower().endswith("extension"):
            return base_name
        return base_name + "Extension"

    # -------------------------
    # Registry getters
    # -------------------------
    def get_registry(self) -> ExtensionRegistry:
        return self.registry

    def get_loaded_extensions(self) -> List[ExtensionRecord]:
        return self.registry.get_active_extensions()

    def get_extension_by_name(self, name: str) -> Optional[ExtensionRecord]:
        return self.registry.get_extension(name)

    # -------------------------
    # Install / Update / Enable / Disable / Remove
    # -------------------------
    async def install_extension(
        self,
        extension_id: str,
        version: str,
        source: str = "local",
        path: Optional[str] = None,
        user_id: Optional[str] = None,
        action: str = "install",
    ) -> bool:
        """Install an extension from local path or marketplace and record the event."""
        self.logger.info("Installing extension %s from %s", extension_id, source)
        dest = self.extension_root / extension_id
        try:
            if source == "local":
                if not path:
                    raise ValueError("path required for local install")
                src = Path(path)
                if dest.exists():
                    self.logger.warning("Extension already installed: %s", extension_id)
                    return False
                shutil.copytree(src, dest)
            else:
                await self.marketplace_client.download_extension(
                    extension_id, version, self.extension_root
                )

            try:
                with get_db_session_context() as session:
                    mp = session.get(MarketplaceExtension, extension_id)
                    if not mp:
                        mp = MarketplaceExtension(
                            extension_id=extension_id, latest_version=version
                        )
                        session.add(mp)
                    else:
                        mp.latest_version = version
                        mp.updated_at = datetime.utcnow()

                    installed = (
                        session.query(InstalledExtension)
                        .filter_by(extension_id=extension_id)
                        .one_or_none()
                    )
                    if installed:
                        installed.version = version
                        installed.installed_by = user_id
                        installed.installed_at = datetime.utcnow()
                        installed.source = source
                        installed.directory = str(dest)
                    else:
                        session.add(
                            InstalledExtension(
                                extension_id=extension_id,
                                version=version,
                                installed_by=user_id,
                                installed_at=datetime.utcnow(),
                                source=source,
                                directory=str(dest),
                            )
                        )

                    # ExtensionInstallEvent model not available - skipping install event logging
                    session.commit()
            except Exception as db_error:  # pragma: no cover - optional DB
                self.logger.debug(
                    "Failed to record installation for %s: %s", extension_id, db_error
                )

            return True
        except Exception as e:
            self.logger.error(
                "Failed to install extension %s: %s", extension_id, e, exc_info=True
            )
            return False

    async def update_extension(
        self,
        name: str,
        version: str,
        source: str = "local",
        path: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Update an installed extension (remove + install)."""
        await self.remove_extension(name, user_id=user_id)
        return await self.install_extension(
            name, version, source, path, user_id=user_id, action="upgrade"
        )

    async def enable_extension(self, name: str) -> Optional[ExtensionRecord]:
        """
        Enable and load an extension (idempotent).
        """
        if self.registry.get_extension(name):
            return self.registry.get_extension(name)
        return await self.load_extension(name)

    async def disable_extension(self, name: str) -> None:
        """
        Disable (unload) an extension (idempotent).
        """
        if self.registry.get_extension(name):
            await self.unload_extension(name)

    async def remove_extension(self, name: str, user_id: Optional[str] = None) -> bool:
        """Remove an extension from disk and registry."""
        try:
            if self.registry.get_extension(name):
                await self.unload_extension(name)
            ext_dir = await self._find_extension_directory(name)
            if ext_dir and ext_dir.exists():
                shutil.rmtree(ext_dir)

            try:
                with get_db_session_context() as session:
                    installed = (
                        session.query(InstalledExtension)
                        .filter_by(extension_id=name)
                        .one_or_none()
                    )
                    version = installed.version if installed else None
                    if installed:
                        session.delete(installed)
                    # ExtensionInstallEvent model not available - skipping removal event logging
                    session.commit()
            except Exception as db_error:  # pragma: no cover - optional DB
                self.logger.debug(
                    "Failed to record removal for %s: %s", name, db_error
                )

            return True
        except Exception as e:
            self.logger.error("Failed to remove extension %s: %s", name, e, exc_info=True)
            return False

    # -------------------------
    # Monitoring / Health
    # -------------------------
    async def start_monitoring(self) -> None:
        await self.resource_monitor.start_monitoring()
        self.logger.info("Extension resource monitoring started")

    async def stop_monitoring(self) -> None:
        await self.resource_monitor.stop_monitoring()
        self.logger.info("Extension resource monitoring stopped")

    async def check_extension_health(self, name: str) -> HealthStatus:
        record = self.registry.get_extension(name)
        if not record:
            return HealthStatus.RED
        return await self.health_checker.check_extension_health(record)

    async def check_all_extensions_health(self) -> Dict[str, HealthStatus]:
        loaded = {r.manifest.name: r for r in self.registry.get_active_extensions()}
        return await self.health_checker.check_all_extensions_health(loaded)

    def get_extension_resource_usage(self, name: str) -> Optional[Dict[str, Any]]:
        usage = self.resource_monitor.get_extension_usage(name)
        if not usage:
            return None
        return {
            "memory_mb": usage.memory_mb,
            "cpu_percent": usage.cpu_percent,
            "disk_mb": usage.disk_mb,
            "network_bytes_sent": usage.network_bytes_sent,
            "network_bytes_recv": usage.network_bytes_recv,
            "uptime_seconds": usage.uptime_seconds,
        }

    def get_all_resource_usage(self) -> Dict[str, Dict[str, Any]]:
        all_usage = self.resource_monitor.get_all_usage()
        return {
            name: {
                "memory_mb": u.memory_mb,
                "cpu_percent": u.cpu_percent,
                "disk_mb": u.disk_mb,
                "network_bytes_sent": u.network_bytes_sent,
                "network_bytes_recv": u.network_bytes_recv,
                "uptime_seconds": u.uptime_seconds,
            }
            for name, u in all_usage.items()
        }

    def get_health_summary(self) -> Dict[str, Any]:
        return self.health_checker.get_health_summary()

    # -------------------------
    # Hook stats / triggers
    # -------------------------
    async def get_extension_hook_stats(self, name: str) -> Dict[str, Any]:
        record = self.registry.get_extension(name)
        if not record or not record.instance:
            return {"error": "Extension not found or not loaded"}

        if hasattr(record.instance, "get_hook_stats"):
            try:
                return record.instance.get_hook_stats()
            except Exception as e:
                self.logger.error("Failed to get hook stats for %s: %s", name, e)
                return {"error": str(e)}

        return {"hooks_enabled": False, "message": "Extension does not support hooks"}

    async def get_all_extension_hook_stats(self) -> Dict[str, Dict[str, Any]]:
        stats: Dict[str, Dict[str, Any]] = {}
        for record in self.registry.get_active_extensions():
            stats[record.manifest.name] = await self.get_extension_hook_stats(
                record.manifest.name
            )
        return stats

    async def trigger_extension_hook(
        self,
        extension_name: str,
        hook_type: str,
        data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Trigger a hook on a specific extension.
        """
        record = self.registry.get_extension(extension_name)
        if not record or not record.instance:
            return {"error": f"Extension {extension_name} not found or not loaded"}

        try:
            if hasattr(record.instance, "handle_hook"):
                result = await record.instance.handle_hook(hook_type, data, user_context)

                # Global hook event
                await self.trigger_hook_safe(
                    HookTypes.EXTENSION_ACTIVATED if hook_type == "activate" else hook_type,
                    {
                        "extension_name": extension_name,
                        "hook_type": hook_type,
                        "hook_data": data,
                        "hook_result": result,
                        "user_context": user_context,
                    },
                )
                return {"success": True, "result": result}
            else:
                return {"error": f"Extension {extension_name} does not support hook handling"}
        except Exception as e:
            self.logger.error(
                "Failed to trigger hook %s on %s: %s", hook_type, extension_name, e, exc_info=True
            )
            return {"error": str(e)}

    async def trigger_all_extension_hooks(
        self,
        hook_type: str,
        data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
        filter_extensions: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Trigger a hook on all loaded extensions or filtered subset.
        """
        results: Dict[str, Dict[str, Any]] = {}
        for record in self.registry.get_active_extensions():
            ext_name = record.manifest.name
            if filter_extensions and ext_name not in filter_extensions:
                continue
            try:
                results[ext_name] = await self.trigger_extension_hook(
                    ext_name, hook_type, data, user_context
                )
            except Exception as e:
                self.logger.error("Failed to trigger hook on %s: %s", ext_name, e, exc_info=True)
                results[ext_name] = {"error": str(e)}
        return results

    async def register_extension_lifecycle_hooks(self) -> None:
        """
        Register standard lifecycle hooks.
        """
        await self.register_hook(
            HookTypes.EXTENSION_LOADED,
            self._on_extension_loaded_hook,
            priority=25,
            source_name="extension_manager_lifecycle",
        )
        await self.register_hook(
            HookTypes.EXTENSION_ACTIVATED,
            self._on_extension_activated_hook,
            priority=25,
            source_name="extension_manager_lifecycle",
        )
        await self.register_hook(
            HookTypes.EXTENSION_DEACTIVATED,
            self._on_extension_deactivated_hook,
            priority=25,
            source_name="extension_manager_lifecycle",
        )
        await self.register_hook(
            HookTypes.EXTENSION_UNLOADED,
            self._on_extension_unloaded_hook,
            priority=25,
            source_name="extension_manager_lifecycle",
        )
        await self.register_hook(
            HookTypes.EXTENSION_ERROR,
            self._on_extension_error_hook,
            priority=10,
            source_name="extension_manager_error_handler",
        )
        self.logger.info("Extension manager lifecycle hooks registered")

    async def _on_extension_loaded_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        ext = context.get("extension_name")
        if ext:
            record = self.registry.get_extension(ext)
            if record:
                self.resource_monitor.register_extension(record)
        return {
            "manager": "extension_manager",
            "action": "extension_loaded",
            "extension_name": ext,
            "monitoring_enabled": True,
        }

    async def _on_extension_activated_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        ext = context.get("extension_name")
        if ext:
            try:
                status = await self.check_extension_health(ext)
                self.logger.info("Extension %s health status: %s", ext, status)
            except Exception as e:
                self.logger.warning("Failed to check health for %s: %s", ext, e)
        return {
            "manager": "extension_manager",
            "action": "extension_activated",
            "extension_name": ext,
            "health_check_performed": True,
        }

    async def _on_extension_deactivated_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        ext = context.get("extension_name")
        reason = context.get("deactivation_reason", "unknown")
        self.logger.info("Extension %s deactivated: %s", ext, reason)
        return {
            "manager": "extension_manager",
            "action": "extension_deactivated",
            "extension_name": ext,
            "reason": reason,
            "audit_logged": True,
        }

    async def _on_extension_unloaded_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        ext = context.get("extension_name")
        if ext:
            self.resource_monitor.unregister_extension(ext)
        return {
            "manager": "extension_manager",
            "action": "extension_unloaded",
            "extension_name": ext,
            "monitoring_cleaned": True,
        }

    async def _on_extension_error_hook(self, context: Dict[str, Any]) -> Dict[str, Any]:
        ext = context.get("extension_name")
        error_message = context.get("error", "Unknown error")
        if ext:
            self.registry.update_status(ext, ExtensionStatus.ERROR, error_message)
        try:
            bus = get_event_bus()
            bus.publish(
                "extensions",
                "error",
                {"name": ext, "error": error_message, "timestamp": context.get("timestamp")},
                roles=["admin"],
            )
        except Exception as e:
            self.logger.debug("Failed to publish extension error event: %s", e)
        return {
            "manager": "extension_manager",
            "action": "extension_error_handled",
            "extension_name": ext,
            "error_logged": True,
            "status_updated": True,
        }

    # -------------------------
    # AI-powered hooks (simple rules; plug your ML later)
    # -------------------------
    async def setup_ai_powered_hooks(self) -> None:
        await self.register_hook(
            "ai_extension_recommendation",
            self._ai_recommend_extensions,
            priority=50,
            source_name="extension_manager_ai",
        )
        await self.register_hook(
            "ai_health_analysis",
            self._ai_analyze_extension_health,
            priority=50,
            source_name="extension_manager_ai",
        )
        await self.register_hook(
            "ai_extension_optimization",
            self._ai_optimize_extensions,
            priority=50,
            source_name="extension_manager_ai",
        )
        self.logger.info("AI-powered extension hooks registered")

    async def _ai_recommend_extensions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_ctx = context.get("user_context", {})
            current = [r.manifest.name for r in self.registry.get_active_extensions()]
            recs = []

            merged = " ".join(current).lower()
            if "analytics" in merged:
                recs.append(
                    {
                        "extension": "advanced-visualization",
                        "reason": "Complements analytics with advanced charts",
                        "confidence": 0.8,
                    }
                )
            if "database" in merged:
                recs.append(
                    {
                        "extension": "query-optimizer",
                        "reason": "Optimizes database queries for better performance",
                        "confidence": 0.7,
                    }
                )
            return {
                "recommendations": recs,
                "analysis_method": "rule_based_ai",
                "context_analyzed": bool(user_ctx),
            }
        except Exception as e:
            self.logger.error("AI extension recommendation failed: %s", e, exc_info=True)
            return {"error": str(e), "recommendations": []}

    async def _ai_analyze_extension_health(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            name = context.get("extension_name")
            if not name:
                return {"error": "Extension name required for health analysis"}

            usage = self.get_extension_resource_usage(name)
            if not usage:
                return {"error": f"No usage data available for {name}"}

            score = 100.0
            issues: List[str] = []
            recs: List[str] = []

            if usage["memory_mb"] > 500:
                score -= 20
                issues.append("High memory usage detected")
                recs.append("Optimize memory usage or increase system memory")

            if usage["cpu_percent"] > 80:
                score -= 25
                issues.append("High CPU usage detected")
                recs.append("Review algorithms for optimization opportunities")

            if usage["uptime_seconds"] < 3600:
                score -= 10
                issues.append("Frequent restarts detected")
                recs.append("Investigate stability issues and error logs")

            return {
                "extension_name": name,
                "health_score": max(0, score),
                "issues": issues,
                "recommendations": recs,
                "analysis_timestamp": context.get("timestamp"),
                "ai_analysis": True,
            }
        except Exception as e:
            self.logger.error("AI health analysis failed: %s", e, exc_info=True)
            return {"error": str(e)}

    async def _ai_optimize_extensions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            all_usage = self.get_all_resource_usage()
            optimizations: List[Dict[str, Any]] = []

            total_memory = sum(u["memory_mb"] for u in all_usage.values())
            total_cpu = sum(u["cpu_percent"] for u in all_usage.values())

            if total_memory > 2000:
                memory_heavy = [n for n, u in all_usage.items() if u["memory_mb"] > 200]
                optimizations.append(
                    {
                        "type": "memory_optimization",
                        "description": "High total memory usage",
                        "affected_extensions": memory_heavy,
                        "suggestion": "Disable unused extensions or optimize memory use",
                        "priority": "high",
                    }
                )

            if total_cpu > 200:
                cpu_heavy = [n for n, u in all_usage.items() if u["cpu_percent"] > 50]
                optimizations.append(
                    {
                        "type": "cpu_optimization",
                        "description": "High total CPU usage",
                        "affected_extensions": cpu_heavy,
                        "suggestion": "Review algorithms, consider load balancing",
                        "priority": "medium",
                    }
                )

            categories: Dict[str, List[str]] = {}
            for record in self.registry.get_active_extensions():
                category = getattr(record.manifest, "category", "unknown")
                categories.setdefault(category, []).append(record.manifest.name)

            for cat, names in categories.items():
                if len(names) > 3:
                    optimizations.append(
                        {
                            "type": "consolidation",
                            "description": f"Multiple {cat} extensions detected",
                            "affected_extensions": names,
                            "suggestion": f"Consider consolidating {cat} functionality",
                            "priority": "low",
                        }
                    )

            return {
                "optimizations": optimizations,
                "system_metrics": {
                    "total_memory_mb": total_memory,
                    "total_cpu_percent": total_cpu,
                    "active_extensions": len(all_usage),
                },
                "ai_analysis": True,
            }
        except Exception as e:
            self.logger.error("AI optimization analysis failed: %s", e, exc_info=True)
            return {"error": str(e), "optimizations": []}

    # -------------------------
    # MCP hooks
    # -------------------------
    async def enable_mcp_hooks(self) -> None:
        await self.register_hook(
            "mcp_tool_registered",
            self._on_mcp_tool_registered,
            priority=50,
            source_name="extension_manager_mcp",
        )
        await self.register_hook(
            "mcp_tool_called",
            self._on_mcp_tool_called,
            priority=50,
            source_name="extension_manager_mcp",
        )
        await self.register_hook(
            "mcp_service_discovered",
            self._on_mcp_service_discovered,
            priority=50,
            source_name="extension_manager_mcp",
        )
        self.logger.info("MCP-specific extension hooks enabled")

    async def _on_mcp_tool_registered(self, context: Dict[str, Any]) -> Dict[str, Any]:
        ext = context.get("extension_name")
        tool = context.get("tool_name")
        self.logger.info("MCP tool %s registered by extension %s", tool, ext)
        return {
            "manager": "extension_manager",
            "action": "mcp_tool_registered",
            "extension_name": ext,
            "tool_name": tool,
            "registered_successfully": True,
        }

    async def _on_mcp_tool_called(self, context: Dict[str, Any]) -> Dict[str, Any]:
        ext = context.get("extension_name")
        tool = context.get("tool_name")
        ms = context.get("execution_time_ms", 0)
        self.logger.debug("MCP tool %s called by %s in %sms", tool, ext, ms)
        UsageService.increment("tool_calls")
        return {
            "manager": "extension_manager",
            "action": "mcp_tool_called",
            "extension_name": ext,
            "tool_name": tool,
            "execution_time_ms": ms,
            "tracked": True,
        }

    async def _on_mcp_service_discovered(self, context: Dict[str, Any]) -> Dict[str, Any]:
        svc = context.get("service_name")
        cnt = len(context.get("tools", []))
        self.logger.info("MCP service %s discovered with %d tools", svc, cnt)
        return {
            "manager": "extension_manager",
            "action": "mcp_service_discovered",
            "service_name": svc,
            "tools_count": cnt,
            "discovery_successful": True,
        }

    # -------------------------
    # Hook system lifecycle
    # -------------------------
    async def initialize_hook_system(self) -> None:
        """
        Initialize lifecycle + AI + MCP hooks.
        """
        try:
            await self.register_extension_lifecycle_hooks()
            await self.setup_ai_powered_hooks()
            await self.enable_mcp_hooks()
            self.logger.info("Extension manager hook system initialized")
        except Exception as e:
            self.logger.error("Failed to initialize hook system: %s", e, exc_info=True)
            raise

    async def shutdown_hook_system(self) -> None:
        """
        Shutdown the hook system and clean up hooks registered by this manager.
        """
        try:
            if self.hook_manager:
                # Clear by known sources used above
                total = 0
                for source in (
                    "extension_manager_lifecycle",
                    "extension_manager_error_handler",
                    "extension_manager_ai",
                    "extension_manager_mcp",
                ):
                    total += await self.hook_manager.clear_hooks_by_source(source)
                self.logger.info("Cleared %d extension manager hooks", total)
        except Exception as e:
            self.logger.error("Failed to shutdown hook system: %s", e, exc_info=True)

    async def get_hook_integration_status(self) -> Dict[str, Any]:
        """
        Report current hook integration coverage.
        """
        try:
            hook_stats = self.get_hook_stats()
            active = self.registry.get_active_extensions()

            hook_enabled = 0
            for record in active:
                if hasattr(record.instance, "handle_hook"):
                    hook_enabled += 1

            hook_types = hook_stats.get("hook_types", [])
            return {
                "hook_system_enabled": self.are_hooks_enabled(),
                "manager_hooks_registered": hook_stats.get("registered_hooks", 0),
                "manager_hook_types": hook_types,
                "total_extensions": len(active),
                "hook_enabled_extensions": hook_enabled,
                "hook_coverage_percent": (hook_enabled / len(active) * 100) if active else 0,
                "ai_hooks_available": "ai_extension_recommendation" in hook_types,
                "mcp_hooks_available": "mcp_tool_registered" in hook_types,
            }
        except Exception as e:
            self.logger.error("Failed to get hook integration status: %s", e, exc_info=True)
            return {"error": str(e)}

    # -------------------------
    # Monitoring & dep tree snapshots
    # -------------------------
    def get_extension_monitoring_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive monitoring summary including hooks and resources.
        """
        loaded = self.registry.get_active_extensions()
        summary: Dict[str, Any] = {
            "total_extensions": len(loaded),
            "health_summary": self.get_health_summary(),
            "resource_usage": self.get_all_resource_usage(),
            "hook_manager_stats": self.get_hook_stats(),
            "extensions": {},
        }
        for record in loaded:
            name = record.manifest.name
            summary["extensions"][name] = {
                "status": record.status.value,
                "version": record.manifest.version,
                "loaded_at": record.loaded_at.isoformat() if record.loaded_at else None,
                "has_hooks": hasattr(record.instance, "trigger_hooks"),
                "has_mcp": bool(
                    hasattr(record.instance, "_mcp_server")
                    and record.instance._mcp_server is not None
                ),
            }
        return summary

    def get_dependency_tree(self) -> Dict[str, Any]:
        """
        Get the dependency tree for all discovered extensions.
        NOTE: Intended for admin/diagnostic usage.
        """
        try:
            # If we're already in an event loop (FastAPI), use create_task style
            if asyncio.get_event_loop().is_running():
                # Run discovery in a temporary task and wait
                return asyncio.get_event_loop().run_until_complete(self.discover_extensions())  # type: ignore[misc]
            manifests = asyncio.run(self.discover_extensions())
            return self.dependency_resolver.get_dependency_tree(manifests)
        except RuntimeError:
            # Fallback: best effort discovery in a new loop
            manifests = asyncio.run(self.discover_extensions())
            return self.dependency_resolver.get_dependency_tree(manifests)
        except Exception as e:
            self.logger.error("Failed to get dependency tree: %s", e, exc_info=True)
            return {}

    # -------------------------
    # Directory lookup
    # -------------------------
    async def _find_extension_directory(self, name: str) -> Optional[Path]:
        """
        Find the directory for an extension by name, searching all categories.

        Returns:
            Path if found, else None
        """
        # Direct lookup (back-compat)
        direct_path = self.extension_root / name
        if direct_path.exists():
            if (direct_path / "extension.json").exists():
                return direct_path
            # Directory exists but manifest missing; surface path for clearer error handling
            return direct_path

        # Search categorized layout
        try:
            for category_dir in self.extension_root.iterdir():
                if not category_dir.is_dir() or category_dir.name.startswith("__"):
                    continue

                candidate = category_dir / name
                if candidate.exists():
                    if (candidate / "extension.json").exists():
                        return candidate
                    return candidate

                # Fuzzy: scan children with mismatched dir names
                for item in category_dir.iterdir():
                    if not item.is_dir():
                        continue
                    manifest_path = item / "extension.json"
                    if manifest_path.exists():
                        try:
                            manifest = ExtensionManifest.from_file(manifest_path)
                            if manifest.name == name:
                                return item
                        except Exception:
                            continue
        except Exception as e:
            self.logger.error("Error searching for extension %s: %s", name, e, exc_info=True)

        return None


# Global instance helpers
_extension_manager: Optional[ExtensionManager] = None


def get_extension_manager() -> Optional[ExtensionManager]:
    """Get the global extension manager instance."""
    return _extension_manager


def initialize_extension_manager(
    extension_root: Path,
    plugin_router: PluginRouter,
    db_session: Any = None,
    app_instance: Any = None,
) -> ExtensionManager:
    """
    Initialize the global extension manager (idempotent initializer).
    """
    global _extension_manager
    _extension_manager = ExtensionManager(
        extension_root=extension_root,
        plugin_router=plugin_router,
        db_session=db_session,
        app_instance=app_instance,
    )
    return _extension_manager


__all__ = [
    "ExtensionManager",
    "get_extension_manager",
    "initialize_extension_manager",
    "HealthStatus",
    "MarketplaceClient",
]
