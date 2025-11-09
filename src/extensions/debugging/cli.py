"""
Extension Debugging CLI

Command-line interface for extension debugging and monitoring operations.
"""

import asyncio
import click
import json
from datetime import datetime, timedelta
from typing import Optional

from .debug_manager import ExtensionDebugManager, DebugConfiguration
from .models import LogLevel, AlertSeverity


@click.group()
@click.option('--extension-id', required=True, help='Extension ID to debug')
@click.option('--extension-name', help='Extension name (defaults to extension ID)')
@click.option('--config-file', help='Path to debug configuration file')
@click.pass_context
def debug_cli(ctx, extension_id: str, extension_name: Optional[str], config_file: Optional[str]):
    """Extension debugging and monitoring CLI."""
    if extension_name is None:
        extension_name = extension_id
    
    # Load configuration
    config = DebugConfiguration()
    if config_file:
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                for key, value in config_data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
        except Exception as e:
            click.echo(f"Warning: Failed to load config file: {e}")
    
    # Create debug manager
    debug_manager = ExtensionDebugManager(extension_id, extension_name, config)
    
    # Store in context
    ctx.ensure_object(dict)
    ctx.obj['debug_manager'] = debug_manager
    ctx.obj['extension_id'] = extension_id
    ctx.obj['extension_name'] = extension_name


@debug_cli.command()
@click.pass_context
def start(ctx):
    """Start the debug manager."""
    debug_manager = ctx.obj['debug_manager']
    
    async def start_debug():
        await debug_manager.start()
        click.echo(f"Debug manager started for {ctx.obj['extension_name']}")
        
        # Show enabled components
        components = debug_manager._get_enabled_components()
        click.echo(f"Enabled components: {', '.join(components)}")
    
    asyncio.run(start_debug())


@debug_cli.command()
@click.pass_context
def stop(ctx):
    """Stop the debug manager."""
    debug_manager = ctx.obj['debug_manager']
    
    async def stop_debug():
        await debug_manager.stop()
        click.echo(f"Debug manager stopped for {ctx.obj['extension_name']}")
    
    asyncio.run(stop_debug())


@debug_cli.command()
@click.pass_context
def status(ctx):
    """Show debug manager status."""
    debug_manager = ctx.obj['debug_manager']
    summary = debug_manager.get_debug_summary()
    
    click.echo(f"Extension: {summary['extension_name']} ({summary['extension_id']})")
    click.echo(f"Status: {summary['debug_manager_status']}")
    click.echo(f"Health: {summary['overall_health']}")
    click.echo(f"Active Sessions: {summary['active_sessions']}")
    click.echo(f"Debug Overhead: {summary['debug_overhead_ms']:.2f}ms")
    click.echo(f"Enabled Components: {', '.join(summary['enabled_components'])}")
    
    if 'logging' in summary:
        click.echo(f"Total Logs: {summary['logging']['total_logs']}")
    
    if 'metrics' in summary:
        click.echo(f"Metrics: {summary['metrics']}")
    
    if 'errors' in summary:
        click.echo(f"Total Errors: {summary['errors']['total_errors']}")
        click.echo(f"Error Rate: {summary['errors']['error_rate']:.2f}/hour")
    
    if 'alerts' in summary:
        click.echo(f"Active Alerts: {summary['alerts']['active_alerts']}")


@debug_cli.group()
def logs():
    """Log management commands."""
    pass


@logs.command()
@click.option('--level', type=click.Choice(['debug', 'info', 'warning', 'error', 'critical']), help='Filter by log level')
@click.option('--limit', default=50, help='Maximum number of logs to show')
@click.option('--search', help='Search term to filter logs')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.pass_context
def show(ctx, level: Optional[str], limit: int, search: Optional[str], follow: bool):
    """Show extension logs."""
    debug_manager = ctx.obj['debug_manager']
    
    if not debug_manager.logger:
        click.echo("Error: Logging not enabled")
        return
    
    # Convert level to enum
    log_level = None
    if level:
        log_level = LogLevel(level.lower())
    
    if follow:
        # Follow mode - show new logs as they arrive
        click.echo("Following logs (Ctrl+C to stop)...")
        last_timestamp = datetime.utcnow()
        
        try:
            while True:
                logs = debug_manager.logger.get_logs(level=log_level, limit=1000)
                new_logs = [log for log in logs if log.timestamp > last_timestamp]
                
                for log in new_logs:
                    if not search or search.lower() in log.message.lower():
                        timestamp = log.timestamp.strftime('%H:%M:%S')
                        level_color = {
                            'debug': 'white',
                            'info': 'blue',
                            'warning': 'yellow',
                            'error': 'red',
                            'critical': 'bright_red'
                        }.get(log.level.value, 'white')
                        
                        click.echo(f"{timestamp} [{click.style(log.level.value.upper(), fg=level_color)}] {log.source}: {log.message}")
                
                if new_logs:
                    last_timestamp = max(log.timestamp for log in new_logs)
                
                asyncio.sleep(1)
        except KeyboardInterrupt:
            click.echo("\nStopped following logs")
    else:
        # Show recent logs
        logs = debug_manager.logger.get_logs(level=log_level, limit=limit)
        
        if search:
            logs = [log for log in logs if search.lower() in log.message.lower()]
        
        for log in logs[-limit:]:
            timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            level_color = {
                'debug': 'white',
                'info': 'blue',
                'warning': 'yellow',
                'error': 'red',
                'critical': 'bright_red'
            }.get(log.level.value, 'white')
            
            click.echo(f"{timestamp} [{click.style(log.level.value.upper(), fg=level_color)}] {log.source}: {log.message}")
            
            if log.metadata:
                for key, value in log.metadata.items():
                    click.echo(f"  {key}: {value}")


@logs.command()
@click.option('--format', type=click.Choice(['json', 'csv']), default='json', help='Export format')
@click.option('--output', help='Output file path')
@click.pass_context
def export(ctx, format: str, output: Optional[str]):
    """Export logs."""
    debug_manager = ctx.obj['debug_manager']
    
    if not debug_manager.logger:
        click.echo("Error: Logging not enabled")
        return
    
    try:
        exported_data = debug_manager.logger.export_logs(format)
        
        if output:
            with open(output, 'w') as f:
                f.write(exported_data)
            click.echo(f"Logs exported to {output}")
        else:
            click.echo(exported_data)
    except Exception as e:
        click.echo(f"Error exporting logs: {e}")


@debug_cli.group()
def metrics():
    """Metrics management commands."""
    pass


@metrics.command()
@click.option('--metric', help='Specific metric name to show')
@click.option('--hours', default=1, help='Time window in hours')
@click.pass_context
def show(ctx, metric: Optional[str], hours: int):
    """Show extension metrics."""
    debug_manager = ctx.obj['debug_manager']
    
    if not debug_manager.metrics_collector:
        click.echo("Error: Metrics collection not enabled")
        return
    
    since = datetime.utcnow() - timedelta(hours=hours)
    metrics = debug_manager.metrics_collector.get_metrics(metric_name=metric, since=since)
    
    if not metrics:
        click.echo("No metrics found")
        return
    
    # Group by metric name
    metrics_by_name = {}
    for m in metrics:
        if m.metric_name not in metrics_by_name:
            metrics_by_name[m.metric_name] = []
        metrics_by_name[m.metric_name].append(m)
    
    for metric_name, metric_list in metrics_by_name.items():
        click.echo(f"\n{metric_name}:")
        
        if len(metric_list) > 1:
            values = [m.value for m in metric_list]
            click.echo(f"  Count: {len(values)}")
            click.echo(f"  Current: {values[-1]:.2f} {metric_list[-1].unit}")
            click.echo(f"  Average: {sum(values) / len(values):.2f}")
            click.echo(f"  Min: {min(values):.2f}")
            click.echo(f"  Max: {max(values):.2f}")
        else:
            m = metric_list[0]
            click.echo(f"  Value: {m.value:.2f} {m.unit}")
            click.echo(f"  Timestamp: {m.timestamp}")


@metrics.command()
@click.pass_context
def current(ctx):
    """Show current resource usage."""
    debug_manager = ctx.obj['debug_manager']
    
    if not debug_manager.metrics_collector:
        click.echo("Error: Metrics collection not enabled")
        return
    
    usage = debug_manager.metrics_collector.get_current_resource_usage()
    
    click.echo("Current Resource Usage:")
    for key, value in usage.items():
        unit = {
            'cpu_percent': '%',
            'memory_mb': 'MB',
            'memory_percent': '%',
            'disk_read_mb': 'MB',
            'disk_write_mb': 'MB',
            'network_connections': '',
            'threads': '',
            'file_descriptors': ''
        }.get(key, '')
        
        click.echo(f"  {key.replace('_', ' ').title()}: {value:.2f} {unit}")


@debug_cli.group()
def errors():
    """Error management commands."""
    pass


@errors.command()
@click.option('--hours', default=24, help='Time window in hours')
@click.option('--type', help='Filter by error type')
@click.option('--unresolved', is_flag=True, help='Show only unresolved errors')
@click.pass_context
def show(ctx, hours: int, type: Optional[str], unresolved: bool):
    """Show extension errors."""
    debug_manager = ctx.obj['debug_manager']
    
    if not debug_manager.error_tracker:
        click.echo("Error: Error tracking not enabled")
        return
    
    since = datetime.utcnow() - timedelta(hours=hours)
    errors = debug_manager.error_tracker.get_errors(
        error_type=type,
        since=since,
        unresolved_only=unresolved
    )
    
    if not errors:
        click.echo("No errors found")
        return
    
    for error in errors[-20:]:  # Show last 20 errors
        timestamp = error.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        status = "RESOLVED" if error.resolved else "UNRESOLVED"
        status_color = 'green' if error.resolved else 'red'
        
        click.echo(f"{timestamp} [{click.style(status, fg=status_color)}] {error.error_type}: {error.error_message}")
        
        if error.context:
            for key, value in error.context.items():
                if key != 'suggestions':
                    click.echo(f"  {key}: {value}")


@errors.command()
@click.pass_context
def patterns(ctx):
    """Show error patterns."""
    debug_manager = ctx.obj['debug_manager']
    
    if not debug_manager.error_tracker:
        click.echo("Error: Error tracking not enabled")
        return
    
    patterns = debug_manager.error_tracker.get_error_patterns()
    
    if not patterns:
        click.echo("No error patterns found")
        return
    
    click.echo("Error Patterns:")
    for pattern in patterns:
        click.echo(f"\nPattern: {pattern.pattern_id}")
        click.echo(f"  Type: {pattern.error_type}")
        click.echo(f"  Occurrences: {pattern.occurrences}")
        click.echo(f"  First Seen: {pattern.first_seen}")
        click.echo(f"  Last Seen: {pattern.last_seen}")
        click.echo(f"  Message Pattern: {pattern.message_pattern}")
        
        if pattern.resolution_suggestions:
            click.echo("  Suggestions:")
            for suggestion in pattern.resolution_suggestions:
                click.echo(f"    - {suggestion}")


@debug_cli.group()
def alerts():
    """Alert management commands."""
    pass


@alerts.command()
@click.option('--severity', type=click.Choice(['low', 'medium', 'high', 'critical']), help='Filter by severity')
@click.pass_context
def show(ctx, severity: Optional[str]):
    """Show active alerts."""
    debug_manager = ctx.obj['debug_manager']
    
    if not debug_manager.alert_manager:
        click.echo("Error: Alerting not enabled")
        return
    
    severity_filter = None
    if severity:
        severity_filter = AlertSeverity(severity.lower())
    
    alerts = debug_manager.alert_manager.get_active_alerts(severity=severity_filter)
    
    if not alerts:
        click.echo("No active alerts")
        return
    
    for alert in alerts:
        timestamp = alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        severity_color = {
            'low': 'white',
            'medium': 'yellow',
            'high': 'red',
            'critical': 'bright_red'
        }.get(alert.severity.value, 'white')
        
        click.echo(f"{timestamp} [{click.style(alert.severity.value.upper(), fg=severity_color)}] {alert.title}")
        click.echo(f"  {alert.message}")
        
        if alert.metric_name:
            click.echo(f"  Metric: {alert.metric_name} = {alert.current_value}")


@alerts.command()
@click.argument('alert_id')
@click.option('--notes', help='Resolution notes')
@click.pass_context
def resolve(ctx, alert_id: str, notes: Optional[str]):
    """Resolve an alert."""
    debug_manager = ctx.obj['debug_manager']
    
    if not debug_manager.alert_manager:
        click.echo("Error: Alerting not enabled")
        return
    
    async def resolve_alert():
        await debug_manager.alert_manager.resolve_alert(alert_id, notes)
        click.echo(f"Alert {alert_id} resolved")
    
    asyncio.run(resolve_alert())


@debug_cli.group()
def sessions():
    """Debug session management commands."""
    pass


@sessions.command()
@click.option('--session-id', help='Custom session ID')
@click.option('--profiling', is_flag=True, help='Enable profiling')
@click.option('--tracing', is_flag=True, help='Enable tracing')
@click.pass_context
def start(ctx, session_id: Optional[str], profiling: bool, tracing: bool):
    """Start a debug session."""
    debug_manager = ctx.obj['debug_manager']
    
    config = {
        'enable_profiling': profiling,
        'enable_tracing': tracing
    }
    
    session_id = debug_manager.start_debug_session(session_id, config)
    click.echo(f"Debug session started: {session_id}")


@sessions.command()
@click.argument('session_id')
@click.option('--output', help='Output file for session data')
@click.pass_context
def stop(ctx, session_id: str, output: Optional[str]):
    """Stop a debug session."""
    debug_manager = ctx.obj['debug_manager']
    
    session = debug_manager.stop_debug_session(session_id)
    if not session:
        click.echo(f"Session {session_id} not found")
        return
    
    click.echo(f"Debug session stopped: {session_id}")
    click.echo(f"Duration: {(session.end_time - session.start_time).total_seconds():.2f} seconds")
    
    if output:
        with open(output, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)
        click.echo(f"Session data saved to {output}")


@sessions.command()
@click.pass_context
def list(ctx):
    """List active debug sessions."""
    debug_manager = ctx.obj['debug_manager']
    
    if not debug_manager.active_sessions:
        click.echo("No active debug sessions")
        return
    
    click.echo("Active Debug Sessions:")
    for session in debug_manager.active_sessions.values():
        duration = (datetime.utcnow() - session.start_time).total_seconds()
        click.echo(f"  {session.id}: {duration:.0f}s")


@debug_cli.command()
@click.pass_context
def health(ctx):
    """Run health diagnostics."""
    debug_manager = ctx.obj['debug_manager']
    
    async def run_health_check():
        health_status = await debug_manager.run_diagnostics()
        
        click.echo(f"Overall Health: {click.style(health_status.overall_status.upper(), fg='green' if health_status.overall_status == 'healthy' else 'red')}")
        click.echo(f"Last Check: {health_status.last_check}")
        
        click.echo("\nDiagnostic Results:")
        for diagnostic in health_status.diagnostics:
            status_color = {
                'healthy': 'green',
                'warning': 'yellow',
                'error': 'red'
            }.get(diagnostic.status, 'white')
            
            click.echo(f"  {diagnostic.check_name}: {click.style(diagnostic.status.upper(), fg=status_color)}")
            click.echo(f"    {diagnostic.message}")
    
    asyncio.run(run_health_check())


@debug_cli.command()
@click.option('--format', type=click.Choice(['json']), default='json', help='Export format')
@click.option('--output', help='Output file path')
@click.pass_context
def export(ctx, format: str, output: Optional[str]):
    """Export all debug data."""
    debug_manager = ctx.obj['debug_manager']
    
    try:
        exported_data = debug_manager.export_debug_data(format)
        
        if output:
            with open(output, 'w') as f:
                f.write(exported_data)
            click.echo(f"Debug data exported to {output}")
        else:
            click.echo(exported_data)
    except Exception as e:
        click.echo(f"Error exporting debug data: {e}")


if __name__ == '__main__':
    debug_cli()