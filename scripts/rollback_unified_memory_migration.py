#!/usr/bin/env python3
"""
Rollback Script: Unified Memory Migration Rollback
Phase 4.1 Database Schema Consolidation

Provides rollback procedures for safe migration reversal if needed:
- Restores data from backup files
- Recreates legacy table structures
- Validates rollback completion
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Error: psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_migration_rollback.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UnifiedMemoryMigrationRollback:
    """Rollback handler for unified memory migration"""
    
    def __init__(self, db_config: Dict[str, Any], backup_file: str, dry_run: bool = False):
        self.db_config = db_config
        self.backup_file = backup_file
        self.dry_run = dry_run
        self.backup_data = None
        
        # Legacy table schemas for recreation
        self.legacy_schemas = {
            'memory_items': """
                CREATE TABLE IF NOT EXISTS memory_items (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    scope TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding VECTOR(768),
                    metadata JSONB DEFAULT '{}'::JSONB,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_memory_items_scope_kind ON memory_items(scope, kind);
                CREATE INDEX IF NOT EXISTS idx_memory_items_embedding ON memory_items USING ivfflat (embedding vector_l2_ops);
            """,
            'memory_entries': """
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    vector_id VARCHAR(255) NOT NULL,
                    user_id UUID NOT NULL,
                    session_id VARCHAR(255),
                    content TEXT NOT NULL,
                    query TEXT,
                    result JSONB,
                    embedding_id VARCHAR(255),
                    memory_metadata JSONB DEFAULT '{}',
                    ttl TIMESTAMP,
                    timestamp INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    ui_source VARCHAR(50),
                    conversation_id UUID,
                    memory_type VARCHAR(50) DEFAULT 'general',
                    tags TEXT[] DEFAULT '{}',
                    importance_score INTEGER DEFAULT 5 CHECK (importance_score >= 1 AND importance_score <= 10),
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP,
                    ai_generated BOOLEAN DEFAULT FALSE,
                    user_confirmed BOOLEAN DEFAULT TRUE
                );
                CREATE INDEX IF NOT EXISTS idx_memory_entries_vector ON memory_entries(vector_id);
                CREATE INDEX IF NOT EXISTS idx_memory_entries_user ON memory_entries(user_id);
                CREATE INDEX IF NOT EXISTS idx_memory_entries_session ON memory_entries(session_id);
                CREATE INDEX IF NOT EXISTS idx_memory_entries_created ON memory_entries(created_at);
                CREATE INDEX IF NOT EXISTS idx_memory_entries_ttl ON memory_entries(ttl);
                CREATE INDEX IF NOT EXISTS idx_memory_entries_ui_source ON memory_entries(ui_source);
                CREATE INDEX IF NOT EXISTS idx_memory_entries_conversation ON memory_entries(conversation_id);
                CREATE INDEX IF NOT EXISTS idx_memory_entries_type ON memory_entries(memory_type);
                CREATE INDEX IF NOT EXISTS idx_memory_entries_tags ON memory_entries USING GIN(tags);
                CREATE INDEX IF NOT EXISTS idx_memory_entries_importance ON memory_entries(importance_score);
                CREATE INDEX IF NOT EXISTS idx_memory_entries_user_conversation ON memory_entries(user_id, conversation_id);
                CREATE INDEX IF NOT EXISTS idx_memory_entries_user_type ON memory_entries(user_id, memory_type);
            """,
            'web_ui_memory_entries': """
                CREATE TABLE IF NOT EXISTS web_ui_memory_entries (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    user_id UUID NULL,
                    ui_source TEXT NOT NULL,
                    session_id TEXT NULL,
                    memory_type TEXT NOT NULL,
                    tags JSONB NOT NULL DEFAULT '[]',
                    metadata JSONB NOT NULL DEFAULT '{}',
                    ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS web_ui_memory_entries_tenant_idx ON web_ui_memory_entries(tenant_id);
                CREATE INDEX IF NOT EXISTS web_ui_memory_entries_user_idx ON web_ui_memory_entries(user_id);
            """,
            'long_term_memory': """
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    user_id VARCHAR,
                    memory_json TEXT
                );
            """
        }
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password']
        )
    
    def load_backup(self) -> bool:
        """Load backup data from file"""
        try:
            if not os.path.exists(self.backup_file):
                logger.error(f"Backup file not found: {self.backup_file}")
                return False
            
            with open(self.backup_file, 'r') as f:
                self.backup_data = json.load(f)
            
            logger.info(f"Loaded backup from: {self.backup_file}")
            logger.info(f"Backup date: {self.backup_data.get('migration_date', 'unknown')}")
            
            tables_info = []
            for table_name, table_data in self.backup_data.get('tables', {}).items():
                tables_info.append(f"{table_name}: {table_data['count']} records")
            
            logger.info(f"Backup contains: {', '.join(tables_info)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load backup: {e}")
            return False
    
    def check_rollback_safety(self) -> bool:
        """Check if rollback is safe to perform"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if unified table exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'memories'
                        )
                    """)
                    
                    if not cur.fetchone()[0]:
                        logger.warning("Unified memories table does not exist - nothing to rollback")
                        return True
                    
                    # Check if there are new records in unified table since backup
                    backup_date = datetime.fromisoformat(self.backup_data['migration_date'].replace('Z', '+00:00'))
                    
                    cur.execute("""
                        SELECT COUNT(*) FROM memories 
                        WHERE created_at > %s
                    """, (backup_date,))
                    
                    new_records = cur.fetchone()[0]
                    
                    if new_records > 0:
                        logger.warning(f"Found {new_records} records created after backup date")
                        logger.warning("These records will be lost during rollback")
                        
                        # In production, you might want to require explicit confirmation
                        response = input("Continue with rollback? (yes/no): ")
                        if response.lower() != 'yes':
                            logger.info("Rollback cancelled by user")
                            return False
                    
                    # Check if legacy tables already exist
                    existing_legacy = []
                    for table_name in self.backup_data.get('tables', {}).keys():
                        cur.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = %s
                            )
                        """, (table_name,))
                        
                        if cur.fetchone()[0]:
                            existing_legacy.append(table_name)
                    
                    if existing_legacy:
                        logger.warning(f"Legacy tables already exist: {existing_legacy}")
                        logger.warning("These will be dropped and recreated")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            return False
    
    def recreate_legacy_tables(self) -> bool:
        """Recreate legacy table structures"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    for table_name in self.backup_data.get('tables', {}).keys():
                        if table_name not in self.legacy_schemas:
                            logger.warning(f"No schema available for table: {table_name}")
                            continue
                        
                        if self.dry_run:
                            logger.info(f"[DRY RUN] Would recreate table: {table_name}")
                            continue
                        
                        logger.info(f"Recreating table: {table_name}")
                        
                        # Drop existing table if it exists
                        cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                        
                        # Create table with schema
                        cur.execute(self.legacy_schemas[table_name])
                        
                        logger.info(f"Table {table_name} recreated successfully")
                    
                    if not self.dry_run:
                        conn.commit()
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to recreate legacy tables: {e}")
            return False
    
    def restore_data(self) -> bool:
        """Restore data from backup to legacy tables"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    total_restored = 0
                    
                    for table_name, table_data in self.backup_data.get('tables', {}).items():
                        if not table_data.get('data'):
                            logger.info(f"No data to restore for table: {table_name}")
                            continue
                        
                        records = table_data['data']
                        logger.info(f"Restoring {len(records)} records to {table_name}")
                        
                        if self.dry_run:
                            logger.info(f"[DRY RUN] Would restore {len(records)} records to {table_name}")
                            total_restored += len(records)
                            continue
                        
                        # Prepare insert statement
                        if not records:
                            continue
                        
                        sample_record = records[0]
                        columns = list(sample_record.keys())
                        placeholders = ', '.join(['%s'] * len(columns))
                        
                        insert_sql = f"""
                            INSERT INTO {table_name} ({', '.join(columns)})
                            VALUES ({placeholders})
                        """
                        
                        # Insert records
                        for record in records:
                            try:
                                values = [record.get(col) for col in columns]
                                cur.execute(insert_sql, values)
                                total_restored += 1
                            except Exception as e:
                                logger.error(f"Failed to restore record in {table_name}: {e}")
                        
                        logger.info(f"Restored {len(records)} records to {table_name}")
                    
                    if not self.dry_run:
                        conn.commit()
                    
                    logger.info(f"Total records restored: {total_restored}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to restore data: {e}")
            return False
    
    def cleanup_unified_schema(self) -> bool:
        """Clean up unified schema after successful rollback"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    if self.dry_run:
                        logger.info("[DRY RUN] Would drop unified schema tables")
                        return True
                    
                    # Drop unified tables
                    tables_to_drop = [
                        'memory_relationships',
                        'memory_access_log', 
                        'memories'
                    ]
                    
                    for table_name in tables_to_drop:
                        logger.info(f"Dropping table: {table_name}")
                        cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                    
                    # Drop helper functions
                    functions_to_drop = [
                        'calculate_decay_score',
                        'update_memory_access',
                        'create_memory_relationship',
                        'soft_delete_memory',
                        'calculate_expires_at',
                        'set_memory_defaults',
                        'update_updated_at_column'
                    ]
                    
                    for func_name in functions_to_drop:
                        logger.info(f"Dropping function: {func_name}")
                        cur.execute(f"DROP FUNCTION IF EXISTS {func_name} CASCADE")
                    
                    # Drop views
                    views_to_drop = [
                        'active_memories_with_decay',
                        'memory_relationship_details',
                        'memory_analytics_by_tenant',
                        'memory_audit_summary'
                    ]
                    
                    for view_name in views_to_drop:
                        logger.info(f"Dropping view: {view_name}")
                        cur.execute(f"DROP VIEW IF EXISTS {view_name} CASCADE")
                    
                    conn.commit()
                    logger.info("Unified schema cleanup completed")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to cleanup unified schema: {e}")
            return False
    
    def validate_rollback(self) -> bool:
        """Validate rollback was successful"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check that legacy tables exist and have data
                    for table_name, table_data in self.backup_data.get('tables', {}).items():
                        expected_count = table_data['count']
                        
                        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                        actual_count = cur.fetchone()[0]
                        
                        if actual_count != expected_count:
                            logger.error(f"Table {table_name}: expected {expected_count}, got {actual_count}")
                            return False
                        
                        logger.info(f"Table {table_name}: {actual_count} records (✓)")
                    
                    # Check that unified table is gone (if cleanup was performed)
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'memories'
                        )
                    """)
                    
                    if cur.fetchone()[0]:
                        logger.warning("Unified memories table still exists")
                    else:
                        logger.info("Unified memories table removed (✓)")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Rollback validation failed: {e}")
            return False
    
    def run_rollback(self) -> bool:
        """Run complete rollback process"""
        logger.info("Starting unified memory migration rollback...")
        
        # Load backup data
        if not self.load_backup():
            return False
        
        # Check rollback safety
        if not self.check_rollback_safety():
            return False
        
        # Recreate legacy tables
        if not self.recreate_legacy_tables():
            return False
        
        # Restore data
        if not self.restore_data():
            return False
        
        # Cleanup unified schema (optional, can be done separately)
        cleanup_response = input("Remove unified schema tables? (yes/no): ") if not self.dry_run else "no"
        if cleanup_response.lower() == 'yes':
            if not self.cleanup_unified_schema():
                logger.warning("Unified schema cleanup failed, but rollback data restoration succeeded")
        
        # Validate rollback
        if not self.dry_run and not self.validate_rollback():
            logger.error("Rollback validation failed")
            return False
        
        logger.info("Rollback completed successfully!")
        return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Rollback unified memory migration')
    parser.add_argument('backup_file', help='Path to backup file created during migration')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', default=5432, type=int, help='Database port')
    parser.add_argument('--database', default='ai_karen', help='Database name')
    parser.add_argument('--user', default='karen_user', help='Database user')
    parser.add_argument('--password', help='Database password')
    
    args = parser.parse_args()
    
    # Get password from environment if not provided
    password = args.password or os.getenv('POSTGRES_PASSWORD')
    if not password:
        logger.error("Database password required (use --password or POSTGRES_PASSWORD env var)")
        sys.exit(1)
    
    db_config = {
        'host': args.host,
        'port': args.port,
        'database': args.database,
        'user': args.user,
        'password': password
    }
    
    rollback = UnifiedMemoryMigrationRollback(db_config, args.backup_file, dry_run=args.dry_run)
    
    try:
        success = rollback.run_rollback()
        if success:
            print("✅ Rollback completed successfully")
            sys.exit(0)
        else:
            print("❌ Rollback failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Rollback interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during rollback: {e}")
        print(f"❌ Rollback failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()