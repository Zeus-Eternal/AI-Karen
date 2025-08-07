#!/usr/bin/env python3
"""
Migration script for consolidating existing authentication databases.

This script migrates data from existing authentication services and databases
into the unified authentication system.

Usage:
    python scripts/migrate_auth_databases.py --target-db auth_unified.db --source-dbs auth.db,auth_sessions.db
    python scripts/migrate_auth_databases.py --target-db auth_unified.db --source-dbs auth.db --dry-run
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_karen_engine.auth.config import DatabaseConfig
from ai_karen_engine.auth.migration_utils import AuthDataMigrator


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('migration.log')
        ]
    )


def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate existing authentication databases to unified system"
    )
    parser.add_argument(
        "--target-db",
        required=True,
        help="Path to target unified database file"
    )
    parser.add_argument(
        "--source-dbs",
        required=True,
        help="Comma-separated list of source database files to migrate from"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform dry run without making changes"
    )
    parser.add_argument(
        "--cleanup-days",
        type=int,
        default=90,
        help="Clean up data older than this many days (default: 90)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate migration after completion"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Parse source databases
        source_databases = [db.strip() for db in args.source_dbs.split(",")]
        
        # Validate source databases exist
        for db_path in source_databases:
            if not Path(db_path).exists():
                logger.warning(f"Source database not found: {db_path}")
        
        # Create target database configuration
        target_config = DatabaseConfig(
            database_url=f"sqlite:///{args.target_db}",
            connection_timeout_seconds=30
        )
        
        # Create migrator
        migrator = AuthDataMigrator(target_config)
        
        logger.info(f"Starting migration {'(DRY RUN)' if args.dry_run else ''}")
        logger.info(f"Target database: {args.target_db}")
        logger.info(f"Source databases: {', '.join(source_databases)}")
        
        # Perform migration
        summary = migrator.migrate_from_existing_databases(
            source_databases=source_databases,
            dry_run=args.dry_run
        )
        
        # Print summary
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        print(f"Started: {summary['started_at']}")
        print(f"Completed: {summary['completed_at']}")
        print(f"Dry Run: {summary['dry_run']}")
        print(f"Migrated Users: {summary['migrated_users']}")
        print(f"Migrated Sessions: {summary['migrated_sessions']}")
        print(f"Migrated Events: {summary['migrated_events']}")
        
        if summary['warnings']:
            print(f"\nWarnings ({len(summary['warnings'])}):")
            for warning in summary['warnings']:
                print(f"  - {warning}")
        
        if summary['errors']:
            print(f"\nErrors ({len(summary['errors'])}):")
            for error in summary['errors']:
                print(f"  - {error}")
        
        # Cleanup old data if not dry run
        if not args.dry_run and args.cleanup_days > 0:
            logger.info(f"Cleaning up data older than {args.cleanup_days} days")
            cleanup_summary = migrator.cleanup_old_data(older_than_days=args.cleanup_days)
            
            print(f"\nCleanup Summary:")
            print(f"  Expired tokens removed: {cleanup_summary['expired_tokens']}")
            print(f"  Old events removed: {cleanup_summary['old_events']}")
            print(f"  Inactive sessions removed: {cleanup_summary['inactive_sessions']}")
        
        # Validate migration if requested
        if args.validate and not args.dry_run:
            logger.info("Validating migration")
            validation_report = migrator.validate_migration()
            
            print(f"\nValidation Report:")
            print(f"  Total users: {validation_report['statistics']['total_users']}")
            print(f"  Active sessions: {validation_report['statistics']['active_sessions']}")
            print(f"  Total events: {validation_report['statistics']['total_events']}")
            
            if validation_report['issues']:
                print(f"\nIssues found ({len(validation_report['issues'])}):")
                for issue in validation_report['issues']:
                    print(f"  - {issue}")
            
            if validation_report['warnings']:
                print(f"\nWarnings ({len(validation_report['warnings'])}):")
                for warning in validation_report['warnings']:
                    print(f"  - {warning}")
        
        print("="*60)
        
        if summary['errors']:
            logger.error("Migration completed with errors")
            sys.exit(1)
        else:
            logger.info("Migration completed successfully")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()