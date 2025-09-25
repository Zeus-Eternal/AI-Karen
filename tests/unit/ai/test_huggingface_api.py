"""
Tests for HuggingFace API integration endpoints.

This module tests the HuggingFace model search, download, and management
API endpoints to ensure they work correctly with the HuggingFace service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from ai_karen_engine.api_routes.model_management_routes import router
from ai_karen_engine.inference.huggingface_service import HFModel, ModelInfo, DownloadJob


# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestHuggingFaceSearchAPI:
    """Test HuggingFace model search API."""
    
    @patch('ai_karen_engine.api_routes.model_management_routes.get_huggingface_service')
    def test_search_models_success(self, mock_get_service):
        """Test successful model search."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock search results
        mock_models = [
            HFModel(
                id="microsoft/DialoGPT-medium",
                name="DialoGPT-medium",
                author="microsoft",
                description="A conversational AI model",
                tags=["conversational", "pytorch"],
                downloads=1000,
                likes=50,
                size=500000000,  # 500MB
                files=[{"rfilename": "pytorch_model.bin", "size": 500000000}]
            ),
            HFModel(
                id="huggingface/CodeBERTa-small-v1",
                name="CodeBERTa-small-v1", 
                author="huggingface",
                description="A code understanding model",
                tags=["code", "bert"],
                downloads=2000,
                likes=75,
                size=200000000,  # 200MB
                files=[{"rfilename": "pytorch_model.bin", "size": 200000000}]
            )
        ]
        mock_service.search_models.return_value = mock_models
        
        # Test request
        response = client.post("/api/models/huggingface/search", json={
            "query": "conversational",
            "tags": ["pytorch"],
            "sort": "downloads",
            "direction": "desc",
            "limit": 10
        })
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == "conversational"
        assert data["total_results"] == 2
        assert len(data["models"]) == 2
        
        # Check first model
        model1 = data["models"][0]
        assert model1["id"] == "microsoft/DialoGPT-medium"
        assert model1["name"] == "DialoGPT-medium"
        assert model1["author"] == "microsoft"
        assert model1["downloads"] == 1000
        assert "conversational" in model1["tags"]
        
        # Verify service was called correctly
        mock_service.search_models.assert_called_once()
    
    @patch('ai_karen_engine.api_routes.model_management_routes.get_huggingface_service')
    def test_search_models_service_unavailable(self, mock_get_service):
        """Test search when HuggingFace service is unavailable."""
        mock_get_service.return_value = None
        
        response = client.post("/api/models/huggingface/search", json={
            "query": "test"
        })
        
        assert response.status_code == 503
        assert "Hugging Face service not available" in response.json()["detail"]
    
    @patch('ai_karen_engine.api_routes.model_management_routes.get_huggingface_service')
    def test_search_models_empty_results(self, mock_get_service):
        """Test search with no results."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.search_models.return_value = []
        
        response = client.post("/api/models/huggingface/search", json={
            "query": "nonexistent_model_xyz"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 0
        assert data["models"] == []
    
    @patch('ai_karen_engine.api_routes.model_management_routes.get_huggingface_service')
    def test_search_models_with_filters(self, mock_get_service):
        """Test search with various filters."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.search_models.return_value = []
        
        response = client.post("/api/models/huggingface/search", json={
            "query": "llama",
            "tags": ["text-generation", "pytorch"],
            "sort": "likes",
            "direction": "asc",
            "limit": 5,
            "filter_format": "gguf"
        })
        
        assert response.status_code == 200
        # Verify the service was called with correct parameters
        mock_service.search_models.assert_called_once()


class TestModelDownloadAPI:
    """Test model download API."""
    
    @patch('ai_karen_engine.api_routes.model_management_routes.get_job_manager')
    @patch('ai_karen_engine.api_routes.model_management_routes.get_huggingface_service')
    def test_download_model_success(self, mock_get_hf_service, mock_get_job_manager):
        """Test successful model download initiation."""
        # Mock services
        mock_hf_service = Mock()
        mock_get_hf_service.return_value = mock_hf_service
        
        mock_job_manager = Mock()
        mock_job = Mock()
        mock_job.id = "job_123"
        mock_job_manager.create_job.return_value = mock_job
        mock_get_job_manager.return_value = mock_job_manager
        
        # Test request
        response = client.post("/api/models/download", json={
            "model_id": "microsoft/DialoGPT-medium",
            "preference": "auto"
        })
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job_123"
        assert "Download started" in data["message"]
        
        # Verify job was created
        mock_job_manager.create_job.assert_called_once()
        call_args = mock_job_manager.create_job.call_args
        assert call_args[1]["kind"] == "download"
        assert "microsoft/DialoGPT-medium" in call_args[1]["title"]
    
    @patch('ai_karen_engine.api_routes.model_management_routes.get_huggingface_service')
    def test_download_model_service_unavailable(self, mock_get_service):
        """Test download when HuggingFace service is unavailable."""
        mock_get_service.return_value = None
        
        response = client.post("/api/models/download", json={
            "model_id": "test/model"
        })
        
        assert response.status_code == 503
        assert "Hugging Face service not available" in response.json()["detail"]
    
    @patch('ai_karen_engine.api_routes.model_management_routes.get_job_manager')
    @patch('ai_karen_engine.api_routes.model_management_routes.get_huggingface_service')
    def test_download_model_with_specific_artifact(self, mock_get_hf_service, mock_get_job_manager):
        """Test download with specific artifact selection."""
        # Mock services
        mock_hf_service = Mock()
        mock_get_hf_service.return_value = mock_hf_service
        
        mock_job_manager = Mock()
        mock_job = Mock()
        mock_job.id = "job_456"
        mock_job_manager.create_job.return_value = mock_job
        mock_get_job_manager.return_value = mock_job_manager
        
        # Test request with specific artifact
        response = client.post("/api/models/download", json={
            "model_id": "microsoft/DialoGPT-medium",
            "artifact": "pytorch_model.bin",
            "preference": "pytorch"
        })
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job_456"
        
        # Verify parameters were passed correctly
        call_args = mock_job_manager.create_job.call_args
        params = call_args[1]["parameters"]
        assert params["artifact"] == "pytorch_model.bin"
        assert params["preference"] == "pytorch"


class TestModelInfoAPI:
    """Test model info API."""
    
    @patch('ai_karen_engine.api_routes.model_management_routes.get_huggingface_service')
    def test_get_model_info_success(self, mock_get_service):
        """Test successful model info retrieval."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock model info
        mock_info = ModelInfo(
            id="microsoft/DialoGPT-medium",
            name="DialoGPT-medium",
            description="A conversational AI model",
            tags=["conversational", "pytorch"],
            files=[
                {"filename": "pytorch_model.bin", "size": 500000000},
                {"filename": "config.json", "size": 1000}
            ],
            config={"model_type": "gpt2"},
            license="MIT",
            downloads=1000,
            likes=50,
            size=500001000
        )
        mock_service.get_model_info.return_value = mock_info
        
        # Test request
        response = client.get("/api/models/huggingface/microsoft%2FDialoGPT-medium/info")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "microsoft/DialoGPT-medium"
        assert data["name"] == "DialoGPT-medium"
        assert data["description"] == "A conversational AI model"
        assert data["license"] == "MIT"
        assert data["downloads"] == 1000
        assert data["likes"] == 50
        assert len(data["files"]) == 2
        assert data["config"]["model_type"] == "gpt2"
        
        # Verify service was called correctly
        mock_service.get_model_info.assert_called_once_with("microsoft/DialoGPT-medium")
    
    @patch('ai_karen_engine.api_routes.model_management_routes.get_huggingface_service')
    def test_get_model_info_not_found(self, mock_get_service):
        """Test model info for non-existent model."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.get_model_info.return_value = None
        
        response = client.get("/api/models/huggingface/nonexistent%2Fmodel/info")
        
        assert response.status_code == 404
        assert "Model not found" in response.json()["detail"]
    
    @patch('ai_karen_engine.api_routes.model_management_routes.get_huggingface_service')
    def test_get_model_info_service_unavailable(self, mock_get_service):
        """Test model info when service is unavailable."""
        mock_get_service.return_value = None
        
        response = client.get("/api/models/huggingface/test%2Fmodel/info")
        
        assert response.status_code == 503
        assert "Hugging Face service not available" in response.json()["detail"]


class TestModelArtifactsAPI:
    """Test model artifacts API."""
    
    @patch('ai_karen_engine.api_routes.model_management_routes.get_huggingface_service')
    def test_get_model_artifacts_success(self, mock_get_service):
        """Test successful artifacts retrieval."""
        # Mock service
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        
        # Mock model info with various file types
        mock_info = ModelInfo(
            id="microsoft/DialoGPT-medium",
            name="DialoGPT-medium",
            description="Test model",
            tags=[],
            files=[
                {"filename": "model.gguf", "size": 400000000},
                {"filename": "pytorch_model.bin", "size": 500000000},
                {"filename": "model.safetensors", "size": 450000000},
                {"filename": "config.json", "size": 1000},
                {"filename": "tokenizer.json", "size": 2000}
            ]
        )
        mock_service.get_model_info.return_value = mock_info
        
        # Mock optimal artifact selection
        mock_service.select_optimal_artifact.return_value = {"filename": "model.gguf"}
        
        # Test request
        response = client.get("/api/models/huggingface/microsoft%2FDialoGPT-medium/artifacts")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert data["model_id"] == "microsoft/DialoGPT-medium"
        assert data["total_files"] == 5
        assert data["recommended"] == "model.gguf"
        
        # Check artifact categorization
        artifacts = data["artifacts"]
        assert len(artifacts["gguf"]) == 1
        assert len(artifacts["pytorch"]) == 1
        assert len(artifacts["safetensors"]) == 1
        assert len(artifacts["other"]) == 2  # config.json and tokenizer.json
        
        # Check GGUF artifact details
        gguf_artifact = artifacts["gguf"][0]
        assert gguf_artifact["filename"] == "model.gguf"
        assert gguf_artifact["type"] == "gguf"
        assert gguf_artifact["size_gb"] == 0.37  # ~400MB in GB
    
    @patch('ai_karen_engine.api_routes.model_management_routes.get_huggingface_service')
    def test_get_model_artifacts_not_found(self, mock_get_service):
        """Test artifacts for non-existent model."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.get_model_info.return_value = None
        
        response = client.get("/api/models/huggingface/nonexistent%2Fmodel/artifacts")
        
        assert response.status_code == 404
        assert "Model not found" in response.json()["detail"]


class TestHuggingFaceAPIIntegration:
    """Integration tests for HuggingFace API endpoints."""
    
    @patch('ai_karen_engine.inference.huggingface_service.HF_AVAILABLE', True)
    @patch('ai_karen_engine.inference.huggingface_service.HfApi')
    def test_search_and_download_flow(self, mock_hf_api):
        """Test complete search -> info -> download flow."""
        # This would be a more comprehensive integration test
        # For now, we'll keep it simple and just verify the endpoints exist
        
        # Test that search endpoint exists
        response = client.post("/api/models/huggingface/search", json={"query": "test"})
        # We expect either 200 (success) or 503 (service unavailable)
        assert response.status_code in [200, 503]
        
        # Test that download endpoint exists
        response = client.post("/api/models/download", json={"model_id": "test/model"})
        # We expect either 200 (success) or 503 (service unavailable)
        assert response.status_code in [200, 503]


if __name__ == "__main__":
    pytest.main([__file__])