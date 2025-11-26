#!/usr/bin/env python3
"""
Apply Enhanced Authentication Migration

This script applies the new enhanced authentication and validation system migration
to update the database schema for the improved AuthService.
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
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'ai_karen')
    db_user = os.getenv('DB_USER', 'karen_user')
    db_password = os.getenv('DB_PASSWORD', 'karen_password')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def check_migration_history_table(cursor):
    """Check if migration_history table exists."""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'migration_history'
        )
    """)
    return cursor.fetchone()[0]


def get_latest_migration(cursor):
    """Get the latest applied migration."""
    cursor.execute("""
        SELECT migration_name, applied_at, status
        FROM migration_history
        WHERE service = 'postgres'
        ORDER BY applied_at DESC
        LIMIT 1
    """)
    return cursor.fetchone()


def record_migration(cursor, migration_name, status='applied'):
    """Record migration in migration_history table."""
    cursor.execute("""
        INSERT INTO migration_history (
            migration_name,
            service,
            applied_at,
            status,
            checksum,
            execution_time_ms
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        migration_name,
        'postgres',
        datetime.utcnow(),
        status,
        'enhanced_auth_validation',  # Simple checksum
        0  # Execution time would be calculated in real implementation
    ))


def apply_migration():
    """Apply the enhanced authentication migration."""
    db_url = get_database_url()
    migration_file = project_root / "data" / "migrations" / "postgres" / "022_enhanced_auth_validation_system.sql"
    
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False
    
    try:
        # Connect to database
        logger.info(f"Connecting to database...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check if migration_history table exists
            if not check_migration_history_table(cursor):
                logger.error("migration_history table not found. Please run initial migrations first.")
                return False
            
            # Check current migration status
            latest_migration = get_latest_migration(cursor)
            if latest_migration:
                logger.info(f"Current migration: {latest_migration['migration_name']} ({latest_migration['status']})")
                
                # Check if this migration is already applied
                if latest_migration['migration_name'] == '022_enhanced_auth_validation_system.sql':
                    logger.info("Enhanced authentication migration already applied.")
                    return True
            
            # Read migration file
            logger.info(f"Reading migration file: {migration_file}")
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            # Apply migration
            logger.info("Applying enhanced authentication migration...")
            cursor.execute(migration_sql)
            
            # Record migration
            record_migration(cursor, '022_enhanced_auth_validation_system.sql')
            
            # Commit transaction
            conn.commit()
            logger.info("Enhanced authentication migration applied successfully!")
            
            # Verify migration
            logger.info("Verifying migration...")
            cursor.execute("SELECT * FROM auth_statistics_enhanced")
            stats = cursor.fetchone()
            if stats:
                logger.info(f"Migration verified. Total users: {stats['total_users']}")
            
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()


def main():
    """Main function."""
    logger.info("Enhanced Authentication Migration Tool")
    logger.info("=" * 50)
    
    if apply_migration():
        logger.info("Migration completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Restart your application services")
        logger.info("2. Test authentication with the new features")
        logger.info("3. Check the auth_statistics_enhanced view for metrics")
        sys.exit(0)
    else:
        logger.error("Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()