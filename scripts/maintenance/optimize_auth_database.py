#!/usr/bin/env python3
"""
Database optimization script for the unified authentication system.

This script provides database optimization, performance analysis, and maintenance
utilities for the consolidated authentication database.

Usage:
    python scripts/optimize_auth_database.py --database auth_unified.db --optimize
    python scripts/optimize_auth_database.py --database auth_unified.db --analyze
    python scripts/optimize_auth_database.py --database auth_unified.db --create-indexes
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from ai_karen_engine.auth.config import DatabaseConfig
from ai_karen_engine.auth.connection_pool import ConnectionPool, QueryOptimizer
from ai_karen_engine.auth.database_schema import DatabaseSchemaManager


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('optimization.log')
        ]
    )


def main():
    """Main optimization script."""
    parser = argparse.ArgumentParser(
        description="Optimize and analyze unified authentication database"
    )
    parser.add_argument(
        "--database",
        required=True,
        help="Path to unified authentication database file"
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Perform database optimization (VACUUM, ANALYZE, etc.)"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze database performance and statistics"
    )
    parser.add_argument(
        "--create-indexes",
        action="store_true",
        help="Create recommended indexes for better performance"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Perform database health check"
    )
    parser.add_argument(
        "--pool-size",
        type=int,
        default=5,
        help="Connection pool size (default: 5)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--output-json",
        help="Output results to JSON file"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate database exists
        if not Path(args.database).exists():
            logger.error(f"Database file not found: {args.database}")
            sys.exit(1)
        
        # Create database configuration
        config = DatabaseConfig(
            database_url=f"sqlite:///{args.database}",
            connection_timeout_seconds=30
        )
        
        # Create connection pool and optimizer
        pool = ConnectionPool(config, pool_size=args.pool_size)
        optimizer = QueryOptimizer(pool)
        schema_manager = DatabaseSchemaManager(config)
        
        results = {
            "database": args.database,
            "timestamp": None,
            "optimization": {},
            "analysis": {},
            "health_check": {},
            "indexes": {}
        }
        
        try:
            logger.info(f"Working with database: {args.database}")
            
            # Perform optimization
            if args.optimize:
                logger.info("Performing database optimization...")
                
                try:
                    # Schema-level optimization
                    schema_manager.optimize_database()
                    
                    # Pool-level optimization
                    pool.optimize_database()
                    
                    results["optimization"] = {
                        "status": "completed",
                        "operations": ["VACUUM", "ANALYZE", "PRAGMA optimize"]
                    }
                    
                    print("✓ Database optimization completed")
                    
                except Exception as e:
                    results["optimization"] = {
                        "status": "failed",
                        "error": str(e)
                    }
                    logger.error(f"Optimization failed: {e}")
            
            # Perform analysis
            if args.analyze:
                logger.info("Analyzing database performance...")
                
                try:
                    # Get table statistics
                    table_stats = optimizer.get_table_statistics()
                    
                    # Get connection pool statistics
                    pool_stats = pool.get_statistics()
                    
                    # Get schema statistics
                    schema_stats = schema_manager.get_table_statistics()
                    
                    results["analysis"] = {
                        "table_statistics": table_stats,
                        "pool_statistics": pool_stats,
                        "schema_statistics": schema_stats
                    }
                    
                    print("\n" + "="*60)
                    print("DATABASE ANALYSIS")
                    print("="*60)
                    
                    print(f"\nTable Statistics:")
                    for table_name, stats in table_stats.items():
                        print(f"  {table_name}:")
                        print(f"    Rows: {stats['row_count']:,}")
                        print(f"    Columns: {stats['column_count']}")
                        print(f"    Indexes: {stats['index_count']}")
                    
                    print(f"\nConnection Pool Statistics:")
                    print(f"  Pool size: {pool_stats['pool_size']}")
                    print(f"  Available connections: {pool_stats['available_connections']}")
                    print(f"  Active connections: {pool_stats['active_connections']}")
                    print(f"  Total queries: {pool_stats['total_queries']:,}")
                    print(f"  Average query time: {pool_stats['avg_query_time']:.4f}s")
                    print(f"  Connections created: {pool_stats['created']}")
                    print(f"  Connections reused: {pool_stats['reused']}")
                    print(f"  Connection errors: {pool_stats['errors']}")
                    
                    print("="*60)
                    
                except Exception as e:
                    results["analysis"] = {
                        "status": "failed",
                        "error": str(e)
                    }
                    logger.error(f"Analysis failed: {e}")
            
            # Create recommended indexes
            if args.create_indexes:
                logger.info("Creating recommended indexes...")
                
                try:
                    index_results = optimizer.create_recommended_indexes()
                    
                    results["indexes"] = index_results
                    
                    print(f"\n✓ Created {len(index_results['created'])} indexes")
                    
                    if index_results['errors']:
                        print(f"⚠ {len(index_results['errors'])} errors occurred:")
                        for error in index_results['errors']:
                            print(f"  - {error}")
                    
                except Exception as e:
                    results["indexes"] = {
                        "status": "failed",
                        "error": str(e)
                    }
                    logger.error(f"Index creation failed: {e}")
            
            # Perform health check
            if args.health_check:
                logger.info("Performing health check...")
                
                try:
                    health = pool.health_check()
                    
                    results["health_check"] = health
                    
                    print(f"\n{'✓' if health['healthy'] else '✗'} Database Health: {'HEALTHY' if health['healthy'] else 'UNHEALTHY'}")
                    
                    if health['issues']:
                        print(f"Issues found:")
                        for issue in health['issues']:
                            print(f"  - {issue}")
                    
                except Exception as e:
                    results["health_check"] = {
                        "healthy": False,
                        "error": str(e)
                    }
                    logger.error(f"Health check failed: {e}")
            
            # Set timestamp
            from datetime import datetime
            results["timestamp"] = datetime.utcnow().isoformat()
            
            # Output to JSON file if requested
            if args.output_json:
                with open(args.output_json, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"\n✓ Results saved to {args.output_json}")
            
            logger.info("Database operations completed successfully")
            
        finally:
            pool.close_all()
            schema_manager.close()
            
    except Exception as e:
        logger.error(f"Database operations failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()