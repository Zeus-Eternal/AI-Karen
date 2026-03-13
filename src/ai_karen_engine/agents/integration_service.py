"""
Agent Integration Service

This module provides the main integration service that connects the UI components
with the backend agent orchestration system, handling all execution modes and
providing a unified interface for agent interactions.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from .models import (
    AgentRequest,
    AgentResponse,
    AgentStreamResponse,
    AgentInfo,
    AgentExecutionMode,
    AgentCapability,
    AgentStatus,
    AgentError,
    StreamChunk,
    AgentMetrics
)
from .execution_handlers import get_execution_handler
from .lifecycle_manager import get_lifecycle_manager
from .capability_router import get_capability_router

logger = logging.getLogger(__name__)


class AgentIntegrationService:
    """Main integration service for agent operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AgentIntegrationService")
        self._active_requests: Dict[str, AgentRequest] = {}
        self._active_streams: Dict[str, AsyncGenerator[StreamChunk, None]] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the integration service."""
        self.logger.info("Initializing Agent Integration Service")
        
        # Initialize lifecycle manager
        lifecycle_manager = get_lifecycle_manager()
        await lifecycle_manager.initialize()
        
        self.logger.info("Agent Integration Service initialized")
    
    async def shutdown(self):
        """Shutdown the integration service."""
        self.logger.info("Shutting down Agent Integration Service")
        
        # Cancel all active streams
        async with self._lock:
            for request_id, stream in self._active_streams.items():
                try:
                    if hasattr(stream, 'aclose'):
                        await stream.aclose()
                except Exception as e:
                    self.logger.error(f"Error closing stream for request {request_id}: {e}")
            
            self._active_streams.clear()
            self._active_requests.clear()
        
        # Shutdown lifecycle manager
        lifecycle_manager = get_lifecycle_manager()
        await lifecycle_manager.shutdown()
        
        self.logger.info("Agent Integration Service shutdown complete")
    
    async def execute_request(self, request: AgentRequest) -> AgentResponse:
        """
        Execute an agent request synchronously.
        
        Args:
            request: The agent request to execute
            
        Returns:
            Agent response
        """
        self.logger.info(f"Executing request {request.request_id} in {request.execution_mode.value} mode")
        
        start_time = datetime.utcnow()
        
        try:
            # Track active request
            async with self._lock:
                self._active_requests[request.request_id] = request
            
            # Validate request feasibility
            router = get_capability_router()
            is_feasible, issues = await router.validate_request_feasibility(request)
            
            if not is_feasible:
                return AgentResponse(
                    request_id=request.request_id,
                    agent_id="none",
                    execution_mode=request.execution_mode,
                    response="",
                    processing_time=0.0,
                    error=AgentError(
                        code="REQUEST_NOT_FEASIBLE",
                        message="Request cannot be fulfilled with available agents",
                        details={"issues": issues},
                        recoverable=False
                    )
                )
            
            # Route request to appropriate agent
            selected_agent, routing_metadata = await router.route_request(request)
            
            if not selected_agent:
                return AgentResponse(
                    request_id=request.request_id,
                    agent_id="none",
                    execution_mode=request.execution_mode,
                    response="",
                    processing_time=0.0,
                    error=AgentError(
                        code="NO_SUITABLE_AGENT",
                        message="No suitable agent found for request",
                        details=routing_metadata,
                        recoverable=True
                    )
                )
            
            # Update agent status to processing
            lifecycle_manager = get_lifecycle_manager()
            await lifecycle_manager.update_agent_status(
                selected_agent.agent_id,
                AgentStatus.PROCESSING,
                metadata={"request_id": request.request_id}
            )
            
            # Get execution handler
            handler = get_execution_handler(selected_agent.execution_mode)
            
            # Update request with selected agent info
            request.agent_id = selected_agent.agent_id
            
            # Execute request
            response = await handler.execute(request)
            
            # Update response metadata with routing information
            response.metadata.update({
                "routing": routing_metadata,
                "selected_agent": {
                    "agent_id": selected_agent.agent_id,
                    "name": selected_agent.name,
                    "execution_mode": selected_agent.execution_mode.value
                }
            })
            
            # Update agent metrics
            await self._update_agent_metrics(selected_agent.agent_id, response, start_time)
            
            # Update agent status back to idle
            await lifecycle_manager.update_agent_status(
                selected_agent.agent_id,
                AgentStatus.IDLE
            )
            
            self.logger.info(f"Request {request.request_id} completed successfully")
            return response
            
        except Exception as e:
            self.logger.error(f"Error executing request {request.request_id}: {e}")
            
            # Update agent status to error if we have one
            if 'selected_agent' in locals():
                await lifecycle_manager.update_agent_status(
                    selected_agent.agent_id,
                    AgentStatus.ERROR,
                    metadata={"error": str(e)}
                )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return AgentResponse(
                request_id=request.request_id,
                agent_id=request.agent_id or "unknown",
                execution_mode=request.execution_mode,
                response="",
                processing_time=processing_time,
                error=AgentError(
                    code="EXECUTION_ERROR",
                    message=str(e),
                    recoverable=True
                )
            )
        
        finally:
            # Clean up active request
            async with self._lock:
                self._active_requests.pop(request.request_id, None)
    
    async def execute_request_stream(self, request: AgentRequest) -> AsyncGenerator[AgentStreamResponse, None]:
        """
        Execute an agent request with streaming response.
        
        Args:
            request: The agent request to execute
            
        Yields:
            Agent stream responses
        """
        self.logger.info(f"Starting stream for request {request.request_id} in {request.execution_mode.value} mode")
        
        try:
            # Track active request and stream
            async with self._lock:
                self._active_requests[request.request_id] = request
            
            # Validate request feasibility
            router = get_capability_router()
            is_feasible, issues = await router.validate_request_feasibility(request)
            
            if not is_feasible:
                yield AgentStreamResponse(
                    request_id=request.request_id,
                    agent_id="none",
                    execution_mode=request.execution_mode,
                    chunk=StreamChunk(
                        content="Request cannot be fulfilled with available agents",
                        chunk_type="error",
                        is_final=True
                    ),
                    is_complete=True,
                    error=AgentError(
                        code="REQUEST_NOT_FEASIBLE",
                        message="Request cannot be fulfilled with available agents",
                        details={"issues": issues},
                        recoverable=False
                    )
                )
                return
            
            # Route request to appropriate agent
            selected_agent, routing_metadata = await router.route_request(request)
            
            if not selected_agent:
                yield AgentStreamResponse(
                    request_id=request.request_id,
                    agent_id="none",
                    execution_mode=request.execution_mode,
                    chunk=StreamChunk(
                        content="No suitable agent found for request",
                        chunk_type="error",
                        is_final=True
                    ),
                    is_complete=True,
                    error=AgentError(
                        code="NO_SUITABLE_AGENT",
                        message="No suitable agent found for request",
                        details=routing_metadata,
                        recoverable=True
                    )
                )
                return
            
            # Update agent status to streaming
            lifecycle_manager = get_lifecycle_manager()
            await lifecycle_manager.update_agent_status(
                selected_agent.agent_id,
                AgentStatus.STREAMING,
                metadata={"request_id": request.request_id}
            )
            
            # Get execution handler
            handler = get_execution_handler(selected_agent.execution_mode)
            
            # Update request with selected agent info
            request.agent_id = selected_agent.agent_id
            
            # Start streaming
            full_response = ""
            chunk_count = 0
            
            async for chunk in handler.execute_stream(request):
                chunk_count += 1
                
                # Accumulate response text
                if chunk.chunk_type == "text":
                    full_response += chunk.content
                
                # Create stream response
                stream_response = AgentStreamResponse(
                    request_id=request.request_id,
                    agent_id=selected_agent.agent_id,
                    execution_mode=selected_agent.execution_mode,
                    chunk=chunk,
                    metadata={
                        "routing": routing_metadata,
                        "selected_agent": {
                            "agent_id": selected_agent.agent_id,
                            "name": selected_agent.name,
                            "execution_mode": selected_agent.execution_mode.value
                        },
                        "chunk_count": chunk_count
                    },
                    is_complete=chunk.is_final
                )
                
                yield stream_response
                
                # Check if streaming is complete
                if chunk.is_final:
                    break
            
            # Update agent metrics
            await self._update_agent_metrics(selected_agent.agent_id, None, datetime.utcnow(), full_response)
            
            # Update agent status back to idle
            await lifecycle_manager.update_agent_status(
                selected_agent.agent_id,
                AgentStatus.IDLE
            )
            
            self.logger.info(f"Stream for request {request.request_id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in stream for request {request.request_id}: {e}")
            
            # Update agent status to error if we have one
            if 'selected_agent' in locals():
                await lifecycle_manager.update_agent_status(
                    selected_agent.agent_id,
                    AgentStatus.ERROR,
                    metadata={"error": str(e)}
                )
            
            yield AgentStreamResponse(
                request_id=request.request_id,
                agent_id=request.agent_id or "unknown",
                execution_mode=request.execution_mode,
                chunk=StreamChunk(
                    content=f"Streaming error: {str(e)}",
                    chunk_type="error",
                    is_final=True
                ),
                is_complete=True,
                error=AgentError(
                    code="STREAMING_ERROR",
                    message=str(e),
                    recoverable=True
                )
            )
        
        finally:
            # Clean up active request
            async with self._lock:
                self._active_requests.pop(request.request_id, None)
                self._active_streams.pop(request.request_id, None)
    
    async def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """Get information about a specific agent."""
        lifecycle_manager = get_lifecycle_manager()
        return await lifecycle_manager.get_agent(agent_id)
    
    async def get_all_agents(self) -> List[AgentInfo]:
        """Get information about all agents."""
        lifecycle_manager = get_lifecycle_manager()
        return await lifecycle_manager.get_all_agents()
    
    async def get_agents_by_execution_mode(self, execution_mode: AgentExecutionMode) -> List[AgentInfo]:
        """Get agents by execution mode."""
        lifecycle_manager = get_lifecycle_manager()
        return await lifecycle_manager.get_agents_by_execution_mode(execution_mode)
    
    async def get_available_agents(
        self,
        execution_mode: Optional[AgentExecutionMode] = None,
        capabilities: Optional[List[AgentCapability]] = None
    ) -> List[AgentInfo]:
        """Get available agents that match criteria."""
        lifecycle_manager = get_lifecycle_manager()
        return await lifecycle_manager.get_available_agents(execution_mode, capabilities)
    
    async def create_agent(
        self,
        agent_id: str,
        name: str,
        description: str,
        execution_mode: AgentExecutionMode,
        config: Dict[str, Any]
    ) -> AgentInfo:
        """Create a new agent."""
        from .models import AgentConfig
        
        # Convert config dict to AgentConfig
        agent_config = AgentConfig(**config)
        
        lifecycle_manager = get_lifecycle_manager()
        return await lifecycle_manager.create_agent(
            agent_id=agent_id,
            name=name,
            description=description,
            execution_mode=execution_mode,
            config=agent_config
        )
    
    async def terminate_agent(self, agent_id: str) -> bool:
        """Terminate an agent."""
        lifecycle_manager = get_lifecycle_manager()
        return await lifecycle_manager.terminate_agent(agent_id)
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        lifecycle_manager = get_lifecycle_manager()
        return await lifecycle_manager.delete_agent(agent_id)
    
    async def get_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """Get metrics for a specific agent."""
        agent_info = await self.get_agent_info(agent_id)
        return agent_info.metrics if agent_info else None
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system-wide metrics."""
        lifecycle_manager = get_lifecycle_manager()
        agents = await lifecycle_manager.get_all_agents()
        
        total_requests = sum(agent.metrics.total_requests for agent in agents)
        total_successful = sum(agent.metrics.successful_requests for agent in agents)
        total_failed = sum(agent.metrics.failed_requests for agent in agents)
        
        # Count agents by status
        status_counts = {}
        for status in AgentStatus:
            status_counts[status.value] = sum(1 for agent in agents if agent.status == status)
        
        # Count agents by execution mode
        mode_counts = {}
        for mode in AgentExecutionMode:
            mode_counts[mode.value] = sum(1 for agent in agents if agent.execution_mode == mode)
        
        return {
            "total_agents": len(agents),
            "total_requests": total_requests,
            "successful_requests": total_successful,
            "failed_requests": total_failed,
            "overall_success_rate": total_successful / total_requests if total_requests > 0 else 0.0,
            "agents_by_status": status_counts,
            "agents_by_execution_mode": mode_counts,
            "active_requests": len(self._active_requests),
            "active_streams": len(self._active_streams)
        }
    
    async def cancel_request(self, request_id: str) -> bool:
        """Cancel an active request."""
        async with self._lock:
            if request_id in self._active_requests:
                # Cancel the stream if it exists
                if request_id in self._active_streams:
                    try:
                        stream = self._active_streams[request_id]
                        if hasattr(stream, 'aclose'):
                            await stream.aclose()
                    except Exception as e:
                        self.logger.error(f"Error canceling stream for request {request_id}: {e}")
                    finally:
                        self._active_streams.pop(request_id, None)
                
                # Remove from active requests
                self._active_requests.pop(request_id, None)
                
                self.logger.info(f"Cancelled request {request_id}")
                return True
            
            return False
    
    async def _update_agent_metrics(
        self,
        agent_id: str,
        response: Optional[AgentResponse],
        start_time: datetime,
        full_response_text: Optional[str] = None
    ):
        """Update agent metrics after request completion."""
        try:
            lifecycle_manager = get_lifecycle_manager()
            
            # Get current metrics
            agent_info = await lifecycle_manager.get_agent(agent_id)
            if not agent_info:
                return
            
            metrics_update = {
                "total_requests": agent_info.metrics.total_requests + 1,
                "last_request_time": datetime.utcnow()
            }
            
            # Update success/failure counts
            if response:
                if response.error:
                    metrics_update["failed_requests"] = agent_info.metrics.failed_requests + 1
                else:
                    metrics_update["successful_requests"] = agent_info.metrics.successful_requests + 1
                
                # Update average response time
                total_time = agent_info.metrics.average_response_time * agent_info.metrics.total_requests
                new_total_time = total_time + response.processing_time
                metrics_update["average_response_time"] = new_total_time / metrics_update["total_requests"]
            
            # Update metrics
            await lifecycle_manager.update_agent_metrics(agent_id, metrics_update)
            
        except Exception as e:
            self.logger.error(f"Error updating metrics for agent {agent_id}: {e}")


# Global integration service instance
_integration_service: Optional[AgentIntegrationService] = None


def get_agent_integration_service() -> AgentIntegrationService:
    """Get the global agent integration service instance."""
    global _integration_service
    if _integration_service is None:
        _integration_service = AgentIntegrationService()
    return _integration_service


async def initialize_agent_integration():
    """Initialize the global agent integration service."""
    service = get_agent_integration_service()
    await service.initialize()


async def shutdown_agent_integration():
    """Shutdown the global agent integration service."""
    service = get_agent_integration_service()
    await service.shutdown()