"""
Telemetry Manager - Prometheus integration for EchoCore monitoring

Provides comprehensive metrics for memory performance, model training,
and system health with Prometheus integration.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class TelemetryManager:
    """
    Manages telemetry and metrics for EchoCore.

    Features:
    - Prometheus metrics integration
    - Memory performance tracking
    - Model training metrics
    - System health monitoring
    - Anomaly detection
    - Self-diagnostics
    """

    def __init__(
        self,
        user_id: str,
        enable_prometheus: bool = True,
        prometheus_port: int = 8000
    ):
        self.user_id = user_id
        self.enable_prometheus = enable_prometheus
        self.prometheus_port = prometheus_port

        # Prometheus metrics (optional)
        self._prometheus_available = False
        self._metrics = {}

        # In-memory metrics (always available)
        self._memory_metrics = defaultdict(list)
        self._model_metrics = defaultdict(list)
        self._health_metrics = defaultdict(list)

        # Counters
        self._total_memory_operations = 0
        self._total_searches = 0
        self._total_stores = 0
        self._total_errors = 0

        # Timing
        self._operation_times = []

        logger.info(f"TelemetryManager initialized for user {user_id}")

        # Initialize Prometheus if enabled
        if self.enable_prometheus:
            self._initialize_prometheus()

    def _initialize_prometheus(self) -> None:
        """Initialize Prometheus metrics."""
        try:
            from prometheus_client import Counter, Histogram, Gauge, Summary

            # Memory operation metrics
            self._metrics["memory_operations_total"] = Counter(
                f"echocore_memory_operations_total_{self.user_id}",
                "Total number of memory operations",
                ["operation_type", "tier"]
            )

            self._metrics["memory_operation_duration"] = Histogram(
                f"echocore_memory_operation_duration_seconds_{self.user_id}",
                "Memory operation duration in seconds",
                ["operation_type", "tier"]
            )

            self._metrics["memory_search_results"] = Histogram(
                f"echocore_memory_search_results_{self.user_id}",
                "Number of results returned from memory search",
                buckets=[0, 1, 5, 10, 20, 50, 100]
            )

            # Memory performance metrics
            self._metrics["memory_hit_rate"] = Gauge(
                f"echocore_memory_hit_rate_{self.user_id}",
                "Memory hit rate (0-1)",
                ["tier"]
            )

            self._metrics["memory_recall_speed"] = Summary(
                f"echocore_memory_recall_speed_seconds_{self.user_id}",
                "Memory recall speed in seconds",
                ["tier"]
            )

            # Model training metrics
            self._metrics["model_training_duration"] = Histogram(
                f"echocore_model_training_duration_seconds_{self.user_id}",
                "Model training duration in seconds"
            )

            self._metrics["model_training_loss"] = Gauge(
                f"echocore_model_training_loss_{self.user_id}",
                "Model training loss"
            )

            self._metrics["model_update_interval"] = Gauge(
                f"echocore_model_update_interval_hours_{self.user_id}",
                "Hours since last model update"
            )

            # Health metrics
            self._metrics["system_health"] = Gauge(
                f"echocore_system_health_{self.user_id}",
                "System health status (1=healthy, 0=unhealthy)",
                ["component"]
            )

            self._metrics["error_count"] = Counter(
                f"echocore_errors_total_{self.user_id}",
                "Total number of errors",
                ["error_type", "component"]
            )

            self._prometheus_available = True
            logger.info("Prometheus metrics initialized")

        except ImportError:
            logger.warning("prometheus_client not available, using in-memory metrics only")
            self._prometheus_available = False

    def record_memory_operation(
        self,
        operation_type: str,
        tier: str,
        duration_seconds: float,
        success: bool = True,
        result_count: Optional[int] = None
    ) -> None:
        """
        Record a memory operation.

        Args:
            operation_type: Type of operation ("search", "store", "retrieve")
            tier: Memory tier ("short_term", "long_term", "persistent")
            duration_seconds: Operation duration in seconds
            success: Whether operation was successful
            result_count: Number of results (for search operations)
        """
        self._total_memory_operations += 1

        if operation_type == "search":
            self._total_searches += 1
        elif operation_type == "store":
            self._total_stores += 1

        if not success:
            self._total_errors += 1

        # Record timing
        self._operation_times.append(duration_seconds)

        # Store in-memory metrics
        self._memory_metrics[f"{operation_type}_{tier}"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "duration": duration_seconds,
            "success": success,
            "result_count": result_count
        })

        # Update Prometheus metrics if available
        if self._prometheus_available:
            self._metrics["memory_operations_total"].labels(
                operation_type=operation_type,
                tier=tier
            ).inc()

            self._metrics["memory_operation_duration"].labels(
                operation_type=operation_type,
                tier=tier
            ).observe(duration_seconds)

            if result_count is not None:
                self._metrics["memory_search_results"].observe(result_count)

        logger.debug(f"Recorded {operation_type} operation on {tier} tier ({duration_seconds:.3f}s)")

    def record_memory_performance(
        self,
        tier: str,
        hit_rate: float,
        recall_speed: float
    ) -> None:
        """
        Record memory performance metrics.

        Args:
            tier: Memory tier
            hit_rate: Hit rate (0-1)
            recall_speed: Recall speed in seconds
        """
        self._memory_metrics[f"performance_{tier}"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "hit_rate": hit_rate,
            "recall_speed": recall_speed
        })

        if self._prometheus_available:
            self._metrics["memory_hit_rate"].labels(tier=tier).set(hit_rate)
            self._metrics["memory_recall_speed"].labels(tier=tier).observe(recall_speed)

    def record_model_training(
        self,
        duration_seconds: float,
        final_loss: float,
        epochs: int,
        samples: int
    ) -> None:
        """
        Record model training metrics.

        Args:
            duration_seconds: Training duration in seconds
            final_loss: Final training loss
            epochs: Number of epochs
            samples: Number of training samples
        """
        self._model_metrics["training"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "duration": duration_seconds,
            "final_loss": final_loss,
            "epochs": epochs,
            "samples": samples
        })

        if self._prometheus_available:
            self._metrics["model_training_duration"].observe(duration_seconds)
            self._metrics["model_training_loss"].set(final_loss)

        logger.info(f"Recorded model training: {duration_seconds:.1f}s, loss={final_loss:.4f}")

    def record_model_update(self, hours_since_last_update: float) -> None:
        """
        Record model update interval.

        Args:
            hours_since_last_update: Hours since last model update
        """
        if self._prometheus_available:
            self._metrics["model_update_interval"].set(hours_since_last_update)

    def record_health_status(
        self,
        component: str,
        healthy: bool,
        issues: Optional[List[str]] = None
    ) -> None:
        """
        Record component health status.

        Args:
            component: Component name
            healthy: Whether component is healthy
            issues: List of issues (if any)
        """
        self._health_metrics[component].append({
            "timestamp": datetime.utcnow().isoformat(),
            "healthy": healthy,
            "issues": issues or []
        })

        if self._prometheus_available:
            self._metrics["system_health"].labels(component=component).set(1 if healthy else 0)

    def record_error(
        self,
        error_type: str,
        component: str,
        error_message: str
    ) -> None:
        """
        Record an error.

        Args:
            error_type: Type of error
            component: Component where error occurred
            error_message: Error message
        """
        self._total_errors += 1

        self._health_metrics["errors"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "component": component,
            "message": error_message
        })

        if self._prometheus_available:
            self._metrics["error_count"].labels(
                error_type=error_type,
                component=component
            ).inc()

        logger.error(f"Recorded error in {component}: {error_type} - {error_message}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive telemetry statistics.

        Returns:
            Dictionary with all statistics
        """
        stats = {
            "user_id": self.user_id,
            "prometheus_available": self._prometheus_available,
            "counters": {
                "total_memory_operations": self._total_memory_operations,
                "total_searches": self._total_searches,
                "total_stores": self._total_stores,
                "total_errors": self._total_errors
            },
            "performance": {
                "avg_operation_time": (
                    sum(self._operation_times) / len(self._operation_times)
                    if self._operation_times else 0
                ),
                "min_operation_time": min(self._operation_times) if self._operation_times else 0,
                "max_operation_time": max(self._operation_times) if self._operation_times else 0
            }
        }

        # Add recent metrics
        stats["recent_memory_operations"] = len(self._memory_metrics)
        stats["recent_model_trainings"] = len(self._model_metrics.get("training", []))
        stats["recent_health_checks"] = len(self._health_metrics)

        return stats

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """
        Detect anomalies in metrics.

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Check error rate
        if self._total_memory_operations > 0:
            error_rate = self._total_errors / self._total_memory_operations
            if error_rate > 0.1:  # 10% error rate threshold
                anomalies.append({
                    "type": "high_error_rate",
                    "severity": "warning",
                    "message": f"High error rate: {error_rate:.1%}",
                    "value": error_rate
                })

        # Check operation times
        if self._operation_times:
            avg_time = sum(self._operation_times) / len(self._operation_times)
            if avg_time > 1.0:  # 1 second threshold
                anomalies.append({
                    "type": "slow_operations",
                    "severity": "warning",
                    "message": f"Slow average operation time: {avg_time:.2f}s",
                    "value": avg_time
                })

        # Check for recent errors
        recent_errors = self._health_metrics.get("errors", [])
        if len(recent_errors) > 10:
            anomalies.append({
                "type": "frequent_errors",
                "severity": "critical",
                "message": f"Frequent errors detected: {len(recent_errors)} recent errors",
                "value": len(recent_errors)
            })

        return anomalies

    def self_diagnose(self) -> Dict[str, Any]:
        """
        Perform self-diagnosis.

        Returns:
            Diagnosis results
        """
        diagnosis = {
            "timestamp": datetime.utcnow().isoformat(),
            "healthy": True,
            "issues": [],
            "recommendations": []
        }

        # Check for anomalies
        anomalies = self.detect_anomalies()
        if anomalies:
            diagnosis["healthy"] = False
            diagnosis["issues"].extend([a["message"] for a in anomalies])

            # Add recommendations
            for anomaly in anomalies:
                if anomaly["type"] == "high_error_rate":
                    diagnosis["recommendations"].append(
                        "Investigate error logs and check component health"
                    )
                elif anomaly["type"] == "slow_operations":
                    diagnosis["recommendations"].append(
                        "Optimize database queries or increase resources"
                    )
                elif anomaly["type"] == "frequent_errors":
                    diagnosis["recommendations"].append(
                        "Review error patterns and implement error recovery"
                    )

        # Check Prometheus availability
        if self.enable_prometheus and not self._prometheus_available:
            diagnosis["issues"].append("Prometheus metrics not available")
            diagnosis["recommendations"].append(
                "Install prometheus_client library for advanced metrics"
            )

        return diagnosis

    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all metrics for analysis.

        Returns:
            Dictionary with all metrics
        """
        return {
            "user_id": self.user_id,
            "statistics": self.get_statistics(),
            "memory_metrics": dict(self._memory_metrics),
            "model_metrics": dict(self._model_metrics),
            "health_metrics": dict(self._health_metrics),
            "anomalies": self.detect_anomalies(),
            "diagnosis": self.self_diagnose()
        }


__all__ = [
    "TelemetryManager"
]
