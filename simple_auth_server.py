#!/usr/bin/env python3
"""
Simple authentication server for testing login functionality
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Simple Auth Server")

# Add CORS middleware with comprehensive configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:9002", 
        "http://127.0.0.1:9002", 
        "http://10.105.235.209:9002",
        "http://localhost:3000",
        "http://localhost:3001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language", 
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Web-UI-Compatible",
        "X-Kari-Trace-Id",
        "User-Agent",
        "Cache-Control",
        "Pragma"
    ],
    expose_headers=[
        "X-Kari-Trace-Id",
        "X-Web-UI-Compatible", 
        "X-Response-Time-Ms",
        "Content-Length",
        "Content-Type"
    ],
    max_age=86400,
)

class LoginCredentials(BaseModel):
    email: str
    password: str
    totp_code: str = None

class LoginResponse(BaseModel):
    token: str
    user_id: str
    email: str
    roles: list
    tenant_id: str
    preferences: dict
    two_factor_enabled: bool

# Test users
TEST_USERS = {
    "admin@kari.ai": {
        "password": "password123",
        "user_id": "admin-001",
        "roles": ["admin", "user"],
        "tenant_id": "default",
        "two_factor_enabled": False,
        "preferences": {
            "personalityTone": "friendly",
            "personalityVerbosity": "balanced",
            "memoryDepth": "medium",
            "customPersonaInstructions": "",
            "preferredLLMProvider": "ollama",
            "preferredModel": "llama3.2:latest",
            "temperature": 0.7,
            "maxTokens": 1000,
            "notifications": {"email": True, "push": False},
            "ui": {"theme": "light", "language": "en", "avatarUrl": ""}
        }
    },
    "user@kari.ai": {
        "password": "password123",
        "user_id": "user-001",
        "roles": ["user"],
        "tenant_id": "default",
        "two_factor_enabled": False,
        "preferences": {
            "personalityTone": "friendly",
            "personalityVerbosity": "balanced",
            "memoryDepth": "medium",
            "customPersonaInstructions": "",
            "preferredLLMProvider": "ollama",
            "preferredModel": "llama3.2:latest",
            "temperature": 0.7,
            "maxTokens": 1000,
            "notifications": {"email": True, "push": False},
            "ui": {"theme": "light", "language": "en", "avatarUrl": ""}
        }
    }
}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Simple auth server is running"}

@app.options("/api/auth/login")
def login_options():
    """Handle CORS preflight for login endpoint"""
    return {"message": "CORS preflight handled"}

@app.options("/api/auth/me")
def me_options():
    """Handle CORS preflight for me endpoint"""
    return {"message": "CORS preflight handled"}

@app.post("/api/auth/login")
def login(credentials: LoginCredentials):
    print(f"Login attempt: {credentials.email}")
    
    # Check if user exists
    if credentials.email not in TEST_USERS:
        print(f"User not found: {credentials.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = TEST_USERS[credentials.email]
    
    # Check password
    if credentials.password != user["password"]:
        print(f"Invalid password for user: {credentials.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    print(f"Login successful for user: {credentials.email}")
    
    # Return login response
    return LoginResponse(
        token="test-token-123",
        user_id=user["user_id"],
        email=credentials.email,
        roles=user["roles"],
        tenant_id=user["tenant_id"],
        preferences=user["preferences"],
        two_factor_enabled=user["two_factor_enabled"]
    )

@app.get("/api/auth/me")
def get_current_user():
    # For testing, return a default user
    return {
        "user_id": "admin-001",
        "email": "admin@kari.ai",
        "roles": ["admin", "user"],
        "tenant_id": "default",
        "two_factor_enabled": False,
        "preferences": {
            "personalityTone": "friendly",
            "personalityVerbosity": "balanced",
            "memoryDepth": "medium",
            "customPersonaInstructions": "",
            "preferredLLMProvider": "ollama",
            "preferredModel": "llama3.2:latest",
            "temperature": 0.7,
            "maxTokens": 1000,
            "notifications": {"email": True, "push": False},
            "ui": {"theme": "light", "language": "en", "avatarUrl": ""}
        }
    }

@app.post("/api/auth/logout")
def logout():
    return {"message": "Logged out successfully"}

if __name__ == "__main__":
    print("Starting simple authentication server...")
    print("Server will be available at: http://localhost:8000")
    print("Test credentials:")
    print("  - admin@kari.ai / password123")
    print("  - user@kari.ai / password123")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")