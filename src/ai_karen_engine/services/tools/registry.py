"""
Enhanced tool registry utilities for copilot integration.

This module extends the existing tool registry with copilot-specific features:
- Capability-based tool organization
- Security policy enforcement
- Citation requirement validation
- RBAC and privacy level management
"""

import asyncio
import logging
from collections import defaultdict
from typing import List, Optional, Dict, Any, Set, Callable
from datetime import datetime

from ai_karen_engine.services.tool_service import (
    ToolService,
    ToolRegistry,
    get_tool_service,
    BaseTool,
    ToolCategory,
    ToolStatus
)
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
from ai_karen_engine.services.tools.contracts import (
    CopilotTool,
    ToolSpec,
    ToolScope,
    RBACLevel,
    PrivacyLevel,
    ToolContext,
    ToolResult,
    Citation,
    PolicyViolationError,
    InsufficientCitationsError
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


class CopilotToolRegistry(ToolRegistry):
    """
    Enhanced tool registry for copilot integration with capability-based organization,
    security policy enforcement, and citation management.
    """
    
    def __init__(self):
        """Initialize copilot tool registry."""
        super().__init__()
        
        # Copilot-specific indices
        self.tools_by_scope: Dict[ToolScope, List[str]] = defaultdict(list)
        self.tools_by_rbac: Dict[RBACLevel, List[str]] = defaultdict(list)
        self.tools_by_privacy: Dict[PrivacyLevel, List[str]] = defaultdict(list)
        self.capability_tools: Dict[str, List[str]] = defaultdict(list)
        
        # Policy enforcement
        self.global_policies: List[Callable[[ToolContext], bool]] = []
        self.scope_policies: Dict[ToolScope, List[Callable]] = defaultdict(list)
        
        # Citation requirements
        self.citation_validators: Dict[str, Callable[[List[Citation]], bool]] = {}
        
        # Security constraints
        self.path_allowlists: Dict[str, List[str]] = {}
        self.path_blocklists: Dict[str, List[str]] = {}
        
        # Metrics
        self.copilot_metrics = {
            "copilot_tools_registered": 0,
            "policy_violations": 0,
            "citation_failures": 0,
            "dry_run_executions": 0,
            "rollback_operations": 0
        }
    
    def register_copilot_tool(
        self, 
        tool: CopilotTool, 
        capabilities: Optional[List[str]] = None,
        aliases: Optional[List[str]] = None
    ) -> bool:
        """
        Register a copilot tool with enhanced indexing.
        
        Args:
            tool: Copilot tool instance
            capabilities: List of capabilities this tool provides
            aliases: Optional aliases for the tool
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Register with base registry
            if not super().register_tool(tool, aliases):
                return False
            
            spec = tool.tool_spec
            tool_name = spec.name
            
            # Update copilot-specific indices
            self.tools_by_scope[spec.scope].append(tool_name)
            self.tools_by_rbac[spec.rbac_level].append(tool_name)
            self.tools_by_privacy[spec.privacy_level].append(tool_name)
            
            # Register capabilities
            if capabilities:
                for capability in capabilities:
                    self.capability_tools[capability].append(tool_name)
            
            # Register required capabilities
            for capability in spec.required_capabilities:
                self.capability_tools[capability].append(tool_name)
            
            # Update metrics
            self.copilot_metrics["copilot_tools_registered"] += 1
            
            logger.info(
                f"Copilot tool {tool_name} registered: "
                f"scope={spec.scope.value}, rbac={spec.rbac_level.value}, "
                f"privacy={spec.privacy_level.value}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to register copilot tool: {e}")
            return False
    
    def unregister_copilot_tool(self, tool_name: str) -> bool:
        """
        Unregister a copilot tool and clean up indices.
        
        Args:
            tool_name: Name of the tool to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            # Get tool before unregistering
            tool = self.get_tool(tool_name)
            if not isinstance(tool, CopilotTool):
                return super().unregister_tool(tool_name)
            
            spec = tool.tool_spec
            
            # Clean up copilot-specific indices
            if tool_name in self.tools_by_scope[spec.scope]:
                self.tools_by_scope[spec.scope].remove(tool_name)
            
            if tool_name in self.tools_by_rbac[spec.rbac_level]:
                self.tools_by_rbac[spec.rbac_level].remove(tool_name)
            
            if tool_name in self.tools_by_privacy[spec.privacy_level]:
                self.tools_by_privacy[spec.privacy_level].remove(tool_name)
            
            # Clean up capability mappings
            for capability, tools in self.capability_tools.items():
                if tool_name in tools:
                    tools.remove(tool_name)
            
            # Clean up empty capability entries
            empty_capabilities = [
                cap for cap, tools in self.capability_tools.items() 
                if not tools
            ]
            for cap in empty_capabilities:
                del self.capability_tools[cap]
            
            # Unregister from base registry
            return super().unregister_tool(tool_name)
            
        except Exception as e:
            logger.error(f"Failed to unregister copilot tool {tool_name}: {e}")
            return False
    
    def find_tools_by_scope(
        self, 
        scope: ToolScope, 
        rbac_level: Optional[RBACLevel] = None,
        privacy_level: Optional[PrivacyLevel] = None
    ) -> List[str]:
        """
        Find tools by scope with optional RBAC and privacy filtering.
        
        Args:
            scope: Tool scope to filter by
            rbac_level: Optional RBAC level filter
            privacy_level: Optional privacy level filter
            
        Returns:
            List of matching tool names
        """
        tools = self.tools_by_scope.get(scope, [])
        
        if rbac_level:
            rbac_tools = set(self.tools_by_rbac.get(rbac_level, []))
            tools = [t for t in tools if t in rbac_tools]
        
        if privacy_level:
            privacy_tools = set(self.tools_by_privacy.get(privacy_level, []))
            tools = [t for t in tools if t in privacy_tools]
        
        return sorted(tools)
    
    def find_tools_by_capability(self, capability: str) -> List[str]:
        """
        Find tools that provide a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of tool names that provide the capability
        """
        return sorted(self.capability_tools.get(capability, []))
    
    def get_available_capabilities(self) -> List[str]:
        """Get list of all available capabilities."""
        return sorted(self.capability_tools.keys())
    
    def validate_tool_access(
        self, 
        tool_name: str, 
        context: ToolContext
    ) -> bool:
        """
        Validate if tool can be accessed with given context.
        
        Args:
            tool_name: Name of the tool
            context: Execution context
            
        Returns:
            True if access is allowed, False otherwise
        """
        tool = self.get_tool(tool_name)
        if not isinstance(tool, CopilotTool):
            return True  # Legacy tools have no restrictions
        
        spec = tool.tool_spec
        
        # Check RBAC permissions
        if not context.has_permission(spec.rbac_level):
            logger.warning(
                f"RBAC check failed for {tool_name}: "
                f"required={spec.rbac_level.value}, "
                f"available={[p.value for p in context.rbac_permissions]}"
            )
            return False
        
        # Check privacy level
        if not context.meets_privacy_level(spec.privacy_level):
            logger.warning(
                f"Privacy check failed for {tool_name}: "
                f"required={spec.privacy_level.value}, "
                f"available={context.privacy_clearance.value}"
            )
            return False
        
        # Apply global policies
        for policy in self.global_policies:
            if not policy(context):
                logger.warning(f"Global policy check failed for {tool_name}")
                self.copilot_metrics["policy_violations"] += 1
                return False
        
        # Apply scope-specific policies
        scope_policies = self.scope_policies.get(spec.scope, [])
        for policy in scope_policies:
            if not policy(context):
                logger.warning(f"Scope policy check failed for {tool_name}")
                self.copilot_metrics["policy_violations"] += 1
                return False
        
        return True
    
    def validate_citations(
        self, 
        tool_name: str, 
        citations: List[Citation]
    ) -> bool:
        """
        Validate citations for tool execution.
        
        Args:
            tool_name: Name of the tool
            citations: List of citations to validate
            
        Returns:
            True if citations are valid, False otherwise
        """
        tool = self.get_tool(tool_name)
        if not isinstance(tool, CopilotTool):
            return True  # Legacy tools don't require citations
        
        # Use tool's built-in validation
        try:
            tool._validate_citations(citations)
            return True
        except InsufficientCitationsError as e:
            logger.warning(f"Citation validation failed for {tool_name}: {e}")
            self.copilot_metrics["citation_failures"] += 1
            return False
    
    def add_global_policy(self, policy: Callable[[ToolContext], bool]):
        """Add a global policy that applies to all tools."""
        self.global_policies.append(policy)
    
    def add_scope_policy(
        self, 
        scope: ToolScope, 
        policy: Callable[[ToolContext], bool]
    ):
        """Add a policy that applies to tools with specific scope."""
        self.scope_policies[scope].append(policy)
    
    def set_path_allowlist(self, tool_name: str, paths: List[str]):
        """Set path allowlist for a specific tool."""
        self.path_allowlists[tool_name] = paths
    
    def set_path_blocklist(self, tool_name: str, paths: List[str]):
        """Set path blocklist for a specific tool."""
        self.path_blocklists[tool_name] = paths
    
    def get_copilot_stats(self) -> Dict[str, Any]:
        """Get copilot-specific registry statistics."""
        stats = super().get_registry_stats()
        
        # Add copilot-specific stats
        stats["copilot_metrics"] = self.copilot_metrics.copy()
        stats["by_scope"] = {
            scope.value: len(tools) 
            for scope, tools in self.tools_by_scope.items()
        }
        stats["by_rbac"] = {
            level.value: len(tools) 
            for level, tools in self.tools_by_rbac.items()
        }
        stats["by_privacy"] = {
            level.value: len(tools) 
            for level, tools in self.tools_by_privacy.items()
        }
        stats["capabilities"] = {
            capability: len(tools) 
            for capability, tools in self.capability_tools.items()
        }
        stats["policies"] = {
            "global_policies": len(self.global_policies),
            "scope_policies": sum(len(policies) for policies in self.scope_policies.values())
        }
        
        return stats


class CopilotToolService(ToolService):
    """
    Enhanced tool service for copilot integration with policy enforcement,
    citation validation, and enhanced execution modes.
    """
    
    def __init__(self, registry: Optional[CopilotToolRegistry] = None):
        """Initialize copilot tool service."""
        super().__init__(registry or CopilotToolRegistry())
        
        # Copilot-specific settings
        self.enforce_citations = True
        self.default_execution_mode = "dry_run"
        self.enable_rollback_tracking = True
        
        # Execution tracking
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.rollback_data: Dict[str, Dict[str, Any]] = {}
        
        # Enhanced metrics
        self.copilot_metrics = {
            "copilot_executions": 0,
            "dry_run_executions": 0,
            "policy_violations": 0,
            "citation_failures": 0,
            "rollbacks_performed": 0
        }
    
    async def execute_copilot_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        context: ToolContext
    ) -> ToolResult:
        """
        Execute a copilot tool with enhanced validation and security.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            context: Enhanced execution context
            
        Returns:
            Enhanced tool result
        """
        start_time = datetime.utcnow()
        
        try:
            # Get tool
            tool = self.registry.get_tool(tool_name)
            if not tool:
                return ToolResult(
                    success=False,
                    execution_mode=context.execution_mode,
                    error=f"Tool '{tool_name}' not found",
                    correlation_id=context.correlation_id
                )
            
            # Validate access
            if not self.registry.validate_tool_access(tool_name, context):
                self.copilot_metrics["policy_violations"] += 1
                return ToolResult(
                    success=False,
                    execution_mode=context.execution_mode,
                    error=f"Access denied for tool '{tool_name}'",
                    error_code="ACCESS_DENIED",
                    correlation_id=context.correlation_id
                )
            
            # Validate citations for copilot tools
            if isinstance(tool, CopilotTool):
                if not self.registry.validate_citations(tool_name, context.citations):
                    self.copilot_metrics["citation_failures"] += 1
                    return ToolResult(
                        success=False,
                        execution_mode=context.execution_mode,
                        error=f"Insufficient citations for tool '{tool_name}'",
                        error_code="INSUFFICIENT_CITATIONS",
                        correlation_id=context.correlation_id
                    )
                
                # Execute copilot tool
                result = await tool.execute_copilot(parameters, context)
            else:
                # Execute legacy tool (convert to ToolResult)
                from ai_karen_engine.services.tool_service import ToolInput
                tool_input = ToolInput(
                    tool_name=tool_name,
                    parameters=parameters,
                    user_context=context.metadata,
                    user_id=context.user_id,
                    session_id=context.session_id,
                    request_id=context.correlation_id
                )
                
                legacy_result = await tool.execute(tool_input)
                result = ToolResult(
                    success=legacy_result.success,
                    execution_mode=context.execution_mode,
                    result=legacy_result.result,
                    execution_time=legacy_result.execution_time,
                    error=legacy_result.error,
                    correlation_id=context.correlation_id
                )
            
            # Track execution
            self.copilot_metrics["copilot_executions"] += 1
            if context.execution_mode.value == "dry_run":
                self.copilot_metrics["dry_run_executions"] += 1
            
            # Store rollback data if applicable
            if result.can_rollback and result.rollback_data:
                self.rollback_data[context.correlation_id] = result.rollback_data
            
            return result
            
        except Exception as e:
            logger.error(f"Copilot tool service execution error: {e}")
            return ToolResult(
                success=False,
                execution_mode=context.execution_mode,
                error=f"Tool service error: {str(e)}",
                error_code=type(e).__name__,
                correlation_id=context.correlation_id
            )
    
    async def rollback_operation(self, correlation_id: str) -> bool:
        """
        Rollback a previous operation.
        
        Args:
            correlation_id: Correlation ID of the operation to rollback
            
        Returns:
            True if rollback successful, False otherwise
        """
        if correlation_id not in self.rollback_data:
            logger.error(f"No rollback data found for correlation_id: {correlation_id}")
            return False
        
        try:
            rollback_data = self.rollback_data[correlation_id]
            tool_name = rollback_data.get("tool_name")
            
            if not tool_name:
                logger.error(f"No tool name in rollback data for: {correlation_id}")
                return False
            
            tool = self.registry.get_tool(tool_name)
            if not isinstance(tool, CopilotTool):
                logger.error(f"Tool {tool_name} does not support rollback")
                return False
            
            success = await tool.rollback(correlation_id, rollback_data)
            if success:
                self.copilot_metrics["rollbacks_performed"] += 1
                # Clean up rollback data after successful rollback
                del self.rollback_data[correlation_id]
            
            return success
            
        except Exception as e:
            logger.error(f"Rollback failed for {correlation_id}: {e}")
            return False
    
    def get_copilot_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive copilot service statistics."""
        base_stats = super().get_service_stats()
        
        # Add copilot-specific stats
        base_stats["copilot_metrics"] = self.copilot_metrics.copy()
        base_stats["active_executions"] = len(self.active_executions)
        base_stats["pending_rollbacks"] = len(self.rollback_data)
        
        # Add registry stats if it's a copilot registry
        if isinstance(self.registry, CopilotToolRegistry):
            base_stats["copilot_registry"] = self.registry.get_copilot_stats()
        
        return base_stats


# Global copilot tool service instance
_copilot_tool_service: Optional[CopilotToolService] = None


def get_copilot_tool_service() -> CopilotToolService:
    """Get global copilot tool service instance."""
    global _copilot_tool_service
    if _copilot_tool_service is None:
        _copilot_tool_service = CopilotToolService()
    return _copilot_tool_service


async def initialize_copilot_tools() -> CopilotToolService:
    """
    Initialize copilot tool service with enhanced registry.
    
    Returns:
        Initialized copilot tool service
    """
    global _copilot_tool_service
    
    # Create enhanced registry
    registry = CopilotToolRegistry()
    
    # Initialize service
    _copilot_tool_service = CopilotToolService(registry)
    
    # Register core tools (legacy compatibility)
    register_core_tools(_copilot_tool_service)
    
    logger.info("Copilot tools initialization completed")
    return _copilot_tool_service