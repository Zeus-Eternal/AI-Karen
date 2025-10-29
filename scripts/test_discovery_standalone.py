#!/usr/bin/env python3
"""
Standalone test for model discovery engine without full service dependencies.
"""

import asyncio
import tempfile
import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

# Import only the specific module we need
try:
    from ai_karen_engine.services.model_discovery_engine import (
        ModelDiscoveryEngine, ModelType, ModalityType, ModelCategory,
        ModelSpecialization, ModelStatus, Modality, ResourceRequirements, ModelMetadata
    )
    print("✅ Successfully imported ModelDiscoveryEngine")
except ImportError as e:
    print(f"❌ Failed to import ModelDiscoveryEngine: {e}")
    
    # Try importing just the classes we need directly
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "model_discovery_engine", 
        "src/ai_karen_engine/services/model_discovery_engine.py"
    )
    module = importlib.util.module_from_spec(spec)
    
    # Mock the logger to avoid import issues
    import logging
    module.logger = logging.getLogger("test")
    
    try:
        spec.loader.exec_module(module)
        
        # Extract the classes we need
        ModelDiscoveryEngine = module.ModelDiscoveryEngine
        ModelType = module.ModelType
        ModalityType = module.ModalityType
        ModelCategory = module.ModelCategory
        ModelSpecialization = module.ModelSpecialization
        ModelStatus = module.ModelStatus
        Modality = module.Modality
        ResourceRequirements = module.ResourceRequirements
        ModelMetadata = module.ModelMetadata
        
        print("✅ Successfully imported ModelDiscoveryEngine via direct module loading")
    except Exception as e2:
        print(f"❌ Failed to import via direct loading: {e2}")
        sys.exit(1)

async def test_basic_functionality():
    """Test basic model discovery functionality."""
    print("\n🔍 Testing Model Discovery Engine Basic Functionality")
    print("-" * 60)
    
    try:
        # Test enum values
        print("Testing enums...")
        assert ModelType.LLAMA_CPP.value == "llama-cpp"
        assert ModalityType.TEXT.value == "text"
        assert ModelCategory.LANGUAGE.value == "language"
        print("✅ Enums work correctly")
        
        # Test data structures
        print("Testing data structures...")
        metadata = ModelMetadata(
            name="test",
            display_name="Test Model",
            description="A test model",
            version="1.0",
            author="Test Author",
            license="MIT",
            context_length=2048
        )
        assert metadata.name == "test"
        assert metadata.context_length == 2048
        print("✅ ModelMetadata works correctly")
        
        modality = Modality(
            type=ModalityType.TEXT,
            input_supported=True,
            output_supported=True,
            formats=["text", "json"]
        )
        assert modality.type == ModalityType.TEXT
        assert modality.input_supported is True
        print("✅ Modality works correctly")
        
        requirements = ResourceRequirements(
            min_ram_gb=2.0,
            recommended_ram_gb=4.0,
            cpu_cores=2,
            gpu_required=False,
            disk_space_gb=1.0
        )
        assert requirements.min_ram_gb == 2.0
        assert requirements.gpu_required is False
        print("✅ ResourceRequirements works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_discovery_engine_creation():
    """Test creating a ModelDiscoveryEngine instance."""
    print("\n🏗️ Testing ModelDiscoveryEngine Creation")
    print("-" * 60)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            models_dir = Path(temp_dir) / "models"
            models_dir.mkdir()
            cache_dir = Path(temp_dir) / "cache"
            
            # Create discovery engine
            discovery_engine = ModelDiscoveryEngine(
                models_root=str(models_dir),
                cache_dir=str(cache_dir)
            )
            
            print("✅ ModelDiscoveryEngine created successfully")
            
            # Test basic properties
            assert discovery_engine.models_root == models_dir
            assert discovery_engine.cache_dir == cache_dir
            print("✅ Properties set correctly")
            
            # Test type patterns
            assert ModelType.LLAMA_CPP in discovery_engine.type_patterns
            assert ".gguf" in discovery_engine.type_patterns[ModelType.LLAMA_CPP]
            print("✅ Type patterns configured correctly")
            
            # Test modality patterns
            assert ModalityType.TEXT in discovery_engine.modality_patterns
            assert "text" in discovery_engine.modality_patterns[ModalityType.TEXT]
            print("✅ Modality patterns configured correctly")
            
            # Cleanup
            discovery_engine.cleanup()
            print("✅ Cleanup completed successfully")
            
            return True
            
    except Exception as e:
        print(f"❌ Discovery engine creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_file_operations():
    """Test file and directory operations."""
    print("\n📁 Testing File Operations")
    print("-" * 60)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            models_dir = Path(temp_dir) / "models"
            models_dir.mkdir()
            cache_dir = Path(temp_dir) / "cache"
            
            discovery_engine = ModelDiscoveryEngine(
                models_root=str(models_dir),
                cache_dir=str(cache_dir)
            )
            
            # Test model ID generation
            test_path = models_dir / "llama-cpp" / "test.gguf"
            model_id = discovery_engine._generate_model_id(test_path)
            assert isinstance(model_id, str)
            assert len(model_id) > 0
            print(f"✅ Model ID generation works: {model_id}")
            
            # Test directory type detection
            llama_dir = models_dir / "llama-cpp"
            llama_dir.mkdir()
            detected_type = discovery_engine._detect_directory_model_type(llama_dir)
            assert detected_type == ModelType.LLAMA_CPP
            print("✅ Directory type detection works")
            
            # Test metadata enhancement from filename
            metadata = ModelMetadata(
                name="test", display_name="test", description="", version="unknown",
                author="unknown", license="unknown", context_length=0
            )
            enhanced = discovery_engine._enhance_metadata_from_filename(
                "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf", metadata
            )
            assert enhanced.quantization == "Q4_K_M"
            assert enhanced.parameter_count == 1100000000  # 1.1B
            print("✅ Metadata enhancement from filename works")
            
            # Test tag generation
            tags = discovery_engine._generate_tags("test-chat", metadata, [])
            assert isinstance(tags, list)
            print(f"✅ Tag generation works: {tags}")
            
            discovery_engine.cleanup()
            return True
            
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_with_real_models():
    """Test with real models if available."""
    print("\n🎯 Testing with Real Models (if available)")
    print("-" * 60)
    
    models_dir = Path("models")
    if not models_dir.exists():
        print("ℹ️ No real models directory found, skipping real model test")
        return True
    
    try:
        discovery_engine = ModelDiscoveryEngine(models_root=str(models_dir))
        
        # Test discovery
        print("Discovering real models...")
        models = await discovery_engine.discover_all_models()
        
        print(f"✅ Found {len(models)} real models")
        
        if models:
            # Show first few models
            for i, model in enumerate(models[:3]):
                print(f"  {i+1}. {model.display_name}")
                print(f"     Type: {model.type.value}")
                print(f"     Category: {model.category.value}")
                print(f"     Size: {model.size / (1024*1024*1024):.2f} GB")
                print(f"     Modalities: {[m.type.value for m in model.modalities]}")
                print(f"     Tags: {model.tags[:5]}...")  # First 5 tags
                print()
            
            # Test statistics
            stats = discovery_engine.get_discovery_statistics()
            print(f"✅ Statistics generated: {len(stats)} fields")
            print(f"   Total models: {stats.get('total_models', 0)}")
            print(f"   Categories: {list(stats.get('categories', {}).keys())}")
            print(f"   Types: {list(stats.get('types', {}).keys())}")
        
        discovery_engine.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Real models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("🧪 Model Discovery Engine Standalone Test Suite")
    print("=" * 70)
    
    tests = [
        test_basic_functionality,
        test_discovery_engine_creation,
        test_file_operations,
        test_with_real_models
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {i+1}. {test.__name__}: {status}")
    
    passed = sum(results)
    total = len(results)
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Model Discovery Engine is working correctly.")
        return 0
    else:
        print("💥 Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)