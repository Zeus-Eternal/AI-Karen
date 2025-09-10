#!/usr/bin/env python3
"""
Simple authentication bypass for debugging
Creates a minimal auth service that always succeeds
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
import jwt
import time
from datetime import datetime, timezone, timedelta

# Simple router for bypassing complex auth
router = APIRouter(tags=["simple-auth"], prefix="/auth")

# Simple models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

# Simple JWT secret (for testing only)
JWT_SECRET = "test-secret-key-for-debugging"

def create_simple_token(email: str) -> str:
    """Create a simple JWT token"""
    payload = {
        "sub": "test-user-id",
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc),
        "tenant_id": "default",
        "roles": ["user"]
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@router.post("/login-bypass", response_model=LoginResponse)
async def login_bypass(req: LoginRequest, response: Response) -> LoginResponse:
    """Simple login that always succeeds - for debugging only"""
    
    # Create simple token
    access_token = create_simple_token(req.email)
    
    # Simple user data
    user_data = {
        "user_id": "test-user-id",
        "email": req.email,
        "full_name": "Test User",
        "roles": ["user"],
        "tenant_id": "default",
        "preferences": {},
        "two_factor_enabled": False,
        "is_verified": True,
    }
    
    return LoginResponse(
        access_token=access_token,
        expires_in=24 * 60 * 60,  # 24 hours
        user=user_data,
    )

@router.get("/me-bypass")
async def get_current_user_bypass() -> Dict[str, Any]:
    """Simple user info endpoint"""
    return {
        "user_id": "test-user-id",
        "email": "test@example.com",
        "full_name": "Test User",
        "roles": ["user"],
        "tenant_id": "default",
        "preferences": {},
        "two_factor_enabled": False,
        "is_verified": True,
    }

@router.post("/logout-bypass")
async def logout_bypass() -> Dict[str, str]:
    """Simple logout"""
    return {"detail": "Logged out successfully"}