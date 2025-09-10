# AI-Karen: Production AI Platform
[![CI](https://github.com/OWNER/AI-Karen/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/AI-Karen/actions/workflows/ci.yml)

> **Enterprise-ready AI platform with modular architecture, multi-database support, and comprehensive UI ecosystem.**
> AI-Karen provides a production-grade FastAPI backend with multiple frontend interfaces, extensive plugin system, and robust data infrastructure for scalable AI applications.

AI-Karen is a comprehensive, production-ready AI platform designed for enterprise deployments. The system features a modular architecture with FastAPI backend, multiple UI interfaces, extensive plugin ecosystem, and robust multi-database infrastructure optimized for AI workloads.

### LLM Runtime: In‑Process by Default

This project defaults to the in‑process llama‑cpp‑python runtime for local GGUF models. The legacy external Llama.cpp server manager (`serverKent/`) has been removed to simplify operations and reduce latency.

- Place GGUF models under `models/llama-cpp/` (e.g., `Phi-3-mini-4k-instruct-q4.gguf`).
- Default settings point to this model; adjust `llm_settings.json` if needed.
- No HTTP llama server is required — the API performs inference directly.

Optional: If you must run an external `llama-server`, do it outside this repo and point a custom provider to it; in-repo support is intentionally not maintained.

### Startup Warmup

On boot, the backend preloads the default llama‑cpp model (best‑effort) to avoid first‑request latency. Control via `WARMUP_LLM` env (`true` by default).

### Performance Profile (OpenBLAS)

For CPU speedups, a “perf” image variant enables OpenBLAS for llama‑cpp:

- Build: `PROFILE=runtime-perf docker compose build api` (or set `PROFILE=runtime-perf` in your environment).
- Default remains `runtime` (portable, no BLAS). Both variants support in‑process inference.

Tuning env:

- `LLAMA_THREADS`: override CPU threads (default: `os.cpu_count()`).
- `LLAMA_MLOCK`: set `true` to lock model in RAM (requires sufficient memory).
- `n_gpu_layers` in `llm_settings.json`: offload layers to GPU when configured.

---

## Overview

**Core Platform Features:**
* **FastAPI Backend** - Production-grade REST API with comprehensive endpoint coverage (106+ endpoints)
* **Multi-Database Architecture** - PostgreSQL, Redis, DuckDB, Milvus, and Elasticsearch integration
* **Plugin Ecosystem** - 24+ plugins with hot-reload capability and marketplace integration
* **Extension System** - Modular extensions for analytics, automation, and workflow building
* **Multiple UI Interfaces** - Web (Next.js) is the default interface, with Desktop (Tauri) and Streamlit options
* **AI/ML Integration** - HuggingFace Transformers, OpenAI API, local LLM support via llama-cpp-python
* **Production Monitoring** - Prometheus metrics, health checks, and comprehensive logging
* **Authentication & Security** - JWT-based auth, role-based access control, tenant isolation
* **Container Orchestration** - Docker Compose setup with service discovery and health monitoring

**Technology Stack:**
* **Backend**: FastAPI, Python 3.10+, Pydantic, SQLAlchemy, Alembic
* **Databases**: PostgreSQL 15, Redis 7, Elasticsearch 8.9, Milvus 2.3, DuckDB
* **Frontend**: Next.js 15.2.3, React 18, Tauri 2.5, Streamlit
* **AI/ML**: HuggingFace Transformers, llama-cpp-python, scikit-learn 1.5, spaCy 3.7
* **Infrastructure**: Docker, Prometheus, nginx (optional), Kubernetes support

---

## Quick Start

### Prerequisites

* Python 3.10+
* Docker and Docker Compose

### Installation

```bash
git clone https://github.com/OWNER/AI-Karen.git
cd AI-Karen
pip install -r requirements.txt
```

### Launch Services

```bash
# start databases and supporting services
docker compose up -d

# initialize core tables and default admin user
python create_tables.py
python create_admin_user.py  # follow prompts

# start the FastAPI backend
python start.py
```

The web UI is available at <http://localhost:9002> and the API at <http://localhost:8000>.

### Run Tests

```bash
pytest
```

## Database Setup

AI-Karen ships with multiple data stores. The default `docker-compose.yml`
spins up the full stack with sensible development defaults:

| Service | Purpose | Port |
|---------|---------|------|
| PostgreSQL | metadata storage | 5433 |
| Redis | caching and sessions | 6379 |
| Milvus | vector similarity search | 19530 |
| Elasticsearch | full-text search | 9200 |
| DuckDB | local analytics | n/a |

Custom connection strings can be supplied via environment variables defined in `config/`.

## Example Usage

Query the health endpoint:

```bash
curl http://localhost:8000/api/health/summary
```

Create a chat completion using the Python client:

```python
import requests

resp = requests.post(
    "http://localhost:8000/api/chat/completions",
    json={"input": "Hello, AI-Karen"},
)
print(resp.json())
```

---

## Authentication Configuration

The authentication service relies on the `AuthConfig` class for all
runtime settings. Configuration can be provided in environment-specific
YAML or JSON files:

```python
from ai_karen_engine.auth.config import AuthConfig

# Load from a specific file and environment
config = AuthConfig.from_file("config/auth_config.yaml", "development")

# Or discover the file in the default ``config/`` directory
config = AuthConfig.from_environment("production")
```

Example configuration files are provided in `config/auth_config.yaml`
and `config/auth_config.json`.

### Production Authentication Setup

AI-Karen ships with a production-ready authentication stack featuring
PostgreSQL storage, bcrypt password hashing, JWT token management,
Redis-backed sessions, and multi-tenant support. See
[Production Authentication Setup](docs/auth/PRODUCTION_AUTH_SETUP.md) for
full deployment instructions.

**Environment Variables**

```bash
cp config/production_auth_config.env .env
# Edit .env with secure production values
```

**Migration Script**

Initialize the authentication database schema:

```bash
python scripts/run_auth_migration.py
# Optional dry run
python scripts/run_auth_migration.py --dry-run
```

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                           │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Web UI        │  Desktop UI     │     Streamlit UI            │
│  (Next.js)      │   (Tauri)       │   (Modern Interface)        │
│  Port: 9002     │  Native App     │   Port: 8501                │
└─────────────────┴─────────────────┴─────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                             │
│                      Port: 8000                                 │
├─────────────────────────────────────────────────────────────────┤
│  • REST API (106+ endpoints)    • Plugin System (24+ plugins)  │
│  • Authentication & RBAC        • Extension System             │
│  • Multi-tenant Support         • Health Monitoring            │
│  • Prometheus Metrics           • Event Bus                    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    Database Layer                               │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│ PostgreSQL  │   Redis     │   Milvus    │ Elasticsearch│ DuckDB  │
│ Port: 5433  │ Port: 6379  │Port: 19530  │ Port: 9200   │ Local   │
│ (Metadata)  │ (Cache)     │ (Vectors)   │ (Search)     │(Analytics)│
└─────────────┴─────────────┴─────────────┴─────────────┴─────────┘
```

### Key Architectural Principles

1. **Modular Design** - Loosely coupled components with clear interfaces
2. **Horizontal Scalability** - Database services can be scaled independently
3. **Plugin Architecture** - Hot-reloadable plugins with manifest-based configuration
4. **Multi-UI Support** - Different interfaces for different use cases
5. **Production Ready** - Comprehensive monitoring, logging, and health checks

---


## Development Setup

### Local Development Environment

```bash
# Install development dependencies
pip install -e .
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Set environment variables
export POSTGRES_USER=karen_user
export POSTGRES_PASSWORD=karen_secure_pass_change_me
export POSTGRES_DB=ai_karen
export POSTGRES_HOST=postgres  # use 'postgres' when running via Docker
export POSTGRES_PORT=5433  # change if port 5432 is busy
export REDIS_URL=redis://localhost:6379/0
export ELASTICSEARCH_URL=http://localhost:9200
export MILVUS_HOST=localhost
export MILVUS_PORT=19530
```

### Development Commands

| Task | Command |
|------|---------|
| Format code | `black .` |
| Type checking | `mypy .` |
| Linting | `ruff check .` |
| Run tests | `pytest` |
| Start API | `uvicorn main:create_app --factory --reload` |
| Build web UI | `cd ui_launchers/web_ui && npm run build` |
| Build desktop | `cd ui_launchers/desktop_ui && npm run tauri build` |

### Test Environment Setup

The test suite depends on several third-party libraries, including
`httpx`, `sqlalchemy`, `asyncpg`, `aiohttp`, `psutil`,
`prometheus_client`, and `bcrypt`. Install all test dependencies
before running `pytest`:

```bash
pip install -r requirements.txt
```

### Demo Scripts

When running the example demo scripts directly from the repository, set
`PYTHONPATH=src` so the `ai_karen_engine` package can be imported without
modifying `sys.path` inside the scripts:

```bash
PYTHONPATH=src python demo_plugin_system.py
```

### Plugin Development

Create a new plugin in `src/ai_karen_engine/plugins/`:

```bash
mkdir src/ai_karen_engine/plugins/my_plugin
```

**plugin_manifest.json:**
```json
{
  "name": "my_plugin",
  "description": "My custom plugin",
  "plugin_api_version": "0.1.0",
  "required_roles": ["user"],
  "intent": ["my_intent"]
}
```

**handler.py:**
```python
def run(message, context):
    return {
        "intent": "my_intent",
        "confidence": 1.0,
        "response": f"Hello from my_plugin! Message: {message}"
    }
```

Plugins are automatically discovered and hot-reloaded.

---

## Production Deployment

### Docker Compose (Recommended)

```bash
# Production deployment
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With custom environment
cp .env.example .env
# Edit .env with production values
docker compose --env-file .env up -d
```

### Kubernetes Deployment

```bash
# Using Helm chart
helm install ai-karen ./charts/kari/ \
  --set image.tag=latest \
  --set postgresql.enabled=true \
  --set redis.enabled=true
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | PostgreSQL user | `karen_user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `karen_secure_pass_change_me` |
| `POSTGRES_DB` | PostgreSQL database | `ai_karen` |
| `POSTGRES_HOST` | PostgreSQL host | `postgres` |
| `POSTGRES_PORT` | PostgreSQL port | `5433` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `ELASTICSEARCH_URL` | Elasticsearch URL | `http://localhost:9200` |
| `MILVUS_HOST` | Milvus host | `localhost` |
| `MILVUS_PORT` | Milvus port | `19530` |
| `JWT_SECRET_KEY` | JWT signing key | `your-secret-key` |
| `ENABLE_SELF_REFACTOR` | Enable self-refactoring | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `KARI_CORS_ORIGINS` | Comma-separated list of allowed CORS origins | `*` |
| `KARI_CORS_METHODS` | Allowed CORS HTTP methods (comma-separated or `*`) | `*` |
| `KARI_CORS_HEADERS` | Allowed CORS request headers (comma-separated or `*`) | `*` |
| `KARI_CORS_CREDENTIALS` | Whether to allow credentials in CORS requests | `true` |
| `KARI_ECO_MODE` | Skip heavy NLP model loading | `false` |
| `KARI_MEMORY_SURPRISE_THRESHOLD` | Novelty threshold for storing memory | `0.85` |
| `KARI_DISABLE_MEMORY_SURPRISE_FILTER` | Disable surprise filtering to store all memories | `false` |

---

## API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health check |
| `GET` | `/ready` | Readiness probe |
| `GET` | `/metrics` | Application metrics |
| `GET` | `/metrics/prometheus` | Prometheus metrics |
| `POST` | `/chat` | Chat completion |
| `POST` | `/store` | Store memory |
| `POST` | `/search` | Search memories |
| `GET` | `/plugins` | List plugins |
| `GET` | `/models` | List AI models |

The memory query endpoint (`/api/memory/query`) returns at most **100 results** by default.
You can override this cap by providing the `result_limit` parameter in your request.

### Tenant Header

Most API endpoints are tenant-aware. Include an `X-Tenant-ID` header with your
tenant name in requests that are not listed under the public paths. For local
testing you can use `default`:

```bash
curl -H "X-Tenant-ID: default" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"text": "hello"}' http://localhost:8000/chat
```

### Authentication

```bash
# Login with default admin credentials
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@kari.ai", "password": "password123"}'

# Use token
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/chat

# Update your credentials after logging in
curl -X POST http://localhost:8000/api/auth/update_credentials \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"new_password": "strongpass"}'
```

### Plugin Management

```bash
# List plugins
curl http://localhost:8000/plugins

# Enable plugin
curl -X POST http://localhost:8000/plugins/my_plugin/enable

# Reload plugins
curl -X POST http://localhost:8000/plugins/reload
```

---

## Monitoring & Observability

### Health Checks

```bash
# Verify backend is listening on port 8000
ss -ltnp | grep :8000 || lsof -iTCP:8000 -sTCP:LISTEN

# System health
curl http://localhost:8000/health

# API health
curl http://localhost:8000/api/health

# Detailed health summary
curl http://localhost:8000/api/health/summary

# Metrics
curl http://localhost:8000/metrics

# Service-specific health
curl http://localhost:8000/api/services/postgres/health
```

### Metrics

The system exposes Prometheus metrics at `/metrics/prometheus`:

* HTTP request metrics
* Database connection metrics
* Plugin execution metrics
* Memory usage metrics
* AI model performance metrics

### Logging

Structured logging with configurable levels. The server runs at `INFO` level by
default and prints `Greetings, the logs are ready for review` once startup
completes.

```bash
# Increase verbosity if needed
export LOG_LEVEL=DEBUG

# View logs
docker compose logs -f api
```

---

## Troubleshooting

### Common Issues

#### Database Connection Issues

**Problem**: `Connection refused` errors for databases

**Solution**:
```bash
# Check service status
docker compose ps

# Restart services
docker compose restart postgres redis

# Check logs
docker compose logs postgres
```

#### Plugin Loading Failures

**Problem**: Plugins not loading or executing

**Solution**:
```bash
# Validate plugin manifest
python -c "import json; print(json.load(open('src/ai_karen_engine/plugins/my_plugin/plugin_manifest.json')))"

# Reload plugins
curl -X POST http://localhost:8000/plugins/reload

# Check plugin logs
docker compose logs api | grep plugin
```

#### Memory Issues

**Problem**: High memory usage or OOM errors

**Solution**:
```bash
# Check memory usage
docker stats

# Adjust memory limits in docker-compose.yml
# Restart with memory limits
docker compose up -d --force-recreate
```

#### Frontend Build Issues

**Problem**: UI build failures

**Solution**:
```bash
# Clear node modules
cd ui_launchers/web_ui
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+
```

### Performance Optimization

1. **Database Tuning**:
   - Adjust PostgreSQL `shared_buffers` and `work_mem`
   - Configure Redis `maxmemory` policy
   - Optimize Elasticsearch heap size

2. **API Performance**:
   - Enable FastAPI response caching
   - Configure connection pooling
   - Use async endpoints where possible

3. **Frontend Optimization**:
   - Enable Next.js production build optimizations
   - Configure CDN for static assets
   - Implement proper caching headers

### Getting Help

1. **Check Documentation**: Review component-specific README files
2. **System Analysis**: Run `python scripts/doc_analysis.py` for system overview
3. **Health Checks**: Use `/api/health/summary` endpoint
4. **Logs**: Check application and service logs
5. **Community**: Submit issues with system analysis output

---

## Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run the full test suite
5. Submit a pull request

### Code Standards

* **Python**: Black formatting, type hints, docstrings
* **JavaScript/TypeScript**: ESLint, Prettier formatting
* **Rust**: Standard rustfmt formatting
* **Documentation**: Update README files for any architectural changes

### Testing

Install project dependencies before running tests:

```bash
pip install -r requirements.txt
```

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/services/
pytest tests/ui/

# Run with coverage
pytest --cov=src/ai_karen_engine
```

---

## License

This project is dual-licensed:
- **Mozilla Public License 2.0** for open source use
- **Commercial License** for enterprise deployments

See [LICENSE.md](LICENSE.md) and [LICENSE-commercial.txt](LICENSE-commercial.txt) for details.

---

## Documentation

### Component Documentation
- [Web UI Documentation](ui_launchers/web_ui/README.md) - Next.js web interface
- [Desktop UI Documentation](ui_launchers/desktop_ui/README.md) - Tauri desktop application
- [Streamlit UI Documentation](ui_launchers/streamlit_ui/README.md) - Modern Streamlit interface
- [Database Documentation](docker/database/README.md) - Multi-database setup
- [Plugin Documentation](plugin_marketplace/README.md) - Plugin development guide
- [Extension Documentation](extensions/README.md) - Extension system overview
- [Auth Service](docs/auth/auth_service.md) - Core authentication service overview
- [Auth Service Deployment Guide](docs/auth/auth_service_deployment.md) - Environment setup and configuration loading
- [Auth Service Migration Guide](docs/auth/auth_service_migration.md) - Removal of legacy security modules

### Architecture Guides
- [API Reference](docs/api/api_reference.md) - Complete API documentation
- [Architecture Overview](docs/architecture.md) - System architecture details
- [Development Guide](docs/guides/development_guide.md) - Development best practices
- [Security Framework](docs/security.md) - Security implementation
- [Memory Architecture](docs/memory_arch.md) - Memory system design
- [Plugin Specification](docs/plugins/plugin_spec.md) - Plugin development specification
- [Agent Roadmap](docs/agent_roadmap.md) - Production readiness and feature roadmap for the web UI

### Operational Guides
- [Deployment Guide](docs/guides/deployment.md) - Production deployment
- [Monitoring Guide](docs/guides/observability.md) - Monitoring and observability
- [Troubleshooting Guide](docs/guides/troubleshooting.md) - Common issues and solutions

---

*AI-Karen: Production-ready AI platform for enterprise deployments*
