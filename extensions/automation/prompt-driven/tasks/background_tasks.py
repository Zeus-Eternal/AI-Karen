"""
Background tasks for workflow execution and plugin discovery.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from ai_karen_engine.extensions.base import BaseExtension

logger = logging.getLogger(__name__)


async def execute_scheduled_workflows(extension: BaseExtension) -> Dict[str, Any]:
    """
    Background task to execute workflows that are scheduled to run.
    This task runs every minute and checks for workflows that need execution.
    """
    try:
        logger.info("Checking for scheduled workflows to execute...")
        
        # Get the automation extension instance
        automation_extension = extension
        
        executed_workflows = []
        errors = []
        
        # Check each workflow for scheduled execution
        for workflow_id, workflow in automation_extension.workflows.items():
            try:
                if workflow.status.value != "active":
                    continue
                
                # Check if workflow should be executed based on triggers
                should_execute = await _should_execute_workflow(workflow, automation_extension)
                
                if should_execute:
                    logger.info(f"Executing scheduled workflow: {workflow_id}")
                    
                    # Execute the workflow
                    result = await automation_extension.execute_workflow(workflow_id)
                    
                    executed_workflows.append({
                        "workflow_id": workflow_id,
                        "workflow_name": workflow.name,
                        "execution_result": result,
                        "executed_at": datetime.utcnow().isoformat()
                    })
                    
                    logger.info(f"Scheduled workflow {workflow_id} executed with result: {result.get('success', False)}")
            
            except Exception as e:
                error_msg = f"Error executing scheduled workflow {workflow_id}: {str(e)}"
                logger.error(error_msg)
                errors.append({
                    "workflow_id": workflow_id,
                    "error": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        result = {
            "success": True,
            "executed_workflows": executed_workflows,
            "total_executed": len(executed_workflows),
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if executed_workflows:
            logger.info(f"Scheduled execution complete: {len(executed_workflows)} workflows executed")
        
        return result
    
    except Exception as e:
        logger.error(f"Error in scheduled workflow execution task: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def discover_new_plugins(extension: BaseExtension) -> Dict[str, Any]:
    """
    Background task to discover new plugins and update plugin capabilities.
    This task runs every 12 hours to keep the plugin registry up to date.
    """
    try:
        logger.info("Starting plugin discovery task...")
        
        # Get the automation extension instance
        automation_extension = extension
        
        # Store current plugin count
        initial_plugin_count = len(automation_extension.plugin_capabilities)
        
        # Discover new plugins
        await automation_extension._discover_plugin_capabilities()
        
        # Calculate changes
        final_plugin_count = len(automation_extension.plugin_capabilities)
        new_plugins_found = final_plugin_count - initial_plugin_count
        
        # Update workflow templates if new plugins are found
        if new_plugins_found > 0:
            await automation_extension._load_workflow_templates()
            logger.info(f"Updated workflow templates due to {new_plugins_found} new plugins")
        
        # Analyze plugin usage patterns
        plugin_usage_stats = await _analyze_plugin_usage(automation_extension)
        
        result = {
            "success": True,
            "initial_plugin_count": initial_plugin_count,
            "final_plugin_count": final_plugin_count,
            "new_plugins_found": new_plugins_found,
            "plugin_usage_stats": plugin_usage_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Plugin discovery complete: {new_plugins_found} new plugins found")
        return result
    
    except Exception as e:
        logger.error(f"Error in plugin discovery task: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def _should_execute_workflow(workflow, automation_extension) -> bool:
    """
    Check if a workflow should be executed based on its triggers.
    """
    try:
        current_time = datetime.utcnow()
        
        for trigger in workflow.triggers:
            trigger_type = trigger.get("type", "manual")
            
            if trigger_type == "schedule":
                # Check cron schedule
                schedule = trigger.get("schedule")
                if schedule:
                    # Simple schedule checking - in production, use a proper cron library
                    last_execution = await _get_last_execution_time(workflow.id, automation_extension)
                    
                    if await _should_run_on_schedule(schedule, current_time, last_execution):
                        return True
            
            elif trigger_type == "event":
                # Check for pending events
                event_type = trigger.get("event_type")
                if event_type:
                    pending_events = await _check_pending_events(event_type, workflow.id, automation_extension)
                    if pending_events:
                        return True
            
            elif trigger_type == "webhook":
                # Check for webhook triggers (would be handled by webhook endpoint)
                # This is just a placeholder for webhook-triggered workflows
                pass
        
        return False
    
    except Exception as e:
        logger.error(f"Error checking workflow execution conditions: {str(e)}")
        return False


async def _get_last_execution_time(workflow_id: str, automation_extension) -> Optional[datetime]:
    """Get the last execution time for a workflow."""
    try:
        # Find the most recent execution for this workflow
        workflow_executions = [
            e for e in automation_extension.execution_history
            if e.get("workflow_id") == workflow_id
        ]
        
        if workflow_executions:
            # Sort by start time and get the most recent
            workflow_executions.sort(key=lambda x: x.get("start_time", ""), reverse=True)
            last_execution = workflow_executions[0]
            start_time_str = last_execution.get("start_time", "")
            
            if start_time_str:
                return datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
        
        return None
    
    except Exception as e:
        logger.error(f"Error getting last execution time: {str(e)}")
        return None


async def _should_run_on_schedule(schedule: str, current_time: datetime, last_execution: Optional[datetime]) -> bool:
    """
    Simple schedule checker. In production, use a proper cron library like croniter.
    """
    try:
        # Simple schedule patterns
        if schedule == "*/1 * * * *":  # Every minute
            if not last_execution:
                return True
            return (current_time - last_execution).total_seconds() >= 60
        
        elif schedule == "*/5 * * * *":  # Every 5 minutes
            if not last_execution:
                return True
            return (current_time - last_execution).total_seconds() >= 300
        
        elif schedule == "0 * * * *":  # Every hour
            if not last_execution:
                return True
            return (current_time - last_execution).total_seconds() >= 3600
        
        elif schedule == "0 9 * * *":  # Daily at 9 AM
            if not last_execution:
                return current_time.hour == 9 and current_time.minute == 0
            
            # Check if it's 9 AM and we haven't run today
            if current_time.hour == 9 and current_time.minute == 0:
                return last_execution.date() < current_time.date()
        
        elif schedule == "0 0 * * 0":  # Weekly on Sunday
            if not last_execution:
                return current_time.weekday() == 6 and current_time.hour == 0 and current_time.minute == 0
            
            # Check if it's Sunday midnight and we haven't run this week
            if current_time.weekday() == 6 and current_time.hour == 0 and current_time.minute == 0:
                days_since_last = (current_time.date() - last_execution.date()).days
                return days_since_last >= 7
        
        # Default: don't execute if we can't parse the schedule
        return False
    
    except Exception as e:
        logger.error(f"Error checking schedule: {str(e)}")
        return False


async def _check_pending_events(event_type: str, workflow_id: str, automation_extension) -> bool:
    """
    Check for pending events that should trigger workflow execution.
    This is a placeholder - in production, this would integrate with an event system.
    """
    try:
        # This would typically check an event queue or database
        # For now, we'll simulate some basic event checking
        
        if event_type == "github.push":
            # Check for GitHub push events (would integrate with GitHub webhooks)
            return False
        
        elif event_type == "file.created":
            # Check for file creation events (would integrate with file system monitoring)
            return False
        
        elif event_type == "api.request":
            # Check for API request events
            return False
        
        # Default: no pending events
        return False
    
    except Exception as e:
        logger.error(f"Error checking pending events: {str(e)}")
        return False


async def _analyze_plugin_usage(automation_extension) -> Dict[str, Any]:
    """
    Analyze plugin usage patterns from execution history.
    """
    try:
        plugin_usage = {}
        plugin_success_rates = {}
        plugin_avg_durations = {}
        
        # Analyze execution history
        for execution in automation_extension.execution_history:
            steps_executed = execution.get("steps_executed", [])
            
            for step in steps_executed:
                plugin = step.get("plugin", "unknown")
                success = step.get("success", False)
                duration = step.get("duration", 0)
                
                # Count usage
                if plugin not in plugin_usage:
                    plugin_usage[plugin] = {"total": 0, "successful": 0, "durations": []}
                
                plugin_usage[plugin]["total"] += 1
                if success:
                    plugin_usage[plugin]["successful"] += 1
                
                if duration > 0:
                    plugin_usage[plugin]["durations"].append(duration)
        
        # Calculate success rates and average durations
        for plugin, stats in plugin_usage.items():
            total = stats["total"]
            successful = stats["successful"]
            durations = stats["durations"]
            
            plugin_success_rates[plugin] = (successful / total * 100) if total > 0 else 0
            plugin_avg_durations[plugin] = (sum(durations) / len(durations)) if durations else 0
        
        # Find most and least used plugins
        most_used_plugin = max(plugin_usage.keys(), key=lambda p: plugin_usage[p]["total"]) if plugin_usage else None
        least_reliable_plugin = min(plugin_success_rates.keys(), key=lambda p: plugin_success_rates[p]) if plugin_success_rates else None
        
        return {
            "total_plugins_used": len(plugin_usage),
            "plugin_usage_counts": {p: stats["total"] for p, stats in plugin_usage.items()},
            "plugin_success_rates": plugin_success_rates,
            "plugin_avg_durations": plugin_avg_durations,
            "most_used_plugin": most_used_plugin,
            "least_reliable_plugin": least_reliable_plugin,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error analyzing plugin usage: {str(e)}")
        return {
            "error": str(e),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }


async def cleanup_old_execution_history(extension: BaseExtension, days_to_keep: int = 30) -> Dict[str, Any]:
    """
    Background task to clean up old execution history.
    This helps manage memory usage and database size.
    """
    try:
        logger.info(f"Cleaning up execution history older than {days_to_keep} days...")
        
        automation_extension = extension
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        initial_count = len(automation_extension.execution_history)
        
        # Filter out old executions
        filtered_history = []
        for execution in automation_extension.execution_history:
            start_time_str = execution.get("start_time", "")
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                    if start_time >= cutoff_date:
                        filtered_history.append(execution)
                except ValueError:
                    # Keep executions with invalid timestamps
                    filtered_history.append(execution)
            else:
                # Keep executions without timestamps
                filtered_history.append(execution)
        
        # Update the execution history
        automation_extension.execution_history = filtered_history
        
        final_count = len(filtered_history)
        cleaned_count = initial_count - final_count
        
        result = {
            "success": True,
            "initial_count": initial_count,
            "final_count": final_count,
            "cleaned_count": cleaned_count,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Execution history cleanup complete: {cleaned_count} old records removed")
        return result
    
    except Exception as e:
        logger.error(f"Error in execution history cleanup: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def optimize_workflow_performance(extension: BaseExtension) -> Dict[str, Any]:
    """
    Background task to automatically optimize workflow performance based on execution patterns.
    """
    try:
        logger.info("Starting automatic workflow optimization...")
        
        automation_extension = extension
        optimizations_applied = []
        
        for workflow_id, workflow in automation_extension.workflows.items():
            try:
                # Get execution history for this workflow
                workflow_executions = [
                    e for e in automation_extension.execution_history
                    if e.get("workflow_id") == workflow_id
                ]
                
                if len(workflow_executions) < 5:  # Need at least 5 executions for optimization
                    continue
                
                # Analyze performance patterns
                failed_executions = [e for e in workflow_executions if not e.get("success", False)]
                failure_rate = len(failed_executions) / len(workflow_executions)
                
                # Auto-optimize based on patterns
                if failure_rate > 0.2:  # > 20% failure rate
                    # Add retry configurations to frequently failing steps
                    failing_steps = {}
                    for execution in failed_executions:
                        failed_step = execution.get("failed_step")
                        if failed_step:
                            failing_steps[failed_step] = failing_steps.get(failed_step, 0) + 1
                    
                    # Add retry config to steps that fail more than 30% of the time
                    for step in workflow.steps:
                        step_failures = failing_steps.get(step.id, 0)
                        step_failure_rate = step_failures / len(workflow_executions)
                        
                        if step_failure_rate > 0.3 and not step.retry_config:
                            step.retry_config = {
                                "max_retries": 3,
                                "delay": 60,
                                "backoff": "exponential"
                            }
                            
                            optimizations_applied.append({
                                "workflow_id": workflow_id,
                                "workflow_name": workflow.name,
                                "optimization": "added_retry_config",
                                "step_id": step.id,
                                "reason": f"Step failure rate: {step_failure_rate:.1%}"
                            })
                
                # Update workflow timestamp
                workflow.updated_at = datetime.utcnow().isoformat()
            
            except Exception as e:
                logger.error(f"Error optimizing workflow {workflow_id}: {str(e)}")
        
        result = {
            "success": True,
            "optimizations_applied": optimizations_applied,
            "total_optimizations": len(optimizations_applied),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if optimizations_applied:
            logger.info(f"Automatic optimization complete: {len(optimizations_applied)} optimizations applied")
        
        return result
    
    except Exception as e:
        logger.error(f"Error in automatic workflow optimization: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }