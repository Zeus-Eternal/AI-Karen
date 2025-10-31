#!/usr/bin/env python3
"""
Database Consistency Validation CLI

Command-line interface for validating database consistency and performing cleanup operations.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_karen_engine.services.database_consistency_validator import (
    validate_database_consistency,
    get_database_consistency_validator,
)
from ai_karen_engine.services.data_cleanup_service import (
    cleanup_demo_data,
    get_data_cleanup_service,
)
from ai_karen_engine.services.migration_validator import (
    validate_database_migrations,
    get_migration_validator,
)
from ai_karen_engine.services.database_health_checker import (
    check_database_health,
    get_database_health_checker,
)


def print_health_status(health_result):
    """Print health check results in a readable format"""
    print(f"\n{'='*60}")
    print(f"DATABASE HEALTH CHECK REPORT")
    print(f"{'='*60}")
    print(f"Timestamp: {health_result.timestamp}")
    print(f"Overall Status: {health_result.overall_status.value.upper()}")
    print(f"Uptime: {health_result.uptime_seconds:.1f} seconds")
    
    print(f"\nDatabase Connections:")
    for conn in health_result.database_connections:
        status_icon = "✅" if conn.is_connected else "❌"
        degraded_icon = "⚠️" if conn.degraded_mode else ""
        print(f"  {status_icon} {conn.database.value.upper()}: {conn.status.value} "
              f"({conn.response_time_ms:.1f}ms) {degraded_icon}")
        if conn.error_message:
            print(f"    Error: {conn.error_message}")
    
    print(f"\nMigration Status: {health_result.migration_status.value}")
    
    if health_result.critical_issues > 0:
        print(f"\n❌ Critical Issues: {health_result.critical_issues}")
    if health_result.warning_issues > 0:
        print(f"⚠️  Warning Issues: {health_result.warning_issues}")
    if health_result.consistency_issues > 0:
        print(f"🔍 Consistency Issues: {health_result.consistency_issues}")
    
    if health_result.recommendations:
        print(f"\nRecommendations:")
        for i, rec in enumerate(health_result.recommendations, 1):
            print(f"  {i}. {rec}")
    
    if health_result.errors:
        print(f"\nErrors:")
        for error in health_result.errors:
            print(f"  ❌ {error}")


def print_consistency_report(report):
    """Print consistency validation report in a readable format"""
    print(f"\n{'='*60}")
    print(f"DATABASE CONSISTENCY VALIDATION REPORT")
    print(f"{'='*60}")
    print(f"Timestamp: {report.timestamp}")
    print(f"Overall Status: {report.overall_status.value.upper()}")
    
    print(f"\nDatabase Health:")
    for health in report.database_health:
        status_icon = "✅" if health.is_connected else "❌"
        print(f"  {status_icon} {health.database.value.upper()}: {health.status.value} "
              f"({health.response_time_ms:.1f}ms)")
        if health.error_message:
            print(f"    Error: {health.error_message}")
    
    print(f"\nValidation Summary:")
    print(f"  Total Issues: {report.summary.get('total_issues', 0)}")
    print(f"  Critical Issues: {report.summary.get('critical_issues', 0)}")
    print(f"  Warning Issues: {report.summary.get('warning_issues', 0)}")
    print(f"  Auto-fixable Issues: {report.summary.get('auto_fixable_issues', 0)}")
    print(f"  Cleanup Recommendations: {report.summary.get('cleanup_recommendations', 0)}")
    
    if report.validation_issues:
        print(f"\nValidation Issues:")
        for issue in report.validation_issues:
            severity_icon = "❌" if issue.severity.value == "critical" else "⚠️"
            print(f"  {severity_icon} [{issue.category}] {issue.description}")
            if issue.recommendation:
                print(f"    → {issue.recommendation}")
    
    if report.cleanup_recommendations:
        print(f"\nCleanup Recommendations:")
        for i, rec in enumerate(report.cleanup_recommendations, 1):
            print(f"  {i}. {rec}")


def print_cleanup_report(report):
    """Print cleanup report in a readable format"""
    print(f"\n{'='*60}")
    print(f"DATA CLEANUP REPORT")
    print(f"{'='*60}")
    print(f"Timestamp: {report.timestamp}")
    print(f"Dry Run: {report.dry_run}")
    print(f"Total Actions: {report.total_actions}")
    print(f"Successful: {report.successful_actions}")
    print(f"Failed: {report.failed_actions}")
    print(f"Bytes Cleaned: {report.bytes_cleaned:,}")
    
    print(f"\nSummary:")
    for key, value in report.summary.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    if report.actions:
        print(f"\nActions Taken:")
        for action in report.actions:
            action_icon = "✅" if action.action_type.startswith("remove") else "ℹ️"
            print(f"  {action_icon} {action.description}")
            if action.size_bytes:
                print(f"    Size: {action.size_bytes:,} bytes")
            if action.backup_location:
                print(f"    Backup: {action.backup_location}")
    
    if report.errors:
        print(f"\nErrors:")
        for error in report.errors:
            print(f"  ❌ {error}")


async def main():
    parser = argparse.ArgumentParser(
        description="Database Consistency Validation and Cleanup Tool"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Check database health")
    health_parser.add_argument(
        "--detailed", 
        action="store_true", 
        help="Include detailed consistency validation"
    )
    health_parser.add_argument(
        "--json", 
        action="store_true", 
        help="Output results in JSON format"
    )
    
    # Consistency validation command
    consistency_parser = subparsers.add_parser(
        "validate", help="Validate database consistency"
    )
    consistency_parser.add_argument(
        "--data-dir", 
        default="data", 
        help="Data directory to check (default: data)"
    )
    consistency_parser.add_argument(
        "--auto-fix", 
        action="store_true", 
        help="Automatically fix issues that can be auto-fixed"
    )
    consistency_parser.add_argument(
        "--json", 
        action="store_true", 
        help="Output results in JSON format"
    )
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up demo/test data")
    cleanup_parser.add_argument(
        "--data-dir", 
        default="data", 
        help="Data directory to clean (default: data)"
    )
    cleanup_parser.add_argument(
        "--dry-run", 
        action="store_true", 
        default=True,
        help="Only show what would be cleaned (default: true)"
    )
    cleanup_parser.add_argument(
        "--execute", 
        action="store_true", 
        help="Actually perform cleanup (overrides --dry-run)"
    )
    cleanup_parser.add_argument(
        "--json", 
        action="store_true", 
        help="Output results in JSON format"
    )
    
    # Migration validation command
    migration_parser = subparsers.add_parser(
        "migrations", help="Validate database migrations"
    )
    migration_parser.add_argument(
        "--migrations-dir", 
        default="src/ai_karen_engine/database/migrations",
        help="Migrations directory (default: src/ai_karen_engine/database/migrations)"
    )
    migration_parser.add_argument(
        "--create-missing", 
        action="store_true", 
        help="Create missing tables"
    )
    migration_parser.add_argument(
        "--json", 
        action="store_true", 
        help="Output results in JSON format"
    )
    
    # Quick status command
    status_parser = subparsers.add_parser("status", help="Get quick database status")
    status_parser.add_argument(
        "--json", 
        action="store_true", 
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "health":
            print("Checking database health...")
            health_result = await check_database_health(
                include_detailed_validation=args.detailed
            )
            
            if args.json:
                # Convert to JSON-serializable format
                result_dict = {
                    "timestamp": health_result.timestamp.isoformat(),
                    "overall_status": health_result.overall_status.value,
                    "database_connections": [
                        {
                            "database": conn.database.value,
                            "is_connected": conn.is_connected,
                            "response_time_ms": conn.response_time_ms,
                            "status": conn.status.value,
                            "version": conn.version,
                            "connection_count": conn.connection_count,
                            "error_message": conn.error_message,
                            "degraded_mode": conn.degraded_mode,
                        }
                        for conn in health_result.database_connections
                    ],
                    "migration_status": health_result.migration_status.value,
                    "consistency_issues": health_result.consistency_issues,
                    "critical_issues": health_result.critical_issues,
                    "warning_issues": health_result.warning_issues,
                    "recommendations": health_result.recommendations,
                    "uptime_seconds": health_result.uptime_seconds,
                    "errors": health_result.errors,
                }
                print(json.dumps(result_dict, indent=2))
            else:
                print_health_status(health_result)
        
        elif args.command == "validate":
            print("Validating database consistency...")
            report = await validate_database_consistency(
                data_directory=args.data_dir,
                enable_auto_fix=args.auto_fix,
            )
            
            if args.json:
                # Convert to JSON-serializable format
                result_dict = {
                    "timestamp": report.timestamp.isoformat(),
                    "overall_status": report.overall_status.value,
                    "database_health": [
                        {
                            "database": health.database.value,
                            "is_connected": health.is_connected,
                            "response_time_ms": health.response_time_ms,
                            "status": health.status.value,
                            "error_message": health.error_message,
                        }
                        for health in report.database_health
                    ],
                    "validation_issues": [
                        {
                            "database": issue.database.value,
                            "severity": issue.severity.value,
                            "category": issue.category,
                            "description": issue.description,
                            "recommendation": issue.recommendation,
                            "auto_fixable": issue.auto_fixable,
                        }
                        for issue in report.validation_issues
                    ],
                    "cleanup_recommendations": report.cleanup_recommendations,
                    "summary": report.summary,
                }
                print(json.dumps(result_dict, indent=2))
            else:
                print_consistency_report(report)
        
        elif args.command == "cleanup":
            dry_run = args.dry_run and not args.execute
            action_word = "Simulating" if dry_run else "Performing"
            print(f"{action_word} data cleanup...")
            
            report = await cleanup_demo_data(
                data_directory=args.data_dir,
                dry_run=dry_run,
            )
            
            if args.json:
                # Convert to JSON-serializable format
                result_dict = {
                    "timestamp": report.timestamp.isoformat(),
                    "dry_run": report.dry_run,
                    "total_actions": report.total_actions,
                    "successful_actions": report.successful_actions,
                    "failed_actions": report.failed_actions,
                    "bytes_cleaned": report.bytes_cleaned,
                    "actions": [
                        {
                            "action_type": action.action_type,
                            "target": action.target,
                            "description": action.description,
                            "size_bytes": action.size_bytes,
                            "count": action.count,
                            "backup_location": action.backup_location,
                        }
                        for action in report.actions
                    ],
                    "summary": report.summary,
                    "errors": report.errors,
                }
                print(json.dumps(result_dict, indent=2))
            else:
                print_cleanup_report(report)
        
        elif args.command == "migrations":
            print("Validating database migrations...")
            report = await validate_database_migrations(
                migrations_directory=args.migrations_dir
            )
            
            if args.create_missing and report.schema_validation.missing_tables:
                print("Creating missing tables...")
                validator = get_migration_validator()
                create_result = await validator.create_missing_tables(dry_run=False)
                print(f"Table creation result: {create_result}")
            
            if args.json:
                # Convert to JSON-serializable format
                result_dict = {
                    "timestamp": report.timestamp.isoformat(),
                    "overall_status": report.overall_status.value,
                    "current_migration": {
                        "version": report.current_migration.version if report.current_migration else None,
                        "is_current": report.current_migration.is_current if report.current_migration else False,
                    } if report.current_migration else None,
                    "pending_migrations": report.pending_migrations,
                    "schema_validation": {
                        "status": report.schema_validation.status.value,
                        "missing_tables": list(report.schema_validation.missing_tables),
                        "extra_tables": list(report.schema_validation.extra_tables),
                        "issues": report.schema_validation.issues,
                    },
                    "recommendations": report.recommendations,
                    "errors": report.errors,
                }
                print(json.dumps(result_dict, indent=2))
            else:
                print(f"\nMigration Status: {report.overall_status.value}")
                if report.current_migration:
                    print(f"Current Version: {report.current_migration.version}")
                if report.pending_migrations:
                    print(f"Pending Migrations: {len(report.pending_migrations)}")
                
                print(f"\nSchema Status: {report.schema_validation.status.value}")
                if report.schema_validation.missing_tables:
                    print(f"Missing Tables: {', '.join(report.schema_validation.missing_tables)}")
                if report.schema_validation.extra_tables:
                    print(f"Extra Tables: {', '.join(report.schema_validation.extra_tables)}")
                
                if report.recommendations:
                    print(f"\nRecommendations:")
                    for i, rec in enumerate(report.recommendations, 1):
                        print(f"  {i}. {rec}")
        
        elif args.command == "status":
            print("Getting quick database status...")
            checker = get_database_health_checker()
            status = await checker.get_quick_status()
            
            if args.json:
                print(json.dumps(status, indent=2))
            else:
                print(f"\nDatabase Status: {status['overall_status'].upper()}")
                print(f"Uptime: {status['uptime_seconds']:.1f} seconds")
                print(f"Databases:")
                for db, state in status['databases'].items():
                    status_icon = "✅" if state == "connected" else "❌"
                    print(f"  {status_icon} {db.upper()}: {state}")
                
                if 'error' in status:
                    print(f"\nError: {status['error']}")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())