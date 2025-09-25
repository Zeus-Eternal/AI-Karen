"""
Integration tests for Enhanced HuggingFace Model Discovery Service

Simple integration tests to verify the enhanced HuggingFace service
works correctly with the existing infrastructure.
"""

import pytest
from unittest.mock import Mock, patch

from ai_karen_engine.services.enhanced_huggingface_service import (
    EnhancedHuggingFaceService,
    TrainableModel,
    get_enhanced_huggingface_service
)


class TestEnhancedHuggingFaceIntegration:
    """Integration tests for Enhanced HuggingFace Service."""
    
    def test_service_creation(self):
        """Test that the service can be created successfully."""
        with patch('ai_karen_engine.services.enhanced_huggingface_service.HF_AVAILABLE', False):
            service = EnhancedHuggingFaceService()
            assert service is not None
            assert service.api is None  # Should be None when HF not available
    
    def test_trainable_model_basic_functionality(self):
        """Test basic TrainableModel functionality."""
        model = TrainableModel(
            id="test/model",
            name="Test Model",
            tags=["pytorch", "transformers"],
            downloads=1000,
            likes=50,
            family="llama",
            parameters="7B"
        )
        
        # Verify basic properties
        assert model.id == "test/model"
        assert model.name == "Test Model"
        assert model.family == "llama"
        assert model.parameters == "7B"
        
        # Verify training capabilities were inferred
        assert model.supports_fine_tuning is True
        assert model.supports_lora is True
        assert model.supports_full_training is True
        assert model.training_complexity == "medium"
    
    def test_parameter_extraction(self):
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
    
    def test_service_factory_singleton(self):
        """Test that service factory returns singleton."""
        service1 = get_enhanced_huggingface_service()
        service2 = get_enhanced_huggingface_service()
        assert service1 is service2
    
    def test_compatibility_report_basic(self):
        """Test basic compatibility report functionality."""
        with patch('ai_karen_engine.services.enhanced_huggingface_service.HF_AVAILABLE', False):
            service = EnhancedHuggingFaceService()
            
            # Test with non-existent model (should return incompatible)
            report = service.check_training_compatibility("non-existent/model")
            
            assert report.is_compatible is False
            assert report.compatibility_score == 0.0
            assert len(report.warnings) > 0
    
    def test_enhanced_download_job_creation_basic(self):
        """Test basic enhanced download job creation."""
        with patch('ai_karen_engine.services.enhanced_huggingface_service.HF_AVAILABLE', False):
            service = EnhancedHuggingFaceService()
            
            # Mock the required methods
            with patch.object(service, 'check_training_compatibility') as mock_compat, \
                 patch.object(service, 'get_model_info') as mock_info, \
                 patch.object(service, '_start_enhanced_download') as mock_start:
                
                # Setup mocks
                mock_compat.return_value = Mock(
                    is_compatible=True,
                    compatibility_score=0.8,
                    supported_operations=["fine_tuning"]
                )
                mock_info.return_value = Mock(files=[])
                
                # Test job creation
                job = service.download_with_training_setup("test/model")
                
                assert job is not None
                assert job.model_id == "test/model"
                assert job.compatibility_report is not None
    
    def test_artifact_selection_logic(self):
        """Test artifact selection logic."""
        with patch('ai_karen_engine.services.enhanced_huggingface_service.HF_AVAILABLE', False):
            service = EnhancedHuggingFaceService()
            
            # Test SafeTensors preference
            files = [
                {"rfilename": "pytorch_model.bin", "size": 1000000},
                {"rfilename": "model.safetensors", "size": 1000000},
                {"rfilename": "config.json", "size": 1024}
            ]
            
            selected = service._select_training_artifacts(files, Mock())
            
            assert "model.safetensors" in selected
            assert "config.json" in selected
            assert "pytorch_model.bin" not in selected
    
    def test_hardware_requirements_estimation(self):
        """Test hardware requirements estimation."""
        with patch('ai_karen_engine.services.enhanced_huggingface_service.HF_AVAILABLE', False):
            service = EnhancedHuggingFaceService()
            
            # Test small model
            small_model = Mock(files=[{"size": 1000000000}])  # 1GB
            reqs = service._estimate_hardware_requirements(small_model)
            assert reqs["gpu_required"] is False
            
            # Test large model
            large_model = Mock(files=[{"size": 20000000000}])  # 20GB
            reqs = service._estimate_hardware_requirements(large_model)
            assert reqs["gpu_required"] is True
            assert reqs["multi_gpu_beneficial"] is True
    
    def test_conversion_detection(self):
        """Test format conversion detection."""
        with patch('ai_karen_engine.services.enhanced_huggingface_service.HF_AVAILABLE', False):
            service = EnhancedHuggingFaceService()
            
            # Test conversion needed (only .bin files)
            bin_files = [{"rfilename": "pytorch_model.bin", "size": 1000000}]
            assert service._needs_conversion(bin_files) is True
            
            # Test no conversion needed (has SafeTensors)
            safetensors_files = [{"rfilename": "model.safetensors", "size": 1000000}]
            assert service._needs_conversion(safetensors_files) is False


if __name__ == "__main__":
    pytest.main([__file__])