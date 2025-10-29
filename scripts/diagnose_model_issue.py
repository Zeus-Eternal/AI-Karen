#!/usr/bin/env python3
"""
Diagnose the current model configuration and response quality issues.
"""

import json
import os
from pathlib import Path

def analyze_current_setup():
    """Analyze the current model setup."""
    
    print("=== AI-Karen Model Diagnosis ===\n")
    
    # Check model registry
    registry_path = Path("model_registry.json")
    if registry_path.exists():
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        
        print("📋 Current Models in Registry:")
        for model in registry:
            if model.get("type") == "llama-gguf":
                name = model.get("name", "Unknown")
                path = model.get("path", "Unknown")
                print(f"  • {name}")
                if "tinyllama" in name.lower():
                    print(f"    ⚠️  WARNING: TinyLlama (1.1B params) - TOO SMALL for coherent responses")
                elif "phi-3" in name.lower():
                    print(f"    ✅ Phi-3 - Good for reasoning (3.8B params)")
                elif "llama" in name.lower() and "3.2" in name:
                    print(f"    ✅ Llama 3.2 - Excellent for responses")
                print(f"    Path: {path}")
    else:
        print("❌ No model registry found")
    
    print()
    
    # Check provider configuration
    providers_path = Path("config/providers.json")
    if providers_path.exists():
        with open(providers_path, 'r') as f:
            config = json.load(f)
        
        print("🌐 Cloud Provider Status:")
        cloud_providers = config.get("providers", {}).get("cloud", {})
        
        for provider, settings in cloud_providers.items():
            enabled = settings.get("enabled", False)
            has_key = bool(os.getenv(f"{provider.upper()}_API_KEY"))
            
            status = "✅ ACTIVE" if enabled and has_key else "❌ INACTIVE"
            print(f"  • {provider.title()}: {status}")
            
            if enabled and not has_key:
                print(f"    ⚠️  Enabled but missing API key")
    else:
        print("❌ No provider configuration found")
    
    print()
    
    # Check environment variables
    print("🔧 Environment Configuration:")
    important_vars = [
        "OPENAI_API_KEY",
        "HUGGINGFACE_API_KEY", 
        "MODELS_ROOT",
        "ENABLE_LOCAL_PROVIDERS",
        "ENABLE_CLOUD_PROVIDERS"
    ]
    
    for var in important_vars:
        value = os.getenv(var)
        if value:
            if "API_KEY" in var:
                print(f"  • {var}: {'*' * 8}...{value[-4:] if len(value) > 4 else '****'}")
            else:
                print(f"  • {var}: {value}")
        else:
            print(f"  • {var}: ❌ Not set")
    
    print()
    
    # Provide recommendations
    print("🎯 RECOMMENDATIONS:")
    print()
    
    # Check if using TinyLlama
    using_tinyllama = any(
        "tinyllama" in model.get("name", "").lower() 
        for model in (registry if 'registry' in locals() else [])
        if model.get("type") == "llama-gguf"
    )
    
    if using_tinyllama:
        print("❗ CRITICAL ISSUE: Using TinyLlama (1.1B parameters)")
        print("   This model is too small for coherent responses!")
        print("   Solutions:")
        print("   1. 🚀 BEST: Setup cloud providers (OpenAI/HuggingFace)")
        print("      Run: python setup_cloud_providers.py")
        print("   2. 💾 GOOD: Download better local model")
        print("      Run: python setup_better_model.py")
        print()
    
    # Check cloud providers
    has_cloud = any(
        settings.get("enabled") and os.getenv(f"{provider.upper()}_API_KEY")
        for provider, settings in (cloud_providers.items() if 'cloud_providers' in locals() else [])
    )
    
    if not has_cloud:
        print("🌐 No active cloud providers detected")
        print("   Cloud providers offer the best response quality:")
        print("   • OpenAI GPT-4o-mini: Excellent reasoning")
        print("   • HuggingFace: Free tier available")
        print("   Run: python setup_cloud_providers.py")
        print()
    
    # Model size comparison
    print("📊 Model Comparison:")
    print("   TinyLlama-1.1B:     ❌ Too small (current issue)")
    print("   Phi-3-Mini-3.8B:    ✅ Good for basic tasks")
    print("   Llama-3.2-3B:       ✅ Better reasoning")
    print("   GPT-4o-mini:        🚀 Excellent (cloud)")
    print("   GPT-4o:             🚀 Best quality (cloud)")

def test_current_model():
    """Test the current model with a simple prompt."""
    print("\n🧪 TESTING CURRENT MODEL:")
    print("To test your current setup, try asking:")
    print('   "Explain how variables work in Python"')
    print()
    print("Expected with TinyLlama: Incoherent/random response")
    print("Expected with better model: Clear, structured explanation")

def main():
    analyze_current_setup()
    test_current_model()
    
    print("\n" + "="*50)
    print("QUICK FIX COMMANDS:")
    print("  python setup_cloud_providers.py  # Best option")
    print("  python setup_better_model.py     # Local option")
    print("  ./restart_with_better_model.sh   # After setup")

if __name__ == "__main__":
    main()