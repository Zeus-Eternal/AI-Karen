#!/usr/bin/env python3
"""
Test script to verify the API endpoint for plugin discovery.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_api_endpoint():
    """Test the /api/extensions/list endpoint."""
    try:
        from ai_karen_engine.api_routes.extensions.extensions import list_extensions

        print("Testing /api/extensions/list endpoint...")

        # Call the endpoint function directly
        result = await list_extensions()

        print(f"API Result: {result}")

        if isinstance(result, list):
            print(f"Found {len(result)} extensions:")
            for ext in result:
                print(
                    f"  - {ext.get('name', 'Unknown')}: {ext.get('display_name', 'Unknown')} v{ext.get('version', 'Unknown')}"
                )
                print(f"    Status: {ext.get('status', 'Unknown')}")
                print(f"    Description: {ext.get('description', 'No description')}")
                print()

            return len(result) > 0
        else:
            print("ERROR: API did not return a list")
            return False

    except Exception as e:
        print(f"ERROR testing API endpoint: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    print("Testing API endpoint for plugin discovery...")

    # Test API endpoint
    api_ok = await test_api_endpoint()

    # Summary
    print("\n=== Test Summary ===")
    print(f"API endpoint: {'PASS' if api_ok else 'FAIL'}")

    if api_ok:
        print("\nSUCCESS: Plugin discovery API is working!")
        return 0
    else:
        print("\nERROR: Plugin discovery API may not be working properly.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
