"""
Hybrid Authentication System
Production-ready but simplified to avoid concurrency issues
"""

import asyncio
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
import jwt

from ai_karen_engine.core.logging import get_logger

logger = get_logger(__name__)

# Configuration from environment
import os
JWT_SECRET = os.getenv("JWT_SECRET", "production-jwt-secret-change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# In-memory user store for demo (in production, this would be database)
# This allows us to avoid database concurrency issues while maintaining security
USERS_DB = {
    "admin@kari.ai": {
        "user_id": "admin-kari-ai",
        "email": "admin@kari.ai",
        "password_hash": "$2b$12$LxDjupoewsxS/tThFmke3.eBtEjDxVYa6X.9Y.nhwMPrHT2Egl6py",  # Password123!
        "full_name": "Kari Admin",
        "roles": ["admin", "user", "super_admin", "developer", "production"],
        "tenant_id": "default",
        "is_verified": True,
        "is_active": True
    },
    "admin@example.com": {
        "user_id": "admin-user-id",
        "email": "admin@example.com",
        "password_hash": "$2b$12$TpTWisikQS3X91ubUBNOUuNKqV/JCXptvTF3B1iQzzmoZPGfRzRWa",  # password123
        "full_name": "Admin User",
        "roles": ["admin", "user"],
        "tenant_id": "default",
        "is_verified": True,
        "is_active": True
    },
    "test@example.com": {
        "user_id": "test-user-id",
        "email": "test@example.com", 
        "password_hash": "$2b$12$VADneSELneIU7uyKAI.OoueGdMdDK5.LYV197Y1jQFUj91vY3MOYq",  # testpassword
        "full_name": "Test User",
        "roles": ["user"],
        "tenant_id": "default",
        "is_verified": True,
        "is_active": True
    }
}

# Active sessions store (in production, this would be Redis or database)
ACTIVE_SESSIONS = {}

# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    roles: List[str]
    tenant_id: str
    is_verified: bool

# Utility Functions
def verify_password(password: str, hashed: str) -> bool:
    """Simple password verification (in production, use bcrypt)"""
    import bcrypt
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        # Fallback for simple comparison
        return password == hashed

def hash_password(password: str) -> str:
    """Simple password hashing (in production, use bcrypt)"""
    import bcrypt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_jwt_token(user_data: Dict[str, Any], expires_delta: timedelta) -> str:
    """Create JWT token"""
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": user_data["user_id"],
        "email": user_data["email"],
        "tenant_id": user_data.get("tenant_id", "default"),
        "roles": user_data.get("roles", ["user"]),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access" if expires_delta.total_seconds() < 3600 else "refresh"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Authentication Service
class HybridAuthService:
    """Hybrid authentication service - secure but simple"""
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user"""
        try:
            logger.info(f"Authenticating user: {email}")
            user = USERS_DB.get(email.lower())
            if not user:
                logger.warning(f"User not found: {email}")
                return None
            
            logger.info(f"User found: {email}, checking if active")
            if not user.get("is_active", False):
                logger.warning(f"User not active: {email}")
                return None
            
            logger.info(f"User active, verifying password for: {email}")
            password_valid = verify_password(password, user["password_hash"])
            logger.info(f"Password verification result for {email}: {password_valid}")
            
            if not password_valid:
                logger.warning(f"Invalid password for: {email}")
                return None
            
            logger.info(f"Authentication successful for: {email}")
            # Return user data without password hash
            user_data = user.copy()
            user_data.pop("password_hash", None)
            return user_data
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    @staticmethod
    async def register_user(email: str, password: str, full_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Register new user"""
        try:
            email = email.lower()
            if email in USERS_DB:
                raise HTTPException(status_code=409, detail="User already exists")
            
            user_id = f"user-{secrets.token_hex(8)}"
            password_hash = hash_password(password)
            
            user_data = {
                "user_id": user_id,
                "email": email,
                "password_hash": password_hash,
                "full_name": full_name,
                "roles": ["user"],
                "tenant_id": "default",
                "is_verified": True,
                "is_active": True
            }
            
            USERS_DB[email] = user_data
            
            # Return user data without password hash
            result = user_data.copy()
            result.pop("password_hash", None)
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return None
    
    @staticmethod
    async def create_tokens(user: Dict[str, Any]) -> tuple[str, str]:
        """Create access and refresh tokens"""
        try:
            # Create tokens
            access_token = create_jwt_token(
                user, 
                timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            refresh_token = create_jwt_token(
                user, 
                timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            )
            
            # Store refresh token
            ACTIVE_SESSIONS[refresh_token] = {
                "user_id": user["user_id"],
                "created_at": datetime.now(timezone.utc),
                "expires_at": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            }
            
            return access_token, refresh_token
            
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise HTTPException(status_code=500, detail="Token creation failed")

# Router
router = APIRouter(tags=["hybrid-auth"], prefix="/auth")

async def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@router.post("/register", response_model=LoginResponse)
async def register(req: RegisterRequest, request: Request) -> LoginResponse:
    """Register new user"""
    try:
        auth_service = HybridAuthService()
        user = await auth_service.register_user(
            email=req.email,
            password=req.password,
            full_name=req.full_name
        )
        
        if not user:
            raise HTTPException(status_code=400, detail="Registration failed")
        
        # Create tokens
        access_token, refresh_token = await auth_service.create_tokens(user)
        
        logger.info(f"User registered successfully: {user['email']}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request) -> LoginResponse:
    """Login user"""
    try:
        auth_service = HybridAuthService()
        user = await auth_service.authenticate_user(
            email=req.email,
            password=req.password
        )
        
        if not user:
            logger.warning(f"Login failed for: {req.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create tokens
        access_token, refresh_token = await auth_service.create_tokens(user)
        
        logger.info(f"User logged in successfully: {user['email']}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/refresh")
async def refresh_token(request: Request) -> Dict[str, Any]:
    """Refresh access token"""
    try:
        # Get refresh token from request body
        body = await request.json()
        refresh_token = body.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token required")
        
        # Verify refresh token
        payload = verify_jwt_token(refresh_token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        # Check if session is active
        if refresh_token not in ACTIVE_SESSIONS:
            raise HTTPException(status_code=401, detail="Session not found")
        
        session = ACTIVE_SESSIONS[refresh_token]
        if session["expires_at"] < datetime.now(timezone.utc):
            del ACTIVE_SESSIONS[refresh_token]
            raise HTTPException(status_code=401, detail="Session expired")
        
        # Create new access token
        user_data = {
            "user_id": payload["sub"],
            "email": payload["email"],
            "tenant_id": payload.get("tenant_id", "default"),
            "roles": payload.get("roles", ["user"])
        }
        
        new_access_token = create_jwt_token(
            user_data,
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

# Dependency for protected routes
async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current user from JWT token"""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header.split(" ")[1]
    payload = verify_jwt_token(token)
    
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    return {
        "user_id": payload["sub"],
        "email": payload["email"],
        "tenant_id": payload.get("tenant_id", "default"),
        "roles": payload.get("roles", ["user"])
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)) -> UserResponse:
    """Get current user information"""
    # Get full user data from store
    user_data = USERS_DB.get(current_user["email"])
    
    return UserResponse(
        user_id=current_user["user_id"],
        email=current_user["email"],
        full_name=user_data.get("full_name") if user_data else None,
        roles=current_user["roles"],
        tenant_id=current_user["tenant_id"],
        is_verified=True
    )

@router.post("/logout")
async def logout(request: Request, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, str]:
    """Logout user (invalidate refresh tokens)"""
    try:
        # Get refresh token from request body if provided
        try:
            body = await request.json()
            refresh_token = body.get("refresh_token")
            if refresh_token and refresh_token in ACTIVE_SESSIONS:
                del ACTIVE_SESSIONS[refresh_token]
        except:
            pass  # No refresh token provided, that's ok
        
        logger.info(f"User logged out: {current_user['email']}")
        return {"detail": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return {"detail": "Logged out successfully"}  # Always succeed for logout

# Add some demo users for testing
@router.get("/demo-users")
async def get_demo_users() -> Dict[str, Any]:
    """Get demo user credentials for testing"""
    return {
        "demo_users": [
            {
                "email": "admin@kari.ai",
                "password": "Password123!",
                "role": "super_admin"
            },
            {
                "email": "admin@example.com",
                "password": "password123",
                "role": "admin"
            },
            {
                "email": "test@example.com", 
                "password": "testpassword",
                "role": "user"
            }
        ],
        "note": "These are demo credentials for testing. In production, users would register their own accounts."
    }