#!/usr/bin/env python3
"""
Verify Model Locations

Checks that all models are in their correct directories:
- Transformers models in models/transformers/
- GGUF models in models/llama-cpp/
- Stable Diffusion models in models/stable-diffusion/
"""

import os
import json
from pathlib import Path

def check_transformers_models():
    """Check transformers models are in correct location"""
    transformers_dir = Path("./models/transformers")
    
    if not transformers_dir.exists():
        print("❌ models/transformers/ directory does not exist")
        return False
    
    models = list(transformers_dir.iterdir())
    if not models:
        print("⚠️ No models found in models/transformers/")
        return True
    
    print(f"✅ Found {len(models)} transformers models:")
    for model in models:
        if model.is_dir():
            # Check for key transformers files
            has_config = (model / "config.json").exists()
            has_tokenizer = (model / "tokenizer.json").exists() or (model / "tokenizer_config.json").exists()
            has_model = any((model / f).exists() for f in ["pytorch_model.bin", "model.safetensors", "tf_model.h5"])
            
            status = "✅" if (has_config and (has_tokenizer or has_model)) else "⚠️"
            print(f"  {status} {model.name}")
            
            if not (has_config and (has_tokenizer or has_model)):
                print(f"    Missing: config={has_config}, tokenizer={has_tokenizer}, model={has_model}")
    
    return True

def check_gguf_models():
    """Check GGUF models are in correct location"""
    gguf_dir = Path("./models/llama-cpp")
    
    if not gguf_dir.exists():
        print("❌ models/llama-cpp/ directory does not exist")
        return False
    
    gguf_files = list(gguf_dir.glob("*.gguf"))
    if not gguf_files:
        print("⚠️ No GGUF models found in models/llama-cpp/")
        return True
    
    print(f"✅ Found {len(gguf_files)} GGUF models:")
    for model in gguf_files:
        size_mb = model.stat().st_size / (1024 * 1024)
        print(f"  ✅ {model.name} ({size_mb:.1f} MB)")
    
    return True

def check_stable_diffusion_models():
    """Check Stable Diffusion models are in correct location"""
    sd_dir = Path("./models/stable-diffusion")
    
    if not sd_dir.exists():
        print("⚠️ models/stable-diffusion/ directory does not exist (optional)")
        return True
    
    models = list(sd_dir.iterdir())
    if not models:
        print("⚠️ No Stable Diffusion models found in models/stable-diffusion/")
        return True
    
    print(f"✅ Found {len(models)} Stable Diffusion models:")
    for model in models:
        if model.is_dir():
            print(f"  ✅ {model.name}")
    
    return True

def check_misplaced_models():
    """Check for models in wrong locations"""
    models_root = Path("./models")
    expected_dirs = {"transformers", "llama-cpp", "stable-diffusion", "downloads", "configs", "metadata_cache", "basic_cls"}
    
    misplaced = []
    for item in models_root.iterdir():
        if item.is_dir() and item.name not in expected_dirs:
            # Check if this looks like a transformers model
            if any((item / file).exists() for file in ["config.json", "tokenizer.json", "pytorch_model.bin", "model.safetensors"]):
                misplaced.append(item.name)
    
    if misplaced:
        print(f"❌ Found {len(misplaced)} misplaced transformers models:")
        for model in misplaced:
            print(f"  ❌ {model} (should be in models/transformers/)")
        print("\n💡 Run download_essential_models.py to fix these automatically")
        return False
    
    return True

def main():
    """Main verification function"""
    print("🔍 Verifying model locations...\n")
    
    all_good = True
    
    print("1. Checking transformers models...")
    all_good &= check_transformers_models()
    
    print("\n2. Checking GGUF models...")
    all_good &= check_gguf_models()
    
    print("\n3. Checking Stable Diffusion models...")
    all_good &= check_stable_diffusion_models()
    
    print("\n4. Checking for misplaced models...")
    all_good &= check_misplaced_models()
    
    print("\n" + "="*50)
    if all_good:
        print("✅ All models are in their correct locations!")
    else:
        print("❌ Some models need to be reorganized")
        print("💡 Run download_essential_models.py to fix automatically")
    
    print("\n📁 Expected directory structure:")
    print("  models/")
    print("  ├── transformers/          # All HuggingFace transformers models")
    print("  ├── llama-cpp/             # GGUF models for llama.cpp")
    print("  ├── stable-diffusion/      # Stable Diffusion models")
    print("  ├── downloads/             # Temporary downloads")
    print("  └── configs/               # Model configurations")

if __name__ == "__main__":
    main()