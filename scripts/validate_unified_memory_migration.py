#!/usr/bin/env python3
"""
Validation Script: Unified Memory Migration Validation
Phase 4.1 Database Schema Consolidation

Validates the unified memory migration by checking:
- Data integrity and completeness
- Tenant isolation
- Schema compliance
- Performance characteristics
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Tuple
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UnifiedMemoryMigrationValidator:
    """Validator for unified memory migration"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.validation_results = {
            'schema_validation': False,
            'data_integrity': False,
            'tenant_isolation': False,
            'performance_check': False,
            'index_validation': False,
            'function_validation': False
        }
        self.issues = []
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password']
        )
    
    def validate_schema(self) -> bool:
        """Validate unified memory schema exists and is correct"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check if memories table exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'memories'
                        )
                    """)
                    
                    if not cur.fetchone()[0]:
                        self.issues.append("Memories table does not exist")
                        return False
                    
                    # Check required columns
                    cur.execute("""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_name = 'memories'
                        ORDER BY ordinal_position
                    """)
                    
                    columns = {row['column_name']: row for row in cur.fetchall()}
                    
                    required_columns = {
                        'id': 'uuid',
                        'user_id': 'character varying',
                        'text': 'text',
                        'importance': 'integer',
                        'decay_tier': 'character varying',
                        'created_at': 'timestamp with time zone'
                    }
                    
                    for col_name, expected_type in required_columns.items():
                        if col_name not in columns:
                            self.issues.append(f"Missing required column: {col_name}")
                            return False
                        
                        if expected_type not in columns[col_name]['data_type']:
                            self.issues.append(f"Column {col_name} has wrong type: {columns[col_name]['data_type']}")
                    
                    # Check audit log table
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'memory_access_log'
                        )
                    """)
                    
                    if not cur.fetchone()[0]:
                        self.issues.append("Memory access log table does not exist")
                        return False
                    
                    logger.info("✅ Schema validation passed")
                    return True
                    
        except Exception as e:
            self.issues.append(f"Schema validation error: {e}")
            return False
    
    def validate_data_integrity(self) -> bool:
        """Validate data integrity in unified table"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check for null required fields
                    cur.execute("""
                        SELECT COUNT(*) FROM memories 
                        WHERE user_id IS NULL OR text IS NULL OR text = ''
                    """)
                    null_count = cur.fetchone()[0]
                    
                    if null_count > 0:
                        self.issues.append(f"Found {null_count} records with null/empty required fields")
                        return False
                    
                    # Check importance values are in valid range
                    cur.execute("""
                        SELECT COUNT(*) FROM memories 
                        WHERE importance < 1 OR importance > 10
                    """)
                    invalid_importance = cur.fetchone()[0]
                    
                    if invalid_importance > 0:
                        self.issues.append(f"Found {invalid_importance} records with invalid importance scores")
                        return False
                    
                    # Check decay_tier values are valid
                    cur.execute("""
                        SELECT COUNT(*) FROM memories 
                        WHERE decay_tier NOT IN ('short', 'medium', 'long', 'pinned')
                    """)
                    invalid_decay = cur.fetchone()[0]
                    
                    if invalid_decay > 0:
                        self.issues.append(f"Found {invalid_decay} records with invalid decay_tier values")
                        return False
                    
                    # Check JSON fields are valid
                    cur.execute("""
                        SELECT COUNT(*) FROM memories 
                        WHERE tags IS NOT NULL AND NOT (tags::text ~ '^\\[.*\\]$')
                    """)
                    invalid_tags = cur.fetchone()[0]
                    
                    if invalid_tags > 0:
                        self.issues.append(f"Found {invalid_tags} records with invalid tags JSON")
                        return False
                    
                    # Check version numbers are positive
                    cur.execute("""
                        SELECT COUNT(*) FROM memories 
                        WHERE version < 1
                    """)
                    invalid_version = cur.fetchone()[0]
                    
                    if invalid_version > 0:
                        self.issues.append(f"Found {invalid_version} records with invalid version numbers")
                        return False
                    
                    logger.info("✅ Data integrity validation passed")
                    return True
                    
        except Exception as e:
            self.issues.append(f"Data integrity validation error: {e}")
            return False
    
    def validate_tenant_isolation(self) -> bool:
        """Validate tenant isolation is working correctly"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check user distribution
                    cur.execute("""
                        SELECT COUNT(DISTINCT user_id) as unique_users,
                               COUNT(*) as total_records
                        FROM memories
                    """)
                    user_stats = cur.fetchone()
                    
                    if user_stats['unique_users'] == 0:
                        self.issues.append("No users found in memories table")
                        return False
                    
                    # Check org distribution
                    cur.execute("""
                        SELECT COUNT(DISTINCT org_id) as unique_orgs,
                               COUNT(*) FILTER (WHERE org_id IS NOT NULL) as records_with_org
                        FROM memories
                    """)
                    org_stats = cur.fetchone()
                    
                    # Check for potential cross-tenant data leakage
                    cur.execute("""
                        SELECT user_id, COUNT(*) as record_count
                        FROM memories
                        GROUP BY user_id
                        HAVING COUNT(*) > 10000
                    """)
                    large_users = cur.fetchall()
                    
                    if large_users:
                        logger.warning(f"Found {len(large_users)} users with >10k records (potential data issues)")
                    
                    # Validate tenant indexes exist
                    cur.execute("""
                        SELECT indexname FROM pg_indexes 
                        WHERE tablename = 'memories' 
                        AND indexname LIKE '%tenant%' OR indexname LIKE '%user%'
                    """)
                    tenant_indexes = cur.fetchall()
                    
                    if not tenant_indexes:
                        self.issues.append("No tenant isolation indexes found")
                        return False
                    
                    logger.info(f"✅ Tenant isolation validation passed")
                    logger.info(f"   Users: {user_stats['unique_users']}, Orgs: {org_stats['unique_orgs']}")
                    return True
                    
        except Exception as e:
            self.issues.append(f"Tenant isolation validation error: {e}")
            return False
    
    def validate_indexes(self) -> bool:
        """Validate all required indexes exist"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Get all indexes on memories table
                    cur.execute("""
                        SELECT indexname, indexdef
                        FROM pg_indexes 
                        WHERE tablename = 'memories'
                    """)
                    indexes = {row[0]: row[1] for row in cur.fetchall()}
                    
                    required_indexes = [
                        'idx_memories_tenant',
                        'idx_memories_user',
                        'idx_memories_created',
                        'idx_memories_decay_tier',
                        'idx_memories_importance'
                    ]
                    
                    missing_indexes = []
                    for idx_name in required_indexes:
                        if not any(idx_name in existing_idx for existing_idx in indexes.keys()):
                            missing_indexes.append(idx_name)
                    
                    if missing_indexes:
                        self.issues.append(f"Missing required indexes: {missing_indexes}")
                        return False
                    
                    # Check index usage (basic check)
                    cur.execute("""
                        SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
                        FROM pg_stat_user_indexes 
                        WHERE tablename = 'memories'
                        ORDER BY idx_scan DESC
                    """)
                    index_stats = cur.fetchall()
                    
                    logger.info(f"✅ Index validation passed ({len(indexes)} indexes found)")
                    return True
                    
        except Exception as e:
            self.issues.append(f"Index validation error: {e}")
            return False
    
    def validate_functions(self) -> bool:
        """Validate helper functions exist and work"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Check if helper functions exist
                    functions_to_check = [
                        'calculate_decay_score',
                        'update_memory_access',
                        'create_memory_relationship',
                        'soft_delete_memory',
                        'calculate_expires_at'
                    ]
                    
                    for func_name in functions_to_check:
                        cur.execute("""
                            SELECT EXISTS (
                                SELECT FROM pg_proc 
                                WHERE proname = %s
                            )
                        """, (func_name,))
                        
                        if not cur.fetchone()[0]:
                            self.issues.append(f"Missing function: {func_name}")
                            return False
                    
                    # Test calculate_decay_score function
                    cur.execute("""
                        SELECT calculate_decay_score(NOW() - INTERVAL '1 day', 'episodic', 5, 0)
                    """)
                    decay_score = cur.fetchone()[0]
                    
                    if not (0.0 <= decay_score <= 1.0):
                        self.issues.append(f"calculate_decay_score returned invalid value: {decay_score}")
                        return False
                    
                    # Test calculate_expires_at function
                    cur.execute("""
                        SELECT calculate_expires_at('short', NOW())
                    """)
                    expires_at = cur.fetchone()[0]
                    
                    if expires_at is None:
                        self.issues.append("calculate_expires_at returned NULL for 'short' tier")
                        return False
                    
                    logger.info("✅ Function validation passed")
                    return True
                    
        except Exception as e:
            self.issues.append(f"Function validation error: {e}")
            return False
    
    def validate_performance(self) -> bool:
        """Basic performance validation"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Test query performance with tenant filtering
                    start_time = datetime.now()
                    cur.execute("""
                        SELECT COUNT(*) FROM memories 
                        WHERE user_id = 'test_user' 
                        AND created_at > NOW() - INTERVAL '30 days'
                        LIMIT 1000
                    """)
                    end_time = datetime.now()
                    
                    query_time = (end_time - start_time).total_seconds()
                    
                    if query_time > 5.0:  # 5 second threshold
                        self.issues.append(f"Tenant query took too long: {query_time:.2f}s")
                        return False
                    
                    # Test index usage
                    cur.execute("""
                        EXPLAIN (FORMAT JSON) 
                        SELECT * FROM memories 
                        WHERE user_id = 'test_user' 
                        ORDER BY created_at DESC 
                        LIMIT 10
                    """)
                    explain_result = cur.fetchone()[0]
                    
                    # Basic check for index usage (simplified)
                    explain_str = str(explain_result)
                    if 'Index Scan' not in explain_str and 'Bitmap Index Scan' not in explain_str:
                        logger.warning("Query may not be using indexes efficiently")
                    
                    logger.info(f"✅ Performance validation passed (query time: {query_time:.3f}s)")
                    return True
                    
        except Exception as e:
            self.issues.append(f"Performance validation error: {e}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate validation report"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Get basic statistics
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total_records,
                            COUNT(DISTINCT user_id) as unique_users,
                            COUNT(DISTINCT org_id) as unique_orgs,
                            MIN(created_at) as earliest_record,
                            MAX(created_at) as latest_record,
                            AVG(importance) as avg_importance,
                            COUNT(*) FILTER (WHERE deleted_at IS NOT NULL) as soft_deleted
                        FROM memories
                    """)
                    stats = cur.fetchone()
                    
                    # Get decay tier distribution
                    cur.execute("""
                        SELECT decay_tier, COUNT(*) as count
                        FROM memories
                        GROUP BY decay_tier
                        ORDER BY count DESC
                    """)
                    decay_distribution = cur.fetchall()
                    
                    # Get memory type distribution
                    cur.execute("""
                        SELECT memory_type, COUNT(*) as count
                        FROM memories
                        GROUP BY memory_type
                        ORDER BY count DESC
                    """)
                    type_distribution = cur.fetchall()
                    
                    # Get UI source distribution
                    cur.execute("""
                        SELECT ui_source, COUNT(*) as count
                        FROM memories
                        GROUP BY ui_source
                        ORDER BY count DESC
                    """)
                    source_distribution = cur.fetchall()
                    
                    report = {
                        'validation_timestamp': datetime.now().isoformat(),
                        'validation_results': self.validation_results,
                        'issues': self.issues,
                        'statistics': dict(stats),
                        'distributions': {
                            'decay_tier': [dict(row) for row in decay_distribution],
                            'memory_type': [dict(row) for row in type_distribution],
                            'ui_source': [dict(row) for row in source_distribution]
                        },
                        'overall_status': all(self.validation_results.values()) and len(self.issues) == 0
                    }
                    
                    return report
                    
        except Exception as e:
            return {
                'validation_timestamp': datetime.now().isoformat(),
                'validation_results': self.validation_results,
                'issues': self.issues + [f"Report generation error: {e}"],
                'overall_status': False
            }
    
    def run_validation(self) -> bool:
        """Run complete validation"""
        logger.info("Starting unified memory migration validation...")
        
        # Run all validation checks
        self.validation_results['schema_validation'] = self.validate_schema()
        self.validation_results['data_integrity'] = self.validate_data_integrity()
        self.validation_results['tenant_isolation'] = self.validate_tenant_isolation()
        self.validation_results['index_validation'] = self.validate_indexes()
        self.validation_results['function_validation'] = self.validate_functions()
        self.validation_results['performance_check'] = self.validate_performance()
        
        # Generate report
        report = self.generate_report()
        
        # Save report to file
        report_file = f"memory_migration_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Validation report saved to: {report_file}")
        
        # Print summary
        passed = sum(1 for result in self.validation_results.values() if result)
        total = len(self.validation_results)
        
        logger.info(f"Validation summary: {passed}/{total} checks passed")
        
        if self.issues:
            logger.error("Issues found:")
            for issue in self.issues:
                logger.error(f"  - {issue}")
        
        return report['overall_status']

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Validate unified memory migration')
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
    
    validator = UnifiedMemoryMigrationValidator(db_config)
    
    try:
        success = validator.run_validation()
        if success:
            print("✅ Validation completed successfully - migration is valid")
            sys.exit(0)
        else:
            print("❌ Validation failed - migration has issues")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        print(f"❌ Validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()