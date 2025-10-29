"""
Performance Monitoring System Example

This example demonstrates how to use the comprehensive performance monitoring
and analytics system for response optimization.
"""

import asyncio
import time
import random
from datetime import datetime, timedelta

from src.ai_karen_engine.services.response_performance_metrics import (
    performance_collector,
    OptimizationType
)
from src.ai_karen_engine.services.ab_testing_system import (
    ab_testing_system,
    TestType,
    TestVariant
)
from src.ai_karen_engine.services.user_satisfaction_tracker import (
    satisfaction_tracker,
    FeedbackType,
    BehaviorSignal
)
from src.ai_karen_engine.services.optimization_recommendation_engine import (
    recommendation_engine
)


async def simulate_response_processing():
    """Simulate response processing with performance tracking"""
    print("🚀 Starting response processing simulation...")
    
    models = ["gpt-4", "claude-3", "llama-2", "gemini-pro"]
    optimizations = [
        OptimizationType.CACHE_OPTIMIZATION,
        OptimizationType.GPU_ACCELERATION,
        OptimizationType.CONTENT_OPTIMIZATION,
        OptimizationType.PROGRESSIVE_STREAMING
    ]
    
    # Simulate 50 responses
    for i in range(50):
        response_id = f"response_{i:03d}"
        query = f"Example query {i}: How do I optimize my code?"
        model_used = random.choice(models)
        
        print(f"📝 Processing response {i+1}/50 with {model_used}")
        
        # Start tracking
        performance_collector.start_response_tracking(response_id, query, model_used)
        
        # Simulate processing time
        processing_time = random.uniform(0.5, 3.0)
        
        # Randomly apply optimizations
        applied_optimizations = random.sample(optimizations, random.randint(0, 2))
        for opt in applied_optimizations:
            performance_collector.record_optimization_applied(response_id, opt)
        
        # Simulate potential bottlenecks
        if random.random() < 0.2:  # 20% chance of bottleneck
            bottlenecks = ["model_loading", "memory_pressure", "network_latency", "gpu_memory"]
            performance_collector.record_bottleneck(response_id, random.choice(bottlenecks))
        
        # Simulate streaming chunks
        chunks = random.randint(1, 5)
        for _ in range(chunks):
            performance_collector.record_streaming_chunk(response_id)
            await asyncio.sleep(processing_time / chunks)
        
        # Simulate occasional errors
        if random.random() < 0.05:  # 5% error rate
            performance_collector.record_error(response_id, "timeout")
        
        # Finish tracking
        metrics = performance_collector.finish_response_tracking(
            response_id=response_id,
            response_size=random.randint(500, 5000),
            cache_hit_rate=random.uniform(0, 100),
            model_efficiency=random.uniform(70, 95),
            content_relevance_score=random.uniform(80, 98),
            cuda_acceleration_gain=random.uniform(0, 30) if random.random() < 0.3 else None,
            gpu_usage=random.uniform(20, 80) if random.random() < 0.4 else None
        )
        
        print(f"   ✅ Response time: {metrics.response_time:.2f}s, "
              f"Optimizations: {len(applied_optimizations)}, "
              f"Cache hit: {metrics.cache_hit_rate:.1f}%")


async def simulate_user_feedback():
    """Simulate user feedback collection"""
    print("\n💬 Simulating user feedback...")
    
    # Start some user sessions
    sessions = []
    for i in range(10):
        session_id = f"session_{i}"
        user_id = f"user_{i}"
        satisfaction_tracker.start_session_tracking(session_id, user_id)
        sessions.append((session_id, user_id))
    
    # Simulate responses and feedback
    for i, (session_id, user_id) in enumerate(sessions):
        response_id = f"feedback_response_{i}"
        
        # Record response delivery
        satisfaction_tracker.record_response_delivered(
            response_id=response_id,
            session_id=session_id,
            response_time=random.uniform(1.0, 4.0),
            response_length=random.randint(100, 2000),
            model_used=random.choice(["gpt-4", "claude-3", "llama-2"]),
            optimizations_applied=["cache_optimization"] if random.random() < 0.5 else []
        )
        
        # Simulate behavior signals
        behavior_signals = [
            BehaviorSignal.COPY_RESPONSE,
            BehaviorSignal.LONG_READ_TIME,
            BehaviorSignal.SCROLL_THROUGH_RESPONSE,
            BehaviorSignal.IMMEDIATE_EXIT,
            BehaviorSignal.REGENERATE_REQUEST
        ]
        
        for _ in range(random.randint(0, 3)):
            signal = random.choice(behavior_signals)
            satisfaction_tracker.record_behavior_signal(session_id, signal, response_id)
        
        # Simulate explicit feedback (30% of users give feedback)
        if random.random() < 0.3:
            rating = random.randint(1, 5)
            thumbs_up = rating >= 4
            comments = [
                "Very helpful response!",
                "Could be more detailed",
                "Perfect, exactly what I needed",
                "Too slow to generate",
                "Great explanation"
            ]
            
            satisfaction_tracker.record_explicit_feedback(
                response_id=response_id,
                user_id=user_id,
                session_id=session_id,
                feedback_type=FeedbackType.RATING,
                rating=rating,
                thumbs_up=thumbs_up,
                detailed_comment=random.choice(comments) if random.random() < 0.5 else None
            )
            
            print(f"   📊 User {user_id} rated response: {rating}/5 ({'👍' if thumbs_up else '👎'})")


async def demonstrate_ab_testing():
    """Demonstrate A/B testing functionality"""
    print("\n🧪 Setting up A/B test...")
    
    # Create test variants
    variants = [
        TestVariant(
            id="control",
            name="Standard Processing",
            description="Current response processing without optimizations",
            configuration={"cache_enabled": False, "gpu_acceleration": False},
            traffic_percentage=50.0,
            is_control=True
        ),
        TestVariant(
            id="optimized",
            name="Optimized Processing",
            description="Response processing with cache and GPU acceleration",
            configuration={"cache_enabled": True, "gpu_acceleration": True},
            traffic_percentage=50.0,
            is_control=False
        )
    ]
    
    # Create A/B test
    test_id = ab_testing_system.create_test(
        name="Response Optimization Test",
        description="Test the effectiveness of caching and GPU acceleration",
        test_type=TestType.OPTIMIZATION_TECHNIQUE,
        variants=variants,
        target_sample_size=100,
        confidence_level=0.95,
        minimum_effect_size=0.15
    )
    
    print(f"   ✅ Created A/B test: {test_id}")
    
    # Start the test
    ab_testing_system.start_test(test_id)
    print("   🚀 Started A/B test")
    
    # Simulate test data collection
    print("   📊 Collecting test data...")
    
    for i in range(50):  # Simulate 50 test responses
        user_id = f"ab_test_user_{i}"
        variant_id = ab_testing_system.assign_variant(test_id, user_id)
        
        # Simulate different performance based on variant
        if variant_id == "control":
            response_time = random.uniform(2.5, 4.0)  # Slower
            cpu_usage = random.uniform(15, 25)
        else:  # optimized
            response_time = random.uniform(1.5, 2.5)  # Faster
            cpu_usage = random.uniform(8, 15)
        
        # Create performance metrics
        from src.ai_karen_engine.services.response_performance_metrics import ResponsePerformanceMetrics
        
        metrics = ResponsePerformanceMetrics(
            response_id=f"ab_test_response_{i}",
            timestamp=datetime.now(),
            query=f"AB test query {i}",
            model_used="test_model",
            response_time=response_time,
            cpu_usage=cpu_usage,
            memory_usage=random.randint(500_000_000, 1_500_000_000)
        )
        
        # Record test result
        ab_testing_system.record_test_result(test_id, variant_id, metrics)
    
    # Get test status
    status = ab_testing_system.get_test_status(test_id)
    print(f"   📈 Test progress: {status['progress']:.1f}% "
          f"({status['total_sample_size']} samples)")
    
    # Stop and analyze test
    ab_testing_system.stop_test(test_id)
    results = ab_testing_system.analyze_test_results(test_id)
    
    if results and results.winner_variant_id:
        print(f"   🏆 Winner: {results.winner_variant_id} "
              f"(Effect size: {results.effect_size:.2f})")
    else:
        print("   📊 No statistically significant winner")


async def analyze_performance_metrics():
    """Analyze and display performance metrics"""
    print("\n📊 Analyzing Performance Metrics...")
    
    # Get current metrics
    current = performance_collector.get_current_metrics()
    print(f"   🔄 Active responses: {current['active_responses']}")
    print(f"   ⚡ Avg response time (1min): {current['avg_response_time_1min']:.2f}s")
    print(f"   💾 Cache hit rate (1min): {current['cache_hit_rate_1min']:.1f}%")
    print(f"   🔥 Throughput (1min): {current['throughput_1min']:.1f} responses/min")
    
    # Get aggregated metrics
    aggregated = performance_collector.get_aggregated_metrics(timedelta(minutes=5))
    print(f"\n   📈 Last 5 minutes summary:")
    print(f"   • Total responses: {aggregated.total_responses}")
    print(f"   • Average response time: {aggregated.avg_response_time:.2f}s")
    print(f"   • P95 response time: {aggregated.p95_response_time:.2f}s")
    print(f"   • Error rate: {aggregated.error_rate:.1f}%")
    print(f"   • Cache hit rate: {aggregated.cache_hit_rate:.1f}%")
    
    if aggregated.most_used_models:
        print(f"   • Most used models: {dict(list(aggregated.most_used_models.items())[:3])}")
    
    # Analyze bottlenecks
    bottlenecks = performance_collector.analyze_bottlenecks(timedelta(minutes=5))
    if bottlenecks:
        print(f"\n   🚨 Identified bottlenecks:")
        for bottleneck in bottlenecks[:3]:
            print(f"   • {bottleneck.bottleneck_type}: {bottleneck.frequency} occurrences "
                  f"({bottleneck.severity} severity)")


async def analyze_user_satisfaction():
    """Analyze user satisfaction metrics"""
    print("\n😊 Analyzing User Satisfaction...")
    
    satisfaction_metrics = satisfaction_tracker.get_satisfaction_metrics(timedelta(minutes=5))
    
    print(f"   📊 Satisfaction Summary:")
    print(f"   • Total feedback: {satisfaction_metrics.total_feedback_count}")
    print(f"   • Average rating: {satisfaction_metrics.avg_rating:.1f}/5.0")
    print(f"   • Thumbs up: {satisfaction_metrics.thumbs_up_percentage:.1f}%")
    
    if satisfaction_metrics.net_promoter_score is not None:
        print(f"   • Net Promoter Score: {satisfaction_metrics.net_promoter_score:.1f}")
    
    if satisfaction_metrics.common_complaints:
        print(f"   • Common complaints: {satisfaction_metrics.common_complaints[:3]}")
    
    if satisfaction_metrics.common_praise:
        print(f"   • Common praise: {satisfaction_metrics.common_praise[:3]}")
    
    if satisfaction_metrics.improvement_suggestions:
        print(f"   💡 Improvement suggestions:")
        for suggestion in satisfaction_metrics.improvement_suggestions[:3]:
            print(f"   • {suggestion}")


async def generate_optimization_recommendations():
    """Generate and display optimization recommendations"""
    print("\n🎯 Generating Optimization Recommendations...")
    
    recommendations = recommendation_engine.generate_recommendations(force_analysis=True)
    
    if recommendations:
        print(f"   📋 Generated {len(recommendations)} recommendations:")
        
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"\n   {i}. {rec.title} ({rec.priority.value.upper()} priority)")
            print(f"      📝 {rec.description}")
            print(f"      📊 Estimated impact: {rec.estimated_impact:.1f}%")
            print(f"      ⏱️  Effort: {rec.estimated_effort_hours}h")
            print(f"      🎯 Confidence: {rec.confidence_score:.1%}")
    else:
        print("   ℹ️  No recommendations generated (insufficient data)")
    
    # Get quick wins
    quick_wins = recommendation_engine.get_quick_wins(max_effort_hours=8)
    if quick_wins:
        print(f"\n   ⚡ Quick wins (≤8 hours effort):")
        for win in quick_wins[:3]:
            ratio = win.estimated_impact / max(win.estimated_effort_hours, 1)
            print(f"   • {win.title}: {win.estimated_impact:.1f}% impact, "
                  f"{win.estimated_effort_hours}h effort (ratio: {ratio:.1f})")


async def analyze_system_health():
    """Analyze overall system health"""
    print("\n🏥 System Health Analysis...")
    
    health = recommendation_engine.analyze_system_health()
    
    print(f"   🎯 Overall Health Score: {health.overall_health_score:.1f}/100")
    print(f"   ⚡ Performance Score: {health.performance_score:.1f}/100")
    print(f"   😊 Satisfaction Score: {health.satisfaction_score:.1f}/100")
    print(f"   💾 Resource Efficiency: {health.resource_efficiency_score:.1f}/100")
    
    if health.critical_issues:
        print(f"\n   🚨 Critical Issues:")
        for issue in health.critical_issues:
            print(f"   • {issue}")
    
    if health.improvement_opportunities:
        print(f"\n   💡 Improvement Opportunities:")
        for opportunity in health.improvement_opportunities[:3]:
            print(f"   • {opportunity}")
    
    if health.bottleneck_analysis:
        print(f"\n   🔍 Top Bottlenecks:")
        sorted_bottlenecks = sorted(health.bottleneck_analysis.items(), 
                                  key=lambda x: x[1], reverse=True)
        for bottleneck, impact in sorted_bottlenecks[:3]:
            print(f"   • {bottleneck}: {impact:.1f} impact score")


async def main():
    """Main example function"""
    print("🎯 Performance Monitoring System Example")
    print("=" * 50)
    
    try:
        # Run simulations
        await simulate_response_processing()
        await simulate_user_feedback()
        await demonstrate_ab_testing()
        
        # Wait a moment for background processing
        await asyncio.sleep(2)
        
        # Analyze results
        await analyze_performance_metrics()
        await analyze_user_satisfaction()
        await generate_optimization_recommendations()
        await analyze_system_health()
        
        print("\n✅ Performance monitoring example completed successfully!")
        print("\n📊 Key Features Demonstrated:")
        print("   • Real-time performance metrics collection")
        print("   • User satisfaction tracking and analysis")
        print("   • A/B testing for optimization strategies")
        print("   • Automated bottleneck identification")
        print("   • Intelligent optimization recommendations")
        print("   • Comprehensive system health monitoring")
        
    except Exception as e:
        print(f"\n❌ Error during example execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())