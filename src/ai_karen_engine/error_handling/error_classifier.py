"""
Error Classification and Categorization System

This module provides comprehensive error classification with intelligent categorization
based on error type, severity, and context for the CoPilot system.
"""

import re
import traceback
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

from ai_karen_engine.utils.error_handling import ErrorCategory as BaseErrorCategory, ErrorSeverity as BaseErrorSeverity


class ErrorCategory(Enum):
    """Extended error categories for comprehensive classification."""
    
    # Network and connectivity
    NETWORK = "network"
    CONNECTIVITY = "connectivity"
    API_FAILURE = "api_failure"
    
    # System and infrastructure
    SYSTEM = "system"
    INFRASTRUCTURE = "infrastructure"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    
    # Application and business logic
    APPLICATION = "application"
    BUSINESS_LOGIC = "business_logic"
    VALIDATION = "validation"
    
    # Security and authentication
    SECURITY = "security"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    
    # AI/ML specific
    AI_PROCESSING = "ai_processing"
    MODEL_UNAVAILABLE = "model_unavailable"
    LLM_PROVIDER = "llm_provider"
    
    # User interface
    UI_COMPONENT = "ui_component"
    USER_INPUT = "user_input"
    
    # Performance and resources
    PERFORMANCE = "performance"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    TIMEOUT = "timeout"
    
    # Configuration and deployment
    CONFIGURATION = "configuration"
    DEPLOYMENT = "deployment"
    
    # External dependencies
    EXTERNAL_SERVICE = "external_service"
    THIRD_PARTY = "third_party"
    
    # Unknown/unclassified
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity levels with impact assessment."""
    
    LOW = "low"           # Minor issue, no impact on core functionality
    MEDIUM = "medium"     # Degraded functionality, workarounds available
    HIGH = "high"         # Significant impact, limited functionality
    CRITICAL = "critical" # System unavailable, major functionality loss
    FATAL = "fatal"       # Complete system failure, requires immediate attention


class ErrorType(Enum):
    """Specific error types for fine-grained classification."""
    
    # Network errors
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    DNS_ERROR = "dns_error"
    
    # System errors
    MEMORY_ERROR = "memory_error"
    DISK_SPACE_ERROR = "disk_space_error"
    PERMISSION_ERROR = "permission_error"
    PROCESS_ERROR = "process_error"
    
    # Application errors
    VALIDATION_ERROR = "validation_error"
    LOGIC_ERROR = "logic_error"
    DEPENDENCY_ERROR = "dependency_error"
    
    # AI/ML errors
    MODEL_LOADING_ERROR = "model_loading_error"
    INFERENCE_ERROR = "inference_error"
    CONTEXT_TOO_LARGE = "context_too_large"
    TOKEN_LIMIT_EXCEEDED = "token_limit_exceeded"
    
    # Database errors
    CONNECTION_POOL_ERROR = "connection_pool_error"
    QUERY_ERROR = "query_error"
    TRANSACTION_ERROR = "transaction_error"
    
    # UI errors
    RENDER_ERROR = "render_error"
    COMPONENT_ERROR = "component_error"
    STATE_ERROR = "state_error"


@dataclass
class ErrorPattern:
    """Pattern for matching and classifying errors."""
    
    name: str
    patterns: List[str]
    category: ErrorCategory
    severity: ErrorSeverity
    error_type: ErrorType
    recovery_strategies: List[str] = field(default_factory=list)
    user_message: Optional[str] = None
    technical_details: Optional[str] = None
    resolution_steps: List[str] = field(default_factory=list)
    retry_possible: bool = True
    user_action_required: bool = False


@dataclass
class ErrorClassification:
    """Complete error classification result."""
    
    category: ErrorCategory
    severity: ErrorSeverity
    error_type: ErrorType
    pattern_name: Optional[str] = None
    user_message: Optional[str] = None
    technical_details: Optional[str] = None
    resolution_steps: List[str] = field(default_factory=list)
    recovery_strategies: List[str] = field(default_factory=list)
    retry_possible: bool = True
    user_action_required: bool = False
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ErrorClassifier:
    """
    Intelligent error classifier with pattern matching and context analysis.
    
    This classifier provides:
    - Pattern-based error classification
    - Context-aware severity assessment
    - Automatic recovery strategy suggestion
    - User-friendly message generation
    - Technical detail extraction
    """
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.severity_adjusters = self._initialize_severity_adjusters()
        self.context_analyzers = self._initialize_context_analyzers()
    
    def _initialize_patterns(self) -> List[ErrorPattern]:
        """Initialize error patterns for classification."""
        return [
            # Network and connectivity patterns
            ErrorPattern(
                name="connection_refused",
                patterns=[
                    r"connection refused",
                    r"connection.*refused",
                    r"could not connect",
                    r"connection.*failed"
                ],
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH,
                error_type=ErrorType.CONNECTION_ERROR,
                recovery_strategies=["retry_with_backoff", "circuit_breaker"],
                user_message="Unable to connect to the service. Please check your network connection.",
                technical_details="Network connection could not be established",
                resolution_steps=[
                    "Check your internet connection",
                    "Verify the service is available",
                    "Try again in a few moments"
                ],
                retry_possible=True
            ),
            
            ErrorPattern(
                name="timeout_error",
                patterns=[
                    r"timeout",
                    r"timed out",
                    r"request timeout",
                    r"operation timeout"
                ],
                category=ErrorCategory.TIMEOUT,
                severity=ErrorSeverity.MEDIUM,
                error_type=ErrorType.TIMEOUT_ERROR,
                recovery_strategies=["retry_with_backoff", "increase_timeout"],
                user_message="The operation took too long to complete. Please try again.",
                technical_details="Operation exceeded timeout limit",
                resolution_steps=[
                    "Try again with a simpler request",
                    "Check if the service is experiencing high load",
                    "Increase timeout settings if possible"
                ],
                retry_possible=True
            ),
            
            ErrorPattern(
                name="rate_limit_error",
                patterns=[
                    r"rate limit",
                    r"too many requests",
                    r"429",
                    r"quota exceeded"
                ],
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                error_type=ErrorType.RATE_LIMIT_ERROR,
                recovery_strategies=["exponential_backoff", "circuit_breaker"],
                user_message="Too many requests. Please wait before trying again.",
                technical_details="API rate limit exceeded",
                resolution_steps=[
                    "Wait before making another request",
                    "Reduce request frequency",
                    "Consider upgrading your plan if applicable"
                ],
                retry_possible=True
            ),
            
            # AI/ML specific patterns
            ErrorPattern(
                name="model_unavailable",
                patterns=[
                    r"model.*unavailable",
                    r"model.*not found",
                    r"model.*loading.*failed",
                    r"model.*error"
                ],
                category=ErrorCategory.MODEL_UNAVAILABLE,
                severity=ErrorSeverity.HIGH,
                error_type=ErrorType.MODEL_LOADING_ERROR,
                recovery_strategies=["fallback_model", "retry_later"],
                user_message="The AI model is currently unavailable. Using fallback model.",
                technical_details="Requested AI model could not be loaded",
                resolution_steps=[
                    "Try again in a few moments",
                    "Use an alternative model if available",
                    "Contact support if the problem persists"
                ],
                retry_possible=True
            ),
            
            ErrorPattern(
                name="context_too_large",
                patterns=[
                    r"context.*too large",
                    r"token.*limit",
                    r"maximum.*context",
                    r"input.*too long"
                ],
                category=ErrorCategory.AI_PROCESSING,
                severity=ErrorSeverity.MEDIUM,
                error_type=ErrorType.CONTEXT_TOO_LARGE,
                recovery_strategies=["truncate_context", "split_request"],
                user_message="The request is too large. Please reduce the input size.",
                technical_details="Input context exceeds token limit",
                resolution_steps=[
                    "Reduce the length of your input",
                    "Split the request into smaller parts",
                    "Remove unnecessary context"
                ],
                retry_possible=True,
                user_action_required=True
            ),
            
            # Database patterns
            ErrorPattern(
                name="database_connection_error",
                patterns=[
                    r"database.*connection",
                    r"connection.*pool",
                    r"db.*connection",
                    r"sql.*connection"
                ],
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.HIGH,
                error_type=ErrorType.CONNECTION_POOL_ERROR,
                recovery_strategies=["retry_with_backoff", "connection_pool_reset"],
                user_message="Database connection issue. Please try again.",
                technical_details="Database connection could not be established",
                resolution_steps=[
                    "Try again in a few moments",
                    "Check database service status",
                    "Verify connection configuration"
                ],
                retry_possible=True
            ),
            
            ErrorPattern(
                name="permission_error",
                patterns=[
                    r"permission denied",
                    r"access denied",
                    r"unauthorized",
                    r"forbidden"
                ],
                category=ErrorCategory.AUTHORIZATION,
                severity=ErrorSeverity.HIGH,
                error_type=ErrorType.PERMISSION_ERROR,
                recovery_strategies=["reauthenticate", "check_permissions"],
                user_message="You don't have permission to perform this action.",
                technical_details="Authorization check failed",
                resolution_steps=[
                    "Check your permissions",
                    "Contact your administrator",
                    "Ensure you're properly authenticated"
                ],
                retry_possible=False,
                user_action_required=True
            ),
            
            ErrorPattern(
                name="validation_error",
                patterns=[
                    r"validation.*error",
                    r"invalid.*input",
                    r"validation.*failed",
                    r"bad request"
                ],
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.MEDIUM,
                error_type=ErrorType.VALIDATION_ERROR,
                recovery_strategies=["correct_input", "provide_required_fields"],
                user_message="Invalid input provided. Please check your data.",
                technical_details="Input validation failed",
                resolution_steps=[
                    "Check all required fields",
                    "Verify data format",
                    "Review input constraints"
                ],
                retry_possible=False,
                user_action_required=True
            ),
            
            ErrorPattern(
                name="memory_error",
                patterns=[
                    r"memory.*error",
                    r"out of memory",
                    r"memory.*exhausted",
                    r"allocation.*failed"
                ],
                category=ErrorCategory.RESOURCE_EXHAUSTION,
                severity=ErrorSeverity.HIGH,
                error_type=ErrorType.MEMORY_ERROR,
                recovery_strategies=["free_memory", "reduce_load", "restart_service"],
                user_message="System resources are exhausted. Please try again later.",
                technical_details="Memory allocation failed",
                resolution_steps=[
                    "Close other applications",
                    "Reduce request complexity",
                    "Try again when system load is lower"
                ],
                retry_possible=True
            ),
            
            ErrorPattern(
                name="disk_space_error",
                patterns=[
                    r"disk.*space",
                    r"no space left",
                    r"storage.*full",
                    r"insufficient.*space"
                ],
                category=ErrorCategory.RESOURCE_EXHAUSTION,
                severity=ErrorSeverity.CRITICAL,
                error_type=ErrorType.DISK_SPACE_ERROR,
                recovery_strategies=["free_disk_space", "cleanup_temp_files"],
                user_message="Insufficient disk space. Please free up space and try again.",
                technical_details="Disk space is insufficient for operation",
                resolution_steps=[
                    "Free up disk space",
                    "Remove unnecessary files",
                    "Clear temporary files and cache"
                ],
                retry_possible=True,
                user_action_required=True
            )
        ]
    
    def _initialize_severity_adjusters(self) -> Dict[str, Any]:
        """Initialize severity adjustment functions based on context."""
        return {
            "production": lambda base_severity: self._upgrade_severity(base_severity),
            "critical_component": lambda base_severity: self._upgrade_severity(base_severity),
            "user_facing": lambda base_severity: self._upgrade_severity(base_severity),
            "background_task": lambda base_severity: self._downgrade_severity(base_severity),
            "retryable": lambda base_severity: self._downgrade_severity(base_severity),
        }
    
    def _initialize_context_analyzers(self) -> Dict[str, Any]:
        """Initialize context analysis functions."""
        return {
            "component": self._analyze_component_context,
            "user_role": self._analyze_user_role_context,
            "operation": self._analyze_operation_context,
            "time_of_day": self._analyze_time_context,
            "system_load": self._analyze_system_load_context,
        }
    
    def classify_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorClassification:
        """
        Classify an error with comprehensive analysis.
        
        Args:
            error: The exception to classify
            context: Additional context for classification
            
        Returns:
            ErrorClassification with detailed classification
        """
        error_message = str(error)
        error_type_name = type(error).__name__
        traceback_str = traceback.format_exc()
        
        # Find matching pattern
        pattern = self._find_matching_pattern(error_message, error_type_name, traceback_str)
        
        if pattern:
            # Use pattern-based classification
            classification = self._create_classification_from_pattern(pattern, error, context)
        else:
            # Use generic classification
            classification = self._create_generic_classification(error, context)
        
        # Adjust severity based on context
        classification = self._adjust_severity_by_context(classification, context)
        
        # Add context analysis
        classification = self._analyze_error_context(classification, error, context)
        
        # Add metadata
        classification.metadata.update({
            "error_type_name": error_type_name,
            "traceback": traceback_str,
            "classification_timestamp": datetime.utcnow().isoformat(),
        })
        
        return classification
    
    def _find_matching_pattern(
        self,
        error_message: str,
        error_type_name: str,
        traceback_str: str
    ) -> Optional[ErrorPattern]:
        """Find the best matching error pattern."""
        combined_text = f"{error_message} {error_type_name} {traceback_str}".lower()
        
        best_match = None
        best_score = 0
        
        for pattern in self.patterns:
            score = 0
            for pattern_regex in pattern.patterns:
                if re.search(pattern_regex, combined_text, re.IGNORECASE):
                    score += 1
            
            # Bonus for exact error type name match
            if pattern.name.lower() in error_type_name.lower():
                score += 2
            
            if score > best_score:
                best_score = score
                best_match = pattern
        
        return best_match if best_score > 0 else None
    
    def _create_classification_from_pattern(
        self,
        pattern: ErrorPattern,
        error: Exception,
        context: Optional[Dict[str, Any]]
    ) -> ErrorClassification:
        """Create classification from matched pattern."""
        return ErrorClassification(
            category=pattern.category,
            severity=pattern.severity,
            error_type=pattern.error_type,
            pattern_name=pattern.name,
            user_message=pattern.user_message,
            technical_details=pattern.technical_details,
            resolution_steps=pattern.resolution_steps.copy(),
            recovery_strategies=pattern.recovery_strategies.copy(),
            retry_possible=pattern.retry_possible,
            user_action_required=pattern.user_action_required,
            context=context or {},
        )
    
    def _create_generic_classification(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]]
    ) -> ErrorClassification:
        """Create generic classification for unknown errors."""
        error_type_name = type(error).__name__
        error_message = str(error)
        
        # Try to infer category from error type
        category = self._infer_category_from_error_type(error_type_name)
        severity = self._infer_severity_from_error(error)
        error_type = self._infer_error_type(error_type_name, error_message)
        
        return ErrorClassification(
            category=category,
            severity=severity,
            error_type=error_type,
            user_message="An unexpected error occurred. Please try again.",
            technical_details=f"{error_type_name}: {error_message}",
            resolution_steps=[
                "Try the operation again",
                "Check your input data",
                "Contact support if the problem persists"
            ],
            recovery_strategies=["retry_with_backoff"],
            retry_possible=True,
            context=context or {},
        )
    
    def _infer_category_from_error_type(self, error_type_name: str) -> ErrorCategory:
        """Infer error category from error type name."""
        error_type_lower = error_type_name.lower()
        
        if any(keyword in error_type_lower for keyword in ["connection", "network", "http"]):
            return ErrorCategory.NETWORK
        elif any(keyword in error_type_lower for keyword in ["timeout", "time"]):
            return ErrorCategory.TIMEOUT
        elif any(keyword in error_type_lower for keyword in ["permission", "auth"]):
            return ErrorCategory.AUTHORIZATION
        elif any(keyword in error_type_lower for keyword in ["validation", "value"]):
            return ErrorCategory.VALIDATION
        elif any(keyword in error_type_lower for keyword in ["memory", "allocation"]):
            return ErrorCategory.RESOURCE_EXHAUSTION
        elif any(keyword in error_type_lower for keyword in ["database", "sql", "db"]):
            return ErrorCategory.DATABASE
        elif any(keyword in error_type_lower for keyword in ["file", "io", "disk"]):
            return ErrorCategory.FILE_SYSTEM
        else:
            return ErrorCategory.UNKNOWN
    
    def _infer_severity_from_error(self, error: Exception) -> ErrorSeverity:
        """Infer error severity from error characteristics."""
        error_type_name = type(error).__name__
        error_message = str(error).lower()
        
        # Critical errors
        if any(keyword in error_type_name.lower() for keyword in ["critical", "fatal", "system"]):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if any(keyword in error_message for keyword in ["failed", "error", "exception", "corrupt"]):
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if any(keyword in error_message for keyword in ["timeout", "unavailable", "refused"]):
            return ErrorSeverity.MEDIUM
        
        # Default to low severity
        return ErrorSeverity.LOW
    
    def _infer_error_type(self, error_type_name: str, error_message: str) -> ErrorType:
        """Infer specific error type from error information."""
        combined_text = f"{error_type_name} {error_message}".lower()
        
        if any(keyword in combined_text for keyword in ["connection", "connect"]):
            return ErrorType.CONNECTION_ERROR
        elif any(keyword in combined_text for keyword in ["timeout", "time"]):
            return ErrorType.TIMEOUT_ERROR
        elif any(keyword in combined_text for keyword in ["memory", "allocation"]):
            return ErrorType.MEMORY_ERROR
        elif any(keyword in combined_text for keyword in ["validation", "value"]):
            return ErrorType.VALIDATION_ERROR
        elif any(keyword in combined_text for keyword in ["permission", "access"]):
            return ErrorType.PERMISSION_ERROR
        else:
            return ErrorType.LOGIC_ERROR
    
    def _adjust_severity_by_context(
        self,
        classification: ErrorClassification,
        context: Optional[Dict[str, Any]]
    ) -> ErrorClassification:
        """Adjust severity based on context."""
        if not context:
            return classification
        
        for context_key, adjuster in self.severity_adjusters.items():
            if context_key in context and context[context_key]:
                try:
                    classification.severity = adjuster(classification.severity)
                except Exception:
                    # Keep original severity if adjustment fails
                    pass
        
        return classification
    
    def _analyze_error_context(
        self,
        classification: ErrorClassification,
        error: Exception,
        context: Optional[Dict[str, Any]]
    ) -> ErrorClassification:
        """Analyze error context and enrich classification."""
        if not context:
            return classification
        
        for context_key, analyzer in self.context_analyzers.items():
            if context_key in context:
                try:
                    additional_info = analyzer(context[context_key], error, classification)
                    classification.context.update(additional_info)
                except Exception:
                    # Continue if analysis fails
                    pass
        
        return classification
    
    def _analyze_component_context(
        self,
        component: str,
        error: Exception,
        classification: ErrorClassification
    ) -> Dict[str, Any]:
        """Analyze component-specific context."""
        return {
            "component": component,
            "component_criticality": self._assess_component_criticality(component),
        }
    
    def _analyze_user_role_context(
        self,
        user_role: str,
        error: Exception,
        classification: ErrorClassification
    ) -> Dict[str, Any]:
        """Analyze user role context."""
        return {
            "user_role": user_role,
            "requires_admin_action": user_role.lower() in ["admin", "developer"],
        }
    
    def _analyze_operation_context(
        self,
        operation: str,
        error: Exception,
        classification: ErrorClassification
    ) -> Dict[str, Any]:
        """Analyze operation context."""
        return {
            "operation": operation,
            "operation_type": self._classify_operation(operation),
        }
    
    def _analyze_time_context(
        self,
        timestamp: str,
        error: Exception,
        classification: ErrorClassification
    ) -> Dict[str, Any]:
        """Analyze time-based context."""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = dt.hour
            
            return {
                "time_of_day": hour,
                "business_hours": 9 <= hour <= 17,
                "peak_usage": hour in [10, 11, 14, 15, 16],
            }
        except Exception:
            return {"time_analysis_failed": True}
    
    def _analyze_system_load_context(
        self,
        system_load: Dict[str, Any],
        error: Exception,
        classification: ErrorClassification
    ) -> Dict[str, Any]:
        """Analyze system load context."""
        return {
            "system_load": system_load,
            "high_load": system_load.get("cpu_percent", 0) > 80,
            "memory_pressure": system_load.get("memory_percent", 0) > 85,
        }
    
    def _assess_component_criticality(self, component: str) -> str:
        """Assess component criticality."""
        critical_components = [
            "authentication", "authorization", "database", "ai_processing",
            "model_orchestrator", "core_api"
        ]
        
        if component.lower() in critical_components:
            return "critical"
        elif component.lower().endswith("_api"):
            return "high"
        else:
            return "medium"
    
    def _classify_operation(self, operation: str) -> str:
        """Classify operation type."""
        operation_lower = operation.lower()
        
        if any(keyword in operation_lower for keyword in ["create", "add", "insert"]):
            return "write"
        elif any(keyword in operation_lower for keyword in ["read", "get", "fetch", "list"]):
            return "read"
        elif any(keyword in operation_lower for keyword in ["update", "modify", "edit"]):
            return "update"
        elif any(keyword in operation_lower for keyword in ["delete", "remove"]):
            return "delete"
        else:
            return "other"
    
    def _upgrade_severity(self, severity: ErrorSeverity) -> ErrorSeverity:
        """Upgrade severity by one level."""
        severity_order = [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]
        current_index = severity_order.index(severity)
        new_index = min(current_index + 1, len(severity_order) - 1)
        return severity_order[new_index]
    
    def _downgrade_severity(self, severity: ErrorSeverity) -> ErrorSeverity:
        """Downgrade severity by one level."""
        severity_order = [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]
        current_index = severity_order.index(severity)
        new_index = max(current_index - 1, 0)
        return severity_order[new_index]
    
    def add_pattern(self, pattern: ErrorPattern) -> None:
        """Add a new error pattern."""
        self.patterns.append(pattern)
    
    def remove_pattern(self, pattern_name: str) -> bool:
        """Remove an error pattern by name."""
        for i, pattern in enumerate(self.patterns):
            if pattern.name == pattern_name:
                del self.patterns[i]
                return True
        return False
    
    def get_patterns_by_category(self, category: ErrorCategory) -> List[ErrorPattern]:
        """Get all patterns for a specific category."""
        return [p for p in self.patterns if p.category == category]
    
    def get_patterns_by_severity(self, severity: ErrorSeverity) -> List[ErrorPattern]:
        """Get all patterns for a specific severity."""
        return [p for p in self.patterns if p.severity == severity]