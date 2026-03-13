"""
Content Safety Module for the Agent Safety System.

This module provides content filtering, validation, and safety checks
to ensure agents operate safely and securely.
"""

import asyncio
import logging
import re
import time
from typing import Any, Dict, List, Optional, Set, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

# Import data structures from agent_safety.py
from ..agent_safety import (
    ContentType, SafetyLevel, RiskLevel, ContentInput, ContentOutput, 
    ValidationResult, FilteredOutput, Context, FilterRule
)

logger = logging.getLogger(__name__)


@dataclass
class SafetyConfig:
    """Safety configuration data structure."""
    input_filters: Dict[str, Any] = field(default_factory=dict)
    scanners: Dict[str, Any] = field(default_factory=dict)
    context_rules: Dict[str, Any] = field(default_factory=dict)
    output_filters: Dict[str, Any] = field(default_factory=dict)
    rules_db: Dict[str, Any] = field(default_factory=dict)
    models: Dict[str, Any] = field(default_factory=dict)
    sensitivity_level: SafetyLevel = SafetyLevel.MEDIUM
    agent_specific_rules: Dict[str, List[str]] = field(default_factory=dict)
    enable_ml_filtering: bool = True
    enable_adaptive_learning: bool = True
    enable_real_time_scanning: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class FilterRulesManager:
    """Manager for filter rules."""
    
    def __init__(self, config: SafetyConfig):
        """Initialize the Filter Rules Manager."""
        self.config = config
        self._filter_rules: Dict[str, FilterRule] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the Filter Rules Manager."""
        # Load default filter rules
        await self._load_default_filter_rules()
    
    async def _load_default_filter_rules(self) -> None:
        """Load default filter rules."""
        default_rules = [
            FilterRule(
                rule_id="default_harmful_content",
                name="Default Harmful Content Filter",
                description="Filter out harmful content",
                pattern=r"(harmful|dangerous|unsafe|toxic)",
                content_types=[ContentType.TEXT],
                risk_level=RiskLevel.HIGH_RISK
            ),
            FilterRule(
                rule_id="default_pii_content",
                name="Default PII Content Filter",
                description="Filter out personally identifiable information",
                pattern=r"(\d{3}-\d{2}-\d{4}|\d{9})",
                content_types=[ContentType.TEXT],
                risk_level=RiskLevel.MEDIUM_RISK
            ),
            FilterRule(
                rule_id="default_security_content",
                name="Default Security Content Filter",
                description="Filter out security-sensitive content",
                pattern=r"(password|secret|key|token)",
                content_types=[ContentType.TEXT],
                risk_level=RiskLevel.HIGH_RISK
            )
        ]
        
        for rule in default_rules:
            self._filter_rules[rule.rule_id] = rule
    
    async def add_rule(self, rule: FilterRule) -> bool:
        """
        Add a filter rule.
        
        Args:
            rule: Filter rule to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        async with self._lock:
            if rule.rule_id in self._filter_rules:
                return False
            
            self._filter_rules[rule.rule_id] = rule
            return True
    
    async def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a filter rule.
        
        Args:
            rule_id: ID of the rule to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        async with self._lock:
            if rule_id not in self._filter_rules:
                return False
            
            del self._filter_rules[rule_id]
            return True
    
    async def get_rules(self, category: Optional[str] = None, active_only: bool = True) -> List[FilterRule]:
        """
        Get filter rules.
        
        Args:
            category: Optional category to filter by
            active_only: Whether to only return active rules
            
        Returns:
            List of filter rules
        """
        async with self._lock:
            rules = list(self._filter_rules.values())
            
            if active_only:
                rules = [rule for rule in rules if rule.is_active]
            
            if category:
                rules = [rule for rule in rules if category in rule.metadata.get("categories", [])]
            
            return rules


class ContentScanner(ABC):
    """Abstract base class for content scanners."""
    
    @abstractmethod
    async def scan(self, content_input: ContentInput, context: Context) -> ValidationResult:
        """
        Scan content for safety issues.
        
        Args:
            content_input: Content input to scan
            context: Context for the scan
            
        Returns:
            Validation result
        """
        pass


class RegexContentScanner(ContentScanner):
    """Content scanner using regular expressions."""
    
    def __init__(self, filter_rules_manager: FilterRulesManager):
        """Initialize the Regex Content Scanner."""
        self.filter_rules_manager = filter_rules_manager
    
    async def scan(self, content_input: ContentInput, context: Context) -> ValidationResult:
        """
        Scan content using regular expressions.
        
        Args:
            content_input: Content input to scan
            context: Context for the scan
            
        Returns:
            Validation result
        """
        content = str(content_input.content)
        violations = []
        matched_patterns = []
        is_safe = True
        confidence = 1.0
        risk_level = RiskLevel.SAFE
        
        # Get filter rules
        rules = await self.filter_rules_manager.get_rules(active_only=True)
        
        # Check each rule
        for rule in rules:
            if content_input.content_type in rule.content_types:
                if re.search(rule.pattern, content, re.IGNORECASE):
                    violations.append(f"Matched rule: {rule.name}")
                    matched_patterns.append(rule.pattern)
                    
                    if rule.risk_level.value > risk_level.value:
                        risk_level = rule.risk_level
                    
                    if rule.risk_level in [RiskLevel.HIGH_RISK, RiskLevel.CRITICAL_RISK]:
                        is_safe = False
                        confidence = 0.9
        
        return ValidationResult(
            is_safe=is_safe,
            confidence=confidence,
            risk_level=risk_level,
            violations=violations,
            matched_patterns=matched_patterns
        )


class MLContentScanner(ContentScanner):
    """Content scanner using machine learning models."""
    
    def __init__(self, config: SafetyConfig):
        """Initialize the ML Content Scanner."""
        self.config = config
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the ML Content Scanner."""
        # In a real implementation, this would load ML models
        self._initialized = True
    
    async def scan(self, content_input: ContentInput, context: Context) -> ValidationResult:
        """
        Scan content using machine learning models.
        
        Args:
            content_input: Content input to scan
            context: Context for the scan
            
        Returns:
            Validation result
        """
        if not self._initialized:
            await self.initialize()
        
        content = str(content_input.content)
        violations = []
        is_safe = True
        confidence = 0.95
        risk_level = RiskLevel.SAFE
        
        # In a real implementation, this would use ML models to scan content
        # For now, we'll use a simple heuristic
        if len(content) > 10000:
            violations.append("Content is too long")
            risk_level = RiskLevel.MEDIUM_RISK
            confidence = 0.8
        
        if "harmful" in content.lower() or "dangerous" in content.lower():
            violations.append("Potentially harmful content detected")
            risk_level = RiskLevel.HIGH_RISK
            is_safe = False
            confidence = 0.9
        
        return ValidationResult(
            is_safe=is_safe,
            confidence=confidence,
            risk_level=risk_level,
            violations=violations
        )


class ContentSafetyModule(BaseService):
    """
    Content Safety Module for the Agent Safety System.
    
    This module provides content filtering, validation, and safety checks
    to ensure agents operate safely and securely.
    """
    
    def __init__(self, config: SafetyConfig):
        """Initialize the Content Safety Module."""
        # Convert SafetyConfig to ServiceConfig for parent class
        service_config = ServiceConfig(
            name=getattr(config, 'name', 'content_safety'),
            version=getattr(config, 'version', '1.0.0')
        )
        super().__init__(service_config)
        self.config = config
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Initialize components
        self.filter_rules_manager = FilterRulesManager(config)
        self.scanners: List[ContentScanner] = []
        
        # Metrics and audit data
        self._metrics: Dict[str, Any] = {
            "total_checks": 0,
            "unsafe_content_count": 0,
            "filtered_content_count": 0,
            "average_processing_time": 0.0,
            "last_updated": datetime.utcnow()
        }
        
        self._audit_logs: List[Dict[str, Any]] = []
        self._metrics_lock = asyncio.Lock()
        self._audit_lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the Content Safety Module."""
        if self._initialized:
            return
        
        async with self._lock:
            try:
                # Initialize filter rules manager
                await self.filter_rules_manager.initialize()
                
                # Initialize scanners
                self.scanners = [
                    RegexContentScanner(self.filter_rules_manager)
                ]
                
                if self.config.enable_ml_filtering:
                    ml_scanner = MLContentScanner(self.config)
                    await ml_scanner.initialize()
                    self.scanners.append(ml_scanner)
                
                self._initialized = True
                logger.info("Content Safety Module initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Content Safety Module: {e}")
                raise RuntimeError(f"Content Safety Module initialization failed: {e}")
    
    async def validate_content(self, content_input: ContentInput, context: Context) -> ValidationResult:
        """
        Validate content for safety.
        
        Args:
            content_input: Content input to validate
            context: Context for validation
            
        Returns:
            Validation result
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Initialize result
            violations = []
            matched_patterns = []
            is_safe = True
            confidence = 1.0
            risk_level = RiskLevel.SAFE
            
            # Run all scanners
            for scanner in self.scanners:
                result = await scanner.scan(content_input, context)
                
                if not result.is_safe:
                    is_safe = False
                
                violations.extend(result.violations)
                matched_patterns.extend(result.matched_patterns)
                
                if result.risk_level.value > risk_level.value:
                    risk_level = result.risk_level
                
                confidence = min(confidence, result.confidence)
            
            # Create validation result
            validation_result = ValidationResult(
                is_safe=is_safe,
                confidence=confidence,
                risk_level=risk_level,
                violations=violations,
                matched_patterns=matched_patterns
            )
            
            # Update metrics
            await self._update_metrics(validation_result, time.time() - start_time)
            
            # Log audit entry
            await self._log_audit_entry(
                action="validate_content",
                context=context,
                content_input=content_input,
                result=validation_result
            )
            
            return validation_result
        except Exception as e:
            logger.error(f"Error validating content: {e}")
            
            # Log error
            await self._log_audit_entry(
                action="validate_content_error",
                context=context,
                content_input=content_input,
                error=str(e)
            )
            
            return ValidationResult(
                is_safe=False,
                confidence=0.0,
                risk_level=RiskLevel.CRITICAL_RISK,
                violations=["Content validation failed"]
            )
    
    async def filter_output(self, content_output: ContentOutput, context: Context) -> ContentOutput:
        """
        Filter content output to remove unsafe parts.
        
        Args:
            content_output: Content output to filter
            context: Context for filtering
            
        Returns:
            Filtered content output
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Create content input for validation
            content_input = ContentInput(
                content=content_output.content,
                content_type=content_output.content_type,
                metadata=content_output.metadata
            )
            
            # Validate content
            validation_result = await self.validate_content(content_input, context)
            
            # Create filtered output
            filtered_output = ContentOutput(
                content=content_output.content,
                content_type=content_output.content_type,
                is_filtered=not validation_result.is_safe,
                filter_reason=", ".join(validation_result.violations) if validation_result.violations else None,
                processing_time=time.time() - start_time,
                metadata=content_output.metadata
            )
            
            # Update metrics
            if filtered_output.is_filtered:
                async with self._metrics_lock:
                    self._metrics["filtered_content_count"] += 1
            
            # Log audit entry
            await self._log_audit_entry(
                action="filter_output",
                context=context,
                content_output=content_output,
                filtered_output=filtered_output
            )
            
            return filtered_output
        except Exception as e:
            logger.error(f"Error filtering output: {e}")
            
            # Log error
            await self._log_audit_entry(
                action="filter_output_error",
                context=context,
                content_output=content_output,
                error=str(e)
            )
            
            # Return original content with error
            return ContentOutput(
                content=content_output.content,
                content_type=content_output.content_type,
                is_filtered=False,
                filter_reason="Filtering failed",
                processing_time=time.time() - start_time,
                metadata=content_output.metadata
            )
    
    async def ml_enhanced_validation(self, content_input: ContentInput, context: Context) -> ValidationResult:
        """
        Perform ML-enhanced content validation.
        
        Args:
            content_input: Content input to validate
            context: Context for validation
            
        Returns:
            Validation result
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Find ML scanner
            ml_scanner = None
            for scanner in self.scanners:
                if isinstance(scanner, MLContentScanner):
                    ml_scanner = scanner
                    break
            
            if not ml_scanner:
                # Fall back to regular validation
                return await self.validate_content(content_input, context)
            
            # Validate content using ML scanner
            result = await ml_scanner.scan(content_input, context)
            
            # Update metrics
            await self._update_metrics(result, time.time() - start_time)
            
            # Log audit entry
            await self._log_audit_entry(
                action="ml_enhanced_validation",
                context=context,
                content_input=content_input,
                result=result
            )
            
            return result
        except Exception as e:
            logger.error(f"Error in ML-enhanced validation: {e}")
            
            # Log error
            await self._log_audit_entry(
                action="ml_enhanced_validation_error",
                context=context,
                content_input=content_input,
                error=str(e)
            )
            
            # Fall back to regular validation
            return await self.validate_content(content_input, context)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get content safety metrics.
        
        Returns:
            Content safety metrics
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._metrics_lock:
            return self._metrics.copy()
    
    async def get_audit_logs(
        self, 
        agent_id: Optional[str] = None, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get content safety audit logs.
        
        Args:
            agent_id: Optional agent ID to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            limit: Maximum number of logs to return
            
        Returns:
            List of audit logs
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._audit_lock:
            logs = self._audit_logs.copy()
            
            # Filter by agent ID
            if agent_id:
                logs = [log for log in logs if log.get("context", {}).get("agent_id") == agent_id]
            
            # Filter by time range
            if start_time:
                logs = [log for log in logs if log.get("timestamp", datetime.min) >= start_time]
            
            if end_time:
                logs = [log for log in logs if log.get("timestamp", datetime.min) <= end_time]
            
            # Sort by timestamp (newest first)
            logs.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
            
            # Limit results
            return logs[:limit]
    
    async def _update_metrics(self, result: ValidationResult, processing_time: float) -> None:
        """
        Update metrics based on validation result.
        
        Args:
            result: Validation result
            processing_time: Processing time in seconds
        """
        async with self._metrics_lock:
            self._metrics["total_checks"] += 1
            
            if not result.is_safe:
                self._metrics["unsafe_content_count"] += 1
            
            # Update average processing time
            total_time = self._metrics["average_processing_time"] * (self._metrics["total_checks"] - 1)
            total_time += processing_time
            self._metrics["average_processing_time"] = total_time / self._metrics["total_checks"]
            
            self._metrics["last_updated"] = datetime.utcnow()
    
    async def _log_audit_entry(
        self,
        action: str,
        context: Context,
        **kwargs
    ) -> None:
        """
        Log an audit entry.
        
        Args:
            action: Action being audited
            context: Context for the action
            **kwargs: Additional data to log
        """
        async with self._audit_lock:
            audit_entry = {
                "timestamp": datetime.utcnow(),
                "action": action,
                "context": {
                    "agent_id": context.agent_id,
                    "user_id": context.user_id,
                    "session_id": context.session_id,
                    "task_id": context.task_id
                },
                **kwargs
            }
            
            self._audit_logs.append(audit_entry)
            
            # Limit audit log size
            if len(self._audit_logs) > 10000:
                self._audit_logs = self._audit_logs[-10000:]
    
    async def health_check(self) -> bool:
        """Check health of the Content Safety Module."""
        if not self._initialized:
            return False
        
        try:
            # Check if scanners are available
            if not self.scanners:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Content Safety Module health check failed: {e}")
            return False