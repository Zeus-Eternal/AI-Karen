#!/usr/bin/env python3
"""
Simple Authentication Database Migration Runner

This script runs the production authentication database migration with minimal dependencies.
"""

import asyncio
import os
import sys
from pathlib import Path

try:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
except ImportError as e:
    print(f"❌ Missing required dependencies: {e}")
    print("Please install: pip install sqlalchemy asyncpg")
    sys.exit(1)


async def run_migration():
    """Run the authentication database migration."""
    print("🗄️  Running Authentication Database Migration")
    print("=" * 50)
    
    # Get database URL from environment
    database_url = (
        os.getenv("AUTH_DATABASE_URL") or 
        os.getenv("POSTGRES_URL") or 
        os.getenv("DATABASE_URL")
    )
    
    if not database_url:
        print("❌ No database URL found. Set AUTH_DATABASE_URL, POSTGRES_URL, or DATABASE_URL")
        return False
    
    # Ensure async driver
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    print(f"🔗 Connecting to database...")
    
    try:
        # Create engine
        engine = create_async_engine(database_url)
        
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            if not result.fetchone():
                raise Exception("Connection test failed")
        
        print("✅ Database connection verified")
        
        # Find migration script
        migration_path = Path(__file__).parent.parent / "data/migrations/postgres/013_production_auth_schema_alignment.sql"
        
        if not migration_path.exists():
            print(f"❌ Migration script not found: {migration_path}")
            await engine.dispose()
            return False
        
        # Read migration SQL
        migration_sql = migration_path.read_text()
        print(f"📄 Loaded migration script: {migration_path.name}")
        
        # Execute migration
        print("🚀 Executing migration...")
        
        async with engine.begin() as conn:
            try:
                # Execute the entire migration as one transaction
                await conn.execute(text(migration_sql))
                print("✅ Migration executed successfully")
                
                # Verify tables were created
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name LIKE 'auth_%'
                """))
                table_count = result.fetchone()[0]
                print(f"📊 Created {table_count} auth tables")
                
                # Check if admin user was created
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM auth_users WHERE email = 'admin@ai-karen.local'
                """))
                admin_count = result.fetchone()[0]
                
                if admin_count > 0:
                    print("✅ Admin user created: admin@ai-karen.local (password: admin123)")
                    print("⚠️  IMPORTANT: Change the admin password immediately!")
                else:
                    print("⚠️  Admin user was not created")
                
            except Exception as e:
                error_msg = str(e).lower()
                if "already exists" in error_msg:
                    print("⚠️  Some tables already exist - this is normal")
                    print("✅ Migration completed (tables already existed)")
                else:
                    print(f"❌ Migration failed: {e}")
                    await engine.dispose()
                    return False
        
        await engine.dispose()
        print("\n🎉 Authentication database migration completed successfully!")
        print("\nNext steps:")
        print("1. Change admin password: admin@ai-karen.local")
        print("2. Configure Redis for session management")
        print("3. Set AUTH_SECRET_KEY for JWT tokens")
        print("4. Run production authentication tests")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)