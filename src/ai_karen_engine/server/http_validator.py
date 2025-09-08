"""
HTTP Request Validation Framework

This module provides comprehensive HTTP request validation capabilities
including method validation, header validation, content length checks,
and security analysis integration.
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from fastapi import Request

from ai_karen_engine.monitoring.validation_metrics import (
    get_validation_metrics_collector,
    ValidationEventType,
    ThreatLevel,
    ValidationMetricsData
)

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
        self.metrics_collector = get_validation_metrics_collector()
    
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
        start_time = time.time()
        
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
                
                # Check if this is a trusted API endpoint that should have relaxed security
                is_trusted_endpoint = self._is_trusted_api_endpoint(request)
                
                # Apply different thresholds based on endpoint trust level
                if is_trusted_endpoint:
                    # For trusted API endpoints, do NOT hard-block; downgrade to monitoring-only.
                    should_block = False
                else:
                    # For other endpoints, original strict logic
                    should_block = (
                        security_result["threat_level"] == "critical"
                        or (
                            security_result["threat_level"] == "high"
                            and security_result.get("confidence_score", 0) > 0.8
                        )
                    )
                
                if should_block:
                    return ValidationResult(
                        is_valid=False,
                        error_type="security_threat",
                        error_message="Request contains security threats",
                        security_threat_level=security_result["threat_level"],
                        should_rate_limit=True,
                        validation_details=validation_details
                    )
            
            # If all validations pass
            processing_time_ms = (time.time() - start_time) * 1000
            result = ValidationResult(
                is_valid=True,
                security_threat_level="none",
                validation_details=validation_details
            )
            
            # Record successful validation metrics
            self._record_validation_metrics(request, result, processing_time_ms)
            
            return result
            
        except Exception as e:
            logger.error(f"Error during request validation: {e}", exc_info=True)
            processing_time_ms = (time.time() - start_time) * 1000
            result = ValidationResult(
                is_valid=False,
                error_type="validation_error",
                error_message="Internal validation error",
                validation_details=validation_details
            )
            
            # Record error metrics
            self._record_validation_metrics(request, result, processing_time_ms)
            
            return result
    
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
    
    def _is_trusted_api_endpoint(self, request: Request) -> bool:
        """Check if the request is to a trusted API endpoint that should have relaxed security."""
        try:
            path = str(request.url.path).lower()
            
            # List of trusted API endpoint patterns
            trusted_patterns = [
                "/api/health",
                "/health",
                "/api/ping",
                "/ping",
                "/api/status",
                "/status",
                "/api/providers/",
                "/api/auth/",
                "/api/plugins",
                "/api/analytics/",
                "/api/system/",
                "/api/models/",
                "/api/memory/",
                "/api/conversations/",
                "/api/files/",
                "/api/websocket",
                "/api/audit/",
                "/api/copilot/",
                "/copilot/",
                "/docs",
                "/openapi.json",
                "/favicon.ico"
            ]
            
            # Check if the path starts with any trusted pattern
            for pattern in trusted_patterns:
                if path.startswith(pattern):
                    return True
            
            return False
            
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
        Analyze request for security threats using the SecurityAnalyzer.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Dictionary with security analysis results
        """
        try:
            # Import SecurityAnalyzer here to avoid circular imports
            from .security_analyzer import SecurityAnalyzer
            
            # Create or reuse security analyzer instance
            if not hasattr(self, '_security_analyzer'):
                self._security_analyzer = SecurityAnalyzer()
            
            # Perform comprehensive security analysis
            assessment = await self._security_analyzer.analyze_request(request)
            
            return {
                "threat_level": assessment.threat_level,
                "threats_found": assessment.attack_categories,
                "analysis_complete": True,
                "detected_patterns": assessment.detected_patterns,
                "client_reputation": assessment.client_reputation,
                "recommended_action": assessment.recommended_action,
                "confidence_score": assessment.confidence_score,
                "risk_factors": assessment.risk_factors
            }
            
        except Exception as e:
            logger.error(f"Error during security analysis: {e}")
            # Fallback to basic analysis if SecurityAnalyzer fails
            return await self._basic_security_analysis(request)
    
    async def _basic_security_analysis(self, request: Request) -> Dict[str, Any]:
        """
        Fallback basic security analysis if SecurityAnalyzer fails.
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Dictionary with basic security analysis results
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
            logger.error(f"Error during basic security analysis: {e}")
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
    
    def _record_validation_metrics(self, request: Request, result: ValidationResult, processing_time_ms: float):
        """Record validation metrics for monitoring"""
        try:
            # Determine event type and threat level
            if result.is_valid:
                event_type = ValidationEventType.REQUEST_VALIDATED
                threat_level = ThreatLevel.NONE
            else:
                event_type = ValidationEventType.REQUEST_REJECTED
                threat_level = self._map_threat_level(result.security_threat_level)
            
            # Extract client information
            client_ip = getattr(request.client, 'host', 'unknown') if hasattr(request, 'client') and request.client else "unknown"
            client_ip_hash = self._hash_ip(client_ip) if client_ip != "unknown" else "unknown"
            
            # Extract request characteristics
            endpoint = str(request.url.path) if hasattr(request, 'url') else "unknown"
            method = getattr(request, 'method', 'unknown')
            user_agent = request.headers.get('user-agent', '') if hasattr(request, 'headers') else ''
            user_agent_category = self._categorize_user_agent(user_agent)
            
            # Extract attack categories from validation details
            attack_categories = []
            if result.validation_details and 'security_analysis' in result.validation_details:
                security_analysis = result.validation_details['security_analysis']
                attack_categories = security_analysis.get('threats_found', [])
            
            # Prepare additional labels
            additional_labels = {
                'confidence_score': str(result.validation_details.get('security_analysis', {}).get('confidence_score', 0.0)),
                'client_reputation': result.validation_details.get('security_analysis', {}).get('client_reputation', 'unknown'),
                'validation_rule_details': result.error_type or 'standard_validation'
            }
            
            # Record request characteristics
            if hasattr(request, 'headers'):
                headers_count = len(request.headers)
                content_length = int(request.headers.get('content-length', 0))
                
                self.metrics_collector.record_request_characteristics(
                    endpoint=endpoint,
                    method=method,
                    size_bytes=content_length,
                    headers_count=headers_count,
                    validation_result="allowed" if result.is_valid else "blocked"
                )
            
            # Create and record metrics data
            metrics_data = ValidationMetricsData(
                event_type=event_type,
                threat_level=threat_level,
                validation_rule=result.error_type or "standard_validation",
                client_ip_hash=client_ip_hash,
                endpoint=endpoint,
                http_method=method,
                user_agent_category=user_agent_category,
                processing_time_ms=processing_time_ms,
                attack_categories=attack_categories,
                additional_labels=additional_labels
            )
            
            self.metrics_collector.record_validation_event(metrics_data)
            
        except Exception as e:
            logger.error(f"Error recording validation metrics: {e}")
    
    def _hash_ip(self, ip: str) -> str:
        """Create a hash of the IP address for privacy"""
        import hashlib
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    def _map_threat_level(self, threat_level_str: str) -> ThreatLevel:
        """Map string threat level to ThreatLevel enum"""
        mapping = {
            "none": ThreatLevel.NONE,
            "low": ThreatLevel.LOW,
            "medium": ThreatLevel.MEDIUM,
            "high": ThreatLevel.HIGH,
            "critical": ThreatLevel.CRITICAL
        }
        return mapping.get(threat_level_str.lower(), ThreatLevel.NONE)
    
    def _categorize_user_agent(self, user_agent: str) -> str:
        """Categorize user agent into broad categories"""
        if not user_agent:
            return "unknown"
        
        user_agent_lower = user_agent.lower()
        
        # Bot detection
        bot_indicators = ['bot', 'crawler', 'spider', 'scraper', 'indexer']
        if any(indicator in user_agent_lower for indicator in bot_indicators):
            return "bot"
        
        # Browser detection
        browsers = ['chrome', 'firefox', 'safari', 'edge', 'opera']
        if any(browser in user_agent_lower for browser in browsers):
            return "browser"
        
        # Mobile detection
        mobile_indicators = ['mobile', 'android', 'iphone', 'ipad']
        if any(indicator in user_agent_lower for indicator in mobile_indicators):
            return "mobile"
        
        # API client detection
        api_indicators = ['curl', 'wget', 'python', 'java', 'go-http', 'postman']
        if any(indicator in user_agent_lower for indicator in api_indicators):
            return "api_client"
        
        # Security tool detection
        security_tools = ['sqlmap', 'nikto', 'nmap', 'masscan', 'zap', 'burp']
        if any(tool in user_agent_lower for tool in security_tools):
            return "security_tool"
        
        return "other"
