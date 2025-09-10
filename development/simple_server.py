#!/usr/bin/env python3
"""
Simple FastAPI server for AI-Karen with minimal dependencies
Bypasses heavy database initialization for quick startup
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env")

app = FastAPI(title="AI-Karen Simple Server", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8020", "http://127.0.0.1:8020", "http://127.0.0.1:44985", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Simple server running"}

@app.get("/api/health")
async def api_health_check():
    return {"status": "ok", "message": "API endpoints available"}

@app.get("/api/models/library")
async def get_models_library(quick: bool = True, ttl: int = 60):
    """Mock models library endpoint"""
    return {
        "models": [
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "provider": "openai",
                "status": "available",
                "capabilities": ["text-generation", "chat"]
            },
            {
                "id": "claude-3",
                "name": "Claude 3",
                "provider": "anthropic", 
                "status": "available",
                "capabilities": ["text-generation", "chat"]
            }
        ],
        "total_count": 2,
        "local_count": 0,
        "available_count": 2
    }

@app.post("/api/auth/login")
async def login(credentials: dict):
    """Mock login endpoint"""
    email = credentials.get("email")
    password = credentials.get("password")
    
    if email == "admin@kari.ai" and password == "Password123!":
        return {
            "access_token": "mock_jwt_token_12345",
            "refresh_token": "mock_refresh_token_67890",
            "token_type": "bearer",
            "expires_in": 86400,
            "user": {
                "user_id": "admin-user-id",
                "email": "admin@kari.ai",
                "full_name": "Admin User",
                "roles": ["admin", "user"],
                "tenant_id": "default-tenant",
                "preferences": {
                    "memoryDepth": "high",
                    "preferredModel": "gpt-4",
                    "personalityTone": "professional"
                },
                "two_factor_enabled": False,
                "is_verified": True
            }
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/auth/session")
async def get_session():
    """Mock session endpoint"""
    return {"authenticated": False, "user": None}

@app.get("/api/copilot/start")
async def copilot_start():
    """Mock copilot start endpoint"""
    return {"status": "started", "session_id": "mock_session_123"}

@app.get("/api/models/stats")
async def get_models_stats():
    """Mock models stats endpoint"""
    return {
        "total_models": 2,
        "active_models": 1,
        "memory_usage": "2.1GB",
        "cpu_usage": "15%",
        "gpu_usage": "0%"
    }

@app.get("/api/plugins")
async def get_plugins():
    """Mock plugins endpoint"""
    return {
        "plugins": [
            {
                "id": "gmail_plugin",
                "name": "Gmail Plugin",
                "status": "active",
                "version": "1.0.0"
            }
        ],
        "total": 1
    }

@app.get("/api/analytics/usage")
async def get_analytics_usage():
    """Mock analytics usage endpoint"""
    return {
        "requests_today": 42,
        "tokens_used": 15000,
        "active_users": 1,
        "uptime": "99.9%"
    }

@app.get("/api/web/analytics/system")
async def get_web_analytics_system():
    """Mock web analytics system endpoint"""
    return {
        "system_health": "healthy",
        "response_time": "120ms",
        "error_rate": "0.1%",
        "throughput": "50 req/min"
    }

@app.get("/api/health/degraded-mode")
async def get_health_degraded_mode():
    """Mock degraded mode health endpoint"""
    return {
        "degraded_mode": False,
        "services": {
            "database": "healthy",
            "ai_models": "healthy",
            "cache": "healthy"
        }
    }

@app.get("/api/auth/validate-session")
async def validate_session():
    """Mock session validation endpoint"""
    return {
        "valid": True,
        "user": {
            "user_id": "admin-user-id",
            "email": "admin@kari.ai",
            "roles": ["admin", "user"],
            "tenant_id": "default-tenant"
        },
        "expires_at": "2025-12-31T23:59:59Z"
    }

@app.post("/copilot/assist")
async def copilot_assist(request: dict):
    """Mock copilot assist endpoint"""
    return {
        "response": "This is a mock response from the copilot assist endpoint. The full AI Karen system is not available.",
        "status": "mock",
        "timestamp": "2025-01-01T00:00:00Z"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
