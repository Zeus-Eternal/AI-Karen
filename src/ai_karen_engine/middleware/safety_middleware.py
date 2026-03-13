"""
Safety Middleware for CoPilot Architecture.

This middleware provides comprehensive safety checks for all requests and responses
in the CoPilot Architecture, including content safety validation, authorization checks,
and integration with the existing safety systems.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
from enum import Enum

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.services.agents.agent_safety import AgentSafety
from src.services.agents.agent_safety_types import (
    SafetyConfig, SafetyLevel, RiskLevel, ValidationResult, Context
)
from src.auth.auth_middleware import get_current_user

logger = logging.getLogger(__name__)


class SafetyAction(str, Enum):
    """Enum representing different safety actions."""
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    QUARANTINE = "quarantine"
    ESCALATE = "escalate"


class SafetyMiddlewareConfig:
    """Configuration for the Safety Middleware."""
    
    def __init__(
        self,
        enable_content_safety: bool = True,
        enable_authorization: bool = True,
        enable_behavior_monitoring: bool = True,
        enable_compliance_checking: bool = True,
        default_safety_level: SafetyLevel = SafetyLevel.MEDIUM,
        strict_mode: bool = False,
        log_safety_events: bool = True,
        blocked_response_template: Optional[Dict[str, Any]] = None,
        warn_response_template: Optional[Dict[str, Any]] = None
    ):
        self.enable_content_safety = enable_content_safety
        self.enable_authorization = enable_authorization
        self.enable_behavior_monitoring = enable_behavior_monitoring
        self.enable_compliance_checking = enable_compliance_checking
        self.default_safety_level = default_safety_level
        self.strict_mode = strict_mode
        self.log_safety_events = log_safety_events
        
        # Default response templates
        self.blocked_response_template = blocked_response_template or {
            "error": "Content blocked by safety check",
            "message": "The requested content was blocked due to safety concerns",
            "safety_action": "block"
        }
        
        self.warn_response_template = warn_response_template or {
            "warning": "Content safety warning",
            "message": "The content triggered a safety warning but was allowed to proceed",
            "safety_action": "warn"
        }


class SafetyEvent:
    """Data class for safety events."""
    
    def __init__(
        self,
        event_type: str,
        severity: SafetyLevel,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        description: str = "",
        details: Optional[Dict[str, Any]] = None,
        action_taken: SafetyAction = SafetyAction.ALLOW,
        timestamp: Optional[datetime] = None
    ):
        self.event_type = event_type
        self.severity = severity
        self.agent_id = agent_id
        self.user_id = user_id
        self.description = description
        self.details = details or {}
        self.action_taken = action_taken
        self.timestamp = timestamp or datetime.utcnow()


class SafetyMiddleware(BaseHTTPMiddleware):
    """
    Safety Middleware for CoPilot Architecture.
    
    This middleware provides comprehensive safety checks for all requests and responses,
    including content safety validation, authorization checks, and integration with
    the existing safety systems.
    """
    
    def __init__(self, app, config: Optional[SafetyMiddlewareConfig] = None):
        super().__init__(app)
        self.config = config or SafetyMiddlewareConfig()
        
        # Initialize safety components
        self._agent_safety: Optional[AgentSafety] = None
        self._safety_config: Optional[SafetyConfig] = None
        
        # Paths that should skip safety checks
        self._skip_safety_paths = {
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/auth/login",
            "/api/auth/health",
            "/api/auth/status",
            "/api/auth/first-run",
            "/api/auth/first-run/setup",
            "/api/auth/register",
            "/api/auth/reset-password",
            "/api/auth/validate-session",
        }
        
        # Thread-safe data structures
        self._safety_events: List[SafetyEvent] = []
        
        logger.info("Safety Middleware initialized")
    
    async def _get_agent_safety(self) -> AgentSafety:
        """Get or initialize the Agent Safety service."""
        if self._agent_safety is None:
            safety_config = await self._get_safety_config()
            self._agent_safety = AgentSafety(config=safety_config)
            await self._agent_safety.initialize()
        return self._agent_safety
    
    async def _get_safety_config(self) -> SafetyConfig:
        """Get or initialize the Safety Configuration."""
        if self._safety_config is None:
            self._safety_config = SafetyConfig(
                name="safety_middleware",
                version="1.0.0",
                sensitivity_level=self.config.default_safety_level,
                enable_ml_filtering=True,
                enable_adaptive_learning=True,
                enable_real_time_scanning=True
            )
        return self._safety_config
    
    def _should_skip_safety_check(self, request: Request) -> bool:
        """Check if safety checks should be skipped for this request."""
        path = request.url.path
        
        # Skip paths in the skip list
        if path in self._skip_safety_paths:
            return True
        
        # Skip paths with certain prefixes
        for prefix in ["/static/", "/public/", "/api/health/"]:
            if path.startswith(prefix):
                return True
        
        # Skip OPTIONS requests
        if request.method.upper() == "OPTIONS":
            return True
        
        return False
    
    async def _extract_request_content(self, request: Request) -> Dict[str, Any]:
        """Extract content from the request for safety checking."""
        content = {
            "path": request.url.path,
            "method": request.method,
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
        }
        
        # Try to extract body content
        import json
        try:
            if request.method.upper() in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    content["body_size"] = len(body)
                    # For JSON requests, try to parse the body
                    if "application/json" in request.headers.get("content-type", ""):
                        try:
                            content["body"] = json.loads(body.decode("utf-8"))
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # If parsing fails, just store the raw body
                            content["raw_body"] = body.decode("utf-8", errors="replace")
        except Exception as e:
            logger.warning(f"Failed to extract request content: {e}")
        
        return content
    
    async def _check_content_safety(
        self, 
        content: Dict[str, Any], 
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> ValidationResult:
        """Check content safety using the Agent Safety service."""
        if not self.config.enable_content_safety:
            # Return a safe result if content safety is disabled
            return ValidationResult(
                is_safe=True,
                confidence=1.0,
                risk_level=RiskLevel.SAFE
            )
        
        try:
            agent_safety = await self._get_agent_safety()
            
            # Convert content to string for safety checking
            content_str = str(content)
            
            # Check content safety
            result = await agent_safety.check_content_safety(
                content=content_str,
                agent_id=agent_id or "unknown"
            )
            
            return result
        except Exception as e:
            logger.error(f"Error in content safety check: {e}")
            # In strict mode, treat errors as unsafe
            if self.config.strict_mode:
                return ValidationResult(
                    is_safe=False,
                    confidence=0.0,
                    risk_level=RiskLevel.CRITICAL_RISK,
                    violations=["Content safety check failed"]
                )
            else:
                # In non-strict mode, allow content but log the error
                return ValidationResult(
                    is_safe=True,
                    confidence=0.5,
                    risk_level=RiskLevel.MEDIUM_RISK,
                    violations=["Content safety check failed - allowed due to non-strict mode"]
                )
    
    async def _check_authorization(
        self, 
        request: Request, 
        resource: str, 
        action: str
    ) -> bool:
        """Check authorization for the requested resource and action."""
        if not self.config.enable_authorization:
            return True
        
        try:
            # Get current user from request
            user = await get_current_user(request)
            user_id = user.get("id") if user else None
            user_roles = user.get("roles", []) if user else []
            
            # Simple role-based authorization
            # In a real implementation, this would be more sophisticated
            if "admin" in user_roles:
                return True
            
            # For now, allow all authenticated users
            if user_id:
                return True
            
            return False
        except HTTPException:
            # If authentication is required but fails, deny access
            return False
        except Exception as e:
            logger.error(f"Error in authorization check: {e}")
            # In strict mode, deny access on errors
            if self.config.strict_mode:
                return False
            else:
                # In non-strict mode, allow access but log the error
                return True
    
    async def _determine_safety_action(self, validation_result: ValidationResult) -> SafetyAction:
        """Determine the appropriate safety action based on validation result."""
        if validation_result.is_safe:
            return SafetyAction.ALLOW
        
        # Determine action based on risk level
        if validation_result.risk_level == RiskLevel.CRITICAL_RISK:
            return SafetyAction.BLOCK
        elif validation_result.risk_level == RiskLevel.HIGH_RISK:
            return SafetyAction.BLOCK if self.config.strict_mode else SafetyAction.WARN
        elif validation_result.risk_level == RiskLevel.MEDIUM_RISK:
            return SafetyAction.WARN
        else:
            return SafetyAction.ALLOW
    
    async def _create_safety_response(
        self,
        action: SafetyAction,
        validation_result: ValidationResult,
        request: Request
    ) -> Optional[JSONResponse]:
        """Create a response based on the safety action."""
        if action == SafetyAction.ALLOW:
            # Allow the request to proceed
            return None
        
        if action == SafetyAction.BLOCK:
            response_data = self.config.blocked_response_template.copy()
            response_data["violations"] = validation_result.violations
            response_data["risk_level"] = validation_result.risk_level.value
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=response_data
            )
        
        if action == SafetyAction.WARN:
            response_data = self.config.warn_response_template.copy()
            response_data["violations"] = validation_result.violations
            response_data["risk_level"] = validation_result.risk_level.value
            
            # Log the warning but allow the request to proceed
            # The actual response will be created by the next middleware/handler
            # We'll just add a warning header
            return None
        
        # For other actions, block the request
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "Safety action not supported"}
        )
    
    async def _log_safety_event(
        self,
        event_type: str,
        severity: SafetyLevel,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        description: str = "",
        details: Optional[Dict[str, Any]] = None,
        action_taken: SafetyAction = SafetyAction.ALLOW
    ) -> None:
        """Log a safety event."""
        if not self.config.log_safety_events:
            return
        
        event = SafetyEvent(
            event_type=event_type,
            severity=severity,
            agent_id=agent_id,
            user_id=user_id,
            description=description,
            details=details,
            action_taken=action_taken
        )
        
        self._safety_events.append(event)
        
        # Keep only the last 1000 events
        if len(self._safety_events) > 1000:
            self._safety_events = self._safety_events[-1000:]
        
        # Log the event
        log_method = logger.info
        if severity == SafetyLevel.CRITICAL:
            log_method = logger.critical
        elif severity == SafetyLevel.HIGH:
            log_method = logger.error
        elif severity == SafetyLevel.MEDIUM:
            log_method = logger.warning
        
        log_method(
            f"SAFETY EVENT: {event_type} - {description}",
            extra={
                "event_type": event_type,
                "severity": severity.value,
                "agent_id": agent_id,
                "user_id": user_id,
                "action_taken": action_taken.value,
                "details": details
            }
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch method."""
        start_time = time.time()
        
        # Skip safety checks for certain paths
        if self._should_skip_safety_check(request):
            return await call_next(request)
        
        try:
            # Extract request content for safety checking
            request_content = await self._extract_request_content(request)
            
            # Get user information if available
            user_id = None
            try:
                user = await get_current_user(request)
                user_id = user.get("id") if user else None
            except HTTPException:
                # User is not authenticated
                pass
            
            # Check content safety
            safety_result = await self._check_content_safety(
                content=request_content,
                user_id=user_id
            )
            
            # Determine safety action
            safety_action = await self._determine_safety_action(safety_result)
            
            # Log safety event
            await self._log_safety_event(
                event_type="content_safety_check",
                severity=SafetyLevel.HIGH if not safety_result.is_safe else SafetyLevel.LOW,
                user_id=user_id,
                description=f"Content safety check: {safety_action.value}",
                details={
                    "path": request.url.path,
                    "method": request.method,
                    "is_safe": safety_result.is_safe,
                    "risk_level": safety_result.risk_level.value,
                    "violations": safety_result.violations
                },
                action_taken=safety_action
            )
            
            # Create safety response if needed
            safety_response = await self._create_safety_response(
                action=safety_action,
                validation_result=safety_result,
                request=request
            )
            
            if safety_response:
                return safety_response
            
            # If safety checks passed, process the request
            response = await call_next(request)
            
            # Add safety headers to response
            response.headers["X-Safety-Checked"] = "true"
            response.headers["X-Safety-Action"] = safety_action.value
            
            # Log processing time
            processing_time = time.time() - start_time
            if processing_time > 1.0:  # Log slow requests
                logger.info(
                    f"Slow safety middleware processing: {request.url.path} took {processing_time:.2f}s"
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in Safety Middleware: {e}")
            
            # In strict mode, return an error response
            if self.config.strict_mode:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"error": "Internal safety check error"}
                )
            
            # In non-strict mode, allow the request to proceed but log the error
            return await call_next(request)
    
    def get_safety_events(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
        severity: Optional[SafetyLevel] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get safety events with optional filtering.
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type
            severity: Filter by severity level
            user_id: Filter by user ID
            agent_id: Filter by agent ID
            
        Returns:
            List of safety event dictionaries
        """
        events = self._safety_events.copy()
        
        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        
        # Sort by timestamp (newest first)
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Apply limit
        if limit:
            events = events[:limit]
        
        # Convert to dictionaries
        return [
            {
                "event_type": event.event_type,
                "severity": event.severity.value,
                "agent_id": event.agent_id,
                "user_id": event.user_id,
                "description": event.description,
                "details": event.details,
                "action_taken": event.action_taken.value,
                "timestamp": event.timestamp.isoformat()
            }
            for event in events
        ]
    
    def clear_safety_events(self) -> None:
        """Clear all safety events."""
        self._safety_events.clear()
        logger.info("Safety events cleared")