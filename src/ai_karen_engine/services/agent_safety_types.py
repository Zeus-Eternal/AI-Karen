"""
Agent Safety data types and structures.

This module contains all the data types and structures used by the Agent Safety system
to avoid circular import issues.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from ai_karen_engine.core.services.base import ServiceConfig

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Content type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    STRUCTURED = "structured"


class SafetyLevel(str, Enum):
    """Safety level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    """Risk level enumeration."""
    SAFE = "safe"
    LOW_RISK = "low_risk"
    MEDIUM_RISK = "medium_risk"
    HIGH_RISK = "high_risk"
    CRITICAL_RISK = "critical_risk"


@dataclass
class ContentInput:
    """Content input data structure."""
    content: Any
    content_type: ContentType
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ContentOutput:
    """Content output data structure."""
    content: Any
    content_type: ContentType
    is_filtered: bool = False
    filter_reason: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Validation result data structure."""
    is_safe: bool
    confidence: float
    risk_level: RiskLevel
    is_compliant: bool = True
    violations: List[str] = field(default_factory=list)
    matched_patterns: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FilteredOutput:
    """Filtered output data structure."""
    content: Any
    content_type: ContentType
    is_filtered: bool
    filter_reason: Optional[str] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Context:
    """Context data structure for content analysis."""
    agent_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    task_id: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FilterRule:
    """Filter rule data structure."""
    rule_id: str
    name: str
    description: str
    pattern: str
    content_types: List[ContentType] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM_RISK
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SafetyConfig(ServiceConfig):
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
    
    def __post_init__(self):
        """Initialize ServiceConfig fields."""
        if not hasattr(self, 'name') or not self.name:
            self.name = "agent_safety"
        if not hasattr(self, 'version') or not self.version:
            self.version = "1.0.0"


@dataclass
class BehaviorData:
    """Behavior data structure for agent monitoring."""
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metrics: Dict[str, Any] = field(default_factory=dict)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    response_patterns: Dict[str, Any] = field(default_factory=dict)
    interaction_patterns: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehaviorMetrics:
    """Behavior metrics data structure."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_usage: float = 0.0
    response_time: float = 0.0
    error_rate: float = 0.0
    task_completion_rate: float = 0.0
    interaction_frequency: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyResult:
    """Anomaly detection result data structure."""
    is_anomaly: bool
    anomaly_score: float
    anomaly_type: str
    confidence: float
    description: str
    detected_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternResult:
    """Pattern recognition result data structure."""
    pattern_detected: bool
    pattern_type: str
    confidence: float
    pattern_id: Optional[str] = None
    severity: RiskLevel = RiskLevel.LOW_RISK
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BaselineResult:
    """Baseline comparison result data structure."""
    baseline_id: str
    deviation_score: float
    is_within_threshold: bool
    threshold: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehaviorProfile:
    """Agent behavior profile data structure."""
    agent_id: str
    profile_type: str
    behavior_trends: Dict[str, Any] = field(default_factory=dict)
    risk_history: List[Dict[str, Any]] = field(default_factory=list)
    behavior_categories: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskAssessment:
    """Risk assessment data structure."""
    risk_level: RiskLevel
    risk_score: float
    factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CorrelationResult:
    """Correlation analysis result data structure."""
    correlation_detected: bool
    correlation_type: str
    correlation_strength: float
    confidence: float
    correlated_agents: List[str] = field(default_factory=list)
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehaviorAnalysis:
    """Complete behavior analysis result data structure."""
    agent_id: str
    anomaly_result: AnomalyResult
    pattern_result: PatternResult
    baseline_result: BaselineResult
    profile_result: BehaviorProfile
    risk_result: RiskAssessment
    correlation_result: CorrelationResult
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)