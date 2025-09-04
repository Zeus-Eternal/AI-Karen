#!/usr/bin/env python3
"""
Direct test of LLM functionality without API authentication
"""

import sys
import os
sys.path.append('src')

from ai_karen_engine.integrations.providers.huggingface_provider import HuggingFaceProvider
import asyncio

async def test_huggingface_provider():
    """Test HuggingFace provider directly"""
    print("🧪 Testing HuggingFace provider directly...")
    
    try:
        # Initialize provider
        provider = HuggingFaceProvider()
        
        # Test simple completion
        messages = [{"role": "user", "content": "Hello, what is 2+2?"}]
        
        print("📤 Sending request to HuggingFace provider...")
        response = await provider.complete(
            messages=messages,
            model="gpt2",
            max_tokens=50,
            temperature=0.7
        )
        
        print("✅ Response received:")
        print(f"Content: {response.get('content', 'No content')}")
        print(f"Model: {response.get('model', 'Unknown')}")
        print(f"Tokens: {response.get('usage', {}).get('total_tokens', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing HuggingFace provider: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_huggingface_provider())
    if result:
        print("\n🎉 LLM provider test successful! The issue was just authentication.")
        print("Your models are working properly - you just need to bypass auth or get a token.")
    else:
        print("\n💥 LLM provider test failed - there may be a deeper issue.")