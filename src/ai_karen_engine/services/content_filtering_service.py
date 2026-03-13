"""
Content Filtering Service for CoPilot Architecture.

This service provides comprehensive content filtering functionality including
text analysis, pattern matching, and ML-based content safety validation.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ai_karen_engine.core.services.base import BaseService, ServiceConfig
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.middleware.content_safety_checker import (
    ContentSafetyChecker
)
from src.services.agents.agent_safety_types import (
    SafetyLevel, RiskLevel, ValidationResult, ContentType
)

logger = get_logger(__name__)


class FilterType(str, Enum):
    """Filter type enumeration."""
    KEYWORD = "keyword"
    PATTERN = "pattern"
    REGEX = "regex"
    ML_MODEL = "ml_model"
    BLACKLIST = "blacklist"
    WHITELIST = "whitelist"


class FilterAction(str, Enum):
    """Filter action enumeration."""
    BLOCK = "block"
    FLAG = "flag"
    MASK = "mask"
    REDACT = "redact"
    REPLACE = "replace"
    LOG = "log"


@dataclass
class FilterRule:
    """Filter rule data structure."""
    rule_id: str
    name: str
    description: str
    filter_type: FilterType
    content_type: ContentType
    patterns: List[str]
    action: FilterAction
    replacement: Optional[str] = None
    sensitivity_level: SafetyLevel = SafetyLevel.MEDIUM
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentFilterResult:
    """Content filter result data structure."""
    is_safe: bool
    safety_level: SafetyLevel
    filtered_content: Any
    matched_rules: List[str]
    actions_taken: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentFilteringConfig(ServiceConfig):
    """Content filtering configuration."""
    enable_text_filtering: bool = True
    enable_image_filtering: bool = True
    enable_audio_filtering: bool = True
    enable_video_filtering: bool = True
    enable_ml_filtering: bool = True
    default_action: FilterAction = FilterAction.FLAG
    default_sensitivity: SafetyLevel = SafetyLevel.MEDIUM
    cache_ttl: int = 300  # 5 minutes
    strict_mode: bool = False
    
    def __post_init__(self):
        """Initialize ServiceConfig fields."""
        if not hasattr(self, 'name') or not self.name:
            self.name = "content_filtering_service"
        if not hasattr(self, 'version') or not self.version:
            self.version = "1.0.0"


class ContentFilteringService(BaseService):
    """
    Content Filtering Service for CoPilot Architecture.
    
    This service provides comprehensive content filtering functionality including
    text analysis, pattern matching, and ML-based content safety validation.
    """
    
    def __init__(self, config: Optional[ContentFilteringConfig] = None):
        """Initialize the Content Filtering Service."""
        super().__init__(config or ContentFilteringConfig())
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Initialize content safety checker
        self._safety_checker = ContentSafetyChecker(self.config.__dict__)
        
        # Thread-safe data structures
        self._filter_rules: Dict[str, FilterRule] = {}
        self._rule_cache: Dict[str, Tuple[FilterRule, float]] = {}
        
        # Load configuration from environment
        self._load_config_from_env()
    
    def _load_config_from_env(self) -> None:
        """Load configuration from environment variables."""
        import os
        
        if "CONTENT_FILTER_ENABLE_TEXT" in os.environ:
            self.config.enable_text_filtering = os.environ["CONTENT_FILTER_ENABLE_TEXT"].lower() == "true"
        
        if "CONTENT_FILTER_ENABLE_IMAGE" in os.environ:
            self.config.enable_image_filtering = os.environ["CONTENT_FILTER_ENABLE_IMAGE"].lower() == "true"
        
        if "CONTENT_FILTER_ENABLE_AUDIO" in os.environ:
            self.config.enable_audio_filtering = os.environ["CONTENT_FILTER_ENABLE_AUDIO"].lower() == "true"
        
        if "CONTENT_FILTER_ENABLE_VIDEO" in os.environ:
            self.config.enable_video_filtering = os.environ["CONTENT_FILTER_ENABLE_VIDEO"].lower() == "true"
        
        if "CONTENT_FILTER_ENABLE_ML" in os.environ:
            self.config.enable_ml_filtering = os.environ["CONTENT_FILTER_ENABLE_ML"].lower() == "true"
        
        if "CONTENT_FILTER_STRICT_MODE" in os.environ:
            self.config.strict_mode = os.environ["CONTENT_FILTER_STRICT_MODE"].lower() == "true"
    
    async def initialize(self) -> None:
        """Initialize the Content Filtering Service."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Load default filter rules
                await self._load_default_filter_rules()
                
                self._initialized = True
                logger.info("Content Filtering Service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Content Filtering Service: {e}")
                raise RuntimeError(f"Content Filtering Service initialization failed: {e}")
    
    async def _load_default_filter_rules(self) -> None:
        """Load default filter rules."""
        default_rules = [
            # Text filtering rules
            FilterRule(
                rule_id="profanity_filter",
                name="Profanity Filter",
                description="Filter out profane language",
                filter_type=FilterType.KEYWORD,
                content_type=ContentType.TEXT,
                patterns=[
                    "badword1", "badword2", "badword3", "swear1", "swear2"
                ],
                action=FilterAction.MASK,
                replacement="***",
                sensitivity_level=SafetyLevel.HIGH
            ),
            FilterRule(
                rule_id="pii_email_filter",
                name="PII Email Filter",
                description="Filter out email addresses",
                filter_type=FilterType.PATTERN,
                content_type=ContentType.TEXT,
                patterns=[
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                ],
                action=FilterAction.REDACT,
                replacement="[EMAIL]",
                sensitivity_level=SafetyLevel.MEDIUM
            ),
            FilterRule(
                rule_id="pii_phone_filter",
                name="PII Phone Filter",
                description="Filter out phone numbers",
                filter_type=FilterType.PATTERN,
                content_type=ContentType.TEXT,
                patterns=[
                    r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                    r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',
                    r'\b\d{3}[-.]?\d{4}[-.]?\d{4}\b'
                ],
                action=FilterAction.REDACT,
                replacement="[PHONE]",
                sensitivity_level=SafetyLevel.MEDIUM
            ),
            FilterRule(
                rule_id="pii_ssn_filter",
                name="PII SSN Filter",
                description="Filter out Social Security Numbers",
                filter_type=FilterType.PATTERN,
                content_type=ContentType.TEXT,
                patterns=[
                    r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'
                ],
                action=FilterAction.REDACT,
                replacement="[SSN]",
                sensitivity_level=SafetyLevel.HIGH
            ),
            FilterRule(
                rule_id="security_threat_filter",
                name="Security Threat Filter",
                description="Filter out security threats and attacks",
                filter_type=FilterType.KEYWORD,
                content_type=ContentType.TEXT,
                patterns=[
                    "sql injection", "xss", "cross-site scripting", "csrf",
                    "buffer overflow", "heap overflow", "stack overflow",
                    "remote code execution", "privilege escalation",
                    "directory traversal", "path traversal"
                ],
                action=FilterAction.BLOCK,
                sensitivity_level=SafetyLevel.CRITICAL
            ),
            FilterRule(
                rule_id="hate_speech_filter",
                name="Hate Speech Filter",
                description="Filter out hate speech",
                filter_type=FilterType.KEYWORD,
                content_type=ContentType.TEXT,
                patterns=[
                    "hate_term1", "hate_term2", "hate_term3"
                ],
                action=FilterAction.BLOCK,
                sensitivity_level=SafetyLevel.HIGH
            ),
            # Image filtering rules
            FilterRule(
                rule_id="explicit_content_filter",
                name="Explicit Content Filter",
                description="Filter out explicit images",
                filter_type=FilterType.ML_MODEL,
                content_type=ContentType.IMAGE,
                patterns=[],
                action=FilterAction.BLOCK,
                sensitivity_level=SafetyLevel.HIGH
            ),
            # Audio filtering rules
            FilterRule(
                rule_id="explicit_audio_filter",
                name="Explicit Audio Filter",
                description="Filter out explicit audio",
                filter_type=FilterType.ML_MODEL,
                content_type=ContentType.AUDIO,
                patterns=[],
                action=FilterAction.BLOCK,
                sensitivity_level=SafetyLevel.HIGH
            ),
            # Video filtering rules
            FilterRule(
                rule_id="explicit_video_filter",
                name="Explicit Video Filter",
                description="Filter out explicit video",
                filter_type=FilterType.ML_MODEL,
                content_type=ContentType.VIDEO,
                patterns=[],
                action=FilterAction.BLOCK,
                sensitivity_level=SafetyLevel.HIGH
            )
        ]
        
        for rule in default_rules:
            self._filter_rules[rule.rule_id] = rule
    
    async def filter_content(
        self,
        content: Any,
        content_type: ContentType,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ContentFilterResult:
        """
        Filter content based on filter rules.
        
        Args:
            content: Content to filter
            content_type: Type of content
            user_id: Optional user ID
            context: Optional context for filtering
            
        Returns:
            Content filter result
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Initialize result
            is_safe = True
            safety_level = SafetyLevel.LOW
            filtered_content = content
            matched_rules = []
            actions_taken = []
            
            # Get applicable rules
            applicable_rules = [
                rule for rule in self._filter_rules.values()
                if rule.is_active and rule.content_type == content_type
            ]
            
            # Apply rules
            for rule in applicable_rules:
                # Check if rule matches
                if await self._rule_matches(rule, content, content_type, context):
                    matched_rules.append(rule.rule_id)
                    
                    # Apply action
                    action_result = await self._apply_rule_action(
                        rule, content, content_type, context
                    )
                    
                    filtered_content = action_result["content"]
                    actions_taken.append(action_result["action"])
                    
                    # Update safety level
                    if rule.sensitivity_level.value > safety_level.value:
                        safety_level = rule.sensitivity_level
                    
                    # Update safety status
                    if rule.action == FilterAction.BLOCK:
                        is_safe = False
            
            # Use content safety checker for additional validation
            if isinstance(filtered_content, str):
                safety_check = self._safety_checker.check_content_safety(
                    content=filtered_content,
                    content_type=content_type
                )
                
                # Update result based on safety check
                if not safety_check.is_safe:
                    is_safe = False
                    # Convert RiskLevel to SafetyLevel for comparison
                    if safety_check.risk_level.value > safety_level.value:
                        # Map RiskLevel to SafetyLevel
                        if safety_check.risk_level == RiskLevel.CRITICAL_RISK:
                            safety_level = SafetyLevel.CRITICAL
                        elif safety_check.risk_level == RiskLevel.HIGH_RISK:
                            safety_level = SafetyLevel.HIGH
                        elif safety_check.risk_level == RiskLevel.MEDIUM_RISK:
                            safety_level = SafetyLevel.MEDIUM
                        elif safety_check.risk_level == RiskLevel.LOW_RISK:
                            safety_level = SafetyLevel.LOW
                        else:
                            safety_level = SafetyLevel.LOW
                    
                    # Add safety check to matched rules
                    if "safety_check" not in matched_rules:
                        matched_rules.append("safety_check")
                    
                    # Add safety check action
                    if "safety_check" not in actions_taken:
                        actions_taken.append("safety_check")
            
            return ContentFilterResult(
                is_safe=is_safe,
                safety_level=safety_level,
                filtered_content=filtered_content,
                matched_rules=matched_rules,
                actions_taken=actions_taken
            )
            
        except Exception as e:
            logger.error(f"Error filtering content: {e}")
            return ContentFilterResult(
                is_safe=False,
                safety_level=SafetyLevel.CRITICAL,
                filtered_content=content,
                matched_rules=["error"],
                actions_taken=["error"]
            )
    
    async def _rule_matches(
        self,
        rule: FilterRule,
        content: Any,
        content_type: ContentType,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if a rule matches content.
        
        Args:
            rule: Rule to check
            content: Content to check
            content_type: Type of content
            context: Optional context
            
        Returns:
            True if rule matches, False otherwise
        """
        try:
            # Skip if rule doesn't match content type
            if rule.content_type != content_type:
                return False
            
            # Skip if no patterns
            if not rule.patterns:
                return False
            
            # Check based on filter type
            if rule.filter_type == FilterType.KEYWORD:
                # Keyword matching
                if isinstance(content, str):
                    content_lower = content.lower()
                    for pattern in rule.patterns:
                        if pattern.lower() in content_lower:
                            return True
                return False
            
            elif rule.filter_type == FilterType.PATTERN or rule.filter_type == FilterType.REGEX:
                # Pattern/Regex matching
                if isinstance(content, str):
                    for pattern in rule.patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            return True
                return False
            
            elif rule.filter_type == FilterType.ML_MODEL:
                # ML model matching
                # For now, we'll return False as ML models are not implemented
                # In a real implementation, this would call an ML model API
                return False
            
            elif rule.filter_type == FilterType.BLACKLIST:
                # Blacklist matching
                if isinstance(content, str):
                    content_lower = content.lower()
                    for pattern in rule.patterns:
                        if pattern.lower() == content_lower:
                            return True
                return False
            
            elif rule.filter_type == FilterType.WHITELIST:
                # Whitelist matching (inverse of blacklist)
                if isinstance(content, str):
                    content_lower = content.lower()
                    for pattern in rule.patterns:
                        if pattern.lower() == content_lower:
                            return False
                    return True
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking rule match: {e}")
            return False
    
    async def _apply_rule_action(
        self,
        rule: FilterRule,
        content: Any,
        content_type: ContentType,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply a rule action to content.
        
        Args:
            rule: Rule to apply
            content: Content to apply rule to
            content_type: Type of content
            context: Optional context
            
        Returns:
            Dictionary with action result
        """
        try:
            if rule.action == FilterAction.BLOCK:
                return {
                    "content": None,
                    "action": "blocked"
                }
            
            elif rule.action == FilterAction.FLAG:
                return {
                    "content": content,
                    "action": "flagged"
                }
            
            elif rule.action == FilterAction.MASK:
                if isinstance(content, str):
                    for pattern in rule.patterns:
                        if rule.filter_type == FilterType.KEYWORD:
                            content = content.replace(pattern, rule.replacement or "***")
                        elif rule.filter_type == FilterType.PATTERN or rule.filter_type == FilterType.REGEX:
                            content = re.sub(
                                pattern,
                                rule.replacement or "***",
                                content,
                                flags=re.IGNORECASE
                            )
                
                return {
                    "content": content,
                    "action": "masked"
                }
            
            elif rule.action == FilterAction.REDACT:
                if isinstance(content, str):
                    for pattern in rule.patterns:
                        if rule.filter_type == FilterType.KEYWORD:
                            content = content.replace(pattern, rule.replacement or "[REDACTED]")
                        elif rule.filter_type == FilterType.PATTERN or rule.filter_type == FilterType.REGEX:
                            content = re.sub(
                                pattern,
                                rule.replacement or "[REDACTED]",
                                content,
                                flags=re.IGNORECASE
                            )
                
                return {
                    "content": content,
                    "action": "redacted"
                }
            
            elif rule.action == FilterAction.REPLACE:
                if isinstance(content, str) and rule.replacement:
                    for pattern in rule.patterns:
                        if rule.filter_type == FilterType.KEYWORD:
                            content = content.replace(pattern, rule.replacement)
                        elif rule.filter_type == FilterType.PATTERN or rule.filter_type == FilterType.REGEX:
                            content = re.sub(
                                pattern,
                                rule.replacement,
                                content,
                                flags=re.IGNORECASE
                            )
                
                return {
                    "content": content,
                    "action": "replaced"
                }
            
            elif rule.action == FilterAction.LOG:
                return {
                    "content": content,
                    "action": "logged"
                }
            
            return {
                "content": content,
                "action": "none"
            }
            
        except Exception as e:
            logger.error(f"Error applying rule action: {e}")
            return {
                "content": content,
                "action": "error"
            }
    
    async def add_rule(self, rule: FilterRule) -> bool:
        """
        Add a new filter rule.
        
        Args:
            rule: Rule to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            self._filter_rules[rule.rule_id] = rule
            logger.info(f"Added filter rule: {rule.name} ({rule.rule_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to add rule {rule.rule_id}: {e}")
            return False
    
    async def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a filter rule.
        
        Args:
            rule_id: ID of the rule to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            if rule_id in self._filter_rules:
                del self._filter_rules[rule_id]
                logger.info(f"Removed filter rule: {rule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove rule {rule_id}: {e}")
            return False
    
    async def get_rule(self, rule_id: str) -> Optional[FilterRule]:
        """
        Get a filter rule.
        
        Args:
            rule_id: ID of the rule to get
            
        Returns:
            Rule if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        return self._filter_rules.get(rule_id)
    
    async def get_rules(
        self,
        content_type: Optional[ContentType] = None,
        filter_type: Optional[FilterType] = None,
        is_active: Optional[bool] = None
    ) -> List[FilterRule]:
        """
        Get filter rules.
        
        Args:
            content_type: Optional content type to filter by
            filter_type: Optional filter type to filter by
            is_active: Optional active status to filter by
            
        Returns:
            List of rules
        """
        if not self._initialized:
            await self.initialize()
        
        rules = list(self._filter_rules.values())
        
        if content_type:
            rules = [r for r in rules if r.content_type == content_type]
        
        if filter_type:
            rules = [r for r in rules if r.filter_type == filter_type]
        
        if is_active is not None:
            rules = [r for r in rules if r.is_active == is_active]
        
        return rules
    
    async def enable_rule(self, rule_id: str) -> bool:
        """
        Enable a filter rule.
        
        Args:
            rule_id: ID of the rule to enable
            
        Returns:
            True if enabling was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            rule = self._filter_rules.get(rule_id)
            if rule:
                rule.is_active = True
                rule.updated_at = datetime.utcnow()
                logger.info(f"Enabled filter rule: {rule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to enable rule {rule_id}: {e}")
            return False
    
    async def disable_rule(self, rule_id: str) -> bool:
        """
        Disable a filter rule.
        
        Args:
            rule_id: ID of the rule to disable
            
        Returns:
            True if disabling was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            rule = self._filter_rules.get(rule_id)
            if rule:
                rule.is_active = False
                rule.updated_at = datetime.utcnow()
                logger.info(f"Disabled filter rule: {rule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to disable rule {rule_id}: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the content filtering service.
        
        Returns:
            Dictionary with content filtering service statistics
        """
        if not self._initialized:
            await self.initialize()
        
        # Count rules by content type
        rules_by_content_type = {}
        for rule in self._filter_rules.values():
            content_type = rule.content_type.value
            if content_type not in rules_by_content_type:
                rules_by_content_type[content_type] = []
            rules_by_content_type[content_type].append(rule.rule_id)
        
        # Count rules by filter type
        rules_by_filter_type = {}
        for rule in self._filter_rules.values():
            filter_type = rule.filter_type.value
            if filter_type not in rules_by_filter_type:
                rules_by_filter_type[filter_type] = []
            rules_by_filter_type[filter_type].append(rule.rule_id)
        
        # Count rules by action
        rules_by_action = {}
        for rule in self._filter_rules.values():
            action = rule.action.value
            if action not in rules_by_action:
                rules_by_action[action] = []
            rules_by_action[action].append(rule.rule_id)
        
        # Count rules by sensitivity level
        rules_by_sensitivity = {}
        for rule in self._filter_rules.values():
            sensitivity = rule.sensitivity_level.value
            if sensitivity not in rules_by_sensitivity:
                rules_by_sensitivity[sensitivity] = []
            rules_by_sensitivity[sensitivity].append(rule.rule_id)
        
        # Count active vs inactive rules
        active_rules = [r for r in self._filter_rules.values() if r.is_active]
        inactive_rules = [r for r in self._filter_rules.values() if not r.is_active]
        
        return {
            "total_rules": len(self._filter_rules),
            "active_rules": len(active_rules),
            "inactive_rules": len(inactive_rules),
            "rules_by_content_type": {
                content_type: len(rules)
                for content_type, rules in rules_by_content_type.items()
            },
            "rules_by_filter_type": {
                filter_type: len(rules)
                for filter_type, rules in rules_by_filter_type.items()
            },
            "rules_by_action": {
                action: len(rules)
                for action, rules in rules_by_action.items()
            },
            "rules_by_sensitivity": {
                sensitivity: len(rules)
                for sensitivity, rules in rules_by_sensitivity.items()
            },
            "config": {
                "enable_text_filtering": self.config.enable_text_filtering,
                "enable_image_filtering": self.config.enable_image_filtering,
                "enable_audio_filtering": self.config.enable_audio_filtering,
                "enable_video_filtering": self.config.enable_video_filtering,
                "enable_ml_filtering": self.config.enable_ml_filtering,
                "default_action": self.config.default_action.value,
                "default_sensitivity": self.config.default_sensitivity.value,
                "strict_mode": self.config.strict_mode
            }
        }
    
    async def health_check(self) -> bool:
        """
        Check health of the Content Filtering Service.
        
        Returns:
            True if service is healthy, False otherwise
        """
        if not self._initialized:
            return False
        
        try:
            # Check if we can filter content
            test_content = "This is a test content"
            filter_result = await self.filter_content(
                content=test_content,
                content_type=ContentType.TEXT
            )
            
            if not filter_result:
                return False
            
            # Check if we can add and remove a rule
            test_rule = FilterRule(
                rule_id="test_rule",
                name="Test Rule",
                description="Rule for health check",
                filter_type=FilterType.KEYWORD,
                content_type=ContentType.TEXT,
                patterns=["test"],
                action=FilterAction.FLAG
            )
            
            # Add rule
            if not await self.add_rule(test_rule):
                return False
            
            # Get rule
            retrieved_rule = await self.get_rule("test_rule")
            if not retrieved_rule:
                return False
            
            # Remove rule
            if not await self.remove_rule("test_rule"):
                return False
            
            return True
        except Exception as e:
            logger.error(f"Content Filtering Service health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Content Filtering Service."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Content Filtering Service started successfully")
    
    async def stop(self) -> None:
        """Stop the Content Filtering Service."""
        if not self._initialized:
            return
        
        # Clear caches
        self._rule_cache.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Content Filtering Service stopped successfully")