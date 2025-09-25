# AI-Karen Developer Setup Guide

## Overview

This comprehensive guide covers setting up a complete development environment for AI-Karen, including all services, development tools, and best practices for contributing to the project.

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10+ with WSL2
- **CPU**: 4+ cores (8+ recommended for AI workloads)
- **RAM**: 16GB minimum (32GB recommended)
- **Storage**: 100GB+ available space (SSD recommended)
- **Network**: Stable internet connection for dependencies and model downloads

### Required Software
- **Python**: 3.11+ (3.11.x recommended)
- **Node.js**: 18.x or 20.x LTS
- **Docker**: 24.0+ with Docker Compose 2.20+
- **Git**: 2.30+
- **Code Editor**: VS Code (recommended) or your preferred IDE

## Initial Setup

### 1. Clone Repository

```bash
# Clone the repository
git clone https://github.com/OWNER/AI-Karen.git
cd AI-Karen

# Set up git hooks
git config core.hooksPath .githooks
chmod +x .githooks/*
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables for development
nano .env
```

**Development Environment Variables:**
```bash
# Development settings
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true

# Database settings (development)
POSTGRES_USER=karen_user
POSTGRES_PASSWORD=karen_dev_pass
POSTGRES_DB=ai_karen_dev
POSTGRES_HOST=localhost
POSTGRES_PORT=5433

# Redis settings
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# API settings
KAREN_BACKEND_URL=http://127.0.0.1:8000
API_BASE_URL=http://127.0.0.1:8000
KAREN_AUTH_PROXY_TIMEOUT_MS=30000

# Performance settings (development)
KARI_LAZY_LOADING=false
KARI_MINIMAL_STARTUP=false
KARI_ECO_MODE=false
WARMUP_LLM=false

# CORS settings (permissive for development)
KARI_CORS_ORIGINS=http://localhost:3000,http://localhost:8020,http://127.0.0.1:3000,http://127.0.0.1:8020
KARI_CORS_METHODS=*
KARI_CORS_HEADERS=*
KARI_CORS_CREDENTIALS=true

# Security (development keys - change for production)
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# AI Model settings
LLAMA_THREADS=4
LLAMA_MLOCK=false
PROFILE=runtime  # Use 'runtime-perf' for optimized builds
```

### 3. Python Environment Setup

```bash
# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install development dependencies
pip install -e .

# Install pre-commit hooks
pre-commit install

# Verify installation
python -c "import ai_karen_engine; print('AI-Karen engine imported successfully')"
```

### 4. Node.js Environment Setup

```bash
# Install Node.js dependencies for Web UI
cd ui_launchers/web_ui
npm install

# Install development dependencies
npm install --save-dev

# Build for development
npm run dev &

# Return to root directory
cd ../..
```

### 5. Docker Services Setup

```bash
# Start database and supporting services
docker compose up -d postgres redis milvus elasticsearch

# Wait for services to be ready
sleep 30

# Verify services are running
docker compose ps
```

### 6. Database Initialization

```bash
# Create database tables
python create_tables.py

# Create default admin user
python create_admin_user.py
# Follow prompts to set admin credentials

# Verify database setup
python -c "
from ai_karen_engine.database.connection import get_db_connection
conn = get_db_connection()
print('Database connection successful')
conn.close()
"
```

### 7. AI Models Setup

```bash
# Create models directory
mkdir -p models/llama-cpp

# Download a small model for development (optional)
cd models/llama-cpp
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf

# Verify model file
ls -la *.gguf
cd ../..
```

## Development Workflow

### 1. Starting Development Environment

```bash
# Start all services
docker compose up -d

# Start API in development mode
python start.py

# In another terminal, start Web UI
cd ui_launchers/web_ui
npm run dev
```

**Access URLs:**
- API: http://localhost:8000
- Web UI: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 2. Development Commands

**Backend Development:**
```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src/ai_karen_engine --cov-report=html

# Type checking
mypy src/

# Code formatting
black src/ tests/

# Linting
ruff check src/ tests/

# Run specific test file
pytest tests/test_auth.py -v

# Run tests with debugging
pytest tests/test_auth.py -v -s --pdb
```

**Frontend Development:**
```bash
cd ui_launchers/web_ui

# Start development server
npm run dev

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Type checking
npm run type-check

# Linting
npm run lint

# Build for production
npm run build

# Start production build
npm start
```

### 3. Code Quality Tools

**Pre-commit Configuration:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

**VS Code Configuration:**
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": false,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "88"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "eslint.workingDirectories": ["ui_launchers/web_ui"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true,
    "**/.next": true
  }
}
```

## Development Best Practices

### 1. Code Organization

**Backend Structure:**
```
src/ai_karen_engine/
├── api_routes/          # FastAPI route handlers
├── auth/               # Authentication system
├── core/               # Core application logic
├── database/           # Database models and connections
├── memory/             # Memory management system
├── plugins/            # Plugin system
├── services/           # Business logic services
└── utils/              # Utility functions
```

**Frontend Structure:**
```
ui_launchers/web_ui/src/
├── app/                # Next.js app router
├── components/         # Reusable UI components
├── lib/                # Utility libraries
├── hooks/              # Custom React hooks
├── types/              # TypeScript type definitions
└── __tests__/          # Test files
```

### 2. Testing Strategy

**Backend Testing:**
```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from ai_karen_engine.core.gateway.app import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_auth_login(client):
    response = client.post("/api/auth/dev-login", json={})
    assert response.status_code == 200
    assert "access_token" in response.json()
```

**Frontend Testing:**
```typescript
// ui_launchers/web_ui/src/__tests__/api-client.test.ts
import { getApiClient } from '../lib/api-client';

describe('API Client', () => {
  it('should make successful health check', async () => {
    const client = getApiClient();
    const response = await client.healthCheck();
    expect(response.status).toBe(200);
  });

  it('should handle authentication', async () => {
    const client = getApiClient();
    const response = await client.post('/api/auth/dev-login', {});
    expect(response.data).toHaveProperty('access_token');
  });
});
```

### 3. Database Development

**Migration Workflow:**
```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Review generated migration
cat alembic/versions/xxx_add_new_table.py

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

**Database Testing:**
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ai_karen_engine.database.models import Base

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

### 4. Plugin Development

**Plugin Structure:**
```
src/ai_karen_engine/plugins/my_plugin/
├── __init__.py
├── plugin_manifest.json
├── handler.py
├── config.py
└── tests/
    └── test_my_plugin.py
```

**Plugin Manifest:**
```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "description": "My custom plugin",
  "plugin_api_version": "0.1.0",
  "required_roles": ["user"],
  "intent": ["my_intent"],
  "dependencies": [],
  "config_schema": {
    "type": "object",
    "properties": {
      "setting1": {"type": "string"},
      "setting2": {"type": "integer"}
    }
  }
}
```

**Plugin Handler:**
```python
# handler.py
from typing import Dict, Any
from ai_karen_engine.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.setting1 = config.get('setting1', 'default')
    
    def run(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "intent": "my_intent",
            "confidence": 1.0,
            "response": f"Processed: {message}",
            "metadata": {"plugin": "my_plugin"}
        }
    
    def health_check(self) -> bool:
        return True

def create_plugin(config: Dict[str, Any]) -> MyPlugin:
    return MyPlugin(config)
```

## Debugging and Profiling

### 1. Backend Debugging

**Debug Configuration:**
```python
# debug_config.py
import logging
import sys

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug.log')
    ]
)

# Enable SQL query logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

**Performance Profiling:**
```bash
# Profile with py-spy
pip install py-spy
py-spy record -o profile.svg -d 60 -p $(pgrep -f "python.*start")

# Memory profiling
pip install memory-profiler
python -m memory_profiler start.py

# Line profiling
pip install line_profiler
kernprof -l -v start.py
```

### 2. Frontend Debugging

**Browser DevTools:**
- Network tab for API requests
- Console for JavaScript errors
- Performance tab for rendering issues
- Application tab for storage inspection

**React DevTools:**
```bash
# Install React DevTools extension
# Available for Chrome, Firefox, and Edge
```

**Next.js Debugging:**
```javascript
// next.config.js
module.exports = {
  experimental: {
    instrumentationHook: true,
  },
  logging: {
    fetches: {
      fullUrl: true,
    },
  },
}
```

## Integration Testing

### 1. End-to-End Testing

**Playwright Setup:**
```bash
cd ui_launchers/web_ui
npm install @playwright/test
npx playwright install
```

**E2E Test Example:**
```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test('user can login and access dashboard', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Login
  await page.click('[data-testid="login-button"]');
  await page.waitForURL('**/dashboard');
  
  // Verify dashboard loaded
  await expect(page.locator('h1')).toContainText('Dashboard');
});
```

### 2. API Integration Testing

```python
# tests/integration/test_api_integration.py
import pytest
import requests
import time

class TestAPIIntegration:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Wait for services to be ready
        self.wait_for_service("http://localhost:8000/health")
    
    def wait_for_service(self, url, timeout=30):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    return
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
        raise Exception(f"Service at {url} not ready after {timeout}s")
    
    def test_full_auth_flow(self):
        # Login
        response = requests.post(
            "http://localhost:8000/api/auth/dev-login",
            json={}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Use token for authenticated request
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "http://localhost:8000/api/user/profile",
            headers=headers
        )
        assert response.status_code == 200
```

## Performance Optimization

### 1. Development Performance

**Fast Startup Configuration:**
```bash
# Use optimized startup for development
KARI_LAZY_LOADING=true
KARI_MINIMAL_STARTUP=true
WARMUP_LLM=false

# Start with optimized mode
python start_optimized.py
```

**Database Optimization:**
```sql
-- Development database optimizations
ALTER SYSTEM SET fsync = off;
ALTER SYSTEM SET synchronous_commit = off;
ALTER SYSTEM SET checkpoint_segments = 32;
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
```

### 2. Build Optimization

**Docker Development:**
```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

# Install development dependencies
RUN pip install debugpy

# Enable hot reload
ENV PYTHONPATH=/app/src
ENV FLASK_ENV=development

# Expose debug port
EXPOSE 5678

CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "start.py"]
```

**Next.js Development:**
```javascript
// next.config.js
module.exports = {
  experimental: {
    turbo: {
      loaders: {
        '.svg': ['@svgr/webpack'],
      },
    },
  },
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }
    return config;
  },
}
```

## Troubleshooting Development Issues

### Common Issues

1. **Port Conflicts:**
   ```bash
   # Find process using port
   lsof -i :8000
   
   # Kill process
   kill -9 <PID>
   
   # Use different port
   uvicorn main:app --port 8001
   ```

2. **Database Connection Issues:**
   ```bash
   # Reset database
   docker compose down postgres
   docker volume rm ai-karen_postgres_data
   docker compose up -d postgres
   python create_tables.py
   ```

3. **Node.js Issues:**
   ```bash
   # Clear npm cache
   npm cache clean --force
   
   # Remove node_modules
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Python Environment Issues:**
   ```bash
   # Recreate virtual environment
   rm -rf venv/
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Contributing Guidelines

### 1. Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-new-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push branch
git push origin feature/my-new-feature

# Create pull request
# Use GitHub/GitLab web interface
```

### 2. Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

### 3. Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No breaking changes (or properly documented)
- [ ] Performance impact considered
- [ ] Security implications reviewed

This developer setup guide provides everything needed to start contributing to AI-Karen effectively. For additional help, refer to the project's issue tracker and community discussions.