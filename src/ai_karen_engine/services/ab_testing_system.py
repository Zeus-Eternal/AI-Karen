"""
A/B Testing System for Response Optimization

This module provides comprehensive A/B testing capabilities for different response
strategies and optimizations, allowing for data-driven optimization decisions.
"""

import asyncio
import json
import logging
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import statistics
import threading

from .response_performance_metrics import ResponsePerformanceMetrics, performance_collector

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Status of an A/B test"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestType(Enum):
    """Types of A/B tests"""
    RESPONSE_STRATEGY = "response_strategy"
    OPTIMIZATION_TECHNIQUE = "optimization_technique"
    MODEL_SELECTION = "model_selection"
    CACHING_STRATEGY = "caching_strategy"
    CONTENT_FORMATTING = "content_formatting"
    STREAMING_APPROACH = "streaming_approach"


@dataclass
class TestVariant:
    """A variant in an A/B test"""
    id: str
    name: str
    description: str
    configuration: Dict[str, Any]
    traffic_percentage: float
    is_control: bool = False


@dataclass
class TestMetrics:
    """Metrics for a test variant"""
    variant_id: str
    sample_size: int
    avg_response_time: float
    p95_response_time: float
    avg_cpu_usage: float
    avg_memory_usage: float
    cache_hit_rate: float
    error_rate: float
    user_satisfaction: Optional[float]
    conversion_rate: Optional[float]  # For business metrics
    confidence_interval: Tuple[float, float]
    statistical_significance: float


@dataclass
class ABTest:
    """A/B test configuration and state"""
    id: str
    name: str
    description: str
    test_type: TestType
    variants: List[TestVariant]
    status: TestStatus
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    target_sample_size: int
    confidence_level: float
    minimum_effect_size: float
    success_metrics: List[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    results: Optional[Dict[str, Any]] = None


@dataclass
class TestResult:
    """Results of an A/B test"""
    test_id: str
    winner_variant_id: Optional[str]
    confidence_level: float
    effect_size: float
    p_value: float
    variant_metrics: Dict[str, TestMetrics]
    recommendations: List[str]
    statistical_summary: str
    business_impact: Optional[Dict[str, float]]


class ABTestingSystem:
    """Comprehensive A/B testing system for response optimization"""
    
    def __init__(self):
        self.active_tests: Dict[str, ABTest] = {}
        self.test_assignments: Dict[str, Dict[str, str]] = {}  # user_id -> test_id -> variant_id
        self.test_results: Dict[str, List[ResponsePerformanceMetrics]] = defaultdict(list)
        self.lock = threading.Lock()
        
        # Statistical configuration
        self.default_confidence_level = 0.95
        self.minimum_sample_size = 100
        self.maximum_test_duration = timedelta(days=30)
    
    def create_test(
        self,
        name: str,
        description: str,
        test_type: TestType,
        variants: List[TestVariant],
        target_sample_size: int = 1000,
        confidence_level: float = 0.95,
        minimum_effect_size: float = 0.1,
        success_metrics: List[str] = None,
        created_by: str = "system"
    ) -> str:
        """Create a new A/B test"""
        if success_metrics is None:
            success_metrics = ["response_time", "user_satisfaction"]
        
        # Validate variants
        total_traffic = sum(v.traffic_percentage for v in variants)
        if abs(total_traffic - 100.0) > 0.01:
            raise ValueError(f"Variant traffic percentages must sum to 100%, got {total_traffic}%")
        
        control_variants = [v for v in variants if v.is_control]
        if len(control_variants) != 1:
            raise ValueError("Exactly one variant must be marked as control")
        
        test_id = self._generate_test_id(name)
        test = ABTest(
            id=test_id,
            name=name,
            description=description,
            test_type=test_type,
            variants=variants,
            status=TestStatus.DRAFT,
            start_date=None,
            end_date=None,
            target_sample_size=target_sample_size,
            confidence_level=confidence_level,
            minimum_effect_size=minimum_effect_size,
            success_metrics=success_metrics,
            created_by=created_by,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with self.lock:
            self.active_tests[test_id] = test
        
        logger.info(f"Created A/B test: {name} (ID: {test_id})")
        return test_id
    
    def start_test(self, test_id: str) -> bool:
        """Start an A/B test"""
        with self.lock:
            if test_id not in self.active_tests:
                logger.error(f"Test {test_id} not found")
                return False
            
            test = self.active_tests[test_id]
            if test.status != TestStatus.DRAFT:
                logger.error(f"Test {test_id} cannot be started from status {test.status}")
                return False
            
            test.status = TestStatus.ACTIVE
            test.start_date = datetime.now()
            test.updated_at = datetime.now()
        
        logger.info(f"Started A/B test: {test.name} (ID: {test_id})")
        return True
    
    def pause_test(self, test_id: str) -> bool:
        """Pause an active A/B test"""
        with self.lock:
            if test_id not in self.active_tests:
                return False
            
            test = self.active_tests[test_id]
            if test.status != TestStatus.ACTIVE:
                return False
            
            test.status = TestStatus.PAUSED
            test.updated_at = datetime.now()
        
        logger.info(f"Paused A/B test: {test.name} (ID: {test_id})")
        return True
    
    def resume_test(self, test_id: str) -> bool:
        """Resume a paused A/B test"""
        with self.lock:
            if test_id not in self.active_tests:
                return False
            
            test = self.active_tests[test_id]
            if test.status != TestStatus.PAUSED:
                return False
            
            test.status = TestStatus.ACTIVE
            test.updated_at = datetime.now()
        
        logger.info(f"Resumed A/B test: {test.name} (ID: {test_id})")
        return True
    
    def stop_test(self, test_id: str, reason: str = "manual") -> bool:
        """Stop an A/B test and analyze results"""
        with self.lock:
            if test_id not in self.active_tests:
                return False
            
            test = self.active_tests[test_id]
            if test.status not in [TestStatus.ACTIVE, TestStatus.PAUSED]:
                return False
            
            test.status = TestStatus.COMPLETED
            test.end_date = datetime.now()
            test.updated_at = datetime.now()
        
        # Analyze results
        results = self.analyze_test_results(test_id)
        if results:
            with self.lock:
                self.active_tests[test_id].results = asdict(results)
        
        logger.info(f"Stopped A/B test: {test.name} (ID: {test_id}), reason: {reason}")
        return True
    
    def assign_variant(self, test_id: str, user_id: str) -> Optional[str]:
        """Assign a user to a test variant"""
        with self.lock:
            if test_id not in self.active_tests:
                return None
            
            test = self.active_tests[test_id]
            if test.status != TestStatus.ACTIVE:
                return None
            
            # Check if user already assigned
            if user_id in self.test_assignments and test_id in self.test_assignments[user_id]:
                return self.test_assignments[user_id][test_id]
            
            # Assign variant based on consistent hashing
            variant_id = self._assign_variant_by_hash(user_id, test.variants)
            
            # Store assignment
            if user_id not in self.test_assignments:
                self.test_assignments[user_id] = {}
            self.test_assignments[user_id][test_id] = variant_id
            
            return variant_id
    
    def get_variant_configuration(self, test_id: str, variant_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific variant"""
        with self.lock:
            if test_id not in self.active_tests:
                return None
            
            test = self.active_tests[test_id]
            for variant in test.variants:
                if variant.id == variant_id:
                    return variant.configuration
            
            return None
    
    def record_test_result(self, test_id: str, variant_id: str, metrics: ResponsePerformanceMetrics) -> None:
        """Record performance metrics for a test variant"""
        with self.lock:
            if test_id not in self.active_tests:
                return
            
            # Store metrics with variant information
            key = f"{test_id}:{variant_id}"
            self.test_results[key].append(metrics)
    
    def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get current status and metrics for a test"""
        with self.lock:
            if test_id not in self.active_tests:
                return None
            
            test = self.active_tests[test_id]
            
            # Calculate current metrics for each variant
            variant_stats = {}
            for variant in test.variants:
                key = f"{test_id}:{variant.id}"
                metrics_list = self.test_results[key]
                
                if metrics_list:
                    variant_stats[variant.id] = {
                        'sample_size': len(metrics_list),
                        'avg_response_time': statistics.mean([m.response_time for m in metrics_list]),
                        'avg_cpu_usage': statistics.mean([m.cpu_usage for m in metrics_list]),
                        'error_rate': len([m for m in metrics_list if m.error_occurred]) / len(metrics_list) * 100,
                        'cache_hit_rate': statistics.mean([m.cache_hit_rate for m in metrics_list])
                    }
                else:
                    variant_stats[variant.id] = {
                        'sample_size': 0,
                        'avg_response_time': 0.0,
                        'avg_cpu_usage': 0.0,
                        'error_rate': 0.0,
                        'cache_hit_rate': 0.0
                    }
            
            return {
                'test': asdict(test),
                'variant_stats': variant_stats,
                'total_sample_size': sum(stats['sample_size'] for stats in variant_stats.values()),
                'progress': min(100.0, sum(stats['sample_size'] for stats in variant_stats.values()) / test.target_sample_size * 100)
            }
    
    def analyze_test_results(self, test_id: str) -> Optional[TestResult]:
        """Analyze A/B test results and determine statistical significance"""
        with self.lock:
            if test_id not in self.active_tests:
                return None
            
            test = self.active_tests[test_id]
            
            # Collect metrics for each variant
            variant_metrics = {}
            control_variant_id = None
            
            for variant in test.variants:
                key = f"{test_id}:{variant.id}"
                metrics_list = self.test_results[key]
                
                if variant.is_control:
                    control_variant_id = variant.id
                
                if not metrics_list:
                    continue
                
                # Calculate comprehensive metrics
                response_times = [m.response_time for m in metrics_list]
                cpu_usages = [m.cpu_usage for m in metrics_list]
                memory_usages = [m.memory_usage for m in metrics_list]
                cache_hit_rates = [m.cache_hit_rate for m in metrics_list]
                user_satisfactions = [m.user_satisfaction_score for m in metrics_list if m.user_satisfaction_score is not None]
                
                # Calculate confidence interval for response time
                mean_response_time = statistics.mean(response_times)
                if len(response_times) > 1:
                    stdev = statistics.stdev(response_times)
                    margin_of_error = 1.96 * stdev / (len(response_times) ** 0.5)  # 95% CI
                    confidence_interval = (mean_response_time - margin_of_error, mean_response_time + margin_of_error)
                else:
                    confidence_interval = (mean_response_time, mean_response_time)
                
                variant_metrics[variant.id] = TestMetrics(
                    variant_id=variant.id,
                    sample_size=len(metrics_list),
                    avg_response_time=mean_response_time,
                    p95_response_time=statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else mean_response_time,
                    avg_cpu_usage=statistics.mean(cpu_usages),
                    avg_memory_usage=statistics.mean(memory_usages),
                    cache_hit_rate=statistics.mean(cache_hit_rates),
                    error_rate=len([m for m in metrics_list if m.error_occurred]) / len(metrics_list) * 100,
                    user_satisfaction=statistics.mean(user_satisfactions) if user_satisfactions else None,
                    conversion_rate=None,  # Would need business logic to calculate
                    confidence_interval=confidence_interval,
                    statistical_significance=0.0  # Will be calculated below
                )
            
            if not variant_metrics or control_variant_id not in variant_metrics:
                return None
            
            # Perform statistical analysis
            control_metrics = variant_metrics[control_variant_id]
            winner_variant_id = None
            best_improvement = 0.0
            p_value = 1.0
            
            for variant_id, metrics in variant_metrics.items():
                if variant_id == control_variant_id:
                    continue
                
                # Calculate statistical significance using t-test approximation
                control_key = f"{test_id}:{control_variant_id}"
                variant_key = f"{test_id}:{variant_id}"
                
                control_times = [m.response_time for m in self.test_results[control_key]]
                variant_times = [m.response_time for m in self.test_results[variant_key]]
                
                if len(control_times) > 1 and len(variant_times) > 1:
                    # Simple t-test approximation
                    control_mean = statistics.mean(control_times)
                    variant_mean = statistics.mean(variant_times)
                    
                    improvement = (control_mean - variant_mean) / control_mean * 100
                    
                    if improvement > best_improvement and improvement > test.minimum_effect_size * 100:
                        best_improvement = improvement
                        winner_variant_id = variant_id
                        
                        # Simplified p-value calculation
                        pooled_std = (statistics.stdev(control_times) + statistics.stdev(variant_times)) / 2
                        if pooled_std > 0:
                            t_stat = abs(control_mean - variant_mean) / (pooled_std * ((1/len(control_times) + 1/len(variant_times)) ** 0.5))
                            # Rough p-value approximation
                            p_value = max(0.001, 2 * (1 - min(0.999, t_stat / 3)))
                        
                        metrics.statistical_significance = max(0, 100 - p_value * 100)
            
            # Generate recommendations
            recommendations = self._generate_test_recommendations(test, variant_metrics, winner_variant_id)
            
            # Create statistical summary
            statistical_summary = self._create_statistical_summary(test, variant_metrics, winner_variant_id, p_value)
            
            return TestResult(
                test_id=test_id,
                winner_variant_id=winner_variant_id,
                confidence_level=test.confidence_level,
                effect_size=best_improvement / 100,
                p_value=p_value,
                variant_metrics=variant_metrics,
                recommendations=recommendations,
                statistical_summary=statistical_summary,
                business_impact=None  # Would need business metrics
            )
    
    def get_active_tests(self) -> List[ABTest]:
        """Get all active tests"""
        with self.lock:
            return [test for test in self.active_tests.values() if test.status == TestStatus.ACTIVE]
    
    def get_test_history(self, limit: int = 50) -> List[ABTest]:
        """Get test history"""
        with self.lock:
            all_tests = list(self.active_tests.values())
            all_tests.sort(key=lambda t: t.updated_at, reverse=True)
            return all_tests[:limit]
    
    def _generate_test_id(self, name: str) -> str:
        """Generate unique test ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"test_{timestamp}_{name_hash}"
    
    def _assign_variant_by_hash(self, user_id: str, variants: List[TestVariant]) -> str:
        """Assign variant using consistent hashing"""
        # Create hash of user ID
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        percentage = (hash_value % 10000) / 100.0  # 0-99.99%
        
        # Assign based on traffic percentages
        cumulative = 0.0
        for variant in variants:
            cumulative += variant.traffic_percentage
            if percentage < cumulative:
                return variant.id
        
        # Fallback to last variant
        return variants[-1].id
    
    def _generate_test_recommendations(
        self, 
        test: ABTest, 
        variant_metrics: Dict[str, TestMetrics], 
        winner_variant_id: Optional[str]
    ) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if winner_variant_id:
            winner_metrics = variant_metrics[winner_variant_id]
            control_variant_id = next(v.id for v in test.variants if v.is_control)
            control_metrics = variant_metrics[control_variant_id]
            
            improvement = (control_metrics.avg_response_time - winner_metrics.avg_response_time) / control_metrics.avg_response_time * 100
            
            recommendations.append(f"Deploy winning variant '{winner_variant_id}' - shows {improvement:.1f}% response time improvement")
            
            if winner_metrics.cache_hit_rate > control_metrics.cache_hit_rate:
                recommendations.append("Winner shows improved cache performance - consider optimizing cache strategy")
            
            if winner_metrics.avg_cpu_usage < control_metrics.avg_cpu_usage:
                recommendations.append("Winner shows reduced CPU usage - consider resource allocation optimization")
        else:
            recommendations.append("No statistically significant winner found - consider extending test duration or increasing sample size")
            
            # Analyze why no winner was found
            sample_sizes = [m.sample_size for m in variant_metrics.values()]
            if min(sample_sizes) < self.minimum_sample_size:
                recommendations.append(f"Increase sample size - minimum {self.minimum_sample_size} samples per variant recommended")
        
        return recommendations
    
    def _create_statistical_summary(
        self, 
        test: ABTest, 
        variant_metrics: Dict[str, TestMetrics], 
        winner_variant_id: Optional[str], 
        p_value: float
    ) -> str:
        """Create statistical summary of test results"""
        total_samples = sum(m.sample_size for m in variant_metrics.values())
        
        summary = f"Test '{test.name}' completed with {total_samples} total samples across {len(variant_metrics)} variants.\n"
        
        if winner_variant_id:
            summary += f"Winner: Variant '{winner_variant_id}' with p-value {p_value:.3f} "
            summary += f"({'significant' if p_value < 0.05 else 'not significant'} at α=0.05).\n"
        else:
            summary += "No statistically significant winner identified.\n"
        
        # Add variant performance summary
        summary += "\nVariant Performance:\n"
        for variant_id, metrics in variant_metrics.items():
            is_control = any(v.is_control and v.id == variant_id for v in test.variants)
            control_label = " (Control)" if is_control else ""
            summary += f"- {variant_id}{control_label}: {metrics.avg_response_time:.2f}s avg response time, "
            summary += f"{metrics.sample_size} samples, {metrics.error_rate:.1f}% error rate\n"
        
        return summary


# Global A/B testing system instance
ab_testing_system = ABTestingSystem()