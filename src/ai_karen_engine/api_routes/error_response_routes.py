"""
Intelligent Error Response API Routes

This module provides API endpoints for generating intelligent error responses
using Karen's core LLM capabilities and provider health monitoring.
"""

import hashlib
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from ai_karen_engine.core.dependencies import get_current_user_context
from ai_karen_engine.core.logging import get_logger
from ai_karen_engine.services.error_response_service import (
    ErrorResponseService,
    IntelligentErrorResponse,
    ErrorContext,
    ErrorCategory,
    ErrorSeverity
)
from ai_karen_engine.services.provider_health_monitor import get_health_monitor

logger = get_logger(__name__)
router = APIRouter(tags=["error-response"], prefix="/error-response")

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# Global service instance
_error_response_service: Optional[ErrorResponseService] = None

# Response cache for common errors
_response_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl = 300  # 5 minutes


def get_error_response_service() -> ErrorResponseService:
    """Get or create the error response service instance"""
    global _error_response_service
    if _error_response_service is None:
        _error_response_service = ErrorResponseService()
    return _error_response_service


class ErrorAnalysisRequest(BaseModel):
    """Request model for error analysis"""
    error_message: str = Field(..., description="The error message to analyze")
    error_type: Optional[str] = Field(None, description="Optional error type or class name")
    status_code: Optional[int] = Field(None, description="Optional HTTP status code")
    provider_name: Optional[str] = Field(None, description="Optional provider name that caused the error")
    request_path: Optional[str] = Field(None, description="Optional request path where error occurred")
    user_context: Optional[Dict[str, Any]] = Field(None, description="Optional user context data")
    use_ai_analysis: bool = Field(True, description="Whether to use AI-powered analysis")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_message": "OpenAI API key not found",
                "error_type": "AuthenticationError",
                "status_code": 401,
                "provider_name": "openai",
                "request_path": "/api/chat",
                "use_ai_analysis": True
            }
        }
    )


class ErrorAnalysisResponse(BaseModel):
    """Response model for error analysis"""
    title: str = Field(..., description="Brief, user-friendly error title")
    summary: str = Field(..., description="Clear explanation of what went wrong")
    category: ErrorCategory = Field(..., description="Error category for classification")
    severity: ErrorSeverity = Field(..., description="Error severity level")
    next_steps: List[str] = Field(..., description="Actionable steps to resolve the issue")
    provider_health: Optional[Dict[str, Any]] = Field(None, description="Current provider health status")
    contact_admin: bool = Field(False, description="Whether user should contact admin")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retrying")
    help_url: Optional[str] = Field(None, description="URL to relevant documentation")
    technical_details: Optional[str] = Field(None, description="Technical details for debugging")
    cached: bool = Field(False, description="Whether response was served from cache")
    response_time_ms: float = Field(..., description="Response generation time in milliseconds")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "OpenAI API Key Missing",
                "summary": "The OpenAI API key is not configured in your environment.",
                "category": "api_key_missing",
                "severity": "high",
                "next_steps": [
                    "Add OPENAI_API_KEY to your .env file",
                    "Get your API key from https://platform.openai.com/api-keys",
                    "Restart the application after adding the key"
                ],
                "provider_health": {
                    "name": "openai",
                    "status": "unknown",
                    "success_rate": 0.95,
                    "response_time": 1200,
                    "last_check": "2024-01-15T10:30:00Z"
                },
                "contact_admin": False,
                "retry_after": None,
                "help_url": "https://platform.openai.com/docs/quickstart",
                "technical_details": "OPENAI_API_KEY environment variable not set",
                "cached": False,
                "response_time_ms": 150.5
            }
        }
    )


class ProviderHealthResponse(BaseModel):
    """Response model for provider health status"""
    providers: Dict[str, Dict[str, Any]] = Field(..., description="Health status for all providers")
    healthy_count: int = Field(..., description="Number of healthy providers")
    total_count: int = Field(..., description="Total number of monitored providers")
    last_updated: str = Field(..., description="Last update timestamp")


def _generate_cache_key(request: ErrorAnalysisRequest) -> str:
    """Generate cache key for error analysis request"""
    key_data = f"{request.error_message}:{request.error_type}:{request.status_code}:{request.provider_name}"
    return hashlib.md5(key_data.encode()).hexdigest()


def _get_cached_response(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached response if available and not expired"""
    if cache_key in _response_cache:
        cached_data = _response_cache[cache_key]
        cache_time = cached_data.get("timestamp", 0)
        
        if time.time() - cache_time < _cache_ttl:
            logger.debug(f"Serving cached response for key: {cache_key}")
            response_data = cached_data["response"].copy()
            response_data["cached"] = True
            return response_data
        else:
            # Remove expired cache entry
            del _response_cache[cache_key]
            logger.debug(f"Removed expired cache entry for key: {cache_key}")
    
    return None


def _cache_response(cache_key: str, response: Dict[str, Any]) -> None:
    """Cache response for future use"""
    _response_cache[cache_key] = {
        "response": response,
        "timestamp": time.time()
    }
    logger.debug(f"Cached response for key: {cache_key}")


@router.post("/analyze", response_model=ErrorAnalysisResponse)
@limiter.limit("30/minute")  # Rate limit: 30 requests per minute per IP
async def analyze_error(
    error_request: ErrorAnalysisRequest,
    request: Request,
    user_context: Optional[Dict[str, Any]] = Depends(get_current_user_context)
) -> ErrorAnalysisResponse:
    """
    Analyze an error and generate intelligent, actionable response
    
    This endpoint analyzes error messages using rule-based classification
    and AI-powered response generation to provide users with specific,
    actionable guidance for resolving issues.
    
    **Rate Limiting**: 30 requests per minute per IP address
    **Caching**: Common error patterns are cached for 5 minutes
    
    Args:
        request: Error analysis request with error details
        http_request: FastAPI request object for rate limiting
        user_context: Current user context from authentication
        
    Returns:
        ErrorAnalysisResponse with intelligent analysis and guidance
        
    Raises:
        HTTPException: 429 if rate limit exceeded, 500 for service errors
    """
    start_time = time.time()
    
    try:
        # Generate cache key for this request
        cache_key = _generate_cache_key(error_request)
        
        # Check cache first
        cached_response = _get_cached_response(cache_key)
        if cached_response:
            cached_response["response_time_ms"] = (time.time() - start_time) * 1000
            return ErrorAnalysisResponse(**cached_response)
        
        # Get error response service
        service = get_error_response_service()
        
        # Build additional context
        additional_context = {
            "user_id": user_context.get("user_id") if user_context else None,
            "tenant_id": user_context.get("tenant_id") if user_context else None,
            "request_path": error_request.request_path,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add user-provided context
        if error_request.user_context:
            additional_context.update(error_request.user_context)
        
        # Analyze the error
        logger.info(f"Analyzing error: {error_request.error_message[:100]}...")
        
        intelligent_response = service.analyze_error(
            error_message=error_request.error_message,
            error_type=error_request.error_type,
            status_code=error_request.status_code,
            provider_name=error_request.provider_name,
            additional_context=additional_context,
            use_ai_analysis=error_request.use_ai_analysis
        )
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Convert to response model
        response_data = {
            "title": intelligent_response.title,
            "summary": intelligent_response.summary,
            "category": intelligent_response.category,
            "severity": intelligent_response.severity,
            "next_steps": intelligent_response.next_steps,
            "provider_health": intelligent_response.provider_health,
            "contact_admin": intelligent_response.contact_admin,
            "retry_after": intelligent_response.retry_after,
            "help_url": intelligent_response.help_url,
            "technical_details": intelligent_response.technical_details,
            "cached": False,
            "response_time_ms": response_time_ms
        }
        
        # Cache the response for common errors
        if intelligent_response.category in [
            ErrorCategory.API_KEY_MISSING,
            ErrorCategory.API_KEY_INVALID,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.PROVIDER_DOWN,
            ErrorCategory.AUTHENTICATION
        ]:
            _cache_response(cache_key, response_data)
        
        logger.info(f"Generated error response in {response_time_ms:.1f}ms")
        
        return ErrorAnalysisResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error analysis failed: {e}", exc_info=True)
        
        # Return a fallback response
        response_time_ms = (time.time() - start_time) * 1000
        
        fallback_response = ErrorAnalysisResponse(
            title="Analysis Error",
            summary="Unable to analyze the error at this time.",
            category=ErrorCategory.SYSTEM_ERROR,
            severity=ErrorSeverity.MEDIUM,
            next_steps=[
                "Try again in a moment",
                "Contact admin if the problem persists"
            ],
            contact_admin=True,
            technical_details=f"Analysis service error: {str(e)}",
            cached=False,
            response_time_ms=response_time_ms
        )
        
        return fallback_response


@router.get("/provider-health", response_model=ProviderHealthResponse)
@limiter.limit("60/minute")  # Rate limit: 60 requests per minute per IP
async def get_provider_health(
    request: Request,
    user_context: Optional[Dict[str, Any]] = Depends(get_current_user_context)
) -> ProviderHealthResponse:
    """
    Get current health status for all monitored providers
    
    This endpoint returns the current health status of all AI providers
    being monitored by the system, including success rates, response times,
    and availability status.
    
    **Rate Limiting**: 60 requests per minute per IP address
    
    Args:
        request: FastAPI request object for rate limiting
        user_context: Current user context from authentication
        
    Returns:
        ProviderHealthResponse with health status for all providers
    """
    try:
        health_monitor = get_health_monitor()
        all_health = health_monitor.get_all_provider_health()
        
        # Convert health info to response format
        providers = {}
        healthy_count = 0
        
        for provider_name, health_info in all_health.items():
            providers[provider_name] = {
                "name": health_info.name,
                "status": health_info.status.value,
                "success_rate": health_info.success_rate,
                "response_time": health_info.response_time,
                "consecutive_failures": health_info.consecutive_failures,
                "last_check": health_info.last_check.isoformat() if health_info.last_check else None,
                "last_success": health_info.last_success.isoformat() if health_info.last_success else None,
                "last_failure": health_info.last_failure.isoformat() if health_info.last_failure else None,
                "error_message": health_info.error_message
            }
            
            if health_info.status.value == "healthy":
                healthy_count += 1
        
        return ProviderHealthResponse(
            providers=providers,
            healthy_count=healthy_count,
            total_count=len(providers),
            last_updated=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get provider health: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve provider health status"
        )


@router.post("/cache/clear")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute per IP
async def clear_response_cache(
    request: Request,
    user_context: Optional[Dict[str, Any]] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """
    Clear the error response cache
    
    This endpoint clears the cached error responses, forcing fresh analysis
    for all subsequent requests. Useful for testing or when provider status
    has changed significantly.
    
    **Rate Limiting**: 10 requests per minute per IP address
    **Authentication**: Requires valid user session
    
    Args:
        request: FastAPI request object for rate limiting
        user_context: Current user context from authentication
        
    Returns:
        Dictionary with cache clear status and statistics
    """
    try:
        global _response_cache
        
        # Get cache statistics before clearing
        cache_stats = {
            "entries_cleared": len(_response_cache),
            "cache_size_bytes": sum(
                len(str(entry)) for entry in _response_cache.values()
            ),
            "cleared_at": datetime.utcnow().isoformat()
        }
        
        # Clear the cache
        _response_cache.clear()
        
        # Also clear provider health cache
        health_monitor = get_health_monitor()
        health_monitor.clear_cache()
        
        logger.info(f"Error response cache cleared by user: {user_context.get('user_id', 'unknown')}")
        
        return {
            "success": True,
            "message": "Error response cache cleared successfully",
            "statistics": cache_stats
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear error response cache"
        )


@router.get("/cache/stats")
@limiter.limit("60/minute")  # Rate limit: 60 requests per minute per IP
async def get_cache_stats(
    request: Request,
    user_context: Optional[Dict[str, Any]] = Depends(get_current_user_context)
) -> Dict[str, Any]:
    """
    Get error response cache statistics
    
    This endpoint returns statistics about the error response cache,
    including hit rates, cache size, and provider health cache status.
    
    **Rate Limiting**: 60 requests per minute per IP address
    
    Args:
        request: FastAPI request object for rate limiting
        user_context: Current user context from authentication
        
    Returns:
        Dictionary with cache statistics and health information
    """
    try:
        # Get response cache stats
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        total_size = 0
        
        for cache_key, cache_data in _response_cache.items():
            cache_time = cache_data.get("timestamp", 0)
            total_size += len(str(cache_data))
            
            if current_time - cache_time < _cache_ttl:
                valid_entries += 1
            else:
                expired_entries += 1
        
        # Get provider health cache stats
        health_monitor = get_health_monitor()
        health_stats = health_monitor.get_cache_stats()
        
        return {
            "response_cache": {
                "total_entries": len(_response_cache),
                "valid_entries": valid_entries,
                "expired_entries": expired_entries,
                "cache_size_bytes": total_size,
                "cache_ttl_seconds": _cache_ttl
            },
            "provider_health_cache": health_stats,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache statistics"
        )


"""
Custom exception handler for rate limiting errors.

The original implementation attempted to register the handler using
``@router.exception_handler`` which is not supported by ``APIRouter`` in
FastAPI.  This caused an ``AttributeError`` during module import.  We instead
define the handler normally and register it with
``router.add_exception_handler`` after its definition.
"""


# Rate limit error handler
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors with intelligent response."""
    service = get_error_response_service()

    # Generate intelligent response for rate limiting
    intelligent_response = service.analyze_error(
        error_message="Rate limit exceeded for error analysis API",
        error_type="RateLimitExceeded",
        status_code=429,
        additional_context={
            "endpoint": str(request.url),
            "client_ip": get_remote_address(request),
            "retry_after": 60,
        },
        use_ai_analysis=False,  # Don't use AI for rate limit errors to avoid recursion
    )

    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "intelligent_response": {
                "title": intelligent_response.title,
                "summary": intelligent_response.summary,
                "next_steps": intelligent_response.next_steps,
                "retry_after": 60,
            },
            "detail": f"Rate limit exceeded: {exc.detail}",
        },
        headers={"Retry-After": "60"},
    )


# Register the custom rate limit handler with the router.
#
# Older versions of FastAPI's ``APIRouter`` exposed an ``add_exception_handler``
# method while newer versions provide an ``exception_handler`` decorator.  We
# support both to maintain compatibility across environments.
if hasattr(router, "add_exception_handler"):
    router.add_exception_handler(RateLimitExceeded, rate_limit_handler)  # type: ignore[attr-defined]
elif hasattr(router, "exception_handler"):
    router.exception_handler(RateLimitExceeded)(rate_limit_handler)  # type: ignore[attr-defined]


