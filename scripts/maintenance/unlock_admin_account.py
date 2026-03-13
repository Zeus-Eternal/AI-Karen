#!/usr/bin/env python3
"""
Unlock Admin Account
Comprehensive script to unlock the admin account and clear all lockout conditions.
"""


import asyncio
import asyncpg
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def _load_env_file(env_filename=".env"):
    """Load env vars from the workspace root .env if they are not already set."""
    env_path = Path(__file__).resolve().parents[2] / env_filename
    if not env_path.is_file():
        return False

    try:
        with env_path.open() as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, _, value = line.partition("=")
                key = key.strip()
                if not key:
                    continue

                value = value.strip()
                if "#" in value:
                    value = value.split("#", 1)[0].strip()

                if (
                    len(value) >= 2
                    and value[0] == value[-1]
                    and value[0] in ("'", '"')
                ):
                    value = value[1:-1]

                os.environ.setdefault(key, value)
        return True
    except OSError:
        return False


def _reset_local_user_lockout(email: str):
    """Reset lockout state stored in data/users.json so the simple auth service agrees."""
    repo_root = Path(__file__).resolve().parents[2]
    users_file = repo_root / "data" / "users.json"
    try:
        identifier = users_file.relative_to(repo_root)
    except ValueError:
        identifier = users_file

    if not users_file.is_file():
        return False, f"{identifier} not found"

    try:
        with users_file.open("r") as handle:
            data = json.load(handle)
    except Exception as exc:
        return False, f"Could not read {identifier}: {exc}"

    user_entry = data.get(email)
    if not user_entry:
        return False, f"{email} not present in {identifier}"

    user_entry["failed_login_attempts"] = 0
    user_entry["locked_until"] = None

    try:
        with users_file.open("w") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
    except Exception as exc:
        return False, f"Failed to write {identifier}: {exc}"

    return True, f"Reset lockout state in {identifier}"


async def unlock_admin_account():
    """Unlock the admin account and clear all lockout conditions."""
    print("🔓 Unlocking admin account...")
    
    # Load local environment overrides if available (helps scripts run without sourcing .env)
    _load_env_file()

    # Database connection details from environment
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'user': os.getenv('POSTGRES_USER', 'karen_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'karen_secure_pass_change_me'),
        'database': os.getenv('POSTGRES_DB', 'ai_karen')
    }
    
    admin_email = "admin@kari.ai"
    
    try:
        print(f"   📡 Connecting to database at {db_config['host']}:{db_config['port']}")
        conn = await asyncpg.connect(**db_config)
        
        # Step 1: Find the admin user
        admin_user = await conn.fetchrow("""
            SELECT user_id, email, failed_login_attempts, locked_until, is_active
            FROM auth_users 
            WHERE email = $1
        """, admin_email)
        
        if not admin_user:
            print(f"   ❌ Admin user {admin_email} not found!")
            await conn.close()
            return False

        print(f"   ✅ Found admin user: {admin_user['user_id']}")
        print(f"      Failed attempts: {admin_user['failed_login_attempts']}")
        print(f"      Locked until: {admin_user['locked_until']}")
        print(f"      Active: {admin_user['is_active']}")

        reset_success, reset_msg = _reset_local_user_lockout(admin_email)
        if reset_success:
            print(f"   ✅ {reset_msg}")
        else:
            print(f"   ℹ️  {reset_msg}")
        
        # Step 2: Clear all lockout conditions
        print("   🧹 Clearing lockout conditions...")
        
        # Reset failed login attempts and unlock
        updated = await conn.execute("""
            UPDATE auth_users 
            SET 
                failed_login_attempts = 0,
                locked_until = NULL,
                is_active = TRUE,
                updated_at = $2
            WHERE user_id = $1
        """, admin_user['user_id'], datetime.now(timezone.utc))
        
        print(f"   ✅ Updated auth_users: {updated}")
        
        # Step 3: Clear any rate limiting entries
        print("   🧹 Clearing rate limiting...")
        
        # Clear from rate_limits table
        try:
            rate_limit_cleared = await conn.execute("""
                DELETE FROM rate_limits 
                WHERE identifier LIKE $1 OR identifier LIKE $2
            """, f"%{admin_email}%", f"%{admin_user['user_id']}%")
            print(f"   ✅ Cleared rate limits: {rate_limit_cleared}")
        except Exception as e:
            print(f"   ℹ️  Rate limits table issue: {e}")
        
        # Step 4: Clear old sessions that might be causing issues
        print("   🧹 Clearing old sessions...")
        
        try:
            sessions_cleared = await conn.execute("""
                DELETE FROM auth_sessions 
                WHERE user_id = $1
            """, admin_user['user_id'])
            print(f"   ✅ Cleared old sessions: {sessions_cleared}")
        except Exception as e:
            print(f"   ℹ️  Sessions clearing issue: {e}")
        
        # Step 5: Clear any auth events that might be causing issues
        print("   🧹 Clearing problematic auth events...")
        
        try:
            # Clear recent failed login events for this user
            events_cleared = await conn.execute("""
                DELETE FROM auth_events 
                WHERE email = $1 AND event_type = 'login_failed' 
                AND timestamp > NOW() - INTERVAL '1 hour'
            """, admin_email)
            print(f"   ✅ Cleared recent failed auth events: {events_cleared}")
        except Exception as e:
            print(f"   ℹ️  Auth events clearing issue: {e}")
        
        # Step 6: Verify the unlock
        print("   🔍 Verifying unlock...")
        
        unlocked_user = await conn.fetchrow("""
            SELECT user_id, email, failed_login_attempts, locked_until, is_active
            FROM auth_users 
            WHERE email = $1
        """, admin_email)
        
        if unlocked_user:
            print(f"   ✅ Admin user status after unlock:")
            print(f"      Failed attempts: {unlocked_user['failed_login_attempts']}")
            print(f"      Locked until: {unlocked_user['locked_until']}")
            print(f"      Active: {unlocked_user['is_active']}")
            
            if (unlocked_user['failed_login_attempts'] == 0 and 
                unlocked_user['locked_until'] is None and 
                unlocked_user['is_active']):
                print("   ✅ Account successfully unlocked!")
                success = True
            else:
                print("   ⚠️  Account may still have issues")
                success = False
        else:
            print("   ❌ Could not verify unlock")
            success = False
        
        await conn.close()
        return success
        
    except Exception as e:
        print(f"   ❌ Error unlocking account: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function."""
    print("🚀 AI Karen Admin Account Unlocker")
    print("=" * 40)
    
    success = await unlock_admin_account()
    
    print("\n" + "="*40)
    if success:
        print("✅ Admin account unlocked successfully!")
        print("\n👤 You can now try logging in with:")
        print("   • Email: admin@kari.ai")
        print("   • Password: Password123!")
        print("\n🌐 Try logging in to the web UI now")
        print("⚠️  If you still have issues, restart the server")
    else:
        print("❌ Failed to unlock admin account")
        print("🔧 You may need to restart the authentication service")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Failed with error: {e}")
        sys.exit(1)
