"""
Context Validation Service for CoPilot Architecture.

This service provides comprehensive validation for context data, ensuring data integrity,
security compliance, and proper formatting across all context operations.
"""

import logging
import re
import uuid
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field

try:
    from pydantic import BaseModel, Field, validator
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field, validator

from .context_manager import (
    ContextData, ContextError, ContextErrorType,
    ContextRequest, ContextUpdateRequest, ContextFile, MemoryAccessLevel
)

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Validation severity enumeration."""
    INFO = "info"  # Informational validation issue
    WARNING = "warning"  # Warning that might cause issues
    ERROR = "error"  # Error that will cause operation failure
    CRITICAL = "critical"  # Critical error that must be fixed


class ValidationRuleType(str, Enum):
    """Validation rule type enumeration."""
    REQUIRED = "required"  # Required field validation
    FORMAT = "format"  # Format validation
    TYPE = "type"  # Type validation
    RANGE = "range"  # Range validation
    LENGTH = "length"  # Length validation
    PATTERN = "pattern"  # Pattern validation
    CUSTOM = "custom"  # Custom validation rule
    SECURITY = "security"  # Security validation
    BUSINESS = "business"  # Business rule validation


@dataclass
class ValidationResult:
    """Validation result data model."""
    rule_id: str
    rule_name: str
    rule_type: ValidationRuleType
    severity: ValidationSeverity
    message: str
    field_path: str
    value: Any = None
    expected: Any = None
    is_valid: bool = True
    context: Dict[str, Any] = field(default_factory=dict)


class ValidationReport(BaseModel):
    """Validation report model."""
    
    is_valid: bool = Field(..., description="Overall validation status")
    results: List[ValidationResult] = Field(default_factory=list, description="Validation results")
    error_count: int = Field(0, description="Number of error-level validation issues")
    warning_count: int = Field(0, description="Number of warning-level validation issues")
    info_count: int = Field(0, description="Number of info-level validation issues")
    critical_count: int = Field(0, description="Number of critical-level validation issues")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")
    
    @validator('error_count')
    def validate_error_count(cls, v, values):
        results = values.get('results', [])
        return sum(1 for r in results if r.severity == ValidationSeverity.ERROR and not r.is_valid)
    
    @validator('warning_count')
    def validate_warning_count(cls, v, values):
        results = values.get('results', [])
        return sum(1 for r in results if r.severity == ValidationSeverity.WARNING and not r.is_valid)
    
    @validator('info_count')
    def validate_info_count(cls, v, values):
        results = values.get('results', [])
        return sum(1 for r in results if r.severity == ValidationSeverity.INFO and not r.is_valid)
    
    @validator('critical_count')
    def validate_critical_count(cls, v, values):
        results = values.get('results', [])
        return sum(1 for r in results if r.severity == ValidationSeverity.CRITICAL and not r.is_valid)
    
    @validator('is_valid')
    def validate_is_valid(cls, v, values):
        critical_count = values.get('critical_count', 0)
        error_count = values.get('error_count', 0)
        return critical_count == 0 and error_count == 0


class ValidationRule(BaseModel):
    """Validation rule model."""
    
    rule_id: str = Field(..., description="Rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    rule_type: ValidationRuleType = Field(..., description="Rule type")
    severity: ValidationSeverity = Field(..., description="Validation severity")
    field_path: str = Field(..., description="Path to field to validate")
    enabled: bool = Field(True, description="Whether the rule is enabled")
    
    # Rule-specific parameters
    required: Optional[bool] = Field(None, description="Whether field is required")
    data_type: Optional[str] = Field(None, description="Expected data type")
    min_length: Optional[int] = Field(None, description="Minimum length")
    max_length: Optional[int] = Field(None, description="Maximum length")
    min_value: Optional[Union[int, float]] = Field(None, description="Minimum value")
    max_value: Optional[Union[int, float]] = Field(None, description="Maximum value")
    pattern: Optional[str] = Field(None, description="Regex pattern")
    allowed_values: Optional[List[Any]] = Field(None, description="List of allowed values")
    forbidden_values: Optional[List[Any]] = Field(None, description="List of forbidden values")
    custom_validator: Optional[str] = Field(None, description="Custom validator function name")
    
    def validate(self, data: Any, context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate data against this rule.
        
        Args:
            data: Data to validate
            context: Additional validation context
            
        Returns:
            Validation result
        """
        context = context or {}
        
        # Get the field value from the data
        field_value = self._get_field_value(data, self.field_path)
        
        # Check if field is required
        if self.required and field_value is None:
            return ValidationResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                rule_type=self.rule_type,
                severity=self.severity,
                message=f"Field '{self.field_path}' is required",
                field_path=self.field_path,
                value=field_value,
                expected="non-null value",
                is_valid=False,
                context=context
            )
        
        # Skip further validation if field is not required and is None
        if field_value is None:
            return ValidationResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                rule_type=self.rule_type,
                severity=self.severity,
                message=f"Field '{self.field_path}' is not required and is null",
                field_path=self.field_path,
                value=field_value,
                is_valid=True,
                context=context
            )
        
        # Validate data type
        if self.data_type:
            if not self._validate_type(field_value, self.data_type):
                return ValidationResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    rule_type=self.rule_type,
                    severity=self.severity,
                    message=f"Field '{self.field_path}' must be of type {self.data_type}",
                    field_path=self.field_path,
                    value=field_value,
                    expected=self.data_type,
                    is_valid=False,
                    context=context
                )
        
        # Validate length
        if self.min_length is not None or self.max_length is not None:
            if not self._validate_length(field_value, self.min_length, self.max_length):
                return ValidationResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    rule_type=ValidationRuleType.LENGTH,
                    severity=self.severity,
                    message=f"Field '{self.field_path}' length must be between {self.min_length} and {self.max_length}",
                    field_path=self.field_path,
                    value=field_value,
                    expected=f"length between {self.min_length} and {self.max_length}",
                    is_valid=False,
                    context=context
                )
        
        # Validate range
        if self.min_value is not None or self.max_value is not None:
            if not self._validate_range(field_value, self.min_value, self.max_value):
                return ValidationResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    rule_type=ValidationRuleType.RANGE,
                    severity=self.severity,
                    message=f"Field '{self.field_path}' must be between {self.min_value} and {self.max_value}",
                    field_path=self.field_path,
                    value=field_value,
                    expected=f"value between {self.min_value} and {self.max_value}",
                    is_valid=False,
                    context=context
                )
        
        # Validate pattern
        if self.pattern:
            if not self._validate_pattern(field_value, self.pattern):
                return ValidationResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    rule_type=ValidationRuleType.PATTERN,
                    severity=self.severity,
                    message=f"Field '{self.field_path}' must match pattern {self.pattern}",
                    field_path=self.field_path,
                    value=field_value,
                    expected=f"pattern {self.pattern}",
                    is_valid=False,
                    context=context
                )
        
        # Validate allowed values
        if self.allowed_values:
            if field_value not in self.allowed_values:
                return ValidationResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    rule_type=ValidationRuleType.CUSTOM,
                    severity=self.severity,
                    message=f"Field '{self.field_path}' must be one of {self.allowed_values}",
                    field_path=self.field_path,
                    value=field_value,
                    expected=f"one of {self.allowed_values}",
                    is_valid=False,
                    context=context
                )
        
        # Validate forbidden values
        if self.forbidden_values:
            if field_value in self.forbidden_values:
                return ValidationResult(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    rule_type=ValidationRuleType.SECURITY,
                    severity=self.severity,
                    message=f"Field '{self.field_path}' must not be one of {self.forbidden_values}",
                    field_path=self.field_path,
                    value=field_value,
                    expected=f"not one of {self.forbidden_values}",
                    is_valid=False,
                    context=context
                )
        
        # If all validations passed
        return ValidationResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            rule_type=self.rule_type,
            severity=self.severity,
            message=f"Field '{self.field_path}' is valid",
            field_path=self.field_path,
            value=field_value,
            is_valid=True,
            context=context
        )
    
    def _get_field_value(self, data: Any, field_path: str) -> Any:
        """Get field value from data using dot notation."""
        if not field_path:
            return data
        
        parts = field_path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate data type."""
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "datetime": datetime,
            "uuid": (str, uuid.UUID)  # UUID can be string or UUID object
        }
        
        expected_type_class = type_map.get(expected_type)
        if not expected_type_class:
            return True  # Unknown type, skip validation
        
        if isinstance(expected_type_class, tuple):
            return isinstance(value, expected_type_class)
        
        return isinstance(value, expected_type_class)
    
    def _validate_length(self, value: Any, min_length: Optional[int], max_length: Optional[int]) -> bool:
        """Validate length."""
        if not hasattr(value, '__len__'):
            return True  # No length attribute, skip validation
        
        length = len(value)
        
        if min_length is not None and length < min_length:
            return False
        
        if max_length is not None and length > max_length:
            return False
        
        return True
    
    def _validate_range(self, value: Any, min_value: Optional[Union[int, float]], max_value: Optional[Union[int, float]]) -> bool:
        """Validate range."""
        if not isinstance(value, (int, float)):
            return True  # Not numeric, skip validation
        
        if min_value is not None and value < min_value:
            return False
        
        if max_value is not None and value > max_value:
            return False
        
        return True
    
    def _validate_pattern(self, value: Any, pattern: str) -> bool:
        """Validate pattern."""
        if not isinstance(value, str):
            return True  # Not string, skip validation
        
        return bool(re.match(pattern, value))


class ContextValidationService:
    """Context Validation Service for CoPilot Architecture."""
    
    def __init__(self):
        """Initialize Context Validation Service."""
        # Default validation rules
        self._rules: Dict[str, ValidationRule] = {}
        
        # Initialize default rules
        self._initialize_default_rules()
        
        # Metrics
        self._metrics = {
            "validations_performed": 0,
            "validations_passed": 0,
            "validations_failed": 0,
            "rules_executed": 0,
            "errors": 0
        }
    
    def _initialize_default_rules(self) -> None:
        """Initialize default validation rules."""
        # Context ID validation
        self.add_rule(ValidationRule(
            rule_id="context_id_required",
            name="Context ID Required",
            description="Context ID must be provided",
            rule_type=ValidationRuleType.REQUIRED,
            severity=ValidationSeverity.ERROR,
            field_path="context_id",
            required=True,
            data_type="uuid"
        ))
        
        # Session ID validation
        self.add_rule(ValidationRule(
            rule_id="session_id_required",
            name="Session ID Required",
            description="Session ID must be provided",
            rule_type=ValidationRuleType.REQUIRED,
            severity=ValidationSeverity.ERROR,
            field_path="session_id",
            required=True,
            data_type="str"
        ))
        
        # User ID validation
        self.add_rule(ValidationRule(
            rule_id="user_id_required",
            name="User ID Required",
            description="User ID must be provided",
            rule_type=ValidationRuleType.REQUIRED,
            severity=ValidationSeverity.ERROR,
            field_path="user_id",
            required=True,
            data_type="str"
        ))
        
        # Tenant ID validation
        self.add_rule(ValidationRule(
            rule_id="tenant_id_required",
            name="Tenant ID Required",
            description="Tenant ID must be provided",
            rule_type=ValidationRuleType.REQUIRED,
            severity=ValidationSeverity.ERROR,
            field_path="tenant_id",
            required=True,
            data_type="str"
        ))
        
        # Context type validation
        self.add_rule(ValidationRule(
            rule_id="context_type_required",
            name="Context Type Required",
            description="Context type must be provided",
            rule_type=ValidationRuleType.REQUIRED,
            severity=ValidationSeverity.ERROR,
            field_path="context_type",
            required=True,
            allowed_values=["conversation", "document", "workflow", "agent", "system"]
        ))
        
        # Title validation
        self.add_rule(ValidationRule(
            rule_id="title_length",
            name="Title Length",
            description="Title must be between 1 and 255 characters",
            rule_type=ValidationRuleType.LENGTH,
            severity=ValidationSeverity.WARNING,
            field_path="title",
            min_length=1,
            max_length=255
        ))
        
        # Content validation
        self.add_rule(ValidationRule(
            rule_id="content_type",
            name="Content Type",
            description="Content must be a dictionary",
            rule_type=ValidationRuleType.TYPE,
            severity=ValidationSeverity.ERROR,
            field_path="content",
            data_type="dict"
        ))
        
        # Access level validation
        self.add_rule(ValidationRule(
            rule_id="access_level_required",
            name="Access Level Required",
            description="Access level must be provided",
            rule_type=ValidationRuleType.REQUIRED,
            severity=ValidationSeverity.ERROR,
            field_path="access_level",
            required=True,
            allowed_values=[level.value for level in MemoryAccessLevel]
        ))
        
        # Tags validation
        self.add_rule(ValidationRule(
            rule_id="tags_type",
            name="Tags Type",
            description="Tags must be a list of strings",
            rule_type=ValidationRuleType.TYPE,
            severity=ValidationSeverity.WARNING,
            field_path="tags",
            data_type="list"
        ))
        
        # Created at validation
        self.add_rule(ValidationRule(
            rule_id="created_at_type",
            name="Created At Type",
            description="Created at must be a datetime",
            rule_type=ValidationRuleType.TYPE,
            severity=ValidationSeverity.WARNING,
            field_path="created_at",
            data_type="datetime"
        ))
        
        # Updated at validation
        self.add_rule(ValidationRule(
            rule_id="updated_at_type",
            name="Updated At Type",
            description="Updated at must be a datetime",
            rule_type=ValidationRuleType.TYPE,
            severity=ValidationSeverity.WARNING,
            field_path="updated_at",
            data_type="datetime"
        ))
        
        # Expires at validation
        self.add_rule(ValidationRule(
            rule_id="expires_at_future",
            name="Expires At Future",
            description="Expires at must be in the future if provided",
            rule_type=ValidationRuleType.BUSINESS,
            severity=ValidationSeverity.WARNING,
            field_path="expires_at",
            custom_validator="validate_expires_at_future"
        ))
        
        # Files validation
        self.add_rule(ValidationRule(
            rule_id="files_type",
            name="Files Type",
            description="Files must be a list of ContextFile objects",
            rule_type=ValidationRuleType.TYPE,
            severity=ValidationSeverity.WARNING,
            field_path="files",
            data_type="list"
        ))
        
        # Agent ID validation
        self.add_rule(ValidationRule(
            rule_id="agent_id_type",
            name="Agent ID Type",
            description="Agent ID must be a string",
            rule_type=ValidationRuleType.TYPE,
            severity=ValidationSeverity.WARNING,
            field_path="agent_id",
            data_type="str"
        ))
    
    async def validate_context(
        self,
        context: Union[ContextData, Dict[str, Any]],
        correlation_id: Optional[str] = None
    ) -> ValidationReport:
        """
        Validate context data.
        
        Args:
            context: Context data to validate
            correlation_id: Correlation ID for tracking
            
        Returns:
            Validation report
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            # Convert to dict if needed
            if isinstance(context, ContextData):
                context_dict = context.__dict__
            else:
                context_dict = context
            
            # Create validation report
            report = ValidationReport(
                is_valid=True,
                results=[],
                correlation_id=correlation_id
            )
            
            # Apply all enabled rules
            for rule in self._rules.values():
                if not rule.enabled:
                    continue
                
                try:
                    result = rule.validate(context_dict, {"correlation_id": correlation_id})
                    report.results.append(result)
                    
                    # Update metrics
                    self._metrics["rules_executed"] += 1
                    
                    if not result.is_valid:
                        self._metrics["validations_failed"] += 1
                    else:
                        self._metrics["validations_passed"] += 1
                        
                except Exception as e:
                    logger.error(f"Error executing validation rule {rule.rule_id}: {e}")
                    
                    # Add error result
                    error_result = ValidationResult(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        rule_type=ValidationRuleType.CUSTOM,
                        severity=ValidationSeverity.ERROR,
                        message=f"Validation rule execution error: {str(e)}",
                        field_path=rule.field_path,
                        is_valid=False,
                        context={"correlation_id": correlation_id, "exception": str(e)}
                    )
                    report.results.append(error_result)
                    self._metrics["errors"] += 1
                    self._metrics["validations_failed"] += 1
            
            # Update overall metrics
            self._metrics["validations_performed"] += 1
            
            logger.debug(
                f"Context validation completed with {len(report.results)} rules",
                extra={"correlation_id": correlation_id}
            )
            
            return report
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Context validation failed: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            # Return error report
            return ValidationReport(
                is_valid=False,
                results=[ValidationResult(
                    rule_id="validation_error",
                    rule_name="Validation Error",
                    rule_type=ValidationRuleType.CUSTOM,
                    severity=ValidationSeverity.CRITICAL,
                    message=error_msg,
                    field_path="",
                    is_valid=False,
                    context={"correlation_id": correlation_id, "exception": str(e)}
                )],
                correlation_id=correlation_id
            )
    
    async def validate_context_request(
        self,
        request: ContextRequest,
        correlation_id: Optional[str] = None
    ) -> ValidationReport:
        """
        Validate context request.
        
        Args:
            request: Context request to validate
            correlation_id: Correlation ID for tracking
            
        Returns:
            Validation report
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            # Convert to dict
            request_dict = request.__dict__
            
            # Create validation report
            report = ValidationReport(
                is_valid=True,
                results=[],
                correlation_id=correlation_id
            )
            
            # Apply all enabled rules
            for rule in self._rules.values():
                if not rule.enabled:
                    continue
                
                try:
                    result = rule.validate(request_dict, {"correlation_id": correlation_id})
                    report.results.append(result)
                    
                    # Update metrics
                    self._metrics["rules_executed"] += 1
                    
                    if not result.is_valid:
                        self._metrics["validations_failed"] += 1
                    else:
                        self._metrics["validations_passed"] += 1
                        
                except Exception as e:
                    logger.error(f"Error executing validation rule {rule.rule_id}: {e}")
                    
                    # Add error result
                    error_result = ValidationResult(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        rule_type=ValidationRuleType.CUSTOM,
                        severity=ValidationSeverity.ERROR,
                        message=f"Validation rule execution error: {str(e)}",
                        field_path=rule.field_path,
                        is_valid=False,
                        context={"correlation_id": correlation_id, "exception": str(e)}
                    )
                    report.results.append(error_result)
                    self._metrics["errors"] += 1
                    self._metrics["validations_failed"] += 1
            
            # Update overall metrics
            self._metrics["validations_performed"] += 1
            
            logger.debug(
                f"Context request validation completed with {len(report.results)} rules",
                extra={"correlation_id": correlation_id}
            )
            
            return report
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Context request validation failed: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            # Return error report
            return ValidationReport(
                is_valid=False,
                results=[ValidationResult(
                    rule_id="validation_error",
                    rule_name="Validation Error",
                    rule_type=ValidationRuleType.CUSTOM,
                    severity=ValidationSeverity.CRITICAL,
                    message=error_msg,
                    field_path="",
                    is_valid=False,
                    context={"correlation_id": correlation_id, "exception": str(e)}
                )],
                correlation_id=correlation_id
            )
    
    async def validate_context_update(
        self,
        request: ContextUpdateRequest,
        correlation_id: Optional[str] = None
    ) -> ValidationReport:
        """
        Validate context update request.
        
        Args:
            request: Context update request to validate
            correlation_id: Correlation ID for tracking
            
        Returns:
            Validation report
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        
        try:
            # Convert to dict
            request_dict = request.__dict__
            
            # Create validation report
            report = ValidationReport(
                is_valid=True,
                results=[],
                correlation_id=correlation_id
            )
            
            # Apply all enabled rules
            for rule in self._rules.values():
                if not rule.enabled:
                    continue
                
                try:
                    result = rule.validate(request_dict, {"correlation_id": correlation_id})
                    report.results.append(result)
                    
                    # Update metrics
                    self._metrics["rules_executed"] += 1
                    
                    if not result.is_valid:
                        self._metrics["validations_failed"] += 1
                    else:
                        self._metrics["validations_passed"] += 1
                        
                except Exception as e:
                    logger.error(f"Error executing validation rule {rule.rule_id}: {e}")
                    
                    # Add error result
                    error_result = ValidationResult(
                        rule_id=rule.rule_id,
                        rule_name=rule.name,
                        rule_type=ValidationRuleType.CUSTOM,
                        severity=ValidationSeverity.ERROR,
                        message=f"Validation rule execution error: {str(e)}",
                        field_path=rule.field_path,
                        is_valid=False,
                        context={"correlation_id": correlation_id, "exception": str(e)}
                    )
                    report.results.append(error_result)
                    self._metrics["errors"] += 1
                    self._metrics["validations_failed"] += 1
            
            # Update overall metrics
            self._metrics["validations_performed"] += 1
            
            logger.debug(
                f"Context update validation completed with {len(report.results)} rules",
                extra={"correlation_id": correlation_id}
            )
            
            return report
            
        except Exception as e:
            self._metrics["errors"] += 1
            error_msg = f"Context update validation failed: {str(e)}"
            logger.error(
                error_msg,
                extra={"correlation_id": correlation_id}
            )
            
            # Return error report
            return ValidationReport(
                is_valid=False,
                results=[ValidationResult(
                    rule_id="validation_error",
                    rule_name="Validation Error",
                    rule_type=ValidationRuleType.CUSTOM,
                    severity=ValidationSeverity.CRITICAL,
                    message=error_msg,
                    field_path="",
                    is_valid=False,
                    context={"correlation_id": correlation_id, "exception": str(e)}
                )],
                correlation_id=correlation_id
            )
    
    def add_rule(self, rule: ValidationRule) -> None:
        """
        Add a validation rule.
        
        Args:
            rule: Validation rule to add
        """
        self._rules[rule.rule_id] = rule
        logger.info(f"Added validation rule {rule.rule_id}: {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a validation rule.
        
        Args:
            rule_id: ID of rule to remove
            
        Returns:
            True if rule was removed, False if not found
        """
        if rule_id in self._rules:
            del self._rules[rule_id]
            logger.info(f"Removed validation rule {rule_id}")
            return True
        
        logger.warning(f"Validation rule {rule_id} not found")
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """
        Enable a validation rule.
        
        Args:
            rule_id: ID of rule to enable
            
        Returns:
            True if rule was enabled, False if not found
        """
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True
            logger.info(f"Enabled validation rule {rule_id}")
            return True
        
        logger.warning(f"Validation rule {rule_id} not found")
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """
        Disable a validation rule.
        
        Args:
            rule_id: ID of rule to disable
            
        Returns:
            True if rule was disabled, False if not found
        """
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False
            logger.info(f"Disabled validation rule {rule_id}")
            return True
        
        logger.warning(f"Validation rule {rule_id} not found")
        return False
    
    def get_rule(self, rule_id: str) -> Optional[ValidationRule]:
        """
        Get a validation rule.
        
        Args:
            rule_id: ID of rule to get
            
        Returns:
            Validation rule if found, None otherwise
        """
        return self._rules.get(rule_id)
    
    def list_rules(self, enabled_only: bool = False) -> List[ValidationRule]:
        """
        List validation rules.
        
        Args:
            enabled_only: Whether to return only enabled rules
            
        Returns:
            List of validation rules
        """
        rules = list(self._rules.values())
        
        if enabled_only:
            rules = [rule for rule in rules if rule.enabled]
        
        return rules
    
    async def validate_expires_at_future(self, value: Any, context: Dict[str, Any]) -> bool:
        """
        Validate that expires_at is in the future.
        
        Args:
            value: Value to validate
            context: Validation context
            
        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return True  # Not required
        
        if not isinstance(value, datetime):
            return False  # Must be datetime
        
        return value > datetime.utcnow()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get service metrics.
        
        Returns:
            Service metrics
        """
        return {
            **self._metrics,
            "total_rules": len(self._rules),
            "enabled_rules": len([r for r in self._rules.values() if r.enabled]),
            "disabled_rules": len([r for r in self._rules.values() if not r.enabled])
        }
    
    async def reset_metrics(self) -> None:
        """Reset service metrics."""
        self._metrics = {
            "validations_performed": 0,
            "validations_passed": 0,
            "validations_failed": 0,
            "rules_executed": 0,
            "errors": 0
        }
        
        logger.info("Reset validation service metrics")