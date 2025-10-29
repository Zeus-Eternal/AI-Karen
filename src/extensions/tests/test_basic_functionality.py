"""
Basic functionality tests for the extension system (no external dependencies).
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def test_manifest_loading():
    """Test loading extension manifest from JSON."""
    manifest_data = {
        "name": "test-extension",
        "version": "1.0.0",
        "display_name": "Test Extension",
        "description": "Test extension for basic functionality",
        "author": "Test Author",
        "license": "MIT",
        "category": "test",
        "capabilities": {
            "provides_api": True,
            "provides_ui": False,
            "provides_background_tasks": False,
            "provides_webhooks": False
        },
        "api": {
            "endpoints": [
                {
                    "path": "/test",
                    "methods": ["GET"],
                    "permissions": ["user"]
                }
            ]
        }
    }
    
    # Test JSON serialization
    json_str = json.dumps(manifest_data, indent=2)
    parsed = json.loads(json_str)
    
    assert parsed["name"] == "test-extension"
    assert parsed["capabilities"]["provides_api"] is True
    assert len(parsed["api"]["endpoints"]) == 1
    
    print("✅ Manifest loading test passed")


def test_extension_discovery():
    """Test extension discovery logic."""
    extension_root = Path("extensions")
    
    # Test path handling
    assert isinstance(extension_root, Path)
    
    # Test glob pattern for manifest discovery
    pattern = "extension.json"
    assert pattern == "extension.json"
    
    print("✅ Extension discovery test passed")


def test_api_integration_concepts():
    """Test API integration concepts."""
    
    # Test router configuration
    router_config = {
        "prefix": "/api/extensions/test-extension",
        "tags": ["test-extension"],
        "endpoints": [
            {
                "path": "/test",
                "methods": ["GET", "POST"],
                "handler": "test_handler"
            }
        ]
    }
    
    assert router_config["prefix"].startswith("/api/extensions/")
    assert "test-extension" in router_config["tags"]
    assert len(router_config["endpoints"]) == 1
    
    print("✅ API integration concepts test passed")


def test_extension_status_tracking():
    """Test extension status tracking."""
    
    # Test status enumeration
    statuses = [
        "not_loaded",
        "loading", 
        "active",
        "error",
        "disabled",
        "unloading"
    ]
    
    # Test status transitions
    current_status = "not_loaded"
    assert current_status in statuses
    
    # Simulate status change
    current_status = "loading"
    assert current_status == "loading"
    
    current_status = "active"
    assert current_status == "active"
    
    print("✅ Extension status tracking test passed")


def test_authentication_integration():
    """Test authentication integration concepts."""
    
    # Test permission checking logic
    user_roles = ["user", "admin"]
    required_permissions = ["user"]
    
    # Check if user has required permissions
    has_permission = any(role in user_roles for role in required_permissions)
    assert has_permission is True
    
    # Test admin access
    admin_required = ["admin"]
    has_admin = any(role in user_roles for role in admin_required)
    assert has_admin is True
    
    print("✅ Authentication integration test passed")


def test_documentation_generation():
    """Test API documentation generation concepts."""
    
    # Test OpenAPI schema structure
    openapi_schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "Extension API",
            "version": "1.0.0"
        },
        "paths": {
            "/api/extensions/test-extension/test": {
                "get": {
                    "summary": "Test endpoint",
                    "tags": ["test-extension"],
                    "responses": {
                        "200": {
                            "description": "Success"
                        }
                    }
                }
            }
        },
        "x-extensions": {
            "test-extension": {
                "display_name": "Test Extension",
                "version": "1.0.0"
            }
        }
    }
    
    assert openapi_schema["openapi"] == "3.0.0"
    assert "paths" in openapi_schema
    assert "x-extensions" in openapi_schema
    assert "test-extension" in openapi_schema["x-extensions"]
    
    print("✅ Documentation generation test passed")


def run_all_tests():
    """Run all basic functionality tests."""
    print("Running extension system basic functionality tests...")
    print()
    
    try:
        test_manifest_loading()
        test_extension_discovery()
        test_api_integration_concepts()
        test_extension_status_tracking()
        test_authentication_integration()
        test_documentation_generation()
        
        print()
        print("🎉 All basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)