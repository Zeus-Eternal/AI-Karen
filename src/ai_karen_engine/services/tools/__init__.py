"""
Enhanced tools package for AI Karen engine with copilot integration.

This package contains implementations of core tools converted from TypeScript,
additional Python-specific tools, and enhanced copilot tools with security
and citation support.
"""

# Core tools (legacy)
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

# Enhanced contracts and specifications
from ai_karen_engine.services.tools.contracts import (
    # Enums
    ToolScope,
    RBACLevel,
    PrivacyLevel,
    ExecutionMode,
    
    # Data classes
    Citation,
    SecurityConstraint,
    ToolSpec,
    ToolContext,
    ToolResult,
    
    # Base classes
    CopilotTool,
    
    # Exceptions
    PolicyViolationError,
    InsufficientCitationsError,
    
    # Utility functions
    create_citation,
    create_file_citation,
    create_db_citation,
    create_tool_context
)

# Copilot tools (MVP set)
from ai_karen_engine.services.tools.copilot_tools import (
    CodeSearchSpansTool,
    CodeApplyDiffTool,
    TestRunSubsetTool,
    GitOpenPRTool,
    SecurityScanSecretsTool,
    COPILOT_TOOLS
)

# Enhanced registry and service
from ai_karen_engine.services.tools.registry import (
    # Legacy functions
    register_core_tools,
    unregister_core_tools,
    get_core_tool_names,
    initialize_core_tools,
    
    # Enhanced classes
    CopilotToolRegistry,
    CopilotToolService,
    
    # Enhanced functions
    get_copilot_tool_service,
    initialize_copilot_tools
)

# Capability system (imported at service level, not tools level)
# These will be imported by services that need capability management

__all__ = [
    # Core tools (legacy)
    "DateTool",
    "TimeTool", 
    "WeatherTool",
    "BookDatabaseTool",
    "GmailUnreadTool",
    "GmailComposeTool",
    "KarenPluginTool",
    "KarenMemoryQueryTool",
    "KarenMemoryStoreTool",
    "KarenSystemStatusTool",
    "KarenAnalyticsTool",
    
    # Copilot tools (MVP set)
    "CodeSearchSpansTool",
    "CodeApplyDiffTool", 
    "TestRunSubsetTool",
    "GitOpenPRTool",
    "SecurityScanSecretsTool",
    "COPILOT_TOOLS",
    
    # Enhanced contracts
    "ToolScope",
    "RBACLevel",
    "PrivacyLevel",
    "ExecutionMode",
    "Citation",
    "SecurityConstraint",
    "ToolSpec",
    "ToolContext",
    "ToolResult",
    "CopilotTool",
    "PolicyViolationError",
    "InsufficientCitationsError",
    "create_citation",
    "create_file_citation",
    "create_db_citation",
    "create_tool_context",
    
    # Enhanced registry and service
    "CopilotToolRegistry",
    "CopilotToolService",
    "get_copilot_tool_service",
    "initialize_copilot_tools",
    
    # Legacy functions
    "register_core_tools",
    "unregister_core_tools",
    "get_core_tool_names",
    "initialize_core_tools"
]