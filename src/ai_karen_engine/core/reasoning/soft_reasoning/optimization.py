"""
Bayesian Optimization for Soft Reasoning

Implements Bayesian optimization to refine embeddings based on verifier feedback,
as described in the Soft Reasoning paper.

Key concepts:
- Gaussian Process surrogate model for embedding-to-score mapping
- Acquisition functions (UCB, EI, PI) for exploration-exploitation balance
- Sequential optimization of embeddings
- Efficient search through high-dimensional embedding spaces
"""

from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AcquisitionFunction(Enum):
    """Acquisition functions for Bayesian optimization"""
    UCB = "ucb"                    # Upper Confidence Bound
    EI = "ei"                      # Expected Improvement
    PI = "pi"                      # Probability of Improvement
    THOMPSON = "thompson"          # Thompson Sampling


@dataclass
class OptimizationConfig:
    """Configuration for Bayesian optimization"""
    acquisition_fn: AcquisitionFunction = AcquisitionFunction.UCB
    exploration_weight: float = 2.0       # UCB exploration parameter (β)
    max_iterations: int = 20              # Maximum optimization iterations
    convergence_threshold: float = 0.01   # Stop if improvement < threshold
    initial_samples: int = 5              # Initial random samples
    length_scale: float = 1.0             # GP kernel length scale
    noise_variance: float = 0.01          # Observation noise variance


@dataclass
class OptimizationResult:
    """Result from Bayesian optimization"""
    best_embedding: List[float]
    best_score: float
    num_iterations: int
    converged: bool
    history: List[Tuple[List[float], float]]  # (embedding, score) pairs


class BayesianOptimizer:
    """
    Bayesian Optimizer for refining embeddings.

    Uses a Gaussian Process surrogate model to efficiently search
    the embedding space for high-scoring regions.
    """

    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or OptimizationConfig()
        self._observations: List[Tuple[List[float], float]] = []
        self._best_score = float('-inf')
        self._best_embedding: Optional[List[float]] = None

    def optimize(
        self,
        initial_embedding: List[float],
        score_function: Callable[[List[float]], float],
        *,
        perturb_fn: Optional[Callable[[List[float]], List[float]]] = None,
    ) -> OptimizationResult:
        """
        Optimize embedding to maximize score function.

        Args:
            initial_embedding: Starting embedding vector
            score_function: Function that scores embeddings (higher is better)
            perturb_fn: Optional perturbation function for generating candidates

        Returns:
            OptimizationResult with best embedding and optimization statistics
        """
        logger.info("Starting Bayesian optimization for embedding refinement")

        # Initialize with random samples
        self._initialize(initial_embedding, score_function, perturb_fn)

        converged = False
        for iteration in range(self.config.max_iterations):
            # Select next candidate using acquisition function
            candidate = self._select_next_candidate(initial_embedding, perturb_fn)

            # Evaluate candidate
            score = score_function(candidate)
            self._observations.append((candidate, score))

            # Update best
            if score > self._best_score:
                improvement = score - self._best_score
                self._best_score = score
                self._best_embedding = candidate

                logger.debug(f"Iteration {iteration}: New best score {score:.4f} (improvement: {improvement:.4f})")

                # Check convergence
                if improvement < self.config.convergence_threshold:
                    converged = True
                    logger.info(f"Converged after {iteration + 1} iterations")
                    break
            else:
                logger.debug(f"Iteration {iteration}: Score {score:.4f} (no improvement)")

        if self._best_embedding is None:
            # Fallback to initial embedding if optimization failed
            self._best_embedding = initial_embedding
            self._best_score = score_function(initial_embedding)

        return OptimizationResult(
            best_embedding=self._best_embedding,
            best_score=self._best_score,
            num_iterations=len(self._observations),
            converged=converged,
            history=self._observations.copy()
        )

    def _initialize(
        self,
        initial_embedding: List[float],
        score_function: Callable[[List[float]], float],
        perturb_fn: Optional[Callable[[List[float]], List[float]]],
    ) -> None:
        """Initialize with random samples"""
        self._observations.clear()
        self._best_score = float('-inf')
        self._best_embedding = None

        # Evaluate initial embedding
        initial_score = score_function(initial_embedding)
        self._observations.append((initial_embedding, initial_score))
        self._best_score = initial_score
        self._best_embedding = initial_embedding

        # Generate and evaluate random perturbations
        for _ in range(self.config.initial_samples - 1):
            if perturb_fn:
                candidate = perturb_fn(initial_embedding)
            else:
                candidate = self._default_perturb(initial_embedding)

            score = score_function(candidate)
            self._observations.append((candidate, score))

            if score > self._best_score:
                self._best_score = score
                self._best_embedding = candidate

    def _select_next_candidate(
        self,
        initial_embedding: List[float],
        perturb_fn: Optional[Callable[[List[float]], List[float]]],
    ) -> List[float]:
        """
        Select next candidate to evaluate using acquisition function.

        Generates multiple candidates and selects the one with highest
        acquisition value.
        """
        num_candidates = 20  # Number of candidates to evaluate
        candidates = []

        # Generate candidates
        for _ in range(num_candidates):
            if perturb_fn:
                candidate = perturb_fn(
                    self._best_embedding or initial_embedding
                )
            else:
                candidate = self._default_perturb(
                    self._best_embedding or initial_embedding
                )
            candidates.append(candidate)

        # Compute acquisition values
        acquisition_values = [
            self._acquisition_value(c) for c in candidates
        ]

        # Select best
        best_idx = max(range(len(candidates)), key=lambda i: acquisition_values[i])
        return candidates[best_idx]

    def _acquisition_value(self, embedding: List[float]) -> float:
        """
        Compute acquisition function value for a candidate embedding.

        Uses Gaussian Process posterior to estimate mean and uncertainty.
        """
        if self.config.acquisition_fn == AcquisitionFunction.UCB:
            return self._ucb(embedding)
        elif self.config.acquisition_fn == AcquisitionFunction.EI:
            return self._expected_improvement(embedding)
        elif self.config.acquisition_fn == AcquisitionFunction.PI:
            return self._probability_improvement(embedding)
        elif self.config.acquisition_fn == AcquisitionFunction.THOMPSON:
            return self._thompson_sampling(embedding)
        else:
            return self._ucb(embedding)

    def _ucb(self, embedding: List[float]) -> float:
        """
        Upper Confidence Bound acquisition function.

        UCB = μ(x) + β * σ(x)

        Balances exploitation (μ) and exploration (σ).
        """
        mean, std = self._gp_predict(embedding)
        beta = self.config.exploration_weight
        return mean + beta * std

    def _expected_improvement(self, embedding: List[float]) -> float:
        """
        Expected Improvement acquisition function.

        EI measures the expected improvement over the current best.
        """
        mean, std = self._gp_predict(embedding)

        if std < 1e-8:
            return 0.0

        # Compute improvement
        improvement = mean - self._best_score
        z = improvement / std

        # EI = improvement * Φ(z) + std * φ(z)
        # Using approximations for normal CDF and PDF
        phi_z = 0.5 * (1.0 + math.erf(z / math.sqrt(2)))  # CDF
        pdf_z = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)  # PDF

        ei = improvement * phi_z + std * pdf_z
        return max(0.0, ei)

    def _probability_improvement(self, embedding: List[float]) -> float:
        """
        Probability of Improvement acquisition function.

        PI measures the probability of improving over the current best.
        """
        mean, std = self._gp_predict(embedding)

        if std < 1e-8:
            return 0.0

        improvement = mean - self._best_score
        z = improvement / std

        # PI = Φ(z)
        pi = 0.5 * (1.0 + math.erf(z / math.sqrt(2)))
        return pi

    def _thompson_sampling(self, embedding: List[float]) -> float:
        """
        Thompson Sampling: sample from posterior.

        Returns a sample from N(μ(x), σ²(x)).
        """
        mean, std = self._gp_predict(embedding)
        return random.gauss(mean, std)

    def _gp_predict(self, embedding: List[float]) -> Tuple[float, float]:
        """
        Simplified Gaussian Process prediction.

        Returns (mean, std) for the given embedding.

        This is a simplified implementation using local interpolation.
        For production, consider using a proper GP library like scikit-learn.
        """
        if not self._observations:
            return (0.0, 1.0)

        # Compute kernel similarities to observed points
        similarities = []
        scores = []

        for obs_emb, obs_score in self._observations:
            sim = self._rbf_kernel(embedding, obs_emb)
            similarities.append(sim)
            scores.append(obs_score)

        # Weighted average for mean (kernel regression)
        total_sim = sum(similarities) + 1e-8
        mean = sum(sim * score for sim, score in zip(similarities, scores)) / total_sim

        # Uncertainty decreases with proximity to observations
        max_sim = max(similarities)
        std = math.sqrt(1.0 - max_sim + self.config.noise_variance)

        return (mean, std)

    def _rbf_kernel(self, x1: List[float], x2: List[float]) -> float:
        """
        Radial Basis Function (RBF) kernel.

        k(x1, x2) = exp(-||x1 - x2||² / (2 * length_scale²))
        """
        squared_dist = sum((a - b) ** 2 for a, b in zip(x1, x2))
        length_scale = self.config.length_scale
        return math.exp(-squared_dist / (2 * length_scale ** 2))

    def _default_perturb(self, embedding: List[float]) -> List[float]:
        """Default perturbation: add Gaussian noise"""
        std = 0.1
        return [x + random.gauss(0, std) for x in embedding]

    def reset(self) -> None:
        """Reset optimizer state"""
        self._observations.clear()
        self._best_score = float('-inf')
        self._best_embedding = None


def optimize_embedding_batch(
    embeddings: List[List[float]],
    score_function: Callable[[List[float]], float],
    config: Optional[OptimizationConfig] = None,
) -> List[OptimizationResult]:
    """
    Optimize multiple embeddings in parallel.

    Args:
        embeddings: List of initial embeddings to optimize
        score_function: Function to score embeddings
        config: Optimization configuration

    Returns:
        List of optimization results
    """
    optimizer = BayesianOptimizer(config)
    results = []

    for embedding in embeddings:
        result = optimizer.optimize(embedding, score_function)
        results.append(result)
        optimizer.reset()  # Reset for next embedding

    return results
