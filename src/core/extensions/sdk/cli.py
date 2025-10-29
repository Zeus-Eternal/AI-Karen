"""
Command-line interface for Kari Extensions SDK.
"""

import click
import json
import sys
from pathlib import Path
from typing import Optional

from .extension_sdk import ExtensionSDK, SDKConfig


@click.group()
@click.option('--workspace', type=click.Path(), help='Extension workspace directory')
@click.pass_context
def cli(ctx, workspace):
    """Kari Extensions SDK - Build powerful extensions for Kari AI."""
    # Initialize SDK
    config = None
    if workspace:
        config = SDKConfig(workspace_path=Path(workspace))
    
    ctx.ensure_object(dict)
    ctx.obj['sdk'] = ExtensionSDK(config)


@cli.command()
@click.argument('name')
@click.option('--template', default='basic', help='Extension template to use')
@click.option('--author', help='Extension author name')
@click.option('--description', help='Extension description')
@click.pass_context
def create(ctx, name, template, author, description):
    """Create a new extension from template."""
    sdk = ctx.obj['sdk']
    
    try:
        kwargs = {}
        if author:
            kwargs['author'] = author
        if description:
            kwargs['description'] = description
        
        extension_path = sdk.create_extension(name, template, **kwargs)
        
        click.echo(f"✅ Extension '{name}' created successfully!")
        click.echo(f"📁 Location: {extension_path}")
        click.echo(f"📖 Next steps:")
        click.echo(f"   cd {extension_path}")
        click.echo(f"   kari-ext dev --watch")
        
    except Exception as e:
        click.echo(f"❌ Failed to create extension: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--path', type=click.Path(exists=True), default='.', help='Extension directory path')
@click.pass_context
def validate(ctx, path):
    """Validate an extension for compliance and best practices."""
    sdk = ctx.obj['sdk']
    extension_path = Path(path).resolve()
    
    try:
        click.echo(f"🔍 Validating extension at {extension_path}...")
        results = sdk.validate_extension(extension_path)
        
        # Display results
        if results['valid']:
            click.echo(f"✅ Extension is valid! Score: {results['score']}/100")
        else:
            click.echo(f"❌ Extension validation failed. Score: {results['score']}/100")
        
        if results['errors']:
            click.echo("\n🚨 Errors:")
            for error in results['errors']:
                click.echo(f"  • {error}")
        
        if results['warnings']:
            click.echo("\n⚠️  Warnings:")
            for warning in results['warnings']:
                click.echo(f"  • {warning}")
        
        # Show detailed checks
        if results['checks']:
            click.echo("\n📋 Detailed Checks:")
            for check_name, check_result in results['checks'].items():
                status = "✅" if check_result.get('passed', False) else "❌"
                click.echo(f"  {status} {check_name.replace('_', ' ').title()}")
        
        if not results['valid']:
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--path', type=click.Path(exists=True), default='.', help='Extension directory path')
@click.pass_context
def test(ctx, path):
    """Run tests for an extension."""
    sdk = ctx.obj['sdk']
    extension_path = Path(path).resolve()
    
    try:
        click.echo(f"🧪 Running tests for extension at {extension_path}...")
        results = sdk.test_extension(extension_path)
        
        # Display results
        total_tests = results['passed'] + results['failed']
        click.echo(f"📊 Test Results: {results['passed']}/{total_tests} passed")
        
        if results['coverage'] > 0:
            click.echo(f"📈 Coverage: {results['coverage']:.1f}%")
        
        if results['errors']:
            click.echo("\n❌ Errors:")
            for error in results['errors']:
                click.echo(f"  • {error}")
        
        if results['failed'] > 0:
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Testing failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--path', type=click.Path(exists=True), default='.', help='Extension directory path')
@click.option('--watch', is_flag=True, help='Enable file watching for hot reload')
@click.option('--port', default=8000, help='Development server port')
@click.pass_context
def dev(ctx, path, watch, port):
    """Start development server for extension testing."""
    sdk = ctx.obj['sdk']
    extension_path = Path(path).resolve()
    
    try:
        click.echo(f"🚀 Starting development server for {extension_path.name}...")
        sdk.start_dev_server(extension_path, watch=watch, port=port)
        
    except KeyboardInterrupt:
        click.echo("\n🛑 Development server stopped")
    except Exception as e:
        click.echo(f"❌ Failed to start dev server: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--path', type=click.Path(exists=True), default='.', help='Extension directory path')
@click.pass_context
def package(ctx, path):
    """Package extension for distribution."""
    sdk = ctx.obj['sdk']
    extension_path = Path(path).resolve()
    
    try:
        click.echo(f"📦 Packaging extension at {extension_path}...")
        package_path = sdk.package_extension(extension_path)
        
        click.echo(f"✅ Extension packaged successfully!")
        click.echo(f"📁 Package: {package_path}")
        
    except Exception as e:
        click.echo(f"❌ Packaging failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--path', type=click.Path(exists=True), default='.', help='Extension directory path')
@click.option('--token', help='Marketplace authentication token')
@click.pass_context
def publish(ctx, path, token):
    """Publish extension to marketplace."""
    sdk = ctx.obj['sdk']
    extension_path = Path(path).resolve()
    
    try:
        click.echo(f"🚀 Publishing extension at {extension_path}...")
        result = sdk.publish_extension(extension_path, marketplace_token=token)
        
        if result.get('success'):
            click.echo(f"✅ Extension published successfully!")
            click.echo(f"📍 Marketplace URL: {result.get('marketplace_url')}")
        else:
            click.echo(f"❌ Publishing failed: {result.get('error')}")
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"❌ Publishing failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def templates(ctx):
    """List available extension templates."""
    sdk = ctx.obj['sdk']
    
    try:
        templates = sdk.list_templates()
        
        click.echo("📋 Available Extension Templates:")
        click.echo()
        
        for template in templates:
            click.echo(f"🔧 {template['name']}")
            click.echo(f"   {template['description']}")
            if 'features' in template:
                click.echo(f"   Features: {', '.join(template['features'])}")
            click.echo()
        
        click.echo("💡 Use 'kari-ext create <name> --template <template>' to create an extension")
        
    except Exception as e:
        click.echo(f"❌ Failed to list templates: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--path', type=click.Path(exists=True), default='.', help='Extension directory path')
@click.pass_context
def info(ctx, path):
    """Show information about an extension."""
    sdk = ctx.obj['sdk']
    extension_path = Path(path).resolve()
    
    try:
        info = sdk.get_extension_info(extension_path)
        
        click.echo(f"📋 Extension Information:")
        click.echo(f"   Name: {info['name']}")
        click.echo(f"   Version: {info['version']}")
        click.echo(f"   Description: {info['description']}")
        click.echo(f"   Author: {info['author']}")
        click.echo(f"   Path: {info['path']}")
        
        # Show capabilities
        capabilities = info['manifest'].get('capabilities', {})
        if any(capabilities.values()):
            click.echo(f"   Capabilities:")
            for cap, enabled in capabilities.items():
                if enabled:
                    click.echo(f"     • {cap.replace('_', ' ').title()}")
        
    except Exception as e:
        click.echo(f"❌ Failed to get extension info: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def marketplace(ctx):
    """Show marketplace information."""
    sdk = ctx.obj['sdk']
    
    try:
        info = sdk.get_marketplace_info()
        
        click.echo("🏪 Kari Extensions Marketplace")
        click.echo(f"   Marketplace: {info['marketplace_url']}")
        click.echo(f"   Registry: {info['registry_url']}")
        click.echo(f"   Documentation: {info['docs_url']}")
        click.echo(f"   Community: {info['community_url']}")
        click.echo(f"   SDK Version: {info['sdk_version']}")
        
    except Exception as e:
        click.echo(f"❌ Failed to get marketplace info: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--path', type=click.Path(exists=True), default='.', help='Extension directory path')
@click.pass_context
def docs(ctx, path):
    """Generate documentation for an extension."""
    sdk = ctx.obj['sdk']
    extension_path = Path(path).resolve()
    
    try:
        click.echo(f"📚 Generating documentation for {extension_path.name}...")
        docs_path = sdk.generate_docs(extension_path)
        
        click.echo(f"✅ Documentation generated!")
        click.echo(f"📁 Location: {docs_path}")
        
    except Exception as e:
        click.echo(f"❌ Documentation generation failed: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()