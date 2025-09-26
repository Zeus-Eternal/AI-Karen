import logging
from datetime import datetime
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ai_karen_engine.models.shared_types import FlowInput, FlowOutput, FlowType


class FlowRegistrationError(Exception):
    """Raised when flow registration fails."""
    pass


class FlowExecutionError(Exception):
    """Raised when flow execution fails."""
    pass


class FlowManager:
    """
    Manages AI processing workflows similar to Genkit flows.
    Handles flow registration, discovery, and execution.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ai_orchestrator.flow_manager")
        self._flows: Dict[FlowType, Callable] = {}
        self._flow_metadata: Dict[FlowType, Dict[str, Any]] = {}
        self._execution_stats: Dict[FlowType, Dict[str, Any]] = {}
        
        # Initialize execution stats for all flow types
        for flow_type in FlowType:
            self._execution_stats[flow_type] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "average_duration": 0.0,
                "last_execution": None
            }
    
    def register_flow(
        self, 
        flow_type: FlowType, 
        handler: Callable,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a flow handler with optional metadata."""
        try:
            if flow_type in self._flows:
                self.logger.warning(f"Overriding existing flow handler for {flow_type}")
            
            self._flows[flow_type] = handler
            self._flow_metadata[flow_type] = metadata or {}
            
            self.logger.info(f"Registered flow handler for {flow_type}")
            
        except Exception as e:
            raise FlowRegistrationError(f"Failed to register flow {flow_type}: {e}")
    
    def get_available_flows(self) -> List[FlowType]:
        """Get list of available flow types."""
        return list(self._flows.keys())
    
    def get_flow_metadata(self, flow_type: FlowType) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific flow type."""
        return self._flow_metadata.get(flow_type)
    
    def get_flow_stats(self, flow_type: FlowType) -> Optional[Dict[str, Any]]:
        """Get execution statistics for a specific flow type."""
        return self._execution_stats.get(flow_type)
    
    async def execute_flow(self, flow_type: FlowType, input_data: FlowInput) -> FlowOutput:
        """Execute a registered flow with the given input."""
        if flow_type not in self._flows:
            raise FlowExecutionError(f"Flow {flow_type} is not registered")
        
        handler = self._flows[flow_type]
        stats = self._execution_stats[flow_type]
        
        start_time = datetime.now()
        stats["total_executions"] += 1
        
        try:
            self.logger.info(f"Executing flow {flow_type}")
            result = await handler(input_data)
            
            # Update success stats
            stats["successful_executions"] += 1
            duration = (datetime.now() - start_time).total_seconds()
            
            # Update average duration
            if stats["average_duration"] == 0.0:
                stats["average_duration"] = duration
            else:
                stats["average_duration"] = (stats["average_duration"] + duration) / 2
            
            stats["last_execution"] = datetime.now()
            
            self.logger.info(f"Flow {flow_type} executed successfully in {duration:.2f}s")
            return result
            
        except Exception as e:
            stats["failed_executions"] += 1
            self.logger.error(f"Flow {flow_type} execution failed: {e}")
            raise FlowExecutionError(f"Flow {flow_type} execution failed: {e}")
