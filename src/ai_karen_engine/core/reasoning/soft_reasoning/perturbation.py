"""
Embedding Perturbation for Soft Reasoning

Implements controlled embedding perturbation strategies from the Soft Reasoning paper:
"Soft Reasoning: Navigating Solution Spaces in Large Language Models
through Controlled Embedding Exploration"

Key concepts:
- Controlled perturbation of first-token embeddings
- Gaussian noise with adaptive variance
- Directional perturbation toward semantic goals
- Diversity-aware exploration strategies
"""

from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PerturbationStrategy(Enum):
    """Strategies for perturbing embeddings"""
    GAUSSIAN = "gaussian"              # Add Gaussian noise
    DIRECTIONAL = "directional"        # Perturb toward a direction
    ADAPTIVE = "adaptive"              # Adapt variance based on confidence
    DIVERSE = "diverse"                # Maximize diversity in exploration
    HYBRID = "hybrid"                  # Combine multiple strategies


@dataclass
class PerturbationConfig:
    """Configuration for embedding perturbation"""
    strategy: PerturbationStrategy = PerturbationStrategy.ADAPTIVE
    base_variance: float = 0.01        # Base variance for Gaussian noise
    min_variance: float = 0.001        # Minimum variance
    max_variance: float = 0.1          # Maximum variance
    adaptive_factor: float = 2.0       # Factor for adapting variance
    diversity_weight: float = 0.3      # Weight for diversity objective
    directional_strength: float = 0.1  # Strength of directional perturbation


class EmbeddingPerturber:
    """
    Perturbs embeddings for controlled exploration of solution space.

    Based on the Soft Reasoning paper's approach of optimizing
    the first-token embedding to guide LLM generation.
    """

    def __init__(self, config: Optional[PerturbationConfig] = None):
        self.config = config or PerturbationConfig()
        self._history: List[List[float]] = []  # Track explored embeddings

    def perturb(
        self,
        embedding: List[float],
        *,
        confidence: Optional[float] = None,
        target_direction: Optional[List[float]] = None,
        diversity_boost: bool = False,
    ) -> List[float]:
        """
        Perturb an embedding using the configured strategy.

        Args:
            embedding: Original embedding vector
            confidence: Current confidence score (0-1), used for adaptive strategies
            target_direction: Optional target direction for directional perturbation
            diversity_boost: If True, increase perturbation to explore diverse regions

        Returns:
            Perturbed embedding vector
        """
        strategy = self.config.strategy

        if strategy == PerturbationStrategy.GAUSSIAN:
            return self._gaussian_perturb(embedding, self.config.base_variance)
        elif strategy == PerturbationStrategy.DIRECTIONAL:
            if target_direction is None:
                logger.warning("Directional perturbation requires target_direction, falling back to Gaussian")
                return self._gaussian_perturb(embedding, self.config.base_variance)
            return self._directional_perturb(embedding, target_direction)
        elif strategy == PerturbationStrategy.ADAPTIVE:
            return self._adaptive_perturb(embedding, confidence)
        elif strategy == PerturbationStrategy.DIVERSE:
            return self._diverse_perturb(embedding, diversity_boost)
        elif strategy == PerturbationStrategy.HYBRID:
            return self._hybrid_perturb(embedding, confidence, target_direction, diversity_boost)
        else:
            return self._gaussian_perturb(embedding, self.config.base_variance)

    def perturb_batch(
        self,
        embedding: List[float],
        num_perturbations: int,
        *,
        confidence: Optional[float] = None,
    ) -> List[List[float]]:
        """
        Generate multiple perturbed versions of an embedding.

        Useful for parallel exploration of the solution space.

        Args:
            embedding: Original embedding vector
            num_perturbations: Number of perturbed versions to generate
            confidence: Current confidence score for adaptive strategies

        Returns:
            List of perturbed embedding vectors
        """
        perturbed = []
        for i in range(num_perturbations):
            # Increase diversity for later perturbations
            diversity_boost = i > num_perturbations // 2
            p = self.perturb(embedding, confidence=confidence, diversity_boost=diversity_boost)
            perturbed.append(p)
            self._history.append(p)
        return perturbed

    def _gaussian_perturb(self, embedding: List[float], variance: float) -> List[float]:
        """Add Gaussian noise to embedding"""
        std = math.sqrt(variance)
        return [x + random.gauss(0, std) for x in embedding]

    def _directional_perturb(
        self,
        embedding: List[float],
        direction: List[float]
    ) -> List[float]:
        """
        Perturb embedding toward a target direction.

        Useful for steering toward known good regions of the solution space.
        """
        strength = self.config.directional_strength

        # Normalize direction
        norm = math.sqrt(sum(d * d for d in direction))
        if norm < 1e-8:
            return embedding
        direction_normalized = [d / norm for d in direction]

        # Add directional component + some noise
        perturbed = [
            e + strength * d + random.gauss(0, 0.01)
            for e, d in zip(embedding, direction_normalized)
        ]
        return perturbed

    def _adaptive_perturb(
        self,
        embedding: List[float],
        confidence: Optional[float]
    ) -> List[float]:
        """
        Adapt perturbation variance based on confidence.

        Low confidence → larger perturbations (explore more)
        High confidence → smaller perturbations (exploit current region)
        """
        if confidence is None:
            confidence = 0.5

        # Inverse relationship: low confidence → high variance
        adaptive_variance = self.config.base_variance * (
            1.0 + (1.0 - confidence) * self.config.adaptive_factor
        )

        # Clamp to configured bounds
        adaptive_variance = max(
            self.config.min_variance,
            min(self.config.max_variance, adaptive_variance)
        )

        return self._gaussian_perturb(embedding, adaptive_variance)

    def _diverse_perturb(
        self,
        embedding: List[float],
        diversity_boost: bool
    ) -> List[float]:
        """
        Perturb to maximize diversity from previously explored embeddings.

        Computes average of history and perturbs away from it.
        """
        if not self._history:
            return self._gaussian_perturb(embedding, self.config.base_variance)

        # Compute average of explored embeddings
        dim = len(embedding)
        avg_history = [0.0] * dim
        for hist_emb in self._history[-10:]:  # Use recent history
            for i, val in enumerate(hist_emb):
                avg_history[i] += val
        avg_history = [x / len(self._history[-10:]) for x in avg_history]

        # Compute direction away from average
        away_direction = [e - avg for e, avg in zip(embedding, avg_history)]

        # Normalize and scale
        norm = math.sqrt(sum(d * d for d in away_direction))
        if norm > 1e-8:
            away_direction = [d / norm for d in away_direction]

        diversity_weight = self.config.diversity_weight
        if diversity_boost:
            diversity_weight *= 2.0

        # Perturb away from average + add noise
        perturbed = [
            e + diversity_weight * d + random.gauss(0, self.config.base_variance)
            for e, d in zip(embedding, away_direction)
        ]
        return perturbed

    def _hybrid_perturb(
        self,
        embedding: List[float],
        confidence: Optional[float],
        target_direction: Optional[List[float]],
        diversity_boost: bool
    ) -> List[float]:
        """
        Combine multiple perturbation strategies.

        Balances exploration (diversity) and exploitation (directional).
        """
        # Start with adaptive perturbation
        perturbed = self._adaptive_perturb(embedding, confidence)

        # Add diversity component if we have history
        if self._history:
            diverse = self._diverse_perturb(perturbed, diversity_boost)
            # Blend: 70% adaptive, 30% diverse
            perturbed = [
                0.7 * p + 0.3 * d
                for p, d in zip(perturbed, diverse)
            ]

        # Add directional component if provided
        if target_direction:
            directional = self._directional_perturb(perturbed, target_direction)
            # Blend: 80% current, 20% directional
            perturbed = [
                0.8 * p + 0.2 * d
                for p, d in zip(perturbed, directional)
            ]

        return perturbed

    def reset_history(self) -> None:
        """Clear exploration history"""
        self._history.clear()

    def get_exploration_diversity(self) -> float:
        """
        Compute diversity metric for explored embeddings.

        Returns:
            Diversity score (0-1), higher means more diverse exploration
        """
        if len(self._history) < 2:
            return 0.0

        # Compute average pairwise distance
        total_dist = 0.0
        count = 0
        for i, emb1 in enumerate(self._history):
            for emb2 in self._history[i+1:]:
                dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(emb1, emb2)))
                total_dist += dist
                count += 1

        if count == 0:
            return 0.0

        avg_dist = total_dist / count

        # Normalize to 0-1 range (assuming embedding space has typical scale)
        # This is a heuristic normalization
        return min(1.0, avg_dist / 10.0)
