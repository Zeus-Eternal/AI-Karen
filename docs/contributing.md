# Contributing to AI Karen

We welcome contributions from the community! Whether you're fixing bugs, adding features, improving documentation, or creating plugins and extensions, your contributions help make AI Karen better for everyone.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contribution Types](#contribution-types)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation Guidelines](#documentation-guidelines)
- [Pull Request Process](#pull-request-process)
- [Community Guidelines](#community-guidelines)

## Getting Started

Before contributing, please:

1. **Read the Code of Conduct** - We maintain a welcoming and inclusive community
2. **Check existing issues** - Your contribution might already be in progress
3. **Join our discussions** - Connect with other contributors and maintainers
4. **Review the architecture** - Understand the system design and patterns

## Development Setup

### Prerequisites

Ensure you have the required software installed:

- **Python 3.10+** - Core backend development
- **Node.js 18+** - Frontend development
- **Docker & Docker Compose** - For database services
- **Git** - Version control

### Quick Setup

```bash
# Clone your fork
git clone https://github.com/your-username/ai-karen.git
cd ai-karen

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -r requirements.txt

# Install development tools
pip install pytest pytest-asyncio black ruff mypy pre-commit

# Set up pre-commit hooks
pre-commit install

# Set required environment variables
export KARI_MODEL_SIGNING_KEY=dev-signing-key
export KARI_DUCKDB_PASSWORD=dev-duckdb-pass
export KARI_JOB_SIGNING_KEY=dev-job-key

# Start database services
cd docker/database && docker compose up -d

# Verify setup
PYTHONPATH=src pytest tests/test_basic_setup.py
```

For detailed setup instructions, see the [Development Guide](development_guide.md).

## Contribution Types

### 🐛 Bug Fixes

- Fix existing functionality that isn't working correctly
- Improve error handling and edge cases
- Resolve performance issues
- Fix security vulnerabilities

### ✨ New Features

- Add new AI capabilities or integrations
- Implement new UI components or interfaces
- Create new plugins or extensions
- Add new API endpoints or services

### 📚 Documentation

- Improve README files and setup instructions
- Add code examples and tutorials
- Update API documentation
- Create troubleshooting guides

### 🔧 Plugins and Extensions

- Create new plugins for specific functionality
- Build extensions that compose multiple plugins
- Integrate with external services and APIs
- Add new AI model providers

### 🧪 Testing

- Add unit tests for existing code
- Create integration tests
- Improve test coverage
- Add performance benchmarks

## Development Workflow

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/your-username/ai-karen.git
cd ai-karen

# Add upstream remote
git remote add upstream https://github.com/original-org/ai-karen.git
```

### 2. Create Feature Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### 3. Make Changes

- Follow the coding standards outlined below
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass locally

### 4. Commit Changes

Use conventional commit messages:

```bash
git add .
git commit -m "feat(plugins): add new data processing plugin

- Add support for CSV data processing
- Implement data validation and transformation
- Add comprehensive error handling
- Include unit tests and documentation"
```

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
```

## Coding Standards

### Python Code Style

**Formatting and Linting:**
```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint code
ruff check src/ tests/ --fix

# Type checking
mypy src/ai_karen_engine --strict
```

**Code Quality Requirements:**
- Use type hints for all function parameters and return values
- Follow PEP 8 style guidelines
- Write descriptive docstrings using Google style
- Keep functions focused and single-purpose
- Use meaningful variable and function names

**Example:**
```python
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

async def process_user_data(
    user_data: List[Dict[str, str]],
    options: Optional[Dict[str, str]] = None
) -> Dict[str, int]:
    """Process user data with optional configuration.
    
    Args:
        user_data: List of user data dictionaries
        options: Optional processing configuration
        
    Returns:
        Dictionary with processing results and statistics
        
    Raises:
        ValueError: If user_data is empty or invalid
    """
    if not user_data:
        raise ValueError("User data cannot be empty")
    
    logger.info(f"Processing {len(user_data)} user records")
    
    # Processing logic here
    return {"processed_count": len(user_data)}
```

### JavaScript/TypeScript Code Style

**Formatting:**
```bash
# Format code
npm run format

# Lint code
npm run lint

# Type checking
npm run type-check
```

**Requirements:**
- Use TypeScript for all new JavaScript code
- Follow Prettier formatting rules
- Use ESLint configuration provided
- Provide explicit type annotations
- Use modern ES6+ features

### Plugin Development Standards

**Plugin Structure:**
```
plugin_marketplace/category/plugin-name/
├── plugin_manifest.json    # Plugin metadata
├── handler.py             # Main plugin logic
├── README.md              # Plugin documentation
├── requirements.txt       # Plugin dependencies (optional)
└── tests/                 # Plugin tests
    └── test_handler.py
```

**Plugin Manifest Example:**
```json
{
    "name": "data-processor",
    "version": "1.0.0",
    "description": "Process and transform data",
    "author": "Your Name",
    "license": "MIT",
    "handler": "handler.py",
    "permissions": ["basic", "file_access"],
    "dependencies": {
        "python": ["pandas>=1.3.0"]
    },
    "tags": ["data", "processing", "utility"]
}
```

**Plugin Handler Example:**
```python
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def handle(params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Plugin handler function.
    
    Args:
        params: Plugin execution parameters
        context: Execution context including user info
        
    Returns:
        Plugin execution result
    """
    try:
        # Plugin logic here
        result = process_data(params.get("data", []))
        
        return {
            "status": "success",
            "result": result,
            "metadata": {
                "processed_items": len(result)
            }
        }
    except Exception as e:
        logger.error(f"Plugin execution failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def process_data(data):
    """Process the input data."""
    # Implementation here
    return data
```

## Testing Requirements

### Test Coverage

- Maintain minimum 85% test coverage
- Write unit tests for all new functions
- Add integration tests for API endpoints
- Include edge case and error condition tests

### Running Tests

```bash
# Run all tests
PYTHONPATH=src pytest

# Run with coverage
PYTHONPATH=src pytest --cov=src/ai_karen_engine --cov-report=html

# Run specific test files
pytest tests/test_plugins.py -v

# Run tests for specific functionality
pytest -k "test_plugin_execution"
```

### Writing Tests

**Unit Test Example:**
```python
import pytest
from unittest.mock import AsyncMock, patch
from ai_karen_engine.services import PluginService

@pytest.mark.asyncio
async def test_plugin_execution_success():
    """Test successful plugin execution."""
    plugin_service = PluginService()
    
    with patch('ai_karen_engine.plugins.router.PluginRouter.dispatch') as mock_dispatch:
        mock_dispatch.return_value = ("success", "output", "")
        
        result = await plugin_service.execute_plugin(
            name="test-plugin",
            params={"input": "test"},
            user_context={"user_id": "test_user"}
        )
        
        assert result[0] == "success"
        mock_dispatch.assert_called_once()

@pytest.mark.asyncio
async def test_plugin_execution_failure():
    """Test plugin execution failure handling."""
    plugin_service = PluginService()
    
    with patch('ai_karen_engine.plugins.router.PluginRouter.dispatch') as mock_dispatch:
        mock_dispatch.side_effect = Exception("Plugin failed")
        
        with pytest.raises(Exception, match="Plugin failed"):
            await plugin_service.execute_plugin(
                name="failing-plugin",
                params={},
                user_context={"user_id": "test_user"}
            )
```

**Integration Test Example:**
```python
import pytest
from fastapi.testclient import TestClient
from ai_karen_engine.fastapi import app

client = TestClient(app)

def test_plugin_api_execution():
    """Test plugin execution via API."""
    response = client.post("/plugins/execute", json={
        "name": "test-plugin",
        "params": {"input": "test data"},
        "user_context": {"user_id": "test_user"}
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["status"] == "success"

def test_plugin_api_invalid_plugin():
    """Test API response for invalid plugin."""
    response = client.post("/plugins/execute", json={
        "name": "nonexistent-plugin",
        "params": {},
        "user_context": {"user_id": "test_user"}
    })
    
    assert response.status_code == 404
    assert "error" in response.json()
```

## Documentation Guidelines

### README Files

When updating README files:

1. **Keep them current** - Update when functionality changes
2. **Include examples** - Provide working code examples
3. **Be comprehensive** - Cover setup, usage, and troubleshooting
4. **Use clear language** - Write for your target audience
5. **Add screenshots** - Visual aids for UI components

### Code Documentation

- Write docstrings for all public functions and classes
- Include parameter types and descriptions
- Document return values and exceptions
- Add usage examples for complex functions

### API Documentation

- Use FastAPI's automatic documentation features
- Provide clear endpoint descriptions
- Include request/response examples
- Document error responses and status codes

## Pull Request Process

### Before Submitting

**Pre-submission Checklist:**
- [ ] All tests pass locally (`PYTHONPATH=src pytest`)
- [ ] Code follows style guidelines (`black`, `ruff`, `mypy`)
- [ ] Documentation is updated
- [ ] Commit messages follow conventional format
- [ ] No merge conflicts with main branch
- [ ] Pre-commit hooks pass

### PR Description Template

Use this template for your pull request description:

```markdown
## Description
Brief description of the changes made and why.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Refactoring (no functional changes)

## How Has This Been Tested?
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] Tested on multiple environments

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
```

### Review Process

**For Contributors:**
1. Address all review comments promptly
2. Update code based on feedback
3. Ensure tests still pass after changes
4. Request re-review when ready
5. Be responsive to maintainer questions

**Review Timeline:**
- Initial review: Within 3-5 business days
- Follow-up reviews: Within 1-2 business days
- Complex changes may require additional time

## Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please:

- **Be respectful** - Treat all community members with respect
- **Be inclusive** - Welcome newcomers and help them get started
- **Be constructive** - Provide helpful feedback and suggestions
- **Be patient** - Remember that everyone is learning
- **Be collaborative** - Work together to solve problems

### Getting Help

If you need help with your contribution:

1. **Check the documentation** - Start with the development guide
2. **Search existing issues** - Your question might already be answered
3. **Ask in discussions** - Use GitHub Discussions for questions
4. **Join our community** - Connect with other contributors
5. **Contact maintainers** - Reach out directly if needed

### Recognition

We value all contributions and recognize contributors through:

- **Contributor list** - All contributors are listed in our README
- **Release notes** - Significant contributions are highlighted
- **Community highlights** - Outstanding contributions are featured
- **Maintainer opportunities** - Active contributors may be invited to join the maintainer team

## Plugin and Extension Marketplace

### Publishing Guidelines

When creating plugins or extensions for the marketplace:

1. **Follow naming conventions** - Use clear, descriptive names
2. **Provide comprehensive documentation** - Include setup and usage instructions
3. **Add proper licensing** - Specify license terms clearly
4. **Include tests** - Provide test coverage for your code
5. **Version appropriately** - Follow semantic versioning
6. **Tag appropriately** - Use relevant tags for discoverability

### Quality Standards

All marketplace contributions must meet these standards:

- **Security** - No security vulnerabilities or malicious code
- **Performance** - Efficient resource usage
- **Reliability** - Proper error handling and edge case management
- **Documentation** - Clear documentation and examples
- **Testing** - Adequate test coverage

### Submission Process

1. Create your plugin/extension following the guidelines
2. Test thoroughly in your development environment
3. Submit a pull request with your contribution
4. Respond to review feedback promptly
5. Update based on maintainer suggestions

Thank you for contributing to AI Karen! Your contributions help make this project better for everyone. If you have questions about contributing, please don't hesitate to ask in our GitHub Discussions or reach out to the maintainers directly.
