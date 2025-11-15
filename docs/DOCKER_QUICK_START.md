# AI-Karen Docker Quick Start Guide

This guide will help you get AI-Karen running with Docker Compose.

## Prerequisites

- Docker 20.10+ and Docker Compose V2
- At least 8GB RAM (16GB+ recommended)
- 20GB free disk space

## Quick Start (3 steps)

### 1. Configure Environment

The `.env` file has been created with default values. **You should change the passwords before production use!**

```bash
# Edit the .env file to set secure passwords
nano .env
```

Key variables to customize:
- `POSTGRES_PASSWORD` - PostgreSQL database password
- `REDIS_PASSWORD` - Redis password
- `AUTH_SECRET_KEY` - JWT secret for authentication
- `GRAFANA_ADMIN_PASSWORD` - Grafana admin password

### 2. Start Core Services

Start all services except the optional local LLM:

```bash
docker compose up -d
```

This will start:
- **PostgreSQL** - Primary database (port 5433)
- **Redis** - Caching and rate limiting (port 6380)
- **Elasticsearch** - Search and analytics (port 9200)
- **Milvus** - Vector database (port 19530)
  - Includes: etcd, MinIO
- **Prometheus** - Metrics collection (port 9090)
- **Grafana** - Monitoring dashboard (port 3001)
- **API** - FastAPI backend (port 8000)
- **Web** - Next.js frontend (port 8010)

### 3. Verify Services

Check that all services are running:

```bash
docker compose ps
```

Wait for all services to report as "healthy":

```bash
# Watch service health status
watch -n 2 'docker compose ps --format "table {{.Name}}\t{{.Status}}"'
```

## Access the Application

Once all services are healthy:

- **Frontend**: http://localhost:8010
- **API Docs**: http://localhost:8000/docs
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090

## Optional: Local LLM Service

The local LLM service is **disabled by default** because it requires a model file.

### To Enable Local LLM:

1. **Download a model** (recommended: Phi-3-mini-4k-instruct):
   ```bash
   # Example using wget
   cd models/llama-cpp/
   wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf
   ```

2. **Start with the local-llm profile**:
   ```bash
   docker compose --profile local-llm up -d
   ```

See `models/llama-cpp/README.md` for more details.

## Troubleshooting

### Services Won't Start

1. **Check Docker is running**:
   ```bash
   docker ps
   ```

2. **Check for port conflicts**:
   ```bash
   # Check if ports are already in use
   lsof -i :8000,8010,5433,6380,9200,19530,9090,3001
   ```

3. **View service logs**:
   ```bash
   # All services
   docker compose logs

   # Specific service
   docker compose logs api
   docker compose logs postgres
   docker compose logs milvus
   ```

### Milvus Won't Start

Milvus requires more time to initialize. Check:

```bash
# Watch Milvus logs
docker compose logs -f milvus

# Check dependencies
docker compose ps milvus-etcd milvus-minio
```

### API Won't Start

The API depends on all databases being healthy. Check:

```bash
# Check database health
docker compose exec postgres pg_isready -U karen_user

# Check Redis
docker compose exec redis redis-cli -a karen_redis_pass_change_me ping

# Check API logs
docker compose logs api
```

### Out of Memory

If you encounter memory issues:

1. **Increase Docker memory limit** (Docker Desktop):
   - Settings → Resources → Memory → 8GB+

2. **Reduce Elasticsearch memory**:
   ```bash
   # Edit docker-compose.yml
   # Change ES_JAVA_OPTS from -Xms1g -Xmx1g to -Xms512m -Xmx512m
   ```

3. **Start services selectively**:
   ```bash
   # Start only core services
   docker compose up -d postgres redis milvus-etcd milvus-minio milvus api
   ```

## Useful Commands

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api

# Last 100 lines
docker compose logs --tail=100 api
```

### Restart Services

```bash
# Restart specific service
docker compose restart api

# Restart all services
docker compose restart
```

### Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes all data)
docker compose down -v
```

### Update Services

```bash
# Pull latest images
docker compose pull

# Rebuild and restart
docker compose up -d --build
```

### Clean Up

```bash
# Remove stopped containers
docker compose down

# Remove volumes (data)
docker compose down -v

# Remove images
docker compose down --rmi all

# Full cleanup
docker system prune -a --volumes
```

## Service Details

### PostgreSQL
- **Port**: 5433 (mapped from 5432)
- **User**: karen_user
- **Database**: ai_karen
- **Data**: Stored in `postgres_data` volume

### Redis
- **Port**: 6380 (mapped from 6379)
- **Password**: Set in .env (`REDIS_PASSWORD`)
- **Data**: Stored in `redis_data` volume

### Milvus
- **Port**: 19530 (gRPC)
- **Dependencies**: etcd (metadata), MinIO (object storage)
- **Data**: Stored in `milvus_data` volume
- **Health**: http://localhost:9091/healthz

### Grafana
- **Port**: 3001 (mapped from 3000)
- **Default Login**: admin/admin
- **Dashboards**: Pre-configured for AI-Karen metrics

## Development Mode

For active development with hot-reload:

```bash
# Start with bind mounts
docker compose up -d

# The API and Web services use bind mounts by default
# Changes to Python/TypeScript files will auto-reload
```

## Production Considerations

Before deploying to production:

1. **Change all passwords** in `.env`
2. **Set secure JWT secret** (`AUTH_SECRET_KEY`)
3. **Enable security features**:
   ```bash
   AUTH_ENABLE_SECURITY_FEATURES=true
   AUTH_ENABLE_RATE_LIMITING=true
   AUTH_SESSION_COOKIE_SECURE=true
   ```
4. **Use external databases** (optional but recommended)
5. **Set up SSL/TLS** with a reverse proxy (nginx, Traefik)
6. **Configure backups** for volumes
7. **Monitor resource usage** with Grafana

## Getting Help

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Logs**: `docker compose logs`
- **GitHub Issues**: https://github.com/Zeus-Eternal/AI-Karen/issues

## Next Steps

After starting the services:

1. Visit http://localhost:8010 for the web interface
2. Visit http://localhost:8000/docs for API documentation
3. Check Grafana dashboards at http://localhost:3001
4. Review logs: `docker compose logs -f`

Enjoy using AI-Karen! 🚀
