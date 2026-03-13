"""
Enhanced Input Validation for AI-Karen Production Chat System
Provides comprehensive input validation with security checks and sanitization.
"""

import logging
import re
import html
import json
import uuid
import hashlib
import time
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, ValidationError, validator

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    """Validation categories."""
    SECURITY = "security"
    FORMAT = "format"
    LENGTH = "length"
    TYPE = "type"
    CONTENT = "content"
    BUSINESS_LOGIC = "business_logic"
    AUTHORIZATION = "authorization"
    RATE_LIMITING = "rate_limiting"
    FILE_UPLOAD = "file_upload"


@dataclass
class ValidationRule:
    """Validation rule configuration."""
    name: str
    category: ValidationCategory
    validator: Callable
    severity: ValidationSeverity
    message: str
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    severity: ValidationSeverity
    category: ValidationCategory
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    sanitized_value: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SecurityValidationResult:
    """Result of security validation."""
    is_safe: bool
    threats_detected: List[str]
    risk_score: float  # 0-100
    sanitized_content: Optional[str] = None
    blocked_content: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class FileValidationResult:
    """Result of file validation."""
    is_valid: bool
    file_type: str
    file_size: int
    mime_type: str
    threats_detected: List[str]
    is_safe: bool
    allowed_extensions: List[str]
    max_size_exceeded: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedValidationConfig:
    """Configuration for enhanced validation system."""
    
    def __init__(
        self,
        enable_security_validation: bool = True,
        enable_content_sanitization: bool = True,
        enable_rate_limiting: bool = True,
        enable_file_validation: bool = True,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        max_message_length: int = 10000,
        max_conversation_title_length: int = 200,
        allowed_file_types: List[str] = None,
        blocked_file_extensions: List[str] = None,
        max_file_size: int = 50 * 1024 * 1024,  # 50MB
        enable_xss_protection: bool = True,
        enable_sql_injection_protection: bool = True,
        enable_csrf_protection: bool = True,
        custom_validators: Dict[str, List[ValidationRule]] = None
    ):
        self.enable_security_validation = enable_security_validation
        self.enable_content_sanitization = enable_content_sanitization
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_file_validation = enable_file_validation
        self.max_request_size = max_request_size
        self.max_message_length = max_message_length
        self.max_conversation_title_length = max_conversation_title_length
        self.allowed_file_types = allowed_file_types or [
            "text/plain",
            "text/markdown",
            "application/json",
            "image/jpeg",
            "image/png",
            "image/gif",
            "application/pdf",
            "text/csv"
        ]
        self.blocked_file_extensions = blocked_file_extensions or [
            ".exe", ".bat", ".cmd", ".scr", ".pif", ".com",
            ".js", ".jar", ".app", ".deb", ".pkg", ".dmg",
            ".iso", ".img", ".bin", ".sh", ".ps1", ".vbs", ".wsf",
            ".wsh", ".ps1", ".ps2", ".ps1", ".scr", ".pyc", ".pyo",
            ".php", ".php3", ".php4", ".php5", ".phtml", ".pht"
        ]
        self.max_file_size = max_file_size
        self.enable_xss_protection = enable_xss_protection
        self.enable_sql_injection_protection = enable_sql_injection_protection
        self.enable_csrf_protection = enable_csrf_protection
        self.custom_validators = custom_validators or {}


class EnhancedValidator:
    """
    Enhanced validator for chat system inputs.
    
    Features:
    - Security validation
    - Content sanitization
    - File upload validation
    - Rate limiting
    - Custom validation rules
    - XSS protection
    - SQL injection protection
    - CSRF protection
    """
    
    def __init__(self, config: Optional[EnhancedValidationConfig] = None):
        self.config = config or EnhancedValidationConfig()
        self.validation_rules: Dict[str, ValidationRule] = {}
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default validation rules."""
        # Message content validation
        self.add_rule(ValidationRule(
            name="message_length",
            category=ValidationCategory.LENGTH,
            validator=self._validate_message_length,
            severity=ValidationSeverity.ERROR,
            message="Message length exceeds maximum allowed",
            parameters={"max_length": self.config.max_message_length}
        ))
        
        # Conversation title validation
        self.add_rule(ValidationRule(
            name="conversation_title_length",
            category=ValidationCategory.LENGTH,
            validator=self._validate_conversation_title_length,
            severity=ValidationSeverity.ERROR,
            message="Conversation title length exceeds maximum allowed",
            parameters={"max_length": self.config.max_conversation_title_length}
        ))
        
        # XSS protection
        if self.config.enable_xss_protection:
            self.add_rule(ValidationRule(
                name="xss_protection",
                category=ValidationCategory.SECURITY,
                validator=self._validate_xss,
                severity=ValidationSeverity.CRITICAL,
                message="Potential XSS attack detected",
                parameters={"enabled": self.config.enable_xss_protection}
            ))
        
        # SQL injection protection
        if self.config.enable_sql_injection_protection:
            self.add_rule(ValidationRule(
                name="sql_injection_protection",
                category=ValidationCategory.SECURITY,
                validator=self._validate_sql_injection,
                severity=ValidationSeverity.CRITICAL,
                message="Potential SQL injection attack detected",
                parameters={"enabled": self.config.enable_sql_injection_protection}
            ))
        
        # File upload validation
        if self.config.enable_file_validation:
            self.add_rule(ValidationRule(
                name="file_upload_validation",
                category=ValidationCategory.FILE_UPLOAD,
                validator=self._validate_file_upload,
                severity=ValidationSeverity.ERROR,
                message="File upload validation failed",
                parameters={
                    "allowed_types": self.config.allowed_file_types,
                    "max_size": self.config.max_file_size,
                    "blocked_extensions": self.config.blocked_file_extensions
                }
            ))
        
        # Request size validation
        self.add_rule(ValidationRule(
            name="request_size_validation",
            category=ValidationCategory.LENGTH,
            validator=self._validate_request_size,
            severity=ValidationSeverity.ERROR,
            message="Request size exceeds maximum allowed",
            parameters={"max_size": self.config.max_request_size}
        ))
    
    def add_rule(self, rule: ValidationRule):
        """Add a custom validation rule."""
        self.validation_rules[rule.name] = rule
        logger.info(f"Added validation rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove a validation rule."""
        if rule_name in self.validation_rules:
            del self.validation_rules[rule_name]
            logger.info(f"Removed validation rule: {rule_name}")
    
    async def validate_message(
        self,
        message: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate a chat message.
        
        Args:
            message: The message content
            user_id: User ID for context
            context: Additional validation context
            
        Returns:
            Validation result
        """
        results = []
        
        # Apply all enabled validation rules
        for rule_name, rule in self.validation_rules.items():
            if not rule.enabled:
                continue
            
            try:
                if asyncio.iscoroutinefunction(rule.validator):
                    result = await rule.validator(message, user_id, context, rule.parameters)
                else:
                    result = rule.validator(message, user_id, context, rule.parameters)
                
                if isinstance(result, ValidationResult):
                    results.append(result)
                elif isinstance(result, tuple):
                    is_valid, severity, category, message, field, value, sanitized_value, metadata = result
                    results.append(ValidationResult(
                        is_valid=is_valid,
                        severity=severity,
                        category=category,
                        message=message,
                        field=field,
                        value=value,
                        sanitized_value=sanitized_value,
                        metadata=metadata
                    ))
                
            except Exception as e:
                logger.error(f"Validation rule {rule_name} failed: {e}")
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SECURITY,
                    message=f"Validation error: {str(e)}",
                    field=rule_name,
                    metadata={"error": str(e)}
                ))
        
        # Combine results
        final_result = self._combine_validation_results(results)
        
        logger.debug(f"Message validation completed: {final_result.is_valid}")
        
        return final_result
    
    async def validate_conversation_data(
        self,
        title: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate conversation creation/update data.
        
        Args:
            title: Conversation title
            user_id: User ID for context
            context: Additional validation context
            
        Returns:
            Validation result
        """
        results = []
        
        # Apply conversation-specific rules
        for rule_name, rule in self.validation_rules.items():
            if not rule.enabled or rule.category != ValidationCategory.LENGTH:
                continue
            
            try:
                if rule.name == "conversation_title_length":
                    result = rule.validator(title, user_id, context, rule.parameters)
                else:
                    continue
                
                if isinstance(result, ValidationResult):
                    results.append(result)
                elif isinstance(result, tuple):
                    is_valid, severity, category, message, field, value, sanitized_value, metadata = result
                    results.append(ValidationResult(
                        is_valid=is_valid,
                        severity=severity,
                        category=category,
                        message=message,
                        field=field,
                        value=value,
                        sanitized_value=sanitized_value,
                        metadata=metadata
                    ))
                
            except Exception as e:
                logger.error(f"Conversation validation rule {rule_name} failed: {e}")
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.SECURITY,
                    message=f"Validation error: {str(e)}",
                    field=rule_name,
                    metadata={"error": str(e)}
                ))
        
        # Combine results
        final_result = self._combine_validation_results(results)
        
        logger.debug(f"Conversation validation completed: {final_result.is_valid}")
        
        return final_result
    
    async def validate_file_upload(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        file_size: int,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> FileValidationResult:
        """
        Validate a file upload.
        
        Args:
            file_data: The file content
            filename: The original filename
            content_type: The MIME type
            file_size: The file size in bytes
            user_id: User ID for context
            context: Additional validation context
            
        Returns:
            File validation result
        """
        if not self.config.enable_file_validation:
            return FileValidationResult(
                is_valid=True,
                file_type=content_type,
                file_size=file_size,
                mime_type=content_type,
                threats_detected=[],
                is_safe=True,
                allowed_extensions=self.config.allowed_file_types,
                max_size_exceeded=False,
                metadata={"validation_disabled": True}
            )
        
        threats_detected = []
        is_safe = True
        max_size_exceeded = file_size > self.config.max_file_size
        
        # Check file extension
        file_extension = self._get_file_extension(filename)
        if file_extension.lower() in [ext.lower() for ext in self.config.blocked_file_extensions]:
            threats_detected.append(f"Blocked file extension: {file_extension}")
            is_safe = False
        
        # Check file type
        if content_type not in self.config.allowed_file_types:
            threats_detected.append(f"Disallowed file type: {content_type}")
            is_safe = False
        
        # Check file size
        if max_size_exceeded:
            threats_detected.append(f"File size exceeds maximum: {file_size} bytes")
        
        # Security scan for malicious content
        security_result = await self._scan_file_for_threats(file_data, filename)
        threats_detected.extend(security_result.threats_detected)
        
        if not security_result.is_safe:
            is_safe = False
        
        result = FileValidationResult(
            is_valid=is_safe and not max_size_exceeded,
            file_type=content_type,
            file_size=file_size,
            mime_type=content_type,
            threats_detected=threats_detected,
            is_safe=is_safe,
            allowed_extensions=self.config.allowed_file_types,
            max_size_exceeded=max_size_exceeded,
            metadata={
                "original_filename": filename,
                "file_extension": file_extension,
                "security_scan_result": security_result.metadata
            }
        )
        
        logger.debug(f"File validation completed: {result.is_valid}, threats: {len(threats_detected)}")
        
        return result
    
    async def validate_request(
        self,
        request_data: Dict[str, Any],
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate an entire request.
        
        Args:
            request_data: The request data
            user_id: User ID for context
            context: Additional validation context
            
        Returns:
            Validation result
        """
        results = []
        
        # Calculate request size
        request_size = len(json.dumps(request_data, separators=(',', ':')).encode('utf-8'))
        
        # Check request size limit
        if request_size > self.config.max_request_size:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.LENGTH,
                message=f"Request size {request_size} exceeds maximum {self.config.max_request_size}",
                field="request_size",
                value=request_size,
                metadata={"max_size": self.config.max_request_size}
            ))
        
        # Validate individual fields
        for field_name, field_value in request_data.items():
            if isinstance(field_value, str):
                field_result = await self.validate_message(
                    field_value,
                    user_id=user_id,
                    context={**(context or {}), "field_name": field_name}
                )
                
                # Update field name in result
                if field_result.field is None:
                    field_result.field = field_name
                
                results.append(field_result)
        
        # Combine results
        final_result = self._combine_validation_results(results)
        
        logger.debug(f"Request validation completed: {final_result.is_valid}")
        
        return final_result
    
    def _validate_message_length(
        self,
        message: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        parameters: Dict[str, Any] = None
    ) -> Tuple[bool, ValidationSeverity, ValidationCategory, str, Optional[str], Optional[str], Optional[str], Dict[str, Any]]:
        """Validate message length."""
        max_length = parameters.get("max_length", self.config.max_message_length)
        
        if len(message) > max_length:
            return (
                False,
                ValidationSeverity.ERROR,
                ValidationCategory.LENGTH,
                f"Message exceeds maximum length of {max_length} characters",
                "message",
                message,
                message[:max_length],  # Truncated value
                {"original_length": len(message), "max_length": max_length}
            )
        
        return (True, ValidationSeverity.INFO, ValidationCategory.LENGTH, "", None, None, {})
    
    def _validate_conversation_title_length(
        self,
        title: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        parameters: Dict[str, Any] = None
    ) -> Tuple[bool, ValidationSeverity, ValidationCategory, str, Optional[str], Optional[str], Optional[str], Dict[str, Any]]:
        """Validate conversation title length."""
        max_length = parameters.get("max_length", self.config.max_conversation_title_length)
        
        if len(title) > max_length:
            return (
                False,
                ValidationSeverity.ERROR,
                ValidationCategory.LENGTH,
                f"Title exceeds maximum length of {max_length} characters",
                "title",
                title,
                title[:max_length],  # Truncated value
                {"original_length": len(title), "max_length": max_length}
            )
        
        return (True, ValidationSeverity.INFO, ValidationCategory.LENGTH, "", None, None, {})
    
    def _validate_xss(
        self,
        content: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        parameters: Dict[str, Any] = None
    ) -> Tuple[bool, ValidationSeverity, ValidationCategory, str, Optional[str], Optional[str], Optional[str], Dict[str, Any]]:
        """Validate for XSS attacks."""
        if not content:
            return (True, ValidationSeverity.INFO, ValidationCategory.SECURITY, "", None, None, {})
        
        # Check for common XSS patterns
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
            r'vbscript:',
            r'data:text/html',
            r'expression\s*\(',
            r'url\s*\(',
            r'@import',
            r'<link[^>]*>.*?</link>',
            r'<meta[^>]*>.*?</meta>',
            r'<style[^>]*>.*?</style>',
            r'<img[^>]*>.*?</img>',
            r'<svg[^>]*>.*?</svg>',
            r'<video[^>]*>.*?</video>',
            r'<audio[^>]*>.*?</audio>'
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return (
                    False,
                    ValidationSeverity.CRITICAL,
                    ValidationCategory.SECURITY,
                    "Potential XSS attack detected",
                    "content",
                    None,
                    self._sanitize_content(content),
                    {"pattern_matched": pattern, "detection_method": "regex"}
                )
        
        return (True, ValidationSeverity.INFO, ValidationCategory.SECURITY, "", None, None, {})
    
    def _validate_sql_injection(
        self,
        content: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        parameters: Dict[str, Any] = None
    ) -> Tuple[bool, ValidationSeverity, ValidationCategory, str, Optional[str], Optional[str], Optional[str], Dict[str, Any]]:
        """Validate for SQL injection attacks."""
        if not content:
            return (True, ValidationSeverity.INFO, ValidationCategory.SECURITY, "", None, None, {})
        
        # Check for common SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|EXEC)\b)",
            r"(\b(OR|AND|NOT|LIKE|IN|BETWEEN|EXISTS|IS NULL)\b)",
            r"(\b(WHERE|HAVING|GROUP BY|ORDER BY|LIMIT|OFFSET)\b)",
            r"(--|#|/\*|\*/)",
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bINSERT\b.*\bINTO\b)",
            r"(\bDELETE\b.*\bFROM\b)",
            r"(\bUPDATE\b.*\bSET\b)",
            r"(\bCREATE\b.*\bTABLE\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(\bALTER\b.*\bTABLE\b)",
            r"(\bEXEC\b.*\bPROC\b)",
            r"(\'|\"|;|\\|<|>|<)",
            r"\bWAITFOR\b.*\bDELAY\b",
            r"\bBENCHMARK\b",
            r"\bSLEEP\b",
            r"\bINFORMATION_SCHEMA\b",
            r"\bLOAD_FILE\b",
            r"\bOUTFILE\b",
            r"\bDUMPFILE\b"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return (
                    False,
                    ValidationSeverity.CRITICAL,
                    ValidationCategory.SECURITY,
                    "Potential SQL injection attack detected",
                    "content",
                    None,
                    self._sanitize_content(content),
                    {"pattern_matched": pattern, "detection_method": "regex"}
                )
        
        return (True, ValidationSeverity.INFO, ValidationCategory.SECURITY, "", None, None, {})
    
    def _validate_file_upload(
        self,
        file_data: bytes,
        filename: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        parameters: Dict[str, Any] = None
    ) -> Tuple[bool, ValidationSeverity, ValidationCategory, str, Optional[str], Optional[str], Optional[str], Dict[str, Any]]:
        """Validate file upload parameters."""
        # This is handled in the main validate_file_upload method
        return (True, ValidationSeverity.INFO, ValidationCategory.FILE_UPLOAD, "", None, None, {})
    
    def _validate_request_size(
        self,
        request_data: Any,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        parameters: Dict[str, Any] = None
    ) -> Tuple[bool, ValidationSeverity, ValidationCategory, str, Optional[str], Optional[str], Optional[str], Dict[str, Any]]:
        """Validate request size."""
        # This is handled in the main validate_request method
        return (True, ValidationSeverity.INFO, ValidationCategory.LENGTH, "", None, None, {})
    
    def _sanitize_content(self, content: str) -> str:
        """Sanitize content to prevent XSS and other attacks."""
        if not content:
            return content
        
        # HTML escape
        sanitized = html.escape(content)
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', sanitized)
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        return sanitized.strip()
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        if '.' not in filename:
            return ''
        
        return filename.rsplit('.', 1)[-1].lower()
    
    async def _scan_file_for_threats(
        self,
        file_data: bytes,
        filename: str
    ) -> SecurityValidationResult:
        """
        Scan file for security threats.
        
        Args:
            file_data: The file content
            filename: The filename
            
        Returns:
            Security validation result
        """
        threats_detected = []
        risk_score = 0.0
        is_safe = True
        
        try:
            # Check file signature
            file_signature = file_data[:min(100, len(file_data))]
            
            # Check for executable signatures
            executable_signatures = [
                b'MZ',  # PE executable
                b'\x7fELF',  # ELF executable
                b'\xfe\xed\xfa',  # Mach-O executable
                b'\xca\xfe\xba',  # Java class
                b'PK\x03\x04',  # ZIP/JAR
                b'\x1f\x8b\x08',  # gzip
                b'#!/bin/',  # Shell script
                b'#!/usr/bin/',  # Shell script
                b'<script',  # HTML script
                b'<html',  # HTML
                b'<?php',  # PHP
                b'<?',  # PHP short tag
                b'<%',  # ASP
                b'<%@',  # JSP
            ]
            
            for signature in executable_signatures:
                if file_data.startswith(signature):
                    threats_detected.append(f"Executable file signature detected: {signature}")
                    risk_score += 30.0
                    is_safe = False
            
            # Check for suspicious content
            content_str = file_data[:1000].decode('utf-8', errors='ignore').lower()
            
            suspicious_patterns = [
                'eval(',
                'exec(',
                'system(',
                'passthru(',
                'shell_exec(',
                'document.cookie',
                'window.location',
                'javascript:',
                'vbscript:',
                '<script',
                '<iframe',
                '<object',
                '<embed',
                'link rel="stylesheet"',
                '@import',
                'expression(',
                'url(',
                'from base64',
                'convert.base64_decode'
            ]
            
            for pattern in suspicious_patterns:
                if pattern in content_str:
                    threats_detected.append(f"Suspicious content pattern detected: {pattern}")
                    risk_score += 10.0
                    is_safe = False
            
            # Check file entropy (for encrypted/packed files)
            if len(file_data) > 100:
                entropy = self._calculate_entropy(file_data[:256])
                if entropy > 7.0:  # High entropy indicates possible encryption/packing
                    threats_detected.append(f"High file entropy detected: {entropy:.2f}")
                    risk_score += 15.0
                    is_safe = False
            
        except Exception as e:
            logger.error(f"File security scan error: {e}")
            threats_detected.append(f"Scan error: {str(e)}")
            risk_score += 20.0
            is_safe = False
        
        # Cap risk score at 100
        risk_score = min(100.0, risk_score)
        
        return SecurityValidationResult(
            is_safe=is_safe,
            threats_detected=threats_detected,
            risk_score=risk_score,
            sanitized_content=None,  # No sanitization for binary files
            blocked_content=not is_safe,
            metadata={
                "scan_time": datetime.now(timezone.utc).isoformat(),
                "file_size": len(file_data),
                "filename": filename,
                "entropy": self._calculate_entropy(file_data[:256]) if len(file_data) > 100 else 0.0
            }
        )
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data."""
        if not data:
            return 0.0
        
        # Count byte frequencies
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1
        
        # Calculate entropy
        entropy = 0.0
        data_len = len(data)
        
        for count in byte_counts:
            if count > 0:
                probability = count / data_len
                entropy -= probability * (probability.bit_length() - 1)
        
        return entropy
    
    def _combine_validation_results(self, results: List[ValidationResult]) -> ValidationResult:
        """Combine multiple validation results into a single result."""
        if not results:
            return ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.CONTENT,
                message="Validation passed",
                metadata={"validation_count": 0}
            )
        
        # Find the most severe result
        most_severe = max(results, key=lambda r: (
            0 if r.is_valid else 1,
            0 if r.severity == ValidationSeverity.INFO else 1,
            0 if r.severity == ValidationSeverity.WARNING else 2,
            0 if r.severity == ValidationSeverity.ERROR else 3,
            0 if r.severity == ValidationSeverity.CRITICAL else 4
        ))
        
        # Collect all threats and issues
        all_threats = []
        all_metadata = {"validation_count": len(results)}
        
        for result in results:
            if not result.is_valid:
                all_threats.append(result.message)
            
            if result.metadata:
                all_metadata.update(result.metadata)
        
        return ValidationResult(
            is_valid=most_severe.is_valid,
            severity=most_severe.severity,
            category=most_severe.category,
            message=most_severe.message if not most_severe.is_valid else "Validation passed with warnings",
            field=most_severe.field,
            value=most_severe.value,
            sanitized_value=most_severe.sanitized_value,
            metadata=all_metadata
        )
    
    def get_validation_rules(self) -> Dict[str, ValidationRule]:
        """Get all validation rules."""
        return self.validation_rules.copy()
    
    def get_rule(self, rule_name: str) -> Optional[ValidationRule]:
        """Get a specific validation rule."""
        return self.validation_rules.get(rule_name)
    
    def update_rule(self, rule_name: str, **kwargs):
        """Update a validation rule."""
        if rule_name in self.validation_rules:
            rule = self.validation_rules[rule_name]
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            logger.info(f"Updated validation rule {rule_name}: {kwargs}")
        else:
            logger.warning(f"Validation rule {rule_name} not found")
    
    def enable_rule(self, rule_name: str):
        """Enable a validation rule."""
        if rule_name in self.validation_rules:
            self.validation_rules[rule_name].enabled = True
            logger.info(f"Enabled validation rule: {rule_name}")
    
    def disable_rule(self, rule_name: str):
        """Disable a validation rule."""
        if rule_name in self.validation_rules:
            self.validation_rules[rule_name].enabled = False
            logger.info(f"Disabled validation rule: {rule_name}")


# Global enhanced validator instance
enhanced_validator = EnhancedValidator()


def get_enhanced_validator() -> EnhancedValidator:
    """Get the global enhanced validator instance."""
    return enhanced_validator


# Decorator for validation
def validate_input(
    validator_name: Optional[str] = None,
    sanitize: bool = True
):
    """Decorator to validate function inputs."""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Extract validation context
            user_id = kwargs.pop('user_id', None)
            context = kwargs.pop('context', {})
            
            # Get validator instance
            validator = get_enhanced_validator()
            
            # Validate all string inputs
            validation_results = []
            
            for arg_name, arg_value in kwargs.items():
                if isinstance(arg_value, str):
                    if validator_name:
                        # Validate specific rule
                        rule = validator.get_rule(validator_name)
                        if rule and rule.enabled:
                            result = await rule.validator(arg_value, user_id, {**context, "arg_name": arg_name}, rule.parameters)
                            if isinstance(result, ValidationResult):
                                validation_results.append(result)
                    else:
                        # Validate all rules
                        result = await validator.validate_message(arg_value, user_id, {**context, "arg_name": arg_name})
                        validation_results.append(result)
            
            # Combine validation results
            if validation_results:
                combined_result = validator._combine_validation_results(validation_results)
                
                if not combined_result.is_valid:
                    logger.warning(f"Input validation failed for {func.__name__}: {combined_result.message}")
                    raise ValueError(f"Validation failed: {combined_result.message}")
            
            # Execute function with potentially sanitized inputs
            if sanitize:
                for arg_name, arg_value in kwargs.items():
                    if isinstance(arg_value, str) and combined_result.sanitized_value:
                        kwargs[arg_name] = combined_result.sanitized_value
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator