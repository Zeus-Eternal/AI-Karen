#!/usr/bin/env python3
"""
Diagnostic script to test API endpoints and identify issues.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_result(title, result):
    """Print a formatted result."""
    print(f"{title}:")
    print(f"  Status: {result.get('status', 'N/A')}")
    if "error" in result:
        print(f"  Error: {result.get('error', 'N/A')}")
    if "detail" in result:
        print(f"  Detail: {result.get('detail', 'N/A')}")
    print()


def test_endpoint(url, method="GET", headers=None, data=None):
    """Test an endpoint and return the result."""
    headers = headers or {}
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=5)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=5)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=5)
        else:
            return {
                "status": "ERROR",
                "error": f"Unsupported method: {method}",
                "detail": response.text if "response" in locals() else None,
            }

        result = {
            "status": response.status_code,
            "headers": dict(response.headers),
            "elapsed": response.elapsed.total_seconds(),
        }

        # Try to parse JSON, otherwise use text
        try:
            result["detail"] = response.json()
        except (json.JSONDecodeError, ValueError):
            result["detail"] = response.text

        return result
    except requests.exceptions.Timeout:
        return {
            "status": "TIMEOUT",
            "error": "Request timed out",
            "detail": f"Request to {url} exceeded 5 second timeout",
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "CONNECTION_ERROR",
            "error": "Failed to connect to server",
            "detail": f"Could not connect to {BASE_URL}",
        }
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "detail": str(e)}


def main():
    """Main diagnostic function."""
    print_section(f"API Endpoint Diagnostic - {datetime.now().isoformat()}")

    # Test 1: OpenAPI spec to verify routes exist
    print_section("1. Verifying Route Registration (OpenAPI Spec)")
    openapi_url = f"{BASE_URL}/openapi.json"
    result = test_endpoint(openapi_url, "GET")
    print_result(f"GET {openapi_url}", result)

    if result["status"] == 200:
        openapi_data = result["detail"]  # Already a dict, not a string

        # Check for conversation routes
        conversation_routes = [
            "/api/conversations/ensure-session/{session_id}",
            "/api/conversations/by-session/{session_id}",
            "/api/conversations/create",
            "/api/conversations/{conversation_id}",
            "/api/conversations/{conversation_id}/messages",
        ]

        print("Checking conversation routes:")
        for route in conversation_routes:
            if route in openapi_data["paths"]:
                print(f"  ✅ {route}")
            else:
                print(f"  ❌ {route} - NOT FOUND")

        # Check for copilot routes
        copilot_routes = [
            "/api/copilot/assist",
            "/api/copilot/health",
            "/api/copilot/start",
        ]

        print("\nChecking copilot routes:")
        for route in copilot_routes:
            if route in openapi_data["paths"]:
                print(f"  ✅ {route}")
            else:
                print(f"  ❌ {route} - NOT FOUND")

    # Test 2: Test conversation ensure-session endpoint
    print_section("2. Testing /api/conversations/ensure-session/{session_id}")
    session_id = "test-session-123"
    url = f"{BASE_URL}/api/conversations/ensure-session/{session_id}"

    # Test with development headers
    headers = {
        "X-Development-Mode": "true",
        "X-Skip-Auth": "dev",
        "X-Mock-User-ID": "test-user",
    }

    print(f"Testing: {url}")
    print(f"Headers: {headers}")
    result = test_endpoint(url, "POST", headers=headers, data={})
    print_result(f"POST {url}", result)

    # Test 3: Test copilot/assist endpoint
    print_section("3. Testing /api/copilot/assist")
    url = f"{BASE_URL}/api/copilot/assist"
    payload = {
        "user_id": "test-user",
        "message": "Hello, this is a test message",
        "session_id": "test-session-123",
        "stream": False,
    }

    print(f"Testing: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Headers: {headers}")
    result = test_endpoint(url, "POST", headers=headers, data=payload)
    print_result(f"POST {url}", result)

    # Test 4: Test without authentication
    print_section("4. Testing Without Authentication Headers")
    print("Testing endpoints without auth headers to see default behavior:")

    # Test conversation endpoint
    url = f"{BASE_URL}/api/conversations/ensure-session/{session_id}"
    result = test_endpoint(url, "POST", headers={})
    print_result(f"POST {url} (no auth)", result)

    # Test copilot endpoint
    url = f"{BASE_URL}/api/copilot/assist"
    result = test_endpoint(url, "POST", headers={}, data=payload)
    print_result(f"POST {url} (no auth)", result)

    # Test 5: Check service health
    print_section("5. Checking Service Health")
    health_url = f"{BASE_URL}/health"
    result = test_endpoint(health_url, "GET")
    print_result(f"GET {health_url}", result)

    if result["status"] == 200:
        try:
            health_data = json.loads(result["detail"])
            print("Health Status:")
            print(f"  Status: {health_data.get('status', 'N/A')}")
            print(f"  Environment: {health_data.get('environment', 'N/A')}")
            print(f"  Version: {health_data.get('version', 'N/A')}")
        except json.JSONDecodeError:
            pass

    print_section("Diagnostic Complete")
    print("If endpoints return 401/403, authentication is blocking requests.")
    print("If endpoints return 404, routes are not registered correctly.")
    print("If endpoints return 500, service dependencies are failing.")


if __name__ == "__main__":
    main()
