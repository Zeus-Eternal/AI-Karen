"""
Request Priority Service Helper

This module provides helper functionality for request priority operations in KAREN AI system.
It handles request prioritization, request scheduling, and other request-related operations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid
import heapq

logger = logging.getLogger(__name__)


class RequestPriorityServiceHelper:
    """
    Helper service for request priority operations.
    
    This service provides methods for prioritizing, scheduling, and managing
    requests in KAREN AI system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the request priority service helper.
        
        Args:
            config: Configuration dictionary for the request priority service
        """
        self.config = config
        self.request_priority_enabled = config.get("request_priority_enabled", True)
        self.auto_prioritize = config.get("auto_prioritize", False)
        self.prioritization_interval = config.get("prioritization_interval", 60)  # 1 minute
        self.max_queue_size = config.get("max_queue_size", 1000)
        self.request_queue = []
        self.request_priorities = {}
        self.request_schedules = {}
        self._is_initialized = False
        self._is_running = False
        
    async def initialize(self) -> bool:
        """
        Initialize the request priority service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            logger.info("Initializing request priority service")
            
            # Initialize request priority
            if self.request_priority_enabled:
                await self._initialize_request_priority()
                
            self._is_initialized = True
            logger.info("Request priority service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing request priority service: {str(e)}")
            return False
    
    async def _initialize_request_priority(self) -> None:
        """Initialize request priority."""
        # In a real implementation, this would set up request priority
        logger.info("Initializing request priority")
        
    async def start(self) -> bool:
        """
        Start the request priority service.
        
        Returns:
            True if the service started successfully, False otherwise
        """
        try:
            logger.info("Starting request priority service")
            
            # Start request priority
            if self.request_priority_enabled:
                await self._start_request_priority()
                
            self._is_running = True
            logger.info("Request priority service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting request priority service: {str(e)}")
            return False
    
    async def _start_request_priority(self) -> None:
        """Start request priority."""
        # In a real implementation, this would start request priority
        logger.info("Starting request priority")
        
    async def stop(self) -> bool:
        """
        Stop the request priority service.
        
        Returns:
            True if the service stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping request priority service")
            
            # Stop request priority
            if self.request_priority_enabled:
                await self._stop_request_priority()
                
            self._is_running = False
            self._is_initialized = False
            logger.info("Request priority service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping request priority service: {str(e)}")
            return False
    
    async def _stop_request_priority(self) -> None:
        """Stop request priority."""
        # In a real implementation, this would stop request priority
        logger.info("Stopping request priority")
        
    async def health_check(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check the health of the request priority service.
        
        Args:
            data: Optional data for the health check
            context: Optional context for the health check
            
        Returns:
            Dictionary containing health status information
        """
        try:
            if not self._is_initialized:
                return {"status": "unhealthy", "message": "Request priority service is not initialized"}
                
            # Check request priority health
            request_health = {"status": "healthy", "message": "Request priority is healthy"}
            if self.request_priority_enabled:
                request_health = await self._health_check_request_priority()
                
            # Determine overall health
            overall_status = request_health.get("status", "healthy")
            
            return {
                "status": overall_status,
                "message": f"Request priority service is {overall_status}",
                "request_health": request_health,
                "request_queue_size": len(self.request_queue),
                "request_priorities_count": len(self.request_priorities),
                "request_schedules_count": len(self.request_schedules)
            }
            
        except Exception as e:
            logger.error(f"Error checking request priority service health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    async def _health_check_request_priority(self) -> Dict[str, Any]:
        """Check request priority health."""
        # In a real implementation, this would check request priority health
        return {"status": "healthy", "message": "Request priority is healthy"}
        
    async def prioritize_request(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prioritize a request.
        
        Args:
            data: Optional data for the request prioritization
            context: Optional context for the request prioritization
            
        Returns:
            Dictionary containing the prioritization result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Request priority service is not initialized"}
                
            # Check if request priority is enabled
            if not self.request_priority_enabled:
                return {"status": "error", "message": "Request priority is disabled"}
                
            # Get prioritization parameters
            request_id = data.get("request_id") if data else None
            request_data = data.get("request_data") if data else None
            priority = data.get("priority") if data else None
            options = data.get("options", {}) if data else {}
            
            # Validate request_id
            if not request_id:
                return {"status": "error", "message": "Request ID is required for request prioritization"}
            if not request_data:
                return {"status": "error", "message": "Request data is required for request prioritization"}
                
            # If priority is not provided, calculate it
            if priority is None:
                priority = await self._calculate_request_priority(request_id, request_data, options, context)
                
            # Create prioritization
            prioritization_id = str(uuid.uuid4())
            prioritization = {
                "prioritization_id": prioritization_id,
                "request_id": request_id,
                "priority": priority,
                "status": "prioritized",
                "created_at": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Add prioritization to request priorities
            self.request_priorities[request_id] = prioritization
            
            # Add request to queue
            await self._add_request_to_queue(request_id, priority, request_data, options, context)
            
            return {
                "status": "success",
                "message": "Request prioritized successfully",
                "prioritization_id": prioritization_id,
                "request_id": request_id,
                "priority": priority
            }
            
        except Exception as e:
            logger.error(f"Error prioritizing request: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _calculate_request_priority(self, request_id: str, request_data: Dict[str, Any], options: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> float:
        """Calculate request priority."""
        # In a real implementation, this would calculate request priority based on various factors
        logger.info(f"Calculating priority for request: {request_id}")
        
        # Get request type
        request_type = request_data.get("type", "default")
        
        # Get request urgency
        urgency = request_data.get("urgency", 0.5)  # 0.0 to 1.0
        
        # Get request importance
        importance = request_data.get("importance", 0.5)  # 0.0 to 1.0
        
        # Get request complexity
        complexity = request_data.get("complexity", 0.5)  # 0.0 to 1.0
        
        # Get request deadline (if any)
        deadline = request_data.get("deadline")
        deadline_factor = 0.0
        if deadline:
            deadline_time = datetime.fromisoformat(deadline)
            current_time = datetime.now()
            time_to_deadline = (deadline_time - current_time).total_seconds()
            
            # Calculate deadline factor (higher priority as deadline approaches)
            if time_to_deadline > 0:
                deadline_factor = min(1.0, 1.0 - (time_to_deadline / 86400.0))  # Normalize to days
            else:
                deadline_factor = 1.0  # Overdue
        
        # Calculate priority based on factors
        priority = (urgency * 0.3) + (importance * 0.3) + (deadline_factor * 0.3) + ((1.0 - complexity) * 0.1)
        
        # Adjust priority based on request type
        if request_type == "critical":
            priority = min(1.0, priority + 0.2)
        elif request_type == "urgent":
            priority = min(1.0, priority + 0.1)
        elif request_type == "background":
            priority = max(0.0, priority - 0.2)
        
        return priority
    
    async def _add_request_to_queue(self, request_id: str, priority: float, request_data: Dict[str, Any], options: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> None:
        """Add request to queue."""
        # Check if queue is full
        if len(self.request_queue) >= self.max_queue_size:
            # Remove lowest priority request
            heapq.heappop(self.request_queue)
        
        # Add request to queue (using negative priority for max heap)
        heapq.heappush(self.request_queue, (-priority, request_id, request_data))
    
    async def get_next_request(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the next request from the queue.
        
        Args:
            data: Optional data for the request
            context: Optional context for the request
            
        Returns:
            Dictionary containing the next request
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Request priority service is not initialized"}
                
            # Check if request priority is enabled
            if not self.request_priority_enabled:
                return {"status": "error", "message": "Request priority is disabled"}
                
            # Check if queue is empty
            if not self.request_queue:
                return {"status": "success", "message": "No requests in queue", "request": None}
                
            # Get next request
            _, request_id, request_data = heapq.heappop(self.request_queue)
            
            # Get request priority
            request_priority = self.request_priorities.get(request_id)
            priority = request_priority["priority"] if request_priority else 0.0
            
            return {
                "status": "success",
                "message": "Next request retrieved successfully",
                "request": {
                    "request_id": request_id,
                    "priority": priority,
                    "request_data": request_data
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting next request: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def schedule_request(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Schedule a request.
        
        Args:
            data: Optional data for the request scheduling
            context: Optional context for the request scheduling
            
        Returns:
            Dictionary containing the scheduling result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Request priority service is not initialized"}
                
            # Check if request priority is enabled
            if not self.request_priority_enabled:
                return {"status": "error", "message": "Request priority is disabled"}
                
            # Get scheduling parameters
            request_id = data.get("request_id") if data else None
            request_data = data.get("request_data") if data else None
            schedule_time = data.get("schedule_time") if data else None
            options = data.get("options", {}) if data else {}
            
            # Validate request_id
            if not request_id:
                return {"status": "error", "message": "Request ID is required for request scheduling"}
            if not request_data:
                return {"status": "error", "message": "Request data is required for request scheduling"}
            if not schedule_time:
                return {"status": "error", "message": "Schedule time is required for request scheduling"}
                
            # Parse schedule time
            if isinstance(schedule_time, str):
                schedule_time = datetime.fromisoformat(schedule_time)
            elif not isinstance(schedule_time, datetime):
                return {"status": "error", "message": "Invalid schedule time format"}
                
            # Create schedule
            schedule_id = str(uuid.uuid4())
            schedule = {
                "schedule_id": schedule_id,
                "request_id": request_id,
                "request_data": request_data,
                "schedule_time": schedule_time.isoformat(),
                "status": "scheduled",
                "created_at": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Add schedule to request schedules
            self.request_schedules[schedule_id] = schedule
            
            return {
                "status": "success",
                "message": "Request scheduled successfully",
                "schedule_id": schedule_id,
                "request_id": request_id,
                "schedule_time": schedule_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling request: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_scheduled_requests(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get scheduled requests.
        
        Args:
            data: Optional data for the request
            context: Optional context for the request
            
        Returns:
            Dictionary containing the scheduled requests
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Request priority service is not initialized"}
                
            # Check if request priority is enabled
            if not self.request_priority_enabled:
                return {"status": "error", "message": "Request priority is disabled"}
                
            # Get current time
            current_time = datetime.now()
            
            # Get scheduled requests
            scheduled_requests = []
            for schedule_id, schedule in self.request_schedules.items():
                schedule_time = datetime.fromisoformat(schedule["schedule_time"])
                
                # Check if request is scheduled for now or in the past
                if schedule_time <= current_time:
                    scheduled_requests.append({
                        "schedule_id": schedule_id,
                        "request_id": schedule["request_id"],
                        "request_data": schedule["request_data"],
                        "schedule_time": schedule["schedule_time"]
                    })
                    
                    # Remove schedule
                    self.request_schedules.pop(schedule_id)
            
            return {
                "status": "success",
                "message": "Scheduled requests retrieved successfully",
                "scheduled_requests": scheduled_requests,
                "count": len(scheduled_requests)
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduled requests: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def reprioritize_requests(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Reprioritize requests.
        
        Args:
            data: Optional data for the request reprioritization
            context: Optional context for the request reprioritization
            
        Returns:
            Dictionary containing the reprioritization result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Request priority service is not initialized"}
                
            # Check if request priority is enabled
            if not self.request_priority_enabled:
                return {"status": "error", "message": "Request priority is disabled"}
                
            # Get reprioritization parameters
            reprioritization_type = data.get("reprioritization_type", "auto") if data else "auto"
            options = data.get("options", {}) if data else {}
            
            # Create reprioritization
            reprioritization_id = str(uuid.uuid4())
            reprioritization = {
                "reprioritization_id": reprioritization_id,
                "reprioritization_type": reprioritization_type,
                "status": "reprioritizing",
                "created_at": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Reprioritize requests
            result = await self._reprioritize_requests(reprioritization_type, options, context)
            
            return {
                "status": "success",
                "message": "Requests reprioritized successfully",
                "reprioritization_id": reprioritization_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error reprioritizing requests: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _reprioritize_requests(self, reprioritization_type: str, options: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Reprioritize requests."""
        # In a real implementation, this would reprioritize requests
        logger.info(f"Reprioritizing requests with type: {reprioritization_type}")
        
        # Simulate request reprioritization
        await asyncio.sleep(1)
        
        # Get current requests in queue
        current_requests = []
        temp_queue = []
        
        # Extract requests from queue
        while self.request_queue:
            neg_priority, request_id, request_data = heapq.heappop(self.request_queue)
            priority = -neg_priority
            current_requests.append((priority, request_id, request_data))
            temp_queue.append((neg_priority, request_id, request_data))
        
        # Restore queue
        for item in temp_queue:
            heapq.heappush(self.request_queue, item)
        
        # Reprioritize requests based on reprioritization type
        reprioritized_requests = []
        for priority, request_id, request_data in current_requests:
            if reprioritization_type in ["auto", "urgency"]:
                # Increase priority for urgent requests
                if request_data.get("urgency", 0.5) > 0.7:
                    priority = min(1.0, priority + 0.1)
            if reprioritization_type in ["auto", "importance"]:
                # Increase priority for important requests
                if request_data.get("importance", 0.5) > 0.7:
                    priority = min(1.0, priority + 0.1)
            if reprioritization_type in ["auto", "deadline"]:
                # Increase priority for requests with approaching deadlines
                deadline = request_data.get("deadline")
                if deadline:
                    deadline_time = datetime.fromisoformat(deadline)
                    current_time = datetime.now()
                    time_to_deadline = (deadline_time - current_time).total_seconds()
                    if 0 < time_to_deadline < 3600:  # Less than 1 hour
                        priority = min(1.0, priority + 0.2)
            
            # Update request priority
            self.request_priorities[request_id]["priority"] = priority
            reprioritized_requests.append({
                "request_id": request_id,
                "old_priority": float(-neg_priority) if isinstance(neg_priority, (int, float)) else 0.0,
                "new_priority": priority,
                "change": priority - (float(-neg_priority) if isinstance(neg_priority, (int, float)) else 0.0)
            })
        
        # Rebuild queue with new priorities
        self.request_queue = []
        for priority, request_id, request_data in current_requests:
            heapq.heappush(self.request_queue, (-priority, request_id, request_data))
        
        # Return reprioritization result
        result = {
            "reprioritization_type": reprioritization_type,
            "status": "completed",
            "message": "Request reprioritization completed successfully",
            "reprioritization_time": 1.0,  # Simulated reprioritization time
            "reprioritized_requests": reprioritized_requests,
            "total_requests": len(reprioritized_requests)
        }
        
        return result
    
    async def balance_requests(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Balance requests across resources.
        
        Args:
            data: Optional data for the request balancing
            context: Optional context for the request balancing
            
        Returns:
            Dictionary containing the balancing result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Request priority service is not initialized"}
                
            # Check if request priority is enabled
            if not self.request_priority_enabled:
                return {"status": "error", "message": "Request priority is disabled"}
                
            # Get balancing parameters
            resources = data.get("resources", []) if data else []
            balancing_strategy = data.get("balancing_strategy", "load") if data else "load"
            options = data.get("options", {}) if data else {}
            
            # Create balancing
            balancing_id = str(uuid.uuid4())
            balancing = {
                "balancing_id": balancing_id,
                "resources": resources,
                "balancing_strategy": balancing_strategy,
                "status": "balancing",
                "created_at": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Balance requests
            result = await self._balance_requests(resources, balancing_strategy, options, context)
            
            return {
                "status": "success",
                "message": "Requests balanced successfully",
                "balancing_id": balancing_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error balancing requests: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _balance_requests(self, resources: List[str], balancing_strategy: str, options: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Balance requests across resources."""
        # In a real implementation, this would balance requests across resources
        logger.info(f"Balancing requests across resources: {resources} with strategy: {balancing_strategy}")
        
        # Simulate request balancing
        await asyncio.sleep(1)
        
        # Get current requests in queue
        current_requests = []
        temp_queue = []
        
        # Extract requests from queue
        while self.request_queue:
            neg_priority, request_id, request_data = heapq.heappop(self.request_queue)
            priority = -neg_priority
            current_requests.append((priority, request_id, request_data))
            temp_queue.append((neg_priority, request_id, request_data))
        
        # Restore queue
        for item in temp_queue:
            heapq.heappush(self.request_queue, item)
        
        # If no resources provided, use default resources
        if not resources:
            resources = ["resource1", "resource2", "resource3"]
        
        # Distribute requests across resources based on balancing strategy
        balanced_requests = {}
        for resource in resources:
            balanced_requests[resource] = []
        
        # Distribute requests based on balancing strategy
        if balancing_strategy == "round_robin":
            for i, (priority, request_id, request_data) in enumerate(current_requests):
                resource = resources[i % len(resources)]
                balanced_requests[resource].append({
                    "request_id": request_id,
                    "priority": priority,
                    "request_data": request_data
                })
        elif balancing_strategy == "load":
            # Sort requests by priority (highest first)
            current_requests.sort(key=lambda x: x[0], reverse=True)
            
            # Distribute requests to least loaded resource
            resource_loads = {resource: 0 for resource in resources}
            
            for priority, request_id, request_data in current_requests:
                # Find least loaded resource
                least_loaded_resource = min(resource_loads.items(), key=lambda x: x[1])[0]
                
                # Add request to least loaded resource
                balanced_requests[least_loaded_resource].append({
                    "request_id": request_id,
                    "priority": priority,
                    "request_data": request_data
                })
                
                # Update resource load
                resource_loads[least_loaded_resource] += 1
        elif balancing_strategy == "priority":
            # Sort requests by priority (highest first)
            current_requests.sort(key=lambda x: x[0], reverse=True)
            
            # Distribute requests based on priority and resource capacity
            resource_capacities = {resource: 1.0 for resource in resources}
            
            for priority, request_id, request_data in current_requests:
                # Find resource with highest capacity
                highest_capacity_resource = max(resource_capacities.items(), key=lambda x: x[1])[0]
                
                # Add request to highest capacity resource
                balanced_requests[highest_capacity_resource].append({
                    "request_id": request_id,
                    "priority": priority,
                    "request_data": request_data
                })
                
                # Update resource capacity
                resource_capacities[highest_capacity_resource] *= 0.9  # Reduce capacity
        
        # Calculate statistics
        request_counts = {resource: len(requests) for resource, requests in balanced_requests.items()}
        total_requests = sum(request_counts.values())
        average_requests_per_resource = total_requests / len(resources) if resources else 0
        
        # Return balancing result
        result = {
            "balancing_strategy": balancing_strategy,
            "status": "completed",
            "message": "Request balancing completed successfully",
            "balancing_time": 1.0,  # Simulated balancing time
            "balanced_requests": balanced_requests,
            "request_counts": request_counts,
            "total_requests": total_requests,
            "average_requests_per_resource": average_requests_per_resource
        }
        
        return result
    
    async def get_status(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get status of the request priority service.
        
        Args:
            data: Optional data for the status request
            context: Optional context for the status request
            
        Returns:
            Dictionary containing the status information
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Request priority service is not initialized"}
                
            status = {
                "request_priority_enabled": self.request_priority_enabled,
                "auto_prioritize": self.auto_prioritize,
                "prioritization_interval": self.prioritization_interval,
                "max_queue_size": self.max_queue_size,
                "is_running": self._is_running,
                "request_queue_size": len(self.request_queue),
                "request_priorities_count": len(self.request_priorities),
                "request_schedules_count": len(self.request_schedules)
            }
            
            return {
                "status": "success",
                "message": "Request priority status retrieved successfully",
                "request_priority_status": status
            }
            
        except Exception as e:
            logger.error(f"Error getting request priority status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_stats(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get statistics for the request priority service.
        
        Args:
            data: Optional data for the stats request
            context: Optional context for the stats request
            
        Returns:
            Dictionary containing the statistics
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Request priority service is not initialized"}
                
            # Get current requests in queue
            current_requests = []
            temp_queue = []
            
            # Extract requests from queue
            while self.request_queue:
                neg_priority, request_id, request_data = heapq.heappop(self.request_queue)
                priority = -neg_priority
                current_requests.append((priority, request_id, request_data))
                temp_queue.append((neg_priority, request_id, request_data))
            
            # Restore queue
            for item in temp_queue:
                heapq.heappush(self.request_queue, item)
            
            # Calculate priority distribution
            priority_distribution = {
                "high": len([t for t in current_requests if t[0] > 0.7]),
                "medium": len([t for t in current_requests if 0.3 <= t[0] <= 0.7]),
                "low": len([t for t in current_requests if t[0] < 0.3])
            }
            
            # Calculate type distribution
            type_distribution = {}
            for priority, request_id, request_data in current_requests:
                request_type = request_data.get("type", "default")
                if request_type not in type_distribution:
                    type_distribution[request_type] = 0
                type_distribution[request_type] += 1
            
            # Calculate average priority
            average_priority = sum(t[0] for t in current_requests) / len(current_requests) if current_requests else 0
            
            # Calculate highest and lowest priority
            highest_priority = max(t[0] for t in current_requests) if current_requests else 0
            lowest_priority = min(t[0] for t in current_requests) if current_requests else 0
            
            # Get scheduled requests
            scheduled_requests = []
            current_time = datetime.now()
            for schedule_id, schedule in self.request_schedules.items():
                schedule_time = datetime.fromisoformat(schedule["schedule_time"])
                scheduled_requests.append({
                    "schedule_id": schedule_id,
                    "request_id": schedule["request_id"],
                    "schedule_time": schedule["schedule_time"],
                    "time_until_schedule": (schedule_time - current_time).total_seconds()
                })
            
            # Sort scheduled requests by schedule time
            scheduled_requests.sort(key=lambda x: x["time_until_schedule"])
            
            stats = {
                "request_priority_enabled": self.request_priority_enabled,
                "auto_prioritize": self.auto_prioritize,
                "prioritization_interval": self.prioritization_interval,
                "max_queue_size": self.max_queue_size,
                "is_running": self._is_running,
                "request_queue_size": len(self.request_queue),
                "request_priorities_count": len(self.request_priorities),
                "request_schedules_count": len(self.request_schedules),
                "priority_distribution": priority_distribution,
                "type_distribution": type_distribution,
                "average_priority": average_priority,
                "highest_priority": highest_priority,
                "lowest_priority": lowest_priority,
                "scheduled_requests": scheduled_requests[:10]  # Return top 10 scheduled requests
            }
            
            return {
                "status": "success",
                "message": "Request priority statistics retrieved successfully",
                "request_priority_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting request priority statistics: {str(e)}")
            return {"status": "error", "message": str(e)}