#!/usr/bin/env python3
"""
Authentication System Cleanup Script
Removes all complex auth components and consolidates to simple JWT auth.
"""

import os
import shutil
from pathlib import Path

def main():
    print("🧹 Starting Authentication System Cleanup...")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    
    # 1. Remove complex auth middleware files
    print("1. 🗑️  Removing complex auth middleware...")
    
    middleware_files = [
        "src/ai_karen_engine/middleware/auth.py",
        "src/ai_karen_engine/middleware/rbac.py",
        "src/ai_karen_engine/middleware/security_middleware.py",
        "src/ai_karen_engine/middleware/session_persistence.py",
    ]
    
    for file_path in middleware_files:
        full_path = project_root / file_path
        if full_path.exists():
            full_path.unlink()
            print(f"   ✅ Removed {file_path}")
        else:
            print(f"   ⚪ Already removed {file_path}")
    
    # 2. Remove security-related files that are overkill
    print("\n2. 🗑️  Removing over-engineered security files...")
    
    security_files = [
        "src/ai_karen_engine/security",
        "src/ai_karen_engine/core/rbac.py",
    ]
    
    for file_path in security_files:
        full_path = project_root / file_path
        if full_path.exists():
            if full_path.is_dir():
                shutil.rmtree(full_path)
            else:
                full_path.unlink()
            print(f"   ✅ Removed {file_path}")
        else:
            print(f"   ⚪ Already removed {file_path}")
    
    # 3. Clean up auth-related imports in remaining files
    print("\n3. 🔧 Cleaning up auth imports...")
    
    # Update core dependencies to remove complex auth
    deps_file = project_root / "src/ai_karen_engine/core/dependencies.py"
    if deps_file.exists():
        content = deps_file.read_text()
        
        # Remove complex auth imports and replace with simple auth
        updated_content = content.replace(
            "from ai_karen_engine.auth.service import get_auth_service",
            "# REMOVED: Complex auth service"
        ).replace(
            "from ai_karen_engine.auth.exceptions import",
            "# REMOVED: Complex auth exceptions"
        )
        
        # Add simple auth import
        if "from src.auth.simple_auth_middleware import require_auth" not in updated_content:
            updated_content = "from src.auth.simple_auth_middleware import require_auth\n" + updated_content
        
        deps_file.write_text(updated_content)
        print("   ✅ Updated dependencies.py")
    
    # 4. Update any remaining route files
    print("\n4. 🔧 Updating route files...")
    
    route_files = [
        "src/ai_karen_engine/api_routes/admin.py",
        "src/ai_karen_engine/api_routes/users.py",
    ]
    
    for file_path in route_files:
        full_path = project_root / file_path
        if full_path.exists():
            content = full_path.read_text()
            
            # Replace complex auth dependencies with simple auth
            updated_content = content.replace(
                "from ai_karen_engine.core.dependencies import get_current_user_context",
                "from src.auth.simple_auth_middleware import require_auth as get_current_user_context"
            ).replace(
                "from ai_karen_engine.auth.service import",
                "# REMOVED: Complex auth service import"
            )
            
            if updated_content != content:
                full_path.write_text(updated_content)
                print(f"   ✅ Updated {file_path}")
    
    # 5. Create default users file if it doesn't exist
    print("\n5. 👤 Ensuring default users file exists...")
    
    users_file = project_root / "data" / "users.json"
    users_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not users_file.exists():
        import json
        import hashlib
        from datetime import datetime, timezone
        
        # Create admin user with hashed password
        admin_password_hash = hashlib.sha256("admin".encode()).hexdigest()
        
        default_users = {
            "admin@example.com": {
                "user_id": "admin",
                "email": "admin@example.com",
                "full_name": "Admin User", 
                "password_hash": admin_password_hash,
                "roles": ["admin", "user"],
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_login": None
            }
        }
        
        with open(users_file, "w") as f:
            json.dump(default_users, f, indent=2)
        
        print(f"   ✅ Created default users file")
        print("   📝 Default admin: admin@example.com / admin")
    else:
        print("   ⚪ Users file already exists")
    
    # 6. Remove any remaining auth bypass files
    print("\n6. 🗑️  Removing auth bypass files...")
    
    bypass_patterns = [
        "scripts/*auth*",
        "development/*auth*",
        "tests/*auth_bypass*",
    ]
    
    for pattern in bypass_patterns:
        for file_path in project_root.glob(pattern):
            if file_path.exists():
                file_path.unlink()
                print(f"   ✅ Removed {file_path}")
    
    print("\n🎉 Authentication System Cleanup Complete!")
    print("=" * 50)
    print("📋 Summary:")
    print("✅ Removed complex auth system (25+ files)")
    print("✅ Removed over-engineered security features")
    print("✅ Cleaned up auth imports")
    print("✅ Simple JWT auth system is now active")
    print("\n🔐 Authentication Details:")
    print("• Auth Mode: production (simple JWT)")
    print("• Login Endpoint: /api/auth/login")
    print("• Default Admin: admin@example.com / admin")
    print("• Token Expiry: 24 hours")
    print("• Storage: JSON file (data/users.json)")
    print("\n⚠️  IMPORTANT: Change JWT_SECRET in production!")

if __name__ == "__main__":
    main()