"""
Automated Optimization Recommendation Engine

This module provides intelligent recommendations for response optimization based on
performance data, user satisfaction metrics, and system analytics.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import statistics
import threading

from ...internal.response_performance_metrics import ResponsePerformanceMetrics, performance_collector
from ...internal.user_satisfaction_tracker import satisfaction_tracker, SatisfactionMetrics
from ...internal.ab_testing_system import ab_testing_system, TestType, TestVariant

logger = logging.getLogger(__name__)


class RecommendationType(Enum):
    """Types of optimization recommendations"""
    MODEL_OPTIMIZATION = "model_optimization"
    CACHE_OPTIMIZATION = "cache_optimization"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    CONTENT_OPTIMIZATION = "content_optimization"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    USER_EXPERIENCE_OPTIMIZATION = "user_experience_optimization"
    SYSTEM_CONFIGURATION = "system_configuration"


class Priority(Enum):
    """Recommendation priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ImplementationComplexity(Enum):
    """Implementation complexity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class OptimizationRecommendation:
    """A specific optimization recommendation"""
    id: str
    title: str
    description: str
    recommendation_type: RecommendationType
    priority: Priority
    complexity: ImplementationComplexity
    estimated_impact: float  # 0-100 percentage improvement
    confidence_score: float  # 0-1 confidence in recommendation
    supporting_data: Dict[str, Any]
    implementation_steps: List[str]
    success_metrics: List[str]
    estimated_effort_hours: int
    prerequisites: List[str]
    risks: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    implemented: bool = False
    implementation_date: Optional[datetime] = None
    actual_impact: Optional[float] = None


@dataclass
class RecommendationSuite:
    """A suite of related recommendations"""
    id: str
    name: str
    description: str
    recommendations: List[OptimizationRecommendation]
    total_estimated_impact: float
    total_effort_hours: int
    implementation_order: List[str]  # Recommendation IDs in order
    created_at: datetime


@dataclass
class SystemHealthAnalysis:
    """Analysis of overall system health and performance"""
    overall_health_score: float  # 0-100
    performance_score: float
    satisfaction_score: float
    resource_efficiency_score: float
    critical_issues: List[str]
    improvement_opportunities: List[str]
    trending_metrics: Dict[str, str]  # metric -> trend (IMPROVING/DECLINING/STABLE)
    bottleneck_analysis: Dict[str, float]  # bottleneck -> impact score


class OptimizationRecommendationEngine:
    """Intelligent optimization recommendation system"""
    
    def __init__(self):
        self.recommendations_history: List[OptimizationRecommendation] = []
        self.recommendation_suites: List[RecommendationSuite] = []
        self.lock = threading.Lock()
        
        # Analysis configuration
        self.analysis_window = timedelta(hours=24)
        self.min_data_points = 50
        self.performance_thresholds = {
            'response_time': 3.0,  # seconds
            'cpu_usage': 5.0,      # percentage
            'memory_usage': 1024 * 1024 * 1024,  # 1GB
            'error_rate': 5.0,     # percentage
            'satisfaction': 3.5    # out of 5
        }
        
        # Start background recommendation generation
        self._start_background_analysis()
    
    def generate_recommendations(self, force_analysis: bool = False) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on current system state"""
        try:
            # Collect performance data
            performance_metrics = performance_collector.get_aggregated_metrics(self.analysis_window)
            satisfaction_metrics = satisfaction_tracker.get_satisfaction_metrics(self.analysis_window)
            
            if performance_metrics.total_responses < self.min_data_points and not force_analysis:
                logger.info(f"Insufficient data for recommendations: {performance_metrics.total_responses} responses")
                return []
            
            recommendations = []
            
            # Analyze different aspects of the system
            recommendations.extend(self._analyze_performance_issues(performance_metrics))
            recommendations.extend(self._analyze_satisfaction_issues(satisfaction_metrics))
            recommendations.extend(self._analyze_resource_utilization(performance_metrics))
            recommendations.extend(self._analyze_model_performance(performance_metrics))
            recommendations.extend(self._analyze_cache_effectiveness(performance_metrics))
            recommendations.extend(self._analyze_optimization_effectiveness(performance_metrics))
            
            # Sort by priority and impact
            recommendations.sort(key=lambda r: (
                self._priority_score(r.priority),
                r.estimated_impact,
                r.confidence_score
            ), reverse=True)
            
            # Store recommendations
            with self.lock:
                self.recommendations_history.extend(recommendations)
                # Keep only recent recommendations
                cutoff_date = datetime.now() - timedelta(days=30)
                self.recommendations_history = [
                    r for r in self.recommendations_history 
                    if r.created_at >= cutoff_date
                ]
            
            logger.info(f"Generated {len(recommendations)} optimization recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def create_recommendation_suite(
        self, 
        name: str, 
        description: str, 
        recommendation_ids: List[str]
    ) -> Optional[str]:
        """Create a suite of related recommendations"""
        with self.lock:
            # Find recommendations
            recommendations = []
            for rec_id in recommendation_ids:
                rec = next((r for r in self.recommendations_history if r.id == rec_id), None)
                if rec:
                    recommendations.append(rec)
            
            if not recommendations:
                return None
            
            # Calculate suite metrics
            total_impact = sum(r.estimated_impact for r in recommendations)
            total_effort = sum(r.estimated_effort_hours for r in recommendations)
            
            # Determine implementation order based on dependencies and impact
            implementation_order = self._determine_implementation_order(recommendations)
            
            suite_id = self._generate_suite_id()
            suite = RecommendationSuite(
                id=suite_id,
                name=name,
                description=description,
                recommendations=recommendations,
                total_estimated_impact=total_impact,
                total_effort_hours=total_effort,
                implementation_order=implementation_order,
                created_at=datetime.now()
            )
            
            self.recommendation_suites.append(suite)
            return suite_id
    
    def analyze_system_health(self) -> SystemHealthAnalysis:
        """Analyze overall system health and performance"""
        try:
            performance_metrics = performance_collector.get_aggregated_metrics(self.analysis_window)
            satisfaction_metrics = satisfaction_tracker.get_satisfaction_metrics(self.analysis_window)
            
            # Calculate health scores
            performance_score = self._calculate_performance_score(performance_metrics)
            satisfaction_score = self._calculate_satisfaction_score(satisfaction_metrics)
            resource_efficiency_score = self._calculate_resource_efficiency_score(performance_metrics)
            
            overall_health_score = (performance_score + satisfaction_score + resource_efficiency_score) / 3
            
            # Identify critical issues
            critical_issues = []
            if performance_metrics.avg_response_time > self.performance_thresholds['response_time']:
                critical_issues.append(f"High response time: {performance_metrics.avg_response_time:.2f}s")
            
            if performance_metrics.error_rate > self.performance_thresholds['error_rate']:
                critical_issues.append(f"High error rate: {performance_metrics.error_rate:.1f}%")
            
            if satisfaction_metrics.avg_rating < self.performance_thresholds['satisfaction']:
                critical_issues.append(f"Low user satisfaction: {satisfaction_metrics.avg_rating:.1f}/5.0")
            
            # Identify improvement opportunities
            improvement_opportunities = []
            if performance_metrics.cache_hit_rate < 70:
                improvement_opportunities.append("Improve cache hit rate")
            
            if performance_metrics.avg_gpu_usage and performance_metrics.avg_gpu_usage < 30:
                improvement_opportunities.append("Increase GPU utilization")
            
            # Analyze trends
            trending_metrics = self._analyze_metric_trends()
            
            # Bottleneck analysis
            bottleneck_analysis = self._analyze_bottlenecks(performance_metrics)
            
            return SystemHealthAnalysis(
                overall_health_score=overall_health_score,
                performance_score=performance_score,
                satisfaction_score=satisfaction_score,
                resource_efficiency_score=resource_efficiency_score,
                critical_issues=critical_issues,
                improvement_opportunities=improvement_opportunities,
                trending_metrics=trending_metrics,
                bottleneck_analysis=bottleneck_analysis
            )
            
        except Exception as e:
            logger.error(f"Error analyzing system health: {e}")
            return SystemHealthAnalysis(
                overall_health_score=50.0,
                performance_score=50.0,
                satisfaction_score=50.0,
                resource_efficiency_score=50.0,
                critical_issues=["Error analyzing system health"],
                improvement_opportunities=[],
                trending_metrics={},
                bottleneck_analysis={}
            )
    
    def get_recommendations_by_priority(self, priority: Priority) -> List[OptimizationRecommendation]:
        """Get recommendations filtered by priority"""
        with self.lock:
            return [r for r in self.recommendations_history if r.priority == priority and not r.implemented]
    
    def get_quick_wins(self, max_effort_hours: int = 8) -> List[OptimizationRecommendation]:
        """Get quick win recommendations (high impact, low effort)"""
        with self.lock:
            quick_wins = [
                r for r in self.recommendations_history 
                if (r.estimated_effort_hours <= max_effort_hours and 
                    r.estimated_impact >= 20 and 
                    r.complexity in [ImplementationComplexity.LOW, ImplementationComplexity.MEDIUM] and
                    not r.implemented)
            ]
            
            # Sort by impact/effort ratio
            quick_wins.sort(key=lambda r: r.estimated_impact / max(r.estimated_effort_hours, 1), reverse=True)
            return quick_wins
    
    def mark_recommendation_implemented(
        self, 
        recommendation_id: str, 
        actual_impact: Optional[float] = None
    ) -> bool:
        """Mark a recommendation as implemented"""
        with self.lock:
            for rec in self.recommendations_history:
                if rec.id == recommendation_id:
                    rec.implemented = True
                    rec.implementation_date = datetime.now()
                    rec.actual_impact = actual_impact
                    logger.info(f"Marked recommendation {recommendation_id} as implemented")
                    return True
            return False
    
    def suggest_ab_tests(self) -> List[Dict[str, Any]]:
        """Suggest A/B tests based on recommendations"""
        suggestions = []
        
        with self.lock:
            # Group recommendations by type
            by_type = defaultdict(list)
            for rec in self.recommendations_history:
                if not rec.implemented and rec.confidence_score < 0.8:  # Only suggest tests for uncertain recommendations
                    by_type[rec.recommendation_type].append(rec)
        
        for rec_type, recommendations in by_type.items():
            if len(recommendations) >= 2:  # Need at least 2 variants
                # Create A/B test suggestion
                test_name = f"Test {rec_type.value.replace('_', ' ').title()}"
                
                variants = []
                for i, rec in enumerate(recommendations[:3]):  # Max 3 variants
                    variants.append({
                        'id': f'variant_{i+1}',
                        'name': rec.title,
                        'description': rec.description,
                        'configuration': rec.supporting_data,
                        'traffic_percentage': 100.0 / len(recommendations[:3]),
                        'is_control': i == 0
                    })
                
                suggestions.append({
                    'name': test_name,
                    'description': f"Test different {rec_type.value} strategies",
                    'test_type': TestType.OPTIMIZATION_TECHNIQUE,
                    'variants': variants,
                    'estimated_impact': max(r.estimated_impact for r in recommendations[:3]),
                    'confidence_needed': 0.95
                })
        
        return suggestions
    
    def _analyze_performance_issues(self, metrics) -> List[OptimizationRecommendation]:
        """Analyze performance issues and generate recommendations"""
        recommendations = []
        
        # High response time
        if metrics.avg_response_time > self.performance_thresholds['response_time']:
            impact = min(90, (metrics.avg_response_time - self.performance_thresholds['response_time']) * 30)
            
            recommendations.append(OptimizationRecommendation(
                id=self._generate_recommendation_id(),
                title="Optimize Response Time",
                description=f"Average response time is {metrics.avg_response_time:.2f}s, exceeding threshold of {self.performance_thresholds['response_time']}s",
                recommendation_type=RecommendationType.PERFORMANCE_OPTIMIZATION,
                priority=Priority.HIGH if metrics.avg_response_time > 5.0 else Priority.MEDIUM,
                complexity=ImplementationComplexity.MEDIUM,
                estimated_impact=impact,
                confidence_score=0.9,
                supporting_data={
                    'current_avg_response_time': metrics.avg_response_time,
                    'p95_response_time': metrics.p95_response_time,
                    'threshold': self.performance_thresholds['response_time']
                },
                implementation_steps=[
                    "Enable response caching for similar queries",
                    "Implement model preloading",
                    "Optimize content generation pipeline",
                    "Consider GPU acceleration for inference"
                ],
                success_metrics=['avg_response_time', 'p95_response_time'],
                estimated_effort_hours=16,
                prerequisites=["Performance monitoring in place"],
                risks=["May increase memory usage", "Requires careful cache invalidation"],
                created_at=datetime.now()
            ))
        
        # High error rate
        if metrics.error_rate > self.performance_thresholds['error_rate']:
            recommendations.append(OptimizationRecommendation(
                id=self._generate_recommendation_id(),
                title="Reduce Error Rate",
                description=f"Error rate is {metrics.error_rate:.1f}%, exceeding threshold of {self.performance_thresholds['error_rate']}%",
                recommendation_type=RecommendationType.SYSTEM_CONFIGURATION,
                priority=Priority.CRITICAL,
                complexity=ImplementationComplexity.HIGH,
                estimated_impact=70,
                confidence_score=0.95,
                supporting_data={
                    'current_error_rate': metrics.error_rate,
                    'threshold': self.performance_thresholds['error_rate']
                },
                implementation_steps=[
                    "Analyze error patterns and root causes",
                    "Implement better error handling and recovery",
                    "Add model fallback mechanisms",
                    "Improve input validation"
                ],
                success_metrics=['error_rate', 'system_availability'],
                estimated_effort_hours=24,
                prerequisites=["Error logging and monitoring"],
                risks=["May mask underlying issues if not properly analyzed"],
                created_at=datetime.now()
            ))
        
        return recommendations
    
    def _analyze_satisfaction_issues(self, metrics: SatisfactionMetrics) -> List[OptimizationRecommendation]:
        """Analyze user satisfaction issues"""
        recommendations = []
        
        if metrics.avg_rating < self.performance_thresholds['satisfaction']:
            recommendations.append(OptimizationRecommendation(
                id=self._generate_recommendation_id(),
                title="Improve User Satisfaction",
                description=f"Average user satisfaction is {metrics.avg_rating:.1f}/5.0, below threshold of {self.performance_thresholds['satisfaction']}",
                recommendation_type=RecommendationType.USER_EXPERIENCE_OPTIMIZATION,
                priority=Priority.HIGH,
                complexity=ImplementationComplexity.MEDIUM,
                estimated_impact=60,
                confidence_score=0.85,
                supporting_data={
                    'current_avg_rating': metrics.avg_rating,
                    'threshold': self.performance_thresholds['satisfaction'],
                    'common_complaints': metrics.common_complaints
                },
                implementation_steps=[
                    "Analyze common user complaints",
                    "Improve response relevance and accuracy",
                    "Enhance content formatting and presentation",
                    "Implement personalization features"
                ],
                success_metrics=['avg_rating', 'thumbs_up_percentage', 'net_promoter_score'],
                estimated_effort_hours=20,
                prerequisites=["User feedback collection system"],
                risks=["Changes may initially confuse existing users"],
                created_at=datetime.now()
            ))
        
        return recommendations
    
    def _analyze_resource_utilization(self, metrics) -> List[OptimizationRecommendation]:
        """Analyze resource utilization issues"""
        recommendations = []
        
        # High CPU usage
        if metrics.avg_cpu_usage > self.performance_thresholds['cpu_usage']:
            recommendations.append(OptimizationRecommendation(
                id=self._generate_recommendation_id(),
                title="Optimize CPU Usage",
                description=f"Average CPU usage is {metrics.avg_cpu_usage:.1f}%, exceeding threshold of {self.performance_thresholds['cpu_usage']}%",
                recommendation_type=RecommendationType.RESOURCE_OPTIMIZATION,
                priority=Priority.HIGH,
                complexity=ImplementationComplexity.MEDIUM,
                estimated_impact=50,
                confidence_score=0.8,
                supporting_data={
                    'current_cpu_usage': metrics.avg_cpu_usage,
                    'threshold': self.performance_thresholds['cpu_usage']
                },
                implementation_steps=[
                    "Profile CPU-intensive operations",
                    "Implement GPU acceleration where possible",
                    "Optimize model inference pipeline",
                    "Add request batching and queuing"
                ],
                success_metrics=['avg_cpu_usage', 'system_throughput'],
                estimated_effort_hours=18,
                prerequisites=["Performance profiling tools"],
                risks=["GPU acceleration may require additional hardware"],
                created_at=datetime.now()
            ))
        
        return recommendations
    
    def _analyze_model_performance(self, metrics) -> List[OptimizationRecommendation]:
        """Analyze model performance issues"""
        recommendations = []
        
        if metrics.most_used_models:
            # Find underperforming models
            model_performance = {}
            for model, usage_count in metrics.most_used_models.items():
                # This would need actual model performance data
                # For now, we'll use a placeholder analysis
                if usage_count > metrics.total_responses * 0.1:  # Models used in >10% of responses
                    model_performance[model] = usage_count
            
            if len(model_performance) > 1:
                recommendations.append(OptimizationRecommendation(
                    id=self._generate_recommendation_id(),
                    title="Optimize Model Selection",
                    description="Analyze and optimize model selection strategy based on usage patterns",
                    recommendation_type=RecommendationType.MODEL_OPTIMIZATION,
                    priority=Priority.MEDIUM,
                    complexity=ImplementationComplexity.MEDIUM,
                    estimated_impact=40,
                    confidence_score=0.7,
                    supporting_data={
                        'model_usage': metrics.most_used_models,
                        'total_responses': metrics.total_responses
                    },
                    implementation_steps=[
                        "Analyze model performance by task type",
                        "Implement intelligent model routing",
                        "A/B test different model selection strategies",
                        "Optimize model loading and caching"
                    ],
                    success_metrics=['model_efficiency', 'response_time', 'user_satisfaction'],
                    estimated_effort_hours=12,
                    prerequisites=["Model performance tracking"],
                    risks=["May affect response consistency"],
                    created_at=datetime.now()
                ))
        
        return recommendations
    
    def _analyze_cache_effectiveness(self, metrics) -> List[OptimizationRecommendation]:
        """Analyze cache effectiveness"""
        recommendations = []
        
        if metrics.cache_hit_rate < 50:  # Less than 50% cache hit rate
            recommendations.append(OptimizationRecommendation(
                id=self._generate_recommendation_id(),
                title="Improve Cache Hit Rate",
                description=f"Cache hit rate is {metrics.cache_hit_rate:.1f}%, indicating poor cache effectiveness",
                recommendation_type=RecommendationType.CACHE_OPTIMIZATION,
                priority=Priority.MEDIUM,
                complexity=ImplementationComplexity.LOW,
                estimated_impact=35,
                confidence_score=0.8,
                supporting_data={
                    'current_cache_hit_rate': metrics.cache_hit_rate,
                    'target_hit_rate': 70.0
                },
                implementation_steps=[
                    "Analyze cache miss patterns",
                    "Implement smarter cache key generation",
                    "Increase cache size if memory allows",
                    "Implement cache warming strategies"
                ],
                success_metrics=['cache_hit_rate', 'response_time'],
                estimated_effort_hours=8,
                prerequisites=["Cache monitoring in place"],
                risks=["Increased memory usage"],
                created_at=datetime.now()
            ))
        
        return recommendations
    
    def _analyze_optimization_effectiveness(self, metrics) -> List[OptimizationRecommendation]:
        """Analyze effectiveness of current optimizations"""
        recommendations = []
        
        if hasattr(metrics, 'optimization_effectiveness'):
            ineffective_optimizations = [
                opt for opt, effectiveness in metrics.optimization_effectiveness.items()
                if effectiveness < 10  # Less than 10% improvement
            ]
            
            if ineffective_optimizations:
                recommendations.append(OptimizationRecommendation(
                    id=self._generate_recommendation_id(),
                    title="Review Ineffective Optimizations",
                    description=f"Some optimizations show low effectiveness: {', '.join(ineffective_optimizations)}",
                    recommendation_type=RecommendationType.SYSTEM_CONFIGURATION,
                    priority=Priority.LOW,
                    complexity=ImplementationComplexity.LOW,
                    estimated_impact=20,
                    confidence_score=0.6,
                    supporting_data={
                        'ineffective_optimizations': ineffective_optimizations,
                        'optimization_effectiveness': metrics.optimization_effectiveness
                    },
                    implementation_steps=[
                        "Analyze why optimizations are ineffective",
                        "Consider disabling or reconfiguring ineffective optimizations",
                        "A/B test alternative optimization strategies"
                    ],
                    success_metrics=['optimization_effectiveness', 'system_performance'],
                    estimated_effort_hours=6,
                    prerequisites=["Optimization tracking"],
                    risks=["May temporarily reduce performance during changes"],
                    created_at=datetime.now()
                ))
        
        return recommendations
    
    def _calculate_performance_score(self, metrics) -> float:
        """Calculate performance score (0-100)"""
        score = 100.0
        
        # Response time penalty
        if metrics.avg_response_time > self.performance_thresholds['response_time']:
            penalty = min(50, (metrics.avg_response_time - self.performance_thresholds['response_time']) * 10)
            score -= penalty
        
        # Error rate penalty
        if metrics.error_rate > self.performance_thresholds['error_rate']:
            penalty = min(30, metrics.error_rate * 2)
            score -= penalty
        
        # CPU usage penalty
        if metrics.avg_cpu_usage > self.performance_thresholds['cpu_usage']:
            penalty = min(20, (metrics.avg_cpu_usage - self.performance_thresholds['cpu_usage']) * 2)
            score -= penalty
        
        return max(0, score)
    
    def _calculate_satisfaction_score(self, metrics: SatisfactionMetrics) -> float:
        """Calculate satisfaction score (0-100)"""
        if metrics.total_feedback_count == 0:
            return 50.0  # Neutral score with no data
        
        # Convert 1-5 rating to 0-100 score
        base_score = (metrics.avg_rating - 1) / 4 * 100
        
        # Adjust based on thumbs up percentage
        if metrics.thumbs_up_percentage > 0:
            thumbs_adjustment = (metrics.thumbs_up_percentage - 50) / 2  # -25 to +25
            base_score += thumbs_adjustment
        
        return max(0, min(100, base_score))
    
    def _calculate_resource_efficiency_score(self, metrics) -> float:
        """Calculate resource efficiency score (0-100)"""
        score = 100.0
        
        # Cache efficiency
        if metrics.cache_hit_rate < 70:
            score -= (70 - metrics.cache_hit_rate) * 0.5
        
        # Throughput efficiency (responses per minute)
        if metrics.throughput < 10:  # Less than 10 responses per minute
            score -= (10 - metrics.throughput) * 2
        
        return max(0, score)
    
    def _analyze_metric_trends(self) -> Dict[str, str]:
        """Analyze trends in key metrics"""
        # This would analyze historical data to determine trends
        # For now, return placeholder data
        return {
            'response_time': 'STABLE',
            'satisfaction': 'IMPROVING',
            'error_rate': 'DECLINING',
            'cache_hit_rate': 'STABLE'
        }
    
    def _analyze_bottlenecks(self, metrics) -> Dict[str, float]:
        """Analyze system bottlenecks"""
        bottlenecks = {}
        
        if metrics.avg_response_time > self.performance_thresholds['response_time']:
            bottlenecks['response_generation'] = metrics.avg_response_time
        
        if metrics.cache_hit_rate < 50:
            bottlenecks['cache_efficiency'] = 100 - metrics.cache_hit_rate
        
        if metrics.error_rate > self.performance_thresholds['error_rate']:
            bottlenecks['error_handling'] = metrics.error_rate
        
        return bottlenecks
    
    def _priority_score(self, priority: Priority) -> int:
        """Convert priority to numeric score for sorting"""
        return {
            Priority.CRITICAL: 4,
            Priority.HIGH: 3,
            Priority.MEDIUM: 2,
            Priority.LOW: 1
        }[priority]
    
    def _determine_implementation_order(self, recommendations: List[OptimizationRecommendation]) -> List[str]:
        """Determine optimal implementation order for recommendations"""
        # Sort by priority, then by dependencies, then by impact
        sorted_recs = sorted(recommendations, key=lambda r: (
            self._priority_score(r.priority),
            len(r.prerequisites),
            r.estimated_impact
        ), reverse=True)
        
        return [r.id for r in sorted_recs]
    
    def _generate_recommendation_id(self) -> str:
        """Generate unique recommendation ID"""
        import uuid
        return f"rec_{uuid.uuid4().hex[:12]}"
    
    def _generate_suite_id(self) -> str:
        """Generate unique suite ID"""
        import uuid
        return f"suite_{uuid.uuid4().hex[:12]}"
    
    def _start_background_analysis(self) -> None:
        """Start background recommendation generation"""
        def analyze():
            import time
            while True:
                try:
                    # Generate recommendations every hour
                    recommendations = self.generate_recommendations()
                    if recommendations:
                        logger.info(f"Background analysis generated {len(recommendations)} recommendations")
                    
                    time.sleep(3600)  # 1 hour
                except Exception as e:
                    logger.error(f"Error in background recommendation analysis: {e}")
                    time.sleep(1800)  # Wait 30 minutes on error
        
        analysis_thread = threading.Thread(target=analyze, daemon=True)
        analysis_thread.start()


# Global optimization recommendation engine instance
recommendation_engine = OptimizationRecommendationEngine()