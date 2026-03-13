"""
Content Safety Checker for Safety Middleware.

This module provides content safety checking functionality, including
keyword matching, pattern detection, and ML-based content analysis.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from src.services.agents.agent_safety_types import (
    SafetyLevel, RiskLevel, ValidationResult, ContentType
)

logger = logging.getLogger(__name__)


class ContentSafetyResult(str, Enum):
    """Enum representing content safety results."""
    SAFE = "safe"
    WARNING = "warning"
    BLOCKED = "blocked"


@dataclass
class SafetyRule:
    """Data class for safety rules."""
    
    rule_id: str
    name: str
    description: str
    pattern: str
    risk_level: RiskLevel
    content_types: List[ContentType]
    is_active: bool = True
    flags: List[str] = field(default_factory=list)


@dataclass
class PatternMatch:
    """Data class for pattern matches."""
    
    rule_id: str
    rule_name: str
    matched_text: str
    risk_level: RiskLevel
    start_pos: int
    end_pos: int


class ContentSafetyChecker:
    """
    Content Safety Checker for Safety Middleware.
    
    This class provides content safety checking functionality, including
    keyword matching, pattern detection, and ML-based content analysis.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Content Safety Checker."""
        self.config = config or {}
        
        # Initialize safety rules
        self._safety_rules: Dict[str, SafetyRule] = {}
        self._load_default_rules()
        
        # Load custom rules from config
        custom_rules = self.config.get("custom_rules", {})
        for rule_id, rule_data in custom_rules.items():
            try:
                self.add_rule(SafetyRule(
                    rule_id=rule_id,
                    name=rule_data.get("name", rule_id),
                    description=rule_data.get("description", ""),
                    pattern=rule_data.get("pattern", ""),
                    risk_level=RiskLevel(rule_data.get("risk_level", "medium_risk")),
                    content_types=[
                        ContentType(ct) for ct in rule_data.get("content_types", ["text"])
                    ],
                    is_active=rule_data.get("is_active", True),
                    flags=rule_data.get("flags", [])
                ))
            except Exception as e:
                logger.warning(f"Failed to load custom rule {rule_id}: {e}")
        
        # Compile regex patterns for performance
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._compile_patterns()
        
        logger.info(f"Content Safety Checker initialized with {len(self._safety_rules)} rules")
    
    def _load_default_rules(self) -> None:
        """Load default safety rules."""
        default_rules = [
            SafetyRule(
                rule_id="harmful_content",
                name="Harmful Content",
                description="Detects harmful or dangerous content",
                pattern=r"\b(harmful|dangerous|unsafe|toxic|hate|violence|abuse)\b",
                risk_level=RiskLevel.HIGH_RISK,
                content_types=[ContentType.TEXT],
                flags=["harmful", "dangerous"]
            ),
            SafetyRule(
                rule_id="pii_data",
                name="PII Data",
                description="Detects personally identifiable information",
                pattern=r"\b(\d{3}-\d{2}-\d{4}|\d{9})\b",  # SSN pattern
                risk_level=RiskLevel.MEDIUM_RISK,
                content_types=[ContentType.TEXT],
                flags=["pii", "personal_data"]
            ),
            SafetyRule(
                rule_id="credit_card",
                name="Credit Card Numbers",
                description="Detects credit card numbers",
                pattern=r"\b(\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4})\b",
                risk_level=RiskLevel.HIGH_RISK,
                content_types=[ContentType.TEXT],
                flags=["financial", "pii"]
            ),
            SafetyRule(
                rule_id="sql_injection",
                name="SQL Injection",
                description="Detects potential SQL injection attempts",
                pattern=r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC|ALTER)\b|(''|\';|';|\"|\";|\"|--|#|\/\*|\*\/)",
                risk_level=RiskLevel.CRITICAL_RISK,
                content_types=[ContentType.TEXT],
                flags=["security", "injection"]
            ),
            SafetyRule(
                rule_id="xss",
                name="XSS Attacks",
                description="Detects potential XSS attacks",
                pattern=r"(<script|javascript:|on\w+\s*=|eval\(|expression\()",
                risk_level=RiskLevel.CRITICAL_RISK,
                content_types=[ContentType.TEXT],
                flags=["security", "xss"]
            ),
            SafetyRule(
                rule_id="command_injection",
                name="Command Injection",
                description="Detects potential command injection attempts",
                pattern=r"(;|\||&|\$\(|`|>|<|\${)",
                risk_level=RiskLevel.CRITICAL_RISK,
                content_types=[ContentType.TEXT],
                flags=["security", "injection"]
            ),
            SafetyRule(
                rule_id="path_traversal",
                name="Path Traversal",
                description="Detects potential path traversal attempts",
                pattern=r"(\.\./|\.\.\\\)",
                risk_level=RiskLevel.HIGH_RISK,
                content_types=[ContentType.TEXT],
                flags=["security", "path_traversal"]
            ),
            SafetyRule(
                rule_id="email_addresses",
                name="Email Addresses",
                description="Detects email addresses",
                pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                risk_level=RiskLevel.LOW_RISK,
                content_types=[ContentType.TEXT],
                flags=["pii", "contact"]
            ),
            SafetyRule(
                rule_id="phone_numbers",
                name="Phone Numbers",
                description="Detects phone numbers",
                pattern=r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b",
                risk_level=RiskLevel.LOW_RISK,
                content_types=[ContentType.TEXT],
                flags=["pii", "contact"]
            ),
            SafetyRule(
                rule_id="api_keys",
                name="API Keys",
                description="Detects potential API keys",
                pattern=r"\b[A-Za-z0-9]{32,}\b",
                risk_level=RiskLevel.HIGH_RISK,
                content_types=[ContentType.TEXT],
                flags=["security", "api_key"]
            )
        ]
        
        for rule in default_rules:
            self._safety_rules[rule.rule_id] = rule
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for better performance."""
        for rule_id, rule in self._safety_rules.items():
            if rule.is_active:
                try:
                    self._compiled_patterns[rule_id] = re.compile(
                        rule.pattern, 
                        re.IGNORECASE | re.MULTILINE
                    )
                except re.error as e:
                    logger.warning(f"Failed to compile pattern for rule {rule_id}: {e}")
                    rule.is_active = False
    
    def add_rule(self, rule: SafetyRule) -> bool:
        """
        Add a new safety rule.
        
        Args:
            rule: Safety rule to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        try:
            self._safety_rules[rule.rule_id] = rule
            
            # Compile pattern if rule is active
            if rule.is_active:
                self._compiled_patterns[rule.rule_id] = re.compile(
                    rule.pattern, 
                    re.IGNORECASE | re.MULTILINE
                )
            
            logger.info(f"Added safety rule: {rule.name} ({rule.rule_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to add safety rule {rule.rule_id}: {e}")
            return False
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a safety rule.
        
        Args:
            rule_id: ID of the rule to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        try:
            if rule_id in self._safety_rules:
                del self._safety_rules[rule_id]
                
                # Remove compiled pattern
                if rule_id in self._compiled_patterns:
                    del self._compiled_patterns[rule_id]
                
                logger.info(f"Removed safety rule: {rule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove safety rule {rule_id}: {e}")
            return False
    
    def get_rule(self, rule_id: str) -> Optional[SafetyRule]:
        """
        Get a safety rule.
        
        Args:
            rule_id: ID of the rule to get
            
        Returns:
            Safety rule if found, None otherwise
        """
        return self._safety_rules.get(rule_id)
    
    def get_rules(self, active_only: bool = True) -> List[SafetyRule]:
        """
        Get safety rules.
        
        Args:
            active_only: Whether to return only active rules
            
        Returns:
            List of safety rules
        """
        rules = list(self._safety_rules.values())
        if active_only:
            rules = [rule for rule in rules if rule.is_active]
        return rules
    
    def check_content_safety(
        self, 
        content: str, 
        content_type: ContentType = ContentType.TEXT
    ) -> ValidationResult:
        """
        Check content safety against all active rules.
        
        Args:
            content: Content to check
            content_type: Type of content
            
        Returns:
            Validation result with safety assessment
        """
        if not content or not isinstance(content, str):
            return ValidationResult(
                is_safe=True,
                confidence=1.0,
                risk_level=RiskLevel.SAFE
            )
        
        matches = []
        violations = []
        is_safe = True
        confidence = 1.0
        risk_level = RiskLevel.SAFE
        
        # Check against all active rules
        for rule_id, rule in self._safety_rules.items():
            if not rule.is_active or content_type not in rule.content_types:
                continue
            
            # Get compiled pattern
            pattern = self._compiled_patterns.get(rule_id)
            if not pattern:
                continue
            
            # Find all matches
            for match in pattern.finditer(content):
                match_obj = PatternMatch(
                    rule_id=rule_id,
                    rule_name=rule.name,
                    matched_text=match.group(),
                    risk_level=rule.risk_level,
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                matches.append(match_obj)
                
                # Add violation
                violations.append(f"Matched rule: {rule.name}")
                
                # Update risk level if this rule has higher risk
                if rule.risk_level.value > risk_level.value:
                    risk_level = rule.risk_level
                
                # Update confidence based on match
                confidence = min(confidence, 0.9)
                
                # If high or critical risk, content is not safe
                if rule.risk_level in [RiskLevel.HIGH_RISK, RiskLevel.CRITICAL_RISK]:
                    is_safe = False
        
        # If no matches, content is safe
        if not matches:
            return ValidationResult(
                is_safe=True,
                confidence=1.0,
                risk_level=RiskLevel.SAFE
            )
        
        return ValidationResult(
            is_safe=is_safe,
            confidence=confidence,
            risk_level=risk_level,
            violations=violations,
            matched_patterns=[match.matched_text for match in matches]
        )
    
    def sanitize_content(
        self, 
        content: str, 
        content_type: ContentType = ContentType.TEXT,
        method: str = "redact"
    ) -> str:
        """
        Sanitize content by removing or redacting unsafe content.
        
        Args:
            content: Content to sanitize
            content_type: Type of content
            method: Sanitization method ("redact" or "remove")
            
        Returns:
            Sanitized content
        """
        if not content or not isinstance(content, str):
            return content
        
        sanitized = content
        
        # Apply all active rules
        for rule_id, rule in self._safety_rules.items():
            if not rule.is_active or content_type not in rule.content_types:
                continue
            
            # Get compiled pattern
            pattern = self._compiled_patterns.get(rule_id)
            if not pattern:
                continue
            
            if method == "redact":
                # Redact matched content
                sanitized = pattern.sub("[REDACTED]", sanitized)
            elif method == "remove":
                # Remove matched content
                sanitized = pattern.sub("", sanitized)
        
        return sanitized
    
    def analyze_content(
        self, 
        content: str, 
        content_type: ContentType = ContentType.TEXT
    ) -> Dict[str, Any]:
        """
        Analyze content and return detailed safety information.
        
        Args:
            content: Content to analyze
            content_type: Type of content
            
        Returns:
            Dictionary with detailed safety analysis
        """
        # Check content safety
        result = self.check_content_safety(content, content_type)
        
        # Find all matches
        matches = []
        for rule_id, rule in self._safety_rules.items():
            if not rule.is_active or content_type not in rule.content_types:
                continue
            
            # Get compiled pattern
            pattern = self._compiled_patterns.get(rule_id)
            if not pattern:
                continue
            
            # Find all matches
            for match in pattern.finditer(content):
                match_obj = PatternMatch(
                    rule_id=rule_id,
                    rule_name=rule.name,
                    matched_text=match.group(),
                    risk_level=rule.risk_level,
                    start_pos=match.start(),
                    end_pos=match.end()
                )
                matches.append(match_obj)
        
        # Group matches by risk level
        matches_by_risk = {}
        for match in matches:
            risk_level = match.risk_level.value
            if risk_level not in matches_by_risk:
                matches_by_risk[risk_level] = []
            matches_by_risk[risk_level].append(match)
        
        return {
            "is_safe": result.is_safe,
            "confidence": result.confidence,
            "risk_level": result.risk_level.value,
            "violations": result.violations,
            "matched_patterns": result.matched_patterns,
            "total_matches": len(matches),
            "matches_by_risk": matches_by_risk,
            "content_length": len(content),
            "content_type": content_type.value
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the safety checker.
        
        Returns:
            Dictionary with safety checker statistics
        """
        active_rules = [rule for rule in self._safety_rules.values() if rule.is_active]
        inactive_rules = [rule for rule in self._safety_rules.values() if not rule.is_active]
        
        # Group rules by risk level
        rules_by_risk = {}
        for rule in self._safety_rules.values():
            risk_level = rule.risk_level.value
            if risk_level not in rules_by_risk:
                rules_by_risk[risk_level] = []
            rules_by_risk[risk_level].append(rule)
        
        # Group rules by content type
        rules_by_content_type = {}
        for rule in self._safety_rules.values():
            for content_type in rule.content_types:
                ct = content_type.value
                if ct not in rules_by_content_type:
                    rules_by_content_type[ct] = []
                rules_by_content_type[ct].append(rule)
        
        return {
            "total_rules": len(self._safety_rules),
            "active_rules": len(active_rules),
            "inactive_rules": len(inactive_rules),
            "compiled_patterns": len(self._compiled_patterns),
            "rules_by_risk": {
                risk_level: len(rules)
                for risk_level, rules in rules_by_risk.items()
            },
            "rules_by_content_type": {
                content_type: len(rules)
                for content_type, rules in rules_by_content_type.items()
            }
        }