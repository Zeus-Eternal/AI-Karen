# AI-Karen: Production AI Platform
[![CI](https://github.com/OWNER/AI-Karen/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/AI-Karen/actions/workflows/ci.yml)

> **Enterprise-ready AI platform with modular architecture, multi-database support, and comprehensive UI ecosystem.**
> AI-Karen provides a production-grade FastAPI backend with multiple frontend interfaces, extensive plugin system, and robust data infrastructure for scalable AI applications.

AI-Karen is a comprehensive, production-ready AI platform designed for enterprise deployments. The system features a modular architecture with FastAPI backend, multiple UI interfaces, extensive plugin ecosystem, and robust multi-database infrastructure optimized for AI workloads.

---

## Overview

**Core Platform Features:**
* **FastAPI Backend** - Production-grade REST API with comprehensive endpoint coverage (106+ endpoints)
* **Multi-Database Architecture** - PostgreSQL, Redis, DuckDB, Milvus, and Elasticsearch integration
* **Plugin Ecosystem** - 24+ plugins with hot-reload capability and marketplace integration
* **Extension System** - Modular extensions for analytics, automation, and workflow building
* **Multiple UI Interfaces** - Web (Next.js), Desktop (Tauri), and Streamlit applications
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
│ Port: 5432  │ Port: 6379  │Port: 19530  │ Port: 9200   │ Local   │
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

## Quick Start

### Prerequisites

* **Docker & Docker Compose** - For containerized services
* **Python 3.10+** - For backend development
* **Node.js 18+** - For frontend development
* **Rust toolchain** - For Tauri desktop builds (optional)

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd AI-Karen

# Install Python dependencies
./scripts/install.sh

# Download AI models (optional)
python scripts/install_models.py
```

### 2. Start Infrastructure Services

```bash
# Start all database services
docker compose up -d postgres redis elasticsearch milvus

# Wait for services to be ready
./scripts/health-check.sh
```

### 3. Initialize Databases

```bash
# Apply PostgreSQL migrations (creates all tables including `memory_entries`)
./docker/database/scripts/migrate.sh --service postgres

# Create Elasticsearch index
curl -X PUT "http://localhost:9200/ai_karen_index"
```

### 4. Start Backend API

```bash
# Start FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Verify API is running
curl http://localhost:8000/health
```

### 5. Start Frontend (Choose One)

#### Web UI (Next.js)
```bash
cd ui_launchers/web_ui
npm install
npm run dev
# Access at http://localhost:9002
```

#### Desktop UI (Tauri)
```bash
cd ui_launchers/desktop_ui
npm install
npm run tauri dev
# Native desktop application launches
```

#### Streamlit UI
```bash
cd ui_launchers/streamlit_ui
pip install -r requirements.txt
streamlit run app.py
# Access at http://localhost:8501
```

### 6. Verify Installation

```bash
# Run system health check
python cli.py --self-test

# Run test suite
pytest -v

# Check all services
curl http://localhost:8000/api/health/summary
```

### Running Demo Scripts

Run the example demos with the project source on your `PYTHONPATH`:

```bash
PYTHONPATH=src python demo_plugin_system.py
PYTHONPATH=src python demo_tool_system.py
PYTHONPATH=src python demo_analytics_dashboard.py
```

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
export REDIS_URL=redis://localhost:6379/0
export POSTGRES_URL=postgresql://postgres:postgres@localhost:5432/postgres
export ELASTICSEARCH_URL=http://localhost:9200
export MILVUS_URL=localhost:19530
```

### Development Commands

| Task | Command |
|------|---------|
| Format code | `black .` |
| Type checking | `mypy .` |
| Linting | `ruff check .` |
| Run tests | `pytest` |
| Start API | `uvicorn main:app --reload` |
| Build web UI | `cd ui_launchers/web_ui && npm run build` |
| Build desktop | `cd ui_launchers/desktop_ui && npm run tauri build` |

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
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With custom environment
cp .env.example .env
# Edit .env with production values
docker-compose --env-file .env up -d
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
| `POSTGRES_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/postgres` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `ELASTICSEARCH_URL` | Elasticsearch URL | `http://localhost:9200` |
| `MILVUS_URL` | Milvus connection string | `localhost:19530` |
| `JWT_SECRET_KEY` | JWT signing key | `your-secret-key` |
| `ENABLE_SELF_REFACTOR` | Enable self-refactoring | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

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
# Login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/chat
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
# System health
curl http://localhost:8000/health

# Detailed health summary
curl http://localhost:8000/api/health/summary

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

Structured logging with configurable levels:

```bash
# Set log level
export LOG_LEVEL=DEBUG

# View logs
docker-compose logs -f api
```

---

## Troubleshooting

### Common Issues

#### Database Connection Issues

**Problem**: `Connection refused` errors for databases

**Solution**:
```bash
# Check service status
docker-compose ps

# Restart services
docker-compose restart postgres redis

# Check logs
docker-compose logs postgres
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
docker-compose logs api | grep plugin
```

#### Memory Issues

**Problem**: High memory usage or OOM errors

**Solution**:
```bash
# Check memory usage
docker stats

# Adjust memory limits in docker-compose.yml
# Restart with memory limits
docker-compose up -d --force-recreate
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

### Architecture Guides
- [API Reference](docs/api_reference.md) - Complete API documentation
- [Architecture Overview](docs/architecture.md) - System architecture details
- [Development Guide](docs/development_guide.md) - Development best practices
- [Security Framework](docs/security.md) - Security implementation
- [Memory Architecture](docs/memory_arch.md) - Memory system design
- [Plugin Specification](docs/plugin_spec.md) - Plugin development specification

### Operational Guides
- [Deployment Guide](docs/deployment.md) - Production deployment
- [Monitoring Guide](docs/observability.md) - Monitoring and observability
- [Troubleshooting Guide](docs/troubleshooting.md) - Common issues and solutions

---

*AI-Karen: Production-ready AI platform for enterprise deployments*