"""
Workflow Service Helper

This module provides helper functionality for workflow operations in KAREN AI system.
It handles workflow management, workflow execution, and other workflow-related operations.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class WorkflowServiceHelper:
    """
    Helper service for workflow operations.
    
    This service provides methods for managing workflows, executing workflows,
    and other workflow-related operations in KAREN AI system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the workflow service helper.
        
        Args:
            config: Configuration dictionary for the workflow service
        """
        self.config = config
        self.workflows_enabled = config.get("workflows_enabled", True)
        self.max_workflows = config.get("max_workflows", 100)
        self.max_workflow_steps = config.get("max_workflow_steps", 50)
        self.workflow_timeout = config.get("workflow_timeout", 300)  # 5 minutes
        self.workflows = {}
        self.workflow_executions = []
        self._is_initialized = False
        self._is_running = False
        
    async def initialize(self) -> bool:
        """
        Initialize the workflow service.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            logger.info("Initializing workflow service")
            
            # Initialize workflows
            if self.workflows_enabled:
                await self._initialize_workflows()
                
            self._is_initialized = True
            logger.info("Workflow service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing workflow service: {str(e)}")
            return False
    
    async def _initialize_workflows(self) -> None:
        """Initialize workflows."""
        # In a real implementation, this would set up workflows
        logger.info("Initializing workflows")
        
    async def start(self) -> bool:
        """
        Start the workflow service.
        
        Returns:
            True if the service started successfully, False otherwise
        """
        try:
            logger.info("Starting workflow service")
            
            # Start workflows
            if self.workflows_enabled:
                await self._start_workflows()
                
            self._is_running = True
            logger.info("Workflow service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting workflow service: {str(e)}")
            return False
    
    async def _start_workflows(self) -> None:
        """Start workflows."""
        # In a real implementation, this would start workflows
        logger.info("Starting workflows")
        
    async def stop(self) -> bool:
        """
        Stop the workflow service.
        
        Returns:
            True if the service stopped successfully, False otherwise
        """
        try:
            logger.info("Stopping workflow service")
            
            # Stop workflows
            if self.workflows_enabled:
                await self._stop_workflows()
                
            self._is_running = False
            self._is_initialized = False
            logger.info("Workflow service stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping workflow service: {str(e)}")
            return False
    
    async def _stop_workflows(self) -> None:
        """Stop workflows."""
        # In a real implementation, this would stop workflows
        logger.info("Stopping workflows")
        
    async def health_check(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check the health of the workflow service.
        
        Args:
            data: Optional data for the health check
            context: Optional context for the health check
            
        Returns:
            Dictionary containing health status information
        """
        try:
            if not self._is_initialized:
                return {"status": "unhealthy", "message": "Workflow service is not initialized"}
                
            # Check workflows health
            workflows_health = {"status": "healthy", "message": "Workflows are healthy"}
            if self.workflows_enabled:
                workflows_health = await self._health_check_workflows()
                
            # Determine overall health
            overall_status = workflows_health.get("status", "healthy")
            
            return {
                "status": overall_status,
                "message": f"Workflow service is {overall_status}",
                "workflows_health": workflows_health,
                "workflows_count": len(self.workflows),
                "workflow_executions_count": len(self.workflow_executions)
            }
            
        except Exception as e:
            logger.error(f"Error checking workflow service health: {str(e)}")
            return {"status": "unhealthy", "message": str(e)}
    
    async def _health_check_workflows(self) -> Dict[str, Any]:
        """Check workflows health."""
        # In a real implementation, this would check workflows health
        return {"status": "healthy", "message": "Workflows are healthy"}
        
    async def create_workflow(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a workflow.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Workflow service is not initialized"}
                
            # Check if workflows are enabled
            if not self.workflows_enabled:
                return {"status": "error", "message": "Workflows are disabled"}
                
            # Get workflow parameters
            name = data.get("name") if data else None
            description = data.get("description") if data else None
            steps = data.get("steps", []) if data else []
            triggers = data.get("triggers", []) if data else []
            metadata = data.get("metadata", {}) if data else {}
            
            # Validate name
            if not name:
                return {"status": "error", "message": "Name is required for workflow"}
                
            # Validate steps
            if not steps:
                return {"status": "error", "message": "Steps are required for workflow"}
                
            # Validate number of steps
            if len(steps) > self.max_workflow_steps:
                return {"status": "error", "message": f"Workflow exceeds maximum number of steps ({self.max_workflow_steps})"}
                
            # Check if workflow already exists
            if name in self.workflows:
                return {"status": "error", "message": f"Workflow {name} already exists"}
                
            # Check if we have reached the maximum number of workflows
            if len(self.workflows) >= self.max_workflows:
                return {"status": "error", "message": "Maximum number of workflows reached"}
                
            # Create workflow
            workflow_id = str(uuid.uuid4())
            workflow = {
                "workflow_id": workflow_id,
                "name": name,
                "description": description,
                "steps": steps,
                "triggers": triggers,
                "status": "created",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "metadata": metadata,
                "context": context or {}
            }
            
            # Add workflow to workflows
            self.workflows[workflow_id] = workflow
            
            return {
                "status": "success",
                "message": "Workflow created successfully",
                "workflow_id": workflow_id,
                "workflow": workflow
            }
            
        except Exception as e:
            logger.error(f"Error creating workflow: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_workflow(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a workflow.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Workflow service is not initialized"}
                
            # Get workflow parameters
            workflow_id = data.get("workflow_id") if data else None
            name = data.get("name") if data else None
            
            # Validate parameters
            if not workflow_id and not name:
                return {"status": "error", "message": "Workflow ID or name is required"}
                
            # Get workflow
            workflow = None
            if workflow_id:
                if workflow_id in self.workflows:
                    workflow = self.workflows[workflow_id]
            elif name:
                # Search for workflow by name
                for w in self.workflows.values():
                    if w["name"] == name:
                        workflow = w
                        break
                            
            if not workflow:
                return {"status": "error", "message": "Workflow not found"}
                
            return {
                "status": "success",
                "message": "Workflow retrieved successfully",
                "workflow_id": workflow["workflow_id"],
                "workflow": workflow
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def update_workflow(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update a workflow.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Workflow service is not initialized"}
                
            # Get workflow parameters
            workflow_id = data.get("workflow_id") if data else None
            name = data.get("name") if data else None
            description = data.get("description") if data else None
            steps = data.get("steps") if data else None
            triggers = data.get("triggers") if data else None
            status = data.get("status") if data else None
            metadata = data.get("metadata") if data else None
            
            # Validate workflow_id
            if not workflow_id:
                return {"status": "error", "message": "Workflow ID is required"}
                
            # Get workflow
            if workflow_id not in self.workflows:
                return {"status": "error", "message": f"Workflow {workflow_id} not found"}
                
            workflow = self.workflows[workflow_id]
                
            # Update workflow
            if name is not None:
                workflow["name"] = name
            if description is not None:
                workflow["description"] = description
            if steps is not None:
                # Validate number of steps
                if len(steps) > self.max_workflow_steps:
                    return {"status": "error", "message": f"Workflow exceeds maximum number of steps ({self.max_workflow_steps})"}
                workflow["steps"] = steps
            if triggers is not None:
                workflow["triggers"] = triggers
            if status is not None:
                workflow["status"] = status
            if metadata is not None:
                workflow["metadata"].update(metadata)
                
            # Update timestamp
            workflow["updated_at"] = datetime.now().isoformat()
            
            return {
                "status": "success",
                "message": "Workflow updated successfully",
                "workflow_id": workflow_id,
                "workflow": workflow
            }
            
        except Exception as e:
            logger.error(f"Error updating workflow: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def delete_workflow(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Delete a workflow.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Workflow service is not initialized"}
                
            # Get workflow parameters
            workflow_id = data.get("workflow_id") if data else None
            
            # Validate workflow_id
            if not workflow_id:
                return {"status": "error", "message": "Workflow ID is required"}
                
            # Get workflow
            if workflow_id not in self.workflows:
                return {"status": "error", "message": f"Workflow {workflow_id} not found"}
                
            workflow = self.workflows.pop(workflow_id)
                
            return {
                "status": "success",
                "message": "Workflow deleted successfully",
                "workflow_id": workflow_id,
                "workflow": workflow
            }
            
        except Exception as e:
            logger.error(f"Error deleting workflow: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def execute_workflow(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Workflow service is not initialized"}
                
            # Check if workflows are enabled
            if not self.workflows_enabled:
                return {"status": "error", "message": "Workflows are disabled"}
                
            # Get workflow parameters
            workflow_id = data.get("workflow_id") if data else None
            name = data.get("name") if data else None
            input_data = data.get("input_data", {}) if data else {}
            
            # Validate parameters
            if not workflow_id and not name:
                return {"status": "error", "message": "Workflow ID or name is required"}
                
            # Get workflow
            workflow = None
            if workflow_id:
                if workflow_id in self.workflows:
                    workflow = self.workflows[workflow_id]
            elif name:
                # Search for workflow by name
                for w in self.workflows.values():
                    if w["name"] == name:
                        workflow = w
                        break
                            
            if not workflow:
                return {"status": "error", "message": "Workflow not found"}
                
            # Create workflow execution
            execution_id = str(uuid.uuid4())
            workflow_execution = {
                "execution_id": execution_id,
                "workflow_id": workflow["workflow_id"],
                "workflow_name": workflow["name"],
                "status": "running",
                "input_data": input_data,
                "output_data": {},
                "step_results": [],
                "current_step": 0,
                "created_at": datetime.now().isoformat(),
                "context": context or {}
            }
            
            # Add workflow execution to workflow executions
            self.workflow_executions.append(workflow_execution)
            
            # Execute workflow
            result = await self._execute_workflow(workflow, workflow_execution, input_data, context)
            
            # Update workflow execution
            workflow_execution["status"] = result.get("status", "completed")
            workflow_execution["output_data"] = result.get("output_data", {})
            workflow_execution["step_results"] = result.get("step_results", [])
            workflow_execution["completed_at"] = datetime.now().isoformat()
            workflow_execution["result"] = result
            
            return {
                "status": "success",
                "message": "Workflow executed successfully",
                "execution_id": execution_id,
                "workflow_id": workflow["workflow_id"],
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _execute_workflow(self, workflow: Dict[str, Any], workflow_execution: Dict[str, Any], input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a workflow."""
        # In a real implementation, this would execute a workflow
        logger.info(f"Executing workflow {workflow['workflow_id']} with name: {workflow['name']}")
        
        # Get workflow details
        workflow_id = workflow["workflow_id"]
        workflow_name = workflow["name"]
        steps = workflow["steps"]
        
        # Execute workflow steps
        step_results = []
        current_output = input_data
        
        for i, step in enumerate(steps):
            # Update current step
            workflow_execution["current_step"] = i + 1
            
            # Execute step
            step_result = await self._execute_step(step, current_output, context)
            step_results.append(step_result)
            
            # Update current output
            current_output = step_result.get("output_data", {})
            
            # Check if step failed
            if step_result.get("status") == "failed":
                return {
                    "workflow_id": workflow_id,
                    "workflow_name": workflow_name,
                    "status": "failed",
                    "message": f"Workflow failed at step {i+1}",
                    "step_results": step_results,
                    "output_data": current_output
                }
                
        # Return workflow execution result
        result = {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "status": "completed",
            "message": f"Workflow {workflow_name} executed successfully",
            "step_results": step_results,
            "output_data": current_output,
            "execution_time": 5.0  # Simulated execution time
        }
        
        return result
    
    async def _execute_step(self, step: Dict[str, Any], input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a workflow step."""
        # In a real implementation, this would execute a workflow step
        logger.info(f"Executing step: {step.get('name', 'Unnamed step')}")
        
        # Get step details
        step_name = step.get("name", "Unnamed step")
        step_type = step.get("type", "unknown")
        step_config = step.get("config", {})
        
        # Simulate step execution
        await asyncio.sleep(1)
        
        # Return step result
        result = {
            "step_name": step_name,
            "step_type": step_type,
            "status": "completed",
            "message": f"Step {step_name} executed successfully",
            "input_data": input_data,
            "output_data": {
                "step_output": f"Output from step {step_name}",
                "timestamp": datetime.now().isoformat()
            },
            "execution_time": 1.0  # Simulated execution time
        }
        
        return result
    
    async def list_workflows(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List workflows.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Workflow service is not initialized"}
                
            # Get list parameters
            status = data.get("status") if data else None
            limit = data.get("limit", 100) if data else 100
            offset = data.get("offset", 0) if data else 0
            
            # Get all workflows
            all_workflows = list(self.workflows.values())
                
            # Filter workflows based on parameters
            filtered_workflows = []
            for workflow in all_workflows:
                if status and workflow["status"] != status:
                    continue
                filtered_workflows.append(workflow)
                
            # Sort workflows by creation time (newest first)
            filtered_workflows.sort(key=lambda x: x["created_at"], reverse=True)
                
            # Apply pagination
            paginated_workflows = filtered_workflows[offset:offset+limit]
            
            return {
                "status": "success",
                "message": "Workflows listed successfully",
                "total_count": len(filtered_workflows),
                "limit": limit,
                "offset": offset,
                "workflows": paginated_workflows
            }
            
        except Exception as e:
            logger.error(f"Error listing workflows: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def list_workflow_executions(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List workflow executions.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Workflow service is not initialized"}
                
            # Get list parameters
            workflow_id = data.get("workflow_id") if data else None
            status = data.get("status") if data else None
            limit = data.get("limit", 100) if data else 100
            offset = data.get("offset", 0) if data else 0
            
            # Get all workflow executions
            all_executions = self.workflow_executions
                
            # Filter workflow executions based on parameters
            filtered_executions = []
            for execution in all_executions:
                if workflow_id and execution["workflow_id"] != workflow_id:
                    continue
                if status and execution["status"] != status:
                    continue
                filtered_executions.append(execution)
                
            # Sort workflow executions by creation time (newest first)
            filtered_executions.sort(key=lambda x: x["created_at"], reverse=True)
                
            # Apply pagination
            paginated_executions = filtered_executions[offset:offset+limit]
            
            return {
                "status": "success",
                "message": "Workflow executions listed successfully",
                "total_count": len(filtered_executions),
                "limit": limit,
                "offset": offset,
                "workflow_executions": paginated_executions
            }
            
        except Exception as e:
            logger.error(f"Error listing workflow executions: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def search_workflows(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search workflows.
        
        Args:
            data: Optional data for the operation
            context: Optional context for operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Workflow service is not initialized"}
                
            # Get search parameters
            query = data.get("query") if data else None
            status = data.get("status") if data else None
            start_time = data.get("start_time") if data else None
            end_time = data.get("end_time") if data else None
            limit = data.get("limit", 100) if data else 100
            offset = data.get("offset", 0) if data else 0
            
            if not query:
                return {"status": "error", "message": "Query is required for search"}
                
            # Get all workflows
            all_workflows = list(self.workflows.values())
                
            # Search workflows based on query
            matched_workflows = []
            for workflow in all_workflows:
                # Check if workflow matches query
                workflow_json = json.dumps(workflow, default=str)
                if query.lower() in workflow_json.lower():
                    # Check additional filters
                    if status and workflow["status"] != status:
                        continue
                    if start_time and workflow["created_at"] < start_time:
                        continue
                    if end_time and workflow["created_at"] > end_time:
                        continue
                    matched_workflows.append(workflow)
                    
            # Sort workflows by creation time (newest first)
            matched_workflows.sort(key=lambda x: x["created_at"], reverse=True)
                
            # Apply pagination
            paginated_workflows = matched_workflows[offset:offset+limit]
            
            return {
                "status": "success",
                "message": "Workflows searched successfully",
                "query": query,
                "total_count": len(matched_workflows),
                "limit": limit,
                "offset": offset,
                "workflows": paginated_workflows
            }
            
        except Exception as e:
            logger.error(f"Error searching workflows: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_workflow_execution(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a workflow execution.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Workflow service is not initialized"}
                
            # Get execution parameters
            execution_id = data.get("execution_id") if data else None
            
            # Validate execution_id
            if not execution_id:
                return {"status": "error", "message": "Execution ID is required"}
                
            # Get workflow execution
            workflow_execution = None
            for execution in self.workflow_executions:
                if execution["execution_id"] == execution_id:
                    workflow_execution = execution
                    break
                    
            if not workflow_execution:
                return {"status": "error", "message": f"Workflow execution {execution_id} not found"}
                
            return {
                "status": "success",
                "message": "Workflow execution retrieved successfully",
                "execution_id": execution_id,
                "workflow_execution": workflow_execution
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow execution: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_status(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get the status of the workflow service.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the status information
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Workflow service is not initialized"}
                
            status = {
                "workflows_enabled": self.workflows_enabled,
                "is_running": self._is_running,
                "workflows_count": len(self.workflows),
                "workflow_executions_count": len(self.workflow_executions),
                "max_workflows": self.max_workflows,
                "max_workflow_steps": self.max_workflow_steps,
                "workflow_timeout": self.workflow_timeout
            }
            
            return {
                "status": "success",
                "message": "Workflow status retrieved successfully",
                "workflow_status": status
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_stats(self, data: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get statistics for the workflow service.
        
        Args:
            data: Optional data for the operation
            context: Optional context for the operation
            
        Returns:
            Dictionary containing the statistics
        """
        try:
            if not self._is_initialized:
                return {"status": "error", "message": "Workflow service is not initialized"}
                
            # Get all workflows
            all_workflows = list(self.workflows.values())
                
            # Count by status
            status_counts = {}
            for workflow in all_workflows:
                status = workflow["status"]
                if status not in status_counts:
                    status_counts[status] = 0
                status_counts[status] += 1
                
            # Get all workflow executions
            all_executions = self.workflow_executions
                
            # Count executions by status
            execution_status_counts = {}
            for execution in all_executions:
                status = execution["status"]
                if status not in execution_status_counts:
                    execution_status_counts[status] = 0
                execution_status_counts[status] += 1
                
            # Calculate average execution time for completed workflow executions
            completed_executions = [e for e in all_executions if e["status"] == "completed"]
            total_execution_time = 0
            for execution in completed_executions:
                if "created_at" in execution and "completed_at" in execution:
                    start_time = datetime.fromisoformat(execution["created_at"])
                    end_time = datetime.fromisoformat(execution["completed_at"])
                    execution_time = (end_time - start_time).total_seconds()
                    total_execution_time += execution_time
                    
            average_execution_time = total_execution_time / len(completed_executions) if completed_executions else 0
            
            # Calculate average steps per workflow
            total_steps = sum(len(workflow["steps"]) for workflow in all_workflows)
            average_steps = total_steps / len(all_workflows) if all_workflows else 0
            
            stats = {
                "workflows_enabled": self.workflows_enabled,
                "is_running": self._is_running,
                "total_workflows": len(all_workflows),
                "workflow_executions_count": len(all_executions),
                "completed_executions_count": len(completed_executions),
                "max_workflows": self.max_workflows,
                "max_workflow_steps": self.max_workflow_steps,
                "workflow_timeout": self.workflow_timeout,
                "status_counts": status_counts,
                "execution_status_counts": execution_status_counts,
                "average_execution_time": average_execution_time,
                "average_steps": average_steps
            }
            
            return {
                "status": "success",
                "message": "Workflow statistics retrieved successfully",
                "workflow_stats": stats
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow statistics: {str(e)}")
            return {"status": "error", "message": str(e)}