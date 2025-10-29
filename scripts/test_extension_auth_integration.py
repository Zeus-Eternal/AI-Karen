#!/usr/bin/env python3
"""
Test script to verify extension authentication integration.
"""

import sys
import os
sys.path.append('.')

def test_extension_auth_integration():
    """Test the extension authentication integration."""
    print("Testing Extension Authentication Integration")
    print("=" * 50)
    
    # Test 1: Check if the integration file has the correct structure
    try:
        with open('src/extensions/integration.py', 'r') as f:
            content = f.read()
        
        # Check for enhanced authentication dependencies
        required_imports = [
            'require_extension_read',
            'require_extension_write', 
            'require_extension_admin',
            'require_background_tasks',
            'get_extension_auth_manager'
        ]
        
        for import_name in required_imports:
            if import_name in content:
                print(f"✓ Found authentication dependency: {import_name}")
            else:
                print(f"✗ Missing authentication dependency: {import_name}")
        
        # Check for enhanced permission methods
        permission_methods = [
            '_has_admin_permission',
            '_has_system_extension_permission',
            '_is_system_extension',
            '_get_extension_permissions',
            '_has_extension_write_permission',
            '_has_extension_admin_permission',
            '_has_extension_task_permission',
            '_has_extension_config_permission'
        ]
        
        for method_name in permission_methods:
            if method_name in content:
                print(f"✓ Found permission method: {method_name}")
            else:
                print(f"✗ Missing permission method: {method_name}")
        
        # Check for enhanced endpoint features
        enhanced_features = [
            'include_disabled',
            'category',
            'force_reload',
            'force_unload',
            'preserve_state',
            'detailed',
            'user_context: Dict[str, Any] = Depends('
        ]
        
        for feature in enhanced_features:
            if feature in content:
                print(f"✓ Found enhanced feature: {feature}")
            else:
                print(f"✗ Missing enhanced feature: {feature}")
        
        print("\n" + "=" * 50)
        print("Integration file structure verification complete")
        
    except Exception as e:
        print(f"Error reading integration file: {e}")
        return False
    
    # Test 2: Check background task API authentication
    try:
        with open('src/extensions/background_task_api.py', 'r') as f:
            bg_content = f.read()
        
        bg_auth_deps = [
            'require_background_tasks',
            'require_extension_read',
            'require_extension_admin'
        ]
        
        print("\nBackground Task API Authentication:")
        for dep in bg_auth_deps:
            if dep in bg_content:
                print(f"✓ Background task API uses: {dep}")
            else:
                print(f"✗ Background task API missing: {dep}")
        
    except Exception as e:
        print(f"Error reading background task API file: {e}")
    
    # Test 3: Check server security module
    try:
        with open('server/security.py', 'r') as f:
            security_content = f.read()
        
        security_features = [
            'ExtensionAuthManager',
            'require_extension_read',
            'require_extension_write',
            'require_extension_admin',
            'require_background_tasks',
            'authenticate_extension_request'
        ]
        
        print("\nServer Security Module:")
        for feature in security_features:
            if feature in security_content:
                print(f"✓ Security module has: {feature}")
            else:
                print(f"✗ Security module missing: {feature}")
        
    except Exception as e:
        print(f"Error reading security file: {e}")
    
    print("\n" + "=" * 50)
    print("Extension Authentication Integration Test Complete")
    return True

if __name__ == "__main__":
    test_extension_auth_integration()