#!/usr/bin/env python3
"""
Test script to verify that the circular import issue has been resolved.
This test focuses only on the imports that were causing the circular import error.
"""

import sys
import os
import traceback

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_circular_import_fix():
    """Test that the circular import issue has been resolved."""
    success = True
    errors = []
    
    # Test the specific import that was failing in the error message
    try:
        print("Testing: from ai_karen_engine.extension_host.__init__2 import get_extension_manager")
        from ai_karen_engine.extension_host.__init__2 import get_extension_manager
        print("✅ SUCCESS: get_extension_manager from __init__2 imported successfully")
    except Exception as e:
        success = False
        error_msg = f"❌ FAILED: get_extension_manager from __init__2 import failed: {str(e)}"
        errors.append(error_msg)
        print(error_msg)
        traceback.print_exc()
    
    # Test the import that was failing in the api_routes/extensions.py
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
    
    # Test the import from ai_karen_engine.extension_host to extensions
    try:
        print("\nTesting: from ai_karen_engine.extension_host import ExtensionManager")
        from ai_karen_engine.extension_host import ExtensionManager
        print("✅ SUCCESS: ExtensionManager imported successfully")
    except Exception as e:
        success = False
        error_msg = f"❌ FAILED: ExtensionManager import failed: {str(e)}"
        errors.append(error_msg)
        print(error_msg)
        traceback.print_exc()
    
    # Test the import from ai_karen_engine.extension_host to get_extension_manager
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
    
    # Test the import from ai_karen_engine.extensions to get_extension_manager
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
    
    # Summary
    print("\n" + "="*50)
    if success:
        print("🎉 ALL CIRCULAR IMPORT TESTS PASSED! The circular import issue has been resolved.")
    else:
        print(f"❌ {len(errors)} CIRCULAR IMPORT TESTS FAILED. The circular import issue is not fully resolved.")
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    return success

if __name__ == "__main__":
    success = test_circular_import_fix()
    sys.exit(0 if success else 1)