#!/usr/bin/env python3
"""
NeuroVault Database Migration Runner
Safely applies the NeuroVault schema extensions to the existing database.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.database.client import MultiTenantPostgresClient
from ai_karen_engine.database.config import DatabaseConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NeuroVaultMigrationRunner:
    """Handles the NeuroVault database schema migration."""
    
    def __init__(self, db_client: MultiTenantPostgresClient):
        self.db_client = db_client
        self.migration_file = Path(__file__).parent.parent / "data/migrations/postgres/015_neuro_vault_schema_extensions.sql"
    
    async def check_prerequisites(self) -> bool:
        """Check if the database is ready for NeuroVault migration."""
        try:
            async with self.db_client.get_async_session() as session:
                # Check if memory_items table exists
                result = await session.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'memory_items'
                    );
                """)
                memory_items_exists = result.scalar()
                
                if not memory_items_exists:
                    logger.error("memory_items table does not exist. Please run base migrations first.")
                    return False
                
                # Check if NeuroVault columns already exist
                result = await session.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'memory_items' 
                    AND column_name IN ('neuro_type', 'decay_lambda', 'reflection_count');
                """)
                existing_columns = [row[0] for row in result.fetchall()]
                
                if existing_columns:
                    logger.warning(f"NeuroVault columns already exist: {existing_columns}")
                    logger.info("Migration may have already been applied. Proceeding with caution...")
                
                # Check if memory_relationships table exists
                result = await session.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'memory_relationships'
                    );
                """)
                relationships_exists = result.scalar()
                
                if relationships_exists:
                    logger.warning("memory_relationships table already exists. Migration may have been applied.")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to check prerequisites: {e}")
            return False
    
    async def backup_existing_data(self) -> bool:
        """Create a backup of existing memory data before migration."""
        try:
            backup_table_name = f"memory_items_backup_{int(asyncio.get_event_loop().time())}"
            
            async with self.db_client.get_async_session() as session:
                # Create backup table
                await session.execute(f"""
                    CREATE TABLE {backup_table_name} AS 
                    SELECT * FROM memory_items;
                """)
                
                # Get count of backed up records
                result = await session.execute(f"SELECT COUNT(*) FROM {backup_table_name};")
                backup_count = result.scalar()
                
                await session.commit()
                
                logger.info(f"Created backup table '{backup_table_name}' with {backup_count} records")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    async def apply_migration(self) -> bool:
        """Apply the NeuroVault schema migration."""
        try:
            if not self.migration_file.exists():
                logger.error(f"Migration file not found: {self.migration_file}")
                return False
            
            # Read migration SQL
            migration_sql = self.migration_file.read_text()
            
            async with self.db_client.get_async_session() as session:
                # Execute migration in a transaction
                logger.info("Applying NeuroVault schema extensions...")
                
                # Split SQL into individual statements and execute
                statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
                
                for i, statement in enumerate(statements):
                    if statement.upper().startswith(('CREATE', 'ALTER', 'INSERT', 'UPDATE')):
                        try:
                            await session.execute(statement)
                            logger.debug(f"Executed statement {i+1}/{len(statements)}")
                        except Exception as e:
                            # Log warning for statements that might already exist
                            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                                logger.warning(f"Statement {i+1} skipped (already exists): {e}")
                            else:
                                raise
                
                await session.commit()
                logger.info("NeuroVault schema migration completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to apply migration: {e}")
            return False
    
    async def verify_migration(self) -> bool:
        """Verify that the migration was applied correctly."""
        try:
            async with self.db_client.get_async_session() as session:
                # Check NeuroVault columns exist
                result = await session.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'memory_items' 
                    AND column_name IN (
                        'neuro_type', 'decay_lambda', 'reflection_count', 
                        'source_memories', 'derived_memories', 'importance_decay',
                        'last_reflection', 'importance_score', 'access_count'
                    );
                """)
                neuro_columns = [row[0] for row in result.fetchall()]
                
                expected_columns = [
                    'neuro_type', 'decay_lambda', 'reflection_count',
                    'source_memories', 'derived_memories', 'importance_decay',
                    'last_reflection', 'importance_score', 'access_count'
                ]
                
                missing_columns = set(expected_columns) - set(neuro_columns)
                if missing_columns:
                    logger.error(f"Missing NeuroVault columns: {missing_columns}")
                    return False
                
                # Check memory_relationships table exists
                result = await session.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'memory_relationships'
                    );
                """)
                relationships_exists = result.scalar()
                
                if not relationships_exists:
                    logger.error("memory_relationships table was not created")
                    return False
                
                # Check functions exist
                result = await session.execute("""
                    SELECT routine_name 
                    FROM information_schema.routines 
                    WHERE routine_schema = 'public' 
                    AND routine_name IN (
                        'calculate_decay_score', 'update_memory_access', 'create_memory_relationship'
                    );
                """)
                functions = [row[0] for row in result.fetchall()]
                
                expected_functions = ['calculate_decay_score', 'update_memory_access', 'create_memory_relationship']
                missing_functions = set(expected_functions) - set(functions)
                if missing_functions:
                    logger.error(f"Missing NeuroVault functions: {missing_functions}")
                    return False
                
                # Check views exist
                result = await session.execute("""
                    SELECT table_name 
                    FROM information_schema.views 
                    WHERE table_schema = 'public' 
                    AND table_name IN (
                        'active_memories_with_decay', 'memory_relationship_details', 'memory_analytics'
                    );
                """)
                views = [row[0] for row in result.fetchall()]
                
                expected_views = ['active_memories_with_decay', 'memory_relationship_details', 'memory_analytics']
                missing_views = set(expected_views) - set(views)
                if missing_views:
                    logger.error(f"Missing NeuroVault views: {missing_views}")
                    return False
                
                logger.info("NeuroVault migration verification completed successfully")
                logger.info(f"Added columns: {neuro_columns}")
                logger.info(f"Created functions: {functions}")
                logger.info(f"Created views: {views}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to verify migration: {e}")
            return False
    
    async def run_migration(self, create_backup: bool = True) -> bool:
        """Run the complete NeuroVault migration process."""
        logger.info("Starting NeuroVault database migration...")
        
        # Step 1: Check prerequisites
        if not await self.check_prerequisites():
            logger.error("Prerequisites check failed. Aborting migration.")
            return False
        
        # Step 2: Create backup (optional)
        if create_backup:
            if not await self.backup_existing_data():
                logger.error("Backup creation failed. Aborting migration.")
                return False
        
        # Step 3: Apply migration
        if not await self.apply_migration():
            logger.error("Migration application failed.")
            return False
        
        # Step 4: Verify migration
        if not await self.verify_migration():
            logger.error("Migration verification failed.")
            return False
        
        logger.info("NeuroVault database migration completed successfully!")
        return True


async def main():
    """Main entry point for the migration runner."""
    try:
        # Initialize database client
        config = DatabaseConfig()
        db_client = MultiTenantPostgresClient(config)
        
        # Initialize and run migration
        migration_runner = NeuroVaultMigrationRunner(db_client)
        
        # Check command line arguments
        create_backup = "--no-backup" not in sys.argv
        
        success = await migration_runner.run_migration(create_backup=create_backup)
        
        if success:
            logger.info("Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("Migration failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Migration runner failed: {e}")
        sys.exit(1)
    finally:
        # Close database connections
        if 'db_client' in locals():
            await db_client.close()


if __name__ == "__main__":
    asyncio.run(main())