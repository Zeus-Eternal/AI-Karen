# AI Karen Development Guide

This comprehensive guide covers development workflows, environment setup, testing procedures, and contribution guidelines for the AI Karen platform. Whether you're building plugins, extensions, or contributing to the core system, this guide will help you get started.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Development Workflows](#development-workflows)
- [Testing Procedures](#testing-procedures)
- [Code Style and Standards](#code-style-and-standards)
- [Debugging Procedures](#debugging-procedures)
- [Documentation Guidelines](#documentation-guidelines)
- [Contributing Guidelines](#contributing-guidelines)

## Development Environment Setup

### Prerequisites

**Required Software:**
- **Python 3.10+** - Core backend development
- **Node.js 18+** - Frontend development and tooling
- **Docker & Docker Compose** - Containerized services
- **Git** - Version control
- **PostgreSQL 14+** - Primary database (or use Docker)
- **Redis 6+** - Caching and real-time features (or use Docker)

**Optional Software:**
- **Rust toolchain** - For Tauri desktop builds
- **DuckDB** - Analytics database
- **Milvus** - Vector database for embeddings

### Environment Variables

Set these required environment variables before development:

| Variable | Purpose | Example Value |
| -------- | ------- | ------------- |
| `KARI_MODEL_SIGNING_KEY` | Cryptographic key for LLM orchestrator model verification | `export KARI_MODEL_SIGNING_KEY=dev-signing-key-123` |
| `KARI_DUCKDB_PASSWORD` | Encryption password for automation DuckDB database | `export KARI_DUCKDB_PASSWORD=dev-duckdb-pass` |
| `KARI_JOB_SIGNING_KEY` | Signs automation tasks for integrity checks | `export KARI_JOB_SIGNING_KEY=dev-job-key-456` |
| `KARI_LOG_DIR` | Directory for log files | `export KARI_LOG_DIR=$HOME/.kari/logs` |
| `DATABASE_URL` | PostgreSQL connection string | `export DATABASE_URL=postgresql://user:pass@localhost:5432/karen_dev` |
| `REDIS_URL` | Redis connection string | `export REDIS_URL=redis://localhost:6379/0` |

**Optional Environment Variables:**
- `OPENAI_API_KEY` - For OpenAI model integration
- `GEMINI_API_KEY` - For Google Gemini integration
- `DEEPSEEK_API_KEY` - For DeepSeek model integration
- `KARI_MAX_LLM_CONCURRENT` - Maximum concurrent LLM requests (default: 8)
- `KARI_LLM_TIMEOUT` - LLM request timeout in seconds (default: 60)
- `KARI_ENV` - Selects the runtime environment. Use `local` (the default) to
  run entirely on your machine without relying on external services.
- `KARI_ECO_MODE` - Skip heavy NLP model loading for low-resource environments
- `KARI_MEMORY_SURPRISE_THRESHOLD` - Novelty threshold for memory storage (default: 0.85)
- `KARI_DISABLE_MEMORY_SURPRISE_FILTER` - Disable surprise filtering to store all memories

### Local Development Setup

1. **Clone the Repository**
```bash
git clone https://github.com/your-org/ai-karen.git
cd ai-karen
```

2. **Set Up Python Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black ruff mypy pre-commit
```

3. **Set Up Pre-commit Hooks**
```bash
pre-commit install
```

4. **Start Database Services (Docker)**
```bash
# Start all database services
cd docker/database
docker-compose up -d

# Or start individual services
docker-compose up -d postgres redis
```

5. **Initialize Database**
```bash
# Run database migrations
python -m ai_karen_engine.database.migrations migrate

# Seed initial data (optional)
python scripts/seed_database.py
```

6. **Verify Installation**
```bash
# Run tests to verify setup
PYTHONPATH=src pytest tests/test_basic_setup.py

# Start the API server
uvicorn main:app --reload --port 8000
```

## Development Workflows

### Backend Development (Python API)

**Start the API Server:**
```bash
# Development mode with hot reload
uvicorn main:app --reload --port 8000

# Increase log verbosity
KARI_LOG_LEVEL=DEBUG uvicorn main:app --reload --port 8000

# API documentation available at:
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

On startup the server logs `Greetings, the logs are ready for review` to confirm
that logging is configured correctly.

**Common Development Tasks:**
```bash
# Run specific tests
pytest tests/test_llm_orchestrator.py -v

# Run tests with coverage
pytest --cov=src/ai_karen_engine tests/

# Format code
black src/ tests/
ruff check src/ tests/ --fix

# Type checking
mypy src/ai_karen_engine --strict
```

### Frontend Development

#### Web UI (Next.js)
```bash
cd ui_launchers/web_ui

# Install dependencies
npm install

# Start development server
npm run dev

# Available at http://localhost:9002
```

#### Streamlit UI
```bash
cd ui_launchers/streamlit_ui

# Install dependencies
pip install -r requirements.txt

# Start development server with auto-reload
streamlit run app.py --server.runOnSave true

# Available at http://localhost:8501
```

#### Desktop UI (Tauri)
```bash
cd ui_launchers/desktop_ui

# Install Rust and Tauri CLI
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
cargo install tauri-cli

# Install Node.js dependencies
npm install

# Development mode with hot reload
npm run tauri dev

# Build production binary
npm run tauri build
```

### Plugin Development

1. **Create Plugin Structure**
```bash
mkdir -p plugin_marketplace/custom/my-plugin
cd plugin_marketplace/custom/my-plugin
```

2. **Create Plugin Files**
```python
# plugin_manifest.json
{
    "name": "my-plugin",
    "version": "1.0.0",
    "description": "My custom plugin",
    "handler": "handler.py",
    "permissions": ["basic"]
}

# handler.py
async def handle(params, context):
    """Plugin handler function"""
    return {"result": "Hello from my plugin!"}
```

3. **Test Plugin**
```bash
# Reload plugins
curl -X POST http://localhost:8000/plugins/reload

# Test plugin execution
curl -X POST http://localhost:8000/plugins/execute \
  -H "Content-Type: application/json" \
  -d '{"name": "my-plugin", "params": {}}'
```

### Extension Development

1. **Create Extension Structure**
```bash
mkdir -p extensions/my-extension
cd extensions/my-extension
```

2. **Create Extension Manifest**
```json
{
  "name": "my-extension",
  "version": "1.0.0",
  "description": "My custom extension",
  "main": "extension.py",
  "dependencies": {
    "plugins": ["data-processor@^1.0.0"]
  },
  "permissions": ["database.read", "ui.register_components"]
}
```

3. **Implement Extension**
```python
# extension.py
from ai_karen_engine.extensions import BaseExtension

class MyExtension(BaseExtension):
    async def initialize(self):
        await self.register_plugins(["data-processor"])
        await self.setup_ui_components()
    
    async def activate(self):
        self.logger.info("Extension activated")
    
    async def deactivate(self):
        self.logger.info("Extension deactivated")
```

## Testing Procedures

### Running Tests

**All Tests:**
```bash
# Run all tests
PYTHONPATH=src pytest

# Run with coverage
PYTHONPATH=src pytest --cov=src/ai_karen_engine --cov-report=html

# Run specific test categories
pytest tests/core/  # Core infrastructure tests
pytest tests/services/  # Service layer tests
pytest tests/api/  # API endpoint tests
```

**Integration Tests:**
```bash
# Database integration tests
pytest tests/test_database_integration.py

# API integration tests
pytest tests/test_api_integration.py

# Plugin system tests
pytest tests/test_plugin_integration.py
```

**Performance Tests:**
```bash
# Load testing
pytest tests/performance/ -v

# Memory usage tests
pytest tests/test_memory_usage.py
```

### Test Configuration

**Test Environment Variables:**
```bash
export KARI_TEST_MODE=true
export KARI_MODEL_SIGNING_KEY=test-key
export KARI_DUCKDB_PASSWORD=test-pass
export KARI_JOB_SIGNING_KEY=test-job-key
export DATABASE_URL=postgresql://test:test@localhost:5432/karen_test
```

**Test Database Setup:**
```bash
# Create test database
createdb karen_test

# Run test migrations
PYTHONPATH=src python -m ai_karen_engine.database.migrations migrate --database-url postgresql://test:test@localhost:5432/karen_test
```

### Writing Tests

**Unit Test Example:**
```python
import pytest
from ai_karen_engine.services import get_plugin_service

@pytest.mark.asyncio
async def test_plugin_execution():
    plugin_service = get_plugin_service()
    
    result = await plugin_service.execute_plugin(
        name="test-plugin",
        params={"input": "test"},
        user_context={"user_id": "test_user"}
    )
    
    assert result["status"] == "success"
    assert "output" in result
```

**Integration Test Example:**
```python
import pytest
from fastapi.testclient import TestClient
from ai_karen_engine.fastapi import app

client = TestClient(app)

def test_api_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_plugin_api_execution():
    response = client.post("/plugins/execute", json={
        "name": "test-plugin",
        "params": {"input": "test"}
    })
    assert response.status_code == 200
    assert "result" in response.json()
```

## Code Style and Standards

### Python Code Style

**Formatting:**
- Use `black` for code formatting
- Use `isort` for import sorting
- Line length: 88 characters (black default)

**Linting:**
- Use `ruff` for fast Python linting
- Follow PEP 8 guidelines
- Use type hints for all functions

**Type Checking:**
- Use `mypy` with strict mode
- Provide type annotations for all public APIs
- Use `typing` module for complex types

**Example:**
```python
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

async def process_data(
    data: List[Dict[str, Union[str, int]]],
    options: Optional[Dict[str, str]] = None
) -> Dict[str, List[str]]:
    """Process input data with optional configuration.
    
    Args:
        data: List of data dictionaries to process
        options: Optional processing configuration
        
    Returns:
        Dictionary containing processed results
        
    Raises:
        ValueError: If data format is invalid
    """
    if not data:
        raise ValueError("Data cannot be empty")
    
    logger.info(f"Processing {len(data)} records")
    
    # Processing logic here
    result = {"processed": []}
    
    return result
```

### JavaScript/TypeScript Code Style

**Formatting:**
- Use Prettier for code formatting
- Use ESLint for linting
- 2-space indentation
- Semicolons required

**TypeScript:**
- Strict TypeScript configuration
- Explicit return types for functions
- Interface definitions for complex objects

**Example:**
```typescript
interface UserData {
  id: string;
  name: string;
  email: string;
  preferences?: Record<string, unknown>;
}

export async function fetchUserData(userId: string): Promise<UserData> {
  try {
    const response = await fetch(`/api/users/${userId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch user: ${response.statusText}`);
    }
    
    const userData: UserData = await response.json();
    return userData;
  } catch (error) {
    console.error('Error fetching user data:', error);
    throw error;
  }
}
```

### Documentation Standards

**Python Docstrings:**
- Use Google-style docstrings
- Document all parameters and return values
- Include usage examples for complex functions

**Code Comments:**
- Use comments to explain "why", not "what"
- Keep comments up-to-date with code changes
- Use TODO comments for future improvements

**API Documentation:**
- Use FastAPI automatic documentation
- Provide clear endpoint descriptions
- Include request/response examples

## Debugging Procedures

### Backend Debugging

**Logging Configuration:**
```python
import logging

# Set up detailed logging for development
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable specific module debugging
logging.getLogger('ai_karen_engine.llm_orchestrator').setLevel(logging.DEBUG)
logging.getLogger('ai_karen_engine.plugins').setLevel(logging.DEBUG)
```

**Debug Mode:**
```bash
# Start API with debug logging
KARI_LOG_LEVEL=DEBUG uvicorn main:app --reload --port 8000

# Enable SQL query logging
KARI_DB_ECHO=true uvicorn main:app --reload --port 8000
```

**Using Python Debugger:**
```python
import pdb

def problematic_function():
    # Set breakpoint
    pdb.set_trace()
    
    # Your code here
    result = complex_operation()
    return result
```

**Performance Profiling:**
```bash
# Profile API performance
pip install py-spy
py-spy record -o profile.svg -- python -m uvicorn main:app --port 8000

# Memory profiling
pip install memory-profiler
python -m memory_profiler your_script.py
```

### Frontend Debugging

**Browser Developer Tools:**
- Use Chrome/Firefox DevTools for debugging
- Check Network tab for API calls
- Use Console for JavaScript errors
- Use React DevTools for component debugging

**Next.js Debugging:**
```bash
# Enable debug mode
DEBUG=* npm run dev

# TypeScript checking
npm run type-check
```

**Streamlit Debugging:**
```bash
# Enable debug mode
streamlit run app.py --logger.level debug

# Show component tree
streamlit run app.py --server.enableStaticServing false
```

### Database Debugging

**Query Debugging:**
```python
# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Manual query execution
from ai_karen_engine.database import get_db_client

async with get_db_client().get_session() as session:
    result = await session.execute("SELECT * FROM users LIMIT 5")
    print(result.fetchall())
```

**Connection Issues:**
```bash
# Test database connection
psql -h localhost -U karen_user -d karen_dev -c "SELECT version();"

# Check Redis connection
redis-cli ping
```

## Documentation Guidelines

### README Files

**Structure:**
1. Brief description and purpose
2. Features and capabilities
3. Prerequisites and dependencies
4. Installation/setup instructions
5. Usage examples
6. Configuration options
7. Troubleshooting
8. Contributing guidelines

**Best Practices:**
- Keep README files up-to-date with code changes
- Include working code examples
- Use clear, concise language
- Add screenshots for UI components
- Link to relevant documentation

### API Documentation

**FastAPI Documentation:**
- Use descriptive endpoint summaries
- Provide request/response examples
- Document error responses
- Include authentication requirements

**Example:**
```python
@app.post("/plugins/execute", 
          summary="Execute a plugin",
          description="Execute a plugin with given parameters and user context",
          response_model=PluginExecutionResult)
async def execute_plugin(
    request: PluginExecutionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute a plugin with the provided parameters.
    
    - **name**: Plugin name to execute
    - **params**: Plugin-specific parameters
    - **user_context**: User context for execution
    
    Returns the plugin execution result including output and metadata.
    """
    # Implementation here
```

### Code Documentation

**Inline Documentation:**
- Document complex algorithms and business logic
- Explain non-obvious code decisions
- Include links to relevant specifications or RFCs
- Use type hints as documentation

## Contributing Guidelines

### Development Workflow

1. **Fork and Clone**
```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/your-username/ai-karen.git
cd ai-karen
```

2. **Create Feature Branch**
```bash
# Create and switch to feature branch
git checkout -b feature/my-new-feature

# Or for bug fixes
git checkout -b fix/bug-description
```

3. **Make Changes**
- Follow code style guidelines
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

4. **Commit Changes**
```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new plugin execution feature

- Add support for async plugin execution
- Implement plugin timeout handling
- Add comprehensive error handling
- Update API documentation"
```

5. **Push and Create PR**
```bash
# Push to your fork
git push origin feature/my-new-feature

# Create pull request on GitHub
```

### Commit Message Guidelines

**Format:**
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(plugins): add plugin timeout configuration

fix(api): resolve memory leak in conversation service

docs(readme): update installation instructions

test(core): add unit tests for LLM orchestrator
```

### Pull Request Guidelines

**Before Submitting:**
- [ ] All tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] No merge conflicts with main branch

**PR Description Template:**
```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Documentation
- [ ] README updated
- [ ] API documentation updated
- [ ] Code comments added

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests pass locally
- [ ] No breaking changes (or clearly documented)
```

### Code Review Process

**For Reviewers:**
1. Check code quality and style
2. Verify test coverage
3. Test functionality manually if needed
4. Provide constructive feedback
5. Approve when ready

**For Contributors:**
1. Address all review comments
2. Update code based on feedback
3. Ensure tests still pass
4. Request re-review when ready

### Release Process

**Version Numbering:**
- Follow Semantic Versioning (SemVer)
- Format: MAJOR.MINOR.PATCH
- Breaking changes increment MAJOR
- New features increment MINOR
- Bug fixes increment PATCH

**Release Checklist:**
1. Update version numbers
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Create GitHub release
6. Deploy to staging
7. Deploy to production

## Accessibility Guidelines

To meet WCAG AA requirements, ensure all text maintains a contrast ratio of at least **4.5:1** (or **3:1** for large headings). Interactive widgets must be reachable with the keyboard and provide visible focus outlines.

### Keyboard Shortcuts

| Action | Shortcut |
| ------ | -------- |
| Focus search | `/` |
| Toggle dark mode | `Ctrl+Shift+D` |
| Open help | `?` |

These shortcuts should be implemented in custom components where possible.

## Continuous Integration

All pull requests trigger the workflow defined in `.github/workflows/ci.yml`.
The job installs dependencies and then runs the following checks:

1. `ruff` for linting
2. `black --check` for formatting
3. `mypy --strict` for type safety
4. `pytest` with coverage

If the tests pass, the workflow builds a Docker image from the repository's
`Dockerfile` and pushes it to the GitHub Container Registry under the commit
SHA tag.

## Documentation Maintenance

### Keeping Documentation Current

As the AI Karen system evolves, it's crucial to keep documentation synchronized with code changes:

**Documentation Update Checklist:**
- [ ] Update README files when adding new features
- [ ] Update API documentation when changing endpoints
- [ ] Update environment variable documentation when adding new config
- [ ] Update setup instructions when changing dependencies
- [ ] Update troubleshooting guides when resolving common issues

**Automated Documentation Checks:**
```bash
# Run documentation validation
python scripts/validate_documentation.py

# Check for broken links
python scripts/link_checker.py

# Validate code examples
python scripts/code_example_validator.py
```

**Documentation Review Process:**
1. Technical accuracy review by subject matter experts
2. User experience review from documentation perspective
3. Consistency review for tone, style, and formatting
4. Completeness review to ensure all features are documented

This development guide provides comprehensive information for contributing to the AI Karen project. For specific questions or issues, please refer to the project's GitHub issues or contact the development team.
