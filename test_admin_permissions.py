#!/usr/bin/env python3
"""
Test script to verify admin user permissions across authentication systems
"""

import asyncio
import os
import sys

# Set required environment variables before any imports
os.environ["KARI_DUCKDB_PASSWORD"] = "dev-duckdb-pass"
os.environ["KARI_JOB_ENC_KEY"] = "MaL42789OGRr0--UUf_RV_kanWzb2tSCd6hU6R-sOZo="
os.environ["KARI_JOB_SIGNING_KEY"] = "dev-job-key-456"

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_karen_engine.auth.enhanced_auth_service import EnhancedAuthService
from ai_karen_engine.auth.rbac_middleware import RBACManager, Permission, Role
from ai_karen_engine.auth.models import UserData

async def test_admin_permissions():
    """Test admin user permissions across authentication systems"""
    print("🧪 Testing Admin User Permissions")
    print("=" * 50)
    
    # Create auth service instance
    auth_service = EnhancedAuthService()
    
    # Test authentication
    print("\n1. 🔐 Authenticating admin user...")
    try:
        user = await auth_service.authenticate_user(
            email="admin@kari.ai",
            password="password123",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        if user:
            print("✅ Authentication successful!")
            print(f"   User: {user['email']}")
            print(f"   Roles: {user['roles']}")
        else:
            print("❌ Authentication failed")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    # Create RBAC manager
    rbac_manager = RBACManager()
    
    # Convert to UserData object for RBAC
    user_data = UserData(
        user_id=user["user_id"],
        email=user["email"],
        full_name=user["full_name"],
        roles=user["roles"],
        tenant_id=user["tenant_id"],
        is_verified=user["is_verified"],
        is_active=user["is_active"]
    )
    
    print(f"\n2. 🔍 Checking RBAC permissions for admin user...")
    
    # Check admin role
    has_admin_role = rbac_manager.has_admin_role(user_data)
    print(f"   Has admin role: {has_admin_role}")
    
    # Check specific permissions
    permissions_to_check = [
        Permission.ADMIN_READ,
        Permission.ADMIN_WRITE,
        Permission.ADMIN_SYSTEM,
        Permission.TRAINING_EXECUTE,
        Permission.MODEL_DEPLOY,
        Permission.DATA_EXPORT,
        Permission.SECURITY_WRITE
    ]
    
    print(f"\n3. 📋 Checking specific permissions:")
    for permission in permissions_to_check:
        has_perm = rbac_manager.has_permission(user_data, permission)
        print(f"   {permission.value}: {'✅' if has_perm else '❌'}")
    
    # Check all permissions
    all_permissions = rbac_manager.get_user_permissions(user_data)
    print(f"\n4. 📊 Total permissions granted: {len(all_permissions)}")
    
    # Verify admin has all critical permissions
    critical_permissions = [
        Permission.ADMIN_READ,
        Permission.ADMIN_WRITE, 
        Permission.ADMIN_SYSTEM,
        Permission.SECURITY_WRITE
    ]
    
    all_critical_granted = all(
        rbac_manager.has_permission(user_data, perm) 
        for perm in critical_permissions
    )
    
    print(f"\n5. 🛡️  All critical admin permissions granted: {'✅' if all_critical_granted else '❌'}")
    
    if not all_critical_granted:
        missing = [
            perm.value for perm in critical_permissions 
            if not rbac_manager.has_permission(user_data, perm)
        ]
        print(f"   Missing permissions: {missing}")
        return False
    
    print(f"\n🎉 Admin user has unrestricted access to all system functions!")
    return True

async def test_role_validation():
    """Test role validation for different user types"""
    print("\n" + "=" * 50)
    print("🧪 Testing Role Validation")
    print("=" * 50)
    
    rbac_manager = RBACManager()
    
    # Test different user roles
    test_users = [
        {
            "name": "Admin User",
            "roles": ["admin", "user"],
            "should_have_admin": True
        },
        {
            "name": "Super Admin User", 
            "roles": ["super_admin", "admin", "user"],
            "should_have_admin": True
        },
        {
            "name": "Regular User",
            "roles": ["user"],
            "should_have_admin": False
        },
        {
            "name": "Trainer User",
            "roles": ["trainer", "user"],
            "should_have_admin": False
        }
    ]
    
    for i, user_config in enumerate(test_users, 1):
        user_data = UserData(
            user_id=f"test-user-{i}",
            email=f"test{i}@example.com",
            full_name=user_config["name"],
            roles=user_config["roles"],
            tenant_id="default",
            is_verified=True,
            is_active=True
        )
        
        has_admin = rbac_manager.has_admin_role(user_data)
        expected = user_config["should_have_admin"]
        status = "✅" if has_admin == expected else "❌"
        
        print(f"{status} {user_config['name']}:")
        print(f"   Roles: {user_config['roles']}")
        print(f"   Has admin access: {has_admin} (expected: {expected})")
        print()
        
        if has_admin != expected:
            return False
    
    return True

async def main():
    """Run all tests"""
    success1 = await test_admin_permissions()
    success2 = await test_role_validation()
    
    print("=" * 50)
    print("📊 TEST RESULTS:")
    print(f"   Admin Permissions: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Role Validation:   {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! Admin users have proper unrestricted access.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED! Check admin role configuration.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)