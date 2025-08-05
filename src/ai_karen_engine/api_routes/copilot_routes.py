"""API routes for CopilotKit integration."""

import logging
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ai_karen_engine.integrations.llm_registry import get_llm_registry
from ai_karen_engine.integrations.providers.copilotkit_provider import CopilotKitProvider

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class CodeCompletionRequest(BaseModel):
    code: str
    language: str
    cursor_position: Optional[int] = None
    max_suggestions: Optional[int] = 5

class CodeCompletionResponse(BaseModel):
    suggestions: List[Dict[str, Any]]
    provider: str
    language: str

class CodeAnalysisRequest(BaseModel):
    code: str
    language: str
    analysis_type: Optional[str] = "comprehensive"

class CodeAnalysisResponse(BaseModel):
    analysis: Dict[str, Any]
    provider: str
    language: str

class DocumentationRequest(BaseModel):
    code: str
    language: str
    style: Optional[str] = "comprehensive"

class DocumentationResponse(BaseModel):
    documentation: str
    provider: str
    language: str

class ContextualSuggestionsRequest(BaseModel):
    context: str
    type: Optional[str] = "general"
    max_suggestions: Optional[int] = 3

class ContextualSuggestionsResponse(BaseModel):
    suggestions: List[Dict[str, Any]]
    provider: str
    type: str

class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    response: str
    provider: str
    model: str
    metadata: Dict[str, Any]

# Create router
router = APIRouter(prefix="/api/copilot", tags=["copilot"])

def get_copilot_provider() -> CopilotKitProvider:
    """Get CopilotKit provider instance."""
    try:
        llm_registry = get_llm_registry()
        provider = llm_registry.get_provider("copilotkit")
        
        if not provider or not isinstance(provider, CopilotKitProvider):
            raise HTTPException(status_code=503, detail="CopilotKit provider not available")
        
        return provider
    except Exception as e:
        logger.error(f"Failed to get CopilotKit provider: {e}")
        raise HTTPException(status_code=503, detail="CopilotKit service unavailable")

@router.post("/completion", response_model=CodeCompletionResponse)
async def get_code_completion(
    request: CodeCompletionRequest,
    provider: CopilotKitProvider = Depends(get_copilot_provider)
):
    """Get code completion suggestions."""
    try:
        suggestions = await provider.get_code_completion(
            code_context=request.code,
            language=request.language,
            cursor_position=request.cursor_position or len(request.code)
        )
        
        return CodeCompletionResponse(
            suggestions=suggestions[:request.max_suggestions],
            provider="copilotkit",
            language=request.language
        )
        
    except Exception as e:
        logger.error(f"Code completion failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get code completion")

@router.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(
    request: CodeAnalysisRequest,
    provider: CopilotKitProvider = Depends(get_copilot_provider)
):
    """Analyze code for issues and improvements."""
    try:
        analysis = await provider.analyze_code(
            code=request.code,
            language=request.language,
            analysis_type=request.analysis_type
        )
        
        return CodeAnalysisResponse(
            analysis=analysis,
            provider="copilotkit",
            language=request.language
        )
        
    except Exception as e:
        logger.error(f"Code analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze code")

@router.post("/generate-docs", response_model=DocumentationResponse)
async def generate_documentation(
    request: DocumentationRequest,
    provider: CopilotKitProvider = Depends(get_copilot_provider)
):
    """Generate documentation for code."""
    try:
        documentation = await provider.generate_documentation(
            code=request.code,
            language=request.language,
            style=request.style
        )
        
        return DocumentationResponse(
            documentation=documentation,
            provider="copilotkit",
            language=request.language
        )
        
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate documentation")

@router.post("/suggestions", response_model=ContextualSuggestionsResponse)
async def get_contextual_suggestions(
    request: ContextualSuggestionsRequest,
    provider: CopilotKitProvider = Depends(get_copilot_provider)
):
    """Get contextual suggestions based on context."""
    try:
        suggestions = await provider.get_contextual_suggestions(
            context=request.context,
            suggestion_type=request.type
        )
        
        return ContextualSuggestionsResponse(
            suggestions=suggestions[:request.max_suggestions],
            provider="copilotkit",
            type=request.type
        )
        
    except Exception as e:
        logger.error(f"Contextual suggestions failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get contextual suggestions")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_copilot(
    request: ChatRequest,
    provider: CopilotKitProvider = Depends(get_copilot_provider)
):
    """Chat with CopilotKit AI assistant."""
    try:
        response = await provider.generate_response(
            prompt=request.prompt,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return ChatResponse(
            response=response,
            provider="copilotkit",
            model=request.model or provider.models.get("chat", "gpt-4"),
            metadata={
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "timestamp": "2024-01-01T00:00:00Z"  # Would be actual timestamp
            }
        )
        
    except Exception as e:
        logger.error(f"CopilotKit chat failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat request")

@router.get("/status")
async def get_copilot_status(
    provider: CopilotKitProvider = Depends(get_copilot_provider)
):
    """Get CopilotKit provider status."""
    try:
        status = await provider.get_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get CopilotKit status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider status")

@router.get("/models")
async def get_available_models(
    provider: CopilotKitProvider = Depends(get_copilot_provider)
):
    """Get available CopilotKit models."""
    try:
        models = provider.get_available_models()
        return {
            "models": models,
            "default_models": provider.models,
            "provider": "copilotkit"
        }
    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available models")

@router.get("/features")
async def get_available_features(
    provider: CopilotKitProvider = Depends(get_copilot_provider)
):
    """Get available CopilotKit features."""
    try:
        return {
            "features": provider.features,
            "provider": "copilotkit",
            "available": provider.is_available()
        }
    except Exception as e:
        logger.error(f"Failed to get available features: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available features")

@router.get("/health")
async def health_check(
    provider: CopilotKitProvider = Depends(get_copilot_provider)
):
    """Health check for CopilotKit service."""
    try:
        status = await provider.get_status()
        
        if status.get("available", False):
            return {
                "status": "healthy",
                "provider": "copilotkit",
                "timestamp": "2024-01-01T00:00:00Z",  # Would be actual timestamp
                "details": status
            }
        else:
            return {
                "status": "unhealthy",
                "provider": "copilotkit",
                "timestamp": "2024-01-01T00:00:00Z",
                "details": status
            }
            
    except Exception as e:
        logger.error(f"CopilotKit health check failed: {e}")
        return {
            "status": "error",
            "provider": "copilotkit",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }

# Export router for inclusion in main FastAPI app
__all__ = ["router"]