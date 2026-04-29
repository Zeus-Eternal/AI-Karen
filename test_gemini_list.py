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
        print(f"Discovered models: {[m for m in provider.discovered_models if 'flash' in m]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
