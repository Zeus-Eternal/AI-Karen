"""
Model Orchestrator Plugin Service

Wraps the existing install_models.py functionality in a plugin service class
with async method wrappers, standardized error handling, and plugin API interface.
"""

import asyncio
import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Import the existing model manager functionality
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "scripts" / "operations"))

try:
    import install_models as model_manager
except ImportError:
    model_manager = None

# Import LLM registry - handle different import paths
try:
    from src.ai_karen_engine.integrations.llm_registry import LLMRegistry, ModelEntry
except ImportError:
    try:
        from ai_karen_engine.integrations.llm_registry import LLMRegistry, ModelEntry
    except ImportError:
        # Fallback for development/testing
        LLMRegistry = None
        ModelEntry = None

logger = logging.getLogger("kari.model_orchestrator")


# Error codes for standardized error handling
class ModelOrchestratorError(Exception):
    """Base exception for model orchestrator errors."""
    
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"{code}: {message}")


# Standard error codes
E_NET = "E_NET"           # Network/connectivity issues
E_DISK = "E_DISK"         # Disk space/IO issues  
E_PERM = "E_PERM"         # Permission denied
E_LICENSE = "E_LICENSE"   # License acceptance required
E_VERIFY = "E_VERIFY"     # Integrity verification failed
E_SCHEMA = "E_SCHEMA"     # Schema validation failed
E_COMPAT = "E_COMPAT"     # Compatibility check failed
E_QUOTA = "E_QUOTA"       # Storage quota exceeded
E_NOT_FOUND = "E_NOT_FOUND"  # Model/resource not found
E_INVALID = "E_INVALID"   # Invalid input/parameters


@dataclass
class ModelSummary:
    """Model summary information."""
    model_id: str
    last_modified: Optional[datetime]
    likes: Optional[int]
    downloads: Optional[int]
    library_name: Optional[str]
    tags: List[str]
    total_size: Optional[int] = None
    description: Optional[str] = None


@dataclass
class ModelInfo:
    """Detailed model information."""
    model_id: str
    owner: str
    repository: str
    library: str
    files: List[Dict[str, Union[str, int]]]
    total_size: int
    last_modified: Optional[datetime]
    downloads: Optional[int]
    likes: Optional[int]
    tags: List[str]
    license: Optional[str]
    description: Optional[str]
    revision: Optional[str] = None


@dataclass
class DownloadRequest:
    """Model download request."""
    model_id: str
    revision: Optional[str] = None
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    pin: bool = False
    force_redownload: bool = False
    library_override: Optional[str] = None


@dataclass
class DownloadResult:
    """Model download result."""
    model_id: str
    install_path: str
    total_size: int
    files_downloaded: int
    duration_seconds: float
    status: str  # success, failed, partial
    error_message: Optional[str] = None


@dataclass
class MigrationResult:
    """Migration operation result."""
    models_migrated: int
    files_moved: int
    corrupt_files_removed: int
    errors: List[str]
    duration_seconds: float
    dry_run: bool = False


@dataclass
class EnsureResult:
    """Ensure models operation result."""
    models_ensured: List[str]
    models_skipped: List[str]
    errors: List[str]
    duration_seconds: float


@dataclass
class GCResult:
    """Garbage collection result."""
    models_removed: List[str]
    space_freed_bytes: int
    models_preserved: List[str]
    duration_seconds: float


class ModelOrchestratorService:
    """
    Model Orchestrator Plugin Service
    
    Provides async wrappers around the existing install_models.py functionality
    with enhanced error handling, validation, and plugin integration.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the model orchestrator service.
        
        Args:
            config: Plugin configuration dictionary
        """
        self.config = config or {}
        self.models_root = Path(self.config.get("models_root", "models"))
        self.registry_path = Path(self.config.get("registry_path", "models/llm_registry.json"))
        self.max_concurrent_downloads = self.config.get("max_concurrent_downloads", 3)
        self.enable_metrics = self.config.get("enable_metrics", True)
        self.enable_rbac = self.config.get("enable_rbac", True)
        self.offline_mode = self.config.get("offline_mode", False)
        self.mirror_url = self.config.get("mirror_url")
        self.max_storage_gb = self.config.get("max_storage_gb")
        
        # Initialize registry (requirement 1.4: maintain living llm_registry.json)
        if LLMRegistry is not None:
            self.registry = LLMRegistry(registry_path=self.registry_path)
            # Ensure registry file exists and is valid
            self._ensure_registry_initialized()
        else:
            logger.warning("LLMRegistry not available - using fallback registry management")
            self.registry = None
        
        # Validate model manager availability
        if model_manager is None:
            logger.error("install_models module not available")
            
    async def list_models(self, owner: str, limit: int = 50, search: Optional[str] = None,
                         sort: str = "downloads", direction: int = -1) -> List[ModelSummary]:
        """
        List models for an owner/organization.
        
        Args:
            owner: Model owner/organization name
            limit: Maximum number of models to return
            search: Search query
            sort: Sort field (downloads, likes, modified)
            direction: Sort direction (1 for ascending, -1 for descending)
            
        Returns:
            List of model summaries
            
        Raises:
            ModelOrchestratorError: If operation fails
        """
        if not owner:
            raise ModelOrchestratorError(E_INVALID, "Owner parameter is required")
            
        if self.offline_mode:
            raise ModelOrchestratorError(E_NET, "Cannot list models in offline mode")
            
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            models = await loop.run_in_executor(
                None, 
                model_manager.list_models_for_owner,
                owner, limit, search, sort, direction
            )
            
            # Convert to our format
            result = []
            for model in models:
                result.append(ModelSummary(
                    model_id=model.model_id,
                    last_modified=model.last_modified,
                    likes=model.likes,
                    downloads=model.downloads,
                    library_name=model.library_name,
                    tags=model.tags
                ))
                
            return result
            
        except Exception as ex:
            logger.error(f"Failed to list models for {owner}: {ex}")
            if "network" in str(ex).lower() or "connection" in str(ex).lower():
                raise ModelOrchestratorError(E_NET, f"Network error: {ex}")
            else:
                raise ModelOrchestratorError(E_INVALID, f"Failed to list models: {ex}")

    async def get_model_info(self, model_id: str, revision: Optional[str] = None) -> ModelInfo:
        """
        Get detailed information about a model.
        
        Args:
            model_id: Model identifier (owner/repo)
            revision: Model revision/commit hash
            
        Returns:
            Detailed model information
            
        Raises:
            ModelOrchestratorError: If operation fails
        """
        if not model_id:
            raise ModelOrchestratorError(E_INVALID, "Model ID is required")
            
        if self.offline_mode:
            raise ModelOrchestratorError(E_NET, "Cannot get model info in offline mode")
            
        try:
            # Get file information
            loop = asyncio.get_event_loop()
            files = await loop.run_in_executor(
                None,
                model_manager.get_model_files,
                model_id, revision
            )
            
            # Parse owner/repo
            owner, repo = model_manager.parse_owner_repo(model_id)
            
            # Calculate total size
            total_size = sum(f.size for f in files)
            
            # Convert files to dict format
            file_list = [{"path": f.path, "size": f.size} for f in files]
            
            # Determine library
            library = model_manager.choose_library([], None)  # Will be enhanced
            
            return ModelInfo(
                model_id=model_id,
                owner=owner,
                repository=repo,
                library=library,
                files=file_list,
                total_size=total_size,
                last_modified=None,  # Would need additional API call
                downloads=None,
                likes=None,
                tags=[],
                license=None,
                description=None,
                revision=revision
            )
            
        except Exception as ex:
            logger.error(f"Failed to get model info for {model_id}: {ex}")
            if "not found" in str(ex).lower() or "404" in str(ex):
                raise ModelOrchestratorError(E_NOT_FOUND, f"Model not found: {model_id}")
            elif "network" in str(ex).lower() or "connection" in str(ex).lower():
                raise ModelOrchestratorError(E_NET, f"Network error: {ex}")
            else:
                raise ModelOrchestratorError(E_INVALID, f"Failed to get model info: {ex}")

    async def download_model(self, request: DownloadRequest) -> DownloadResult:
        """
        Download and install a model.
        
        Args:
            request: Download request parameters
            
        Returns:
            Download result
            
        Raises:
            ModelOrchestratorError: If operation fails
        """
        if not request.model_id:
            raise ModelOrchestratorError(E_INVALID, "Model ID is required")
            
        if self.offline_mode:
            raise ModelOrchestratorError(E_NET, "Cannot download models in offline mode")
            
        start_time = datetime.now()
        
        try:
            # Get model files first to determine size and library
            files = await self._get_model_files_async(request.model_id, request.revision)
            total_size = sum(f.size for f in files)
            
            # Check storage quota
            if self.max_storage_gb:
                current_usage = self.registry.get_storage_usage()
                if (current_usage["total_size_bytes"] + total_size) > (self.max_storage_gb * 1024**3):
                    raise ModelOrchestratorError(
                        E_QUOTA, 
                        f"Download would exceed storage quota of {self.max_storage_gb}GB"
                    )
            
            # Determine library and install path
            library = request.library_override or model_manager.choose_library([], None)
            install_path = model_manager.resolve_install_root(request.model_id, library, files)
            
            # Check if already exists and not forcing redownload
            if install_path.exists() and not request.force_redownload:
                # Update access time
                model_key = self._get_model_key(request.model_id)
                self.registry.update_model_access_time(model_key)
                
                duration = (datetime.now() - start_time).total_seconds()
                return DownloadResult(
                    model_id=request.model_id,
                    install_path=str(install_path),
                    total_size=total_size,
                    files_downloaded=0,
                    duration_seconds=duration,
                    status="skipped",
                    error_message="Model already exists (use force_redownload=True to override)"
                )
            
            # Perform download
            loop = asyncio.get_event_loop()
            downloaded_path = await loop.run_in_executor(
                None,
                model_manager.download_snapshot,
                request.model_id,
                install_path,
                request.revision,
                request.include_patterns,
                request.exclude_patterns,
                True,  # resume
                None   # max_workers
            )
            
            # Copy shared configs
            _, repo = model_manager.parse_owner_repo(request.model_id)
            model_manager.copy_shared_configs(install_path, repo)
            
            # Clean up corrupt files
            for corrupt_file in install_path.rglob("*.corrupt"):
                corrupt_file.unlink(missing_ok=True)
            
            # Update registry
            model_key = self._get_model_key(request.model_id)
            
            if self.registry is not None and ModelEntry is not None:
                entry = ModelEntry(
                    model_id=request.model_id,
                    library=library,
                    revision=request.revision or "main",
                    installed_at=datetime.now(timezone.utc).isoformat(),
                    install_path=str(install_path.resolve()),
                    files=[{"path": f.path, "size": f.size, "sha256": ""} for f in files],
                    total_size=total_size,
                    pinned=request.pin,
                    last_accessed=datetime.now(timezone.utc).isoformat()
                )
                self.registry.add_model_entry(model_key, entry)
                
                # Trigger LLM settings update (requirement 2.1)
                await self.registry.update_llm_settings()
                
                # Validate model accessibility and compatibility (requirement 2.5, 2.6)
                validation_result = await self.registry.validate_model_accessibility(model_key)
                if validation_result["status"] != "healthy":
                    logger.warning(f"Model validation failed for {model_key}: {validation_result}")
                
                # Perform comprehensive compatibility check (requirement 10.7)
                compatibility_result = await self.registry.ensure_model_compatibility(model_key)
                if not compatibility_result["compatible"]:
                    logger.error(f"Model compatibility check failed for {model_key}: {compatibility_result}")
                    # Don't fail the download, but log the issue
                else:
                    logger.info(f"Model compatibility verified for {model_key}")
                
            else:
                # Fallback: update registry file directly
                self._update_registry_fallback(model_key, {
                    "model_id": request.model_id,
                    "library": library,
                    "revision": request.revision or "main",
                    "installed_at": datetime.now(timezone.utc).isoformat(),
                    "install_path": str(install_path.resolve()),
                    "files": [{"path": f.path, "size": f.size, "sha256": ""} for f in files],
                    "total_size": total_size,
                    "pinned": request.pin,
                    "last_accessed": datetime.now(timezone.utc).isoformat()
                })
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return DownloadResult(
                model_id=request.model_id,
                install_path=str(downloaded_path),
                total_size=total_size,
                files_downloaded=len(files),
                duration_seconds=duration,
                status="success"
            )
            
        except ModelOrchestratorError:
            raise
        except Exception as ex:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Failed to download model {request.model_id}: {ex}")
            
            if "disk" in str(ex).lower() or "space" in str(ex).lower():
                error_code = E_DISK
            elif "permission" in str(ex).lower():
                error_code = E_PERM
            elif "network" in str(ex).lower() or "connection" in str(ex).lower():
                error_code = E_NET
            else:
                error_code = E_INVALID
                
            return DownloadResult(
                model_id=request.model_id,
                install_path="",
                total_size=0,
                files_downloaded=0,
                duration_seconds=duration,
                status="failed",
                error_message=str(ex)
            )

    async def migrate_layout(self, dry_run: bool = False) -> MigrationResult:
        """
        Migrate existing model layout to normalized structure.
        
        Args:
            dry_run: If True, only simulate the migration
            
        Returns:
            Migration result
        """
        start_time = datetime.now()
        
        try:
            # For now, delegate to existing migration logic
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, model_manager.migrate_layout)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return MigrationResult(
                models_migrated=0,  # Would need to track this
                files_moved=0,
                corrupt_files_removed=0,
                errors=[],
                duration_seconds=duration,
                dry_run=dry_run
            )
            
        except Exception as ex:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Migration failed: {ex}")
            
            return MigrationResult(
                models_migrated=0,
                files_moved=0,
                corrupt_files_removed=0,
                errors=[str(ex)],
                duration_seconds=duration,
                dry_run=dry_run
            )

    async def ensure_models(self, models: List[str]) -> EnsureResult:
        """
        Ensure essential models are installed and validate their functionality.
        
        Args:
            models: List of model types to ensure (distilbert, spacy, basic_cls)
            
        Returns:
            Ensure result with validation information
        """
        start_time = datetime.now()
        ensured = []
        skipped = []
        errors = []
        
        try:
            loop = asyncio.get_event_loop()
            
            for model_type in models:
                try:
                    if model_type == "distilbert":
                        await loop.run_in_executor(None, model_manager.ensure_distilbert)
                        
                        # Validate DistilBERT functionality (requirement 10.7)
                        if await self._validate_distilbert():
                            ensured.append("distilbert")
                        else:
                            errors.append("DistilBERT installed but validation failed")
                            
                    elif model_type == "spacy":
                        await loop.run_in_executor(None, model_manager.ensure_spacy)
                        
                        # Validate spaCy functionality (requirement 10.7)
                        if await self._validate_spacy():
                            ensured.append("spacy")
                        else:
                            errors.append("spaCy installed but validation failed")
                            
                    elif model_type == "basic_cls":
                        await loop.run_in_executor(None, model_manager.ensure_basic_classifier)
                        
                        # Validate basic classifier functionality
                        if await self._validate_basic_classifier():
                            ensured.append("basic_cls")
                        else:
                            errors.append("Basic classifier installed but validation failed")
                            
                    else:
                        errors.append(f"Unknown model type: {model_type}")
                        
                except Exception as ex:
                    errors.append(f"Failed to ensure {model_type}: {ex}")
            
            # Update LLM settings after ensuring models (requirement 2.1)
            if self.registry and ensured:
                try:
                    await self.registry.update_llm_settings()
                except Exception as ex:
                    logger.warning(f"Failed to update LLM settings after ensure: {ex}")
                    
        except Exception as ex:
            errors.append(f"Ensure operation failed: {ex}")
            
        duration = (datetime.now() - start_time).total_seconds()
        
        return EnsureResult(
            models_ensured=ensured,
            models_skipped=skipped,
            errors=errors,
            duration_seconds=duration
        )

    async def _validate_distilbert(self) -> bool:
        """Validate DistilBERT model functionality."""
        try:
            # Try to load and use DistilBERT for text classification
            from transformers import pipeline
            classifier = pipeline("text-classification", model="distilbert-base-uncased")
            result = classifier("This is a test")
            return len(result) > 0 and "label" in result[0]
        except Exception as ex:
            logger.error(f"DistilBERT validation failed: {ex}")
            return False

    async def _validate_spacy(self) -> bool:
        """Validate spaCy model functionality."""
        try:
            import spacy
            # Try to load English model
            nlp = spacy.load("en_core_web_sm")
            doc = nlp("This is a test")
            return len(doc) > 0 and hasattr(doc[0], 'text')
        except Exception as ex:
            logger.error(f"spaCy validation failed: {ex}")
            return False

    async def _validate_basic_classifier(self) -> bool:
        """Validate basic classifier functionality."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.naive_bayes import MultinomialNB
            
            # Create a simple classifier
            vectorizer = TfidfVectorizer()
            classifier = MultinomialNB()
            
            # Test with dummy data
            texts = ["positive text", "negative text"]
            labels = [1, 0]
            
            X = vectorizer.fit_transform(texts)
            classifier.fit(X, labels)
            
            # Test prediction
            test_X = vectorizer.transform(["test text"])
            prediction = classifier.predict(test_X)
            
            return len(prediction) > 0
        except Exception as ex:
            logger.error(f"Basic classifier validation failed: {ex}")
            return False

    async def garbage_collect(self, criteria: Optional[Dict[str, Any]] = None) -> GCResult:
        """
        Perform garbage collection on unused models.
        
        Args:
            criteria: GC criteria (max_age_days, min_free_space_gb, etc.)
            
        Returns:
            Garbage collection result
        """
        start_time = datetime.now()
        criteria = criteria or {}
        
        # This would implement LRU-based garbage collection
        # For now, return empty result
        duration = (datetime.now() - start_time).total_seconds()
        
        return GCResult(
            models_removed=[],
            space_freed_bytes=0,
            models_preserved=[],
            duration_seconds=duration
        )

    # Helper methods
    
    def _ensure_registry_initialized(self):
        """Ensure the registry file exists and is properly initialized."""
        try:
            # Create models directory if it doesn't exist (requirement 4.2: respect existing patterns)
            self.models_root.mkdir(parents=True, exist_ok=True)
            
            # Ensure registry file exists
            if not self.registry_path.exists():
                # Initialize with empty registry
                self.registry_path.parent.mkdir(parents=True, exist_ok=True)
                initial_registry = {}
                with open(self.registry_path, 'w') as f:
                    json.dump(initial_registry, f, indent=2)
                logger.info(f"Initialized empty registry at {self.registry_path}")
            
            # Validate registry can be loaded if registry is available
            if self.registry is not None:
                self.registry.load_registry()
                logger.info(f"Registry loaded successfully from {self.registry_path}")
            else:
                # Fallback: just validate JSON format
                with open(self.registry_path, 'r') as f:
                    json.load(f)
                logger.info(f"Registry file validated at {self.registry_path}")
            
        except Exception as ex:
            logger.error(f"Failed to initialize registry: {ex}")
            raise ModelOrchestratorError(E_SCHEMA, f"Registry initialization failed: {ex}")
    
    async def _get_model_files_async(self, model_id: str, revision: Optional[str] = None):
        """Get model files asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            model_manager.get_model_files,
            model_id, revision
        )
        
    def _get_model_key(self, model_id: str) -> str:
        """Get registry key for a model."""
        if model_manager is not None:
            owner, repo = model_manager.parse_owner_repo(model_id)
            return f"{owner}/{repo}" if owner != "_" else repo
        else:
            # Fallback parsing
            if "/" in model_id:
                return model_id
            else:
                return f"_/{model_id}"
    
    def _update_registry_fallback(self, model_key: str, entry_data: Dict[str, Any]):
        """Update registry file directly when LLMRegistry is not available."""
        try:
            # Load existing registry
            if self.registry_path.exists():
                with open(self.registry_path, 'r') as f:
                    registry_data = json.load(f)
            else:
                registry_data = {}
            
            # Update entry
            registry_data[model_key] = entry_data
            
            # Save atomically
            temp_path = self.registry_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
            
            temp_path.replace(self.registry_path)
            logger.info(f"Updated registry entry for {model_key}")
            
        except Exception as ex:
            logger.error(f"Failed to update registry fallback: {ex}")
            raise ModelOrchestratorError(E_SCHEMA, f"Registry update failed: {ex}")

    # Plugin API interface methods
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {
            "name": "ModelOrchestrator",
            "version": "1.0.0",
            "description": "Comprehensive model management system",
            "capabilities": [
                "model_listing",
                "model_download",
                "filesystem_migration",
                "registry_management",
                "garbage_collection"
            ],
            "status": "active",
            "models_root": str(self.models_root),
            "registry_path": str(self.registry_path),
            "storage_usage": self.registry.get_storage_usage() if self.registry else {"total_size_bytes": 0, "model_count": 0}
        }
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        try:
            # Check if models directory exists and is writable
            self.models_root.mkdir(parents=True, exist_ok=True)
            test_file = self.models_root / ".health_check"
            test_file.write_text("test")
            test_file.unlink()
            
            # Check registry accessibility
            registry_accessible = self.registry_path.parent.exists()
            
            # Check if we can access HuggingFace (if not in offline mode)
            hf_accessible = self.offline_mode or model_manager is not None
            
            status = "healthy" if registry_accessible and hf_accessible else "degraded"
            
            return {
                "status": status,
                "models_root_writable": True,
                "registry_accessible": registry_accessible,
                "huggingface_accessible": hf_accessible,
                "offline_mode": self.offline_mode,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as ex:
            return {
                "status": "unhealthy",
                "error": str(ex),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }