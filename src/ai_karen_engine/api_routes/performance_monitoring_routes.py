"""
Performance Monitoring API Routes

This module provides REST API endpoints for accessing performance metrics,
analytics, A/B testing, user satisfaction data, and optimization recommendations.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Body, Depends
try:
    from pydantic import BaseModel, Field
except ImportError:
    from ai_karen_engine.pydantic_stub import BaseModel, Field

from ..services.response_performance_metrics import (
    performance_collector, 
    ResponsePerformanceMetrics,
    AggregatedMetrics,
    OptimizationType
)
from ..services.ab_testing_system import (
    ab_testing_system,
    ABTest,
    TestVariant,
    TestType,
    TestStatus
)
from ..services.user_satisfaction_tracker import (
    satisfaction_tracker,
    FeedbackType,
    BehaviorSignal,
    SatisfactionMetrics
)
from ..services.optimization_recommendation_engine import (
    recommendation_engine,
    RecommendationType,
    Priority,
    SystemHealthAnalysis
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/performance", tags=["performance"])


# Pydantic models for API requests/responses
class PerformanceMetricsResponse(BaseModel):
    current_metrics: Dict[str, Any]
    aggregated_metrics: Dict[str, Any]
    time_period_hours: int


class FeedbackRequest(BaseModel):
    response_id: str
    feedback_type: str
    rating: Optional[int] = None
    thumbs_up: Optional[bool] = None
    detailed_comment: Optional[str] = None
    context_tags: Optional[List[str]] = None


class BehaviorSignalRequest(BaseModel):
    session_id: str
    signal: str
    response_id: Optional[str] = None


class ABTestRequest(BaseModel):
    name: str
    description: str
    test_type: str
    variants: List[Dict[str, Any]]
    target_sample_size: int = 1000
    confidence_level: float = 0.95
    minimum_effect_size: float = 0.1
    success_metrics: List[str] = ["response_time", "user_satisfaction"]


class RecommendationSuiteRequest(BaseModel):
    name: str
    description: str
    recommendation_ids: List[str]


@router.get("/metrics/current")
async def get_current_metrics():
    """Get current real-time performance metrics"""
    try:
        current_metrics = performance_collector.get_current_metrics()
        return {
            "status": "success",
            "data": current_metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting current metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve current metrics")


@router.get("/metrics/aggregated")
async def get_aggregated_metrics(
    hours: int = Query(24, description="Time period in hours", ge=1, le=168)
):
    """Get aggregated performance metrics for a time period"""
    try:
        time_period = timedelta(hours=hours)
        aggregated_metrics = performance_collector.get_aggregated_metrics(time_period)
        
        return {
            "status": "success",
            "data": {
                "period_start": aggregated_metrics.period_start.isoformat(),
                "period_end": aggregated_metrics.period_end.isoformat(),
                "total_responses": aggregated_metrics.total_responses,
                "avg_response_time": aggregated_metrics.avg_response_time,
                "p95_response_time": aggregated_metrics.p95_response_time,
                "p99_response_time": aggregated_metrics.p99_response_time,
                "avg_cpu_usage": aggregated_metrics.avg_cpu_usage,
                "avg_memory_usage": aggregated_metrics.avg_memory_usage,
                "avg_gpu_usage": aggregated_metrics.avg_gpu_usage,
                "cache_hit_rate": aggregated_metrics.cache_hit_rate,
                "avg_user_satisfaction": aggregated_metrics.avg_user_satisfaction,
                "error_rate": aggregated_metrics.error_rate,
                "throughput": aggregated_metrics.throughput,
                "most_used_models": aggregated_metrics.most_used_models,
                "optimization_effectiveness": {
                    opt.value: effectiveness 
                    for opt, effectiveness in aggregated_metrics.optimization_effectiveness.items()
                },
                "identified_bottlenecks": aggregated_metrics.identified_bottlenecks
            },
            "time_period_hours": hours
        }
    except Exception as e:
        logger.error(f"Error getting aggregated metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve aggregated metrics")


@router.get("/metrics/history")
async def get_metrics_history(
    limit: int = Query(100, description="Maximum number of metrics to return", ge=1, le=1000)
):
    """Get historical performance metrics"""
    try:
        history = performance_collector.get_metrics_history(limit)
        
        # Convert to serializable format
        history_data = []
        for metrics in history:
            data = {
                "response_id": metrics.response_id,
                "timestamp": metrics.timestamp.isoformat(),
                "query": metrics.query,
                "model_used": metrics.model_used,
                "response_time": metrics.response_time,
                "cpu_usage": metrics.cpu_usage,
                "memory_usage": metrics.memory_usage,
                "gpu_usage": metrics.gpu_usage,
                "gpu_memory_usage": metrics.gpu_memory_usage,
                "cache_hit_rate": metrics.cache_hit_rate,
                "user_satisfaction_score": metrics.user_satisfaction_score,
                "model_efficiency": metrics.model_efficiency,
                "content_relevance_score": metrics.content_relevance_score,
                "cuda_acceleration_gain": metrics.cuda_acceleration_gain,
                "optimizations_applied": [opt.value for opt in metrics.optimizations_applied],
                "response_size": metrics.response_size,
                "streaming_chunks": metrics.streaming_chunks,
                "error_occurred": metrics.error_occurred,
                "error_type": metrics.error_type,
                "bottlenecks": metrics.bottlenecks
            }
            history_data.append(data)
        
        return {
            "status": "success",
            "data": history_data,
            "count": len(history_data)
        }
    except Exception as e:
        logger.error(f"Error getting metrics history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics history")


@router.get("/bottlenecks")
async def get_bottleneck_analysis(
    hours: int = Query(24, description="Time period in hours for analysis", ge=1, le=168)
):
    """Get bottleneck analysis for a time period"""
    try:
        time_period = timedelta(hours=hours)
        bottlenecks = performance_collector.analyze_bottlenecks(time_period)
        
        bottleneck_data = []
        for bottleneck in bottlenecks:
            data = {
                "bottleneck_type": bottleneck.bottleneck_type,
                "frequency": bottleneck.frequency,
                "avg_impact": bottleneck.avg_impact,
                "affected_models": bottleneck.affected_models,
                "suggested_optimizations": bottleneck.suggested_optimizations,
                "severity": bottleneck.severity
            }
            bottleneck_data.append(data)
        
        return {
            "status": "success",
            "data": bottleneck_data,
            "time_period_hours": hours
        }
    except Exception as e:
        logger.error(f"Error getting bottleneck analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bottleneck analysis")


@router.post("/feedback")
async def record_user_feedback(
    feedback: FeedbackRequest,
    user_id: str = Query(..., description="User ID"),
    session_id: str = Query(..., description="Session ID")
):
    """Record user feedback for a response"""
    try:
        # Validate feedback type
        try:
            feedback_type = FeedbackType(feedback.feedback_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid feedback type: {feedback.feedback_type}")
        
        feedback_id = satisfaction_tracker.record_explicit_feedback(
            response_id=feedback.response_id,
            user_id=user_id,
            session_id=session_id,
            feedback_type=feedback_type,
            rating=feedback.rating,
            thumbs_up=feedback.thumbs_up,
            detailed_comment=feedback.detailed_comment,
            context_tags=feedback.context_tags
        )
        
        return {
            "status": "success",
            "feedback_id": feedback_id,
            "message": "Feedback recorded successfully"
        }
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to record feedback")


@router.post("/behavior")
async def record_behavior_signal(behavior: BehaviorSignalRequest):
    """Record user behavior signal"""
    try:
        # Validate behavior signal
        try:
            signal = BehaviorSignal(behavior.signal)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid behavior signal: {behavior.signal}")
        
        satisfaction_tracker.record_behavior_signal(
            session_id=behavior.session_id,
            signal=signal,
            response_id=behavior.response_id
        )
        
        return {
            "status": "success",
            "message": "Behavior signal recorded successfully"
        }
    except Exception as e:
        logger.error(f"Error recording behavior signal: {e}")
        raise HTTPException(status_code=500, detail="Failed to record behavior signal")


@router.get("/satisfaction")
async def get_satisfaction_metrics(
    hours: int = Query(24, description="Time period in hours", ge=1, le=168)
):
    """Get user satisfaction metrics"""
    try:
        time_period = timedelta(hours=hours)
        metrics = satisfaction_tracker.get_satisfaction_metrics(time_period)
        
        return {
            "status": "success",
            "data": {
                "period_start": metrics.period_start.isoformat(),
                "period_end": metrics.period_end.isoformat(),
                "total_feedback_count": metrics.total_feedback_count,
                "avg_rating": metrics.avg_rating,
                "satisfaction_distribution": {
                    level.name: count for level, count in metrics.satisfaction_distribution.items()
                },
                "thumbs_up_percentage": metrics.thumbs_up_percentage,
                "net_promoter_score": metrics.net_promoter_score,
                "common_complaints": metrics.common_complaints,
                "common_praise": metrics.common_praise,
                "satisfaction_by_model": metrics.satisfaction_by_model,
                "satisfaction_by_optimization": metrics.satisfaction_by_optimization,
                "behavior_signal_frequency": {
                    signal.name: freq for signal, freq in metrics.behavior_signal_frequency.items()
                },
                "improvement_suggestions": metrics.improvement_suggestions
            },
            "time_period_hours": hours
        }
    except Exception as e:
        logger.error(f"Error getting satisfaction metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve satisfaction metrics")


@router.get("/satisfaction/trends")
async def get_satisfaction_trends(
    hours: int = Query(168, description="Time period in hours for trend analysis", ge=24, le=720)
):
    """Get user satisfaction trends and analysis"""
    try:
        time_period = timedelta(hours=hours)
        analysis = satisfaction_tracker.analyze_feedback_trends(time_period)
        
        return {
            "status": "success",
            "data": {
                "feedback_trend": analysis.feedback_trend,
                "key_issues": analysis.key_issues,
                "positive_patterns": analysis.positive_patterns,
                "model_performance_ranking": analysis.model_performance_ranking,
                "optimization_effectiveness": analysis.optimization_effectiveness,
                "user_segment_insights": analysis.user_segment_insights,
                "actionable_recommendations": analysis.actionable_recommendations
            },
            "time_period_hours": hours
        }
    except Exception as e:
        logger.error(f"Error getting satisfaction trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve satisfaction trends")


@router.post("/ab-tests")
async def create_ab_test(test_request: ABTestRequest):
    """Create a new A/B test"""
    try:
        # Validate test type
        try:
            test_type = TestType(test_request.test_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid test type: {test_request.test_type}")
        
        # Create test variants
        variants = []
        for variant_data in test_request.variants:
            variant = TestVariant(
                id=variant_data["id"],
                name=variant_data["name"],
                description=variant_data["description"],
                configuration=variant_data["configuration"],
                traffic_percentage=variant_data["traffic_percentage"],
                is_control=variant_data.get("is_control", False)
            )
            variants.append(variant)
        
        test_id = ab_testing_system.create_test(
            name=test_request.name,
            description=test_request.description,
            test_type=test_type,
            variants=variants,
            target_sample_size=test_request.target_sample_size,
            confidence_level=test_request.confidence_level,
            minimum_effect_size=test_request.minimum_effect_size,
            success_metrics=test_request.success_metrics
        )
        
        return {
            "status": "success",
            "test_id": test_id,
            "message": "A/B test created successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        raise HTTPException(status_code=500, detail="Failed to create A/B test")


@router.post("/ab-tests/{test_id}/start")
async def start_ab_test(test_id: str):
    """Start an A/B test"""
    try:
        success = ab_testing_system.start_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found or cannot be started")
        
        return {
            "status": "success",
            "message": f"A/B test {test_id} started successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting A/B test: {e}")
        raise HTTPException(status_code=500, detail="Failed to start A/B test")


@router.post("/ab-tests/{test_id}/stop")
async def stop_ab_test(test_id: str):
    """Stop an A/B test and analyze results"""
    try:
        success = ab_testing_system.stop_test(test_id)
        if not success:
            raise HTTPException(status_code=404, detail="Test not found or cannot be stopped")
        
        return {
            "status": "success",
            "message": f"A/B test {test_id} stopped successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping A/B test: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop A/B test")


@router.get("/ab-tests")
async def get_ab_tests(
    status: Optional[str] = Query(None, description="Filter by test status"),
    limit: int = Query(50, description="Maximum number of tests to return", ge=1, le=100)
):
    """Get A/B tests"""
    try:
        if status == "active":
            tests = ab_testing_system.get_active_tests()
        else:
            tests = ab_testing_system.get_test_history(limit)
        
        # Filter by status if specified
        if status and status != "active":
            try:
                status_enum = TestStatus(status)
                tests = [t for t in tests if t.status == status_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        # Convert to serializable format
        tests_data = []
        for test in tests:
            test_data = {
                "id": test.id,
                "name": test.name,
                "description": test.description,
                "test_type": test.test_type.value,
                "status": test.status.value,
                "start_date": test.start_date.isoformat() if test.start_date else None,
                "end_date": test.end_date.isoformat() if test.end_date else None,
                "target_sample_size": test.target_sample_size,
                "confidence_level": test.confidence_level,
                "minimum_effect_size": test.minimum_effect_size,
                "success_metrics": test.success_metrics,
                "created_by": test.created_by,
                "created_at": test.created_at.isoformat(),
                "updated_at": test.updated_at.isoformat(),
                "variants": [
                    {
                        "id": v.id,
                        "name": v.name,
                        "description": v.description,
                        "traffic_percentage": v.traffic_percentage,
                        "is_control": v.is_control
                    }
                    for v in test.variants
                ],
                "results": test.results
            }
            tests_data.append(test_data)
        
        return {
            "status": "success",
            "data": tests_data,
            "count": len(tests_data)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting A/B tests: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve A/B tests")


@router.get("/ab-tests/{test_id}/status")
async def get_ab_test_status(test_id: str):
    """Get current status and metrics for an A/B test"""
    try:
        status = ab_testing_system.get_test_status(test_id)
        if not status:
            raise HTTPException(status_code=404, detail="Test not found")
        
        return {
            "status": "success",
            "data": status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting A/B test status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve test status")


@router.get("/recommendations")
async def get_optimization_recommendations(
    priority: Optional[str] = Query(None, description="Filter by priority"),
    recommendation_type: Optional[str] = Query(None, description="Filter by type"),
    implemented: bool = Query(False, description="Include implemented recommendations")
):
    """Get optimization recommendations"""
    try:
        recommendations = recommendation_engine.generate_recommendations(force_analysis=True)
        
        # Filter recommendations
        if priority:
            try:
                priority_enum = Priority(priority)
                recommendations = [r for r in recommendations if r.priority == priority_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")
        
        if recommendation_type:
            try:
                type_enum = RecommendationType(recommendation_type)
                recommendations = [r for r in recommendations if r.recommendation_type == type_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid recommendation type: {recommendation_type}")
        
        if not implemented:
            recommendations = [r for r in recommendations if not r.implemented]
        
        # Convert to serializable format
        recommendations_data = []
        for rec in recommendations:
            data = {
                "id": rec.id,
                "title": rec.title,
                "description": rec.description,
                "recommendation_type": rec.recommendation_type.value,
                "priority": rec.priority.value,
                "complexity": rec.complexity.value,
                "estimated_impact": rec.estimated_impact,
                "confidence_score": rec.confidence_score,
                "supporting_data": rec.supporting_data,
                "implementation_steps": rec.implementation_steps,
                "success_metrics": rec.success_metrics,
                "estimated_effort_hours": rec.estimated_effort_hours,
                "prerequisites": rec.prerequisites,
                "risks": rec.risks,
                "created_at": rec.created_at.isoformat(),
                "expires_at": rec.expires_at.isoformat() if rec.expires_at else None,
                "implemented": rec.implemented,
                "implementation_date": rec.implementation_date.isoformat() if rec.implementation_date else None,
                "actual_impact": rec.actual_impact
            }
            recommendations_data.append(data)
        
        return {
            "status": "success",
            "data": recommendations_data,
            "count": len(recommendations_data)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recommendations")


@router.get("/recommendations/quick-wins")
async def get_quick_wins(
    max_effort_hours: int = Query(8, description="Maximum effort hours for quick wins", ge=1, le=40)
):
    """Get quick win recommendations (high impact, low effort)"""
    try:
        quick_wins = recommendation_engine.get_quick_wins(max_effort_hours)
        
        # Convert to serializable format
        quick_wins_data = []
        for rec in quick_wins:
            data = {
                "id": rec.id,
                "title": rec.title,
                "description": rec.description,
                "estimated_impact": rec.estimated_impact,
                "estimated_effort_hours": rec.estimated_effort_hours,
                "impact_effort_ratio": rec.estimated_impact / max(rec.estimated_effort_hours, 1),
                "complexity": rec.complexity.value,
                "implementation_steps": rec.implementation_steps,
                "success_metrics": rec.success_metrics
            }
            quick_wins_data.append(data)
        
        return {
            "status": "success",
            "data": quick_wins_data,
            "count": len(quick_wins_data)
        }
    except Exception as e:
        logger.error(f"Error getting quick wins: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quick wins")


@router.get("/health")
async def get_system_health():
    """Get overall system health analysis"""
    try:
        health_analysis = recommendation_engine.analyze_system_health()
        
        return {
            "status": "success",
            "data": {
                "overall_health_score": health_analysis.overall_health_score,
                "performance_score": health_analysis.performance_score,
                "satisfaction_score": health_analysis.satisfaction_score,
                "resource_efficiency_score": health_analysis.resource_efficiency_score,
                "critical_issues": health_analysis.critical_issues,
                "improvement_opportunities": health_analysis.improvement_opportunities,
                "trending_metrics": health_analysis.trending_metrics,
                "bottleneck_analysis": health_analysis.bottleneck_analysis
            }
        }
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system health")


@router.post("/recommendations/{recommendation_id}/implement")
async def mark_recommendation_implemented(
    recommendation_id: str,
    actual_impact: Optional[float] = Body(None, description="Actual impact achieved")
):
    """Mark a recommendation as implemented"""
    try:
        success = recommendation_engine.mark_recommendation_implemented(
            recommendation_id, actual_impact
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        return {
            "status": "success",
            "message": f"Recommendation {recommendation_id} marked as implemented"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking recommendation as implemented: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark recommendation as implemented")


@router.get("/dashboard")
async def get_performance_dashboard():
    """Get comprehensive performance dashboard data"""
    try:
        # Collect all dashboard data
        current_metrics = performance_collector.get_current_metrics()
        aggregated_metrics = performance_collector.get_aggregated_metrics(timedelta(hours=24))
        satisfaction_metrics = satisfaction_tracker.get_satisfaction_metrics(timedelta(hours=24))
        health_analysis = recommendation_engine.analyze_system_health()
        active_tests = ab_testing_system.get_active_tests()
        recent_recommendations = recommendation_engine.get_recommendations_by_priority(Priority.HIGH)
        
        dashboard_data = {
            "current_metrics": current_metrics,
            "performance_summary": {
                "avg_response_time": aggregated_metrics.avg_response_time,
                "p95_response_time": aggregated_metrics.p95_response_time,
                "throughput": aggregated_metrics.throughput,
                "error_rate": aggregated_metrics.error_rate,
                "cache_hit_rate": aggregated_metrics.cache_hit_rate
            },
            "satisfaction_summary": {
                "avg_rating": satisfaction_metrics.avg_rating,
                "thumbs_up_percentage": satisfaction_metrics.thumbs_up_percentage,
                "net_promoter_score": satisfaction_metrics.net_promoter_score,
                "total_feedback_count": satisfaction_metrics.total_feedback_count
            },
            "health_analysis": {
                "overall_health_score": health_analysis.overall_health_score,
                "performance_score": health_analysis.performance_score,
                "satisfaction_score": health_analysis.satisfaction_score,
                "resource_efficiency_score": health_analysis.resource_efficiency_score,
                "critical_issues": health_analysis.critical_issues
            },
            "active_ab_tests": len(active_tests),
            "high_priority_recommendations": len(recent_recommendations),
            "model_usage": aggregated_metrics.most_used_models,
            "optimization_effectiveness": {
                opt.value: effectiveness 
                for opt, effectiveness in aggregated_metrics.optimization_effectiveness.items()
            }
        }
        
        return {
            "status": "success",
            "data": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@router.post("/export")
async def export_performance_data(
    hours: int = Query(168, description="Hours of data to export", ge=1, le=720),
    format: str = Query("json", description="Export format (json)")
):
    """Export performance data"""
    try:
        if format != "json":
            raise HTTPException(status_code=400, detail="Only JSON format is currently supported")
        
        # Export metrics to temporary file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            performance_collector.export_metrics(f.name, timedelta(hours=hours))
            temp_file = f.name
        
        # Read the exported data
        with open(temp_file, 'r') as f:
            export_data = json.load(f)
        
        # Clean up temporary file
        os.unlink(temp_file)
        
        return {
            "status": "success",
            "data": export_data,
            "exported_records": len(export_data),
            "time_period_hours": hours
        }
    except Exception as e:
        logger.error(f"Error exporting performance data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export performance data")