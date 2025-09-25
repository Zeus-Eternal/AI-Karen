"""
Test Transformer Model Configuration System

Tests the enhanced transformer model configuration system including:
- Precision settings with hardware validation
- Dynamic batch size recommendations
- Multi-GPU device allocation and load balancing
- Optimization flags interface
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

from src.ai_karen_engine.services.system_model_manager import (
    SystemModelManager,
    TransformerConfig
)


class TestTransformerConfiguration:
    """Test transformer model configuration functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SystemModelManager()
    
    def test_transformer_config_dataclass(self):
        """Test TransformerConfig dataclass with all fields."""
        config = TransformerConfig(
            precision="fp16",
            torch_dtype="auto",
            load_in_8bit=False,
            load_in_4bit=False,
            device="cuda",
            device_map="auto",
            low_cpu_mem_usage=True,
            batch_size=8,
            max_length=512,
            dynamic_batch_size=True,
            use_cache=True,
            attention_implementation="flash_attention_2",
            use_flash_attention=True,
            gradient_checkpointing=False,
            mixed_precision=True,
            compile_model=False,
            multi_gpu_strategy="auto",
            gpu_memory_fraction=0.9,
            enable_cpu_offload=False,
            bnb_4bit_compute_dtype="float16",
            bnb_4bit_use_double_quant=False,
            bnb_4bit_quant_type="nf4",
            use_bettertransformer=False,
            optimize_for_inference=True,
            enable_xformers=False
        )
        
        # Test serialization
        config_dict = asdict(config)
        assert config_dict["precision"] == "fp16"
        assert config_dict["batch_size"] == 8
        assert config_dict["use_flash_attention"] is True
        
        # Test deserialization
        new_config = TransformerConfig(**config_dict)
        assert new_config.precision == "fp16"
        assert new_config.batch_size == 8
    
    @patch('torch.cuda.is_available')
    @patch('torch.cuda.device_count')
    @patch('torch.cuda.get_device_properties')
    @patch('torch.cuda.is_bf16_supported')
    def test_transformer_config_validation_gpu_available(
        self, mock_bf16, mock_props, mock_device_count, mock_cuda_available
    ):
        """Test transformer configuration validation with GPU available."""
        # Mock GPU availability
        mock_cuda_available.return_value = True
        mock_device_count.return_value = 2
        mock_bf16.return_value = True
        
        # Mock GPU properties
        mock_gpu_props = Mock()
        mock_gpu_props.total_memory = 8 * 1024**3  # 8GB
        mock_props.return_value = mock_gpu_props
        
        config = TransformerConfig(
            precision="bf16",
            device="cuda:0",
            load_in_4bit=False,
            load_in_8bit=False,
            batch_size=4
        )
        
        result = self.manager._validate_transformer_config(config)
        
        assert result["valid"] is True
        assert "warnings" in result
    
    @patch('torch.cuda.is_available')
    def test_transformer_config_validation_no_gpu(self, mock_cuda_available):
        """Test transformer configuration validation without GPU."""
        mock_cuda_available.return_value = False
        
        config = TransformerConfig(
            precision="bf16",
            device="cpu"
        )
        
        result = self.manager._validate_transformer_config(config)
        
        assert result["valid"] is False
        assert "bf16 precision not supported on CPU" in result["error"]
    
    @patch('torch.cuda.is_available')
    def test_transformer_config_validation_quantization_conflicts(self, mock_cuda_available):
        """Test validation of conflicting quantization settings."""
        mock_cuda_available.return_value = True
        
        config = TransformerConfig(
            load_in_4bit=True,
            load_in_8bit=True,
            device="cuda"
        )
        
        result = self.manager._validate_transformer_config(config)
        
        assert result["valid"] is False
        assert "Cannot use both 4-bit and 8-bit quantization" in result["error"]
    
    @patch('torch.cuda.is_available')
    def test_transformer_config_validation_device_not_available(self, mock_cuda_available):
        """Test validation when requested GPU device is not available."""
        mock_cuda_available.return_value = False
        
        config = TransformerConfig(
            device="cuda:0"
        )
        
        result = self.manager._validate_transformer_config(config)
        
        assert result["valid"] is False
        assert "CUDA device requested but not available" in result["error"]
    
    @patch('psutil.virtual_memory')
    @patch('torch.cuda.is_available')
    @patch('torch.cuda.device_count')
    @patch('torch.cuda.get_device_properties')
    @patch('torch.cuda.is_bf16_supported')
    def test_hardware_recommendations_transformer(
        self, mock_bf16, mock_props, mock_device_count, mock_cuda_available, mock_memory
    ):
        """Test hardware recommendations for transformer models."""
        # Mock system resources
        mock_memory.return_value.total = 16 * 1024**3  # 16GB RAM
        mock_cuda_available.return_value = True
        mock_device_count.return_value = 1
        mock_bf16.return_value = True
        
        # Mock GPU properties
        mock_gpu_props = Mock()
        mock_gpu_props.total_memory = 8 * 1024**3  # 8GB GPU memory
        mock_props.return_value = mock_gpu_props
        
        recommendations = self.manager.get_hardware_recommendations("distilbert-base-uncased")
        
        assert "system_info" in recommendations
        assert recommendations["system_info"]["memory_gb"] == 16.0
        assert recommendations["system_info"]["gpu_available"] is True
        assert recommendations["system_info"]["gpu_memory_gb"] == 8.0
        
        # Check transformer-specific recommendations
        assert "recommended_device" in recommendations
        assert "recommended_precision" in recommendations
        assert "recommended_batch_size" in recommendations
        assert "dynamic_batch_sizes" in recommendations
    
    def test_dynamic_batch_size_calculation(self):
        """Test dynamic batch size calculation based on memory."""
        # Test GPU scenarios
        assert self.manager._calculate_optimal_batch_size(32, True, 24) == 32  # High-end GPU
        assert self.manager._calculate_optimal_batch_size(16, True, 16) == 16  # Mid-range GPU
        assert self.manager._calculate_optimal_batch_size(8, True, 8) == 8    # Entry GPU
        assert self.manager._calculate_optimal_batch_size(4, True, 4) == 4    # Low-end GPU
        assert self.manager._calculate_optimal_batch_size(2, True, 2) == 1    # Very low GPU
        
        # Test CPU scenarios
        assert self.manager._calculate_optimal_batch_size(32, False, 0) == 8  # High RAM
        assert self.manager._calculate_optimal_batch_size(16, False, 0) == 4  # Mid RAM
        assert self.manager._calculate_optimal_batch_size(8, False, 0) == 2   # Low RAM
        assert self.manager._calculate_optimal_batch_size(4, False, 0) == 1   # Very low RAM
    
    def test_dynamic_batch_sizes_scenarios(self):
        """Test dynamic batch sizes for different scenarios."""
        batch_sizes = self.manager._get_dynamic_batch_sizes(16, True, 8)
        
        assert "training" in batch_sizes
        assert "inference" in batch_sizes
        assert "evaluation" in batch_sizes
        assert "fine_tuning" in batch_sizes
        assert "memory_constrained" in batch_sizes
        assert "performance_optimized" in batch_sizes
        
        # Training should use less memory than inference
        assert batch_sizes["training"] <= batch_sizes["inference"]
        
        # Fine-tuning should use least memory
        assert batch_sizes["fine_tuning"] <= batch_sizes["training"]
        
        # Memory constrained should be 1
        assert batch_sizes["memory_constrained"] == 1
    
    @patch('torch.cuda.is_available')
    @patch('torch.cuda.device_count')
    @patch('torch.cuda.get_device_properties')
    def test_multi_gpu_configuration(self, mock_props, mock_device_count, mock_cuda_available):
        """Test multi-GPU configuration recommendations."""
        mock_cuda_available.return_value = True
        mock_device_count.return_value = 2
        
        # Mock GPU properties for 2 GPUs
        gpu_props = [
            Mock(name="GPU 0", total_memory=8*1024**3, major=8, minor=0),
            Mock(name="GPU 1", total_memory=8*1024**3, major=8, minor=0)
        ]
        mock_props.side_effect = gpu_props
        
        config = self.manager.get_multi_gpu_configuration("distilbert-base-uncased")
        
        assert config["gpu_count"] == 2
        assert len(config["gpu_info"]) == 2
        assert config["total_memory_gb"] == 16.0
        assert "recommended_strategy" in config
        assert "device_map" in config
        assert "load_balancing" in config
    
    @patch('torch.cuda.is_available')
    def test_multi_gpu_configuration_no_gpu(self, mock_cuda_available):
        """Test multi-GPU configuration when no GPU is available."""
        mock_cuda_available.return_value = False
        
        config = self.manager.get_multi_gpu_configuration("distilbert-base-uncased")
        
        assert "error" in config
        assert "CUDA not available" in config["error"]
    
    @patch('torch.cuda.is_available')
    @patch('torch.cuda.device_count')
    def test_multi_gpu_configuration_single_gpu(self, mock_device_count, mock_cuda_available):
        """Test multi-GPU configuration with single GPU."""
        mock_cuda_available.return_value = True
        mock_device_count.return_value = 1
        
        config = self.manager.get_multi_gpu_configuration("distilbert-base-uncased")
        
        assert "error" in config
        assert "Multi-GPU requires at least 2 GPUs" in config["error"]
    
    def test_device_map_generation(self):
        """Test device map generation for different strategies."""
        gpu_info = [
            {"device_id": 0, "memory_gb": 8.0},
            {"device_id": 1, "memory_gb": 8.0}
        ]
        
        # Test sequential strategy
        device_map = self.manager._generate_device_map(gpu_info, "sequential")
        assert device_map["strategy"] == "sequential"
        assert "device_assignment" in device_map
        
        # Test model parallel strategy
        device_map = self.manager._generate_device_map(gpu_info, "model_parallel")
        assert device_map["strategy"] == "model_parallel"
        
        # Test data parallel strategy
        device_map = self.manager._generate_device_map(gpu_info, "data_parallel")
        assert device_map["strategy"] == "data_parallel"
    
    def test_load_balancing_calculation(self):
        """Test load balancing calculation for multi-GPU setup."""
        gpu_info = [
            {"device_id": 0, "memory_gb": 8.0},
            {"device_id": 1, "memory_gb": 4.0}
        ]
        
        balancing = self.manager._calculate_load_balancing(gpu_info)
        
        assert "cuda:0" in balancing
        assert "cuda:1" in balancing
        
        # GPU 0 should have higher fraction due to more memory
        assert balancing["cuda:0"]["memory_fraction"] > balancing["cuda:1"]["memory_fraction"]
        assert balancing["cuda:0"]["priority"] == "high"
    
    def test_transformer_config_update_and_save(self):
        """Test updating and saving transformer configuration."""
        model_id = "distilbert-base-uncased"
        
        new_config = {
            "precision": "bf16",
            "batch_size": 16,
            "device": "cuda",
            "use_flash_attention": True,
            "mixed_precision": True
        }
        
        # Mock validation to pass
        with patch.object(self.manager, '_validate_transformer_config') as mock_validate:
            mock_validate.return_value = {"valid": True}
            
            success = self.manager.update_model_configuration(model_id, new_config)
            assert success is True
            
            # Verify configuration was updated
            saved_config = self.manager.get_model_configuration(model_id)
            assert saved_config["precision"] == "bf16"
            assert saved_config["batch_size"] == 16
            assert saved_config["use_flash_attention"] is True
    
    def test_transformer_config_validation_warnings(self):
        """Test configuration validation with warnings."""
        with patch('torch.cuda.is_available') as mock_cuda:
            mock_cuda.return_value = True
            
            config = TransformerConfig(
                precision="int4",
                load_in_4bit=False,  # This should generate a warning
                device="cuda"
            )
            
            result = self.manager._validate_transformer_config(config)
            
            assert result["valid"] is True
            assert "warnings" in result
            assert any("int4 precision specified but load_in_4bit is False" in w 
                     for w in result["warnings"])


class TestTransformerConfigurationAPI:
    """Test API endpoints for transformer configuration."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from src.ai_karen_engine.api_routes.model_management_routes import router
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    def test_get_system_models_endpoint(self, client):
        """Test getting system models via API."""
        with patch('src.ai_karen_engine.services.system_model_manager.get_system_model_manager') as mock_manager:
            mock_manager.return_value.get_system_models.return_value = [
                {
                    "id": "distilbert-base-uncased",
                    "name": "DistilBERT Base Uncased",
                    "family": "bert",
                    "format": "safetensors",
                    "configuration": {
                        "precision": "fp16",
                        "batch_size": 1,
                        "device": "auto"
                    }
                }
            ]
            
            response = client.get("/api/models/system")
            assert response.status_code == 200
            
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == "distilbert-base-uncased"
    
    def test_get_hardware_recommendations_endpoint(self, client):
        """Test getting hardware recommendations via API."""
        with patch('src.ai_karen_engine.services.system_model_manager.get_system_model_manager') as mock_manager:
            mock_manager.return_value.get_hardware_recommendations.return_value = {
                "system_info": {
                    "memory_gb": 16.0,
                    "gpu_available": True,
                    "gpu_memory_gb": 8.0
                },
                "recommended_precision": "fp16",
                "recommended_batch_size": 8
            }
            
            response = client.get("/api/models/system/distilbert-base-uncased/hardware-recommendations")
            assert response.status_code == 200
            
            data = response.json()
            assert data["system_info"]["memory_gb"] == 16.0
            assert data["recommended_precision"] == "fp16"
    
    def test_update_configuration_endpoint(self, client):
        """Test updating model configuration via API."""
        with patch('src.ai_karen_engine.services.system_model_manager.get_system_model_manager') as mock_manager:
            mock_manager.return_value.update_model_configuration.return_value = True
            
            config_data = {
                "configuration": {
                    "precision": "bf16",
                    "batch_size": 16,
                    "use_flash_attention": True
                }
            }
            
            response = client.put(
                "/api/models/system/distilbert-base-uncased/configuration",
                json=config_data
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["message"] == "Configuration updated successfully"
    
    def test_validate_configuration_endpoint(self, client):
        """Test configuration validation via API."""
        with patch('src.ai_karen_engine.services.system_model_manager.get_system_model_manager') as mock_manager:
            # Mock the system models and config class
            mock_manager.return_value.system_models = {
                "distilbert-base-uncased": {
                    "config_class": TransformerConfig
                }
            }
            mock_manager.return_value._validate_configuration.return_value = {
                "valid": True,
                "warnings": []
            }
            
            config_data = {
                "configuration": {
                    "precision": "fp16",
                    "batch_size": 8
                }
            }
            
            response = client.post(
                "/api/models/system/validate-configuration?model_id=distilbert-base-uncased",
                json=config_data
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["valid"] is True
    
    def test_multi_gpu_config_endpoint(self, client):
        """Test multi-GPU configuration endpoint."""
        with patch('src.ai_karen_engine.services.system_model_manager.get_system_model_manager') as mock_manager:
            mock_manager.return_value.get_multi_gpu_configuration.return_value = {
                "gpu_count": 2,
                "total_memory_gb": 16.0,
                "recommended_strategy": "data_parallel"
            }
            
            response = client.get("/api/models/system/distilbert-base-uncased/multi-gpu-config")
            assert response.status_code == 200
            
            data = response.json()
            assert data["gpu_count"] == 2
            assert data["recommended_strategy"] == "data_parallel"


if __name__ == "__main__":
    pytest.main([__file__])