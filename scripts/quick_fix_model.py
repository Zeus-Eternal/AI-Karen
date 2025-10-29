#!/usr/bin/env python3
"""
Quick fix to switch from TinyLlama to Phi-3 for better responses.
"""

import json
from pathlib import Path

def switch_to_phi3():
    """Switch the system to use Phi-3 instead of TinyLlama."""
    
    print("🔧 Switching from TinyLlama to Phi-3...")
    
    # Update TinyLlama service config to use Phi-3
    config_dir = Path("models/configs")
    config_dir.mkdir(parents=True, exist_ok=True)
    
    phi3_config = {
        "model_name": "Phi-3-mini-4k-instruct-q4.gguf",
        "model_path": "./models/llama-cpp/Phi-3-mini-4k-instruct-q4.gguf",
        "max_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.9,
        "enable_fallback": True,
        "cache_enabled": True,
        "context_length": 4096
    }
    
    with open(config_dir / "tinyllama.json", 'w') as f:
        json.dump(phi3_config, f, indent=2)
    
    print("✅ Updated TinyLlama service to use Phi-3")
    
    # Update environment variables
    env_path = Path(".env")
    if env_path.exists():
        env_content = env_path.read_text()
        
        # Add missing model configuration
        new_lines = []
        if "MODELS_ROOT=" not in env_content:
            new_lines.append("MODELS_ROOT=./models")
        if "ENABLE_LOCAL_PROVIDERS=" not in env_content:
            new_lines.append("ENABLE_LOCAL_PROVIDERS=true")
        if "ENABLE_CLOUD_PROVIDERS=" not in env_content:
            new_lines.append("ENABLE_CLOUD_PROVIDERS=true")
        
        if new_lines:
            env_content += "\n" + "\n".join(new_lines)
            env_path.write_text(env_content)
            print("✅ Updated environment configuration")
    
    # Create a simple test script
    with open("test_model_response.py", 'w') as f:
        f.write('''#!/usr/bin/env python3
"""Test the model response quality."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_model():
    """Test the current model with a simple question."""
    try:
        from ai_karen_engine.services.tinyllama_service import TinyLlamaService
        
        service = TinyLlamaService()
        
        test_prompt = "Explain how variables work in Python programming."
        
        print("🧪 Testing model response...")
        print(f"Question: {test_prompt}")
        print("\\n" + "="*50)
        
        response = await service.generate_scaffold(
            text=test_prompt,
            scaffold_type="reasoning",
            max_tokens=200
        )
        
        print("Response:")
        print(response)
        print("="*50)
        
        # Analyze response quality
        if len(response) < 50:
            print("❌ Response too short - possible model issue")
        elif any(word in response.lower() for word in ["blood", "genetics", "allele"]):
            print("❌ Response is incoherent - model mixing up topics")
        elif "variable" in response.lower() and "python" in response.lower():
            print("✅ Response looks coherent and on-topic!")
        else:
            print("⚠️  Response quality unclear - please review manually")
            
    except Exception as e:
        print(f"❌ Error testing model: {e}")
        print("Make sure the backend is running: python start.py")

if __name__ == "__main__":
    asyncio.run(test_model())
''')
    
    print("✅ Created test script")
    
    print("\n🎯 QUICK FIX COMPLETE!")
    print("\nNext steps:")
    print("1. Restart the backend: python3 start.py")
    print("2. Test the fix: python3 test_model_response.py")
    print("3. If still having issues, run: python3 setup_cloud_providers.py")

if __name__ == "__main__":
    switch_to_phi3()