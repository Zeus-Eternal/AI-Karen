# KAREN-Theme-Enterprise UI - Launch Guide

## Problem Solved

The original docker-compose.yml in `ui_launchers/KAREN-Theme-Enterprise/docker/` referenced a non-existent `kari-backend:latest` image, causing the launch to fail.

## Solution

Created a new docker-compose configuration that properly integrates the Enterprise Theme UI with the main AI-Karen backend stack.

## Quick Start

### ⭐ RECOMMENDED: Development Mode (Fastest, with Hot-Reload)

```bash
# From the project root
docker compose -f docker-compose.yml -f docker-compose.enterprise-dev.yml up -d
```

**Why Development Mode?**
- ✅ No build timeouts
- ✅ Hot-reload enabled for instant updates
- ✅ Uses existing node_modules
- ✅ Faster startup time
- ✅ Easier debugging

### Alternative 1: Using the Launch Script

```bash
# From the project root
./launch_enterprise_ui.sh -d
```

**Note:** The launch script currently uses the production configuration which may have build timeout issues. Development mode is recommended.

### Alternative 2: Production Build (Slower, Not Recommended)

```bash
# From the project root
docker compose -f docker-compose.yml -f docker-compose.enterprise.yml up -d --build
```

**Note:** This may timeout due to large build size. Use development mode instead.

**Stop services:**
```bash
docker compose -f docker-compose.yml -f docker-compose.enterprise.yml down
```

**View logs:**
```bash
docker compose -f docker-compose.yml -f docker-compose.enterprise.yml logs -f enterprise-ui
```

## What Gets Launched

The configuration launches these services:

1. **enterprise-ui** (port 3000) - The Enterprise Theme Next.js UI
2. **api** (port 8000) - AI-Karen FastAPI backend
3. **postgres** (port 5433) - PostgreSQL database
4. **redis** (port 6380) - Redis cache
5. **elasticsearch** (port 9200) - Search engine
6. **milvus** (port 19531) - Vector database
7. **prometheus** (port 9090) - Metrics collection
8. **grafana** (port 3001) - Monitoring dashboard

Plus supporting services (milvus-etcd, milvus-minio).

## Access Points

After launching with **development mode**, access the services at:

- **Enterprise UI**: http://localhost:9002 (development mode with hot-reload)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboard**: http://localhost:3001 (if started)
- **Prometheus**: http://localhost:9090

## Architecture

The solution uses Docker Compose's multi-file override feature:

1. **docker-compose.yml** - Base configuration with all backend services
2. **docker-compose.enterprise.yml** - Adds the Enterprise Theme UI service

The Enterprise UI service:
- Builds from `./ui_launchers/KAREN-Theme-Enterprise/docker/Dockerfile`
- Connects to the `api` service internally (http://api:8000)
- Exposes port 3000 for browser access
- Depends on the API service being healthy

## Troubleshooting

### Port Already in Use

If port 3000 is already in use:

```bash
# Check what's using the port
lsof -i :3000

# Either stop the conflicting service or change the port in docker-compose.enterprise.yml
```

### Build Failures

If the Enterprise UI build fails:

```bash
# Try building manually to see detailed errors
cd ui_launchers/KAREN-Theme-Enterprise
docker build -f docker/Dockerfile -t karen-enterprise-ui .

# Or rebuild with no cache
docker compose -f docker-compose.yml -f docker-compose.enterprise.yml build --no-cache enterprise-ui
```

### Backend Not Starting

If the API service fails to start:

```bash
# Check backend logs
docker compose -f docker-compose.yml -f docker-compose.enterprise.yml logs -f api

# Verify database is healthy
docker compose -f docker-compose.yml -f docker-compose.enterprise.yml ps postgres
```

### Service Health Checks

```bash
# Check all service statuses
docker compose -f docker-compose.yml -f docker-compose.enterprise.yml ps

# Check specific service health
docker inspect karen-enterprise-ui | grep -A 10 Health
```

## File Structure

```
/mnt/Development/KIRO/AI-Karen/
├── docker-compose.yml                  # Base backend services
├── docker-compose.enterprise.yml       # Enterprise UI overlay
├── launch_enterprise_ui.sh            # Convenience launch script
└── ui_launchers/
    └── KAREN-Theme-Enterprise/
        ├── docker/
        │   ├── Dockerfile              # Enterprise UI image build
        │   ├── docker-compose.yml      # (Original - not used from root)
        │   └── docker-compose.production.yml
        └── ... (UI source code)
```

## Development vs Production

### Development Mode
```bash
# Use the launch script for development
./launch_enterprise_ui.sh -d
```
- Hot-reload enabled
- Debug logging
- Lower resource limits

### Production Deployment
For production, use the standalone production compose file in the UI directory:

```bash
cd ui_launchers/KAREN-Theme-Enterprise/docker
docker compose -f docker-compose.production.yml up -d
```

**Note**: The production configuration includes:
- Nginx reverse proxy
- SSL/TLS support
- Resource limits
- Health checks
- Monitoring stack (Prometheus, Grafana, cAdvisor)

## Next Steps

1. Ensure your `.env` file is configured properly
2. Run `./launch_enterprise_ui.sh -d -b` to start
3. Access the UI at http://localhost:3000
4. Check logs if needed: `docker compose logs -f enterprise-ui`

## Related Documentation

- [Main README.md](../README.md) - Project overview
- [docker-compose.yml](../docker-compose.yml) - Backend services configuration
- [KAREN-Theme-Enterprise README](./ui_launchers/KAREN-Theme-Enterprise/README.md) - UI-specific documentation
