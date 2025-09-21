#!/usr/bin/env python3
"""
Authentication System Migration Script
Removes complex auth system and replaces with simple JWT auth.
"""

import os
import shutil
from pathlib import Path

def main():
    print("🔄 Starting Authentication System Migration...")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    
    # 1. Remove old auth bypass systems
    print("1. 🗑️  Removing auth bypass systems...")
    
    bypass_files = [
        "scripts/simple_auth_bypass.py",
        "scripts/temp_auth_bypass.py", 
        "development/simple_auth_bypass.py",
        "tests/test_simple_auth_bypass.py"
    ]
    
    for file_path in bypass_files:
        full_path = project_root / file_path
        if full_path.exists():
            full_path.unlink()
            print(f"   ✅ Removed {file_path}")
        else:
            print(f"   ⚪ Already removed {file_path}")
    
    # 2. Create backup of complex auth system
    print("\n2. 💾 Backing up complex auth system...")
    
    auth_backup_dir = project_root / "backups" / "complex_auth_system"
    auth_backup_dir.mkdir(parents=True, exist_ok=True)
    
    complex_auth_files = [
        "src/ai_karen_engine/auth",
        "src/ai_karen_engine/api_routes/auth.py",
        "src/ai_karen_engine/api_routes/auth_session_routes.py"
    ]
    
    for file_path in complex_auth_files:
        full_path = project_root / file_path
        if full_path.exists():
            backup_path = auth_backup_dir / file_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir():
                shutil.copytree(full_path, backup_path, dirs_exist_ok=True)
            else:
                shutil.copy2(full_path, backup_path)
            print(f"   ✅ Backed up {file_path}")
    
    # 3. Update configuration files
    print("\n3. ⚙️  Updating configuration files...")
    
    # Update main.py reference if it exists
    main_py_path = project_root / "main.py"
    if main_py_path.exists():
        content = main_py_path.read_text()
        if "simple_auth_bypass" in content:
            updated_content = content.replace(
                "from scripts.simple_auth_bypass import router as bypass_router",
                "# REMOVED: auth bypass system"
            ).replace(
                "app.include_router(bypass_router)",
                "# REMOVED: auth bypass router"
            )
            main_py_path.write_text(updated_content)
            print("   ✅ Updated main.py")
    
    # 4. Create default user file
    print("\n4. 👤 Creating default users file...")
    
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
        
        print(f"   ✅ Created default users file at {users_file}")
        print("   📝 Default admin: admin@example.com / admin")
    else:
        print("   ⚪ Users file already exists")
    
    # 5. Create startup test script
    print("\n5. 🧪 Creating startup test script...")
    
    test_script = project_root / "test_simple_auth.py"
    test_content = '''#!/usr/bin/env python3
"""
Simple Authentication Test Script
Tests the new simplified auth system.
"""

import asyncio
import aiohttp
import json

async def test_auth():
    """Test the simplified auth system"""
    print("🧪 Testing Simple Authentication System")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Health check
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    print("1. ✅ Health endpoint working")
                else:
                    print(f"1. ❌ Health endpoint failed: {response.status}")
                    return False
        except Exception as e:
            print(f"1. ❌ Health endpoint error: {e}")
            return False
        
        # Test 2: Auth health
        try:
            async with session.get(f"{base_url}/api/auth/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"2. ✅ Auth service healthy: {data.get('users', '0')} users")
                else:
                    print(f"2. ❌ Auth health failed: {response.status}")
                    return False
        except Exception as e:
            print(f"2. ❌ Auth health error: {e}")
            return False
        
        # Test 3: Login
        try:
            login_data = {
                "email": "admin@example.com",
                "password": "admin"
            }
            
            async with session.post(
                f"{base_url}/api/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get("access_token")
                    user = data.get("user", {})
                    print(f"3. ✅ Login successful: {user.get('email')}")
                    print(f"   🎫 Token: {token[:20]}...")
                    
                    # Test 4: Protected endpoint
                    headers = {"Authorization": f"Bearer {token}"}
                    async with session.get(f"{base_url}/api/auth/me", headers=headers) as me_response:
                        if me_response.status == 200:
                            me_data = await me_response.json()
                            print(f"4. ✅ Protected endpoint working: {me_data.get('email')}")
                            return True
                        else:
                            print(f"4. ❌ Protected endpoint failed: {me_response.status}")
                            return False
                else:
                    print(f"3. ❌ Login failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
        except Exception as e:
            print(f"3. ❌ Login error: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_auth())
    
    if success:
        print("\\n✅ Simple auth system is working correctly!")
        print("🔐 You can now login with:")
        print("   Email: admin@example.com")
        print("   Password: admin")
    else:
        print("\\n❌ Simple auth system test failed!")
        print("🔧 Make sure the server is running on port 8000")
'''
    
    test_script.write_text(test_content)
    test_script.chmod(0o755)
    print(f"   ✅ Created test script at {test_script}")
    
    print("\n🎉 Authentication Migration Complete!")
    print("=" * 50)
    print("📋 Next Steps:")
    print("1. Start the server: poetry run python start.py")
    print("2. Test auth system: python test_simple_auth.py")
    print("3. Login credentials: admin@example.com / admin")
    print("4. Update frontend to use /api/auth/* endpoints")
    print("\n⚠️  IMPORTANT: Change the JWT_SECRET in production!")

if __name__ == "__main__":
    main()
