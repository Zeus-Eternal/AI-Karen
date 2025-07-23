#!/usr/bin/env python3
"""
Demo script for the AI Karen Plugin System.

This script demonstrates the plugin discovery, validation, registration,
and execution capabilities of the new plugin system.
"""

import asyncio
import json
from pathlib import Path

import sys
sys.path.append('src')

from ai_karen_engine.services.plugin_service import (
    PluginService, ExecutionMode
)
from ai_karen_engine.services.plugin_registry import PluginRegistry
from ai_karen_engine.services.plugin_execution import PluginExecutionEngine


async def main():
    """Main demo function."""
    print("🚀 AI Karen Plugin System Demo")
    print("=" * 50)
    
    # Initialize plugin service
    print("\n1. Initializing Plugin Service...")
    service = PluginService(marketplace_path=Path("plugin_marketplace"))
    await service.initialize()
    print("✅ Plugin service initialized successfully!")
    
    # Discover plugins
    print("\n2. Discovering Plugins...")
    discovered = await service.discover_plugins()
    print(f"✅ Discovered {len(discovered)} plugins:")
    for name, metadata in discovered.items():
        print(f"   - {name} (v{metadata.manifest.version}) - {metadata.manifest.description}")
    
    # Validate and register plugins
    print("\n3. Validating and Registering Plugins...")
    results = await service.validate_and_register_all_discovered()
    successful = sum(1 for success in results.values() if success)
    print(f"✅ Successfully registered {successful}/{len(results)} plugins:")
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {name}")
    
    # Get available plugins
    print("\n4. Available Plugins:")
    available = service.get_available_plugins()
    for plugin in available:
        print(f"   📦 {plugin.manifest.name}")
        print(f"      Version: {plugin.manifest.version}")
        print(f"      Category: {plugin.manifest.category}")
        print(f"      Type: {plugin.manifest.plugin_type.value}")
        print(f"      Author: {plugin.manifest.author}")
        print(f"      Description: {plugin.manifest.description}")
        if plugin.manifest.tags:
            print(f"      Tags: {', '.join(plugin.manifest.tags)}")
        print()
    
    # Execute hello-world plugin if available
    hello_plugin = service.get_plugin("hello-world")
    if hello_plugin:
        print("5. Executing Hello World Plugin...")
        try:
            result = await service.execute_plugin(
                plugin_name="hello-world",
                parameters={"name": "AI Karen User"},
                execution_mode=ExecutionMode.DIRECT,  # Use direct mode to avoid sandbox issues
                timeout_seconds=10
            )
            
            print(f"✅ Plugin execution completed!")
            print(f"   Status: {result.status.value}")
            print(f"   Result: {result.result}")
            print(f"   Execution time: {result.execution_time:.3f}s")
            
        except Exception as e:
            print(f"❌ Plugin execution failed: {e}")
    
    # Execute math calculator if available
    math_plugin = service.get_plugin("math-calculator")
    if math_plugin:
        print("\n6. Executing Math Calculator Plugin...")
        try:
            result = await service.execute_plugin(
                plugin_name="math-calculator",
                parameters={"operation": "multiply", "a": 6, "b": 7},
                execution_mode=ExecutionMode.DIRECT,
                timeout_seconds=10
            )
            
            print(f"✅ Plugin execution completed!")
            print(f"   Status: {result.status.value}")
            print(f"   Result: {result.result}")
            print(f"   Execution time: {result.execution_time:.3f}s")
            
        except Exception as e:
            print(f"❌ Plugin execution failed: {e}")
    
    # Show service statistics
    print("\n7. Service Statistics:")
    stats = service.get_service_stats()
    print(f"   Total plugins: {stats['registry_stats']['total_plugins']}")
    print(f"   Registered plugins: {stats['registry_stats']['by_status'].get('registered', 0)}")
    print(f"   Total executions: {stats['execution_metrics']['executions_total']}")
    print(f"   Successful executions: {stats['execution_metrics']['executions_successful']}")
    
    # Health check
    print("\n8. Health Check:")
    health = await service.health_check()
    print(f"   Overall status: {health['status']}")
    for component, info in health['components'].items():
        print(f"   {component}: {info['status']}")
    
    # Get marketplace info
    print("\n9. Plugin Marketplace Info:")
    registry_stats = stats['registry_stats']
    print(f"   Total plugins: {registry_stats['total_plugins']}")
    print(f"   Categories: {list(registry_stats['by_category'].keys())}")
    print(f"   Types: {list(registry_stats['by_type'].keys())}")
    
    # Cleanup
    await service.cleanup()
    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())