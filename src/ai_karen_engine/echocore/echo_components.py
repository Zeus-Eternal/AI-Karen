"""
Echo Components - Analyzer, Synthesizer, and Pipeline
Advanced components for pattern analysis, insight generation, and workflow orchestration.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
import asyncio

from ai_karen_engine.echocore.enhanced_dark_tracker import EnhancedDarkTracker, EventSeverity
from ai_karen_engine.echocore.enhanced_echo_vault import EnhancedEchoVault
from ai_karen_engine.echocore.production_fine_tuner import ProductionFineTuner

logger = logging.getLogger(__name__)


@dataclass
class EchoPattern:
    """Represents a discovered pattern in echo data."""
    pattern_type: str
    description: str
    frequency: int
    confidence: float
    first_seen: str
    last_seen: str
    examples: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class EchoInsight:
    """Represents a synthesized insight from echo analysis."""
    insight_id: str
    category: str
    title: str
    description: str
    importance: float  # 0-1 scale
    actionable: bool
    recommendations: List[str]
    supporting_data: Dict[str, Any]
    generated_at: str


class EchoAnalyzer:
    """
    Analyzes echo data to discover patterns and anomalies.

    Features:
    - Pattern discovery
    - Anomaly detection
    - Trend analysis
    - User behavior modeling
    - Performance analysis
    - Error pattern detection
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._pattern_cache: Dict[str, EchoPattern] = {}

    async def analyze_events(
        self,
        tracker: EnhancedDarkTracker,
        lookback_days: int = 7
    ) -> Dict[str, Any]:
        """
        Analyze events from tracker.

        Args:
            tracker: Dark tracker instance
            lookback_days: Number of days to analyze

        Returns:
            Analysis results
        """
        start_time = datetime.utcnow() - timedelta(days=lookback_days)

        # Get events
        events = await tracker.query_events(start_time=start_time, limit=10000)

        if not events:
            return {"status": "no_data", "message": "No events to analyze"}

        # Perform analyses
        patterns = await self._discover_patterns(events)
        anomalies = await self._detect_anomalies(events)
        trends = await self._analyze_trends(events)
        user_behavior = await self._model_user_behavior(events)

        return {
            "status": "success",
            "analyzed_events": len(events),
            "time_range": {
                "start": start_time.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "patterns": [asdict(p) for p in patterns],
            "anomalies": anomalies,
            "trends": trends,
            "user_behavior": user_behavior
        }

    async def _discover_patterns(self, events: List[Dict]) -> List[EchoPattern]:
        """Discover patterns in events."""
        patterns = []

        # Pattern 1: Frequent event types
        event_types = Counter(e.get("type") for e in events if e.get("type"))
        for event_type, count in event_types.most_common(10):
            if count >= 5:  # Threshold for pattern
                examples = [e for e in events if e.get("type") == event_type][:3]
                timestamps = [e.get("ts") for e in examples if e.get("ts")]

                pattern = EchoPattern(
                    pattern_type="frequent_event",
                    description=f"Frequent {event_type} events",
                    frequency=count,
                    confidence=min(count / len(events), 1.0),
                    first_seen=min(timestamps) if timestamps else "",
                    last_seen=max(timestamps) if timestamps else "",
                    examples=examples,
                    metadata={"event_type": event_type}
                )
                patterns.append(pattern)

        # Pattern 2: Error clusters
        errors = [e for e in events if e.get("severity") in ["error", "critical"]]
        if errors:
            error_types = Counter(e.get("type") for e in errors)
            for error_type, count in error_types.most_common(5):
                pattern = EchoPattern(
                    pattern_type="error_cluster",
                    description=f"Cluster of {error_type} errors",
                    frequency=count,
                    confidence=0.9,
                    first_seen=errors[0].get("ts", ""),
                    last_seen=errors[-1].get("ts", ""),
                    examples=errors[:3],
                    metadata={"error_type": error_type, "total_errors": len(errors)}
                )
                patterns.append(pattern)

        # Pattern 3: Time-based patterns
        hourly_events = defaultdict(int)
        for event in events:
            try:
                ts = datetime.fromisoformat(event["ts"])
                hour = ts.hour
                hourly_events[hour] += 1
            except (KeyError, ValueError):
                continue

        if hourly_events:
            peak_hour = max(hourly_events.items(), key=lambda x: x[1])
            if peak_hour[1] >= len(events) * 0.2:  # 20% of events in one hour
                pattern = EchoPattern(
                    pattern_type="temporal_pattern",
                    description=f"Peak activity at hour {peak_hour[0]}",
                    frequency=peak_hour[1],
                    confidence=0.8,
                    first_seen="",
                    last_seen="",
                    examples=[],
                    metadata={"peak_hour": peak_hour[0], "hourly_distribution": dict(hourly_events)}
                )
                patterns.append(pattern)

        self._pattern_cache = {p.pattern_type: p for p in patterns}
        return patterns

    async def _detect_anomalies(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Detect anomalies in events."""
        anomalies = []

        # Anomaly 1: Sudden spike in error rate
        errors = [e for e in events if e.get("severity") in ["error", "critical"]]
        error_rate = len(errors) / len(events) if events else 0

        if error_rate > 0.1:  # More than 10% errors
            anomalies.append({
                "type": "high_error_rate",
                "description": f"High error rate detected: {error_rate:.2%}",
                "severity": "warning" if error_rate < 0.2 else "critical",
                "details": {
                    "error_count": len(errors),
                    "total_events": len(events),
                    "error_rate": error_rate
                }
            })

        # Anomaly 2: Missing events (gaps in timeline)
        if len(events) >= 2:
            timestamps = sorted([
                datetime.fromisoformat(e["ts"])
                for e in events if e.get("ts")
            ])

            for i in range(1, len(timestamps)):
                gap = (timestamps[i] - timestamps[i-1]).total_seconds()
                if gap > 3600:  # 1 hour gap
                    anomalies.append({
                        "type": "event_gap",
                        "description": f"Large gap in events: {gap/3600:.1f} hours",
                        "severity": "info",
                        "details": {
                            "gap_seconds": gap,
                            "start": timestamps[i-1].isoformat(),
                            "end": timestamps[i].isoformat()
                        }
                    })

        return anomalies

    async def _analyze_trends(self, events: List[Dict]) -> Dict[str, Any]:
        """Analyze trends in events."""
        # Group events by day
        daily_counts = defaultdict(int)
        for event in events:
            try:
                ts = datetime.fromisoformat(event["ts"])
                day = ts.strftime("%Y-%m-%d")
                daily_counts[day] += 1
            except (KeyError, ValueError):
                continue

        sorted_days = sorted(daily_counts.items())

        if len(sorted_days) < 2:
            return {"trend": "insufficient_data"}

        # Calculate trend
        counts = [c for _, c in sorted_days]
        avg_first_half = sum(counts[:len(counts)//2]) / (len(counts)//2)
        avg_second_half = sum(counts[len(counts)//2:]) / (len(counts) - len(counts)//2)

        trend_direction = "increasing" if avg_second_half > avg_first_half else "decreasing"
        trend_magnitude = abs(avg_second_half - avg_first_half) / avg_first_half if avg_first_half > 0 else 0

        return {
            "trend": trend_direction,
            "magnitude": trend_magnitude,
            "daily_counts": dict(sorted_days),
            "avg_events_per_day": sum(counts) / len(counts)
        }

    async def _model_user_behavior(self, events: List[Dict]) -> Dict[str, Any]:
        """Model user behavior from events."""
        # Activity patterns
        activity_by_type = Counter(e.get("type") for e in events if e.get("type"))

        # Interaction frequency
        if events:
            timestamps = [
                datetime.fromisoformat(e["ts"])
                for e in events if e.get("ts")
            ]
            if len(timestamps) >= 2:
                time_span = (max(timestamps) - min(timestamps)).total_seconds()
                avg_interval = time_span / len(timestamps) if len(timestamps) > 1 else 0
            else:
                avg_interval = 0
        else:
            avg_interval = 0

        return {
            "total_interactions": len(events),
            "activity_distribution": dict(activity_by_type.most_common(10)),
            "avg_interval_seconds": avg_interval,
            "active_days": len(set(
                datetime.fromisoformat(e["ts"]).strftime("%Y-%m-%d")
                for e in events if e.get("ts")
            ))
        }


class EchoSynthesizer:
    """
    Synthesizes insights from analyzed echo data.

    Features:
    - Generate actionable insights
    - Recommend improvements
    - Identify opportunities
    - Risk assessment
    - Personalization suggestions
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def synthesize_insights(
        self,
        analysis_results: Dict[str, Any],
        vault_data: Optional[Dict[str, Any]] = None
    ) -> List[EchoInsight]:
        """
        Synthesize insights from analysis results.

        Args:
            analysis_results: Results from EchoAnalyzer
            vault_data: Optional user vault data for context

        Returns:
            List of insights
        """
        insights = []

        # Insight from patterns
        if "patterns" in analysis_results:
            for pattern_data in analysis_results["patterns"]:
                if pattern_data["pattern_type"] == "error_cluster":
                    insight = EchoInsight(
                        insight_id=f"insight_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        category="reliability",
                        title="Error Cluster Detected",
                        description=f"Multiple {pattern_data['metadata'].get('error_type')} errors observed",
                        importance=0.9,
                        actionable=True,
                        recommendations=[
                            "Review error logs for root cause",
                            "Implement better error handling",
                            "Add monitoring alerts"
                        ],
                        supporting_data=pattern_data,
                        generated_at=datetime.utcnow().isoformat()
                    )
                    insights.append(insight)

        # Insight from anomalies
        if "anomalies" in analysis_results:
            for anomaly in analysis_results["anomalies"]:
                if anomaly["type"] == "high_error_rate":
                    insight = EchoInsight(
                        insight_id=f"insight_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_anom",
                        category="performance",
                        title="High Error Rate",
                        description=anomaly["description"],
                        importance=1.0 if anomaly["severity"] == "critical" else 0.7,
                        actionable=True,
                        recommendations=[
                            "Investigate recent changes",
                            "Check system resources",
                            "Review error logs"
                        ],
                        supporting_data=anomaly,
                        generated_at=datetime.utcnow().isoformat()
                    )
                    insights.append(insight)

        # Insight from trends
        if "trends" in analysis_results:
            trends = analysis_results["trends"]
            if trends.get("trend") == "increasing" and trends.get("magnitude", 0) > 0.5:
                insight = EchoInsight(
                    insight_id=f"insight_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_trend",
                    category="growth",
                    title="Growing User Activity",
                    description=f"User activity increasing by {trends['magnitude']:.1%}",
                    importance=0.8,
                    actionable=True,
                    recommendations=[
                        "Scale infrastructure",
                        "Optimize performance",
                        "Prepare for increased load"
                    ],
                    supporting_data=trends,
                    generated_at=datetime.utcnow().isoformat()
                )
                insights.append(insight)

        # Insight from user behavior
        if "user_behavior" in analysis_results:
            behavior = analysis_results["user_behavior"]
            if behavior.get("total_interactions", 0) > 100:
                insight = EchoInsight(
                    insight_id=f"insight_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_engage",
                    category="engagement",
                    title="High User Engagement",
                    description=f"{behavior['total_interactions']} interactions recorded",
                    importance=0.6,
                    actionable=False,
                    recommendations=[
                        "Maintain current experience",
                        "Gather user feedback",
                        "Consider feature expansion"
                    ],
                    supporting_data=behavior,
                    generated_at=datetime.utcnow().isoformat()
                )
                insights.append(insight)

        return insights


class EchoPipeline:
    """
    Orchestrates the complete echo workflow.

    Features:
    - End-to-end echo processing
    - Coordinated analysis and synthesis
    - Automated fine-tuning triggers
    - Report generation
    - Scheduled execution
    """

    def __init__(
        self,
        user_id: str,
        base_dir: Path = Path("data/users")
    ):
        self.user_id = user_id
        self.base_dir = Path(base_dir)

        # Initialize components
        self.vault = EnhancedEchoVault(user_id, base_dir)
        self.tracker = EnhancedDarkTracker(user_id, base_dir)
        self.analyzer = EchoAnalyzer()
        self.synthesizer = EchoSynthesizer()

        self.logger = logging.getLogger(__name__)

    async def run_full_pipeline(
        self,
        lookback_days: int = 7,
        generate_report: bool = True,
        trigger_fine_tuning: bool = False,
        model_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the complete echo pipeline.

        Args:
            lookback_days: Days of data to analyze
            generate_report: Whether to generate a report
            trigger_fine_tuning: Whether to trigger model fine-tuning
            model_path: Path to model for fine-tuning

        Returns:
            Pipeline results
        """
        self.logger.info(f"Starting echo pipeline for user {self.user_id}")

        results = {
            "user_id": self.user_id,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "status": "running"
        }

        try:
            # Step 1: Analyze events
            self.logger.info("Step 1: Analyzing events")
            analysis = await self.analyzer.analyze_events(self.tracker, lookback_days)
            results["analysis"] = analysis

            # Step 2: Synthesize insights
            self.logger.info("Step 2: Synthesizing insights")
            vault_data = await self.vault.restore()
            insights = await self.synthesizer.synthesize_insights(analysis, vault_data)
            results["insights"] = [asdict(i) for i in insights]

            # Step 3: Update vault with insights
            self.logger.info("Step 3: Updating vault")
            vault_update = {
                "last_analysis": datetime.utcnow().isoformat(),
                "insight_count": len(insights),
                "patterns_discovered": len(analysis.get("patterns", []))
            }
            await self.vault.backup(vault_update, create_snapshot=True)

            # Step 4: Generate report if requested
            if generate_report:
                self.logger.info("Step 4: Generating report")
                report = await self._generate_report(analysis, insights)
                results["report"] = report

            # Step 5: Trigger fine-tuning if requested
            if trigger_fine_tuning and model_path:
                self.logger.info("Step 5: Triggering fine-tuning")
                fine_tuner = ProductionFineTuner(
                    logs_path=self.tracker.current_log,
                    output_dir=self.base_dir / self.user_id / "models"
                )
                training_run = await fine_tuner.fine_tune(model_path)
                results["fine_tuning"] = asdict(training_run)

            results["status"] = "completed"
            results["completed_at"] = datetime.utcnow().isoformat()

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            results["completed_at"] = datetime.utcnow().isoformat()
            self.logger.error(f"Pipeline failed: {e}")

        return results

    async def _generate_report(
        self,
        analysis: Dict[str, Any],
        insights: List[EchoInsight]
    ) -> Dict[str, Any]:
        """Generate a summary report."""
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_events_analyzed": analysis.get("analyzed_events", 0),
                "patterns_found": len(analysis.get("patterns", [])),
                "anomalies_detected": len(analysis.get("anomalies", [])),
                "insights_generated": len(insights),
                "high_priority_insights": len([i for i in insights if i.importance >= 0.8])
            },
            "key_insights": [
                {
                    "title": i.title,
                    "category": i.category,
                    "importance": i.importance,
                    "actionable": i.actionable
                }
                for i in sorted(insights, key=lambda x: x.importance, reverse=True)[:5]
            ],
            "recommendations": [
                rec
                for i in insights if i.actionable
                for rec in i.recommendations
            ][:10]
        }


__all__ = [
    "EchoPattern",
    "EchoInsight",
    "EchoAnalyzer",
    "EchoSynthesizer",
    "EchoPipeline"
]
