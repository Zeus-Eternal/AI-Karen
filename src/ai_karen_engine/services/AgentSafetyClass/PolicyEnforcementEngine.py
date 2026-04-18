"""
Policy Enforcement Engine for the Agent Safety System.

This module provides policy enforcement mechanisms with override capabilities,
violation handling, escalation, and policy testing for agent safety.
"""

import asyncio
import logging
import json
import time
from typing import Any, Dict, List, Optional, Set, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

# Import data structures from agent_safety_types.py to avoid circular imports
from ..agent_safety_types import (
    SafetyLevel, RiskLevel, ValidationResult, Context
)

logger = logging.getLogger(__name__)


class PolicyType(str, Enum):
    """Policy type enumeration."""
    CONTENT_POLICY = "content_policy"
    ACTION_POLICY = "action_policy"
    BEHAVIOR_POLICY = "behavior_policy"
    RESOURCE_POLICY = "resource_policy"
    COMPLIANCE_POLICY = "compliance_policy"


class PolicyStatus(str, Enum):
    """Policy status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    DEPRECATED = "deprecated"


class EnforcementAction(str, Enum):
    """Enforcement action enumeration."""
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"
    ESCALATE = "escalate"
    OVERRIDE = "override"


@dataclass
class Policy:
    """Policy data structure."""
    policy_id: str
    name: str
    description: str
    policy_type: PolicyType
    status: PolicyStatus = PolicyStatus.ACTIVE
    rules: Dict[str, Any] = field(default_factory=dict)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    enforcement_action: EnforcementAction = EnforcementAction.BLOCK
    override_allowed: bool = False
    override_roles: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyViolation:
    """Policy violation data structure."""
    violation_id: str
    policy_id: str
    policy_name: str
    agent_id: str
    violation_type: str
    severity: RiskLevel
    description: str
    detected_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyEnforcementResult:
    """Policy enforcement result data structure."""
    policy_id: str
    policy_name: str
    enforcement_action: EnforcementAction
    is_violation: bool
    is_allowed: bool
    violation: Optional[PolicyViolation] = None
    override_granted: bool = False
    override_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyTestResult:
    """Policy test result data structure."""
    policy_id: str
    test_name: str
    passed: bool
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PolicyValidator(ABC):
    """Abstract base class for policy validators."""
    
    @abstractmethod
    async def validate(self, policy: Policy, context: Context, **kwargs) -> bool:
        """
        Validate a policy against context.
        
        Args:
            policy: Policy to validate
            context: Context for validation
            **kwargs: Additional parameters
            
        Returns:
            True if policy is valid, False otherwise
        """
        pass


class ContentPolicyValidator(PolicyValidator):
    """Validator for content policies."""
    
    async def validate(self, policy: Policy, context: Context, **kwargs) -> bool:
        """
        Validate a content policy.
        
        Args:
            policy: Policy to validate
            context: Context for validation
            **kwargs: Additional parameters including 'content'
            
        Returns:
            True if policy is valid, False otherwise
        """
        content = kwargs.get("content", "")
        
        # Check content against policy rules
        for rule_name, rule_value in policy.rules.items():
            if rule_name == "max_length" and len(content) > rule_value:
                return False
            elif rule_name == "blocked_words" and any(word in content.lower() for word in rule_value):
                return False
            elif rule_name == "allowed_words" and not any(word in content.lower() for word in rule_value):
                return False
        
        return True


class ActionPolicyValidator(PolicyValidator):
    """Validator for action policies."""
    
    async def validate(self, policy: Policy, context: Context, **kwargs) -> bool:
        """
        Validate an action policy.
        
        Args:
            policy: Policy to validate
            context: Context for validation
            **kwargs: Additional parameters including 'action' and 'parameters'
            
        Returns:
            True if policy is valid, False otherwise
        """
        action = kwargs.get("action", "")
        parameters = kwargs.get("parameters", {})
        
        # Check action against policy rules
        for rule_name, rule_value in policy.rules.items():
            if rule_name == "allowed_actions" and action not in rule_value:
                return False
            elif rule_name == "blocked_actions" and action in rule_value:
                return False
            elif rule_name == "required_parameters" and not all(param in parameters for param in rule_value):
                return False
            elif rule_name == "blocked_parameters" and any(param in parameters for param in rule_value):
                return False
        
        return True


class BehaviorPolicyValidator(PolicyValidator):
    """Validator for behavior policies."""
    
    async def validate(self, policy: Policy, context: Context, **kwargs) -> bool:
        """
        Validate a behavior policy.
        
        Args:
            policy: Policy to validate
            context: Context for validation
            **kwargs: Additional parameters including 'behavior_data'
            
        Returns:
            True if policy is valid, False otherwise
        """
        behavior_data = kwargs.get("behavior_data", {})
        metrics = behavior_data.get("metrics", {})
        
        # Check behavior against policy rules
        for rule_name, rule_value in policy.rules.items():
            if rule_name in metrics and metrics[rule_name] > rule_value:
                return False
        
        return True


class PolicyEnforcementEngine(BaseService):
    """
    Policy Enforcement Engine for the Agent Safety System.
    
    This engine provides policy enforcement mechanisms with override capabilities,
    violation handling, escalation, and policy testing for agent safety.
    """
    
    def __init__(self, config: ServiceConfig):
        """Initialize the Policy Enforcement Engine."""
        super().__init__(config)
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Initialize policy validators
        self._validators = {
            PolicyType.CONTENT_POLICY: ContentPolicyValidator(),
            PolicyType.ACTION_POLICY: ActionPolicyValidator(),
            PolicyType.BEHAVIOR_POLICY: BehaviorPolicyValidator()
        }
        
        # Thread-safe data structures
        self._policies: Dict[str, Policy] = {}
        self._violations: List[PolicyViolation] = []
        self._test_results: List[PolicyTestResult] = []
        
        # Thread-safe locks
        self._policies_lock = asyncio.Lock()
        self._violations_lock = asyncio.Lock()
        self._test_results_lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the Policy Enforcement Engine."""
        if self._initialized:
            return
        
        async with self._lock:
            try:
                # Load default policies
                await self._load_default_policies()
                
                self._initialized = True
                logger.info("Policy Enforcement Engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Policy Enforcement Engine: {e}")
                raise RuntimeError(f"Policy Enforcement Engine initialization failed: {e}")
    
    async def _load_default_policies(self) -> None:
        """Load default policies."""
        default_policies = [
            Policy(
                policy_id="default_content_policy",
                name="Default Content Policy",
                description="Default policy for content safety",
                policy_type=PolicyType.CONTENT_POLICY,
                rules={
                    "max_length": 10000,
                    "blocked_words": ["harmful", "dangerous", "unsafe"]
                }
            ),
            Policy(
                policy_id="default_action_policy",
                name="Default Action Policy",
                description="Default policy for action safety",
                policy_type=PolicyType.ACTION_POLICY,
                rules={
                    "blocked_actions": ["execute_code", "system_command"],
                    "required_parameters": ["agent_id"]
                }
            ),
            Policy(
                policy_id="default_behavior_policy",
                name="Default Behavior Policy",
                description="Default policy for behavior safety",
                policy_type=PolicyType.BEHAVIOR_POLICY,
                rules={
                    "error_rate": 0.1,
                    "response_time": 5.0
                }
            )
        ]
        
        for policy in default_policies:
            self._policies[policy.policy_id] = policy
    
    async def add_policy(self, policy: Policy) -> bool:
        """
        Add a policy.
        
        Args:
            policy: Policy to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._policies_lock:
            if policy.policy_id in self._policies:
                return False
            
            self._policies[policy.policy_id] = policy
            return True
    
    async def remove_policy(self, policy_id: str) -> bool:
        """
        Remove a policy.
        
        Args:
            policy_id: ID of the policy to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._policies_lock:
            if policy_id not in self._policies:
                return False
            
            del self._policies[policy_id]
            return True
    
    async def get_policy(self, policy_id: str) -> Optional[Policy]:
        """
        Get a policy by ID.
        
        Args:
            policy_id: ID of the policy to get
            
        Returns:
            Policy if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._policies_lock:
            return self._policies.get(policy_id)
    
    async def get_policies(
        self, 
        policy_type: Optional[PolicyType] = None, 
        status: Optional[PolicyStatus] = None
    ) -> List[Policy]:
        """
        Get policies filtered by type and/or status.
        
        Args:
            policy_type: Optional policy type to filter by
            status: Optional policy status to filter by
            
        Returns:
            List of policies
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._policies_lock:
            policies = list(self._policies.values())
            
            if policy_type:
                policies = [p for p in policies if p.policy_type == policy_type]
            
            if status:
                policies = [p for p in policies if p.status == status]
            
            return policies
    
    async def enforce_policy(
        self,
        policy_id: str,
        context: Context,
        **kwargs
    ) -> PolicyEnforcementResult:
        """
        Enforce a policy.
        
        Args:
            policy_id: ID of the policy to enforce
            context: Context for enforcement
            **kwargs: Additional parameters for validation
            
        Returns:
            Policy enforcement result
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get policy
            policy = await self.get_policy(policy_id)
            if not policy:
                return PolicyEnforcementResult(
                    policy_id=policy_id,
                    policy_name="Unknown Policy",
                    enforcement_action=EnforcementAction.BLOCK,
                    is_violation=True,
                    is_allowed=False,
                    violation=PolicyViolation(
                        violation_id=f"violation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                        policy_id=policy_id,
                        policy_name="Unknown Policy",
                        agent_id=context.agent_id,
                        violation_type="policy_not_found",
                        severity=RiskLevel.HIGH_RISK,
                        description=f"Policy {policy_id} not found"
                    )
                )
            
            # Check if policy is active
            if policy.status != PolicyStatus.ACTIVE:
                return PolicyEnforcementResult(
                    policy_id=policy_id,
                    policy_name=policy.name,
                    enforcement_action=EnforcementAction.ALLOW,
                    is_violation=False,
                    is_allowed=True
                )
            
            # Get validator for policy type
            validator = self._validators.get(policy.policy_type)
            if not validator:
                return PolicyEnforcementResult(
                    policy_id=policy_id,
                    policy_name=policy.name,
                    enforcement_action=EnforcementAction.BLOCK,
                    is_violation=True,
                    is_allowed=False,
                    violation=PolicyViolation(
                        violation_id=f"violation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                        policy_id=policy_id,
                        policy_name=policy.name,
                        agent_id=context.agent_id,
                        violation_type="validator_not_found",
                        severity=RiskLevel.HIGH_RISK,
                        description=f"Validator for policy type {policy.policy_type} not found"
                    )
                )
            
            # Validate policy
            is_valid = await validator.validate(policy, context, **kwargs)
            
            # Create enforcement result
            if is_valid:
                return PolicyEnforcementResult(
                    policy_id=policy_id,
                    policy_name=policy.name,
                    enforcement_action=EnforcementAction.ALLOW,
                    is_violation=False,
                    is_allowed=True
                )
            else:
                # Create violation
                violation = PolicyViolation(
                    violation_id=f"violation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                    policy_id=policy_id,
                    policy_name=policy.name,
                    agent_id=context.agent_id,
                    violation_type="policy_violation",
                    severity=RiskLevel.MEDIUM_RISK,
                    description=f"Policy {policy.name} violated"
                )
                
                # Record violation
                await self._record_violation(violation)
                
                # Determine enforcement action
                enforcement_action = policy.enforcement_action
                
                # Check for override
                override_granted = False
                override_reason = None
                
                if policy.override_allowed and kwargs.get("request_override", False):
                    override_role = kwargs.get("override_role", "")
                    if override_role in policy.override_roles:
                        override_granted = True
                        override_reason = f"Override granted for role {override_role}"
                        enforcement_action = EnforcementAction.OVERRIDE
                
                return PolicyEnforcementResult(
                    policy_id=policy_id,
                    policy_name=policy.name,
                    enforcement_action=enforcement_action,
                    is_violation=True,
                    is_allowed=enforcement_action in [EnforcementAction.ALLOW, EnforcementAction.OVERRIDE],
                    violation=violation,
                    override_granted=override_granted,
                    override_reason=override_reason
                )
        except Exception as e:
            logger.error(f"Error enforcing policy {policy_id}: {e}")
            
            # Create violation for error
            violation = PolicyViolation(
                violation_id=f"violation_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                policy_id=policy_id,
                policy_name="Error",
                agent_id=context.agent_id,
                violation_type="enforcement_error",
                severity=RiskLevel.CRITICAL_RISK,
                description=f"Error enforcing policy: {str(e)}"
            )
            
            return PolicyEnforcementResult(
                policy_id=policy_id,
                policy_name="Error",
                enforcement_action=EnforcementAction.BLOCK,
                is_violation=True,
                is_allowed=False,
                violation=violation
            )
    
    async def enforce_policies(
        self,
        policy_type: PolicyType,
        context: Context,
        **kwargs
    ) -> List[PolicyEnforcementResult]:
        """
        Enforce all policies of a given type.
        
        Args:
            policy_type: Type of policies to enforce
            context: Context for enforcement
            **kwargs: Additional parameters for validation
            
        Returns:
            List of policy enforcement results
        """
        if not self._initialized:
            await self.initialize()
        
        # Get policies of the specified type
        policies = await self.get_policies(policy_type=policy_type, status=PolicyStatus.ACTIVE)
        
        # Enforce each policy
        results = []
        for policy in policies:
            result = await self.enforce_policy(policy.policy_id, context, **kwargs)
            results.append(result)
        
        return results
    
    async def test_policy(
        self,
        policy_id: str,
        test_name: str,
        test_data: Dict[str, Any]
    ) -> PolicyTestResult:
        """
        Test a policy.
        
        Args:
            policy_id: ID of the policy to test
            test_name: Name of the test
            test_data: Test data
            
        Returns:
            Policy test result
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get policy
            policy = await self.get_policy(policy_id)
            if not policy:
                return PolicyTestResult(
                    policy_id=policy_id,
                    test_name=test_name,
                    passed=False,
                    message=f"Policy {policy_id} not found"
                )
            
            # Create context for test
            context = Context(agent_id="test_agent")
            
            # Get validator for policy type
            validator = self._validators.get(policy.policy_type)
            if not validator:
                return PolicyTestResult(
                    policy_id=policy_id,
                    test_name=test_name,
                    passed=False,
                    message=f"Validator for policy type {policy.policy_type} not found"
                )
            
            # Test policy
            is_valid = await validator.validate(policy, context, **test_data)
            
            # Create test result
            if is_valid:
                return PolicyTestResult(
                    policy_id=policy_id,
                    test_name=test_name,
                    passed=True,
                    message="Policy test passed"
                )
            else:
                return PolicyTestResult(
                    policy_id=policy_id,
                    test_name=test_name,
                    passed=False,
                    message="Policy test failed"
                )
        except Exception as e:
            logger.error(f"Error testing policy {policy_id}: {e}")
            
            return PolicyTestResult(
                policy_id=policy_id,
                test_name=test_name,
                passed=False,
                message=f"Error testing policy: {str(e)}"
            )
    
    async def get_violations(
        self,
        agent_id: Optional[str] = None,
        policy_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[PolicyViolation]:
        """
        Get policy violations.
        
        Args:
            agent_id: Optional agent ID to filter by
            policy_id: Optional policy ID to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            limit: Maximum number of violations to return
            
        Returns:
            List of policy violations
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._violations_lock:
            violations = self._violations.copy()
            
            # Filter by agent ID
            if agent_id:
                violations = [v for v in violations if v.agent_id == agent_id]
            
            # Filter by policy ID
            if policy_id:
                violations = [v for v in violations if v.policy_id == policy_id]
            
            # Filter by time range
            if start_time:
                violations = [v for v in violations if v.detected_at >= start_time]
            
            if end_time:
                violations = [v for v in violations if v.detected_at <= end_time]
            
            # Sort by timestamp (newest first)
            violations.sort(key=lambda x: x.detected_at, reverse=True)
            
            # Limit results
            return violations[:limit]
    
    async def get_test_results(
        self,
        policy_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[PolicyTestResult]:
        """
        Get policy test results.
        
        Args:
            policy_id: Optional policy ID to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            limit: Maximum number of test results to return
            
        Returns:
            List of policy test results
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._test_results_lock:
            test_results = self._test_results.copy()
            
            # Filter by policy ID
            if policy_id:
                test_results = [t for t in test_results if t.policy_id == policy_id]
            
            # Filter by time range
            if start_time:
                test_results = [t for t in test_results if t.timestamp >= start_time]
            
            if end_time:
                test_results = [t for t in test_results if t.timestamp <= end_time]
            
            # Sort by timestamp (newest first)
            test_results.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Limit results
            return test_results[:limit]
    
    async def _record_violation(self, violation: PolicyViolation) -> None:
        """
        Record a policy violation.
        
        Args:
            violation: Policy violation to record
        """
        async with self._violations_lock:
            self._violations.append(violation)
            
            # Limit violations list size
            if len(self._violations) > 10000:
                self._violations = self._violations[-10000:]
    
    async def _record_test_result(self, test_result: PolicyTestResult) -> None:
        """
        Record a policy test result.
        
        Args:
            test_result: Policy test result to record
        """
        async with self._test_results_lock:
            self._test_results.append(test_result)
            
            # Limit test results list size
            if len(self._test_results) > 10000:
                self._test_results = self._test_results[-10000:]
    
    async def health_check(self) -> bool:
        """Check health of the Policy Enforcement Engine."""
        if not self._initialized:
            return False
        
        try:
            # Check if validators are available
            if not self._validators:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Policy Enforcement Engine health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Policy Enforcement Engine."""
        if not self._initialized:
            await self.initialize()
    
    async def stop(self) -> None:
        """Stop the Policy Enforcement Engine."""
        # Clean up resources if needed
        self._initialized = False