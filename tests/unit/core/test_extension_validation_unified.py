#!/usr/bin/env python3
"""
Test script to validate the updated extension validation system with unified patterns.
Tests the consolidated extension validation logic and new API endpoint compatibility.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.extensions.validator import ExtensionValidator, ValidationError
from ai_karen_engine.extensions.models import ExtensionManifest


def create_test_manifest(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a basic test manifest with optional overrides."""
    base_manifest = {
        "name": "test-extension",
        "version": "1.0.0",
        "display_name": "Test Extension",
        "description": "A test extension for validation testing",
        "author": "Test Author",
        "license": "MIT",
        "category": "development",
        "tags": ["test", "validation"],
        "api_version": "1.0",
        "kari_min_version": "0.4.0",
        "capabilities": {
            "provides_ui": False,
            "provides_api": True,
            "provides_background_tasks": False,
            "provides_webhooks": False
        },
        "dependencies": {
            "plugins": [],
            "extensions": [],
            "system_services": []
        },
        "permissions": {
            "data_access": [],
            "plugin_access": [],
            "system_access": [],
            "network_access": []
        },
        "resources": {
            "max_memory_mb": 256,
            "max_cpu_percent": 10,
            "max_disk_mb": 100,
            "enforcement_action": "default"
        },
        "ui": {
            "control_room_pages": []
        },
        "api": {
            "endpoints": []
        },
        "background_tasks": [],
        "marketplace": {
            "price": "free",
            "support_url": None,
            "documentation_url": None,
            "screenshots": []
        }
    }
    
    if overrides:
        base_manifest.update(overrides)
    
    return base_manifest


def test_basic_validation():
    """Test basic manifest validation."""
    print("Testing basic manifest validation...")
    
    validator = ExtensionValidator()
    manifest_data = create_test_manifest()
    
    try:
        is_valid, errors, warnings, field_errors = validator.validate_manifest_enhanced(manifest_data)
        
        if is_valid:
            print("✅ Basic validation passed")
            return True
        else:
            print(f"❌ Basic validation failed: {errors}")
            return False
            
    except Exception as e:
        print(f"❌ Basic validation error: {e}")
        return False


def test_unified_api_endpoint_validation():
    """Test validation of unified API endpoints."""
    print("Testing unified API endpoint validation...")
    
    validator = ExtensionValidator()
    
    # Test with unified endpoints
    manifest_data = create_test_manifest({
        "api": {
            "endpoints": [
                {
                    "path": "/copilot/assist",
                    "methods": ["POST"]
                },
                {
                    "path": "/memory/search", 
                    "methods": ["POST"]
                }
            ]
        },
        "permissions": {
            "data_access": ["memory:read"],
            "system_access": ["chat:write"],
            "plugin_access": [],
            "network_access": []
        }
    })
    
    try:
        is_valid, errors, warnings, field_errors = validator.validate_manifest_enhanced(manifest_data)
        
        # Should be valid but may have warnings about RBAC scopes
        if is_valid:
            print("✅ Unified API endpoint validation passed")
            if warnings:
                print(f"   Warnings: {warnings}")
            return True
        else:
            print(f"❌ Unified API endpoint validation failed: {errors}")
            return False
            
    except Exception as e:
        print(f"❌ Unified API endpoint validation error: {e}")
        return False


def test_legacy_endpoint_detection():
    """Test detection of legacy API endpoints."""
    print("Testing legacy endpoint detection...")
    
    validator = ExtensionValidator()
    
    # Test with legacy endpoints
    manifest_data = create_test_manifest({
        "api": {
            "endpoints": [
                {
                    "path": "/ag_ui/memory/query",
                    "methods": ["POST"]
                },
                {
                    "path": "/memory_ag_ui/commit",
                    "methods": ["POST"]
                }
            ]
        }
    })
    
    try:
        is_valid, errors, warnings, field_errors = validator.validate_manifest_enhanced(manifest_data)
        
        # Should be valid but have warnings about legacy endpoints
        legacy_warnings = [w for w in warnings if "legacy" in w.lower()]
        
        if is_valid and legacy_warnings:
            print("✅ Legacy endpoint detection passed")
            print(f"   Detected legacy warnings: {len(legacy_warnings)}")
            return True
        else:
            print(f"❌ Legacy endpoint detection failed - expected warnings about legacy endpoints")
            print(f"   Warnings: {warnings}")
            return False
            
    except Exception as e:
        print(f"❌ Legacy endpoint detection error: {e}")
        return False


def test_rbac_scope_validation():
    """Test RBAC scope validation."""
    print("Testing RBAC scope validation...")
    
    validator = ExtensionValidator()
    
    # Test extension with memory access but missing scopes
    manifest_data = create_test_manifest({
        "api": {
            "endpoints": [
                {
                    "path": "/memory/search",
                    "methods": ["POST"]
                }
            ]
        },
        "permissions": {
            "data_access": ["read", "write"],  # Missing memory:read, memory:write
            "system_access": [],
            "plugin_access": [],
            "network_access": []
        }
    })
    
    try:
        is_valid, errors, warnings, field_errors = validator.validate_manifest_enhanced(manifest_data)
        
        # Should have warnings about missing RBAC scopes
        scope_warnings = [w for w in warnings if "scope" in w.lower()]
        
        if scope_warnings:
            print("✅ RBAC scope validation passed")
            print(f"   Detected scope warnings: {len(scope_warnings)}")
            return True
        else:
            print(f"❌ RBAC scope validation failed - expected warnings about missing scopes")
            print(f"   Warnings: {warnings}")
            return False
            
    except Exception as e:
        print(f"❌ RBAC scope validation error: {e}")
        return False


def test_tenant_isolation_validation():
    """Test tenant isolation validation."""
    print("Testing tenant isolation validation...")
    
    validator = ExtensionValidator()
    
    # Test extension with data access and database dependencies
    manifest_data = create_test_manifest({
        "permissions": {
            "data_access": ["read", "write", "admin"],
            "system_access": [],
            "plugin_access": [],
            "network_access": []
        },
        "dependencies": {
            "plugins": [],
            "extensions": [],
            "system_services": ["postgres", "milvus"]
        }
    })
    
    try:
        is_valid, errors, warnings, field_errors = validator.validate_manifest_enhanced(manifest_data)
        
        # Should have warnings about tenant isolation
        tenant_warnings = [w for w in warnings if "tenant" in w.lower() or "isolation" in w.lower()]
        
        if tenant_warnings:
            print("✅ Tenant isolation validation passed")
            print(f"   Detected tenant warnings: {len(tenant_warnings)}")
            return True
        else:
            print(f"❌ Tenant isolation validation failed - expected warnings about tenant isolation")
            print(f"   Warnings: {warnings}")
            return False
            
    except Exception as e:
        print(f"❌ Tenant isolation validation error: {e}")
        return False


def test_security_compliance_validation():
    """Test security compliance validation."""
    print("Testing security compliance validation...")
    
    validator = ExtensionValidator()
    
    # Test extension with high resource limits and admin permissions
    manifest_data = create_test_manifest({
        "permissions": {
            "data_access": ["admin"],
            "system_access": ["admin"],
            "plugin_access": [],
            "network_access": ["outbound_http", "inbound"]
        },
        "resources": {
            "max_memory_mb": 4096,  # High memory
            "max_cpu_percent": 50,  # High CPU
            "max_disk_mb": 100,
            "enforcement_action": "default"
        }
    })
    
    try:
        is_valid, errors, warnings, field_errors = validator.validate_manifest_enhanced(manifest_data)
        
        # Should have warnings about security concerns
        security_warnings = [w for w in warnings if any(term in w.lower() for term in ["admin", "security", "http", "memory", "cpu"])]
        
        if security_warnings:
            print("✅ Security compliance validation passed")
            print(f"   Detected security warnings: {len(security_warnings)}")
            return True
        else:
            print(f"❌ Security compliance validation failed - expected security warnings")
            print(f"   Warnings: {warnings}")
            return False
            
    except Exception as e:
        print(f"❌ Security compliance validation error: {e}")
        return False


def test_manifest_format_consistency():
    """Test manifest format consistency validation."""
    print("Testing manifest format consistency...")
    
    validator = ExtensionValidator()
    
    # Test with inconsistent format
    manifest_data = create_test_manifest({
        "name": "Invalid_Name_Format",  # Should be kebab-case
        "category": "invalid-category",  # Not in standard categories
        "api_version": "0.5"  # Not supported version
    })
    
    try:
        is_valid, errors, warnings, field_errors = validator.validate_manifest_enhanced(manifest_data)
        
        # Should have errors/warnings about format consistency
        format_issues = errors + warnings
        format_warnings = [issue for issue in format_issues if any(term in issue.lower() for term in ["name", "category", "version"])]
        
        if format_warnings:
            print("✅ Manifest format consistency validation passed")
            print(f"   Detected format issues: {len(format_warnings)}")
            return True
        else:
            print(f"❌ Manifest format consistency validation failed - expected format warnings")
            print(f"   Issues: {format_issues}")
            return False
            
    except Exception as e:
        print(f"❌ Manifest format consistency validation error: {e}")
        return False


def test_validation_report_generation():
    """Test comprehensive validation report generation."""
    print("Testing validation report generation...")
    
    validator = ExtensionValidator()
    manifest_data = create_test_manifest({
        "api": {
            "endpoints": [
                {
                    "path": "/ag_ui/memory/legacy",  # Legacy endpoint
                    "methods": ["POST"]
                }
            ]
        },
        "permissions": {
            "data_access": ["admin"],
            "system_access": [],
            "plugin_access": [],
            "network_access": ["outbound_http"]
        }
    })
    
    try:
        manifest = ExtensionManifest.from_dict(manifest_data)
        report = validator.get_validation_report(manifest)
        
        # Check report structure
        required_fields = ["manifest_name", "manifest_version", "is_valid", "errors", "warnings", 
                          "recommendations", "compatibility", "summary"]
        
        missing_fields = [field for field in required_fields if field not in report]
        
        if not missing_fields and report["recommendations"]:
            print("✅ Validation report generation passed")
            print(f"   Report contains {len(report['recommendations'])} recommendations")
            print(f"   Overall score: {report['summary']['overall_score']}")
            return True
        else:
            print(f"❌ Validation report generation failed")
            print(f"   Missing fields: {missing_fields}")
            print(f"   Report: {report}")
            return False
            
    except Exception as e:
        print(f"❌ Validation report generation error: {e}")
        return False


async def main():
    """Run all validation tests."""
    print("🔍 Testing Updated Extension Validation System")
    print("=" * 60)
    
    tests = [
        test_basic_validation,
        test_unified_api_endpoint_validation,
        test_legacy_endpoint_detection,
        test_rbac_scope_validation,
        test_tenant_isolation_validation,
        test_security_compliance_validation,
        test_manifest_format_consistency,
        test_validation_report_generation,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All extension validation tests passed!")
        print("✅ Extension validation system successfully updated with unified patterns")
        return True
    else:
        print("⚠️  Some tests failed - validation system needs attention")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)