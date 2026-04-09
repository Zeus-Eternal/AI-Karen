"""
Fix script for API endpoint issues.
This script will:
1. Check database configuration
2. Verify service health
3. Test endpoints
4. Provide diagnostic information
"""

import os
import sys
import asyncio
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
    if "detail" in result and isinstance(result["detail"], dict):
        # Try to find a user-friendly message
        for key in ["user_message", "message", "detail", "error"]:
            if key in result["detail"]:
                print(f"  Message: {result['detail'][key][:200]}")
                break
    elif isinstance(result["detail"], str) and len(result["detail"]) < 500:
        print(f"  Detail: {result['detail']}")
    print()


def check_database_config():
    """Check database configuration."""
    print_section("1. Checking Database Configuration")

    try:
        with open(".env", "r") as f:
            env_content = f.read()

        # Check for asyncpg driver
        if "asyncpg" in env_content:
            print("  ✅ asyncpg driver found in .env (good for async operations)")
        else:
            print("  ⚠️  asyncpg driver NOT found in .env")
            print("     Recommendation: Use asyncpg for async database operations")

        # Check for database URL
        if "DATABASE_URL" in env_content:
            print("  ✅ DATABASE_URL found in .env")
            # Mask the password
            for line in env_content.split("\n"):
                if "DATABASE_URL" in line:
                    print(f"     {line.split('=')[0]}=*****")
        else:
            print("  ❌ DATABASE_URL NOT found in .env")
            return False

        return True
    except Exception as e:
        print(f"  ❌ Error reading .env file: {e}")
        return False


def check_service_health():
    """Check service health."""
    print_section("2. Checking Service Health")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"  ❌ Health check failed: {response.status_code}")
            print(f"  Detail: {response.text[:200]}")
            return False

        health = response.json()
        print(f"  Overall Status: {health.get('status', 'unknown')}")
        print(f"  Environment: {health.get('environment', 'unknown')}")
        print(f"  Version: {health.get('version', 'unknown')}")

        # Check services
        services = health.get("services", {})
        if isinstance(services, dict):
            print("\n  Service Status:")
            for service_name, service_info in services.items():
                if isinstance(service_info, dict):
                    status = service_info.get("status", "unknown")
                    print(f"    {service_name}: {status}")
                else:
                    print(f"    {service_name}: {service_info}")

        return response.status_code == 200
    except Exception as e:
        print(f"  ❌ Error checking health: {e}")
        return False


def test_conversation_endpoint():
    """Test conversation ensure-session endpoint."""
    print_section("3. Testing /api/conversations/ensure-session")

    headers = {
        "X-Development-Mode": "true",
        "X-Skip-Auth": "dev",
        "X-Mock-User-ID": "test-user",
    }

    response = requests.post(
        f"{BASE_URL}/api/conversations/ensure-session/test-session-{datetime.now().timestamp()}",
        headers=headers,
        timeout=5,
    )

    print_result(
        f"POST /api/conversations/ensure-session",
        {"status": response.status_code, "detail": response.text},
    )

    return response.status_code


def test_copilot_endpoint():
    """Test copilot assist endpoint."""
    print_section("4. Testing /api/copilot/assist")

    headers = {
        "X-Development-Mode": "true",
        "X-Skip-Auth": "dev",
        "X-Mock-User-ID": "test-user",
    }

    payload = {
        "user_id": "test-user",
        "message": "Hello, this is a test message",
        "top_k": 6,
        "stream": False,
        "context": {},
    }

    response = requests.post(
        f"{BASE_URL}/api/copilot/assist", json=payload, headers=headers, timeout=5
    )

    print_result(
        f"POST /api/copilot/assist",
        {"status": response.status_code, "detail": response.text},
    )

    return response.status_code


def check_recent_logs():
    """Check recent server logs for errors."""
    print_section("5. Checking Recent Server Logs")

    try:
        # Check server log for errors
        log_file = Path("server.log")
        if log_file.exists():
            with open(log_file, "r") as f:
                # Get last 100 lines
                lines = f.readlines()
                recent_lines = lines[-100:]

            print("  Recent log entries (last 100 lines):")
            for line in recent_lines[-20:]:  # Show last 20 lines
                if (
                    "error" in line.lower()
                    or "exception" in line.lower()
                    or "failed" in line.lower()
                ):
                    print(f"    {line.strip()}")
            print("    ...")
        else:
            print("  ❌ server.log not found")
    except Exception as e:
        print(f"  ❌ Error reading server.log: {e}")


def verify_routes():
    """Verify routes are registered."""
    print_section("6. Verifying Route Registration")

    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code != 200:
            print(f"  ❌ Failed to get OpenAPI spec: {response.status_code}")
            return False

        openapi = response.json()
        paths = openapi.get("paths", {})

        routes = [
            "/api/conversations/ensure-session/{session_id}",
            "/api/conversations/create",
            "/api/conversations/{conversation_id}",
            "/api/copilot/assist",
            "/api/copilot/health",
            "/api/copilot/start",
        ]

        all_found = True
        print("  Checking routes:")
        for route in routes:
            if route in paths:
                print(f"    ✅ {route}")
            else:
                print(f"    ❌ {route} - NOT FOUND")
                all_found = False

        return all_found
    except Exception as e:
        print(f"  ❌ Error verifying routes: {e}")
        return False


def main():
    """Main fix diagnostic function."""
    print_section(f"API Endpoint Fix Diagnostic - {datetime.now().isoformat()}")

    results = {}

    # Run all checks
    results["database_config"] = check_database_config()
    results["service_health"] = check_service_health()
    results["routes_registered"] = verify_routes()
    results["conversation_status"] = test_conversation_endpoint()
    results["copilot_status"] = test_copilot_endpoint()
    results["recent_logs"] = check_recent_logs()

    # Summary
    print_section("Diagnostic Summary")

    print("Database Configuration:")
    print(
        f"  {'✅ PASS' if results['database_config'] else '❌ FAIL'} - {'Configured' if results['database_config'] else 'Not configured'}"
    )

    print("\nService Health:")
    print(
        f"  {'✅ PASS' if results['service_health'] else '❌ FAIL'} - {'Healthy' if results['service_health'] else 'Not healthy'}"
    )

    print("\nRoute Registration:")
    print(
        f"  {'✅ PASS' if results['routes_registered'] else '❌ FAIL'} - {'Routes registered' if results['routes_registered'] else 'Routes not registered'}"
    )

    print("\nConversation Endpoint:")
    print(
        f"  {'✅ PASS' if results['conversation_status'] in [200, 201] else '⚠️  WARN'} - {results['conversation_status']}"
    )

    print("\nCopilot Endpoint:")
    if results["copilot_status"] in [200, 201]:
        print(f"  ✅ PASS - {results['copilot_status']}")
    elif results["copilot_status"] == 503:
        print(
            f"  ❌ FAIL - {results['copilot_status']} (Greenlet error - database async issue)"
        )
    else:
        print(f"  ⚠️  WARN - {results['copilot_status']}")

    print("\n" + "=" * 80)
    print("Recommendations:")
    print("=" * 80)

    if not results["database_config"]:
        print("\n1. Fix database configuration:")
        print("   - Add DATABASE_URL with asyncpg driver to .env")
        print(
            "   - Example: DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname"
        )

    if results["copilot_status"] == 503:
        print("\n2. Fix greenlet error:")
        print("   - Ensure database uses asyncpg driver")
        print("   - Check ChatOrchestrator initialization in dependencies.py")
        print("   - Verify all database operations use async context managers")
        print("   - Review server logs for detailed error information")

    if not results["routes_registered"]:
        print("\n3. Fix route registration:")
        print("   - Check server/routers.py for proper router mounting")
        print("   - Verify both conversation_router and copilot_router are imported")

    print("\n4. Fix frontend authentication:")
    print(
        "   - Ensure frontend sends X-Development-Mode, X-Skip-Auth, X-Mock-User-ID headers"
    )
    print("   - Or use production authentication tokens")

    print("\n" + "=" * 80)
    print("Diagnostic complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
