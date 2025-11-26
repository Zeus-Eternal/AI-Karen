"""
Agent Safety Service

This service provides safety mechanisms for agents, including content filtering,
guardrails, and safety monitoring.
"""

from typing import Dict, List, Any, Optional, Union, Callable, Set
import logging
from dataclasses import dataclass
from enum import Enum
import re
import json

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """Enumeration of safety levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyViolationType(Enum):
    """Enumeration of safety violation types."""
    HATE_SPEECH = "hate_speech"
    HARASSMENT = "harassment"
    VIOLENCE = "violence"
    SELF_HARM = "self_harm"
    SEXUAL_CONTENT = "sexual_content"
    ILLEGAL_ACTIVITIES = "illegal_activities"
    MISINFORMATION = "misinformation"
    PRIVACY_VIOLATION = "privacy_violation"
    SECURITY_RISK = "security_risk"
    CUSTOM_VIOLATION = "custom_violation"


@dataclass
class SafetyPolicy:
    """Represents a safety policy."""
    name: str
    description: str
    violation_types: List[SafetyViolationType]
    level: SafetyLevel
    enabled: bool = True
    action: str = "block"  # block, warn, log, custom
    custom_action: Optional[Callable] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SafetyViolation:
    """Represents a safety violation."""
    violation_type: SafetyViolationType
    severity: SafetyLevel
    description: str
    content: str
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SafetyCheckResult:
    """Result of a safety check."""
    is_safe: bool
    violations: List[SafetyViolation]
    overall_risk_level: SafetyLevel
    metadata: Optional[Dict[str, Any]] = None


class AgentSafety:
    """
    Provides safety mechanisms for agents.
    
    This class is responsible for:
    - Content filtering and safety checks
    - Guardrails for agent behavior
    - Safety monitoring and violation handling
    - Safety policy management
    """
    
    def __init__(self):
        self._policies: Dict[str, SafetyPolicy] = {}
        self._violation_patterns: Dict[SafetyViolationType, List[str]] = {}
        self._violation_handlers: Dict[SafetyViolationType, Callable] = {}
        
        # Initialize default violation patterns
        self._initialize_default_patterns()
        
        # Initialize default policies
        self._initialize_default_policies()
        
        # Callbacks for safety events
        self._on_violation: Optional[Callable[[SafetyViolation], None]] = None
        self._on_policy_triggered: Optional[Callable[[SafetyPolicy, SafetyViolation], None]] = None
    
    def register_policy(self, policy: SafetyPolicy) -> None:
        """Register a safety policy."""
        self._policies[policy.name] = policy
        logger.info(f"Registered safety policy: {policy.name}")
    
    def unregister_policy(self, policy_name: str) -> bool:
        """Unregister a safety policy."""
        if policy_name in self._policies:
            del self._policies[policy_name]
            logger.info(f"Unregistered safety policy: {policy_name}")
            return True
        else:
            logger.warning(f"Attempted to unregister non-existent policy: {policy_name}")
            return False
    
    def get_policy(self, policy_name: str) -> Optional[SafetyPolicy]:
        """Get a safety policy by name."""
        return self._policies.get(policy_name)
    
    def get_all_policies(self) -> Dict[str, SafetyPolicy]:
        """Get all safety policies."""
        return self._policies.copy()
    
    def enable_policy(self, policy_name: str) -> bool:
        """Enable a safety policy."""
        policy = self._policies.get(policy_name)
        if policy:
            policy.enabled = True
            logger.info(f"Enabled safety policy: {policy_name}")
            return True
        else:
            logger.warning(f"Attempted to enable non-existent policy: {policy_name}")
            return False
    
    def disable_policy(self, policy_name: str) -> bool:
        """Disable a safety policy."""
        policy = self._policies.get(policy_name)
        if policy:
            policy.enabled = False
            logger.info(f"Disabled safety policy: {policy_name}")
            return True
        else:
            logger.warning(f"Attempted to disable non-existent policy: {policy_name}")
            return False
    
    def add_violation_pattern(self, violation_type: SafetyViolationType, pattern: str) -> None:
        """Add a violation pattern for a specific violation type."""
        if violation_type not in self._violation_patterns:
            self._violation_patterns[violation_type] = []
        self._violation_patterns[violation_type].append(pattern)
        logger.debug(f"Added violation pattern for {violation_type.value}: {pattern}")
    
    def remove_violation_pattern(self, violation_type: SafetyViolationType, pattern: str) -> bool:
        """Remove a violation pattern."""
        if violation_type in self._violation_patterns and pattern in self._violation_patterns[violation_type]:
            self._violation_patterns[violation_type].remove(pattern)
            logger.debug(f"Removed violation pattern for {violation_type.value}: {pattern}")
            return True
        else:
            logger.warning(f"Attempted to remove non-existent violation pattern: {pattern}")
            return False
    
    def register_violation_handler(self, violation_type: SafetyViolationType, handler: Callable) -> None:
        """Register a handler for a specific violation type."""
        self._violation_handlers[violation_type] = handler
        logger.info(f"Registered violation handler for {violation_type.value}")
    
    def check_content_safety(self, content: str, policy_names: Optional[List[str]] = None) -> SafetyCheckResult:
        """
        Check if content is safe according to the specified policies.
        
        Args:
            content: Content to check
            policy_names: List of policy names to check against. If None, all enabled policies are used.
            
        Returns:
            Safety check result
        """
        violations = []
        
        # Determine which policies to check
        if policy_names is None:
            policies = [p for p in self._policies.values() if p.enabled]
        else:
            policies = [self._policies[name] for name in policy_names if name in self._policies]
        
        # Check each policy
        for policy in policies:
            for violation_type in policy.violation_types:
                if self._check_violation(content, violation_type):
                    violation = SafetyViolation(
                        violation_type=violation_type,
                        severity=policy.level,
                        description=f"Content violates {policy.name} policy",
                        content=content
                    )
                    violations.append(violation)
        
        # Determine overall risk level
        overall_risk_level = SafetyLevel.LOW
        for violation in violations:
            if violation.severity.value > overall_risk_level.value:
                overall_risk_level = violation.severity
        
        # Create result
        result = SafetyCheckResult(
            is_safe=len(violations) == 0,
            violations=violations,
            overall_risk_level=overall_risk_level
        )
        
        # Handle violations
        for violation in violations:
            self._handle_violation(violation)
            
            # Call policy triggered callback if set
            if self._on_policy_triggered:
                for policy in policies:
                    if violation.violation_type in policy.violation_types:
                        self._on_policy_triggered(policy, violation)
                        break
        
        return result
    
    def check_agent_action_safety(self, agent_id: str, action: Dict[str, Any], policy_names: Optional[List[str]] = None) -> SafetyCheckResult:
        """
        Check if an agent action is safe according to the specified policies.
        
        Args:
            agent_id: ID of the agent
            action: Action to check
            policy_names: List of policy names to check against. If None, all enabled policies are used.
            
        Returns:
            Safety check result
        """
        # Convert action to JSON string for content checking
        action_json = json.dumps(action, default=str)
        
        # Add agent context
        context = {"agent_id": agent_id}
        
        # Check content safety
        result = self.check_content_safety(action_json, policy_names)
        
        # Add context to violations
        for violation in result.violations:
            violation.context = context
        
        return result
    
    def sanitize_content(self, content: str, policy_names: Optional[List[str]] = None) -> str:
        """
        Sanitize content by removing or redacting violations.
        
        Args:
            content: Content to sanitize
            policy_names: List of policy names to check against. If None, all enabled policies are used.
            
        Returns:
            Sanitized content
        """
        result = self.check_content_safety(content, policy_names)
        
        if result.is_safe:
            return content
        
        sanitized = content
        
        # Redact violations
        for violation in result.violations:
            if violation.violation_type in self._violation_patterns:
                for pattern in self._violation_patterns[violation.violation_type]:
                    sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def get_safety_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about safety checks and violations.
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_policies": len(self._policies),
            "enabled_policies": sum(1 for p in self._policies.values() if p.enabled),
            "violation_types": {vt.value: len(patterns) for vt, patterns in self._violation_patterns.items()},
            "registered_handlers": len(self._violation_handlers)
        }
        
        return stats
    
    def set_safety_callbacks(
        self,
        on_violation: Optional[Callable[[SafetyViolation], None]] = None,
        on_policy_triggered: Optional[Callable[[SafetyPolicy, SafetyViolation], None]] = None
    ) -> None:
        """Set callbacks for safety events."""
        self._on_violation = on_violation
        self._on_policy_triggered = on_policy_triggered
    
    def _initialize_default_patterns(self) -> None:
        """Initialize default violation patterns."""
        # Hate speech patterns
        self._violation_patterns[SafetyViolationType.HATE_SPEECH] = [
            r"\b(hate|discrimination|racism|sexism|homophobia|transphobia|xenophobia)\b",
            r"\b(slur|derogatory|offensive|insult)\b"
        ]
        
        # Harassment patterns
        self._violation_patterns[SafetyViolationType.HARASSMENT] = [
            r"\b(harass|bully|stalk|threaten|intimidate)\b",
            r"\b(unwanted|inappropriate|offensive)\s+(contact|attention|behavior)\b"
        ]
        
        # Violence patterns
        self._violation_patterns[SafetyViolationType.VIOLENCE] = [
            r"\b(violence|violent|attack|kill|murder|assault)\b",
            r"\b(weapon|gun|knife|bomb|explosive)\b"
        ]
        
        # Self-harm patterns
        self._violation_patterns[SafetyViolationType.SELF_HARM] = [
            r"\b(self.harm|suicide|suicidal|kill\s+myself)\b",
            r"\b(depression|depressed|hopeless|worthless)\b"
        ]
        
        # Sexual content patterns
        self._violation_patterns[SafetyViolationType.SEXUAL_CONTENT] = [
            r"\b(porn|pornography|explicit|nude|naked)\b",
            r"\b(sexual|sexually)\s+(explicit|content|material)\b"
        ]
        
        # Illegal activities patterns
        self._violation_patterns[SafetyViolationType.ILLEGAL_ACTIVITIES] = [
            r"\b(illegal|criminal|unlawful|prohibited)\b",
            r"\b(drug|drugs|substance|narcotic)\s+(abuse|use|trafficking)\b"
        ]
        
        # Misinformation patterns
        self._violation_patterns[SafetyViolationType.MISINFORMATION] = [
            r"\b(fake|false|misleading|deceptive)\s+(news|information|claim)\b",
            r"\b(conspiracy|conspiracy\s+theory|hoax)\b"
        ]
        
        # Privacy violation patterns
        self._violation_patterns[SafetyViolationType.PRIVACY_VIOLATION] = [
            r"\b(private|confidential|sensitive|personal)\s+(information|data)\b",
            r"\b(SSN|social\s+security|credit\s+card|password)\b"
        ]
        
        # Security risk patterns
        self._violation_patterns[SafetyViolationType.SECURITY_RISK] = [
            r"\b(security|vulnerability|exploit|breach)\b",
            r"\b(hack|hacking|malware|virus|phishing)\b"
        ]
    
    def _initialize_default_policies(self) -> None:
        """Initialize default safety policies."""
        # Content safety policy
        content_policy = SafetyPolicy(
            name="content_safety",
            description="General content safety policy",
            violation_types=[
                SafetyViolationType.HATE_SPEECH,
                SafetyViolationType.HARASSMENT,
                SafetyViolationType.VIOLENCE,
                SafetyViolationType.SELF_HARM,
                SafetyViolationType.SEXUAL_CONTENT,
                SafetyViolationType.ILLEGAL_ACTIVITIES,
                SafetyViolationType.MISINFORMATION
            ],
            level=SafetyLevel.MEDIUM,
            action="block"
        )
        self.register_policy(content_policy)
        
        # Privacy policy
        privacy_policy = SafetyPolicy(
            name="privacy_protection",
            description="Privacy protection policy",
            violation_types=[
                SafetyViolationType.PRIVACY_VIOLATION
            ],
            level=SafetyLevel.HIGH,
            action="block"
        )
        self.register_policy(privacy_policy)
        
        # Security policy
        security_policy = SafetyPolicy(
            name="security_protection",
            description="Security protection policy",
            violation_types=[
                SafetyViolationType.SECURITY_RISK
            ],
            level=SafetyLevel.CRITICAL,
            action="block"
        )
        self.register_policy(security_policy)
    
    def _check_violation(self, content: str, violation_type: SafetyViolationType) -> bool:
        """Check if content contains a violation of the specified type."""
        if violation_type not in self._violation_patterns:
            return False
        
        for pattern in self._violation_patterns[violation_type]:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def _handle_violation(self, violation: SafetyViolation) -> None:
        """Handle a safety violation."""
        logger.warning(f"Safety violation detected: {violation.violation_type.value} - {violation.description}")
        
        # Call violation callback if set
        if self._on_violation:
            self._on_violation(violation)
        
        # Call violation type handler if registered
        if violation.violation_type in self._violation_handlers:
            self._violation_handlers[violation.violation_type](violation)