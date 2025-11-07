"""
Cognitive Orchestrator: Human-Like Reasoning Flow

Orchestrates multiple cognitive capabilities to achieve human-like reasoning:
- Metacognitive monitoring and strategy selection
- Self-refinement with iterative feedback
- Soft reasoning with embedding optimization
- Causal reasoning and counterfactual thinking
- Adaptive learning from experience

Integrates all cognitive subsystems into a coherent reasoning pipeline.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger(__name__)


class CognitiveMode(Enum):
    """Overall cognitive processing mode"""
    FAST = "fast"                     # Quick, intuitive processing
    DELIBERATE = "deliberate"         # Slow, analytical processing
    ADAPTIVE = "adaptive"             # Switch between fast and deliberate
    REFLECTIVE = "reflective"         # Include self-reflection
    EXPLORATORY = "exploratory"       # Broad information gathering


@dataclass
class CognitiveTask:
    """Task to be processed"""
    query: str
    task_type: Optional[str] = None
    context: Optional[List[str]] = None
    constraints: Optional[Dict[str, Any]] = None
    priority: int = 5                 # 1-10, higher = more important
    requires_certainty: bool = False   # Require high certainty
    requires_explanation: bool = False # Require reasoning trace


@dataclass
class CognitiveResponse:
    """Response from cognitive processing"""
    output: str
    confidence: float
    certainty: float
    reasoning_trace: List[str]
    metacognitive_state: str
    strategy_used: str
    refinement_iterations: int
    quality_score: float
    knowledge_gaps: List[str]
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CognitiveConfig:
    """Configuration for cognitive orchestrator"""
    default_mode: CognitiveMode = CognitiveMode.ADAPTIVE
    enable_self_refine: bool = True
    enable_metacognition: bool = True
    enable_soft_reasoning: bool = True
    enable_causal_reasoning: bool = False
    max_refinement_iterations: int = 3
    quality_threshold: float = 0.75
    confidence_threshold: float = 0.7
    enable_learning: bool = True


class CognitiveOrchestrator:
    """
    Orchestrates human-like cognitive processing.

    Integrates:
    - MetacognitiveMonitor: Self-awareness and strategy selection
    - SelfRefiner: Iterative improvement
    - SoftReasoningEngine: Retrieval and embedding optimization
    - CausalReasoningEngine: Causal inference (optional)
    - ReasoningVerifier: Quality assessment

    Provides human-like cognitive flow:
    1. Understand task and select strategy
    2. Gather relevant information
    3. Generate initial reasoning
    4. Self-monitor and identify issues
    5. Refine iteratively
    6. Verify quality and certainty
    7. Learn from outcome
    """

    def __init__(
        self,
        *,
        config: Optional[CognitiveConfig] = None,
        llm: Optional[Any] = None,
        metacognitive_monitor: Optional[Any] = None,
        self_refiner: Optional[Any] = None,
        soft_reasoning: Optional[Any] = None,
        verifier: Optional[Any] = None,
        causal_engine: Optional[Any] = None,
    ):
        self.config = config or CognitiveConfig()
        self.llm = llm

        # Initialize subsystems
        self.metacognition = metacognitive_monitor
        self.refiner = self_refiner
        self.soft_reasoning = soft_reasoning
        self.verifier = verifier
        self.causal_engine = causal_engine

        # Auto-initialize if not provided
        self._auto_initialize()

        self._task_history: List[Tuple[CognitiveTask, CognitiveResponse]] = []

    def process(
        self,
        task: CognitiveTask,
        *,
        mode: Optional[CognitiveMode] = None,
    ) -> CognitiveResponse:
        """
        Process a cognitive task with human-like reasoning.

        Args:
            task: Task to process
            mode: Optional cognitive mode override

        Returns:
            CognitiveResponse with result and metadata
        """
        start_time = time.time()
        mode = mode or self.config.default_mode

        logger.info(f"Processing task in {mode.value} mode: {task.query[:50]}...")

        # Phase 1: Task understanding and strategy selection
        strategy = self._select_strategy(task, mode)
        logger.debug(f"Selected strategy: {strategy}")

        # Phase 2: Information gathering (if soft reasoning enabled)
        context = self._gather_information(task)

        # Phase 3: Initial generation
        reasoning_trace = [f"Strategy: {strategy}"]
        initial_output = self._generate_initial_response(
            task, context, strategy, reasoning_trace
        )

        # Phase 4: Metacognitive monitoring
        metacog_state = self._monitor_state(task, initial_output, context)
        logger.debug(f"Metacognitive state: {metacog_state.cognitive_state}")

        # Phase 5: Decide on processing depth
        should_refine, should_explore = self._decide_processing_depth(
            task, initial_output, metacog_state, mode
        )

        current_output = initial_output
        refinement_iterations = 0

        # Phase 6: Self-refinement (if needed)
        if should_refine and self.config.enable_self_refine and self.refiner:
            refine_result = self.refiner.refine(
                query=task.query,
                initial_output=initial_output,
                context=context,
                criteria=self._get_refinement_criteria(task),
            )
            current_output = refine_result.final_output
            refinement_iterations = refine_result.total_iterations
            reasoning_trace.append(
                f"Refined over {refinement_iterations} iterations "
                f"(Δ quality: {refine_result.improvement:+.2f})"
            )

        # Phase 7: Additional exploration (if needed)
        if should_explore:
            current_output = self._expand_reasoning(
                task, current_output, context, reasoning_trace
            )

        # Phase 8: Quality verification
        quality_score, verification_feedback = self._verify_quality(
            task, current_output, context
        )

        # Phase 9: Final metacognitive assessment
        final_metacog = self._monitor_state(task, current_output, context)
        confidence = final_metacog.confidence
        certainty = final_metacog.certainty

        # Phase 10: Learn from experience (if enabled)
        if self.config.enable_learning and self.metacognition:
            self._update_learning(task, current_output, quality_score, strategy)

        processing_time = time.time() - start_time

        response = CognitiveResponse(
            output=current_output,
            confidence=confidence,
            certainty=certainty,
            reasoning_trace=reasoning_trace,
            metacognitive_state=final_metacog.cognitive_state.value,
            strategy_used=strategy,
            refinement_iterations=refinement_iterations,
            quality_score=quality_score,
            knowledge_gaps=final_metacog.knowledge_gaps,
            processing_time=processing_time,
            metadata={
                "mode": mode.value,
                "initial_quality": quality_score - (
                    (refine_result.improvement if should_refine and self.refiner else 0)
                ),
                "verification_feedback": verification_feedback,
            }
        )

        # Store in history
        self._task_history.append((task, response))

        logger.info(
            f"Completed in {processing_time:.2f}s: "
            f"quality={quality_score:.2f}, confidence={confidence:.2f}"
        )

        return response

    def process_simple(
        self,
        query: str,
        *,
        context: Optional[List[str]] = None,
        requires_certainty: bool = False,
    ) -> str:
        """
        Simplified interface for processing a query.

        Args:
            query: Query string
            context: Optional context
            requires_certainty: If True, ensures high certainty

        Returns:
            Output string
        """
        task = CognitiveTask(
            query=query,
            context=context,
            requires_certainty=requires_certainty,
        )
        response = self.process(task)
        return response.output

    def reflect(self) -> Dict[str, Any]:
        """
        Generate reflection on recent cognitive processing.

        Returns:
            Reflection insights
        """
        if not self.metacognition:
            return {"message": "Metacognition not enabled"}

        reflection = self.metacognition.get_reflection()

        # Add task-specific insights
        if self._task_history:
            recent_tasks = self._task_history[-10:]
            avg_quality = sum(r.quality_score for _, r in recent_tasks) / len(recent_tasks)
            avg_confidence = sum(r.confidence for _, r in recent_tasks) / len(recent_tasks)

            reflection["recent_performance"] = {
                "avg_quality": avg_quality,
                "avg_confidence": avg_confidence,
                "num_tasks": len(recent_tasks),
            }

        return reflection

    # Internal methods

    def _auto_initialize(self) -> None:
        """Auto-initialize subsystems if not provided"""
        # LLM
        if self.llm is None:
            try:
                from ai_karen_engine.integrations.llm_utils import LLMUtils
                self.llm = LLMUtils()
            except ImportError:
                logger.warning("Could not initialize LLM")

        # Metacognition
        if self.metacognition is None and self.config.enable_metacognition:
            try:
                from ai_karen_engine.core.reasoning.synthesis.metacognition import (
                    MetacognitiveMonitor
                )
                self.metacognition = MetacognitiveMonitor()
            except ImportError:
                logger.warning("Could not initialize MetacognitiveMonitor")

        # Refiner
        if self.refiner is None and self.config.enable_self_refine:
            try:
                from ai_karen_engine.core.reasoning.synthesis.self_refine import (
                    create_self_refiner
                )
                self.refiner = create_self_refiner(llm=self.llm, verifier=self.verifier)
            except ImportError:
                logger.warning("Could not initialize SelfRefiner")

        # Soft Reasoning
        if self.soft_reasoning is None and self.config.enable_soft_reasoning:
            try:
                from ai_karen_engine.core.reasoning.soft_reasoning import (
                    SoftReasoningEngine
                )
                self.soft_reasoning = SoftReasoningEngine()
            except ImportError:
                logger.warning("Could not initialize SoftReasoningEngine")

        # Verifier
        if self.verifier is None:
            try:
                from ai_karen_engine.core.reasoning.soft_reasoning.verifier import (
                    ReasoningVerifier
                )
                self.verifier = ReasoningVerifier()
            except ImportError:
                logger.warning("Could not initialize ReasoningVerifier")

        # Causal Engine
        if self.causal_engine is None and self.config.enable_causal_reasoning:
            try:
                from ai_karen_engine.core.reasoning.causal import get_causal_engine
                self.causal_engine = get_causal_engine()
            except ImportError:
                logger.warning("Could not initialize CausalReasoningEngine")

    def _select_strategy(
        self,
        task: CognitiveTask,
        mode: CognitiveMode
    ) -> str:
        """Select reasoning strategy"""
        if self.metacognition:
            strategy = self.metacognition.select_strategy(
                query=task.query,
                task_type=task.task_type,
            )
            return strategy.value

        # Fallback heuristic
        return "analytical"

    def _gather_information(
        self,
        task: CognitiveTask
    ) -> Optional[List[str]]:
        """Gather relevant information"""
        # Use provided context
        context = task.context or []

        # Augment with soft reasoning retrieval
        if self.soft_reasoning and self.config.enable_soft_reasoning:
            try:
                results = self.soft_reasoning.query(task.query, top_k=5)
                retrieved = [
                    r.get("payload", {}).get("text", "")
                    for r in results
                    if r.get("payload")
                ]
                context.extend([r for r in retrieved if r])
            except Exception as e:
                logger.warning(f"Soft reasoning retrieval failed: {e}")

        return context if context else None

    def _generate_initial_response(
        self,
        task: CognitiveTask,
        context: Optional[List[str]],
        strategy: str,
        reasoning_trace: List[str],
    ) -> str:
        """Generate initial response"""
        if self.llm is None:
            return "Unable to generate response: LLM not initialized"

        # Build prompt
        prompt = self._build_prompt(task, context, strategy)

        try:
            from ai_karen_engine.integrations.llm_utils import LLMUtils
            if isinstance(self.llm, LLMUtils):
                output = self.llm.generate_text(prompt, max_tokens=500)
                reasoning_trace.append("Generated initial response")
                return output
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"Error generating response: {str(e)}"

    def _monitor_state(
        self,
        task: CognitiveTask,
        output: str,
        context: Optional[List[str]]
    ) -> Any:
        """Monitor metacognitive state"""
        if self.metacognition:
            return self.metacognition.monitor_reasoning_process(
                query=task.query,
                current_output=output,
                context=context,
            )

        # Fallback mock state
        from ai_karen_engine.core.reasoning.synthesis.metacognition import (
            MetacognitiveState,
            CognitiveState,
            ReasoningStrategy,
        )
        return MetacognitiveState(
            cognitive_state=CognitiveState.CONFIDENT,
            confidence=0.7,
            certainty=0.7,
            knowledge_gaps=[],
            active_strategy=ReasoningStrategy.ANALYTICAL,
            performance_estimate=0.7,
        )

    def _decide_processing_depth(
        self,
        task: CognitiveTask,
        initial_output: str,
        metacog_state: Any,
        mode: CognitiveMode,
    ) -> Tuple[bool, bool]:
        """Decide whether to refine and/or explore more"""
        should_refine = False
        should_explore = False

        # Fast mode: minimal processing
        if mode == CognitiveMode.FAST:
            return False, False

        # Reflective mode: always refine
        if mode == CognitiveMode.REFLECTIVE:
            should_refine = True

        # Check metacognitive state
        if self.metacognition:
            # Low confidence → refine
            if metacog_state.confidence < self.config.confidence_threshold:
                should_refine = True

            # Knowledge gaps → explore
            if len(metacog_state.knowledge_gaps) > 0:
                should_explore = True

            # Should seek more info?
            seek, _ = self.metacognition.should_seek_more_information()
            if seek:
                should_explore = True

        # Task requirements
        if task.requires_certainty and metacog_state.certainty < 0.8:
            should_refine = True

        # Adaptive mode: decide based on initial quality
        if mode == CognitiveMode.ADAPTIVE:
            initial_quality = self._quick_quality_check(initial_output)
            if initial_quality < self.config.quality_threshold:
                should_refine = True

        return should_refine, should_explore

    def _get_refinement_criteria(self, task: CognitiveTask) -> List[str]:
        """Get criteria for refinement"""
        criteria = ["accuracy", "coherence", "completeness"]

        if task.requires_certainty:
            criteria.append("confidence")

        if task.requires_explanation:
            criteria.append("clarity")

        return criteria

    def _expand_reasoning(
        self,
        task: CognitiveTask,
        current_output: str,
        context: Optional[List[str]],
        reasoning_trace: List[str],
    ) -> str:
        """Expand reasoning with additional exploration"""
        # For now, a simple placeholder
        # In full implementation, would gather more info and regenerate
        reasoning_trace.append("Explored additional information")
        return current_output

    def _verify_quality(
        self,
        task: CognitiveTask,
        output: str,
        context: Optional[List[str]]
    ) -> Tuple[float, str]:
        """Verify quality of output"""
        if self.verifier:
            try:
                result = self.verifier.verify(
                    query=task.query,
                    response=output,
                    context=context,
                )
                return result.overall_score, result.feedback
            except Exception as e:
                logger.warning(f"Verification failed: {e}")

        # Fallback heuristic
        score = self._quick_quality_check(output)
        return score, f"Quality score: {score:.2f}"

    def _quick_quality_check(self, output: str) -> float:
        """Quick heuristic quality check"""
        score = 0.5

        words = len(output.split())
        if 20 <= words <= 300:
            score += 0.2

        if output.count('.') >= 2:
            score += 0.2

        if not any(hw in output.lower() for hw in ['maybe', 'perhaps', 'might']):
            score += 0.1

        return min(1.0, score)

    def _update_learning(
        self,
        task: CognitiveTask,
        output: str,
        quality_score: float,
        strategy: str,
    ) -> None:
        """Update learning based on task outcome"""
        if not self.metacognition:
            return

        # Consider successful if quality above threshold
        success = quality_score >= self.config.quality_threshold

        from ai_karen_engine.core.reasoning.synthesis.metacognition import ReasoningStrategy
        strategy_enum = ReasoningStrategy.ANALYTICAL  # Default
        try:
            strategy_enum = ReasoningStrategy(strategy)
        except ValueError:
            pass

        self.metacognition.update_performance(
            task_success=success,
            actual_quality=quality_score,
            strategy_used=strategy_enum,
        )

    def _build_prompt(
        self,
        task: CognitiveTask,
        context: Optional[List[str]],
        strategy: str,
    ) -> str:
        """Build prompt for generation"""
        prompt_parts = []

        # Strategy guidance
        strategy_guidance = {
            "analytical": "Analyze this step-by-step using logical reasoning.",
            "causal": "Explain the causal relationships and mechanisms.",
            "comparative": "Compare and contrast the different aspects.",
            "exploratory": "Explore the topic comprehensively.",
            "focused": "Focus on the specific details requested.",
        }

        guidance = strategy_guidance.get(strategy, "")
        if guidance:
            prompt_parts.append(guidance)

        # Context
        if context:
            context_str = "\n".join(f"- {c}" for c in context[:5])
            prompt_parts.append(f"\nRelevant context:\n{context_str}")

        # Query
        prompt_parts.append(f"\nQuery: {task.query}")

        # Requirements
        if task.requires_certainty:
            prompt_parts.append("\nProvide a confident, certain answer.")
        if task.requires_explanation:
            prompt_parts.append("\nExplain your reasoning.")

        prompt_parts.append("\nResponse:")

        return "\n".join(prompt_parts)


def create_cognitive_orchestrator(**config_kwargs) -> CognitiveOrchestrator:
    """
    Factory function to create a CognitiveOrchestrator.

    Args:
        **config_kwargs: Configuration parameters

    Returns:
        Configured CognitiveOrchestrator instance
    """
    config = CognitiveConfig(**config_kwargs) if config_kwargs else None
    return CognitiveOrchestrator(config=config)
