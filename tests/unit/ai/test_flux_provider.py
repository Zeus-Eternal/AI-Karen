"""
Unit tests for FluxProvider
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import base64
import io
from PIL import Image

from ai_karen_engine.integrations.providers.flux_provider import FluxProvider
from ai_karen_engine.integrations.llm_utils import GenerationFailed


class TestFluxProvider:
    """Test FluxProvider functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the diffusers import to avoid dependency issues in tests
        self.mock_diffusers = Mock()
        self.mock_torch = Mock()
        
        # Create mock pipeline
        self.mock_pipeline = Mock()
        
        # Mock image result
        self.mock_image = Mock(spec=Image.Image)
        self.mock_image.save = Mock()
        
        self.mock_pipeline.return_value.images = [self.mock_image]
        
    @patch('ai_karen_engine.integrations.providers.flux_provider.FluxPipeline')
    @patch('ai_karen_engine.integrations.providers.flux_provider.torch')
    def test_provider_initialization_dev_variant(self, mock_torch, mock_flux_pipeline):
        """Test provider initialization with dev variant."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.bfloat16 = "bfloat16"
        mock_torch.float16 = "float16"
        mock_torch.float32 = "float32"
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        mock_flux_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = FluxProvider(
            model="test-flux-model",
            variant="dev",
            device="cuda"
        )
        
        assert provider.model == "test-flux-model"
        assert provider.variant == "dev"
        assert provider.device == "cuda"
        assert provider.metadata["type"] == "image"
        assert provider.metadata["subtype"] == "flux"
        assert provider.metadata["variant"] == "dev"
        assert "text2img" in provider.metadata["capabilities"]
        assert provider.metadata["steps_range"] == [20, 50]
        assert provider.metadata["guidance_scale_range"] == [3.0, 10.0]
        
        mock_flux_pipeline.from_pretrained.assert_called_once()
    
    @patch('ai_karen_engine.integrations.providers.flux_provider.FluxPipeline')
    @patch('ai_karen_engine.integrations.providers.flux_provider.torch')
    def test_provider_initialization_schnell_variant(self, mock_torch, mock_flux_pipeline):
        """Test provider initialization with schnell variant."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.bfloat16 = "bfloat16"
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        mock_flux_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = FluxProvider(
            model="test-flux-model",
            variant="schnell",
            device="cuda"
        )
        
        assert provider.variant == "schnell"
        assert provider.metadata["variant"] == "schnell"
        assert provider.metadata["steps_range"] == [1, 8]
        assert provider.metadata["guidance_scale_range"] == [0.0, 2.0]
    
    @patch('ai_karen_engine.integrations.providers.flux_provider.FluxPipeline')
    @patch('ai_karen_engine.integrations.providers.flux_provider.torch')
    def test_generate_image_dev_variant(self, mock_torch, mock_flux_pipeline):
        """Test image generation with dev variant."""
        # Setup mocks
        mock_torch.cuda.is_available.return_value = True
        mock_torch.bfloat16 = "bfloat16"
        mock_torch.manual_seed = Mock()
        mock_torch.cuda.manual_seed = Mock()
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        
        # Mock image generation result
        mock_image = Mock()
        mock_buffer = io.BytesIO(b"fake_image_data")
        mock_image.save = Mock(side_effect=lambda buf, format: buf.write(b"fake_image_data"))
        
        mock_result = Mock()
        mock_result.images = [mock_image]
        mock_pipeline_instance.return_value = mock_result
        
        mock_flux_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        # Create provider
        provider = FluxProvider(model="test-model", variant="dev")
        provider._pipeline = mock_pipeline_instance
        
        # Test image generation
        with patch('base64.b64encode') as mock_b64encode:
            mock_b64encode.return_value = b"encoded_image"
            mock_b64encode.return_value.decode.return_value = "encoded_image_string"
            
            result = provider.generate_image(
                prompt="test prompt",
                width=1024,
                height=1024
            )
        
        # Verify result structure
        assert "images" in result
        assert "prompt" in result
        assert "parameters" in result
        assert "metadata" in result
        assert "generation_time" in result
        
        assert result["prompt"] == "test prompt"
        assert result["parameters"]["width"] == 1024
        assert result["parameters"]["height"] == 1024
        assert result["parameters"]["num_inference_steps"] == 28  # Default for dev
        assert result["parameters"]["guidance_scale"] == 3.5  # Default for dev
        assert result["parameters"]["variant"] == "dev"
        
        # Verify pipeline was called with correct parameters
        mock_pipeline_instance.assert_called_once_with(
            prompt="test prompt",
            width=1024,
            height=1024,
            num_inference_steps=28,
            guidance_scale=3.5,
            num_images_per_prompt=1,
            max_sequence_length=512
        )
    
    @patch('ai_karen_engine.integrations.providers.flux_provider.FluxPipeline')
    @patch('ai_karen_engine.integrations.providers.flux_provider.torch')
    def test_generate_image_schnell_variant(self, mock_torch, mock_flux_pipeline):
        """Test image generation with schnell variant."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.bfloat16 = "bfloat16"
        mock_torch.manual_seed = Mock()
        mock_torch.cuda.manual_seed = Mock()
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        
        mock_image = Mock()
        mock_image.save = Mock(side_effect=lambda buf, format: buf.write(b"fake_image_data"))
        
        mock_result = Mock()
        mock_result.images = [mock_image]
        mock_pipeline_instance.return_value = mock_result
        
        mock_flux_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = FluxProvider(model="test-model", variant="schnell")
        provider._pipeline = mock_pipeline_instance
        
        with patch('base64.b64encode') as mock_b64encode:
            mock_b64encode.return_value = b"encoded_image"
            mock_b64encode.return_value.decode.return_value = "encoded_image_string"
            
            result = provider.generate_image(
                prompt="test prompt",
                width=1024,
                height=1024
            )
        
        # Verify schnell-specific defaults
        assert result["parameters"]["num_inference_steps"] == 4  # Default for schnell
        assert result["parameters"]["guidance_scale"] == 0.0  # Default for schnell
        assert result["parameters"]["variant"] == "schnell"
    
    @patch('ai_karen_engine.integrations.providers.flux_provider.FluxPipeline')
    @patch('ai_karen_engine.integrations.providers.flux_provider.torch')
    def test_generate_image_with_custom_parameters(self, mock_torch, mock_flux_pipeline):
        """Test image generation with custom parameters."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.bfloat16 = "bfloat16"
        mock_torch.manual_seed = Mock()
        mock_torch.cuda.manual_seed = Mock()
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        
        mock_image = Mock()
        mock_image.save = Mock(side_effect=lambda buf, format: buf.write(b"fake_image_data"))
        
        mock_result = Mock()
        mock_result.images = [mock_image]
        mock_pipeline_instance.return_value = mock_result
        
        mock_flux_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = FluxProvider(model="test-model", variant="dev")
        provider._pipeline = mock_pipeline_instance
        
        with patch('base64.b64encode') as mock_b64encode:
            mock_b64encode.return_value = b"encoded_image"
            mock_b64encode.return_value.decode.return_value = "encoded_image_string"
            
            result = provider.generate_image(
                prompt="test prompt",
                width=512,
                height=768,
                num_inference_steps=40,
                guidance_scale=5.0,
                seed=42,
                max_sequence_length=256
            )
        
        # Verify custom parameters were used
        assert result["parameters"]["width"] == 512
        assert result["parameters"]["height"] == 768
        assert result["parameters"]["num_inference_steps"] == 40
        assert result["parameters"]["guidance_scale"] == 5.0
        assert result["parameters"]["seed"] == 42
        assert result["parameters"]["max_sequence_length"] == 256
        
        # Verify seed was set
        mock_torch.manual_seed.assert_called_with(42)
        mock_torch.cuda.manual_seed.assert_called_with(42)
    
    def test_generate_text_not_supported(self):
        """Test that text generation raises appropriate error."""
        provider = FluxProvider(model="test-model")
        
        with pytest.raises(GenerationFailed, match="Text generation not supported"):
            provider.generate_text("test prompt")
    
    def test_embed_not_supported(self):
        """Test that embedding raises appropriate error."""
        provider = FluxProvider(model="test-model")
        
        with pytest.raises(GenerationFailed, match="Text embedding not supported"):
            provider.embed("test text")
    
    @patch('ai_karen_engine.integrations.providers.flux_provider.FluxPipeline')
    @patch('ai_karen_engine.integrations.providers.flux_provider.torch')
    def test_is_available_with_dependencies(self, mock_torch, mock_flux_pipeline):
        """Test availability check when dependencies are available."""
        provider = FluxProvider(model="test-model")
        assert provider.is_available() is True
    
    @patch('ai_karen_engine.integrations.providers.flux_provider.FluxPipeline', side_effect=ImportError)
    def test_is_available_without_dependencies(self, mock_flux_pipeline):
        """Test availability check when dependencies are missing."""
        provider = FluxProvider(model="test-model")
        assert provider.is_available() is False
    
    @patch('ai_karen_engine.integrations.providers.flux_provider.FluxPipeline')
    @patch('ai_karen_engine.integrations.providers.flux_provider.torch')
    async def test_get_status(self, mock_torch, mock_flux_pipeline):
        """Test provider status."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_properties.return_value.total_memory = 16000000000
        mock_torch.bfloat16 = "bfloat16"
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        mock_flux_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = FluxProvider(model="test-model", variant="dev")
        
        status = await provider.get_status()
        
        assert status["provider"] == "flux"
        assert status["model"] == "test-model"
        assert status["variant"] == "dev"
        assert status["available"] is True
        assert status["pipeline_loaded"] is True
        assert status["gpu_available"] is True
        assert status["resolution"] == [1024, 1024]
        assert "capabilities" in status
    
    @patch('ai_karen_engine.integrations.providers.flux_provider.FluxPipeline')
    @patch('ai_karen_engine.integrations.providers.flux_provider.torch')
    def test_health_check_healthy(self, mock_torch, mock_flux_pipeline):
        """Test health check when provider is healthy."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.bfloat16 = "bfloat16"
        mock_torch.manual_seed = Mock()
        mock_torch.cuda.manual_seed = Mock()
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        
        mock_image = Mock()
        mock_image.save = Mock(side_effect=lambda buf, format: buf.write(b"fake_image_data"))
        
        mock_result = Mock()
        mock_result.images = [mock_image]
        mock_pipeline_instance.return_value = mock_result
        
        mock_flux_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = FluxProvider(model="test-model", variant="schnell")
        
        with patch('base64.b64encode') as mock_b64encode:
            mock_b64encode.return_value = b"encoded_image"
            mock_b64encode.return_value.decode.return_value = "encoded_image_string"
            
            health = provider.health_check()
        
        assert health["status"] == "healthy"
        assert "response_time" in health
        assert health["model_tested"] == "test-model"
        assert health["variant"] == "schnell"
        assert "capabilities" in health
        assert "optimal_steps" in health
        assert "optimal_guidance" in health
    
    def test_health_check_dependencies_missing(self):
        """Test health check when dependencies are missing."""
        with patch.object(FluxProvider, 'is_available', return_value=False):
            provider = FluxProvider(model="test-model")
            health = provider.health_check()
            
            assert health["status"] == "unhealthy"
            assert "dependencies not installed" in health["error"]
    
    @patch('ai_karen_engine.integrations.providers.flux_provider.FluxPipeline')
    @patch('ai_karen_engine.integrations.providers.flux_provider.torch')
    def test_get_model_metadata(self, mock_torch, mock_flux_pipeline):
        """Test getting model metadata."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.bfloat16 = "bfloat16"
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        mock_flux_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = FluxProvider(
            model="test-model",
            model_path="/path/to/model",
            variant="dev"
        )
        
        metadata = provider.get_model_metadata()
        
        assert metadata["type"] == "image"
        assert metadata["subtype"] == "flux"
        assert metadata["model_name"] == "test-model"
        assert metadata["model_path"] == "/path/to/model"
        assert metadata["variant"] == "dev"
        assert metadata["pipeline_loaded"] is True
        assert "capabilities" in metadata
    
    @patch('ai_karen_engine.integrations.providers.flux_provider.FluxPipeline')
    @patch('ai_karen_engine.integrations.providers.flux_provider.torch')
    def test_get_generation_parameters_dev(self, mock_torch, mock_flux_pipeline):
        """Test getting generation parameters for dev variant."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.bfloat16 = "bfloat16"
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        mock_flux_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = FluxProvider(model="test-model", variant="dev")
        
        params = provider.get_generation_parameters()
        
        assert "prompt" in params
        assert "width" in params
        assert "height" in params
        assert "num_inference_steps" in params
        assert "guidance_scale" in params
        assert "max_sequence_length" in params
        
        assert params["prompt"]["required"] is True
        assert params["width"]["default"] == 1024
        assert params["height"]["default"] == 1024
        assert params["num_inference_steps"]["default"] == 28
        assert params["guidance_scale"]["default"] == 3.5
    
    @patch('ai_karen_engine.integrations.providers.flux_provider.FluxPipeline')
    @patch('ai_karen_engine.integrations.providers.flux_provider.torch')
    def test_get_generation_parameters_schnell(self, mock_torch, mock_flux_pipeline):
        """Test getting generation parameters for schnell variant."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.bfloat16 = "bfloat16"
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        mock_flux_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = FluxProvider(model="test-model", variant="schnell")
        
        params = provider.get_generation_parameters()
        
        assert params["num_inference_steps"]["default"] == 4
        assert params["guidance_scale"]["default"] == 0.0
    
    @patch('ai_karen_engine.integrations.providers.flux_provider.FluxPipeline')
    @patch('ai_karen_engine.integrations.providers.flux_provider.torch')
    def test_get_optimal_parameters(self, mock_torch, mock_flux_pipeline):
        """Test getting optimal parameters."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.bfloat16 = "bfloat16"
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        mock_flux_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        # Test dev variant
        provider_dev = FluxProvider(model="test-model", variant="dev")
        optimal_dev = provider_dev.get_optimal_parameters()
        
        assert optimal_dev["num_inference_steps"] == 28
        assert optimal_dev["guidance_scale"] == 3.5
        assert optimal_dev["width"] == 1024
        assert optimal_dev["height"] == 1024
        
        # Test schnell variant
        provider_schnell = FluxProvider(model="test-model", variant="schnell")
        optimal_schnell = provider_schnell.get_optimal_parameters()
        
        assert optimal_schnell["num_inference_steps"] == 4
        assert optimal_schnell["guidance_scale"] == 0.0
    
    def test_get_available_models(self):
        """Test getting available models list."""
        provider = FluxProvider(model="test-model")
        
        models = provider.get_available_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert "black-forest-labs/FLUX.1-dev" in models
        assert "black-forest-labs/FLUX.1-schnell" in models