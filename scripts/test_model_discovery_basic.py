#!/usr/bin/env python3
"""
Basic integration test for model discovery system.
This test verifies that the model discovery engine can find and categorize models.
"""

import asyncio
import tempfile
import json
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from ai_karen_engine.services.model_discovery_engine import (
    ModelDiscoveryEngine, ModelType, ModalityType, ModelCategory
)

async def test_basic_discovery():
    """Test basic model discovery functionality."""
    print("Testing Model Discovery Engine...")
    
    # Create temporary test environment
    with tempfile.TemporaryDirectory() as temp_dir:
        models_dir = Path(temp_dir) / "models"
        models_dir.mkdir()
        
        # Create test llama-cpp model
        llama_dir = models_dir / "llama-cpp"
        llama_dir.mkdir()
        
        gguf_file = llama_dir / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf"
        with open(gguf_file, 'wb') as f:
            f.write(b'GGUF')  # Magic number
            f.write(b'\x00' * 1000)  # Dummy content
        
        # Create test transformers model
        transformers_dir = models_dir / "transformers"
        transformers_dir.mkdir()
        
        gpt2_dir = transformers_dir / "gpt2"
        gpt2_dir.mkdir()
        
        config_data = {
            "model_type": "gpt2",
            "n_positions": 1024,
            "architectures": ["GPT2LMHeadModel"]
        }
        with open(gpt2_dir / "config.json", 'w') as f:
            json.dump(config_data, f)
        
        with open(gpt2_dir / "pytorch_model.bin", 'wb') as f:
            f.write(b'\x00' * 5000)
        
        # Initialize discovery engine
        cache_dir = Path(temp_dir) / "cache"
        discovery_engine = ModelDiscoveryEngine(
            models_root=str(models_dir),
            cache_dir=str(cache_dir)
        )
        
        try:
            # Test discovery
            print("Discovering models...")
            models = await discovery_engine.discover_all_models()
            
            print(f"Found {len(models)} models:")
            for model in models:
                print(f"  - {model.display_name} ({model.type.value}, {model.category.value})")
                print(f"    Path: {model.path}")
                print(f"    Size: {model.size / (1024*1024):.1f} MB")
                print(f"    Modalities: {[m.type.value for m in model.modalities]}")
                print(f"    Tags: {model.tags}")
                print()
            
            # Verify we found expected models
            assert len(models) >= 2, f"Expected at least 2 models, found {len(models)}"
            
            # Check model types
            model_types = {model.type for model in models}
            assert ModelType.LLAMA_CPP in model_types, "Should find llama-cpp model"
            assert ModelType.TRANSFORMERS in model_types, "Should find transformers model"
            
            # Test filtering
            print("Testing model filtering...")
            language_models = discovery_engine.filter_models(category=ModelCategory.LANGUAGE)
            print(f"Language models: {len(language_models)}")
            
            # Test statistics
            print("Testing statistics...")
            stats = discovery_engine.get_discovery_statistics()
            print(f"Statistics: {stats}")
            
            print("✅ All tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            discovery_engine.cleanup()

async def test_metadata_extraction():
    """Test metadata extraction from config files."""
    print("\nTesting metadata extraction...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        models_dir = Path(temp_dir) / "models"
        models_dir.mkdir()
        
        # Create model with detailed config
        model_dir = models_dir / "test_model"
        model_dir.mkdir()
        
        config_data = {
            "model_type": "llama",
            "max_position_embeddings": 2048,
            "architectures": ["LlamaForCausalLM"],
            "license": "Apache 2.0",
            "language": ["en"],
            "task": ["text-generation", "chat"]
        }
        with open(model_dir / "config.json", 'w') as f:
            json.dump(config_data, f)
        
        # Create README with additional info
        readme_content = """# Test Model

This is a test language model for chat applications.

- Parameters: 1.1B
- Quantization: Q4_K_M
- License: Apache 2.0
"""
        with open(model_dir / "README.md", 'w') as f:
            f.write(readme_content)
        
        cache_dir = Path(temp_dir) / "cache"
        discovery_engine = ModelDiscoveryEngine(
            models_root=str(models_dir),
            cache_dir=str(cache_dir)
        )
        
        try:
            # Test metadata extraction
            metadata = await discovery_engine.extract_model_metadata(str(model_dir))
            
            print(f"Extracted metadata:")
            print(f"  Architecture: {metadata.architecture}")
            print(f"  Context length: {metadata.context_length}")
            print(f"  License: {metadata.license}")
            print(f"  Use cases: {metadata.use_cases}")
            print(f"  Language support: {metadata.language_support}")
            
            # Verify metadata
            assert metadata.architecture == "llama", f"Expected 'llama', got '{metadata.architecture}'"
            assert metadata.context_length == 2048, f"Expected 2048, got {metadata.context_length}"
            assert "text-generation" in metadata.use_cases, "Should include text-generation use case"
            
            print("✅ Metadata extraction test passed!")
            return True
            
        except Exception as e:
            print(f"❌ Metadata extraction test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            discovery_engine.cleanup()

async def test_real_models():
    """Test with real models if available."""
    print("\nTesting with real models (if available)...")
    
    models_dir = Path("models")
    if not models_dir.exists():
        print("No real models directory found, skipping real model test")
        return True
    
    discovery_engine = ModelDiscoveryEngine(models_root=str(models_dir))
    
    try:
        models = await discovery_engine.discover_all_models()
        
        print(f"Found {len(models)} real models:")
        for model in models[:5]:  # Show first 5
            print(f"  - {model.display_name}")
            print(f"    Type: {model.type.value}")
            print(f"    Category: {model.category.value}")
            print(f"    Size: {model.size / (1024*1024*1024):.2f} GB")
            print(f"    Status: {model.status.value}")
            print()
        
        if models:
            # Test organization
            organized = await discovery_engine.organize_models_by_category(models)
            print(f"Models by category:")
            for category, model_list in organized.items():
                print(f"  {category}: {len(model_list)} models")
        
        print("✅ Real models test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Real models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        discovery_engine.cleanup()

async def main():
    """Run all tests."""
    print("🔍 Model Discovery Engine Test Suite")
    print("=" * 50)
    
    tests = [
        test_basic_discovery,
        test_metadata_extraction,
        test_real_models
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {i+1}. {test.__name__}: {status}")
    
    passed = sum(results)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)