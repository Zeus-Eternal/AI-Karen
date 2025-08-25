# Troubleshooting Guide

This short guide covers common issues when running Kari in development or production.

## Services Fail to Start

1. Ensure Docker is running and you have enough free memory.
2. Check each container's logs with `docker compose logs <service>`.
3. Delete any leftover volumes and retry:
   ```bash
   docker compose down -v
   docker compose up -d
   ```

## Cannot Access the API

Confirm the backend container is healthy by visiting `http://localhost:8000/ping`.
If the service is not reachable, verify that port **8000** is exposed and not blocked by a firewall.

## Database Errors

If migrations fail, run:
```bash
python scripts/install.sh --migrate
```
This will apply the latest Alembic migrations.

For further help, open an issue and include the output of `python scripts/doc_analysis.py`.
