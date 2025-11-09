"""
Advanced Case Quality Analyzer - Next-Level Intelligence

This module provides sophisticated quality analysis for case-memory learning:
- Multi-dimensional quality scoring
- Predictive quality assessment
- Diversity metrics
- Conflict detection
- Anomaly detection
- Automated quality improvement suggestions
"""

from __future__ import annotations
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from .case_types import Case, Reward

logger = logging.getLogger(__name__)


@dataclass
class QualityDimensions:
    """Multi-dimensional quality scores"""
    relevance: float  # 0-1: How relevant to task domain
    completeness: float  # 0-1: Completeness of solution
    efficiency: float  # 0-1: Resource efficiency
    novelty: float  # 0-1: Novelty/uniqueness
    reusability: float  # 0-1: Reusability potential
    reliability: float  # 0-1: Reliability score
    complexity: float  # 0-1: Solution complexity
    clarity: float  # 0-1: Clarity of documentation

    def overall_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate weighted overall quality score"""
        if weights is None:
            weights = {
                'relevance': 0.20,
                'completeness': 0.15,
                'efficiency': 0.15,
                'novelty': 0.10,
                'reusability': 0.15,
                'reliability': 0.15,
                'complexity': 0.05,
                'clarity': 0.05
            }

        score = 0.0
        for dim, value in self.__dict__.items():
            score += value * weights.get(dim, 0.0)
        return score


@dataclass
class QualityAnalysis:
    """Comprehensive quality analysis result"""
    case_id: str
    dimensions: QualityDimensions
    overall_score: float
    confidence: float  # 0-1: Confidence in assessment
    warnings: List[str]
    suggestions: List[str]
    anomalies: List[str]
    comparisons: Dict[str, float]  # Comparison to similar cases
    timestamp: datetime


class CaseQualityAnalyzer:
    """
    Advanced quality analyzer for case-memory learning

    Features:
    - Multi-dimensional quality scoring
    - Predictive quality assessment
    - Diversity and novelty analysis
    - Conflict and anomaly detection
    - Quality improvement suggestions
    - Comparative analysis
    """

    def __init__(self, history_window: int = 1000):
        self.history_window = history_window
        self.case_history: List[Case] = []
        self.quality_history: List[QualityAnalysis] = []
        self.category_stats: Dict[str, Dict[str, float]] = defaultdict(dict)

    def analyze_case(self, case: Case, similar_cases: Optional[List[Case]] = None) -> QualityAnalysis:
        """Perform comprehensive quality analysis on a case"""

        # Calculate quality dimensions
        dimensions = self._calculate_dimensions(case, similar_cases)

        # Calculate overall score
        overall_score = dimensions.overall_score()

        # Calculate confidence based on data availability
        confidence = self._calculate_confidence(case, similar_cases)

        # Detect warnings
        warnings = self._detect_warnings(case, dimensions)

        # Generate improvement suggestions
        suggestions = self._generate_suggestions(case, dimensions)

        # Detect anomalies
        anomalies = self._detect_anomalies(case, dimensions)

        # Comparative analysis
        comparisons = self._comparative_analysis(case, similar_cases)

        analysis = QualityAnalysis(
            case_id=case.case_id,
            dimensions=dimensions,
            overall_score=overall_score,
            confidence=confidence,
            warnings=warnings,
            suggestions=suggestions,
            anomalies=anomalies,
            comparisons=comparisons,
            timestamp=datetime.utcnow()
        )

        # Update history
        self._update_history(case, analysis)

        return analysis

    def _calculate_dimensions(self, case: Case, similar_cases: Optional[List[Case]]) -> QualityDimensions:
        """Calculate all quality dimensions"""

        # Relevance: Based on reward signals
        relevance = case.reward.score

        # Completeness: Based on outcome and steps
        completeness = self._assess_completeness(case)

        # Efficiency: Steps vs outcome ratio
        efficiency = self._assess_efficiency(case)

        # Novelty: Comparison to similar cases
        novelty = self._assess_novelty(case, similar_cases)

        # Reusability: Based on generalization potential
        reusability = self._assess_reusability(case)

        # Reliability: Based on consistency of reward signals
        reliability = self._assess_reliability(case)

        # Complexity: Based on solution complexity
        complexity = self._assess_complexity(case)

        # Clarity: Based on documentation quality
        clarity = self._assess_clarity(case)

        return QualityDimensions(
            relevance=relevance,
            completeness=completeness,
            efficiency=efficiency,
            novelty=novelty,
            reusability=reusability,
            reliability=reliability,
            complexity=complexity,
            clarity=clarity
        )

    def _assess_completeness(self, case: Case) -> float:
        """Assess completeness of the case"""
        score = 0.0

        # Check for all required fields
        if case.task_text: score += 0.2
        if case.plan_text: score += 0.2
        if case.steps: score += 0.3
        if case.outcome_text: score += 0.2
        if case.tags: score += 0.1

        return min(score, 1.0)

    def _assess_efficiency(self, case: Case) -> float:
        """Assess efficiency based on steps and outcome"""
        if not case.steps:
            return 0.5  # Neutral if no steps

        # Fewer steps with good outcome = higher efficiency
        num_steps = len(case.steps)
        reward = case.reward.score

        # Normalize: 1-5 steps = excellent, 6-10 = good, 11+ = poor
        step_efficiency = max(0.0, 1.0 - (num_steps - 1) / 20)

        # Combine with reward
        return (step_efficiency * 0.4) + (reward * 0.6)

    def _assess_novelty(self, case: Case, similar_cases: Optional[List[Case]]) -> float:
        """Assess novelty compared to similar cases"""
        if not similar_cases:
            return 0.8  # High novelty if no similar cases

        # Compare embeddings if available
        if case.embeddings and case.embeddings.get('task'):
            similarities = []
            for sim_case in similar_cases[:5]:
                if sim_case.embeddings and sim_case.embeddings.get('task'):
                    sim = self._cosine_similarity(
                        case.embeddings['task'],
                        sim_case.embeddings['task']
                    )
                    similarities.append(sim)

            if similarities:
                avg_similarity = sum(similarities) / len(similarities)
                novelty = 1.0 - avg_similarity  # Higher novelty = lower similarity
                return max(0.0, min(1.0, novelty))

        return 0.5  # Neutral if can't calculate

    def _assess_reusability(self, case: Case) -> float:
        """Assess reusability potential"""
        score = 0.0

        # Well-documented cases are more reusable
        if case.plan_text and len(case.plan_text) > 50:
            score += 0.3

        # General tags indicate broader applicability
        if case.tags:
            score += min(0.3, len(case.tags) * 0.1)

        # Steps with clear patterns are reusable
        if case.steps and len(case.steps) >= 2:
            score += 0.2

        # Pointers to resources enhance reusability
        if case.pointers:
            score += min(0.2, len(case.pointers) * 0.05)

        return min(score, 1.0)

    def _assess_reliability(self, case: Case) -> float:
        """Assess reliability based on reward signals"""
        signals = case.reward.signals

        if not signals or len(signals) < 2:
            return case.reward.score  # Use overall score if limited signals

        # Calculate coefficient of variation
        values = list(signals.values())
        mean = np.mean(values)
        std = np.std(values)

        if mean == 0:
            return 0.5

        cv = std / mean  # Lower CV = more reliable
        reliability = max(0.0, 1.0 - cv)

        # Weight by overall score
        return (reliability * 0.6) + (case.reward.score * 0.4)

    def _assess_complexity(self, case: Case) -> float:
        """Assess solution complexity"""
        complexity = 0.0

        # More steps = higher complexity
        if case.steps:
            complexity += min(0.4, len(case.steps) * 0.05)

        # Tool usage indicates complexity
        tool_count = sum(1 for step in case.steps if step.tool_io is not None)
        complexity += min(0.3, tool_count * 0.1)

        # Longer plans/outcomes = more complex
        if case.plan_text:
            complexity += min(0.15, len(case.plan_text) / 2000)
        if case.outcome_text:
            complexity += min(0.15, len(case.outcome_text) / 2000)

        return min(complexity, 1.0)

    def _assess_clarity(self, case: Case) -> float:
        """Assess clarity of documentation"""
        score = 0.0

        # Clear task description
        if case.task_text and len(case.task_text) > 20:
            score += 0.25

        # Well-documented plan
        if case.plan_text and len(case.plan_text) > 30:
            score += 0.25

        # Clear outcome
        if case.outcome_text and len(case.outcome_text) > 20:
            score += 0.25

        # Tagged appropriately
        if case.tags:
            score += 0.25

        return score

    def _calculate_confidence(self, case: Case, similar_cases: Optional[List[Case]]) -> float:
        """Calculate confidence in quality assessment"""
        confidence = 0.5  # Base confidence

        # More reward signals = higher confidence
        if case.reward.signals:
            confidence += min(0.2, len(case.reward.signals) * 0.05)

        # Similar cases for comparison = higher confidence
        if similar_cases:
            confidence += min(0.2, len(similar_cases) * 0.04)

        # Complete data = higher confidence
        if case.plan_text and case.steps and case.outcome_text:
            confidence += 0.1

        return min(confidence, 1.0)

    def _detect_warnings(self, case: Case, dimensions: QualityDimensions) -> List[str]:
        """Detect quality warnings"""
        warnings = []

        if dimensions.completeness < 0.6:
            warnings.append("Case lacks complete documentation")

        if dimensions.efficiency < 0.4:
            warnings.append("Solution appears inefficient - too many steps")

        if dimensions.reliability < 0.5:
            warnings.append("Inconsistent reward signals detected")

        if dimensions.clarity < 0.5:
            warnings.append("Documentation clarity needs improvement")

        if not case.tags:
            warnings.append("No tags assigned - impacts discoverability")

        if case.reward.score < 0.5:
            warnings.append("Low overall reward score")

        return warnings

    def _generate_suggestions(self, case: Case, dimensions: QualityDimensions) -> List[str]:
        """Generate quality improvement suggestions"""
        suggestions = []

        if dimensions.completeness < 0.8:
            if not case.plan_text:
                suggestions.append("Add detailed plan description")
            if not case.steps:
                suggestions.append("Include execution steps")
            if not case.tags:
                suggestions.append("Add relevant tags for categorization")

        if dimensions.efficiency < 0.6:
            suggestions.append("Consider optimizing solution to reduce steps")

        if dimensions.clarity < 0.7:
            suggestions.append("Improve documentation clarity and detail")

        if dimensions.reusability < 0.6:
            suggestions.append("Add more context to increase reusability")
            suggestions.append("Include resource pointers for reference")

        if dimensions.novelty < 0.3:
            suggestions.append("Case appears very similar to existing cases - consider merging")

        return suggestions

    def _detect_anomalies(self, case: Case, dimensions: QualityDimensions) -> List[str]:
        """Detect anomalies in case quality"""
        anomalies = []

        # High reward but low completeness
        if case.reward.score > 0.8 and dimensions.completeness < 0.5:
            anomalies.append("High reward with incomplete documentation - suspicious")

        # Low reward but high confidence signals
        if case.reward.score < 0.3 and len(case.reward.signals) > 3:
            anomalies.append("Consistently low reward across multiple signals")

        # Very high complexity with very low steps
        if dimensions.complexity > 0.7 and len(case.steps) < 2:
            anomalies.append("High complexity claim with minimal steps - inconsistent")

        # No embeddings
        if not case.embeddings:
            anomalies.append("Missing embeddings - retrieval will be impaired")

        return anomalies

    def _comparative_analysis(self, case: Case, similar_cases: Optional[List[Case]]) -> Dict[str, float]:
        """Compare case to similar cases"""
        if not similar_cases:
            return {}

        comparisons = {}

        # Average reward comparison
        avg_reward = sum(c.reward.score for c in similar_cases) / len(similar_cases)
        comparisons['reward_vs_similar'] = case.reward.score - avg_reward

        # Steps comparison
        avg_steps = sum(len(c.steps) for c in similar_cases) / len(similar_cases)
        comparisons['steps_vs_similar'] = len(case.steps) - avg_steps

        # Recency comparison
        if similar_cases[0].created_at:
            days_newer = (case.created_at - similar_cases[0].created_at).days
            comparisons['days_vs_most_recent'] = float(days_newer)

        return comparisons

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        v1 = np.array(vec1)
        v2 = np.array(vec2)

        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def _update_history(self, case: Case, analysis: QualityAnalysis) -> None:
        """Update history for trend analysis"""
        self.case_history.append(case)
        self.quality_history.append(analysis)

        # Maintain window size
        if len(self.case_history) > self.history_window:
            self.case_history.pop(0)
            self.quality_history.pop(0)

        # Update category statistics
        for tag in case.tags:
            if tag not in self.category_stats:
                self.category_stats[tag] = {
                    'count': 0,
                    'avg_quality': 0.0,
                    'avg_reward': 0.0
                }

            stats = self.category_stats[tag]
            stats['count'] += 1
            stats['avg_quality'] = (
                (stats['avg_quality'] * (stats['count'] - 1) + analysis.overall_score)
                / stats['count']
            )
            stats['avg_reward'] = (
                (stats['avg_reward'] * (stats['count'] - 1) + case.reward.score)
                / stats['count']
            )

    def get_quality_trends(self, lookback_days: int = 30) -> Dict[str, Any]:
        """Analyze quality trends over time"""
        if not self.quality_history:
            return {}

        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        recent = [a for a in self.quality_history if a.timestamp >= cutoff]

        if not recent:
            return {}

        return {
            'avg_quality': sum(a.overall_score for a in recent) / len(recent),
            'avg_confidence': sum(a.confidence for a in recent) / len(recent),
            'total_warnings': sum(len(a.warnings) for a in recent),
            'total_suggestions': sum(len(a.suggestions) for a in recent),
            'total_anomalies': sum(len(a.anomalies) for a in recent),
            'case_count': len(recent),
            'quality_trend': self._calculate_trend([a.overall_score for a in recent]),
            'category_stats': dict(self.category_stats)
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return 'stable'

        # Simple linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        if slope > 0.01:
            return 'improving'
        elif slope < -0.01:
            return 'declining'
        else:
            return 'stable'


# Global analyzer instance
_global_analyzer: Optional[CaseQualityAnalyzer] = None

def get_quality_analyzer() -> CaseQualityAnalyzer:
    """Get global quality analyzer instance"""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = CaseQualityAnalyzer()
    return _global_analyzer
