"""
PerformanceAdaptiveRouter initialization script for Karen AI

This module provides initialization and startup code for the PerformanceAdaptiveRouter
to ensure it's properly integrated with the main Karen AI system.
"""

import asyncio
import logging
import os
import threading
import time
from typing import Optional

from .performance_adaptive_router import (
    AdaptiveConfig,
    PerformanceAdaptiveRouter,
    get_performance_adaptive_router,
    initialize_performance_adaptive_router
)

logger = logging.getLogger(__name__)


def load_config_from_environment() -> AdaptiveConfig:
    """Load PerformanceAdaptiveRouter configuration from environment variables."""
    return AdaptiveConfig(
        # Core settings
        enable_adaptive_routing=os.environ.get('KAREN_ENABLE_ADAPTIVE_ROUTING', 'true').lower() == 'true',
        enable_predictive_routing=os.environ.get('KAREN_ENABLE_PREDICTIVE_ROUTING', 'true').lower() == 'true',
        enable_ml_optimization=os.environ.get('KAREN_ENABLE_ML_OPTIMIZATION', 'true').lower() == 'true',
        
        # Performance monitoring
        metrics_collection_interval=float(os.environ.get('KAREN_METRICS_INTERVAL', '5.0')),
        performance_history_size=int(os.environ.get('KAREN_PERFORMANCE_HISTORY_SIZE', '1000')),
        anomaly_detection_enabled=os.environ.get('KAREN_ANOMALY_DETECTION', 'true').lower() == 'true',
        anomaly_threshold=float(os.environ.get('KAREN_ANOMALY_THRESHOLD', '2.0')),
        
        # Adaptive routing
        routing_update_interval=float(os.environ.get('KAREN_ROUTING_UPDATE_INTERVAL', '30.0')),
        strategy_switch_threshold=float(os.environ.get('KAREN_STRATEGY_SWITCH_THRESHOLD', '0.2')),
        load_balancing_enabled=os.environ.get('KAREN_LOAD_BALANCING', 'true').lower() == 'true',
        max_concurrent_routes=int(os.environ.get('KAREN_MAX_CONCURRENT_ROUTES', '10')),
        
        # Machine learning
        ml_model_update_interval=float(os.environ.get('KAREN_ML_UPDATE_INTERVAL', '300.0')),
        prediction_confidence_threshold=float(os.environ.get('KAREN_PREDICTION_CONFIDENCE', '0.7')),
        min_training_samples=int(os.environ.get('KAREN_MIN_TRAINING_SAMPLES', '100')),
        
        # Optimization
        auto_optimization_enabled=os.environ.get('KAREN_AUTO_OPTIMIZATION', 'true').lower() == 'true',
        optimization_interval=float(os.environ.get('KAREN_OPTIMIZATION_INTERVAL', '600.0')),
        performance_degradation_threshold=float(os.environ.get('KAREN_PERFORMANCE_DEGRADATION_THRESHOLD', '0.15')),
        
        # Analytics and reporting
        analytics_history_size=int(os.environ.get('KAREN_ANALYTICS_HISTORY_SIZE', '5000')),
        enable_performance_dashboard=os.environ.get('KAREN_PERFORMANCE_DASHBOARD', 'true').lower() == 'true',
        report_generation_interval=float(os.environ.get('KAREN_REPORT_INTERVAL', '3600.0')),
        
        # Integration settings
        integrate_with_fallback_manager=os.environ.get('KAREN_INTEGRATE_FALLBACK', 'true').lower() == 'true',
        integrate_with_health_monitor=os.environ.get('KAREN_INTEGRATE_HEALTH', 'true').lower() == 'true',
        integrate_with_provider_switcher=os.environ.get('KAREN_INTEGRATE_SWITCHER', 'true').lower() == 'true'
    )


def initialize_performance_router_sync() -> PerformanceAdaptiveRouter:
    """
    Initialize the PerformanceAdaptiveRouter synchronously.
    
    This function provides a synchronous interface for initializing the router
    without requiring an async context, making it easier to call from
    synchronous initialization code.
    """
    try:
        # Load configuration
        config = load_config_from_environment()
        
        # Get the global router instance
        router = get_performance_adaptive_router(config)
        
        # Start monitoring in a background thread
        def start_monitoring():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(router.start_monitoring())
            except Exception as e:
                logger.error(f"Failed to start performance monitoring: {e}")
            finally:
                loop.close()
        
        monitoring_thread = threading.Thread(target=start_monitoring, daemon=True)
        monitoring_thread.start()
        
        logger.info("PerformanceAdaptiveRouter initialized and monitoring started in background thread")
        
        return router
        
    except Exception as e:
        logger.error(f"Failed to initialize PerformanceAdaptiveRouter: {e}")
        raise


async def initialize_performance_router_async() -> PerformanceAdaptiveRouter:
    """
    Initialize the PerformanceAdaptiveRouter asynchronously.
    
    This function provides an async interface for initializing the router
    for use in async contexts.
    """
    try:
        # Load configuration
        config = load_config_from_environment()
        
        # Initialize and start monitoring
        router = await initialize_performance_adaptive_router(config)
        
        logger.info("PerformanceAdaptiveRouter initialized and monitoring started")
        
        return router
        
    except Exception as e:
        logger.error(f"Failed to initialize PerformanceAdaptiveRouter: {e}")
        raise


def get_performance_router_status() -> dict:
    """
    Get the current status of the PerformanceAdaptiveRouter.
    
    Returns a dictionary with status information about the router.
    """
    try:
        router = get_performance_adaptive_router()
        
        # Get basic status
        status = {
            "initialized": router is not None,
            "monitoring_active": router._monitoring_active if router else False,
            "current_strategy": router._current_strategy.value if router else None,
            "providers_monitored": len(router._provider_metrics) if router else 0,
            "routing_decisions_count": len(router._routing_decisions) if router else 0,
            "anomalies_detected": router._analytics.anomalies_detected if router else 0,
            "last_updated": time.time()
        }
        
        # Add analytics if available
        if router:
            analytics = router.get_routing_analytics()
            status.update({
                "total_requests": analytics.total_requests,
                "successful_requests": analytics.successful_requests,
                "failed_requests": analytics.failed_requests,
                "routing_accuracy": analytics.routing_accuracy,
                "average_latency": analytics.average_latency,
                "provider_usage": analytics.provider_usage_counts,
                "strategy_usage": analytics.strategy_usage
            })
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get PerformanceAdaptiveRouter status: {e}")
        return {
            "initialized": False,
            "error": str(e),
            "last_updated": time.time()
        }


def shutdown_performance_router() -> None:
    """
    Shutdown the PerformanceAdaptiveRouter gracefully.
    
    This function stops monitoring and cleans up resources.
    """
    try:
        router = get_performance_adaptive_router()
        if router:
            # Stop monitoring
            if router._monitoring_active:
                asyncio.create_task(router.stop_monitoring())
                logger.info("PerformanceAdaptiveRouter monitoring stopped")
            else:
                logger.info("PerformanceAdaptiveRouter was not active")
        else:
            logger.info("PerformanceAdaptiveRouter was not initialized")
            
    except Exception as e:
        logger.error(f"Failed to shutdown PerformanceAdaptiveRouter: {e}")


# Export functions for easy import
__all__ = [
    "load_config_from_environment",
    "initialize_performance_router_sync",
    "initialize_performance_router_async",
    "get_performance_router_status",
    "shutdown_performance_router"
]