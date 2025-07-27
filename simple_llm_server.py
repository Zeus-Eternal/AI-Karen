#!/usr/bin/env python3
"""
Simple LLM server for testing web UI integration
"""

import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Create a simple FastAPI app
app = FastAPI(title="LLM Test Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Import and mount LLM routes
from ai_karen_engine.api_routes.llm_routes import router as llm_router
app.include_router(llm_router)

# Add basic memory and chat endpoints for web UI compatibility
from fastapi import HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class MemoryQuery(BaseModel):
    text: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata_filter: Optional[Dict[str, Any]] = None
    top_k: Optional[int] = 5
    similarity_threshold: Optional[float] = 0.7

class MemoryStoreRequest(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatProcessRequest(BaseModel):
    message: str
    conversation_history: List[Dict[str, Any]]
    relevant_memories: List[Dict[str, Any]]
    user_settings: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class GenerateStarterRequest(BaseModel):
    context: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user_id: str
    email: str
    roles: List[str]
    tenant_id: str
    preferences: Dict[str, Any]

class UserResponse(BaseModel):
    user_id: str
    email: str
    roles: List[str]
    tenant_id: str
    preferences: Dict[str, Any]

@app.post("/api/memory/query")
async def query_memories(query: MemoryQuery):
    """Basic memory query endpoint - returns empty for now"""
    return {"memories": []}

@app.post("/api/memory/store")
async def store_memory(request: MemoryStoreRequest):
    """Basic memory store endpoint - returns success for now"""
    return {"memory_id": f"mem_{hash(request.content) % 10000}", "success": True}

@app.post("/api/ai/generate-starter")
async def generate_starter(request: GenerateStarterRequest):
    """Generate conversation starter suggestions"""
    starters = [
        "What can you help me with today?",
        "Tell me about the available LLM providers",
        "How do I configure my AI settings?",
        "What's new in AI Karen?",
        "Help me get started with LLM integration"
    ]
    return {"starters": starters}

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request):
    """User authentication endpoint"""
    try:
        from ai_karen_engine.services.user_service import UserService
        from ai_karen_engine.core.services.base import ServiceConfig
        
        # Initialize user service
        user_service_config = ServiceConfig(name="user_service", enabled=True)
        user_service = UserService(user_service_config)
        await user_service.initialize()
        
        # Authenticate user
        auth_result = await user_service.authenticate_user(
            email=request.email,
            password=request.password,
            user_agent=req.headers.get("user-agent", ""),
            ip=req.client.host if req.client else "127.0.0.1"
        )
        
        return LoginResponse(
            token=auth_result["token"],
            user_id=auth_result["user_id"],
            email=auth_result["email"],
            roles=auth_result["roles"],
            tenant_id=auth_result["tenant_id"],
            preferences=auth_result["preferences"]
        )
        
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user(req: Request):
    """Get current user information"""
    try:
        from ai_karen_engine.services.user_service import UserService
        from ai_karen_engine.core.services.base import ServiceConfig
        
        # Get authorization header
        auth_header = req.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        token = auth_header.split(" ")[1]
        
        # Initialize user service
        user_service_config = ServiceConfig(name="user_service", enabled=True)
        user_service = UserService(user_service_config)
        await user_service.initialize()
        
        # Validate session
        user_context = await user_service.validate_user_session(
            token=token,
            user_agent=req.headers.get("user-agent", ""),
            ip=req.client.host if req.client else "127.0.0.1"
        )
        
        if not user_context:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        return UserResponse(
            user_id=user_context["user_id"],
            email=user_context["email"],
            roles=user_context["roles"],
            tenant_id=user_context["tenant_id"],
            preferences=user_context["preferences"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/chat/process")
async def process_chat(request: ChatProcessRequest):
    """Chat processing endpoint with user authentication and database integration"""
    try:
        # Import required services
        from ai_karen_engine.services.ai_orchestrator.ai_orchestrator import AIOrchestrator
        from ai_karen_engine.services.user_service import UserService
        from ai_karen_engine.core.services.base import ServiceConfig
        from ai_karen_engine.models.shared_types import FlowInput, FlowType
        
        # Initialize services
        user_service_config = ServiceConfig(name="user_service", enabled=True)
        user_service = UserService(user_service_config)
        await user_service.initialize()
        
        orchestrator_config = ServiceConfig(name="ai_orchestrator", enabled=True)
        orchestrator = AIOrchestrator(orchestrator_config)
        await orchestrator.initialize()
        
        # Get user ID from request or use default
        user_id = request.user_id or "default_user"
        session_id = request.session_id or f"session_{hash(request.message) % 10000}"
        
        # Get user preferences if user_id is provided and valid
        user_settings = request.user_settings
        if user_id != "default_user":
            try:
                llm_preferences = await user_service.get_user_llm_preferences(user_id)
                # Merge with request settings, giving priority to request
                merged_settings = llm_preferences.copy()
                merged_settings.update(user_settings)
                user_settings = merged_settings
            except Exception as e:
                print(f"Failed to get user preferences: {e}")
                # Continue with request settings
        
        # Create FlowInput for the conversation processing
        flow_input = FlowInput(
            prompt=request.message,
            conversation_history=request.conversation_history,
            user_settings=user_settings,
            user_id=user_id,
            session_id=session_id,
            context_from_memory=request.relevant_memories
        )
        
        # Process using the conversation processing flow
        result = await orchestrator.conversation_processing_flow(flow_input)
        
        # Save conversation if user is authenticated
        if user_id != "default_user":
            try:
                # Add the new message and response to conversation history
                updated_messages = request.conversation_history.copy()
                updated_messages.append({"role": "user", "content": request.message})
                updated_messages.append({"role": "assistant", "content": result.response})
                
                await user_service.save_user_conversation(
                    user_id=user_id,
                    session_id=session_id,
                    messages=updated_messages,
                    metadata={
                        "ai_data": result.ai_data.__dict__ if result.ai_data else None,
                        "proactive_suggestion": result.proactive_suggestion
                    }
                )
            except Exception as e:
                print(f"Failed to save conversation: {e}")
                # Continue without saving
        
        return {
            "finalResponse": result.response,
            "aiDataForFinalResponse": result.ai_data.__dict__ if result.ai_data else None,
            "suggestedNewFacts": result.memory_to_store,
            "proactiveSuggestion": result.proactive_suggestion,
            "suggestions": [result.proactive_suggestion] if result.proactive_suggestion else []
        }
        
    except Exception as e:
        print(f"Chat processing error: {e}")
        import traceback
        traceback.print_exc()
        # Return a fallback response with LLM provider info
        return {
            "finalResponse": f"I received your message: '{request.message}'. The LLM integration is working! You can configure LLM providers in Settings > LLM tab. Currently available providers include Ollama (local), OpenAI, Gemini, Deepseek, and HuggingFace.",
            "aiDataForFinalResponse": None,
            "suggestedNewFacts": None,
            "proactiveSuggestion": "Would you like to explore the LLM settings to configure your preferred AI provider?",
            "suggestions": ["Would you like to explore the LLM settings to configure your preferred AI provider?"]
        }

@app.get("/health")
async def health():
    return {"status": "ok", "message": "LLM server is running"}

@app.get("/")
async def root():
    return {
        "message": "LLM Test Server",
        "endpoints": {
            "health": "/health",
            "providers": "/api/llm/providers",
            "profiles": "/api/llm/profiles",
            "health_check": "/api/llm/health-check",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting simple LLM server...")
    print("📍 Server: http://localhost:8000")
    print("📋 Providers: http://localhost:8000/api/llm/providers")
    print("📋 Profiles: http://localhost:8000/api/llm/profiles")
    print("🔍 Health: http://localhost:8000/api/llm/health-check")
    print("📖 Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )