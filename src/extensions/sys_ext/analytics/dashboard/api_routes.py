"""API routes for enhanced analytics dashboard."""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from ai_karen_engine.extensions.manager import ExtensionManager
from .analytics_extension import AnalyticsDashboardExtension

logger = logging.getLogger(__name__)

# Pydantic models for API responses
class ConversationAnalyticsResponse(BaseModel):
    timestamp: str
    message_count: int
    response_time: float
    user_satisfaction: float
    ai_insights: int
    token_usage: int
    llm_provider: str

class MemoryNetworkResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    clusters: List[str]
    total_memories: int

class UserEngagementResponse(BaseModel):
    timestamp: str
    user_id: str
    component_type: str
    component_id: str
    interaction_type: str
    duration: int
    success: bool
    error_message: Optional[str] = None

class AnalyticsStatsResponse(BaseModel):
    total_conversations: int
    total_messages: int
    avg_response_time: float
    avg_satisfaction: float
    total_insights: int
    active_users: int
    top_llm_providers: List[Dict[str, Any]]

# Create router
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

def get_analytics_extension() -> AnalyticsDashboardExtension:
    """Get the analytics extension instance."""
    try:
        extension_manager = ExtensionManager()
        extension = extension_manager.get_extension_by_name("analytics-dashboard")
        if not extension or not isinstance(extension.instance, AnalyticsDashboardExtension):
            raise HTTPException(status_code=503, detail="Analytics extension not available")
        return extension.instance
    except Exception as e:
        logger.error(f"Failed to get analytics extension: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")

@router.get("/conversation-data", response_model=List[ConversationAnalyticsResponse])
async def get_conversation_analytics(
    timeframe: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    user_id: Optional[str] = Query(None),
    extension: AnalyticsDashboardExtension = Depends(get_analytics_extension)
):
    """Get conversation analytics data for AG-UI charts."""
    try:
        data = await extension.get_conversation_analytics(timeframe, user_id)
        return [ConversationAnalyticsResponse(**item) for item in data]
    except Exception as e:
        logger.error(f"Failed to get conversation analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation analytics")

@router.get("/memory-network", response_model=MemoryNetworkResponse)
async def get_memory_network(
    user_id: Optional[str] = Query(None),
    extension: AnalyticsDashboardExtension = Depends(get_analytics_extension)
):
    """Get memory network data for AG-UI network visualization."""
    try:
        data = await extension.get_memory_network_data(user_id)
        return MemoryNetworkResponse(**data)
    except Exception as e:
        logger.error(f"Failed to get memory network data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve memory network data")

@router.get("/user-engagement", response_model=List[UserEngagementResponse])
async def get_user_engagement(
    user_id: Optional[str] = Query(None),
    extension: AnalyticsDashboardExtension = Depends(get_analytics_extension)
):
    """Get user engagement data for AG-UI data grids."""
    try:
        data = await extension.get_user_engagement_grid_data(user_id)
        return [UserEngagementResponse(**item) for item in data]
    except Exception as e:
        logger.error(f"Failed to get user engagement data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user engagement data")

@router.get("/stats", response_model=AnalyticsStatsResponse)
async def get_analytics_stats(
    timeframe: str = Query("24h", regex="^(1h|24h|7d|30d)$"),
    extension: AnalyticsDashboardExtension = Depends(get_analytics_extension)
):
    """Get aggregated analytics statistics."""
    try:
        # Get conversation data
        conversation_data = await extension.get_conversation_analytics(timeframe)
        
        if not conversation_data:
            return AnalyticsStatsResponse(
                total_conversations=0,
                total_messages=0,
                avg_response_time=0.0,
                avg_satisfaction=0.0,
                total_insights=0,
                active_users=0,
                top_llm_providers=[]
            )
        
        # Calculate statistics
        total_conversations = len(set(item.get('message_id', '') for item in conversation_data))
        total_messages = len(conversation_data)
        avg_response_time = sum(item.get('response_time', 0) for item in conversation_data) / len(conversation_data)
        avg_satisfaction = sum(item.get('user_satisfaction', 0) for item in conversation_data) / len(conversation_data)
        total_insights = sum(item.get('ai_insights_count', 0) for item in conversation_data)
        active_users = len(set(item.get('user_id', '') for item in conversation_data if item.get('user_id')))
        
        # Top LLM providers
        provider_counts = {}
        for item in conversation_data:
            provider = item.get('llm_provider', 'unknown')
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
        
        top_providers = [
            {'provider': provider, 'count': count}
            for provider, count in sorted(provider_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        return AnalyticsStatsResponse(
            total_conversations=total_conversations,
            total_messages=total_messages,
            avg_response_time=round(avg_response_time, 2),
            avg_satisfaction=round(avg_satisfaction, 2),
            total_insights=total_insights,
            active_users=active_users,
            top_llm_providers=top_providers
        )
        
    except Exception as e:
        logger.error(f"Failed to get analytics stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics statistics")

@router.get("/prometheus-metrics")
async def get_prometheus_metrics(
    extension: AnalyticsDashboardExtension = Depends(get_analytics_extension)
):
    """Get Prometheus metrics in text format."""
    try:
        metrics = await extension.get_prometheus_metrics()
        return {"metrics": metrics, "content_type": "text/plain"}
    except Exception as e:
        logger.error(f"Failed to get Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve Prometheus metrics")

@router.get("/health")
async def get_analytics_health(
    extension: AnalyticsDashboardExtension = Depends(get_analytics_extension)
):
    """Get analytics service health status."""
    try:
        status = await extension.get_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get analytics health: {e}")
        raise HTTPException(status_code=500, detail="Analytics service health check failed")

# Export router for inclusion in main FastAPI app
__all__ = ["router"]