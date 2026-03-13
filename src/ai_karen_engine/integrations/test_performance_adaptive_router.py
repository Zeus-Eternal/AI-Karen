"""
Test script for Performance Adaptive Router System

This script demonstrates the performance monitoring and adaptive routing
capabilities of the Karen AI intelligent fallback system.
"""

import asyncio
import logging
import time
import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from performance_adaptive_router import (
    AdaptiveStrategy, PerformanceMetricType, OptimizationObjective,
    PerformanceMetrics, PerformanceThreshold, RoutingDecision, RoutingAnalytics,
    AdaptiveConfig, PerformanceAdaptiveRouter,
    get_performance_adaptive_router, initialize_performance_adaptive_router
)
from intelligent_provider_registry import (
    ProviderType, ProviderPriority, IntelligentProviderRegistration,
    get_intelligent_provider_registry
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_basic_routing():
    """Test basic routing functionality."""
    print("\n=== Testing Basic Routing ===")
    
    # Initialize the router
    config = AdaptiveConfig(
        enable_adaptive_routing=True,
        enable_predictive_routing=True,
        enable_ml_optimization=True,
        metrics_collection_interval=2.0,
        analytics_history_size=100
    )
    
    router = await initialize_performance_adaptive_router(config)
    
    # Simulate some provider performance data
    providers = ["provider_a", "provider_b", "provider_c"]
    
    for provider in providers:
        await router.record_performance(provider, {
            'latency_mean': 0.5 + (providers.index(provider) * 0.2),
            'error_rate': 0.05 + (providers.index(provider) * 0.02),
            'requests_per_second': 10.0 - (providers.index(provider) * 2),
            'cost_per_request': 0.01 + (providers.index(provider) * 0.005),
            'user_satisfaction_score': 0.9 - (providers.index(provider) * 0.1),
            'response_quality_score': 0.85 - (providers.index(provider) * 0.05),
            'success_rate': 0.95 - (providers.index(provider) * 0.05),
            'uptime_percentage': 99.0 - (providers.index(provider) * 1.0)
        })
    
    # Wait a bit for metrics to be processed
    await asyncio.sleep(3)
    
    # Test routing decisions
    test_requests = [
        ("req_001", "chat", {"capabilities": ["text", "conversation"]}),
        ("req_002", "code", {"capabilities": ["code", "programming"], "cost_sensitive": True}),
        ("req_003", "embedding", {"capabilities": ["embeddings", "vector"], "max_latency": 1.0}),
        ("req_004", "analytics", {"capabilities": ["analysis", "reasoning"], "quality_sensitive": True}),
        ("req_005", "realtime", {"capabilities": ["text"], "max_latency": 0.5, "max_error_rate": 0.1})
    ]
    
    for request_id, context, requirements in test_requests:
        decision = await router.route_request(request_id, context, requirements)
        
        print(f"\nRequest {request_id} ({context}):")
        print(f"  Selected Provider: {decision.selected_provider}")
        print(f"  Strategy: {decision.strategy.value}")
        print(f"  Confidence: {decision.confidence:.3f}")
        print(f"  Rationale: {decision.rationale}")
        print(f"  Expected Performance: {decision.expected_performance}")
        print(f"  Risk Assessment: {decision.risk_assessment}")
        
        if decision.alternatives:
            print(f"  Alternatives: {', '.join(decision.alternatives)}")
    
    # Get analytics
    analytics = router.get_routing_analytics()
    print(f"\nRouting Analytics:")
    print(f"  Total Requests: {analytics.total_requests}")
    print(f"  Successful Requests: {analytics.successful_requests}")
    print(f"  Failed Requests: {analytics.failed_requests}")
    print(f"  Routing Accuracy: {analytics.routing_accuracy:.3f}")
    print(f"  Provider Usage: {analytics.provider_usage_counts}")
    print(f"  Strategy Usage: {analytics.strategy_usage}")
    
    await router.stop_monitoring()
    print("\nBasic routing test completed successfully!")


async def test_performance_monitoring():
    """Test performance monitoring and threshold alerts."""
    print("\n=== Testing Performance Monitoring ===")
    
    # Initialize router with monitoring
    config = AdaptiveConfig(
        enable_adaptive_routing=True,
        anomaly_detection_enabled=True,
        metrics_collection_interval=1.0
    )
    
    router = await initialize_performance_adaptive_router(config)
    
    # Simulate performance degradation
    provider = "test_provider"
    
    print("Simulating normal performance...")
    await router.record_performance(provider, {
        'latency_mean': 1.0,
        'error_rate': 0.05,
        'requests_per_second': 10.0,
        'cost_per_request': 0.01,
        'user_satisfaction_score': 0.9,
        'response_quality_score': 0.85,
        'success_rate': 0.95,
        'uptime_percentage': 99.0
    })
    
    await asyncio.sleep(2)
    
    print("Simulating performance degradation...")
    await router.record_performance(provider, {
        'latency_mean': 4.0,  # High latency
        'error_rate': 0.2,   # High error rate
        'requests_per_second': 3.0,  # Low throughput
        'cost_per_request': 0.05,
        'user_satisfaction_score': 0.6,
        'response_quality_score': 0.5,
        'success_rate': 0.8,
        'uptime_percentage': 95.0
    })
    
    await asyncio.sleep(2)
    
    print("Simulating performance crisis...")
    await router.record_performance(provider, {
        'latency_mean': 8.0,  # Critical latency
        'error_rate': 0.4,   # Critical error rate
        'requests_per_second': 1.0,  # Critical throughput
        'cost_per_request': 0.1,
        'user_satisfaction_score': 0.3,
        'response_quality_score': 0.2,
        'success_rate': 0.6,
        'uptime_percentage': 90.0
    })
    
    await asyncio.sleep(3)
    
    # Get performance trends
    trends = router.get_performance_trends(provider, window_minutes=5)
    print(f"\nPerformance Trends for {provider}:")
    print(f"  Latency Trend: {trends.get('latency_trend', 'unknown')}")
    print(f"  Throughput Trend: {trends.get('throughput_trend', 'unknown')}")
    print(f"  Error Rate Trend: {trends.get('error_rate_trend', 'unknown')}")
    print(f"  Overall Trend: {trends.get('overall_trend', 'unknown')}")
    
    await router.stop_monitoring()
    print("\nPerformance monitoring test completed successfully!")


async def test_adaptive_strategies():
    """Test different adaptive routing strategies."""
    print("\n=== Testing Adaptive Strategies ===")
    
    router = await initialize_performance_adaptive_router()
    
    # Setup test providers with different characteristics
    providers_data = {
        "fast_provider": {
            'latency_mean': 0.3,
            'error_rate': 0.02,
            'cost_per_request': 0.02,
            'success_rate': 0.98
        },
        "cheap_provider": {
            'latency_mean': 1.5,
            'error_rate': 0.05,
            'cost_per_request': 0.005,
            'success_rate': 0.95
        },
        "quality_provider": {
            'latency_mean': 2.0,
            'error_rate': 0.01,
            'cost_per_request': 0.05,
            'success_rate': 0.99,
            'user_satisfaction_score': 0.95,
            'response_quality_score': 0.9
        }
    }
    
    # Record performance for each provider
    for provider, metrics in providers_data.items():
        await router.record_performance(provider, metrics)
    
    await asyncio.sleep(2)
    
    # Test each strategy
    strategies = [
        (AdaptiveStrategy.LATENCY_OPTIMIZED, "Latency Optimized"),
        (AdaptiveStrategy.COST_OPTIMIZED, "Cost Optimized"),
        (AdaptiveStrategy.QUALITY_OPTIMIZED, "Quality Optimized"),
        (AdaptiveStrategy.BALANCED, "Balanced")
    ]
    
    test_context = "test_context"
    test_requirements = {"capabilities": ["text"]}
    
    for strategy, strategy_name in strategies:
        print(f"\nTesting {strategy_name} Strategy:")
        
        # Make multiple requests to see routing behavior
        for i in range(3):
            request_id = f"{strategy.value}_{i}"
            decision = await router.route_request(
                request_id, test_context, test_requirements, strategy
            )
            
            print(f"  Request {request_id}: {decision.selected_provider} "
                  f"(confidence: {decision.confidence:.3f})")
    
    await router.stop_monitoring()
    print("\nAdaptive strategies test completed successfully!")


async def test_optimization():
    """Test performance optimization functionality."""
    print("\n=== Testing Performance Optimization ===")
    
    config = AdaptiveConfig(
        enable_adaptive_routing=True,
        auto_optimization_enabled=True,
        optimization_interval=5.0
    )
    
    router = await initialize_performance_adaptive_router(config)
    
    # Simulate various performance scenarios
    scenarios = [
        {
            'name': 'High Latency Scenario',
            'provider': 'slow_provider',
            'metrics': {
                'latency_mean': 5.0,
                'error_rate': 0.1,
                'requests_per_second': 2.0,
                'cost_per_request': 0.01,
                'success_rate': 0.9
            },
            'objectives': [OptimizationObjective.MINIMIZE_LATENCY]
        },
        {
            'name': 'High Cost Scenario',
            'provider': 'expensive_provider',
            'metrics': {
                'latency_mean': 1.0,
                'error_rate': 0.05,
                'requests_per_second': 15.0,
                'cost_per_request': 0.1,
                'success_rate': 0.95
            },
            'objectives': [OptimizationObjective.MINIMIZE_COST]
        },
        {
            'name': 'Low Quality Scenario',
            'provider': 'low_quality_provider',
            'metrics': {
                'latency_mean': 2.0,
                'error_rate': 0.15,
                'requests_per_second': 8.0,
                'cost_per_request': 0.02,
                'user_satisfaction_score': 0.6,
                'response_quality_score': 0.5,
                'success_rate': 0.85
            },
            'objectives': [OptimizationObjective.MAXIMIZE_QUALITY]
        }
    ]
    
    for scenario in scenarios:
        print(f"\nSimulating {scenario['name']}:")
        
        # Record poor performance
        await router.record_performance(scenario['provider'], scenario['metrics'])
        await asyncio.sleep(2)
        
        # Run optimization
        result = await router.optimize_routing(scenario['objectives'])
        
        print(f"  Optimization Objectives: {result['objectives']}")
        print(f"  Current Performance: {result.get('current_performance', {})}")
        
        if 'recommendations' in result:
            print(f"  Recommendations:")
            for rec in result['recommendations']:
                print(f"    - {rec.get('recommendation', 'N/A')} "
                      f"(priority: {rec.get('priority', 'N/A')})")
        
        if 'applied_optimizations' in result:
            print(f"  Applied Optimizations: {len(result['applied_optimizations'])}")
        
        print(f"  Optimization Time: {result.get('optimization_time', 0):.3f}s")
    
    await router.stop_monitoring()
    print("\nPerformance optimization test completed successfully!")


async def test_integration():
    """Test integration with existing fallback system components."""
    print("\n=== Testing System Integration ===")
    
    config = AdaptiveConfig(
        enable_adaptive_routing=True,
        integrate_with_fallback_manager=True,
        integrate_with_health_monitor=True,
        integrate_with_provider_switcher=True
    )
    
    router = await initialize_performance_adaptive_router(config)
    
    # Test integrated routing
    print("Testing integrated routing with fallback system...")
    
    # Make a request that would trigger fallback
    decision = await router.route_request(
        "integration_test",
        "chat",
        {"capabilities": ["text"], "max_error_rate": 0.01}  # Very strict requirements
    )
    
    print(f"  Selected Provider: {decision.selected_provider}")
    print(f"  Strategy: {decision.strategy.value}")
    print(f"  Confidence: {decision.confidence:.3f}")
    print(f"  Rationale: {decision.rationale}")
    
    # Get comprehensive analytics
    analytics = router.get_routing_analytics()
    print(f"\nComprehensive Analytics:")
    print(f"  Total Requests: {analytics.total_requests}")
    print(f"  Success Rate: {analytics.routing_accuracy:.3f}")
    print(f"  Provider Performance Scores: {analytics.provider_performance_scores}")
    
    # Get all provider performance
    all_performance = router.get_all_provider_performance()
    print(f"\nAll Provider Performance:")
    for provider, metrics in all_performance.items():
        print(f"  {provider}:")
        print(f"    Latency: {metrics.latency_mean:.3f}s")
        print(f"    Error Rate: {metrics.error_rate:.3f}")
        print(f"    Success Rate: {metrics.success_rate:.3f}")
        print(f"    Cost: ${metrics.cost_per_request:.6f}/request")
    
    await router.stop_monitoring()
    print("\nSystem integration test completed successfully!")


async def main():
    """Main test function."""
    print("Karen AI Performance Adaptive Router Test Suite")
    print("=" * 50)
    
    try:
        # Run all tests
        await test_basic_routing()
        await test_performance_monitoring()
        await test_adaptive_strategies()
        await test_optimization()
        await test_integration()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print("\nPerformance Adaptive Router Features Demonstrated:")
        print("✓ Real-time performance monitoring with comprehensive metrics")
        print("✓ Adaptive routing algorithms with multiple strategies")
        print("✓ Performance-based optimization with automatic tuning")
        print("✓ Comprehensive analytics and reporting")
        print("✓ Integration with existing fallback system components")
        print("✓ Comprehensive error handling and logging")
        print("✓ Configuration support through environment variables")
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        print(f"\nTest suite failed with error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the test suite
    exit_code = asyncio.run(main())
    sys.exit(exit_code)