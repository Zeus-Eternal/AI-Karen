#!/usr/bin/env python3
"""
Verify Model Setup for AI-Karen

Checks:
1. Virtual environment (.env_karen)
2. Model directory structure
3. Downloaded models in correct locations
4. Environment variables
"""

import os
import sys
from pathlib import Path
import json

def check_virtual_environment():
    """Check if we're using the correct virtual environment"""
    print("🔍 Checking virtual environment...")
    
    venv_path = Path(".env_karen")
    if not venv_path.exists():
        print("❌ .env_karen virtual environment not found!")
        return False
    
    # Check if we're using the correct Python
    current_python = Path(sys.executable)
    expected_python = venv_path / "bin" / "python"
    
    if expected_python.exists():
        print(f"✅ .env_karen virtual environment found")
        print(f"📍 Current Python: {current_python}")
        print(f"📍 Expected Python: {expected_python}")
        
        if str(current_python).startswith(str(venv_path.absolute())):
            print("✅ Using correct virtual environment")
            return True
        else:
            print("⚠️ Not using .env_karen virtual environment")
            print("💡 Run: source .env_karen/bin/activate")
            return False
    else:
        print("❌ .env_karen/bin/python not found!")
        return False

def check_model_directories():
    """Check model directory structure"""
    print("\n🔍 Checking model directories...")
    
    expected_dirs = [
        "models",
        "models/transformers",
        "models/llama-cpp",
        "models/stable-diffusion",
        "models/downloads",
        "models/metadata_cache"
    ]
    
    all_good = True
    for dir_path in expected_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - missing")
            all_good = False
    
    return all_good

def check_transformers_models():
    """Check transformers models in correct location"""
    print("\n🔍 Checking transformers models...")
    
    transformers_dir = Path("models/transformers")
    if not transformers_dir.exists():
        print("❌ models/transformers directory not found!")
        return False
    
    # List all subdirectories (models)
    models = [d for d in transformers_dir.iterdir() if d.is_dir()]
    
    if not models:
        print("⚠️ No transformers models found in models/transformers/")
        return False
    
    print(f"✅ Found {len(models)} transformers models:")
    for model in models:
        # Check if model has essential files
        config_file = model / "config.json"
        if config_file.exists():
            print(f"  ✅ {model.name} (with config)")
        else:
            print(f"  ⚠️ {model.name} (no config.json)")
    
    return True

def check_environment_variables():
    """Check relevant environment variables"""
    print("\n🔍 Checking environment variables...")
    
    important_vars = [
        "HUGGINGFACE_CACHE_DIR",
        "LLAMACPP_MODELS_PATH",
        "MODELS_ROOT",
        "MODEL_REGISTRY_PATH"
    ]
    
    for var in important_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}={value}")
        else:
            print(f"⚠️ {var} not set")

def check_model_registry():
    """Check model registry file"""
    print("\n🔍 Checking model registry...")
    
    registry_path = Path("model_registry.json")
    if not registry_path.exists():
        print("⚠️ model_registry.json not found")
        return False
    
    try:
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        
        print(f"✅ Model registry found with {len(registry)} entries")
        
        # Show model types
        types = {}
        for model in registry:
            model_type = model.get('type', 'unknown')
            types[model_type] = types.get(model_type, 0) + 1
        
        for model_type, count in types.items():
            print(f"  📊 {model_type}: {count} models")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading model registry: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 AI-Karen Model Setup Verification")
    print("=" * 50)
    
    checks = [
        ("Virtual Environment", check_virtual_environment),
        ("Model Directories", check_model_directories),
        ("Transformers Models", check_transformers_models),
        ("Environment Variables", check_environment_variables),
        ("Model Registry", check_model_registry)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
        if result:
            passed += 1
    
    print(f"\n📊 {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("🎉 All checks passed! Your model setup looks good.")
    else:
        print("⚠️ Some issues found. Please address them before proceeding.")
        print("\n💡 Common fixes:")
        print("1. Activate .env_karen: source .env_karen/bin/activate")
        print("2. Run download script: python download_essential_models.py")
        print("3. Check .env file for correct paths")

if __name__ == "__main__":
    main()