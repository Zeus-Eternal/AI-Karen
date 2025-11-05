"""
Long-Term Memory - OLAP analytics using existing DuckDBClient

Provides analytical queries over historical user data.
Uses DuckDB for OLAP workloads: trends, patterns, aggregations.
Integrates with existing DuckDBClient infrastructure.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsQuery:
    """Represents an analytics query."""
    query_type: str  # "trend", "aggregate", "pattern", "timeseries"
    time_range: Dict[str, str]  # {"start": "ISO8601", "end": "ISO8601"}
    filters: Dict[str, Any]
    group_by: Optional[List[str]] = None
    metrics: Optional[List[str]] = None


@dataclass
class TrendAnalysis:
    """Result of trend analysis."""
    metric: str
    period: str
    data_points: List[Dict[str, Any]]
    trend: str  # "increasing", "decreasing", "stable"
    change_percent: float
    summary: str


class LongTermMemory:
    """
    Long-term memory using existing DuckDBClient.

    Features:
    - OLAP analytics for historical data
    - Trend analysis over time
    - Aggregated statistics
    - Pattern detection
    - Time-series queries
    """

    def __init__(
        self,
        user_id: str,
        duckdb_client: Optional[Any] = None
    ):
        self.user_id = user_id
        self.duckdb_client = duckdb_client

        # Determine if using fallback
        self._using_fallback = duckdb_client is None

        # Fallback: in-memory storage
        self._fallback_records: List[Dict[str, Any]] = []

        # Metrics
        self._total_queries = 0

        logger.info(f"LongTermMemory initialized for user {user_id} (fallback={self._using_fallback})")

    async def store_interaction(
        self,
        interaction_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store an interaction record for long-term analytics.

        Args:
            interaction_type: Type of interaction (e.g., "query", "response", "action")
            content: Interaction content
            metadata: Optional metadata

        Returns:
            Stored record
        """
        record = {
            "user_id": self.user_id,
            "interaction_type": interaction_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        if self._using_fallback:
            await self._store_fallback(record)
        else:
            await self._store_duckdb(record)

        logger.debug(f"Stored interaction: {interaction_type}")
        return record

    async def _store_duckdb(self, record: Dict[str, Any]) -> None:
        """Store record using DuckDBClient."""
        # DuckDBClient uses long_term_memory table
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.duckdb_client._get_conn().execute,
            """
            INSERT INTO long_term_memory (user_id, memory_json)
            VALUES (?, ?)
            """,
            (record["user_id"], json.dumps(record))
        )

    async def _store_fallback(self, record: Dict[str, Any]) -> None:
        """Store record in fallback in-memory storage."""
        self._fallback_records.append(record)

    async def query_trends(
        self,
        metric: str,
        period: str = "daily",
        days: int = 30
    ) -> TrendAnalysis:
        """
        Analyze trends for a specific metric over time.

        Args:
            metric: Metric to analyze (e.g., "query_count", "interaction_count")
            period: Aggregation period ("hourly", "daily", "weekly")
            days: Number of days to analyze

        Returns:
            TrendAnalysis with trend data
        """
        self._total_queries += 1

        start_time = datetime.utcnow() - timedelta(days=days)

        if self._using_fallback:
            return await self._analyze_trends_fallback(metric, period, start_time)
        else:
            return await self._analyze_trends_duckdb(metric, period, start_time)

    async def _analyze_trends_duckdb(
        self,
        metric: str,
        period: str,
        start_time: datetime
    ) -> TrendAnalysis:
        """Analyze trends using DuckDB."""
        loop = asyncio.get_event_loop()

        # Query for time series data
        query = f"""
        SELECT
            strftime(timestamp, '%Y-%m-%d') as period,
            COUNT(*) as count
        FROM long_term_memory
        WHERE user_id = ? AND timestamp >= ?
        GROUP BY period
        ORDER BY period
        """

        try:
            conn = await loop.run_in_executor(
                None,
                self.duckdb_client._get_conn
            )
            results = await loop.run_in_executor(
                None,
                conn.execute(query, (self.user_id, start_time.isoformat())).fetchall
            )

            data_points = [
                {"period": row[0], "value": row[1]}
                for row in results
            ]

        except Exception as e:
            logger.error(f"DuckDB trend query failed: {e}")
            data_points = []

        return self._calculate_trend(metric, period, data_points)

    async def _analyze_trends_fallback(
        self,
        metric: str,
        period: str,
        start_time: datetime
    ) -> TrendAnalysis:
        """Analyze trends using fallback in-memory storage."""
        # Filter records by time range
        filtered = [
            r for r in self._fallback_records
            if datetime.fromisoformat(r["timestamp"]) >= start_time
        ]

        # Group by period
        from collections import defaultdict
        period_counts = defaultdict(int)

        for record in filtered:
            timestamp = datetime.fromisoformat(record["timestamp"])
            if period == "daily":
                key = timestamp.strftime("%Y-%m-%d")
            elif period == "weekly":
                key = timestamp.strftime("%Y-W%W")
            elif period == "hourly":
                key = timestamp.strftime("%Y-%m-%d %H:00")
            else:
                key = timestamp.strftime("%Y-%m-%d")

            period_counts[key] += 1

        # Convert to data points
        data_points = [
            {"period": period, "value": count}
            for period, count in sorted(period_counts.items())
        ]

        return self._calculate_trend(metric, period, data_points)

    def _calculate_trend(
        self,
        metric: str,
        period: str,
        data_points: List[Dict[str, Any]]
    ) -> TrendAnalysis:
        """Calculate trend from data points."""
        if not data_points:
            return TrendAnalysis(
                metric=metric,
                period=period,
                data_points=[],
                trend="stable",
                change_percent=0.0,
                summary="No data available"
            )

        # Calculate trend
        values = [dp["value"] for dp in data_points]
        first_half_avg = sum(values[:len(values)//2]) / (len(values)//2) if len(values) >= 2 else values[0]
        second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)

        change_percent = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0.0

        if change_percent > 10:
            trend = "increasing"
        elif change_percent < -10:
            trend = "decreasing"
        else:
            trend = "stable"

        summary = f"{metric} is {trend} with {change_percent:+.1f}% change over {period} periods"

        return TrendAnalysis(
            metric=metric,
            period=period,
            data_points=data_points,
            trend=trend,
            change_percent=change_percent,
            summary=summary
        )

    async def aggregate_statistics(
        self,
        group_by: str,
        metrics: List[str],
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Calculate aggregated statistics.

        Args:
            group_by: Field to group by
            metrics: List of metrics to calculate
            days: Number of days to include

        Returns:
            List of aggregated results
        """
        self._total_queries += 1

        start_time = datetime.utcnow() - timedelta(days=days)

        if self._using_fallback:
            return await self._aggregate_fallback(group_by, metrics, start_time)
        else:
            return await self._aggregate_duckdb(group_by, metrics, start_time)

    async def _aggregate_duckdb(
        self,
        group_by: str,
        metrics: List[str],
        start_time: datetime
    ) -> List[Dict[str, Any]]:
        """Calculate aggregates using DuckDB."""
        # DuckDB aggregation would go here
        # For now, use fallback
        logger.warning("DuckDB aggregation not yet implemented, using fallback")
        return await self._aggregate_fallback(group_by, metrics, start_time)

    async def _aggregate_fallback(
        self,
        group_by: str,
        metrics: List[str],
        start_time: datetime
    ) -> List[Dict[str, Any]]:
        """Calculate aggregates using fallback storage."""
        from collections import defaultdict

        # Filter by time
        filtered = [
            r for r in self._fallback_records
            if datetime.fromisoformat(r["timestamp"]) >= start_time
        ]

        # Group by field
        groups = defaultdict(list)
        for record in filtered:
            key = record.get(group_by, "unknown")
            groups[key].append(record)

        # Calculate metrics for each group
        results = []
        for group_key, records in groups.items():
            result = {group_by: group_key, "count": len(records)}

            # Add requested metrics
            for metric in metrics:
                if metric == "avg_length":
                    lengths = [len(r.get("content", "")) for r in records]
                    result[metric] = sum(lengths) / len(lengths) if lengths else 0
                elif metric == "total":
                    result[metric] = len(records)

            results.append(result)

        return results

    async def query_patterns(
        self,
        pattern_type: str,
        min_frequency: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Detect patterns in user behavior.

        Args:
            pattern_type: Type of pattern to detect
            min_frequency: Minimum frequency to consider

        Returns:
            List of detected patterns
        """
        self._total_queries += 1

        if self._using_fallback:
            return await self._detect_patterns_fallback(pattern_type, min_frequency)
        else:
            return await self._detect_patterns_duckdb(pattern_type, min_frequency)

    async def _detect_patterns_duckdb(
        self,
        pattern_type: str,
        min_frequency: int
    ) -> List[Dict[str, Any]]:
        """Detect patterns using DuckDB."""
        logger.warning("DuckDB pattern detection not yet implemented, using fallback")
        return await self._detect_patterns_fallback(pattern_type, min_frequency)

    async def _detect_patterns_fallback(
        self,
        pattern_type: str,
        min_frequency: int
    ) -> List[Dict[str, Any]]:
        """Detect patterns using fallback storage."""
        from collections import Counter

        # Count interaction types
        type_counts = Counter(r.get("interaction_type") for r in self._fallback_records)

        # Filter by frequency
        patterns = [
            {
                "pattern_type": pattern_type,
                "value": interaction_type,
                "frequency": count,
                "percentage": count / len(self._fallback_records) * 100 if self._fallback_records else 0
            }
            for interaction_type, count in type_counts.items()
            if count >= min_frequency
        ]

        return sorted(patterns, key=lambda x: x["frequency"], reverse=True)

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "user_id": self.user_id,
            "using_fallback": self._using_fallback,
            "metrics": {
                "total_queries": self._total_queries
            }
        }

        if self._using_fallback:
            stats["record_count"] = len(self._fallback_records)
        else:
            # Would query DuckDB for count
            stats["record_count"] = 0

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check.

        Returns:
            Health check results
        """
        healthy = True
        issues = []

        # Check DuckDB connection
        if not self._using_fallback and self.duckdb_client:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self.duckdb_client._get_conn
                )
            except Exception as e:
                healthy = False
                issues.append(f"DuckDB connection error: {e}")

        return {
            "healthy": healthy,
            "using_fallback": self._using_fallback,
            "issues": issues,
            "statistics": await self.get_statistics()
        }


__all__ = [
    "LongTermMemory",
    "AnalyticsQuery",
    "TrendAnalysis"
]
