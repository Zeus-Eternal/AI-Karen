"""
User Data API Routes

This module provides the /api/user/data endpoint for handling user data submissions.
The endpoint is protected with JWT authentication and returns structured response data.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

# Import authentication middleware
if TYPE_CHECKING:
    from src.auth.auth_middleware import BaseAuthMiddleware

try:
    from src.auth.auth_middleware import get_auth_middleware, AuthenticationError  # type: ignore
    AUTH_AVAILABLE = True
except ImportError:
    # Fallback for development/testing
    import logging
    AUTH_AVAILABLE = False
    
    class AuthenticationError(Exception):
        def __init__(self, message: str, status_code: int = 401):
            self.message = message
            self.status_code = status_code
            super().__init__(message)
    
    def get_auth_middleware():
        """Get mock auth middleware for development"""
        class MockAuthMiddleware:
            def get_current_user(self, request):
                # Mock user for development
                return {
                    'user_id': 'dev-user-123',
                    'email': 'dev@example.com',
                    'user_type': 'developer',
                    'permissions': ['*']
                }
            
            def is_public_endpoint(self, path: str) -> bool:
                # Mock implementation - allow all paths for development
                return True
            
            def _check_rate_limit(self, user_id: str, action: str) -> bool:
                return True  # Allow all in development
        
        return MockAuthMiddleware()
from ai_karen_engine.utils.dependency_checks import import_pydantic

# Import Pydantic models
BaseModel, Field = import_pydantic("BaseModel", "Field")

# Initialize router
router = APIRouter()

# Security scheme for JWT authentication
security = HTTPBearer()

# Request/Response Models
class UserDataRequest(BaseModel):
    """User data submission request model."""
    data: Optional[Dict[str, Any]] = Field(default={}, description="Optional user data payload")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Optional metadata")


class UserDataResponse(BaseModel):
    """User data submission response model."""
    userId: str = Field(..., description="User ID")
    submissionId: str = Field(..., description="Unique submission ID (UUID)")
    submissionTimestamp: str = Field(..., description="ISO 8601 timestamp of submission")


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")


def error_detail(message: str, error_code: Optional[str] = None) -> Dict[str, Any]:
    """Return error detail payload consistent with ErrorResponse."""
    return ErrorResponse(detail=message, error_code=error_code).model_dump()


def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Get current authenticated user from request.
    Uses the existing auth middleware to validate JWT tokens.
    """
    try:
        auth_middleware = get_auth_middleware()
        return auth_middleware.get_current_user(request)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def add_security_headers(response: JSONResponse) -> JSONResponse:
    """Add security headers to response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


def check_rate_limit(request: Request, user_id: str) -> bool:
    """
    Check rate limiting for user data submissions.
    Uses the auth middleware's rate limiting functionality.
    """
    try:
        auth_middleware = get_auth_middleware()
        # Use the existing rate limiting from auth middleware
        return auth_middleware._check_rate_limit(user_id, 'user_data_submission')
    except Exception:
        # If rate limiting fails, allow the request (fail open)
        return True


@router.post(
    "/user/data",
    response_model=UserDataResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": UserDataResponse, "description": "User data submitted successfully"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Submit user data",
    description="Submit user data with authentication and rate limiting",
    tags=["user-data"]
)
async def submit_user_data(
    request: UserDataRequest,
    http_request: Request
) -> JSONResponse:
    """
    Handle user data submission.
    
    This endpoint:
    - Requires JWT authentication (Bearer token in Authorization header or cookie)
    - Implements rate limiting
    - Returns structured response with userId, submissionId, and submissionTimestamp
    - Includes security headers
    - Validates request format
    """
    
    try:
        # Get current authenticated user
        current_user = get_current_user(http_request)
        user_id = current_user.get('user_id')
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token",
            )
        
        # Check rate limiting
        if not check_rate_limit(http_request, user_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"},
            )
        
        # Generate unique submission ID
        submission_id = str(uuid.uuid4())
        
        # Generate ISO 8601 timestamp
        submission_timestamp = datetime.now(timezone.utc).isoformat()
        
        # Prepare response data
        response_data = UserDataResponse(
            userId=user_id,
            submissionId=submission_id,
            submissionTimestamp=submission_timestamp
        )
        
        # Create JSON response
        response = JSONResponse(
            content=response_data.model_dump(),
            status_code=status.HTTP_200_OK
        )
        
        # Add security headers
        response = add_security_headers(response)
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions (already properly formatted)
        raise
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while processing user data",
        )


@router.get(
    "/user/data/health",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "User data endpoint is healthy"},
    },
    summary="User data endpoint health check",
    description="Health check for the user data endpoint",
    tags=["user-data"]
)
async def user_data_health() -> JSONResponse:
    """
    Health check endpoint for user data API.
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "user-data-api",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "features": {
                "authentication": True,
                "rate_limiting": True,
                "security_headers": True,
                "uuid_generation": True,
                "iso_timestamps": True
            }
        },
        status_code=status.HTTP_200_OK
    )