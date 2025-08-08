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

### Required Settings

The server requires two critical environment variables:

* `DATABASE_URL` – connection string to your PostgreSQL (or other supported) database
* `SECRET_KEY` – secret used for token signing

Provide them before starting the application:

```bash
export DATABASE_URL="postgresql://user:pass@db:5432/kari"
export SECRET_KEY="your-production-secret"
```

The application will fail fast at startup if either value is missing.

### Debug Mode

Debug logging is disabled by default. Set `DEBUG=true` to enable verbose output during development.
