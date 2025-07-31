"""
Intelligent Authentication Middleware.

This module provides middleware for request preprocessing, context enrichment,
and enhanced rate limiting based on risk scores while maintaining UI consistency.
"""

from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import logging

try:
    from fastapi import Request, Response, HTTPException, status
    from fastapi.responses import JSONResponse
except Exception:
    from ai_karen_engine.fastapi_stub import Request, Response, HTTPException, status, JSONResponse

from ai_karen_engine.security.models import AuthContext, RiskLevel
from ai_karen_engine.security.intelligent_auth_service import IntelligentAuthService
from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)


class IntelligentAuthMiddleware:
    """
    Middleware for intelligent authentication preprocessing and context enrichment.
    
    Features:
    - Request context enrichment with geolocation and device data
    - Risk-based rate limiting enhancements
    - Audit logging for all intelligent authentication decisions
    - UI-consistent error responses
    """

    def __init__(self, 
                 intelligent_auth_service: Optional[IntelligentAuthService] = None,
                 enable_geolocation: bool = True,
                 enable_device_fingerprinting: bool = True,
                 enable_risk_based_rate_limiting: bool = True):
        """
        Initialize the intelligent authentication middleware.
        
        Args:
            intelligent_auth_service: Optional intelligent auth service instance
            enable_geolocation: Whether to enable geolocation enrichment
            enable_device_fingerprinting: Whether to enable device fingerprinting
            enable_risk_based_rate_limiting: Whether to enable risk-based rate limiting
        """
        self.intelligent_auth_service = intelligent_auth_service
        self.enable_geolocation = enable_geolocation
        self.enable_device_fingerprinting = enable_device_fingerprinting
        self.enable_risk_based_rate_limiting = enable_risk_based_rate_limiting
        
        # Enhanced rate limiting storage
        self._rate_limit_storage: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._risk_based_limits: Dict[str, Dict[str, Any]] = {}
        
        # Audit logging storage
        self._audit_log: List[Dict[str, Any]] = []
        
        logger.info("Intelligent Authentication Middleware initialized")

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through intelligent authentication middleware.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/endpoint in chain
            
        Returns:
            Response: Processed response
        """
        start_time = time.time()
        
        try:
            # Check if this is an authentication-related request
            if self._is_auth_request(request):
                # Enrich request context
                await self._enrich_request_context(request)
                
                # Apply risk-based rate limiting
                if self.enable_risk_based_rate_limiting:
                    await self._apply_risk_based_rate_limiting(request)
            
            # Process request
            response = await call_next(request)
            
            # Post-process authentication responses
            if self._is_auth_request(request):
                await self._post_process_auth_response(request, response)
            
            # Log processing time
            processing_time = time.time() - start_time
            if processing_time > 1.0:  # Log slow requests
                logger.warning(
                    f"Slow middleware processing",
                    extra={
                        "path": request.url.path,
                        "processing_time": processing_time,
                        "client_ip": self._get_client_ip(request)
                    }
                )
            
            return response
            
        except HTTPException as e:
            # Ensure HTTP exceptions maintain UI consistency
            return await self._create_consistent_error_response(request, e)
        except Exception as e:
            # Handle unexpected errors with consistent formatting
            logger.error(
                f"Middleware error",
                extra={
                    "path": request.url.path,
                    "error": str(e),
                    "client_ip": self._get_client_ip(request)
                }
            )
            return await self._create_consistent_error_response(
                request,
                HTTPException(status_code=500, detail="Internal server error")
            )

    def _is_auth_request(self, request: Request) -> bool:
        """Check if request is authentication-related."""
        auth_paths = ["/api/auth/login", "/api/auth/register", "/api/auth/analyze", "/api/auth/token"]
        return any(request.url.path.startswith(path) for path in auth_paths)

    async def _enrich_request_context(self, request: Request) -> None:
        """
        Enrich request context with additional security data.
        
        Args:
            request: FastAPI request object
        """
        try:
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            
            # Add geolocation data if enabled
            if self.enable_geolocation:
                geolocation_data = await self._get_geolocation_data(client_ip)
                if geolocation_data:
                    # Store in request state for later use
                    if not hasattr(request.state, "auth_context"):
                        request.state.auth_context = {}
                    request.state.auth_context["geolocation"] = geolocation_data
            
            # Add device fingerprinting if enabled
            if self.enable_device_fingerprinting:
                device_fingerprint = await self._generate_device_fingerprint(request)
                if device_fingerprint:
                    if not hasattr(request.state, "auth_context"):
                        request.state.auth_context = {}
                    request.state.auth_context["device_fingerprint"] = device_fingerprint
            
            # Add threat intelligence context
            threat_context = await self._get_threat_context(client_ip, user_agent)
            if threat_context:
                if not hasattr(request.state, "auth_context"):
                    request.state.auth_context = {}
                request.state.auth_context["threat_context"] = threat_context
            
            logger.debug(
                f"Request context enriched",
                extra={
                    "client_ip": client_ip,
                    "has_geolocation": self.enable_geolocation and "geolocation" in getattr(request.state, "auth_context", {}),
                    "has_device_fingerprint": self.enable_device_fingerprinting and "device_fingerprint" in getattr(request.state, "auth_context", {}),
                    "has_threat_context": "threat_context" in getattr(request.state, "auth_context", {})
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to enrich request context: {e}")

    async def _apply_risk_based_rate_limiting(self, request: Request) -> None:
        """
        Apply enhanced rate limiting based on risk assessment.
        
        Args:
            request: FastAPI request object
            
        Raises:
            HTTPException: If rate limit is exceeded
        """
        try:
            client_ip = self._get_client_ip(request)
            now = datetime.utcnow()
            
            # Get current attempts for this IP
            attempts = self._rate_limit_storage[client_ip]
            
            # Clean old attempts (older than 1 hour)
            attempts = [
                attempt for attempt in attempts 
                if now - attempt["timestamp"] < timedelta(hours=1)
            ]
            self._rate_limit_storage[client_ip] = attempts
            
            # Get risk-based limits for this IP
            risk_limits = self._risk_based_limits.get(client_ip, {
                "base_limit": 10,  # Base limit per hour
                "current_limit": 10,
                "risk_multiplier": 1.0,
                "last_updated": now
            })
            
            # Check if we need to update risk assessment
            if (now - risk_limits["last_updated"]).seconds > 300:  # Update every 5 minutes
                await self._update_risk_based_limits(client_ip, risk_limits)
            
            # Check current rate limit
            current_attempts = len([
                attempt for attempt in attempts
                if now - attempt["timestamp"] < timedelta(minutes=60)
            ])
            
            if current_attempts >= risk_limits["current_limit"]:
                # Log rate limit exceeded
                logger.warning(
                    f"Rate limit exceeded",
                    extra={
                        "client_ip": client_ip,
                        "current_attempts": current_attempts,
                        "limit": risk_limits["current_limit"],
                        "risk_multiplier": risk_limits["risk_multiplier"]
                    }
                )
                
                # Create audit log entry
                await self._log_security_event(
                    "rate_limit_exceeded",
                    {
                        "client_ip": client_ip,
                        "attempts": current_attempts,
                        "limit": risk_limits["current_limit"],
                        "path": request.url.path
                    }
                )
                
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later."
                )
            
            # Record this attempt
            attempts.append({
                "timestamp": now,
                "path": request.url.path,
                "user_agent": request.headers.get("user-agent", "")
            })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Risk-based rate limiting failed: {e}")

    async def _update_risk_based_limits(self, client_ip: str, risk_limits: Dict[str, Any]) -> None:
        """
        Update risk-based rate limits for a client IP.
        
        Args:
            client_ip: Client IP address
            risk_limits: Current risk limits dictionary
        """
        try:
            if not self.intelligent_auth_service:
                return
            
            # Get recent attempts for risk assessment
            recent_attempts = self._rate_limit_storage.get(client_ip, [])
            
            # Calculate risk multiplier based on recent activity
            risk_multiplier = 1.0
            
            # Increase limits for low-risk IPs, decrease for high-risk
            if len(recent_attempts) > 20:  # High activity
                risk_multiplier = 0.5  # Stricter limits
            elif len(recent_attempts) < 5:  # Low activity
                risk_multiplier = 2.0  # More lenient limits
            
            # Update limits
            risk_limits.update({
                "current_limit": max(1, int(risk_limits["base_limit"] * risk_multiplier)),
                "risk_multiplier": risk_multiplier,
                "last_updated": datetime.utcnow()
            })
            
            self._risk_based_limits[client_ip] = risk_limits
            
            logger.debug(
                f"Updated risk-based limits",
                extra={
                    "client_ip": client_ip,
                    "new_limit": risk_limits["current_limit"],
                    "risk_multiplier": risk_multiplier
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to update risk-based limits: {e}")

    async def _post_process_auth_response(self, request: Request, response: Response) -> None:
        """
        Post-process authentication responses for audit logging.
        
        Args:
            request: FastAPI request object
            response: FastAPI response object
        """
        try:
            client_ip = self._get_client_ip(request)
            
            # Log authentication decision
            await self._log_security_event(
                "auth_response",
                {
                    "client_ip": client_ip,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "user_agent": request.headers.get("user-agent", ""),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Add security headers to response
            if hasattr(response, "headers"):
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["X-Frame-Options"] = "DENY"
                response.headers["X-XSS-Protection"] = "1; mode=block"
            
        except Exception as e:
            logger.warning(f"Failed to post-process auth response: {e}")

    async def _get_geolocation_data(self, client_ip: str) -> Optional[Dict[str, Any]]:
        """
        Get geolocation data for client IP.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Optional geolocation data dictionary
        """
        try:
            # In a real implementation, this would call a geolocation service
            # For now, return mock data for non-local IPs
            if client_ip in ["127.0.0.1", "localhost", "::1"]:
                return {
                    "country": "Local",
                    "region": "Local",
                    "city": "Local",
                    "latitude": 0.0,
                    "longitude": 0.0,
                    "timezone": "UTC",
                    "is_usual_location": True
                }
            
            # Mock geolocation data
            return {
                "country": "US",
                "region": "California",
                "city": "San Francisco",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "timezone": "America/Los_Angeles",
                "is_usual_location": False
            }
            
        except Exception as e:
            logger.warning(f"Failed to get geolocation data: {e}")
            return None

    async def _generate_device_fingerprint(self, request: Request) -> Optional[str]:
        """
        Generate device fingerprint from request headers.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Optional device fingerprint string
        """
        try:
            # Collect fingerprinting data
            fingerprint_data = {
                "user_agent": request.headers.get("user-agent", ""),
                "accept": request.headers.get("accept", ""),
                "accept_language": request.headers.get("accept-language", ""),
                "accept_encoding": request.headers.get("accept-encoding", ""),
                "connection": request.headers.get("connection", ""),
                "upgrade_insecure_requests": request.headers.get("upgrade-insecure-requests", "")
            }
            
            # Create simple fingerprint hash
            import hashlib
            fingerprint_string = "|".join(f"{k}:{v}" for k, v in fingerprint_data.items())
            fingerprint = hashlib.md5(fingerprint_string.encode()).hexdigest()
            
            return fingerprint
            
        except Exception as e:
            logger.warning(f"Failed to generate device fingerprint: {e}")
            return None

    async def _get_threat_context(self, client_ip: str, user_agent: str) -> Optional[Dict[str, Any]]:
        """
        Get threat intelligence context for the request.
        
        Args:
            client_ip: Client IP address
            user_agent: User agent string
            
        Returns:
            Optional threat context dictionary
        """
        try:
            # Mock threat intelligence data
            threat_context = {
                "is_tor_exit_node": False,
                "is_vpn": False,
                "ip_reputation_score": 0.1,
                "known_attack_patterns": [],
                "threat_actor_indicators": []
            }
            
            # Simple heuristics for demo
            if "tor" in user_agent.lower():
                threat_context["is_tor_exit_node"] = True
                threat_context["ip_reputation_score"] = 0.7
            
            if "vpn" in user_agent.lower():
                threat_context["is_vpn"] = True
                threat_context["ip_reputation_score"] = 0.3
            
            return threat_context
            
        except Exception as e:
            logger.warning(f"Failed to get threat context: {e}")
            return None

    async def _log_security_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Log security event for audit purposes.
        
        Args:
            event_type: Type of security event
            event_data: Event data dictionary
        """
        try:
            audit_entry = {
                "event_type": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": event_data
            }
            
            # Store in memory (in production, this would go to a persistent audit log)
            self._audit_log.append(audit_entry)
            
            # Keep only last 1000 entries to prevent memory issues
            if len(self._audit_log) > 1000:
                self._audit_log = self._audit_log[-1000:]
            
            # Log to structured logger
            logger.info(
                f"Security event: {event_type}",
                extra={
                    "event_type": event_type,
                    "event_data": event_data
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to log security event: {e}")

    async def _create_consistent_error_response(self, request: Request, exception: HTTPException) -> JSONResponse:
        """
        Create UI-consistent error response.
        
        Args:
            request: FastAPI request object
            exception: HTTP exception
            
        Returns:
            JSONResponse with consistent error format
        """
        try:
            # Determine if this is an API request or web request
            is_api_request = request.url.path.startswith("/api/")
            
            # Create consistent error response format
            error_response = {
                "error": True,
                "status_code": exception.status_code,
                "detail": exception.detail,
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path
            }
            
            # Add request ID if available
            if hasattr(request.state, "auth_context") and "request_id" in request.state.auth_context:
                error_response["request_id"] = request.state.auth_context["request_id"]
            
            # Log error response
            logger.info(
                f"Error response generated",
                extra={
                    "status_code": exception.status_code,
                    "detail": exception.detail,
                    "path": request.url.path,
                    "client_ip": self._get_client_ip(request)
                }
            )
            
            return JSONResponse(
                status_code=exception.status_code,
                content=error_response,
                headers={
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                    "X-XSS-Protection": "1; mode=block"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create consistent error response: {e}")
            # Fallback to basic error response
            return JSONResponse(
                status_code=500,
                content={"error": True, "detail": "Internal server error"}
            )

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client IP address string
        """
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent audit log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries
        """
        return self._audit_log[-limit:] if self._audit_log else []

    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """
        Get rate limiting statistics.
        
        Returns:
            Dictionary with rate limiting statistics
        """
        return {
            "total_ips_tracked": len(self._rate_limit_storage),
            "total_risk_profiles": len(self._risk_based_limits),
            "active_rate_limits": sum(
                1 for attempts in self._rate_limit_storage.values() 
                if len(attempts) > 0
            )
        }