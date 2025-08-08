# Deployment Guide

This document provides a high level overview of how to deploy the Kari AI platform in a production environment.

## Docker Compose

The fastest way to get Kari running is with Docker Compose. The repository includes a `docker-compose.yml` file which starts the API, databases and optional services.

```bash
# Start the full stack in the background
docker compose up -d
```

The API will be available on port **8000** and the default web interface on port **9002**.

## Kubernetes

A lightweight Helm chart is included under `src/charts/kari`. It deploys the API with health probes and Prometheus metrics.

```bash
helm install my-kari src/charts/kari
```

Be sure to provision PostgreSQL, Redis and any vector stores before installing the chart.

## Configuration

Runtime settings are controlled via environment variables or the `config.json` file. Review `config/README.md` for parameter descriptions.

### Required Environment Variables

For security and database connectivity, the server **requires** certain settings to be supplied via environment variables. Set them before starting the application:

```bash
export SECRET_KEY="your-production-secret"
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

Deployments missing these values will fail to start.

Debug features are disabled by default. To enable interactive docs and hot reload, set:

```bash
export DEBUG=true
```

