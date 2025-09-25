"""
Unit tests for Model Library Service

Tests the comprehensive model library service functionality including:
- Model discovery and metadata management
- Download management with progress tracking
- Integration with existing model registry
- Predefined model configurations
- Model validation and security
"""

import json
import pytest
import tempfile
import time
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock, call
from dataclasses import asdict

from src.ai_karen_engine.services.model_library_service import (
    ModelLibraryService,
    ModelInfo,
    DownloadTask,
    ModelMetadata,
    ModelDownloadManager,
    ModelMetadataService
)


class TestModelLibraryService:
    """Test cases for ModelLibraryService."""
    
    @pytest.fixture
    def temp_registry_file(self):
        """Create temporary registry file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            registry_data = {
                "models": [
                    {
                        "id": "test-local-model",
                        "name": "Test Local Model",
                        "provider": "llama-cpp",
                        "path": "/fake/path/model.gguf",
                        "type": "gguf",
                        "source": "local",
                        "size": 1000000,
                        "capabilities": ["text-generation"],
                        "metadata": {
                            "parameters": "1B",
                            "quantization": "Q4_K_M",
                            "memory_requirement": "1GB",
                            "context_length": 2048,
                            "license": "Apache 2.0",
                            "tags": ["test"]
                        }
                    }
                ],
                "repositories": [
                    {
                        "name": "huggingface",
                        "baseUrl": "https://huggingface.co",
                        "type": "gguf"
                    }
                ]
            }
            json.dump(registry_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def temp_models_dir(self):
        """Create temporary models directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def service(self, temp_registry_file, temp_models_dir):
        """Create service instance with temporary files."""
        with patch('src.ai_karen_engine.services.model_library_service.Path') as mock_path:
            # Mock the models directory
            mock_path.return_value.mkdir.return_value = None
            
            service = ModelLibraryService(registry_path=temp_registry_file)
            service.models_dir = Path(temp_models_dir)
            return service
    
    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service.registry_path.exists()
        assert isinstance(service.download_manager, ModelDownloadManager)
        assert isinstance(service.metadata_service, ModelMetadataService)
        assert "models" in service.registry
        assert "repositories" in service.registry
    
    def test_load_registry_dict_format(self, temp_registry_file):
        """Test loading registry in dict format."""
        service = ModelLibraryService(registry_path=temp_registry_file)
        
        assert len(service.registry["models"]) == 1
        assert len(service.registry["repositories"]) == 1
        assert service.registry["models"][0]["id"] == "test-local-model"
    
    def test_load_registry_list_format(self):
        """Test loading registry in old list format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            # Old list format
            old_data = [
                {
                    "id": "old-model",
                    "name": "Old Model",
                    "type": "gguf",
                    "path": "/old/path"
                }
            ]
            json.dump(old_data, f)
            temp_path = f.name
        
        try:
            service = ModelLibraryService(registry_path=temp_path)
            
            # Should convert to new format
            assert isinstance(service.registry, dict)
            assert "models" in service.registry
            assert "repositories" in service.registry
            assert len(service.registry["models"]) == 1
            assert service.registry["models"][0]["id"] == "old-model"
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_load_nonexistent_registry(self):
        """Test loading non-existent registry file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "nonexistent.json"
            service = ModelLibraryService(registry_path=str(registry_path))
            
            # Should create default registry
            assert service.registry["models"] == []
            assert service.registry["repositories"] == []
    
    @patch('pathlib.Path.exists')
    def test_get_available_models_local_and_predefined(self, mock_exists, service):
        """Test getting available models including local and predefined."""
        # Mock file existence for local model
        mock_exists.return_value = True
        
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 1000000
            
            models = service.get_available_models()
            
            # Should have local model + predefined models
            assert len(models) >= 3  # 1 local + 2+ predefined
            
            # Check local model
            local_models = [m for m in models if m.status == "local"]
            assert len(local_models) >= 1
            local_model = local_models[0]
            assert local_model.id == "test-local-model"
            assert local_model.name == "Test Local Model"
            assert local_model.size == 1000000
            
            # Check predefined models
            available_models = [m for m in models if m.status == "available"]
            assert len(available_models) >= 2
            
            # Verify TinyLlama models are present
            model_ids = [m.id for m in available_models]
            assert "tinyllama-1.1b-chat-q4" in model_ids
            assert "tinyllama-1.1b-instruct-q4" in model_ids
    
    @patch('pathlib.Path.exists')
    def test_get_available_models_missing_local_file(self, mock_exists, service):
        """Test getting available models when local file is missing."""
        # Mock file doesn't exist
        mock_exists.return_value = False
        
        models = service.get_available_models()
        
        # Local model should have error status
        local_models = [m for m in models if m.id == "test-local-model"]
        assert len(local_models) == 1
        assert local_models[0].status == "error"
    
    def test_create_model_info_from_registry(self, service):
        """Test creating ModelInfo from registry data."""
        model_data = {
            "id": "test-model",
            "name": "Test Model",
            "provider": "llama-cpp",
            "path": "/fake/path/model.gguf",
            "size": 500000,
            "capabilities": ["text-generation", "chat"],
            "downloadInfo": {
                "downloadDate": 1234567890
            }
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 500000
            
            model_info = service._create_model_info_from_registry(model_data)
            
            assert model_info is not None
            assert model_info.id == "test-model"
            assert model_info.name == "Test Model"
            assert model_info.provider == "llama-cpp"
            assert model_info.size == 500000
            assert model_info.status == "local"
            assert model_info.capabilities == ["text-generation", "chat"]
            assert model_info.disk_usage == 500000
            assert model_info.download_date == 1234567890
    
    def test_create_model_info_from_predefined(self, service):
        """Test creating ModelInfo from predefined model data."""
        predefined_models = service.metadata_service.get_predefined_models()
        tinyllama_data = predefined_models["tinyllama-1.1b-chat-q4"]
        
        model_info = service._create_model_info_from_predefined(tinyllama_data)
        
        assert model_info.id == "tinyllama-1.1b-chat-q4"
        assert model_info.name == "TinyLlama 1.1B Chat Q4_K_M"
        assert model_info.provider == "llama-cpp"
        assert model_info.size == 669000000
        assert model_info.status == "available"
        assert "chat" in model_info.capabilities
        assert model_info.download_url is not None
        assert model_info.checksum is not None
    
    @patch.object(ModelDownloadManager, 'download_model')
    def test_download_model_success(self, mock_download, service):
        """Test successful model download initiation."""
        # Mock download manager
        mock_task = DownloadTask(
            task_id="test-task",
            model_id="tinyllama-1.1b-chat-q4",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            total_size=669000000,
            downloaded_size=0,
            progress=0.0,
            status="pending"
        )
        mock_download.return_value = mock_task
        
        task = service.download_model("tinyllama-1.1b-chat-q4")
        
        assert task is not None
        assert task.model_id == "tinyllama-1.1b-chat-q4"
        assert task.status == "pending"
        mock_download.assert_called_once()
    
    def test_download_model_unknown_model(self, service):
        """Test downloading unknown model."""
        task = service.download_model("unknown-model")
        assert task is None
    
    def test_download_model_missing_url(self, service):
        """Test downloading model with missing URL."""
        # Mock predefined model without download URL
        with patch.object(service.metadata_service, 'get_predefined_models') as mock_predefined:
            mock_predefined.return_value = {
                "test-model": {
                    "id": "test-model",
                    "name": "Test Model",
                    # Missing download_url and filename
                }
            }
            
            task = service.download_model("test-model")
            assert task is None
    
    @patch.object(ModelDownloadManager, 'get_download_status')
    def test_get_download_status(self, mock_get_status, service):
        """Test getting download status."""
        mock_task = DownloadTask(
            task_id="test-task",
            model_id="test-model",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            total_size=1000000,
            downloaded_size=500000,
            progress=50.0,
            status="downloading"
        )
        mock_get_status.return_value = mock_task
        
        status = service.get_download_status("test-task")
        
        assert status is not None
        assert status.progress == 50.0
        assert status.status == "downloading"
        mock_get_status.assert_called_once_with("test-task")
    
    @patch.object(ModelDownloadManager, 'cancel_download')
    def test_cancel_download(self, mock_cancel, service):
        """Test canceling download."""
        mock_cancel.return_value = True
        
        result = service.cancel_download("test-task")
        
        assert result is True
        mock_cancel.assert_called_once_with("test-task")
    
    def test_delete_model_success(self, service, temp_models_dir):
        """Test successful model deletion."""
        # Create a fake model file
        model_path = Path(temp_models_dir) / "test_model.gguf"
        model_path.write_text("fake model data")
        
        # Add model to registry
        service.registry["models"].append({
            "id": "delete-test-model",
            "name": "Delete Test Model",
            "path": str(model_path),
            "provider": "llama-cpp"
        })
        
        result = service.delete_model("delete-test-model")
        
        assert result is True
        assert not model_path.exists()
        
        # Model should be removed from registry
        model_ids = [m["id"] for m in service.registry["models"]]
        assert "delete-test-model" not in model_ids
    
    def test_delete_model_not_found(self, service):
        """Test deleting non-existent model."""
        result = service.delete_model("non-existent-model")
        assert result is False
    
    def test_delete_model_directory(self, service, temp_models_dir):
        """Test deleting model directory."""
        # Create a fake model directory
        model_dir = Path(temp_models_dir) / "test_model_dir"
        model_dir.mkdir()
        (model_dir / "model.bin").write_text("fake model data")
        (model_dir / "config.json").write_text("{}")
        
        # Add model to registry
        service.registry["models"].append({
            "id": "delete-dir-model",
            "name": "Delete Directory Model",
            "path": str(model_dir),
            "provider": "transformers"
        })
        
        result = service.delete_model("delete-dir-model")
        
        assert result is True
        assert not model_dir.exists()
    
    def test_get_model_info(self, service):
        """Test getting specific model info."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 1000000
            
            model_info = service.get_model_info("test-local-model")
            
            assert model_info is not None
            assert model_info.id == "test-local-model"
            assert model_info.name == "Test Local Model"
    
    def test_get_model_info_not_found(self, service):
        """Test getting info for non-existent model."""
        model_info = service.get_model_info("non-existent-model")
        assert model_info is None
    
    def test_validate_checksum_success(self, service, temp_models_dir):
        """Test successful checksum validation."""
        # Create a test file
        test_file = Path(temp_models_dir) / "test_file.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        # Calculate expected SHA256
        import hashlib
        expected_hash = hashlib.sha256(test_content).hexdigest()
        expected_checksum = f"sha256:{expected_hash}"
        
        result = service.validate_checksum(test_file, expected_checksum)
        assert result is True
    
    def test_validate_checksum_failure(self, service, temp_models_dir):
        """Test checksum validation failure."""
        # Create a test file
        test_file = Path(temp_models_dir) / "test_file.txt"
        test_file.write_bytes(b"Hello, World!")
        
        # Use wrong checksum
        wrong_checksum = "sha256:wrong_hash_value"
        
        result = service.validate_checksum(test_file, wrong_checksum)
        assert result is False
    
    def test_validate_checksum_placeholder(self, service, temp_models_dir):
        """Test checksum validation with placeholder."""
        # Create a test file
        test_file = Path(temp_models_dir) / "test_file.txt"
        test_file.write_bytes(b"Hello, World!")
        
        # Use placeholder checksum
        placeholder_checksum = "sha256:placeholder_checksum_for_validation"
        
        result = service.validate_checksum(test_file, placeholder_checksum)
        assert result is True  # Should skip validation for placeholders
    
    def test_validate_checksum_unsupported_algorithm(self, service, temp_models_dir):
        """Test checksum validation with unsupported algorithm."""
        # Create a test file
        test_file = Path(temp_models_dir) / "test_file.txt"
        test_file.write_bytes(b"Hello, World!")
        
        # Use unsupported algorithm
        unsupported_checksum = "blake2b:some_hash_value"
        
        result = service.validate_checksum(test_file, unsupported_checksum)
        assert result is False
    
    def test_validate_checksum_missing_file(self, service, temp_models_dir):
        """Test checksum validation with missing file."""
        missing_file = Path(temp_models_dir) / "missing_file.txt"
        checksum = "sha256:some_hash"
        
        result = service.validate_checksum(missing_file, checksum)
        assert result is False
    
    def test_get_model_disk_usage_file(self, service, temp_models_dir):
        """Test getting disk usage for model file."""
        # Create a test model file
        model_file = Path(temp_models_dir) / "model.gguf"
        test_data = b"x" * 1000  # 1000 bytes
        model_file.write_bytes(test_data)
        
        # Add to registry
        service.registry["models"].append({
            "id": "disk-test-model",
            "path": str(model_file)
        })
        
        usage = service.get_model_disk_usage("disk-test-model")
        assert usage == 1000
    
    def test_get_model_disk_usage_directory(self, service, temp_models_dir):
        """Test getting disk usage for model directory."""
        # Create a test model directory
        model_dir = Path(temp_models_dir) / "model_dir"
        model_dir.mkdir()
        
        # Create files in directory
        (model_dir / "file1.bin").write_bytes(b"x" * 500)
        (model_dir / "file2.bin").write_bytes(b"x" * 300)
        
        # Add to registry
        service.registry["models"].append({
            "id": "disk-dir-model",
            "path": str(model_dir)
        })
        
        usage = service.get_model_disk_usage("disk-dir-model")
        assert usage == 800  # 500 + 300
    
    def test_get_model_disk_usage_not_found(self, service):
        """Test getting disk usage for non-existent model."""
        usage = service.get_model_disk_usage("non-existent-model")
        assert usage is None
    
    @patch('shutil.disk_usage')
    def test_get_available_disk_space(self, mock_disk_usage, service):
        """Test getting available disk space."""
        # Mock disk usage
        mock_usage = Mock()
        mock_usage.free = 5000000000  # 5GB
        mock_disk_usage.return_value = mock_usage
        
        available = service.get_available_disk_space()
        assert available == 5000000000
    
    def test_get_total_models_disk_usage(self, service, temp_models_dir):
        """Test getting total disk usage of all models."""
        # Create test model files
        model1 = Path(temp_models_dir) / "model1.gguf"
        model2 = Path(temp_models_dir) / "model2.gguf"
        model1.write_bytes(b"x" * 1000)
        model2.write_bytes(b"x" * 2000)
        
        # Add to registry
        service.registry["models"] = [
            {"id": "model1", "path": str(model1)},
            {"id": "model2", "path": str(model2)}
        ]
        
        total_usage = service.get_total_models_disk_usage()
        assert total_usage == 3000  # 1000 + 2000
    
    def test_download_progress_callback(self, service):
        """Test download progress callback."""
        task = DownloadTask(
            task_id="callback-test",
            model_id="test-model",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            total_size=1000,
            downloaded_size=500,
            progress=50.0,
            status="downloading"
        )
        
        # Test callback doesn't raise exception
        service._download_progress_callback(task)
        
        # Test with completed status
        task.status = "completed"
        with patch.object(service, '_add_downloaded_model_to_registry') as mock_add:
            service._download_progress_callback(task)
            mock_add.assert_called_once_with(task)
    
    def test_add_downloaded_model_to_registry(self, service, temp_models_dir):
        """Test adding downloaded model to registry."""
        # Create download directory and file
        download_dir = Path(temp_models_dir) / "downloads"
        download_dir.mkdir()
        downloaded_file = download_dir / "test_model.gguf"
        downloaded_file.write_bytes(b"fake model data")
        
        # Mock download manager
        service.download_manager.download_dir = download_dir
        
        # Create task
        task = DownloadTask(
            task_id="add-test",
            model_id="tinyllama-1.1b-chat-q4",
            url="https://example.com/model.gguf",
            filename="test_model.gguf",
            total_size=1000,
            downloaded_size=1000,
            progress=100.0,
            status="completed"
        )
        
        # Mock save registry
        with patch.object(service, '_save_registry') as mock_save:
            service._add_downloaded_model_to_registry(task)
            
            # Check model was added to registry
            model_ids = [m["id"] for m in service.registry["models"]]
            assert "tinyllama-1.1b-chat-q4" in model_ids
            
            # Check file was moved
            final_path = service.models_dir / "llama-cpp" / "test_model.gguf"
            assert final_path.exists()
            
            mock_save.assert_called_once()
    
    def test_save_registry(self, service, temp_registry_file):
        """Test saving registry to file."""
        # Modify registry
        service.registry["models"].append({
            "id": "new-model",
            "name": "New Model"
        })
        
        # Save registry
        service._save_registry()
        
        # Verify file was updated
        with open(temp_registry_file, 'r') as f:
            saved_data = json.load(f)
        
        model_ids = [m["id"] for m in saved_data["models"]]
        assert "new-model" in model_ids


class TestModelInfo:
    """Test cases for ModelInfo dataclass."""
    
    def test_model_info_creation(self):
        """Test creating ModelInfo with all fields."""
        metadata = {
            "parameters": "1B",
            "quantization": "Q4_K_M",
            "memory_requirement": "1GB"
        }
        
        model_info = ModelInfo(
            id="test-model",
            name="Test Model",
            provider="llama-cpp",
            size=1000000,
            description="Test model description",
            capabilities=["text-generation"],
            status="local",
            download_progress=None,
            metadata=metadata,
            local_path="/path/to/model.gguf",
            download_url="https://example.com/model.gguf",
            checksum="sha256:abc123",
            disk_usage=1000000,
            last_used=1234567890,
            download_date=1234567890
        )
        
        assert model_info.id == "test-model"
        assert model_info.name == "Test Model"
        assert model_info.provider == "llama-cpp"
        assert model_info.size == 1000000
        assert model_info.status == "local"
        assert model_info.capabilities == ["text-generation"]
        assert model_info.metadata["parameters"] == "1B"
        assert model_info.disk_usage == 1000000
    
    def test_model_info_minimal(self):
        """Test creating ModelInfo with minimal fields."""
        model_info = ModelInfo(
            id="minimal-model",
            name="Minimal Model",
            provider="test",
            size=0,
            description="",
            capabilities=[],
            status="unknown"
        )
        
        assert model_info.id == "minimal-model"
        assert model_info.name == "Minimal Model"
        assert model_info.status == "unknown"
        assert model_info.download_progress is None
        assert model_info.metadata is None


class TestDownloadTask:
    """Test cases for DownloadTask dataclass."""
    
    def test_download_task_creation(self):
        """Test creating DownloadTask."""
        task = DownloadTask(
            task_id="test-task",
            model_id="test-model",
            url="https://example.com/model.gguf",
            filename="model.gguf",
            total_size=1000000,
            downloaded_size=500000,
            progress=50.0,
            status="downloading",
            error_message=None,
            start_time=1234567890,
            estimated_time_remaining=60.0
        )
        
        assert task.task_id == "test-task"
        assert task.model_id == "test-model"
        assert task.url == "https://example.com/model.gguf"
        assert task.filename == "model.gguf"
        assert task.total_size == 1000000
        assert task.downloaded_size == 500000
        assert task.progress == 50.0
        assert task.status == "downloading"
        assert task.start_time == 1234567890
        assert task.estimated_time_remaining == 60.0
    
    def test_download_task_defaults(self):
        """Test DownloadTask with default values."""
        task = DownloadTask(
            task_id="default-task",
            model_id="default-model",
            url="https://example.com/model.gguf",
            filename="model.gguf"
        )
        
        assert task.total_size == 0
        assert task.downloaded_size == 0
        assert task.progress == 0.0
        assert task.status == 'pending'
        assert task.error_message is None
        assert task.start_time is None
        assert task.estimated_time_remaining is None


if __name__ == '__main__':
    pytest.main([__file__])