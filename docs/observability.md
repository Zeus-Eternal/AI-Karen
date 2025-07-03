# Observability

Kari exposes metrics and traces so operators can monitor performance.

## Prometheus Metrics

Metrics are gathered in memory and exposed at `/metrics` in JSON and `/metrics/prometheus` for Prometheus text format.

Example metrics:

- `embedding_time_seconds`
- `vector_upsert_seconds`
- `vector_search_latency_seconds`

Use `docker compose up` to start a Prometheus container that scrapes `http://localhost:8000/metrics`.

## Tracing

The reference code emits minimal traces through `print()` statements. In production you can integrate OpenTelemetry and send traces to Tempo or Jaeger.

## Dashboards

Grafana dashboards should include:

| Panel | Metric |
| ----- | ------ |
| Embedding Latency | `embedding_time_seconds` |
| Vector Search     | `vector_search_latency_seconds` |
| Memory Usage      | Custom Python gauge or system metric |

See `ui/desktop_ui/README.md` for adding the metrics dashboard to the Control Room.
The new Diagnostics page surfaces the output of `get_system_health()` with a JSON viewer.
