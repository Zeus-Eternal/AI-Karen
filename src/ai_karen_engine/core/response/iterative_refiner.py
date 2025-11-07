"""
Iterative Self-Refinement Pipeline for Response Generation

Implements the 5-step iterative refinement process described in:
"Response Generation in Kari AI: An Iterative Neuro-Symbolic Framework
for Contextual Expression and Self-Refinement"

This module integrates with:
- Reasoning module (SelfRefiner, MetacognitiveMonitor)
- Memory module (MemoryManager, MemoryQuery)
- Response types (ResponseRequest, FormattedResponse)

Author: AI-Karen Core Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Tuple

# Import unified types from reasoning module
from ai_karen_engine.core.reasoning.synthesis.self_refine import (
    SelfRefiner,
    RefinementCriteria,
    RefinementResult,
)
from ai_karen_engine.core.reasoning.synthesis.metacognition import (
    MetacognitiveMonitor,
    MetacognitiveState,
    CognitiveState,
)

# Import unified types from memory module
from ai_karen_engine.core.memory.types import (
    MemoryEntry,
    MemoryQuery,
    MemoryQueryResult,
    MemoryType,
)
from ai_karen_engine.core.memory.protocols import MemoryManager

# Import unified response types
from ai_karen_engine.core.response.types import (
    ResponseRequest,
    FormattedResponse,
    ReasoningTrace,
    IntentType,
    SentimentType,
    PersonaType,
    ResponseStatus,
    make_response_id,
)


# ===================================
# REFINEMENT STAGE ENUMS
# ===================================

class RefinementStage(str, Enum):
    """Stages in the iterative refinement pipeline."""
    INITIAL_GENERATION = "initial_generation"
    COHERENCE_CHECK = "coherence_check"
    PERSONA_ALIGNMENT = "persona_alignment"
    MEMORY_CONSISTENCY = "memory_consistency"
    QUALITY_VERIFICATION = "quality_verification"
    FINALIZATION = "finalization"


class RefinementStatus(str, Enum):
    """Status of refinement iteration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONVERGED = "converged"
    MAX_ITERATIONS = "max_iterations"
    FAILED = "failed"


# ===================================
# DATA STRUCTURES
# ===================================

@dataclass
class RefinementIteration:
    """Single iteration in the refinement pipeline."""
    iteration_num: int
    stage: RefinementStage
    input_text: str
    output_text: str
    feedback: str

    # Quality metrics
    coherence_score: float = 0.0
    persona_alignment_score: float = 0.0
    memory_consistency_score: float = 0.0
    overall_quality: float = 0.0

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    time_ms: float = 0.0

    # Cognitive state
    cognitive_state: Optional[str] = None
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "iteration_num": self.iteration_num,
            "stage": self.stage.value,
            "input_text": self.input_text[:200] + "..." if len(self.input_text) > 200 else self.input_text,
            "output_text": self.output_text[:200] + "..." if len(self.output_text) > 200 else self.output_text,
            "feedback": self.feedback,
            "coherence_score": self.coherence_score,
            "persona_alignment_score": self.persona_alignment_score,
            "memory_consistency_score": self.memory_consistency_score,
            "overall_quality": self.overall_quality,
            "timestamp": self.timestamp.isoformat(),
            "time_ms": self.time_ms,
            "cognitive_state": self.cognitive_state,
            "confidence": self.confidence,
        }


@dataclass
class RefinementPipelineResult:
    """Result of the complete refinement pipeline."""
    request_id: str
    final_response: str
    status: RefinementStatus

    # Iteration history
    iterations: List[RefinementIteration] = field(default_factory=list)
    total_iterations: int = 0

    # Quality metrics
    initial_quality: float = 0.0
    final_quality: float = 0.0
    quality_improvement: float = 0.0

    # Timing
    total_time_ms: float = 0.0

    # Metadata
    converged: bool = False
    convergence_reason: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "final_response": self.final_response,
            "status": self.status.value,
            "iterations": [it.to_dict() for it in self.iterations],
            "total_iterations": self.total_iterations,
            "initial_quality": self.initial_quality,
            "final_quality": self.final_quality,
            "quality_improvement": self.quality_improvement,
            "total_time_ms": self.total_time_ms,
            "converged": self.converged,
            "convergence_reason": self.convergence_reason,
            "error": self.error,
        }


# ===================================
# PROTOCOLS
# ===================================

@dataclass
class RefinementConfig:
    """Configuration for iterative refinement."""
    max_iterations: int = 5
    convergence_threshold: float = 0.85  # Stop if quality > threshold
    min_improvement: float = 0.02  # Stop if improvement < threshold

    # Stage weights for overall quality
    coherence_weight: float = 0.35
    persona_weight: float = 0.25
    memory_weight: float = 0.25
    verification_weight: float = 0.15

    # Timeouts
    stage_timeout_ms: float = 5000
    total_timeout_ms: float = 30000

    # Enable/disable stages
    enable_coherence_check: bool = True
    enable_persona_alignment: bool = True
    enable_memory_consistency: bool = True
    enable_quality_verification: bool = True


class ResponseGenerator(Protocol):
    """Protocol for generating responses."""

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from prompt."""
        ...


# ===================================
# ITERATIVE REFINEMENT PIPELINE
# ===================================

class IterativeRefinementPipeline:
    """
    Iterative self-refinement pipeline for response generation.

    Implements the 5-step process:
    1. Initial Generation
    2. Coherence Check
    3. Persona Alignment
    4. Memory Consistency
    5. Quality Verification

    Integrates with:
    - SelfRefiner from reasoning module
    - MetacognitiveMonitor for cognitive state tracking
    - MemoryManager for consistency checks
    """

    def __init__(
        self,
        generator: ResponseGenerator,
        memory_manager: Optional[MemoryManager] = None,
        config: Optional[RefinementConfig] = None,
    ):
        """
        Initialize pipeline.

        Args:
            generator: Response generator (LLM client)
            memory_manager: Optional memory manager for consistency checks
            config: Refinement configuration
        """
        self.generator = generator
        self.memory_manager = memory_manager
        self.config = config or RefinementConfig()

        # Initialize reasoning components
        self.self_refiner = SelfRefiner(llm_client=generator)
        self.metacog_monitor = MetacognitiveMonitor(llm_client=generator)

    async def refine(
        self,
        request: ResponseRequest,
        initial_response: Optional[str] = None,
        memory_context: Optional[List[MemoryEntry]] = None,
    ) -> RefinementPipelineResult:
        """
        Execute the iterative refinement pipeline.

        Args:
            request: Response request with user input and context
            initial_response: Optional initial response (if None, will generate)
            memory_context: Optional memory context for consistency checks

        Returns:
            RefinementPipelineResult with refined response and metrics
        """
        start_time = time.time()
        iterations: List[RefinementIteration] = []

        try:
            # Step 1: Initial Generation
            current_response = initial_response
            if current_response is None:
                current_response = await self._generate_initial(request)

            # Track initial quality
            initial_quality = await self._assess_quality(
                request, current_response, memory_context
            )

            # Iterative refinement loop
            for i in range(self.config.max_iterations):
                iteration_start = time.time()

                # Step 2: Coherence Check
                if self.config.enable_coherence_check:
                    current_response, coherence_iter = await self._check_coherence(
                        request, current_response, i
                    )
                    iterations.append(coherence_iter)

                # Step 3: Persona Alignment
                if self.config.enable_persona_alignment:
                    current_response, persona_iter = await self._align_persona(
                        request, current_response, i
                    )
                    iterations.append(persona_iter)

                # Step 4: Memory Consistency
                if self.config.enable_memory_consistency and memory_context:
                    current_response, memory_iter = await self._check_memory_consistency(
                        request, current_response, memory_context, i
                    )
                    iterations.append(memory_iter)

                # Step 5: Quality Verification
                if self.config.enable_quality_verification:
                    current_response, quality_iter = await self._verify_quality(
                        request, current_response, memory_context, i
                    )
                    iterations.append(quality_iter)

                # Check convergence
                current_quality = await self._assess_quality(
                    request, current_response, memory_context
                )

                # Convergence condition 1: Quality threshold met
                if current_quality >= self.config.convergence_threshold:
                    total_time = (time.time() - start_time) * 1000
                    return RefinementPipelineResult(
                        request_id=request.request_id,
                        final_response=current_response,
                        status=RefinementStatus.CONVERGED,
                        iterations=iterations,
                        total_iterations=i + 1,
                        initial_quality=initial_quality,
                        final_quality=current_quality,
                        quality_improvement=current_quality - initial_quality,
                        total_time_ms=total_time,
                        converged=True,
                        convergence_reason="Quality threshold met",
                    )

                # Convergence condition 2: Minimal improvement
                if i > 0:
                    prev_quality = iterations[-1].overall_quality if iterations else initial_quality
                    improvement = current_quality - prev_quality
                    if improvement < self.config.min_improvement:
                        total_time = (time.time() - start_time) * 1000
                        return RefinementPipelineResult(
                            request_id=request.request_id,
                            final_response=current_response,
                            status=RefinementStatus.CONVERGED,
                            iterations=iterations,
                            total_iterations=i + 1,
                            initial_quality=initial_quality,
                            final_quality=current_quality,
                            quality_improvement=current_quality - initial_quality,
                            total_time_ms=total_time,
                            converged=True,
                            convergence_reason="Minimal improvement",
                        )

                # Check timeout
                elapsed_time = (time.time() - start_time) * 1000
                if elapsed_time >= self.config.total_timeout_ms:
                    return RefinementPipelineResult(
                        request_id=request.request_id,
                        final_response=current_response,
                        status=RefinementStatus.MAX_ITERATIONS,
                        iterations=iterations,
                        total_iterations=i + 1,
                        initial_quality=initial_quality,
                        final_quality=current_quality,
                        quality_improvement=current_quality - initial_quality,
                        total_time_ms=elapsed_time,
                        converged=False,
                        convergence_reason="Timeout",
                    )

            # Max iterations reached
            total_time = (time.time() - start_time) * 1000
            final_quality = await self._assess_quality(
                request, current_response, memory_context
            )

            return RefinementPipelineResult(
                request_id=request.request_id,
                final_response=current_response,
                status=RefinementStatus.MAX_ITERATIONS,
                iterations=iterations,
                total_iterations=self.config.max_iterations,
                initial_quality=initial_quality,
                final_quality=final_quality,
                quality_improvement=final_quality - initial_quality,
                total_time_ms=total_time,
                converged=False,
                convergence_reason="Max iterations",
            )

        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            return RefinementPipelineResult(
                request_id=request.request_id,
                final_response=current_response or "",
                status=RefinementStatus.FAILED,
                iterations=iterations,
                total_iterations=len(iterations),
                initial_quality=initial_quality if 'initial_quality' in locals() else 0.0,
                final_quality=0.0,
                quality_improvement=0.0,
                total_time_ms=total_time,
                converged=False,
                error=str(e),
            )

    async def _generate_initial(self, request: ResponseRequest) -> str:
        """Generate initial response."""
        prompt = f"User ({request.persona.value}): {request.user_text}\nAssistant:"
        return self.generator.generate(prompt)

    async def _check_coherence(
        self, request: ResponseRequest, response: str, iteration: int
    ) -> Tuple[str, RefinementIteration]:
        """Check and improve coherence."""
        start_time = time.time()

        # Use SelfRefiner for coherence check
        criteria = RefinementCriteria(
            check_coherence=True,
            check_relevance=True,
            check_completeness=True,
        )

        result = self.self_refiner.refine(
            query=request.user_text,
            initial_output=response,
            criteria=criteria,
        )

        # Monitor cognitive state
        metacog_state = self.metacog_monitor.monitor_reasoning_process(
            query=request.user_text,
            current_output=result.refined_output,
        )

        time_ms = (time.time() - start_time) * 1000

        iteration_data = RefinementIteration(
            iteration_num=iteration,
            stage=RefinementStage.COHERENCE_CHECK,
            input_text=response,
            output_text=result.refined_output,
            feedback=result.feedback[-1] if result.feedback else "Coherence verified",
            coherence_score=result.confidence,
            overall_quality=result.confidence,
            time_ms=time_ms,
            cognitive_state=metacog_state.state.value if metacog_state else None,
            confidence=metacog_state.confidence if metacog_state else result.confidence,
        )

        return result.refined_output, iteration_data

    async def _align_persona(
        self, request: ResponseRequest, response: str, iteration: int
    ) -> Tuple[str, RefinementIteration]:
        """Align response with persona."""
        start_time = time.time()

        # Create persona-specific criteria
        persona_prompt = f"""
Review the following response for alignment with the '{request.persona.value}' persona:

Response: {response}

Is the tone, style, and language appropriate for this persona?
If not, rewrite it to better match the persona while maintaining the core message.
"""

        aligned_response = self.generator.generate(persona_prompt)

        # Simple scoring based on length and style consistency
        persona_score = 0.8  # Placeholder - could use more sophisticated scoring

        time_ms = (time.time() - start_time) * 1000

        iteration_data = RefinementIteration(
            iteration_num=iteration,
            stage=RefinementStage.PERSONA_ALIGNMENT,
            input_text=response,
            output_text=aligned_response,
            feedback=f"Aligned with {request.persona.value} persona",
            persona_alignment_score=persona_score,
            overall_quality=persona_score,
            time_ms=time_ms,
        )

        return aligned_response, iteration_data

    async def _check_memory_consistency(
        self,
        request: ResponseRequest,
        response: str,
        memory_context: List[MemoryEntry],
        iteration: int,
    ) -> Tuple[str, RefinementIteration]:
        """Check consistency with memory context."""
        start_time = time.time()

        # Build context summary
        context_summary = "\n".join([
            f"- {entry.content[:100]}..." for entry in memory_context[:5]
        ])

        consistency_prompt = f"""
Review the following response for consistency with previous context:

Context:
{context_summary}

Response: {response}

Is the response consistent with the context? If not, revise it to maintain consistency.
"""

        consistent_response = self.generator.generate(consistency_prompt)

        # Simple scoring
        memory_score = 0.85  # Placeholder

        time_ms = (time.time() - start_time) * 1000

        iteration_data = RefinementIteration(
            iteration_num=iteration,
            stage=RefinementStage.MEMORY_CONSISTENCY,
            input_text=response,
            output_text=consistent_response,
            feedback="Checked memory consistency",
            memory_consistency_score=memory_score,
            overall_quality=memory_score,
            time_ms=time_ms,
        )

        return consistent_response, iteration_data

    async def _verify_quality(
        self,
        request: ResponseRequest,
        response: str,
        memory_context: Optional[List[MemoryEntry]],
        iteration: int,
    ) -> Tuple[str, RefinementIteration]:
        """Final quality verification."""
        start_time = time.time()

        quality_score = await self._assess_quality(request, response, memory_context)

        time_ms = (time.time() - start_time) * 1000

        iteration_data = RefinementIteration(
            iteration_num=iteration,
            stage=RefinementStage.QUALITY_VERIFICATION,
            input_text=response,
            output_text=response,  # No change in verification
            feedback=f"Quality score: {quality_score:.2f}",
            overall_quality=quality_score,
            time_ms=time_ms,
        )

        return response, iteration_data

    async def _assess_quality(
        self,
        request: ResponseRequest,
        response: str,
        memory_context: Optional[List[MemoryEntry]],
    ) -> float:
        """
        Assess overall quality of response.

        Returns score 0-1.
        """
        # Placeholder implementation
        # In production, this would use more sophisticated metrics

        scores = []
        weights = []

        # Coherence (length and structure heuristics)
        if self.config.enable_coherence_check:
            coherence = min(1.0, len(response.split()) / 50)  # Prefer 50+ words
            scores.append(coherence)
            weights.append(self.config.coherence_weight)

        # Persona alignment (placeholder)
        if self.config.enable_persona_alignment:
            persona_score = 0.8
            scores.append(persona_score)
            weights.append(self.config.persona_weight)

        # Memory consistency (placeholder)
        if self.config.enable_memory_consistency:
            memory_score = 0.85 if memory_context else 0.5
            scores.append(memory_score)
            weights.append(self.config.memory_weight)

        # Overall quality
        if scores:
            weighted_sum = sum(s * w for s, w in zip(scores, weights))
            total_weight = sum(weights)
            return weighted_sum / total_weight if total_weight > 0 else 0.5

        return 0.5


# ===================================
# FACTORY FUNCTIONS
# ===================================

def create_refinement_pipeline(
    generator: ResponseGenerator,
    memory_manager: Optional[MemoryManager] = None,
    max_iterations: int = 5,
    convergence_threshold: float = 0.85,
) -> IterativeRefinementPipeline:
    """
    Factory function to create refinement pipeline.

    Args:
        generator: Response generator
        memory_manager: Optional memory manager
        max_iterations: Maximum refinement iterations
        convergence_threshold: Quality threshold for convergence

    Returns:
        Configured IterativeRefinementPipeline
    """
    config = RefinementConfig(
        max_iterations=max_iterations,
        convergence_threshold=convergence_threshold,
    )

    return IterativeRefinementPipeline(
        generator=generator,
        memory_manager=memory_manager,
        config=config,
    )


__all__ = [
    # Enums
    "RefinementStage",
    "RefinementStatus",
    # Data structures
    "RefinementIteration",
    "RefinementPipelineResult",
    "RefinementConfig",
    # Protocol
    "ResponseGenerator",
    # Main class
    "IterativeRefinementPipeline",
    # Factory
    "create_refinement_pipeline",
]
