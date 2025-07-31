#!/usr/bin/env python3
"""
Apply Production Authentication Migration
Applies only the production authentication tables migration
"""

import sys
import os
import psycopg2
from pathlib import Path

def get_database_url():
    """Get database URL from environment"""
    database_url = (
        os.getenv("DATABASE_URL") or
        os.getenv("POSTGRES_URL") or
        os.getenv("DB_URL")
    )
    
    if not database_url:
        # Try to construct from individual components
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "ai_karen")
        user = os.getenv("POSTGRES_USER", "karen_user")
        password = os.getenv("POSTGRES_PASSWORD", "karen_secure_pass_change_me")
        
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    return database_url

def apply_auth_migration():
    """Apply the production authentication migration"""
    database_url = get_database_url()
    
    if not database_url:
        print("❌ Database URL not provided. Set DATABASE_URL environment variable")
        sys.exit(1)
    
    print(f"🔗 Using database: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    # Get migration file
    migrations_dir = Path(__file__).parent.parent / "data" / "migrations" / "postgres"
    migration_file = migrations_dir / "010_add_production_auth_columns.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)
    
    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                # Create migrations table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version VARCHAR(255) PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Check if migration already applied
                cur.execute(
                    "SELECT version FROM schema_migrations WHERE version = %s",
                    ("010_add_production_auth_columns",)
                )
                
                if cur.fetchone():
                    print("✅ Production authentication migration already applied")
                    return
                
                print("📄 Applying production authentication migration...")
                
                # Read and execute migration SQL
                sql_content = migration_file.read_text()
                cur.execute(sql_content)
                
                # Record migration as applied
                cur.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    ("010_add_production_auth_columns",)
                )
                
                conn.commit()
                
        print("✅ Production authentication migration applied successfully!")
        print("\n📋 Created tables:")
        print("  - users")
        print("  - user_sessions")
        print("  - chat_memories")
        print("  - password_reset_tokens")
        print("  - email_verification_tokens")
        print("\n👤 Default users created:")
        print("  - admin@karen.ai (password: admin123)")
        print("  - demo@karen.ai (password: demo123)")
        print("\n🔒 Please change default passwords in production!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    apply_auth_migration()