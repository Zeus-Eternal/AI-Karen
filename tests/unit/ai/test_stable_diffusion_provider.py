"""
Unit tests for StableDiffusionProvider
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import base64
import io
from PIL import Image

from ai_karen_engine.integrations.providers.stable_diffusion_provider import StableDiffusionProvider
from ai_karen_engine.integrations.llm_utils import GenerationFailed


class TestStableDiffusionProvider:
    """Test StableDiffusionProvider functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the diffusers import to avoid dependency issues in tests
        self.mock_diffusers = Mock()
        self.mock_torch = Mock()
        
        # Create mock pipeline
        self.mock_pipeline = Mock()
        self.mock_img2img_pipeline = Mock()
        self.mock_inpaint_pipeline = Mock()
        
        # Mock image result
        self.mock_image = Mock(spec=Image.Image)
        self.mock_image.save = Mock()
        
        self.mock_pipeline.return_value.images = [self.mock_image]
        self.mock_img2img_pipeline.return_value.images = [self.mock_image]
        
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.StableDiffusionPipeline')
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.torch')
    def test_provider_initialization(self, mock_torch, mock_sd_pipeline):
        """Test provider initialization."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.float16 = "float16"
        mock_torch.float32 = "float32"
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        mock_sd_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = StableDiffusionProvider(
            model="test-model",
            use_local=True,
            device="cuda"
        )
        
        assert provider.model == "test-model"
        assert provider.device == "cuda"
        assert provider.metadata["type"] == "image"
        assert provider.metadata["subtype"] == "stable-diffusion"
        assert "text2img" in provider.metadata["capabilities"]
        
        mock_sd_pipeline.from_pretrained.assert_called_once()
    
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.StableDiffusionPipeline')
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.torch')
    def test_generate_image_success(self, mock_torch, mock_sd_pipeline):
        """Test successful image generation."""
        # Setup mocks
        mock_torch.cuda.is_available.return_value = True
        mock_torch.float16 = "float16"
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
        
        mock_sd_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        # Create provider
        provider = StableDiffusionProvider(model="test-model", use_local=True)
        provider._pipeline = mock_pipeline_instance
        
        # Test image generation
        with patch('base64.b64encode') as mock_b64encode:
            mock_b64encode.return_value = b"encoded_image"
            mock_b64encode.return_value.decode.return_value = "encoded_image_string"
            
            result = provider.generate_image(
                prompt="test prompt",
                width=512,
                height=512,
                num_inference_steps=20,
                guidance_scale=7.5
            )
        
        # Verify result structure
        assert "images" in result
        assert "prompt" in result
        assert "parameters" in result
        assert "metadata" in result
        assert "generation_time" in result
        
        assert result["prompt"] == "test prompt"
        assert result["parameters"]["width"] == 512
        assert result["parameters"]["height"] == 512
        assert result["parameters"]["num_inference_steps"] == 20
        assert result["parameters"]["guidance_scale"] == 7.5
        
        # Verify pipeline was called with correct parameters
        mock_pipeline_instance.assert_called_once_with(
            prompt="test prompt",
            negative_prompt=None,
            width=512,
            height=512,
            num_inference_steps=20,
            guidance_scale=7.5,
            num_images_per_prompt=1
        )
    
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.StableDiffusionPipeline')
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.torch')
    def test_generate_image_with_seed(self, mock_torch, mock_sd_pipeline):
        """Test image generation with seed."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.float16 = "float16"
        mock_torch.manual_seed = Mock()
        mock_torch.cuda.manual_seed = Mock()
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        
        mock_image = Mock()
        mock_image.save = Mock(side_effect=lambda buf, format: buf.write(b"fake_image_data"))
        
        mock_result = Mock()
        mock_result.images = [mock_image]
        mock_pipeline_instance.return_value = mock_result
        
        mock_sd_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = StableDiffusionProvider(model="test-model", use_local=True)
        provider._pipeline = mock_pipeline_instance
        
        with patch('base64.b64encode') as mock_b64encode:
            mock_b64encode.return_value = b"encoded_image"
            mock_b64encode.return_value.decode.return_value = "encoded_image_string"
            
            result = provider.generate_image(
                prompt="test prompt",
                seed=42
            )
        
        # Verify seed was set
        mock_torch.manual_seed.assert_called_with(42)
        mock_torch.cuda.manual_seed.assert_called_with(42)
        
        assert result["parameters"]["seed"] == 42
    
    def test_generate_text_not_supported(self):
        """Test that text generation raises appropriate error."""
        provider = StableDiffusionProvider(model="test-model", use_local=False)
        
        with pytest.raises(GenerationFailed, match="Text generation not supported"):
            provider.generate_text("test prompt")
    
    def test_embed_not_supported(self):
        """Test that embedding raises appropriate error."""
        provider = StableDiffusionProvider(model="test-model", use_local=False)
        
        with pytest.raises(GenerationFailed, match="Text embedding not supported"):
            provider.embed("test text")
    
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.StableDiffusionPipeline')
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.torch')
    def test_is_available_with_dependencies(self, mock_torch, mock_sd_pipeline):
        """Test availability check when dependencies are available."""
        provider = StableDiffusionProvider(model="test-model", use_local=False)
        assert provider.is_available() is True
    
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.StableDiffusionPipeline', side_effect=ImportError)
    def test_is_available_without_dependencies(self, mock_sd_pipeline):
        """Test availability check when dependencies are missing."""
        provider = StableDiffusionProvider(model="test-model", use_local=False)
        assert provider.is_available() is False
    
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.StableDiffusionPipeline')
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.torch')
    async def test_get_status(self, mock_torch, mock_sd_pipeline):
        """Test provider status."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.get_device_properties.return_value.total_memory = 8000000000
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        mock_sd_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = StableDiffusionProvider(model="test-model", use_local=True)
        
        status = await provider.get_status()
        
        assert status["provider"] == "stable-diffusion"
        assert status["model"] == "test-model"
        assert status["available"] is True
        assert status["pipeline_loaded"] is True
        assert status["gpu_available"] is True
        assert "capabilities" in status
    
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.StableDiffusionPipeline')
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.torch')
    def test_health_check_healthy(self, mock_torch, mock_sd_pipeline):
        """Test health check when provider is healthy."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.float16 = "float16"
        mock_torch.manual_seed = Mock()
        mock_torch.cuda.manual_seed = Mock()
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        
        mock_image = Mock()
        mock_image.save = Mock(side_effect=lambda buf, format: buf.write(b"fake_image_data"))
        
        mock_result = Mock()
        mock_result.images = [mock_image]
        mock_pipeline_instance.return_value = mock_result
        
        mock_sd_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = StableDiffusionProvider(model="test-model", use_local=True)
        
        with patch('base64.b64encode') as mock_b64encode:
            mock_b64encode.return_value = b"encoded_image"
            mock_b64encode.return_value.decode.return_value = "encoded_image_string"
            
            health = provider.health_check()
        
        assert health["status"] == "healthy"
        assert "response_time" in health
        assert health["model_tested"] == "test-model"
        assert "capabilities" in health
    
    def test_health_check_dependencies_missing(self):
        """Test health check when dependencies are missing."""
        with patch.object(StableDiffusionProvider, 'is_available', return_value=False):
            provider = StableDiffusionProvider(model="test-model", use_local=False)
            health = provider.health_check()
            
            assert health["status"] == "unhealthy"
            assert "dependencies not installed" in health["error"]
    
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.StableDiffusionPipeline')
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.torch')
    def test_get_model_metadata(self, mock_torch, mock_sd_pipeline):
        """Test getting model metadata."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.float16 = "float16"
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        mock_sd_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = StableDiffusionProvider(
            model="test-model",
            model_path="/path/to/model",
            use_local=True
        )
        
        metadata = provider.get_model_metadata()
        
        assert metadata["type"] == "image"
        assert metadata["subtype"] == "stable-diffusion"
        assert metadata["model_name"] == "test-model"
        assert metadata["model_path"] == "/path/to/model"
        assert metadata["pipeline_loaded"] is True
        assert "capabilities" in metadata
    
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.StableDiffusionPipeline')
    @patch('ai_karen_engine.integrations.providers.stable_diffusion_provider.torch')
    def test_get_generation_parameters(self, mock_torch, mock_sd_pipeline):
        """Test getting generation parameters."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.float16 = "float16"
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.to.return_value = mock_pipeline_instance
        mock_sd_pipeline.from_pretrained.return_value = mock_pipeline_instance
        
        provider = StableDiffusionProvider(model="test-model", use_local=True)
        
        params = provider.get_generation_parameters()
        
        assert "prompt" in params
        assert "width" in params
        assert "height" in params
        assert "num_inference_steps" in params
        assert "guidance_scale" in params
        
        assert params["prompt"]["required"] is True
        assert params["width"]["default"] == 512
        assert params["height"]["default"] == 512
    
    def test_get_available_models(self):
        """Test getting available models list."""
        provider = StableDiffusionProvider(model="test-model", use_local=False)
        
        models = provider.get_available_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert "runwayml/stable-diffusion-v1-5" in models
        assert "stabilityai/stable-diffusion-xl-base-1.0" in models