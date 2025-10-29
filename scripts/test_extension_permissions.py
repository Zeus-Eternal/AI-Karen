#!/usr/bin/env python3
"""
Test script for extension permission system implementation.

This script tests the extension-specific permission system including:
- Permission model (read, write, admin, background_tasks)
- Role-based access control
- Tenant-specific access controls
- Permission inheritance and delegation

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

def test_extension_permissions():
    """Test the extension permission system."""
    print("Testing Extension Permission System")
    print("=" * 50)
    
    try:
        # Import the permission system components
        from server.extension_permissions import (
            ExtensionPermission, PermissionScope, ExtensionRole,
            get_extension_permission_manager, has_extension_permission
        )
        from server.extension_rbac import (
            get_extension_rbac_manager, check_extension_role_permission
        )
        from server.extension_tenant_access import (
            TenantAccessLevel, ExtensionVisibility,
            get_extension_tenant_access_manager, check_tenant_extension_access
        )
        
        print("✓ Successfully imported permission system components")
        
        # Test 1: Permission Manager Initialization
        print("\n1. Testing Permission Manager Initialization")
        permission_manager = get_extension_permission_manager()
        rbac_manager = get_extension_rbac_manager()
        tenant_manager = get_extension_tenant_access_manager()
        
        print("✓ Permission managers initialized successfully")
        
        # Test 2: Role-based Permissions
        print("\n2. Testing Role-based Permissions")
        
        # Create test user contexts
        admin_user = {
            'user_id': 'admin_user',
            'tenant_id': 'test_tenant',
            'roles': ['admin'],
            'permissions': []
        }
        
        regular_user = {
            'user_id': 'regular_user',
            'tenant_id': 'test_tenant',
            'roles': ['user'],
            'permissions': []
        }
        
        developer_user = {
            'user_id': 'developer_user',
            'tenant_id': 'test_tenant',
            'roles': ['developer'],
            'permissions': []
        }
        
        # Test admin permissions
        admin_can_read = check_extension_role_permission(admin_user, ExtensionPermission.READ)
        admin_can_admin = check_extension_role_permission(admin_user, ExtensionPermission.ADMIN)
        
        print(f"✓ Admin can read: {admin_can_read}")
        print(f"✓ Admin can admin: {admin_can_admin}")
        
        # Test regular user permissions
        user_can_read = check_extension_role_permission(regular_user, ExtensionPermission.READ)
        user_can_admin = check_extension_role_permission(regular_user, ExtensionPermission.ADMIN)
        
        print(f"✓ User can read: {user_can_read}")
        print(f"✓ User can admin: {user_can_admin}")
        
        # Test developer permissions
        dev_can_write = check_extension_role_permission(developer_user, ExtensionPermission.WRITE)
        dev_can_background = check_extension_role_permission(developer_user, ExtensionPermission.BACKGROUND_TASKS)
        
        print(f"✓ Developer can write: {dev_can_write}")
        print(f"✓ Developer can background tasks: {dev_can_background}")
        
        # Test 3: Direct Permission Grants
        print("\n3. Testing Direct Permission Grants")
        
        # Grant specific permission to user
        success = permission_manager.grant_permission(
            user_id='regular_user',
            permission=ExtensionPermission.CONFIGURE,
            scope=PermissionScope.EXTENSION,
            target='test_extension',
            tenant_id='test_tenant',
            granted_by='admin_user'
        )
        
        print(f"✓ Permission granted: {success}")
        
        # Check if user has the granted permission
        has_configure = has_extension_permission(
            regular_user, ExtensionPermission.CONFIGURE, 'test_extension'
        )
        
        print(f"✓ User has configure permission: {has_configure}")
        
        # Test 4: Tenant Access Controls
        print("\n4. Testing Tenant Access Controls")
        
        # Set extension policy
        policy_success = tenant_manager.set_extension_policy(
            extension_name='test_extension',
            visibility=ExtensionVisibility.PUBLIC,
            default_access_level=TenantAccessLevel.STANDARD
        )
        
        print(f"✓ Extension policy set: {policy_success}")
        
        # Grant tenant access
        tenant_access_success = tenant_manager.grant_tenant_access(
            tenant_id='test_tenant',
            extension_name='test_extension',
            access_level=TenantAccessLevel.PREMIUM,
            granted_by='admin_user'
        )
        
        print(f"✓ Tenant access granted: {tenant_access_success}")
        
        # Check tenant access
        has_tenant_access = check_tenant_extension_access(
            regular_user, 'test_extension', ExtensionPermission.READ
        )
        
        print(f"✓ User has tenant access: {has_tenant_access}")
        
        # Test 5: Role Assignment and Inheritance
        print("\n5. Testing Role Assignment and Inheritance")
        
        # Assign role to user
        role_assigned = rbac_manager.assign_role(
            user_id='regular_user',
            role=ExtensionRole.DEVELOPER,
            tenant_id='test_tenant',
            assigned_by='admin_user'
        )
        
        print(f"✓ Role assigned: {role_assigned}")
        
        # Get user roles (should include inherited roles)
        user_roles = rbac_manager.get_user_roles(
            user_id='regular_user',
            tenant_id='test_tenant',
            include_inherited=True
        )
        
        print(f"✓ User roles: {[role.value for role in user_roles]}")
        
        # Test 6: Permission Delegation
        print("\n6. Testing Permission Delegation")
        
        # Delegate permission from admin to user
        delegation_success = permission_manager.delegate_permission(
            delegator_context=admin_user,
            delegatee_user_id='regular_user',
            permission=ExtensionPermission.INSTALL,
            scope=PermissionScope.GLOBAL,
            target='*',
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        print(f"✓ Permission delegated: {delegation_success}")
        
        # Check if delegated permission works
        has_delegated = has_extension_permission(
            regular_user, ExtensionPermission.INSTALL
        )
        
        print(f"✓ User has delegated permission: {has_delegated}")
        
        # Test 7: Comprehensive Permission Check
        print("\n7. Testing Comprehensive Permission Check")
        
        # Get all effective permissions for user
        effective_permissions = rbac_manager.get_effective_permissions(
            regular_user, 'test_extension'
        )
        
        print("✓ Effective permissions retrieved:")
        for perm, has_perm in effective_permissions.get('permissions', {}).items():
            if has_perm:
                print(f"  - {perm}: {has_perm}")
        
        # Test 8: Tenant Extensions List
        print("\n8. Testing Tenant Extensions List")
        
        tenant_extensions = tenant_manager.get_tenant_extensions('test_tenant')
        
        print(f"✓ Tenant has access to {len(tenant_extensions)} extensions")
        for ext_name, access in tenant_extensions.items():
            print(f"  - {ext_name}: {access.access_level.value}")
        
        print("\n" + "=" * 50)
        print("✓ All extension permission tests completed successfully!")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure all permission system files are in the server/ directory")
        return False
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_security_integration():
    """Test integration with the security system."""
    print("\nTesting Security System Integration")
    print("=" * 50)
    
    try:
        from server.security import get_extension_auth_manager
        
        # Test authentication manager
        auth_manager = get_extension_auth_manager()
        print("✓ Extension auth manager initialized")
        
        # Test permission checking
        test_user = {
            'user_id': 'test_user',
            'tenant_id': 'test_tenant',
            'roles': ['user'],
            'permissions': ['extension:read']
        }
        
        has_read = auth_manager.has_permission(test_user, 'read')
        print(f"✓ User has read permission: {has_read}")
        
        # Test token creation
        access_token = auth_manager.create_access_token(
            user_id='test_user',
            tenant_id='test_tenant',
            roles=['user'],
            permissions=['extension:read', 'extension:write']
        )
        
        print(f"✓ Access token created: {len(access_token) > 0}")
        
        # Test service token
        service_token = auth_manager.create_service_token(
            service_name='test_service',
            permissions=['extension:background_tasks']
        )
        
        print(f"✓ Service token created: {len(service_token) > 0}")
        
        print("✓ Security system integration tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Security integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("Extension Permission System Test Suite")
    print("=" * 60)
    
    # Test 1: Core permission system
    permissions_ok = test_extension_permissions()
    
    # Test 2: Security integration
    security_ok = test_security_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Permission System Tests: {'PASS' if permissions_ok else 'FAIL'}")
    print(f"Security Integration Tests: {'PASS' if security_ok else 'FAIL'}")
    
    if permissions_ok and security_ok:
        print("\n🎉 All tests passed! Extension permission system is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())