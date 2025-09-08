# Kari Helm Chart

This chart deploys the Kari API as a single pod with basic service exposure. The deployment includes health probes and metrics annotations for Prometheus.

## Features

- **Liveness and Readiness:** Kubernetes probes call `/livez` and `/readyz` on the container.
- **Metrics Exposure:** `/metrics` is exposed through the service so Prometheus can scrape metrics.
- **Secure Service Account:** Pod runs under its own minimal service account.

## Usage

```bash
helm install kari ./charts/kari
```

Set `image.repository`, `image.tag`, or `service.port` in `values.yaml` to match your environment.
