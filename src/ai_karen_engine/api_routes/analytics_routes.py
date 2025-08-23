"""
Analytics API Routes
Provides usage analytics and metrics endpoints for the web UI.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# Debug: Log when router is created
logger.info("Analytics router created successfully")


class UsageAnalytics(BaseModel):
    """Usage analytics response matching frontend interface."""
    
    total_interactions: int = Field(..., description="Total number of interactions")
    unique_users: int = Field(..., description="Number of unique users")
    popular_features: List[Dict[str, Any]] = Field(
        default_factory=list, description="Most popular features"
    )
    peak_hours: List[int] = Field(
        default_factory=list, description="Peak usage hours (0-23)"
    )
    user_satisfaction: float = Field(..., description="User satisfaction score (0-100)")
    time_range: str = Field(..., description="Time range for the analytics")
    timestamp: str = Field(..., description="Timestamp when analytics were generated")


class FeatureUsage(BaseModel):
    """Feature usage statistics."""
    
    name: str = Field(..., description="Feature name")
    usage_count: int = Field(..., description="Number of times used")


async def get_mock_analytics_data(time_range: str) -> UsageAnalytics:
    """
    Generate mock analytics data for development.
    In production, this would query actual database metrics.
    """
    # Parse time range
    hours = 24  # default
    if time_range.endswith('h'):
        hours = int(time_range[:-1])
    elif time_range.endswith('d'):
        hours = int(time_range[:-1]) * 24
    elif time_range.endswith('w'):
        hours = int(time_range[:-1]) * 24 * 7
    elif time_range.endswith('m'):
        hours = int(time_range[:-1]) * 24 * 30
    
    # Generate realistic mock data based on time range
    base_interactions = max(10, hours * 2)
    
    return UsageAnalytics(
        total_interactions=base_interactions + (hours // 24) * 15,
        unique_users=max(1, (base_interactions // 10) + (hours // 48)),
        popular_features=[
            {"name": "Chat Conversations", "usage_count": base_interactions // 2},
            {"name": "Code Generation", "usage_count": base_interactions // 3},
            {"name": "File Analysis", "usage_count": base_interactions // 4},
            {"name": "Memory Search", "usage_count": base_interactions // 5},
            {"name": "Plugin Execution", "usage_count": base_interactions // 6},
        ],
        peak_hours=[9, 10, 11, 14, 15, 16, 20, 21],  # Typical work hours + evening
        user_satisfaction=85.5,  # Mock satisfaction score
        time_range=time_range,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/usage", response_model=UsageAnalytics)
async def get_usage_analytics(
    range: str = Query(default="24h", description="Time range (e.g., 24h, 7d, 30d)")
) -> UsageAnalytics:
    """
    Get usage analytics for the specified time range.
    
    Args:
        range: Time range for analytics (24h, 7d, 30d, etc.)
        
    Returns:
        Usage analytics data
    """
    try:
        logger.info(f"Fetching usage analytics for range: {range}")
        
        # For now, return mock data
        # TODO: Implement actual database queries for real analytics
        analytics_data = await get_mock_analytics_data(range)
        
        logger.debug(f"Generated analytics data: {analytics_data.total_interactions} interactions")
        return analytics_data
        
    except ValueError as e:
        logger.error(f"Invalid time range format: {range} - {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid time range format: {range}. Use formats like 24h, 7d, 30d"
        )
    except Exception as e:
        logger.error(f"Failed to fetch usage analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch usage analytics"
        )


@router.get("/features", response_model=List[FeatureUsage])
async def get_feature_usage(
    range: str = Query(default="24h", description="Time range (e.g., 24h, 7d, 30d)")
) -> List[FeatureUsage]:
    """
    Get feature usage statistics for the specified time range.
    
    Args:
        range: Time range for analytics
        
    Returns:
        List of feature usage statistics
    """
    try:
        logger.info(f"Fetching feature usage for range: {range}")
        
        # Generate mock feature usage data
        analytics_data = await get_mock_analytics_data(range)
        
        features = [
            FeatureUsage(name=feature["name"], usage_count=feature["usage_count"])
            for feature in analytics_data.popular_features
        ]
        
        return features
        
    except Exception as e:
        logger.error(f"Failed to fetch feature usage: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch feature usage statistics"
        )


@router.get("/summary")
async def get_analytics_summary() -> Dict[str, Any]:
    """
    Get a summary of key analytics metrics.
    
    Returns:
        Summary of key metrics
    """
    try:
        logger.info("Fetching analytics summary")
        
        # Get data for different time ranges
        daily_data = await get_mock_analytics_data("24h")
        weekly_data = await get_mock_analytics_data("7d")
        monthly_data = await get_mock_analytics_data("30d")
        
        return {
            "daily": {
                "interactions": daily_data.total_interactions,
                "users": daily_data.unique_users,
                "satisfaction": daily_data.user_satisfaction,
            },
            "weekly": {
                "interactions": weekly_data.total_interactions,
                "users": weekly_data.unique_users,
                "satisfaction": weekly_data.user_satisfaction,
            },
            "monthly": {
                "interactions": monthly_data.total_interactions,
                "users": monthly_data.unique_users,
                "satisfaction": monthly_data.user_satisfaction,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch analytics summary: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch analytics summary"
        )