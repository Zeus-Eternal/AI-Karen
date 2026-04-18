"""
Production Monitoring Service

This service provides monitoring for production environments.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import time

from .internal.perf_aggregators import PerformanceAggregator
from .internal.slo_rules import SLORules


@dataclass
class Alert:
    """An alert from monitoring."""
    id: str
    name: str
    severity: str
    message: str
    timestamp: float
    source: str
    metadata: Dict[str, Any] = None
    resolved: bool = False
    resolved_at: Optional[float] = None


@dataclass
class MonitoringConfig:
    """Configuration for production monitoring."""
    alert_thresholds: Dict[str, float] = None
    slo_targets: Dict[str, float] = None
    check_interval: int = 60
    retention_period: int = 86400


class ProductionMonitoringService:
    """
    Production Monitoring Service provides monitoring for production environments.
    
    This service provides alerting, SLO monitoring, and
    production-specific metrics collection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Production Monitoring Service.
        
        Args:
            config: Configuration for production monitoring
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Monitoring configuration
        self.monitoring_config = MonitoringConfig(**config.get("monitoring", {}))
        
        # Performance aggregator
        self.performance_aggregator = PerformanceAggregator(
            config.get("performance", {})
        )
        
        # SLO rules
        self.slo_rules = SLORules(config.get("slo", {}))
        
        # Alerts storage
        self.alerts: Dict[str, Alert] = {}
        
        # Start monitoring tasks
        self._start_monitoring_tasks()
    
    def _start_monitoring_tasks(self):
        """Start background monitoring tasks."""
        # Performance monitoring
        self.performance_task = asyncio.create_task(self._performance_monitoring_loop())
        
        # SLO monitoring
        self.slo_task = asyncio.create_task(self._slo_monitoring_loop())
        
        # Alert processing
        self.alert_task = asyncio.create_task(self._alert_processing_loop())
    
    async def _performance_monitoring_loop(self):
        """Background task for performance monitoring."""
        while True:
            try:
                # Collect performance metrics
                metrics = await self.performance_aggregator.collect_metrics()
                
                # Check thresholds
                await self._check_performance_thresholds(metrics)
                
                await asyncio.sleep(self.monitoring_config.check_interval)
            except Exception as e:
                self.logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(self.monitoring_config.check_interval)
    
    async def _slo_monitoring_loop(self):
        """Background task for SLO monitoring."""
        while True:
            try:
                # Check SLO compliance
                slo_results = await self.slo_rules.check_compliance()
                
                # Generate alerts for SLO violations
                await self._process_slo_violations(slo_results)
                
                # Check every 5 minutes
                await asyncio.sleep(300)
            except Exception as e:
                self.logger.error(f"Error in SLO monitoring: {e}")
                await asyncio.sleep(300)
    
    async def _alert_processing_loop(self):
        """Background task for alert processing."""
        while True:
            try:
                # Process alerts
                await self._process_alerts()
                
                # Check every minute
                await asyncio.sleep(60)
            except Exception as e:
                self.logger.error(f"Error in alert processing: {e}")
                await asyncio.sleep(60)
    
    async def _check_performance_thresholds(self, metrics: Dict[str, Any]):
        """Check performance metrics against thresholds."""
        thresholds = self.monitoring_config.alert_thresholds or {}
        
        for metric_name, value in metrics.items():
            threshold = thresholds.get(metric_name)
            if threshold is not None and value > threshold:
                # Create alert
                alert = Alert(
                    id=f"perf_{metric_name}_{int(time.time())}",
                    name=f"Performance Alert: {metric_name}",
                    severity="warning",
                    message=f"{metric_name} exceeded threshold: {value} > {threshold}",
                    timestamp=time.time(),
                    source="performance_monitoring",
                    metadata={"metric_name": metric_name, "value": value, "threshold": threshold}
                )
                
                self.alerts[alert.id] = alert
                self.logger.warning(f"Performance alert created: {alert.id}")
    
    async def _process_slo_violations(self, slo_results: Dict[str, Any]):
        """Process SLO violations."""
        for slo_name, result in slo_results.items():
            if not result.get("compliant", True):
                # Create alert
                alert = Alert(
                    id=f"slo_{slo_name}_{int(time.time())}",
                    name=f"SLO Violation: {slo_name}",
                    severity="critical",
                    message=f"SLO violation: {slo_name} - {result.get('message', 'No details')}",
                    timestamp=time.time(),
                    source="slo_monitoring",
                    metadata={"slo_name": slo_name, "result": result}
                )
                
                self.alerts[alert.id] = alert
                self.logger.critical(f"SLO violation alert created: {alert.id}")
    
    async def _process_alerts(self):
        """Process and route alerts."""
        # Implementation would route alerts to appropriate channels
        # (e.g., email, Slack, PagerDuty, etc.)
        
        # Clean up old alerts
        await self._cleanup_old_alerts()
    
    async def _cleanup_old_alerts(self):
        """Clean up old alerts based on retention policy."""
        cutoff_time = time.time() - self.monitoring_config.retention_period
        
        # Remove old alerts
        to_remove = [
            alert_id for alert_id, alert in self.alerts.items()
            if alert.timestamp < cutoff_time and alert.resolved
        ]
        
        for alert_id in to_remove:
            del self.alerts[alert_id]
        
        if to_remove:
            self.logger.info(f"Cleaned up {len(to_remove)} old alerts")
    
    async def record_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record a performance metric.
        
        Args:
            name: The metric name
            value: The metric value
            tags: Optional metric tags
        """
        await self.performance_aggregator.record_metric(name, value, tags)
    
    async def get_performance_metrics(
        self,
        name: str,
        time_range: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Get performance metrics for a name.
        
        Args:
            name: The metric name
            time_range: Time range with 'start' and 'end'
            
        Returns:
            List of metric data points
        """
        return await self.performance_aggregator.get_metrics(name, time_range)
    
    async def get_slo_status(self) -> Dict[str, Any]:
        """
        Get the status of all SLOs.
        
        Returns:
            Dictionary of SLO status information
        """
        return await self.slo_rules.get_status()
    
    async def get_alerts(
        self,
        severity: Optional[str] = None,
        resolved: Optional[bool] = None,
        source: Optional[str] = None
    ) -> List[Alert]:
        """
        Get alerts with optional filtering.
        
        Args:
            severity: Optional severity filter
            resolved: Optional resolved status filter
            source: Optional source filter
            
        Returns:
            List of matching alerts
        """
        alerts = list(self.alerts.values())
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        if source:
            alerts = [a for a in alerts if a.source == source]
        
        # Sort by timestamp
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        
        return alerts
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an alert.
        
        Args:
            alert_id: The alert ID to resolve
            
        Returns:
            True if resolved, False otherwise
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            return False
        
        if alert.resolved:
            return False
        
        alert.resolved = True
        alert.resolved_at = time.time()
        
        self.logger.info(f"Resolved alert: {alert_id}")
        return True
    
    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """
        Get monitoring service statistics.
        
        Returns:
            Dictionary of statistics
        """
        # Count alerts by severity
        severity_counts = {}
        for alert in self.alerts.values():
            severity = alert.severity
            if severity not in severity_counts:
                severity_counts[severity] = 0
            severity_counts[severity] += 1
        
        # Count alerts by source
        source_counts = {}
        for alert in self.alerts.values():
            source = alert.source
            if source not in source_counts:
                source_counts[source] = 0
            source_counts[source] += 1
        
        # Count resolved vs unresolved
        resolved_count = sum(1 for a in self.alerts.values() if a.resolved)
        unresolved_count = len(self.alerts) - resolved_count
        
        return {
            "total_alerts": len(self.alerts),
            "resolved_alerts": resolved_count,
            "unresolved_alerts": unresolved_count,
            "severity_counts": severity_counts,
            "source_counts": source_counts,
            "slo_status": await self.get_slo_status(),
            "performance_stats": await self.performance_aggregator.get_stats()
        }
    
    async def close(self):
        """Close the monitoring service."""
        # Cancel monitoring tasks
        if hasattr(self, "performance_task"):
            self.performance_task.cancel()
        
        if hasattr(self, "slo_task"):
            self.slo_task.cancel()
        
        if hasattr(self, "alert_task"):
            self.alert_task.cancel()
        
        # Close components
        await self.performance_aggregator.close()
        await self.slo_rules.close()
        
        self.logger.info("Closed production monitoring service")
