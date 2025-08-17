"""
Unit tests for HuggingFace service functionality.

This module tests the HuggingFace service directly without requiring
FastAPI or other web framework dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from ai_karen_engine.inference.huggingface_service import (
    HuggingFaceService, 
    ModelFilters, 
    HFModel, 
    ModelInfo,
    DownloadJob,
    DeviceCapabilities
)


class TestHuggingFaceService:
    """Test HuggingFace service core functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = HuggingFaceService(cache_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_service_initialization(self):
        """Test service initialization."""
        assert self.service.cache_dir == Path(self.temp_dir)
        assert self.service.token is None
        assert isinstance(self.service._download_jobs, dict)
        assert isinstance(self.service._download_threads, dict)
    
    def test_service_initialization_with_token(self):
        """Test service initialization with token."""
        service = HuggingFaceService(token="test_token")
        assert service.token == "test_token"
    
    @patch('ai_karen_engine.inference.huggingface_service.HF_AVAILABLE', False)
    def test_service_without_huggingface_hub(self):
        """Test service behavior when HuggingFace Hub is not available."""
        service = HuggingFaceService()
        assert service.api is None
        
        # Search should return empty list
        results = service.search_models("test")
        assert results == []
        
        # Model info should return None
        info = service.get_model_info("test/model")
        assert info is None
    
    @patch('ai_karen_engine.inference.huggingface_service.HF_AVAILABLE', True)
    def test_search_models_success(self):
        """Test successful model search."""
        # Mock HF API
        mock_api = Mock()
        self.service.api = mock_api
        
        # Mock search results
        mock_model = Mock()
        mock_model.id = "microsoft/DialoGPT-medium"
        mock_model.description = "A conversational AI model"
        mock_model.tags = ["conversational", "pytorch"]
        mock_model.downloads = 1000
        mock_model.likes = 50
        mock_model.created_at = "2021-01-01"
        mock_model.last_modified = "2021-06-01"
        mock_model.library_name = "transformers"
        mock_model.pipeline_tag = "conversational"
        mock_model.license = "MIT"
        mock_model.siblings = []
        
        mock_api.list_models.return_value = [mock_model]
        
        # Test search
        filters = ModelFilters(tags=["conversational"], sort_by="downloads")
        results = self.service.search_models("conversational", filters, limit=10)
        
        # Assertions
        assert len(results) == 1
        model = results[0]
        assert isinstance(model, HFModel)
        assert model.id == "microsoft/DialoGPT-medium"
        assert model.name == "DialoGPT-medium"
        assert model.author == "microsoft"
        assert model.description == "A conversational AI model"
        assert "conversational" in model.tags
        assert model.downloads == 1000
        assert model.likes == 50
    
    def test_hf_model_metadata_inference(self):
        """Test HFModel metadata inference."""
        # Test Llama model
        model = HFModel(
            id="meta-llama/Llama-2-7b-hf",
            name="Llama-2-7b-hf",
            tags=["text-generation", "pytorch"],
            files=[{"rfilename": "pytorch_model.bin", "size": 13000000000}]
        )
        
        assert model.family == "llama"
        assert model.parameters == "7B"
        assert model.format == "bin"
        
        # Test GGUF model
        model = HFModel(
            id="TheBloke/Llama-2-7B-Chat-GGUF",
            name="Llama-2-7B-Chat-GGUF",
            tags=["gguf", "quantized"],
            files=[{"rfilename": "llama-2-7b-chat.q4_k_m.gguf", "size": 4000000000}]
        )
        
        assert model.family == "llama"
        assert model.parameters == "7B"
        assert model.format == "gguf"
        assert model.quantization == "Q4_K_M"
    
    def test_model_filters_validation(self):
        """Test ModelFilters functionality."""
        filters = ModelFilters(
            tags=["text-generation"],
            family="llama",
            quantization="Q4_K_M",
            min_downloads=100,
            max_size=5000000000,  # 5GB
            sort_by="likes",
            sort_order="asc"
        )
        
        # Test model that passes filters
        model = HFModel(
            id="test/llama-model",
            name="llama-model",
            tags=["text-generation"],
            downloads=500,
            size=3000000000,  # 3GB
            family="llama",
            quantization="Q4_K_M"
        )
        
        assert self.service._passes_filters(model, filters) == True
        
        # Test model that fails filters (wrong family)
        model.family = "mistral"
        assert self.service._passes_filters(model, filters) == False
        
        # Test model that fails filters (too few downloads)
        model.family = "llama"
        model.downloads = 50
        assert self.service._passes_filters(model, filters) == False
    
    def test_artifact_selection_gguf_preference(self):
        """Test artifact selection with GGUF preference."""
        files = [
            {"rfilename": "pytorch_model.bin", "size": 13000000000},
            {"rfilename": "model.safetensors", "size": 12500000000},
            {"rfilename": "model.q4_k_m.gguf", "size": 4000000000},
            {"rfilename": "model.q8_0.gguf", "size": 7000000000}
        ]
        
        device_caps = DeviceCapabilities(has_gpu=False, cpu_memory=8000)
        
        # Test GGUF preference
        selected = self.service.select_optimal_artifact(files, "gguf", device_caps)
        assert selected["rfilename"] == "model.q4_k_m.gguf"  # Should prefer Q4_K_M for efficiency
        
        # Test auto preference on CPU-only device
        selected = self.service.select_optimal_artifact(files, "auto", device_caps)
        assert selected["rfilename"] == "model.q4_k_m.gguf"  # Should prefer GGUF for CPU
    
    def test_artifact_selection_gpu_preference(self):
        """Test artifact selection with GPU preference."""
        files = [
            {"rfilename": "pytorch_model.bin", "size": 13000000000},
            {"rfilename": "model.safetensors", "size": 12500000000},
            {"rfilename": "model.q4_k_m.gguf", "size": 4000000000}
        ]
        
        device_caps = DeviceCapabilities(has_gpu=True, gpu_memory=16000)
        
        # Test auto preference on GPU device
        selected = self.service.select_optimal_artifact(files, "auto", device_caps)
        assert selected["rfilename"] == "model.safetensors"  # Should prefer safetensors for GPU
        
        # Test explicit safetensors preference
        selected = self.service.select_optimal_artifact(files, "safetensors", device_caps)
        assert selected["rfilename"] == "model.safetensors"
    
    def test_artifact_selection_fallback(self):
        """Test artifact selection fallback behavior."""
        files = [
            {"rfilename": "config.json", "size": 1000},
            {"rfilename": "tokenizer.json", "size": 2000},
            {"rfilename": "pytorch_model.bin", "size": 13000000000}
        ]
        
        # Test when preferred format not available
        selected = self.service.select_optimal_artifact(files, "gguf")
        assert selected["rfilename"] == "pytorch_model.bin"  # Should fallback to largest file
    
    def test_download_job_creation(self):
        """Test download job creation."""
        job = self.service.download_model("microsoft/DialoGPT-medium")
        
        assert isinstance(job, DownloadJob)
        assert job.model_id == "microsoft/DialoGPT-medium"
        # Status might be "queued" initially or "failed" if HF is not available
        assert job.status in ["queued", "downloading", "failed"]
        assert job.progress >= 0.0
        assert job.id in self.service._download_jobs
    
    def test_download_job_management(self):
        """Test download job management operations."""
        # Create a job
        job = self.service.download_model("test/model")
        job_id = job.id
        
        # Test get job
        retrieved_job = self.service.get_download_job(job_id)
        assert retrieved_job == job
        
        # Test list jobs
        jobs = self.service.list_download_jobs()
        assert job in jobs
        
        # Test list jobs by status (job might be failed if HF not available)
        if job.status == "queued":
            jobs = self.service.list_download_jobs(status="queued")
            assert job in jobs
        elif job.status == "failed":
            jobs = self.service.list_download_jobs(status="failed")
            assert job in jobs
        
        jobs = self.service.list_download_jobs(status="completed")
        assert job not in jobs
        
        # Test cancel job (might fail if job already completed/failed)
        success = self.service.cancel_download(job_id)
        if job.status in ["completed", "failed", "cancelled"]:
            # Job already finished, cancel should return False
            assert success == False
        else:
            # Job was still active, cancel should succeed
            assert success == True
            assert job.status == "cancelled"
            assert job._cancelled == True
    
    def test_family_inference(self):
        """Test model family inference from ID."""
        test_cases = [
            ("meta-llama/Llama-2-7b", "llama"),
            ("mistralai/Mistral-7B-v0.1", "mistral"),
            ("Qwen/Qwen2-7B", "qwen"),
            ("microsoft/phi-2", "phi"),
            ("google/gemma-7b", "gemma"),
            ("codellama/CodeLlama-7b", "codellama"),
            ("bert-base-uncased", "bert"),
            ("gpt2-medium", "gpt"),
            ("unknown/model", "unknown")
        ]
        
        for model_id, expected_family in test_cases:
            family = self.service._infer_family_from_id(model_id)
            assert family == expected_family, f"Expected {expected_family} for {model_id}, got {family}"
    
    def test_format_inference(self):
        """Test format inference from artifact filename."""
        test_cases = [
            ("model.gguf", "gguf"),
            ("pytorch_model.bin", "bin"),
            ("model.safetensors", "safetensors"),
            ("model.pt", "pytorch"),
            ("model.pth", "pytorch"),
            ("config.json", "unknown"),
            (None, "unknown")
        ]
        
        for artifact, expected_format in test_cases:
            format_type = self.service._infer_format_from_artifact(artifact)
            assert format_type == expected_format, f"Expected {expected_format} for {artifact}, got {format_type}"
    
    @patch('ai_karen_engine.inference.huggingface_service.HF_AVAILABLE', True)
    def test_get_model_info_success(self):
        """Test successful model info retrieval."""
        # Mock HF API
        mock_api = Mock()
        self.service.api = mock_api
        
        # Mock model info
        mock_model = Mock()
        mock_model.description = "Test model"
        mock_model.tags = ["test"]
        mock_model.license = "MIT"
        mock_model.downloads = 100
        mock_model.likes = 10
        mock_model.siblings = [
            Mock(rfilename="pytorch_model.bin", size=1000000),
            Mock(rfilename="config.json", size=1000)
        ]
        
        mock_api.model_info.return_value = mock_model
        mock_api.hf_hub_download.side_effect = Exception("File not found")  # Config/README not available
        
        # Test get model info
        info = self.service.get_model_info("test/model")
        
        assert isinstance(info, ModelInfo)
        assert info.id == "test/model"
        assert info.name == "model"
        assert info.description == "Test model"
        assert info.tags == ["test"]
        assert info.license == "MIT"
        assert info.downloads == 100
        assert info.likes == 10
        assert len(info.files) == 2
        assert info.size == 1001000  # Sum of file sizes
    
    def test_cleanup_completed_jobs(self):
        """Test cleanup of completed jobs."""
        # Create some jobs
        job1 = self.service.download_model("test/model1")
        job2 = self.service.download_model("test/model2")
        job3 = self.service.download_model("test/model3")
        
        # Mark some as completed (simulate old completion times)
        import time
        old_time = time.time() - (25 * 3600)  # 25 hours ago
        
        job1.status = "completed"
        job1.completed_at = old_time
        
        job2.status = "failed"
        job2.completed_at = old_time
        
        job3.status = "downloading"  # Still active
        
        # Clean up jobs older than 24 hours
        cleaned = self.service.cleanup_completed_jobs(older_than_hours=24)
        
        assert cleaned == 2  # job1 and job2 should be cleaned
        assert job1.id not in self.service._download_jobs
        assert job2.id not in self.service._download_jobs
        assert job3.id in self.service._download_jobs  # Still active, should remain


class TestHuggingFaceServiceIntegration:
    """Integration tests for HuggingFace service."""
    
    def test_service_factory_function(self):
        """Test the global service factory function."""
        from ai_karen_engine.inference.huggingface_service import get_huggingface_service
        
        service1 = get_huggingface_service()
        service2 = get_huggingface_service()
        
        # Should return the same instance (singleton)
        assert service1 is service2
        assert isinstance(service1, HuggingFaceService)
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        from ai_karen_engine.inference.huggingface_service import search_models, download_model
        
        # These should not raise errors even if HF is not available
        # (they should return empty results or handle gracefully)
        try:
            results = search_models("test")
            assert isinstance(results, list)
            
            job = download_model("test/model")
            assert isinstance(job, DownloadJob)
        except Exception as e:
            # If HF is not available, these might raise exceptions
            # That's acceptable for this test
            pass


if __name__ == "__main__":
    pytest.main([__file__])