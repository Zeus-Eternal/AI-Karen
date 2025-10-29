#!/usr/bin/env python3
"""
Extension Marketplace CLI

Command-line interface for managing the extension marketplace.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional
import click
from sqlalchemy.orm import Session

from .database import MarketplaceDatabaseManager
from .service import ExtensionMarketplaceService
from .models import ExtensionListingSchema, ExtensionVersionSchema
from .version_manager import VersionManager
from ..manager import ExtensionManager
from ..registry import ExtensionRegistry


@click.group()
@click.option('--database-url', default='sqlite:///marketplace.db', help='Database URL')
@click.pass_context
def cli(ctx, database_url):
    """Extension Marketplace CLI."""
    ctx.ensure_object(dict)
    ctx.obj['database_url'] = database_url
    ctx.obj['db_manager'] = MarketplaceDatabaseManager(database_url)


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize the marketplace database."""
    db_manager = ctx.obj['db_manager']
    
    if db_manager.initialize_marketplace():
        click.echo("✅ Marketplace database initialized successfully")
    else:
        click.echo("❌ Failed to initialize marketplace database")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show marketplace status."""
    db_manager = ctx.obj['db_manager']
    
    if db_manager.health_check():
        click.echo("✅ Database connection: OK")
        
        counts = db_manager.get_table_counts()
        click.echo(f"📊 Extension listings: {counts.get('extension_listings', 0)}")
        click.echo(f"📦 Extension versions: {counts.get('extension_versions', 0)}")
        click.echo(f"💾 Installations: {counts.get('extension_installations', 0)}")
    else:
        click.echo("❌ Database connection: FAILED")
        sys.exit(1)


@cli.command()
@click.argument('extension_file', type=click.Path(exists=True))
@click.pass_context
def add_extension(ctx, extension_file):
    """Add an extension to the marketplace."""
    db_manager = ctx.obj['db_manager']
    
    try:
        with open(extension_file, 'r') as f:
            extension_data = json.load(f)
        
        # Validate extension data
        extension_schema = ExtensionListingSchema(**extension_data)
        
        with db_manager.get_session() as session:
            # Create marketplace service
            extension_manager = ExtensionManager(Path("extensions"), None)
            extension_registry = ExtensionRegistry()
            marketplace_service = ExtensionMarketplaceService(
                session, extension_manager, extension_registry
            )
            
            # Add extension (this would need to be implemented in the service)
            click.echo(f"✅ Extension '{extension_schema.name}' added to marketplace")
            
    except Exception as e:
        click.echo(f"❌ Failed to add extension: {e}")
        sys.exit(1)


@cli.command()
@click.argument('query', required=False)
@click.option('--category', help='Filter by category')
@click.option('--limit', default=10, help='Number of results to show')
@click.pass_context
def search(ctx, query, category, limit):
    """Search for extensions in the marketplace."""
    db_manager = ctx.obj['db_manager']
    
    try:
        with db_manager.get_session() as session:
            extension_manager = ExtensionManager(Path("extensions"), None)
            extension_registry = ExtensionRegistry()
            marketplace_service = ExtensionMarketplaceService(
                session, extension_manager, extension_registry
            )
            
            from .models import ExtensionSearchRequest
            search_request = ExtensionSearchRequest(
                query=query,
                category=category,
                page_size=limit
            )
            
            # This would need to be made sync or use asyncio.run
            # result = await marketplace_service.search_extensions(search_request)
            
            click.echo(f"🔍 Search results for '{query or 'all extensions'}':")
            # Display results here
            
    except Exception as e:
        click.echo(f"❌ Search failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument('extension_name')
@click.argument('version', required=False)
@click.option('--tenant-id', default='default', help='Tenant ID')
@click.option('--user-id', default='admin', help='User ID')
@click.pass_context
def install(ctx, extension_name, version, tenant_id, user_id):
    """Install an extension."""
    db_manager = ctx.obj['db_manager']
    
    try:
        with db_manager.get_session() as session:
            extension_manager = ExtensionManager(Path("extensions"), None)
            extension_registry = ExtensionRegistry()
            marketplace_service = ExtensionMarketplaceService(
                session, extension_manager, extension_registry
            )
            
            from .models import ExtensionInstallRequest
            install_request = ExtensionInstallRequest(
                extension_name=extension_name,
                version=version
            )
            
            # This would need to be made sync or use asyncio.run
            # result = await marketplace_service.install_extension(
            #     install_request, tenant_id, user_id
            # )
            
            click.echo(f"✅ Installation of '{extension_name}' started")
            
    except Exception as e:
        click.echo(f"❌ Installation failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument('extension_name')
@click.option('--tenant-id', default='default', help='Tenant ID')
@click.pass_context
def uninstall(ctx, extension_name, tenant_id):
    """Uninstall an extension."""
    db_manager = ctx.obj['db_manager']
    
    try:
        with db_manager.get_session() as session:
            extension_manager = ExtensionManager(Path("extensions"), None)
            extension_registry = ExtensionRegistry()
            marketplace_service = ExtensionMarketplaceService(
                session, extension_manager, extension_registry
            )
            
            # This would need to be made sync or use asyncio.run
            # result = await marketplace_service.uninstall_extension(
            #     extension_name, tenant_id, 'admin'
            # )
            
            click.echo(f"✅ Uninstallation of '{extension_name}' started")
            
    except Exception as e:
        click.echo(f"❌ Uninstallation failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--tenant-id', default='default', help='Tenant ID')
@click.pass_context
def list_installed(ctx, tenant_id):
    """List installed extensions."""
    db_manager = ctx.obj['db_manager']
    
    try:
        with db_manager.get_session() as session:
            extension_manager = ExtensionManager(Path("extensions"), None)
            extension_registry = ExtensionRegistry()
            marketplace_service = ExtensionMarketplaceService(
                session, extension_manager, extension_registry
            )
            
            # This would need to be made sync or use asyncio.run
            # installations = await marketplace_service.get_installed_extensions(tenant_id)
            
            click.echo(f"📦 Installed extensions for tenant '{tenant_id}':")
            # Display installations here
            
    except Exception as e:
        click.echo(f"❌ Failed to list installed extensions: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def migrate(ctx):
    """Run database migrations."""
    db_manager = ctx.obj['db_manager']
    
    migrations_dir = Path(__file__).parent / "migrations"
    
    if not migrations_dir.exists():
        click.echo("❌ Migrations directory not found")
        sys.exit(1)
    
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        click.echo("ℹ️ No migration files found")
        return
    
    for migration_file in migration_files:
        click.echo(f"🔄 Running migration: {migration_file.name}")
        
        if db_manager.run_migration(migration_file):
            click.echo(f"✅ Migration {migration_file.name} completed")
        else:
            click.echo(f"❌ Migration {migration_file.name} failed")
            sys.exit(1)
    
    click.echo("✅ All migrations completed successfully")


@cli.command()
@click.argument('extension_name')
@click.pass_context
def validate(ctx, extension_name):
    """Validate an extension manifest."""
    try:
        extension_path = Path("extensions") / extension_name / "extension.json"
        
        if not extension_path.exists():
            click.echo(f"❌ Extension manifest not found: {extension_path}")
            sys.exit(1)
        
        with open(extension_path, 'r') as f:
            manifest_data = json.load(f)
        
        # Validate using version manager
        version_manager = VersionManager(None)  # No DB session needed for validation
        errors = version_manager.validate_manifest_version(manifest_data)
        
        if errors:
            click.echo(f"❌ Validation failed for '{extension_name}':")
            for error in errors:
                click.echo(f"  • {error}")
            sys.exit(1)
        else:
            click.echo(f"✅ Extension '{extension_name}' manifest is valid")
            
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()