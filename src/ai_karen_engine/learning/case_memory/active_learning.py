"""
Active Learning and Continuous Improvement Engine

This module provides intelligent learning optimization through:
- User feedback collection and processing
- Reinforcement learning from outcomes
- Exploration vs exploitation strategies
- A/B testing for retrieval strategies
- Continuous model improvement
- Adaptive admission policies
- Feedback loop monitoring
"""

from __future__ import annotations
import logging
import random
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback signals"""
    EXPLICIT_POSITIVE = "explicit_positive"  # User explicitly liked
    EXPLICIT_NEGATIVE = "explicit_negative"  # User explicitly disliked
    IMPLICIT_USAGE = "implicit_usage"  # User used the suggestion
    IMPLICIT_IGNORE = "implicit_ignore"  # User ignored the suggestion
    OUTCOME_SUCCESS = "outcome_success"  # Task succeeded
    OUTCOME_FAILURE = "outcome_failure"  # Task failed
    QUALITY_RATING = "quality_rating"  # Numeric quality rating


@dataclass
class FeedbackSignal:
    """Individual feedback signal"""
    feedback_id: str
    case_id: str
    user_id: Optional[str]
    tenant_id: str
    feedback_type: FeedbackType
    value: float  # Normalized 0-1 score
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False


@dataclass
class RetrievalStrategy:
    """Configuration for retrieval strategy"""
    strategy_id: str
    name: str
    k_fast: int
    k_final: int
    distance_cutoff: float
    reranker_weight: float
    novelty_bonus: float
    recency_decay: float


@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy"""
    strategy_id: str
    usage_count: int = 0
    success_count: int = 0
    avg_satisfaction: float = 0.0
    avg_task_success: float = 0.0
    avg_latency_ms: float = 0.0
    confidence_interval: Tuple[float, float] = (0.0, 1.0)


class ActiveLearningEngine:
    """
    Active learning engine for continuous improvement

    Features:
    - Multi-armed bandit for strategy selection
    - Feedback collection and processing
    - Reinforcement learning from outcomes
    - A/B testing framework
    - Adaptive policy optimization
    - Exploration-exploitation balance
    - Concept drift detection
    """

    def __init__(
        self,
        exploration_rate: float = 0.1,
        feedback_window: int = 1000,
        ab_test_duration_hours: int = 24
    ):
        self.exploration_rate = exploration_rate
        self.feedback_window = feedback_window
        self.ab_test_duration_hours = ab_test_duration_hours

        # Storage
        self.feedback_history: deque = deque(maxlen=feedback_window)
        self.strategies: Dict[str, RetrievalStrategy] = {}
        self.strategy_performance: Dict[str, StrategyPerformance] = {}
        self.case_feedback: Dict[str, List[FeedbackSignal]] = defaultdict(list)
        self.active_ab_tests: Dict[str, Dict[str, Any]] = {}

        # Learning state
        self.strategy_arms: Dict[str, float] = {}  # Multi-armed bandit values
        self.last_strategy_update = datetime.utcnow()
        self.feedback_processors: List[Callable] = []

        # Initialize default strategies
        self._initialize_default_strategies()

    def _initialize_default_strategies(self) -> None:
        """Initialize default retrieval strategies"""
        strategies = [
            RetrievalStrategy(
                strategy_id="balanced",
                name="Balanced",
                k_fast=24,
                k_final=6,
                distance_cutoff=0.45,
                reranker_weight=0.7,
                novelty_bonus=0.1,
                recency_decay=0.05
            ),
            RetrievalStrategy(
                strategy_id="precise",
                name="Precise",
                k_fast=16,
                k_final=4,
                distance_cutoff=0.35,
                reranker_weight=0.9,
                novelty_bonus=0.0,
                recency_decay=0.02
            ),
            RetrievalStrategy(
                strategy_id="exploratory",
                name="Exploratory",
                k_fast=32,
                k_final=8,
                distance_cutoff=0.55,
                reranker_weight=0.5,
                novelty_bonus=0.3,
                recency_decay=0.1
            ),
            RetrievalStrategy(
                strategy_id="conservative",
                name="Conservative",
                k_fast=12,
                k_final=3,
                distance_cutoff=0.25,
                reranker_weight=1.0,
                novelty_bonus=0.0,
                recency_decay=0.01
            )
        ]

        for strategy in strategies:
            self.strategies[strategy.strategy_id] = strategy
            self.strategy_performance[strategy.strategy_id] = StrategyPerformance(
                strategy_id=strategy.strategy_id
            )
            self.strategy_arms[strategy.strategy_id] = 0.5  # Initial value

    def select_strategy(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> RetrievalStrategy:
        """
        Select retrieval strategy using multi-armed bandit

        Balances exploration (trying new strategies) vs exploitation
        (using best known strategy)
        """
        # Check if in A/B test
        if context and context.get('user_id'):
            active_test = self._get_active_ab_test(context['user_id'])
            if active_test:
                return self.strategies[active_test['strategy_id']]

        # Exploration: randomly select a strategy
        if random.random() < self.exploration_rate:
            strategy_id = random.choice(list(self.strategies.keys()))
            logger.info(f"Exploring strategy: {strategy_id}")
            return self.strategies[strategy_id]

        # Exploitation: select best performing strategy
        best_strategy_id = max(
            self.strategy_arms.items(),
            key=lambda x: x[1]
        )[0]

        logger.info(f"Exploiting strategy: {best_strategy_id}")
        return self.strategies[best_strategy_id]

    def record_feedback(
        self,
        case_id: str,
        user_id: Optional[str],
        tenant_id: str,
        feedback_type: FeedbackType,
        value: float,
        context: Optional[Dict[str, Any]] = None
    ) -> FeedbackSignal:
        """Record user feedback signal"""
        feedback = FeedbackSignal(
            feedback_id=f"fb_{datetime.utcnow().timestamp()}",
            case_id=case_id,
            user_id=user_id,
            tenant_id=tenant_id,
            feedback_type=feedback_type,
            value=value,
            context=context or {}
        )

        # Store feedback
        self.feedback_history.append(feedback)
        self.case_feedback[case_id].append(feedback)

        # Process feedback immediately
        self._process_feedback(feedback)

        logger.info(
            f"Recorded feedback for case {case_id}: {feedback_type.value} = {value:.2f}"
        )

        return feedback

    def _process_feedback(self, feedback: FeedbackSignal) -> None:
        """Process feedback signal and update learning"""
        if feedback.processed:
            return

        # Update strategy performance if strategy info available
        strategy_id = feedback.context.get('strategy_id')
        if strategy_id and strategy_id in self.strategy_performance:
            perf = self.strategy_performance[strategy_id]
            perf.usage_count += 1

            # Update success metrics
            if feedback.feedback_type in [
                FeedbackType.EXPLICIT_POSITIVE,
                FeedbackType.IMPLICIT_USAGE,
                FeedbackType.OUTCOME_SUCCESS
            ]:
                perf.success_count += 1

            # Update satisfaction
            old_avg = perf.avg_satisfaction
            n = perf.usage_count
            perf.avg_satisfaction = ((old_avg * (n - 1)) + feedback.value) / n

            # Update multi-armed bandit values
            self._update_bandit_arms(strategy_id, feedback.value)

        # Run custom feedback processors
        for processor in self.feedback_processors:
            try:
                processor(feedback)
            except Exception as e:
                logger.error(f"Feedback processor failed: {e}")

        feedback.processed = True

    def _update_bandit_arms(self, strategy_id: str, reward: float) -> None:
        """Update multi-armed bandit arm values using UCB1"""
        if strategy_id not in self.strategy_arms:
            return

        perf = self.strategy_performance[strategy_id]

        # Update average reward
        current_avg = self.strategy_arms[strategy_id]
        n = perf.usage_count

        # Exponentially weighted moving average
        alpha = 0.1  # Learning rate
        new_avg = (1 - alpha) * current_avg + alpha * reward

        # Add exploration bonus (UCB1)
        total_pulls = sum(p.usage_count for p in self.strategy_performance.values())
        if total_pulls > 0 and n > 0:
            exploration_bonus = np.sqrt(2 * np.log(total_pulls) / n)
            new_avg += exploration_bonus * 0.1

        self.strategy_arms[strategy_id] = new_avg

    def start_ab_test(
        self,
        test_name: str,
        strategy_a: str,
        strategy_b: str,
        user_split: float = 0.5,
        duration_hours: Optional[int] = None
    ) -> str:
        """
        Start A/B test comparing two strategies

        Args:
            test_name: Name of the test
            strategy_a: ID of strategy A
            strategy_b: ID of strategy B
            user_split: Fraction of users for strategy A (rest get B)
            duration_hours: Test duration in hours

        Returns:
            Test ID
        """
        if strategy_a not in self.strategies or strategy_b not in self.strategies:
            raise ValueError("Invalid strategy IDs")

        test_id = f"test_{datetime.utcnow().timestamp()}"
        duration = duration_hours or self.ab_test_duration_hours

        self.active_ab_tests[test_id] = {
            'name': test_name,
            'strategy_a': strategy_a,
            'strategy_b': strategy_b,
            'user_split': user_split,
            'start_time': datetime.utcnow(),
            'end_time': datetime.utcnow() + timedelta(hours=duration),
            'results_a': {'count': 0, 'success': 0, 'satisfaction': []},
            'results_b': {'count': 0, 'success': 0, 'satisfaction': []},
            'user_assignments': {}  # user_id -> strategy_id
        }

        logger.info(f"Started A/B test '{test_name}': {strategy_a} vs {strategy_b}")
        return test_id

    def _get_active_ab_test(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get active A/B test assignment for user"""
        for test_id, test in self.active_ab_tests.items():
            # Check if test is still active
            if datetime.utcnow() > test['end_time']:
                continue

            # Check if user already assigned
            if user_id in test['user_assignments']:
                strategy_id = test['user_assignments'][user_id]
                return {'strategy_id': strategy_id, 'test_id': test_id}

            # Assign user to a strategy
            if random.random() < test['user_split']:
                strategy_id = test['strategy_a']
            else:
                strategy_id = test['strategy_b']

            test['user_assignments'][user_id] = strategy_id
            return {'strategy_id': strategy_id, 'test_id': test_id}

        return None

    def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get results of an A/B test"""
        if test_id not in self.active_ab_tests:
            raise ValueError(f"Test {test_id} not found")

        test = self.active_ab_tests[test_id]
        results_a = test['results_a']
        results_b = test['results_b']

        # Calculate metrics
        metrics_a = self._calculate_test_metrics(results_a)
        metrics_b = self._calculate_test_metrics(results_b)

        # Statistical significance
        significance = self._calculate_significance(
            results_a['satisfaction'],
            results_b['satisfaction']
        )

        return {
            'test_name': test['name'],
            'strategy_a': test['strategy_a'],
            'strategy_b': test['strategy_b'],
            'duration_hours': (test['end_time'] - test['start_time']).total_seconds() / 3600,
            'is_complete': datetime.utcnow() > test['end_time'],
            'metrics_a': metrics_a,
            'metrics_b': metrics_b,
            'winner': metrics_a['avg_satisfaction'] > metrics_b['avg_satisfaction'] and 'a' or 'b',
            'improvement': abs(metrics_a['avg_satisfaction'] - metrics_b['avg_satisfaction']),
            'statistical_significance': significance,
            'confidence_level': significance['confidence']
        }

    def _calculate_test_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics for A/B test results"""
        count = results['count']
        if count == 0:
            return {
                'sample_size': 0,
                'success_rate': 0.0,
                'avg_satisfaction': 0.0,
                'std_deviation': 0.0
            }

        satisfaction_scores = results['satisfaction']
        return {
            'sample_size': count,
            'success_rate': results['success'] / count,
            'avg_satisfaction': np.mean(satisfaction_scores) if satisfaction_scores else 0.0,
            'std_deviation': np.std(satisfaction_scores) if satisfaction_scores else 0.0
        }

    def _calculate_significance(
        self,
        sample_a: List[float],
        sample_b: List[float]
    ) -> Dict[str, Any]:
        """Calculate statistical significance using t-test"""
        if len(sample_a) < 2 or len(sample_b) < 2:
            return {'significant': False, 'confidence': 0.0, 'p_value': 1.0}

        from scipy import stats

        # Perform independent t-test
        t_stat, p_value = stats.ttest_ind(sample_a, sample_b)

        # Confidence levels
        confidence = 1.0 - p_value

        return {
            'significant': p_value < 0.05,  # 95% confidence
            'confidence': confidence,
            'p_value': p_value,
            't_statistic': t_stat
        }

    def optimize_admission_policy(
        self,
        recent_cases: List[Any],
        current_policy: Any
    ) -> Dict[str, float]:
        """
        Optimize admission policy parameters based on feedback

        Suggests new policy parameters that maximize case quality
        """
        # Analyze recent case quality vs admission threshold
        quality_by_threshold = defaultdict(list)

        for case in recent_cases:
            # Group by admission threshold bucket
            reward = case.reward.score
            threshold_bucket = int(reward * 10) / 10  # 0.1 increments
            quality_by_threshold[threshold_bucket].append(reward)

        # Find optimal threshold
        best_threshold = current_policy.min_reward
        best_avg_quality = 0.0

        for threshold, rewards in quality_by_threshold.items():
            if len(rewards) >= 5:  # Minimum sample size
                avg_quality = np.mean(rewards)
                if avg_quality > best_avg_quality:
                    best_avg_quality = avg_quality
                    best_threshold = threshold

        # Analyze novelty threshold
        novelty_scores = []
        quality_scores = []
        for case in recent_cases:
            # Would need actual novelty calculation
            # For now, use placeholder
            novelty_scores.append(0.5)
            quality_scores.append(case.reward.score)

        # Calculate correlation
        if len(novelty_scores) > 5:
            correlation = np.corrcoef(novelty_scores, quality_scores)[0, 1]
            novelty_adjustment = correlation * 0.1  # Adjust based on correlation
        else:
            novelty_adjustment = 0.0

        # Suggest new parameters
        new_params = {
            'min_reward': max(0.4, min(0.8, best_threshold)),
            'novelty_threshold': max(
                0.05,
                min(0.3, current_policy.novelty_threshold + novelty_adjustment)
            ),
            'decay_lambda': current_policy.decay_lambda,  # Keep stable for now
            'confidence': best_avg_quality
        }

        logger.info(f"Optimized admission policy: {new_params}")
        return new_params

    def detect_concept_drift(
        self,
        window_size: int = 100
    ) -> Dict[str, Any]:
        """
        Detect concept drift in feedback patterns

        Returns drift indicators and recommended actions
        """
        if len(self.feedback_history) < window_size * 2:
            return {'drift_detected': False, 'confidence': 0.0}

        # Split into recent and historical windows
        recent = list(self.feedback_history)[-window_size:]
        historical = list(self.feedback_history)[-2*window_size:-window_size]

        # Calculate satisfaction distributions
        recent_satisfaction = [f.value for f in recent]
        historical_satisfaction = [f.value for f in historical]

        # Statistical test for distribution change
        from scipy import stats
        ks_stat, p_value = stats.ks_2samp(recent_satisfaction, historical_satisfaction)

        drift_detected = p_value < 0.05
        confidence = 1.0 - p_value

        # Calculate drift metrics
        recent_mean = np.mean(recent_satisfaction)
        historical_mean = np.mean(historical_satisfaction)
        drift_magnitude = recent_mean - historical_mean

        result = {
            'drift_detected': drift_detected,
            'confidence': confidence,
            'drift_magnitude': drift_magnitude,
            'drift_direction': 'improving' if drift_magnitude > 0 else 'declining',
            'recent_avg': recent_mean,
            'historical_avg': historical_mean,
            'recommended_action': self._recommend_drift_action(drift_detected, drift_magnitude)
        }

        if drift_detected:
            logger.warning(f"Concept drift detected: {result}")

        return result

    def _recommend_drift_action(self, drift_detected: bool, magnitude: float) -> str:
        """Recommend action based on drift detection"""
        if not drift_detected:
            return "continue_monitoring"

        if magnitude < -0.2:
            return "retrain_models"  # Significant performance drop
        elif magnitude < -0.1:
            return "adjust_strategies"  # Moderate drop
        elif magnitude > 0.2:
            return "exploit_improvement"  # Significant improvement
        else:
            return "continue_monitoring"

    def add_feedback_processor(self, processor: Callable[[FeedbackSignal], None]) -> None:
        """Add custom feedback processor"""
        self.feedback_processors.append(processor)

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive learning system summary"""
        return {
            'total_feedback': len(self.feedback_history),
            'strategy_performance': {
                sid: {
                    'usage_count': perf.usage_count,
                    'success_rate': perf.success_count / perf.usage_count if perf.usage_count > 0 else 0,
                    'avg_satisfaction': perf.avg_satisfaction,
                    'bandit_value': self.strategy_arms[sid]
                }
                for sid, perf in self.strategy_performance.items()
            },
            'best_strategy': max(self.strategy_arms.items(), key=lambda x: x[1])[0],
            'exploration_rate': self.exploration_rate,
            'active_ab_tests': len([t for t in self.active_ab_tests.values() if datetime.utcnow() <= t['end_time']]),
            'concept_drift': self.detect_concept_drift()
        }


# Global active learning instance
_global_active_learning: Optional[ActiveLearningEngine] = None

def get_active_learning_engine() -> ActiveLearningEngine:
    """Get global active learning engine instance"""
    global _global_active_learning
    if _global_active_learning is None:
        _global_active_learning = ActiveLearningEngine()
    return _global_active_learning
