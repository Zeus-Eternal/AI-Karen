#!/usr/bin/env python3
"""
Demo script for the Tool Abstraction Service.

This script demonstrates the core functionality of the tool service including
tool registration, discovery, validation, and execution.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from ai_karen_engine.services.tool_service import (
    ToolService, 
    ToolRegistry, 
    ToolInput,
    ToolCategory,
    initialize_tool_service
)
from ai_karen_engine.services.tools.core_tools import (
    DateTool,
    TimeTool,
    WeatherTool,
    BookDatabaseTool
)
from ai_karen_engine.services.tools.registry import register_core_tools


async def demo_tool_service():
    """Demonstrate tool service functionality."""
    print("=" * 60)
    print("AI Karen Tool Abstraction Service Demo")
    print("=" * 60)
    
    # Initialize tool service with core tools
    print("\n1. Initializing tool service...")
    tool_service = await initialize_tool_service()
    
    # Register basic tools manually to avoid dependency issues
    basic_tools = [
        (DateTool(), ["current_date", "date", "today"]),
        (TimeTool(), ["current_time", "time", "clock"]),
        (WeatherTool(), ["weather", "forecast"]),
        (BookDatabaseTool(), ["book_lookup", "book_search"])
    ]
    
    for tool, aliases in basic_tools:
        tool_service.register_tool(tool, aliases)
    
    print(f"✓ Tool service initialized with {len(basic_tools)} core tools")
    
    # List available tools
    print("\n2. Available tools:")
    tools = tool_service.list_tools()
    for i, tool_name in enumerate(tools, 1):
        metadata = tool_service.get_tool_metadata(tool_name)
        print(f"   {i:2d}. {tool_name} - {metadata.description}")
    
    # Show tool categories
    print("\n3. Tools by category:")
    for category in ToolCategory:
        category_tools = tool_service.list_tools(category=category)
        if category_tools:
            print(f"   {category.value}: {', '.join(category_tools)}")
    
    # Demonstrate tool execution
    print("\n4. Tool execution examples:")
    
    # Example 1: Get current date
    print("\n   a) Getting current date:")
    date_input = ToolInput(
        tool_name="get_current_date",
        parameters={}
    )
    result = await tool_service.execute_tool(date_input)
    print(f"      Result: {result.result}")
    print(f"      Execution time: {result.execution_time:.3f}s")
    
    # Example 2: Get current time
    print("\n   b) Getting current time:")
    time_input = ToolInput(
        tool_name="get_current_time",
        parameters={}
    )
    result = await tool_service.execute_tool(time_input)
    print(f"      Result: {result.result}")
    
    # Example 3: Weather (will fail due to missing location, showing validation)
    print("\n   c) Weather tool validation:")
    weather_input = ToolInput(
        tool_name="get_weather",
        parameters={}  # Missing required location parameter
    )
    result = await tool_service.execute_tool(weather_input)
    print(f"      Success: {result.success}")
    print(f"      Error: {result.error}")
    
    # Example 4: Weather with valid parameters
    print("\n   d) Getting weather for London:")
    weather_input = ToolInput(
        tool_name="get_weather",
        parameters={"location": "London", "temperature_unit": "C"}
    )
    result = await tool_service.execute_tool(weather_input)
    print(f"      Success: {result.success}")
    if result.success:
        print(f"      Result: {result.result}")
    else:
        print(f"      Error: {result.error}")
    
    # Example 5: Book database query
    print("\n   e) Querying book database:")
    book_input = ToolInput(
        tool_name="query_book_database",
        parameters={"book_title": "Dune"}
    )
    result = await tool_service.execute_tool(book_input)
    if result.success:
        book_data = json.loads(result.result)
        print(f"      Found: {book_data.get('title')} by {book_data.get('author')}")
        print(f"      Genre: {book_data.get('genre')}")
        print(f"      Year: {book_data.get('publishedYear')}")
    
    # Example 6: Tool aliases
    print("\n   f) Using tool aliases:")
    alias_input = ToolInput(
        tool_name="date",  # Using alias instead of full name
        parameters={}
    )
    result = await tool_service.execute_tool(alias_input)
    print(f"      Using 'date' alias: {result.result}")
    
    # Show tool schemas
    print("\n5. Tool schema example (weather tool):")
    schema = tool_service.get_tool_schema("get_weather")
    print(f"   Required parameters: {schema['required']}")
    print(f"   Parameters:")
    for param_name, param_def in schema['properties'].items():
        print(f"     - {param_name}: {param_def['description']}")
    
    # Show service statistics
    print("\n6. Service statistics:")
    stats = tool_service.get_service_stats()
    service_metrics = stats['service_metrics']
    registry_stats = stats['registry_stats']
    
    print(f"   Total tools: {registry_stats['total_tools']}")
    print(f"   Total executions: {service_metrics['executions_total']}")
    print(f"   Successful executions: {service_metrics['executions_successful']}")
    print(f"   Failed executions: {service_metrics['executions_failed']}")
    print(f"   Cached executions: {service_metrics['executions_cached']}")
    print(f"   Average execution time: {service_metrics['average_execution_time']:.3f}s")
    
    # Health check
    print("\n7. Health check:")
    health = await tool_service.health_check()
    print(f"   Overall status: {health['status']}")
    for component, status in health['components'].items():
        print(f"   {component}: {status['status']}")
    
    # Search functionality
    print("\n8. Tool search:")
    search_results = tool_service.search_tools("time")
    print(f"   Search for 'time': {search_results}")
    
    search_results = tool_service.search_tools("weather")
    print(f"   Search for 'weather': {search_results}")
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


async def demo_caching():
    """Demonstrate caching functionality."""
    print("\n" + "=" * 40)
    print("Caching Demo")
    print("=" * 40)
    
    tool_service = await initialize_tool_service()
    tool_service.register_tool(DateTool(), ["date"])
    
    # Execute same tool twice to show caching
    print("\n1. First execution (no cache):")
    start_time = datetime.now()
    
    tool_input = ToolInput(
        tool_name="get_current_date",
        parameters={}
    )
    
    result1 = await tool_service.execute_tool(tool_input)
    end_time = datetime.now()
    
    print(f"   Result: {result1.result}")
    print(f"   Execution time: {result1.execution_time:.3f}s")
    print(f"   Cached: {result1.metadata.get('cached', False)}")
    
    print("\n2. Second execution (should be cached):")
    result2 = await tool_service.execute_tool(tool_input)
    
    print(f"   Result: {result2.result}")
    print(f"   Execution time: {result2.execution_time:.3f}s")
    print(f"   Cached: {result2.metadata.get('cached', False)}")
    
    print(f"\n3. Cache statistics:")
    stats = tool_service.get_service_stats()
    print(f"   Cache size: {stats['cache_size']}")
    print(f"   Cached executions: {stats['service_metrics']['executions_cached']}")


async def main():
    """Main demo function."""
    try:
        await demo_tool_service()
        await demo_caching()
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())