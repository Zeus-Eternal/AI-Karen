"""
Unit tests for Enhanced Model Registry

Tests the enhanced model registry functionality including:
- Model discovery and management
- Status tracking and metadata management
- Repository management
- Search and filtering capabilities
"""

import json
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.ai_karen_engine.services.model_registry import (
    EnhancedModelRegistry,
    ModelEntry,
    ModelMetadata,
    DownloadInfo,
    Repository,
    ModelStatus,
    ModelSource
)


class TestEnhancedModelRegistry:
    """Test cases for EnhancedModelRegistry."""
    
    @pytest.fixture
    def temp_registry_file(self):
        """Create temporary registry file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            registry_data = {
                "models": [
                    {
                        "id": "test-model-1",
                        "name": "Test Model 1",
                        "provider": "test-provider",
                        "type": "gguf",
                        "source": "local",
                        "path": "/fake/path/model1.gguf",
                        "size": 1000000,
                        "capabilities": ["text-generation"],
                        "metadata": {
                            "parameters": "1B",
                            "quantization": "Q4_K_M",
                            "memory_requirement": "1GB",
                            "context_length": 2048,
                            "license": "Apache 2.0",
                            "tags": ["test", "small"]
                        }
                    }
                ],
                "repositories": [
                    {
                        "name": "test-repo",
                        "base_url": "https://test.example.com",
                        "type": "gguf",
                        "description": "Test repository"
                    }
                ],
                "predefined_models": []
            }
            json.dump(registry_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
        Path(temp_path + '.backup').unlink(missing_ok=True)
    
    @pytest.fixture
    def registry(self, temp_registry_file):
        """Create registry instance with temporary file."""
        return EnhancedModelRegistry(temp_registry_file)
    
    def test_registry_initialization(self, registry):
        """Test registry initialization."""
        assert len(registry.models) >= 1  # At least the test model
        assert len(registry.repositories) >= 1  # At least the test repo
        assert len(registry.predefined_models) >= 2  # TinyLlama models
    
    def test_load_existing_registry(self, temp_registry_file):
        """Test loading existing registry file."""
        registry = EnhancedModelRegistry(temp_registry_file)
        
        # Check loaded model
        assert "test-model-1" in registry.models
        model = registry.models["test-model-1"]
        assert model.name == "Test Model 1"
        assert model.provider == "test-provider"
        assert model.capabilities == ["text-generation"]
        
        # Check loaded repository
        assert "test-repo" in registry.repositories
        repo = registry.repositories["test-repo"]
        assert repo.base_url == "https://test.example.com"
    
    def test_create_default_registry(self):
        """Test creating default registry when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "new_registry.json"
            registry = EnhancedModelRegistry(str(registry_path))
            
            # Should have default repositories
            assert "huggingface" in registry.repositories
            assert "huggingface-transformers" in registry.repositories
            
            # Should have predefined models
            assert "tinyllama-1.1b-chat-q4" in registry.predefined_models
            assert "tinyllama-1.1b-instruct-q4" in registry.predefined_models
    
    def test_add_model(self, registry):
        """Test adding a new model."""
        metadata = ModelMetadata(
            parameters="2B",
            quantization="Q8_0",
            memory_requirement="2GB",
            context_length=4096,
            license="MIT",
            tags=["test", "medium"]
        )
        
        model = ModelEntry(
            id="test-model-2",
            name="Test Model 2",
            provider="test-provider",
            type="gguf",
            source=ModelSource.LOCAL,
            path="/fake/path/model2.gguf",
            size=2000000,
            capabilities=["text-generation", "chat"],
            metadata=metadata,
            status=ModelStatus.LOCAL
        )
        
        result = registry.add_model(model)
        assert result is True
        assert "test-model-2" in registry.models
        
        retrieved = registry.get_model("test-model-2")
        assert retrieved is not None
        assert retrieved.name == "Test Model 2"
        assert retrieved.metadata.parameters == "2B"
    
    def test_remove_model(self, registry):
        """Test removing a model."""
        # Add a model first
        model = ModelEntry(
            id="temp-model",
            name="Temporary Model",
            provider="test",
            type="gguf",
            source=ModelSource.LOCAL,
            status=ModelStatus.LOCAL
        )
        registry.add_model(model)
        
        # Remove it
        result = registry.remove_model("temp-model")
        assert result is True
        assert "temp-model" not in registry.models
        
        # Try to remove non-existent model
        result = registry.remove_model("non-existent")
        assert result is False
    
    def test_update_model_status(self, registry):
        """Test updating model status."""
        model_id = "test-model-1"
        
        result = registry.update_model_status(model_id, ModelStatus.DOWNLOADING)
        assert result is True
        
        model = registry.get_model(model_id)
        assert model.status == ModelStatus.DOWNLOADING
        
        # Test with path update
        new_path = "/new/path/model.gguf"
        result = registry.update_model_status(model_id, ModelStatus.LOCAL, new_path)
        assert result is True
        
        model = registry.get_model(model_id)
        assert model.status == ModelStatus.LOCAL
        assert model.path == new_path
    
    def test_list_models_filtering(self, registry):
        """Test listing models with filtering."""
        # Add another model with different provider
        model = ModelEntry(
            id="other-model",
            name="Other Model",
            provider="other-provider",
            type="transformers",
            source=ModelSource.LOCAL,
            status=ModelStatus.AVAILABLE
        )
        registry.add_model(model)
        
        # Test provider filtering
        test_provider_models = registry.list_models(provider="test-provider")
        assert len(test_provider_models) >= 1
        assert all(m.provider == "test-provider" for m in test_provider_models)
        
        # Test status filtering
        available_models = registry.list_models(status=ModelStatus.AVAILABLE)
        assert len(available_models) >= 1
        assert all(m.status == ModelStatus.AVAILABLE for m in available_models)
        
        # Test combined filtering
        filtered = registry.list_models(provider="other-provider", status=ModelStatus.AVAILABLE)
        assert len(filtered) >= 1
        assert all(m.provider == "other-provider" and m.status == ModelStatus.AVAILABLE for m in filtered)
    
    def test_search_models(self, registry):
        """Test model search functionality."""
        # Add searchable models
        model1 = ModelEntry(
            id="search-model-1",
            name="Chat Model",
            provider="test",
            type="gguf",
            source=ModelSource.LOCAL,
            description="A model for chat applications",
            capabilities=["chat", "text-generation"],
            status=ModelStatus.LOCAL
        )
        
        model2 = ModelEntry(
            id="search-model-2",
            name="Code Model",
            provider="test",
            type="gguf",
            source=ModelSource.LOCAL,
            description="A model for code generation",
            capabilities=["code-generation"],
            status=ModelStatus.LOCAL
        )
        
        registry.add_model(model1)
        registry.add_model(model2)
        
        # Test text search
        results = registry.search_models("chat")
        assert len(results) >= 1
        assert any("chat" in m.name.lower() or "chat" in (m.description or "").lower() for m in results)
        
        # Test capability search
        results = registry.search_models("", capabilities=["chat"])
        assert len(results) >= 1
        assert all("chat" in (m.capabilities or []) for m in results)
        
        # Test provider search
        results = registry.search_models("", provider="test")
        assert len(results) >= 2
        assert all(m.provider == "test" for m in results)
        
        # Test combined search
        results = registry.search_models("code", capabilities=["code-generation"], provider="test")
        assert len(results) >= 1
        assert all("code" in m.name.lower() and "code-generation" in (m.capabilities or []) for m in results)
    
    def test_repository_management(self, registry):
        """Test repository management."""
        # Add new repository
        repo = Repository(
            name="new-repo",
            base_url="https://new.example.com",
            type="transformers",
            description="New test repository",
            auth_required=True
        )
        
        result = registry.add_repository(repo)
        assert result is True
        assert "new-repo" in registry.repositories
        
        # Get repository
        retrieved = registry.get_repository("new-repo")
        assert retrieved is not None
        assert retrieved.base_url == "https://new.example.com"
        assert retrieved.auth_required is True
        
        # List repositories
        repos = registry.list_repositories()
        assert len(repos) >= 3  # Default + test + new
        assert any(r.name == "new-repo" for r in repos)
    
    def test_discover_models(self, registry):
        """Test model discovery from repositories."""
        # Test discovery from huggingface repo (should return predefined models)
        discovered = registry.discover_models("huggingface")
        assert len(discovered) >= 2  # TinyLlama models
        
        # Test discovery from non-existent repo
        discovered = registry.discover_models("non-existent")
        assert len(discovered) == 0
    
    def test_get_model_metadata(self, registry):
        """Test getting model metadata."""
        # Test existing model metadata
        metadata = registry.get_model_metadata("test-model-1")
        assert metadata is not None
        assert metadata.parameters == "1B"
        assert metadata.quantization == "Q4_K_M"
        
        # Test predefined model metadata
        metadata = registry.get_model_metadata("tinyllama-1.1b-chat-q4")
        assert metadata is not None
        assert metadata.parameters == "1.1B"
        assert "chat" in metadata.tags
        
        # Test non-existent model
        metadata = registry.get_model_metadata("non-existent")
        assert metadata is None
    
    def test_get_statistics(self, registry):
        """Test getting registry statistics."""
        stats = registry.get_statistics()
        
        assert "total_models" in stats
        assert "local_models" in stats
        assert "available_models" in stats
        assert "providers" in stats
        assert "total_size_bytes" in stats
        assert "repositories" in stats
        assert "predefined_models" in stats
        
        assert stats["total_models"] >= 1
        assert stats["repositories"] >= 2
        assert stats["predefined_models"] >= 2
        assert isinstance(stats["providers"], dict)
    
    def test_save_registry(self, registry, temp_registry_file):
        """Test saving registry to file."""
        # Add a new model
        model = ModelEntry(
            id="save-test-model",
            name="Save Test Model",
            provider="test",
            type="gguf",
            source=ModelSource.LOCAL,
            status=ModelStatus.LOCAL
        )
        registry.add_model(model)
        
        # Save registry
        registry.save_registry()
        
        # Verify backup was created
        backup_path = Path(temp_registry_file + '.backup')
        assert backup_path.exists()
        
        # Load registry again and verify model was saved
        new_registry = EnhancedModelRegistry(temp_registry_file)
        assert "save-test-model" in new_registry.models
        assert new_registry.models["save-test-model"].name == "Save Test Model"
    
    def test_convert_old_format(self):
        """Test converting old list format to new dict format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Old list format
            old_data = [
                {
                    "id": "old-model",
                    "name": "Old Model",
                    "type": "transformers",
                    "source": "local",
                    "path": "/old/path"
                }
            ]
            json.dump(old_data, f)
            temp_path = f.name
        
        try:
            registry = EnhancedModelRegistry(temp_path)
            
            # Should have converted and loaded the model
            assert "old-model" in registry.models
            model = registry.models["old-model"]
            assert model.name == "Old Model"
            assert model.type == "transformers"
            
            # Should have default repositories
            assert len(registry.repositories) >= 2
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_predefined_models_initialization(self, registry):
        """Test that predefined models are properly initialized."""
        predefined = registry.get_predefined_models()
        
        # Check TinyLlama models
        assert "tinyllama-1.1b-chat-q4" in predefined
        assert "tinyllama-1.1b-instruct-q4" in predefined
        
        chat_model = predefined["tinyllama-1.1b-chat-q4"]
        assert chat_model["name"] == "TinyLlama 1.1B Chat Q4_K_M"
        assert chat_model["provider"] == "llama-cpp"
        assert "chat" in chat_model["capabilities"]
        assert "download_info" in chat_model
        assert chat_model["download_info"]["url"].startswith("https://huggingface.co")
        
        instruct_model = predefined["tinyllama-1.1b-instruct-q4"]
        assert instruct_model["name"] == "TinyLlama 1.1B Instruct Q4_K_M"
        assert "instruction-following" in instruct_model["capabilities"]


class TestModelEntry:
    """Test cases for ModelEntry dataclass."""
    
    def test_model_entry_creation(self):
        """Test creating ModelEntry with all fields."""
        metadata = ModelMetadata(
            parameters="1B",
            quantization="Q4_K_M",
            memory_requirement="1GB",
            context_length=2048,
            license="Apache 2.0",
            tags=["test"]
        )
        
        download_info = DownloadInfo(
            url="https://example.com/model.gguf",
            filename="model.gguf",
            checksum="sha256:abc123"
        )
        
        model = ModelEntry(
            id="test-model",
            name="Test Model",
            provider="test-provider",
            type="gguf",
            source=ModelSource.DOWNLOADED,
            path="/path/to/model.gguf",
            size=1000000,
            description="Test model description",
            capabilities=["text-generation"],
            metadata=metadata,
            download_info=download_info,
            status=ModelStatus.LOCAL
        )
        
        assert model.id == "test-model"
        assert model.name == "Test Model"
        assert model.provider == "test-provider"
        assert model.source == ModelSource.DOWNLOADED
        assert model.status == ModelStatus.LOCAL
        assert model.metadata.parameters == "1B"
        assert model.download_info.url == "https://example.com/model.gguf"
    
    def test_model_entry_minimal(self):
        """Test creating ModelEntry with minimal required fields."""
        model = ModelEntry(
            id="minimal-model",
            name="Minimal Model",
            provider="test",
            type="gguf",
            source=ModelSource.LOCAL
        )
        
        assert model.id == "minimal-model"
        assert model.name == "Minimal Model"
        assert model.status == ModelStatus.UNKNOWN  # Default value
        assert model.path is None
        assert model.metadata is None


class TestModelMetadata:
    """Test cases for ModelMetadata dataclass."""
    
    def test_metadata_creation(self):
        """Test creating ModelMetadata."""
        metadata = ModelMetadata(
            parameters="1.1B",
            quantization="Q4_K_M",
            memory_requirement="~1GB",
            context_length=2048,
            license="Apache 2.0",
            tags=["chat", "small"],
            architecture="Llama",
            training_data="SlimPajama",
            performance_metrics={"speed": "fast"}
        )
        
        assert metadata.parameters == "1.1B"
        assert metadata.quantization == "Q4_K_M"
        assert metadata.context_length == 2048
        assert "chat" in metadata.tags
        assert metadata.architecture == "Llama"
        assert metadata.performance_metrics["speed"] == "fast"


class TestRepository:
    """Test cases for Repository dataclass."""
    
    def test_repository_creation(self):
        """Test creating Repository."""
        repo = Repository(
            name="test-repo",
            base_url="https://test.example.com",
            type="gguf",
            description="Test repository",
            auth_required=True
        )
        
        assert repo.name == "test-repo"
        assert repo.base_url == "https://test.example.com"
        assert repo.type == "gguf"
        assert repo.auth_required is True
    
    def test_repository_minimal(self):
        """Test creating Repository with minimal fields."""
        repo = Repository(
            name="minimal-repo",
            base_url="https://minimal.example.com",
            type="transformers"
        )
        
        assert repo.name == "minimal-repo"
        assert repo.auth_required is False  # Default value
        assert repo.description is None


class TestDownloadInfo:
    """Test cases for DownloadInfo dataclass."""
    
    def test_download_info_creation(self):
        """Test creating DownloadInfo."""
        download_info = DownloadInfo(
            url="https://example.com/model.gguf",
            filename="model.gguf",
            checksum="sha256:abc123",
            mirrors=["https://mirror1.com", "https://mirror2.com"],
            download_date=time.time()
        )
        
        assert download_info.url == "https://example.com/model.gguf"
        assert download_info.filename == "model.gguf"
        assert download_info.checksum == "sha256:abc123"
        assert len(download_info.mirrors) == 2
        assert download_info.download_date is not None
    
    def test_download_info_minimal(self):
        """Test creating DownloadInfo with minimal fields."""
        download_info = DownloadInfo(
            url="https://example.com/model.gguf",
            filename="model.gguf"
        )
        
        assert download_info.url == "https://example.com/model.gguf"
        assert download_info.filename == "model.gguf"
        assert download_info.checksum is None
        assert download_info.mirrors is None