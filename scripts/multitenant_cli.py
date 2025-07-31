#!/usr/bin/env python3
"""
Multi-Tenant Database CLI Tool

Command-line interface for managing the multi-tenant database system.
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from src.ai_karen_engine.database.client import MultiTenantPostgresClient
    from src.ai_karen_engine.database.migrations import MigrationManager
    from src.ai_karen_engine.database.models import Tenant, User
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all dependencies are installed.")
    sys.exit(1)


def setup_database(args):
    """Set up the database with initial migrations."""
    print("Setting up multi-tenant database...")

    try:
        # Initialize migration manager
        manager = MigrationManager(args.database_url)

        # Initialize Alembic
        if manager.initialize_alembic():
            print("✓ Alembic initialized")
        else:
            print("✗ Failed to initialize Alembic")
            return False

        # Create initial migration
        if manager.create_initial_migration():
            print("✓ Initial migration created")
        else:
            print("✗ Failed to create initial migration")
            return False

        # Run migrations
        if manager.run_migrations():
            print("✓ Migrations applied")
        else:
            print("✗ Failed to run migrations")
            return False

        # Create shared tables
        client = MultiTenantPostgresClient(args.database_url)
        client.create_shared_tables()
        print("✓ Shared tables created")

        print("Database setup completed successfully!")
        return True

    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False


def create_tenant(args):
    """Create a new tenant."""
    print(f"Creating tenant: {args.name}")

    try:
        manager = MigrationManager(args.database_url)

        # Generate tenant ID if not provided
        tenant_id = args.tenant_id or str(uuid.uuid4())

        # Set up tenant database
        success = manager.setup_tenant_database(
            tenant_id=tenant_id, tenant_name=args.name, tenant_slug=args.slug
        )

        if success:
            print(f"✓ Tenant created successfully!")
            print(f"  ID: {tenant_id}")
            print(f"  Name: {args.name}")
            print(f"  Slug: {args.slug}")
            return True
        else:
            print("✗ Failed to create tenant")
            return False

    except Exception as e:
        print(f"✗ Tenant creation failed: {e}")
        return False


def list_tenants(args):
    """List all tenants."""
    print("Listing tenants...")

    try:
        client = MultiTenantPostgresClient(args.database_url)

        with client.get_sync_session() as session:
            tenants = session.query(Tenant).all()

            if not tenants:
                print("No tenants found.")
                return True

            print(f"\nFound {len(tenants)} tenant(s):")
            print("-" * 80)

            for tenant in tenants:
                print(f"ID: {tenant.id}")
                print(f"Name: {tenant.name}")
                print(f"Slug: {tenant.slug}")
                print(f"Tier: {tenant.subscription_tier}")
                print(f"Active: {tenant.is_active}")
                print(f"Created: {tenant.created_at}")

                # Get tenant stats
                stats = client.get_tenant_stats(tenant.id)
                if "error" not in stats:
                    print(f"Stats: {stats}")

                print("-" * 80)

        return True

    except Exception as e:
        print(f"✗ Failed to list tenants: {e}")
        return False


def delete_tenant(args):
    """Delete a tenant and all its data."""
    print(f"Deleting tenant: {args.tenant_id}")

    if not args.force:
        confirm = input(
            "This will permanently delete all tenant data. Continue? (y/N): "
        )
        if confirm.lower() != "y":
            print("Operation cancelled.")
            return True

    try:
        manager = MigrationManager(args.database_url)

        success = manager.teardown_tenant_database(args.tenant_id)

        if success:
            print("✓ Tenant deleted successfully!")
            return True
        else:
            print("✗ Failed to delete tenant")
            return False

    except Exception as e:
        print(f"✗ Tenant deletion failed: {e}")
        return False


def validate_tenant(args):
    """Validate tenant schema integrity."""
    print(f"Validating tenant: {args.tenant_id}")

    try:
        manager = MigrationManager(args.database_url)

        validation = manager.validate_tenant_schema(args.tenant_id)

        print(f"\nValidation Results for {args.tenant_id}:")
        print("-" * 50)
        print(f"Schema exists: {validation['schema_exists']}")

        if validation["schema_exists"]:
            print("\nTables:")
            for table, exists in validation["tables_exist"].items():
                status = "✓" if exists else "✗"
                print(f"  {status} {table}")

            print("\nIndexes:")
            for table, count in validation["indexes_exist"].items():
                print(f"  {table}: {count} indexes")

        if validation["errors"]:
            print("\nErrors:")
            for error in validation["errors"]:
                print(f"  ✗ {error}")
        else:
            print("\n✓ No validation errors found")

        return len(validation["errors"]) == 0

    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False


def database_status(args):
    """Show database status."""
    print("Database Status")
    print("=" * 50)

    try:
        manager = MigrationManager(args.database_url)
        client = MultiTenantPostgresClient(args.database_url)

        # Get database status
        status = manager.get_database_status()

        print(f"Database URL: {status['database_url']}")
        print(f"Migrations Dir: {status['migrations_dir']}")
        print(f"Alembic Initialized: {status['alembic_initialized']}")
        print(f"Current Revision: {status.get('current_revision', 'None')}")
        print(f"Tenant Count: {status['tenant_count']}")
        print(f"Health: {status['health']}")

        if "error" in status:
            print(f"Error: {status['error']}")

        # Get client health
        health = client.health_check()
        print(f"\nClient Health: {health['status']}")
        if health["status"] == "healthy":
            print(f"Pool Size: {health['pool_size']}")
            print(f"Async Available: {health['async_available']}")

        return True

    except Exception as e:
        print(f"✗ Failed to get database status: {e}")
        return False


def migration_history(args):
    """Show migration history."""
    print("Migration History")
    print("=" * 50)

    try:
        manager = MigrationManager(args.database_url)

        history = manager.get_migration_history()

        if not history:
            print("No migration history found.")
            return True

        for migration in history:
            status = "→ CURRENT" if migration["is_current"] else ""
            print(f"{migration['revision']}: {migration['message']} {status}")
            if migration["down_revision"]:
                print(f"  ↳ From: {migration['down_revision']}")

        return True

    except Exception as e:
        print(f"✗ Failed to get migration history: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Tenant Database Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s setup --database-url postgresql://user:pass@localhost/db
  %(prog)s create-tenant --name "Acme Corp" --slug "acme-corp"
  %(prog)s list-tenants
  %(prog)s validate-tenant --tenant-id 12345678-1234-1234-1234-123456789abc
  %(prog)s delete-tenant --tenant-id 12345678-1234-1234-1234-123456789abc --force
        """,
    )

    parser.add_argument(
        "--database-url",
        default=(
            os.getenv("POSTGRES_URL")
            or os.getenv("DATABASE_URL")
            or "postgresql://postgres:postgres@localhost/ai_karen"
        ),
        help="Database connection URL",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up the database")

    # Create tenant command
    create_parser = subparsers.add_parser("create-tenant", help="Create a new tenant")
    create_parser.add_argument("--name", required=True, help="Tenant name")
    create_parser.add_argument("--slug", required=True, help="Tenant slug")
    create_parser.add_argument(
        "--tenant-id", help="Tenant ID (auto-generated if not provided)"
    )

    # List tenants command
    list_parser = subparsers.add_parser("list-tenants", help="List all tenants")

    # Delete tenant command
    delete_parser = subparsers.add_parser("delete-tenant", help="Delete a tenant")
    delete_parser.add_argument("--tenant-id", required=True, help="Tenant ID to delete")
    delete_parser.add_argument("--force", action="store_true", help="Skip confirmation")

    # Validate tenant command
    validate_parser = subparsers.add_parser(
        "validate-tenant", help="Validate tenant schema"
    )
    validate_parser.add_argument(
        "--tenant-id", required=True, help="Tenant ID to validate"
    )

    # Database status command
    status_parser = subparsers.add_parser("status", help="Show database status")

    # Migration history command
    history_parser = subparsers.add_parser("history", help="Show migration history")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Command dispatch
    commands = {
        "setup": setup_database,
        "create-tenant": create_tenant,
        "list-tenants": list_tenants,
        "delete-tenant": delete_tenant,
        "validate-tenant": validate_tenant,
        "status": database_status,
        "history": migration_history,
    }

    command_func = commands.get(args.command)
    if not command_func:
        print(f"Unknown command: {args.command}")
        return 1

    try:
        success = command_func(args)
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
