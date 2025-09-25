"""
Basic tests for Enhanced HuggingFace Model Discovery Service

Simple tests that verify the core functionality without external dependencies.
"""

import pytest

from ai_karen_engine.services.enhanced_huggingface_service import (
    TrainableModel,
    CompatibilityReport,
    EnhancedDownloadJob,
    TrainingFilters,
    get_enhanced_huggingface_service
)


class TestTrainableModelBasic:
    """Basic tests for TrainableModel class."""
    
    def test_trainable_model_creation(self):
        """Test basic TrainableModel creation."""
        model = TrainableModel(
            id="test/model",
            name="Test Model",
            tags=["pytorch", "transformers"],
            downloads=1000,
            likes=50
        )
        
        assert model.id == "test/model"
        assert model.name == "Test Model"
        assert model.downloads == 1000
        assert model.likes == 50
    
    def test_parameter_extraction_basic(self):
        """Test parameter count extraction."""
        model = TrainableModel(
            id="test/model",
            name="Test Model",
            tags=[],
            downloads=0,
            likes=0
        )
        
        # Test parameter extraction
        assert model._extract_parameter_count("7B") == 7.0
        assert model._extract_parameter_count("1.3B") == 1.3
        assert model._extract_parameter_count("117M") == 0.117
        assert model._extract_parameter_count("invalid") is None
        assert model._extract_parameter_count("") is None
    
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
    
    def test_training_capability_inference_unknown_family(self):
        """Test training capability inference for unknown model family."""
        model = TrainableModel(
            id="unknown/model",
            name="Unknown Model",
            tags=["pytorch"],
            family="unknown",
            parameters="1B",
            downloads=1000,
            likes=10
        )
        
        # Unknown family should not support training by default
        assert model.supports_fine_tuning is False
        assert model.supports_lora is False
        assert model.supports_full_training is False
        # Training complexity is inferred from parameter count, not family
        assert model.training_complexity == "easy"  # 1B model is considered easy


class TestCompatibilityReportBasic:
    """Basic tests for CompatibilityReport class."""
    
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
        assert "fine_tuning" in report.supported_operations
        assert "lora" in report.supported_operations
        assert len(report.warnings) == 1
        assert len(report.recommendations) == 1
        assert report.hardware_requirements["min_gpu_memory"] == 16
        assert report.framework_compatibility["transformers"] is True


class TestTrainingFiltersBasic:
    """Basic tests for TrainingFilters class."""
    
    def test_training_filters_creation(self):
        """Test training filters creation."""
        filters = TrainingFilters(
            supports_fine_tuning=True,
            supports_lora=True,
            min_parameters="1B",
            max_parameters="13B",
            memory_requirements=16
        )
        
        assert filters.supports_fine_tuning is True
        assert filters.supports_lora is True
        assert filters.min_parameters == "1B"
        assert filters.max_parameters == "13B"
        assert filters.memory_requirements == 16
    
    def test_training_filters_defaults(self):
        """Test training filters with default values."""
        filters = TrainingFilters()
        
        assert filters.supports_fine_tuning is True
        assert filters.supports_lora is False
        assert filters.supports_full_training is False
        assert filters.min_parameters is None
        assert filters.max_parameters is None
        assert len(filters.training_frameworks) == 0


class TestEnhancedDownloadJobBasic:
    """Basic tests for EnhancedDownloadJob class."""
    
    def test_enhanced_download_job_creation(self):
        """Test enhanced download job creation."""
        job = EnhancedDownloadJob(
            id="test_job",
            model_id="test/model",
            status="downloading",
            progress=0.5,
            selected_artifacts=["config.json", "model.safetensors"],
            conversion_needed=False,
            post_download_actions=["register_with_model_store"]
        )
        
        assert job.id == "test_job"
        assert job.model_id == "test/model"
        assert job.status == "downloading"
        assert job.progress == 0.5
        assert len(job.selected_artifacts) == 2
        assert "config.json" in job.selected_artifacts
        assert job.conversion_needed is False
        assert len(job.post_download_actions) == 1


class TestServiceFactoryBasic:
    """Basic tests for service factory."""
    
    def test_service_factory_singleton(self):
        """Test that service factory returns singleton."""
        service1 = get_enhanced_huggingface_service()
        service2 = get_enhanced_huggingface_service()
        assert service1 is service2
    
    def test_service_factory_returns_correct_type(self):
        """Test that service factory returns correct type."""
        from ai_karen_engine.services.enhanced_huggingface_service import EnhancedHuggingFaceService
        
        service = get_enhanced_huggingface_service()
        assert isinstance(service, EnhancedHuggingFaceService)


if __name__ == "__main__":
    pytest.main([__file__])