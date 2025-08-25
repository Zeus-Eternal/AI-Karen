# Observability

Kari exposes metrics and traces so operators can monitor performance.

## Prometheus Metrics

Metrics are gathered in memory and exposed at `/metrics` in JSON and `/metrics/prometheus` for Prometheus text format.

Example metrics:

- `embedding_time_seconds`
- `vector_upsert_seconds`
- `vector_search_latency_seconds`
- `memory_store_total`
- `memory_recall_total`
- `plugin_exec_total`
- `document_index_total`
- `document_search_total`
- `doc_chunks_indexed`
- `doc_search_latency`
- `metadata_hit_rate`

Use `docker compose up` to start a Prometheus container that scrapes `http://localhost:8000/metrics`.

### Health Check SLO Metrics

The core health monitor exposes latency and availability metrics for each
registered service:

- `health_check_latency_seconds{check="<name>"}`
- `health_check_availability{check="<name>"}`

These are scraped by the Prometheus service defined in
`monitoring/prometheus.yml`. Alert rules for SLO breaches live in
`monitoring/alert_rules.yml`.

Run `docker compose up prometheus grafana` to persist metrics and view the
included `monitoring/grafana_dashboard.json` for real-time SLO compliance.

## Tracing

The reference code emits minimal traces through `print()` statements. In production you can integrate OpenTelemetry and send traces to Tempo or Jaeger.

## Dashboards

Grafana dashboards should include:

| Panel | Metric |
| ----- | ------ |
| Embedding Latency | `embedding_time_seconds` |
| Vector Search     | `vector_search_latency_seconds` |
| Memory Usage      | Custom Python gauge or system metric |
| Memory Stores     | `memory_store_total` |
| Memory Recalls    | `memory_recall_total` |
| Plugin Calls      | `plugin_exec_total` |
| Doc Indexes       | `document_index_total` |
| Doc Searches      | `document_search_total` |

See `ui_launchers/desktop_ui/README.md` for adding the metrics dashboard to the Control Room.
The new Diagnostics page surfaces the output of `get_system_health()` with a JSON viewer.

### Grafana Dashboard JSON

Import the following snippet into Grafana to create a basic dashboard:

```json
{
  "title": "Kari Metrics",
  "panels": [
    {"type": "graph", "title": "Requests", "targets": [{"expr": "kari_http_requests_total"}]},
    {"type": "graph", "title": "Memory Stores", "targets": [{"expr": "memory_store_total"}]},
    {"type": "graph", "title": "Memory Recalls", "targets": [{"expr": "memory_recall_total"}]},
    {"type": "graph", "title": "Plugin Calls", "targets": [{"expr": "plugin_exec_total"}]},
    {"type": "graph", "title": "Doc Searches", "targets": [{"expr": "document_search_total"}]}
  ]
}
```
