#!/usr/bin/env python3
"""
Test script to verify authentication system connectivity and CORS configuration
"""

import json
import sys
from typing import Any, Dict

import requests


def test_cors_preflight(url: str, origin: str) -> Dict[str, Any]:
    """Test CORS preflight request"""
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,Authorization",
    }

    try:
        response = requests.options(url, headers=headers, timeout=5)
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "error": None,
        }
    except Exception as e:
        return {"success": False, "status_code": None, "headers": {}, "error": str(e)}


def test_health_endpoint(base_url: str) -> Dict[str, Any]:
    """Test health endpoint"""
    url = f"{base_url}/health"
    try:
        response = requests.get(url, timeout=5)
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "data": response.json()
            if response.headers.get("content-type", "").startswith("application/json")
            else response.text,
            "error": None,
        }
    except Exception as e:
        return {"success": False, "status_code": None, "data": None, "error": str(e)}


def test_auth_endpoints(base_url: str, origin: str) -> Dict[str, Any]:
    """Test authentication endpoints"""
    results = {}

    # Test auth endpoints
    auth_endpoints = ["/api/auth/login", "/api/auth/register", "/api/auth/me"]

    for endpoint in auth_endpoints:
        url = f"{base_url}{endpoint}"

        # Test CORS preflight
        cors_result = test_cors_preflight(url, origin)

        results[endpoint] = {"cors_preflight": cors_result, "endpoint_url": url}

    return results


def main():
    """Main test function"""
    print("🔍 Testing Authentication System Connectivity")
    print("=" * 60)

    # Test configurations
    backend_urls = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://10.105.235.209:8000",
    ]

    frontend_origins = [
        "http://localhost:9002",
        "http://127.0.0.1:9002",
        "http://10.105.235.209:9002",
    ]

    all_tests_passed = True

    for backend_url in backend_urls:
        print(f"\n🌐 Testing Backend: {backend_url}")
        print("-" * 40)

        # Test health endpoint
        health_result = test_health_endpoint(backend_url)
        print(f"Health Check: {'✅ PASS' if health_result['success'] else '❌ FAIL'}")
        if not health_result["success"]:
            print(f"  Error: {health_result['error']}")
            all_tests_passed = False
            continue

        # Test CORS for each origin
        for origin in frontend_origins:
            print(f"\n  🔗 Testing CORS from origin: {origin}")

            auth_results = test_auth_endpoints(backend_url, origin)

            for endpoint, result in auth_results.items():
                cors_success = result["cors_preflight"]["success"]
                print(f"    {endpoint}: {'✅ PASS' if cors_success else '❌ FAIL'}")

                if not cors_success:
                    print(f"      Status: {result['cors_preflight']['status_code']}")
                    print(f"      Error: {result['cors_preflight']['error']}")
                    all_tests_passed = False

    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 All connectivity tests PASSED! Authentication system is ready.")
    else:
        print("⚠️  Some tests FAILED. Check the errors above.")

    print("\n📋 Next Steps:")
    print("1. If tests passed: Try accessing the web UI and test authentication")
    print("2. If tests failed: Check server logs and CORS configuration")
    print("3. Restart the backend server to apply new CORS settings")

    return 0 if all_tests_passed else 1


if __name__ == "__main__":
    sys.exit(main())
