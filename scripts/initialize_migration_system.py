#!/usr/bin/env python3
"""
Initialize Migration System

This script creates the migration_history table and sets up the migration system
for the AI Karen database.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment or config."""
    # Try environment variable first
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url
    
    # Try to construct from individual components
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5434')  # Default to Docker port
    db_name = os.getenv('DB_NAME', 'ai_karen')
    db_user = os.getenv('DB_USER', 'karen_user')
    db_password = os.getenv('DB_PASSWORD', 'karen_password')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def create_migration_history_table(cursor):
    """Create the migration_history table."""
    logger.info("Creating migration_history table...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migration_history (
            id SERIAL PRIMARY KEY,
            migration_name VARCHAR(255) NOT NULL,
            service VARCHAR(50) NOT NULL DEFAULT 'postgres',
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            status VARCHAR(20) NOT NULL DEFAULT 'applied',
            checksum VARCHAR(64),
            execution_time_ms INTEGER DEFAULT 0,
            UNIQUE(migration_name, service)
        )
    """)
    
    # Create index for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_migration_history_service_applied 
        ON migration_history(service, applied_at DESC)
    """)
    
    logger.info("Migration history table created successfully")


def record_existing_migrations(cursor):
    """Record existing migrations that have already been applied."""
    logger.info("Recording existing migrations...")
    
    # List of migrations that should be considered as already applied
    # based on the existing database schema
    existing_migrations = [
        "001_create_auth_tables.sql",
        "001_create_tables.sql", 
        "002_create_extension_tables.sql",
        "002_create_memory_entries_table.sql",
        "003_web_ui_integration.sql",
        "004_create_memory_entries_table.sql",
        "005_create_conversations_table.sql",
        "006_create_plugin_executions_table.sql",
        "007_create_audit_log_table.sql",
        "008_create_web_ui_memory_entries_table.sql",
        "009_create_memory_items_table.sql",
        "009_create_production_auth_tables.sql",
        "010_add_production_auth_columns.sql",
        "011_add_messages_table.sql",
        "012_create_usage_and_rate_limit_tables.sql",
        "013_production_auth_schema_alignment.sql",
        "014_fix_user_id_type_mismatch.sql",
        "015_neuro_vault_schema_extensions.sql",
        "016_unified_memory_schema.sql",
        "017_case_memory.sql",
        "018_admin_management_system.sql",
        "019_performance_optimization_indexes.sql",
        "020_admin_system_production_deployment.sql",
        "021_admin_system_rollback.sql"
    ]
    
    # Check which tables exist to determine which migrations have been applied
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    logger.info(f"Found {len(existing_tables)} existing tables")
    
    # Record migrations based on existing schema
    applied_migrations = []
    
    # Basic auth tables indicate early migrations
    if 'auth_users' in existing_tables:
        applied_migrations.extend([
            "001_create_auth_tables.sql",
            "009_create_production_auth_tables.sql",
            "013_production_auth_schema_alignment.sql"
        ])
    
    # Memory tables
    if 'memory_entries' in existing_tables:
        applied_migrations.extend([
            "002_create_memory_entries_table.sql",
            "016_unified_memory_schema.sql"
        ])
    
    # Extension tables
    if 'extensions' in existing_tables:
        applied_migrations.append("002_create_extension_tables.sql")
    
    # Conversations
    if 'conversations' in existing_tables:
        applied_migrations.append("005_create_conversations_table.sql")
    
    # Admin system
    if 'audit_logs' in existing_tables:
        applied_migrations.extend([
            "018_admin_management_system.sql",
            "021_admin_system_rollback.sql"
        ])
    
    # Remove duplicates and sort
    applied_migrations = sorted(list(set(applied_migrations)))
    
    # Insert migration records
    for migration in applied_migrations:
        try:
            cursor.execute("""
                INSERT INTO migration_history (migration_name, service, applied_at, status)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (migration_name, service) DO NOTHING
            """, (migration, 'postgres', datetime.utcnow(), 'applied'))
            logger.info(f"Recorded migration: {migration}")
        except Exception as e:
            logger.warning(f"Could not record migration {migration}: {e}")
    
    logger.info(f"Recorded {len(applied_migrations)} existing migrations")


def initialize_migration_system():
    """Initialize the migration system."""
    db_url = get_database_url()
    
    try:
        # Connect to database
        logger.info(f"Connecting to database...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Create migration_history table
            create_migration_history_table(cursor)
            
            # Record existing migrations
            record_existing_migrations(cursor)
            
            # Commit changes
            conn.commit()
            
            # Verify setup
            cursor.execute("""
                SELECT COUNT(*) as migration_count 
                FROM migration_history 
                WHERE service = 'postgres'
            """)
            count = cursor.fetchone()['migration_count']
            
            logger.info(f"Migration system initialized with {count} recorded migrations")
            
            # Show latest migration
            cursor.execute("""
                SELECT migration_name, applied_at, status
                FROM migration_history
                WHERE service = 'postgres'
                ORDER BY applied_at DESC
                LIMIT 1
            """)
            latest = cursor.fetchone()
            if latest:
                logger.info(f"Latest migration: {latest['migration_name']} ({latest['status']})")
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to initialize migration system: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()


def main():
    """Main function."""
    logger.info("Migration System Initialization")
    logger.info("=" * 40)
    
    if initialize_migration_system():
        logger.info("Migration system initialized successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Apply the enhanced auth migration:")
        logger.info("   python scripts/apply_enhanced_auth_migration.py")
        logger.info("2. Restart your application services")
        sys.exit(0)
    else:
        logger.error("Migration system initialization failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()