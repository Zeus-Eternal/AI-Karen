"""
Execution Pipeline with Guardrails and Approval Workflow

This module implements the execution pipeline for agent plans with comprehensive
guardrails, RBAC-based approval workflows, rollback mechanisms, and audit trails.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import traceback

from ai_karen_engine.agents.planner import Plan, PlanStep, RiskLevel, ConfidenceLevel
from ai_karen_engine.services.tools.registry import CopilotToolService
from ai_karen_engine.services.tools.contracts import (
    ToolContext,
    ToolResult,
    ExecutionMode,
    RBACLevel,
    PrivacyLevel,
    Citation
)


class ApprovalStatus(Enum):
    """Status of approval requests."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


class ExecutionStatus(Enum):
    """Status of plan execution."""
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLBACK_REQUIRED = "rollback_required"
    ROLLBACK_IN_PROGRESS = "rollback_in_progress"
    ROLLBACK_COMPLETED = "rollback_completed"


class GuardrailViolation(Enum):
    """Types of guardrail violations."""
    INSUFFICIENT_CITATIONS = "insufficient_citations"
    RBAC_VIOLATION = "rbac_violation"
    PRIVACY_VIOLATION = "privacy_violation"
    RISK_THRESHOLD_EXCEEDED = "risk_threshold_exceeded"
    TIMEOUT_EXCEEDED = "timeout_exceeded"
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"
    POLICY_VIOLATION = "policy_violation"


@dataclass
class ApprovalRequest:
    """Request for manual approval of high-risk operations."""
    request_id: str
    plan_id: str
    step_id: Optional[str]  # None for plan-level approval
    user_id: str
    
    # Request details
    operation_description: str
    risk_assessment: str
    required_approver_level: RBACLevel
    
    # Approval workflow
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Approval decision
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Context
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if approval request has expired."""
        return (
            self.expires_at is not None and 
            datetime.utcnow() > self.expires_at
        )
    
    def can_auto_approve(self, user_rbac_level: RBACLevel) -> bool:
        """Check if request can be auto-approved based on user RBAC level."""
        rbac_hierarchy = {
            RBACLevel.AUTOMATION: 1,
            RBACLevel.DEVELOPER: 2,
            RBACLevel.ADMIN: 3
        }
        
        user_level = rbac_hierarchy.get(user_rbac_level, 0)
        required_level = rbac_hierarchy.get(self.required_approver_level, 3)
        
        return user_level >= required_level


@dataclass
class ExecutionContext:
    """Context for plan execution with guardrails and tracking."""
    execution_id: str
    plan: Plan
    user_id: str
    session_id: str
    
    # Execution configuration
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN
    enable_rollback: bool = True
    timeout_seconds: int = 300
    
    # RBAC and permissions
    user_rbac_level: RBACLevel = RBACLevel.DEVELOPER
    rbac_permissions: Set[RBACLevel] = field(default_factory=set)
    privacy_clearance: PrivacyLevel = PrivacyLevel.INTERNAL
    
    # Guardrail configuration
    enforce_citations: bool = True
    min_citations_required: int = 2
    max_risk_level: RiskLevel = RiskLevel.MEDIUM
    
    # Circuit breaker settings
    max_consecutive_failures: int = 3
    failure_timeout_seconds: int = 60
    
    # Tracking
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # State
    status: ExecutionStatus = ExecutionStatus.QUEUED
    current_step_index: int = 0
    completed_steps: Set[str] = field(default_factory=set)
    failed_steps: Set[str] = field(default_factory=set)
    
    # Results and rollback data
    step_results: Dict[str, ToolResult] = field(default_factory=dict)
    rollback_data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Metrics
    total_execution_time: Optional[timedelta] = None
    step_execution_times: Dict[str, timedelta] = field(default_factory=dict)


@dataclass
class GuardrailCheck:
    """Result of a guardrail check."""
    passed: bool
    violation_type: Optional[GuardrailViolation] = None
    message: str = ""
    severity: str = "info"  # info, warning, error, critical
    suggested_action: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "violation_type": self.violation_type.value if self.violation_type else None,
            "message": self.message,
            "severity": self.severity,
            "suggested_action": self.suggested_action
        }


class CircuitBreaker:
    """Circuit breaker for handling consecutive failures."""
    
    def __init__(self, max_failures: int = 3, timeout_seconds: int = 60):
        self.max_failures = max_failures
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half_open
    
    def can_execute(self) -> bool:
        """Check if execution is allowed based on circuit breaker state."""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if (
                self.last_failure_time and 
                datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.timeout_seconds)
            ):
                self.state = "half_open"
                return True
            return False
        
        # half_open state
        return True
    
    def record_success(self):
        """Record successful execution."""
        self.failure_count = 0
        self.state = "closed"
        self.last_failure_time = None
    
    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.max_failures:
            self.state = "open"
        elif self.state == "half_open":
            self.state = "open"


class GuardrailEngine:
    """Engine for enforcing guardrails and policies."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Policy functions
        self.global_policies: List[Callable[[ExecutionContext, PlanStep], GuardrailCheck]] = []
        self.step_policies: Dict[str, List[Callable]] = {}
        
        # Metrics
        self.guardrail_metrics = {
            "checks_performed": 0,
            "violations_detected": 0,
            "auto_approvals": 0,
            "manual_approvals_required": 0
        }
    
    def add_global_policy(self, policy: Callable[[ExecutionContext, PlanStep], GuardrailCheck]):
        """Add a global policy that applies to all steps."""
        self.global_policies.append(policy)
    
    def add_step_policy(
        self, 
        tool_name: str, 
        policy: Callable[[ExecutionContext, PlanStep], GuardrailCheck]
    ):
        """Add a policy specific to a tool."""
        if tool_name not in self.step_policies:
            self.step_policies[tool_name] = []
        self.step_policies[tool_name].append(policy)
    
    async def check_guardrails(
        self, 
        context: ExecutionContext, 
        step: PlanStep
    ) -> List[GuardrailCheck]:
        """Perform all guardrail checks for a step."""
        checks = []
        
        try:
            # Basic guardrail checks
            checks.extend(await self._check_basic_guardrails(context, step))
            
            # Global policy checks
            for policy in self.global_policies:
                try:
                    check = policy(context, step)
                    checks.append(check)
                except Exception as e:
                    self.logger.error(f"Global policy check failed: {e}")
                    checks.append(GuardrailCheck(
                        passed=False,
                        violation_type=GuardrailViolation.POLICY_VIOLATION,
                        message=f"Policy check error: {str(e)}",
                        severity="error"
                    ))
            
            # Tool-specific policy checks
            tool_policies = self.step_policies.get(step.tool_name, [])
            for policy in tool_policies:
                try:
                    check = policy(context, step)
                    checks.append(check)
                except Exception as e:
                    self.logger.error(f"Tool policy check failed for {step.tool_name}: {e}")
                    checks.append(GuardrailCheck(
                        passed=False,
                        violation_type=GuardrailViolation.POLICY_VIOLATION,
                        message=f"Tool policy error: {str(e)}",
                        severity="error"
                    ))
            
            # Update metrics
            self.guardrail_metrics["checks_performed"] += len(checks)
            violations = sum(1 for check in checks if not check.passed)
            self.guardrail_metrics["violations_detected"] += violations
            
            return checks
            
        except Exception as e:
            self.logger.error(f"Guardrail check failed: {e}")
            return [GuardrailCheck(
                passed=False,
                violation_type=GuardrailViolation.POLICY_VIOLATION,
                message=f"Guardrail system error: {str(e)}",
                severity="critical"
            )]
    
    async def _check_basic_guardrails(
        self, 
        context: ExecutionContext, 
        step: PlanStep
    ) -> List[GuardrailCheck]:
        """Perform basic guardrail checks."""
        checks = []
        
        # Citation requirement check
        if context.enforce_citations and step.tool_name.startswith(("code.apply", "fs.write", "git.")):
            if len(step.required_citations) < context.min_citations_required:
                checks.append(GuardrailCheck(
                    passed=False,
                    violation_type=GuardrailViolation.INSUFFICIENT_CITATIONS,
                    message=f"Step requires {context.min_citations_required} citations, found {len(step.required_citations)}",
                    severity="error",
                    suggested_action="Add more supporting citations from knowledge base"
                ))
            else:
                checks.append(GuardrailCheck(
                    passed=True,
                    message=f"Citation requirement satisfied ({len(step.required_citations)} citations)",
                    severity="info"
                ))
        
        # Risk level check
        if step.risk_assessment:
            if step.risk_assessment.level.value > context.max_risk_level.value:
                checks.append(GuardrailCheck(
                    passed=False,
                    violation_type=GuardrailViolation.RISK_THRESHOLD_EXCEEDED,
                    message=f"Step risk level {step.risk_assessment.level.name} exceeds maximum {context.max_risk_level.name}",
                    severity="warning",
                    suggested_action="Require manual approval or reduce operation scope"
                ))
            else:
                checks.append(GuardrailCheck(
                    passed=True,
                    message=f"Risk level {step.risk_assessment.level.name} within acceptable limits",
                    severity="info"
                ))
        
        # RBAC check (simplified - would integrate with actual RBAC system)
        required_rbac = getattr(step, 'required_rbac_level', RBACLevel.DEVELOPER)
        if context.user_rbac_level.value < required_rbac.value:
            checks.append(GuardrailCheck(
                passed=False,
                violation_type=GuardrailViolation.RBAC_VIOLATION,
                message=f"User RBAC level {context.user_rbac_level.name} insufficient for {required_rbac.name}",
                severity="error",
                suggested_action="Require approval from user with sufficient permissions"
            ))
        else:
            checks.append(GuardrailCheck(
                passed=True,
                message=f"RBAC check passed for {required_rbac.name}",
                severity="info"
            ))
        
        return checks


class ApprovalWorkflow:
    """Workflow manager for approval requests."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Active approval requests
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[ApprovalRequest] = []
        
        # Configuration
        self.default_expiry_hours = 24
        self.auto_approval_enabled = True
        
        # Metrics
        self.approval_metrics = {
            "requests_created": 0,
            "auto_approvals": 0,
            "manual_approvals": 0,
            "rejections": 0,
            "expirations": 0
        }
    
    async def create_approval_request(
        self,
        plan_id: str,
        user_id: str,
        operation_description: str,
        risk_assessment: str,
        required_approver_level: RBACLevel,
        step_id: Optional[str] = None,
        expiry_hours: Optional[int] = None
    ) -> ApprovalRequest:
        """Create a new approval request."""
        request_id = str(uuid.uuid4())
        
        expiry_time = None
        if expiry_hours or self.default_expiry_hours:
            hours = expiry_hours or self.default_expiry_hours
            expiry_time = datetime.utcnow() + timedelta(hours=hours)
        
        request = ApprovalRequest(
            request_id=request_id,
            plan_id=plan_id,
            step_id=step_id,
            user_id=user_id,
            operation_description=operation_description,
            risk_assessment=risk_assessment,
            required_approver_level=required_approver_level,
            expires_at=expiry_time
        )
        
        self.pending_approvals[request_id] = request
        self.approval_metrics["requests_created"] += 1
        
        self.logger.info(f"Created approval request {request_id} for plan {plan_id}")
        return request
    
    async def check_auto_approval(
        self, 
        request: ApprovalRequest, 
        user_rbac_level: RBACLevel
    ) -> bool:
        """Check if request can be auto-approved."""
        if not self.auto_approval_enabled:
            return False
        
        if request.can_auto_approve(user_rbac_level):
            request.status = ApprovalStatus.AUTO_APPROVED
            request.approved_by = "system"
            request.approved_at = datetime.utcnow()
            
            self.approval_metrics["auto_approvals"] += 1
            self.logger.info(f"Auto-approved request {request.request_id}")
            return True
        
        return False
    
    async def approve_request(
        self, 
        request_id: str, 
        approver_id: str,
        approver_rbac_level: RBACLevel
    ) -> bool:
        """Manually approve a request."""
        request = self.pending_approvals.get(request_id)
        if not request:
            return False
        
        if request.status != ApprovalStatus.PENDING:
            return False
        
        if request.is_expired():
            request.status = ApprovalStatus.EXPIRED
            self.approval_metrics["expirations"] += 1
            return False
        
        if not request.can_auto_approve(approver_rbac_level):
            self.logger.warning(f"Approver {approver_id} lacks sufficient RBAC level for request {request_id}")
            return False
        
        request.status = ApprovalStatus.APPROVED
        request.approved_by = approver_id
        request.approved_at = datetime.utcnow()
        
        self.approval_metrics["manual_approvals"] += 1
        self.logger.info(f"Manually approved request {request_id} by {approver_id}")
        return True
    
    async def reject_request(
        self, 
        request_id: str, 
        rejector_id: str, 
        reason: str
    ) -> bool:
        """Reject an approval request."""
        request = self.pending_approvals.get(request_id)
        if not request:
            return False
        
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.REJECTED
        request.rejection_reason = reason
        request.metadata["rejected_by"] = rejector_id
        request.metadata["rejected_at"] = datetime.utcnow().isoformat()
        
        self.approval_metrics["rejections"] += 1
        self.logger.info(f"Rejected request {request_id} by {rejector_id}: {reason}")
        return True
    
    async def cleanup_expired_requests(self):
        """Clean up expired approval requests."""
        expired_requests = [
            request_id for request_id, request in self.pending_approvals.items()
            if request.is_expired() and request.status == ApprovalStatus.PENDING
        ]
        
        for request_id in expired_requests:
            request = self.pending_approvals[request_id]
            request.status = ApprovalStatus.EXPIRED
            self.approval_history.append(request)
            del self.pending_approvals[request_id]
            self.approval_metrics["expirations"] += 1
        
        if expired_requests:
            self.logger.info(f"Cleaned up {len(expired_requests)} expired approval requests")
    
    def get_pending_approvals(self, user_id: Optional[str] = None) -> List[ApprovalRequest]:
        """Get pending approval requests, optionally filtered by user."""
        requests = [
            request for request in self.pending_approvals.values()
            if request.status == ApprovalStatus.PENDING
        ]
        
        if user_id:
            requests = [r for r in requests if r.user_id == user_id]
        
        return sorted(requests, key=lambda x: x.requested_at)


class ExecutionPipeline:
    """
    Main execution pipeline with guardrails, approval workflows, and rollback support.
    """
    
    def __init__(self, tool_service: CopilotToolService):
        self.tool_service = tool_service
        self.logger = logging.getLogger(__name__)
        
        # Components
        self.guardrail_engine = GuardrailEngine()
        self.approval_workflow = ApprovalWorkflow()
        
        # Active executions
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.execution_history: List[ExecutionContext] = []
        
        # Circuit breakers per user
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Configuration
        self.max_concurrent_executions = 10
        self.default_timeout_seconds = 300
        
        # Metrics
        self.pipeline_metrics = {
            "executions_started": 0,
            "executions_completed": 0,
            "executions_failed": 0,
            "rollbacks_performed": 0,
            "guardrail_violations": 0
        }
        
        # Initialize default policies
        self._initialize_default_policies()
    
    def _initialize_default_policies(self):
        """Initialize default guardrail policies."""
        
        # Global timeout policy
        def timeout_policy(context: ExecutionContext, step: PlanStep) -> GuardrailCheck:
            if context.timeout_seconds > 600:  # 10 minutes max
                return GuardrailCheck(
                    passed=False,
                    violation_type=GuardrailViolation.TIMEOUT_EXCEEDED,
                    message=f"Timeout {context.timeout_seconds}s exceeds maximum 600s",
                    severity="error",
                    suggested_action="Reduce timeout or break into smaller operations"
                )
            return GuardrailCheck(passed=True, message="Timeout within limits")
        
        self.guardrail_engine.add_global_policy(timeout_policy)
        
        # Write operation policy
        def write_operation_policy(context: ExecutionContext, step: PlanStep) -> GuardrailCheck:
            if step.tool_name.startswith(("code.apply", "fs.write")) and context.execution_mode != ExecutionMode.DRY_RUN:
                if not step.required_citations:
                    return GuardrailCheck(
                        passed=False,
                        violation_type=GuardrailViolation.INSUFFICIENT_CITATIONS,
                        message="Write operations require citations in non-dry-run mode",
                        severity="error",
                        suggested_action="Add citations or use dry-run mode first"
                    )
            return GuardrailCheck(passed=True, message="Write operation policy satisfied")
        
        self.guardrail_engine.add_global_policy(write_operation_policy)
    
    async def execute_plan(
        self,
        plan: Plan,
        user_id: str,
        session_id: str,
        execution_mode: ExecutionMode = ExecutionMode.DRY_RUN,
        user_rbac_level: RBACLevel = RBACLevel.DEVELOPER,
        privacy_clearance: PrivacyLevel = PrivacyLevel.INTERNAL
    ) -> ExecutionContext:
        """
        Execute a plan with full guardrails and approval workflow.
        
        Args:
            plan: Plan to execute
            user_id: User executing the plan
            session_id: Session identifier
            execution_mode: Execution mode (dry_run, apply, etc.)
            user_rbac_level: User's RBAC level
            privacy_clearance: User's privacy clearance level
            
        Returns:
            Execution context with results and status
        """
        execution_id = str(uuid.uuid4())
        
        # Create execution context
        context = ExecutionContext(
            execution_id=execution_id,
            plan=plan,
            user_id=user_id,
            session_id=session_id,
            execution_mode=execution_mode,
            user_rbac_level=user_rbac_level,
            privacy_clearance=privacy_clearance,
            rbac_permissions={user_rbac_level},
            correlation_id=str(uuid.uuid4())
        )
        
        try:
            # Check concurrent execution limits
            if len(self.active_executions) >= self.max_concurrent_executions:
                context.status = ExecutionStatus.FAILED
                self.logger.error(f"Execution limit reached: {len(self.active_executions)}")
                return context
            
            # Check circuit breaker
            circuit_breaker = self._get_circuit_breaker(user_id)
            if not circuit_breaker.can_execute():
                context.status = ExecutionStatus.FAILED
                self.logger.error(f"Circuit breaker open for user {user_id}")
                return context
            
            # Register execution
            self.active_executions[execution_id] = context
            context.status = ExecutionStatus.RUNNING
            context.started_at = datetime.utcnow()
            
            self.pipeline_metrics["executions_started"] += 1
            
            # Check if plan requires approval
            if plan.requires_approval:
                approval_granted = await self._handle_plan_approval(context)
                if not approval_granted:
                    context.status = ExecutionStatus.FAILED
                    return context
            
            # Execute steps
            await self._execute_steps(context)
            
            # Update final status
            if context.status == ExecutionStatus.RUNNING:
                if all(step.status == "completed" for step in plan.steps):
                    context.status = ExecutionStatus.COMPLETED
                    circuit_breaker.record_success()
                    self.pipeline_metrics["executions_completed"] += 1
                else:
                    context.status = ExecutionStatus.FAILED
                    circuit_breaker.record_failure()
                    self.pipeline_metrics["executions_failed"] += 1
            
            context.completed_at = datetime.utcnow()
            context.total_execution_time = context.completed_at - context.started_at
            
            return context
            
        except Exception as e:
            self.logger.error(f"Plan execution failed: {e}")
            context.status = ExecutionStatus.FAILED
            context.completed_at = datetime.utcnow()
            
            circuit_breaker = self._get_circuit_breaker(user_id)
            circuit_breaker.record_failure()
            self.pipeline_metrics["executions_failed"] += 1
            
            return context
        
        finally:
            # Clean up active execution
            if execution_id in self.active_executions:
                self.execution_history.append(context)
                del self.active_executions[execution_id]
    
    async def _handle_plan_approval(self, context: ExecutionContext) -> bool:
        """Handle plan-level approval if required."""
        try:
            # Create approval request
            approval_request = await self.approval_workflow.create_approval_request(
                plan_id=context.plan.plan_id,
                user_id=context.user_id,
                operation_description=f"Execute plan: {context.plan.name}",
                risk_assessment=context.plan.approval_reason,
                required_approver_level=RBACLevel.ADMIN  # High-risk plans need admin approval
            )
            
            # Check for auto-approval
            if await self.approval_workflow.check_auto_approval(approval_request, context.user_rbac_level):
                return True
            
            # Wait for manual approval (in real implementation, this would be async)
            # For now, we'll simulate based on user RBAC level
            if context.user_rbac_level == RBACLevel.ADMIN:
                await self.approval_workflow.approve_request(
                    approval_request.request_id,
                    context.user_id,
                    context.user_rbac_level
                )
                return True
            else:
                # In real implementation, this would wait for approval or timeout
                self.logger.warning(f"Plan {context.plan.plan_id} requires manual approval")
                return False
            
        except Exception as e:
            self.logger.error(f"Plan approval handling failed: {e}")
            return False
    
    async def _execute_steps(self, context: ExecutionContext):
        """Execute plan steps with guardrails."""
        for step in context.plan.steps:
            if context.status != ExecutionStatus.RUNNING:
                break
            
            try:
                # Check if step is ready to execute
                if not step.is_ready_to_execute(context.completed_steps):
                    continue
                
                # Run guardrail checks
                guardrail_checks = await self.guardrail_engine.check_guardrails(context, step)
                
                # Check for violations
                violations = [check for check in guardrail_checks if not check.passed]
                if violations:
                    self.pipeline_metrics["guardrail_violations"] += len(violations)
                    
                    # Log violations
                    for violation in violations:
                        self.logger.warning(f"Guardrail violation in step {step.step_id}: {violation.message}")
                    
                    # Handle critical violations
                    critical_violations = [v for v in violations if v.severity == "critical"]
                    if critical_violations:
                        step.status = "failed"
                        context.failed_steps.add(step.step_id)
                        continue
                    
                    # Handle approval-required violations
                    approval_required_violations = [
                        v for v in violations 
                        if v.violation_type in [
                            GuardrailViolation.RISK_THRESHOLD_EXCEEDED,
                            GuardrailViolation.RBAC_VIOLATION
                        ]
                    ]
                    
                    if approval_required_violations and not await self._handle_step_approval(context, step, violations):
                        step.status = "failed"
                        context.failed_steps.add(step.step_id)
                        continue
                
                # Execute step
                await self._execute_step(context, step)
                
            except Exception as e:
                self.logger.error(f"Step execution failed: {e}")
                step.status = "failed"
                context.failed_steps.add(step.step_id)
    
    async def _handle_step_approval(
        self, 
        context: ExecutionContext, 
        step: PlanStep, 
        violations: List[GuardrailCheck]
    ) -> bool:
        """Handle step-level approval for guardrail violations."""
        try:
            violation_descriptions = [v.message for v in violations]
            
            approval_request = await self.approval_workflow.create_approval_request(
                plan_id=context.plan.plan_id,
                user_id=context.user_id,
                operation_description=f"Execute step: {step.name}",
                risk_assessment=f"Guardrail violations: {'; '.join(violation_descriptions)}",
                required_approver_level=RBACLevel.ADMIN,
                step_id=step.step_id
            )
            
            # Check for auto-approval
            if await self.approval_workflow.check_auto_approval(approval_request, context.user_rbac_level):
                return True
            
            # For demo purposes, auto-approve if user is admin
            if context.user_rbac_level == RBACLevel.ADMIN:
                await self.approval_workflow.approve_request(
                    approval_request.request_id,
                    context.user_id,
                    context.user_rbac_level
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Step approval handling failed: {e}")
            return False
    
    async def _execute_step(self, context: ExecutionContext, step: PlanStep):
        """Execute a single step with timing and rollback tracking."""
        step_start_time = datetime.utcnow()
        step.started_at = step_start_time
        step.status = "running"
        
        try:
            # Create tool context
            tool_context = ToolContext(
                user_id=context.user_id,
                session_id=context.session_id,
                execution_mode=step.execution_mode,
                rbac_permissions=context.rbac_permissions,
                privacy_clearance=context.privacy_clearance,
                citations=step.required_citations,
                correlation_id=context.correlation_id,
                metadata={
                    "plan_id": context.plan.plan_id,
                    "step_id": step.step_id,
                    "execution_id": context.execution_id
                }
            )
            
            # Execute tool
            result = await self.tool_service.execute_copilot_tool(
                step.tool_name,
                step.parameters,
                tool_context
            )
            
            # Store result
            step.result = result
            context.step_results[step.step_id] = result
            
            # Track rollback data
            if result.can_rollback and result.rollback_data:
                context.rollback_data[step.step_id] = result.rollback_data
            
            # Update step status
            if result.success:
                step.status = "completed"
                context.completed_steps.add(step.step_id)
            else:
                step.status = "failed"
                context.failed_steps.add(step.step_id)
            
            step.completed_at = datetime.utcnow()
            context.step_execution_times[step.step_id] = step.completed_at - step_start_time
            
        except Exception as e:
            self.logger.error(f"Step execution error: {e}")
            step.status = "failed"
            step.completed_at = datetime.utcnow()
            context.failed_steps.add(step.step_id)
            
            # Store error in result
            step.result = ToolResult(
                success=False,
                execution_mode=step.execution_mode,
                error=f"Execution error: {str(e)}",
                error_code=type(e).__name__,
                correlation_id=context.correlation_id
            )
    
    async def rollback_execution(self, execution_id: str) -> bool:
        """
        Rollback a failed or cancelled execution.
        
        Args:
            execution_id: ID of the execution to rollback
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            # Find execution context
            context = None
            if execution_id in self.active_executions:
                context = self.active_executions[execution_id]
            else:
                # Look in history
                for hist_context in self.execution_history:
                    if hist_context.execution_id == execution_id:
                        context = hist_context
                        break
            
            if not context:
                self.logger.error(f"Execution {execution_id} not found for rollback")
                return False
            
            if not context.enable_rollback:
                self.logger.error(f"Rollback not enabled for execution {execution_id}")
                return False
            
            context.status = ExecutionStatus.ROLLBACK_IN_PROGRESS
            
            # Rollback completed steps in reverse order
            rollback_success = True
            completed_steps = [
                step for step in reversed(context.plan.steps)
                if step.step_id in context.completed_steps
            ]
            
            for step in completed_steps:
                try:
                    if step.step_id in context.rollback_data:
                        rollback_data = context.rollback_data[step.step_id]
                        success = await self.tool_service.rollback_operation(context.correlation_id)
                        
                        if not success:
                            self.logger.error(f"Failed to rollback step {step.step_id}")
                            rollback_success = False
                        else:
                            self.logger.info(f"Successfully rolled back step {step.step_id}")
                
                except Exception as e:
                    self.logger.error(f"Rollback error for step {step.step_id}: {e}")
                    rollback_success = False
            
            # Update status
            if rollback_success:
                context.status = ExecutionStatus.ROLLBACK_COMPLETED
                self.pipeline_metrics["rollbacks_performed"] += 1
            else:
                context.status = ExecutionStatus.ROLLBACK_REQUIRED
            
            return rollback_success
            
        except Exception as e:
            self.logger.error(f"Rollback execution failed: {e}")
            return False
    
    def _get_circuit_breaker(self, user_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for user."""
        if user_id not in self.circuit_breakers:
            self.circuit_breakers[user_id] = CircuitBreaker()
        return self.circuit_breakers[user_id]
    
    async def get_execution_status(self, execution_id: str) -> Optional[ExecutionContext]:
        """Get execution status by ID."""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        
        # Look in history
        for context in self.execution_history:
            if context.execution_id == execution_id:
                return context
        
        return None
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an active execution."""
        if execution_id not in self.active_executions:
            return False
        
        context = self.active_executions[execution_id]
        context.status = ExecutionStatus.CANCELLED
        
        self.logger.info(f"Cancelled execution {execution_id}")
        return True
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get comprehensive pipeline metrics."""
        return {
            "pipeline": self.pipeline_metrics.copy(),
            "guardrails": self.guardrail_engine.guardrail_metrics.copy(),
            "approvals": self.approval_workflow.approval_metrics.copy(),
            "active_executions": len(self.active_executions),
            "circuit_breakers": {
                user_id: {
                    "state": cb.state,
                    "failure_count": cb.failure_count,
                    "last_failure": cb.last_failure_time.isoformat() if cb.last_failure_time else None
                }
                for user_id, cb in self.circuit_breakers.items()
            }
        }