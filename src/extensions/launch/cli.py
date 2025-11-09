"""
CLI for extension ecosystem launch.
"""

import click
import asyncio
import json
from pathlib import Path

from .launch_manager import LaunchManager


@click.group()
def launch_cli():
    """Kari Extensions Ecosystem Launch Commands."""
    pass


@launch_cli.command()
@click.option('--phase', default='beta', type=click.Choice(['alpha', 'beta', 'stable']), 
              help='Launch phase to execute')
@click.option('--dry-run', is_flag=True, help='Simulate launch without making changes')
def execute(phase, dry_run):
    """Execute the extension ecosystem launch."""
    if dry_run:
        click.echo("🧪 DRY RUN MODE - No changes will be made")
    
    click.echo(f"🚀 Executing Kari Extensions Ecosystem Launch - {phase.upper()} Phase")
    
    try:
        launch_manager = LaunchManager()
        
        # Run the launch
        results = asyncio.run(launch_manager.execute_launch(phase))
        
        # Display results
        if results["success"]:
            click.echo("✅ Launch completed successfully!")
            click.echo(f"📊 Completed tasks: {len(results['completed_tasks'])}")
            click.echo(f"📚 Extensions published: {len(results.get('published_extensions', []))}")
            click.echo(f"🤝 Community channels: {len(results.get('community_channels', []))}")
        else:
            click.echo("⚠️  Launch completed with issues")
            click.echo(f"❌ Failed tasks: {len(results['failed_tasks'])}")
            for task in results['failed_tasks']:
                click.echo(f"  • {task}")
        
        # Show metrics
        if results.get("metrics"):
            click.echo("\n📈 Launch Metrics:")
            metrics = results["metrics"]
            click.echo(f"  • Marketplace Extensions: {metrics.get('marketplace_extensions', 0)}")
            click.echo(f"  • Active Developers: {metrics.get('active_developers', 0)}")
            click.echo(f"  • Community Members: {metrics.get('community_members', 0)}")
        
    except Exception as e:
        click.echo(f"❌ Launch failed: {e}")
        exit(1)


@launch_cli.command()
def status():
    """Check launch status."""
    launch_manager = LaunchManager()
    status_info = launch_manager.get_launch_status()
    
    click.echo("📊 Extension Ecosystem Launch Status")
    click.echo(f"Status: {status_info['status']}")
    
    if status_info['status'] == 'launched':
        click.echo(f"Phase: {status_info['phase']}")
        click.echo(f"Launched: {status_info['launched_at']}")
        click.echo(f"Completed Tasks: {status_info['completed_tasks']}")
        click.echo(f"Extensions Published: {status_info['extensions_published']}")
        click.echo(f"Community Channels: {status_info['community_channels']}")
        
        if status_info['failed_tasks'] > 0:
            click.echo(f"⚠️  Failed Tasks: {status_info['failed_tasks']}")
    
    elif status_info['status'] == 'not_launched':
        click.echo("Extension ecosystem has not been launched yet")
        click.echo("Run 'kari-ext-launch execute' to start the launch process")


@launch_cli.command()
def metrics():
    """Show post-launch metrics."""
    launch_manager = LaunchManager()
    
    # Check if launched
    status_info = launch_manager.get_launch_status()
    if status_info['status'] == 'not_launched':
        click.echo("Extension ecosystem has not been launched yet")
        return
    
    metrics = launch_manager.get_post_launch_metrics()
    
    click.echo("📈 Post-Launch Metrics")
    click.echo(f"SDK Downloads: {metrics['sdk_downloads']}")
    click.echo(f"Active Developers: {metrics['active_developers']}")
    click.echo(f"Extensions Published: {metrics['extensions_published']}")
    click.echo(f"Community Members: {metrics['community_members']}")
    click.echo(f"Marketplace Visits: {metrics['marketplace_visits']}")
    click.echo(f"Documentation Views: {metrics['documentation_views']}")
    click.echo(f"Support Tickets: {metrics['support_tickets']}")
    click.echo(f"GitHub Stars: {metrics['github_stars']}")
    click.echo(f"Discord Members: {metrics['discord_members']}")


@launch_cli.command()
@click.option('--output', type=click.Path(), help='Output file for launch report')
def report(output):
    """Generate launch report."""
    launch_manager = LaunchManager()
    
    # Get launch status and metrics
    status_info = launch_manager.get_launch_status()
    
    if status_info['status'] == 'not_launched':
        click.echo("Extension ecosystem has not been launched yet")
        return
    
    metrics = launch_manager.get_post_launch_metrics()
    
    # Generate report
    report_data = {
        "launch_status": status_info,
        "metrics": metrics,
        "generated_at": click.DateTime().convert(None, None, None).isoformat()
    }
    
    if output:
        output_path = Path(output)
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        click.echo(f"📄 Launch report saved to {output_path}")
    else:
        click.echo("📄 Launch Report")
        click.echo(json.dumps(report_data, indent=2))


@launch_cli.command()
def checklist():
    """Show launch checklist."""
    launch_manager = LaunchManager()
    checklist_items = launch_manager.launch_config["launch_checklist"]
    
    click.echo("✅ Extension Ecosystem Launch Checklist")
    click.echo()
    
    for i, item in enumerate(checklist_items, 1):
        click.echo(f"{i:2d}. {item.replace('_', ' ').title()}")
    
    click.echo()
    click.echo("💡 Use 'kari-ext-launch execute' to run the launch process")


if __name__ == '__main__':
    launch_cli()