"""
Prompt-Driven Automation Extension - AI-Native Workflow Automation

This extension represents Kari's answer to N8N, but powered by AI understanding rather than 
visual workflow builders. It can:
- Understand natural language workflow descriptions
- Automatically discover and configure available plugins
- Self-adapt workflows based on execution results
- Learn from user feedback to improve automation

Example: "Monitor our GitHub repo and notify Slack when tests fail"
-> AI discovers GitHub and Slack plugins, configures the workflow automatically
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ai_karen_engine.extensions.base import BaseExtension
from ai_karen_engine.hooks.hook_mixin import HookMixin

# Import the original automation components
from ai_karen_engine.automation_manager import get_automation_manager

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"


class WorkflowStep(BaseModel):
    """Individual step in a workflow."""
    id: str
    plugin: str
    params: Dict[str, Any]
    conditions: Optional[Dict[str, Any]] = None
    retry_config: Optional[Dict[str, Any]] = None


class Workflow(BaseModel):
    """Workflow definition."""
    id: str
    name: str
    description: str
    prompt: str  # Original natural language description
    steps: List[WorkflowStep]
    triggers: List[Dict[str, Any]]
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: str
    updated_at: str
    execution_count: int = 0
    success_rate: float = 0.0


class WorkflowRequest(BaseModel):
    """Request to create a workflow from natural language."""
    prompt: str
    name: Optional[str] = None
    triggers: Optional[List[Dict[str, Any]]] = None


class ExecutionRequest(BaseModel):
    """Request to execute a workflow."""
    workflow_id: str
    input_data: Optional[Dict[str, Any]] = None
    dry_run: bool = False


class PromptDrivenAutomationExtension(BaseExtension, HookMixin):
    """Prompt-Driven Automation Extension - AI-Native Workflow Platform."""
    
    async def _initialize(self) -> None:
        """Initialize the Prompt-Driven Automation Extension."""
        self.logger.info("Prompt-Driven Automation Extension initializing...")
        
        # Initialize workflow storage
        self.workflows: Dict[str, Workflow] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.plugin_capabilities: Dict[str, Dict[str, Any]] = {}
        self.workflow_templates: Dict[str, Dict[str, Any]] = {}
        
        # Get automation manager from the original system
        self.automation_manager = get_automation_manager()
        
        # Discover available plugins
        await self._discover_plugin_capabilities()
        
        # Load workflow templates
        await self._load_workflow_templates()
        
        # Set up MCP tools for AI integration
        await self._setup_mcp_tools()
        
        # Register hooks for learning and adaptation
        await self._register_learning_hooks()
        
        self.logger.info("Prompt-Driven Automation Extension initialized successfully")
    
    async def _discover_plugin_capabilities(self) -> None:
        """Discover available plugins and their capabilities."""
        try:
            # This would typically query the plugin router for available plugins
            # For now, we'll simulate with common plugin types
            default_plugins = {
                "github_integration": {
                    "description": "GitHub repository monitoring and management",
                    "capabilities": ["monitor_repo", "get_issues", "create_pr", "check_status"],
                    "inputs": ["repo_url", "token", "branch"],
                    "outputs": ["status", "data", "events"]
                },
                "slack_notifier": {
                    "description": "Slack messaging and notifications",
                    "capabilities": ["send_message", "create_channel", "get_users"],
                    "inputs": ["channel", "message", "webhook_url"],
                    "outputs": ["message_id", "status"]
                },
                "email_sender": {
                    "description": "Email sending and management",
                    "capabilities": ["send_email", "send_bulk", "get_templates"],
                    "inputs": ["to", "subject", "body", "attachments"],
                    "outputs": ["message_id", "delivery_status"]
                },
                "file_processor": {
                    "description": "File processing and manipulation",
                    "capabilities": ["read_file", "write_file", "convert_format", "extract_data"],
                    "inputs": ["file_path", "format", "options"],
                    "outputs": ["processed_data", "file_path"]
                },
                "time_query": {
                    "description": "Time and date operations",
                    "capabilities": ["get_time", "format_date", "calculate_duration"],
                    "inputs": ["timezone", "format"],
                    "outputs": ["timestamp", "formatted_time"]
                },
                "web_scraper": {
                    "description": "Web scraping and data extraction",
                    "capabilities": ["scrape_page", "monitor_changes", "extract_data"],
                    "inputs": ["url", "selectors", "frequency"],
                    "outputs": ["scraped_data", "changes"]
                }
            }
            
            self.plugin_capabilities.update(default_plugins)
            self.logger.info(f"Discovered {len(default_plugins)} plugin capabilities")
            
        except Exception as e:
            self.logger.error(f"Failed to discover plugin capabilities: {e}")
    
    async def _load_workflow_templates(self) -> None:
        """Load common workflow templates for quick setup."""
        templates = {
            "github_slack_monitoring": {
                "name": "GitHub to Slack Monitoring",
                "description": "Monitor GitHub repository and send Slack notifications",
                "pattern": r"monitor.*github.*slack|github.*notify.*slack",
                "plugins": ["github_integration", "slack_notifier"],
                "template": {
                    "steps": [
                        {
                            "id": "monitor_repo",
                            "plugin": "github_integration",
                            "params": {"action": "monitor_repo", "events": ["push", "pr", "issues"]},
                            "conditions": {"on_change": True}
                        },
                        {
                            "id": "notify_slack",
                            "plugin": "slack_notifier",
                            "params": {"action": "send_message", "message": "{{previous.event_data}}"},
                            "conditions": {"if": "{{previous.success}}"}
                        }
                    ]
                }
            },
            "file_processing_pipeline": {
                "name": "File Processing Pipeline",
                "description": "Process files and send email notifications",
                "pattern": r"process.*file.*email|file.*process.*notify",
                "plugins": ["file_processor", "email_sender"],
                "template": {
                    "steps": [
                        {
                            "id": "process_file",
                            "plugin": "file_processor",
                            "params": {"action": "extract_data"},
                            "retry_config": {"max_retries": 3, "delay": 60}
                        },
                        {
                            "id": "send_notification",
                            "plugin": "email_sender",
                            "params": {"action": "send_email", "subject": "File processed", "body": "{{previous.summary}}"},
                            "conditions": {"if": "{{previous.success}}"}
                        }
                    ]
                }
            },
            "web_monitoring": {
                "name": "Web Content Monitoring",
                "description": "Monitor web pages for changes and notify",
                "pattern": r"monitor.*web.*notify|web.*changes.*alert",
                "plugins": ["web_scraper", "slack_notifier", "email_sender"],
                "template": {
                    "steps": [
                        {
                            "id": "scrape_page",
                            "plugin": "web_scraper",
                            "params": {"action": "monitor_changes"},
                            "conditions": {"schedule": "*/30 * * * *"}
                        },
                        {
                            "id": "notify_changes",
                            "plugin": "slack_notifier",
                            "params": {"action": "send_message", "message": "Changes detected: {{previous.changes}}"},
                            "conditions": {"if": "{{previous.has_changes}}"}
                        }
                    ]
                }
            }
        }
        
        self.workflow_templates.update(templates)
        self.logger.info(f"Loaded {len(templates)} workflow templates")
    
    async def _setup_mcp_tools(self) -> None:
        """Set up MCP tools for AI-powered automation."""
        mcp_server = self.create_mcp_server()
        if mcp_server:
            # Register automation tools
            await self.register_mcp_tool(
                name="create_workflow_from_prompt",
                handler=self._create_workflow_from_prompt_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Natural language description of the workflow"},
                        "name": {"type": "string", "description": "Optional workflow name"},
                        "triggers": {"type": "array", "description": "Optional trigger configuration"}
                    },
                    "required": ["prompt"]
                },
                description="Create a workflow from natural language description"
            )
            
            await self.register_mcp_tool(
                name="discover_plugins_for_task",
                handler=self._discover_plugins_for_task_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "task_description": {"type": "string", "description": "Description of the task"},
                        "required_capabilities": {"type": "array", "items": {"type": "string"}, "description": "Required capabilities"}
                    },
                    "required": ["task_description"]
                },
                description="Discover suitable plugins for a specific task"
            )
            
            await self.register_mcp_tool(
                name="optimize_workflow",
                handler=self._optimize_workflow_tool,
                schema={
                    "type": "object",
                    "properties": {
                        "workflow_id": {"type": "string", "description": "Workflow to optimize"},
                        "optimization_goal": {"type": "string", "enum": ["speed", "reliability", "cost", "accuracy"], "description": "Optimization target"}
                    },
                    "required": ["workflow_id", "optimization_goal"]
                },
                description="Optimize an existing workflow based on execution history"
            )
    
    async def _register_learning_hooks(self) -> None:
        """Register hooks for learning and adaptation."""
        try:
            await self.register_hook(
                'workflow_execution_complete',
                self._learn_from_execution,
                priority=90
            )
            
            await self.register_hook(
                'workflow_execution_failed',
                self._adapt_from_failure,
                priority=90
            )
            
            self.logger.info("Learning hooks registered")
            
        except Exception as e:
            self.logger.error(f"Failed to register learning hooks: {e}")
    
    async def _create_workflow_from_prompt_tool(self, prompt: str, name: Optional[str] = None, triggers: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """MCP tool to create workflows from natural language prompts."""
        try:
            # Use AI to analyze the prompt and understand the intent
            analysis_result = await self.plugin_orchestrator.execute_plugin(
                intent="analyze_text",
                params={
                    "text": prompt,
                    "analysis_type": "workflow_intent"
                },
                user_context={"roles": ["user"]}
            )
            
            # Extract workflow components from the analysis
            workflow_intent = analysis_result.get("intent", "general") if analysis_result else "general"
            entities = analysis_result.get("entities", []) if analysis_result else []
            
            # Find matching template
            matching_template = self._find_matching_template(prompt, workflow_intent)
            
            # Generate workflow steps
            workflow_steps = await self._generate_workflow_steps(prompt, entities, matching_template)
            
            # Create workflow
            workflow_id = f"workflow_{len(self.workflows) + 1}"
            workflow = Workflow(
                id=workflow_id,
                name=name or f"Workflow from: {prompt[:50]}...",
                description=prompt,
                prompt=prompt,
                steps=workflow_steps,
                triggers=triggers or [{"type": "manual"}],
                status=WorkflowStatus.DRAFT,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            )
            
            self.workflows[workflow_id] = workflow
            
            return {
                "success": True,
                "workflow": workflow.dict(),
                "message": f"Workflow '{workflow.name}' created successfully",
                "analysis": {
                    "intent": workflow_intent,
                    "entities": entities,
                    "template_used": matching_template["name"] if matching_template else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow from prompt: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _discover_plugins_for_task_tool(self, task_description: str, required_capabilities: Optional[List[str]] = None) -> Dict[str, Any]:
        """MCP tool to discover suitable plugins for a task."""
        try:
            # Use AI to analyze the task and extract requirements
            analysis_result = await self.plugin_orchestrator.execute_plugin(
                intent="analyze_text",
                params={
                    "text": task_description,
                    "analysis_type": "capability_extraction"
                },
                user_context={"roles": ["user"]}
            )
            
            extracted_capabilities = analysis_result.get("capabilities", []) if analysis_result else []
            all_capabilities = list(set(extracted_capabilities + (required_capabilities or [])))
            
            # Find matching plugins
            suitable_plugins = []
            for plugin_name, plugin_info in self.plugin_capabilities.items():
                plugin_capabilities = plugin_info.get("capabilities", [])
                
                # Calculate match score
                matches = len(set(all_capabilities) & set(plugin_capabilities))
                if matches > 0:
                    score = matches / len(all_capabilities) if all_capabilities else 0
                    suitable_plugins.append({
                        "plugin": plugin_name,
                        "description": plugin_info.get("description", ""),
                        "capabilities": plugin_capabilities,
                        "match_score": score,
                        "matched_capabilities": list(set(all_capabilities) & set(plugin_capabilities))
                    })
            
            # Sort by match score
            suitable_plugins.sort(key=lambda x: x["match_score"], reverse=True)
            
            return {
                "success": True,
                "task_description": task_description,
                "required_capabilities": all_capabilities,
                "suitable_plugins": suitable_plugins[:5],  # Top 5 matches
                "total_plugins_found": len(suitable_plugins)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to discover plugins for task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _optimize_workflow_tool(self, workflow_id: str, optimization_goal: str) -> Dict[str, Any]:
        """MCP tool to optimize workflows based on execution history."""
        try:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                return {
                    "success": False,
                    "error": f"Workflow '{workflow_id}' not found"
                }
            
            # Analyze execution history for this workflow
            workflow_executions = [
                exec_record for exec_record in self.execution_history
                if exec_record.get("workflow_id") == workflow_id
            ]
            
            if not workflow_executions:
                return {
                    "success": False,
                    "error": "No execution history available for optimization"
                }
            
            # Generate optimization recommendations
            optimizations = self._generate_optimization_recommendations(
                workflow, workflow_executions, optimization_goal
            )
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "optimization_goal": optimization_goal,
                "current_performance": {
                    "execution_count": len(workflow_executions),
                    "success_rate": workflow.success_rate,
                    "avg_duration": sum(e.get("duration", 0) for e in workflow_executions) / len(workflow_executions)
                },
                "optimizations": optimizations
            }
            
        except Exception as e:
            self.logger.error(f"Failed to optimize workflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _find_matching_template(self, prompt: str, intent: str) -> Optional[Dict[str, Any]]:
        """Find the best matching workflow template for a prompt."""
        import re
        
        best_match = None
        best_score = 0
        
        for template_id, template in self.workflow_templates.items():
            pattern = template.get("pattern", "")
            if pattern and re.search(pattern, prompt.lower()):
                # Simple scoring based on pattern match and intent
                score = 1.0
                if intent in template.get("description", "").lower():
                    score += 0.5
                
                if score > best_score:
                    best_score = score
                    best_match = template
        
        return best_match
    
    async def _generate_workflow_steps(self, prompt: str, entities: List[str], template: Optional[Dict[str, Any]] = None) -> List[WorkflowStep]:
        """Generate workflow steps based on prompt analysis."""
        steps = []
        
        if template:
            # Use template as base
            template_steps = template.get("template", {}).get("steps", [])
            for i, step_template in enumerate(template_steps):
                step = WorkflowStep(
                    id=step_template["id"],
                    plugin=step_template["plugin"],
                    params=step_template["params"],
                    conditions=step_template.get("conditions"),
                    retry_config=step_template.get("retry_config")
                )
                steps.append(step)
        else:
            # Generate steps from scratch based on entities and available plugins
            # This is a simplified implementation - in practice, this would use more sophisticated AI
            
            # Try to identify action words and map to plugins
            action_words = ["monitor", "send", "notify", "process", "check", "create", "update"]
            service_words = ["github", "slack", "email", "file", "web", "database"]
            
            prompt_lower = prompt.lower()
            identified_actions = [word for word in action_words if word in prompt_lower]
            identified_services = [word for word in service_words if word in prompt_lower]
            
            # Create basic steps based on identified patterns
            step_counter = 1
            for service in identified_services:
                for action in identified_actions:
                    # Find suitable plugin
                    suitable_plugin = self._find_plugin_for_service_action(service, action)
                    if suitable_plugin:
                        step = WorkflowStep(
                            id=f"step_{step_counter}",
                            plugin=suitable_plugin,
                            params={"action": action, "service": service},
                            conditions={"if": f"{{previous.success}}"} if step_counter > 1 else None
                        )
                        steps.append(step)
                        step_counter += 1
        
        return steps
    
    def _find_plugin_for_service_action(self, service: str, action: str) -> Optional[str]:
        """Find the best plugin for a service and action combination."""
        service_plugin_map = {
            "github": "github_integration",
            "slack": "slack_notifier",
            "email": "email_sender",
            "file": "file_processor",
            "web": "web_scraper",
            "time": "time_query"
        }
        
        return service_plugin_map.get(service)
    
    def _generate_optimization_recommendations(self, workflow: Workflow, executions: List[Dict[str, Any]], goal: str) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on execution history."""
        recommendations = []
        
        # Analyze execution patterns
        failed_executions = [e for e in executions if not e.get("success", False)]
        avg_duration = sum(e.get("duration", 0) for e in executions) / len(executions)
        
        if goal == "reliability" and failed_executions:
            # Recommend retry configurations
            failing_steps = {}
            for execution in failed_executions:
                failed_step = execution.get("failed_step")
                if failed_step:
                    failing_steps[failed_step] = failing_steps.get(failed_step, 0) + 1
            
            for step_id, failure_count in failing_steps.items():
                recommendations.append({
                    "type": "add_retry_config",
                    "step_id": step_id,
                    "description": f"Add retry configuration to step '{step_id}' (failed {failure_count} times)",
                    "config": {"max_retries": 3, "delay": 60, "backoff": "exponential"}
                })
        
        elif goal == "speed" and avg_duration > 300:  # > 5 minutes
            # Recommend parallel execution where possible
            recommendations.append({
                "type": "parallelize_steps",
                "description": "Consider running independent steps in parallel",
                "potential_savings": f"Could reduce execution time by up to 30%"
            })
        
        elif goal == "cost":
            # Recommend resource optimization
            recommendations.append({
                "type": "optimize_resources",
                "description": "Consider using more cost-effective plugins or reducing execution frequency",
                "suggestion": "Review plugin usage and consider alternatives"
            })
        
        if not recommendations:
            recommendations.append({
                "type": "no_optimization_needed",
                "description": f"Workflow is already optimized for {goal}",
                "current_performance": "Within acceptable ranges"
            })
        
        return recommendations
    
    async def _learn_from_execution(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook to learn from successful workflow executions."""
        try:
            execution_data = context.get("execution", {})
            workflow_id = execution_data.get("workflow_id")
            
            if workflow_id and workflow_id in self.workflows:
                workflow = self.workflows[workflow_id]
                
                # Update success metrics
                workflow.execution_count += 1
                if execution_data.get("success", False):
                    # Update success rate using exponential moving average
                    workflow.success_rate = workflow.success_rate * 0.9 + 0.1
                
                # Store execution record
                execution_record = {
                    "workflow_id": workflow_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": execution_data.get("success", False),
                    "duration": execution_data.get("duration", 0),
                    "steps_executed": execution_data.get("steps_executed", []),
                    "output": execution_data.get("output")
                }
                self.execution_history.append(execution_record)
                
                # Keep only recent history (last 1000 executions)
                if len(self.execution_history) > 1000:
                    self.execution_history = self.execution_history[-1000:]
            
            return {"success": True, "learning_applied": True}
            
        except Exception as e:
            self.logger.error(f"Failed to learn from execution: {e}")
            return {"success": False, "error": str(e)}
    
    async def _adapt_from_failure(self, context: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook to adapt workflows based on failures."""
        try:
            failure_data = context.get("failure", {})
            workflow_id = failure_data.get("workflow_id")
            
            if workflow_id and workflow_id in self.workflows:
                workflow = self.workflows[workflow_id]
                
                # Update failure metrics
                workflow.success_rate = max(workflow.success_rate * 0.9, 0.0)
                
                # Analyze failure and suggest adaptations
                failed_step = failure_data.get("failed_step")
                error_type = failure_data.get("error_type", "unknown")
                
                # Store failure record with more details
                failure_record = {
                    "workflow_id": workflow_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": False,
                    "failed_step": failed_step,
                    "error_type": error_type,
                    "error_message": failure_data.get("error_message"),
                    "duration": failure_data.get("duration", 0)
                }
                self.execution_history.append(failure_record)
                
                # Auto-adapt based on failure patterns
                if error_type == "timeout" and failed_step:
                    # Suggest increasing timeout or adding retry
                    self.logger.info(f"Suggesting timeout increase for step {failed_step} in workflow {workflow_id}")
                elif error_type == "network_error":
                    # Suggest retry with backoff
                    self.logger.info(f"Suggesting retry configuration for network errors in workflow {workflow_id}")
            
            return {"success": True, "adaptation_applied": True}
            
        except Exception as e:
            self.logger.error(f"Failed to adapt from failure: {e}")
            return {"success": False, "error": str(e)}
    
    async def execute_workflow(self, workflow_id: str, input_data: Optional[Dict[str, Any]] = None, dry_run: bool = False) -> Dict[str, Any]:
        """Execute a workflow with monitoring and error handling."""
        try:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                return {"success": False, "error": f"Workflow '{workflow_id}' not found"}
            
            if workflow.status not in [WorkflowStatus.ACTIVE, WorkflowStatus.DRAFT]:
                return {"success": False, "error": f"Workflow is in '{workflow.status}' status and cannot be executed"}
            
            execution_id = f"exec_{workflow_id}_{int(datetime.utcnow().timestamp())}"
            start_time = datetime.utcnow()
            
            self.logger.info(f"Starting workflow execution: {execution_id}")
            
            # Initialize execution context
            execution_context = {
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "input_data": input_data or {},
                "dry_run": dry_run,
                "start_time": start_time.isoformat(),
                "steps_executed": [],
                "current_data": input_data or {}
            }
            
            # Execute workflow steps
            for i, step in enumerate(workflow.steps):
                step_start_time = datetime.utcnow()
                
                try:
                    # Check step conditions
                    if step.conditions and not self._evaluate_conditions(step.conditions, execution_context):
                        self.logger.info(f"Skipping step {step.id} due to conditions")
                        continue
                    
                    # Execute step
                    if not dry_run:
                        step_result = await self._execute_workflow_step(step, execution_context)
                    else:
                        step_result = {"success": True, "data": {"dry_run": True}, "message": "Dry run - step not executed"}
                    
                    step_duration = (datetime.utcnow() - step_start_time).total_seconds()
                    
                    # Record step execution
                    step_record = {
                        "step_id": step.id,
                        "plugin": step.plugin,
                        "success": step_result.get("success", False),
                        "duration": step_duration,
                        "output": step_result.get("data"),
                        "message": step_result.get("message", "")
                    }
                    execution_context["steps_executed"].append(step_record)
                    
                    # Update current data with step output
                    if step_result.get("success") and step_result.get("data"):
                        execution_context["current_data"].update(step_result["data"])
                    
                    # Handle step failure
                    if not step_result.get("success"):
                        if step.retry_config:
                            # Implement retry logic
                            retry_result = await self._retry_step(step, execution_context, step_result)
                            if retry_result.get("success"):
                                step_record.update(retry_result)
                                execution_context["current_data"].update(retry_result.get("data", {}))
                            else:
                                # Step failed after retries
                                execution_context["failed_step"] = step.id
                                execution_context["error"] = retry_result.get("error", "Step failed after retries")
                                break
                        else:
                            # No retry config, fail immediately
                            execution_context["failed_step"] = step.id
                            execution_context["error"] = step_result.get("error", "Step failed")
                            break
                
                except Exception as e:
                    self.logger.error(f"Error executing step {step.id}: {e}")
                    execution_context["failed_step"] = step.id
                    execution_context["error"] = str(e)
                    break
            
            # Calculate execution results
            end_time = datetime.utcnow()
            total_duration = (end_time - start_time).total_seconds()
            success = "failed_step" not in execution_context
            
            execution_result = {
                "success": success,
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "duration": total_duration,
                "steps_executed": len(execution_context["steps_executed"]),
                "output": execution_context["current_data"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "dry_run": dry_run
            }
            
            if not success:
                execution_result.update({
                    "failed_step": execution_context.get("failed_step"),
                    "error": execution_context.get("error")
                })
            
            # Update workflow metrics
            if not dry_run:
                workflow.execution_count += 1
                if success:
                    workflow.success_rate = workflow.success_rate * 0.9 + 0.1
                else:
                    workflow.success_rate = max(workflow.success_rate * 0.9, 0.0)
                workflow.updated_at = datetime.utcnow().isoformat()
            
            # Store execution record
            self.execution_history.append(execution_result)
            
            # Trigger learning hooks
            if success:
                await self.trigger_hook('workflow_execution_complete', {"execution": execution_result}, {"roles": ["system"]})
            else:
                await self.trigger_hook('workflow_execution_failed', {"failure": execution_result}, {"roles": ["system"]})
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Failed to execute workflow {workflow_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "workflow_id": workflow_id
            }
    
    async def _execute_workflow_step(self, step: WorkflowStep, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step."""
        try:
            # Resolve parameters with context data
            resolved_params = self._resolve_step_parameters(step.params, execution_context)
            
            # Execute the plugin
            result = await self.plugin_orchestrator.execute_plugin(
                intent=step.plugin,
                params=resolved_params,
                user_context={"roles": ["automation"], "workflow_id": execution_context["workflow_id"]}
            )
            
            if result:
                return {
                    "success": True,
                    "data": result,
                    "message": f"Step {step.id} executed successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Plugin {step.plugin} returned no result",
                    "message": f"Step {step.id} failed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Step {step.id} failed with exception"
            }
    
    def _resolve_step_parameters(self, params: Dict[str, Any], execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve step parameters with execution context data."""
        resolved = {}
        
        for key, value in params.items():
            if isinstance(value, str) and "{{" in value and "}}" in value:
                # Simple template resolution
                resolved_value = value
                
                # Replace {{previous.field}} with data from previous steps
                if "{{previous." in value:
                    if execution_context["steps_executed"]:
                        last_step = execution_context["steps_executed"][-1]
                        last_output = last_step.get("output", {})
                        
                        # Simple field extraction
                        import re
                        matches = re.findall(r'\{\{previous\.(\w+)\}\}', value)
                        for match in matches:
                            field_value = last_output.get(match, "")
                            resolved_value = resolved_value.replace(f"{{{{previous.{match}}}}}", str(field_value))
                
                # Replace {{input.field}} with input data
                if "{{input." in value:
                    import re
                    matches = re.findall(r'\{\{input\.(\w+)\}\}', value)
                    for match in matches:
                        field_value = execution_context["input_data"].get(match, "")
                        resolved_value = resolved_value.replace(f"{{{{input.{match}}}}}", str(field_value))
                
                resolved[key] = resolved_value
            else:
                resolved[key] = value
        
        return resolved
    
    def _evaluate_conditions(self, conditions: Dict[str, Any], execution_context: Dict[str, Any]) -> bool:
        """Evaluate step conditions."""
        try:
            # Simple condition evaluation
            if "if" in conditions:
                condition = conditions["if"]
                
                # Handle {{previous.success}} conditions
                if "{{previous.success}}" in condition:
                    if execution_context["steps_executed"]:
                        last_step = execution_context["steps_executed"][-1]
                        return last_step.get("success", False)
                    return False
                
                # Handle other simple conditions
                if condition == "true":
                    return True
                elif condition == "false":
                    return False
            
            # Handle schedule conditions (for background execution)
            if "schedule" in conditions:
                # This would be handled by the scheduler
                return True
            
            # Handle on_change conditions
            if "on_change" in conditions:
                return conditions["on_change"]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error evaluating conditions: {e}")
            return False
    
    async def _retry_step(self, step: WorkflowStep, execution_context: Dict[str, Any], original_result: Dict[str, Any]) -> Dict[str, Any]:
        """Retry a failed step according to its retry configuration."""
        retry_config = step.retry_config or {}
        max_retries = retry_config.get("max_retries", 3)
        delay = retry_config.get("delay", 60)
        backoff = retry_config.get("backoff", "linear")
        
        for attempt in range(max_retries):
            self.logger.info(f"Retrying step {step.id}, attempt {attempt + 1}/{max_retries}")
            
            # Calculate delay
            if backoff == "exponential":
                actual_delay = delay * (2 ** attempt)
            else:
                actual_delay = delay * (attempt + 1)
            
            # Wait before retry
            await asyncio.sleep(actual_delay)
            
            # Retry the step
            retry_result = await self._execute_workflow_step(step, execution_context)
            
            if retry_result.get("success"):
                self.logger.info(f"Step {step.id} succeeded on retry attempt {attempt + 1}")
                return retry_result
        
        self.logger.error(f"Step {step.id} failed after {max_retries} retry attempts")
        return {
            "success": False,
            "error": f"Step failed after {max_retries} retries",
            "original_error": original_result.get("error"),
            "retries_attempted": max_retries
        }
    
    def create_api_router(self) -> APIRouter:
        """Create API routes for the Prompt-Driven Automation Extension."""
        router = APIRouter(prefix=f"/api/extensions/{self.manifest.name}")
        
        @router.post("/workflows")
        async def create_workflow(request: WorkflowRequest):
            """Create a workflow from natural language prompt."""
            result = await self._create_workflow_from_prompt_tool(
                request.prompt, request.name, request.triggers
            )
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.get("/workflows")
        async def list_workflows():
            """List all workflows."""
            return {
                "workflows": [workflow.dict() for workflow in self.workflows.values()],
                "total": len(self.workflows)
            }
        
        @router.get("/workflows/{workflow_id}")
        async def get_workflow(workflow_id: str):
            """Get a specific workflow."""
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            return workflow.dict()
        
        @router.post("/workflows/{workflow_id}/execute")
        async def execute_workflow_endpoint(workflow_id: str, request: ExecutionRequest):
            """Execute a workflow."""
            result = await self.execute_workflow(
                workflow_id, request.input_data, request.dry_run
            )
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.put("/workflows/{workflow_id}/status")
        async def update_workflow_status(workflow_id: str, status: WorkflowStatus):
            """Update workflow status."""
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            workflow.status = status
            workflow.updated_at = datetime.utcnow().isoformat()
            
            return {"success": True, "workflow": workflow.dict()}
        
        @router.post("/discover")
        async def discover_plugins(task_description: str, required_capabilities: Optional[List[str]] = None):
            """Discover suitable plugins for a task."""
            result = await self._discover_plugins_for_task_tool(task_description, required_capabilities)
            return result
        
        @router.get("/execution-history")
        async def get_execution_history(
            workflow_id: Optional[str] = Query(None),
            limit: int = Query(50, le=1000),
            offset: int = Query(0, ge=0)
        ):
            """Get workflow execution history."""
            history = self.execution_history
            
            if workflow_id:
                history = [e for e in history if e.get("workflow_id") == workflow_id]
            
            # Sort by timestamp (most recent first)
            history.sort(key=lambda x: x.get("start_time", ""), reverse=True)
            
            # Apply pagination
            paginated_history = history[offset:offset + limit]
            
            return {
                "executions": paginated_history,
                "total": len(history),
                "limit": limit,
                "offset": offset
            }
        
        @router.get("/templates")
        async def get_workflow_templates():
            """Get available workflow templates."""
            return {
                "templates": self.workflow_templates,
                "total": len(self.workflow_templates)
            }
        
        @router.post("/workflows/{workflow_id}/optimize")
        async def optimize_workflow(workflow_id: str, optimization_goal: str):
            """Optimize a workflow based on execution history."""
            result = await self._optimize_workflow_tool(workflow_id, optimization_goal)
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            return result
        
        @router.get("/plugins")
        async def get_available_plugins():
            """Get available plugins and their capabilities."""
            return {
                "plugins": self.plugin_capabilities,
                "total": len(self.plugin_capabilities)
            }
        
        @router.get("/metrics")
        async def get_automation_metrics():
            """Get automation system metrics."""
            total_workflows = len(self.workflows)
            active_workflows = len([w for w in self.workflows.values() if w.status == WorkflowStatus.ACTIVE])
            total_executions = len(self.execution_history)
            successful_executions = len([e for e in self.execution_history if e.get("success", False)])
            
            return {
                "total_workflows": total_workflows,
                "active_workflows": active_workflows,
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
                "avg_workflow_success_rate": sum(w.success_rate for w in self.workflows.values()) / total_workflows if total_workflows > 0 else 0
            }
        
        # Register webhook routes
        from .webhooks.webhook_handlers import register_webhook_routes
        register_webhook_routes(router, self)
        
        return router

    
    def create_ui_components(self) -> Dict[str, Any]:
        """Create UI components for the Automation Studio."""
        components = super().create_ui_components()
        
        # Add automation dashboard data
        components["automation_studio"] = {
            "title": "Prompt-Driven Automation Studio",
            "description": "AI-native workflow automation platform",
            "data": {
                "total_workflows": len(self.workflows),
                "active_workflows": len([w for w in self.workflows.values() if w.status == WorkflowStatus.ACTIVE]),
                "total_executions": len(self.execution_history),
                "success_rate": sum(w.success_rate for w in self.workflows.values()) / len(self.workflows) if self.workflows else 0,
                "available_plugins": len(self.plugin_capabilities),
                "workflow_templates": len(self.workflow_templates)
            }
        }
        
        return components
    
    async def _shutdown(self) -> None:
        """Cleanup the Prompt-Driven Automation Extension."""
        self.logger.info("Prompt-Driven Automation Extension shutting down...")
        
        # Save workflow definitions and execution history if needed
        # Clear caches
        self.workflows.clear()
        self.execution_history.clear()
        self.plugin_capabilities.clear()
        self.workflow_templates.clear()
        
        self.logger.info("Prompt-Driven Automation Extension shut down successfully")


# Export the extension class
__all__ = ["PromptDrivenAutomationExtension"]