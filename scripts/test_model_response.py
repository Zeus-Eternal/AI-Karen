#!/usr/bin/env python3
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
        print("\n" + "="*50)
        
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
