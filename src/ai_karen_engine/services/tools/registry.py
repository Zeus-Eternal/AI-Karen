"""
Tool registry utilities for automatic tool registration and management.
"""

import logging
from typing import List, Optional

from ai_karen_engine.services.tool_service import ToolService, ToolRegistry, get_tool_service
from ai_karen_engine.services.tools.core_tools import (
    DateTool,
    TimeTool,
    WeatherTool,
    BookDatabaseTool,
    GmailUnreadTool,
    GmailComposeTool,
    KarenPluginTool,
    KarenMemoryQueryTool,
    KarenMemoryStoreTool,
    KarenSystemStatusTool,
    KarenAnalyticsTool
)

logger = logging.getLogger(__name__)


def register_core_tools(tool_service: Optional[ToolService] = None) -> bool:
    """
    Register all core tools with the tool service.
    
    Args:
        tool_service: Tool service instance (uses global if None)
        
    Returns:
        True if all tools registered successfully, False otherwise
    """
    if tool_service is None:
        tool_service = get_tool_service()
    
    # Define core tools with their aliases
    core_tools = [
        (DateTool(), ["current_date", "date", "today"]),
        (TimeTool(), ["current_time", "time", "clock"]),
        (WeatherTool(), ["weather", "forecast"]),
        (BookDatabaseTool(), ["book_lookup", "book_search"]),
        (GmailUnreadTool(), ["gmail_unread", "check_email"]),
        (GmailComposeTool(), ["gmail_compose", "send_email"]),
        (KarenPluginTool(), ["plugin", "execute_plugin"]),
        (KarenMemoryQueryTool(), ["memory_query", "search_memory", "recall"]),
        (KarenMemoryStoreTool(), ["memory_store", "remember", "save_memory"]),
        (KarenSystemStatusTool(), ["system_status", "health_check"]),
        (KarenAnalyticsTool(), ["analytics", "stats", "usage"])
    ]
    
    success_count = 0
    total_count = len(core_tools)
    
    for tool, aliases in core_tools:
        try:
            if tool_service.register_tool(tool, aliases):
                success_count += 1
                logger.info(f"Registered tool: {tool.metadata.name}")
            else:
                logger.error(f"Failed to register tool: {tool.metadata.name}")
        except Exception as e:
            logger.error(f"Error registering tool {tool.metadata.name}: {e}")
    
    logger.info(f"Registered {success_count}/{total_count} core tools")
    return success_count == total_count


def get_core_tool_names() -> List[str]:
    """Get list of core tool names."""
    return [
        "get_current_date",
        "get_current_time", 
        "get_weather",
        "query_book_database",
        "check_gmail_unread",
        "compose_gmail",
        "execute_karen_plugin",
        "query_karen_memory",
        "store_karen_memory",
        "get_karen_system_status",
        "get_karen_analytics"
    ]


def unregister_core_tools(tool_service: Optional[ToolService] = None) -> bool:
    """
    Unregister all core tools from the tool service.
    
    Args:
        tool_service: Tool service instance (uses global if None)
        
    Returns:
        True if all tools unregistered successfully, False otherwise
    """
    if tool_service is None:
        tool_service = get_tool_service()
    
    tool_names = get_core_tool_names()
    success_count = 0
    
    for tool_name in tool_names:
        try:
            if tool_service.unregister_tool(tool_name):
                success_count += 1
                logger.info(f"Unregistered tool: {tool_name}")
            else:
                logger.warning(f"Tool not found for unregistration: {tool_name}")
        except Exception as e:
            logger.error(f"Error unregistering tool {tool_name}: {e}")
    
    logger.info(f"Unregistered {success_count}/{len(tool_names)} core tools")
    return success_count == len(tool_names)


async def initialize_core_tools() -> ToolService:
    """
    Initialize tool service and register all core tools.
    
    Returns:
        Initialized tool service with core tools registered
    """
    from ai_karen_engine.services.tool_service import initialize_tool_service
    
    # Initialize tool service
    tool_service = await initialize_tool_service()
    
    # Register core tools
    register_core_tools(tool_service)
    
    logger.info("Core tools initialization completed")
    return tool_service
