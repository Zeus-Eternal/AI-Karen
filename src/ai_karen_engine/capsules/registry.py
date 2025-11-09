"""
Capsule Registry - Dynamic Discovery and Management

Auto-discovers and registers capsules from the capsules directory.
Provides lookup, validation, and metadata services for the orchestrator.

Research Alignment:
- Microservices Service Discovery Pattern
- Factory Pattern for Capsule Instantiation
"""

import logging
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Type
import threading

from ai_karen_engine.capsules.base_capsule import BaseCapsule, CapsuleValidationError
from ai_karen_engine.capsules.schemas import CapsuleManifest, CapsuleType

logger = logging.getLogger(__name__)


class CapsuleRegistryError(Exception):
    """Capsule registry operation errors"""
    pass


class CapsuleRegistry:
    """
    Singleton registry for discovering, validating, and managing capsules.

    Responsibilities:
    - Auto-discover capsules from filesystem
    - Validate manifests
    - Lazy-load capsule classes
    - Provide lookup services
    - Track metrics
    """

    _instance: Optional['CapsuleRegistry'] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._capsules: Dict[str, Dict] = {}
        self._manifests: Dict[str, CapsuleManifest] = {}
        self._instances: Dict[str, BaseCapsule] = {}
        self._metrics = {
            "capsules_discovered": 0,
            "capsules_loaded": 0,
            "capsules_failed": 0,
        }
        self._initialized = True

        logger.info("Capsule registry initialized")

    def discover(self, capsules_dir: Optional[Path] = None) -> int:
        """
        Discover capsules from the capsules directory.

        Args:
            capsules_dir: Optional custom capsules directory

        Returns:
            Number of capsules discovered

        Raises:
            CapsuleRegistryError: On discovery failure
        """
        if capsules_dir is None:
            # Default to the capsules directory
            capsules_dir = Path(__file__).parent

        if not capsules_dir.exists() or not capsules_dir.is_dir():
            raise CapsuleRegistryError(f"Invalid capsules directory: {capsules_dir}")

        discovered_count = 0

        # Scan for capsule directories
        for item in capsules_dir.iterdir():
            # Skip non-directories and private/common modules
            if not item.is_dir():
                continue
            if item.name.startswith('_') or item.name.startswith('.'):
                continue
            if item.name in ['__pycache__', 'tests']:
                continue

            # Check for manifest.yaml
            manifest_path = item / "manifest.yaml"
            if not manifest_path.exists():
                logger.debug(f"Skipping {item.name}: no manifest.yaml")
                continue

            try:
                # Load manifest
                import yaml
                with open(manifest_path, 'r') as f:
                    manifest_data = yaml.safe_load(f)

                manifest = CapsuleManifest(**manifest_data)

                # Register capsule metadata
                self._capsules[manifest.id] = {
                    'name': manifest.name,
                    'dir': item,
                    'version': manifest.version,
                    'type': manifest.type,
                    'entrypoint': manifest.entrypoint,
                    'capabilities': manifest.capabilities,
                }
                self._manifests[manifest.id] = manifest

                discovered_count += 1
                self._metrics['capsules_discovered'] += 1

                logger.info(
                    f"Discovered capsule: {manifest.id} v{manifest.version} "
                    f"({manifest.type.value})"
                )

            except Exception as e:
                logger.warning(f"Failed to discover capsule in {item.name}: {e}")
                self._metrics['capsules_failed'] += 1

        logger.info(f"Capsule discovery complete: {discovered_count} capsules found")
        return discovered_count

    def get_capsule(self, capsule_id: str, reload: bool = False) -> BaseCapsule:
        """
        Get or load a capsule instance.

        Args:
            capsule_id: Capsule identifier
            reload: Force reload of capsule class

        Returns:
            Capsule instance

        Raises:
            CapsuleRegistryError: If capsule not found or load fails
        """
        # Check if already loaded
        if capsule_id in self._instances and not reload:
            return self._instances[capsule_id]

        # Check if registered
        if capsule_id not in self._capsules:
            raise CapsuleRegistryError(f"Capsule not found: {capsule_id}")

        # Load capsule class
        try:
            capsule_info = self._capsules[capsule_id]
            capsule_dir = capsule_info['dir']

            # Import the handler module
            handler_path = capsule_dir / capsule_info['entrypoint']
            spec = importlib.util.spec_from_file_location(
                f"capsule_{capsule_id.replace('.', '_')}",
                handler_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find capsule class (should inherit from BaseCapsule)
            capsule_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type) and
                    issubclass(attr, BaseCapsule) and
                    attr is not BaseCapsule
                ):
                    capsule_class = attr
                    break

            if capsule_class is None:
                raise CapsuleRegistryError(
                    f"No BaseCapsule subclass found in {handler_path}"
                )

            # Instantiate capsule
            instance = capsule_class(capsule_dir)

            # Cache instance
            self._instances[capsule_id] = instance
            self._metrics['capsules_loaded'] += 1

            logger.info(f"Loaded capsule: {capsule_id}")
            return instance

        except Exception as e:
            self._metrics['capsules_failed'] += 1
            raise CapsuleRegistryError(f"Failed to load capsule {capsule_id}: {e}") from e

    def get_manifest(self, capsule_id: str) -> CapsuleManifest:
        """
        Get capsule manifest without loading the capsule.

        Args:
            capsule_id: Capsule identifier

        Returns:
            Capsule manifest

        Raises:
            CapsuleRegistryError: If capsule not found
        """
        if capsule_id not in self._manifests:
            raise CapsuleRegistryError(f"Capsule not found: {capsule_id}")

        return self._manifests[capsule_id]

    def list_capsules(self, capsule_type: Optional[CapsuleType] = None) -> List[str]:
        """
        List registered capsule IDs, optionally filtered by type.

        Args:
            capsule_type: Optional filter by capsule type

        Returns:
            List of capsule IDs
        """
        if capsule_type is None:
            return list(self._capsules.keys())

        return [
            cid for cid, info in self._capsules.items()
            if info['type'] == capsule_type
        ]

    def get_capabilities(self, capsule_id: str) -> List[str]:
        """
        Get capsule capabilities.

        Args:
            capsule_id: Capsule identifier

        Returns:
            List of capabilities

        Raises:
            CapsuleRegistryError: If capsule not found
        """
        if capsule_id not in self._capsules:
            raise CapsuleRegistryError(f"Capsule not found: {capsule_id}")

        return self._capsules[capsule_id]['capabilities']

    def get_metrics(self) -> Dict[str, int]:
        """Get registry metrics"""
        return self._metrics.copy()

    def reload_all(self) -> None:
        """Reload all capsule instances"""
        logger.info("Reloading all capsules...")
        self._instances.clear()
        logger.info("All capsule instances cleared")


# Singleton instance
_registry: Optional[CapsuleRegistry] = None


def get_capsule_registry() -> CapsuleRegistry:
    """Get or create the global capsule registry"""
    global _registry
    if _registry is None:
        _registry = CapsuleRegistry()
    return _registry


__all__ = [
    "CapsuleRegistry",
    "CapsuleRegistryError",
    "get_capsule_registry",
]
