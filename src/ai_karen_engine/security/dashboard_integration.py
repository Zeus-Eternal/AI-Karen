"""
Dashboard integration for intelligent authentication system.

This module provides dashboard data providers for Grafana integration, pre-built dashboard
templates, custom query interfaces, and data export capabilities for external analysis tools.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from .observability import AuthObservabilityService, AuthEvent, SecurityAlert, SecurityInsight

logger = logging.getLogger(__name__)


class QueryTimeRange(Enum):
    """Time range options for dashboard queries."""
    LAST_HOUR = "1h"
    LAST_6_HOURS = "6h"
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"


class MetricType(Enum):
    """Types of metrics available for dashboard queries."""
    AUTHENTICATION_ATTEMPTS = "auth_attempts"
    RISK_SCORES = "risk_scores"
    THREAT_INTELLIGENCE = "threat_intel"
    ML_PERFORMANCE = "ml_performance"
    GEOGRAPHIC_DISTRIBUTION = "geo_distribution"
    DEVICE_ANALYSIS = "device_analysis"
    BEHAVIORAL_PATTERNS = "behavioral_patterns"
    SECURITY_ALERTS = "security_alerts"


@dataclass
class DashboardQuery:
    """Dashboard query specification."""
    metric_type: MetricType
    time_range: QueryTimeRange
    filters: Dict[str, Any] = None
    aggregation: str = "count"  # count, avg, sum, max, min
    group_by: List[str] = None
    limit: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'metric_type': self.metric_type.value,
            'time_range': self.time_range.value,
            'filters': self.filters or {},
            'aggregation': self.aggregation,
            'group_by': self.group_by or [],
            'limit': self.limit
        }


@dataclass
class DashboardDataPoint:
    """Single data point for dashboard visualization."""
    timestamp: datetime
    value: Union[int, float]
    labels: Dict[str, str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'labels': self.labels or {},
            'metadata': self.metadata or {}
        }


@dataclass
class DashboardQueryResult:
    """Result of a dashboard query."""
    query: DashboardQuery
    data_points: List[DashboardDataPoint]
    total_count: int
    execution_time_ms: float
    generated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'query': self.query.to_dict(),
            'data_points': [dp.to_dict() for dp in self.data_points],
            'total_count': self.total_count,
            'execution_time_ms': self.execution_time_ms,
            'generated_at': self.generated_at.isoformat()
        }


class GrafanaDashboardTemplate:
    """Pre-built Grafana dashboard template for intelligent authentication."""
    
    @staticmethod
    def create_authentication_overview_dashboard() -> Dict[str, Any]:
        """Create authentication overview dashboard template."""
        return {
            "dashboard": {
                "id": None,
                "title": "Intelligent Authentication Overview",
                "tags": ["authentication", "security", "ai-karen"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Authentication Attempts",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(rate(intelligent_auth_attempts_total[5m]))",
                                "legendFormat": "Attempts/sec"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Success Rate",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(rate(intelligent_auth_attempts_total{outcome=\"success\"}[5m])) / sum(rate(intelligent_auth_attempts_total[5m])) * 100",
                                "legendFormat": "Success %"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "High Risk Attempts",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(rate(intelligent_auth_attempts_total{risk_level=\"high\"}[5m]))",
                                "legendFormat": "High Risk/sec"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
                    },
                    {
                        "id": 4,
                        "title": "Blocked Attempts",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(rate(intelligent_auth_blocks_total[5m]))",
                                "legendFormat": "Blocked/sec"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
                    },
                    {
                        "id": 5,
                        "title": "Authentication Attempts Over Time",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "sum by (outcome) (rate(intelligent_auth_attempts_total[5m]))",
                                "legendFormat": "{{outcome}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                    },
                    {
                        "id": 6,
                        "title": "Risk Score Distribution",
                        "type": "histogram",
                        "targets": [
                            {
                                "expr": "intelligent_auth_risk_score_distribution",
                                "legendFormat": "Risk Score"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                    },
                    {
                        "id": 7,
                        "title": "Geographic Distribution",
                        "type": "worldmap",
                        "targets": [
                            {
                                "expr": "sum by (country) (rate(intelligent_auth_attempts_total[5m]))",
                                "legendFormat": "{{country}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
                    },
                    {
                        "id": 8,
                        "title": "ML Processing Performance",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, sum(rate(intelligent_auth_ml_processing_duration_seconds_bucket[5m])) by (le, component))",
                                "legendFormat": "{{component}} p95"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
                    }
                ],
                "time": {"from": "now-1h", "to": "now"},
                "refresh": "30s"
            }
        }
    
    @staticmethod
    def create_security_monitoring_dashboard() -> Dict[str, Any]:
        """Create security monitoring dashboard template."""
        return {
            "dashboard": {
                "id": None,
                "title": "Intelligent Authentication Security Monitoring",
                "tags": ["security", "threats", "ai-karen"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Threat Detections",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(rate(intelligent_auth_threat_detections_total[5m]))",
                                "legendFormat": "Threats/sec"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Security Alerts",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(rate(intelligent_auth_security_alerts_total[5m]))",
                                "legendFormat": "Alerts/sec"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "Behavioral Anomalies",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(rate(intelligent_auth_behavioral_anomalies_total[5m]))",
                                "legendFormat": "Anomalies/sec"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
                    },
                    {
                        "id": 4,
                        "title": "IP Reputation Checks",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(rate(intelligent_auth_ip_reputation_checks_total[5m]))",
                                "legendFormat": "Checks/sec"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
                    },
                    {
                        "id": 5,
                        "title": "Threat Types Over Time",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "sum by (threat_type) (rate(intelligent_auth_threat_detections_total[5m]))",
                                "legendFormat": "{{threat_type}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                    },
                    {
                        "id": 6,
                        "title": "Alert Severity Distribution",
                        "type": "piechart",
                        "targets": [
                            {
                                "expr": "sum by (severity) (rate(intelligent_auth_security_alerts_total[5m]))",
                                "legendFormat": "{{severity}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                    },
                    {
                        "id": 7,
                        "title": "Component Health Status",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "intelligent_auth_component_health",
                                "legendFormat": "{{component}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16}
                    }
                ],
                "time": {"from": "now-6h", "to": "now"},
                "refresh": "1m"
            }
        }
    
    @staticmethod
    def create_ml_performance_dashboard() -> Dict[str, Any]:
        """Create ML performance monitoring dashboard template."""
        return {
            "dashboard": {
                "id": None,
                "title": "Intelligent Authentication ML Performance",
                "tags": ["ml", "performance", "ai-karen"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "ML Analysis Success Rate",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "sum(rate(intelligent_auth_ml_analysis_success_total[5m])) / (sum(rate(intelligent_auth_ml_analysis_success_total[5m])) + sum(rate(intelligent_auth_ml_analysis_failure_total[5m]))) * 100",
                                "legendFormat": "Success %"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Average Processing Time",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "avg(intelligent_auth_ml_processing_duration_seconds)",
                                "legendFormat": "Avg Time (s)"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "Cache Hit Rate",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "avg(intelligent_auth_cache_hit_rate)",
                                "legendFormat": "Hit Rate %"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
                    },
                    {
                        "id": 4,
                        "title": "Request Duration",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, sum(rate(intelligent_auth_request_duration_seconds_bucket[5m])) by (le))",
                                "legendFormat": "p95 Duration (s)"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
                    },
                    {
                        "id": 5,
                        "title": "ML Component Performance",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, sum(rate(intelligent_auth_ml_processing_duration_seconds_bucket[5m])) by (le, component))",
                                "legendFormat": "{{component}} p95"
                            },
                            {
                                "expr": "histogram_quantile(0.50, sum(rate(intelligent_auth_ml_processing_duration_seconds_bucket[5m])) by (le, component))",
                                "legendFormat": "{{component}} p50"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                    },
                    {
                        "id": 6,
                        "title": "ML Analysis Failures",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "sum by (component, error_type) (rate(intelligent_auth_ml_analysis_failure_total[5m]))",
                                "legendFormat": "{{component}} - {{error_type}}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                    }
                ],
                "time": {"from": "now-1h", "to": "now"},
                "refresh": "30s"
            }
        }


class DashboardDataProvider:
    """Data provider for dashboard queries and analytics."""
    
    def __init__(self, observability_service: AuthObservabilityService):
        self.observability_service = observability_service
        self.logger = logger
    
    def execute_query(self, query: DashboardQuery) -> DashboardQueryResult:
        """Execute a dashboard query and return results."""
        start_time = datetime.now()
        
        try:
            # Convert time range to hours
            hours_back = self._time_range_to_hours(query.time_range)
            
            # Execute query based on metric type
            if query.metric_type == MetricType.AUTHENTICATION_ATTEMPTS:
                data_points = self._query_authentication_attempts(query, hours_back)
            elif query.metric_type == MetricType.RISK_SCORES:
                data_points = self._query_risk_scores(query, hours_back)
            elif query.metric_type == MetricType.THREAT_INTELLIGENCE:
                data_points = self._query_threat_intelligence(query, hours_back)
            elif query.metric_type == MetricType.ML_PERFORMANCE:
                data_points = self._query_ml_performance(query, hours_back)
            elif query.metric_type == MetricType.GEOGRAPHIC_DISTRIBUTION:
                data_points = self._query_geographic_distribution(query, hours_back)
            elif query.metric_type == MetricType.DEVICE_ANALYSIS:
                data_points = self._query_device_analysis(query, hours_back)
            elif query.metric_type == MetricType.BEHAVIORAL_PATTERNS:
                data_points = self._query_behavioral_patterns(query, hours_back)
            elif query.metric_type == MetricType.SECURITY_ALERTS:
                data_points = self._query_security_alerts(query, hours_back)
            else:
                raise ValueError(f"Unsupported metric type: {query.metric_type}")
            
            # Apply filters and limits
            data_points = self._apply_filters(data_points, query.filters or {})
            if query.limit:
                data_points = data_points[:query.limit]
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return DashboardQueryResult(
                query=query,
                data_points=data_points,
                total_count=len(data_points),
                execution_time_ms=execution_time,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error executing dashboard query: {e}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return DashboardQueryResult(
                query=query,
                data_points=[],
                total_count=0,
                execution_time_ms=execution_time,
                generated_at=datetime.now()
            )
    
    def _time_range_to_hours(self, time_range: QueryTimeRange) -> int:
        """Convert time range enum to hours."""
        mapping = {
            QueryTimeRange.LAST_HOUR: 1,
            QueryTimeRange.LAST_6_HOURS: 6,
            QueryTimeRange.LAST_24_HOURS: 24,
            QueryTimeRange.LAST_7_DAYS: 168,
            QueryTimeRange.LAST_30_DAYS: 720
        }
        return mapping.get(time_range, 24)
    
    def _query_authentication_attempts(self, query: DashboardQuery, hours_back: int) -> List[DashboardDataPoint]:
        """Query authentication attempts data."""
        stats = self.observability_service.get_authentication_statistics(hours_back)
        
        data_points = []
        
        # Create data points based on aggregation type
        if query.aggregation == "count":
            data_points.append(DashboardDataPoint(
                timestamp=datetime.now(),
                value=stats['total_events'],
                labels={'metric': 'total_attempts'}
            ))
            
            # Add breakdown by event type if requested
            if query.group_by and 'event_type' in query.group_by:
                for event_type, count in stats['events_by_type'].items():
                    data_points.append(DashboardDataPoint(
                        timestamp=datetime.now(),
                        value=count,
                        labels={'metric': 'attempts', 'event_type': event_type}
                    ))
        
        return data_points
    
    def _query_risk_scores(self, query: DashboardQuery, hours_back: int) -> List[DashboardDataPoint]:
        """Query risk scores data."""
        stats = self.observability_service.get_authentication_statistics(hours_back)
        
        return [
            DashboardDataPoint(
                timestamp=datetime.now(),
                value=stats['avg_risk_score'],
                labels={'metric': 'avg_risk_score'}
            )
        ]
    
    def _query_threat_intelligence(self, query: DashboardQuery, hours_back: int) -> List[DashboardDataPoint]:
        """Query threat intelligence data."""
        stats = self.observability_service.get_threat_intelligence_statistics(hours_back)
        
        data_points = [
            DashboardDataPoint(
                timestamp=datetime.now(),
                value=stats['total_threat_hits'],
                labels={'metric': 'threat_hits'}
            ),
            DashboardDataPoint(
                timestamp=datetime.now(),
                value=stats['high_threat_hits'],
                labels={'metric': 'high_threat_hits'}
            ),
            DashboardDataPoint(
                timestamp=datetime.now(),
                value=stats['threat_hit_rate'],
                labels={'metric': 'threat_hit_rate'}
            )
        ]
        
        return data_points
    
    def _query_ml_performance(self, query: DashboardQuery, hours_back: int) -> List[DashboardDataPoint]:
        """Query ML performance data."""
        stats = self.observability_service.get_ml_performance_statistics(hours_back)
        
        data_points = [
            DashboardDataPoint(
                timestamp=datetime.now(),
                value=stats['nlp_success_rate'],
                labels={'metric': 'nlp_success_rate'}
            ),
            DashboardDataPoint(
                timestamp=datetime.now(),
                value=stats['embedding_success_rate'],
                labels={'metric': 'embedding_success_rate'}
            ),
            DashboardDataPoint(
                timestamp=datetime.now(),
                value=stats['avg_nlp_processing_time_ms'],
                labels={'metric': 'avg_nlp_processing_time_ms'}
            ),
            DashboardDataPoint(
                timestamp=datetime.now(),
                value=stats['avg_embedding_processing_time_ms'],
                labels={'metric': 'avg_embedding_processing_time_ms'}
            )
        ]
        
        return data_points
    
    def _query_geographic_distribution(self, query: DashboardQuery, hours_back: int) -> List[DashboardDataPoint]:
        """Query geographic distribution data."""
        # Get events and group by country
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        events = self.observability_service.metrics_aggregator.get_events_in_timerange(start_time, end_time)
        
        country_counts = {}
        for event in events:
            if event.country:
                country_counts[event.country] = country_counts.get(event.country, 0) + 1
        
        data_points = []
        for country, count in country_counts.items():
            data_points.append(DashboardDataPoint(
                timestamp=datetime.now(),
                value=count,
                labels={'metric': 'country_attempts', 'country': country}
            ))
        
        return data_points
    
    def _query_device_analysis(self, query: DashboardQuery, hours_back: int) -> List[DashboardDataPoint]:
        """Query device analysis data."""
        # Get events and analyze device patterns
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        events = self.observability_service.metrics_aggregator.get_events_in_timerange(start_time, end_time)
        
        known_devices = len([e for e in events if e.is_known_device])
        unknown_devices = len([e for e in events if e.is_known_device is False])
        
        return [
            DashboardDataPoint(
                timestamp=datetime.now(),
                value=known_devices,
                labels={'metric': 'known_devices'}
            ),
            DashboardDataPoint(
                timestamp=datetime.now(),
                value=unknown_devices,
                labels={'metric': 'unknown_devices'}
            )
        ]
    
    def _query_behavioral_patterns(self, query: DashboardQuery, hours_back: int) -> List[DashboardDataPoint]:
        """Query behavioral patterns data."""
        # Get events and analyze behavioral patterns
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        events = self.observability_service.metrics_aggregator.get_events_in_timerange(start_time, end_time)
        
        usual_locations = len([e for e in events if e.is_usual_location])
        unusual_locations = len([e for e in events if e.is_usual_location is False])
        
        return [
            DashboardDataPoint(
                timestamp=datetime.now(),
                value=usual_locations,
                labels={'metric': 'usual_locations'}
            ),
            DashboardDataPoint(
                timestamp=datetime.now(),
                value=unusual_locations,
                labels={'metric': 'unusual_locations'}
            )
        ]
    
    def _query_security_alerts(self, query: DashboardQuery, hours_back: int) -> List[DashboardDataPoint]:
        """Query security alerts data."""
        alerts = self.observability_service.get_recent_alerts(hours_back)
        
        # Group by severity
        severity_counts = {}
        for alert in alerts:
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        data_points = []
        for severity, count in severity_counts.items():
            data_points.append(DashboardDataPoint(
                timestamp=datetime.now(),
                value=count,
                labels={'metric': 'alerts', 'severity': severity}
            ))
        
        return data_points
    
    def _apply_filters(self, data_points: List[DashboardDataPoint], filters: Dict[str, Any]) -> List[DashboardDataPoint]:
        """Apply filters to data points."""
        if not filters:
            return data_points
        
        filtered_points = []
        for point in data_points:
            include_point = True
            
            for filter_key, filter_value in filters.items():
                if filter_key in point.labels:
                    if point.labels[filter_key] != filter_value:
                        include_point = False
                        break
                elif filter_key in point.metadata:
                    if point.metadata[filter_key] != filter_value:
                        include_point = False
                        break
            
            if include_point:
                filtered_points.append(point)
        
        return filtered_points


class DashboardExporter:
    """Export dashboard data for external analysis tools."""
    
    def __init__(self, data_provider: DashboardDataProvider):
        self.data_provider = data_provider
        self.logger = logger
    
    def export_to_csv(self, query: DashboardQuery) -> str:
        """Export query results to CSV format."""
        result = self.data_provider.execute_query(query)
        
        if not result.data_points:
            return "timestamp,value,labels,metadata\n"
        
        csv_lines = ["timestamp,value,labels,metadata"]
        
        for point in result.data_points:
            labels_str = json.dumps(point.labels or {})
            metadata_str = json.dumps(point.metadata or {})
            
            csv_lines.append(f"{point.timestamp.isoformat()},{point.value},\"{labels_str}\",\"{metadata_str}\"")
        
        return "\n".join(csv_lines)
    
    def export_to_json(self, query: DashboardQuery) -> str:
        """Export query results to JSON format."""
        result = self.data_provider.execute_query(query)
        return json.dumps(result.to_dict(), indent=2)
    
    def export_prometheus_format(self, query: DashboardQuery) -> str:
        """Export query results in Prometheus exposition format."""
        result = self.data_provider.execute_query(query)
        
        if not result.data_points:
            return ""
        
        lines = []
        metric_name = f"intelligent_auth_{query.metric_type.value}"
        
        # Add help and type comments
        lines.append(f"# HELP {metric_name} Dashboard query result for {query.metric_type.value}")
        lines.append(f"# TYPE {metric_name} gauge")
        
        for point in result.data_points:
            labels_str = ""
            if point.labels:
                label_pairs = [f'{k}="{v}"' for k, v in point.labels.items()]
                labels_str = "{" + ",".join(label_pairs) + "}"
            
            lines.append(f"{metric_name}{labels_str} {point.value} {int(point.timestamp.timestamp() * 1000)}")
        
        return "\n".join(lines)
    
    def export_elasticsearch_bulk(self, query: DashboardQuery, index_name: str = "intelligent-auth") -> str:
        """Export query results in Elasticsearch bulk format."""
        result = self.data_provider.execute_query(query)
        
        if not result.data_points:
            return ""
        
        lines = []
        
        for point in result.data_points:
            # Index action
            index_action = {
                "index": {
                    "_index": index_name,
                    "_type": "_doc"
                }
            }
            lines.append(json.dumps(index_action))
            
            # Document
            doc = {
                "@timestamp": point.timestamp.isoformat(),
                "metric_type": query.metric_type.value,
                "value": point.value,
                "labels": point.labels or {},
                "metadata": point.metadata or {},
                "query_info": {
                    "time_range": query.time_range.value,
                    "aggregation": query.aggregation,
                    "filters": query.filters or {}
                }
            }
            lines.append(json.dumps(doc))
        
        return "\n".join(lines) + "\n"


class CustomQueryInterface:
    """Custom query interface for advanced dashboard analytics."""
    
    def __init__(self, data_provider: DashboardDataProvider):
        self.data_provider = data_provider
        self.logger = logger
    
    def execute_custom_query(self, query_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a custom query with advanced filtering and aggregation."""
        try:
            # Parse query specification
            metric_type = MetricType(query_spec.get('metric_type', 'auth_attempts'))
            time_range = QueryTimeRange(query_spec.get('time_range', '24h'))
            
            query = DashboardQuery(
                metric_type=metric_type,
                time_range=time_range,
                filters=query_spec.get('filters', {}),
                aggregation=query_spec.get('aggregation', 'count'),
                group_by=query_spec.get('group_by', []),
                limit=query_spec.get('limit')
            )
            
            result = self.data_provider.execute_query(query)
            
            # Apply custom post-processing if specified
            if 'post_processing' in query_spec:
                result = self._apply_post_processing(result, query_spec['post_processing'])
            
            return result.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error executing custom query: {e}")
            return {
                'error': str(e),
                'query_spec': query_spec,
                'generated_at': datetime.now().isoformat()
            }
    
    def _apply_post_processing(self, result: DashboardQueryResult, post_processing: Dict[str, Any]) -> DashboardQueryResult:
        """Apply custom post-processing to query results."""
        # Example post-processing operations
        if post_processing.get('sort_by'):
            sort_field = post_processing['sort_by']
            reverse = post_processing.get('sort_desc', False)
            
            if sort_field == 'value':
                result.data_points.sort(key=lambda x: x.value, reverse=reverse)
            elif sort_field == 'timestamp':
                result.data_points.sort(key=lambda x: x.timestamp, reverse=reverse)
        
        if post_processing.get('calculate_percentiles'):
            values = [point.value for point in result.data_points]
            if values:
                import statistics
                percentiles = {
                    'p50': statistics.median(values),
                    'p95': statistics.quantiles(values, n=20)[18] if len(values) > 1 else values[0],
                    'p99': statistics.quantiles(values, n=100)[98] if len(values) > 1 else values[0]
                }
                
                # Add percentile data points
                for percentile, value in percentiles.items():
                    result.data_points.append(DashboardDataPoint(
                        timestamp=datetime.now(),
                        value=value,
                        labels={'metric': 'percentile', 'percentile': percentile}
                    ))
        
        return result
    
    def get_available_metrics(self) -> List[Dict[str, Any]]:
        """Get list of available metrics for querying."""
        return [
            {
                'metric_type': metric.value,
                'description': self._get_metric_description(metric),
                'supported_aggregations': ['count', 'avg', 'sum', 'max', 'min'],
                'available_labels': self._get_metric_labels(metric)
            }
            for metric in MetricType
        ]
    
    def _get_metric_description(self, metric: MetricType) -> str:
        """Get description for a metric type."""
        descriptions = {
            MetricType.AUTHENTICATION_ATTEMPTS: "Authentication attempt counts and success rates",
            MetricType.RISK_SCORES: "Risk score distributions and statistics",
            MetricType.THREAT_INTELLIGENCE: "Threat intelligence hits and analysis",
            MetricType.ML_PERFORMANCE: "Machine learning processing performance metrics",
            MetricType.GEOGRAPHIC_DISTRIBUTION: "Geographic distribution of authentication attempts",
            MetricType.DEVICE_ANALYSIS: "Device fingerprinting and analysis results",
            MetricType.BEHAVIORAL_PATTERNS: "User behavioral pattern analysis",
            MetricType.SECURITY_ALERTS: "Security alerts and incident data"
        }
        return descriptions.get(metric, "No description available")
    
    def _get_metric_labels(self, metric: MetricType) -> List[str]:
        """Get available labels for a metric type."""
        label_mapping = {
            MetricType.AUTHENTICATION_ATTEMPTS: ['event_type', 'outcome', 'risk_level'],
            MetricType.RISK_SCORES: ['risk_level'],
            MetricType.THREAT_INTELLIGENCE: ['threat_type', 'severity'],
            MetricType.ML_PERFORMANCE: ['component', 'success'],
            MetricType.GEOGRAPHIC_DISTRIBUTION: ['country', 'region'],
            MetricType.DEVICE_ANALYSIS: ['device_type', 'known_device'],
            MetricType.BEHAVIORAL_PATTERNS: ['pattern_type', 'anomaly_level'],
            MetricType.SECURITY_ALERTS: ['severity', 'category', 'source']
        }
        return label_mapping.get(metric, [])


# Convenience functions for creating dashboard components
def create_dashboard_data_provider(observability_service: AuthObservabilityService) -> DashboardDataProvider:
    """Create dashboard data provider."""
    return DashboardDataProvider(observability_service)


def create_dashboard_exporter(data_provider: DashboardDataProvider) -> DashboardExporter:
    """Create dashboard exporter."""
    return DashboardExporter(data_provider)


def create_custom_query_interface(data_provider: DashboardDataProvider) -> CustomQueryInterface:
    """Create custom query interface."""
    return CustomQueryInterface(data_provider)


def get_grafana_dashboard_templates() -> Dict[str, Dict[str, Any]]:
    """Get all available Grafana dashboard templates."""
    return {
        'authentication_overview': GrafanaDashboardTemplate.create_authentication_overview_dashboard(),
        'security_monitoring': GrafanaDashboardTemplate.create_security_monitoring_dashboard(),
        'ml_performance': GrafanaDashboardTemplate.create_ml_performance_dashboard()
    }