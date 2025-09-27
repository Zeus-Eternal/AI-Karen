# AI-Karen Test Organization Guide

## Overview

The AI-Karen test suite has been completely reorganized for better maintainability, faster execution, and clearer separation of concerns. Tests are now organized by type and functionality.

## Directory Structure

```
tests/
├── conftest.py                      # Global pytest configuration and fixtures
├── __init__.py
├── fixtures/                       # Shared test fixtures and data
├── unit/                           # Unit tests for individual components
│   ├── core/                       # Core engine tests (145 files)
│   ├── services/                   # Service layer tests
│   ├── middleware/                 # Middleware tests (21 files)
│   ├── models/                     # Database model tests (24 files)
│   ├── utils/                      # Utility function tests (9 files)
│   ├── ai/                         # AI/ML component tests (45 files)
│   └── database/                   # Database layer tests (25 files)
├── integration/                    # Integration tests
│   ├── api/                        # API integration tests (13 files)
│   ├── database/                   # Database integration tests (2 files)
│   ├── auth/                       # Authentication flow tests
│   ├── services/                   # Service integration tests (9 files)
│   ├── marketplace/                # Marketplace example validation
│   └── external/                   # External service integration (20 files)
├── e2e/                           # End-to-end tests
├── performance/                    # Performance and load tests (16 files)
├── security/                      # Security-focused tests (5 files)
├── manual/                        # Manual test scripts and helpers
│   └── scripts/                   # Shell scripts for manual testing
├── stubs/                         # Test stubs and mocks
└── data/                          # Test data and fixtures
```

## Test Categories

### Unit Tests (269 files)
- **Core (145 files)**: Core engine functionality, orchestration, memory management
- **AI (45 files)**: LLM providers, embeddings, model orchestration, GPU operations
- **Database (25 files)**: Database clients, connections, migrations
- **Models (24 files)**: Database models, schemas, validation
- **Middleware (21 files)**: Authentication, RBAC, session management
- **Utils (9 files)**: Utility functions, encryption, validation

### Integration Tests (45 files)
- **External (20 files)**: Third-party service integrations
- **API (13 files)**: API endpoint integration tests
- **Services (9 files)**: Service-to-service integration
- **Marketplace**: Marketplace example validation
- **Database (2 files)**: Database integration flows

### Specialized Tests
- **Performance (16 files)**: Load testing, benchmarks, optimization
- **Security (5 files)**: Security components, threat detection
- **Manual**: Manual tests and scripts

## Running Tests

### Using the Test Runner Script

```bash
# Run all unit tests
python run_tests.py --unit

# Run integration tests
python run_tests.py --integration

# Run tests by category
python run_tests.py --category middleware
python run_tests.py --category ai

# Run tests by marker
python run_tests.py --auth          # Authentication tests
python run_tests.py --database      # Database tests
python run_tests.py --llm           # LLM tests

# Run with coverage
python run_tests.py --unit --coverage

# Run fast tests only
python run_tests.py --fast

# Run specific files
python run_tests.py tests_new/unit/middleware/test_auth_middleware.py
```

### Using Poetry and Pytest Directly

```bash
# Run all tests
poetry run pytest

# Run specific test types
poetry run pytest tests/unit
poetry run pytest tests/integration

# Run with markers
poetry run pytest -m "auth"
poetry run pytest -m "database and not slow"

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run in parallel
poetry run pytest -n auto
```

## Test Markers

Tests are marked with the following markers for selective execution:

- `unit`: Unit tests for individual components
- `integration`: Integration tests between components
- `e2e`: End-to-end tests
- `performance`: Performance and load tests
- `security`: Security-focused tests
- `manual`: Manual tests requiring human intervention
- `slow`: Tests that take a long time to run
- `database`: Tests that require database connection
- `external`: Tests that require external services
- `auth`: Authentication-related tests
- `api`: API endpoint tests
- `memory`: Memory system tests
- `llm`: LLM and AI model tests

## Configuration Files

### pytest_new.ini
The main pytest configuration with:
- Test paths and patterns
- Marker definitions
- Coverage settings
- Warning filters
- Execution options

### .coveragerc
Coverage configuration for:
- Source inclusion/exclusion
- Report formatting
- HTML and XML output

## Best Practices

### Test Organization
1. **Unit tests** should test individual functions/methods in isolation
2. **Integration tests** should test component interactions
3. **E2E tests** should test complete user workflows
4. **Performance tests** should measure and validate performance metrics

### Naming Conventions
- Test files: `test_[component_name].py`
- Test classes: `Test[ComponentName]`
- Test methods: `test_[functionality]`

### Test Structure
```python
def test_functionality():
    # Arrange
    setup_data = create_test_data()
    
    # Act
    result = function_under_test(setup_data)
    
    # Assert
    assert result == expected_value
```

### Fixtures and Mocks
- Use fixtures for shared test data
- Mock external dependencies
- Keep tests isolated and deterministic

## Continuous Integration

The organized structure supports:
- **Parallel execution** for faster CI runs
- **Targeted testing** based on changed components
- **Progressive testing** (unit → integration → e2e)
- **Coverage tracking** by component and functionality

## Migration Notes

### What Was Done
1. **Analyzed 770+ test files** scattered in the old structure
2. **Categorized tests** by type and functionality using pattern matching
3. **Moved 340 files successfully** to the new organized structure
4. **Created proper directory structure** with init files
5. **Updated configuration** for the new test paths

### Files Moved by Category
- Unit/Core: 145 files
- Unit/AI: 45 files  
- Unit/Database: 25 files
- Unit/Models: 24 files
- Unit/Middleware: 21 files
- Integration/External: 20 files
- Performance: 16 files
- Integration/API: 13 files
- Unit/Utils: 9 files
- Integration/Services: 9 files
- Security: 5 files
- Manual: 6 files

### Legacy Structure
The old `tests/` directory is preserved for reference and gradual migration. Once the new structure is validated, the old directory can be removed.

## Next Steps

1. **Validate test execution** with the new structure
2. **Update CI/CD pipelines** to use new test paths
3. **Add missing test markers** to existing tests
4. **Create additional fixtures** for common test scenarios
5. **Remove duplicate tests** identified during organization
6. **Update documentation references** to new test paths
