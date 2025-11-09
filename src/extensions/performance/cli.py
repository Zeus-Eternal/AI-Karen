"""
Performance CLI Tool

Command-line interface for managing extension performance optimization.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import click
import logging

from .config import PerformanceConfig, create_default_config
from .integration import PerformanceIntegration
from .cache_manager import ExtensionCacheManager
from .resource_optimizer import ExtensionResourceOptimizer
from .scaling_manager import ExtensionScalingManager
from .performance_monitor import ExtensionPerformanceMonitor


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool):
    """Extension Performance Management CLI."""
    # Setup logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Load configuration
    if config:
        performance_config = PerformanceConfig.from_file(Path(config))
    else:
        performance_config = create_default_config()
    
    ctx.ensure_object(dict)
    ctx.obj['config'] = performance_config
    ctx.obj['verbose'] = verbose


@cli.group()
@click.pass_context
def cache(ctx):
    """Cache management commands."""
    pass


@cache.command()
@click.option('--size-mb', type=int, help='Cache size in MB')
@click.option('--max-entries', type=int, help='Maximum number of cache entries')
@click.option('--ttl', type=float, help='Default TTL in seconds')
@click.pass_context
def configure(ctx, size_mb: Optional[int], max_entries: Optional[int], ttl: Optional[float]):
    """Configure cache settings."""
    config = ctx.obj['config']
    
    if size_mb is not None:
        config.cache.max_size_mb = size_mb
    if max_entries is not None:
        config.cache.max_entries = max_entries
    if ttl is not None:
        config.cache.default_ttl = ttl
    
    click.echo(f"Cache configuration updated:")
    click.echo(f"  Size: {config.cache.max_size_mb} MB")
    click.echo(f"  Max entries: {config.cache.max_entries}")
    click.echo(f"  Default TTL: {config.cache.default_ttl} seconds")


@cache.command()
@click.pass_context
def stats(ctx):
    """Show cache statistics."""
    async def show_stats():
        config = ctx.obj['config']
        cache_manager = ExtensionCacheManager(
            max_size_mb=config.cache.max_size_mb,
            max_entries=config.cache.max_entries,
            default_ttl=config.cache.default_ttl
        )
        
        await cache_manager.start()
        try:
            stats = await cache_manager.get_stats()
            
            click.echo("Cache Statistics:")
            click.echo(f"  Hits: {stats.hits}")
            click.echo(f"  Misses: {stats.misses}")
            click.echo(f"  Hit rate: {stats.hit_rate:.2%}")
            click.echo(f"  Evictions: {stats.evictions}")
            click.echo(f"  Total size: {stats.total_size / (1024*1024):.2f} MB")
            click.echo(f"  Entry count: {stats.entry_count}")
            
        finally:
            await cache_manager.stop()
    
    asyncio.run(show_stats())


@cache.command()
@click.pass_context
def clear(ctx):
    """Clear all cache entries."""
    async def clear_cache():
        config = ctx.obj['config']
        cache_manager = ExtensionCacheManager(
            max_size_mb=config.cache.max_size_mb,
            max_entries=config.cache.max_entries
        )
        
        await cache_manager.start()
        try:
            await cache_manager.clear()
            click.echo("Cache cleared successfully")
        finally:
            await cache_manager.stop()
    
    asyncio.run(clear_cache())


@cli.group()
@click.pass_context
def resources(ctx):
    """Resource optimization commands."""
    pass


@resources.command()
@click.pass_context
def monitor(ctx):
    """Monitor system resource usage."""
    async def monitor_resources():
        optimizer = ExtensionResourceOptimizer()
        await optimizer.start()
        
        try:
            usage = await optimizer.get_system_resource_usage()
            
            click.echo("System Resource Usage:")
            click.echo(f"  Memory: {usage.get('memory_percent', 0):.1f}%")
            click.echo(f"  Available Memory: {usage.get('memory_available_gb', 0):.2f} GB")
            click.echo(f"  CPU: {usage.get('cpu_percent', 0):.1f}%")
            click.echo(f"  Disk Read: {usage.get('disk_read_mb_per_sec', 0):.2f} MB/s")
            click.echo(f"  Disk Write: {usage.get('disk_write_mb_per_sec', 0):.2f} MB/s")
            click.echo(f"  Network Sent: {usage.get('network_sent_mb_per_sec', 0):.2f} MB/s")
            click.echo(f"  Network Received: {usage.get('network_recv_mb_per_sec', 0):.2f} MB/s")
            
        finally:
            await optimizer.stop()
    
    asyncio.run(monitor_resources())


@resources.command()
@click.argument('extension_name')
@click.pass_context
def optimize(ctx, extension_name: str):
    """Optimize resources for a specific extension."""
    async def optimize_extension():
        optimizer = ExtensionResourceOptimizer()
        await optimizer.start()
        
        try:
            # Memory optimization
            memory_result = await optimizer.optimize_extension_memory(extension_name)
            cpu_result = await optimizer.optimize_extension_cpu(extension_name)
            
            click.echo(f"Optimization results for {extension_name}:")
            click.echo(f"  Memory optimization: {'Success' if memory_result else 'No improvement'}")
            click.echo(f"  CPU optimization: {'Success' if cpu_result else 'No improvement'}")
            
            # Get recommendations
            recommendations = await optimizer.get_optimization_recommendations()
            ext_recommendations = [r for r in recommendations if r.extension_name == extension_name]
            
            if ext_recommendations:
                click.echo("  Recommendations:")
                for rec in ext_recommendations:
                    click.echo(f"    - {rec.description}")
            
        finally:
            await optimizer.stop()
    
    asyncio.run(optimize_extension())


@cli.group()
@click.pass_context
def scaling(ctx):
    """Scaling management commands."""
    pass


@scaling.command()
@click.argument('extension_name')
@click.argument('target_instances', type=int)
@click.option('--reason', default='manual', help='Reason for scaling')
@click.pass_context
def scale(ctx, extension_name: str, target_instances: int, reason: str):
    """Scale an extension to target number of instances."""
    async def scale_extension():
        config = ctx.obj['config']
        if not config.scaling.enable_scaling:
            click.echo("Scaling is disabled in configuration")
            return
        
        optimizer = ExtensionResourceOptimizer()
        await optimizer.start()
        
        scaling_manager = ExtensionScalingManager(optimizer)
        await scaling_manager.start()
        
        try:
            success = await scaling_manager.scale_extension(
                extension_name=extension_name,
                target_instances=target_instances,
                reason=reason
            )
            
            if success:
                click.echo(f"Successfully scaled {extension_name} to {target_instances} instances")
            else:
                click.echo(f"Failed to scale {extension_name}")
                
        finally:
            await scaling_manager.stop()
            await optimizer.stop()
    
    asyncio.run(scale_extension())


@scaling.command()
@click.argument('extension_name')
@click.pass_context
def status(ctx, extension_name: str):
    """Show scaling status for an extension."""
    async def show_scaling_status():
        config = ctx.obj['config']
        if not config.scaling.enable_scaling:
            click.echo("Scaling is disabled in configuration")
            return
        
        optimizer = ExtensionResourceOptimizer()
        await optimizer.start()
        
        scaling_manager = ExtensionScalingManager(optimizer)
        await scaling_manager.start()
        
        try:
            instances = await scaling_manager.get_extension_instances(extension_name)
            
            click.echo(f"Scaling status for {extension_name}:")
            click.echo(f"  Total instances: {len(instances)}")
            
            for instance in instances:
                click.echo(f"    {instance.instance_id}: {instance.status} (PID: {instance.process_id})")
                
        finally:
            await scaling_manager.stop()
            await optimizer.stop()
    
    asyncio.run(show_scaling_status())


@cli.group()
@click.pass_context
def monitor(ctx):
    """Performance monitoring commands."""
    pass


@monitor.command()
@click.argument('extension_name')
@click.option('--hours', type=float, default=24.0, help='Time period in hours')
@click.pass_context
def summary(ctx, extension_name: str, hours: float):
    """Show performance summary for an extension."""
    async def show_summary():
        config = ctx.obj['config']
        if not config.monitoring.enable_monitoring:
            click.echo("Monitoring is disabled in configuration")
            return
        
        # Create minimal performance system for monitoring
        cache_manager = ExtensionCacheManager()
        await cache_manager.start()
        
        optimizer = ExtensionResourceOptimizer()
        await optimizer.start()
        
        scaling_manager = ExtensionScalingManager(optimizer)
        await scaling_manager.start()
        
        monitor = ExtensionPerformanceMonitor(
            cache_manager=cache_manager,
            resource_optimizer=optimizer,
            scaling_manager=scaling_manager
        )
        await monitor.start()
        
        try:
            summary = await monitor.get_performance_summary(extension_name, hours)
            
            if summary:
                click.echo(f"Performance Summary for {extension_name} (last {hours} hours):")
                click.echo(f"  Average CPU: {summary.avg_cpu_usage:.1f}%")
                click.echo(f"  Max CPU: {summary.max_cpu_usage:.1f}%")
                click.echo(f"  Average Memory: {summary.avg_memory_usage:.1f} MB")
                click.echo(f"  Max Memory: {summary.max_memory_usage:.1f} MB")
                click.echo(f"  Total Requests: {summary.total_requests}")
                click.echo(f"  Average Response Time: {summary.avg_response_time:.1f} ms")
                click.echo(f"  Total Errors: {summary.total_errors}")
                click.echo(f"  Performance Score: {summary.performance_score:.1f}/100")
                click.echo(f"  Reliability Score: {summary.reliability_score:.1f}/100")
                click.echo(f"  Efficiency Score: {summary.efficiency_score:.1f}/100")
                
                if summary.recommendations:
                    click.echo("  Recommendations:")
                    for rec in summary.recommendations:
                        click.echo(f"    - {rec}")
            else:
                click.echo(f"No performance data available for {extension_name}")
                
        finally:
            await monitor.stop()
            await scaling_manager.stop()
            await optimizer.stop()
            await cache_manager.stop()
    
    asyncio.run(show_summary())


@monitor.command()
@click.option('--extension', help='Filter alerts by extension name')
@click.pass_context
def alerts(ctx, extension: Optional[str]):
    """Show active performance alerts."""
    async def show_alerts():
        config = ctx.obj['config']
        if not config.monitoring.enable_monitoring:
            click.echo("Monitoring is disabled in configuration")
            return
        
        # Create minimal performance system for monitoring
        cache_manager = ExtensionCacheManager()
        await cache_manager.start()
        
        optimizer = ExtensionResourceOptimizer()
        await optimizer.start()
        
        scaling_manager = ExtensionScalingManager(optimizer)
        await scaling_manager.start()
        
        monitor = ExtensionPerformanceMonitor(
            cache_manager=cache_manager,
            resource_optimizer=optimizer,
            scaling_manager=scaling_manager
        )
        await monitor.start()
        
        try:
            alerts = await monitor.get_active_alerts(extension)
            
            if alerts:
                click.echo(f"Active Performance Alerts:")
                for alert in alerts:
                    click.echo(f"  [{alert.severity.upper()}] {alert.extension_name}: {alert.message}")
            else:
                click.echo("No active performance alerts")
                
        finally:
            await monitor.stop()
            await scaling_manager.stop()
            await optimizer.stop()
            await cache_manager.stop()
    
    asyncio.run(show_alerts())


@cli.group()
@click.pass_context
def config(ctx):
    """Configuration management commands."""
    pass


@config.command()
@click.pass_context
def show(ctx):
    """Show current configuration."""
    config = ctx.obj['config']
    config_dict = config.to_dict()
    
    click.echo("Current Performance Configuration:")
    click.echo(json.dumps(config_dict, indent=2))


@config.command()
@click.argument('output_path', type=click.Path())
@click.pass_context
def export(ctx, output_path: str):
    """Export configuration to file."""
    config = ctx.obj['config']
    output_file = Path(output_path)
    
    config.save_to_file(output_file)
    click.echo(f"Configuration exported to {output_file}")


@config.command()
@click.argument('extension_name')
@click.option('--loading-strategy', type=click.Choice(['eager', 'lazy', 'on_demand', 'background']))
@click.option('--max-memory-mb', type=int, help='Maximum memory in MB')
@click.option('--max-cpu-percent', type=float, help='Maximum CPU percentage')
@click.option('--enable-scaling', is_flag=True, help='Enable scaling for this extension')
@click.pass_context
def extension(ctx, extension_name: str, loading_strategy: Optional[str], 
              max_memory_mb: Optional[int], max_cpu_percent: Optional[float],
              enable_scaling: bool):
    """Configure performance settings for a specific extension."""
    config = ctx.obj['config']
    ext_config = config.get_extension_config(extension_name)
    
    if loading_strategy:
        ext_config.loading_strategy = loading_strategy
    if max_memory_mb is not None:
        ext_config.max_memory_mb = max_memory_mb
    if max_cpu_percent is not None:
        ext_config.max_cpu_percent = max_cpu_percent
    if enable_scaling:
        ext_config.enable_scaling = True
    
    click.echo(f"Updated configuration for {extension_name}:")
    click.echo(f"  Loading strategy: {ext_config.loading_strategy}")
    click.echo(f"  Max memory: {ext_config.max_memory_mb} MB")
    click.echo(f"  Max CPU: {ext_config.max_cpu_percent}%")
    click.echo(f"  Scaling enabled: {ext_config.enable_scaling}")


@cli.command()
@click.argument('extension_root', type=click.Path(exists=True))
@click.option('--config-file', type=click.Path(), help='Configuration file to use')
@click.pass_context
def benchmark(ctx, extension_root: str, config_file: Optional[str]):
    """Run performance benchmark on extensions."""
    async def run_benchmark():
        # Load configuration
        if config_file:
            config = PerformanceConfig.from_file(Path(config_file))
        else:
            config = ctx.obj['config']
        
        # Create performance integration
        integration = PerformanceIntegration(
            extension_root=Path(extension_root),
            cache_size_mb=config.cache.max_size_mb,
            enable_scaling=config.scaling.enable_scaling,
            enable_monitoring=config.monitoring.enable_monitoring
        )
        
        await integration.start()
        
        try:
            click.echo("Running performance benchmark...")
            
            # Get performance status
            status = await integration.get_performance_status()
            
            click.echo("Benchmark Results:")
            click.echo(f"  Cache hit rate: {status['cache_stats'].hit_rate:.2%}")
            click.echo(f"  System memory usage: {status['system_resources'].get('memory_percent', 0):.1f}%")
            click.echo(f"  System CPU usage: {status['system_resources'].get('cpu_percent', 0):.1f}%")
            
            # Show loading metrics if available
            loading_metrics = status.get('loading_metrics', [])
            if loading_metrics:
                avg_load_time = sum(m.total_load_time for m in loading_metrics) / len(loading_metrics)
                click.echo(f"  Average extension load time: {avg_load_time:.2f}s")
            
        finally:
            await integration.stop()
    
    asyncio.run(run_benchmark())


if __name__ == '__main__':
    cli()