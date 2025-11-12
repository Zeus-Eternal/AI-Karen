# Model Orchestrator Monitoring

This directory contains comprehensive monitoring configuration for the Model Orchestrator plugin, integrating with Kari's existing monitoring infrastructure.

## Overview

The Model Orchestrator monitoring system provides:

- **Prometheus Metrics**: Comprehensive metrics collection for model operations
- **Grafana Dashboards**: Rich visualizations for monitoring model orchestrator health
- **Alert Rules**: Proactive alerting for issues and SLA breaches
- **Structured Logging**: Centralized logging with audit trails
- **Health Checks**: Integration with existing health monitoring

## Components

### Prometheus Configuration

- **File**: `prometheus.yml`
- **Scrape Endpoints**:
  - `/api/models/metrics` - Core model orchestrator metrics
  - `/api/models/health/metrics` - Health check metrics
- **Scrape Interval**: 30 seconds for model operations, 60 seconds for health

### Grafana Dashboards

- **File**: `model_orchestrator_dashboard.json`
  - **Panels**:
    - Model Operations Overview
    - Download Success Rate
    - Storage Usage
    - Health Status
    - Download Operations & Duration
    - Models by Library
    - Storage by Library
    - Active Downloads
    - Registry Operations
    - Error Rates
    - License Compliance
    - Garbage Collection
- **File**: `llamacpp_runtime_dashboard.json`
  - **Panels**:
    - Chat Response Latency (p95)
    - Llama-CPP Inference Latency (p95)
    - Tokens Per Second
    - Memory Fetch Latency
    - Fallback Activation Rate
    - System Load & GPU Utilization
    - Tokens Used Per Response

### Alert Rules

- **File**: `model_orchestrator_alerts.yml`
- **Alert Groups**:
  - `model_orchestrator_alerts` - Operational alerts
  - `model_orchestrator_sla` - SLA monitoring
- **Key Alerts**:
  - Model download failures
  - Storage space warnings
  - Registry corruption
  - High operation latency
  - License violations
  - Health check failures

### Logging Configuration

- **File**: `../config/model_orchestrator_logging.yml`
- **Log Files**:
  - `model_orchestrator.log` - General operations
  - `model_orchestrator_audit.log` - Audit trail
  - `model_orchestrator_errors.log` - Error tracking
- **Integration**: Elasticsearch for log aggregation

## Metrics

### Core Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `model_orchestrator_downloads_total` | Counter | Total model downloads |
| `model_orchestrator_downloads_successful_total` | Counter | Successful downloads |
| `model_orchestrator_downloads_failed_total` | Counter | Failed downloads |
| `model_orchestrator_download_duration_seconds` | Histogram | Download duration |
| `model_orchestrator_models_total` | Gauge | Total models installed |
| `model_orchestrator_storage_usage_bytes` | Gauge | Storage usage |
| `model_orchestrator_storage_limit_bytes` | Gauge | Storage limit |
| `model_orchestrator_concurrent_downloads` | Gauge | Active downloads |
| `model_orchestrator_health_status` | Gauge | Health check status |
| `model_orchestrator_registry_integrity_check` | Gauge | Registry integrity |

### Performance Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `model_orchestrator_operation_duration_seconds` | Histogram | Operation latency |
| `model_orchestrator_registry_reads_total` | Counter | Registry read operations |
| `model_orchestrator_registry_writes_total` | Counter | Registry write operations |
| `model_orchestrator_errors_total` | Counter | Error count by type |

### Business Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `model_orchestrator_license_acceptances_total` | Counter | License acceptances |
| `model_orchestrator_license_violations_total` | Counter | License violations |
| `model_orchestrator_gc_runs_total` | Counter | Garbage collection runs |
| `model_orchestrator_gc_models_removed_total` | Counter | Models removed by GC |
| `model_orchestrator_gc_space_freed_bytes` | Counter | Space freed by GC |

## Alerts

### Critical Alerts

- **ModelRegistryCorrupted**: Registry integrity check failed
- **ModelStorageSpaceCritical**: Storage >95% full
- **ModelOrchestratorUnhealthy**: Health checks failing
- **UnacceptedLicenseDownload**: License violations detected

### Warning Alerts

- **ModelDownloadFailed**: Download operations failing
- **ModelStorageSpaceLow**: Storage >85% full
- **HighModelDownloadConcurrency**: Too many concurrent downloads
- **ModelOperationLatencyHigh**: Operations taking too long

### SLA Alerts

- **ModelDownloadSLABreach**: Download success rate <95%
- **ModelOperationAvailabilitySLA**: Operation availability <99%

## Setup

### Automatic Setup

Run the monitoring setup script:

```bash
python scripts/monitoring/setup_model_orchestrator_monitoring.py
```

### Manual Setup

1. **Prometheus**: Ensure `prometheus.yml` includes model orchestrator scrape configs
2. **Grafana**: Import `model_orchestrator_dashboard.json` and `llamacpp_runtime_dashboard.json`
3. **Alerts**: Load `model_orchestrator_alerts.yml` into Prometheus
4. **Logging**: Configure logging with `model_orchestrator_logging.yml`

### Grafana Production Readiness

To operate Grafana in production with enterprise capabilities enabled:

1. **Provision Dashboards**
   - Mount `monitoring/model_orchestrator_dashboard.json` to `/etc/grafana/provisioning/dashboards/model-orchestrator/`.
   - Mount `monitoring/llamacpp_runtime_dashboard.json` to `/etc/grafana/provisioning/dashboards/llamacpp-runtime/`.
   - Mount `monitoring/grafana_provisioning.yml` to `/etc/grafana/provisioning/`.
2. **Apply Enterprise License**
   - Set `GF_ENTERPRISE_LICENSE_TEXT` or `GF_ENTERPRISE_LICENSE_PATH` before starting Grafana.
   - Confirm **Administration → License** in Grafana shows status `Active` and matches the production organization.
3. **Enable Required Features**
   - Enable and configure enterprise reporting, alerting, RBAC, and SSO/SCIM integrations as mandated by Kari AI policy.
   - Provide SMTP credentials for scheduled reports and validate Slack/email notifiers defined in `grafana_provisioning.yml`.
4. **Harden Access**
   - Enforce SSO/SAML groups, SCIM provisioning, and per-folder RBAC (e.g., `Runtime Intelligence`, `Model Orchestrator`).
   - Require API tokens to use service accounts with least privilege for automation.
5. **Health Validation**
   - Verify `GET http://<grafana-host>/api/health` returns `{"database":"ok"}`.
   - Validate Prometheus datasource status and dashboard refresh without permission errors.
   - Generate an on-demand PDF/CSV report from the Llama-CPP dashboard to confirm enterprise licensing is functional.

### Docker Compose

The monitoring stack is integrated into `docker-compose.yml`:

```bash
docker-compose up -d prometheus grafana elasticsearch
```

## Access

- **Grafana Dashboard**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Health Check**: http://localhost:8000/health
- **Metrics Endpoint**: http://localhost:8000/api/models/metrics

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MODEL_ORCHESTRATOR_ENABLE_METRICS` | Enable metrics collection | `true` |
| `MODEL_ORCHESTRATOR_HEALTH_CHECK_INTERVAL` | Health check interval (seconds) | `60` |
| `GRAFANA_ADMIN_PASSWORD` | Grafana admin password | `admin` |
| `SLACK_WEBHOOK_URL` | Slack webhook for alerts | - |
| `ALERT_EMAIL_ADDRESSES` | Email addresses for alerts | - |

### Customization

- **Metrics**: Modify scrape intervals in `prometheus.yml`
- **Dashboards**: Customize panels in `model_orchestrator_dashboard.json`
- **Alerts**: Adjust thresholds in `model_orchestrator_alerts.yml`
- **Logging**: Configure log levels in `model_orchestrator_logging.yml`

## Troubleshooting

### Common Issues

1. **Metrics not appearing**: Check Prometheus scrape targets
2. **Dashboard not loading**: Verify Grafana provisioning
3. **Alerts not firing**: Check alert rule syntax
4. **Logs not aggregating**: Verify Elasticsearch connection

### Debug Commands

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check model orchestrator health
curl http://localhost:8000/health | jq .model_orchestrator

# Check metrics endpoint
curl http://localhost:8000/api/models/metrics

# View logs
docker logs ai-karen-api | grep model_orchestrator
```

## Maintenance

### Log Rotation

Logs are automatically rotated:
- **Size**: 10MB per file
- **Retention**: 5-10 backup files
- **Compression**: Enabled for archived logs

### Metric Retention

Prometheus retention (configurable):
- **Default**: 15 days
- **Production**: 90 days recommended

### Dashboard Updates

Dashboard updates are automatically provisioned when the container restarts.

## Security

### Access Control

- Grafana requires authentication
- Prometheus metrics may contain sensitive information
- Audit logs contain user activity

### Data Protection

- Logs are structured to avoid PII exposure
- Sensitive fields are automatically redacted
- Audit logs have extended retention for compliance

## Support

For issues with Model Orchestrator monitoring:

1. Check the monitoring setup script output
2. Review container logs for errors
3. Verify configuration files syntax
4. Test individual components (Prometheus, Grafana, etc.)

## Integration

This monitoring system integrates with:

- **Existing Kari health checks**: `/health` endpoint
- **Service registry**: Plugin status reporting
- **Authentication system**: User context in logs
- **Error tracking**: Centralized error reporting
- **Audit system**: Compliance and security logging