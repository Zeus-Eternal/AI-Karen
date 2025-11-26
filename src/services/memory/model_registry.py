"""
Enhanced Model Registry for Model Library

This module provides an enhanced model registry that extends the existing model_registry.json
structure to support download metadata, remote repositories, and comprehensive model management.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum

logger = logging.getLogger("kari.model_registry")

class ModelStatus(Enum):
    """Model status enumeration."""
    LOCAL = "local"
    AVAILABLE = "available"
    DOWNLOADING = "downloading"
    ERROR = "error"
    UNKNOWN = "unknown"

class ModelSource(Enum):
    """Model source enumeration."""
    LOCAL = "local"
    DOWNLOADED = "downloaded"
    HF_HUB = "hf_hub"
    REMOTE = "remote"

@dataclass
class ModelMetadata:
    """Model metadata structure."""
    parameters: str
    quantization: str
    memory_requirement: str
    context_length: int
    license: str
    tags: List[str]
    architecture: Optional[str] = None
    training_data: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None

@dataclass
class DownloadInfo:
    """Download information structure."""
    url: str
    filename: str
    checksum: Optional[str] = None
    mirrors: Optional[List[str]] = None
    download_date: Optional[float] = None

@dataclass
class Repository:
    """Repository information structure."""
    name: str
    base_url: str
    type: str
    description: Optional[str] = None
    auth_required: bool = False

@dataclass
class ModelEntry:
    """Complete model entry structure."""
    id: str
    name: str
    provider: str
    type: str
    source: ModelSource
    path: Optional[str] = None
    size: Optional[int] = None
    description: Optional[str] = None
    capabilities: Optional[List[str]] = None
    metadata: Optional[ModelMetadata] = None
    download_info: Optional[DownloadInfo] = None
    status: ModelStatus = ModelStatus.UNKNOWN
    last_updated: Optional[float] = None

class EnhancedModelRegistry:
    """Enhanced model registry with download metadata and remote repository support."""
    
    def __init__(self, registry_path: str = "model_registry.json"):
        self.registry_path = Path(registry_path)
        self.models: Dict[str, ModelEntry] = {}
        self.repositories: Dict[str, Repository] = {}
        self.predefined_models: Dict[str, Dict[str, Any]] = {}
        
        # Load existing registry
        self._load_registry()
        
        # Initialize predefined models
        self._initialize_predefined_models()
    
    def _load_registry(self):
        """Load existing model registry and convert to enhanced format."""
        if not self.registry_path.exists():
            logger.info(f"Registry file {self.registry_path} not found, creating new registry")
            self._create_default_registry()
            return
        
        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
            
            # Handle both old list format and new dict format
            if isinstance(data, list):
                # Convert old format to new format
                registry_data = {
                    "models": data,
                    "repositories": [],
                    "predefined_models": []
                }
            else:
                registry_data = data
            
            # Load models
            for model_data in registry_data.get("models", []):
                model_entry = self._convert_to_model_entry(model_data)
                if model_entry:
                    self.models[model_entry.id] = model_entry
            
            # Load repositories - always ensure default repositories exist
            self._create_default_repositories()
            for repo_data in registry_data.get("repositories", []):
                repo = Repository(**repo_data)
                self.repositories[repo.name] = repo
            
            # Load predefined models
            for predefined_data in registry_data.get("predefined_models", []):
                model_id = predefined_data.get("id")
                if model_id:
                    self.predefined_models[model_id] = predefined_data
            
            logger.info(f"Loaded {len(self.models)} models and {len(self.repositories)} repositories")
            
        except Exception as e:
            logger.error(f"Failed to load model registry: {e}")
            self._create_default_registry()
    
    def _convert_to_model_entry(self, model_data: Dict[str, Any]) -> Optional[ModelEntry]:
        """Convert registry data to ModelEntry."""
        try:
            model_id = model_data.get("id", model_data.get("name", ""))
            if not model_id:
                logger.warning("Model entry missing ID, skipping")
                return None
            
            # Convert metadata if present
            metadata = None
            if "metadata" in model_data:
                metadata_data = model_data["metadata"]
                if isinstance(metadata_data, dict):
                    metadata = ModelMetadata(
                        parameters=metadata_data.get("parameters", "unknown"),
                        quantization=metadata_data.get("quantization", "none"),
                        memory_requirement=metadata_data.get("memoryRequirement", 
                                                           metadata_data.get("memory_requirement", "unknown")),
                        context_length=metadata_data.get("contextLength", 
                                                       metadata_data.get("context_length", 0)),
                        license=metadata_data.get("license", "unknown"),
                        tags=metadata_data.get("tags", []),
                        architecture=metadata_data.get("architecture"),
                        training_data=metadata_data.get("trainingData", 
                                                      metadata_data.get("training_data")),
                        performance_metrics=metadata_data.get("performanceMetrics", 
                                                            metadata_data.get("performance_metrics"))
                    )
            
            # Convert download info if present
            download_info = None
            if "downloadInfo" in model_data or "download_info" in model_data:
                download_data = model_data.get("downloadInfo", model_data.get("download_info", {}))
                if isinstance(download_data, dict) and download_data.get("url"):
                    download_info = DownloadInfo(
                        url=download_data["url"],
                        filename=download_data.get("filename", ""),
                        checksum=download_data.get("checksum"),
                        mirrors=download_data.get("mirrors", []),
                        download_date=download_data.get("downloadDate", download_data.get("download_date"))
                    )
            
            # Determine status
            status = ModelStatus.UNKNOWN
            model_path = model_data.get("path")
            if model_path and Path(model_path).exists():
                status = ModelStatus.LOCAL
            elif download_info:
                status = ModelStatus.AVAILABLE
            
            # Determine source
            source_str = model_data.get("source", "local")
            try:
                source = ModelSource(source_str)
            except ValueError:
                source = ModelSource.LOCAL
            
            return ModelEntry(
                id=model_id,
                name=model_data.get("name", model_id),
                provider=model_data.get("provider", model_data.get("type", "unknown")),
                type=model_data.get("type", "unknown"),
                source=source,
                path=model_data.get("path"),
                size=model_data.get("size"),
                description=model_data.get("description"),
                capabilities=model_data.get("capabilities", []),
                metadata=metadata,
                download_info=download_info,
                status=status,
                last_updated=model_data.get("last_updated", time.time())
            )
            
        except Exception as e:
            logger.error(f"Failed to convert model data to ModelEntry: {e}")
            return None
    
    def _create_default_registry(self):
        """Create default registry with basic repositories."""
        self._create_default_repositories()
        logger.info("Created default registry with standard repositories")
    
    def _create_default_repositories(self):
        """Create default repositories if they don't exist."""
        default_repos = {
            "huggingface": Repository(
                name="huggingface",
                base_url="https://huggingface.co",
                type="gguf",
                description="Hugging Face model repository with GGUF format models"
            ),
            "huggingface-transformers": Repository(
                name="huggingface-transformers",
                base_url="https://huggingface.co",
                type="transformers",
                description="Hugging Face transformers model repository"
            )
        }
        
        for repo_name, repo in default_repos.items():
            if repo_name not in self.repositories:
                self.repositories[repo_name] = repo
    
    def _initialize_predefined_models(self):
        """Initialize predefined model configurations."""
        self.predefined_models.update({
            "tinyllama-1.1b-chat-q4": {
                "id": "tinyllama-1.1b-chat-q4",
                "name": "TinyLlama 1.1B Chat Q4_K_M",
                "provider": "llama-cpp",
                "size": 669000000,
                "description": "A compact 1.1B parameter language model optimized for chat applications with Q4_K_M quantization for efficient inference.",
                "capabilities": ["text-generation", "chat", "local-inference", "low-memory"],
                "metadata": {
                    "parameters": "1.1B",
                    "quantization": "Q4_K_M",
                    "memory_requirement": "~1GB",
                    "context_length": 2048,
                    "license": "Apache 2.0",
                    "tags": ["chat", "small", "efficient", "quantized"],
                    "architecture": "Llama",
                    "training_data": "SlimPajama, Starcoderdata",
                    "performance_metrics": {
                        "inference_speed": "fast",
                        "memory_efficiency": "high",
                        "quality_score": "good"
                    }
                },
                "download_info": {
                    "url": "https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
                    "filename": "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf",
                    "checksum": "sha256:placeholder_checksum_for_validation",
                    "mirrors": []
                }
            },
            "tinyllama-1.1b-instruct-q4": {
                "id": "tinyllama-1.1b-instruct-q4",
                "name": "TinyLlama 1.1B Instruct Q4_K_M",
                "provider": "llama-cpp",
                "size": 669000000,
                "description": "TinyLlama model fine-tuned for instruction following with Q4_K_M quantization.",
                "capabilities": ["text-generation", "instruction-following", "local-inference", "low-memory"],
                "metadata": {
                    "parameters": "1.1B",
                    "quantization": "Q4_K_M",
                    "memory_requirement": "~1GB",
                    "context_length": 2048,
                    "license": "Apache 2.0",
                    "tags": ["instruct", "small", "efficient", "quantized"],
                    "architecture": "Llama",
                    "training_data": "SlimPajama, Starcoderdata + Instruction tuning",
                    "performance_metrics": {
                        "inference_speed": "fast",
                        "memory_efficiency": "high",
                        "instruction_following": "good"
                    }
                },
                "download_info": {
                    "url": "https://huggingface.co/TinyLlama/TinyLlama-1.1B-Instruct-v0.1-GGUF/resolve/main/tinyllama-1.1b-instruct-v0.1.Q4_K_M.gguf",
                    "filename": "tinyllama-1.1b-instruct-v0.1.Q4_K_M.gguf",
                    "checksum": "sha256:placeholder_checksum_for_validation",
                    "mirrors": []
                }
            }
        })
    
    def save_registry(self):
        """Save registry to file."""
        try:
            # Convert to serializable format
            registry_data = {
                "models": [self._model_entry_to_dict(model) for model in self.models.values()],
                "repositories": [asdict(repo) for repo in self.repositories.values()],
                "predefined_models": list(self.predefined_models.values())
            }
            
            # Create backup if file exists
            if self.registry_path.exists():
                backup_path = self.registry_path.with_suffix('.json.backup')
                self.registry_path.rename(backup_path)
            
            with open(self.registry_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
            
            logger.info(f"Saved registry with {len(self.models)} models")
            
        except Exception as e:
            logger.error(f"Failed to save model registry: {e}")
            raise
    
    def _model_entry_to_dict(self, model: ModelEntry) -> Dict[str, Any]:
        """Convert ModelEntry to dictionary for serialization."""
        data = {
            "id": model.id,
            "name": model.name,
            "provider": model.provider,
            "type": model.type,
            "source": model.source.value,
            "last_updated": model.last_updated
        }
        
        if model.path:
            data["path"] = model.path
        if model.size:
            data["size"] = model.size
        if model.description:
            data["description"] = model.description
        if model.capabilities:
            data["capabilities"] = model.capabilities
        if model.metadata:
            data["metadata"] = asdict(model.metadata)
        if model.download_info:
            data["downloadInfo"] = asdict(model.download_info)
        
        return data
    
    def add_model(self, model: ModelEntry) -> bool:
        """Add a new model to the registry."""
        try:
            if model.id in self.models:
                logger.warning(f"Model {model.id} already exists, updating")
            
            model.last_updated = time.time()
            self.models[model.id] = model
            
            logger.info(f"Added model {model.id} to registry")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add model {model.id}: {e}")
            return False
    
    def remove_model(self, model_id: str) -> bool:
        """Remove a model from the registry."""
        try:
            if model_id not in self.models:
                logger.warning(f"Model {model_id} not found in registry")
                return False
            
            del self.models[model_id]
            logger.info(f"Removed model {model_id} from registry")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove model {model_id}: {e}")
            return False
    
    def get_model(self, model_id: str) -> Optional[ModelEntry]:
        """Get a model by ID."""
        return self.models.get(model_id)
    
    def list_models(self, provider: Optional[str] = None, 
                   status: Optional[ModelStatus] = None) -> List[ModelEntry]:
        """List models with optional filtering."""
        models = list(self.models.values())
        
        if provider:
            models = [m for m in models if m.provider == provider]
        
        if status:
            models = [m for m in models if m.status == status]
        
        return models
    
    def update_model_status(self, model_id: str, status: ModelStatus, 
                           path: Optional[str] = None) -> bool:
        """Update model status and optionally path."""
        try:
            if model_id not in self.models:
                logger.warning(f"Model {model_id} not found in registry")
                return False
            
            model = self.models[model_id]
            model.status = status
            model.last_updated = time.time()
            
            if path:
                model.path = path
                # Update size if file exists
                if Path(path).exists():
                    try:
                        model.size = Path(path).stat().st_size
                    except Exception as e:
                        logger.warning(f"Failed to get file size for {path}: {e}")
            
            logger.info(f"Updated model {model_id} status to {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update model {model_id} status: {e}")
            return False
    
    def discover_models(self, repository_name: str) -> List[Dict[str, Any]]:
        """Discover available models from a repository."""
        if repository_name not in self.repositories:
            logger.error(f"Repository {repository_name} not found")
            return []
        
        # For now, return predefined models that match the repository
        # In a full implementation, this would query the actual repository
        repo = self.repositories[repository_name]
        discovered = []
        
        for model_id, model_data in self.predefined_models.items():
            if model_data.get("provider") in ["llama-cpp"] and repo.type == "gguf":
                discovered.append(model_data)
        
        logger.info(f"Discovered {len(discovered)} models from {repository_name}")
        return discovered
    
    def add_repository(self, repository: Repository) -> bool:
        """Add a new repository."""
        try:
            self.repositories[repository.name] = repository
            logger.info(f"Added repository {repository.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add repository {repository.name}: {e}")
            return False
    
    def get_repository(self, name: str) -> Optional[Repository]:
        """Get repository by name."""
        return self.repositories.get(name)
    
    def list_repositories(self) -> List[Repository]:
        """List all repositories."""
        return list(self.repositories.values())
    
    def get_predefined_models(self) -> Dict[str, Dict[str, Any]]:
        """Get all predefined model configurations."""
        return self.predefined_models.copy()
    
    def get_model_metadata(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model metadata by ID."""
        model = self.get_model(model_id)
        if model and model.metadata:
            return model.metadata
        
        # Check predefined models
        if model_id in self.predefined_models:
            metadata_data = self.predefined_models[model_id].get("metadata", {})
            if metadata_data:
                return ModelMetadata(
                    parameters=metadata_data.get("parameters", "unknown"),
                    quantization=metadata_data.get("quantization", "none"),
                    memory_requirement=metadata_data.get("memory_requirement", "unknown"),
                    context_length=metadata_data.get("context_length", 0),
                    license=metadata_data.get("license", "unknown"),
                    tags=metadata_data.get("tags", []),
                    architecture=metadata_data.get("architecture"),
                    training_data=metadata_data.get("training_data"),
                    performance_metrics=metadata_data.get("performance_metrics")
                )
        
        return None
    
    def search_models(self, query: str, capabilities: Optional[List[str]] = None,
                     provider: Optional[str] = None) -> List[ModelEntry]:
        """Search models by query, capabilities, and provider."""
        results = []
        query_lower = query.lower() if query else ""
        
        for model in self.models.values():
            # Text search
            if query_lower:
                searchable_text = f"{model.name} {model.description or ''} {' '.join(model.capabilities or [])}".lower()
                if query_lower not in searchable_text:
                    continue
            
            # Capability filter
            if capabilities:
                if not model.capabilities or not any(cap in model.capabilities for cap in capabilities):
                    continue
            
            # Provider filter
            if provider and model.provider != provider:
                continue
            
            results.append(model)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_models = len(self.models)
        local_models = len([m for m in self.models.values() if m.status == ModelStatus.LOCAL])
        available_models = len([m for m in self.models.values() if m.status == ModelStatus.AVAILABLE])
        
        providers = {}
        total_size = 0
        
        for model in self.models.values():
            # Count by provider
            if model.provider not in providers:
                providers[model.provider] = 0
            providers[model.provider] += 1
            
            # Sum sizes
            if model.size:
                total_size += model.size
        
        return {
            "total_models": total_models,
            "local_models": local_models,
            "available_models": available_models,
            "providers": providers,
            "total_size_bytes": total_size,
            "repositories": len(self.repositories),
            "predefined_models": len(self.predefined_models)
        }