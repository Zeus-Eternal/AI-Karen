import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv("/app/.env")

logging.basicConfig(level=logging.INFO)

sys.path.append("/app/src")
from ai_karen_engine.integrations.providers.gemini_provider import GeminiProvider

async def main():
    try:
        provider = GeminiProvider()
        print("Testing generate...")
        response = provider.generate_text("Hello, who are you?", model="gemini-2.5-flash")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
