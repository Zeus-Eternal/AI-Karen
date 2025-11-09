"""
Metacognition: Human-Like Self-Monitoring and Self-Reflection

Implements metacognitive capabilities for human-like reasoning:
- Self-monitoring: Awareness of own cognitive processes
- Self-reflection: Evaluating own performance and strategies
- Cognitive regulation: Adjusting strategies based on performance
- Uncertainty awareness: Recognizing knowledge gaps
- Planning and strategy selection

Based on human metacognitive research and cognitive psychology.
"""

from __future__ import annotations

import logging
import time
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CognitiveState(Enum):
    """Current cognitive state of the system"""
    CONFIDENT = "confident"           # High certainty in reasoning
    UNCERTAIN = "uncertain"           # Low certainty, need more info
    CONFUSED = "confused"             # Contradictory or unclear
    EXPLORING = "exploring"           # Actively seeking information
    CONSOLIDATING = "consolidating"   # Integrating information
    STUCK = "stuck"                   # Unable to progress


class ReasoningStrategy(Enum):
    """Available reasoning strategies"""
    ANALYTICAL = "analytical"         # Step-by-step logical analysis
    INTUITIVE = "intuitive"           # Pattern-based quick reasoning
    EXPLORATORY = "exploratory"       # Broad search for information
    FOCUSED = "focused"               # Deep dive on specific aspect
    COMPARATIVE = "comparative"       # Compare alternatives
    CAUSAL = "causal"                 # Causal chain reasoning


@dataclass
class MetacognitiveState:
    """Current metacognitive state"""
    cognitive_state: CognitiveState
    confidence: float                 # 0-1: confidence in current reasoning
    certainty: float                  # 0-1: certainty about answer
    knowledge_gaps: List[str]         # Identified gaps in knowledge
    active_strategy: ReasoningStrategy
    performance_estimate: float       # 0-1: estimated quality of output
    timestamp: float = field(default_factory=time.time)


@dataclass
class PerformanceMetrics:
    """Track performance across tasks"""
    total_tasks: int = 0
    successful_tasks: int = 0
    avg_confidence: float = 0.0
    avg_quality: float = 0.0
    strategy_success: Dict[ReasoningStrategy, Tuple[int, int]] = field(
        default_factory=dict
    )  # strategy -> (successes, attempts)


@dataclass
class MetacognitiveConfig:
    """Configuration for metacognitive monitoring"""
    enable_uncertainty_detection: bool = True
    enable_strategy_switching: bool = True
    enable_self_correction: bool = True
    confidence_threshold_low: float = 0.4
    confidence_threshold_high: float = 0.7
    performance_window: int = 10      # Track last N tasks
    enable_adaptive_thresholds: bool = True


class MetacognitiveMonitor:
    """
    Metacognitive monitoring system for human-like self-awareness.

    Provides capabilities for:
    - Monitoring own reasoning process
    - Detecting uncertainty and knowledge gaps
    - Selecting appropriate reasoning strategies
    - Self-correcting when detecting errors
    - Adapting based on performance feedback
    """

    def __init__(self, config: Optional[MetacognitiveConfig] = None):
        self.config = config or MetacognitiveConfig()
        self.current_state = MetacognitiveState(
            cognitive_state=CognitiveState.CONFIDENT,
            confidence=0.5,
            certainty=0.5,
            knowledge_gaps=[],
            active_strategy=ReasoningStrategy.ANALYTICAL,
            performance_estimate=0.5,
        )
        self.performance = PerformanceMetrics()
        self._state_history: List[MetacognitiveState] = []

    def monitor_reasoning_process(
        self,
        query: str,
        current_output: str,
        context: Optional[List[str]] = None,
        intermediate_steps: Optional[List[str]] = None,
    ) -> MetacognitiveState:
        """
        Monitor the reasoning process and assess cognitive state.

        Args:
            query: Current query being processed
            current_output: Current output/reasoning
            context: Available context
            intermediate_steps: Intermediate reasoning steps

        Returns:
            Current metacognitive state
        """
        # Assess confidence
        confidence = self._assess_confidence(
            query, current_output, context, intermediate_steps
        )

        # Assess certainty
        certainty = self._assess_certainty(current_output)

        # Identify knowledge gaps
        knowledge_gaps = self._identify_knowledge_gaps(
            query, current_output, context
        )

        # Determine cognitive state
        cognitive_state = self._determine_cognitive_state(
            confidence, certainty, knowledge_gaps
        )

        # Estimate performance
        performance_estimate = self._estimate_performance(
            current_output, confidence, certainty
        )

        # Update state
        self.current_state = MetacognitiveState(
            cognitive_state=cognitive_state,
            confidence=confidence,
            certainty=certainty,
            knowledge_gaps=knowledge_gaps,
            active_strategy=self.current_state.active_strategy,
            performance_estimate=performance_estimate,
        )

        self._state_history.append(self.current_state)

        logger.debug(
            f"Metacognitive state: {cognitive_state.value}, "
            f"confidence={confidence:.2f}, certainty={certainty:.2f}"
        )

        return self.current_state

    def select_strategy(
        self,
        query: str,
        task_type: Optional[str] = None,
        current_state: Optional[MetacognitiveState] = None,
    ) -> ReasoningStrategy:
        """
        Select appropriate reasoning strategy based on task and state.

        Args:
            query: Query to process
            task_type: Type of task (optional)
            current_state: Current metacognitive state

        Returns:
            Recommended reasoning strategy
        """
        state = current_state or self.current_state

        # If current strategy is working well, keep it
        if state.confidence >= self.config.confidence_threshold_high:
            return state.active_strategy

        # If stuck or confused, try switching strategy
        if state.cognitive_state in [CognitiveState.STUCK, CognitiveState.CONFUSED]:
            return self._switch_strategy(state.active_strategy)

        # Select based on task characteristics
        strategy = self._select_by_task_characteristics(query, task_type)

        # Consider performance history
        if self.config.enable_strategy_switching:
            strategy = self._adjust_by_performance(strategy)

        return strategy

    def should_seek_more_information(self) -> Tuple[bool, List[str]]:
        """
        Determine if more information should be sought.

        Returns:
            (should_seek, what_to_seek)
        """
        state = self.current_state

        should_seek = (
            state.cognitive_state in [CognitiveState.UNCERTAIN, CognitiveState.STUCK]
            or state.confidence < self.config.confidence_threshold_low
            or len(state.knowledge_gaps) > 0
        )

        what_to_seek = state.knowledge_gaps if state.knowledge_gaps else [
            "additional context",
            "clarifying information"
        ]

        return should_seek, what_to_seek

    def should_self_correct(
        self,
        output: str,
        quality_score: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Determine if self-correction is needed.

        Args:
            output: Current output
            quality_score: Optional quality score

        Returns:
            (should_correct, reason)
        """
        if not self.config.enable_self_correction:
            return False, ""

        state = self.current_state

        # Low confidence suggests potential errors
        if state.confidence < self.config.confidence_threshold_low:
            return True, "Low confidence in output"

        # Quality below threshold
        if quality_score is not None and quality_score < 0.6:
            return True, f"Quality score {quality_score:.2f} below threshold"

        # Confused state suggests errors
        if state.cognitive_state == CognitiveState.CONFUSED:
            return True, "Confused cognitive state detected"

        # Detect linguistic uncertainty markers
        if self._detect_uncertainty_markers(output):
            return True, "Uncertainty markers detected in output"

        return False, ""

    def update_performance(
        self,
        task_success: bool,
        actual_quality: float,
        strategy_used: ReasoningStrategy,
    ) -> None:
        """
        Update performance metrics with task outcome.

        Args:
            task_success: Whether task was successful
            actual_quality: Actual quality score achieved
            strategy_used: Strategy that was used
        """
        self.performance.total_tasks += 1

        if task_success:
            self.performance.successful_tasks += 1

        # Update averages (exponential moving average)
        alpha = 0.2
        self.performance.avg_confidence = (
            alpha * self.current_state.confidence +
            (1 - alpha) * self.performance.avg_confidence
        )
        self.performance.avg_quality = (
            alpha * actual_quality +
            (1 - alpha) * self.performance.avg_quality
        )

        # Update strategy performance
        if strategy_used not in self.performance.strategy_success:
            self.performance.strategy_success[strategy_used] = (0, 0)

        successes, attempts = self.performance.strategy_success[strategy_used]
        new_successes = successes + (1 if task_success else 0)
        new_attempts = attempts + 1
        self.performance.strategy_success[strategy_used] = (new_successes, new_attempts)

        # Adapt thresholds if enabled
        if self.config.enable_adaptive_thresholds:
            self._adapt_thresholds()

    def get_reflection(self) -> Dict[str, Any]:
        """
        Generate self-reflection on recent performance.

        Returns:
            Dictionary with reflection insights
        """
        perf = self.performance

        success_rate = (
            perf.successful_tasks / perf.total_tasks
            if perf.total_tasks > 0 else 0.0
        )

        # Identify best and worst strategies
        strategy_performance = {}
        best_strategy = None
        best_rate = 0.0

        for strategy, (successes, attempts) in perf.strategy_success.items():
            rate = successes / attempts if attempts > 0 else 0.0
            strategy_performance[strategy.value] = {
                "success_rate": rate,
                "attempts": attempts,
            }
            if rate > best_rate:
                best_rate = rate
                best_strategy = strategy

        # Identify patterns
        patterns = []
        if success_rate < 0.6:
            patterns.append("Overall success rate is low, may need different approach")
        if perf.avg_confidence < 0.5:
            patterns.append("Frequently low confidence, may need more information sources")
        if best_strategy:
            patterns.append(f"Strategy '{best_strategy.value}' performs best")

        return {
            "success_rate": success_rate,
            "avg_confidence": perf.avg_confidence,
            "avg_quality": perf.avg_quality,
            "total_tasks": perf.total_tasks,
            "strategy_performance": strategy_performance,
            "best_strategy": best_strategy.value if best_strategy else None,
            "patterns": patterns,
            "current_state": self.current_state.cognitive_state.value,
        }

    # Internal methods

    def _assess_confidence(
        self,
        query: str,
        output: str,
        context: Optional[List[str]],
        intermediate_steps: Optional[List[str]],
    ) -> float:
        """Assess confidence in current reasoning"""
        confidence = 0.5  # Base confidence

        # More context → higher confidence
        if context and len(context) > 0:
            confidence += min(0.2, len(context) * 0.05)

        # Structured reasoning → higher confidence
        if intermediate_steps and len(intermediate_steps) > 2:
            confidence += 0.1

        # Output characteristics
        if output:
            # Sufficient length
            words = len(output.split())
            if 30 <= words <= 200:
                confidence += 0.1

            # Lacks hedging
            hedge_words = ['maybe', 'perhaps', 'possibly', 'might', 'could be']
            hedges_found = sum(1 for hw in hedge_words if hw in output.lower())
            confidence -= hedges_found * 0.05

            # Has specific details
            if any(char.isdigit() for char in output):
                confidence += 0.05

        return max(0.0, min(1.0, confidence))

    def _assess_certainty(self, output: str) -> float:
        """Assess certainty about the answer"""
        certainty = 0.5

        # Certainty indicators
        certain_markers = [
            'definitely', 'certainly', 'clearly', 'obviously',
            'undoubtedly', 'without doubt'
        ]
        uncertain_markers = [
            'uncertain', 'unclear', 'ambiguous', 'possibly',
            'might', 'could', 'may', 'perhaps'
        ]

        output_lower = output.lower()

        # Count markers
        certain_count = sum(1 for m in certain_markers if m in output_lower)
        uncertain_count = sum(1 for m in uncertain_markers if m in output_lower)

        certainty += certain_count * 0.1
        certainty -= uncertain_count * 0.15

        return max(0.0, min(1.0, certainty))

    def _identify_knowledge_gaps(
        self,
        query: str,
        output: str,
        context: Optional[List[str]]
    ) -> List[str]:
        """Identify gaps in knowledge"""
        gaps = []

        output_lower = output.lower()

        # Explicit gap indicators
        gap_indicators = [
            ("don't know", "unknown information"),
            ("not sure", "uncertain information"),
            ("unclear", "clarification needed"),
            ("more information", "additional context"),
            ("can't determine", "insufficient data"),
        ]

        for indicator, gap_type in gap_indicators:
            if indicator in output_lower:
                gaps.append(gap_type)

        # Question words in output suggest gaps
        question_words = ['what', 'why', 'how', 'when', 'where', 'who']
        if any(f"{qw} " in output_lower for qw in question_words):
            if "?" in output:
                gaps.append("unanswered questions")

        return list(set(gaps))  # Remove duplicates

    def _determine_cognitive_state(
        self,
        confidence: float,
        certainty: float,
        knowledge_gaps: List[str]
    ) -> CognitiveState:
        """Determine current cognitive state"""
        # Stuck: very low confidence and certainty
        if confidence < 0.3 and certainty < 0.3:
            return CognitiveState.STUCK

        # Confused: significant knowledge gaps
        if len(knowledge_gaps) >= 3:
            return CognitiveState.CONFUSED

        # Uncertain: low certainty but reasonable confidence
        if certainty < 0.4:
            return CognitiveState.UNCERTAIN

        # Exploring: moderate confidence, some gaps
        if confidence < 0.6 and len(knowledge_gaps) > 0:
            return CognitiveState.EXPLORING

        # Consolidating: good confidence, improving certainty
        if 0.6 <= confidence < 0.8:
            return CognitiveState.CONSOLIDATING

        # Confident: high confidence and certainty
        return CognitiveState.CONFIDENT

    def _estimate_performance(
        self,
        output: str,
        confidence: float,
        certainty: float
    ) -> float:
        """Estimate performance quality"""
        # Combine confidence and certainty
        base = (confidence + certainty) / 2

        # Adjust based on output characteristics
        if output:
            words = len(output.split())
            if words < 10:
                base *= 0.7  # Too short
            elif words > 500:
                base *= 0.9  # Might be too verbose

        return base

    def _select_by_task_characteristics(
        self,
        query: str,
        task_type: Optional[str]
    ) -> ReasoningStrategy:
        """Select strategy based on task"""
        query_lower = query.lower()

        # Causal questions
        if any(w in query_lower for w in ['why', 'because', 'cause', 'reason']):
            return ReasoningStrategy.CAUSAL

        # Comparative questions
        if any(w in query_lower for w in ['compare', 'difference', 'versus', 'vs']):
            return ReasoningStrategy.COMPARATIVE

        # Exploratory questions
        if any(w in query_lower for w in ['what', 'explain', 'describe']):
            return ReasoningStrategy.EXPLORATORY

        # Focused questions
        if any(w in query_lower for w in ['how', 'when', 'where', 'who']):
            return ReasoningStrategy.FOCUSED

        # Default to analytical
        return ReasoningStrategy.ANALYTICAL

    def _switch_strategy(
        self,
        current_strategy: ReasoningStrategy
    ) -> ReasoningStrategy:
        """Switch to a different strategy"""
        strategies = list(ReasoningStrategy)
        strategies.remove(current_strategy)

        # Try strategy with best historical performance
        best_strategy = current_strategy
        best_rate = 0.0

        for strategy in strategies:
            if strategy in self.performance.strategy_success:
                successes, attempts = self.performance.strategy_success[strategy]
                rate = successes / attempts if attempts > 0 else 0.0
                if rate > best_rate:
                    best_rate = rate
                    best_strategy = strategy

        return best_strategy

    def _adjust_by_performance(
        self,
        strategy: ReasoningStrategy
    ) -> ReasoningStrategy:
        """Adjust strategy based on performance"""
        if strategy not in self.performance.strategy_success:
            return strategy

        successes, attempts = self.performance.strategy_success[strategy]
        success_rate = successes / attempts if attempts > 0 else 0.5

        # If strategy has poor track record, try alternatives
        if attempts >= 3 and success_rate < 0.4:
            return self._switch_strategy(strategy)

        return strategy

    def _detect_uncertainty_markers(self, output: str) -> bool:
        """Detect linguistic uncertainty markers"""
        uncertainty_markers = [
            'i think', 'probably', 'maybe', 'perhaps',
            'might', 'could', 'possibly', 'unclear',
            'not sure', 'uncertain'
        ]

        output_lower = output.lower()
        return any(marker in output_lower for marker in uncertainty_markers)

    def _adapt_thresholds(self) -> None:
        """Adapt confidence thresholds based on performance"""
        if self.performance.total_tasks < 5:
            return  # Not enough data

        # If performing well, can be more strict
        success_rate = (
            self.performance.successful_tasks / self.performance.total_tasks
        )

        if success_rate > 0.8:
            self.config.confidence_threshold_high = min(
                0.9, self.config.confidence_threshold_high + 0.05
            )
        elif success_rate < 0.5:
            # Performing poorly, be more cautious
            self.config.confidence_threshold_low = max(
                0.2, self.config.confidence_threshold_low - 0.05
            )
