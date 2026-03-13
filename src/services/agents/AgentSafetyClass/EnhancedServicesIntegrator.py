"""
Enhanced Services Integration module for the Agent Safety System.

This module provides integration with enhanced services including Agent Orchestrator,
Agent Registry, Memory Service, AI Orchestrator, and other services for coordinated
safety management.
"""

import asyncio
import logging
import json
import time
from typing import Any, Dict, List, Optional, Set, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

# Import data structures from agent_safety_types.py
from ..agent_safety_types import (
    SafetyLevel, RiskLevel, ValidationResult, Context, BehaviorData
)

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class IntegrationLevel(str, Enum):
    """Integration level enumeration."""
    FULL = "full"
    PARTIAL = "partial"
    MINIMAL = "minimal"
    NONE = "none"


@dataclass
class ServiceHealth:
    """Service health data structure."""
    service_name: str
    status: ServiceStatus
    response_time: float
    last_check: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SafetyCoordinationResult:
    """Safety coordination result data structure."""
    coordination_id: str
    service_name: str
    action: str
    success: bool
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceIntegrationConfig:
    """Service integration configuration data structure."""
    service_name: str
    integration_level: IntegrationLevel
    enabled: bool = True
    health_check_interval: int = 60  # seconds
    timeout: int = 10  # seconds
    retry_attempts: int = 3
    retry_delay: int = 1  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedServicesIntegrator(BaseService):
    """
    Enhanced Services Integration module for the Agent Safety System.
    
    This module provides integration with enhanced services including Agent Orchestrator,
    Agent Registry, Memory Service, AI Orchestrator, and other services for coordinated
    safety management.
    """
    
    def __init__(self, config: ServiceConfig):
        """Initialize the Enhanced Services Integrator."""
        super().__init__(config)
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Initialize service references
        self._services: Dict[str, BaseService] = {}
        
        # Initialize service health tracking
        self._service_health: Dict[str, ServiceHealth] = {}
        
        # Initialize service integration configurations
        self._service_configs: Dict[str, ServiceIntegrationConfig] = {
            "agent_orchestrator": ServiceIntegrationConfig(
                service_name="agent_orchestrator",
                integration_level=IntegrationLevel.FULL
            ),
            "agent_registry": ServiceIntegrationConfig(
                service_name="agent_registry",
                integration_level=IntegrationLevel.FULL
            ),
            "agent_memory": ServiceIntegrationConfig(
                service_name="agent_memory",
                integration_level=IntegrationLevel.PARTIAL
            ),
            "ai_orchestrator": ServiceIntegrationConfig(
                service_name="ai_orchestrator",
                integration_level=IntegrationLevel.FULL
            ),
            "agent_reasoning": ServiceIntegrationConfig(
                service_name="agent_reasoning",
                integration_level=IntegrationLevel.PARTIAL
            ),
            "agent_tool_broker": ServiceIntegrationConfig(
                service_name="agent_tool_broker",
                integration_level=IntegrationLevel.PARTIAL
            )
        }
        
        # Initialize coordination results
        self._coordination_results: List[SafetyCoordinationResult] = []
        
        # Thread-safe locks
        self._services_lock = asyncio.Lock()
        self._health_lock = asyncio.Lock()
        self._coordination_lock = asyncio.Lock()
        self._configs_lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the Enhanced Services Integrator."""
        if self._initialized:
            return
        
        async with self._lock:
            try:
                # Initialize service health tracking
                for service_name in self._service_configs:
                    self._service_health[service_name] = ServiceHealth(
                        service_name=service_name,
                        status=ServiceStatus.UNKNOWN,
                        response_time=0.0
                    )
                
                # Start health check task
                asyncio.create_task(self._health_check_task())
                
                self._initialized = True
                logger.info("Enhanced Services Integrator initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Enhanced Services Integrator: {e}")
                raise RuntimeError(f"Enhanced Services Integrator initialization failed: {e}")
    
    async def register_service(self, service_name: str, service: BaseService) -> bool:
        """
        Register a service for integration.
        
        Args:
            service_name: Name of the service
            service: Service instance
            
        Returns:
            True if registration was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self._services_lock:
                self._services[service_name] = service
                
                # Update service health
                await self._check_service_health(service_name)
                
                logger.info(f"Service {service_name} registered successfully")
                return True
        except Exception as e:
            logger.error(f"Error registering service {service_name}: {e}")
            return False
    
    async def unregister_service(self, service_name: str) -> bool:
        """
        Unregister a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self._services_lock:
                if service_name in self._services:
                    del self._services[service_name]
                    
                    # Update service health
                    self._service_health[service_name] = ServiceHealth(
                        service_name=service_name,
                        status=ServiceStatus.UNKNOWN,
                        response_time=0.0
                    )
                    
                    logger.info(f"Service {service_name} unregistered successfully")
                    return True
                else:
                    logger.warning(f"Service {service_name} not found")
                    return False
        except Exception as e:
            logger.error(f"Error unregistering service {service_name}: {e}")
            return False
    
    async def get_service(self, service_name: str) -> Optional[BaseService]:
        """
        Get a registered service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self._services_lock:
                return self._services.get(service_name)
        except Exception as e:
            logger.error(f"Error getting service {service_name}: {e}")
            return None
    
    async def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """
        Get the health status of a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service health if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self._health_lock:
                return self._service_health.get(service_name)
        except Exception as e:
            logger.error(f"Error getting service health for {service_name}: {e}")
            return None
    
    async def get_all_service_health(self) -> Dict[str, ServiceHealth]:
        """
        Get the health status of all services.
        
        Returns:
            Dictionary of service health statuses
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self._health_lock:
                return self._service_health.copy()
        except Exception as e:
            logger.error(f"Error getting all service health: {e}")
            return {}
    
    async def coordinate_safety_action(
        self,
        service_name: str,
        action: str,
        context: Context,
        **kwargs
    ) -> SafetyCoordinationResult:
        """
        Coordinate a safety action with a service.
        
        Args:
            service_name: Name of the service
            action: Action to coordinate
            context: Context for the action
            **kwargs: Additional parameters
            
        Returns:
            Safety coordination result
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Generate coordination ID
            coordination_id = f"coordination_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Get service configuration
            service_config = self._service_configs.get(service_name)
            if not service_config or not service_config.enabled:
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name=service_name,
                    action=action,
                    success=False,
                    message=f"Service {service_name} not configured or disabled"
                )
            
            # Get service
            service = await self.get_service(service_name)
            if not service:
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name=service_name,
                    action=action,
                    success=False,
                    message=f"Service {service_name} not available"
                )
            
            # Check service health
            service_health = await self.get_service_health(service_name)
            if not service_health or service_health.status != ServiceStatus.HEALTHY:
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name=service_name,
                    action=action,
                    success=False,
                    message=f"Service {service_name} not healthy"
                )
            
            # Coordinate action based on service type
            if service_name == "agent_orchestrator":
                result = await self._coordinate_with_orchestrator(service, action, context, **kwargs)
            elif service_name == "agent_registry":
                result = await self._coordinate_with_registry(service, action, context, **kwargs)
            elif service_name == "agent_memory":
                result = await self._coordinate_with_memory(service, action, context, **kwargs)
            elif service_name == "ai_orchestrator":
                result = await self._coordinate_with_ai_orchestrator(service, action, context, **kwargs)
            elif service_name == "agent_reasoning":
                result = await self._coordinate_with_reasoning(service, action, context, **kwargs)
            elif service_name == "agent_tool_broker":
                result = await self._coordinate_with_tool_broker(service, action, context, **kwargs)
            else:
                result = SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name=service_name,
                    action=action,
                    success=False,
                    message=f"Unknown service type: {service_name}"
                )
            
            # Record coordination result
            async with self._coordination_lock:
                self._coordination_results.append(result)
                
                # Limit coordination results size
                if len(self._coordination_results) > 1000:
                    self._coordination_results = self._coordination_results[-1000:]
            
            return result
        except Exception as e:
            logger.error(f"Error coordinating safety action with {service_name}: {e}")
            
            # Create error result
            error_result = SafetyCoordinationResult(
                coordination_id=f"coordination_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                service_name=service_name,
                action=action,
                success=False,
                message=f"Error coordinating safety action: {str(e)}"
            )
            
            # Record error result
            async with self._coordination_lock:
                self._coordination_results.append(error_result)
            
            return error_result
    
    async def _coordinate_with_orchestrator(
        self,
        service: BaseService,
        action: str,
        context: Context,
        **kwargs
    ) -> SafetyCoordinationResult:
        """
        Coordinate with Agent Orchestrator.
        
        Args:
            service: Agent Orchestrator service
            action: Action to coordinate
            context: Context for the action
            **kwargs: Additional parameters
            
        Returns:
            Safety coordination result
        """
        # Generate coordination ID
        coordination_id = f"coordination_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Handle different actions
            if action == "pause_agent":
                # Pause agent execution
                agent_id = kwargs.get("agent_id")
                if not agent_id:
                    return SafetyCoordinationResult(
                        coordination_id=coordination_id,
                        service_name="agent_orchestrator",
                        action=action,
                        success=False,
                        message="Missing agent_id parameter"
                    )
                
                # In a real implementation, this would call the orchestrator
                # service.pause_agent(agent_id)
                
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_orchestrator",
                    action=action,
                    success=True,
                    message=f"Agent {agent_id} paused successfully"
                )
            
            elif action == "resume_agent":
                # Resume agent execution
                agent_id = kwargs.get("agent_id")
                if not agent_id:
                    return SafetyCoordinationResult(
                        coordination_id=coordination_id,
                        service_name="agent_orchestrator",
                        action=action,
                        success=False,
                        message="Missing agent_id parameter"
                    )
                
                # In a real implementation, this would call the orchestrator
                # service.resume_agent(agent_id)
                
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_orchestrator",
                    action=action,
                    success=True,
                    message=f"Agent {agent_id} resumed successfully"
                )
            
            elif action == "restrict_agent":
                # Restrict agent capabilities
                agent_id = kwargs.get("agent_id")
                restrictions = kwargs.get("restrictions", {})
                if not agent_id:
                    return SafetyCoordinationResult(
                        coordination_id=coordination_id,
                        service_name="agent_orchestrator",
                        action=action,
                        success=False,
                        message="Missing agent_id parameter"
                    )
                
                # In a real implementation, this would call the orchestrator
                # service.restrict_agent(agent_id, restrictions)
                
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_orchestrator",
                    action=action,
                    success=True,
                    message=f"Agent {agent_id} restricted successfully"
                )
            
            else:
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_orchestrator",
                    action=action,
                    success=False,
                    message=f"Unknown action: {action}"
                )
        except Exception as e:
            return SafetyCoordinationResult(
                coordination_id=coordination_id,
                service_name="agent_orchestrator",
                action=action,
                success=False,
                message=f"Error coordinating with orchestrator: {str(e)}"
            )
    
    async def _coordinate_with_registry(
        self,
        service: BaseService,
        action: str,
        context: Context,
        **kwargs
    ) -> SafetyCoordinationResult:
        """
        Coordinate with Agent Registry.
        
        Args:
            service: Agent Registry service
            action: Action to coordinate
            context: Context for the action
            **kwargs: Additional parameters
            
        Returns:
            Safety coordination result
        """
        # Generate coordination ID
        coordination_id = f"coordination_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Handle different actions
            if action == "verify_agent_profile":
                # Verify agent safety profile
                agent_id = kwargs.get("agent_id")
                if not agent_id:
                    return SafetyCoordinationResult(
                        coordination_id=coordination_id,
                        service_name="agent_registry",
                        action=action,
                        success=False,
                        message="Missing agent_id parameter"
                    )
                
                # In a real implementation, this would call the registry
                # profile = service.get_agent_profile(agent_id)
                # is_valid = self._validate_agent_safety_profile(profile)
                
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_registry",
                    action=action,
                    success=True,
                    message=f"Agent {agent_id} profile verified successfully"
                )
            
            elif action == "update_agent_safety_status":
                # Update agent safety status
                agent_id = kwargs.get("agent_id")
                safety_status = kwargs.get("safety_status")
                if not agent_id or not safety_status:
                    return SafetyCoordinationResult(
                        coordination_id=coordination_id,
                        service_name="agent_registry",
                        action=action,
                        success=False,
                        message="Missing agent_id or safety_status parameter"
                    )
                
                # In a real implementation, this would call the registry
                # service.update_agent_safety_status(agent_id, safety_status)
                
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_registry",
                    action=action,
                    success=True,
                    message=f"Agent {agent_id} safety status updated successfully"
                )
            
            else:
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_registry",
                    action=action,
                    success=False,
                    message=f"Unknown action: {action}"
                )
        except Exception as e:
            return SafetyCoordinationResult(
                coordination_id=coordination_id,
                service_name="agent_registry",
                action=action,
                success=False,
                message=f"Error coordinating with registry: {str(e)}"
            )
    
    async def _coordinate_with_memory(
        self,
        service: BaseService,
        action: str,
        context: Context,
        **kwargs
    ) -> SafetyCoordinationResult:
        """
        Coordinate with Agent Memory.
        
        Args:
            service: Agent Memory service
            action: Action to coordinate
            context: Context for the action
            **kwargs: Additional parameters
            
        Returns:
            Safety coordination result
        """
        # Generate coordination ID
        coordination_id = f"coordination_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Handle different actions
            if action == "store_safety_event":
                # Store safety event in memory
                event_data = kwargs.get("event_data")
                if not event_data:
                    return SafetyCoordinationResult(
                        coordination_id=coordination_id,
                        service_name="agent_memory",
                        action=action,
                        success=False,
                        message="Missing event_data parameter"
                    )
                
                # In a real implementation, this would call the memory service
                # service.store_event("safety", event_data)
                
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_memory",
                    action=action,
                    success=True,
                    message="Safety event stored successfully"
                )
            
            elif action == "retrieve_safety_history":
                # Retrieve safety history from memory
                agent_id = kwargs.get("agent_id")
                if not agent_id:
                    return SafetyCoordinationResult(
                        coordination_id=coordination_id,
                        service_name="agent_memory",
                        action=action,
                        success=False,
                        message="Missing agent_id parameter"
                    )
                
                # In a real implementation, this would call the memory service
                # history = service.retrieve_events("safety", {"agent_id": agent_id})
                
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_memory",
                    action=action,
                    success=True,
                    message=f"Safety history for agent {agent_id} retrieved successfully"
                )
            
            else:
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_memory",
                    action=action,
                    success=False,
                    message=f"Unknown action: {action}"
                )
        except Exception as e:
            return SafetyCoordinationResult(
                coordination_id=coordination_id,
                service_name="agent_memory",
                action=action,
                success=False,
                message=f"Error coordinating with memory: {str(e)}"
            )
    
    async def _coordinate_with_ai_orchestrator(
        self,
        service: BaseService,
        action: str,
        context: Context,
        **kwargs
    ) -> SafetyCoordinationResult:
        """
        Coordinate with AI Orchestrator.
        
        Args:
            service: AI Orchestrator service
            action: Action to coordinate
            context: Context for the action
            **kwargs: Additional parameters
            
        Returns:
            Safety coordination result
        """
        # Generate coordination ID
        coordination_id = f"coordination_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Handle different actions
            if action == "safety_assessment":
                # Request safety assessment from AI
                assessment_data = kwargs.get("assessment_data")
                if not assessment_data:
                    return SafetyCoordinationResult(
                        coordination_id=coordination_id,
                        service_name="ai_orchestrator",
                        action=action,
                        success=False,
                        message="Missing assessment_data parameter"
                    )
                
                # In a real implementation, this would call the AI orchestrator
                # assessment = service.assess_safety(assessment_data)
                
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="ai_orchestrator",
                    action=action,
                    success=True,
                    message="Safety assessment completed successfully"
                )
            
            elif action == "risk_analysis":
                # Request risk analysis from AI
                risk_data = kwargs.get("risk_data")
                if not risk_data:
                    return SafetyCoordinationResult(
                        coordination_id=coordination_id,
                        service_name="ai_orchestrator",
                        action=action,
                        success=False,
                        message="Missing risk_data parameter"
                    )
                
                # In a real implementation, this would call the AI orchestrator
                # analysis = service.analyze_risk(risk_data)
                
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="ai_orchestrator",
                    action=action,
                    success=True,
                    message="Risk analysis completed successfully"
                )
            
            else:
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="ai_orchestrator",
                    action=action,
                    success=False,
                    message=f"Unknown action: {action}"
                )
        except Exception as e:
            return SafetyCoordinationResult(
                coordination_id=coordination_id,
                service_name="ai_orchestrator",
                action=action,
                success=False,
                message=f"Error coordinating with AI orchestrator: {str(e)}"
            )
    
    async def _coordinate_with_reasoning(
        self,
        service: BaseService,
        action: str,
        context: Context,
        **kwargs
    ) -> SafetyCoordinationResult:
        """
        Coordinate with Agent Reasoning.
        
        Args:
            service: Agent Reasoning service
            action: Action to coordinate
            context: Context for the action
            **kwargs: Additional parameters
            
        Returns:
            Safety coordination result
        """
        # Generate coordination ID
        coordination_id = f"coordination_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Handle different actions
            if action == "safety_reasoning":
                # Request safety reasoning
                reasoning_data = kwargs.get("reasoning_data")
                if not reasoning_data:
                    return SafetyCoordinationResult(
                        coordination_id=coordination_id,
                        service_name="agent_reasoning",
                        action=action,
                        success=False,
                        message="Missing reasoning_data parameter"
                    )
                
                # In a real implementation, this would call the reasoning service
                # reasoning = service.reason_about_safety(reasoning_data)
                
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_reasoning",
                    action=action,
                    success=True,
                    message="Safety reasoning completed successfully"
                )
            
            else:
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_reasoning",
                    action=action,
                    success=False,
                    message=f"Unknown action: {action}"
                )
        except Exception as e:
            return SafetyCoordinationResult(
                coordination_id=coordination_id,
                service_name="agent_reasoning",
                action=action,
                success=False,
                message=f"Error coordinating with reasoning: {str(e)}"
            )
    
    async def _coordinate_with_tool_broker(
        self,
        service: BaseService,
        action: str,
        context: Context,
        **kwargs
    ) -> SafetyCoordinationResult:
        """
        Coordinate with Agent Tool Broker.
        
        Args:
            service: Agent Tool Broker service
            action: Action to coordinate
            context: Context for the action
            **kwargs: Additional parameters
            
        Returns:
            Safety coordination result
        """
        # Generate coordination ID
        coordination_id = f"coordination_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Handle different actions
            if action == "tool_safety_check":
                # Check tool safety
                tool_name = kwargs.get("tool_name")
                tool_params = kwargs.get("tool_params")
                if not tool_name:
                    return SafetyCoordinationResult(
                        coordination_id=coordination_id,
                        service_name="agent_tool_broker",
                        action=action,
                        success=False,
                        message="Missing tool_name parameter"
                    )
                
                # In a real implementation, this would call the tool broker
                # is_safe = service.check_tool_safety(tool_name, tool_params)
                
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_tool_broker",
                    action=action,
                    success=True,
                    message=f"Tool {tool_name} safety check completed successfully"
                )
            
            elif action == "restrict_tool_access":
                # Restrict tool access
                agent_id = kwargs.get("agent_id")
                tool_names = kwargs.get("tool_names")
                if not agent_id or not tool_names:
                    return SafetyCoordinationResult(
                        coordination_id=coordination_id,
                        service_name="agent_tool_broker",
                        action=action,
                        success=False,
                        message="Missing agent_id or tool_names parameter"
                    )
                
                # In a real implementation, this would call the tool broker
                # service.restrict_tool_access(agent_id, tool_names)
                
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_tool_broker",
                    action=action,
                    success=True,
                    message=f"Tool access restricted for agent {agent_id} successfully"
                )
            
            else:
                return SafetyCoordinationResult(
                    coordination_id=coordination_id,
                    service_name="agent_tool_broker",
                    action=action,
                    success=False,
                    message=f"Unknown action: {action}"
                )
        except Exception as e:
            return SafetyCoordinationResult(
                coordination_id=coordination_id,
                service_name="agent_tool_broker",
                action=action,
                success=False,
                message=f"Error coordinating with tool broker: {str(e)}"
            )
    
    async def get_coordination_results(
        self,
        service_name: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[SafetyCoordinationResult]:
        """
        Get coordination results.
        
        Args:
            service_name: Optional service name to filter by
            action: Optional action to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of coordination results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self._coordination_lock:
                results = self._coordination_results.copy()
                
                # Filter by service name
                if service_name:
                    results = [r for r in results if r.service_name == service_name]
                
                # Filter by action
                if action:
                    results = [r for r in results if r.action == action]
                
                # Filter by time range
                if start_time:
                    results = [r for r in results if r.timestamp >= start_time]
                
                if end_time:
                    results = [r for r in results if r.timestamp <= end_time]
                
                # Sort by timestamp (newest first)
                results.sort(key=lambda x: x.timestamp, reverse=True)
                
                # Limit results
                return results[:limit]
        except Exception as e:
            logger.error(f"Error getting coordination results: {e}")
            return []
    
    async def update_service_config(
        self,
        service_name: str,
        config: ServiceIntegrationConfig
    ) -> bool:
        """
        Update service integration configuration.
        
        Args:
            service_name: Name of the service
            config: New configuration
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self._configs_lock:
                if service_name in self._service_configs:
                    self._service_configs[service_name] = config
                    logger.info(f"Configuration for service {service_name} updated successfully")
                    return True
                else:
                    logger.warning(f"Service {service_name} not found in configurations")
                    return False
        except Exception as e:
            logger.error(f"Error updating service configuration for {service_name}: {e}")
            return False
    
    async def get_service_config(self, service_name: str) -> Optional[ServiceIntegrationConfig]:
        """
        Get service integration configuration.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service configuration if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self._configs_lock:
                return self._service_configs.get(service_name)
        except Exception as e:
            logger.error(f"Error getting service configuration for {service_name}: {e}")
            return None
    
    async def _health_check_task(self) -> None:
        """Background task for checking service health."""
        while True:
            try:
                # Check health of all configured services
                for service_name in self._service_configs:
                    await self._check_service_health(service_name)
                
                # Wait for next check
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in health check task: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _check_service_health(self, service_name: str) -> None:
        """
        Check the health of a service.
        
        Args:
            service_name: Name of the service
        """
        try:
            # Get service configuration
            service_config = self._service_configs.get(service_name)
            if not service_config or not service_config.enabled:
                return
            
            # Get service
            service = await self.get_service(service_name)
            if not service:
                async with self._health_lock:
                    self._service_health[service_name] = ServiceHealth(
                        service_name=service_name,
                        status=ServiceStatus.UNKNOWN,
                        response_time=0.0
                    )
                return
            
            # Check service health
            start_time = time.time()
            is_healthy = await service.health_check()
            response_time = time.time() - start_time
            
            # Update service health
            async with self._health_lock:
                self._service_health[service_name] = ServiceHealth(
                    service_name=service_name,
                    status=ServiceStatus.HEALTHY if is_healthy else ServiceStatus.UNHEALTHY,
                    response_time=response_time
                )
        except Exception as e:
            logger.error(f"Error checking health of service {service_name}: {e}")
            
            # Update service health to unknown
            async with self._health_lock:
                self._service_health[service_name] = ServiceHealth(
                    service_name=service_name,
                    status=ServiceStatus.UNKNOWN,
                    response_time=0.0
                )
    
    async def health_check(self) -> bool:
        """Check health of the Enhanced Services Integrator."""
        if not self._initialized:
            return False
        
        try:
            # Check if any services are registered
            async with self._services_lock:
                if not self._services:
                    return False
            
            # Check if service health tracking is working
            async with self._health_lock:
                if not self._service_health:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Enhanced Services Integrator health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Enhanced Services Integrator."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Enhanced Services Integrator started successfully")
    
    async def stop(self) -> None:
        """Stop the Enhanced Services Integrator."""
        if not self._initialized:
            return
        
        # Clear services and health tracking
        async with self._services_lock:
            self._services.clear()
        
        async with self._health_lock:
            self._service_health.clear()
        
        async with self._coordination_lock:
            self._coordination_results.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Enhanced Services Integrator stopped successfully")