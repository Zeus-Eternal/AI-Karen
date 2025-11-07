"""Production analytics API routes for Kari."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

from ai_karen_engine.core.dependencies import AnalyticsService_Dep
from ai_karen_engine.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter()


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
    average_session_duration: float = Field(
        ..., description="Average session duration in minutes"
    )
    time_range: str = Field(..., description="Time range for the analytics")
    timestamp: str = Field(..., description="Timestamp when analytics were generated")


class FeatureUsage(BaseModel):
    """Feature usage statistics."""

    name: str = Field(..., description="Feature name")
    usage_count: int = Field(..., description="Number of times used")


@router.get("/usage", response_model=UsageAnalytics)
async def get_usage_analytics(
    range: str = Query(default="24h", description="Time range (e.g., 24h, 7d, 30d)"),
    analytics_service: AnalyticsService = AnalyticsService_Dep,
) -> UsageAnalytics:
    """
    Get usage analytics for the specified time range.
    
    Args:
        range: Time range for analytics (24h, 7d, 30d, etc.)
        
    Returns:
        Usage analytics data
    """
    try:
        logger.info("Fetching usage analytics for range %s", range)

        hours = AnalyticsService.parse_time_range(range)
        usage_report = analytics_service.get_usage_report(hours)
        analytics_data = UsageAnalytics(
            total_interactions=usage_report["total_interactions"],
            unique_users=usage_report["unique_users"],
            popular_features=usage_report["popular_features"],
            peak_hours=usage_report["peak_hours"],
            user_satisfaction=usage_report["user_satisfaction"],
            average_session_duration=usage_report["average_session_minutes"],
            time_range=range,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.debug(
            "Usage analytics calculated: %s interactions, %s users",
            analytics_data.total_interactions,
            analytics_data.unique_users,
        )
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
    range: str = Query(default="24h", description="Time range (e.g., 24h, 7d, 30d)"),
    analytics_service: AnalyticsService = AnalyticsService_Dep,
) -> List[FeatureUsage]:
    """
    Get feature usage statistics for the specified time range.
    
    Args:
        range: Time range for analytics
        
    Returns:
        List of feature usage statistics
    """
    try:
        logger.info("Fetching feature usage for range %s", range)

        hours = AnalyticsService.parse_time_range(range)
        usage_report = analytics_service.get_usage_report(hours)
        features = [
            FeatureUsage(name=feature["name"], usage_count=feature["usage_count"])
            for feature in usage_report["popular_features"]
        ]

        return features
        
    except Exception as e:
        logger.error(f"Failed to fetch feature usage: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch feature usage statistics"
        )


@router.get("/summary")
async def get_analytics_summary(
    analytics_service: AnalyticsService = AnalyticsService_Dep,
) -> Dict[str, Any]:
    """
    Get a summary of key analytics metrics.
    
    Returns:
        Summary of key metrics
    """
    try:
        logger.info("Fetching analytics summary")

        daily_hours = AnalyticsService.parse_time_range("24h")
        weekly_hours = AnalyticsService.parse_time_range("7d")
        monthly_hours = AnalyticsService.parse_time_range("30d")

        daily_report = analytics_service.get_usage_report(daily_hours)
        weekly_report = analytics_service.get_usage_report(weekly_hours)
        monthly_report = analytics_service.get_usage_report(monthly_hours)
        system_summary = analytics_service.get_analytics_summary()

        return {
            "daily": {
                "interactions": daily_report["total_interactions"],
                "users": daily_report["unique_users"],
                "satisfaction": daily_report["user_satisfaction"],
                "average_session_duration": daily_report["average_session_minutes"],
                "peak_hours": daily_report["peak_hours"],
            },
            "weekly": {
                "interactions": weekly_report["total_interactions"],
                "users": weekly_report["unique_users"],
                "satisfaction": weekly_report["user_satisfaction"],
                "average_session_duration": weekly_report["average_session_minutes"],
                "peak_hours": weekly_report["peak_hours"],
            },
            "monthly": {
                "interactions": monthly_report["total_interactions"],
                "users": monthly_report["unique_users"],
                "satisfaction": monthly_report["user_satisfaction"],
                "average_session_duration": monthly_report["average_session_minutes"],
                "peak_hours": monthly_report["peak_hours"],
            },
            "system": system_summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch analytics summary: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch analytics summary"
        )