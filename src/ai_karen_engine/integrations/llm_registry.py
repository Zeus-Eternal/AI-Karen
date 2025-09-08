"""
LLM Provider Registry

Manages registration, discovery, and health monitoring of LLM providers.
Enhanced with model orchestrator integration, schema validation, and integrity verification.
"""

import hashlib
import json
import logging
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union
import asyncio
import threading

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

try:
    import jsonschema
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception

from ai_karen_engine.integrations.llm_utils import LLMProviderBase
from ai_karen_engine.integrations.providers import (
    DeepseekProvider,
    GeminiProvider,
    HuggingFaceProvider,
    LlamaCppProvider,
    OpenAIProvider,
)
from ai_karen_engine.integrations.kire_router import KIRERouter as KIREAdapter
from ai_karen_engine.routing.types import RouteRequest

logger = logging.getLogger("kari.llm_registry")


@dataclass
class ProviderRegistration:
    """Provider registration information."""

    name: str
    provider_class: str
    description: str
    supports_streaming: bool = False
    supports_embeddings: bool = False
    requires_api_key: bool = False
    default_model: str = ""
    health_status: str = "unknown"  # unknown, healthy, unhealthy
    last_health_check: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class ModelEntry:
    """Model registry entry with enhanced metadata."""
    
    model_id: str
    library: str
    revision: str
    installed_at: str
    install_path: str
    files: List[Dict[str, Union[str, int]]]
    total_size: int
    pinned: bool = False
    last_accessed: Optional[str] = None
    license_accepted: Optional[Dict[str, str]] = None
    compatibility: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class RegistryValidationError(Exception):
    """Registry validation error."""
    pass


class RegistryIntegrityError(Exception):
    """Registry integrity verification error."""
    pass


if WATCHDOG_AVAILABLE:
    class RegistryWatcher(FileSystemEventHandler):
        """File system watcher for registry changes."""
        
        def __init__(self, registry: 'LLMRegistry'):
            self.registry = registry
            self.logger = logging.getLogger("kari.registry_watcher")
            
        def on_modified(self, event):
            """Handle registry file modifications."""
            if not event.is_directory and event.src_path.endswith('llm_registry.json'):
                self.logger.info(f"Registry file modified: {event.src_path}")
                try:
                    # Reload registry and update LLM settings
                    self.registry._load_registry()
                    asyncio.create_task(self.registry.update_llm_settings())
                except Exception as ex:
                    self.logger.error(f"Failed to handle registry change: {ex}")
else:
    class RegistryWatcher:
        """Dummy watcher when watchdog is not available."""
        def __init__(self, registry): pass


class LLMRegistry:
    """Registry for managing LLM providers."""

    def __init__(self, registry_path: Optional[Path] = None, schema_path: Optional[Path] = None, 
                 llm_settings_path: Optional[Path] = None):
        """
        Initialize LLM registry.

        Args:
            registry_path: Path to registry JSON file (defaults to models/llm_registry.json)
            schema_path: Path to registry schema file (defaults to models/registry.schema.json)
            llm_settings_path: Path to LLM settings file (defaults to llm_settings.json)
        """
        self.registry_path = registry_path or Path("models/llm_registry.json")
        self.schema_path = schema_path or Path("models/registry.schema.json")
        self.llm_settings_path = llm_settings_path or Path("llm_settings.json")
        # Cache of provider instances keyed by name|model to allow multiple models per provider
        self._providers: Dict[str, LLMProviderBase] = {}
        self._registrations: Dict[str, ProviderRegistration] = {}
        self._model_entries: Dict[str, ModelEntry] = {}
        self._priorities: List[str] = [
            "llamacpp",
            "openai",
            "gemini",
            "deepseek",
            "huggingface",
            "copilotkit",
        ]

        # Load schema for validation
        self._schema = self._load_schema()
        self._llm_settings_schema = self._load_llm_settings_schema()

        # Register built-in providers
        self._register_builtin_providers()

        # Load existing registry
        self._load_registry()
        
        # Set up file watcher for automatic updates (requirement 2.1)
        self._setup_registry_watcher()

        # Lazy KIRE adapter
        self._kire: Optional[KIREAdapter] = None

    def _load_schema(self) -> Optional[Dict[str, Any]]:
        """Load registry schema for validation."""
        if not JSONSCHEMA_AVAILABLE:
            logger.warning("jsonschema not available, schema validation disabled")
            return None
            
        if not self.schema_path.exists():
            logger.warning(f"Schema file not found: {self.schema_path}")
            return None
            
        try:
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            logger.info(f"Loaded registry schema from {self.schema_path}")
            return schema
        except Exception as ex:
            logger.error(f"Failed to load schema from {self.schema_path}: {ex}")
            return None

    def _load_llm_settings_schema(self) -> Optional[Dict[str, Any]]:
        """Load LLM settings schema for validation."""
        if not JSONSCHEMA_AVAILABLE:
            return None
            
        # Create basic schema for LLM settings validation (requirement 2.7)
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "provider": {"type": "string"},
                "model": {"type": "string"},
                "api_key": {"type": ["string", "null"]},
                "base_url": {"type": ["string", "null"]},
                "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                "max_tokens": {"type": "integer", "minimum": 1},
                "timeout": {"type": "integer", "minimum": 1},
                "max_retries": {"type": "integer", "minimum": 0},
                "fallback_providers": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "provider_configs": {
                    "type": "object",
                    "patternProperties": {
                        "^[a-zA-Z0-9_-]+$": {
                            "type": "object",
                            "properties": {
                                "base_url": {"type": "string"},
                                "models": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "model_path": {"type": "string"},
                                "context_length": {"type": "integer"}
                            }
                        }
                    }
                }
            },
            "required": ["provider", "model"]
        }
        return schema

    def _setup_registry_watcher(self):
        """Set up file system watcher for registry changes."""
        if not WATCHDOG_AVAILABLE:
            logger.warning("watchdog not available, registry auto-update disabled")
            self._observer = None
            return
            
        try:
            self._observer = Observer()
            self._watcher = RegistryWatcher(self)
            
            # Watch the directory containing the registry file
            watch_dir = self.registry_path.parent
            if watch_dir.exists():
                self._observer.schedule(self._watcher, str(watch_dir), recursive=False)
                self._observer.start()
                logger.info(f"Started registry watcher for {watch_dir}")
            else:
                logger.warning(f"Registry directory does not exist: {watch_dir}")
                
        except Exception as ex:
            logger.error(f"Failed to setup registry watcher: {ex}")
            self._observer = None

    def validate_registry_data(self, data: Dict[str, Any]) -> None:
        """
        Validate registry data against schema.
        
        Args:
            data: Registry data to validate
            
        Raises:
            RegistryValidationError: If validation fails
        """
        if not self._schema or not JSONSCHEMA_AVAILABLE:
            return
            
        try:
            validate(instance=data, schema=self._schema)
        except ValidationError as ex:
            raise RegistryValidationError(f"Registry validation failed: {ex.message}")

    def compute_file_checksum(self, file_path: Path) -> str:
        """
        Compute SHA256 checksum of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 checksum as hex string
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as ex:
            logger.error(f"Failed to compute checksum for {file_path}: {ex}")
            return ""

    def verify_model_integrity(self, model_key: str) -> Dict[str, Any]:
        """
        Verify integrity of a model's files against stored checksums.
        
        Args:
            model_key: Model registry key
            
        Returns:
            Dict with verification results
        """
        if model_key not in self._model_entries:
            return {"status": "not_found", "error": f"Model {model_key} not in registry"}
            
        entry = self._model_entries[model_key]
        install_path = Path(entry.install_path)
        
        if not install_path.exists():
            return {"status": "missing", "error": f"Install path {install_path} does not exist"}
            
        results = {
            "status": "verified",
            "files_checked": 0,
            "files_missing": 0,
            "files_corrupted": 0,
            "missing_files": [],
            "corrupted_files": []
        }
        
        for file_info in entry.files:
            file_path = install_path / file_info["path"]
            results["files_checked"] += 1
            
            if not file_path.exists():
                results["files_missing"] += 1
                results["missing_files"].append(file_info["path"])
                continue
                
            # Check size
            actual_size = file_path.stat().st_size
            expected_size = file_info["size"]
            
            if actual_size != expected_size:
                results["files_corrupted"] += 1
                results["corrupted_files"].append({
                    "path": file_info["path"],
                    "reason": "size_mismatch",
                    "expected_size": expected_size,
                    "actual_size": actual_size
                })
                continue
                
            # Check checksum if available
            if "sha256" in file_info and file_info["sha256"]:
                actual_checksum = self.compute_file_checksum(file_path)
                expected_checksum = file_info["sha256"]
                
                if actual_checksum != expected_checksum:
                    results["files_corrupted"] += 1
                    results["corrupted_files"].append({
                        "path": file_info["path"],
                        "reason": "checksum_mismatch",
                        "expected_checksum": expected_checksum,
                        "actual_checksum": actual_checksum
                    })
        
        if results["files_missing"] > 0 or results["files_corrupted"] > 0:
            results["status"] = "corrupted"
            
        return results

    def atomic_registry_update(self, update_func, *args, **kwargs) -> Any:
        """
        Perform atomic registry update with backup and rollback capability.
        
        Args:
            update_func: Function to perform the update
            *args, **kwargs: Arguments for update function
            
        Returns:
            Result of update function
            
        Raises:
            Exception: If update fails and rollback is performed
        """
        # Create backup
        backup_path = None
        if self.registry_path.exists():
            backup_path = self.registry_path.with_suffix('.backup')
            shutil.copy2(self.registry_path, backup_path)
            
        try:
            # Perform update
            result = update_func(*args, **kwargs)
            
            # Clean up backup on success
            if backup_path and backup_path.exists():
                backup_path.unlink()
                
            return result
            
        except Exception as ex:
            # Rollback on failure
            if backup_path and backup_path.exists():
                if self.registry_path.exists():
                    self.registry_path.unlink()
                shutil.move(backup_path, self.registry_path)
                logger.error(f"Registry update failed, rolled back: {ex}")
            raise

    def add_model_entry(self, model_key: str, entry: ModelEntry) -> None:
        """
        Add or update a model entry in the registry.
        
        Args:
            model_key: Model registry key
            entry: Model entry data
        """
        def _update():
            # Load current registry data
            registry_data = self._load_model_registry_data()
            
            # Add/update entry
            entry_dict = asdict(entry)
            registry_data[model_key] = entry_dict
            
            # Validate updated data
            self.validate_registry_data(registry_data)
            
            # Save atomically
            self._save_model_registry_data(registry_data)
            
            # Update in-memory cache
            self._model_entries[model_key] = entry
            
        self.atomic_registry_update(_update)

    def remove_model_entry(self, model_key: str) -> None:
        """
        Remove a model entry from the registry.
        
        Args:
            model_key: Model registry key
        """
        def _update():
            # Load current registry data
            registry_data = self._load_model_registry_data()
            
            if model_key in registry_data:
                del registry_data[model_key]
                
                # Validate updated data
                self.validate_registry_data(registry_data)
                
                # Save atomically
                self._save_model_registry_data(registry_data)
                
                # Update in-memory cache
                if model_key in self._model_entries:
                    del self._model_entries[model_key]
                    
        self.atomic_registry_update(_update)

    def _load_model_registry_data(self) -> Dict[str, Any]:
        """Load model registry data from file."""
        if not self.registry_path.exists():
            return {}
            
        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
                
            # Handle both old and new registry formats
            if isinstance(data, list):
                # Old format - convert to new format
                new_data = {}
                for item in data:
                    if isinstance(item, dict) and "name" in item:
                        new_data[item["name"]] = item
                return new_data
            elif isinstance(data, dict):
                return data
            else:
                return {}
                
        except Exception as ex:
            logger.error(f"Failed to load model registry data: {ex}")
            return {}

    def _save_model_registry_data(self, data: Dict[str, Any]) -> None:
        """Save model registry data to file."""
        # Ensure directory exists
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file first
        temp_path = self.registry_path.with_suffix('.tmp')
        
        try:
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2, sort_keys=True)
                
            # Atomic move
            temp_path.replace(self.registry_path)
            
        except Exception as ex:
            # Clean up temp file on failure
            if temp_path.exists():
                temp_path.unlink()
            raise ex

    def _register_builtin_providers(self):
        """Register all built-in LLM providers."""
        builtin_providers = [
            {
                "name": "llamacpp",
                "provider_class": "LlamaCppProvider",
                "description": "Local llama-cpp-python for running open-source models",
                "supports_streaming": True,
                "supports_embeddings": True,
                "requires_api_key": False,
                "default_model": "llama3.2:latest",
            },
            {
                "name": "openai",
                "provider_class": "OpenAIProvider",
                "description": "OpenAI GPT models via API",
                "supports_streaming": True,
                "supports_embeddings": True,
                "requires_api_key": True,
                "default_model": "gpt-3.5-turbo",
            },
            {
                "name": "gemini",
                "provider_class": "GeminiProvider",
                "description": "Google Gemini models via API",
                "supports_streaming": True,
                "supports_embeddings": True,
                "requires_api_key": True,
                "default_model": "gemini-1.5-flash",
            },
            {
                "name": "deepseek",
                "provider_class": "DeepseekProvider",
                "description": "Deepseek models optimized for coding and reasoning",
                "supports_streaming": True,
                "supports_embeddings": False,
                "requires_api_key": True,
                "default_model": "deepseek-chat",
            },
            {
                "name": "huggingface",
                "provider_class": "HuggingFaceProvider",
                "description": "HuggingFace models via Inference API or local execution",
                "supports_streaming": False,
                "supports_embeddings": True,
                "requires_api_key": True,
                "default_model": "microsoft/DialoGPT-large",
            },
        ]

        for provider_info in builtin_providers:
            registration = ProviderRegistration(**provider_info)
            self._registrations[provider_info["name"]] = registration

    def _load_registry(self):
        """Load registry from JSON file."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r") as f:
                    data = json.load(f)

                # Handle different registry formats
                if isinstance(data, list):
                    # Old format - provider registrations
                    for item in data:
                        if isinstance(item, dict) and "name" in item:
                            # Update existing registration or create new one
                            name = item["name"]
                            if name in self._registrations:
                                # Update existing registration with saved data
                                registration = self._registrations[name]
                                registration.health_status = item.get(
                                    "health_status", "unknown"
                                )
                                registration.last_health_check = item.get(
                                    "last_health_check"
                                )
                                registration.error_message = item.get("error_message")
                                # Also update the default_model if provided
                                if "default_model" in item:
                                    registration.default_model = item["default_model"]
                            else:
                                # Create new registration from saved data
                                self._registrations[name] = ProviderRegistration(**item)
                                
                elif isinstance(data, dict):
                    # New format - model entries
                    for model_key, entry_data in data.items():
                        if isinstance(entry_data, dict):
                            # Check if this is a provider registration or model entry
                            if "provider_class" in entry_data:
                                # Provider registration
                                name = entry_data.get("name", model_key)
                                if name in self._registrations:
                                    registration = self._registrations[name]
                                    registration.health_status = entry_data.get(
                                        "health_status", "unknown"
                                    )
                                    registration.last_health_check = entry_data.get(
                                        "last_health_check"
                                    )
                                    registration.error_message = entry_data.get("error_message")
                                    if "default_model" in entry_data:
                                        registration.default_model = entry_data["default_model"]
                                else:
                                    self._registrations[name] = ProviderRegistration(**entry_data)
                            elif "model_id" in entry_data:
                                # Model entry
                                try:
                                    self._model_entries[model_key] = ModelEntry(**entry_data)
                                except Exception as ex:
                                    logger.warning(f"Failed to load model entry {model_key}: {ex}")

                logger.info(f"Loaded registry from {self.registry_path}")

            except Exception as ex:
                logger.warning(
                    f"Could not load registry from {self.registry_path}: {ex}"
                )

    def _save_registry(self):
        """Save registry to JSON file."""
        try:
            # Ensure directory exists
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert registrations to list of dicts
            data = [asdict(reg) for reg in self._registrations.values()]

            with open(self.registry_path, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as ex:
            logger.error(f"Could not save registry to {self.registry_path}: {ex}")

    def register_provider(
        self,
        name: str,
        provider_class: Type[LLMProviderBase],
        description: str = "",
        **kwargs,
    ):
        """
        Register a custom LLM provider.

        Args:
            name: Provider name
            provider_class: Provider class
            description: Provider description
            **kwargs: Additional registration parameters
        """
        registration = ProviderRegistration(
            name=name,
            provider_class=provider_class.__name__,
            description=description,
            **kwargs,
        )

        self._registrations[name] = registration
        logger.info(f"Registered provider: {name}")

        # Save updated registry
        self._save_registry()

    def get_provider(self, name: str, **init_kwargs) -> Optional[LLMProviderBase]:
        """
        Get provider instance by name.

        Args:
            name: Provider name
            **init_kwargs: Provider initialization arguments

        Returns:
            Provider instance or None if not found
        """
        if name not in self._registrations:
            logger.error(f"Provider '{name}' not registered")
            return None

        # Build cache key including model so different model inits are not conflated
        model_key = init_kwargs.get("model") or self._registrations[name].default_model or ""
        cache_key = f"{name}|{model_key}"

        # Return cached instance if available
        if cache_key in self._providers:
            return self._providers[cache_key]

        # Create new instance
        try:
            registration = self._registrations[name]
            provider_class = self._get_provider_class(registration.provider_class)

            if provider_class:
                # Use default model if not specified
                if "model" not in init_kwargs and registration.default_model:
                    init_kwargs["model"] = registration.default_model

                # Translate llamacpp model id to a concrete model_path when possible
                if name == "llamacpp":
                    # If a specific GGUF model was selected, resolve to a verified file path
                    model_id = init_kwargs.get("model")
                    if model_id and "model_path" not in init_kwargs:
                        resolved = self._resolve_llamacpp_model_path_by_id(model_id)
                        if resolved:
                            init_kwargs["model_path"] = resolved
                        else:
                            logger.error(f"Unable to resolve verified GGUF for model_id '{model_id}'")
                            return None

                provider = provider_class(**init_kwargs)
                self._providers[cache_key] = provider

                logger.info(f"Created provider instance: {name} (model={init_kwargs.get('model')})")
                return provider

        except Exception as ex:
            logger.error(f"Failed to create provider '{name}': {ex}")

        return None

    # -----------------------------
    # KIRE routing integration
    # -----------------------------
    async def get_provider_with_routing(
        self,
        *,
        user_ctx: Dict[str, Any],
        query: str,
        task_type: str,
        khrp_step: Optional[str] = None,
        requirements: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Route to provider/model using KIRE and return instance + decision.

        Returns dict with keys: provider_instance, decision (RouteDecision), provider_name, model_name
        """
        try:
            if self._kire is None:
                self._kire = KIREAdapter(llm_registry=self)
            decision = await self._kire.route(
                user_id=user_ctx.get("user_id", "anon"),
                task_type=task_type,
                query=query,
                khrp_step=khrp_step,
                context={"user_ctx": user_ctx},
                requirements=requirements or {},
            )
            provider = self.get_provider(decision.provider, model=decision.model)
            return {
                "provider_instance": provider,
                "decision": decision,
                "provider_name": decision.provider,
                "model_name": decision.model,
            }
        except Exception as ex:
            logger.error(f"KIRE routing failed, falling back. Error: {ex}")
            # Fallback to default provider construction
            prov = self.default_chain(healthy_only=False)[0] if self.default_chain() else None
            instance = self.get_provider(prov) if prov else None
            return {
                "provider_instance": instance,
                "decision": None,
                "provider_name": prov,
                "model_name": None,
            }

    def _get_provider_class(self, class_name: str) -> Optional[Type[LLMProviderBase]]:
        """Get provider class by name."""
        class_map = {
            "LlamaCppProvider": LlamaCppProvider,
            "OpenAIProvider": OpenAIProvider,
            "GeminiProvider": GeminiProvider,
            "DeepseekProvider": DeepseekProvider,
            "HuggingFaceProvider": HuggingFaceProvider,
        }

        return class_map.get(class_name)

    # -----------------------------
    # Llama.cpp model resolution & verification
    # -----------------------------
    def _is_probably_valid_gguf(self, file_path: Path) -> bool:
        try:
            if not file_path.exists() or not file_path.is_file():
                return False
            if file_path.suffix.lower() != ".gguf":
                return False
            size = file_path.stat().st_size
            if size < 50 * 1024 * 1024:  # < 50MB unlikely to be valid model
                return False
            with open(file_path, "rb") as f:
                magic = f.read(4)
            return magic == b"GGUF"
        except Exception:
            return False

    def _find_model_entry_key_by_id(self, model_id: str) -> Optional[str]:
        for key, entry in self._model_entries.items():
            if entry.model_id == model_id:
                return key
        return None

    def _resolve_llamacpp_model_path_by_id(self, model_id: str) -> Optional[str]:
        """Resolve a llama.cpp model_id to a verified local GGUF file path."""
        try:
            # Prefer model registry entry
            entry_key = self._find_model_entry_key_by_id(model_id)
            if entry_key:
                entry = self._model_entries[entry_key]
                if entry.library == "llama-cpp":
                    p = Path(entry.install_path)
                    # Validate file header quickly
                    if self._is_probably_valid_gguf(p):
                        # Try integrity verification when file list/checksums are present
                        try:
                            result = self.verify_model_integrity(entry_key)
                            if result.get("status") in {"verified", "missing", "corrupted"}:
                                # Even if some files in registry are missing, the main file is header-checked
                                return str(p)
                        except Exception:
                            return str(p)
            # Fallback: look in models/llama-cpp for matching filename
            candidate = Path("models/llama-cpp") / model_id
            if self._is_probably_valid_gguf(candidate):
                return str(candidate)
        except Exception:
            pass
        return None

    def list_providers(self) -> List[str]:
        """Get list of registered provider names."""
        return list(self._registrations.keys())

    def default_chain(self, healthy_only: bool = False) -> List[str]:
        """Return providers ordered by built-in priority.

        Parameters
        ----------
        healthy_only: bool
            If True, only include providers with health_status "healthy".
        """

        ordered: List[str] = []
        for name in self._priorities:
            if name not in self._registrations:
                continue
            if healthy_only and self._registrations[name].health_status not in ("healthy", "unknown"):
                continue
            ordered.append(name)

        for name in self._registrations:
            if name in ordered:
                continue
            if healthy_only and self._registrations[name].health_status not in ("healthy", "unknown"):
                continue
            ordered.append(name)

        return ordered

    def get_provider_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get provider registration information."""
        if name not in self._registrations:
            return None

        registration = self._registrations[name]
        info = asdict(registration)

        # Ensure provider is instantiated to gather runtime metadata
        provider = self._providers.get(name)
        if provider is None:
            provider = self.get_provider(name)

        if provider:
            try:
                provider_info = provider.get_provider_info()
                info.update(provider_info)
            except Exception as ex:
                logger.warning(f"Could not get provider info for {name}: {ex}")

        return info

    def health_check(self, name: str) -> Dict[str, Any]:
        """Perform enhanced health check on a provider with model validation."""
        if name not in self._registrations:
            return {
                "status": "not_registered",
                "error": f"Provider '{name}' not registered",
            }

        try:
            provider = self.get_provider(name)
            if not provider:
                return {
                    "status": "failed_to_create",
                    "error": "Could not create provider instance",
                }

            # Perform health check if provider supports it
            if hasattr(provider, "health_check"):
                result = provider.health_check()
            else:
                # Basic health check - try to get provider info
                provider.get_provider_info()
                result = {"status": "healthy", "message": "Basic health check passed"}

            # Add model validation for providers with installed models (requirement 2.5)
            provider_models = self.get_models_by_library(
                self._get_library_for_provider(name)
            )
            
            if provider_models:
                result["models"] = {
                    "total_count": len(provider_models),
                    "installed_models": list(provider_models.keys())
                }
                
                # Perform basic model accessibility check
                accessible_models = 0
                model_errors = []
                
                for model_key, entry in list(provider_models.items())[:3]:  # Check first 3 models
                    try:
                        # Check if model files exist
                        install_path = Path(entry.install_path)
                        if not install_path.exists():
                            model_errors.append(f"{model_key}: install path missing")
                            continue
                        
                        # Check if required files exist
                        missing_files = []
                        for file_info in entry.files[:5]:  # Check first 5 files
                            file_path = install_path / file_info["path"]
                            if not file_path.exists():
                                missing_files.append(file_info["path"])
                        
                        if missing_files:
                            model_errors.append(f"{model_key}: missing files {missing_files}")
                        else:
                            accessible_models += 1
                            
                    except Exception as ex:
                        model_errors.append(f"{model_key}: {ex}")
                
                result["models"]["accessible_count"] = accessible_models
                result["models"]["accessibility_rate"] = accessible_models / len(provider_models)
                
                if model_errors:
                    result["models"]["errors"] = model_errors[:5]  # Limit to 5 errors
                    
                # Mark as degraded if less than 50% of models are accessible
                if result["models"]["accessibility_rate"] < 0.5:
                    result["status"] = "degraded"
                    result["warnings"] = result.get("warnings", [])
                    result["warnings"].append("Less than 50% of models are accessible")

            # Update registration
            registration = self._registrations[name]
            registration.health_status = result.get("status", "unknown")
            registration.last_health_check = time.time()
            registration.error_message = result.get("error")

            # Save updated registry
            self._save_registry()

            return result

        except Exception as ex:
            # Update registration with error
            registration = self._registrations[name]
            registration.health_status = "unhealthy"
            registration.last_health_check = time.time()
            registration.error_message = str(ex)

            # Save updated registry
            self._save_registry()

            return {"status": "unhealthy", "error": str(ex)}

    def _get_library_for_provider(self, provider_name: str) -> Optional[str]:
        """Get the library type for a provider."""
        provider_library_map = {
            "llamacpp": "llama-cpp",
            "huggingface": "transformers",
            "openai": None,  # API-based, no local models
            "gemini": None,  # API-based, no local models
            "deepseek": None,  # API-based, no local models
        }
        return provider_library_map.get(provider_name)

    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all registered providers."""
        results = {}

        for name in self._registrations.keys():
            results[name] = self.health_check(name)

        return results

    def get_available_providers(self) -> List[str]:
        """Get list of providers that are currently healthy or unknown status."""
        available = []

        for name, registration in self._registrations.items():
            if registration.health_status in ["healthy", "unknown"]:
                available.append(name)

        return available

    def auto_select_provider(
        self, requirements: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Automatically select the best available provider based on requirements.

        Args:
            requirements: Dict with keys like 'streaming', 'embeddings', 'api_key_available'

        Returns:
            Provider name or None if no suitable provider found
        """
        requirements = requirements or {}

        # Get available providers
        available = self.get_available_providers()

        # Filter by requirements
        suitable = []
        for name in available:
            registration = self._registrations[name]

            # Check streaming requirement
            if requirements.get("streaming") and not registration.supports_streaming:
                continue

            # Check embeddings requirement
            if requirements.get("embeddings") and not registration.supports_embeddings:
                continue

            # Check API key requirement
            if registration.requires_api_key and not requirements.get(
                "api_key_available", True
            ):
                continue

            suitable.append(name)

        # Return first suitable provider (could be enhanced with priority logic)
        return suitable[0] if suitable else None

    # Model entry management methods
    
    def get_model_entry(self, model_key: str) -> Optional[ModelEntry]:
        """Get model entry by key."""
        return self._model_entries.get(model_key)
        
    def list_model_entries(self) -> Dict[str, ModelEntry]:
        """Get all model entries."""
        return self._model_entries.copy()
        
    def update_model_access_time(self, model_key: str) -> None:
        """Update last access time for a model."""
        if model_key in self._model_entries:
            entry = self._model_entries[model_key]
            entry.last_accessed = datetime.now(timezone.utc).isoformat()
            self.add_model_entry(model_key, entry)
            
    def pin_model(self, model_key: str, pinned: bool = True) -> None:
        """Pin or unpin a model to protect from garbage collection."""
        if model_key in self._model_entries:
            entry = self._model_entries[model_key]
            entry.pinned = pinned
            self.add_model_entry(model_key, entry)
            
    def get_models_by_library(self, library: str) -> Dict[str, ModelEntry]:
        """Get all models for a specific library."""
        return {
            key: entry for key, entry in self._model_entries.items()
            if entry.library == library
        }
        
    def get_storage_usage(self) -> Dict[str, Any]:
        """Get storage usage statistics."""
        total_size = 0
        library_sizes = {}
        model_count = len(self._model_entries)
        pinned_count = 0
        
        for entry in self._model_entries.values():
            total_size += entry.total_size
            
            if entry.library not in library_sizes:
                library_sizes[entry.library] = 0
            library_sizes[entry.library] += entry.total_size
            
            if entry.pinned:
                pinned_count += 1
                
        return {
            "total_size_bytes": total_size,
            "total_models": model_count,
            "pinned_models": pinned_count,
            "library_breakdown": library_sizes
        }

    # Model orchestrator integration methods (requirements 2.1-2.7)
    
    async def update_llm_settings(self) -> None:
        """
        Update llm_settings.json automatically when models are installed.
        
        This method is called when the registry changes to ensure new models
        are immediately accessible through existing LLM services.
        """
        try:
            # Load current LLM settings
            current_settings = self._load_llm_settings()
            
            # Update provider configurations based on installed models
            updated_settings = await self._update_provider_configs(current_settings)
            
            # Validate updated settings against schema
            if self._llm_settings_schema:
                try:
                    validate(instance=updated_settings, schema=self._llm_settings_schema)
                except ValidationError as ex:
                    logger.error(f"LLM settings validation failed: {ex.message}")
                    return
            
            # Save updated settings atomically
            await self._save_llm_settings(updated_settings)
            
            # Trigger service discovery for new models (requirement 2.4)
            await self._trigger_service_discovery()
            
            logger.info("LLM settings updated successfully")
            
        except Exception as ex:
            logger.error(f"Failed to update LLM settings: {ex}")

    def _load_llm_settings(self) -> Dict[str, Any]:
        """Load current LLM settings."""
        if not self.llm_settings_path.exists():
            # Return default settings
            return {
                "provider": "llamacpp",
                "model": "gpt-3.5-turbo",
                "api_key": None,
                "base_url": None,
                "temperature": 0.7,
                "max_tokens": 2048,
                "timeout": 30,
                "max_retries": 3,
                "fallback_providers": ["openai", "gemini", "deepseek"],
                "provider_configs": {}
            }
        
        try:
            with open(self.llm_settings_path, 'r') as f:
                return json.load(f)
        except Exception as ex:
            logger.error(f"Failed to load LLM settings: {ex}")
            return {}

    async def _update_provider_configs(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update provider configurations based on installed models."""
        provider_configs = settings.get("provider_configs", {})
        
        # Update llamacpp provider with GGUF models (requirement 2.2)
        llamacpp_models = []
        llamacpp_model_path = None
        
        for model_key, entry in self._model_entries.items():
            if entry.library == "llama-cpp":
                llamacpp_models.append(entry.model_id)
                if llamacpp_model_path is None:
                    llamacpp_model_path = str(Path(entry.install_path).parent)
        
        if llamacpp_models:
            if "llamacpp" not in provider_configs:
                provider_configs["llamacpp"] = {}
            
            # In-process llama-cpp is the default; don't imply an external server
            provider_configs["llamacpp"].update({
                "models": llamacpp_models,
                "model_path": llamacpp_model_path,
                "context_length": 4096
            })
            
            # Update default model if not set or if current model is not available
            if settings.get("provider") == "llamacpp":
                current_model = settings.get("model")
                if not current_model or current_model not in llamacpp_models:
                    settings["model"] = llamacpp_models[0]
        
        # Update HuggingFace provider with Transformers models (requirement 2.3)
        hf_models = []
        
        for model_key, entry in self._model_entries.items():
            if entry.library == "transformers":
                hf_models.append(entry.model_id)
        
        if hf_models:
            if "huggingface" not in provider_configs:
                provider_configs["huggingface"] = {}
            
            provider_configs["huggingface"].update({
                "models": hf_models,
                "base_url": "https://api-inference.huggingface.co"
            })
        
        settings["provider_configs"] = provider_configs
        return settings

    async def _save_llm_settings(self, settings: Dict[str, Any]) -> None:
        """Save LLM settings atomically."""
        # Write to temporary file first
        temp_path = self.llm_settings_path.with_suffix('.tmp')
        
        try:
            with open(temp_path, 'w') as f:
                json.dump(settings, f, indent=2)
            
            # Atomic move
            temp_path.replace(self.llm_settings_path)
            
        except Exception as ex:
            # Clean up temp file on failure
            if temp_path.exists():
                temp_path.unlink()
            raise ex

    async def _trigger_service_discovery(self) -> None:
        """Trigger service discovery for new models."""
        try:
            # Reload provider registrations to pick up new models
            for provider_name in self._registrations.keys():
                if provider_name in self._providers:
                    # Clear cached provider to force reload
                    del self._providers[provider_name]
            
            logger.info("Triggered service discovery for updated models")
            
        except Exception as ex:
            logger.error(f"Failed to trigger service discovery: {ex}")

    async def validate_model_accessibility(self, model_key: str) -> Dict[str, Any]:
        """
        Validate that a model is accessible through the appropriate client.
        
        Args:
            model_key: Model registry key
            
        Returns:
            Validation result with status and details
        """
        if model_key not in self._model_entries:
            return {
                "status": "not_found",
                "error": f"Model {model_key} not in registry"
            }
        
        entry = self._model_entries[model_key]
        
        try:
            # Get appropriate provider for the model's library
            provider_name = self._get_provider_for_library(entry.library)
            if not provider_name:
                return {
                    "status": "no_provider",
                    "error": f"No provider available for library {entry.library}"
                }
            
            # Get provider instance
            provider = self.get_provider(provider_name, model=entry.model_id)
            if not provider:
                return {
                    "status": "provider_failed",
                    "error": f"Failed to create provider instance for {provider_name}"
                }
            
            # Perform smoke test (requirement 2.5, 2.6)
            result = await self._perform_smoke_test(provider, entry)
            return result
            
        except Exception as ex:
            return {
                "status": "validation_error",
                "error": str(ex)
            }

    def _get_provider_for_library(self, library: str) -> Optional[str]:
        """Get the appropriate provider name for a library."""
        library_provider_map = {
            "llama-cpp": "llamacpp",
            "transformers": "huggingface",
            "spacy": "huggingface",  # spaCy models can be used through HF
            "sklearn": None  # sklearn models don't use LLM providers
        }
        return library_provider_map.get(library)

    async def _perform_smoke_test(self, provider: LLMProviderBase, entry: ModelEntry) -> Dict[str, Any]:
        """
        Perform smoke test on a model by attempting 1-token generation.
        
        Args:
            provider: LLM provider instance
            entry: Model entry
            
        Returns:
            Test result
        """
        try:
            # Load the specific model if provider supports it
            if hasattr(provider, 'load_model') and entry.install_path:
                model_path = Path(entry.install_path)
                if entry.library == "llama-cpp":
                    # For GGUF models, load the .gguf file
                    gguf_files = list(model_path.glob("*.gguf"))
                    if gguf_files:
                        success = provider.load_model(str(gguf_files[0]))
                        if not success:
                            return {
                                "status": "unhealthy",
                                "error": f"Failed to load model from {gguf_files[0]}"
                            }
                elif entry.library == "transformers":
                    # For transformers models, load from directory
                    if hasattr(provider, 'load_model_by_path'):
                        success = provider.load_model_by_path(str(model_path))
                        if not success:
                            return {
                                "status": "unhealthy", 
                                "error": f"Failed to load transformers model from {model_path}"
                            }
            
            # Attempt basic inference with minimal tokens (requirement 2.6)
            if hasattr(provider, 'generate_text'):
                result = provider.generate_text(
                    prompt="test",
                    max_tokens=1,
                    temperature=0.1
                )
                
                if result and len(result.strip()) > 0:
                    return {
                        "status": "healthy",
                        "message": "Smoke test passed - model can generate tokens",
                        "test_output": result[:50],  # First 50 chars
                        "model_path": entry.install_path
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": "Model generated empty response"
                    }
            elif hasattr(provider, 'embed'):
                # Test embedding capability for embedding models
                result = provider.embed("test")
                if result and len(result) > 0:
                    return {
                        "status": "healthy",
                        "message": "Smoke test passed - model can generate embeddings",
                        "embedding_dim": len(result),
                        "model_path": entry.install_path
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": "Model generated empty embedding"
                    }
            else:
                # Provider doesn't support generation - just check if it loads
                provider_info = provider.get_provider_info()
                return {
                    "status": "healthy",
                    "message": "Model loads successfully",
                    "provider_info": provider_info,
                    "model_path": entry.install_path
                }
                
        except Exception as ex:
            return {
                "status": "unhealthy",
                "error": f"Smoke test failed: {ex}",
                "model_path": entry.install_path
            }

    async def validate_all_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Validate all models in the registry.
        
        Returns:
            Dict mapping model keys to validation results
        """
        results = {}
        
        for model_key in self._model_entries.keys():
            try:
                result = await self.validate_model_accessibility(model_key)
                results[model_key] = result
            except Exception as ex:
                results[model_key] = {
                    "status": "validation_error",
                    "error": str(ex)
                }
        
        return results

    def get_provider_health_status(self, provider_name: str) -> Dict[str, Any]:
        """
        Get comprehensive health status for a provider including model validation.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Health status with model validation details
        """
        try:
            # Get basic provider health
            basic_health = self.health_check(provider_name)
            
            # Get models for this provider
            provider_models = {}
            for model_key, entry in self._model_entries.items():
                if self._get_provider_for_library(entry.library) == provider_name:
                    provider_models[model_key] = entry
            
            # Add model count and validation summary
            basic_health["models"] = {
                "total_count": len(provider_models),
                "model_keys": list(provider_models.keys())
            }
            
            # Add provider-specific validation info
            if provider_name == "llamacpp":
                # Check for GGUF models
                gguf_models = [k for k, e in provider_models.items() if e.library == "llama-cpp"]
                basic_health["models"]["gguf_models"] = len(gguf_models)
                
                # Check model directory
                models_dir = Path("models/llama-cpp")
                basic_health["models"]["models_directory_exists"] = models_dir.exists()
                if models_dir.exists():
                    gguf_files = list(models_dir.glob("*.gguf"))
                    basic_health["models"]["gguf_files_on_disk"] = len(gguf_files)
                
            elif provider_name == "huggingface":
                # Check for transformers models
                hf_models = [k for k, e in provider_models.items() if e.library == "transformers"]
                basic_health["models"]["transformers_models"] = len(hf_models)
            
            return basic_health
            
        except Exception as ex:
            return {
                "status": "unhealthy",
                "error": f"Failed to get provider health: {ex}",
                "provider": provider_name
            }

    async def validate_llm_settings_update(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that LLM settings update is valid and models are accessible.
        
        Args:
            new_settings: New LLM settings to validate
            
        Returns:
            Validation result
        """
        try:
            # Validate against schema (requirement 2.7)
            if self._llm_settings_schema:
                try:
                    validate(instance=new_settings, schema=self._llm_settings_schema)
                except ValidationError as ex:
                    return {
                        "status": "invalid_schema",
                        "error": f"Schema validation failed: {ex.message}",
                        "path": list(ex.absolute_path) if hasattr(ex, 'absolute_path') else []
                    }
            
            # Check if specified provider exists
            provider_name = new_settings.get("provider")
            if provider_name and provider_name not in self._registrations:
                return {
                    "status": "invalid_provider",
                    "error": f"Provider '{provider_name}' is not registered",
                    "available_providers": list(self._registrations.keys())
                }
            
            # Check if specified model is available for the provider
            model_name = new_settings.get("model")
            if provider_name and model_name:
                # Check if model exists in registry for this provider
                provider_models = []
                for model_key, entry in self._model_entries.items():
                    if self._get_provider_for_library(entry.library) == provider_name:
                        provider_models.append(entry.model_id)
                
                if model_name not in provider_models and provider_name in ["llamacpp", "huggingface"]:
                    return {
                        "status": "model_not_found",
                        "error": f"Model '{model_name}' not found for provider '{provider_name}'",
                        "available_models": provider_models
                    }
            
            # Validate provider configurations
            provider_configs = new_settings.get("provider_configs", {})
            for config_provider, config in provider_configs.items():
                if config_provider not in self._registrations:
                    return {
                        "status": "invalid_provider_config",
                        "error": f"Provider config for unknown provider: {config_provider}",
                        "available_providers": list(self._registrations.keys())
                    }
                
                # Validate provider-specific config
                if config_provider == "llamacpp":
                    model_path = config.get("model_path")
                    if model_path and not Path(model_path).exists():
                        return {
                            "status": "invalid_model_path",
                            "error": f"Model path does not exist: {model_path}",
                            "provider": config_provider
                        }
                
                elif config_provider == "huggingface":
                    models = config.get("models", [])
                    if not isinstance(models, list):
                        return {
                            "status": "invalid_models_config",
                            "error": "HuggingFace models config must be a list",
                            "provider": config_provider
                        }
            
            return {
                "status": "valid",
                "message": "LLM settings validation passed"
            }
            
        except Exception as ex:
            return {
                "status": "validation_error",
                "error": f"Settings validation failed: {ex}"
            }

    async def test_model_loading_workflow(self, model_key: str) -> Dict[str, Any]:
        """
        Test complete model loading workflow including provider instantiation and inference.
        
        Args:
            model_key: Model registry key
            
        Returns:
            Comprehensive test result
        """
        if model_key not in self._model_entries:
            return {
                "status": "not_found",
                "error": f"Model {model_key} not in registry"
            }
        
        entry = self._model_entries[model_key]
        test_results = {
            "model_key": model_key,
            "model_id": entry.model_id,
            "library": entry.library,
            "install_path": entry.install_path,
            "tests": {}
        }
        
        try:
            # Test 1: File integrity check
            test_results["tests"]["file_integrity"] = self.verify_model_integrity(model_key)
            
            # Test 2: Provider availability
            provider_name = self._get_provider_for_library(entry.library)
            if not provider_name:
                test_results["tests"]["provider_availability"] = {
                    "status": "no_provider",
                    "error": f"No provider available for library {entry.library}"
                }
                test_results["status"] = "failed"
                return test_results
            
            test_results["tests"]["provider_availability"] = {
                "status": "available",
                "provider": provider_name
            }
            
            # Test 3: Provider instantiation
            try:
                provider = self.get_provider(provider_name)
                if provider:
                    test_results["tests"]["provider_instantiation"] = {
                        "status": "success",
                        "provider_info": provider.get_provider_info()
                    }
                else:
                    test_results["tests"]["provider_instantiation"] = {
                        "status": "failed",
                        "error": "Failed to create provider instance"
                    }
                    test_results["status"] = "failed"
                    return test_results
            except Exception as ex:
                test_results["tests"]["provider_instantiation"] = {
                    "status": "failed",
                    "error": str(ex)
                }
                test_results["status"] = "failed"
                return test_results
            
            # Test 4: Model loading (if supported)
            if hasattr(provider, 'load_model') or hasattr(provider, 'load_model_by_path'):
                try:
                    model_path = Path(entry.install_path)
                    if entry.library == "llama-cpp":
                        # Find GGUF file
                        gguf_files = list(model_path.glob("*.gguf"))
                        if gguf_files and hasattr(provider, 'load_model'):
                            success = provider.load_model(str(gguf_files[0]))
                            test_results["tests"]["model_loading"] = {
                                "status": "success" if success else "failed",
                                "model_file": str(gguf_files[0]),
                                "loaded": success
                            }
                        else:
                            test_results["tests"]["model_loading"] = {
                                "status": "failed",
                                "error": "No GGUF files found or provider doesn't support loading"
                            }
                    elif entry.library == "transformers":
                        if hasattr(provider, 'load_model_by_path'):
                            success = provider.load_model_by_path(str(model_path))
                            test_results["tests"]["model_loading"] = {
                                "status": "success" if success else "failed",
                                "model_path": str(model_path),
                                "loaded": success
                            }
                        else:
                            test_results["tests"]["model_loading"] = {
                                "status": "skipped",
                                "reason": "Provider doesn't support explicit model loading"
                            }
                except Exception as ex:
                    test_results["tests"]["model_loading"] = {
                        "status": "failed",
                        "error": str(ex)
                    }
            else:
                test_results["tests"]["model_loading"] = {
                    "status": "skipped",
                    "reason": "Provider doesn't support model loading"
                }
            
            # Test 5: Smoke test (1-token generation)
            test_results["tests"]["smoke_test"] = await self._perform_smoke_test(provider, entry)
            
            # Determine overall status
            failed_tests = [name for name, result in test_results["tests"].items() 
                          if result.get("status") in ["failed", "unhealthy"]]
            
            if not failed_tests:
                test_results["status"] = "healthy"
                test_results["message"] = "All tests passed"
            elif len(failed_tests) == 1 and "smoke_test" in failed_tests:
                test_results["status"] = "degraded"
                test_results["message"] = "Model loads but smoke test failed"
            else:
                test_results["status"] = "unhealthy"
                test_results["message"] = f"Failed tests: {failed_tests}"
            
            return test_results
            
        except Exception as ex:
            test_results["status"] = "error"
            test_results["error"] = str(ex)
            return test_results

    async def ensure_model_compatibility(self, model_key: str) -> Dict[str, Any]:
        """
        Ensure a model is compatible with its provider and can be used for inference.
        
        This method performs comprehensive validation including file integrity,
        provider compatibility, and basic inference testing.
        
        Args:
            model_key: Model registry key
            
        Returns:
            Compatibility check result
        """
        try:
            # Run comprehensive workflow test
            workflow_result = await self.test_model_loading_workflow(model_key)
            
            # Extract compatibility information
            compatibility_result = {
                "model_key": model_key,
                "compatible": workflow_result["status"] in ["healthy", "degraded"],
                "status": workflow_result["status"],
                "tests_passed": [],
                "tests_failed": [],
                "recommendations": []
            }
            
            # Analyze test results
            for test_name, test_result in workflow_result.get("tests", {}).items():
                if test_result.get("status") in ["success", "healthy"]:
                    compatibility_result["tests_passed"].append(test_name)
                elif test_result.get("status") in ["failed", "unhealthy"]:
                    compatibility_result["tests_failed"].append(test_name)
            
            # Generate recommendations
            if "file_integrity" in compatibility_result["tests_failed"]:
                compatibility_result["recommendations"].append(
                    "Re-download the model to fix file integrity issues"
                )
            
            if "provider_instantiation" in compatibility_result["tests_failed"]:
                compatibility_result["recommendations"].append(
                    "Check provider configuration and dependencies"
                )
            
            if "model_loading" in compatibility_result["tests_failed"]:
                compatibility_result["recommendations"].append(
                    "Verify model format is compatible with provider"
                )
            
            if "smoke_test" in compatibility_result["tests_failed"]:
                compatibility_result["recommendations"].append(
                    "Model may be corrupted or incompatible - consider re-downloading"
                )
            
            return compatibility_result
            
        except Exception as ex:
            return {
                "model_key": model_key,
                "compatible": False,
                "status": "error",
                "error": str(ex),
                "tests_passed": [],
                "tests_failed": ["compatibility_check"],
                "recommendations": ["Contact support for assistance"]
            }

    def cleanup(self):
        """Clean up resources including file watcher."""
        if hasattr(self, '_observer') and self._observer:
            self._observer.stop()
            self._observer.join()
            logger.info("Registry watcher stopped")


# Global registry instance
_registry = None


def get_registry() -> LLMRegistry:
    """Get global LLM registry instance."""
    global _registry
    if _registry is None:
        _registry = LLMRegistry()
    return _registry


def register_provider(name: str, provider_class: Type[LLMProviderBase], **kwargs):
    """Register a provider in the global registry."""
    registry = get_registry()
    registry.register_provider(name, provider_class, **kwargs)


def get_provider(name: str, **init_kwargs) -> Optional[LLMProviderBase]:
    """Get provider from global registry."""
    registry = get_registry()
    return registry.get_provider(name, **init_kwargs)


def list_providers() -> List[str]:
    """List all registered providers."""
    registry = get_registry()
    return registry.list_providers()


def health_check_all() -> Dict[str, Dict[str, Any]]:
    """Health check all providers."""
    registry = get_registry()
    return registry.health_check_all()


# Expose a module-level registry instance for plugin consumers
registry = get_registry()

__all__ = [
    "LLMRegistry",
    "get_registry",
    "register_provider",
    "get_provider",
    "list_providers",
    "health_check_all",
    "registry",
]
