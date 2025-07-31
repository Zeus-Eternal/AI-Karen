#!/usr/bin/env python3
"""
Database Migration Runner
Applies SQL migrations to the production database
"""

import sys
import os
import psycopg2
from pathlib import Path
from typing import List, Tuple

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_karen_engine.core.chat_memory_config import settings
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)


class MigrationRunner:
    """Database migration runner"""
    
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
        logger.info(f"Applying migration: {version}")
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
                    
            logger.info(f"Successfully applied migration: {version}")
            print(f"✅ Successfully applied: {version}")
            
        except Exception as e:
            logger.error(f"Failed to apply migration {version}: {e}")
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
    
    def rollback_migration(self, version: str):
        """Rollback a specific migration (if rollback SQL exists)"""
        rollback_file = self.migrations_dir / f"{version}_rollback.sql"
        
        if not rollback_file.exists():
            raise ValueError(f"No rollback file found for migration: {version}")
        
        logger.info(f"Rolling back migration: {version}")
        print(f"🔄 Rolling back migration: {version}")
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Read and execute rollback SQL
                    sql_content = rollback_file.read_text()
                    cur.execute(sql_content)
                    
                    # Remove migration record
                    cur.execute(
                        "DELETE FROM schema_migrations WHERE version = %s",
                        (version,)
                    )
                    
                    conn.commit()
                    
            logger.info(f"Successfully rolled back migration: {version}")
            print(f"✅ Successfully rolled back: {version}")
            
        except Exception as e:
            logger.error(f"Failed to rollback migration {version}: {e}")
            print(f"❌ Failed to rollback {version}: {e}")
            raise
    
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
    
    parser = argparse.ArgumentParser(description="Database Migration Runner")
    parser.add_argument(
        "command",
        choices=["migrate", "status", "rollback"],
        help="Migration command to run"
    )
    parser.add_argument(
        "--version",
        help="Migration version (for rollback command)"
    )
    parser.add_argument(
        "--database-url",
        default=settings.database_url,
        help="Database URL (defaults to settings)"
    )
    
    args = parser.parse_args()
    
    if not args.database_url:
        print("❌ Database URL not provided. Set DATABASE_URL environment variable or use --database-url")
        sys.exit(1)
    
    runner = MigrationRunner(args.database_url)
    
    try:
        if args.command == "migrate":
            runner.run_migrations()
        elif args.command == "status":
            runner.status()
        elif args.command == "rollback":
            if not args.version:
                print("❌ Version required for rollback command")
                sys.exit(1)
            runner.rollback_migration(args.version)
            
    except Exception as e:
        logger.error(f"Migration command failed: {e}")
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()