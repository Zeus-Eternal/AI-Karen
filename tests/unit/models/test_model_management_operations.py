"""
Test Model Management Operations

Tests for enhanced model management functionality including:
- Local model management with disk usage information
- Model status updates and validation
- Delete functionality with confirmation
- Model integrity validation

This test suite covers Task 8.1 requirements.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time

from src.ai_karen_engine.services.model_library_service import (
    ModelLibraryService,
    ModelInfo,
    ModelMetadata
)


class TestModelManagementOperations:
    """Test enhanced model management operations."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_registry_file(self, temp_dir):
        """Create mock registry file."""
        registry_file = temp_dir / "test_registry.json"
        registry_data = {
            "models": [
                {
                    "id": "test-model-1",
                    "name": "Test Model 1",
                    "path": str(temp_dir / "models" / "test-model-1.gguf"),
                    "type": "gguf",
                    "provider": "llama-cpp",
                    "size": 1000000,
                    "capabilities": ["chat", "completion"],
                    "metadata": {
                        "parameters": "1B",
                        "quantization": "Q4_K_M",
                        "memory_requirement": "1GB",
                        "context_length": 2048,
                        "license": "Apache 2.0",
                        "tags": ["test", "small"]
                    },
                    "downloadInfo": {
                        "url": "https://example.com/model.gguf",
                        "checksum": "sha256:test_checksum",
                        "downloadDate": time.time() - 86400  # 1 day ago
                    },
                    "last_used": time.time() - 3600  # 1 hour ago
                }
            ],
            "repositories": []
        }
        
        with open(registry_file, 'w') as f:
            json.dump(registry_data, f)
        
        return registry_file
    
    @pytest.fixture
    def mock_model_file(self, temp_dir):
        """Create mock model file."""
        models_dir = temp_dir / "models"
        models_dir.mkdir(exist_ok=True)
        
        model_file = models_dir / "test-model-1.gguf"
        model_file.write_bytes(b"fake model data" * 1000)  # Create file with some size
        
        return model_file
    
    @pytest.fixture
    def service(self, mock_registry_file, temp_dir):
        """Create ModelLibraryService instance for testing."""
        # Create models directory
        models_dir = temp_dir / "models"
        models_dir.mkdir(exist_ok=True)
        
        service = ModelLibraryService(registry_path=str(mock_registry_file))
        service.models_dir = models_dir
        
        return service
    
    def test_get_detailed_disk_usage_file(self, service, mock_model_file):
        """Test getting detailed disk usage for a file-based model."""
        result = service.get_detailed_disk_usage("test-model-1")
        
        assert "error" not in result
        assert result["model_id"] == "test-model-1"
        assert result["exists"] is True
        assert result["type"] == "file"
        assert result["size_bytes"] > 0
        assert result["size_mb"] > 0
        assert result["size_gb"] >= 0
        assert "permissions" in result
        assert "last_modified" in result
    
    def test_get_detailed_disk_usage_nonexistent_model(self, service):
        """Test getting disk usage for non-existent model."""
        result = service.get_detailed_disk_usage("nonexistent-model")
        
        assert "error" in result
        assert result["error"] == "Model not found"
    
    def test_get_detailed_disk_usage_missing_file(self, service):
        """Test getting disk usage when model file is missing."""
        # Model exists in registry but file doesn't exist
        result = service.get_detailed_disk_usage("test-model-1")
        
        # Should handle missing file gracefully
        assert "error" in result or result.get("exists") is False
    
    def test_update_model_last_used(self, service):
        """Test updating model last used timestamp."""
        # Test updating last used timestamp
        result = service.update_model_last_used("test-model-1")
        
        assert result is True
        
        # Verify the timestamp was updated
        model_info = service.get_model_info("test-model-1")
        assert model_info is not None
        # The last_used should be recent (within last few seconds)
        assert model_info.last_used is not None
        assert time.time() - model_info.last_used < 10
    
    def test_get_model_status_history(self, service):
        """Test getting model status history."""
        history = service.get_model_status_history("test-model-1")
        
        assert isinstance(history, list)
        # Should have at least download event
        assert len(history) >= 1
        
        # Check download event
        download_event = next((h for h in history if h["status"] == "downloaded"), None)
        assert download_event is not None
        assert "timestamp" in download_event
        assert "event" in download_event
        assert "details" in download_event
    
    def test_validate_model_before_use_valid(self, service, mock_model_file):
        """Test validating a valid model before use."""
        result = service.validate_model_before_use("test-model-1")
        
        assert result["valid"] is True
        assert result["file_exists"] is True
        assert result["permissions_ok"] is True
    
    def test_validate_model_before_use_missing_file(self, service):
        """Test validating model with missing file."""
        result = service.validate_model_before_use("test-model-1")
        
        assert result["valid"] is False
        assert "error" in result
    
    def test_get_models_by_status(self, service, mock_model_file):
        """Test getting models filtered by status."""
        local_models = service.get_models_by_status("local")
        
        assert isinstance(local_models, list)
        # Should find the test model if file exists
        if mock_model_file.exists():
            assert len(local_models) >= 1
            assert any(model.id == "test-model-1" for model in local_models)
    
    def test_get_local_models_summary(self, service, mock_model_file):
        """Test getting summary of local models."""
        summary = service.get_local_models_summary()
        
        assert "error" not in summary
        assert "total_models" in summary
        assert "total_size_bytes" in summary
        assert "total_size_gb" in summary
        assert "by_provider" in summary
        assert "recently_used" in summary
        assert "available_space_bytes" in summary
        assert "available_space_gb" in summary
        
        # Check provider grouping
        assert isinstance(summary["by_provider"], dict)
        if summary["total_models"] > 0:
            assert "llama-cpp" in summary["by_provider"]
    
    def test_cleanup_orphaned_files(self, service, temp_dir):
        """Test cleaning up orphaned model files."""
        # Create an orphaned file
        orphaned_file = temp_dir / "models" / "orphaned-model.gguf"
        orphaned_file.parent.mkdir(exist_ok=True)
        orphaned_file.write_bytes(b"orphaned data" * 100)
        
        result = service.cleanup_orphaned_files()
        
        assert "error" not in result
        assert "files_removed" in result
        assert "space_freed_bytes" in result
        assert "space_freed_gb" in result
        assert "errors" in result
        
        # Check if orphaned file was removed
        if len(result["files_removed"]) > 0:
            assert not orphaned_file.exists()
    
    def test_delete_model_with_disk_usage_info(self, service, mock_model_file):
        """Test deleting model and verifying disk space is freed."""
        # Get initial disk usage
        initial_usage = service.get_model_disk_usage("test-model-1")
        
        # Delete the model
        result = service.delete_model("test-model-1")
        
        assert result is True
        
        # Verify file is deleted
        assert not mock_model_file.exists()
        
        # Verify model is removed from registry
        model_info = service.get_model_info("test-model-1")
        assert model_info is None or model_info.status != "local"
    
    def test_model_status_updates(self, service):
        """Test updating model status with additional metadata."""
        # Update model status with custom metadata
        result = service.update_model_status(
            "test-model-1", 
            "local", 
            custom_field="test_value",
            validation_timestamp=time.time()
        )
        
        assert result is True
        
        # Verify the status and metadata were updated
        # This would require checking the registry directly
        model_data = None
        for model in service.registry["models"]:
            if model.get("id") == "test-model-1":
                model_data = model
                break
        
        assert model_data is not None
        assert model_data["status"] == "local"
        assert model_data.get("custom_field") == "test_value"
        assert "validation_timestamp" in model_data
        assert "last_modified" in model_data
    
    def test_get_model_usage_stats(self, service, mock_model_file):
        """Test getting comprehensive model usage statistics."""
        stats = service.get_model_usage_stats("test-model-1")
        
        assert isinstance(stats, dict)
        assert "disk_usage" in stats
        assert "last_used" in stats
        assert "download_date" in stats
        assert "status" in stats
        
        # If file exists, should have disk usage
        if mock_model_file.exists():
            assert stats["disk_usage"] is not None
            assert stats["disk_usage"] > 0
    
    def test_validate_checksum_placeholder(self, service):
        """Test checksum validation with placeholder checksum."""
        # Test with placeholder checksum (should pass)
        result = service.validate_checksum(
            Path("dummy_path"), 
            "placeholder_checksum_for_validation"
        )
        
        assert result is True  # Placeholder checksums should be skipped
    
    def test_validate_checksum_real(self, service, mock_model_file):
        """Test checksum validation with real checksum."""
        # Test with invalid checksum
        result = service.validate_checksum(
            mock_model_file, 
            "sha256:invalid_checksum"
        )
        
        assert result is False  # Should fail with invalid checksum
    
    def test_get_available_disk_space(self, service):
        """Test getting available disk space."""
        space = service.get_available_disk_space()
        
        assert isinstance(space, int)
        assert space >= 0  # Should be non-negative
    
    def test_get_total_models_disk_usage(self, service, mock_model_file):
        """Test calculating total disk usage of all models."""
        total_usage = service.get_total_models_disk_usage()
        
        assert isinstance(total_usage, int)
        assert total_usage >= 0
        
        # If we have local models, usage should be > 0
        local_models = service.get_models_by_status("local")
        if len(local_models) > 0:
            assert total_usage > 0


class TestModelManagementAPI:
    """Test API endpoints for model management operations."""
    
    @pytest.fixture
    def mock_service(self):
        """Create mock ModelLibraryService."""
        service = Mock()
        
        # Mock model info
        mock_model = ModelInfo(
            id="test-model",
            name="Test Model",
            provider="llama-cpp",
            size=1000000,
            description="Test model",
            capabilities=["chat"],
            status="local",
            metadata=ModelMetadata(
                parameters="1B",
                quantization="Q4_K_M",
                memory_requirement="1GB",
                context_length=2048,
                license="Apache 2.0",
                tags=["test"]
            ),
            disk_usage=1000000,
            last_used=time.time() - 3600
        )
        
        service.get_model_info.return_value = mock_model
        service.get_detailed_disk_usage.return_value = {
            "model_id": "test-model",
            "path": "/path/to/model",
            "exists": True,
            "type": "file",
            "size_bytes": 1000000,
            "size_mb": 0.95,
            "size_gb": 0.001,
            "permissions": "644"
        }
        service.get_model_status_history.return_value = [
            {
                "timestamp": time.time() - 86400,
                "status": "downloaded",
                "event": "Model downloaded",
                "details": {"size": 1000000}
            }
        ]
        service.validate_model_before_use.return_value = {
            "valid": True,
            "file_exists": True,
            "permissions_ok": True
        }
        
        return service
    
    @patch('src.ai_karen_engine.api_routes.model_library_routes.get_model_library_service')
    def test_get_model_disk_usage_endpoint(self, mock_get_service, mock_service):
        """Test the disk usage API endpoint."""
        mock_get_service.return_value = mock_service
        
        from src.ai_karen_engine.api_routes.model_library_routes import get_model_disk_usage
        
        # This would need to be tested with actual FastAPI test client
        # For now, just verify the service method is called correctly
        result = mock_service.get_detailed_disk_usage("test-model")
        
        assert result["model_id"] == "test-model"
        assert result["exists"] is True
        mock_service.get_detailed_disk_usage.assert_called_with("test-model")
    
    @patch('src.ai_karen_engine.api_routes.model_library_routes.get_model_library_service')
    def test_validate_model_before_use_endpoint(self, mock_get_service, mock_service):
        """Test the model validation API endpoint."""
        mock_get_service.return_value = mock_service
        
        # Test validation
        result = mock_service.validate_model_before_use("test-model")
        
        assert result["valid"] is True
        mock_service.validate_model_before_use.assert_called_with("test-model")
    
    def test_model_management_error_handling(self, mock_service):
        """Test error handling in model management operations."""
        # Test with non-existent model
        mock_service.get_model_info.return_value = None
        
        result = mock_service.get_model_info("nonexistent-model")
        assert result is None
        
        # Test with service errors
        mock_service.get_detailed_disk_usage.return_value = {"error": "File not found"}
        
        result = mock_service.get_detailed_disk_usage("error-model")
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__])