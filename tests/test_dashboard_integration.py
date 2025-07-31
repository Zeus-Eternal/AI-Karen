"""
Unit tests for intelligent authentication dashboard integration.

Tests dashboard data providers, Grafana integration, custom query interfaces,
and data export capabilities for external analysis tools.
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from src.ai_karen_engine.security.dashboard_integration import (
    DashboardDataProvider,
    DashboardExporter,
    CustomQueryInterface,
    GrafanaDashboardTemplate,
    DashboardQuery,
    DashboardDataPoint,
    DashboardQueryResult,
    QueryTimeRange,
    MetricType,
    create_dashboard_data_provider,
    create_dashboard_exporter,
    create_custom_query_interface,
    get_grafana_dashboard_templates
)
from src.ai_karen_engine.security.observability import (
    AuthObservabilityService,
    AuthEvent,
    AuthEventType,
    SecurityAlert,
    AlertSeverity
)
from src.ai_karen_engine.security.models import (
    AuthContext,
    RiskLevel,
    GeoLocation
)


@pytest.fixture
def mock_observability_service():
    """Create mock observability service for testing."""
    service = Mock(spec=AuthObservabilityService)
    
    # Mock authentication statistics
    service.get_authentication_statistics.return_value = {
        'total_events': 1000,
        'success_rate': 0.85,
        'failure_rate': 0.15,
        'block_rate': 0.05,
        'avg_risk_score': 0.3,
        'unique_users': 50,
        'unique_ips': 75,
        'unique_countries': 10,
        'avg_processing_time_ms': 150.0,
        'events_by_type': {
            'login_success': 850,
            'login_failure': 150,
            'login_blocked': 50,
            'login_attempt': 1000
        }
    }
    
    # Mock threat intelligence statistics
    service.get_threat_intelligence_statistics.return_value = {
        'total_threat_hits': 25,
        'high_threat_hits': 5,
        'threat_hit_rate': 0.025,
        'avg_threat_score': 0.6,
        'malicious_ips': ['192.168.1.100', '10.0.0.1'],
        'attack_patterns': ['brute_force', 'credential_stuffing']
    }
    
    # Mock ML performance statistics
    service.get_ml_performance_statistics.return_value = {
        'total_events': 1000,
        'nlp_success_rate': 0.95,
        'embedding_success_rate': 0.92,
        'avg_nlp_processing_time_ms': 50.0,
        'avg_embedding_processing_time_ms': 80.0
    }
    
    # Mock recent alerts
    service.get_recent_alerts.return_value = [
        SecurityAlert(
            alert_id="alert_1",
            severity=AlertSeverity.HIGH,
            title="High Risk Login",
            description="High risk login detected",
            source="test",
            timestamp=datetime.now()
        ),
        SecurityAlert(
            alert_id="alert_2",
            severity=AlertSeverity.MEDIUM,
            title="Unusual Location",
            description="Login from unusual location",
            source="test",
            timestamp=datetime.now()
        )
    ]
    
    # Mock metrics aggregator
    mock_aggregator = Mock()
    mock_events = [
        create_mock_auth_event("US", True, True),
        create_mock_auth_event("CA", False, False),
        create_mock_auth_event("UK", True, True)
    ]
    mock_aggregator.get_events_in_timerange.return_value = mock_events
    service.metrics_aggregator = mock_aggregator
    
    return service


def create_mock_auth_event(country, is_usual_location, is_known_device):
    """Create mock authentication event for testing."""
    event = Mock(spec=AuthEvent)
    event.country = country
    event.is_usual_location = is_usual_location
    event.is_known_device = is_known_device
    event.timestamp = datetime.now()
    return event


class TestDashboardQuery:
    """Test DashboardQuery data model."""
    
    def test_dashboard_query_creation(self):
        """Test creating DashboardQuery."""
        query = DashboardQuery(
            metric_type=MetricType.AUTHENTICATION_ATTEMPTS,
            time_range=QueryTimeRange.LAST_24_HOURS,
            filters={'country': 'US'},
            aggregation='count',
            group_by=['event_type'],
            limit=100
        )
        
        assert query.metric_type == MetricType.AUTHENTICATION_ATTEMPTS
        assert query.time_range == QueryTimeRange.LAST_24_HOURS
        assert query.filters == {'country': 'US'}
        assert query.aggregation == 'count'
        assert query.group_by == ['event_type']
        assert query.limit == 100
    
    def test_dashboard_query_to_dict(self):
        """Test DashboardQuery serialization."""
        query = DashboardQuery(
            metric_type=MetricType.RISK_SCORES,
            time_range=QueryTimeRange.LAST_HOUR
        )
        
        query_dict = query.to_dict()
        
        assert query_dict['metric_type'] == 'risk_scores'
        assert query_dict['time_range'] == '1h'
        assert query_dict['filters'] == {}
        assert query_dict['aggregation'] == 'count'
        assert query_dict['group_by'] == []
        assert query_dict['limit'] is None


class TestDashboardDataPoint:
    """Test DashboardDataPoint data model."""
    
    def test_dashboard_data_point_creation(self):
        """Test creating DashboardDataPoint."""
        timestamp = datetime.now()
        point = DashboardDataPoint(
            timestamp=timestamp,
            value=100,
            labels={'metric': 'test', 'country': 'US'},
            metadata={'source': 'test'}
        )
        
        assert point.timestamp == timestamp
        assert point.value == 100
        assert point.labels == {'metric': 'test', 'country': 'US'}
        assert point.metadata == {'source': 'test'}
    
    def test_dashboard_data_point_to_dict(self):
        """Test DashboardDataPoint serialization."""
        timestamp = datetime.now()
        point = DashboardDataPoint(
            timestamp=timestamp,
            value=50.5,
            labels={'metric': 'test'}
        )
        
        point_dict = point.to_dict()
        
        assert point_dict['timestamp'] == timestamp.isoformat()
        assert point_dict['value'] == 50.5
        assert point_dict['labels'] == {'metric': 'test'}
        assert point_dict['metadata'] == {}


class TestDashboardQueryResult:
    """Test DashboardQueryResult data model."""
    
    def test_dashboard_query_result_creation(self):
        """Test creating DashboardQueryResult."""
        query = DashboardQuery(
            metric_type=MetricType.AUTHENTICATION_ATTEMPTS,
            time_range=QueryTimeRange.LAST_HOUR
        )
        
        data_points = [
            DashboardDataPoint(timestamp=datetime.now(), value=100),
            DashboardDataPoint(timestamp=datetime.now(), value=200)
        ]
        
        result = DashboardQueryResult(
            query=query,
            data_points=data_points,
            total_count=2,
            execution_time_ms=150.0,
            generated_at=datetime.now()
        )
        
        assert result.query == query
        assert len(result.data_points) == 2
        assert result.total_count == 2
        assert result.execution_time_ms == 150.0
    
    def test_dashboard_query_result_to_dict(self):
        """Test DashboardQueryResult serialization."""
        query = DashboardQuery(
            metric_type=MetricType.AUTHENTICATION_ATTEMPTS,
            time_range=QueryTimeRange.LAST_HOUR
        )
        
        result = DashboardQueryResult(
            query=query,
            data_points=[],
            total_count=0,
            execution_time_ms=50.0,
            generated_at=datetime.now()
        )
        
        result_dict = result.to_dict()
        
        assert 'query' in result_dict
        assert 'data_points' in result_dict
        assert result_dict['total_count'] == 0
        assert result_dict['execution_time_ms'] == 50.0


class TestGrafanaDashboardTemplate:
    """Test Grafana dashboard template generation."""
    
    def test_create_authentication_overview_dashboard(self):
        """Test creating authentication overview dashboard."""
        dashboard = GrafanaDashboardTemplate.create_authentication_overview_dashboard()
        
        assert 'dashboard' in dashboard
        assert dashboard['dashboard']['title'] == 'Intelligent Authentication Overview'
        assert 'panels' in dashboard['dashboard']
        assert len(dashboard['dashboard']['panels']) > 0
        
        # Check that panels have required fields
        for panel in dashboard['dashboard']['panels']:
            assert 'id' in panel
            assert 'title' in panel
            assert 'type' in panel
            assert 'targets' in panel
            assert 'gridPos' in panel
    
    def test_create_security_monitoring_dashboard(self):
        """Test creating security monitoring dashboard."""
        dashboard = GrafanaDashboardTemplate.create_security_monitoring_dashboard()
        
        assert 'dashboard' in dashboard
        assert dashboard['dashboard']['title'] == 'Intelligent Authentication Security Monitoring'
        assert 'panels' in dashboard['dashboard']
        
        # Check for security-specific panels
        panel_titles = [panel['title'] for panel in dashboard['dashboard']['panels']]
        assert 'Threat Detections' in panel_titles
        assert 'Security Alerts' in panel_titles
        assert 'Behavioral Anomalies' in panel_titles
    
    def test_create_ml_performance_dashboard(self):
        """Test creating ML performance dashboard."""
        dashboard = GrafanaDashboardTemplate.create_ml_performance_dashboard()
        
        assert 'dashboard' in dashboard
        assert dashboard['dashboard']['title'] == 'Intelligent Authentication ML Performance'
        assert 'panels' in dashboard['dashboard']
        
        # Check for ML-specific panels
        panel_titles = [panel['title'] for panel in dashboard['dashboard']['panels']]
        assert 'ML Analysis Success Rate' in panel_titles
        assert 'Average Processing Time' in panel_titles
        assert 'Cache Hit Rate' in panel_titles


class TestDashboardDataProvider:
    """Test DashboardDataProvider functionality."""
    
    def test_data_provider_initialization(self, mock_observability_service):
        """Test DashboardDataProvider initialization."""
        provider = DashboardDataProvider(mock_observability_service)
        
        assert provider.observability_service == mock_observability_service
        assert provider.logger is not None
    
    def test_execute_authentication_attempts_query(self, mock_observability_service):
        """Test executing authentication attempts query."""
        provider = DashboardDataProvider(mock_observability_service)
        
        query = DashboardQuery(
            metric_type=MetricType.AUTHENTICATION_ATTEMPTS,
            time_range=QueryTimeRange.LAST_24_HOURS,
            aggregation='count'
        )
        
        result = provider.execute_query(query)
        
        assert isinstance(result, DashboardQueryResult)
        assert result.query == query
        assert len(result.data_points) > 0
        assert result.total_count > 0
        assert result.execution_time_ms >= 0
    
    def test_execute_risk_scores_query(self, mock_observability_service):
        """Test executing risk scores query."""
        provider = DashboardDataProvider(mock_observability_service)
        
        query = DashboardQuery(
            metric_type=MetricType.RISK_SCORES,
            time_range=QueryTimeRange.LAST_HOUR
        )
        
        result = provider.execute_query(query)
        
        assert isinstance(result, DashboardQueryResult)
        assert len(result.data_points) > 0
        
        # Check that we got risk score data
        risk_score_point = result.data_points[0]
        assert risk_score_point.labels['metric'] == 'avg_risk_score'
        assert isinstance(risk_score_point.value, (int, float))
    
    def test_execute_threat_intelligence_query(self, mock_observability_service):
        """Test executing threat intelligence query."""
        provider = DashboardDataProvider(mock_observability_service)
        
        query = DashboardQuery(
            metric_type=MetricType.THREAT_INTELLIGENCE,
            time_range=QueryTimeRange.LAST_6_HOURS
        )
        
        result = provider.execute_query(query)
        
        assert isinstance(result, DashboardQueryResult)
        assert len(result.data_points) > 0
        
        # Check for threat intelligence metrics
        metrics = [point.labels['metric'] for point in result.data_points]
        assert 'threat_hits' in metrics
        assert 'high_threat_hits' in metrics
        assert 'threat_hit_rate' in metrics
    
    def test_execute_ml_performance_query(self, mock_observability_service):
        """Test executing ML performance query."""
        provider = DashboardDataProvider(mock_observability_service)
        
        query = DashboardQuery(
            metric_type=MetricType.ML_PERFORMANCE,
            time_range=QueryTimeRange.LAST_24_HOURS
        )
        
        result = provider.execute_query(query)
        
        assert isinstance(result, DashboardQueryResult)
        assert len(result.data_points) > 0
        
        # Check for ML performance metrics
        metrics = [point.labels['metric'] for point in result.data_points]
        assert 'nlp_success_rate' in metrics
        assert 'embedding_success_rate' in metrics
    
    def test_execute_geographic_distribution_query(self, mock_observability_service):
        """Test executing geographic distribution query."""
        provider = DashboardDataProvider(mock_observability_service)
        
        query = DashboardQuery(
            metric_type=MetricType.GEOGRAPHIC_DISTRIBUTION,
            time_range=QueryTimeRange.LAST_24_HOURS
        )
        
        result = provider.execute_query(query)
        
        assert isinstance(result, DashboardQueryResult)
        assert len(result.data_points) > 0
        
        # Check for geographic data
        for point in result.data_points:
            assert point.labels['metric'] == 'country_attempts'
            assert 'country' in point.labels
    
    def test_execute_security_alerts_query(self, mock_observability_service):
        """Test executing security alerts query."""
        provider = DashboardDataProvider(mock_observability_service)
        
        query = DashboardQuery(
            metric_type=MetricType.SECURITY_ALERTS,
            time_range=QueryTimeRange.LAST_24_HOURS
        )
        
        result = provider.execute_query(query)
        
        assert isinstance(result, DashboardQueryResult)
        assert len(result.data_points) > 0
        
        # Check for alert severity data
        for point in result.data_points:
            assert point.labels['metric'] == 'alerts'
            assert 'severity' in point.labels
    
    def test_apply_filters(self, mock_observability_service):
        """Test applying filters to query results."""
        provider = DashboardDataProvider(mock_observability_service)
        
        query = DashboardQuery(
            metric_type=MetricType.AUTHENTICATION_ATTEMPTS,
            time_range=QueryTimeRange.LAST_24_HOURS,
            filters={'event_type': 'login_success'}
        )
        
        result = provider.execute_query(query)
        
        # Should have filtered results
        assert isinstance(result, DashboardQueryResult)
    
    def test_apply_limit(self, mock_observability_service):
        """Test applying limit to query results."""
        provider = DashboardDataProvider(mock_observability_service)
        
        query = DashboardQuery(
            metric_type=MetricType.GEOGRAPHIC_DISTRIBUTION,
            time_range=QueryTimeRange.LAST_24_HOURS,
            limit=2
        )
        
        result = provider.execute_query(query)
        
        assert len(result.data_points) <= 2
    
    def test_time_range_conversion(self, mock_observability_service):
        """Test time range conversion to hours."""
        provider = DashboardDataProvider(mock_observability_service)
        
        assert provider._time_range_to_hours(QueryTimeRange.LAST_HOUR) == 1
        assert provider._time_range_to_hours(QueryTimeRange.LAST_6_HOURS) == 6
        assert provider._time_range_to_hours(QueryTimeRange.LAST_24_HOURS) == 24
        assert provider._time_range_to_hours(QueryTimeRange.LAST_7_DAYS) == 168
        assert provider._time_range_to_hours(QueryTimeRange.LAST_30_DAYS) == 720
    
    def test_unsupported_metric_type(self, mock_observability_service):
        """Test handling unsupported metric type."""
        provider = DashboardDataProvider(mock_observability_service)
        
        # Create query with invalid metric type by bypassing enum
        query = DashboardQuery(
            metric_type=MetricType.AUTHENTICATION_ATTEMPTS,  # Will be modified
            time_range=QueryTimeRange.LAST_HOUR
        )
        query.metric_type = "invalid_metric"  # Bypass enum validation
        
        result = provider.execute_query(query)
        
        # Should return empty result without crashing
        assert isinstance(result, DashboardQueryResult)
        assert len(result.data_points) == 0


class TestDashboardExporter:
    """Test DashboardExporter functionality."""
    
    def test_exporter_initialization(self, mock_observability_service):
        """Test DashboardExporter initialization."""
        provider = DashboardDataProvider(mock_observability_service)
        exporter = DashboardExporter(provider)
        
        assert exporter.data_provider == provider
        assert exporter.logger is not None
    
    def test_export_to_csv(self, mock_observability_service):
        """Test exporting query results to CSV."""
        provider = DashboardDataProvider(mock_observability_service)
        exporter = DashboardExporter(provider)
        
        query = DashboardQuery(
            metric_type=MetricType.AUTHENTICATION_ATTEMPTS,
            time_range=QueryTimeRange.LAST_HOUR
        )
        
        csv_data = exporter.export_to_csv(query)
        
        assert isinstance(csv_data, str)
        assert 'timestamp,value,labels,metadata' in csv_data
        lines = csv_data.split('\n')
        assert len(lines) > 1  # Header + data
    
    def test_export_to_json(self, mock_observability_service):
        """Test exporting query results to JSON."""
        provider = DashboardDataProvider(mock_observability_service)
        exporter = DashboardExporter(provider)
        
        query = DashboardQuery(
            metric_type=MetricType.RISK_SCORES,
            time_range=QueryTimeRange.LAST_HOUR
        )
        
        json_data = exporter.export_to_json(query)
        
        assert isinstance(json_data, str)
        parsed_data = json.loads(json_data)
        assert 'query' in parsed_data
        assert 'data_points' in parsed_data
        assert 'total_count' in parsed_data
    
    def test_export_prometheus_format(self, mock_observability_service):
        """Test exporting query results in Prometheus format."""
        provider = DashboardDataProvider(mock_observability_service)
        exporter = DashboardExporter(provider)
        
        query = DashboardQuery(
            metric_type=MetricType.AUTHENTICATION_ATTEMPTS,
            time_range=QueryTimeRange.LAST_HOUR
        )
        
        prometheus_data = exporter.export_prometheus_format(query)
        
        assert isinstance(prometheus_data, str)
        assert '# HELP' in prometheus_data
        assert '# TYPE' in prometheus_data
        assert 'intelligent_auth_auth_attempts' in prometheus_data
    
    def test_export_elasticsearch_bulk(self, mock_observability_service):
        """Test exporting query results in Elasticsearch bulk format."""
        provider = DashboardDataProvider(mock_observability_service)
        exporter = DashboardExporter(provider)
        
        query = DashboardQuery(
            metric_type=MetricType.THREAT_INTELLIGENCE,
            time_range=QueryTimeRange.LAST_HOUR
        )
        
        bulk_data = exporter.export_elasticsearch_bulk(query)
        
        assert isinstance(bulk_data, str)
        lines = bulk_data.strip().split('\n')
        
        # Should have pairs of lines (index action + document)
        assert len(lines) % 2 == 0
        
        # Check format of first pair
        if lines:
            index_action = json.loads(lines[0])
            assert 'index' in index_action
            
            document = json.loads(lines[1])
            assert '@timestamp' in document
            assert 'metric_type' in document
            assert 'value' in document
    
    def test_export_empty_results(self, mock_observability_service):
        """Test exporting empty query results."""
        provider = DashboardDataProvider(mock_observability_service)
        exporter = DashboardExporter(provider)
        
        # Mock empty result
        provider.execute_query = Mock(return_value=DashboardQueryResult(
            query=DashboardQuery(MetricType.AUTHENTICATION_ATTEMPTS, QueryTimeRange.LAST_HOUR),
            data_points=[],
            total_count=0,
            execution_time_ms=10.0,
            generated_at=datetime.now()
        ))
        
        query = DashboardQuery(
            metric_type=MetricType.AUTHENTICATION_ATTEMPTS,
            time_range=QueryTimeRange.LAST_HOUR
        )
        
        csv_data = exporter.export_to_csv(query)
        prometheus_data = exporter.export_prometheus_format(query)
        elasticsearch_data = exporter.export_elasticsearch_bulk(query)
        
        assert csv_data == "timestamp,value,labels,metadata\n"
        assert prometheus_data == ""
        assert elasticsearch_data == ""


class TestCustomQueryInterface:
    """Test CustomQueryInterface functionality."""
    
    def test_custom_query_interface_initialization(self, mock_observability_service):
        """Test CustomQueryInterface initialization."""
        provider = DashboardDataProvider(mock_observability_service)
        interface = CustomQueryInterface(provider)
        
        assert interface.data_provider == provider
        assert interface.logger is not None
    
    def test_execute_custom_query(self, mock_observability_service):
        """Test executing custom query."""
        provider = DashboardDataProvider(mock_observability_service)
        interface = CustomQueryInterface(provider)
        
        query_spec = {
            'metric_type': 'auth_attempts',
            'time_range': '24h',
            'filters': {'country': 'US'},
            'aggregation': 'count',
            'group_by': ['event_type'],
            'limit': 50
        }
        
        result = interface.execute_custom_query(query_spec)
        
        assert isinstance(result, dict)
        assert 'query' in result
        assert 'data_points' in result
        assert 'total_count' in result
    
    def test_execute_custom_query_with_post_processing(self, mock_observability_service):
        """Test executing custom query with post-processing."""
        provider = DashboardDataProvider(mock_observability_service)
        interface = CustomQueryInterface(provider)
        
        query_spec = {
            'metric_type': 'auth_attempts',
            'time_range': '1h',
            'post_processing': {
                'sort_by': 'value',
                'sort_desc': True,
                'calculate_percentiles': True
            }
        }
        
        result = interface.execute_custom_query(query_spec)
        
        assert isinstance(result, dict)
        assert 'data_points' in result
        
        # Should have additional percentile data points
        data_points = result['data_points']
        percentile_points = [dp for dp in data_points if dp.get('labels', {}).get('metric') == 'percentile']
        assert len(percentile_points) > 0
    
    def test_get_available_metrics(self, mock_observability_service):
        """Test getting available metrics."""
        provider = DashboardDataProvider(mock_observability_service)
        interface = CustomQueryInterface(provider)
        
        metrics = interface.get_available_metrics()
        
        assert isinstance(metrics, list)
        assert len(metrics) > 0
        
        for metric in metrics:
            assert 'metric_type' in metric
            assert 'description' in metric
            assert 'supported_aggregations' in metric
            assert 'available_labels' in metric
    
    def test_execute_custom_query_error_handling(self, mock_observability_service):
        """Test custom query error handling."""
        provider = DashboardDataProvider(mock_observability_service)
        interface = CustomQueryInterface(provider)
        
        # Invalid query spec
        query_spec = {
            'metric_type': 'invalid_metric',
            'time_range': 'invalid_range'
        }
        
        result = interface.execute_custom_query(query_spec)
        
        assert isinstance(result, dict)
        assert 'error' in result
        assert 'query_spec' in result


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_create_dashboard_data_provider(self, mock_observability_service):
        """Test create_dashboard_data_provider function."""
        provider = create_dashboard_data_provider(mock_observability_service)
        
        assert isinstance(provider, DashboardDataProvider)
        assert provider.observability_service == mock_observability_service
    
    def test_create_dashboard_exporter(self, mock_observability_service):
        """Test create_dashboard_exporter function."""
        provider = DashboardDataProvider(mock_observability_service)
        exporter = create_dashboard_exporter(provider)
        
        assert isinstance(exporter, DashboardExporter)
        assert exporter.data_provider == provider
    
    def test_create_custom_query_interface(self, mock_observability_service):
        """Test create_custom_query_interface function."""
        provider = DashboardDataProvider(mock_observability_service)
        interface = create_custom_query_interface(provider)
        
        assert isinstance(interface, CustomQueryInterface)
        assert interface.data_provider == provider
    
    def test_get_grafana_dashboard_templates(self):
        """Test get_grafana_dashboard_templates function."""
        templates = get_grafana_dashboard_templates()
        
        assert isinstance(templates, dict)
        assert 'authentication_overview' in templates
        assert 'security_monitoring' in templates
        assert 'ml_performance' in templates
        
        for template_name, template_data in templates.items():
            assert 'dashboard' in template_data
            assert 'title' in template_data['dashboard']
            assert 'panels' in template_data['dashboard']


class TestIntegration:
    """Integration tests for dashboard functionality."""
    
    def test_full_dashboard_workflow(self, mock_observability_service):
        """Test complete dashboard workflow."""
        # Create components
        provider = create_dashboard_data_provider(mock_observability_service)
        exporter = create_dashboard_exporter(provider)
        interface = create_custom_query_interface(provider)
        
        # Execute query
        query = DashboardQuery(
            metric_type=MetricType.AUTHENTICATION_ATTEMPTS,
            time_range=QueryTimeRange.LAST_24_HOURS,
            group_by=['event_type']
        )
        
        result = provider.execute_query(query)
        
        # Export in different formats
        csv_data = exporter.export_to_csv(query)
        json_data = exporter.export_to_json(query)
        prometheus_data = exporter.export_prometheus_format(query)
        
        # Execute custom query
        custom_result = interface.execute_custom_query({
            'metric_type': 'auth_attempts',
            'time_range': '24h',
            'aggregation': 'count'
        })
        
        # Verify all components work together
        assert isinstance(result, DashboardQueryResult)
        assert isinstance(csv_data, str)
        assert isinstance(json_data, str)
        assert isinstance(prometheus_data, str)
        assert isinstance(custom_result, dict)
    
    def test_grafana_template_integration(self):
        """Test Grafana template integration."""
        templates = get_grafana_dashboard_templates()
        
        # Verify templates are valid JSON structures
        for template_name, template_data in templates.items():
            # Should be serializable to JSON
            json_str = json.dumps(template_data)
            parsed = json.loads(json_str)
            
            assert parsed == template_data
            assert 'dashboard' in parsed
            assert 'panels' in parsed['dashboard']
    
    def test_multi_metric_dashboard_query(self, mock_observability_service):
        """Test querying multiple metrics for comprehensive dashboard."""
        provider = create_dashboard_data_provider(mock_observability_service)
        
        metrics_to_query = [
            MetricType.AUTHENTICATION_ATTEMPTS,
            MetricType.RISK_SCORES,
            MetricType.THREAT_INTELLIGENCE,
            MetricType.ML_PERFORMANCE
        ]
        
        results = {}
        for metric_type in metrics_to_query:
            query = DashboardQuery(
                metric_type=metric_type,
                time_range=QueryTimeRange.LAST_24_HOURS
            )
            results[metric_type.value] = provider.execute_query(query)
        
        # Verify all queries executed successfully
        assert len(results) == len(metrics_to_query)
        for metric_name, result in results.items():
            assert isinstance(result, DashboardQueryResult)
            assert result.execution_time_ms >= 0


if __name__ == "__main__":
    pytest.main([__file__])