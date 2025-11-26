"""
Model Registry

This service manages known models, their capabilities, and metadata.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json


class ModelType(Enum):
    """Types of models."""
    LLM = "llm"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    GENERATION = "generation"
    TRANSLATION = "translation"


class ModelCapability(Enum):
    """Model capabilities."""
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    GENERATION = "generation"
    TRANSLATION = "translation"
    CODING = "coding"
    REASONING = "reasoning"


@dataclass
class ModelInfo:
    """Information about a model."""
    id: str
    name: str
    type: ModelType
    provider: str
    capabilities: List[ModelCapability]
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""


class ModelRegistry:
    """
    Model Registry manages known models, their capabilities, and metadata.
    
    This service provides a central registry for all models with their
    capabilities, parameters, and other metadata.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Model Registry.
        
        Args:
            config: Configuration for the model registry
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Model storage
        self.models: Dict[str, ModelInfo] = {}
        
        # Indexes
        self.by_type: Dict[ModelType, List[str]] = {}
        self.by_provider: Dict[str, List[str]] = {}
        self.by_capability: Dict[ModelCapability, List[str]] = {}
        self.by_tag: Dict[str, List[str]] = {}
        
        # Load initial models
        self._load_initial_models()
    
    def _load_initial_models(self):
        """Load initial models from configuration."""
        initial_models = self.config.get("initial_models", [])
        
        for model_data in initial_models:
            model_info = ModelInfo(**model_data)
            self.register_model(model_info)
    
    def register_model(self, model_info: ModelInfo) -> str:
        """
        Register a model in the registry.
        
        Args:
            model_info: Information about the model
            
        Returns:
            The model ID
        """
        # Store the model
        self.models[model_info.id] = model_info
        
        # Update indexes
        self._update_type_index(model_info.id, model_info.type)
        self._update_provider_index(model_info.id, model_info.provider)
        self._update_capability_indexes(model_info.id, model_info.capabilities)
        self._update_tag_indexes(model_info.id, model_info.tags)
        
        self.logger.info(f"Registered model: {model_info.id}")
        return model_info.id
    
    def _update_type_index(self, model_id: str, model_type: ModelType):
        """Update the type index."""
        if model_type not in self.by_type:
            self.by_type[model_type] = []
        if model_id not in self.by_type[model_type]:
            self.by_type[model_type].append(model_id)
    
    def _update_provider_index(self, model_id: str, provider: str):
        """Update the provider index."""
        if provider not in self.by_provider:
            self.by_provider[provider] = []
        if model_id not in self.by_provider[provider]:
            self.by_provider[provider].append(model_id)
    
    def _update_capability_indexes(self, model_id: str, capabilities: List[ModelCapability]):
        """Update capability indexes."""
        for capability in capabilities:
            if capability not in self.by_capability:
                self.by_capability[capability] = []
            if model_id not in self.by_capability[capability]:
                self.by_capability[capability].append(model_id)
    
    def _update_tag_indexes(self, model_id: str, tags: List[str]):
        """Update tag indexes."""
        for tag in tags:
            if tag not in self.by_tag:
                self.by_tag[tag] = []
            if model_id not in self.by_tag[tag]:
                self.by_tag[tag].append(model_id)
    
    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get model information by ID.
        
        Args:
            model_id: The model ID
            
        Returns:
            Model information if found, None otherwise
        """
        return self.models.get(model_id)
    
    def list_models(
        self, 
        model_type: Optional[ModelType] = None,
        provider: Optional[str] = None,
        capability: Optional[ModelCapability] = None,
        tag: Optional[str] = None,
        active_only: bool = True
    ) -> List[ModelInfo]:
        """
        List models with optional filtering.
        
        Args:
            model_type: Filter by model type
            provider: Filter by provider
            capability: Filter by capability
            tag: Filter by tag
            active_only: Only return active models
            
        Returns:
            List of matching models
        """
        # Start with all models
        model_ids = list(self.models.keys())
        
        # Apply filters
        if model_type:
            model_ids = [mid for mid in model_ids if mid in self.by_type.get(model_type, [])]
        
        if provider:
            model_ids = [mid for mid in model_ids if mid in self.by_provider.get(provider, [])]
        
        if capability:
            model_ids = [mid for mid in model_ids if mid in self.by_capability.get(capability, [])]
        
        if tag:
            model_ids = [mid for mid in model_ids if mid in self.by_tag.get(tag, [])]
        
        # Get model info
        models = [self.models[mid] for mid in model_ids]
        
        # Filter by active status
        if active_only:
            models = [m for m in models if m.is_active]
        
        return models
    
    def find_models_by_task(
        self, 
        task: str, 
        model_type: Optional[ModelType] = None
    ) -> List[ModelInfo]:
        """
        Find models suitable for a specific task.
        
        Args:
            task: The task to find models for
            model_type: Optional model type filter
            
        Returns:
            List of suitable models
        """
        # Map tasks to capabilities
        task_to_capability = {
            "chat": ModelCapability.CHAT,
            "completion": ModelCapability.COMPLETION,
            "embedding": ModelCapability.EMBEDDING,
            "classification": ModelCapability.CLASSIFICATION,
            "generation": ModelCapability.GENERATION,
            "translation": ModelCapability.TRANSLATION,
            "coding": ModelCapability.CODING,
            "reasoning": ModelCapability.REASONING
        }
        
        capability = task_to_capability.get(task.lower())
        if not capability:
            return []
        
        # Get models with the required capability
        models = self.list_models(capability=capability)
        
        # Filter by model type if specified
        if model_type:
            models = [m for m in models if m.type == model_type]
        
        return models
    
    def update_model(self, model_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update model information.
        
        Args:
            model_id: The model ID to update
            updates: Dictionary of updates
            
        Returns:
            True if updated, False otherwise
        """
        model = self.get_model(model_id)
        if not model:
            return False
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(model, key):
                setattr(model, key, value)
        
        # Update indexes if needed
        if "capabilities" in updates:
            # Remove old capability indexes
            for capability in model.capabilities:
                if model_id in self.by_capability.get(capability, []):
                    self.by_capability[capability].remove(model_id)
            
            # Add new capability indexes
            self._update_capability_indexes(model_id, updates["capabilities"])
        
        if "tags" in updates:
            # Remove old tag indexes
            for tag in model.tags:
                if model_id in self.by_tag.get(tag, []):
                    self.by_tag[tag].remove(model_id)
            
            # Add new tag indexes
            self._update_tag_indexes(model_id, updates["tags"])
        
        return True
    
    def deactivate_model(self, model_id: str) -> bool:
        """
        Deactivate a model.
        
        Args:
            model_id: The model ID to deactivate
            
        Returns:
            True if deactivated, False otherwise
        """
        return self.update_model(model_id, {"is_active": False})
    
    def activate_model(self, model_id: str) -> bool:
        """
        Activate a model.
        
        Args:
            model_id: The model ID to activate
            
        Returns:
            True if activated, False otherwise
        """
        return self.update_model(model_id, {"is_active": True})
    
    def get_model_stats(self) -> Dict[str, Any]:
        """
        Get model registry statistics.
        
        Returns:
            Dictionary of statistics
        """
        active_models = [m for m in self.models.values() if m.is_active]
        
        return {
            "total_models": len(self.models),
            "active_models": len(active_models),
            "by_type": {
                model_type.value: len(self.by_type.get(model_type, []))
                for model_type in ModelType
            },
            "by_provider": {
                provider: len(self.by_provider.get(provider, []))
                for provider in self.by_provider
            },
            "by_capability": {
                capability.value: len(self.by_capability.get(capability, []))
                for capability in ModelCapability
            }
        }
    
    def export_models(self, file_path: str) -> bool:
        """
        Export model registry to a file.
        
        Args:
            file_path: Path to export to
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            models_data = []
            for model in self.models.values():
                model_dict = {
                    "id": model.id,
                    "name": model.name,
                    "type": model.type.value,
                    "provider": model.provider,
                    "capabilities": [c.value for c in model.capabilities],
                    "parameters": model.parameters,
                    "metadata": model.metadata,
                    "tags": model.tags,
                    "is_active": model.is_active,
                    "created_at": model.created_at,
                    "updated_at": model.updated_at
                }
                models_data.append(model_dict)
            
            with open(file_path, "w") as f:
                json.dump(models_data, f, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Error exporting models: {e}")
            return False
    
    def import_models(self, file_path: str) -> bool:
        """
        Import model registry from a file.
        
        Args:
            file_path: Path to import from
            
        Returns:
            True if imported successfully, False otherwise
        """
        try:
            with open(file_path, "r") as f:
                models_data = json.load(f)
            
            for model_dict in models_data:
                # Convert string enums back to enum objects
                model_type = ModelType(model_dict["type"])
                capabilities = [
                    ModelCapability(c) for c in model_dict["capabilities"]
                ]
                
                model_info = ModelInfo(
                    id=model_dict["id"],
                    name=model_dict["name"],
                    type=model_type,
                    provider=model_dict["provider"],
                    capabilities=capabilities,
                    parameters=model_dict.get("parameters", {}),
                    metadata=model_dict.get("metadata", {}),
                    tags=model_dict.get("tags", []),
                    is_active=model_dict.get("is_active", True),
                    created_at=model_dict.get("created_at", ""),
                    updated_at=model_dict.get("updated_at", "")
                )
                
                self.register_model(model_info)
            
            return True
        except Exception as e:
            self.logger.error(f"Error importing models: {e}")
            return False
