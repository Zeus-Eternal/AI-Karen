"""
Tests for Enhanced HuggingFace Model Discovery Service

Tests the enhanced HuggingFace service functionality including:
- Advanced model search with training filters
- Compatibility detection and analysis
- Enhanced download management
- Model registration and metadata management
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from typing import List, Dict, Any

from ai_karen_engine.services.enhanced_huggingface_service import (
    EnhancedHuggingFaceService,
    TrainingFilters,
    TrainableModel,
    CompatibilityReport,
    EnhancedDownloadJob,
    get_enhanced_huggingface_service
)


class TestEnhancedHuggingFaceService:
    """Test suite for Enhanced HuggingFace Service."""
    
    @pytest.fixture
    def mock_hf_api(self):
        """Mock HuggingFace API."""
        with patch('ai_karen_engine.services.enhanced_huggingface_service.HfApi') as mock_api:
            api_instance = Mock()
            mock_api.return_value = api_instance
            yield api_instance
    
    @pytest.fixture
    def service(self, mock_hf_api):
        """Create service instance with mocked dependencies."""
        with patch('ai_karen_engine.services.enhanced_huggingface_service.HF_AVAILABLE', True):
            service = EnhancedHuggingFaceService()
            return service
    
    @pytest.fixture
    def sample_model_data(self):
        """Sample model data for testing."""
        return Mock(
            id="microsoft/DialoGPT-medium",
            description="Medium-sized conversational AI model",
            tags=["pytorch", "transformers", "conversational"],
            downloads=50000,
            likes=1000,
            created_at="2023-01-01T00:00:00Z",
            last_modified="2023-06-01T00:00:00Z",
            library_name="transformers",
            pipeline_tag="text-generation",
            license="mit",
            siblings=[
                Mock(rfilename="config.json", size=1024),
                Mock(rfilename="pytorch_model.bin", size=500000000),
                Mock(rfilename="tokenizer.json", size=2048)
            ]
        )
    
    def test_search_trainable_models_basic(self, service, mock_hf_api, sample_model_data):
        """Test basic trainable model search."""
        # Setup mock
        mock_hf_api.list_models.return_value = [sample_model_data]
        
        # Test search
        filters = TrainingFilters(supports_fine_tuning=True)
        models = service.search_trainable_models(
            query="conversational",
            filters=filters,
            limit=10
        )
        
        # Verify results
        assert len(models) == 1
        assert isinstance(models[0], TrainableModel)
        assert models[0].id == "microsoft/DialoGPT-medium"
        assert models[0].supports_fine_tuning is True
        
        # Verify API was called correctly
        mock_hf_api.list_models.assert_called_once()
        call_args = mock_hf_api.list_models.call_args[1]
        assert call_args["search"] == "conversational"
        assert call_args["task"] == "text-generation"
        assert call_args["library"] == "transformers"
    
    def test_search_trainable_models_with_filters(self, service, mock_hf_api, sample_model_data):
        """Test trainable model search with advanced filters."""
        # Setup mock
        mock_hf_api.list_models.return_value = [sample_model_data]
        
        # Test search with filters
        filters = TrainingFilters(
            supports_fine_tuning=True,
            supports_lora=True,
            max_parameters="7B",
            memory_requirements=16
        )
        
        models = service.search_trainable_models(
            query="llama",
            filters=filters,
            limit=20
        )
        
        # Verify filtering logic was applied
        assert len(models) <= 20
        mock_hf_api.list_models.assert_called_once()
    
    def test_trainable_model_inference(self, service):
        """Test training capability inference from model metadata."""
        # Create a model with training-friendly characteristics
        model = TrainableModel(
            id="meta-llama/Llama-2-7b-hf",
            name="Llama-2-7b-hf",
            tags=["pytorch", "transformers", "llama"],
            family="llama",
            parameters="7B",
            downloads=100000,
            likes=5000
        )
        
        # Verify training capabilities were inferred
        assert model.supports_fine_tuning is True
        assert model.supports_lora is True
        assert model.supports_full_training is True
        assert model.training_complexity == "medium"
        assert "transformers" in model.training_frameworks
    
    def test_check_training_compatibility(self, service):
        """Test model compatibility checking."""
        # Mock model info
        mock_model_info = Mock()
        mock_model_info.config = {
            "architectures": ["LlamaForCausalLM"],
            "model_type": "llama"
        }
        mock_model_info.files = [
            {"rfilename": "config.json", "size": 1024},
            {"rfilename": "model.safetensors", "size": 13000000000}  # 13GB
        ]
        mock_model_info.license = "apache-2.0"
        
        with patch.object(service, 'get_model_info', return_value=mock_model_info):
            report = service.check_training_compatibility("meta-llama/Llama-2-7b-hf")
        
        # Verify compatibility report
        assert isinstance(report, CompatibilityReport)
        assert report.is_compatible is True
        assert report.compatibility_score > 0.5
        assert "fine_tuning" in report.supported_operations
        assert "lora" in report.supported_operations
        assert report.framework_compatibility.get("transformers") is True
        assert report.framework_compatibility.get("peft") is True
    
    def test_compatibility_caching(self, service):
        """Test that compatibility reports are cached."""
        model_id = "test/model"
        
        # Mock model info
        mock_model_info = Mock()
        mock_model_info.config = {"architectures": ["LlamaForCausalLM"]}
        mock_model_info.files = [{"rfilename": "config.json", "size": 1024}]
        mock_model_info.license = "mit"
        
        with patch.object(service, 'get_model_info', return_value=mock_model_info) as mock_get_info:
            # First call
            report1 = service.check_training_compatibility(model_id)
            
            # Second call should use cache
            report2 = service.check_training_compatibility(model_id)
            
            # Verify caching
            assert report1 is report2
            mock_get_info.assert_called_once()  # Only called once due to caching
    
    def test_enhanced_download_job_creation(self, service):
        """Test enhanced download job creation."""
        model_id = "test/model"
        
        # Mock dependencies
        mock_compatibility = CompatibilityReport(
            is_compatible=True,
            compatibility_score=0.8,
            supported_operations=["fine_tuning", "lora"],
            hardware_requirements={"min_gpu_memory": 16},
            framework_compatibility={"transformers": True, "peft": True},
            warnings=[],
            recommendations=["Use SafeTensors format for optimal training"]
        )
        
        mock_model_info = Mock()
        mock_model_info.files = [
            {"rfilename": "config.json", "size": 1024},
            {"rfilename": "model.safetensors", "size": 13000000000}
        ]
        
        with patch.object(service, 'check_training_compatibility', return_value=mock_compatibility), \
             patch.object(service, 'get_model_info', return_value=mock_model_info), \
             patch.object(service, '_start_enhanced_download'):
            
            job = service.download_with_training_setup(
                model_id=model_id,
                setup_training=True,
                training_config={"auto_optimize": True}
            )
        
        # Verify job creation
        assert isinstance(job, EnhancedDownloadJob)
        assert job.model_id == model_id
        assert job.compatibility_report is mock_compatibility
        assert len(job.selected_artifacts) > 0
        assert "setup_training_environment" in job.post_download_actions
        assert "register_with_model_store" in job.post_download_actions
    
    def test_artifact_selection_safetensors_preference(self, service):
        """Test that SafeTensors files are preferred for training."""
        files = [
            {"rfilename": "pytorch_model.bin", "size": 13000000000},
            {"rfilename": "model.safetensors", "size": 13000000000},
            {"rfilename": "config.json", "size": 1024},
            {"rfilename": "tokenizer.json", "size": 2048}
        ]
        
        device_caps = Mock()
        selected = service._select_training_artifacts(files, device_caps)
        
        # Verify SafeTensors is selected
        assert "model.safetensors" in selected
        assert "config.json" in selected
        assert "tokenizer.json" in selected
        assert "pytorch_model.bin" not in selected
    
    def test_hardware_requirements_estimation(self, service):
        """Test hardware requirements estimation."""
        # Small model (< 2GB)
        small_model_info = Mock()
        small_model_info.files = [{"rfilename": "model.bin", "size": 1000000000}]  # 1GB
        
        small_reqs = service._estimate_hardware_requirements(small_model_info)
        assert small_reqs["min_gpu_memory"] == 4
        assert small_reqs["gpu_required"] is False
        
        # Large model (> 15GB)
        large_model_info = Mock()
        large_model_info.files = [{"rfilename": "model.bin", "size": 20000000000}]  # 20GB
        
        large_reqs = service._estimate_hardware_requirements(large_model_info)
        assert large_reqs["min_gpu_memory"] == 40
        assert large_reqs["gpu_required"] is True
        assert large_reqs["multi_gpu_beneficial"] is True
    
    def test_conversion_detection(self, service):
        """Test detection of models that need format conversion."""
        # Model with only .bin files (needs conversion)
        bin_only_files = [
            {"rfilename": "pytorch_model.bin", "size": 13000000000},
            {"rfilename": "config.json", "size": 1024}
        ]
        assert service._needs_conversion(bin_only_files) is True
        
        # Model with SafeTensors (no conversion needed)
        safetensors_files = [
            {"rfilename": "model.safetensors", "size": 13000000000},
            {"rfilename": "config.json", "size": 1024}
        ]
        assert service._needs_conversion(safetensors_files) is False
        
        # Model with both formats (no conversion needed)
        mixed_files = [
            {"rfilename": "pytorch_model.bin", "size": 13000000000},
            {"rfilename": "model.safetensors", "size": 13000000000},
            {"rfilename": "config.json", "size": 1024}
        ]
        assert service._needs_conversion(mixed_files) is False
    
    def test_post_download_actions_planning(self, service):
        """Test planning of post-download actions."""
        compatibility_report = CompatibilityReport(
            is_compatible=True,
            compatibility_score=0.9,
            supported_operations=["fine_tuning", "lora", "full_training"],
            hardware_requirements={},
            framework_compatibility={"transformers": True, "peft": True},
            warnings=[],
            recommendations=[]
        )
        
        actions = service._plan_post_download_actions(
            setup_training=True,
            training_config={"auto_optimize": True},
            compatibility_report=compatibility_report
        )
        
        # Verify planned actions
        assert "setup_training_environment" in actions
        assert "prepare_fine_tuning" in actions
        assert "setup_lora_config" in actions
        assert "optimize_for_hardware" in actions
        assert "register_with_model_store" in actions
    
    def test_job_management(self, service):
        """Test enhanced download job management."""
        # Create a mock job
        job = EnhancedDownloadJob(
            id="test_job",
            model_id="test/model",
            status="downloading",
            progress=0.5
        )
        
        # Store job
        service._enhanced_jobs["test_job"] = job
        
        # Test retrieval
        retrieved_job = service.get_enhanced_download_job("test_job")
        assert retrieved_job is job
        
        # Test listing
        jobs = service.list_enhanced_download_jobs()
        assert len(jobs) == 1
        assert jobs[0] is job
        
        # Test filtering by status
        downloading_jobs = service.list_enhanced_download_jobs(status="downloading")
        assert len(downloading_jobs) == 1
        
        completed_jobs = service.list_enhanced_download_jobs(status="completed")
        assert len(completed_jobs) == 0
    
    def test_service_factory(self):
        """Test service factory function."""
        # First call creates instance
        service1 = get_enhanced_huggingface_service()
        assert isinstance(service1, EnhancedHuggingFaceService)
        
        # Second call returns same instance
        service2 = get_enhanced_huggingface_service()
        assert service1 is service2


class TestTrainableModel:
    """Test suite for TrainableModel class."""
    
    def test_training_capability_inference_llama(self):
        """Test training capability inference for Llama models."""
        model = TrainableModel(
            id="meta-llama/Llama-2-7b-hf",
            name="Llama-2-7b-hf",
            tags=["pytorch", "transformers"],
            family="llama",
            parameters="7B",
            downloads=100000,
            likes=5000
        )
        
        assert model.supports_fine_tuning is True
        assert model.supports_lora is True
        assert model.supports_full_training is True
        assert model.training_complexity == "medium"
        assert model.memory_requirements == 16
    
    def test_training_capability_inference_small_model(self):
        """Test training capability inference for small models."""
        model = TrainableModel(
            id="microsoft/DialoGPT-small",
            name="DialoGPT-small",
            tags=["pytorch", "transformers"],
            family="gpt",
            parameters="117M",
            downloads=50000,
            likes=1000
        )
        
        assert model.supports_fine_tuning is True
        assert model.supports_lora is True
        assert model.supports_full_training is True
        assert model.training_complexity == "easy"
        assert model.memory_requirements == 4
    
    def test_training_capability_inference_large_model(self):
        """Test training capability inference for large models."""
        model = TrainableModel(
            id="meta-llama/Llama-2-70b-hf",
            name="Llama-2-70b-hf",
            tags=["pytorch", "transformers"],
            family="llama",
            parameters="70B",
            downloads=25000,
            likes=2000
        )
        
        assert model.supports_fine_tuning is True
        assert model.supports_lora is True
        assert model.supports_full_training is False  # Too large for full training
        assert model.training_complexity == "hard"
        assert model.memory_requirements == 40
    
    def test_parameter_count_extraction(self):
        """Test parameter count extraction from strings."""
        model = TrainableModel(
            id="test/model",
            name="test",
            tags=[],
            downloads=0,
            likes=0
        )
        
        # Test various parameter formats
        assert model._extract_parameter_count("7B") == 7.0
        assert model._extract_parameter_count("1.3B") == 1.3
        assert model._extract_parameter_count("117M") == 0.117
        assert model._extract_parameter_count("invalid") is None


class TestCompatibilityReport:
    """Test suite for CompatibilityReport class."""
    
    def test_compatibility_report_creation(self):
        """Test compatibility report creation."""
        report = CompatibilityReport(
            is_compatible=True,
            compatibility_score=0.85,
            supported_operations=["fine_tuning", "lora"],
            hardware_requirements={"min_gpu_memory": 16},
            framework_compatibility={"transformers": True, "peft": True},
            warnings=["Model is large"],
            recommendations=["Use gradient checkpointing"]
        )
        
        assert report.is_compatible is True
        assert report.compatibility_score == 0.85
        assert len(report.supported_operations) == 2
        assert len(report.warnings) == 1
        assert len(report.recommendations) == 1


if __name__ == "__main__":
    pytest.main([__file__])