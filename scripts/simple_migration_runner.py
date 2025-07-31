#!/usr/bin/env python3
"""
Simple Database Migration Runner
Applies SQL migrations to the production database without complex dependencies
"""

import sys
import os
import psycopg2
from pathlib import Path
from typing import List, Tuple

def get_database_url():
    """Get database URL from environment"""
    # Try different environment variable names
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


class SimpleMigrationRunner:
    """Simple database migration runner"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.migrations_dir = Path(__file__).parent.parent / "data" / "migrations" / "postgres"
        
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)
    
    def create_migrations_table(self):
        """Create migrations tracking table if it doesn't exist"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version VARCHAR(255) PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version FROM schema_migrations ORDER BY version")
                return [row[0] for row in cur.fetchall()]
    
    def get_pending_migrations(self) -> List[Tuple[str, Path]]:
        """Get list of pending migrations"""
        applied = set(self.get_applied_migrations())
        pending = []
        
        for migration_file in sorted(self.migrations_dir.glob("*.sql")):
            version = migration_file.stem
            if version not in applied:
                pending.append((version, migration_file))
        
        return pending
    
    def apply_migration(self, version: str, migration_file: Path):
        """Apply a single migration"""
        print(f"📄 Applying migration: {version}")
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Read and execute migration SQL
                    sql_content = migration_file.read_text()
                    cur.execute(sql_content)
                    
                    # Record migration as applied
                    cur.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s)",
                        (version,)
                    )
                    
                    conn.commit()
                    
            print(f"✅ Successfully applied: {version}")
            
        except Exception as e:
            print(f"❌ Failed to apply {version}: {e}")
            raise
    
    def run_migrations(self):
        """Run all pending migrations"""
        print("🚀 Running database migrations")
        print("=" * 50)
        
        # Create migrations table
        self.create_migrations_table()
        
        # Get pending migrations
        pending = self.get_pending_migrations()
        
        if not pending:
            print("✅ No pending migrations")
            return
        
        print(f"📋 Found {len(pending)} pending migrations:")
        for version, _ in pending:
            print(f"  - {version}")
        
        print("\n🔄 Applying migrations...")
        
        # Apply each migration
        for version, migration_file in pending:
            self.apply_migration(version, migration_file)
        
        print(f"\n🎉 Successfully applied {len(pending)} migrations!")
    
    def status(self):
        """Show migration status"""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        print("📊 Migration Status")
        print("=" * 30)
        print(f"Applied migrations: {len(applied)}")
        print(f"Pending migrations: {len(pending)}")
        
        if applied:
            print("\n✅ Applied:")
            for version in applied:
                print(f"  - {version}")
        
        if pending:
            print("\n⏳ Pending:")
            for version, _ in pending:
                print(f"  - {version}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple Database Migration Runner")
    parser.add_argument(
        "command",
        choices=["migrate", "status"],
        help="Migration command to run"
    )
    parser.add_argument(
        "--database-url",
        help="Database URL (defaults to environment variables)"
    )
    
    args = parser.parse_args()
    
    database_url = args.database_url or get_database_url()
    
    if not database_url:
        print("❌ Database URL not provided. Set DATABASE_URL environment variable or use --database-url")
        sys.exit(1)
    
    print(f"🔗 Using database: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    runner = SimpleMigrationRunner(database_url)
    
    try:
        if args.command == "migrate":
            runner.run_migrations()
        elif args.command == "status":
            runner.status()
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()