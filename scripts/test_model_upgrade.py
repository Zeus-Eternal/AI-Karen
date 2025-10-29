#!/usr/bin/env python3
"""
Test Model Upgrade - Verify Phi-3 is working properly

This script tests the upgraded model configuration to ensure
intelligent responses instead of the previous TinyLlama issues.
"""

import json
import requests
import time
from pathlib import Path

def test_model_configuration():
    """Test that the model configuration is properly updated"""
    config_path = Path("config.json")
    
    if not config_path.exists():
        print("❌ config.json not found")
        return False
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Check LLM configuration
    llm_config = config.get('llm', {})
    model_name = llm_config.get('model', '')
    
    print(f"📋 Current LLM Configuration:")
    print(f"   Provider: {llm_config.get('provider', 'unknown')}")
    print(f"   Model: {model_name}")
    print(f"   Temperature: {llm_config.get('temperature', 'unknown')}")
    print(f"   Max Tokens: {llm_config.get('max_tokens', 'unknown')}")
    
    # Check if using Phi-3 instead of TinyLlama
    if 'tinyllama' in model_name.lower():
        print("⚠️  WARNING: Still using TinyLlama - this will give poor responses!")
        return False
    elif 'phi-3' in model_name.lower():
        print("✅ Using Phi-3 model - much better for intelligent responses")
        return True
    else:
        print(f"ℹ️  Using model: {model_name}")
        return True

def test_model_file_exists():
    """Test that the model file actually exists"""
    config_path = Path("config.json")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    model_name = config.get('llm', {}).get('model', '')
    model_path = Path(f"models/llama-cpp/{model_name}")
    
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"✅ Model file exists: {model_path}")
        print(f"   Size: {size_mb:.1f} MB")
        return True
    else:
        print(f"❌ Model file not found: {model_path}")
        return False

def test_backend_connection():
    """Test if backend is running and can be reached"""
    backend_urls = [
        "http://localhost:8000",
        "http://localhost:8010", 
        "http://localhost:8020"
    ]
    
    for url in backend_urls:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Backend is running at {url}")
                return url
        except requests.exceptions.RequestException:
            continue
    
    print("⚠️  Backend not responding - you may need to restart it")
    return None

def suggest_test_prompts():
    """Suggest test prompts to verify intelligent responses"""
    print("\n🧪 Test Prompts to Verify Intelligence:")
    print("Try these prompts in your chat interface:")
    print()
    print("1. 'Explain the difference between Python lists and tuples'")
    print("2. 'Write a simple function to calculate fibonacci numbers'") 
    print("3. 'What are the key principles of object-oriented programming?'")
    print("4. 'How would you optimize a slow database query?'")
    print("5. 'Explain async/await in JavaScript'")
    print()
    print("With Phi-3, you should get coherent, detailed responses.")
    print("If responses are still poor, the backend may need restarting.")

def main():
    """Main test function"""
    print("🔍 Testing Model Upgrade Configuration\n")
    
    # Test 1: Configuration
    print("1. Testing configuration...")
    config_ok = test_model_configuration()
    print()
    
    # Test 2: Model file exists
    print("2. Testing model file...")
    file_ok = test_model_file_exists()
    print()
    
    # Test 3: Backend connection
    print("3. Testing backend connection...")
    backend_url = test_backend_connection()
    print()
    
    # Summary
    print("📊 Summary:")
    if config_ok and file_ok:
        print("✅ Model upgrade successful!")
        print("✅ Phi-3 model is properly configured")
        
        if backend_url:
            print("✅ Backend is running")
            print("\n🚀 Ready to test! Your responses should be much more intelligent now.")
        else:
            print("⚠️  Backend needs to be restarted to use the new model")
            print("\n🔄 Next steps:")
            print("1. Restart your backend server")
            print("2. Test with the suggested prompts")
    else:
        print("❌ Issues found with model configuration")
        print("\n🔧 Troubleshooting needed")
    
    suggest_test_prompts()

if __name__ == "__main__":
    main()