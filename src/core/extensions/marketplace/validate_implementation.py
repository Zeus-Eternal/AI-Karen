#!/usr/bin/env python3
"""
Validate Extension Marketplace Implementation

Simple validation script to check if the marketplace implementation is working.
"""

import sys
import json
from pathlib import Path

def validate_models():
    """Validate that models can be imported and instantiated."""
    try:
        from .models import (
            ExtensionListingSchema, ExtensionVersionSchema, 
            ExtensionSearchRequest, ExtensionInstallRequest
        )
        
        # Test basic model creation
        listing = ExtensionListingSchema(
            name="test-extension",
            display_name="Test Extension",
            description="A test extension",
            author="Test Author",
            category="testing",
            license="MIT"
        )
        
        search_request = ExtensionSearchRequest(
            query="test",
            page=1,
            page_size=10
        )
        
        install_request = ExtensionInstallRequest(
            extension_name="test-extension"
        )
        
        print("✅ Models validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Models validation failed: {e}")
        return False


def validate_version_manager():
    """Validate version manager functionality."""
    try:
        from .version_manager import VersionManager
        
        vm = VersionManager(None)  # No DB session needed for basic tests
        
        # Test version parsing
        version = vm.parse_version("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        
        # Test version comparison
        assert vm.compare_versions("1.2.3", "1.2.4") < 0
        assert vm.compare_versions("1.2.4", "1.2.3") > 0
        assert vm.compare_versions("1.2.3", "1.2.3") == 0
        
        # Test constraint satisfaction
        assert vm.satisfies_constraint("1.2.3", "1.2.3")
        
        # Test manifest validation
        manifest = {
            "version": "1.2.3",
            "api_version": "1.0"
        }
        errors = vm.validate_manifest_version(manifest)
        
        print("✅ Version manager validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Version manager validation failed: {e}")
        return False


def validate_database_manager():
    """Validate database manager functionality."""
    try:
        from .database import MarketplaceDatabaseManager
        
        # Test with in-memory SQLite
        db_manager = MarketplaceDatabaseManager("sqlite:///:memory:")
        
        # Test table creation
        assert db_manager.create_tables()
        
        # Test health check
        assert db_manager.health_check()
        
        # Test session creation
        session = db_manager.get_session()
        assert session is not None
        session.close()
        
        print("✅ Database manager validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Database manager validation failed: {e}")
        return False


def validate_marketplace_client():
    """Validate marketplace client functionality."""
    try:
        # Check if the client file exists and can be parsed
        client_path = Path(__file__).parent.parent.parent.parent.parent / "ui_launchers" / "web_ui" / "src" / "lib" / "extensions" / "marketplace-client.ts"
        
        if client_path.exists():
            content = client_path.read_text()
            
            # Basic checks for key components
            required_components = [
                "ExtensionMarketplaceClient",
                "searchExtensions",
                "installExtension",
                "getExtensionDetails"
            ]
            
            for component in required_components:
                if component not in content:
                    print(f"❌ Missing component in client: {component}")
                    return False
            
            print("✅ Marketplace client validation passed")
            return True
        else:
            print(f"❌ Marketplace client file not found: {client_path}")
            return False
        
    except Exception as e:
        print(f"❌ Marketplace client validation failed: {e}")
        return False


def validate_api_routes():
    """Validate API routes structure."""
    try:
        # Import routes to check for syntax errors
        from .routes import router
        
        # Check that router is properly configured
        assert router is not None
        assert hasattr(router, 'routes')
        
        print("✅ API routes validation passed")
        return True
        
    except Exception as e:
        print(f"❌ API routes validation failed: {e}")
        return False


def validate_cli():
    """Validate CLI functionality."""
    try:
        # Import CLI to check for syntax errors
        from .cli import cli
        
        # Check that CLI is properly configured
        assert cli is not None
        assert hasattr(cli, 'commands')
        
        print("✅ CLI validation passed")
        return True
        
    except Exception as e:
        print(f"❌ CLI validation failed: {e}")
        return False


def validate_integration():
    """Validate integration module."""
    try:
        from .integration import MarketplaceIntegration
        
        # Test basic instantiation
        integration = MarketplaceIntegration(
            database_url="sqlite:///:memory:",
            extensions_path=Path("extensions")
        )
        
        assert integration is not None
        
        print("✅ Integration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Integration validation failed: {e}")
        return False


def main():
    """Run all validations."""
    print("🔍 Validating Extension Marketplace Implementation")
    print("=" * 50)
    
    validations = [
        ("Models", validate_models),
        ("Version Manager", validate_version_manager),
        ("Database Manager", validate_database_manager),
        ("Marketplace Client", validate_marketplace_client),
        ("API Routes", validate_api_routes),
        ("CLI", validate_cli),
        ("Integration", validate_integration)
    ]
    
    passed = 0
    total = len(validations)
    
    for name, validator in validations:
        print(f"\n📋 Validating {name}...")
        if validator():
            passed += 1
        else:
            print(f"   Validation failed for {name}")
    
    print("\n" + "=" * 50)
    print(f"📊 Validation Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All validations passed! Marketplace implementation is ready.")
        return 0
    else:
        print("⚠️  Some validations failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())