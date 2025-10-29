"""
Unit tests for Model Discovery Engine

Tests the comprehensive model discovery and metadata extraction system
to ensure it correctly identifies, categorizes, and validates models.
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from src.ai_karen_engine.services.model_discovery_engine import (
    ModelDiscoveryEngine, ModelInfo, ModelType, ModalityType, ModelCategory,
    ModelSpecialization, ModelStatus, Modality, ResourceRequirements, ModelMetadata
)


class TestModelDiscoveryEngine:
    """Test suite for ModelDiscoveryEngine."""
    
    @pytest.fixture
    def temp_models_dir(self):
        """Create a temporary models directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            models_dir = Path(temp_dir) / "models"
            models_dir.mkdir()
            
            # Create test model structure
            self._create_test_models(models_dir)
            
            yield models_dir
    
    def _create_test_models(self, models_dir: Path):
        """Create test model files and directories."""
        # Create llama-cpp models
        llama_dir = models_dir / "llama-cpp"
        llama_dir.mkdir()
        
        # Create a test GGUF file
        gguf_file = llama_dir / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf"
        with open(gguf_file, 'wb') as f:
            f.write(b'GGUF')  # Magic number
            f.write(b'\x00' * 1000)  # Dummy content
        
        # Create transformers models
        transformers_dir = models_dir / "transformers"
        transformers_dir.mkdir()
        
        gpt2_dir = transformers_dir / "gpt2"
        gpt2_dir.mkdir()
        
        # Create config.json
        config_data = {
            "model_type": "gpt2",
            "n_positions": 1024,
            "n_params": 124000000,
            "architectures": ["GPT2LMHeadModel"],
            "task": ["text-generation"]
        }
        with open(gpt2_dir / "config.json", 'w') as f:
            json.dump(config_data, f)
        
        # Create model file
        model_file = gpt2_dir / "pytorch_model.bin"
        with open(model_file, 'wb') as f:
            f.write(b'\x00' * 5000)  # Dummy content
        
        # Create stable diffusion model
        sd_dir = models_dir / "stable-diffusion"
        sd_dir.mkdir()
        
        sd_model_dir = sd_dir / "stable-diffusion-v1-5"
        sd_model_dir.mkdir()
        
        # Create model_index.json
        index_data = {
            "unet": ["UNet2DConditionModel", "unet"],
            "vae": ["AutoencoderKL", "vae"],
            "text_encoder": ["CLIPTextModel", "text_encoder"]
        }
        with open(sd_model_dir / "model_index.json", 'w') as f:
            json.dump(index_data, f)
        
        # Create required subdirectories
        for subdir in ["unet", "vae", "text_encoder"]:
            (sd_model_dir / subdir).mkdir()
            with open(sd_model_dir / subdir / "config.json", 'w') as f:
                json.dump({"model_type": subdir}, f)
    
    @pytest.fixture
    def discovery_engine(self, temp_models_dir):
        """Create a ModelDiscoveryEngine instance for testing."""
        cache_dir = temp_models_dir.parent / "cache"
        return ModelDiscoveryEngine(
            models_root=str(temp_models_dir),
            cache_dir=str(cache_dir)
        )
    
    @pytest.mark.asyncio
    async def test_discover_all_models(self, discovery_engine):
        """Test discovering all models in the test directory."""
        models = await discovery_engine.discover_all_models()
        
        assert len(models) >= 3  # At least llama-cpp, transformers, and stable-diffusion
        
        # Check that different model types are discovered
        model_types = {model.type for model in models}
        assert ModelType.LLAMA_CPP in model_types
        assert ModelType.TRANSFORMERS in model_types
        assert ModelType.STABLE_DIFFUSION in model_types
    
    @pytest.mark.asyncio
    async def test_scan_llama_cpp_models(self, discovery_engine, temp_models_dir):
        """Test scanning llama-cpp models specifically."""
        llama_dir = temp_models_dir / "llama-cpp"
        models = await discovery_engine.scan_models_directory(str(llama_dir))
        
        assert len(models) >= 1
        
        model = models[0]
        assert model.type == ModelType.LLAMA_CPP
        assert model.name == "tinyllama-1.1b-chat-v2.0.Q4_K_M"
        assert model.path.endswith(".gguf")
        assert model.size > 0
    
    @pytest.mark.asyncio
    async def test_scan_transformers_models(self, discovery_engine, temp_models_dir):
        """Test scanning transformers models specifically."""
        transformers_dir = temp_models_dir / "transformers"
        models = await discovery_engine.scan_models_directory(str(transformers_dir))
        
        assert len(models) >= 1
        
        model = models[0]
        assert model.type == ModelType.TRANSFORMERS
        assert "gpt2" in model.name.lower()
        assert model.metadata.context_length == 1024
        assert model.metadata.parameter_count == 124000000
    
    @pytest.mark.asyncio
    async def test_scan_stable_diffusion_models(self, discovery_engine, temp_models_dir):
        """Test scanning stable diffusion models specifically."""
        sd_dir = temp_models_dir / "stable-diffusion"
        models = await discovery_engine.scan_models_directory(str(sd_dir))
        
        assert len(models) >= 1
        
        model = models[0]
        assert model.type == ModelType.STABLE_DIFFUSION
        assert model.category == ModelCategory.VISION
        assert any(mod.type == ModalityType.IMAGE for mod in model.modalities)
    
    @pytest.mark.asyncio
    async def test_extract_model_metadata(self, discovery_engine, temp_models_dir):
        """Test metadata extraction from config files."""
        gpt2_dir = temp_models_dir / "transformers" / "gpt2"
        metadata = await discovery_engine.extract_model_metadata(str(gpt2_dir))
        
        assert metadata.architecture == "gpt2"
        assert metadata.context_length == 1024
        assert metadata.parameter_count == 124000000
        assert "text-generation" in metadata.use_cases
    
    @pytest.mark.asyncio
    async def test_detect_model_modalities(self, discovery_engine):
        """Test modality detection for different model types."""
        # Test text model
        text_modalities = await discovery_engine.detect_model_modalities("models/llama-cpp/tinyllama.gguf")
        assert any(mod.type == ModalityType.TEXT for mod in text_modalities)
        
        # Test image model
        image_modalities = await discovery_engine.detect_model_modalities("models/stable-diffusion/model")
        assert any(mod.type == ModalityType.IMAGE for mod in image_modalities)
    
    @pytest.mark.asyncio
    async def test_categorize_model(self, discovery_engine):
        """Test model categorization."""
        # Test language model
        metadata = ModelMetadata(
            name="test", display_name="test", description="", version="1.0",
            author="test", license="MIT", context_length=1024
        )
        text_modalities = [Modality(
            type=ModalityType.TEXT, input_supported=True, output_supported=True, formats=["text"]
        )]
        
        category = await discovery_engine.categorize_model("gpt2", metadata, text_modalities)
        assert category == ModelCategory.LANGUAGE
        
        # Test vision model
        image_modalities = [Modality(
            type=ModalityType.IMAGE, input_supported=True, output_supported=True, formats=["jpg"]
        )]
        
        category = await discovery_engine.categorize_model("stable-diffusion", metadata, image_modalities)
        assert category == ModelCategory.VISION
    
    def test_determine_specializations(self, discovery_engine):
        """Test specialization determination."""
        metadata = ModelMetadata(
            name="test", display_name="test", description="", version="1.0",
            author="test", license="MIT", context_length=1024,
            use_cases=["chat", "instruction-following"]
        )
        
        specializations = discovery_engine._determine_specializations("tinyllama-chat", metadata)
        
        assert ModelSpecialization.CHAT in specializations
        
        # Test code model
        code_specializations = discovery_engine._determine_specializations("codellama", metadata)
        assert ModelSpecialization.CODE in code_specializations
    
    def test_generate_tags(self, discovery_engine):
        """Test tag generation."""
        metadata = ModelMetadata(
            name="test", display_name="test", description="", version="1.0",
            author="test", license="MIT", context_length=1024,
            parameter_count=1100000000,  # 1.1B
            quantization="Q4_K_M",
            architecture="llama",
            use_cases=["chat"]
        )
        
        modalities = [Modality(
            type=ModalityType.TEXT, input_supported=True, output_supported=True, formats=["text"]
        )]
        
        tags = discovery_engine._generate_tags("tinyllama-chat", metadata, modalities)
        
        assert "text" in tags
        assert "small" in tags  # < 10B parameters
        assert "quantized" in tags
        assert "q4_k_m" in tags
        assert "llama" in tags
        assert "chat" in tags
    
    def test_estimate_resource_requirements(self, discovery_engine):
        """Test resource requirement estimation."""
        size = 1024 * 1024 * 1024  # 1GB
        metadata = ModelMetadata(
            name="test", display_name="test", description="", version="1.0",
            author="test", license="MIT", context_length=1024,
            parameter_count=1100000000  # 1.1B
        )
        
        requirements = discovery_engine._estimate_resource_requirements(
            size, ModelType.LLAMA_CPP, metadata
        )
        
        assert requirements.min_ram_gb >= 1.0
        assert requirements.recommended_ram_gb >= requirements.min_ram_gb
        assert requirements.disk_space_gb >= 1.0
        assert not requirements.gpu_required  # llama-cpp doesn't require GPU
    
    def test_extract_capabilities(self, discovery_engine):
        """Test capability extraction."""
        modalities = [Modality(
            type=ModalityType.TEXT, input_supported=True, output_supported=True, formats=["text"]
        )]
        
        metadata = ModelMetadata(
            name="test", display_name="test", description="", version="1.0",
            author="test", license="MIT", context_length=1024,
            use_cases=["chat", "instruction-following"],
            quantization="Q4_K_M"
        )
        
        capabilities = discovery_engine._extract_capabilities(
            ModelType.LLAMA_CPP, modalities, metadata
        )
        
        assert "text-generation" in capabilities
        assert "text-understanding" in capabilities
        assert "local-inference" in capabilities
        assert "cpu-optimized" in capabilities
        assert "conversational-ai" in capabilities
        assert "instruction-following" in capabilities
        assert "quantized-inference" in capabilities
    
    @pytest.mark.asyncio
    async def test_validate_model_compatibility(self, discovery_engine, temp_models_dir):
        """Test model compatibility validation."""
        # Test valid GGUF file
        gguf_file = temp_models_dir / "llama-cpp" / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf"
        status = await discovery_engine.validate_model_compatibility(str(gguf_file), ModelType.LLAMA_CPP)
        assert status == ModelStatus.AVAILABLE
        
        # Test valid transformers directory
        gpt2_dir = temp_models_dir / "transformers" / "gpt2"
        status = await discovery_engine.validate_model_compatibility(str(gpt2_dir), ModelType.TRANSFORMERS)
        assert status == ModelStatus.AVAILABLE
        
        # Test non-existent file
        fake_file = temp_models_dir / "nonexistent.gguf"
        status = await discovery_engine.validate_model_compatibility(str(fake_file), ModelType.LLAMA_CPP)
        assert status == ModelStatus.ERROR
    
    @pytest.mark.asyncio
    async def test_organize_models_by_category(self, discovery_engine):
        """Test model organization by category."""
        models = await discovery_engine.discover_all_models()
        organized = await discovery_engine.organize_models_by_category(models)
        
        assert isinstance(organized, dict)
        assert len(organized) > 0
        
        # Check that models are properly categorized
        for category, model_list in organized.items():
            assert isinstance(model_list, list)
            for model in model_list:
                assert model.category.value == category
    
    def test_filter_models(self, discovery_engine):
        """Test model filtering functionality."""
        # Create test models
        models = [
            ModelInfo(
                id="test1", name="test1", display_name="Test 1", type=ModelType.LLAMA_CPP,
                path="/test1", size=1000, modalities=[], capabilities=[], 
                requirements=ResourceRequirements(1.0, 2.0), status=ModelStatus.AVAILABLE,
                metadata=ModelMetadata("test1", "Test 1", "", "1.0", "test", "MIT", 1024),
                category=ModelCategory.LANGUAGE, specialization=[ModelSpecialization.CHAT],
                tags=["small", "chat"], last_updated=0.0
            ),
            ModelInfo(
                id="test2", name="test2", display_name="Test 2", type=ModelType.STABLE_DIFFUSION,
                path="/test2", size=5000, modalities=[], capabilities=[],
                requirements=ResourceRequirements(4.0, 8.0), status=ModelStatus.AVAILABLE,
                metadata=ModelMetadata("test2", "Test 2", "", "1.0", "test", "MIT", 0),
                category=ModelCategory.VISION, specialization=[ModelSpecialization.CREATIVE],
                tags=["large", "image"], last_updated=0.0
            )
        ]
        
        # Add to discovery engine
        with discovery_engine._lock:
            for model in models:
                discovery_engine.discovered_models[model.id] = model
        
        # Test category filter
        language_models = discovery_engine.filter_models(category=ModelCategory.LANGUAGE)
        assert len(language_models) == 1
        assert language_models[0].id == "test1"
        
        # Test specialization filter
        chat_models = discovery_engine.filter_models(specialization=ModelSpecialization.CHAT)
        assert len(chat_models) == 1
        assert chat_models[0].id == "test1"
        
        # Test size filter
        small_models = discovery_engine.filter_models(max_size_gb=0.002)  # 2MB
        assert len(small_models) == 1
        assert small_models[0].id == "test1"
        
        # Test tag filter
        chat_tagged = discovery_engine.filter_models(tags=["chat"])
        assert len(chat_tagged) == 1
        assert chat_tagged[0].id == "test1"
    
    def test_get_discovery_statistics(self, discovery_engine):
        """Test discovery statistics generation."""
        # Add test models
        models = [
            ModelInfo(
                id="test1", name="test1", display_name="Test 1", type=ModelType.LLAMA_CPP,
                path="/test1", size=1000, modalities=[], capabilities=[],
                requirements=ResourceRequirements(1.0, 2.0), status=ModelStatus.AVAILABLE,
                metadata=ModelMetadata("test1", "Test 1", "", "1.0", "test", "MIT", 1024),
                category=ModelCategory.LANGUAGE, specialization=[ModelSpecialization.CHAT],
                tags=["small"], last_updated=0.0
            ),
            ModelInfo(
                id="test2", name="test2", display_name="Test 2", type=ModelType.TRANSFORMERS,
                path="/test2", size=2000, modalities=[], capabilities=[],
                requirements=ResourceRequirements(2.0, 4.0), status=ModelStatus.ERROR,
                metadata=ModelMetadata("test2", "Test 2", "", "1.0", "test", "MIT", 2048),
                category=ModelCategory.LANGUAGE, specialization=[ModelSpecialization.CODE],
                tags=["medium"], last_updated=0.0
            )
        ]
        
        with discovery_engine._lock:
            for model in models:
                discovery_engine.discovered_models[model.id] = model
        
        stats = discovery_engine.get_discovery_statistics()
        
        assert stats["total_models"] == 2
        assert stats["categories"]["language"] == 2
        assert stats["types"]["llama-cpp"] == 1
        assert stats["types"]["transformers"] == 1
        assert stats["statuses"]["available"] == 1
        assert stats["statuses"]["error"] == 1
        assert stats["total_size_gb"] == (3000 / (1024**3))
    
    def test_cache_persistence(self, discovery_engine, temp_models_dir):
        """Test that discovery cache persists between instances."""
        # Create a model info
        model_info = ModelInfo(
            id="test_cache", name="test_cache", display_name="Test Cache", 
            type=ModelType.LLAMA_CPP, path="/test", size=1000, modalities=[], 
            capabilities=[], requirements=ResourceRequirements(1.0, 2.0), 
            status=ModelStatus.AVAILABLE,
            metadata=ModelMetadata("test", "Test", "", "1.0", "test", "MIT", 1024),
            category=ModelCategory.LANGUAGE, specialization=[ModelSpecialization.GENERAL],
            tags=["test"], last_updated=0.0
        )
        
        # Add to cache and save
        with discovery_engine._lock:
            discovery_engine.discovered_models["test_cache"] = model_info
            discovery_engine._save_discovery_cache()
        
        # Create new instance and check if model is loaded
        cache_dir = temp_models_dir.parent / "cache"
        new_engine = ModelDiscoveryEngine(
            models_root=str(temp_models_dir),
            cache_dir=str(cache_dir)
        )
        
        assert "test_cache" in new_engine.discovered_models
        cached_model = new_engine.discovered_models["test_cache"]
        assert cached_model.name == "test_cache"
        assert cached_model.type == ModelType.LLAMA_CPP


@pytest.mark.integration
class TestModelDiscoveryIntegration:
    """Integration tests for model discovery with real model files."""
    
    @pytest.mark.asyncio
    async def test_discover_real_models(self):
        """Test discovery with real models directory (if available)."""
        models_dir = Path("models")
        if not models_dir.exists():
            pytest.skip("Real models directory not available")
        
        discovery_engine = ModelDiscoveryEngine(models_root=str(models_dir))
        
        try:
            models = await discovery_engine.discover_all_models()
            
            # Basic checks
            assert isinstance(models, list)
            
            if models:
                # Check first model has required fields
                model = models[0]
                assert hasattr(model, 'id')
                assert hasattr(model, 'name')
                assert hasattr(model, 'type')
                assert hasattr(model, 'path')
                assert hasattr(model, 'size')
                assert hasattr(model, 'modalities')
                assert hasattr(model, 'capabilities')
                assert hasattr(model, 'metadata')
                
                # Check that path exists
                assert Path(model.path).exists()
                
                print(f"Discovered {len(models)} real models")
                for model in models[:3]:  # Print first 3
                    print(f"  - {model.display_name} ({model.type.value})")
        
        finally:
            discovery_engine.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])