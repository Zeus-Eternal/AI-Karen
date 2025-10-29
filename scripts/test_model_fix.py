#!/usr/bin/env python3
"""
Test script to verify the model fix is working properly.
"""

import asyncio
import json
import time
from pathlib import Path

def test_model_configuration():
    """Test that the model configuration has been updated correctly."""
    print("=== Testing Model Configuration ===\n")
    
    # Check model registry
    registry_path = Path("model_registry.json")
    if registry_path.exists():
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        
        print("📋 Model Registry Status:")
        phi3_found = False
        tinyllama_found = False
        
        for model in registry:
            if isinstance(model, dict) and model.get("name"):
                name = model["name"]
                if "phi-3" in name.lower():
                    phi3_found = True
                    priority = model.get("priority", "unknown")
                    print(f"  ✅ Phi-3 found: {name} (priority: {priority})")
                elif "tinyllama" in name.lower():
                    tinyllama_found = True
                    priority = model.get("priority", "unknown")
                    print(f"  ⚠️  TinyLlama found: {name} (priority: {priority})")
        
        if phi3_found and not tinyllama_found:
            print("  🎯 PERFECT: Only Phi-3 is prioritized")
        elif phi3_found and tinyllama_found:
            print("  ✅ GOOD: Phi-3 is prioritized over TinyLlama")
        else:
            print("  ❌ ISSUE: Phi-3 not found or not prioritized")
    else:
        print("❌ Model registry not found")
    
    print()
    
    # Check TinyLlama config override
    config_path = Path("models/configs/tinyllama.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        model_name = config.get("model_name", "unknown")
        if "phi-3" in model_name.lower():
            print(f"✅ TinyLlama service configured to use: {model_name}")
        else:
            print(f"⚠️  TinyLlama service still using: {model_name}")
    else:
        print("⚠️  TinyLlama config not found - using default")
    
    print()

def test_model_files():
    """Test that the model files exist."""
    print("=== Testing Model Files ===\n")
    
    models_dir = Path("./models/llama-cpp")
    
    # Check for Phi-3
    phi3_path = models_dir / "Phi-3-mini-4k-instruct-q4.gguf"
    if phi3_path.exists():
        size_mb = phi3_path.stat().st_size / (1024 * 1024)
        print(f"✅ Phi-3 model found: {phi3_path} ({size_mb:.1f} MB)")
    else:
        print(f"❌ Phi-3 model not found: {phi3_path}")
    
    # Check for TinyLlama
    tinyllama_path = models_dir / "tinyllama-1.1b-chat-v2.0.Q4_K_M.gguf"
    if tinyllama_path.exists():
        size_mb = tinyllama_path.stat().st_size / (1024 * 1024)
        print(f"⚠️  TinyLlama still present: {tinyllama_path} ({size_mb:.1f} MB)")
    else:
        print(f"✅ TinyLlama removed: {tinyllama_path}")
    
    print()

async def test_model_response():
    """Test the actual model response quality."""
    print("=== Testing Model Response Quality ===\n")
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        from ai_karen_engine.services.tinyllama_service import TinyLlamaService
        
        service = TinyLlamaService()
        
        test_cases = [
            {
                "prompt": "Explain how variables work in Python programming.",
                "expected_keywords": ["variable", "python", "value", "assign"],
                "avoid_keywords": ["blood", "genetics", "allele", "chromosome"]
            },
            {
                "prompt": "What are the benefits of using functions in programming?",
                "expected_keywords": ["function", "code", "reuse", "organize"],
                "avoid_keywords": ["medical", "treatment", "patient", "disease"]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"🧪 Test {i}: {test_case['prompt']}")
            print("-" * 50)
            
            start_time = time.time()
            result = await service.generate_scaffold(
                text=test_case["prompt"],
                scaffold_type="reasoning",
                max_tokens=150
            )
            response_time = (time.time() - start_time) * 1000
            
            print(f"Response ({response_time:.0f}ms):")
            print(result.content)
            print()
            
            # Analyze response quality
            response_lower = result.content.lower()
            
            # Check for expected keywords
            expected_found = sum(1 for keyword in test_case["expected_keywords"] 
                               if keyword in response_lower)
            expected_ratio = expected_found / len(test_case["expected_keywords"])
            
            # Check for unwanted keywords (incoherent responses)
            avoid_found = sum(1 for keyword in test_case["avoid_keywords"] 
                            if keyword in response_lower)
            
            # Quality assessment
            if len(result.content) < 20:
                quality = "❌ TOO SHORT"
            elif avoid_found > 0:
                quality = "❌ INCOHERENT (wrong topic)"
            elif expected_ratio >= 0.5:
                quality = "✅ GOOD (on-topic)"
            elif expected_ratio >= 0.25:
                quality = "⚠️  FAIR (partially on-topic)"
            else:
                quality = "❌ POOR (off-topic)"
            
            print(f"Quality: {quality}")
            print(f"Model: {result.model_name}")
            print(f"Fallback used: {result.used_fallback}")
            print(f"Processing time: {result.processing_time:.3f}s")
            print()
            
    except Exception as e:
        print(f"❌ Error testing model response: {e}")
        print("Make sure the backend is running: python3 start.py")
        print()

def provide_recommendations():
    """Provide recommendations based on test results."""
    print("=== Recommendations ===\n")
    
    print("🎯 IMMEDIATE ACTIONS:")
    print("1. Restart your backend: python3 start.py")
    print("2. Test with a simple question in the UI")
    print("3. Monitor response times and quality")
    print()
    
    print("🚀 FOR EVEN BETTER PERFORMANCE:")
    print("1. Setup cloud providers: python3 setup_cloud_providers.py")
    print("2. Download a larger local model: python3 setup_better_model.py")
    print("3. Configure GPU acceleration if available")
    print()
    
    print("📊 EXPECTED IMPROVEMENTS:")
    print("• Response coherence: Much better (Phi-3 vs TinyLlama)")
    print("• Response time: Similar or slightly slower")
    print("• Degraded mode: Should occur less frequently")
    print("• Overall quality: Significantly improved")

async def main():
    """Run all tests."""
    print("🔧 AI-Karen Model Fix Verification")
    print("=" * 50)
    print()
    
    test_model_configuration()
    test_model_files()
    await test_model_response()
    provide_recommendations()
    
    print("=" * 50)
    print("✅ Model fix verification complete!")

if __name__ == "__main__":
    asyncio.run(main())