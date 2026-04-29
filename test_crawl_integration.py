import asyncio
import logging
import sys
import os

# Add src to sys.path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from ai_karen_engine.integrations.web.crawl4ai_integration import Crawl4AIIntegration

async def test_integration():
    logging.basicConfig(level=logging.INFO)
    integration = Crawl4AIIntegration()
    print(f"Integration available: {integration.available}")
    
    if not integration.available:
        print("Crawl4AI not available!")
        return

    # Try a simple fetch
    # result = await integration.fetch_url("https://example.com")
    # print(f"Fetch success: {result['success']}")
    # print(f"Content length: {len(result['markdown'])}")

if __name__ == "__main__":
    asyncio.run(test_integration())
