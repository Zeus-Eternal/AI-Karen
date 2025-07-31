#!/usr/bin/env python3
"""
Simple FastAPI server to test basic functionality
This bypasses the heavy AI Karen initialization to get the API running quickly
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(title="AI Karen API - Simple Mode")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:9002",
        "http://127.0.0.1:9002",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic health check
@app.get("/health")
def health():
    return {"status": "healthy", "mode": "simple"}

@app.get("/")
def root():
    return {"message": "AI Karen API - Simple Mode", "status": "running"}

# Basic auth endpoints for testing
@app.post("/api/auth/login")
def login(credentials: dict):
    # Simple mock login for testing
    email = credentials.get("email", "")
    password = credentials.get("password", "")
    
    if email and password:
        return {
            "token": "mock-token-123",
            "user_id": "test-user",
            "email": email,
            "roles": ["user"],
            "tenant_id": "default",
            "preferences": {},
            "two_factor_enabled": False
        }
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/auth/me")
def get_current_user():
    # Mock current user for testing
    return {
        "user_id": "test-user",
        "email": "test@example.com",
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
            "notifications": {
                "email": True,
                "push": False,
            },
            "ui": {
                "theme": "light",
                "language": "en",
                "avatarUrl": "",
            },
        },
    }

@app.post("/api/auth/logout")
def logout():
    return {"status": "logged out"}

# Mock conversation endpoints for testing
@app.post("/api/conversations/create")
def create_conversation(request: dict):
    """Mock conversation creation endpoint for testing."""
    session_id = request.get("session_id", "mock-session-123")
    return {
        "conversation": {
            "id": "mock-conversation-123",
            "user_id": "test-user",
            "title": request.get("title", "Test Conversation"),
            "messages": [],
            "metadata": {},
            "is_active": True,
            "created_at": "2025-07-31T00:00:00Z",
            "updated_at": "2025-07-31T00:00:00Z",
            "message_count": 0,
            "last_message_at": None,
            "session_id": session_id,
            "ui_context": request.get("ui_context", {}),
            "ai_insights": {},
            "user_settings": request.get("user_settings", {}),
            "summary": None,
            "tags": request.get("tags", []),
            "last_ai_response_id": None,
            "status": "active",
            "priority": request.get("priority", "normal"),
            "context_memories": [],
            "proactive_suggestions": []
        },
        "success": True,
        "message": "Conversation created successfully"
    }

@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    """Mock get conversation endpoint for testing."""
    return {
        "id": conversation_id,
        "user_id": "test-user",
        "title": "Mock Conversation",
        "messages": [],
        "metadata": {},
        "is_active": True,
        "created_at": "2025-07-31T00:00:00Z",
        "updated_at": "2025-07-31T00:00:00Z",
        "message_count": 0,
        "last_message_at": None,
        "session_id": "mock-session-123",
        "ui_context": {},
        "ai_insights": {},
        "user_settings": {},
        "summary": None,
        "tags": [],
        "last_ai_response_id": None,
        "status": "active",
        "priority": "normal",
        "context_memories": [],
        "proactive_suggestions": []
    }

@app.post("/api/conversations/{conversation_id}/messages")
def add_message(conversation_id: str, request: dict):
    """Mock add message endpoint for testing."""
    return {
        "message": {
            "id": "mock-message-123",
            "role": request.get("role", "user"),
            "content": request.get("content", ""),
            "timestamp": "2025-07-31T00:00:00Z",
            "metadata": request.get("metadata", {}),
            "function_call": None,
            "function_response": None,
            "ui_source": request.get("ui_source", "web_ui"),
            "ai_confidence": None,
            "processing_time_ms": None,
            "tokens_used": None,
            "model_used": None,
            "user_feedback": None,
            "edited": False,
            "edit_history": []
        },
        "success": True
    }

@app.post("/api/chat/process")
def process_chat(request: dict):
    """Mock chat processing endpoint for testing."""
    message = request.get("message", "")
    return {
        "finalResponse": f"Mock response to: {message}",
        "summaryWasGenerated": False,
        "aiDataForFinalResponse": None,
        "suggestedNewFacts": None,
        "proactiveSuggestion": None
    }

# Mock memory endpoints for testing
@app.post("/api/memory/store")
def store_memory(request: dict):
    """Mock memory storage endpoint for testing."""
    return {
        "memory_id": "mock-memory-123",
        "success": True
    }

@app.post("/api/memory/query")
def query_memories(request: dict):
    """Mock memory query endpoint for testing."""
    return {
        "memories": [],
        "total_count": 0
    }

@app.get("/api/memory/stats")
def get_memory_stats():
    """Mock memory stats endpoint for testing."""
    return {
        "total_memories": 0,
        "last_updated": "2025-07-31T00:00:00Z"
    }

if __name__ == "__main__":
    print("🚀 Starting AI Karen API in Simple Mode...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🔗 Health check: http://localhost:8000/health")
    print("📚 API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )