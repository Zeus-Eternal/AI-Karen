#!/usr/bin/env python3
"""
Data Migration Script: Migrate to Unified Memory Schema
Phase 4.1 Database Schema Consolidation

Migrates existing memory data from legacy tables to the new unified memory schema:
- memory_items -> memories
- memory_entries -> memories  
- web_ui_memory_entries -> memories
- long_term_memory -> memories

Includes validation, rollback procedures, and comprehensive logging.
"""

import os
import sys
import json
import logging
import asyncio
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import asyncpg
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Error: Required packages not installed. Install with:")
    print("pip install asyncpg psycopg2-binary")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MigrationStats:
    """Statistics for migration tracking"""
    total_records: int = 0
    migrated_records: int = 0
    failed_records: int = 0
    skipped_records: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

class UnifiedMemoryMigration:
    """Main migration class for unified memory schema"""
    
    def __init__(self, db_config: Dict[str, Any], dry_run: bool = False):
        self.db_config = db_config
        self.dry_run = dry_run
        self.stats = MigrationStats()
        self.backup_file = f"memory_migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Legacy table mappings
        self.legacy_tables = {
            'memory_items': {
                'id_field': 'id',
                'content_field': 'content',
                'mapping': self._map_memory_items
            },
            'memory_entries': {
                'id_field': 'id', 
                'content_field': 'content',
                'mapping': self._map_memory_entries
            },
            'web_ui_memory_entries': {
                'id_field': 'id',
                'content_field': 'content', 
                'mapping': self._map_web_ui_memory_entries
            },
            'long_term_memory': {
                'id_field': 'user_id',  # No UUID, use user_id as identifier
                'content_field': 'memory_json',
                'mapping': self._map_long_term_memory
            }
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
    
    async def get_async_db_connection(self):
        """Get async database connection"""
        return await asyncpg.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password']
        )
    
    def check_prerequisites(self) -> bool:
        """Check if migration prerequisites are met"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if unified memories table exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'memories'
                        )
                    """)
                    
                    if not cur.fetchone()[0]:
                        logger.error("Unified 'memories' table does not exist. Run schema migration first.")
                        return False
                    
                    # Check if legacy tables exist
                    existing_tables = []
                    for table_name in self.legacy_tables.keys():
                        cur.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = %s
                            )
                        """, (table_name,))
                        
                        if cur.fetchone()[0]:
                            existing_tables.append(table_name)
                    
                    if not existing_tables:
                        logger.warning("No legacy memory tables found to migrate")
                        return True
                    
                    logger.info(f"Found legacy tables to migrate: {existing_tables}")
                    return True
                    
        except Exception as e:
            logger.error(f"Prerequisites check failed: {e}")
            return False
    
    def create_backup(self) -> bool:
        """Create backup of existing data"""
        try:
            backup_data = {
                'migration_date': datetime.now().isoformat(),
                'tables': {}
            }
            
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    for table_name in self.legacy_tables.keys():
                        # Check if table exists
                        cur.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = %s
                            )
                        """, (table_name,))
                        
                        if not cur.fetchone()[0]:
                            continue
                        
                        # Get table data
                        cur.execute(f"SELECT * FROM {table_name}")
                        rows = cur.fetchall()
                        
                        backup_data['tables'][table_name] = {
                            'count': len(rows),
                            'data': [dict(row) for row in rows]
                        }
                        
                        logger.info(f"Backed up {len(rows)} records from {table_name}")
            
            # Save backup to file
            with open(self.backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            logger.info(f"Backup created: {self.backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False
    
    def _map_memory_items(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map memory_items table row to unified schema"""
        return {
            'id': row.get('id'),
            'user_id': row.get('scope', 'unknown'),  # Use scope as user_id
            'org_id': None,
            'text': row.get('content', ''),
            'embedding_id': str(row.get('id')) if row.get('id') else None,
            'importance': 5,  # Default importance
            'decay_tier': 'medium',  # Default decay tier
            'tags': '[]',
            'meta': row.get('metadata', {}),
            'created_at': row.get('created_at', datetime.now(timezone.utc)),
            'session_id': None,
            'conversation_id': None,
            'ui_source': 'api',
            'memory_type': row.get('kind', 'general'),
            'ai_generated': False,
            'user_confirmed': True,
            'neuro_type': 'semantic',  # Default for memory_items
            'decay_lambda': 0.04,  # Semantic memory decay rate
            'source_table': 'memory_items'
        }
    
    def _map_memory_entries(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map memory_entries table row to unified schema"""
        return {
            'id': row.get('id'),
            'user_id': str(row.get('user_id', 'unknown')),
            'org_id': row.get('tenant_id'),
            'text': row.get('content', ''),
            'embedding_id': row.get('embedding_id'),
            'importance': row.get('importance_score', 5),
            'decay_tier': 'short',  # Default for memory_entries
            'tags': json.dumps(row.get('tags', [])),
            'meta': row.get('memory_metadata', {}),
            'created_at': row.get('created_at', datetime.now(timezone.utc)),
            'session_id': row.get('session_id'),
            'conversation_id': row.get('conversation_id'),
            'ui_source': row.get('ui_source', 'web'),
            'memory_type': row.get('memory_type', 'general'),
            'ai_generated': row.get('ai_generated', False),
            'user_confirmed': row.get('user_confirmed', True),
            'neuro_type': 'episodic',  # Default for memory_entries
            'decay_lambda': 0.12,  # Episodic memory decay rate
            'access_count': row.get('access_count', 0),
            'last_accessed': row.get('last_accessed'),
            'source_table': 'memory_entries'
        }
    
    def _map_web_ui_memory_entries(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Map web_ui_memory_entries table row to unified schema"""
        return {
            'id': row.get('id'),
            'user_id': str(row.get('user_id', 'unknown')),
            'org_id': row.get('tenant_id'),
            'text': row.get('content', ''),
            'embedding_id': None,  # Web UI entries may not have embeddings
            'importance': 5,  # Default importance
            'decay_tier': 'short',
            'tags': json.dumps(row.get('tags', [])),
            'meta': row.get('metadata', {}),
            'created_at': row.get('created_at', datetime.now(timezone.utc)),
            'session_id': row.get('session_id'),
            'conversation_id': None,
            'ui_source': row.get('ui_source', 'web'),
            'memory_type': row.get('memory_type', 'general'),
            'ai_generated': row.get('ai_generated', False),
            'user_confirmed': True,
            'neuro_type': 'episodic',
            'decay_lambda': 0.12,
            'source_table': 'web_ui_memory_entries'
        }
    
    def _map_long_term_memory(self, row: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Map long_term_memory table row to unified schema (may return multiple records)"""
        try:
            memory_data = json.loads(row.get('memory_json', '{}'))
            if not memory_data:
                return []
            
            # Handle different memory_json structures
            memories = []
            if isinstance(memory_data, list):
                # Array of memories
                for i, memory in enumerate(memory_data):
                    memories.append({
                        'id': None,  # Will be auto-generated
                        'user_id': row.get('user_id', 'unknown'),
                        'org_id': None,
                        'text': str(memory) if not isinstance(memory, dict) else memory.get('content', str(memory)),
                        'embedding_id': None,
                        'importance': 6,  # Slightly higher for long-term memories
                        'decay_tier': 'long',  # Long-term by definition
                        'tags': '[]',
                        'meta': {'original_index': i, 'source_data': memory},
                        'created_at': datetime.now(timezone.utc),
                        'ui_source': 'legacy',
                        'memory_type': 'general',
                        'ai_generated': False,
                        'user_confirmed': True,
                        'neuro_type': 'semantic',  # Long-term memories are typically semantic
                        'decay_lambda': 0.04,
                        'source_table': 'long_term_memory'
                    })
            elif isinstance(memory_data, dict):
                # Single memory object
                memories.append({
                    'id': None,
                    'user_id': row.get('user_id', 'unknown'),
                    'org_id': None,
                    'text': memory_data.get('content', str(memory_data)),
                    'embedding_id': None,
                    'importance': 6,
                    'decay_tier': 'long',
                    'tags': json.dumps(memory_data.get('tags', [])),
                    'meta': memory_data,
                    'created_at': datetime.now(timezone.utc),
                    'ui_source': 'legacy',
                    'memory_type': memory_data.get('type', 'general'),
                    'ai_generated': False,
                    'user_confirmed': True,
                    'neuro_type': 'semantic',
                    'decay_lambda': 0.04,
                    'source_table': 'long_term_memory'
                })
            
            return memories
            
        except json.JSONDecodeError:
            # Treat as plain text
            return [{
                'id': None,
                'user_id': row.get('user_id', 'unknown'),
                'org_id': None,
                'text': row.get('memory_json', ''),
                'embedding_id': None,
                'importance': 6,
                'decay_tier': 'long',
                'tags': '[]',
                'meta': {},
                'created_at': datetime.now(timezone.utc),
                'ui_source': 'legacy',
                'memory_type': 'general',
                'ai_generated': False,
                'user_confirmed': True,
                'neuro_type': 'semantic',
                'decay_lambda': 0.04,
                'source_table': 'long_term_memory'
            }]
    
    def migrate_table(self, table_name: str) -> Tuple[int, int]:
        """Migrate a single table to unified schema"""
        migrated = 0
        failed = 0
        
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check if table exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s
                        )
                    """, (table_name,))
                    
                    if not cur.fetchone()[0]:
                        logger.info(f"Table {table_name} does not exist, skipping")
                        return 0, 0
                    
                    # Get all records from legacy table
                    cur.execute(f"SELECT * FROM {table_name}")
                    rows = cur.fetchall()
                    
                    logger.info(f"Migrating {len(rows)} records from {table_name}")
                    
                    table_config = self.legacy_tables[table_name]
                    mapper = table_config['mapping']
                    
                    for row in rows:
                        try:
                            # Map the row to unified schema
                            mapped_data = mapper(row)
                            
                            # Handle cases where mapper returns multiple records
                            if isinstance(mapped_data, list):
                                records_to_insert = mapped_data
                            else:
                                records_to_insert = [mapped_data]
                            
                            for record in records_to_insert:
                                if self.dry_run:
                                    logger.info(f"[DRY RUN] Would insert: {record['text'][:50]}...")
                                    migrated += 1
                                else:
                                    # Insert into unified memories table
                                    insert_sql = """
                                        INSERT INTO memories (
                                            id, user_id, org_id, text, embedding_id, importance, 
                                            decay_tier, tags, meta, created_at, session_id, 
                                            conversation_id, ui_source, memory_type, ai_generated, 
                                            user_confirmed, neuro_type, decay_lambda, access_count, 
                                            last_accessed
                                        ) VALUES (
                                            COALESCE(%s, gen_random_uuid()), %s, %s, %s, %s, %s, 
                                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                        ) ON CONFLICT (id) DO NOTHING
                                    """
                                    
                                    cur.execute(insert_sql, (
                                        record.get('id'),
                                        record.get('user_id'),
                                        record.get('org_id'),
                                        record.get('text'),
                                        record.get('embedding_id'),
                                        record.get('importance'),
                                        record.get('decay_tier'),
                                        record.get('tags'),
                                        json.dumps(record.get('meta', {})),
                                        record.get('created_at'),
                                        record.get('session_id'),
                                        record.get('conversation_id'),
                                        record.get('ui_source'),
                                        record.get('memory_type'),
                                        record.get('ai_generated'),
                                        record.get('user_confirmed'),
                                        record.get('neuro_type'),
                                        record.get('decay_lambda'),
                                        record.get('access_count', 0),
                                        record.get('last_accessed')
                                    ))
                                    
                                    migrated += 1
                        
                        except Exception as e:
                            logger.error(f"Failed to migrate record from {table_name}: {e}")
                            failed += 1
                    
                    if not self.dry_run:
                        conn.commit()
                    
                    logger.info(f"Completed {table_name}: {migrated} migrated, {failed} failed")
                    
        except Exception as e:
            logger.error(f"Failed to migrate table {table_name}: {e}")
            failed += len(rows) if 'rows' in locals() else 0
        
        return migrated, failed
    
    def validate_migration(self) -> bool:
        """Validate the migration results"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Count records in unified table
                    cur.execute("SELECT COUNT(*) FROM memories")
                    unified_count = cur.fetchone()[0]
                    
                    # Count records in legacy tables
                    legacy_count = 0
                    for table_name in self.legacy_tables.keys():
                        cur.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = %s
                            )
                        """, (table_name,))
                        
                        if cur.fetchone()[0]:
                            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                            count = cur.fetchone()[0]
                            legacy_count += count
                            logger.info(f"Legacy table {table_name}: {count} records")
                    
                    logger.info(f"Unified table: {unified_count} records")
                    logger.info(f"Legacy tables total: {legacy_count} records")
                    
                    # Check for data integrity
                    cur.execute("""
                        SELECT COUNT(*) FROM memories 
                        WHERE user_id IS NULL OR text IS NULL OR text = ''
                    """)
                    invalid_count = cur.fetchone()[0]
                    
                    if invalid_count > 0:
                        logger.warning(f"Found {invalid_count} records with missing required fields")
                    
                    # Check tenant isolation
                    cur.execute("""
                        SELECT COUNT(DISTINCT user_id) as users,
                               COUNT(DISTINCT org_id) as orgs
                        FROM memories
                    """)
                    tenant_stats = cur.fetchone()
                    logger.info(f"Tenant distribution: {tenant_stats[0]} users, {tenant_stats[1]} orgs")
                    
                    return invalid_count == 0
                    
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Run the complete migration"""
        self.stats.start_time = datetime.now()
        
        logger.info("Starting unified memory schema migration...")
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Create backup
        if not self.dry_run and not self.create_backup():
            logger.error("Backup creation failed, aborting migration")
            return False
        
        # Migrate each table
        total_migrated = 0
        total_failed = 0
        
        for table_name in self.legacy_tables.keys():
            migrated, failed = self.migrate_table(table_name)
            total_migrated += migrated
            total_failed += failed
        
        self.stats.migrated_records = total_migrated
        self.stats.failed_records = total_failed
        self.stats.end_time = datetime.now()
        
        # Validate migration
        if not self.dry_run:
            validation_success = self.validate_migration()
            if not validation_success:
                logger.error("Migration validation failed")
                return False
        
        logger.info(f"Migration completed: {total_migrated} migrated, {total_failed} failed")
        logger.info(f"Duration: {self.stats.duration():.2f} seconds")
        
        if not self.dry_run:
            logger.info(f"Backup saved to: {self.backup_file}")
        
        return total_failed == 0

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Migrate to unified memory schema')
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
    
    migration = UnifiedMemoryMigration(db_config, dry_run=args.dry_run)
    
    try:
        success = migration.run_migration()
        if success:
            print("✅ Migration completed successfully")
            sys.exit(0)
        else:
            print("❌ Migration failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        print(f"❌ Migration failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()