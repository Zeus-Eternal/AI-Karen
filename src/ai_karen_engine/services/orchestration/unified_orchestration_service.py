"""
Unified Orchestration Service

This module provides a unified facade for all orchestration, conversation, tools, and plugins
operations in KAREN AI system. It consolidates functionality from multiple orchestration-related
services into a single, consistent interface.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from enum import Enum

from ..base_service import BaseService

logger = logging.getLogger(__name__)


class OrchestrationType(Enum):
    """Enumeration of orchestration types."""
    TASK_ROUTING = "task_routing"
    REASONING = "reasoning"
    CONVERSATION = "conversation"
    TOOLS = "tools"
    PLUGINS = "plugins"
    WORKFLOW = "workflow"
    AGENT = "agent"


class OrchestrationOperation(Enum):
    """Enumeration of orchestration operations."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    ROUTE = "route"
    REASON = "reason"
    CONVERSE = "converse"
    INVOKE = "invoke"
    LOAD = "load"
    UNLOAD = "unload"
    LIST = "list"
    SEARCH = "search"
    VALIDATE = "validate"
    MONITOR = "monitor"
    ANALYZE = "analyze"
    OPTIMIZE = "optimize"


class UnifiedOrchestrationService(BaseService):
    """
    Unified facade for all orchestration, conversation, tools, and plugins operations
    in KAREN AI system.
    
    This service provides a single point of access to all orchestration-related functionality,
    delegating to specialized helper services as needed.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the unified orchestration service.
        
        Args:
            config: Configuration dictionary for the orchestration service
        """
        super().__init__(config)
        self.config = config
        self.orchestration_enabled = config.get("orchestration_enabled", True)
        self.services_initialized = False
        
        # Initialize helper services
        self.task_routing_service = None
        self.reasoning_service = None
        self.conversation_service = None
        self.tools_service = None
        self.plugins_service = None
        self.workflow_service = None
        self.agent_service = None
        
    async def _initialize_service(self) -> None:
        """Initialize the orchestration service and its helpers."""
        try:
            logger.info("Initializing unified orchestration service")
            
            # Initialize helper services
            await self._initialize_helper_services()
            
            self.services_initialized = True
            logger.info("Unified orchestration service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing unified orchestration service: {str(e)}")
            raise
    
    async def _initialize_helper_services(self) -> None:
        """Initialize all helper services."""
        # Import helper services
        from .internal.task_routing_service import TaskRoutingServiceHelper
        from .internal.reasoning_service import ReasoningServiceHelper
        from .internal.conversation_service import ConversationServiceHelper
        from .internal.tools_service import ToolsServiceHelper
        from .internal.plugins_service import PluginsServiceHelper
        from .internal.workflow_service import WorkflowServiceHelper
        from .internal.agent_service import AgentServiceHelper
        
        # Initialize helper services
        self.task_routing_service = TaskRoutingServiceHelper(self.config.get("task_routing", {}))
        self.reasoning_service = ReasoningServiceHelper(self.config.get("reasoning", {}))
        self.conversation_service = ConversationServiceHelper(self.config.get("conversation", {}))
        self.tools_service = ToolsServiceHelper(self.config.get("tools", {}))
        self.plugins_service = PluginsServiceHelper(self.config.get("plugins", {}))
        self.workflow_service = WorkflowServiceHelper(self.config.get("workflow", {}))
        self.agent_service = AgentServiceHelper(self.config.get("agent", {}))
        
        # Initialize all helper services
        await self.task_routing_service.initialize()
        await self.reasoning_service.initialize()
        await self.conversation_service.initialize()
        await self.tools_service.initialize()
        await self.plugins_service.initialize()
        await self.workflow_service.initialize()
        await self.agent_service.initialize()
    
    async def _start_service(self) -> None:
        """Start the orchestration service and its helpers."""
        try:
            logger.info("Starting unified orchestration service")
            
            # Start helper services
            await self.task_routing_service.start()
            await self.reasoning_service.start()
            await self.conversation_service.start()
            await self.tools_service.start()
            await self.plugins_service.start()
            await self.workflow_service.start()
            await self.agent_service.start()
            
            logger.info("Unified orchestration service started successfully")
            
        except Exception as e:
            logger.error(f"Error starting unified orchestration service: {str(e)}")
            raise
    
    async def _stop_service(self) -> None:
        """Stop the orchestration service and its helpers."""
        try:
            logger.info("Stopping unified orchestration service")
            
            # Stop helper services
            if self.task_routing_service:
                await self.task_routing_service.stop()
            if self.reasoning_service:
                await self.reasoning_service.stop()
            if self.conversation_service:
                await self.conversation_service.stop()
            if self.tools_service:
                await self.tools_service.stop()
            if self.plugins_service:
                await self.plugins_service.stop()
            if self.workflow_service:
                await self.workflow_service.stop()
            if self.agent_service:
                await self.agent_service.stop()
                
            self.services_initialized = False
            logger.info("Unified orchestration service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping unified orchestration service: {str(e)}")
            raise
    
    async def _health_check_service(self) -> Dict[str, Any]:
        """Check the health of the orchestration service and its helpers."""
        try:
            health_status = {
                "status": "healthy",
                "message": "Orchestration service is healthy",
                "services": {}
            }
            
            # Check helper services
            if self.task_routing_service:
                health_status["services"]["task_routing"] = await self.task_routing_service.health_check()
            if self.reasoning_service:
                health_status["services"]["reasoning"] = await self.reasoning_service.health_check()
            if self.conversation_service:
                health_status["services"]["conversation"] = await self.conversation_service.health_check()
            if self.tools_service:
                health_status["services"]["tools"] = await self.tools_service.health_check()
            if self.plugins_service:
                health_status["services"]["plugins"] = await self.plugins_service.health_check()
            if self.workflow_service:
                health_status["services"]["workflow"] = await self.workflow_service.health_check()
            if self.agent_service:
                health_status["services"]["agent"] = await self.agent_service.health_check()
                
            # Determine overall health status
            for service_name, service_health in health_status["services"].items():
                if service_health.get("status") != "healthy":
                    health_status["status"] = "degraded"
                    health_status["message"] = f"Service {service_name} is not healthy"
                    
            return health_status
            
        except Exception as e:
            logger.error(f"Error checking orchestration service health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    async def execute_orchestration_operation(self, orchestration_type: OrchestrationType, operation: OrchestrationOperation, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an orchestration operation.
        
        Args:
            orchestration_type: The type of orchestration
            operation: The operation to execute
            data: Data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self.services_initialized:
                return {"status": "error", "message": "Orchestration service is not initialized"}
                
            # Check if orchestration is enabled
            if not self.orchestration_enabled:
                return {"status": "error", "message": "Orchestration is disabled"}
                
            # Delegate to the appropriate helper service
            if orchestration_type == OrchestrationType.TASK_ROUTING:
                return await self._execute_task_routing_operation(operation, data, context)
            elif orchestration_type == OrchestrationType.REASONING:
                return await self._execute_reasoning_operation(operation, data, context)
            elif orchestration_type == OrchestrationType.CONVERSATION:
                return await self._execute_conversation_operation(operation, data, context)
            elif orchestration_type == OrchestrationType.TOOLS:
                return await self._execute_tools_operation(operation, data, context)
            elif orchestration_type == OrchestrationType.PLUGINS:
                return await self._execute_plugins_operation(operation, data, context)
            elif orchestration_type == OrchestrationType.WORKFLOW:
                return await self._execute_workflow_operation(operation, data, context)
            elif orchestration_type == OrchestrationType.AGENT:
                return await self._execute_agent_operation(operation, data, context)
            else:
                return {"status": "error", "message": f"Unsupported orchestration type: {orchestration_type}"}
                
        except Exception as e:
            logger.error(f"Error executing orchestration operation: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _execute_task_routing_operation(self, operation: OrchestrationOperation, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a task routing operation."""
        if not self.task_routing_service:
            return {"status": "error", "message": "Task routing service is not available"}
            
        # Map orchestration operation to task routing operation
        if operation == OrchestrationOperation.ROUTE:
            return await self.task_routing_service.route_task(data, context)
        elif operation == OrchestrationOperation.EXECUTE:
            return await self.task_routing_service.execute_task(data, context)
        elif operation == OrchestrationOperation.MONITOR:
            return await self.task_routing_service.monitor_tasks(data, context)
        elif operation == OrchestrationOperation.LIST:
            return await self.task_routing_service.list_tasks(data, context)
        elif operation == OrchestrationOperation.SEARCH:
            return await self.task_routing_service.search_tasks(data, context)
        elif operation == OrchestrationOperation.ANALYZE:
            return await self.task_routing_service.analyze_tasks(data, context)
        else:
            return {"status": "error", "message": f"Unsupported task routing operation: {operation}"}
    
    async def _execute_reasoning_operation(self, operation: OrchestrationOperation, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a reasoning operation."""
        if not self.reasoning_service:
            return {"status": "error", "message": "Reasoning service is not available"}
            
        # Map orchestration operation to reasoning operation
        if operation == OrchestrationOperation.REASON:
            return await self.reasoning_service.reason(data, context)
        elif operation == OrchestrationOperation.EXECUTE:
            return await self.reasoning_service.execute_reasoning(data, context)
        elif operation == OrchestrationOperation.ANALYZE:
            return await self.reasoning_service.analyze_reasoning(data, context)
        elif operation == OrchestrationOperation.VALIDATE:
            return await self.reasoning_service.validate_reasoning(data, context)
        elif operation == OrchestrationOperation.OPTIMIZE:
            return await self.reasoning_service.optimize_reasoning(data, context)
        else:
            return {"status": "error", "message": f"Unsupported reasoning operation: {operation}"}
    
    async def _execute_conversation_operation(self, operation: OrchestrationOperation, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a conversation operation."""
        if not self.conversation_service:
            return {"status": "error", "message": "Conversation service is not available"}
            
        # Map orchestration operation to conversation operation
        if operation == OrchestrationOperation.CREATE:
            return await self.conversation_service.create_conversation(data, context)
        elif operation == OrchestrationOperation.READ:
            return await self.conversation_service.get_conversation(data, context)
        elif operation == OrchestrationOperation.UPDATE:
            return await self.conversation_service.update_conversation(data, context)
        elif operation == OrchestrationOperation.DELETE:
            return await self.conversation_service.delete_conversation(data, context)
        elif operation == OrchestrationOperation.CONVERSE:
            return await self.conversation_service.converse(data, context)
        elif operation == OrchestrationOperation.LIST:
            return await self.conversation_service.list_conversations(data, context)
        elif operation == OrchestrationOperation.SEARCH:
            return await self.conversation_service.search_conversations(data, context)
        elif operation == OrchestrationOperation.ANALYZE:
            return await self.conversation_service.analyze_conversation(data, context)
        else:
            return {"status": "error", "message": f"Unsupported conversation operation: {operation}"}
    
    async def _execute_tools_operation(self, operation: OrchestrationOperation, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a tools operation."""
        if not self.tools_service:
            return {"status": "error", "message": "Tools service is not available"}
            
        # Map orchestration operation to tools operation
        if operation == OrchestrationOperation.CREATE:
            return await self.tools_service.create_tool(data, context)
        elif operation == OrchestrationOperation.READ:
            return await self.tools_service.get_tool(data, context)
        elif operation == OrchestrationOperation.UPDATE:
            return await self.tools_service.update_tool(data, context)
        elif operation == OrchestrationOperation.DELETE:
            return await self.tools_service.delete_tool(data, context)
        elif operation == OrchestrationOperation.INVOKE:
            return await self.tools_service.invoke_tool(data, context)
        elif operation == OrchestrationOperation.LIST:
            return await self.tools_service.list_tools(data, context)
        elif operation == OrchestrationOperation.SEARCH:
            return await self.tools_service.search_tools(data, context)
        elif operation == OrchestrationOperation.VALIDATE:
            return await self.tools_service.validate_tool(data, context)
        else:
            return {"status": "error", "message": f"Unsupported tools operation: {operation}"}
    
    async def _execute_plugins_operation(self, operation: OrchestrationOperation, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a plugins operation."""
        if not self.plugins_service:
            return {"status": "error", "message": "Plugins service is not available"}
            
        # Map orchestration operation to plugins operation
        if operation == OrchestrationOperation.CREATE:
            return await self.plugins_service.create_plugin(data, context)
        elif operation == OrchestrationOperation.READ:
            return await self.plugins_service.get_plugin(data, context)
        elif operation == OrchestrationOperation.UPDATE:
            return await self.plugins_service.update_plugin(data, context)
        elif operation == OrchestrationOperation.DELETE:
            return await self.plugins_service.delete_plugin(data, context)
        elif operation == OrchestrationOperation.LOAD:
            return await self.plugins_service.load_plugin(data, context)
        elif operation == OrchestrationOperation.UNLOAD:
            return await self.plugins_service.unload_plugin(data, context)
        elif operation == OrchestrationOperation.LIST:
            return await self.plugins_service.list_plugins(data, context)
        elif operation == OrchestrationOperation.SEARCH:
            return await self.plugins_service.search_plugins(data, context)
        elif operation == OrchestrationOperation.VALIDATE:
            return await self.plugins_service.validate_plugin(data, context)
        else:
            return {"status": "error", "message": f"Unsupported plugins operation: {operation}"}
    
    async def _execute_workflow_operation(self, operation: OrchestrationOperation, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a workflow operation."""
        if not self.workflow_service:
            return {"status": "error", "message": "Workflow service is not available"}
            
        # Map orchestration operation to workflow operation
        if operation == OrchestrationOperation.CREATE:
            return await self.workflow_service.create_workflow(data, context)
        elif operation == OrchestrationOperation.READ:
            return await self.workflow_service.get_workflow(data, context)
        elif operation == OrchestrationOperation.UPDATE:
            return await self.workflow_service.update_workflow(data, context)
        elif operation == OrchestrationOperation.DELETE:
            return await self.workflow_service.delete_workflow(data, context)
        elif operation == OrchestrationOperation.EXECUTE:
            return await self.workflow_service.execute_workflow(data, context)
        elif operation == OrchestrationOperation.LIST:
            return await self.workflow_service.list_workflows(data, context)
        elif operation == OrchestrationOperation.SEARCH:
            return await self.workflow_service.search_workflows(data, context)
        elif operation == OrchestrationOperation.VALIDATE:
            return await self.workflow_service.validate_workflow(data, context)
        elif operation == OrchestrationOperation.MONITOR:
            return await self.workflow_service.monitor_workflow(data, context)
        else:
            return {"status": "error", "message": f"Unsupported workflow operation: {operation}"}
    
    async def _execute_agent_operation(self, operation: OrchestrationOperation, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute an agent operation."""
        if not self.agent_service:
            return {"status": "error", "message": "Agent service is not available"}
            
        # Map orchestration operation to agent operation
        if operation == OrchestrationOperation.CREATE:
            return await self.agent_service.create_agent(data, context)
        elif operation == OrchestrationOperation.READ:
            return await self.agent_service.get_agent(data, context)
        elif operation == OrchestrationOperation.UPDATE:
            return await self.agent_service.update_agent(data, context)
        elif operation == OrchestrationOperation.DELETE:
            return await self.agent_service.delete_agent(data, context)
        elif operation == OrchestrationOperation.EXECUTE:
            return await self.agent_service.execute_agent(data, context)
        elif operation == OrchestrationOperation.LIST:
            return await self.agent_service.list_agents(data, context)
        elif operation == OrchestrationOperation.SEARCH:
            return await self.agent_service.search_agents(data, context)
        elif operation == OrchestrationOperation.VALIDATE:
            return await self.agent_service.validate_agent(data, context)
        elif operation == OrchestrationOperation.MONITOR:
            return await self.agent_service.monitor_agent(data, context)
        else:
            return {"status": "error", "message": f"Unsupported agent operation: {operation}"}
    
    async def get_orchestration_status(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the status of all orchestration services.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the status of all orchestration services
        """
        try:
            if not self.services_initialized:
                return {"status": "error", "message": "Orchestration service is not initialized"}
                
            status = {
                "orchestration_enabled": self.orchestration_enabled,
                "services": {}
            }
            
            # Get status of helper services
            if self.task_routing_service:
                status["services"]["task_routing"] = await self.task_routing_service.get_status(data, context)
            if self.reasoning_service:
                status["services"]["reasoning"] = await self.reasoning_service.get_status(data, context)
            if self.conversation_service:
                status["services"]["conversation"] = await self.conversation_service.get_status(data, context)
            if self.tools_service:
                status["services"]["tools"] = await self.tools_service.get_status(data, context)
            if self.plugins_service:
                status["services"]["plugins"] = await self.plugins_service.get_status(data, context)
            if self.workflow_service:
                status["services"]["workflow"] = await self.workflow_service.get_status(data, context)
            if self.agent_service:
                status["services"]["agent"] = await self.agent_service.get_status(data, context)
                
            return {
                "status": "success",
                "message": "Orchestration status retrieved successfully",
                "orchestration_status": status
            }
            
        except Exception as e:
            logger.error(f"Error getting orchestration status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_orchestration_stats(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get statistics for all orchestration services.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing statistics for all orchestration services
        """
        try:
            if not self.services_initialized:
                return {"status": "error", "message": "Orchestration service is not initialized"}
                
            stats = {
                "orchestration_enabled": self.orchestration_enabled,
                "services": {}
            }
            
            # Get stats of helper services
            if self.task_routing_service:
                stats["services"]["task_routing"] = await self.task_routing_service.get_stats(data, context)
            if self.reasoning_service:
                stats["services"]["reasoning"] = await self.reasoning_service.get_stats(data, context)
            if self.conversation_service:
                stats["services"]["conversation"] = await self.conversation_service.get_stats(data, context)
            if self.tools_service:
                stats["services"]["tools"] = await self.tools_service.get_stats(data, context)
            if self.plugins_service:
                stats["services"]["plugins"] = await self.plugins_service.get_stats(data, context)
            if self.workflow_service:
                stats["services"]["workflow"] = await self.workflow_service.get_stats(data, context)
            if self.agent_service:
                stats["services"]["agent"] = await self.agent_service.get_stats(data, context)
                
            return {
                "status": "success",
                "message": "Orchestration statistics retrieved successfully",
                "orchestration_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting orchestration statistics: {str(e)}")
            return {"status": "error", "message": str(e)}