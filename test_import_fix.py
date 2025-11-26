#!/usr/bin/env python3
"""
Test script to verify that the circular import issue has been resolved.
"""

import sys
import os
import traceback

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all the problematic imports now work."""
    success = True
    errors = []
    
    # Test 1: Import extension_host.__init__
    try:
        print("Testing: from ai_karen_engine.extension_host import ExtensionManager")
        from ai_karen_engine.extension_host import ExtensionManager
        print("✅ SUCCESS: ExtensionManager imported successfully")
    except Exception as e:
        success = False
        error_msg = f"❌ FAILED: ExtensionManager import failed: {str(e)}"
        errors.append(error_msg)
        print(error_msg)
        traceback.print_exc()
    
    # Test 2: Import extension_host.get_extension_manager
    try:
        print("\nTesting: from ai_karen_engine.extension_host import get_extension_manager")
        from ai_karen_engine.extension_host import get_extension_manager
        print("✅ SUCCESS: get_extension_manager imported successfully")
    except Exception as e:
        success = False
        error_msg = f"❌ FAILED: get_extension_manager import failed: {str(e)}"
        errors.append(error_msg)
        print(error_msg)
        traceback.print_exc()
    
    # Test 3: Import extensions module
    try:
        print("\nTesting: import ai_karen_engine.extensions")
        import ai_karen_engine.extensions
        print("✅ SUCCESS: extensions module imported successfully")
    except Exception as e:
        success = False
        error_msg = f"❌ FAILED: extensions module import failed: {str(e)}"
        errors.append(error_msg)
        print(error_msg)
        traceback.print_exc()
    
    # Test 4: Import from extensions.__init__
    try:
        print("\nTesting: from ai_karen_engine.extensions import ExtensionRegistry")
        from ai_karen_engine.extensions import ExtensionRegistry
        print("✅ SUCCESS: ExtensionRegistry imported successfully")
    except Exception as e:
        success = False
        error_msg = f"❌ FAILED: ExtensionRegistry import failed: {str(e)}"
        errors.append(error_msg)
        print(error_msg)
        traceback.print_exc()
    
    # Test 5: Test the lazy imports
    try:
        print("\nTesting: from ai_karen_engine.extensions import get_extension_manager")
        from ai_karen_engine.extensions import get_extension_manager
        print("✅ SUCCESS: get_extension_manager from extensions imported successfully")
    except Exception as e:
        success = False
        error_msg = f"❌ FAILED: get_extension_manager from extensions failed: {str(e)}"
        errors.append(error_msg)
        print(error_msg)
        traceback.print_exc()
    
    # Test 6: Test the API routes import
    try:
        print("\nTesting: from ai_karen_engine.api_routes.extensions import router")
        from ai_karen_engine.api_routes.extensions import router
        print("✅ SUCCESS: extensions API router imported successfully")
    except Exception as e:
        success = False
        error_msg = f"❌ FAILED: extensions API router import failed: {str(e)}"
        errors.append(error_msg)
        print(error_msg)
        traceback.print_exc()
    
    # Summary
    print("\n" + "="*50)
    if success:
        print("🎉 ALL IMPORTS SUCCESSFUL! The circular import issue has been resolved.")
    else:
        print(f"❌ {len(errors)} IMPORTS FAILED. The circular import issue is not fully resolved.")
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    return success

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)