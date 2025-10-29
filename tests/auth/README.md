# Comprehensive Authentication Test Suite

This directory contains a comprehensive test suite for the extension authentication system, covering all aspects from unit tests to security vulnerability testing.

## Overview

The authentication test suite is designed to validate the complete authentication flow for the Kari platform's extension system, ensuring that:

- Authentication middleware works correctly
- API endpoints are properly secured
- Frontend authentication flows function end-to-end
- Security vulnerabilities are prevented
- Performance requirements are met

## Test Structure

### 📁 Test Categories

#### 1. Unit Tests (`tests/unit/auth/`)
- **File**: `test_extension_auth_middleware.py`
- **Purpose**: Test core authentication middleware functionality
- **Coverage**:
  - JWT token creation and validation
  - Permission checking logic
  - User context creation
  - Error handling for invalid tokens
  - Development mode authentication
  - Edge cases and error conditions

#### 2. Integration Tests (`tests/integration/auth/`)
- **File**: `test_extension_api_authentication.py`
- **Purpose**: Test authentication integration with FastAPI endpoints
- **Coverage**:
  - Extension API endpoint authentication
  - Role-based access control
  - Tenant isolation
  - Service token authentication
  - API key authentication
  - Concurrent request handling

#### 3. End-to-End Tests (`tests/e2e/`)
- **File**: `test_frontend_authentication_flow.py`
- **Purpose**: Test complete authentication flow from frontend to backend
- **Coverage**:
  - Login and token acquisition
  - Token refresh mechanisms
  - Authenticated API calls
  - Error scenario handling
  - Performance under load
  - CORS and frontend integration

#### 4. Security Tests (`tests/security/`)
- **File**: `test_extension_authentication_security.py`
- **Purpose**: Test security aspects and vulnerability prevention
- **Coverage**:
  - JWT signature verification
  - Token tampering detection
  - Algorithm confusion attacks
  - Timing attack resistance
  - Privilege escalation prevention
  - Information disclosure prevention

### 🎯 Test Metrics

| Category | Test Classes | Test Functions | Coverage Areas |
|----------|-------------|----------------|----------------|
| Unit Tests | 2 | 17 | Middleware core functionality |
| Integration Tests | 3 | 24 | API endpoint security |
| E2E Tests | 3 | 20 | Complete authentication flows |
| Security Tests | 3 | 27 | Vulnerability prevention |
| **Total** | **11** | **88** | **All authentication aspects** |

## Running Tests

### Prerequisites

```bash
# Install required dependencies
pip install pytest fastapi jwt python-multipart

# Ensure server modules are in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/server"
```

### Running Individual Test Categories

```bash
# Unit tests
pytest tests/unit/auth/ -v

# Integration tests  
pytest tests/integration/auth/ -v

# End-to-end tests
pytest tests/e2e/test_frontend_authentication_flow.py -v

# Security tests
pytest tests/security/test_extension_authentication_security.py -v
```

### Running Comprehensive Suite

```bash
# Run the complete authentication test suite
python3 tests/auth/test_comprehensive_authentication_suite.py

# Or using pytest
pytest tests/auth/test_comprehensive_authentication_suite.py -v
```

### Running with Specific Markers

```bash
# Run only security tests
pytest -m security -v

# Run only fast tests (exclude slow performance tests)
pytest -m "not slow" -v

# Run tests that don't require network
pytest -m "not requires_network" -v
```

## Test Configuration

### Configuration Files

- **`conftest.py`**: Shared fixtures and configuration for all authentication tests
- **`test_comprehensive_authentication_suite.py`**: Orchestrates all test categories

### Key Fixtures

- `test_auth_config`: Standard authentication configuration
- `test_auth_manager`: Pre-configured authentication manager
- `mock_request`: Mock FastAPI request object
- `valid_user_context`: Standard user context for testing
- `admin_user_context`: Admin user context for testing

### Environment Variables

```bash
# Optional: Override test configuration
export TEST_SECRET_KEY="custom-test-secret"
export TEST_API_KEY="custom-test-api-key"
export TEST_AUTH_MODE="testing"
```

## Test Data

### Test Users

```python
TEST_USERS = {
    "regular_user": {
        "user_id": "regular_user",
        "tenant_id": "tenant1", 
        "roles": ["user"],
        "permissions": ["extension:read", "extension:write"]
    },
    "admin_user": {
        "user_id": "admin_user",
        "tenant_id": "tenant1",
        "roles": ["admin"], 
        "permissions": ["extension:*"]
    },
    # ... more test users
}
```

### Test Extensions

```python
TEST_EXTENSIONS = {
    "basic-extension": {
        "name": "basic-extension",
        "capabilities": ["read"]
    },
    "advanced-extension": {
        "name": "advanced-extension", 
        "capabilities": ["read", "write", "admin"]
    }
    # ... more test extensions
}
```

## Security Test Coverage

### Vulnerability Tests

- ✅ **JWT Signature Verification**: Prevents token tampering
- ✅ **Algorithm Confusion**: Prevents 'none' algorithm attacks
- ✅ **Token Expiration**: Enforces proper token lifecycle
- ✅ **Timing Attacks**: Consistent validation timing
- ✅ **Privilege Escalation**: Prevents permission elevation
- ✅ **Information Disclosure**: Generic error messages
- ✅ **Brute Force Protection**: Rate limiting considerations
- ✅ **Session Fixation**: Unique token identifiers

### Best Practices Tests

- ✅ **Principle of Least Privilege**: Minimal default permissions
- ✅ **Secure Token Expiration**: Short-lived access tokens
- ✅ **HTTPS Requirements**: Production security requirements
- ✅ **API Key Entropy**: Strong API key generation
- ✅ **Audit Logging**: Comprehensive event tracking

## Performance Benchmarks

### Authentication Performance

- **Target**: < 10ms per authentication request
- **Load Testing**: 100 concurrent requests
- **Token Validation**: Efficient caching and validation

### Test Execution Performance

- **Unit Tests**: < 30 seconds
- **Integration Tests**: < 60 seconds  
- **E2E Tests**: < 120 seconds
- **Security Tests**: < 90 seconds
- **Total Suite**: < 5 minutes

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Fix: Add server to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/server"
```

#### Missing Dependencies
```bash
# Fix: Install test dependencies
pip install -r tests/requirements_test.txt
```

#### Token Validation Failures
```bash
# Fix: Check secret key configuration
export TEST_SECRET_KEY="your-test-secret-key"
```

### Debug Mode

```bash
# Run tests with verbose output and no capture
pytest tests/auth/ -v -s --tb=long

# Run specific test with debugging
pytest tests/unit/auth/test_extension_auth_middleware.py::TestExtensionAuthManager::test_create_access_token -v -s
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Authentication Tests
on: [push, pull_request]

jobs:
  auth-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements_test.txt
      - name: Run authentication tests
        run: |
          export PYTHONPATH="${PYTHONPATH}:$(pwd)/server"
          python3 tests/auth/test_comprehensive_authentication_suite.py
```

## Contributing

### Adding New Tests

1. **Choose the appropriate category** (unit/integration/e2e/security)
2. **Follow naming conventions** (`test_*.py`, `TestClassName`, `test_method_name`)
3. **Use existing fixtures** from `conftest.py`
4. **Add appropriate markers** (`@pytest.mark.security`, etc.)
5. **Update this README** if adding new test categories

### Test Quality Guidelines

- **Isolation**: Tests should not depend on each other
- **Deterministic**: Tests should produce consistent results
- **Fast**: Unit tests should complete quickly
- **Clear**: Test names should describe what they test
- **Comprehensive**: Cover both happy path and error cases

## Validation

Run the validation script to ensure test suite integrity:

```bash
python3 validate_authentication_test_suite.py
```

This validates:
- ✅ All test files exist and have valid syntax
- ✅ Required imports are available
- ✅ Test coverage across all authentication areas
- ✅ Configuration files are present

## Requirements Mapping

This test suite validates the following requirements from the specification:

- **Requirement 1.1-1.5**: Extension API Authentication Resolution
- **Requirement 2.1-2.5**: Backend Service Connectivity Fix  
- **Requirement 3.1-3.5**: Extension Integration Service Error Handling
- **Requirement 4.1-4.5**: Extension Background Task Authentication
- **Requirement 5.1-5.5**: Extension Service Discovery and Health Monitoring

## Success Criteria

The authentication system is considered ready for deployment when:

- ✅ All unit tests pass (100% success rate)
- ✅ All integration tests pass (100% success rate)
- ✅ All E2E tests pass (100% success rate)
- ✅ All security tests pass (100% success rate)
- ✅ Performance benchmarks are met
- ✅ No critical security vulnerabilities detected

---

**Last Updated**: Task 23 Implementation  
**Test Suite Version**: 1.0.0  
**Total Test Coverage**: 88 test functions across 11 test classes