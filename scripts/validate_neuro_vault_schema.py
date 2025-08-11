#!/usr/bin/env python3
"""
NeuroVault Schema Validation Script
Validates that the NeuroVault schema extensions are properly applied.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

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


class NeuroVaultSchemaValidator:
    """Validates the NeuroVault database schema."""
    
    def __init__(self, db_client: MultiTenantPostgresClient):
        self.db_client = db_client
        self.validation_results = {}
    
    async def validate_memory_items_columns(self) -> bool:
        """Validate that all required NeuroVault columns exist in memory_items table."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute("""
                    SELECT column_name, data_type, column_default, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'memory_items' 
                    ORDER BY column_name;
                """)
                columns = {row[0]: {'type': row[1], 'default': row[2], 'nullable': row[3]} 
                          for row in result.fetchall()}
                
                required_columns = {
                    'neuro_type': 'character varying',
                    'decay_lambda': 'real',
                    'reflection_count': 'integer',
                    'source_memories': 'jsonb',
                    'derived_memories': 'jsonb',
                    'importance_decay': 'real',
                    'last_reflection': 'timestamp with time zone',
                    'importance_score': 'integer',
                    'access_count': 'integer',
                    'last_accessed': 'timestamp with time zone',
                    'user_id': 'uuid',
                    'tenant_id': 'uuid',
                    'session_id': 'character varying',
                    'memory_type': 'character varying',
                    'ui_source': 'character varying',
                    'conversation_id': 'uuid',
                    'ai_generated': 'boolean',
                    'user_confirmed': 'boolean',
                    'tags': 'jsonb'
                }
                
                missing_columns = []
                wrong_type_columns = []
                
                for col_name, expected_type in required_columns.items():
                    if col_name not in columns:
                        missing_columns.append(col_name)
                    elif expected_type not in columns[col_name]['type']:
                        wrong_type_columns.append(f"{col_name} (expected {expected_type}, got {columns[col_name]['type']})")
                
                if missing_columns:
                    logger.error(f"Missing columns in memory_items: {missing_columns}")
                    self.validation_results['memory_items_columns'] = False
                    return False
                
                if wrong_type_columns:
                    logger.error(f"Wrong column types in memory_items: {wrong_type_columns}")
                    self.validation_results['memory_items_columns'] = False
                    return False
                
                logger.info(f"✓ All {len(required_columns)} NeuroVault columns exist in memory_items table")
                self.validation_results['memory_items_columns'] = True
                return True
                
        except Exception as e:
            logger.error(f"Failed to validate memory_items columns: {e}")
            self.validation_results['memory_items_columns'] = False
            return False
    
    async def validate_memory_relationships_table(self) -> bool:
        """Validate that the memory_relationships table exists with correct structure."""
        try:
            async with self.db_client.get_async_session() as session:
                # Check table exists
                result = await session.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'memory_relationships'
                    );
                """)
                table_exists = result.scalar()
                
                if not table_exists:
                    logger.error("memory_relationships table does not exist")
                    self.validation_results['memory_relationships_table'] = False
                    return False
                
                # Check columns
                result = await session.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'memory_relationships' 
                    ORDER BY column_name;
                """)
                columns = {row[0]: {'type': row[1], 'nullable': row[2]} 
                          for row in result.fetchall()}
                
                required_columns = {
                    'id': 'uuid',
                    'source_memory_id': 'uuid',
                    'derived_memory_id': 'uuid',
                    'relationship_type': 'character varying',
                    'confidence_score': 'real',
                    'metadata': 'jsonb',
                    'created_at': 'timestamp with time zone',
                    'updated_at': 'timestamp with time zone'
                }
                
                missing_columns = []
                for col_name, expected_type in required_columns.items():
                    if col_name not in columns:
                        missing_columns.append(col_name)
                    elif expected_type not in columns[col_name]['type']:
                        missing_columns.append(f"{col_name} (wrong type)")
                
                if missing_columns:
                    logger.error(f"Missing/incorrect columns in memory_relationships: {missing_columns}")
                    self.validation_results['memory_relationships_table'] = False
                    return False
                
                logger.info("✓ memory_relationships table exists with correct structure")
                self.validation_results['memory_relationships_table'] = True
                return True
                
        except Exception as e:
            logger.error(f"Failed to validate memory_relationships table: {e}")
            self.validation_results['memory_relationships_table'] = False
            return False
    
    async def validate_indexes(self) -> bool:
        """Validate that all required indexes exist."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename IN ('memory_items', 'memory_relationships')
                    AND schemaname = 'public';
                """)
                existing_indexes = {row[0] for row in result.fetchall()}
                
                required_indexes = {
                    'idx_memory_items_neuro_type',
                    'idx_memory_items_decay',
                    'idx_memory_items_reflection',
                    'idx_memory_items_importance',
                    'idx_memory_items_access_count',
                    'idx_memory_items_tenant_user',
                    'idx_memory_items_conversation',
                    'idx_memory_items_session',
                    'idx_memory_items_memory_type',
                    'idx_memory_items_ui_source',
                    'idx_memory_items_ai_generated',
                    'idx_memory_items_tags',
                    'idx_memory_relationships_source',
                    'idx_memory_relationships_derived',
                    'idx_memory_relationships_type',
                    'idx_memory_relationships_created',
                    'idx_memory_relationships_confidence',
                    'idx_memory_relationships_unique'
                }
                
                missing_indexes = required_indexes - existing_indexes
                
                if missing_indexes:
                    logger.warning(f"Missing indexes (may affect performance): {missing_indexes}")
                    # Don't fail validation for missing indexes, just warn
                
                found_indexes = required_indexes & existing_indexes
                logger.info(f"✓ Found {len(found_indexes)}/{len(required_indexes)} NeuroVault indexes")
                
                self.validation_results['indexes'] = True
                return True
                
        except Exception as e:
            logger.error(f"Failed to validate indexes: {e}")
            self.validation_results['indexes'] = False
            return False
    
    async def validate_functions(self) -> bool:
        """Validate that all required functions exist."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute("""
                    SELECT routine_name 
                    FROM information_schema.routines 
                    WHERE routine_schema = 'public' 
                    AND routine_type = 'FUNCTION';
                """)
                existing_functions = {row[0] for row in result.fetchall()}
                
                required_functions = {
                    'calculate_decay_score',
                    'update_memory_access',
                    'create_memory_relationship',
                    'set_default_decay_lambda',
                    'update_updated_at_column'
                }
                
                missing_functions = required_functions - existing_functions
                
                if missing_functions:
                    logger.error(f"Missing NeuroVault functions: {missing_functions}")
                    self.validation_results['functions'] = False
                    return False
                
                logger.info(f"✓ All {len(required_functions)} NeuroVault functions exist")
                self.validation_results['functions'] = True
                return True
                
        except Exception as e:
            logger.error(f"Failed to validate functions: {e}")
            self.validation_results['functions'] = False
            return False
    
    async def validate_views(self) -> bool:
        """Validate that all required views exist."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute("""
                    SELECT table_name 
                    FROM information_schema.views 
                    WHERE table_schema = 'public';
                """)
                existing_views = {row[0] for row in result.fetchall()}
                
                required_views = {
                    'active_memories_with_decay',
                    'memory_relationship_details',
                    'memory_analytics'
                }
                
                missing_views = required_views - existing_views
                
                if missing_views:
                    logger.error(f"Missing NeuroVault views: {missing_views}")
                    self.validation_results['views'] = False
                    return False
                
                logger.info(f"✓ All {len(required_views)} NeuroVault views exist")
                self.validation_results['views'] = True
                return True
                
        except Exception as e:
            logger.error(f"Failed to validate views: {e}")
            self.validation_results['views'] = False
            return False
    
    async def validate_constraints(self) -> bool:
        """Validate that all required constraints exist."""
        try:
            async with self.db_client.get_async_session() as session:
                result = await session.execute("""
                    SELECT constraint_name, table_name 
                    FROM information_schema.table_constraints 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('memory_items', 'memory_relationships')
                    AND constraint_type = 'CHECK';
                """)
                existing_constraints = {f"{row[1]}.{row[0]}" for row in result.fetchall()}
                
                required_constraints = {
                    'memory_items.chk_neuro_type',
                    'memory_items.chk_decay_lambda',
                    'memory_items.chk_importance_decay',
                    'memory_items.chk_reflection_count',
                    'memory_items.chk_importance_score',
                    'memory_items.chk_access_count',
                    'memory_items.chk_memory_type',
                    'memory_items.chk_ui_source',
                    'memory_relationships.chk_relationship_type',
                    'memory_relationships.chk_confidence_score',
                    'memory_relationships.chk_no_self_reference'
                }
                
                missing_constraints = required_constraints - existing_constraints
                
                if missing_constraints:
                    logger.warning(f"Missing constraints (data validation may be reduced): {missing_constraints}")
                    # Don't fail validation for missing constraints, just warn
                
                found_constraints = required_constraints & existing_constraints
                logger.info(f"✓ Found {len(found_constraints)}/{len(required_constraints)} NeuroVault constraints")
                
                self.validation_results['constraints'] = True
                return True
                
        except Exception as e:
            logger.error(f"Failed to validate constraints: {e}")
            self.validation_results['constraints'] = False
            return False
    
    async def test_basic_functionality(self) -> bool:
        """Test basic NeuroVault functionality."""
        try:
            async with self.db_client.get_async_session() as session:
                # Test decay score calculation function
                result = await session.execute("""
                    SELECT calculate_decay_score(NOW() - INTERVAL '1 day', 'episodic', 5, 0);
                """)
                decay_score = result.scalar()
                
                if decay_score is None or not (0.0 <= decay_score <= 1.0):
                    logger.error(f"Invalid decay score calculation: {decay_score}")
                    self.validation_results['basic_functionality'] = False
                    return False
                
                # Test inserting a test memory (and clean it up)
                test_memory_id = await session.execute("""
                    INSERT INTO memory_items (
                        scope, kind, content, neuro_type, importance_score
                    ) VALUES (
                        'test', 'validation', 'Test memory for NeuroVault validation', 'episodic', 7
                    ) RETURNING id;
                """)
                memory_id = test_memory_id.scalar()
                
                # Test memory access update function
                await session.execute(f"SELECT update_memory_access('{memory_id}');")
                
                # Verify access count was updated
                result = await session.execute(f"""
                    SELECT access_count FROM memory_items WHERE id = '{memory_id}';
                """)
                access_count = result.scalar()
                
                if access_count != 1:
                    logger.error(f"Memory access update failed: expected 1, got {access_count}")
                    self.validation_results['basic_functionality'] = False
                    return False
                
                # Clean up test memory
                await session.execute(f"DELETE FROM memory_items WHERE id = '{memory_id}';")
                await session.commit()
                
                logger.info("✓ Basic NeuroVault functionality tests passed")
                self.validation_results['basic_functionality'] = True
                return True
                
        except Exception as e:
            logger.error(f"Failed basic functionality test: {e}")
            self.validation_results['basic_functionality'] = False
            return False
    
    async def run_full_validation(self) -> bool:
        """Run complete NeuroVault schema validation."""
        logger.info("Starting NeuroVault schema validation...")
        
        validations = [
            ("Memory Items Columns", self.validate_memory_items_columns),
            ("Memory Relationships Table", self.validate_memory_relationships_table),
            ("Indexes", self.validate_indexes),
            ("Functions", self.validate_functions),
            ("Views", self.validate_views),
            ("Constraints", self.validate_constraints),
            ("Basic Functionality", self.test_basic_functionality)
        ]
        
        all_passed = True
        
        for validation_name, validation_func in validations:
            logger.info(f"Validating {validation_name}...")
            try:
                result = await validation_func()
                if result:
                    logger.info(f"✓ {validation_name} validation passed")
                else:
                    logger.error(f"✗ {validation_name} validation failed")
                    all_passed = False
            except Exception as e:
                logger.error(f"✗ {validation_name} validation error: {e}")
                all_passed = False
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("NEUROVAULT SCHEMA VALIDATION SUMMARY")
        logger.info("="*50)
        
        for validation_name, validation_func in validations:
            key = validation_name.lower().replace(" ", "_")
            status = "✓ PASS" if self.validation_results.get(key, False) else "✗ FAIL"
            logger.info(f"{validation_name:.<30} {status}")
        
        if all_passed:
            logger.info("\n🎉 All NeuroVault schema validations passed!")
            logger.info("The database is ready for NeuroVault operations.")
        else:
            logger.error("\n❌ Some NeuroVault schema validations failed!")
            logger.error("Please check the errors above and re-run the migration if needed.")
        
        return all_passed


async def main():
    """Main entry point for the validation script."""
    try:
        # Initialize database client
        config = DatabaseConfig()
        db_client = MultiTenantPostgresClient(config)
        
        # Initialize and run validation
        validator = NeuroVaultSchemaValidator(db_client)
        success = await validator.run_full_validation()
        
        if success:
            logger.info("Schema validation completed successfully!")
            sys.exit(0)
        else:
            logger.error("Schema validation failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation script failed: {e}")
        sys.exit(1)
    finally:
        # Close database connections
        if 'db_client' in locals():
            await db_client.close()


if __name__ == "__main__":
    asyncio.run(main())