"""
Tests for Model Library API Routes

Tests the REST API endpoints for model library functionality including:
- Model discovery and listing
- Download management
- Model metadata retrieval
- Local model management
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import test utilities
try:
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
except ImportError:
    pytest.skip("FastAPI not available", allow_module_level=True)

from ai_karen_engine.api_routes.model_library_routes import router
from ai_karen_engine.services.model_library_service import ModelInfo, DownloadTask, ModelMetadata


@pytest.fixture
def app():
    """Create test FastAPI app with model library routes."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_model_library_service():
    """Mock model library service."""
    with patch('ai_karen_engine.api_routes.model_library_routes.get_model_library_service') as mock:
        service = Mock()
        mock.return_value = service
        yield service


@pytest.fixture
def sample_model_info():
    """Sample model info for testing."""
    return ModelInfo(
        id="test-model-1",
        name="Test Model 1",
        provider="llama-cpp",
        size=1000000,
        description="A test model",
        capabilities=["text-generation", "chat"],
        status="available",
        metadata={
            "parameters": "1B",
            "quantization": "Q4_K_M",
            "memory_requirement": "1GB",
            "context_length": 2048,
            "license": "Apache 2.0",
            "tags": ["test", "small"]
        },
        download_url="https://example.com/model.gguf",
        checksum="sha256:test_checksum"
    )


@pytest.fixture
def sample_download_task():
    """Sample download task for testing."""
    return DownloadTask(
        task_id="task-123",
        model_id="test-model-1",
        url="https://example.com/model.gguf",
        filename="test-model.gguf",
        total_size=1000000,
        downloaded_size=500000,
        progress=50.0,
        status="downloading",
        start_time=1234567890.0,
        estimated_time_remaining=60.0
    )


class TestModelLibraryRoutes:
    """Test model library API routes."""
    
    def test_get_available_models_success(self, client, mock_model_library_service, sample_model_info):
        """Test successful model listing."""
        # Setup mock
        mock_model_library_service.get_available_models.return_value = [sample_model_info]
        
        # Make request
        response = client.get("/api/models/library")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        assert "total_count" in data
        assert "local_count" in data
        assert "available_count" in data
        
        assert len(data["models"]) == 1
        assert data["total_count"] == 1
        assert data["available_count"] == 1
        assert data["local_count"] == 0
        
        model = data["models"][0]
        assert model["id"] == "test-model-1"
        assert model["name"] == "Test Model 1"
        assert model["provider"] == "llama-cpp"
        assert model["status"] == "available"
    
    def test_get_available_models_with_filters(self, client, mock_model_library_service, sample_model_info):
        """Test model listing with filters."""
        # Setup mock
        mock_model_library_service.get_available_models.return_value = [sample_model_info]
        
        # Test provider filter
        response = client.get("/api/models/library?provider=llama-cpp")
        assert response.status_code == 200
        data = response.json()
        assert len(data["models"]) == 1
        
        # Test status filter
        response = client.get("/api/models/library?status=available")
        assert response.status_code == 200
        data = response.json()
        assert len(data["models"]) == 1
        
        # Test capability filter
        response = client.get("/api/models/library?capability=chat")
        assert response.status_code == 200
        data = response.json()
        assert len(data["models"]) == 1
        
        # Test filter that excludes model
        response = client.get("/api/models/library?provider=different-provider")
        assert response.status_code == 200
        data = response.json()
        assert len(data["models"]) == 0
    
    def test_get_available_models_error(self, client, mock_model_library_service):
        """Test model listing error handling."""
        # Setup mock to raise exception
        mock_model_library_service.get_available_models.side_effect = Exception("Service error")
        
        # Make request
        response = client.get("/api/models/library")
        
        # Verify error response
        assert response.status_code == 500
        assert "Service error" in response.json()["detail"]
    
    def test_initiate_model_download_success(self, client, mock_model_library_service, sample_model_info, sample_download_task):
        """Test successful model download initiation."""
        # Setup mocks
        mock_model_library_service.get_model_info.return_value = sample_model_info
        mock_model_library_service.download_model.return_value = sample_download_task
        
        # Make request
        response = client.post("/api/models/download", json={"model_id": "test-model-1"})
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["task_id"] == "task-123"
        assert data["model_id"] == "test-model-1"
        assert data["status"] == "downloading"
        assert data["progress"] == 50.0
        assert data["estimated_time_remaining"] == 60.0
    
    def test_initiate_model_download_model_not_found(self, client, mock_model_library_service):
        """Test download initiation with non-existent model."""
        # Setup mock
        mock_model_library_service.get_model_info.return_value = None
        
        # Make request
        response = client.post("/api/models/download", json={"model_id": "non-existent"})
        
        # Verify error response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_initiate_model_download_already_local(self, client, mock_model_library_service, sample_model_info):
        """Test download initiation for already downloaded model."""
        # Setup mock - model is already local
        sample_model_info.status = "local"
        mock_model_library_service.get_model_info.return_value = sample_model_info
        
        # Make request
        response = client.post("/api/models/download", json={"model_id": "test-model-1"})
        
        # Verify error response
        assert response.status_code == 400
        assert "already downloaded" in response.json()["detail"]
    
    def test_get_download_progress_success(self, client, mock_model_library_service, sample_download_task):
        """Test successful download progress retrieval."""
        # Setup mock
        mock_model_library_service.get_download_status.return_value = sample_download_task
        
        # Make request
        response = client.get("/api/models/download/task-123")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["task_id"] == "task-123"
        assert data["model_id"] == "test-model-1"
        assert data["progress"] == 50.0
        assert data["status"] == "downloading"
    
    def test_get_download_progress_not_found(self, client, mock_model_library_service):
        """Test download progress retrieval for non-existent task."""
        # Setup mock
        mock_model_library_service.get_download_status.return_value = None
        
        # Make request
        response = client.get("/api/models/download/non-existent")
        
        # Verify error response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_delete_local_model_success(self, client, mock_model_library_service, sample_model_info):
        """Test successful local model deletion."""
        # Setup mock - model is local
        sample_model_info.status = "local"
        mock_model_library_service.get_model_info.return_value = sample_model_info
        mock_model_library_service.delete_model.return_value = True
        
        # Make request
        response = client.delete("/api/models/test-model-1")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        assert data["model_id"] == "test-model-1"
    
    def test_delete_local_model_not_found(self, client, mock_model_library_service):
        """Test deletion of non-existent model."""
        # Setup mock
        mock_model_library_service.get_model_info.return_value = None
        
        # Make request
        response = client.delete("/api/models/non-existent")
        
        # Verify error response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_delete_local_model_not_local(self, client, mock_model_library_service, sample_model_info):
        """Test deletion of non-local model."""
        # Setup mock - model is not local
        sample_model_info.status = "available"
        mock_model_library_service.get_model_info.return_value = sample_model_info
        
        # Make request
        response = client.delete("/api/models/test-model-1")
        
        # Verify error response
        assert response.status_code == 400
        assert "not a local model" in response.json()["detail"]
    
    def test_cancel_download_success(self, client, mock_model_library_service, sample_download_task):
        """Test successful download cancellation."""
        # Setup mock
        mock_model_library_service.get_download_status.return_value = sample_download_task
        mock_model_library_service.cancel_download.return_value = True
        
        # Make request
        response = client.delete("/api/models/download/task-123")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "cancelled successfully" in data["message"]
        assert data["task_id"] == "task-123"
    
    def test_cancel_download_not_found(self, client, mock_model_library_service):
        """Test cancellation of non-existent download."""
        # Setup mock
        mock_model_library_service.get_download_status.return_value = None
        
        # Make request
        response = client.delete("/api/models/download/non-existent")
        
        # Verify error response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_cancel_download_invalid_status(self, client, mock_model_library_service, sample_download_task):
        """Test cancellation of completed download."""
        # Setup mock - download is completed
        sample_download_task.status = "completed"
        mock_model_library_service.get_download_status.return_value = sample_download_task
        
        # Make request
        response = client.delete("/api/models/download/task-123")
        
        # Verify error response
        assert response.status_code == 400
        assert "Cannot cancel" in response.json()["detail"]
    
    def test_get_model_metadata_success(self, client, mock_model_library_service, sample_model_info):
        """Test successful model metadata retrieval."""
        # Setup mock
        mock_model_library_service.get_model_info.return_value = sample_model_info
        
        metadata = ModelMetadata(
            parameters="1B",
            quantization="Q4_K_M",
            memory_requirement="1GB",
            context_length=2048,
            license="Apache 2.0",
            tags=["test", "small"],
            architecture="Llama",
            training_data="Test data",
            performance_metrics={"speed": "fast"}
        )
        mock_model_library_service.metadata_service.get_model_metadata.return_value = metadata
        
        # Make request
        response = client.get("/api/models/metadata/test-model-1")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["parameters"] == "1B"
        assert data["quantization"] == "Q4_K_M"
        assert data["memory_requirement"] == "1GB"
        assert data["context_length"] == 2048
        assert data["license"] == "Apache 2.0"
        assert data["tags"] == ["test", "small"]
        assert data["architecture"] == "Llama"
    
    def test_get_model_metadata_not_found(self, client, mock_model_library_service):
        """Test metadata retrieval for non-existent model."""
        # Setup mock
        mock_model_library_service.get_model_info.return_value = None
        
        # Make request
        response = client.get("/api/models/metadata/non-existent")
        
        # Verify error response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_list_model_providers(self, client, mock_model_library_service, sample_model_info):
        """Test model providers listing."""
        # Setup mock
        mock_model_library_service.get_available_models.return_value = [sample_model_info]
        
        # Make request
        response = client.get("/api/models/providers")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "providers" in data
        assert "total_providers" in data
        assert data["total_providers"] == 1
        
        provider = data["providers"][0]
        assert provider["name"] == "llama-cpp"
        assert provider["total_models"] == 1
        assert provider["available_models"] == 1
        assert provider["local_models"] == 0
    
    def test_list_model_capabilities(self, client, mock_model_library_service, sample_model_info):
        """Test model capabilities listing."""
        # Setup mock
        mock_model_library_service.get_available_models.return_value = [sample_model_info]
        
        # Make request
        response = client.get("/api/models/capabilities")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "capabilities" in data
        assert "total_capabilities" in data
        assert data["total_capabilities"] == 2
        
        # Check capabilities
        capability_names = [cap["name"] for cap in data["capabilities"]]
        assert "text-generation" in capability_names
        assert "chat" in capability_names
    
    def test_cleanup_downloads(self, client, mock_model_library_service):
        """Test download cleanup."""
        # Make request
        response = client.post("/api/models/cleanup")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "cleanup completed" in data["message"]
        
        # Verify service method was called
        mock_model_library_service.cleanup.assert_called_once()


class TestModelLibraryRoutesIntegration:
    """Integration tests for model library routes."""
    
    @pytest.mark.integration
    def test_full_workflow_simulation(self, client):
        """Test a complete workflow simulation."""
        with patch('ai_karen_engine.api_routes.model_library_routes.get_model_library_service') as mock_service_getter:
            # Create mock service
            service = Mock()
            mock_service_getter.return_value = service
            
            # Mock model info
            model_info = ModelInfo(
                id="workflow-test",
                name="Workflow Test Model",
                provider="llama-cpp",
                size=500000,
                description="Test model for workflow",
                capabilities=["chat"],
                status="available",
                download_url="https://example.com/test.gguf"
            )
            
            # Mock download task
            download_task = DownloadTask(
                task_id="workflow-task",
                model_id="workflow-test",
                url="https://example.com/test.gguf",
                filename="test.gguf",
                total_size=500000,
                downloaded_size=0,
                progress=0.0,
                status="pending"
            )
            
            # Setup service mocks
            service.get_available_models.return_value = [model_info]
            service.get_model_info.return_value = model_info
            service.download_model.return_value = download_task
            service.get_download_status.return_value = download_task
            
            # 1. List available models
            response = client.get("/api/models/library")
            assert response.status_code == 200
            models = response.json()["models"]
            assert len(models) == 1
            assert models[0]["id"] == "workflow-test"
            
            # 2. Initiate download
            response = client.post("/api/models/download", json={"model_id": "workflow-test"})
            assert response.status_code == 200
            task_data = response.json()
            assert task_data["task_id"] == "workflow-task"
            
            # 3. Check download progress
            response = client.get("/api/models/download/workflow-task")
            assert response.status_code == 200
            progress_data = response.json()
            assert progress_data["task_id"] == "workflow-task"
            
            # 4. Simulate download completion and model becomes local
            model_info.status = "local"
            service.delete_model.return_value = True
            
            # 5. Delete local model
            response = client.delete("/api/models/workflow-test")
            assert response.status_code == 200
            delete_data = response.json()
            assert "deleted successfully" in delete_data["message"]


if __name__ == "__main__":
    pytest.main([__file__])