"""
HTTP Request Validation Framework

This module provides comprehensive HTTP request validation capabilities
including method validation, header validation, content length checks,
and security analysis integration.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from fastapi import Request

logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """Configuration for HTTP request validation."""
    max_content_length: int = 10 * 1024 * 1024  # 10MB
    allowed_methods: Set[str] = field(default_factory=lambda: {
        "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"
    })
    max_header_size: int = 8192
    max_headers_count: int = 100
    rate_limit_requests_per_minute: int = 100
    enable_security_analysis: bool = True
    log_invalid_requests: bool = True
    blocked_user_agents: Set[str] = field(default_factory=lambda: {
        "sqlmap", "nikto", "nmap", "masscan", "zap"
    })
    suspicious_headers: Set[str] = field(default_factory=lambda: {
        "x-forwarded-host", "x-cluster-client-ip", "x-real-ip"
    })


@dataclass
class ValidationResult:
    """Result of HTTP request validation."""
    is_valid: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    security_threat_level: str = "none"
    should_rate_limit: bool = False
    sanitized_data: Optional[Dict[str, Any]] = None
    validation_details: Optional[Dict[str, Any]] = None


class HTTPRequestValidator:
    """Comprehensive HTTP request validator."""
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        """Initialize the validator with configuration."""
        self.config = config or ValidationConfig()
        self._setup_validation_patterns()
    
    def _setup_validation_patterns(self):
        """Setup regex patterns for validation."""
        # Common attack patterns
        self.sql_injection_patterns = [
            re.compile(r"(\bunion\b.*\bselect\b)", re.IGNORECASE),
            re.compile(r"(\bselect\b.*\bfrom\b)", re.IGNORECASE),
            re.compile(r"(\binsert\b.*\binto\b)", re.IGNORECASE),
            re.compile(r"(\bdelete\b.*\bfrom\b)", re.IGNORECASE),
            re.compile(r"(\bdrop\b.*\btable\b)", re.IGNORECASE),
        ]
        
        self.xss_patterns = [
            re.compile(r"<script[^>]*>", re.IGNORECASE),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),
            re.compile(r"<iframe[^>]*>", re.IGNORECASE),
        ]
        
        self.path_traversal_patterns = [
            re.compile(r"\.\.\/"),
            re.compile(r"\.\.\\"),
            re.compile(r"%2e%2e%2f", re.IGNORECASE),
            re.compile(r"%2e%2e%5c", re.IGNORECASE),
        ]
    
    async def validate_request(self, request: Request) -> ValidationResult:
        """
        Perform comprehensive request validation.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            ValidationResult with validation outcome and details
        """
        validation_details = {}
        
        try:
            # Basic structure validation
            if not self._validate_basic_structure(request):
                return ValidationResult(
                    is_valid=False,
                    error_type="malformed_request",
                    error_message="Request missing basic HTTP structure",
                    validation_details=validation_details
                )
            
            # HTTP method validation
            method_result = self.is_valid_http_method(request.method)
            validation_details["method_valid"] = method_result
            if not method_result:
                return ValidationResult(
                    is_valid=False,
                    error_type="invalid_method",
                    error_message=f"HTTP method '{request.method}' not allowed",
                    validation_details=validation_details
                )
            
            # Headers validation
            headers_result = await self.validate_headers(request)
            validation_details["headers_valid"] = headers_result["is_valid"]
            validation_details["headers_details"] = headers_result
            if not headers_result["is_valid"]:
                return ValidationResult(
                    is_valid=False,
                    error_type="invalid_headers",
                    error_message=headers_result["error_message"],
                    security_threat_level=headers_result.get("threat_level", "low"),
                    validation_details=validation_details
                )
            
            # Content length validation
            content_length_result = await self.check_content_length(request)
            validation_details["content_length_valid"] = content_length_result["is_valid"]
            if not content_length_result["is_valid"]:
                return ValidationResult(
                    is_valid=False,
                    error_type="content_too_large",
                    error_message=content_length_result["error_message"],
                    validation_details=validation_details
                )
            
            # Security analysis
            if self.config.enable_security_analysis:
                security_result = await self.analyze_security_threats(request)
                validation_details["security_analysis"] = security_result
                if security_result["threat_level"] in ["high", "critical"]:
                    return ValidationResult(
                        is_valid=False,
                        error_type="security_threat",
                        error_message="Request contains security threats",
                        security_threat_level=security_result["threat_level"],
                        should_rate_limit=True,
                        validation_details=validation_details
                    )
            
            # If all validations pass
            return ValidationResult(
                is_valid=True,
                security_threat_level="none",
                validation_details=validation_details
            )
            
        except Exception as e:
            logger.error(f"Error during request validation: {e}", exc_info=True)
            return ValidationResult(
                is_valid=False,
                error_type="validation_error",
                error_message="Internal validation error",
                validation_details=validation_details
            )
    
    def _validate_basic_structure(self, request: Request) -> bool:
        """Validate basic HTTP request structure."""
        try:
            return (
                hasattr(request, 'method') and 
                hasattr(request, 'url') and 
                hasattr(request, 'headers') and
                request.method is not None and
                request.url is not None
            )
        except Exception:
            return False
    
    def is_valid_http_method(self, method: str) -> bool:
        """
        Validate HTTP method against allowed methods.
        
        Args:
            method: HTTP method string
            
        Returns:
            True if method is valid, False otherwise
        """
        if not method or not isinstance(method, str):
            return False
        
        return method.upper() in self.config.allowed_methods
    
    async def validate_headers(self, request: Request) -> Dict[str, Any]:
        """
        Validate request headers for security and compliance.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Dictionary with validation results and details
        """
        try:
            headers = dict(request.headers)
            
            # Check header count
            if len(headers) > self.config.max_headers_count:
                return {
                    "is_valid": False,
                    "error_message": f"Too many headers: {len(headers)} > {self.config.max_headers_count}",
                    "threat_level": "medium"
                }
            
            # Check individual header sizes
            for name, value in headers.items():
                if len(name) + len(value) > self.config.max_header_size:
                    return {
                        "is_valid": False,
                        "error_message": f"Header too large: {name}",
                        "threat_level": "medium"
                    }
            
            # Check for suspicious headers
            suspicious_found = []
            for header_name in headers.keys():
                if header_name.lower() in self.config.suspicious_headers:
                    suspicious_found.append(header_name)
            
            # Check User-Agent for blocked patterns
            user_agent = headers.get("user-agent", "").lower()
            blocked_agent = any(
                blocked in user_agent 
                for blocked in self.config.blocked_user_agents
            )
            
            threat_level = "none"
            if suspicious_found or blocked_agent:
                threat_level = "medium" if blocked_agent else "low"
            
            return {
                "is_valid": not blocked_agent,  # Block if user agent is malicious
                "error_message": "Blocked user agent detected" if blocked_agent else None,
                "threat_level": threat_level,
                "suspicious_headers": suspicious_found,
                "blocked_user_agent": blocked_agent
            }
            
        except Exception as e:
            logger.error(f"Error validating headers: {e}")
            return {
                "is_valid": False,
                "error_message": "Header validation error",
                "threat_level": "low"
            }
    
    async def check_content_length(self, request: Request) -> Dict[str, Any]:
        """
        Validate request content length.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Dictionary with validation results
        """
        try:
            content_length = request.headers.get("content-length")
            
            if content_length is None:
                # No content-length header is acceptable for GET requests
                if request.method.upper() in ["GET", "HEAD", "OPTIONS"]:
                    return {"is_valid": True}
                # For other methods, we'll allow it but it's suspicious
                return {"is_valid": True, "warning": "No content-length header"}
            
            try:
                length = int(content_length)
            except ValueError:
                return {
                    "is_valid": False,
                    "error_message": "Invalid content-length header"
                }
            
            if length < 0:
                return {
                    "is_valid": False,
                    "error_message": "Negative content-length"
                }
            
            if length > self.config.max_content_length:
                return {
                    "is_valid": False,
                    "error_message": f"Content too large: {length} > {self.config.max_content_length}"
                }
            
            return {"is_valid": True, "content_length": length}
            
        except Exception as e:
            logger.error(f"Error checking content length: {e}")
            return {
                "is_valid": False,
                "error_message": "Content length validation error"
            }
    
    async def analyze_security_threats(self, request: Request) -> Dict[str, Any]:
        """
        Analyze request for security threats.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Dictionary with security analysis results
        """
        threats_found = []
        threat_level = "none"
        
        try:
            # Analyze URL path
            path = str(request.url.path)
            query = str(request.url.query) if request.url.query else ""
            
            # Check for SQL injection patterns
            for pattern in self.sql_injection_patterns:
                if pattern.search(path) or pattern.search(query):
                    threats_found.append("sql_injection")
                    threat_level = "high"
                    break
            
            # Check for XSS patterns
            for pattern in self.xss_patterns:
                if pattern.search(path) or pattern.search(query):
                    threats_found.append("xss")
                    threat_level = max(threat_level, "medium", key=lambda x: ["none", "low", "medium", "high", "critical"].index(x))
                    break
            
            # Check for path traversal
            for pattern in self.path_traversal_patterns:
                if pattern.search(path) or pattern.search(query):
                    threats_found.append("path_traversal")
                    threat_level = max(threat_level, "medium", key=lambda x: ["none", "low", "medium", "high", "critical"].index(x))
                    break
            
            # Check for suspicious patterns in headers
            headers = dict(request.headers)
            for header_value in headers.values():
                for pattern in self.sql_injection_patterns + self.xss_patterns:
                    if pattern.search(header_value):
                        threats_found.append("header_injection")
                        threat_level = max(threat_level, "medium", key=lambda x: ["none", "low", "medium", "high", "critical"].index(x))
                        break
            
            return {
                "threat_level": threat_level,
                "threats_found": threats_found,
                "analysis_complete": True
            }
            
        except Exception as e:
            logger.error(f"Error during security analysis: {e}")
            return {
                "threat_level": "low",
                "threats_found": ["analysis_error"],
                "analysis_complete": False,
                "error": str(e)
            }
    
    def sanitize_request_data(self, request: Request) -> Dict[str, Any]:
        """
        Sanitize request data for safe logging.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Dictionary with sanitized request data
        """
        try:
            sanitized = {
                "method": getattr(request, 'method', 'unknown'),
                "path": str(getattr(request.url, 'path', '/')) if hasattr(request, 'url') else 'unknown',
                "query_params": {},
                "headers": {},
                "client_ip": getattr(request.client, 'host', 'unknown') if hasattr(request, 'client') and request.client else "unknown"
            }
            
            # Safely handle query parameters
            if hasattr(request, 'query_params') and request.query_params:
                try:
                    sanitized["query_params"] = dict(request.query_params)
                except (TypeError, AttributeError):
                    sanitized["query_params"] = {}
            
            # Sanitize headers - remove sensitive information
            sensitive_headers = {"authorization", "cookie", "x-api-key", "x-auth-token"}
            if hasattr(request, 'headers') and request.headers:
                try:
                    for name, value in request.headers.items():
                        if name.lower() in sensitive_headers:
                            sanitized["headers"][name] = "[REDACTED]"
                        else:
                            # Truncate long header values
                            sanitized["headers"][name] = value[:100] + "..." if len(value) > 100 else value
                except (TypeError, AttributeError):
                    sanitized["headers"] = {"error": "Could not parse headers"}
            
            # Sanitize query parameters
            sensitive_params = {"password", "token", "key", "secret", "auth"}
            for param, value in sanitized["query_params"].items():
                if any(sensitive in param.lower() for sensitive in sensitive_params):
                    sanitized["query_params"][param] = "[REDACTED]"
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing request data: {e}")
            return {"error": "Failed to sanitize request data"}