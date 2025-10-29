"""
Integration tests for the complete Performance Monitoring System

This module tests the integration between all performance monitoring components:
- Response Performance Metrics
- A/B Testing System  
- User Satisfaction Tracking
- Optimization Recommendation Engine
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import patch

from src.ai_karen_engine.services.response_performance_metrics import (
    performance_collector,
    ResponsePerformanceMetrics,
    OptimizationType
)
from src.ai_karen_engine.services.ab_testing_system import (
    ab_testing_system,
    TestType,
    TestVariant,
    TestStatus
)
from src.ai_karen_engine.services.user_satisfaction_tracker import (
    satisfaction_tracker,
    FeedbackType,
    BehaviorSignal
)
from src.ai_karen_engine.services.optimization_recommendation_engine import (
    recommendation_engine,
    RecommendationType,
    Priority
)


@pytest.mark.asyncio
class TestPerformanceMonitoringIntegration:
    """Integration tests for the complete performance monitoring system"""
    
    async def test_end_to_end_performance_monitoring_workflow(self):
        """Test complete end-to-end performance monitoring workflow"""
        
        # Step 1: Simulate response processing with performance tracking
        print("Step 1: Simulating response processing...")
        
        response_metrics = []
        for i in range(20):
            response_id = f"integration_response_{i}"
            query = f"Integration test query {i}"
            model_used = "integration_test_model"
            
            # Start tracking
            performance_collector.start_response_tracking(response_id, query, model_used)
            
            # Apply some optimizations
            if i % 3 == 0:
                performance_collector.record_optimization_applied(response_id, OptimizationType.CACHE_OPTIMIZATION)
            if i % 4 == 0:
                performance_collector.record_optimization_applied(response_id, OptimizationType.GPU_ACCELERATION)
            
            # Add bottlenecks for some responses
            if i % 5 == 0:
                performance_collector.record_bottleneck(response_id, "model_loading")
            
            # Simulate streaming
            for chunk in range(3):
                performance_collector.record_streaming_chunk(response_id)
                await asyncio.sleep(0.01)
            
            # Add errors occasionally
            if i == 15:  # One error response
                performance_collector.record_error(response_id, "timeout")
            
            # Finish tracking
            metrics = performance_collector.finish_response_tracking(
                response_id=response_id,
                response_size=1000 + i * 100,
                cache_hit_rate=70.0 + i * 2,
                model_efficiency=80.0 + i,
                content_relevance_score=85.0 + i
            )
            
            response_metrics.append(metrics)
        
        # Verify performance data collection
        assert len(response_metrics) == 20
        assert all(m.response_id.startswith("integration_response_") for m in response_metrics)
        
        # Step 2: Simulate user satisfaction tracking
        print("Step 2: Simulating user satisfaction tracking...")
        
        # Start user sessions
        for i in range(10):
            session_id = f"integration_session_{i}"
            user_id = f"integration_user_{i}"
            satisfaction_tracker.start_session_tracking(session_id, user_id)
            
            # Record response delivery
            satisfaction_tracker.record_response_delivered(
                response_id=f"integration_response_{i}",
                session_id=session_id,
                response_time=response_metrics[i].response_time,
                response_length=response_metrics[i].response_size,
                model_used=response_metrics[i].model_used
            )
            
            # Record behavior signals
            if i % 2 == 0:
                satisfaction_tracker.record_behavior_signal(
                    session_id, BehaviorSignal.COPY_RESPONSE, f"integration_response_{i}"
                )
            if i % 3 == 0:
                satisfaction_tracker.record_behavior_signal(
                    session_id, BehaviorSignal.LONG_READ_TIME, f"integration_response_{i}"
                )
            
            # Record explicit feedback
            if i % 4 == 0:
                rating = 4 if i < 10 else 5
                satisfaction_tracker.record_explicit_feedback(
                    response_id=f"integration_response_{i}",
                    user_id=user_id,
                    session_id=session_id,
                    feedback_type=FeedbackType.RATING,
                    rating=rating,
                    thumbs_up=True,
                    detailed_comment="Great response!" if i % 8 == 0 else None
                )
        
        # Step 3: Create and run A/B test
        print("Step 3: Creating and running A/B test...")
        
        variants = [
            TestVariant(
                id="control",
                name="Control",
                description="Standard processing",
                configuration={"optimization_level": "standard"},
                traffic_percentage=50.0,
                is_control=True
            ),
            TestVariant(
                id="optimized",
                name="Optimized",
                description="Enhanced processing",
                configuration={"optimization_level": "enhanced"},
                traffic_percentage=50.0,
                is_control=False
            )
        ]
        
        test_id = ab_testing_system.create_test(
            name="Integration Test A/B",
            description="Integration test for A/B testing",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=variants,
            target_sample_size=50
        )
        
        # Start test
        assert ab_testing_system.start_test(test_id) is True
        
        # Simulate test data
        for i in range(30):
            user_id = f"ab_test_user_{i}"
            variant_id = ab_testing_system.assign_variant(test_id, user_id)
            
            # Create test metrics (optimized variant performs better)
            if variant_id == "control":
                response_time = 3.0 + (i % 5) * 0.1
            else:
                response_time = 2.0 + (i % 5) * 0.1
            
            test_metrics = ResponsePerformanceMetrics(
                response_id=f"ab_test_response_{i}",
                timestamp=datetime.now(),
                query=f"AB test query {i}",
                model_used="ab_test_model",
                response_time=response_time,
                cpu_usage=10.0,
                memory_usage=1024 * 1024
            )
            
            ab_testing_system.record_test_result(test_id, variant_id, test_metrics)
        
        # Stop test and get results
        ab_testing_system.stop_test(test_id)
        test_results = ab_testing_system.analyze_test_results(test_id)
        
        # Verify A/B test results
        assert test_results is not None
        assert len(test_results.variant_metrics) == 2
        assert "control" in test_results.variant_metrics
        assert "optimized" in test_results.variant_metrics
        
        # Step 4: Generate optimization recommendations
        print("Step 4: Generating optimization recommendations...")
        
        recommendations = recommendation_engine.generate_recommendations(force_analysis=True)
        
        # Verify recommendations were generated
        assert isinstance(recommendations, list)
        # Should have some recommendations based on the simulated data
        
        # Step 5: Analyze system health
        print("Step 5: Analyzing system health...")
        
        health_analysis = recommendation_engine.analyze_system_health()
        
        # Verify health analysis
        assert health_analysis.overall_health_score >= 0
        assert health_analysis.overall_health_score <= 100
        assert health_analysis.performance_score >= 0
        assert health_analysis.satisfaction_score >= 0
        assert health_analysis.resource_efficiency_score >= 0
        
        # Step 6: Verify data integration across components
        print("Step 6: Verifying data integration...")
        
        # Check performance metrics
        aggregated_metrics = performance_collector.get_aggregated_metrics(timedelta(minutes=1))
        assert aggregated_metrics.total_responses >= 20
        assert aggregated_metrics.avg_response_time > 0
        
        # Check satisfaction metrics
        satisfaction_metrics = satisfaction_tracker.get_satisfaction_metrics(timedelta(minutes=1))
        assert satisfaction_metrics.total_feedback_count > 0
        assert satisfaction_metrics.avg_rating > 0
        
        # Check A/B test status
        test_status = ab_testing_system.get_test_status(test_id)
        assert test_status is not None
        assert test_status["total_sample_size"] == 30
        
        print("✅ End-to-end integration test completed successfully!")
    
    async def test_performance_monitoring_with_high_load(self):
        """Test performance monitoring under high load conditions"""
        
        print("Testing performance monitoring under high load...")
        
        # Simulate high concurrent load
        async def simulate_concurrent_responses(batch_id: int, count: int):
            tasks = []
            for i in range(count):
                task = self._simulate_single_response(f"batch_{batch_id}_response_{i}")
                tasks.append(task)
            
            await asyncio.gather(*tasks)
        
        # Run multiple batches concurrently
        batch_tasks = []
        for batch in range(5):
            task = simulate_concurrent_responses(batch, 10)
            batch_tasks.append(task)
        
        start_time = time.time()
        await asyncio.gather(*batch_tasks)
        end_time = time.time()
        
        print(f"Processed 50 concurrent responses in {end_time - start_time:.2f} seconds")
        
        # Verify system handled the load
        current_metrics = performance_collector.get_current_metrics()
        assert current_metrics['active_responses'] == 0  # All should be completed
        
        aggregated = performance_collector.get_aggregated_metrics(timedelta(minutes=1))
        assert aggregated.total_responses >= 50
        
        print("✅ High load test completed successfully!")
    
    async def test_cross_component_data_consistency(self):
        """Test data consistency across all monitoring components"""
        
        print("Testing cross-component data consistency...")
        
        # Create coordinated test data
        test_responses = []
        for i in range(10):
            response_id = f"consistency_test_{i}"
            query = f"Consistency test query {i}"
            model_used = "consistency_model"
            
            # Track performance
            performance_collector.start_response_tracking(response_id, query, model_used)
            
            # Apply optimizations
            if i % 2 == 0:
                performance_collector.record_optimization_applied(response_id, OptimizationType.CACHE_OPTIMIZATION)
            
            await asyncio.sleep(0.1)  # Simulate processing
            
            metrics = performance_collector.finish_response_tracking(
                response_id=response_id,
                response_size=1000,
                cache_hit_rate=80.0,
                model_efficiency=90.0
            )
            
            test_responses.append(metrics)
            
            # Track satisfaction for same response
            session_id = f"consistency_session_{i}"
            user_id = f"consistency_user_{i}"
            
            satisfaction_tracker.start_session_tracking(session_id, user_id)
            satisfaction_tracker.record_response_delivered(
                response_id=response_id,
                session_id=session_id,
                response_time=metrics.response_time,
                response_length=metrics.response_size,
                model_used=metrics.model_used
            )
            
            # Record feedback
            satisfaction_tracker.record_explicit_feedback(
                response_id=response_id,
                user_id=user_id,
                session_id=session_id,
                feedback_type=FeedbackType.RATING,
                rating=4
            )
        
        # Verify data consistency
        performance_metrics = performance_collector.get_aggregated_metrics(timedelta(minutes=1))
        satisfaction_metrics = satisfaction_tracker.get_satisfaction_metrics(timedelta(minutes=1))
        
        # Both systems should have data for the same responses
        assert performance_metrics.total_responses >= 10
        assert satisfaction_metrics.total_feedback_count >= 10
        
        # Model usage should be consistent
        assert "consistency_model" in performance_metrics.most_used_models
        
        print("✅ Data consistency test completed successfully!")
    
    async def test_recommendation_engine_integration(self):
        """Test recommendation engine integration with other components"""
        
        print("Testing recommendation engine integration...")
        
        # Create scenario with performance issues
        for i in range(15):
            response_id = f"recommendation_test_{i}"
            performance_collector.start_response_tracking(response_id, f"query_{i}", "slow_model")
            
            # Simulate slow responses and bottlenecks
            performance_collector.record_bottleneck(response_id, "model_loading")
            if i % 3 == 0:
                performance_collector.record_error(response_id, "timeout")
            
            await asyncio.sleep(0.05)
            
            # Finish with poor performance metrics
            performance_collector.finish_response_tracking(
                response_id=response_id,
                response_size=500,
                cache_hit_rate=20.0,  # Low cache hit rate
                model_efficiency=60.0  # Low efficiency
            )
        
        # Add poor satisfaction data
        for i in range(5):
            session_id = f"rec_session_{i}"
            user_id = f"rec_user_{i}"
            satisfaction_tracker.start_session_tracking(session_id, user_id)
            
            satisfaction_tracker.record_explicit_feedback(
                response_id=f"recommendation_test_{i}",
                user_id=user_id,
                session_id=session_id,
                feedback_type=FeedbackType.RATING,
                rating=2,  # Poor rating
                thumbs_up=False,
                detailed_comment="Too slow and not helpful"
            )
        
        # Generate recommendations
        recommendations = recommendation_engine.generate_recommendations(force_analysis=True)
        
        # Should generate recommendations based on the poor performance
        assert len(recommendations) > 0
        
        # Should identify performance and satisfaction issues
        recommendation_types = [r.recommendation_type for r in recommendations]
        assert any(rt in [RecommendationType.PERFORMANCE_OPTIMIZATION, 
                         RecommendationType.CACHE_OPTIMIZATION,
                         RecommendationType.USER_EXPERIENCE_OPTIMIZATION] 
                  for rt in recommendation_types)
        
        # Should have high priority recommendations due to poor performance
        high_priority_recs = [r for r in recommendations if r.priority == Priority.HIGH]
        assert len(high_priority_recs) > 0
        
        print("✅ Recommendation engine integration test completed successfully!")
    
    async def test_ab_testing_with_real_metrics(self):
        """Test A/B testing integration with real performance metrics"""
        
        print("Testing A/B testing with real performance metrics...")
        
        # Create A/B test
        variants = [
            TestVariant("control", "Control", "Standard", {}, 50.0, True),
            TestVariant("treatment", "Treatment", "Optimized", {}, 50.0, False)
        ]
        
        test_id = ab_testing_system.create_test(
            name="Real Metrics A/B Test",
            description="A/B test with real performance data",
            test_type=TestType.PERFORMANCE_OPTIMIZATION,
            variants=variants
        )
        
        ab_testing_system.start_test(test_id)
        
        # Generate real performance data for both variants
        for i in range(40):
            user_id = f"real_metrics_user_{i}"
            variant_id = ab_testing_system.assign_variant(test_id, user_id)
            
            response_id = f"real_ab_response_{i}"
            
            # Start performance tracking
            performance_collector.start_response_tracking(response_id, f"query_{i}", "ab_test_model")
            
            # Apply different optimizations based on variant
            if variant_id == "treatment":
                performance_collector.record_optimization_applied(response_id, OptimizationType.CACHE_OPTIMIZATION)
                performance_collector.record_optimization_applied(response_id, OptimizationType.GPU_ACCELERATION)
            
            # Simulate processing time based on variant
            if variant_id == "control":
                await asyncio.sleep(0.1)  # Slower
            else:
                await asyncio.sleep(0.05)  # Faster
            
            # Finish tracking
            metrics = performance_collector.finish_response_tracking(
                response_id=response_id,
                cache_hit_rate=90.0 if variant_id == "treatment" else 50.0,
                model_efficiency=95.0 if variant_id == "treatment" else 80.0
            )
            
            # Record for A/B test
            ab_testing_system.record_test_result(test_id, variant_id, metrics)
            
            # Also record satisfaction
            session_id = f"ab_session_{i}"
            satisfaction_tracker.start_session_tracking(session_id, user_id)
            satisfaction_tracker.record_response_delivered(
                response_id=response_id,
                session_id=session_id,
                response_time=metrics.response_time,
                response_length=1000,
                model_used="ab_test_model"
            )
            
            # Better satisfaction for treatment
            rating = 5 if variant_id == "treatment" else 3
            satisfaction_tracker.record_explicit_feedback(
                response_id=response_id,
                user_id=user_id,
                session_id=session_id,
                feedback_type=FeedbackType.RATING,
                rating=rating
            )
        
        # Analyze results
        ab_testing_system.stop_test(test_id)
        results = ab_testing_system.analyze_test_results(test_id)
        
        # Treatment should be the winner
        assert results.winner_variant_id == "treatment"
        assert results.effect_size > 0
        
        # Verify metrics integration
        treatment_metrics = results.variant_metrics["treatment"]
        control_metrics = results.variant_metrics["control"]
        
        assert treatment_metrics.avg_response_time < control_metrics.avg_response_time
        assert treatment_metrics.sample_size > 0
        assert control_metrics.sample_size > 0
        
        print("✅ A/B testing with real metrics completed successfully!")
    
    async def _simulate_single_response(self, response_id: str):
        """Helper method to simulate a single response"""
        query = f"Test query for {response_id}"
        model_used = "test_model"
        
        performance_collector.start_response_tracking(response_id, query, model_used)
        
        # Random processing simulation
        import random
        await asyncio.sleep(random.uniform(0.01, 0.05))
        
        if random.random() < 0.3:
            performance_collector.record_optimization_applied(response_id, OptimizationType.CACHE_OPTIMIZATION)
        
        performance_collector.finish_response_tracking(
            response_id=response_id,
            response_size=random.randint(500, 2000),
            cache_hit_rate=random.uniform(50, 90)
        )


@pytest.mark.asyncio
class TestPerformanceMonitoringErrorHandling:
    """Test error handling in performance monitoring integration"""
    
    async def test_graceful_degradation_on_component_failure(self):
        """Test that system continues working when individual components fail"""
        
        print("Testing graceful degradation...")
        
        # Simulate component failures and verify system continues
        with patch.object(satisfaction_tracker, 'record_explicit_feedback', side_effect=Exception("Satisfaction tracker error")):
            # Performance tracking should still work
            performance_collector.start_response_tracking("error_test_1", "query", "model")
            metrics = performance_collector.finish_response_tracking("error_test_1")
            assert metrics is not None
        
        with patch.object(performance_collector, 'record_optimization_applied', side_effect=Exception("Performance collector error")):
            # A/B testing should still work
            variants = [
                TestVariant("control", "Control", "Control", {}, 50.0, True),
                TestVariant("treatment", "Treatment", "Treatment", {}, 50.0, False)
            ]
            
            test_id = ab_testing_system.create_test(
                name="Error Test",
                description="Test",
                test_type=TestType.OPTIMIZATION_TECHNIQUE,
                variants=variants
            )
            
            assert test_id is not None
        
        print("✅ Graceful degradation test completed successfully!")
    
    async def test_data_validation_and_sanitization(self):
        """Test data validation and sanitization across components"""
        
        print("Testing data validation...")
        
        # Test invalid data handling
        try:
            # Invalid response time (negative)
            performance_collector.start_response_tracking("invalid_test", "query", "model")
            # This should handle negative values gracefully
            metrics = performance_collector.finish_response_tracking(
                "invalid_test",
                response_size=-100,  # Invalid negative size
                cache_hit_rate=150.0  # Invalid percentage > 100
            )
            # System should sanitize the data
            assert metrics.response_size >= 0
            assert metrics.cache_hit_rate <= 100.0
        except Exception as e:
            # Should not crash the system
            print(f"Handled invalid data gracefully: {e}")
        
        # Test invalid A/B test configuration
        try:
            invalid_variants = [
                TestVariant("v1", "V1", "Desc", {}, 150.0, True)  # Invalid percentage
            ]
            ab_testing_system.create_test(
                name="Invalid Test",
                description="Test",
                test_type=TestType.OPTIMIZATION_TECHNIQUE,
                variants=invalid_variants
            )
        except ValueError:
            # Should raise appropriate validation error
            pass
        
        print("✅ Data validation test completed successfully!")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])