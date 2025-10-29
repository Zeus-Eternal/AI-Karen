"""
Unit tests for A/B Testing System
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.ai_karen_engine.services.ab_testing_system import (
    ABTestingSystem,
    ABTest,
    TestVariant,
    TestType,
    TestStatus,
    TestResult,
    TestMetrics
)
from src.ai_karen_engine.services.response_performance_metrics import ResponsePerformanceMetrics


class TestABTestingSystem:
    """Test cases for ABTestingSystem"""
    
    @pytest.fixture
    def ab_system(self):
        """Create a test A/B testing system instance"""
        return ABTestingSystem()
    
    @pytest.fixture
    def test_variants(self):
        """Create test variants"""
        return [
            TestVariant(
                id="control",
                name="Control Variant",
                description="Current implementation",
                configuration={"optimization": "none"},
                traffic_percentage=50.0,
                is_control=True
            ),
            TestVariant(
                id="treatment",
                name="Treatment Variant", 
                description="Optimized implementation",
                configuration={"optimization": "cache_enabled"},
                traffic_percentage=50.0,
                is_control=False
            )
        ]
    
    def test_create_test(self, ab_system, test_variants):
        """Test creating an A/B test"""
        test_id = ab_system.create_test(
            name="Cache Optimization Test",
            description="Test cache optimization effectiveness",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants,
            target_sample_size=1000,
            confidence_level=0.95,
            minimum_effect_size=0.1
        )
        
        assert test_id is not None
        assert test_id in ab_system.active_tests
        
        test = ab_system.active_tests[test_id]
        assert test.name == "Cache Optimization Test"
        assert test.test_type == TestType.OPTIMIZATION_TECHNIQUE
        assert test.status == TestStatus.DRAFT
        assert len(test.variants) == 2
        assert test.target_sample_size == 1000
    
    def test_create_test_invalid_traffic(self, ab_system):
        """Test creating test with invalid traffic percentages"""
        invalid_variants = [
            TestVariant("v1", "V1", "Desc", {}, 60.0, True),
            TestVariant("v2", "V2", "Desc", {}, 30.0, False)  # Total = 90%
        ]
        
        with pytest.raises(ValueError, match="traffic percentages must sum to 100%"):
            ab_system.create_test(
                name="Invalid Test",
                description="Test",
                test_type=TestType.OPTIMIZATION_TECHNIQUE,
                variants=invalid_variants
            )
    
    def test_create_test_no_control(self, ab_system):
        """Test creating test without control variant"""
        no_control_variants = [
            TestVariant("v1", "V1", "Desc", {}, 50.0, False),
            TestVariant("v2", "V2", "Desc", {}, 50.0, False)
        ]
        
        with pytest.raises(ValueError, match="Exactly one variant must be marked as control"):
            ab_system.create_test(
                name="No Control Test",
                description="Test",
                test_type=TestType.OPTIMIZATION_TECHNIQUE,
                variants=no_control_variants
            )
    
    def test_start_test(self, ab_system, test_variants):
        """Test starting an A/B test"""
        test_id = ab_system.create_test(
            name="Test",
            description="Test",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants
        )
        
        success = ab_system.start_test(test_id)
        assert success is True
        
        test = ab_system.active_tests[test_id]
        assert test.status == TestStatus.ACTIVE
        assert test.start_date is not None
    
    def test_start_nonexistent_test(self, ab_system):
        """Test starting non-existent test"""
        success = ab_system.start_test("nonexistent_test")
        assert success is False
    
    def test_pause_and_resume_test(self, ab_system, test_variants):
        """Test pausing and resuming a test"""
        test_id = ab_system.create_test(
            name="Test",
            description="Test", 
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants
        )
        
        ab_system.start_test(test_id)
        
        # Pause test
        success = ab_system.pause_test(test_id)
        assert success is True
        assert ab_system.active_tests[test_id].status == TestStatus.PAUSED
        
        # Resume test
        success = ab_system.resume_test(test_id)
        assert success is True
        assert ab_system.active_tests[test_id].status == TestStatus.ACTIVE
    
    def test_stop_test(self, ab_system, test_variants):
        """Test stopping a test"""
        test_id = ab_system.create_test(
            name="Test",
            description="Test",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants
        )
        
        ab_system.start_test(test_id)
        
        success = ab_system.stop_test(test_id)
        assert success is True
        
        test = ab_system.active_tests[test_id]
        assert test.status == TestStatus.COMPLETED
        assert test.end_date is not None
    
    def test_assign_variant(self, ab_system, test_variants):
        """Test variant assignment"""
        test_id = ab_system.create_test(
            name="Test",
            description="Test",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants
        )
        
        ab_system.start_test(test_id)
        
        # Test consistent assignment
        user_id = "test_user_123"
        variant1 = ab_system.assign_variant(test_id, user_id)
        variant2 = ab_system.assign_variant(test_id, user_id)
        
        assert variant1 is not None
        assert variant1 == variant2  # Should be consistent
        assert variant1 in ["control", "treatment"]
    
    def test_assign_variant_inactive_test(self, ab_system, test_variants):
        """Test variant assignment for inactive test"""
        test_id = ab_system.create_test(
            name="Test",
            description="Test",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants
        )
        
        # Don't start the test
        variant = ab_system.assign_variant(test_id, "user_123")
        assert variant is None
    
    def test_get_variant_configuration(self, ab_system, test_variants):
        """Test getting variant configuration"""
        test_id = ab_system.create_test(
            name="Test",
            description="Test",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants
        )
        
        config = ab_system.get_variant_configuration(test_id, "control")
        assert config is not None
        assert config["optimization"] == "none"
        
        config = ab_system.get_variant_configuration(test_id, "treatment")
        assert config is not None
        assert config["optimization"] == "cache_enabled"
    
    def test_record_test_result(self, ab_system, test_variants):
        """Test recording test results"""
        test_id = ab_system.create_test(
            name="Test",
            description="Test",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants
        )
        
        ab_system.start_test(test_id)
        
        # Create test metrics
        metrics = ResponsePerformanceMetrics(
            response_id="test_response",
            timestamp=datetime.now(),
            query="test query",
            model_used="test_model",
            response_time=2.5,
            cpu_usage=10.0,
            memory_usage=1024 * 1024
        )
        
        ab_system.record_test_result(test_id, "control", metrics)
        
        key = f"{test_id}:control"
        assert key in ab_system.test_results
        assert len(ab_system.test_results[key]) == 1
        assert ab_system.test_results[key][0] == metrics
    
    def test_get_test_status(self, ab_system, test_variants):
        """Test getting test status"""
        test_id = ab_system.create_test(
            name="Test",
            description="Test",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants
        )
        
        ab_system.start_test(test_id)
        
        # Add some test data
        metrics = ResponsePerformanceMetrics(
            response_id="test_response",
            timestamp=datetime.now(),
            query="test query",
            model_used="test_model",
            response_time=2.5,
            cpu_usage=10.0,
            memory_usage=1024 * 1024
        )
        
        ab_system.record_test_result(test_id, "control", metrics)
        
        status = ab_system.get_test_status(test_id)
        assert status is not None
        assert "test" in status
        assert "variant_stats" in status
        assert "total_sample_size" in status
        assert "progress" in status
        
        assert status["variant_stats"]["control"]["sample_size"] == 1
        assert status["total_sample_size"] == 1
    
    def test_analyze_test_results(self, ab_system, test_variants):
        """Test analyzing test results"""
        test_id = ab_system.create_test(
            name="Test",
            description="Test",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants
        )
        
        ab_system.start_test(test_id)
        
        # Add control group data (slower responses)
        for i in range(10):
            metrics = ResponsePerformanceMetrics(
                response_id=f"control_{i}",
                timestamp=datetime.now(),
                query=f"query_{i}",
                model_used="test_model",
                response_time=3.0 + i * 0.1,  # 3.0 to 3.9 seconds
                cpu_usage=15.0,
                memory_usage=1024 * 1024
            )
            ab_system.record_test_result(test_id, "control", metrics)
        
        # Add treatment group data (faster responses)
        for i in range(10):
            metrics = ResponsePerformanceMetrics(
                response_id=f"treatment_{i}",
                timestamp=datetime.now(),
                query=f"query_{i}",
                model_used="test_model",
                response_time=2.0 + i * 0.1,  # 2.0 to 2.9 seconds
                cpu_usage=12.0,
                memory_usage=1024 * 1024
            )
            ab_system.record_test_result(test_id, "treatment", metrics)
        
        results = ab_system.analyze_test_results(test_id)
        assert results is not None
        assert results.test_id == test_id
        assert len(results.variant_metrics) == 2
        
        control_metrics = results.variant_metrics["control"]
        treatment_metrics = results.variant_metrics["treatment"]
        
        assert control_metrics.sample_size == 10
        assert treatment_metrics.sample_size == 10
        assert treatment_metrics.avg_response_time < control_metrics.avg_response_time
        
        # Treatment should be the winner
        assert results.winner_variant_id == "treatment"
        assert results.effect_size > 0
    
    def test_get_active_tests(self, ab_system, test_variants):
        """Test getting active tests"""
        # Create and start a test
        test_id = ab_system.create_test(
            name="Active Test",
            description="Test",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants
        )
        ab_system.start_test(test_id)
        
        # Create but don't start another test
        ab_system.create_test(
            name="Inactive Test",
            description="Test",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants
        )
        
        active_tests = ab_system.get_active_tests()
        assert len(active_tests) == 1
        assert active_tests[0].name == "Active Test"
        assert active_tests[0].status == TestStatus.ACTIVE
    
    def test_get_test_history(self, ab_system, test_variants):
        """Test getting test history"""
        # Create multiple tests
        for i in range(3):
            ab_system.create_test(
                name=f"Test {i}",
                description="Test",
                test_type=TestType.OPTIMIZATION_TECHNIQUE,
                variants=test_variants
            )
        
        history = ab_system.get_test_history(limit=2)
        assert len(history) == 2
        
        all_history = ab_system.get_test_history(limit=10)
        assert len(all_history) == 3
    
    def test_variant_assignment_distribution(self, ab_system, test_variants):
        """Test that variant assignment follows traffic percentages"""
        test_id = ab_system.create_test(
            name="Distribution Test",
            description="Test",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants
        )
        ab_system.start_test(test_id)
        
        # Assign variants to many users
        assignments = {}
        for i in range(1000):
            user_id = f"user_{i}"
            variant = ab_system.assign_variant(test_id, user_id)
            assignments[variant] = assignments.get(variant, 0) + 1
        
        # Check distribution is roughly 50/50
        control_pct = assignments.get("control", 0) / 1000 * 100
        treatment_pct = assignments.get("treatment", 0) / 1000 * 100
        
        # Allow for some variance (40-60% range)
        assert 40 <= control_pct <= 60
        assert 40 <= treatment_pct <= 60
    
    def test_hash_based_assignment_consistency(self, ab_system, test_variants):
        """Test that hash-based assignment is consistent across multiple calls"""
        test_id = ab_system.create_test(
            name="Consistency Test",
            description="Test",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=test_variants
        )
        ab_system.start_test(test_id)
        
        # Test multiple users multiple times
        for user_id in ["user_1", "user_2", "user_3"]:
            assignments = []
            for _ in range(10):
                variant = ab_system.assign_variant(test_id, user_id)
                assignments.append(variant)
            
            # All assignments for the same user should be identical
            assert len(set(assignments)) == 1


class TestTestVariant:
    """Test cases for TestVariant"""
    
    def test_variant_creation(self):
        """Test creating a test variant"""
        variant = TestVariant(
            id="test_variant",
            name="Test Variant",
            description="A test variant",
            configuration={"param1": "value1", "param2": 42},
            traffic_percentage=25.0,
            is_control=False
        )
        
        assert variant.id == "test_variant"
        assert variant.name == "Test Variant"
        assert variant.description == "A test variant"
        assert variant.configuration["param1"] == "value1"
        assert variant.configuration["param2"] == 42
        assert variant.traffic_percentage == 25.0
        assert variant.is_control is False


class TestABTest:
    """Test cases for ABTest"""
    
    def test_ab_test_creation(self):
        """Test creating an A/B test"""
        variants = [
            TestVariant("control", "Control", "Control variant", {}, 50.0, True),
            TestVariant("treatment", "Treatment", "Treatment variant", {}, 50.0, False)
        ]
        
        test = ABTest(
            id="test_123",
            name="Test Experiment",
            description="A test experiment",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=variants,
            status=TestStatus.DRAFT,
            start_date=None,
            end_date=None,
            target_sample_size=1000,
            confidence_level=0.95,
            minimum_effect_size=0.1,
            success_metrics=["response_time", "user_satisfaction"],
            created_by="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert test.id == "test_123"
        assert test.name == "Test Experiment"
        assert test.test_type == TestType.OPTIMIZATION_TECHNIQUE
        assert test.status == TestStatus.DRAFT
        assert len(test.variants) == 2
        assert test.target_sample_size == 1000
        assert test.confidence_level == 0.95
        assert "response_time" in test.success_metrics


class TestTestMetrics:
    """Test cases for TestMetrics"""
    
    def test_test_metrics_creation(self):
        """Test creating test metrics"""
        metrics = TestMetrics(
            variant_id="test_variant",
            sample_size=100,
            avg_response_time=2.5,
            p95_response_time=4.0,
            avg_cpu_usage=15.0,
            avg_memory_usage=1024 * 1024 * 512,
            cache_hit_rate=75.0,
            error_rate=2.0,
            user_satisfaction=4.2,
            conversion_rate=12.5,
            confidence_interval=(2.3, 2.7),
            statistical_significance=95.0
        )
        
        assert metrics.variant_id == "test_variant"
        assert metrics.sample_size == 100
        assert metrics.avg_response_time == 2.5
        assert metrics.cache_hit_rate == 75.0
        assert metrics.user_satisfaction == 4.2
        assert metrics.confidence_interval == (2.3, 2.7)


@pytest.mark.asyncio
class TestABTestingIntegration:
    """Integration tests for A/B testing system"""
    
    async def test_complete_ab_test_workflow(self):
        """Test complete A/B test workflow"""
        ab_system = ABTestingSystem()
        
        # Create test variants
        variants = [
            TestVariant(
                id="control",
                name="Control",
                description="Current implementation",
                configuration={"cache_enabled": False},
                traffic_percentage=50.0,
                is_control=True
            ),
            TestVariant(
                id="treatment",
                name="Treatment",
                description="With caching enabled",
                configuration={"cache_enabled": True},
                traffic_percentage=50.0,
                is_control=False
            )
        ]
        
        # Create test
        test_id = ab_system.create_test(
            name="Cache Effectiveness Test",
            description="Test if caching improves response times",
            test_type=TestType.CACHE_OPTIMIZATION,
            variants=variants,
            target_sample_size=100
        )
        
        # Start test
        assert ab_system.start_test(test_id) is True
        
        # Simulate user assignments and results
        users_control = []
        users_treatment = []
        
        for i in range(100):
            user_id = f"user_{i}"
            variant = ab_system.assign_variant(test_id, user_id)
            
            if variant == "control":
                users_control.append(user_id)
                # Simulate slower responses without cache
                response_time = 3.0 + (i % 10) * 0.1
            else:
                users_treatment.append(user_id)
                # Simulate faster responses with cache
                response_time = 2.0 + (i % 10) * 0.1
            
            # Record result
            metrics = ResponsePerformanceMetrics(
                response_id=f"response_{i}",
                timestamp=datetime.now(),
                query=f"query_{i}",
                model_used="test_model",
                response_time=response_time,
                cpu_usage=10.0,
                memory_usage=1024 * 1024
            )
            
            ab_system.record_test_result(test_id, variant, metrics)
        
        # Check test status
        status = ab_system.get_test_status(test_id)
        assert status["total_sample_size"] == 100
        assert status["progress"] == 100.0  # Reached target sample size
        
        # Stop and analyze test
        assert ab_system.stop_test(test_id) is True
        
        # Get final results
        test = ab_system.active_tests[test_id]
        assert test.status == TestStatus.COMPLETED
        assert test.results is not None
        
        # Verify results show treatment as winner
        results = ab_system.analyze_test_results(test_id)
        assert results.winner_variant_id == "treatment"
        assert results.effect_size > 0  # Treatment should be better
        
        # Verify both variants have data
        assert "control" in results.variant_metrics
        assert "treatment" in results.variant_metrics
        assert results.variant_metrics["control"].sample_size > 0
        assert results.variant_metrics["treatment"].sample_size > 0
    
    async def test_ab_test_with_no_significant_difference(self):
        """Test A/B test where variants perform similarly"""
        ab_system = ABTestingSystem()
        
        variants = [
            TestVariant("control", "Control", "Control", {}, 50.0, True),
            TestVariant("treatment", "Treatment", "Treatment", {}, 50.0, False)
        ]
        
        test_id = ab_system.create_test(
            name="No Difference Test",
            description="Test with no significant difference",
            test_type=TestType.OPTIMIZATION_TECHNIQUE,
            variants=variants
        )
        
        ab_system.start_test(test_id)
        
        # Add similar performance data for both variants
        for i in range(50):
            # Control group
            metrics_control = ResponsePerformanceMetrics(
                response_id=f"control_{i}",
                timestamp=datetime.now(),
                query=f"query_{i}",
                model_used="test_model",
                response_time=2.5 + (i % 5) * 0.01,  # Very similar times
                cpu_usage=10.0,
                memory_usage=1024 * 1024
            )
            ab_system.record_test_result(test_id, "control", metrics_control)
            
            # Treatment group
            metrics_treatment = ResponsePerformanceMetrics(
                response_id=f"treatment_{i}",
                timestamp=datetime.now(),
                query=f"query_{i}",
                model_used="test_model",
                response_time=2.5 + (i % 5) * 0.01,  # Very similar times
                cpu_usage=10.0,
                memory_usage=1024 * 1024
            )
            ab_system.record_test_result(test_id, "treatment", metrics_treatment)
        
        ab_system.stop_test(test_id)
        results = ab_system.analyze_test_results(test_id)
        
        # Should not have a clear winner
        assert results.winner_variant_id is None or results.effect_size < 0.05
        assert results.p_value > 0.05  # Not statistically significant