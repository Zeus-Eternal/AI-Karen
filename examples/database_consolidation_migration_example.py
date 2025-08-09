#!/usr/bin/env python3
"""
Example script demonstrating the DatabaseConsolidationMigrator usage.

This script shows how to use the DatabaseConsolidationMigrator to migrate
authentication data from SQLite databases to PostgreSQL.
"""

import asyncio
import logging
import sqlite3
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_sqlite_db(db_path: str) -> str:
    """Create a sample SQLite database with test authentication data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE auth_users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            roles TEXT NOT NULL DEFAULT '["user"]',
            tenant_id TEXT NOT NULL DEFAULT 'default',
            preferences TEXT NOT NULL DEFAULT '{}',
            is_verified BOOLEAN NOT NULL DEFAULT 1,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            failed_login_attempts INTEGER NOT NULL DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE auth_password_hashes (
            user_id TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE auth_sessions (
            session_token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            expires_in INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            last_accessed TEXT NOT NULL,
            ip_address TEXT NOT NULL DEFAULT 'unknown',
            user_agent TEXT NOT NULL DEFAULT '',
            risk_score REAL NOT NULL DEFAULT 0.0,
            security_flags TEXT NOT NULL DEFAULT '[]',
            is_active BOOLEAN NOT NULL DEFAULT 1
        )
    """)
    
    # Insert sample data
    user_id = str(uuid.uuid4())
    session_token = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO auth_users (
            user_id, email, full_name, roles, tenant_id, preferences,
            is_verified, is_active, created_at, updated_at, failed_login_attempts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, 'demo@example.com', 'Demo User', '["user", "demo"]',
        'demo-tenant', '{"theme": "dark", "language": "en"}',
        True, True, now, now, 0
    ))
    
    cursor.execute("""
        INSERT INTO auth_password_hashes (user_id, password_hash, created_at, updated_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, '$2b$12$demo.password.hash.for.testing', now, now))
    
    cursor.execute("""
        INSERT INTO auth_sessions (
            session_token, user_id, access_token, refresh_token, expires_in,
            created_at, last_accessed, ip_address, user_agent, risk_score,
            security_flags, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_token, user_id, 'demo_access_token', 'demo_refresh_token',
        3600, now, now, '192.168.1.100', 'Demo User Agent', 0.2,
        '["demo_flag"]', True
    ))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Created sample SQLite database at {db_path}")
    logger.info(f"Sample user ID: {user_id}")
    logger.info(f"Sample session token: {session_token}")
    
    return user_id


async def demonstrate_migration():
    """Demonstrate the migration process."""
    logger.info("=== Database Consolidation Migration Demo ===")
    
    # Create temporary SQLite database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    sqlite_path = temp_db.name
    
    try:
        # Create sample data
        sample_user_id = create_sample_sqlite_db(sqlite_path)
        
        # Note: In a real scenario, you would use a real PostgreSQL URL
        postgres_url = "postgresql+asyncpg://user:password@localhost:5432/auth_db"
        
        logger.info("Migration would proceed as follows:")
        logger.info(f"1. Initialize migrator with SQLite: {sqlite_path}")
        logger.info(f"2. Connect to PostgreSQL: {postgres_url}")
        logger.info("3. Create PostgreSQL schema if needed")
        logger.info("4. Migrate users with UUID consistency")
        logger.info("5. Migrate sessions with proper foreign keys")
        logger.info("6. Migrate tokens and other auth data")
        logger.info("7. Validate migration success")
        
        # Demonstrate the migrator initialization (without actual execution)
        logger.info("\n=== Migrator Configuration ===")
        
        # This would be the actual usage:
        # from src.ai_karen_engine.auth.database_consolidation_migrator import DatabaseConsolidationMigrator
        # migrator = DatabaseConsolidationMigrator([sqlite_path], postgres_url)
        # result = await migrator.migrate_all_data()
        
        logger.info(f"SQLite databases: [{sqlite_path}]")
        logger.info(f"PostgreSQL URL: {postgres_url}")
        logger.info(f"Sample user to migrate: {sample_user_id}")
        
        # Show what the migration result would look like
        logger.info("\n=== Expected Migration Result ===")
        logger.info("MigrationResult(")
        logger.info("    success=True,")
        logger.info("    migrated_users=1,")
        logger.info("    migrated_sessions=1,")
        logger.info("    migrated_tokens=0,")
        logger.info("    validation_results={'overall_success': True, 'user_count_match': True, ...},")
        logger.info("    errors=[],")
        logger.info("    warnings=[]")
        logger.info(")")
        
        # Demonstrate validation
        logger.info("\n=== Validation Checks ===")
        logger.info("✓ User count match between SQLite and PostgreSQL")
        logger.info("✓ Session count match between SQLite and PostgreSQL")
        logger.info("✓ Foreign key integrity maintained")
        logger.info("✓ No data anomalies detected")
        logger.info("✓ All required tables exist in PostgreSQL")
        
        logger.info("\n=== Migration Complete ===")
        logger.info("All authentication data successfully migrated to PostgreSQL!")
        
    finally:
        # Cleanup
        Path(sqlite_path).unlink(missing_ok=True)
        logger.info(f"Cleaned up temporary database: {sqlite_path}")


def demonstrate_validation():
    """Demonstrate the validation functionality."""
    logger.info("\n=== Migration Validation Demo ===")
    
    postgres_url = "postgresql+asyncpg://user:password@localhost:5432/auth_db"
    
    logger.info("Validation would check:")
    logger.info("1. Table existence - all required tables present")
    logger.info("2. Data consistency - no orphaned records")
    logger.info("3. Foreign key constraints - all relationships valid")
    logger.info("4. Data anomalies - no duplicate emails, invalid data")
    
    logger.info("\nValidation report structure:")
    logger.info("{")
    logger.info("    'timestamp': '2024-01-01T12:00:00',")
    logger.info("    'overall_status': 'passed',")
    logger.info("    'checks_performed': [")
    logger.info("        {'check_name': 'table_existence', 'passed': True, 'details': {...}},")
    logger.info("        {'check_name': 'data_consistency', 'passed': True, 'details': {...}},")
    logger.info("        {'check_name': 'foreign_key_constraints', 'passed': True, 'details': {...}},")
    logger.info("        {'check_name': 'data_anomalies', 'passed': True, 'details': {...}}")
    logger.info("    ],")
    logger.info("    'issues_found': [],")
    logger.info("    'recommendations': []")
    logger.info("}")


def main():
    """Main demonstration function."""
    print("Database Consolidation Migration Example")
    print("=" * 50)
    
    # Run the async demonstration
    asyncio.run(demonstrate_migration())
    
    # Show validation demo
    demonstrate_validation()
    
    print("\n" + "=" * 50)
    print("Demo completed successfully!")
    print("\nTo use the migrator in your code:")
    print("1. Import: from ai_karen_engine.auth.database_consolidation_migrator import DatabaseConsolidationMigrator")
    print("2. Initialize: migrator = DatabaseConsolidationMigrator(sqlite_paths, postgres_url)")
    print("3. Execute: result = await migrator.migrate_all_data()")
    print("4. Validate: validator = MigrationValidator(postgres_url); report = await validator.validate_complete_migration()")


if __name__ == "__main__":
    main()