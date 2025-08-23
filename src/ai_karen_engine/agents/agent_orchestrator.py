"""
Agent Orchestrator - Main Integration Point

This module provides the main orchestration layer that integrates the agent planner,
execution pipeline, guardrails, and audit logging into a cohesive system for
copilot operations.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import uuid

from ai_karen_engine.agents.planner import (
    AgentPlanner, 
    Plan, 
    EmotionalContext,
    InteractionOutcome
)
from ai_karen_engine.agents.execution_pipeline import (
    ExecutionPipeline,
    ExecutionContext,
    ExecutionStatus,
    ApprovalStatus
)
from ai_karen_engine.agents.audit_logger import (
    AuditLogger,
    AuditEventType,
    AuditSeverity,
    get_audit_logger
)
from ai_karen_engine.services.knowledge.index_hub import IndexHub
from ai_karen_engine.services.cognitive.episodic_memory import EpisodicMemoryService
from ai_karen_engine.services.cognitive.working_memory import WorkingMemoryService
from ai_karen_engine.services.tools.registry import CopilotToolRegistry, CopilotToolService
from ai_karen_engine.services.tools.contracts import ExecutionMode, RBACLevel, PrivacyLevel


@dataclass
class AgentRequest:
    """Request for agent assistance."""
    request_id: str
    user_id: str
    session_id: str
    query: str
    
    # Context
    selected_files: List[str] = None
    workspace_context: Dict[str, Any] = None
    
    # Execution preferences
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN
    user_rbac_level: RBACLevel = RBACLevel.DEVELOPER
    privacy_clearance: PrivacyLevel = PrivacyLevel.INTERNAL
    
    # Behavioral preferences
    emotional_context: EmotionalContext = EmotionalContext.FOCUSED
    require_approval: bool = False
    enable_rollback: bool = True
    
    def __post_init__(self):
        if self.selected_files is None:
            self.selected_files = []
        if self.workspace_context is None:
            self.workspace_context = {}


@dataclass
class AgentResponse:
    """Response from agent processing."""
    request_id: str
    success: bool
    
    # Plan information
    plan: Optional[Plan] = None
    plan_summary: str = ""
    
    # Execution information
    execution_context: Optional[ExecutionContext] = None
    execution_summary: str = ""
    
    # Results
    artifacts: List[Dict[str, Any]] = None
    recommendations: List[str] = None
    
    # Reasoning and explanation
    reasoning_explanation: str = ""
    confidence_level: str = "medium"
    
    # Status and tracking
    status: str = "completed"  # planning, executing, completed, failed, requires_approval
    correlation_id: str = ""
    
    # Error information
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    
    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
        if self.recommendations is None:
            self.recommendations = []


class AgentOrchestrator:
    """
    Main orchestrator for agent operations, integrating planning, execution,
    guardrails, and audit logging into a unified system.
    """
    
    def __init__(
        self,
        index_hub: IndexHub,
        episodic_memory: EpisodicMemoryService,
        working_memory: WorkingMemoryService,
        tool_registry: CopilotToolRegistry,
        tool_service: CopilotToolService,
        audit_logger: Optional[AuditLogger] = None
    ):
        self.index_hub = index_hub
        self.episodic_memory = episodic_memory
        self.working_memory = working_memory
        self.tool_registry = tool_registry
        self.tool_service = tool_service
        self.audit_logger = audit_logger or get_audit_logger()
        
        # Initialize components
        self.agent_planner = AgentPlanner(
            index_hub=index_hub,
            episodic_memory=episodic_memory,
            working_memory=working_memory,
            tool_registry=tool_registry,
            tool_service=tool_service
        )
        
        self.execution_pipeline = ExecutionPipeline(tool_service)
        
        self.logger = logging.getLogger(__name__)
        
        # Active requests tracking
        self.active_requests: Dict[str, AgentRequest] = {}
        self.request_history: List[str] = []
        
        # Configuration
        self.max_concurrent_requests = 5
        self.default_timeout_seconds = 300
        
        # Metrics
        self.orchestrator_metrics = {
            "requests_processed": 0,
            "plans_created": 0,
            "executions_completed": 0,
            "approvals_required": 0,
            "errors_encountered": 0
        }
    
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """
        Process an agent request through the complete pipeline.
        
        Args:
            request: Agent request with query and context
            
        Returns:
            Agent response with plan, execution results, and explanations
        """
        correlation_id = str(uuid.uuid4())
        
        try:
            # Check concurrent request limits
            if len(self.active_requests) >= self.max_concurrent_requests:
                return AgentResponse(
                    request_id=request.request_id,
                    success=False,
                    status="failed",
                    error_message="Maximum concurrent requests exceeded",
                    error_code="RATE_LIMIT_EXCEEDED",
                    correlation_id=correlation_id
                )
            
            # Register active request
            self.active_requests[request.request_id] = request
            
            # Log request start
            await self.audit_logger.log_event(
                event_type=AuditEventType.PLAN_CREATED,
                correlation_id=correlation_id,
                message=f"Processing agent request: {request.query[:100]}...",
                user_id=request.user_id,
                session_id=request.session_id,
                details={
                    "request_id": request.request_id,
                    "query_length": len(request.query),
                    "selected_files": len(request.selected_files),
                    "execution_mode": request.execution_mode.value,
                    "emotional_context": request.emotional_context.value
                }
            )
            
            # Update emotional context in reasoning engine
            self.agent_planner.reasoning_engine.update_emotional_context(request.emotional_context)
            
            # Phase 1: Plan Creation
            plan_response = await self._create_plan_phase(request, correlation_id)
            if not plan_response.success:
                return plan_response
            
            # Phase 2: Approval Workflow (if required)
            if plan_response.plan.requires_approval or request.require_approval:
                approval_response = await self._approval_phase(request, plan_response.plan, correlation_id)
                if not approval_response.success:
                    return approval_response
            
            # Phase 3: Execution
            execution_response = await self._execution_phase(request, plan_response.plan, correlation_id)
            
            # Phase 4: Learning and Feedback
            await self._learning_phase(request, plan_response.plan, execution_response, correlation_id)
            
            return execution_response
            
        except Exception as e:
            self.logger.error(f"Agent orchestration failed: {e}")
            self.orchestrator_metrics["errors_encountered"] += 1
            
            # Log error
            await self.audit_logger.log_event(
                event_type=AuditEventType.PLAN_FAILED,
                correlation_id=correlation_id,
                message=f"Agent request failed: {str(e)}",
                severity=AuditSeverity.ERROR,
                user_id=request.user_id,
                session_id=request.session_id,
                error_message=str(e),
                error_code=type(e).__name__
            )
            
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                status="failed",
                error_message=f"Orchestration error: {str(e)}",
                error_code=type(e).__name__,
                correlation_id=correlation_id
            )
        
        finally:
            # Clean up active request
            if request.request_id in self.active_requests:
                del self.active_requests[request.request_id]
                self.request_history.append(request.request_id)
    
    async def _create_plan_phase(
        self, 
        request: AgentRequest, 
        correlation_id: str
    ) -> AgentResponse:
        """Phase 1: Create execution plan."""
        try:
            # Create plan
            plan = await self.agent_planner.create_plan(
                query=request.query,
                user_id=request.user_id,
                session_id=request.session_id,
                context={
                    "selected_files": request.selected_files,
                    "workspace_context": request.workspace_context,
                    "privacy_sensitive": request.privacy_clearance == PrivacyLevel.CONFIDENTIAL,
                    "high_risk_operation": request.execution_mode != ExecutionMode.DRY_RUN
                },
                execution_mode=request.execution_mode
            )
            
            # Log plan creation
            await self.audit_logger.log_plan_created(
                plan=plan,
                correlation_id=correlation_id,
                user_id=request.user_id,
                session_id=request.session_id
            )
            
            self.orchestrator_metrics["plans_created"] += 1
            
            # Generate explanation
            reasoning_explanation = ""
            if plan.cognition_trail:
                reasoning_explanation = plan.cognition_trail.generate_explanation()
            
            # Determine status
            status = "requires_approval" if plan.requires_approval else "planning_complete"
            
            return AgentResponse(
                request_id=request.request_id,
                success=True,
                plan=plan,
                plan_summary=plan.generate_summary(),
                reasoning_explanation=reasoning_explanation,
                confidence_level=plan.confidence_score.confidence_level.name.lower().replace('_', ' ') if plan.confidence_score else "medium",
                status=status,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self.logger.error(f"Plan creation failed: {e}")
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                status="failed",
                error_message=f"Plan creation failed: {str(e)}",
                error_code=type(e).__name__,
                correlation_id=correlation_id
            )
    
    async def _approval_phase(
        self, 
        request: AgentRequest, 
        plan: Plan, 
        correlation_id: str
    ) -> AgentResponse:
        """Phase 2: Handle approval workflow."""
        try:
            # Create approval request
            approval_request = await self.execution_pipeline.approval_workflow.create_approval_request(
                plan_id=plan.plan_id,
                user_id=request.user_id,
                operation_description=f"Execute plan: {plan.name}",
                risk_assessment=plan.approval_reason,
                required_approver_level=RBACLevel.ADMIN
            )
            
            # Log approval request
            await self.audit_logger.log_approval_request(
                request=approval_request,
                correlation_id=correlation_id
            )
            
            # Check for auto-approval
            auto_approved = await self.execution_pipeline.approval_workflow.check_auto_approval(
                approval_request, request.user_rbac_level
            )
            
            if auto_approved:
                # Log auto-approval
                await self.audit_logger.log_approval_decision(
                    request=approval_request,
                    correlation_id=correlation_id,
                    approved=True,
                    auto_approved=True
                )
                
                return AgentResponse(
                    request_id=request.request_id,
                    success=True,
                    plan=plan,
                    status="approved",
                    correlation_id=correlation_id
                )
            else:
                # Manual approval required
                self.orchestrator_metrics["approvals_required"] += 1
                
                return AgentResponse(
                    request_id=request.request_id,
                    success=False,
                    plan=plan,
                    status="requires_approval",
                    error_message="Manual approval required for high-risk operations",
                    error_code="APPROVAL_REQUIRED",
                    correlation_id=correlation_id,
                    recommendations=[
                        "Contact an administrator for approval",
                        "Consider using dry-run mode first",
                        "Reduce operation scope to lower risk level"
                    ]
                )
            
        except Exception as e:
            self.logger.error(f"Approval phase failed: {e}")
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                status="failed",
                error_message=f"Approval workflow failed: {str(e)}",
                error_code=type(e).__name__,
                correlation_id=correlation_id
            )
    
    async def _execution_phase(
        self, 
        request: AgentRequest, 
        plan: Plan, 
        correlation_id: str
    ) -> AgentResponse:
        """Phase 3: Execute the plan."""
        try:
            # Execute plan
            execution_context = await self.execution_pipeline.execute_plan(
                plan=plan,
                user_id=request.user_id,
                session_id=request.session_id,
                execution_mode=request.execution_mode,
                user_rbac_level=request.user_rbac_level,
                privacy_clearance=request.privacy_clearance
            )
            
            # Log execution completion
            await self.audit_logger.log_plan_execution_completed(execution_context)
            
            # Generate execution summary
            execution_summary = self._generate_execution_summary(execution_context)
            
            # Collect artifacts
            artifacts = self._collect_execution_artifacts(execution_context)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(execution_context)
            
            # Determine final status
            success = execution_context.status == ExecutionStatus.COMPLETED
            status = execution_context.status.value
            
            if success:
                self.orchestrator_metrics["executions_completed"] += 1
            
            return AgentResponse(
                request_id=request.request_id,
                success=success,
                plan=plan,
                execution_context=execution_context,
                execution_summary=execution_summary,
                artifacts=artifacts,
                recommendations=recommendations,
                status=status,
                correlation_id=correlation_id,
                error_message=None if success else "Execution failed - see execution context for details"
            )
            
        except Exception as e:
            self.logger.error(f"Execution phase failed: {e}")
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                status="failed",
                error_message=f"Execution failed: {str(e)}",
                error_code=type(e).__name__,
                correlation_id=correlation_id
            )
    
    async def _learning_phase(
        self, 
        request: AgentRequest, 
        plan: Plan, 
        response: AgentResponse, 
        correlation_id: str
    ):
        """Phase 4: Learn from execution outcomes."""
        try:
            # Determine interaction outcome
            if response.success:
                outcome = InteractionOutcome.SUCCESS
            elif response.status == "requires_approval":
                outcome = InteractionOutcome.PARTIAL_SUCCESS
            else:
                outcome = InteractionOutcome.FAILURE
            
            # Update agent planner with outcome
            await self.agent_planner.learn_from_plan_outcome(
                plan_id=plan.plan_id,
                outcome=outcome,
                user_feedback=None  # Would come from user in real scenario
            )
            
            # Store episodic memory
            await self.episodic_memory.store_episodic_memory(
                conversation_id=request.session_id,
                user_id=request.user_id,
                content=f"Agent request: {request.query}",
                context_summary=f"Plan: {plan.name}, Status: {response.status}",
                interaction_type="agent_assistance",
                session_id=request.session_id,
                success_indicators=["plan_executed"] if response.success else [],
                failure_indicators=["execution_failed"] if not response.success else [],
                metadata={
                    "request_id": request.request_id,
                    "plan_id": plan.plan_id,
                    "correlation_id": correlation_id,
                    "execution_mode": request.execution_mode.value,
                    "step_count": len(plan.steps)
                }
            )
            
            self.logger.info(f"Learning phase completed for request {request.request_id}")
            
        except Exception as e:
            self.logger.error(f"Learning phase failed: {e}")
    
    def _generate_execution_summary(self, context: ExecutionContext) -> str:
        """Generate human-readable execution summary."""
        summary_parts = [
            f"Execution Status: {context.status.value.title()}",
            f"Steps Completed: {len(context.completed_steps)}/{len(context.plan.steps)}",
        ]
        
        if context.failed_steps:
            summary_parts.append(f"Steps Failed: {len(context.failed_steps)}")
        
        if context.total_execution_time:
            summary_parts.append(f"Total Time: {context.total_execution_time}")
        
        if context.rollback_data:
            summary_parts.append(f"Rollback Available: {len(context.rollback_data)} steps")
        
        return "\n".join(summary_parts)
    
    def _collect_execution_artifacts(self, context: ExecutionContext) -> List[Dict[str, Any]]:
        """Collect artifacts from execution results."""
        artifacts = []
        
        for step_id, result in context.step_results.items():
            if result.success and result.result:
                # Find the step
                step = next((s for s in context.plan.steps if s.step_id == step_id), None)
                if step:
                    artifact = {
                        "type": "step_result",
                        "step_name": step.name,
                        "tool_name": step.tool_name,
                        "content": result.result,
                        "execution_mode": result.execution_mode.value,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    artifacts.append(artifact)
        
        return artifacts
    
    def _generate_recommendations(self, context: ExecutionContext) -> List[str]:
        """Generate recommendations based on execution results."""
        recommendations = []
        
        if context.status == ExecutionStatus.COMPLETED:
            recommendations.append("✅ All steps completed successfully")
            
            if context.execution_mode == ExecutionMode.DRY_RUN:
                recommendations.append("Consider running in apply mode to make changes permanent")
        
        elif context.status == ExecutionStatus.FAILED:
            recommendations.append("❌ Execution failed - review error details")
            
            if context.failed_steps:
                recommendations.append(f"Focus on fixing {len(context.failed_steps)} failed steps")
            
            if context.rollback_data:
                recommendations.append("Consider rolling back completed changes")
        
        elif context.status == ExecutionStatus.ROLLBACK_REQUIRED:
            recommendations.append("⚠️ Rollback required due to failures")
            recommendations.append("Use rollback operation to restore previous state")
        
        # Add general recommendations
        if len(context.completed_steps) > 0 and len(context.failed_steps) > 0:
            recommendations.append("Partial success - review completed steps before retrying")
        
        return recommendations
    
    async def rollback_request(self, request_id: str) -> bool:
        """Rollback a previous request execution."""
        try:
            # Find execution context in history
            # This would typically query a database
            # For now, we'll simulate
            
            # In a real implementation, you would:
            # 1. Find the execution context by request_id
            # 2. Call execution_pipeline.rollback_execution()
            # 3. Log the rollback operation
            
            self.logger.info(f"Rollback requested for {request_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed for {request_id}: {e}")
            return False
    
    async def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a request."""
        if request_id in self.active_requests:
            return {
                "request_id": request_id,
                "status": "active",
                "request": self.active_requests[request_id]
            }
        
        # Check history (would query database in real implementation)
        if request_id in self.request_history:
            return {
                "request_id": request_id,
                "status": "completed",
                "in_history": True
            }
        
        return None
    
    def get_orchestrator_metrics(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator metrics."""
        return {
            "orchestrator": self.orchestrator_metrics.copy(),
            "active_requests": len(self.active_requests),
            "request_history_count": len(self.request_history),
            "planner": {
                "active_plans": len(self.agent_planner.active_plans),
                "plan_history": sum(len(plans) for plans in self.agent_planner.plan_history.values())
            },
            "execution_pipeline": self.execution_pipeline.get_pipeline_metrics(),
            "audit": self.audit_logger.get_audit_metrics()
        }


# Global orchestrator instance
_agent_orchestrator: Optional[AgentOrchestrator] = None


def get_agent_orchestrator() -> Optional[AgentOrchestrator]:
    """Get global agent orchestrator instance."""
    return _agent_orchestrator


async def initialize_agent_orchestrator(
    index_hub: IndexHub,
    episodic_memory: EpisodicMemoryService,
    working_memory: WorkingMemoryService,
    tool_registry: CopilotToolRegistry,
    tool_service: CopilotToolService,
    audit_logger: Optional[AuditLogger] = None
) -> AgentOrchestrator:
    """Initialize the agent orchestrator system."""
    global _agent_orchestrator
    
    _agent_orchestrator = AgentOrchestrator(
        index_hub=index_hub,
        episodic_memory=episodic_memory,
        working_memory=working_memory,
        tool_registry=tool_registry,
        tool_service=tool_service,
        audit_logger=audit_logger
    )
    
    return _agent_orchestrator