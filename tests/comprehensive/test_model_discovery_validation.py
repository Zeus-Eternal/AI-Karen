"""
Comprehensive Model Discovery Tests
Validates that all models in models/* directory are found and properly registered.
"""

import pytest
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from src.ai_karen_engine.services.model_discovery_engine import ModelDiscoveryEngine
from src.ai_karen_engine.services.model_validation_system import ModelValidationSystem
from src.ai_karen_engine.core.shared_types import ModelInfo, ModelType, Modality, ModelStatus


class TestModelDiscoveryValidation:
    """Test suite for comprehensive model discovery validation."""
    
    @pytest.fixture
    async def discovery_engine(self):
        """Create a model discovery engine for testing."""
        engine = ModelDiscoveryEngine()
        await engine.initialize()
        return engine
    
    @pytest.fixture
    async def validation_system(self):
        """Create a model validation system for testing."""
        system = ModelValidationSystem()
        await system.initialize()
        return system
    
    @pytest.fixture
    def models_directory(self, tmp_path):
        """Create a temporary models directory with test models."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        
        # Create various model types
        self._create_test_model(models_dir / "llama-cpp", "llama-2-7b.gguf", ModelType.LLAMA_CPP)
        self._create_test_model(models_dir / "huggingface", "bert-base", ModelType.HUGGINGFACE)
        self._create_test_model(models_dir / "transformers", "gpt2", ModelType.TRANSFORMERS)
        self._create_test_model(models_dir / "openai", "gpt-3.5-turbo", ModelType.OPENAI)
        self._create_test_model(models_dir / "vision", "clip-vit", ModelType.VISION)
        self._create_test_model(models_dir / "audio", "whisper-base", ModelType.AUDIO)
        
        return str(models_dir)
    
    def _create_test_model(self, model_dir: Path, model_name: str, model_type: ModelType):
        """Create a test model directory with config files."""
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Create model file
        if model_type == ModelType.LLAMA_CPP:
            (model_dir / f"{model_name}").touch()
        else:
            (model_dir / model_name).mkdir(exist_ok=True)
            (model_dir / model_name / "config.json").write_text('{"model_type": "' + model_type.value + '"}')
            (model_dir / model_name / "tokenizer_config.json").write_text('{"tokenizer_class": "AutoTokenizer"}')
    
    @pytest.mark.asyncio
    async def test_discover_all_model_types(self, discovery_engine, models_directory):
        """Test that all model types in models/* directory are discovered."""
        with patch.object(discovery_engine, 'models_base_path', models_directory):
            discovered_models = await discovery_engine.discover_all_models()
            
            # Verify all model types are found
            model_types = {model.type for model in discovered_models}
            expected_types = {
                ModelType.LLAMA_CPP,
                ModelType.HUGGINGFACE,
                ModelType.TRANSFORMERS,
                ModelType.OPENAI,
                ModelType.VISION,
                ModelType.AUDIO
            }
            
            assert model_types == expected_types, f"Missing model types: {expected_types - model_types}"
            assert len(discovered_models) >= 6, "Should discover at least 6 test models"
    
    @pytest.mark.asyncio
    async def test_model_metadata_extraction(self, discovery_engine, models_directory):
        """Test that model metadata is properly extracted."""
        with patch.object(discovery_engine, 'models_base_path', models_directory):
            discovered_models = await discovery_engine.discover_all_models()
            
            for model in discovered_models:
                # Verify required metadata fields
                assert model.id is not None, f"Model {model.name} missing ID"
                assert model.name is not None, f"Model {model.name} missing name"
                assert model.type is not None, f"Model {model.name} missing type"
                assert model.path is not None, f"Model {model.name} missing path"
                assert model.modalities is not None, f"Model {model.name} missing modalities"
                assert model.status is not None, f"Model {model.name} missing status"
                
                # Verify path exists
                assert os.path.exists(model.path), f"Model path does not exist: {model.path}"
    
    @pytest.mark.asyncio
    async def test_modality_detection(self, discovery_engine, models_directory):
        """Test that model modalities are correctly detected."""
        with patch.object(discovery_engine, 'models_base_path', models_directory):
            discovered_models = await discovery_engine.discover_all_models()
            
            # Find specific model types and verify their modalities
            vision_models = [m for m in discovered_models if m.type == ModelType.VISION]
            audio_models = [m for m in discovered_models if m.type == ModelType.AUDIO]
            text_models = [m for m in discovered_models if m.type in [ModelType.LLAMA_CPP, ModelType.HUGGINGFACE]]
            
            # Verify vision models have image modality
            for model in vision_models:
                assert Modality.IMAGE in model.modalities, f"Vision model {model.name} missing image modality"
            
            # Verify audio models have audio modality
            for model in audio_models:
                assert Modality.AUDIO in model.modalities, f"Audio model {model.name} missing audio modality"
            
            # Verify text models have text modality
            for model in text_models:
                assert Modality.TEXT in model.modalities, f"Text model {model.name} missing text modality"
    
    @pytest.mark.asyncio
    async def test_model_categorization(self, discovery_engine, models_directory):
        """Test that models are properly categorized."""
        with patch.object(discovery_engine, 'models_base_path', models_directory):
            discovered_models = await discovery_engine.discover_all_models()
            
            for model in discovered_models:
                # Verify category is assigned
                assert model.category is not None, f"Model {model.name} missing category"
                assert model.category.primary is not None, f"Model {model.name} missing primary category"
                
                # Verify category matches model type
                if model.type == ModelType.VISION:
                    assert "VISION" in model.category.primary
                elif model.type == ModelType.AUDIO:
                    assert "AUDIO" in model.category.primary
                else:
                    assert "LANGUAGE" in model.category.primary or "TEXT" in model.category.primary
    
    @pytest.mark.asyncio
    async def test_model_validation(self, discovery_engine, validation_system, models_directory):
        """Test that discovered models pass validation checks."""
        with patch.object(discovery_engine, 'models_base_path', models_directory):
            discovered_models = await discovery_engine.discover_all_models()
            
            for model in discovered_models:
                # Validate each discovered model
                is_valid = await validation_system.validate_model_compatibility(model)
                
                # All test models should be valid
                assert is_valid, f"Model {model.name} failed validation"
                
                # Verify model status is set correctly
                if is_valid:
                    assert model.status in [ModelStatus.AVAILABLE, ModelStatus.LOADING]
                else:
                    assert model.status == ModelStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_model_registry_integration(self, discovery_engine, models_directory):
        """Test that discovered models are properly registered."""
        with patch.object(discovery_engine, 'models_base_path', models_directory):
            discovered_models = await discovery_engine.discover_all_models()
            
            # Register models
            await discovery_engine.register_discovered_models(discovered_models)
            
            # Verify models are in registry
            registry = await discovery_engine.get_model_registry()
            registered_ids = {model.id for model in registry}
            discovered_ids = {model.id for model in discovered_models}
            
            assert registered_ids == discovered_ids, "Not all discovered models were registered"
    
    @pytest.mark.asyncio
    async def test_model_organization(self, discovery_engine, models_directory):
        """Test that models are properly organized by category."""
        with patch.object(discovery_engine, 'models_base_path', models_directory):
            discovered_models = await discovery_engine.discover_all_models()
            organized_models = await discovery_engine.organize_models_by_category(discovered_models)
            
            # Verify organization structure
            assert isinstance(organized_models, dict), "Models should be organized in a dictionary"
            assert len(organized_models) > 0, "Should have at least one category"
            
            # Verify all models are included in organization
            total_organized = sum(len(models) for models in organized_models.values())
            assert total_organized == len(discovered_models), "All models should be organized"
    
    @pytest.mark.asyncio
    async def test_real_models_directory_discovery(self, discovery_engine):
        """Test discovery on the actual models directory if it exists."""
        real_models_path = "models"
        if os.path.exists(real_models_path):
            discovered_models = await discovery_engine.discover_all_models()
            
            # Verify we found some models
            assert len(discovered_models) > 0, "Should discover models in real models directory"
            
            # Verify each model has required properties
            for model in discovered_models:
                assert model.id, f"Model missing ID: {model}"
                assert model.name, f"Model missing name: {model}"
                assert model.type, f"Model missing type: {model}"
                assert model.path, f"Model missing path: {model}"
                assert os.path.exists(model.path), f"Model path doesn't exist: {model.path}"
    
    @pytest.mark.asyncio
    async def test_model_refresh_functionality(self, discovery_engine, models_directory):
        """Test that model registry can be refreshed with new models."""
        with patch.object(discovery_engine, 'models_base_path', models_directory):
            # Initial discovery
            initial_models = await discovery_engine.discover_all_models()
            initial_count = len(initial_models)
            
            # Add a new model
            new_model_dir = Path(models_directory) / "new_model"
            self._create_test_model(new_model_dir, "new-test-model", ModelType.HUGGINGFACE)
            
            # Refresh registry
            await discovery_engine.refresh_model_registry()
            
            # Verify new model is discovered
            refreshed_models = await discovery_engine.discover_all_models()
            assert len(refreshed_models) > initial_count, "New model should be discovered after refresh"
    
    @pytest.mark.asyncio
    async def test_error_handling_corrupted_models(self, discovery_engine, tmp_path):
        """Test handling of corrupted or invalid model files."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        
        # Create corrupted model files
        corrupted_dir = models_dir / "corrupted"
        corrupted_dir.mkdir()
        (corrupted_dir / "invalid.gguf").write_text("invalid content")
        (corrupted_dir / "config.json").write_text("invalid json {")
        
        with patch.object(discovery_engine, 'models_base_path', str(models_dir)):
            # Should not crash on corrupted models
            discovered_models = await discovery_engine.discover_all_models()
            
            # Corrupted models should either be excluded or marked as invalid
            for model in discovered_models:
                if "corrupted" in model.path:
                    assert model.status == ModelStatus.ERROR, "Corrupted models should have ERROR status"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])