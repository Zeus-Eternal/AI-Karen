#!/usr/bin/env python3
"""
Authentication Database Migration Runner

This script runs the production authentication database migration to ensure
the database schema is properly set up for production use.

Usage:
    python scripts/run_auth_migration.py [--dry-run] [--force]
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.ext.asyncio import create_async_engine
    from ai_karen_engine.auth.config import AuthConfig
except ImportError as e:
    print(f"❌ Missing required dependencies: {e}")
    print("Please install required packages:")
    print("pip install sqlalchemy asyncpg")
    sys.exit(1)


class AuthMigrationRunner:
    """Run authentication database migrations."""
    
    def __init__(self, dry_run: bool = False, force: bool = False):
        self.dry_run = dry_run
        self.force = force
        self.config = AuthConfig.from_env()
        
    async def run_migration(self) -> bool:
        """Run the authentication database migration."""
        print("🗄️  Authentication Database Migration Runner")
        print("=" * 50)
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
        
        # Step 1: Verify database connection
        if not await self._verify_database_connection():
            return False
        
        # Step 2: Check current schema state
        if not await self._check_current_schema():
            return False
        
        # Step 3: Run migration
        if not await self._run_migration_script():
            return False
        
        # Step 4: Verify migration success
        if not await self._verify_migration_success():
            return False
        
        print("\n✅ Authentication database migration completed successfully!")
        return True
    
    async def _verify_database_connection(self) -> bool:
        """Verify database connection."""
        print("🔗 Verifying database connection...")
        
        try:
            engine = create_async_engine(self.config.database.database_url)
            
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                
                if row and row[0] == 1:
                    print("✅ Database connection verified")
                    await engine.dispose()
                    return True
                else:
                    print("❌ Database connection test failed")
                    await engine.dispose()
                    return False
                    
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def _check_current_schema(self) -> bool:
        """Check current database schema state."""
        print("📋 Checking current database schema...")
        
        try:
            engine = create_async_engine(self.config.database.database_url)
            
            async with engine.begin() as conn:
                # Check if auth tables exist
                auth_tables = [
                    'auth_users',
                    'auth_password_hashes',
                    'auth_sessions',
                    'auth_providers',
                    'user_identities',
                    'auth_password_reset_tokens',
                    'auth_email_verification_tokens',
                    'auth_events'
                ]
                
                existing_tables = []
                missing_tables = []
                
                for table in auth_tables:
                    result = await conn.execute(text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = '{table}'
                        )
                    """))
                    exists = result.fetchone()[0]
                    
                    if exists:
                        existing_tables.append(table)
                    else:
                        missing_tables.append(table)
                
                print(f"📊 Schema Status:")
                print(f"   Existing tables: {len(existing_tables)}")
                print(f"   Missing tables: {len(missing_tables)}")
                
                if missing_tables:
                    print(f"   Missing: {', '.join(missing_tables)}")
                
                if existing_tables and not self.force:
                    print("⚠️  Some auth tables already exist.")
                    print("   Use --force to run migration anyway.")
                    if not missing_tables:
                        print("   All required tables exist. Migration may not be necessary.")
                        await engine.dispose()
                        return False
                
                await engine.dispose()
                return True
                
        except Exception as e:
            print(f"❌ Schema check failed: {e}")
            return False
    
    async def _run_migration_script(self) -> bool:
        """Run the migration script."""
        print("🚀 Running authentication database migration...")
        
        # Find migration script
        migration_path = Path(__file__).resolve().parents[2] / "data/migrations/postgres/013_production_auth_schema_alignment.sql"
        
        if not migration_path.exists():
            print(f"❌ Migration script not found: {migration_path}")
            return False
        
        try:
            # Read migration SQL
            migration_sql = migration_path.read_text()
            print(f"📄 Loaded migration script: {migration_path.name}")
            
            if self.dry_run:
                print("🔍 DRY RUN: Would execute migration script")
                print(f"   Script size: {len(migration_sql)} characters")
                return True
            
            # Execute migration
            engine = create_async_engine(self.config.database.database_url)
            
            async with engine.begin() as conn:
                # Split migration into individual statements
                statements = self._split_sql_statements(migration_sql)
                
                print(f"📝 Executing {len(statements)} SQL statements...")
                
                executed = 0
                warnings = 0
                
                for i, statement in enumerate(statements, 1):
                    if statement.strip() and not statement.strip().startswith('--'):
                        try:
                            await conn.execute(text(statement))
                            executed += 1
                            
                            # Show progress for long migrations
                            if i % 10 == 0:
                                print(f"   Progress: {i}/{len(statements)} statements")
                                
                        except Exception as e:
                            # Some statements might fail if already executed
                            error_msg = str(e).lower()
                            if any(phrase in error_msg for phrase in [
                                "already exists",
                                "duplicate",
                                "constraint already exists"
                            ]):
                                warnings += 1
                                print(f"   ⚠️  Statement {i}: {e}")
                            else:
                                print(f"   ❌ Statement {i} failed: {e}")
                                await engine.dispose()
                                return False
                
                print(f"✅ Migration completed: {executed} statements executed, {warnings} warnings")
                await engine.dispose()
                return True
                
        except Exception as e:
            print(f"❌ Migration execution failed: {e}")
            return False
    
    def _split_sql_statements(self, sql: str) -> List[str]:
        """Split SQL script into individual statements."""
        # Simple SQL statement splitter
        # This handles basic cases but might need enhancement for complex SQL
        statements = []
        current_statement = []
        
        for line in sql.split('\n'):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('--'):
                continue
            
            current_statement.append(line)
            
            # Check if statement ends with semicolon
            if line.endswith(';'):
                statement = ' '.join(current_statement)
                if statement.strip():
                    statements.append(statement)
                current_statement = []
        
        # Add any remaining statement
        if current_statement:
            statement = ' '.join(current_statement)
            if statement.strip():
                statements.append(statement)
        
        return statements
    
    async def _verify_migration_success(self) -> bool:
        """Verify that migration was successful."""
        print("🔍 Verifying migration success...")
        
        if self.dry_run:
            print("🔍 DRY RUN: Would verify migration success")
            return True
        
        try:
            engine = create_async_engine(self.config.database.database_url)
            
            async with engine.begin() as conn:
                # Check that all required tables exist
                required_tables = [
                    'auth_users',
                    'auth_password_hashes',
                    'auth_sessions',
                    'auth_providers',
                    'user_identities',
                    'auth_password_reset_tokens',
                    'auth_email_verification_tokens',
                    'auth_events'
                ]
                
                missing_tables = []
                
                for table in required_tables:
                    result = await conn.execute(text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = '{table}'
                        )
                    """))
                    exists = result.fetchone()[0]
                    
                    if not exists:
                        missing_tables.append(table)
                
                if missing_tables:
                    print(f"❌ Migration verification failed. Missing tables: {', '.join(missing_tables)}")
                    await engine.dispose()
                    return False
                
                # Check that admin user was created
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM auth_users WHERE email = 'admin@ai-karen.local'
                """))
                admin_count = result.fetchone()[0]
                
                if admin_count == 0:
                    print("⚠️  Admin user was not created during migration")
                else:
                    print("✅ Admin user verified")
                
                # Check that functions were created
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.routines 
                    WHERE routine_name IN ('cleanup_expired_auth_sessions', 'get_auth_statistics')
                """))
                function_count = result.fetchone()[0]
                
                if function_count < 2:
                    print("⚠️  Some database functions may not have been created")
                else:
                    print("✅ Database functions verified")
                
                print("✅ Migration verification completed successfully")
                await engine.dispose()
                return True
                
        except Exception as e:
            print(f"❌ Migration verification failed: {e}")
            return False


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run authentication database migration")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--force", action="store_true", help="Run migration even if tables already exist")
    
    args = parser.parse_args()
    
    # Run migration
    runner = AuthMigrationRunner(dry_run=args.dry_run, force=args.force)
    success = await runner.run_migration()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())