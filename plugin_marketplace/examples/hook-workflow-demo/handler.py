"""
Hook Workflow Demo Plugin

Demonstrates the hook-based workflow capabilities in the AI Karen plugin system.
This plugin showcases how hooks can be used for:
- Pre-execution validation
- Post-execution logging
- Error handling and recovery
- Workflow orchestration
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


async def run(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main plugin entry point demonstrating hook-based workflow.
    
    Args:
        params: Plugin parameters including:
            - workflow_steps: List of workflow steps to execute
            - enable_hooks: Whether to demonstrate hook functionality
            - simulate_error: Whether to simulate an error for testing
            - delay_seconds: Delay between steps for demonstration
    
    Returns:
        Dictionary containing workflow execution results and hook demonstrations
    """
    try:
        # Extract parameters
        workflow_steps = params.get("workflow_steps", ["step1", "step2", "step3"])
        enable_hooks = params.get("enable_hooks", True)
        simulate_error = params.get("simulate_error", False)
        delay_seconds = params.get("delay_seconds", 1)
        
        logger.info(f"Starting hook workflow demo with {len(workflow_steps)} steps")
        
        # Simulate pre-execution hook validation
        if enable_hooks:
            validation_result = await simulate_pre_execution_hook(params)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Pre-execution validation failed",
                    "validation_result": validation_result,
                    "hook_demo": "pre_execution_hook_failed"
                }
        
        # Execute workflow steps
        step_results = []
        for i, step in enumerate(workflow_steps):
            logger.info(f"Executing workflow step {i+1}/{len(workflow_steps)}: {step}")
            
            # Simulate step execution
            step_start_time = datetime.utcnow()
            
            # Add delay for demonstration
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)
            
            # Simulate error if requested
            if simulate_error and i == len(workflow_steps) - 1:
                raise ValueError(f"Simulated error in step: {step}")
            
            step_result = {
                "step_name": step,
                "step_number": i + 1,
                "status": "completed",
                "start_time": step_start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "data": {
                    "processed_items": (i + 1) * 10,
                    "step_type": "demo_step",
                    "hook_integration": enable_hooks
                }
            }
            
            step_results.append(step_result)
            
            # Simulate step-level hooks
            if enable_hooks:
                hook_result = await simulate_step_hook(step, step_result)
                step_result["hook_result"] = hook_result
        
        # Simulate post-execution hook
        post_execution_result = None
        if enable_hooks:
            post_execution_result = await simulate_post_execution_hook(step_results)
        
        # Prepare final result
        result = {
            "success": True,
            "workflow_name": "hook_workflow_demo",
            "total_steps": len(workflow_steps),
            "completed_steps": len(step_results),
            "execution_time_seconds": sum(
                (datetime.fromisoformat(step["end_time"]) - 
                 datetime.fromisoformat(step["start_time"])).total_seconds()
                for step in step_results
            ),
            "step_results": step_results,
            "hook_demonstrations": {
                "pre_execution_hook": enable_hooks,
                "step_hooks": enable_hooks,
                "post_execution_hook": enable_hooks,
                "post_execution_result": post_execution_result
            },
            "metadata": {
                "plugin_version": "1.0.0",
                "hook_system_version": "1.0",
                "demonstration_mode": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        logger.info(f"Hook workflow demo completed successfully with {len(step_results)} steps")
        return result
        
    except Exception as e:
        logger.error(f"Hook workflow demo failed: {str(e)}", exc_info=True)
        
        # Simulate error handling hook
        error_handling_result = None
        if enable_hooks:
            error_handling_result = await simulate_error_handling_hook(e, params)
        
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "partial_results": step_results if 'step_results' in locals() else [],
            "hook_demonstrations": {
                "error_handling_hook": enable_hooks,
                "error_handling_result": error_handling_result
            },
            "recovery_suggestions": [
                "Check workflow step parameters",
                "Verify system resources are available",
                "Review hook configuration",
                "Enable detailed logging for debugging"
            ],
            "metadata": {
                "plugin_version": "1.0.0",
                "error_timestamp": datetime.utcnow().isoformat(),
                "demonstration_mode": True
            }
        }


async def simulate_pre_execution_hook(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate a pre-execution hook that validates workflow parameters.
    
    In a real implementation, this would be handled by the hook system.
    """
    logger.info("Simulating pre-execution hook: parameter validation")
    
    validation_checks = []
    
    # Check workflow steps
    workflow_steps = params.get("workflow_steps", [])
    if not workflow_steps:
        validation_checks.append({
            "check": "workflow_steps_present",
            "status": "failed",
            "message": "No workflow steps provided"
        })
    else:
        validation_checks.append({
            "check": "workflow_steps_present",
            "status": "passed",
            "message": f"Found {len(workflow_steps)} workflow steps"
        })
    
    # Check step count limits
    if len(workflow_steps) > 10:
        validation_checks.append({
            "check": "step_count_limit",
            "status": "failed",
            "message": "Too many workflow steps (max 10)"
        })
    else:
        validation_checks.append({
            "check": "step_count_limit",
            "status": "passed",
            "message": "Step count within limits"
        })
    
    # Check delay parameter
    delay_seconds = params.get("delay_seconds", 1)
    if delay_seconds > 5:
        validation_checks.append({
            "check": "delay_limit",
            "status": "warning",
            "message": "Delay is quite high, workflow may be slow"
        })
    else:
        validation_checks.append({
            "check": "delay_limit",
            "status": "passed",
            "message": "Delay parameter acceptable"
        })
    
    # Determine overall validation result
    failed_checks = [check for check in validation_checks if check["status"] == "failed"]
    
    return {
        "valid": len(failed_checks) == 0,
        "checks": validation_checks,
        "failed_checks": len(failed_checks),
        "warning_checks": len([check for check in validation_checks if check["status"] == "warning"]),
        "hook_type": "pre_execution",
        "timestamp": datetime.utcnow().isoformat()
    }


async def simulate_step_hook(step_name: str, step_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate a step-level hook that processes individual step results.
    
    In a real implementation, this would be handled by the hook system.
    """
    logger.info(f"Simulating step hook for: {step_name}")
    
    # Simulate step analysis
    processed_items = step_result["data"]["processed_items"]
    
    analysis = {
        "step_name": step_name,
        "performance_score": min(100, processed_items * 2),  # Simple scoring
        "resource_usage": {
            "memory_mb": processed_items * 0.5,
            "cpu_percent": min(50, processed_items * 0.1)
        },
        "recommendations": []
    }
    
    # Add recommendations based on performance
    if analysis["performance_score"] < 50:
        analysis["recommendations"].append("Consider optimizing step processing")
    
    if analysis["resource_usage"]["memory_mb"] > 25:
        analysis["recommendations"].append("Monitor memory usage")
    
    if not analysis["recommendations"]:
        analysis["recommendations"].append("Step performance is optimal")
    
    return {
        "hook_type": "step_processing",
        "analysis": analysis,
        "timestamp": datetime.utcnow().isoformat()
    }


async def simulate_post_execution_hook(step_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Simulate a post-execution hook that analyzes overall workflow results.
    
    In a real implementation, this would be handled by the hook system.
    """
    logger.info("Simulating post-execution hook: workflow analysis")
    
    # Calculate overall statistics
    total_items_processed = sum(step["data"]["processed_items"] for step in step_results)
    total_execution_time = sum(
        (datetime.fromisoformat(step["end_time"]) - 
         datetime.fromisoformat(step["start_time"])).total_seconds()
        for step in step_results
    )
    
    # Generate workflow summary
    summary = {
        "total_steps": len(step_results),
        "total_items_processed": total_items_processed,
        "total_execution_time_seconds": total_execution_time,
        "average_items_per_second": total_items_processed / max(total_execution_time, 1),
        "workflow_efficiency": "high" if total_items_processed > 50 else "medium"
    }
    
    # Generate insights
    insights = []
    
    if summary["average_items_per_second"] > 20:
        insights.append("Workflow processing rate is excellent")
    elif summary["average_items_per_second"] > 10:
        insights.append("Workflow processing rate is good")
    else:
        insights.append("Consider optimizing workflow for better performance")
    
    if len(step_results) > 5:
        insights.append("Complex workflow with many steps - consider breaking into sub-workflows")
    
    return {
        "hook_type": "post_execution",
        "summary": summary,
        "insights": insights,
        "timestamp": datetime.utcnow().isoformat()
    }


async def simulate_error_handling_hook(error: Exception, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate an error handling hook that provides recovery suggestions.
    
    In a real implementation, this would be handled by the hook system.
    """
    logger.info(f"Simulating error handling hook for: {type(error).__name__}")
    
    error_analysis = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_category": "simulation" if "Simulated" in str(error) else "runtime",
        "severity": "high" if "critical" in str(error).lower() else "medium"
    }
    
    # Generate recovery suggestions based on error type
    recovery_suggestions = []
    
    if isinstance(error, ValueError):
        recovery_suggestions.extend([
            "Validate input parameters before execution",
            "Check data types and value ranges",
            "Review workflow step configuration"
        ])
    elif isinstance(error, TimeoutError):
        recovery_suggestions.extend([
            "Increase execution timeout limits",
            "Optimize workflow step performance",
            "Consider breaking large steps into smaller ones"
        ])
    else:
        recovery_suggestions.extend([
            "Review error logs for detailed information",
            "Check system resources and dependencies",
            "Verify plugin configuration"
        ])
    
    # Add context-specific suggestions
    if params.get("simulate_error"):
        recovery_suggestions.append("Disable error simulation for normal operation")
    
    return {
        "hook_type": "error_handling",
        "error_analysis": error_analysis,
        "recovery_suggestions": recovery_suggestions,
        "auto_recovery_possible": error_analysis["error_category"] == "simulation",
        "timestamp": datetime.utcnow().isoformat()
    }


# Plugin metadata for introspection
__plugin_info__ = {
    "name": "hook_workflow_demo",
    "version": "1.0.0",
    "description": "Demonstrates hook-based workflow capabilities",
    "author": "AI Karen Team",
    "capabilities": [
        "workflow_orchestration",
        "hook_demonstration",
        "error_simulation",
        "performance_analysis",
        "parameter_validation"
    ],
    "hook_types": [
        "pre_execution",
        "step_processing", 
        "post_execution",
        "error_handling"
    ]
}