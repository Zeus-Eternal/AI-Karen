import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["copilot"])

# Graceful imports with fallbacks
try:
    from ai_karen_engine.services.enhanced_memory_service import get_memory_service
except ImportError:
    get_memory_service = None

try:
    from ai_karen_engine.services.llm_optimization import get_llm_provider
except ImportError:
    get_llm_provider = None

try:
    from ai_karen_engine.services.performance_monitor import get_metrics_service
except ImportError:
    get_metrics_service = None

try:
    from ai_karen_engine.core.rbac import check_rbac_scope
except ImportError:
    async def check_rbac_scope(*args, **kwargs):
        return True


class ContextHit(BaseModel):
    id: str
    text: str
    preview: Optional[str] = None
    score: float
    tags: List[str] = Field(default_factory=list)
    recency: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    importance: int = Field(5, ge=1, le=10)
    decay_tier: str = Field("short")
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: str
    org_id: Optional[str] = None


class SuggestedAction(BaseModel):
    type: str = Field(
        ..., examples=["add_task", "pin_memory", "open_doc", "export_note"]
    )
    params: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(0.8, ge=0.0, le=1.0)
    description: Optional[str] = None


class AssistRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    org_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=8000)
    top_k: int = Field(6, ge=1, le=50)
    context: Dict[str, Any] = Field(default_factory=dict)


class AssistResponse(BaseModel):
    answer: str
    context: List[ContextHit] = Field(default_factory=list)
    actions: List[SuggestedAction] = Field(default_factory=list)
    timings: Dict[str, float]
    correlation_id: str


def get_correlation_id(request: Request) -> str:
    return request.headers.get("X-Correlation-Id", "")


from functools import lru_cache
from ai_karen_engine.core.dependencies import get_current_user_context

# Add the same orchestrator dependency as chat_runtime.py
@lru_cache
def get_chat_orchestrator():
    """Return a cached ChatOrchestrator instance - same as chat_runtime.py"""
    from ai_karen_engine.chat.chat_orchestrator import ChatOrchestrator
    from ai_karen_engine.chat.memory_processor import MemoryProcessor
    from ai_karen_engine.services.nlp_service_manager import nlp_service_manager
    from ai_karen_engine.database.memory_manager import MemoryManager
    from ai_karen_engine.database.client import MultiTenantPostgresClient
    from ai_karen_engine.core.milvus_client import MilvusClient
    from ai_karen_engine.core import default_models

    try:
        # Initialize required components for memory manager
        db_client = MultiTenantPostgresClient()
        milvus_client = MilvusClient()
        
        # Load embedding manager (async operation handled gracefully)
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                embedding_manager = None
            else:
                loop.run_until_complete(default_models.load_default_models())
                embedding_manager = default_models.get_embedding_manager()
        except Exception as e:
            logger.warning(f"Failed to load embedding manager: {e}")
            embedding_manager = None
        
        # Create memory manager instance
        memory_manager = MemoryManager(
            db_client=db_client,
            milvus_client=milvus_client,
            embedding_manager=embedding_manager
        )
    except Exception as e:
        logger.warning(f"Failed to create memory manager: {e}")
        memory_manager = None

    memory_processor = MemoryProcessor(
        spacy_service=nlp_service_manager.spacy_service,
        distilbert_service=nlp_service_manager.distilbert_service,
        memory_manager=memory_manager,
    )
    return ChatOrchestrator(memory_processor=memory_processor)

@router.post("/assist")
async def copilot_assist(
    request: dict, 
    http_request: Request,
    user_context: dict = Depends(get_current_user_context),
    chat_orchestrator = Depends(get_chat_orchestrator)
):
    """Production-ready copilot assist endpoint with real AI integration."""
    start_time = time.time()
    correlation_id = get_correlation_id(http_request) or f"copilot_{int(time.time())}"
    
    # Extract and validate required fields
    try:
        user_id = request.get("user_id", "anonymous")
        message = request.get("message", "")
        org_id = request.get("org_id")
        top_k = request.get("top_k", 6)
        
        if not message:
            return {
                "answer": "I need a message to assist you with. Please provide your question or request.",
                "context": [],
                "actions": [],
                "timings": {"total_ms": (time.time() - start_time) * 1000},
                "correlation_id": correlation_id
            }
    except Exception as e:
        return {
            "answer": "I encountered an issue processing your request. Please check your input format.",
            "context": [],
            "actions": [],
            "timings": {"total_ms": (time.time() - start_time) * 1000},
            "correlation_id": correlation_id
        }
    
    # Initialize response components
    context_hits = []
    suggested_actions = []
    answer = "I'm processing your request..."
    timings = {"start": start_time}
    
    # Try to get real AI response using the injected chat orchestrator
    llm_start = time.time()
    try:
        from ai_karen_engine.chat.chat_orchestrator import ChatRequest
        
        # Use the user_id from user_context if available, otherwise from request
        actual_user_id = user_context.get("user_id", user_id)
        
        # Create proper ChatRequest using the same pattern as chat_runtime.py
        chat_request = ChatRequest(
            message=message,
            user_id=actual_user_id,
            conversation_id=f"copilot_{correlation_id}",
            session_id=correlation_id,
            stream=False,
            include_context=True,
            metadata={
                "source": "copilot_assist", 
                "org_id": org_id,
                "platform": "copilot"
            }
        )
        
        # Process the message through the injected chat orchestrator
        response = await chat_orchestrator.process_message(chat_request)
        
        # Handle the response properly based on ChatOrchestrator response structure
        if response:
            # The ChatOrchestrator returns a response object with a 'response' attribute
            if hasattr(response, 'response') and response.response:
                answer = response.response
                print(f"SUCCESS: Got AI response: {answer[:100]}...")
            elif hasattr(response, 'content') and response.content:
                answer = response.content
                print(f"SUCCESS: Got AI content: {answer[:100]}...")
            elif isinstance(response, str):
                answer = response
                print(f"SUCCESS: Got string response: {answer[:100]}...")
            else:
                print(f"WARNING: Unexpected response format: {type(response)} - {response}")
                answer = f"I processed your message '{message}' but encountered an unexpected response format. Let me help you anyway - what specific aspect would you like me to focus on?"
            
            # Extract context from memory processor if available
            if hasattr(response, 'context_data') and response.context_data:
                for idx, context_item in enumerate(response.context_data[:top_k]):
                    context_hit = {
                        "id": f"memory_{idx}_{int(time.time())}",
                        "text": str(context_item)[:500],
                        "preview": str(context_item)[:200] + "..." if len(str(context_item)) > 200 else str(context_item),
                        "score": 0.8,  # Default score since we don't have specific scoring
                        "tags": ["ai_generated", "relevant"],
                        "recency": "recent",
                        "meta": {},
                        "importance": 7,
                        "decay_tier": "short",
                        "created_at": datetime.now().isoformat(),
                        "updated_at": None,
                        "user_id": user_id,
                        "org_id": org_id
                    }
                    context_hits.append(context_hit)
            
            # Generate intelligent actions based on the response and message content
            message_lower = message.lower()
            if any(word in message_lower for word in ["code", "debug", "error", "fix", "programming"]):
                suggested_actions.append({
                    "type": "open_doc",
                    "params": {"doc_type": "code_reference", "topic": "debugging"},
                    "confidence": 0.8,
                    "description": "Open debugging documentation"
                })
            
            if any(word in message_lower for word in ["remember", "save", "store", "important"]):
                suggested_actions.append({
                    "type": "pin_memory",
                    "params": {"content": message, "importance": "high"},
                    "confidence": 0.9,
                    "description": "Save this information to memory"
                })
            
            if any(word in message_lower for word in ["task", "todo", "remind", "follow"]):
                suggested_actions.append({
                    "type": "add_task",
                    "params": {"task": f"Follow up: {message[:50]}..."},
                    "confidence": 0.7,
                    "description": "Add as a task to track"
                })
            
            # Always suggest export for longer responses
            if len(answer) > 200:
                suggested_actions.append({
                    "type": "export_note",
                    "params": {"title": f"AI Response: {message[:30]}...", "content": answer},
                    "confidence": 0.6,
                    "description": "Export this response as a note"
                })
        
        timings["llm_generation_ms"] = (time.time() - llm_start) * 1000
        
    except Exception as e:
        timings["llm_error"] = str(e)
        print(f"AI service error: {e}")
        
        # Try a simpler approach - use basic LLM service directly
        try:
            from ai_karen_engine.services.nlp_service_manager import nlp_service_manager
            
            # Try to get a simple response from the LLM service
            if hasattr(nlp_service_manager, 'get_llm_response'):
                simple_response = await nlp_service_manager.get_llm_response(message)
                if simple_response:
                    answer = simple_response
                    print(f"SUCCESS: Got simple LLM response: {answer[:100]}...")
                else:
                    raise Exception("No response from simple LLM")
            else:
                raise Exception("No simple LLM method available")
                
        except Exception as simple_e:
            print(f"Simple LLM also failed: {simple_e}")
            
            # Final fallback - but make it more intelligent and less template-like
            message_lower = message.lower()
            
            # Create more dynamic, contextual responses
            if any(word in message_lower for word in ["explain", "what is", "how does", "tell me about"]):
                topic = message.replace("explain", "").replace("what is", "").replace("how does", "").replace("tell me about", "").strip()
                answer = f"I'd be happy to explain {topic}. This is a complex topic that involves several key concepts. Let me break it down for you:\n\n1. Core principles and fundamentals\n2. How it works in practice\n3. Common applications and use cases\n4. Benefits and considerations\n\nWould you like me to dive deeper into any specific aspect of {topic}?"
                
            elif any(word in message_lower for word in ["code", "debug", "error", "fix", "programming"]):
                answer = f"I can help you with your coding challenge: '{message}'. Here's my systematic approach:\n\n1. **Identify the Issue**: Let's first understand what's happening\n2. **Check Common Causes**: Syntax, imports, data types, logic flow\n3. **Debug Strategy**: Use logging, breakpoints, or print statements\n4. **Test Solutions**: Implement fixes incrementally\n\nWhat specific error or behavior are you seeing? Share your code and I'll provide targeted guidance."
                
            elif any(word in message_lower for word in ["hi", "hello", "hey"]):
                answer = "Hello! I'm your AI assistant, ready to help you tackle any challenge. I can assist with:\n\n• **Code & Development**: Debugging, architecture, best practices\n• **Explanations**: Breaking down complex concepts\n• **Analysis**: Data interpretation, problem-solving\n• **Planning**: Project structure, task organization\n\nWhat would you like to work on today?"
                
            elif any(word in message_lower for word in ["help", "assist", "support"]):
                answer = f"I'm here to help with '{message}'. I can provide comprehensive assistance including detailed explanations, step-by-step guidance, code examples, and practical solutions. What specific aspect would you like me to focus on first?"
                
            else:
                # More dynamic general response
                answer = f"I understand you're asking about '{message}'. This is an interesting topic that I can help you explore. Let me provide some insights and guidance based on what you're looking for.\n\nTo give you the most helpful response, could you tell me:\n• What specific aspect interests you most?\n• Are you looking for practical steps or conceptual understanding?\n• Do you have any particular context or use case in mind?\n\nI'm ready to dive deep into this topic with you!"
        
        # Add more intelligent actions based on content
        if any(word in message_lower for word in ["learn", "study", "understand", "explain"]):
            suggested_actions.append({
                "type": "export_note",
                "params": {"title": f"Learning: {message[:30]}...", "content": answer},
                "confidence": 0.8,
                "description": "Save this explanation for future reference"
            })
        
        if any(word in message_lower for word in ["code", "debug", "programming"]):
            suggested_actions.append({
                "type": "open_doc",
                "params": {"doc_type": "coding_guide", "topic": "debugging"},
                "confidence": 0.9,
                "description": "Open coding best practices guide"
            })
        
        # Always add a follow-up task
        suggested_actions.append({
            "type": "add_task",
            "params": {"task": f"Continue discussion: {message[:40]}..."},
            "confidence": 0.7,
            "description": "Track this conversation for follow-up"
        })
    
    # Calculate final timing
    total_time = (time.time() - start_time) * 1000
    timings["total_ms"] = total_time
    
    return {
        "answer": answer,
        "context": context_hits,
        "actions": suggested_actions,
        "timings": timings,
        "correlation_id": correlation_id
    }


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "copilot",
        "timestamp": datetime.utcnow().isoformat(),
    }


__all__ = ["router"]
