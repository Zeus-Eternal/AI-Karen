# HTTP Request Validation Monitoring Guide

This guide explains the comprehensive monitoring and metrics system for the HTTP request validation framework, including Prometheus metrics, Grafana dashboards, and alerting rules.

## Overview

The validation monitoring system provides real-time visibility into:
- HTTP request validation events
- Security threat detection and analysis
- Rate limiting effectiveness
- System performance and health
- Client behavior patterns
- Attack pattern recognition

## Metrics Categories

### 1. Core Validation Metrics

#### `http_validation_requests_total`
- **Type**: Counter
- **Description**: Total HTTP validation requests processed
- **Labels**: `event_type`, `validation_rule`, `endpoint`, `method`, `result`
- **Usage**: Track overall validation activity and success rates

#### `http_validation_duration_seconds`
- **Type**: Histogram
- **Description**: Time spent on HTTP request validation
- **Labels**: `validation_rule`, `endpoint`, `method`
- **Buckets**: 0.001s to 5.0s
- **Usage**: Monitor validation performance and identify bottlenecks

### 2. Security Threat Metrics

#### `http_security_threats_total`
- **Type**: Counter
- **Description**: Total security threats detected
- **Labels**: `threat_level`, `attack_category`, `endpoint`, `method`, `client_reputation`
- **Usage**: Track security incidents and threat patterns

#### `http_security_threat_confidence`
- **Type**: Histogram
- **Description**: Confidence score of security threat detection
- **Labels**: `threat_level`, `attack_category`
- **Buckets**: 0.1 to 1.0
- **Usage**: Assess accuracy of threat detection

#### `http_blocked_requests_total`
- **Type**: Counter
- **Description**: Total blocked requests by reason
- **Labels**: `block_reason`, `threat_level`, `endpoint`, `method`
- **Usage**: Monitor blocking effectiveness

### 3. Attack Pattern Metrics

#### `http_attack_patterns_detected_total`
- **Type**: Counter
- **Description**: Total attack patterns detected by type
- **Labels**: `pattern_type`, `pattern_category`, `endpoint`, `method`
- **Usage**: Identify common attack vectors

#### `http_attack_pattern_frequency`
- **Type**: Histogram
- **Description**: Frequency of attack patterns per request
- **Labels**: `pattern_category`
- **Buckets**: 1 to 100 patterns
- **Usage**: Detect coordinated attacks

### 4. Rate Limiting Metrics

#### `http_rate_limit_events_total`
- **Type**: Counter
- **Description**: Total rate limiting events
- **Labels**: `rule_name`, `scope`, `algorithm`, `action`, `endpoint`
- **Usage**: Monitor rate limiting effectiveness

#### `http_rate_limit_current_usage`
- **Type**: Gauge
- **Description**: Current rate limit usage as percentage of limit
- **Labels**: `rule_name`, `scope`, `client_hash`, `endpoint`
- **Usage**: Track real-time rate limit consumption

### 5. Client Behavior Metrics

#### `http_client_reputation_score`
- **Type**: Histogram
- **Description**: Client reputation scores
- **Labels**: `reputation_category`, `endpoint`
- **Buckets**: 0.0 to 1.0
- **Usage**: Monitor client trustworthiness

#### `http_suspicious_clients_total`
- **Type**: Counter
- **Description**: Total suspicious client activities
- **Labels**: `activity_type`, `reputation`, `endpoint`
- **Usage**: Track suspicious behavior patterns

### 6. System Health Metrics

#### `http_validation_system_health`
- **Type**: Gauge
- **Description**: Validation system health status (1=healthy, 0=unhealthy)
- **Labels**: `component`
- **Usage**: Monitor system component health

#### `http_validation_errors_total`
- **Type**: Counter
- **Description**: Total validation system errors
- **Labels**: `error_type`, `component`, `severity`
- **Usage**: Track system errors and reliability

## Dashboards

### 1. HTTP Request Validation System Dashboard
**File**: `monitoring/validation_system_dashboard.json`

**Panels**:
- Validation Overview (request rate)
- Validation Results (success/failure ratio)
- Security Threats by Level (time series)
- Attack Patterns Detected (bar gauge)
- Rate Limiting Events (time series)
- Validation Performance (latency percentiles)
- Client Reputation Distribution
- Top Blocked Endpoints
- System Health Status
- Request Size Distribution
- User Agent Categories
- Threat Intelligence Statistics
- Validation Events by Hour (heatmap)

### 2. Security Monitoring Dashboard
**File**: `monitoring/security_monitoring_dashboard.json`

**Panels**:
- Security Threat Level Overview
- Real-time Security Events
- Attack Categories Distribution
- Top Attacked Endpoints
- Client Reputation Analysis
- Security Tool Detection
- Threat Confidence Scores
- Rate Limiting Effectiveness
- Geographic Threat Heatmap
- Attack Pattern Timeline
- Suspicious Activity Indicators
- Threat Intelligence Growth

## Alerting Rules

### Critical Security Alerts

#### `CriticalSecurityThreatDetected`
- **Condition**: Any critical-level security threats detected
- **Severity**: Critical
- **Action**: Immediate investigation required

#### `HighVolumeSecurityThreats`
- **Condition**: >10 high/critical threats per second for 2 minutes
- **Severity**: Critical
- **Action**: Possible coordinated attack

#### `CoordinatedAttackSuspected`
- **Condition**: Multiple endpoints under attack simultaneously
- **Severity**: Critical
- **Action**: Activate incident response

### Attack-Specific Alerts

#### `SQLInjectionAttackDetected`
- **Condition**: >5 SQL injection patterns per second
- **Severity**: High
- **Action**: Review blocked requests, consider IP blocking

#### `XSSAttackDetected`
- **Condition**: >10 XSS patterns per second for 2 minutes
- **Severity**: High
- **Action**: Monitor for escalation

#### `AuthEndpointAbuse`
- **Condition**: >5 auth endpoint rate limits per second
- **Severity**: High
- **Action**: Possible brute force attack

### System Health Alerts

#### `ValidationSystemUnhealthy`
- **Condition**: Any validation component unhealthy
- **Severity**: Critical
- **Action**: System may not be protecting against threats

#### `ValidationPerformanceDegraded`
- **Condition**: 95th percentile latency >100ms for 5 minutes
- **Severity**: Warning
- **Action**: Performance investigation needed

## API Endpoints

### Metrics and Health

#### `GET /api/validation/metrics/summary`
Get validation metrics summary
```json
{
  "status": "success",
  "timestamp": "2024-01-01T12:00:00Z",
  "metrics_summary": {
    "collector_uptime_seconds": 3600,
    "metrics_registered": 25,
    "prometheus_available": true
  }
}
```

#### `GET /api/validation/health`
Get system health status
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "components": {
    "metrics_collector": "healthy",
    "validation_system": "healthy",
    "prometheus_integration": "healthy"
  }
}
```

### Testing and Debugging

#### `POST /api/validation/test/security-event`
Generate test security events for monitoring verification
```bash
curl -X POST "/api/validation/test/security-event?threat_level=high&attack_type=sql_injection"
```

#### `POST /api/validation/test/rate-limit-event`
Generate test rate limit events
```bash
curl -X POST "/api/validation/test/rate-limit-event?rule_name=test_rule&scope=ip"
```

#### `GET /api/validation/debug/metrics-list`
List all available metrics with descriptions

### Statistics

#### `GET /api/validation/stats/threats?hours=24`
Get threat statistics for specified time period

## Configuration

### Prometheus Configuration
**File**: `monitoring/prometheus.yml`

```yaml
scrape_configs:
  - job_name: 'validation-system'
    metrics_path: /metrics/prometheus
    static_configs:
      - targets: ['api:8000']
    scrape_interval: 10s
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'http_validation_.*|http_security_.*|http_rate_limit_.*'
        target_label: component
        replacement: 'validation_system'
```

### Alert Rules
**File**: `monitoring/validation_security_alerts.yml`

Contains comprehensive alerting rules for:
- Critical security threats
- Attack pattern detection
- Rate limiting events
- System health monitoring
- Performance degradation
- Coordinated attack detection

## Best Practices

### 1. Metric Cardinality Management
- Endpoints are sanitized to prevent cardinality explosion
- Client IPs are hashed for privacy
- Dynamic segments are replaced with placeholders
- Cache is used to optimize performance

### 2. Performance Optimization
- Metrics collection is non-blocking
- Cache cleanup prevents memory leaks
- Batch processing for high-volume events
- Graceful degradation when Prometheus unavailable

### 3. Security Considerations
- Client IPs are hashed, not stored in plain text
- Sensitive headers are redacted in logs
- Threat intelligence data is anonymized
- Rate limiting prevents metrics DoS

### 4. Monitoring Strategy
- Use multiple dashboard views for different audiences
- Set up progressive alerting (info → warning → critical)
- Monitor both technical and business metrics
- Regular review of alert thresholds

## Troubleshooting

### Common Issues

#### High Cardinality Metrics
**Symptoms**: Prometheus performance issues, high memory usage
**Solution**: Review endpoint sanitization, check for unbounded labels

#### Missing Metrics
**Symptoms**: Dashboards show no data
**Solution**: Check Prometheus scraping, verify metrics registration

#### False Positive Alerts
**Symptoms**: Too many alerts, alert fatigue
**Solution**: Adjust thresholds, add context to alert conditions

#### Performance Impact
**Symptoms**: Validation latency increased
**Solution**: Optimize metrics collection, check for blocking operations

### Debugging Commands

```bash
# Check metrics endpoint
curl http://localhost:8000/metrics/prometheus | grep http_validation

# Test security event generation
curl -X POST "http://localhost:8000/api/validation/test/security-event?threat_level=high"

# Check system health
curl http://localhost:8000/api/validation/health

# Get metrics summary
curl http://localhost:8000/api/validation/metrics/summary
```

## Integration Examples

### Custom Alert Integration
```python
from ai_karen_engine.monitoring.validation_metrics import record_validation_event, ValidationEventType, ThreatLevel

# Record custom security event
record_validation_event(
    event_type=ValidationEventType.SECURITY_THREAT_DETECTED,
    threat_level=ThreatLevel.HIGH,
    validation_rule="custom_rule",
    client_ip_hash="hashed_ip",
    endpoint="/api/sensitive",
    attack_categories=["custom_attack"],
    additional_labels={"custom_field": "value"}
)
```

### Dashboard Customization
1. Import dashboard JSON into Grafana
2. Customize panels for your specific needs
3. Add organization-specific metrics
4. Configure alerting channels (Slack, email, PagerDuty)

### Metric Export
```python
# Get validation metrics collector
from ai_karen_engine.monitoring.validation_metrics import get_validation_metrics_collector

collector = get_validation_metrics_collector()
summary = collector.get_metrics_summary()
```

This monitoring system provides comprehensive visibility into the HTTP request validation framework, enabling proactive security monitoring and performance optimization.