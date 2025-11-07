"""
Business Intelligence and Analytics Layer

This module provides enterprise-level analytics and insights:
- KPI tracking and dashboards
- ROI and value attribution
- Trend analysis and forecasting
- Performance analytics
- Cost optimization
- Success prediction
- Causal impact analysis
- Reporting and visualization data
"""

from __future__ import annotations
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from .case_types import Case

logger = logging.getLogger(__name__)


@dataclass
class KPIMetrics:
    """Key Performance Indicators for learning system"""
    # Volume metrics
    total_cases: int = 0
    cases_this_period: int = 0
    cases_growth_rate: float = 0.0

    # Quality metrics
    avg_case_quality: float = 0.0
    quality_trend: str = "stable"  # improving, stable, declining
    high_quality_ratio: float = 0.0  # % of cases with reward >= 0.7

    # Usage metrics
    total_retrievals: int = 0
    retrieval_success_rate: float = 0.0
    avg_cases_per_retrieval: float = 0.0

    # Value metrics
    estimated_roi: float = 0.0
    time_saved_hours: float = 0.0
    cost_savings: float = 0.0

    # Performance metrics
    avg_admission_latency_ms: float = 0.0
    avg_retrieval_latency_ms: float = 0.0
    system_uptime_percent: float = 100.0


@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    trend_direction: str  # up, down, stable
    forecast_next_period: float
    confidence_interval: Tuple[float, float]
    anomalies_detected: List[str]


@dataclass
class ROICalculation:
    """ROI calculation result"""
    period_start: datetime
    period_end: datetime
    total_investment: float  # Cost of running system
    total_return: float  # Value generated
    roi_percent: float
    time_saved_hours: float
    cost_per_case: float
    value_per_case: float
    break_even_cases: int


@dataclass
class SuccessPrediction:
    """Success prediction for a task"""
    task_description: str
    predicted_success_prob: float
    confidence: float
    contributing_factors: Dict[str, float]
    similar_cases_count: int
    recommended_approach: Optional[str]


class BusinessIntelligenceEngine:
    """
    Enterprise business intelligence and analytics engine

    Features:
    - Real-time KPI tracking
    - Trend analysis and forecasting
    - ROI and value attribution
    - Success prediction models
    - Cost optimization analytics
    - Performance attribution
    - Causal impact analysis
    - Executive reporting
    """

    def __init__(
        self,
        cost_per_case: float = 0.10,  # Default cost per case stored
        value_per_hour_saved: float = 50.0  # Default value of time saved
    ):
        self.cost_per_case = cost_per_case
        self.value_per_hour_saved = value_per_hour_saved

        # Historical data
        self.case_history: List[Case] = []
        self.kpi_history: List[KPIMetrics] = []
        self.retrieval_history: List[Dict[str, Any]] = []

        # Analytics cache
        self.cached_trends: Dict[str, TrendAnalysis] = {}
        self.last_analytics_update = datetime.utcnow()

    def calculate_kpis(
        self,
        cases: List[Case],
        retrievals: List[Dict[str, Any]],
        period_days: int = 30
    ) -> KPIMetrics:
        """Calculate comprehensive KPIs for the learning system"""
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        previous_cutoff = cutoff - timedelta(days=period_days)

        # Filter cases by period
        current_period = [c for c in cases if c.created_at >= cutoff]
        previous_period = [c for c in cases if previous_cutoff <= c.created_at < cutoff]

        # Volume metrics
        total_cases = len(cases)
        cases_this_period = len(current_period)
        cases_previous = len(previous_period)

        if cases_previous > 0:
            cases_growth_rate = (cases_this_period - cases_previous) / cases_previous
        else:
            cases_growth_rate = 0.0

        # Quality metrics
        if current_period:
            avg_quality = sum(c.reward.score for c in current_period) / len(current_period)
            high_quality_count = sum(1 for c in current_period if c.reward.score >= 0.7)
            high_quality_ratio = high_quality_count / len(current_period)

            # Quality trend
            if previous_period:
                prev_avg = sum(c.reward.score for c in previous_period) / len(previous_period)
                if avg_quality > prev_avg + 0.05:
                    quality_trend = "improving"
                elif avg_quality < prev_avg - 0.05:
                    quality_trend = "declining"
                else:
                    quality_trend = "stable"
            else:
                quality_trend = "stable"
        else:
            avg_quality = 0.0
            high_quality_ratio = 0.0
            quality_trend = "stable"

        # Usage metrics
        recent_retrievals = [r for r in retrievals if r.get('timestamp', cutoff) >= cutoff]
        total_retrievals = len(recent_retrievals)

        if recent_retrievals:
            successful = sum(1 for r in recent_retrievals if r.get('success', False))
            retrieval_success_rate = successful / len(recent_retrievals)

            total_cases_retrieved = sum(r.get('cases_returned', 0) for r in recent_retrievals)
            avg_cases_per_retrieval = total_cases_retrieved / len(recent_retrievals)
        else:
            retrieval_success_rate = 0.0
            avg_cases_per_retrieval = 0.0

        # Value metrics
        roi_calc = self.calculate_roi(cases, period_days)
        estimated_roi = roi_calc.roi_percent
        time_saved = roi_calc.time_saved_hours
        cost_savings = roi_calc.total_return - roi_calc.total_investment

        # Performance metrics
        if recent_retrievals:
            latencies = [r.get('latency_ms', 0) for r in recent_retrievals]
            avg_retrieval_latency = sum(latencies) / len(latencies) if latencies else 0.0
        else:
            avg_retrieval_latency = 0.0

        kpi = KPIMetrics(
            total_cases=total_cases,
            cases_this_period=cases_this_period,
            cases_growth_rate=cases_growth_rate,
            avg_case_quality=avg_quality,
            quality_trend=quality_trend,
            high_quality_ratio=high_quality_ratio,
            total_retrievals=total_retrievals,
            retrieval_success_rate=retrieval_success_rate,
            avg_cases_per_retrieval=avg_cases_per_retrieval,
            estimated_roi=estimated_roi,
            time_saved_hours=time_saved,
            cost_savings=cost_savings,
            avg_retrieval_latency_ms=avg_retrieval_latency
        )

        # Store for trend analysis
        self.kpi_history.append(kpi)

        return kpi

    def calculate_roi(
        self,
        cases: List[Case],
        period_days: int = 30
    ) -> ROICalculation:
        """
        Calculate Return on Investment for the learning system

        Factors:
        - Cost: Storage, compute, maintenance
        - Return: Time saved, quality improvements, automation
        """
        period_start = datetime.utcnow() - timedelta(days=period_days)
        period_end = datetime.utcnow()

        # Filter cases to period
        period_cases = [c for c in cases if c.created_at >= period_start]

        # Calculate investment (costs)
        total_cases_stored = len(cases)
        storage_cost = total_cases_stored * self.cost_per_case

        # Estimate compute cost (simplified)
        compute_cost = len(period_cases) * 0.05  # $0.05 per case processed

        total_investment = storage_cost + compute_cost

        # Calculate return (value)
        # 1. Time saved from reusing cases
        successful_cases = [c for c in period_cases if c.reward.score >= 0.6]
        avg_steps_per_case = sum(len(c.steps) for c in successful_cases) / len(successful_cases) if successful_cases else 5
        time_per_step_minutes = 10  # Average time per step
        time_saved_hours = (len(successful_cases) * avg_steps_per_case * time_per_step_minutes) / 60

        # 2. Value of time saved
        time_value = time_saved_hours * self.value_per_hour_saved

        # 3. Quality improvement value (avoid rework)
        high_quality_cases = [c for c in period_cases if c.reward.score >= 0.8]
        rework_avoided = len(high_quality_cases) * 2 * self.value_per_hour_saved  # 2 hours per rework avoided

        total_return = time_value + rework_avoided

        # Calculate ROI
        if total_investment > 0:
            roi_percent = ((total_return - total_investment) / total_investment) * 100
        else:
            roi_percent = 0.0

        # Cost and value per case
        cost_per_case = total_investment / len(period_cases) if period_cases else 0.0
        value_per_case = total_return / len(period_cases) if period_cases else 0.0

        # Break-even analysis
        if value_per_case > cost_per_case:
            break_even_cases = int(total_investment / (value_per_case - cost_per_case))
        else:
            break_even_cases = 0

        return ROICalculation(
            period_start=period_start,
            period_end=period_end,
            total_investment=total_investment,
            total_return=total_return,
            roi_percent=roi_percent,
            time_saved_hours=time_saved_hours,
            cost_per_case=cost_per_case,
            value_per_case=value_per_case,
            break_even_cases=break_even_cases
        )

    def analyze_trends(
        self,
        metric_name: str,
        lookback_periods: int = 10
    ) -> TrendAnalysis:
        """
        Analyze trends for a specific metric

        Uses time series analysis to detect trends and forecast future values
        """
        if len(self.kpi_history) < 2:
            # Not enough data for trend analysis
            return TrendAnalysis(
                metric_name=metric_name,
                current_value=0.0,
                previous_value=0.0,
                change_percent=0.0,
                trend_direction="stable",
                forecast_next_period=0.0,
                confidence_interval=(0.0, 0.0),
                anomalies_detected=[]
            )

        # Extract metric values from history
        recent_kpis = self.kpi_history[-lookback_periods:]
        values = [getattr(kpi, metric_name, 0.0) for kpi in recent_kpis]

        current_value = values[-1]
        previous_value = values[-2] if len(values) >= 2 else current_value

        # Calculate change
        if previous_value != 0:
            change_percent = ((current_value - previous_value) / previous_value) * 100
        else:
            change_percent = 0.0

        # Determine trend direction
        if change_percent > 5:
            trend_direction = "up"
        elif change_percent < -5:
            trend_direction = "down"
        else:
            trend_direction = "stable"

        # Simple linear forecast
        if len(values) >= 3:
            x = np.arange(len(values))
            coeffs = np.polyfit(x, values, 1)
            forecast_next = coeffs[0] * len(values) + coeffs[1]

            # Calculate confidence interval (simplified)
            residuals = values - (coeffs[0] * x + coeffs[1])
            std_error = np.std(residuals)
            confidence_interval = (
                forecast_next - 1.96 * std_error,
                forecast_next + 1.96 * std_error
            )
        else:
            forecast_next = current_value
            confidence_interval = (current_value * 0.9, current_value * 1.1)

        # Detect anomalies (values > 2 std deviations)
        anomalies = []
        if len(values) >= 5:
            mean = np.mean(values)
            std = np.std(values)
            for i, v in enumerate(values):
                if abs(v - mean) > 2 * std:
                    anomalies.append(f"Period {i}: {v:.2f} (outlier)")

        return TrendAnalysis(
            metric_name=metric_name,
            current_value=current_value,
            previous_value=previous_value,
            change_percent=change_percent,
            trend_direction=trend_direction,
            forecast_next_period=forecast_next,
            confidence_interval=confidence_interval,
            anomalies_detected=anomalies
        )

    def predict_success(
        self,
        task_description: str,
        similar_cases: List[Case],
        context: Optional[Dict[str, Any]] = None
    ) -> SuccessPrediction:
        """
        Predict likelihood of success for a task

        Uses historical similar cases to predict outcome
        """
        if not similar_cases:
            return SuccessPrediction(
                task_description=task_description,
                predicted_success_prob=0.5,
                confidence=0.0,
                contributing_factors={},
                similar_cases_count=0,
                recommended_approach=None
            )

        # Calculate success probability from similar cases
        success_cases = [c for c in similar_cases if c.reward.score >= 0.6]
        predicted_prob = len(success_cases) / len(similar_cases)

        # Calculate confidence based on sample size and consistency
        confidence = min(len(similar_cases) / 20, 1.0)  # More cases = higher confidence
        reward_std = np.std([c.reward.score for c in similar_cases])
        confidence *= (1.0 - reward_std)  # Lower variance = higher confidence

        # Analyze contributing factors
        factors = {}

        # Factor 1: Historical success rate
        factors['historical_success_rate'] = predicted_prob

        # Factor 2: Recent performance trend
        if len(similar_cases) >= 5:
            recent_rewards = [c.reward.score for c in similar_cases[-5:]]
            older_rewards = [c.reward.score for c in similar_cases[:-5]]
            if older_rewards:
                trend = np.mean(recent_rewards) - np.mean(older_rewards)
                factors['performance_trend'] = max(-1.0, min(1.0, trend * 2))

        # Factor 3: Complexity match
        if context and context.get('expected_steps'):
            expected_steps = context['expected_steps']
            avg_steps = np.mean([len(c.steps) for c in similar_cases])
            complexity_match = 1.0 - abs(expected_steps - avg_steps) / max(expected_steps, avg_steps, 1)
            factors['complexity_match'] = complexity_match

        # Recommend best approach
        if success_cases:
            best_case = max(success_cases, key=lambda c: c.reward.score)
            if best_case.plan_text:
                recommended_approach = best_case.plan_text[:200] + "..."
            else:
                recommended_approach = "Follow patterns from similar high-performing cases"
        else:
            recommended_approach = None

        return SuccessPrediction(
            task_description=task_description,
            predicted_success_prob=predicted_prob,
            confidence=confidence,
            contributing_factors=factors,
            similar_cases_count=len(similar_cases),
            recommended_approach=recommended_approach
        )

    def attribute_performance(
        self,
        cases: List[Case],
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Attribute performance improvements to specific factors

        Analyzes what drives success: tags, tools, users, time periods, etc.
        """
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        recent_cases = [c for c in cases if c.created_at >= cutoff]

        if not recent_cases:
            return {}

        attribution = {}

        # 1. Tag attribution
        tag_performance = defaultdict(lambda: {'count': 0, 'total_reward': 0.0})
        for case in recent_cases:
            for tag in case.tags:
                tag_performance[tag]['count'] += 1
                tag_performance[tag]['total_reward'] += case.reward.score

        tag_attribution = {
            tag: perf['total_reward'] / perf['count']
            for tag, perf in tag_performance.items()
            if perf['count'] >= 3
        }
        attribution['by_tag'] = dict(sorted(tag_attribution.items(), key=lambda x: x[1], reverse=True)[:10])

        # 2. Tool attribution
        tool_performance = defaultdict(lambda: {'count': 0, 'total_reward': 0.0})
        for case in recent_cases:
            tools_used = {step.tool_io.tool_name for step in case.steps if step.tool_io}
            for tool in tools_used:
                tool_performance[tool]['count'] += 1
                tool_performance[tool]['total_reward'] += case.reward.score

        tool_attribution = {
            tool: perf['total_reward'] / perf['count']
            for tool, perf in tool_performance.items()
            if perf['count'] >= 3
        }
        attribution['by_tool'] = dict(sorted(tool_attribution.items(), key=lambda x: x[1], reverse=True)[:10])

        # 3. Temporal attribution (day of week, time of day)
        day_performance = defaultdict(lambda: {'count': 0, 'total_reward': 0.0})
        for case in recent_cases:
            day = case.created_at.strftime('%A')
            day_performance[day]['count'] += 1
            day_performance[day]['total_reward'] += case.reward.score

        day_attribution = {
            day: perf['total_reward'] / perf['count']
            for day, perf in day_performance.items()
        }
        attribution['by_day_of_week'] = day_attribution

        # 4. Complexity attribution
        complexity_buckets = {
            'simple': {'count': 0, 'total_reward': 0.0},
            'moderate': {'count': 0, 'total_reward': 0.0},
            'complex': {'count': 0, 'total_reward': 0.0}
        }
        for case in recent_cases:
            steps = len(case.steps)
            if steps <= 3:
                bucket = 'simple'
            elif steps <= 7:
                bucket = 'moderate'
            else:
                bucket = 'complex'

            complexity_buckets[bucket]['count'] += 1
            complexity_buckets[bucket]['total_reward'] += case.reward.score

        complexity_attribution = {
            bucket: perf['total_reward'] / perf['count']
            for bucket, perf in complexity_buckets.items()
            if perf['count'] > 0
        }
        attribution['by_complexity'] = complexity_attribution

        return attribution

    def generate_executive_report(
        self,
        cases: List[Case],
        retrievals: List[Dict[str, Any]],
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate comprehensive executive report

        Provides high-level summary for business stakeholders
        """
        kpis = self.calculate_kpis(cases, retrievals, period_days)
        roi = self.calculate_roi(cases, period_days)
        attribution = self.attribute_performance(cases, period_days)

        # Key trends
        trends = {
            'quality': self.analyze_trends('avg_case_quality'),
            'volume': self.analyze_trends('cases_this_period'),
            'usage': self.analyze_trends('total_retrievals')
        }

        return {
            'report_period': {
                'start': (datetime.utcnow() - timedelta(days=period_days)).isoformat(),
                'end': datetime.utcnow().isoformat(),
                'days': period_days
            },
            'executive_summary': {
                'total_cases': kpis.total_cases,
                'period_growth': f"{kpis.cases_growth_rate:+.1%}",
                'avg_quality': f"{kpis.avg_case_quality:.2f}/1.0",
                'quality_trend': kpis.quality_trend,
                'roi': f"{roi.roi_percent:+.1f}%",
                'time_saved': f"{roi.time_saved_hours:.1f} hours",
                'cost_savings': f"${roi.total_return - roi.total_investment:,.2f}"
            },
            'key_metrics': {
                'volume': {
                    'current': kpis.cases_this_period,
                    'trend': trends['volume'].trend_direction,
                    'forecast': f"{trends['volume'].forecast_next_period:.0f} cases"
                },
                'quality': {
                    'current': kpis.avg_case_quality,
                    'high_quality_ratio': f"{kpis.high_quality_ratio:.1%}",
                    'trend': trends['quality'].trend_direction
                },
                'usage': {
                    'retrievals': kpis.total_retrievals,
                    'success_rate': f"{kpis.retrieval_success_rate:.1%}",
                    'trend': trends['usage'].trend_direction
                },
                'performance': {
                    'avg_latency_ms': kpis.avg_retrieval_latency_ms,
                    'uptime': f"{kpis.system_uptime_percent:.2f}%"
                }
            },
            'financial_impact': {
                'total_investment': f"${roi.total_investment:,.2f}",
                'total_return': f"${roi.total_return:,.2f}",
                'net_value': f"${roi.total_return - roi.total_investment:,.2f}",
                'roi_percent': f"{roi.roi_percent:+.1f}%",
                'cost_per_case': f"${roi.cost_per_case:.2f}",
                'value_per_case': f"${roi.value_per_case:.2f}",
                'break_even_cases': roi.break_even_cases
            },
            'performance_drivers': {
                'top_tags': list(attribution.get('by_tag', {}).items())[:5],
                'top_tools': list(attribution.get('by_tool', {}).items())[:5],
                'best_day': max(attribution.get('by_day_of_week', {}).items(), key=lambda x: x[1])[0] if attribution.get('by_day_of_week') else 'N/A',
                'optimal_complexity': max(attribution.get('by_complexity', {}).items(), key=lambda x: x[1])[0] if attribution.get('by_complexity') else 'N/A'
            },
            'recommendations': self._generate_recommendations(kpis, roi, trends)
        }

    def _generate_recommendations(
        self,
        kpis: KPIMetrics,
        roi: ROICalculation,
        trends: Dict[str, TrendAnalysis]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Quality recommendations
        if kpis.avg_case_quality < 0.6:
            recommendations.append("PRIORITY: Improve case quality through better reward signals and filtering")
        elif kpis.quality_trend == "declining":
            recommendations.append("Address declining quality trend - review admission policies")

        # ROI recommendations
        if roi.roi_percent < 100:
            recommendations.append("ROI below target - focus on high-value use cases to improve returns")
        elif roi.roi_percent > 300:
            recommendations.append("Excellent ROI - consider expanding system capacity")

        # Usage recommendations
        if kpis.retrieval_success_rate < 0.7:
            recommendations.append("Improve retrieval success rate through better indexing and ranking")

        # Growth recommendations
        if kpis.cases_growth_rate < 0:
            recommendations.append("Case volume declining - investigate adoption barriers")
        elif kpis.cases_growth_rate > 0.5:
            recommendations.append("Strong growth - ensure infrastructure can scale")

        # Performance recommendations
        if kpis.avg_retrieval_latency_ms > 1000:
            recommendations.append("High retrieval latency - optimize vector search and caching")

        return recommendations


# Global BI engine instance
_global_bi_engine: Optional[BusinessIntelligenceEngine] = None

def get_bi_engine() -> BusinessIntelligenceEngine:
    """Get global business intelligence engine instance"""
    global _global_bi_engine
    if _global_bi_engine is None:
        _global_bi_engine = BusinessIntelligenceEngine()
    return _global_bi_engine
