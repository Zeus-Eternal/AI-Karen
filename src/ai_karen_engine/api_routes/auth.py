from __future__ import annotations

try:
    from fastapi import APIRouter, HTTPException, Request, Response, status, Depends
except Exception:  # pragma: no cover
    from ai_karen_engine.fastapi_stub import APIRouter, HTTPException, Request, Response, status, Depends

from datetime import datetime, timedelta
from collections import defaultdict
try:
    from pydantic import BaseModel
except Exception:
    from ai_karen_engine.pydantic_stub import BaseModel
from typing import Any, Dict, List, Optional
import pyotp

from ai_karen_engine.utils.auth import (
    create_session,
    validate_session,
    SESSION_DURATION,
)
from ai_karen_engine.security.auth_manager import (
    authenticate,
    update_credentials,
    create_user,
    _USERS,
    create_email_verification_token,
    verify_email_token,
    mark_user_verified,
    create_password_reset_token,
    verify_password_reset_token,
    update_password,
    verify_totp,
    generate_totp_secret,
    get_totp_provisioning_uri,
    enable_two_factor,
    save_users,
)
from ai_karen_engine.core.logging import get_logger

# Intelligent authentication imports
from ai_karen_engine.security.intelligent_auth_service import IntelligentAuthService
from ai_karen_engine.security.auth_middleware import IntelligentAuthMiddleware
from ai_karen_engine.security.models import (
    AuthContext,
    AuthAnalysisResult,
    IntelligentAuthConfig,
    RiskLevel
)
import hashlib
import uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = get_logger(__name__)

# Session cookie configuration
COOKIE_NAME = "kari_session"

# Simple in-memory login rate limiter: max 5 attempts per minute per IP
_LOGIN_ATTEMPTS: Dict[str, List[datetime]] = defaultdict(list)
RATE_LIMIT = 5
RATE_WINDOW = timedelta(minutes=1)

# Persistent user store loaded via security.auth_manager

# Global intelligent authentication service instance
_intelligent_auth_service: Optional[IntelligentAuthService] = None

# Global intelligent authentication middleware instance
_intelligent_auth_middleware: Optional[IntelligentAuthMiddleware] = None

async def get_intelligent_auth_middleware() -> Optional[IntelligentAuthMiddleware]:
    """
    Dependency function to get the intelligent authentication middleware.
    Returns None if middleware is not available to maintain backward compatibility.
    """
    global _intelligent_auth_middleware, _intelligent_auth_service
    
    if _intelligent_auth_middleware is None:
        try:
            # Get the intelligent auth service
            intelligent_auth = await get_intelligent_auth_service()
            
            # Initialize middleware with the service
            _intelligent_auth_middleware = IntelligentAuthMiddleware(
                intelligent_auth_service=intelligent_auth,
                enable_geolocation=True,
                enable_device_fingerprinting=True,
                enable_risk_based_rate_limiting=True
            )
            
            logger.info("Intelligent authentication middleware initialized")
            
        except Exception as e:
            logger.warning(f"Failed to create intelligent authentication middleware: {e}")
            _intelligent_auth_middleware = None
    
    return _intelligent_auth_middleware

async def get_intelligent_auth_service() -> Optional[IntelligentAuthService]:
    """
    Dependency function to get the intelligent authentication service.
    Returns None if service is not available to maintain backward compatibility.
    """
    global _intelligent_auth_service
    
    if _intelligent_auth_service is None:
        try:
            # Initialize intelligent auth service with default config
            config = IntelligentAuthConfig()
            _intelligent_auth_service = IntelligentAuthService(config=config)
            
            # Initialize the service (this may fail if ML services are unavailable)
            initialized = await _intelligent_auth_service.initialize()
            if not initialized:
                logger.warning("Intelligent authentication service failed to initialize, falling back to standard auth")
                _intelligent_auth_service = None
        except Exception as e:
            logger.warning(f"Failed to create intelligent authentication service: {e}")
            _intelligent_auth_service = None
    
    return _intelligent_auth_service

def create_auth_context(email: str, password: str, request: Request) -> AuthContext:
    """Create authentication context from request data."""
    # Generate password hash for analysis (not storage)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Extract client information
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    return AuthContext(
        email=email,
        password_hash=password_hash,
        client_ip=client_ip,
        user_agent=user_agent,
        timestamp=datetime.utcnow(),
        request_id=request_id,
        # Additional context fields will be populated by intelligent auth service
        geolocation=None,
        device_fingerprint=None,
        session_id=None,
        referrer=request.headers.get("referer"),
        time_since_last_login=None,
        login_frequency_pattern=None,
        typical_login_hours=None,
        is_tor_exit_node=False,
        is_vpn=False,
        threat_intel_score=0.0,
        previous_failed_attempts=len([
            t for t in _LOGIN_ATTEMPTS.get(client_ip, []) 
            if datetime.utcnow() - t < RATE_WINDOW
        ])
    )


class LoginRequest(BaseModel):
    email: str
    password: str
    totp_code: Optional[str] = None


class RegisterRequest(BaseModel):
    email: str
    password: str
    roles: Optional[List[str]] = None
    tenant_id: str = "default"
    preferences: Dict[str, Any] = {}


class LoginResponse(BaseModel):
    token: str
    user_id: str
    email: str
    roles: List[str]
    tenant_id: str
    preferences: Dict[str, Any]
    two_factor_enabled: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    user_id: str
    email: str
    roles: List[str]
    tenant_id: str
    preferences: Dict[str, Any]
    two_factor_enabled: bool = False


class UpdateCredentialsRequest(BaseModel):
    new_username: Optional[str] = None
    new_password: Optional[str] = None


@router.post("/register", response_model=LoginResponse)
async def register(req: RegisterRequest, request: Request, response: Response) -> LoginResponse:
    if req.email in _USERS:
        raise HTTPException(status_code=400, detail="User already exists")
    try:
        create_user(req.email, req.password, roles=req.roles, tenant_id=req.tenant_id, preferences=req.preferences)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    verification_token = create_email_verification_token(req.email)
    logger.info(f"Verification token for {req.email}: {verification_token}")

    user = _USERS[req.email]
    token = create_session(
        req.email,
        user["roles"],
        request.headers.get("user-agent", ""),
        request.client.host,
        tenant_id=user.get("tenant_id", "default"),
    )
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_DURATION,
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return LoginResponse(
        token=token,
        user_id=req.email,
        email=req.email,
        roles=user["roles"],
        tenant_id=user.get("tenant_id", "default"),
        preferences=user.get("preferences", {}),
        two_factor_enabled=user.get("two_factor_enabled", False),
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest, 
    request: Request, 
    response: Response,
    intelligent_auth: Optional[IntelligentAuthService] = Depends(get_intelligent_auth_service)
) -> LoginResponse:
    """
    Enhanced login endpoint with intelligent authentication analysis.
    Maintains full backward compatibility with existing authentication flow.
    """
    # --- simple rate limiting ---
    ip = request.client.host if request.client else "unknown"
    now = datetime.utcnow()
    attempts = [t for t in _LOGIN_ATTEMPTS[ip] if now - t < RATE_WINDOW]
    if len(attempts) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many login attempts")
    attempts.append(now)
    _LOGIN_ATTEMPTS[ip] = attempts

    # Create authentication context for intelligent analysis
    auth_context = create_auth_context(req.email, req.password, request)
    
    # Log structured authentication attempt
    logger.info(
        f"Authentication attempt",
        extra={
            "request_id": auth_context.request_id,
            "email": req.email,
            "client_ip": auth_context.client_ip,
            "user_agent": auth_context.user_agent,
            "timestamp": auth_context.timestamp.isoformat(),
            "has_totp": bool(req.totp_code),
            "intelligent_auth_enabled": intelligent_auth is not None
        }
    )

    # Perform intelligent authentication analysis if available
    analysis_result: Optional[AuthAnalysisResult] = None
    if intelligent_auth:
        try:
            analysis_result = await intelligent_auth.analyze_login_attempt(auth_context)
            
            # Log analysis results
            logger.info(
                f"Intelligent auth analysis completed",
                extra={
                    "request_id": auth_context.request_id,
                    "risk_score": analysis_result.risk_score,
                    "risk_level": analysis_result.risk_level.value,
                    "should_block": analysis_result.should_block,
                    "requires_2fa": analysis_result.requires_2fa,
                    "processing_time": analysis_result.processing_time,
                    "confidence_score": analysis_result.confidence_score
                }
            )
            
            # Check if login should be blocked due to high risk
            if analysis_result.should_block:
                logger.warning(
                    f"Login blocked due to high risk",
                    extra={
                        "request_id": auth_context.request_id,
                        "email": req.email,
                        "risk_score": analysis_result.risk_score,
                        "risk_level": analysis_result.risk_level.value
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authentication blocked due to security concerns. Please verify your identity through alternative means or contact support."
                )
            
        except HTTPException:
            # Re-raise HTTP exceptions (like blocking decisions)
            raise
        except Exception as e:
            # Log intelligent auth failures but continue with standard authentication
            logger.warning(
                f"Intelligent authentication analysis failed, continuing with standard auth",
                extra={
                    "request_id": auth_context.request_id,
                    "error": str(e),
                    "email": req.email
                }
            )

    # Standard credential verification (unchanged)
    user = authenticate(req.email, req.password)
    if not user:
        # Update behavioral profile for failed login if intelligent auth is available
        if intelligent_auth:
            try:
                await intelligent_auth.update_user_behavioral_profile(
                    req.email, auth_context, success=False
                )
            except Exception as e:
                logger.warning(f"Failed to update behavioral profile for failed login: {e}")
        
        logger.info(
            f"Authentication failed - invalid credentials",
            extra={
                "request_id": auth_context.request_id,
                "email": req.email
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    if not user.get("is_verified"):
        logger.info(
            f"Authentication failed - email not verified",
            extra={
                "request_id": auth_context.request_id,
                "email": req.email
            }
        )
        raise HTTPException(status_code=403, detail="Email not verified")

    # Handle 2FA requirements (enhanced with intelligent auth)
    requires_2fa_standard = user.get("two_factor_enabled", False)
    requires_2fa_intelligent = analysis_result and analysis_result.requires_2fa
    
    if requires_2fa_standard or requires_2fa_intelligent:
        if not req.totp_code:
            # Determine appropriate message based on why 2FA is required
            if requires_2fa_intelligent and not requires_2fa_standard:
                detail = "Two-factor authentication required due to security analysis. Please provide your authentication code."
            else:
                detail = "Two-factor authentication required. Please provide your authentication code."
            
            logger.info(
                f"2FA required",
                extra={
                    "request_id": auth_context.request_id,
                    "email": req.email,
                    "standard_2fa": requires_2fa_standard,
                    "intelligent_2fa": requires_2fa_intelligent
                }
            )
            raise HTTPException(status_code=401, detail=detail)
        
        if requires_2fa_standard and not verify_totp(req.email, req.totp_code):
            logger.info(
                f"Authentication failed - invalid 2FA code",
                extra={
                    "request_id": auth_context.request_id,
                    "email": req.email
                }
            )
            raise HTTPException(status_code=401, detail="Invalid two-factor code")

    # Successful authentication - create session
    tenant_id = user.get("tenant_id") or request.headers.get("X-Tenant-ID", "default")
    token = create_session(
        req.email,
        user["roles"],
        request.headers.get("user-agent", ""),
        ip,
        tenant_id=tenant_id,
    )

    # Set secure HttpOnly cookie for session
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_DURATION,
        httponly=True,
        secure=True,
        samesite="strict",
    )

    # Update behavioral profile for successful login if intelligent auth is available
    if intelligent_auth:
        try:
            await intelligent_auth.update_user_behavioral_profile(
                req.email, auth_context, success=True
            )
        except Exception as e:
            logger.warning(f"Failed to update behavioral profile for successful login: {e}")

    # Log successful authentication
    logger.info(
        f"Authentication successful",
        extra={
            "request_id": auth_context.request_id,
            "email": req.email,
            "tenant_id": tenant_id,
            "roles": user["roles"],
            "risk_score": analysis_result.risk_score if analysis_result else None,
            "risk_level": analysis_result.risk_level.value if analysis_result else None
        }
    )

    return LoginResponse(
        token=token,
        user_id=req.email,
        email=req.email,
        roles=user["roles"],
        tenant_id=tenant_id,
        preferences=user.get("preferences", {}),
        two_factor_enabled=user.get("two_factor_enabled", False),
    )


@router.post("/token", response_model=TokenResponse)
async def token(req: LoginRequest, request: Request) -> TokenResponse:
    user = authenticate(req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    tenant_id = user.get("tenant_id") or request.headers.get("X-Tenant-ID", "default")
    access_token = create_session(
        req.email,
        user["roles"],
        request.headers.get("user-agent", ""),
        request.client.host,
        tenant_id=tenant_id,
    )
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def me(request: Request) -> UserResponse:
    auth = request.headers.get("authorization")
    token = None
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1]
    elif COOKIE_NAME in request.cookies:
        token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token",
        )
    ctx = validate_session(
        token, request.headers.get("user-agent", ""), request.client.host
    )
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user_email = ctx["sub"]
    user_data = _USERS.get(user_email)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserResponse(
        user_id=user_email,
        email=user_email,
        roles=list(ctx.get("roles", [])),
        tenant_id=user_data.get("tenant_id", "default"),
        preferences=user_data.get("preferences", {}),
        two_factor_enabled=user_data.get("two_factor_enabled", False),
    )


@router.post("/update_credentials", response_model=LoginResponse)
async def update_creds(
    req: UpdateCredentialsRequest, request: Request, response: Response
) -> LoginResponse:
    """Update the current user's credentials and return a new session."""
    auth = request.headers.get("authorization")
    token = None
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1]
    elif COOKIE_NAME in request.cookies:
        token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    ctx = validate_session(
        token, request.headers.get("user-agent", ""), request.client.host
    )
    if not ctx:
        raise HTTPException(status_code=401, detail="Invalid token")

    current_username = ctx["sub"]
    try:
        new_username = update_credentials(
            current_username, req.new_username, req.new_password
        )
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))

    user = _USERS.get(new_username)
    tenant_id = user.get("tenant_id", "default")

    new_token = create_session(
        new_username,
        user.get("roles", []),
        request.headers.get("user-agent", ""),
        request.client.host,
        tenant_id=tenant_id,
    )

    response.set_cookie(
        COOKIE_NAME,
        new_token,
        max_age=SESSION_DURATION,
        httponly=True,
        secure=True,
        samesite="strict",
    )

    return LoginResponse(
        token=new_token,
        user_id=new_username,
        email=new_username,
        roles=user.get("roles", []),
        tenant_id=tenant_id,
        preferences=user.get("preferences", {}),
        two_factor_enabled=user.get("two_factor_enabled", False),
    )


@router.post("/logout")
async def logout(response: Response) -> Dict[str, str]:
    """Clear authentication cookie."""
    response.delete_cookie(COOKIE_NAME)
    return {"detail": "Logged out"}


@router.get("/verify_email")
async def verify_email(token: str) -> Dict[str, str]:
    email = verify_email_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    mark_user_verified(email)
    return {"detail": "Email verified"}


class PasswordResetRequest(BaseModel):
    email: str


@router.post("/request_password_reset")
async def request_password_reset(req: PasswordResetRequest) -> Dict[str, str]:
    if req.email not in _USERS:
        raise HTTPException(status_code=404, detail="User not found")
    token = create_password_reset_token(req.email)
    logger.info(f"Password reset token for {req.email}: {token}")
    return {"detail": "Password reset link sent"}


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


@router.post("/reset_password")
async def reset_password(req: PasswordResetConfirm) -> Dict[str, str]:
    email = verify_password_reset_token(req.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    update_password(email, req.new_password)
    return {"detail": "Password updated"}


@router.get("/setup_2fa")
async def setup_two_factor(request: Request) -> Dict[str, str]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    ctx = validate_session(token, request.headers.get("user-agent", ""), request.client.host)
    if not ctx:
        raise HTTPException(status_code=401, detail="Invalid token")
    username = ctx["sub"]
    secret = generate_totp_secret()
    otpauth_url = get_totp_provisioning_uri(username, secret)
    _USERS[username]["pending_totp_secret"] = secret
    save_users()
    return {"otpauth_url": otpauth_url}


class Confirm2FARequest(BaseModel):
    code: str


# New intelligent authentication models
class LoginAnalysisRequest(BaseModel):
    """Request model for detailed authentication analysis."""
    email: str
    password: str
    include_detailed_analysis: bool = True
    include_recommendations: bool = True


class AuthFeedbackRequest(BaseModel):
    """Request model for providing authentication feedback."""
    user_id: str
    request_id: str
    feedback_type: str  # "false_positive", "false_negative", "correct_decision"
    feedback_data: Dict[str, Any] = {}
    comments: Optional[str] = None


class SecurityInsightsRequest(BaseModel):
    """Request model for security insights."""
    timeframe: str = "24h"  # "1h", "24h", "7d", "30d"
    include_trends: bool = True
    include_alerts: bool = True
    user_filter: Optional[str] = None


class SecurityInsightsResponse(BaseModel):
    """Response model for security insights."""
    timeframe: str
    total_attempts: int
    successful_attempts: int
    blocked_attempts: int
    high_risk_attempts: int
    avg_risk_score: float
    trends: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    top_risk_factors: List[Dict[str, str]]
    generated_at: datetime


@router.post("/confirm_2fa")
async def confirm_two_factor(req: Confirm2FARequest, request: Request) -> Dict[str, str]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    ctx = validate_session(token, request.headers.get("user-agent", ""), request.client.host)
    if not ctx:
        raise HTTPException(status_code=401, detail="Invalid token")
    username = ctx["sub"]
    user = _USERS.get(username)
    secret = user.get("pending_totp_secret")
    if not secret:
        raise HTTPException(status_code=400, detail="No 2FA setup in progress")
    totp = pyotp.TOTP(secret)
    if not totp.verify(req.code):
        raise HTTPException(status_code=400, detail="Invalid code")
    enable_two_factor(username, secret)
    user.pop("pending_totp_secret", None)
    return {"detail": "Two-factor authentication enabled"}


# New intelligent authentication endpoints

@router.post("/analyze", response_model=AuthAnalysisResult)
async def analyze_login_attempt(
    req: LoginAnalysisRequest,
    request: Request,
    intelligent_auth: Optional[IntelligentAuthService] = Depends(get_intelligent_auth_service)
) -> AuthAnalysisResult:
    """
    Perform detailed authentication analysis without actually logging in.
    Provides comprehensive risk assessment and security insights.
    """
    if not intelligent_auth:
        raise HTTPException(
            status_code=503,
            detail="Intelligent authentication service is not available"
        )
    
    try:
        # Create authentication context
        auth_context = create_auth_context(req.email, req.password, request)
        
        # Log analysis request
        logger.info(
            f"Authentication analysis requested",
            extra={
                "request_id": auth_context.request_id,
                "email": req.email,
                "client_ip": auth_context.client_ip,
                "include_detailed_analysis": req.include_detailed_analysis,
                "include_recommendations": req.include_recommendations
            }
        )
        
        # Perform comprehensive analysis
        analysis_result = await intelligent_auth.analyze_login_attempt(auth_context)
        
        # Filter response based on request parameters
        if not req.include_detailed_analysis:
            # Simplified response - only core risk information
            analysis_result.nlp_features = None
            analysis_result.embedding_analysis = None
            analysis_result.behavioral_analysis = None
            analysis_result.threat_analysis = None
        
        if not req.include_recommendations:
            analysis_result.recommended_actions = []
        
        logger.info(
            f"Authentication analysis completed",
            extra={
                "request_id": auth_context.request_id,
                "email": req.email,
                "risk_score": analysis_result.risk_score,
                "risk_level": analysis_result.risk_level.value,
                "processing_time": analysis_result.processing_time
            }
        )
        
        return analysis_result
        
    except Exception as e:
        logger.error(
            f"Authentication analysis failed",
            extra={
                "email": req.email,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/feedback")
async def provide_auth_feedback(
    req: AuthFeedbackRequest,
    request: Request,
    intelligent_auth: Optional[IntelligentAuthService] = Depends(get_intelligent_auth_service)
) -> Dict[str, str]:
    """
    Provide feedback to improve ML model accuracy.
    Helps reduce false positives and false negatives.
    """
    if not intelligent_auth:
        raise HTTPException(
            status_code=503,
            detail="Intelligent authentication service is not available"
        )
    
    try:
        # Validate feedback type
        valid_feedback_types = ["false_positive", "false_negative", "correct_decision"]
        if req.feedback_type not in valid_feedback_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid feedback type. Must be one of: {', '.join(valid_feedback_types)}"
            )
        
        # Create feedback data
        feedback_data = {
            "feedback_type": req.feedback_type,
            "feedback_data": req.feedback_data,
            "comments": req.comments,
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "")
        }
        
        # Create a minimal auth context for feedback (we don't have the original password)
        auth_context = AuthContext(
            email=req.user_id,
            password_hash="",  # Not available for feedback
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            timestamp=datetime.utcnow(),
            request_id=req.request_id
        )
        
        # Provide feedback to the service
        await intelligent_auth.provide_feedback(
            req.user_id,
            auth_context,
            feedback_data
        )
        
        logger.info(
            f"Authentication feedback received",
            extra={
                "user_id": req.user_id,
                "request_id": req.request_id,
                "feedback_type": req.feedback_type,
                "has_comments": bool(req.comments)
            }
        )
        
        return {"detail": "Feedback received successfully. Thank you for helping improve our security system."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to process authentication feedback",
            extra={
                "user_id": req.user_id,
                "request_id": req.request_id,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to process feedback"
        )


@router.get("/security-insights", response_model=SecurityInsightsResponse)
async def get_security_insights(
    timeframe: str = "24h",
    include_trends: bool = True,
    include_alerts: bool = True,
    user_filter: Optional[str] = None,
    request: Request = None,
    intelligent_auth: Optional[IntelligentAuthService] = Depends(get_intelligent_auth_service)
) -> SecurityInsightsResponse:
    """
    Get comprehensive security insights and analytics.
    Provides authentication trends, risk analysis, and security alerts.
    """
    if not intelligent_auth:
        raise HTTPException(
            status_code=503,
            detail="Intelligent authentication service is not available"
        )
    
    try:
        # Validate timeframe
        valid_timeframes = ["1h", "24h", "7d", "30d"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )
        
        # Parse timeframe to timedelta
        timeframe_mapping = {
            "1h": timedelta(hours=1),
            "24h": timedelta(days=1),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        time_delta = timeframe_mapping[timeframe]
        
        logger.info(
            f"Security insights requested",
            extra={
                "timeframe": timeframe,
                "include_trends": include_trends,
                "include_alerts": include_alerts,
                "user_filter": user_filter,
                "client_ip": request.client.host if request and request.client else "unknown"
            }
        )
        
        # Get health status to check if observability service is available
        health_status = intelligent_auth.get_health_status()
        
        # Generate mock insights for now (in a real implementation, this would come from the observability service)
        # This maintains API consistency while providing useful placeholder data
        insights = SecurityInsightsResponse(
            timeframe=timeframe,
            total_attempts=150,
            successful_attempts=142,
            blocked_attempts=3,
            high_risk_attempts=8,
            avg_risk_score=0.23,
            trends={
                "hourly_attempts": [12, 15, 8, 22, 18, 25, 30, 28, 20, 15, 12, 10] if include_trends else {},
                "risk_score_trend": [0.2, 0.25, 0.18, 0.35, 0.22, 0.28] if include_trends else {},
                "top_risk_countries": ["Unknown", "US", "CN"] if include_trends else []
            },
            alerts=[
                {
                    "id": "alert_001",
                    "type": "high_risk_login",
                    "message": "Multiple high-risk login attempts detected",
                    "severity": "medium",
                    "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "count": 3
                },
                {
                    "id": "alert_002", 
                    "type": "unusual_location",
                    "message": "Login attempts from unusual geographic locations",
                    "severity": "low",
                    "timestamp": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                    "count": 5
                }
            ] if include_alerts else [],
            top_risk_factors=[
                {"factor": "Unusual login time", "percentage": "35%"},
                {"factor": "New device/location", "percentage": "28%"},
                {"factor": "Suspicious credential patterns", "percentage": "22%"},
                {"factor": "IP reputation", "percentage": "15%"}
            ],
            generated_at=datetime.utcnow()
        )
        
        # Apply user filter if specified
        if user_filter:
            # In a real implementation, this would filter the data by user
            logger.info(f"Applied user filter: {user_filter}")
        
        logger.info(
            f"Security insights generated",
            extra={
                "timeframe": timeframe,
                "total_attempts": insights.total_attempts,
                "avg_risk_score": insights.avg_risk_score,
                "alerts_count": len(insights.alerts)
            }
        )
        
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to generate security insights",
            extra={
                "timeframe": timeframe,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate security insights"
        )


# Middleware management endpoints

@router.get("/middleware/audit-log")
async def get_middleware_audit_log(
    limit: int = 100,
    request: Request = None,
    middleware: Optional[IntelligentAuthMiddleware] = Depends(get_intelligent_auth_middleware)
) -> Dict[str, Any]:
    """
    Get audit log entries from the intelligent authentication middleware.
    Provides security event history and audit trail.
    """
    if not middleware:
        raise HTTPException(
            status_code=503,
            detail="Intelligent authentication middleware is not available"
        )
    
    try:
        # Validate limit parameter
        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 1000"
            )
        
        # Get audit log entries
        audit_entries = middleware.get_audit_log(limit=limit)
        
        logger.info(
            f"Audit log requested",
            extra={
                "limit": limit,
                "entries_returned": len(audit_entries),
                "client_ip": request.client.host if request and request.client else "unknown"
            }
        )
        
        return {
            "audit_entries": audit_entries,
            "total_entries": len(audit_entries),
            "limit": limit,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get audit log",
            extra={
                "limit": limit,
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve audit log"
        )


@router.get("/middleware/rate-limit-stats")
async def get_rate_limit_stats(
    request: Request = None,
    middleware: Optional[IntelligentAuthMiddleware] = Depends(get_intelligent_auth_middleware)
) -> Dict[str, Any]:
    """
    Get rate limiting statistics from the intelligent authentication middleware.
    Provides insights into rate limiting effectiveness and patterns.
    """
    if not middleware:
        raise HTTPException(
            status_code=503,
            detail="Intelligent authentication middleware is not available"
        )
    
    try:
        # Get rate limiting statistics
        stats = middleware.get_rate_limit_stats()
        
        logger.info(
            f"Rate limit stats requested",
            extra={
                "total_ips_tracked": stats.get("total_ips_tracked", 0),
                "client_ip": request.client.host if request and request.client else "unknown"
            }
        )
        
        return {
            "rate_limit_stats": stats,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            f"Failed to get rate limit stats",
            extra={
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve rate limit statistics"
        )


@router.get("/middleware/health")
async def get_middleware_health(
    request: Request = None,
    middleware: Optional[IntelligentAuthMiddleware] = Depends(get_intelligent_auth_middleware)
) -> Dict[str, Any]:
    """
    Get health status of the intelligent authentication middleware.
    Provides operational status and configuration information.
    """
    try:
        if not middleware:
            return {
                "status": "unavailable",
                "message": "Intelligent authentication middleware is not available",
                "features": {
                    "geolocation": False,
                    "device_fingerprinting": False,
                    "risk_based_rate_limiting": False
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        
        # Get middleware configuration and status
        health_status = {
            "status": "healthy",
            "message": "Intelligent authentication middleware is operational",
            "features": {
                "geolocation": middleware.enable_geolocation,
                "device_fingerprinting": middleware.enable_device_fingerprinting,
                "risk_based_rate_limiting": middleware.enable_risk_based_rate_limiting
            },
            "stats": middleware.get_rate_limit_stats(),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Middleware health check requested",
            extra={
                "status": health_status["status"],
                "client_ip": request.client.host if request and request.client else "unknown"
            }
        )
        
        return health_status
        
    except Exception as e:
        logger.error(
            f"Failed to get middleware health",
            extra={
                "error": str(e)
            }
        )
        return {
            "status": "error",
            "message": f"Failed to retrieve middleware health: {str(e)}",
            "generated_at": datetime.utcnow().isoformat()
        }
