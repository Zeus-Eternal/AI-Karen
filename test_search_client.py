
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.curdir))
sys.path.insert(0, os.path.join(os.path.abspath(os.curdir), "src"))

# Mock logging
logging.basicConfig(level=logging.DEBUG)

import importlib.util
from pathlib import Path

def load_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load the search_client module
search_client_path = os.path.join(os.path.abspath(os.curdir), "src/ai_karen_engine/extensions/plugins/intelligent-search/search_client.py")
search_client_module = load_module_from_path("intelligent_search_client", search_client_path)
WebSearchClient = search_client_module.WebSearchClient

async def test_duckduckgo():
    print("Testing DuckDuckGo search...")
    client = WebSearchClient()
    async with client:
        response = await client.search("latest news", max_results=5)
        print(f"Query: {response.query}")
        print(f"Provider: {response.provider}")
        print(f"Error: {response.error}")
        print(f"Results found: {len(response.results)}")
        
        for i, result in enumerate(response.results):
            print(f"[{i+1}] {result.title}")
            print(f"    URL: {result.url}")
            print(f"    Snippet: {result.snippet[:100]}...")

if __name__ == "__main__":
    asyncio.run(test_duckduckgo())
