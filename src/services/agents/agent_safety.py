"""
Agent Safety service for managing agent safety and security.

This service provides safety mechanisms for agents, including content filtering,
action validation, and security checks to ensure agents operate safely.
"""

import asyncio
import logging
import re
import json
import time
import threading
from typing import Any, Dict, List, Optional, Set, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from ai_karen_engine.core.services.base import BaseService, ServiceConfig

# Import Agent Safety classes
from .AgentSafetyClass.BehaviorTracker import BehaviorTracker
from .AgentSafetyClass.AnomalyDetector import AnomalyDetector
from .AgentSafetyClass.PatternRecognizer import PatternRecognizer
from .AgentSafetyClass.BaselineGenerator import BaselineGenerator
from .AgentSafetyClass.BehaviorProfiler import BehaviorProfiler
from .AgentSafetyClass.RiskAssessor import RiskAssessor
from .AgentSafetyClass.CorrelationEngine import CorrelationEngine
from .AgentSafetyClass.BehaviorLogger import BehaviorLogger
# AgentSafety will be defined in this file
from .AgentSafetyClass.PolicyEnforcementEngine import PolicyEnforcementEngine, PolicyType, Policy, PolicyEnforcementResult, EnforcementAction
from .AgentSafetyClass.EnhancedServicesIntegrator import EnhancedServicesIntegrator

logger = logging.getLogger(__name__)


# Import data types from agent_safety_types module
from .agent_safety_types import (
    ContentType, SafetyLevel, RiskLevel,
    ContentInput, ContentOutput, ValidationResult, FilteredOutput,
    Context, FilterRule, SafetyConfig, BehaviorData,
    BehaviorMetrics, AnomalyResult, PatternResult, BaselineResult,
    BehaviorProfile, RiskAssessment, CorrelationResult, BehaviorAnalysis
)

class ComplianceIntegrator:
    """
    Compliance integration module for Karen's compliance systems.
    
    This module provides integration with Karen's compliance frameworks,
    including compliance checking, audit trail generation, and reporting.
    """
    
    def __init__(self, config: SafetyConfig):
        """Initialize the Compliance Integrator."""
        self.config = config
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Compliance configuration
        self._compliance_config = {
            "enable_compliance_checking": True,
            "enable_audit_trail": True,
            "enable_reporting": True,
            "compliance_standards": ["SOC2", "GDPR", "HIPAA", "ISO27001"],
            "audit_retention_days": 365,
            "report_generation_interval": 86400,  # 24 hours
            "compliance_check_interval": 3600,  # 1 hour
            "violation_threshold": 3,
            "auto_escalation": True,
            "escalation_contacts": ["compliance_officer", "security_team"],
            "log_file_path": "logs/compliance.log",
            "enable_detailed_logging": True,
            "log_level": "INFO",
            "max_log_size": 10485760,  # 10MB
            "log_backup_count": 5,
            "enable_log_rotation": True
        }
        
        # Thread-safe data structures
        self._compliance_violations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._audit_trail: List[Dict[str, Any]] = []
        self._compliance_reports: Dict[str, Dict[str, Any]] = {}
        
        # Thread-safe locks
        self._violations_lock = asyncio.Lock()
        self._audit_lock = asyncio.Lock()
        self._reports_lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the Compliance Integrator."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Initialize compliance checking
                if self._compliance_config["enable_compliance_checking"]:
                    await self._initialize_compliance_checking()
                
                # Initialize audit trail
                if self._compliance_config["enable_audit_trail"]:
                    await self._initialize_audit_trail()
                
                # Initialize reporting
                if self._compliance_config["enable_reporting"]:
                    await self._initialize_reporting()
                
                self._initialized = True
                logger.info("Compliance Integrator initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Compliance Integrator: {e}")
                raise RuntimeError(f"Compliance Integrator initialization failed: {e}")
    
    async def _initialize_compliance_checking(self) -> None:
        """Initialize compliance checking."""
        # Load compliance rules and standards
        logger.debug("Compliance checking initialized")
    
    async def _initialize_audit_trail(self) -> None:
        """Initialize audit trail."""
        # Set up audit logging
        logger.debug("Audit trail initialized")
    
    async def _initialize_reporting(self) -> None:
        """Initialize reporting."""
        # Set up report generation
        logger.debug("Reporting initialized")
    
    async def check_content_compliance(
        self,
        content: str,
        agent_id: str = "unknown"
    ) -> ValidationResult:
        """
        Check content compliance.
        
        Args:
            content: Content to check
            agent_id: ID of the agent generating the content
            
        Returns:
            Compliance validation result
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            violations = []
            is_compliant = True
            confidence = 1.0
            risk_level = RiskLevel.SAFE
            
            # Check against compliance standards
            for standard in self._compliance_config["compliance_standards"]:
                standard_result = await self._check_standard_compliance(
                    standard=standard,
                    content=content,
                    agent_id=agent_id
                )
                
                if not standard_result.is_compliant:
                    violations.extend(standard_result.violations)
                    is_compliant = False
                    if standard_result.risk_level.value > risk_level.value:
                        risk_level = standard_result.risk_level
            
            # Record audit trail
            if self._compliance_config["enable_audit_trail"]:
                await self._record_audit_entry(
                    action="content_check",
                    agent_id=agent_id,
                    details={
                        "content_length": len(content),
                        "is_compliant": is_compliant,
                        "violations": violations,
                        "risk_level": risk_level.value
                    }
                )
            
            return ValidationResult(
                is_safe=is_compliant,
                confidence=confidence,
                risk_level=risk_level,
                violations=violations
            )
        except Exception as e:
            logger.error(f"Error checking content compliance: {e}")
            return ValidationResult(
                is_safe=False,
                confidence=0.0,
                risk_level=RiskLevel.CRITICAL_RISK,
                violations=["Content compliance check failed"]
            )
    
    async def check_action_compliance(
        self,
        agent_id: str,
        action: str,
        parameters: Dict[str, Any]
    ) -> ValidationResult:
        """
        Check action compliance.
        
        Args:
            agent_id: Unique identifier of the agent
            action: Action to check
            parameters: Parameters for the action
            
        Returns:
            Compliance validation result
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            violations = []
            is_compliant = True
            confidence = 1.0
            risk_level = RiskLevel.SAFE
            
            # Check against compliance standards
            for standard in self._compliance_config["compliance_standards"]:
                standard_result = await self._check_action_standard_compliance(
                    standard=standard,
                    agent_id=agent_id,
                    action=action,
                    parameters=parameters
                )
                
                if not standard_result.is_compliant:
                    violations.extend(standard_result.violations)
                    is_compliant = False
                    if standard_result.risk_level.value > risk_level.value:
                        risk_level = standard_result.risk_level
            
            # Record audit trail
            if self._compliance_config["enable_audit_trail"]:
                await self._record_audit_entry(
                    action="action_check",
                    agent_id=agent_id,
                    details={
                        "action": action,
                        "parameters": {k: v for k, v in parameters.items() if not k.startswith("password")},
                        "is_compliant": is_compliant,
                        "violations": violations,
                        "risk_level": risk_level.value
                    }
                )
            
            return ValidationResult(
                is_safe=is_compliant,
                confidence=confidence,
                risk_level=risk_level,
                violations=violations
            )
        except Exception as e:
            logger.error(f"Error checking action compliance: {e}")
            return ValidationResult(
                is_safe=False,
                confidence=0.0,
                risk_level=RiskLevel.CRITICAL_RISK,
                violations=["Action compliance check failed"]
            )
    
    async def check_response_compliance(
        self,
        agent_id: str,
        response: str
    ) -> ValidationResult:
        """
        Check response compliance.
        
        Args:
            agent_id: Unique identifier of the agent
            response: Response to check
            
        Returns:
            Compliance validation result
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            violations = []
            is_compliant = True
            confidence = 1.0
            risk_level = RiskLevel.SAFE
            
            # Check against compliance standards
            for standard in self._compliance_config["compliance_standards"]:
                standard_result = await self._check_standard_compliance(
                    standard=standard,
                    content=response,
                    agent_id=agent_id
                )
                
                if not standard_result.is_compliant:
                    violations.extend(standard_result.violations)
                    is_compliant = False
                    if standard_result.risk_level.value > risk_level.value:
                        risk_level = standard_result.risk_level
            
            # Record audit trail
            if self._compliance_config["enable_audit_trail"]:
                await self._record_audit_entry(
                    action="response_check",
                    agent_id=agent_id,
                    details={
                        "response_length": len(response),
                        "is_compliant": is_compliant,
                        "violations": violations,
                        "risk_level": risk_level.value
                    }
                )
            
            return ValidationResult(
                is_safe=is_compliant,
                confidence=confidence,
                risk_level=risk_level,
                violations=violations
            )
        except Exception as e:
            logger.error(f"Error checking response compliance: {e}")
            return ValidationResult(
                is_safe=False,
                confidence=0.0,
                risk_level=RiskLevel.CRITICAL_RISK,
                violations=["Response compliance check failed"]
            )
    
    async def check_behavior_compliance(
        self,
        agent_id: str,
        behavior_data: BehaviorData
    ) -> bool:
        """
        Check behavior compliance.
        
        Args:
            agent_id: Unique identifier of the agent
            behavior_data: Behavior data to check
            
        Returns:
            True if behavior is compliant, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            violations = []
            is_compliant = True
            
            # Check against compliance standards
            for standard in self._compliance_config["compliance_standards"]:
                standard_result = await self._check_behavior_standard_compliance(
                    standard=standard,
                    agent_id=agent_id,
                    behavior_data=behavior_data
                )
                
                if not standard_result.is_compliant:
                    violations.extend(standard_result.violations)
                    is_compliant = False
            
            # Record violations
            if violations:
                async with self._violations_lock:
                    self._compliance_violations[agent_id].append({
                        "timestamp": datetime.utcnow(),
                        "violations": violations,
                        "behavior_data": behavior_data
                    })
            
            # Record audit trail
            if self._compliance_config["enable_audit_trail"]:
                await self._record_audit_entry(
                    action="behavior_check",
                    agent_id=agent_id,
                    details={
                        "is_compliant": is_compliant,
                        "violations": violations,
                        "metrics": behavior_data.metrics
                    }
                )
            
            # Check for violation threshold
            if self._compliance_config["auto_escalation"]:
                await self._check_violation_threshold(agent_id)
            
            return is_compliant
        except Exception as e:
            logger.error(f"Error checking behavior compliance: {e}")
            return False
    
    async def _check_standard_compliance(
        self,
        standard: str,
        content: str,
        agent_id: str
    ) -> ValidationResult:
        """
        Check compliance against a specific standard.
        
        Args:
            standard: Compliance standard to check
            content: Content to check
            agent_id: ID of the agent
            
        Returns:
            Compliance validation result
        """
        violations = []
        is_compliant = True
        confidence = 1.0
        risk_level = RiskLevel.SAFE
        
        # Standard-specific compliance checks
        if standard == "GDPR":
            # Check for GDPR compliance
            if "personal_data" in content.lower():
                violations.append("Potential personal data detected")
                risk_level = RiskLevel.MEDIUM_RISK
                
        elif standard == "HIPAA":
            # Check for HIPAA compliance
            if "health_information" in content.lower():
                violations.append("Potential health information detected")
                risk_level = RiskLevel.HIGH_RISK
                
        elif standard == "SOC2":
            # Check for SOC2 compliance
            if "security_incident" in content.lower():
                violations.append("Potential security incident detected")
                risk_level = RiskLevel.HIGH_RISK
                
        elif standard == "ISO27001":
            # Check for ISO27001 compliance
            if "information_security" in content.lower():
                violations.append("Potential information security issue detected")
                risk_level = RiskLevel.MEDIUM_RISK
        
        if violations:
            is_compliant = False
        
        return ValidationResult(
            is_safe=is_compliant,
            confidence=confidence,
            risk_level=risk_level,
            violations=violations
        )
    
    async def _check_action_standard_compliance(
        self,
        standard: str,
        agent_id: str,
        action: str,
        parameters: Dict[str, Any]
    ) -> ValidationResult:
        """
        Check action compliance against a specific standard.
        
        Args:
            standard: Compliance standard to check
            agent_id: ID of the agent
            action: Action to check
            parameters: Parameters for the action
            
        Returns:
            Compliance validation result
        """
        violations = []
        is_compliant = True
        confidence = 1.0
        risk_level = RiskLevel.SAFE
        
        # Standard-specific action compliance checks
        if standard == "GDPR":
            # Check for GDPR compliance in actions
            if action == "access_personal_data" and "consent" not in parameters:
                violations.append("Missing consent for personal data access")
                risk_level = RiskLevel.HIGH_RISK
                
        elif standard == "HIPAA":
            # Check for HIPAA compliance in actions
            if action == "access_health_data" and "authorization" not in parameters:
                violations.append("Missing authorization for health data access")
                risk_level = RiskLevel.CRITICAL_RISK
                
        elif standard == "SOC2":
            # Check for SOC2 compliance in actions
            if action == "modify_security_settings" and "approval" not in parameters:
                violations.append("Missing approval for security settings modification")
                risk_level = RiskLevel.HIGH_RISK
                
        elif standard == "ISO27001":
            # Check for ISO27001 compliance in actions
            if action == "access_sensitive_data" and "classification" not in parameters:
                violations.append("Missing data classification for sensitive data access")
                risk_level = RiskLevel.MEDIUM_RISK
        
        if violations:
            is_compliant = False
        
        return ValidationResult(
            is_safe=is_compliant,
            confidence=confidence,
            risk_level=risk_level,
            violations=violations
        )
    
    async def _check_behavior_standard_compliance(
        self,
        standard: str,
        agent_id: str,
        behavior_data: BehaviorData
    ) -> ValidationResult:
        """
        Check behavior compliance against a specific standard.
        
        Args:
            standard: Compliance standard to check
            agent_id: ID of the agent
            behavior_data: Behavior data to check
            
        Returns:
            Compliance validation result
        """
        violations = []
        is_compliant = True
        confidence = 1.0
        risk_level = RiskLevel.SAFE
        
        # Standard-specific behavior compliance checks
        if standard == "GDPR":
            # Check for GDPR compliance in behavior
            if behavior_data.metrics.get("data_access_count", 0) > 100:
                violations.append("Excessive data access detected")
                risk_level = RiskLevel.MEDIUM_RISK
                
        elif standard == "HIPAA":
            # Check for HIPAA compliance in behavior
            if behavior_data.metrics.get("health_data_access_count", 0) > 50:
                violations.append("Excessive health data access detected")
                risk_level = RiskLevel.HIGH_RISK
                
        elif standard == "SOC2":
            # Check for SOC2 compliance in behavior
            if behavior_data.metrics.get("security_policy_violations", 0) > 0:
                violations.append("Security policy violations detected")
                risk_level = RiskLevel.HIGH_RISK
                
        elif standard == "ISO27001":
            # Check for ISO27001 compliance in behavior
            if behavior_data.metrics.get("unauthorized_access_attempts", 0) > 0:
                violations.append("Unauthorized access attempts detected")
                risk_level = RiskLevel.HIGH_RISK
        
        if violations:
            is_compliant = False
        
        return ValidationResult(
            is_safe=is_compliant,
            confidence=confidence,
            risk_level=risk_level,
            violations=violations
        )
    
    async def _record_audit_entry(
        self,
        action: str,
        agent_id: str,
        details: Dict[str, Any]
    ) -> None:
        """
        Record audit entry.
        
        Args:
            action: Action being audited
            agent_id: ID of the agent
            details: Details of the action
        """
        async with self._audit_lock:
            audit_entry = {
                "timestamp": datetime.utcnow(),
                "action": action,
                "agent_id": agent_id,
                "details": details
            }
            
            self._audit_trail.append(audit_entry)
            
            # Limit audit trail size
            if len(self._audit_trail) > 10000:
                self._audit_trail = self._audit_trail[-10000:]
    
    async def _check_violation_threshold(self, agent_id: str) -> None:
        """
        Check if violation threshold is exceeded and escalate if needed.
        
        Args:
            agent_id: ID of the agent
        """
        async with self._violations_lock:
            agent_violations = self._compliance_violations.get(agent_id, [])
            
            # Count violations in the last 24 hours
            one_day_ago = datetime.utcnow() - timedelta(days=1)
            recent_violations = [
                v for v in agent_violations
                if v["timestamp"] > one_day_ago
            ]
            
            if len(recent_violations) >= self._compliance_config["violation_threshold"]:
                # Escalate violations
                await self._escalate_violations(agent_id, recent_violations)
    
    async def _escalate_violations(self, agent_id: str, violations: List[Dict[str, Any]]) -> None:
        """
        Escalate compliance violations.
        
        Args:
            agent_id: ID of the agent
            violations: List of violations to escalate
        """
        # Record escalation in audit trail
        await self._record_audit_entry(
            action="violation_escalation",
            agent_id=agent_id,
            details={
                "violation_count": len(violations),
                "escalation_contacts": self._compliance_config["escalation_contacts"]
            }
        )
        
        # In a real implementation, this would send notifications
        # to the escalation contacts
        logger.warning(f"Compliance violations escalated for agent {agent_id}")
    
    async def generate_report(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate compliance report.
        
        Args:
            agent_id: Optional agent ID to generate report for
            start_time: Optional start time for report period
            end_time: Optional end time for report period
            
        Returns:
            Compliance report
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Generate report ID
            report_id = f"compliance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Filter data by time range
            if start_time is None:
                start_time = datetime.utcnow() - timedelta(days=30)
            if end_time is None:
                end_time = datetime.utcnow()
            
            # Get compliance violations
            async with self._violations_lock:
                if agent_id:
                    violations = [
                        v for v in self._compliance_violations.get(agent_id, [])
                        if start_time <= v["timestamp"] <= end_time
                    ]
                else:
                    violations = []
                    for aid, agent_violations in self._compliance_violations.items():
                        violations.extend([
                            v for v in agent_violations
                            if start_time <= v["timestamp"] <= end_time
                        ])
            
            # Get audit trail
            async with self._audit_lock:
                audit_entries = [
                    entry for entry in self._audit_trail
                    if start_time <= entry["timestamp"] <= end_time
                ]
                
                if agent_id:
                    audit_entries = [
                        entry for entry in audit_entries
                        if entry["agent_id"] == agent_id
                    ]
            
            # Generate report
            report = {
                "report_id": report_id,
                "generated_at": datetime.utcnow(),
                "report_period": {
                    "start_time": start_time,
                    "end_time": end_time
                },
                "agent_id": agent_id,
                "compliance_standards": self._compliance_config["compliance_standards"],
                "summary": {
                    "total_violations": len(violations),
                    "total_audit_entries": len(audit_entries),
                    "violation_rate": len(violations) / max(len(audit_entries), 1)
                },
                "violations": violations,
                "audit_entries": audit_entries,
                "recommendations": self._generate_recommendations(violations)
            }
            
            # Store report
            async with self._reports_lock:
                self._compliance_reports[report_id] = report
            
            return report
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, violations: List[Dict[str, Any]]) -> List[str]:
        """
        Generate recommendations based on compliance violations.
        
        Args:
            violations: List of compliance violations
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Count violation types
        violation_types = {}
        for violation in violations:
            for v in violation.get("violations", []):
                violation_types[v] = violation_types.get(v, 0) + 1
        
        # Generate recommendations based on violation types
        for violation_type, count in violation_types.items():
            if "personal data" in violation_type.lower():
                recommendations.append("Implement stronger personal data protection measures")
            elif "health information" in violation_type.lower():
                recommendations.append("Review and strengthen health information handling procedures")
            elif "security" in violation_type.lower():
                recommendations.append("Enhance security controls and monitoring")
            elif "access" in violation_type.lower():
                recommendations.append("Review and tighten access controls")
        
        # Add general recommendations
        if violations:
            recommendations.append("Review and update compliance policies")
            recommendations.append("Provide additional compliance training")
        
        return recommendations
    
    async def health_check(self) -> bool:
        """Check health of the Compliance Integrator."""
        if not self._initialized:
            return False
            
        try:
            # Check if compliance checking is enabled
            if not self._compliance_config["enable_compliance_checking"]:
                return False
            
            # Check if audit trail is enabled
            if not self._compliance_config["enable_audit_trail"]:
                return False
            
            # Check if reporting is enabled
            if not self._compliance_config["enable_reporting"]:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Compliance Integrator health check failed: {e}")
            return False
    
    async def start(self) -> None:
        """Start the Compliance Integrator."""
        if not self._initialized:
            await self.initialize()
        
        logger.info("Compliance Integrator started successfully")
    
    async def stop(self) -> None:
        """Stop the Compliance Integrator."""
        if not self._initialized:
            return
        
        # Clear data structures
        async with self._violations_lock:
            self._compliance_violations.clear()
        
        async with self._audit_lock:
            self._audit_trail.clear()
        
        async with self._reports_lock:
            self._compliance_reports.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Compliance Integrator stopped successfully")


class AgentSafety(BaseService):
    """
    Agent Safety service for managing agent safety and security.
    
    This service provides safety mechanisms for agents, including content filtering,
    action validation, and security checks to ensure agents operate safely.
    """
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        """Initialize the Agent Safety service."""
        super().__init__(config or SafetyConfig())
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Initialize content safety components
        self._filter_rules: Dict[str, FilterRule] = {}
        self._content_scanners = {}
        self._context_analyzers = {}
        
        # Initialize behavior monitoring components
        self.behavior_tracker = BehaviorTracker(config=self.config)
        self.anomaly_detector = AnomalyDetector(config=self.config)
        self.pattern_recognizer = PatternRecognizer(config=self.config)
        self.baseline_generator = BaselineGenerator(config=self.config)
        self.behavior_profiler = BehaviorProfiler(config=self.config)
        self.risk_assessor = RiskAssessor(config=self.config)
        self.correlation_engine = CorrelationEngine(config=self.config)
        self.behavior_logger = BehaviorLogger(config=self.config)
        # Note: agent_safety_logger removed to prevent circular instantiation
        
        # Initialize compliance integration
        self.compliance_integrator = ComplianceIntegrator(config=self.config)
        
        # Initialize policy enforcement engine
        # Create a ServiceConfig for the PolicyEnforcementEngine
        pe_config = ServiceConfig(name="policy_enforcement", version="1.0.0")
        self.policy_enforcement_engine = PolicyEnforcementEngine(config=pe_config)
        
        # Initialize enhanced services integrator
        # Create a ServiceConfig for the EnhancedServicesIntegrator
        esi_config = ServiceConfig(name="enhanced_services_integration", version="1.0.0")
        self.enhanced_services_integrator = EnhancedServicesIntegrator(config=esi_config)
        
        # Thread-safe data structures
        self._agent_behavior_data: Dict[str, List[BehaviorData]] = defaultdict(list)
        self._agent_behavior_profiles: Dict[str, BehaviorProfile] = {}
        self._agent_baselines: Dict[str, Dict[str, Any]] = {}
        self._agent_risk_history: Dict[str, List[RiskAssessment]] = defaultdict(list)
        
        # Thread-safe locks
        self._behavior_data_lock = asyncio.Lock()
        self._profiles_lock = asyncio.Lock()
        self._baselines_lock = asyncio.Lock()
        self._risk_history_lock = asyncio.Lock()
        self._compliance_lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize the Agent Safety service."""
        if self._initialized:
            return
            
        async with self._lock:
            try:
                # Initialize behavior monitoring components
                modules_to_initialize = [
                    ("behavior tracker", self.behavior_tracker),
                    ("anomaly detector", self.anomaly_detector),
                    ("pattern recognizer", self.pattern_recognizer),
                    ("baseline generator", self.baseline_generator),
                    ("behavior profiler", self.behavior_profiler),
                    ("risk assessor", self.risk_assessor),
                    ("correlation engine", self.correlation_engine),
                    ("behavior logger", self.behavior_logger)
                ]
                
                for module_name, module in modules_to_initialize:
                    try:
                        await module.initialize()
                        logger.debug(f"Successfully initialized {module_name}")
                    except Exception as e:
                        logger.error(f"Failed to initialize {module_name}: {e}")
                        # Continue with other modules even if one fails
                
                # Initialize compliance integrator
                await self.compliance_integrator.initialize()
                
                # Initialize policy enforcement engine
                await self.policy_enforcement_engine.initialize()
                
                # Initialize enhanced services integrator
                await self.enhanced_services_integrator.initialize()
                
                # Load default filter rules
                await self._load_default_filter_rules()
                
                self._initialized = True
                logger.info("Agent Safety service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Agent Safety service: {e}")
                raise RuntimeError(f"Agent Safety service initialization failed: {e}")
    
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
    
    async def check_content_safety(self, content: str, agent_id: str = "unknown") -> ValidationResult:
        """
        Check if content is safe.
        
        Args:
            content: Content to check
            agent_id: ID of the agent generating the content
            
        Returns:
            Validation result
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Create content input
            content_input = ContentInput(
                content=content,
                content_type=ContentType.TEXT,
                metadata={"agent_id": agent_id}
            )
            
            # Create context
            context = Context(agent_id=agent_id)
            
            # Apply filter rules
            violations = []
            matched_patterns = []
            is_safe = True
            confidence = 1.0
            risk_level = RiskLevel.SAFE
            
            for rule_id, rule in self._filter_rules.items():
                if rule.is_active and ContentType.TEXT in rule.content_types:
                    if re.search(rule.pattern, content, re.IGNORECASE):
                        violations.append(f"Matched rule: {rule.name}")
                        matched_patterns.append(rule.pattern)
                        if rule.risk_level.value > risk_level.value:
                            risk_level = rule.risk_level
                        if rule.risk_level in [RiskLevel.HIGH_RISK, RiskLevel.CRITICAL_RISK]:
                            is_safe = False
                            confidence = 0.9
            
            # Check compliance
            compliance_result = await self.compliance_integrator.check_content_compliance(
                content=content,
                agent_id=agent_id
            )
            
            if not compliance_result.is_compliant:
                violations.extend(compliance_result.violations)
                is_safe = False
                if compliance_result.risk_level.value > risk_level.value:
                    risk_level = compliance_result.risk_level
            
            # Enforce content policy
            policy_result = await self.enforce_content_policy(content, agent_id)
            
            # Process policy enforcement results
            for result in policy_result:
                if result.is_violation:
                    violations.append(f"Policy violation: {result.policy_name}")
                    is_safe = False
                    
                    # Update risk level based on violation severity
                    if result.violation and result.violation.severity.value > risk_level.value:
                        risk_level = result.violation.severity
                    
                    # Update confidence based on enforcement action
                    if result.enforcement_action == EnforcementAction.BLOCK:
                        confidence = 0.0
                    elif result.enforcement_action == EnforcementAction.WARN:
                        confidence = min(confidence, 0.5)
            
            return ValidationResult(
                is_safe=is_safe,
                confidence=confidence,
                risk_level=risk_level,
                violations=violations,
                matched_patterns=matched_patterns
            )
        except Exception as e:
            logger.error(f"Error checking content safety: {e}")
            return ValidationResult(
                is_safe=False,
                confidence=0.0,
                risk_level=RiskLevel.CRITICAL_RISK,
                violations=["Content safety check failed"]
            )
    
    async def check_action_safety(
        self,
        agent_id: str,
        action: str,
        parameters: Dict[str, Any]
    ) -> ValidationResult:
        """
        Check if an action is safe for an agent to perform.
        
        Args:
            agent_id: Unique identifier of the agent
            action: Action to check
            parameters: Parameters for the action
            
        Returns:
            Validation result
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Check compliance
            compliance_result = await self.compliance_integrator.check_action_compliance(
                agent_id=agent_id,
                action=action,
                parameters=parameters
            )
            
            # Enforce action policy
            policy_result = await self.enforce_action_policy(agent_id, action, parameters)
            
            # Process policy enforcement results
            violations = compliance_result.violations.copy()
            is_safe = compliance_result.is_compliant
            confidence = compliance_result.confidence
            risk_level = compliance_result.risk_level
            
            # Check if any policy was violated
            for result in policy_result:
                if result.is_violation:
                    violations.append(f"Policy violation: {result.policy_name}")
                    is_safe = False
                    
                    # Update risk level based on violation severity
                    if result.violation and result.violation.severity.value > risk_level.value:
                        risk_level = result.violation.severity
                    
                    # Update confidence based on enforcement action
                    if result.enforcement_action == EnforcementAction.BLOCK:
                        confidence = 0.0
                    elif result.enforcement_action == EnforcementAction.WARN:
                        confidence = min(confidence, 0.5)
            
            return ValidationResult(
                is_safe=is_safe,
                confidence=confidence,
                risk_level=risk_level,
                violations=violations
            )
        except Exception as e:
            logger.error(f"Error checking action safety: {e}")
            return ValidationResult(
                is_safe=False,
                confidence=0.0,
                risk_level=RiskLevel.CRITICAL_RISK,
                violations=["Action safety check failed"]
            )
    
    async def check_response_safety(
        self,
        agent_id: str,
        response: str
    ) -> ValidationResult:
        """
        Check if a response from an agent is safe.
        
        Args:
            agent_id: Unique identifier of the agent
            response: Response to check
            
        Returns:
            Validation result
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Check content safety
            content_result = await self.check_content_safety(response, agent_id)
            
            # Check compliance
            compliance_result = await self.compliance_integrator.check_response_compliance(
                agent_id=agent_id,
                response=response
            )
            
            # Combine results
            violations = content_result.violations + compliance_result.violations
            is_safe = content_result.is_safe and compliance_result.is_compliant
            risk_level = max(content_result.risk_level, compliance_result.risk_level, key=lambda x: x.value)
            
            return ValidationResult(
                is_safe=is_safe,
                confidence=min(content_result.confidence, compliance_result.confidence),
                risk_level=risk_level,
                violations=violations
            )
        except Exception as e:
            logger.error(f"Error checking response safety: {e}")
            return ValidationResult(
                is_safe=False,
                confidence=0.0,
                risk_level=RiskLevel.CRITICAL_RISK,
                violations=["Response safety check failed"]
            )
    
    async def track_agent_behavior(self, agent_id: str, behavior_data: BehaviorData) -> bool:
        """
        Track agent behavior.
        
        Args:
            agent_id: Unique identifier of the agent
            behavior_data: Behavior data to track
            
        Returns:
            True if tracking was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            # Thread-safe access to behavior data
            async with self._behavior_data_lock:
                # Add behavior data to agent's history
                self._agent_behavior_data[agent_id].append(behavior_data)
                
                # Limit history size
                if len(self._agent_behavior_data[agent_id]) > 1000:
                    self._agent_behavior_data[agent_id] = self._agent_behavior_data[agent_id][-1000:]
            
            # Log the behavior data
            await self.behavior_logger.log_behavior_data(behavior_data)
            
            # Check compliance
            await self.compliance_integrator.check_behavior_compliance(
                agent_id=agent_id,
                behavior_data=behavior_data
            )
            
            # Enforce behavior policy
            await self.enforce_behavior_policy(agent_id, behavior_data)
            
            return True
        except Exception as e:
            logger.error(f"Error tracking agent behavior: {e}")
            return False
    
    async def generate_compliance_report(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate compliance report.
        
        Args:
            agent_id: Optional agent ID to generate report for
            start_time: Optional start time for report period
            end_time: Optional end time for report period
            
        Returns:
            Compliance report
        """
        if not self._initialized:
            await self.initialize()
            
        try:
            return await self.compliance_integrator.generate_report(
                agent_id=agent_id,
                start_time=start_time,
                end_time=end_time
            )
        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check health of the Agent Safety service."""
        if not self._initialized:
            return False
            
        try:
            # Check behavior monitoring modules health
            behavior_modules_healthy = all([
                await self.behavior_tracker.health_check(),
                await self.anomaly_detector.health_check(),
                await self.pattern_recognizer.health_check(),
                await self.baseline_generator.health_check(),
                await self.behavior_profiler.health_check(),
                await self.risk_assessor.health_check(),
                await self.correlation_engine.health_check(),
                await self.behavior_logger.health_check()
            ])
            
            # Check compliance integrator health
            compliance_healthy = await self.compliance_integrator.health_check()
            
            # Check policy enforcement engine health
            policy_engine_healthy = await self.policy_enforcement_engine.health_check()
            
            # Check enhanced services integrator health
            enhanced_services_healthy = await self.enhanced_services_integrator.health_check()
            
            return behavior_modules_healthy and compliance_healthy and policy_engine_healthy and enhanced_services_healthy
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def enforce_content_policy(
        self,
        content: str,
        agent_id: str = "unknown"
    ) -> List[PolicyEnforcementResult]:
        """
        Enforce content policy.
        
        Args:
            content: Content to check
            agent_id: ID of the agent generating the content
            
        Returns:
            List of policy enforcement results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Create context
            context = Context(agent_id=agent_id)
            
            # Enforce content policies
            return await self.policy_enforcement_engine.enforce_policies(
                policy_type=PolicyType.CONTENT_POLICY,
                context=context,
                content=content
            )
        except Exception as e:
            logger.error(f"Error enforcing content policy: {e}")
            return [PolicyEnforcementResult(
                policy_id="error",
                policy_name="Error",
                enforcement_action=EnforcementAction.BLOCK,
                is_violation=True,
                is_allowed=False
            )]
    
    async def enforce_action_policy(
        self,
        agent_id: str,
        action: str,
        parameters: Dict[str, Any]
    ) -> List[PolicyEnforcementResult]:
        """
        Enforce action policy.
        
        Args:
            agent_id: Unique identifier of the agent
            action: Action to check
            parameters: Parameters for the action
            
        Returns:
            List of policy enforcement results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Create context
            context = Context(agent_id=agent_id)
            
            # Enforce action policies
            return await self.policy_enforcement_engine.enforce_policies(
                policy_type=PolicyType.ACTION_POLICY,
                context=context,
                action=action,
                parameters=parameters
            )
        except Exception as e:
            logger.error(f"Error enforcing action policy: {e}")
            return [PolicyEnforcementResult(
                policy_id="error",
                policy_name="Error",
                enforcement_action=EnforcementAction.BLOCK,
                is_violation=True,
                is_allowed=False
            )]
    
    async def enforce_behavior_policy(
        self,
        agent_id: str,
        behavior_data: BehaviorData
    ) -> List[PolicyEnforcementResult]:
        """
        Enforce behavior policy.
        
        Args:
            agent_id: Unique identifier of the agent
            behavior_data: Behavior data to check
            
        Returns:
            List of policy enforcement results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Create context
            context = Context(agent_id=agent_id)
            
            # Enforce behavior policies
            return await self.policy_enforcement_engine.enforce_policies(
                policy_type=PolicyType.BEHAVIOR_POLICY,
                context=context,
                behavior_data=behavior_data
            )
        except Exception as e:
            logger.error(f"Error enforcing behavior policy: {e}")
            return [PolicyEnforcementResult(
                policy_id="error",
                policy_name="Error",
                enforcement_action=EnforcementAction.BLOCK,
                is_violation=True,
                is_allowed=False
            )]
    
    async def add_safety_policy(
        self,
        policy: Policy
    ) -> bool:
        """
        Add a safety policy.
        
        Args:
            policy: Policy to add
            
        Returns:
            True if addition was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.policy_enforcement_engine.add_policy(policy)
        except Exception as e:
            logger.error(f"Error adding safety policy: {e}")
            return False
    
    async def remove_safety_policy(
        self,
        policy_id: str
    ) -> bool:
        """
        Remove a safety policy.
        
        Args:
            policy_id: ID of the policy to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.policy_enforcement_engine.remove_policy(policy_id)
        except Exception as e:
            logger.error(f"Error removing safety policy: {e}")
            return False
    
    async def get_safety_policy(
        self,
        policy_id: str
    ) -> Optional[Policy]:
        """
        Get a safety policy.
        
        Args:
            policy_id: ID of the policy to get
            
        Returns:
            Policy if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.policy_enforcement_engine.get_policy(policy_id)
        except Exception as e:
            logger.error(f"Error getting safety policy: {e}")
            return None
    
    async def get_safety_policies(
        self,
        policy_type: Optional[PolicyType] = None,
        status: Optional[str] = None
    ) -> List[Policy]:
        """
        Get safety policies.
        
        Args:
            policy_type: Optional policy type to filter by
            status: Optional policy status to filter by
            
        Returns:
            List of policies
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Convert string status to PolicyStatus enum if provided
            policy_status = None
            if status:
                try:
                    from .AgentSafetyClass.PolicyEnforcementEngine import PolicyStatus
                    policy_status = PolicyStatus(status)
                except ValueError:
                    logger.warning(f"Invalid policy status: {status}")
            
            return await self.policy_enforcement_engine.get_policies(
                policy_type=policy_type,
                status=policy_status
            )
        except Exception as e:
            logger.error(f"Error getting safety policies: {e}")
            return []
    
    async def test_safety_policy(
        self,
        policy_id: str,
        test_name: str,
        test_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Test a safety policy.
        
        Args:
            policy_id: ID of the policy to test
            test_name: Name of the test
            test_data: Test data
            
        Returns:
            Test result
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            test_result = await self.policy_enforcement_engine.test_policy(
                policy_id=policy_id,
                test_name=test_name,
                test_data=test_data
            )
            
            return {
                "policy_id": test_result.policy_id,
                "test_name": test_result.test_name,
                "passed": test_result.passed,
                "message": test_result.message,
                "timestamp": test_result.timestamp
            }
        except Exception as e:
            logger.error(f"Error testing safety policy: {e}")
            return {
                "policy_id": policy_id,
                "test_name": test_name,
                "passed": False,
                "message": f"Error testing policy: {str(e)}",
                "timestamp": datetime.utcnow()
            }
    
    async def get_policy_violations(
        self,
        agent_id: Optional[str] = None,
        policy_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
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
        
        try:
            violations = await self.policy_enforcement_engine.get_violations(
                agent_id=agent_id,
                policy_id=policy_id,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            
            return [
                {
                    "violation_id": v.violation_id,
                    "policy_id": v.policy_id,
                    "policy_name": v.policy_name,
                    "agent_id": v.agent_id,
                    "violation_type": v.violation_type,
                    "severity": v.severity.value,
                    "description": v.description,
                    "detected_at": v.detected_at
                }
                for v in violations
            ]
        except Exception as e:
            logger.error(f"Error getting policy violations: {e}")
            return []

    async def register_enhanced_service(self, service_name: str, service: BaseService) -> bool:
        """
        Register an enhanced service for integration.
        
        Args:
            service_name: Name of the service
            service: Service instance
            
        Returns:
            True if registration was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.enhanced_services_integrator.register_service(service_name, service)
        except Exception as e:
            logger.error(f"Error registering enhanced service {service_name}: {e}")
            return False
    
    async def unregister_enhanced_service(self, service_name: str) -> bool:
        """
        Unregister an enhanced service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.enhanced_services_integrator.unregister_service(service_name)
        except Exception as e:
            logger.error(f"Error unregistering enhanced service {service_name}: {e}")
            return False
    
    async def get_enhanced_service_health(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the health status of an enhanced service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service health if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            health = await self.enhanced_services_integrator.get_service_health(service_name)
            if health:
                return {
                    "service_name": health.service_name,
                    "status": health.status.value,
                    "response_time": health.response_time,
                    "last_check": health.last_check
                }
            return None
        except Exception as e:
            logger.error(f"Error getting enhanced service health for {service_name}: {e}")
            return None
    
    async def coordinate_safety_action(
        self,
        service_name: str,
        action: str,
        agent_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Coordinate a safety action with an enhanced service.
        
        Args:
            service_name: Name of the service
            action: Action to coordinate
            agent_id: ID of the agent
            **kwargs: Additional parameters
            
        Returns:
            Safety coordination result
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Create context
            context = Context(agent_id=agent_id)
            
            # Coordinate safety action
            result = await self.enhanced_services_integrator.coordinate_safety_action(
                service_name=service_name,
                action=action,
                context=context,
                **kwargs
            )
            
            return {
                "coordination_id": result.coordination_id,
                "service_name": result.service_name,
                "action": result.action,
                "success": result.success,
                "message": result.message,
                "timestamp": result.timestamp
            }
        except Exception as e:
            logger.error(f"Error coordinating safety action with {service_name}: {e}")
            return {
                "coordination_id": f"coordination_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
                "service_name": service_name,
                "action": action,
                "success": False,
                "message": f"Error coordinating safety action: {str(e)}",
                "timestamp": datetime.utcnow()
            }
    
    async def start(self) -> None:
        """Start the Agent Safety service."""
        if not self._initialized:
            await self.initialize()
        
        # Start behavior monitoring components
        try:
            await self.behavior_tracker.start()
            await self.anomaly_detector.start()
            await self.pattern_recognizer.start()
            await self.baseline_generator.start()
            await self.behavior_profiler.start()
            await self.risk_assessor.start()
            await self.correlation_engine.start()
            await self.behavior_logger.start()
        except Exception as e:
            logger.error(f"Error starting behavior monitoring components: {e}")
        
        # Start compliance integrator
        try:
            await self.compliance_integrator.start()
        except Exception as e:
            logger.error(f"Error starting compliance integrator: {e}")
        
        # Start policy enforcement engine
        try:
            await self.policy_enforcement_engine.start()
        except Exception as e:
            logger.error(f"Error starting policy enforcement engine: {e}")
        
        # Start enhanced services integrator
        try:
            await self.enhanced_services_integrator.start()
        except Exception as e:
            logger.error(f"Error starting enhanced services integrator: {e}")
        
        logger.info("Agent Safety service started successfully")
    
    async def stop(self) -> None:
        """Stop the Agent Safety service."""
        if not self._initialized:
            return
        
        # Stop behavior monitoring components
        try:
            await self.behavior_tracker.stop()
            await self.anomaly_detector.stop()
            await self.pattern_recognizer.stop()
            await self.baseline_generator.stop()
            await self.behavior_profiler.stop()
            await self.risk_assessor.stop()
            await self.correlation_engine.stop()
            await self.behavior_logger.stop()
        except Exception as e:
            logger.error(f"Error stopping behavior monitoring components: {e}")
        
        # Stop compliance integrator
        try:
            await self.compliance_integrator.stop()
        except Exception as e:
            logger.error(f"Error stopping compliance integrator: {e}")
        
        # Stop policy enforcement engine
        try:
            await self.policy_enforcement_engine.stop()
        except Exception as e:
            logger.error(f"Error stopping policy enforcement engine: {e}")
        
        # Stop enhanced services integrator
        try:
            await self.enhanced_services_integrator.stop()
        except Exception as e:
            logger.error(f"Error stopping enhanced services integrator: {e}")
        
        # Clear data structures
        async with self._behavior_data_lock:
            self._agent_behavior_data.clear()
        
        async with self._profiles_lock:
            self._agent_behavior_profiles.clear()
        
        async with self._baselines_lock:
            self._agent_baselines.clear()
        
        async with self._risk_history_lock:
            self._agent_risk_history.clear()
        
        # Reset initialization state
        self._initialized = False
        
        logger.info("Agent Safety service stopped successfully")
