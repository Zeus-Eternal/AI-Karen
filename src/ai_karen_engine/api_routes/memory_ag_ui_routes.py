"""
AG-UI Memory API Routes
Provides endpoints for AG-UI enhanced memory management with CopilotKit integration.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
import logging
from datetime import datetime

from ai_karen_engine.core.memory.ag_ui_manager import AGUIMemoryManager, MemoryGridRow
from ai_karen_engine.integrations.providers.copilotkit_provider import CopilotKitProvider
try:
    from ai_karen_engine.services.nlp_service_manager import spacy_service_manager
except ImportError:
    # Fallback for testing
    spacy_service_manager = None

logger = logging.getLogger("kari.api.memory_ag_ui")

# Initialize router
router = APIRouter(prefix="/api/memory", tags=["memory-ag-ui"])

# Initialize managers
ag_ui_memory_manager = AGUIMemoryManager()

# Initialize CopilotKit provider with default config
try:
    copilot_config = {
        "api_key": "demo_key",  # This would come from environment in production
        "base_url": "https://api.copilotkit.ai",
        "models": {
            "completion": "gpt-4",
            "chat": "gpt-4",
            "embedding": "text-embedding-ada-002"
        },
        "features": {
            "code_completion": True,
            "contextual_suggestions": True,
            "debugging_assistance": True,
            "documentation_generation": True,
            "chat_assistance": True
        }
    }
    copilot_provider = CopilotKitProvider(copilot_config)
except Exception as e:
    logger.warning(f"Failed to initialize CopilotKit provider: {e}")
    copilot_provider = None

# Request/Response models
class MemoryGridRequest(BaseModel):
    user_id: str
    tenant_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    limit: int = Field(default=100, ge=1, le=1000)

class MemoryNetworkRequest(BaseModel):
    user_id: str
    tenant_id: Optional[str] = None
    max_nodes: int = Field(default=50, ge=1, le=200)

class MemoryAnalyticsRequest(BaseModel):
    user_id: str
    tenant_id: Optional[str] = None
    timeframe_days: int = Field(default=30, ge=1, le=365)

class MemorySearchRequest(BaseModel):
    user_id: str
    tenant_id: Optional[str] = None
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = Field(default=50, ge=1, le=200)

class MemoryUpdateRequest(BaseModel):
    user_id: str
    tenant_id: Optional[str] = None
    query: str
    result: Any
    metadata: Optional[Dict[str, Any]] = None

class AISuggestionsRequest(BaseModel):
    content: str
    context: Optional[str] = None
    memory_id: Optional[str] = None
    user_id: str
    tenant_id: Optional[str] = None
    current_type: Optional[str] = None
    current_cluster: Optional[str] = None

class MemoryCategorizeRequest(BaseModel):
    content: str
    user_id: str
    tenant_id: Optional[str] = None

class AISuggestion(BaseModel):
    type: str  # 'enhancement', 'categorization', 'relationship', 'correction'
    content: str
    confidence: float
    reasoning: str

class AISuggestionsResponse(BaseModel):
    suggestions: List[AISuggestion]
    processing_time_ms: float

class CategorizationResponse(BaseModel):
    suggested_type: str
    suggested_cluster: str
    confidence: float
    reasoning: str

# Dependency for user context
def get_user_context(request: Union[MemoryGridRequest, MemoryNetworkRequest, MemoryAnalyticsRequest, MemorySearchRequest, MemoryUpdateRequest, AISuggestionsRequest, MemoryCategorizeRequest]) -> Dict[str, Any]:
    """Extract user context from request."""
    return {
        "user_id": request.user_id,
        "tenant_id": request.tenant_id,
        "session_id": f"ag_ui_session_{request.user_id}_{datetime.now().strftime('%Y%m%d')}"
    }

@router.post("/grid")
async def get_memory_grid_data(request: MemoryGridRequest):
    """
    Get memory data formatted for AG-UI grid display.
    
    Returns memory records with enhanced metadata for grid visualization.
    """
    try:
        logger.info(f"Getting memory grid data for user {request.user_id}")
        
        user_ctx = get_user_context(request)
        
        # Get grid data from AG-UI manager
        grid_data = await ag_ui_memory_manager.get_memory_grid_data(
            user_ctx=user_ctx,
            filters=request.filters,
            limit=request.limit
        )
        
        return {
            "memories": grid_data,
            "total_count": len(grid_data),
            "filters_applied": request.filters or {},
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting memory grid data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory grid data: {str(e)}")

@router.post("/network")
async def get_memory_network_data(request: MemoryNetworkRequest):
    """
    Get memory relationship data for AG-UI network visualization.
    
    Returns nodes and edges for network graph display.
    """
    try:
        logger.info(f"Getting memory network data for user {request.user_id}")
        
        user_ctx = get_user_context(request)
        
        # Get network data from AG-UI manager
        network_data = await ag_ui_memory_manager.get_memory_network_data(
            user_ctx=user_ctx,
            max_nodes=request.max_nodes
        )
        
        return {
            **network_data,
            "metadata": {
                "max_nodes": request.max_nodes,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting memory network data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory network data: {str(e)}")

@router.post("/analytics")
async def get_memory_analytics(request: MemoryAnalyticsRequest):
    """
    Get memory analytics data for AG-UI charts.
    
    Returns analytics data formatted for AG-Charts visualization.
    """
    try:
        logger.info(f"Getting memory analytics for user {request.user_id}")
        
        user_ctx = get_user_context(request)
        
        # Get analytics data from AG-UI manager
        analytics_data = await ag_ui_memory_manager.get_memory_analytics(
            user_ctx=user_ctx,
            timeframe_days=request.timeframe_days
        )
        
        return {
            **analytics_data,
            "metadata": {
                "timeframe_days": request.timeframe_days,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting memory analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory analytics: {str(e)}")

@router.post("/search")
async def search_memories(request: MemorySearchRequest):
    """
    Enhanced semantic search with AG-UI filtering interface.
    
    Performs semantic search with AI-powered ranking and filtering.
    """
    try:
        logger.info(f"Searching memories for user {request.user_id}: '{request.query}'")
        
        user_ctx = get_user_context(request)
        
        # Perform enhanced search
        search_results = await ag_ui_memory_manager.search_memories(
            user_ctx=user_ctx,
            query=request.query,
            filters=request.filters,
            limit=request.limit
        )
        
        return {
            "results": search_results,
            "query": request.query,
            "total_results": len(search_results),
            "filters_applied": request.filters or {},
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search memories: {str(e)}")

@router.post("/update")
async def update_memory_with_metadata(request: MemoryUpdateRequest):
    """
    Enhanced memory update with additional metadata for AG-UI.
    
    Updates memory with AG-UI specific metadata and visualization data.
    """
    try:
        logger.info(f"Updating memory for user {request.user_id}")
        
        user_ctx = get_user_context(request)
        
        # Update memory with enhanced metadata
        success = await ag_ui_memory_manager.update_memory_with_metadata(
            user_ctx=user_ctx,
            query=request.query,
            result=request.result,
            metadata=request.metadata
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update memory")
        
        return {
            "success": True,
            "message": "Memory updated successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update memory: {str(e)}")

@router.post("/ai-suggestions", response_model=AISuggestionsResponse)
async def get_ai_suggestions(request: AISuggestionsRequest):
    """
    Generate CopilotKit-powered AI suggestions for memory enhancement.
    
    Provides intelligent suggestions for improving memory content, categorization, and relationships.
    """
    try:
        start_time = datetime.now()
        logger.info(f"Generating AI suggestions for user {request.user_id}")
        
        suggestions = []
        
        # Generate content enhancement suggestions using CopilotKit
        if request.content.strip():
            try:
                # Use CopilotKit for content enhancement
                enhancement_prompt = f"""
                Analyze this memory content and suggest improvements:
                Content: "{request.content}"
                Context: "{request.context or 'No additional context'}"
                Current Type: {request.current_type or 'unknown'}
                Current Cluster: {request.current_cluster or 'unknown'}
                
                Provide suggestions for:
                1. Content enhancement (make it clearer, more detailed, or better structured)
                2. Categorization (suggest better type and cluster)
                3. Potential relationships with other memories
                4. Any corrections needed
                
                Format your response as:
                Enhancement: [improved content]
                Categorization: Type: [fact/preference/context], Cluster: [technical/personal/work/general]
                Relationships: [potential connections]
                Corrections: [any fixes needed]
                """
                
                if copilot_provider:
                    copilot_response = await copilot_provider.generate_completion(
                        prompt=enhancement_prompt,
                        max_tokens=300,
                        temperature=0.7
                    )
                else:
                    copilot_response = None
                
                if copilot_response:
                    # Parse CopilotKit response into structured suggestions
                    suggestions.extend(_parse_copilot_suggestions(copilot_response, request.content))
                
            except Exception as e:
                logger.warning(f"CopilotKit enhancement failed: {e}")
                # Add fallback suggestion
                suggestions.append(AISuggestion(
                    type="enhancement",
                    content=f"Consider expanding: {request.content[:100]}... [Add more context or details]",
                    confidence=0.5,
                    reasoning="CopilotKit unavailable, using basic enhancement suggestion"
                ))
        
        # Generate NLP-based suggestions using spaCy
        try:
            if spacy_service_manager.is_available():
                nlp_suggestions = await _generate_nlp_suggestions(request.content, request.current_type)
                suggestions.extend(nlp_suggestions)
        except Exception as e:
            logger.warning(f"NLP suggestions failed: {e}")
        
        # Add fallback suggestions if no AI suggestions were generated
        if not suggestions:
            suggestions = _generate_fallback_suggestions(request.content, request.current_type, request.current_cluster)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return AISuggestionsResponse(
            suggestions=suggestions,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error generating AI suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI suggestions: {str(e)}")

@router.post("/categorize", response_model=CategorizationResponse)
async def categorize_memory(request: MemoryCategorizeRequest):
    """
    AI-powered memory categorization using CopilotKit and spaCy.
    
    Suggests the best type and cluster for a memory based on its content.
    """
    try:
        logger.info(f"Categorizing memory for user {request.user_id}")
        
        suggested_type = "context"
        suggested_cluster = "general"
        confidence = 0.5
        reasoning = "Default categorization"
        
        # Use CopilotKit for intelligent categorization
        try:
            categorization_prompt = f"""
            Analyze this memory content and suggest the best categorization:
            Content: "{request.content}"
            
            Choose the best type from: fact, preference, context
            Choose the best cluster from: technical, personal, work, general
            
            Provide your analysis in this format:
            Type: [your choice]
            Cluster: [your choice]
            Confidence: [0.0-1.0]
            Reasoning: [brief explanation]
            """
            
            if copilot_provider:
                copilot_response = await copilot_provider.generate_completion(
                    prompt=categorization_prompt,
                    max_tokens=150,
                    temperature=0.3
                )
            else:
                copilot_response = None
            
            if copilot_response:
                # Parse CopilotKit response
                parsed = _parse_categorization_response(copilot_response)
                if parsed:
                    suggested_type = parsed.get("type", suggested_type)
                    suggested_cluster = parsed.get("cluster", suggested_cluster)
                    confidence = parsed.get("confidence", confidence)
                    reasoning = parsed.get("reasoning", reasoning)
                    
        except Exception as e:
            logger.warning(f"CopilotKit categorization failed: {e}")
        
        # Fallback to rule-based categorization using spaCy
        if confidence < 0.7:
            try:
                if spacy_service_manager.is_available():
                    nlp_categorization = await _categorize_with_nlp(request.content)
                    if nlp_categorization["confidence"] > confidence:
                        suggested_type = nlp_categorization["type"]
                        suggested_cluster = nlp_categorization["cluster"]
                        confidence = nlp_categorization["confidence"]
                        reasoning = nlp_categorization["reasoning"]
            except Exception as e:
                logger.warning(f"NLP categorization failed: {e}")
        
        return CategorizationResponse(
            suggested_type=suggested_type,
            suggested_cluster=suggested_cluster,
            confidence=confidence,
            reasoning=reasoning
        )
        
    except Exception as e:
        logger.error(f"Error categorizing memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to categorize memory: {str(e)}")

# Helper functions
def _parse_copilot_suggestions(response: str, original_content: str) -> List[AISuggestion]:
    """Parse CopilotKit response into structured suggestions."""
    suggestions = []
    
    try:
        lines = response.split('\n')
        current_suggestion = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('1.') or 'enhancement' in line.lower():
                if current_suggestion:
                    suggestions.append(current_suggestion)
                current_suggestion = {
                    "type": "enhancement",
                    "content": "",
                    "confidence": 0.8,
                    "reasoning": ""
                }
            elif line.startswith('2.') or 'categorization' in line.lower():
                if current_suggestion:
                    suggestions.append(current_suggestion)
                current_suggestion = {
                    "type": "categorization", 
                    "content": "",
                    "confidence": 0.7,
                    "reasoning": ""
                }
            elif line.startswith('3.') or 'relationship' in line.lower():
                if current_suggestion:
                    suggestions.append(current_suggestion)
                current_suggestion = {
                    "type": "relationship",
                    "content": "",
                    "confidence": 0.6,
                    "reasoning": ""
                }
            elif line.startswith('4.') or 'correction' in line.lower():
                if current_suggestion:
                    suggestions.append(current_suggestion)
                current_suggestion = {
                    "type": "correction",
                    "content": "",
                    "confidence": 0.9,
                    "reasoning": ""
                }
            elif current_suggestion:
                if not current_suggestion["content"]:
                    current_suggestion["content"] = line
                else:
                    current_suggestion["reasoning"] += " " + line
        
        if current_suggestion:
            suggestions.append(current_suggestion)
            
    except Exception as e:
        logger.warning(f"Error parsing CopilotKit suggestions: {e}")
    
    # Convert to AISuggestion objects
    return [AISuggestion(**suggestion) for suggestion in suggestions if suggestion.get("content")]

async def _generate_nlp_suggestions(content: str, current_type: Optional[str]) -> List[AISuggestion]:
    """Generate suggestions using spaCy NLP analysis."""
    suggestions = []
    
    try:
        # Analyze content with spaCy
        doc = await spacy_service_manager.process_text(content)
        
        if doc:
            # Entity-based suggestions
            if doc.ents:
                entity_text = ", ".join([ent.text for ent in doc.ents])
                suggestions.append(AISuggestion(
                    type="enhancement",
                    content=f"Consider expanding on these key entities: {entity_text}",
                    confidence=0.7,
                    reasoning="Identified important entities that could be elaborated"
                ))
            
            # Sentiment-based type suggestion
            if hasattr(doc, 'sentiment') and current_type != "preference":
                if doc.sentiment.polarity != 0:  # Non-neutral sentiment
                    suggestions.append(AISuggestion(
                        type="categorization",
                        content="Type: preference\nCluster: personal",
                        confidence=0.6,
                        reasoning="Content shows sentiment, suggesting it might be a preference"
                    ))
                    
    except Exception as e:
        logger.warning(f"Error generating NLP suggestions: {e}")
    
    return suggestions

def _generate_fallback_suggestions(content: str, current_type: Optional[str], current_cluster: Optional[str]) -> List[AISuggestion]:
    """Generate basic fallback suggestions when AI is unavailable."""
    suggestions = []
    
    content_lower = content.lower()
    
    # Basic content enhancement
    if len(content) < 50:
        suggestions.append(AISuggestion(
            type="enhancement",
            content=f"{content} [Consider adding more context or details]",
            confidence=0.5,
            reasoning="Content is quite short and could benefit from more detail"
        ))
    
    # Basic categorization suggestions
    if any(word in content_lower for word in ["prefer", "like", "dislike", "favorite"]):
        if current_type != "preference":
            suggestions.append(AISuggestion(
                type="categorization",
                content="Type: preference\nCluster: personal",
                confidence=0.7,
                reasoning="Content contains preference indicators"
            ))
    
    if any(word in content_lower for word in ["code", "programming", "function", "api"]):
        if current_cluster != "technical":
            suggestions.append(AISuggestion(
                type="categorization",
                content=f"Type: {current_type or 'context'}\nCluster: technical",
                confidence=0.8,
                reasoning="Content contains technical terminology"
            ))
    
    return suggestions

def _parse_categorization_response(response: str) -> Optional[Dict[str, Any]]:
    """Parse CopilotKit categorization response."""
    try:
        result = {}
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == "type" and value.lower() in ["fact", "preference", "context"]:
                    result["type"] = value.lower()
                elif key == "cluster" and value.lower() in ["technical", "personal", "work", "general"]:
                    result["cluster"] = value.lower()
                elif key == "confidence":
                    try:
                        result["confidence"] = float(value)
                    except ValueError:
                        pass
                elif key == "reasoning":
                    result["reasoning"] = value
        
        return result if result else None
        
    except Exception as e:
        logger.warning(f"Error parsing categorization response: {e}")
        return None

async def _categorize_with_nlp(content: str) -> Dict[str, Any]:
    """Categorize content using spaCy NLP analysis."""
    try:
        doc = await spacy_service_manager.process_text(content)
        
        if not doc:
            return {
                "type": "context",
                "cluster": "general", 
                "confidence": 0.3,
                "reasoning": "NLP analysis unavailable"
            }
        
        content_lower = content.lower()
        
        # Determine type based on linguistic patterns
        memory_type = "context"
        confidence = 0.5
        
        if any(word in content_lower for word in ["prefer", "like", "dislike", "favorite", "hate"]):
            memory_type = "preference"
            confidence = 0.8
        elif any(word in content_lower for word in ["is", "are", "was", "were", "fact", "true", "false"]):
            memory_type = "fact"
            confidence = 0.7
        
        # Determine cluster based on entities and keywords
        cluster = "general"
        if any(word in content_lower for word in ["code", "programming", "function", "api", "software"]):
            cluster = "technical"
            confidence = min(confidence + 0.1, 1.0)
        elif any(word in content_lower for word in ["work", "project", "task", "business", "meeting"]):
            cluster = "work"
            confidence = min(confidence + 0.1, 1.0)
        elif any(word in content_lower for word in ["family", "friend", "personal", "home"]):
            cluster = "personal"
            confidence = min(confidence + 0.1, 1.0)
        
        return {
            "type": memory_type,
            "cluster": cluster,
            "confidence": confidence,
            "reasoning": f"NLP analysis identified {memory_type} type and {cluster} cluster based on content patterns"
        }
        
    except Exception as e:
        logger.warning(f"Error in NLP categorization: {e}")
        return {
            "type": "context",
            "cluster": "general",
            "confidence": 0.3,
            "reasoning": f"NLP categorization failed: {str(e)}"
        }

# Export router
__all__ = ["router"]