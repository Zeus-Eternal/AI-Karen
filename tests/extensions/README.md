# Extension System Test Suite

This directory contains a comprehensive test suite for the Kari AI Extension System, covering all aspects of extension functionality, security, and performance.

## Test Structure

```
tests/
├── unit/extensions/                    # Unit tests
│   ├── test_extension_manager.py      # ExtensionManager class tests
│   └── test_base_extension.py         # BaseExtension class tests
├── integration/extensions/            # Integration tests
│   └── test_plugin_orchestration.py  # Plugin orchestration tests
├── security/extensions/               # Security tests
│   ├── test_tenant_isolation.py      # Tenant isolation tests
│   └── test_permissions.py           # Permission system tests
├── performance/extensions/            # Performance tests
│   ├── test_resource_limits.py       # Resource limit tests
│   └── test_scaling.py               # Scaling and load tests
├── run_extension_tests.py            # Test runner script
├── pytest_extensions.ini             # Pytest configuration
├── requirements_test.txt             # Test dependencies
└── README.md                         # This file
```

## Test Categories

### 1. Unit Tests (`tests/unit/extensions/`)

Tests individual components in isolation:

#### ExtensionManager Tests (`test_extension_manager.py`)
- Extension discovery and loading
- Lifecycle management (load/unload/reload)
- Status and health monitoring
- Installation and management
- Error handling and recovery
- Registry operations

#### BaseExtension Tests (`test_base_extension.py`)
- Extension initialization and shutdown
- Capability creation (API, UI, background tasks)
- Hook management and lifecycle
- MCP integration (when available)
- Status reporting and configuration

### 2. Integration Tests (`tests/integration/extensions/`)

Tests component interaction and workflows:

#### Plugin Orchestration Tests (`test_plugin_orchestration.py`)
- Single plugin execution
- Sequential workflow execution
- Parallel plugin execution
- Conditional and loop workflows
- Parameter reference resolution
- Context management
- Advanced workflow features

### 3. Security Tests (`tests/security/extensions/`)

Tests security boundaries and isolation:

#### Tenant Isolation Tests (`test_tenant_isolation.py`)
- Data segregation between tenants
- Extension loading with tenant context
- Cross-tenant access prevention
- Resource isolation
- Configuration isolation
- Audit logging

#### Permission Tests (`test_permissions.py`)
- Permission validation and structure
- Data access permission enforcement
- Plugin access permission enforcement
- System access permission enforcement
- Network access permission enforcement
- Runtime permission validation

### 4. Performance Tests (`tests/performance/extensions/`)

Tests performance characteristics and limits:

#### Resource Limits Tests (`test_resource_limits.py`)
- Memory usage tracking and limits
- CPU usage monitoring
- Disk usage tracking
- Resource monitoring startup
- Resource violation handling
- Scaling performance

#### Scaling Tests (`test_scaling.py`)
- Concurrent extension operations
- Load handling capabilities
- Resource contention management
- Thread safety
- System capacity limits
- Burst load handling

## Running Tests

### Run All Tests
```bash
python tests/run_extension_tests.py
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/extensions/ -v

# Integration tests only
pytest tests/integration/extensions/ -v

# Security tests only
pytest tests/security/extensions/ -v

# Performance tests only
pytest tests/performance/extensions/ -v
```

### Run Individual Test Files
```bash
# Extension manager tests
pytest tests/unit/extensions/test_extension_manager.py -v

# Plugin orchestration tests
pytest tests/integration/extensions/test_plugin_orchestration.py -v

# Tenant isolation tests
pytest tests/security/extensions/test_tenant_isolation.py -v

# Resource limits tests
pytest tests/performance/extensions/test_resource_limits.py -v
```

### Run with Coverage
```bash
pytest tests/unit/extensions/ --cov=src/ai_karen_engine/extensions --cov-report=html
```

## Test Requirements

Install test dependencies:
```bash
pip install -r tests/requirements_test.txt
```

### Required Dependencies
- `pytest>=7.0.0` - Core testing framework
- `pytest-asyncio>=0.21.0` - Async test support
- `pytest-mock>=3.10.0` - Mocking utilities
- `psutil>=5.9.0` - System resource monitoring

### Optional Dependencies
- `pytest-cov>=4.0.0` - Code coverage reporting
- `pytest-timeout>=2.1.0` - Test timeout handling

## Test Configuration

Tests are configured via `pytest_extensions.ini`:
- Async test mode enabled
- 5-minute timeout for long-running tests
- Colored output and verbose reporting
- Warning filters for clean output

## Test Data and Fixtures

### Common Fixtures
- `temp_extension_root` - Temporary directory for test extensions
- `mock_plugin_router` - Mock plugin router with realistic behavior
- `mock_db_session` - Mock database session with tenant isolation
- `extension_manager` - Configured ExtensionManager instance
- `sample_manifest` - Valid extension manifest for testing

### Test Extension Creation
Tests create realistic extension structures:
```python
def create_test_extension(self, temp_dir: Path, manifest_data: dict):
    """Create a test extension directory with manifest and __init__.py."""
    # Creates proper extension structure for testing
```

## Performance Benchmarks

### Expected Performance Characteristics

#### Discovery Performance
- Single extension: < 1 second
- 10 extensions: < 5 seconds
- Scaling: < 500ms per extension

#### Loading Performance
- Single extension: < 2 seconds
- 5 extensions (concurrent): < 8 seconds
- Memory per extension: < 50MB

#### Orchestration Performance
- Single plugin: < 100ms
- Sequential workflow (5 steps): < 200ms
- Parallel execution (5 plugins): < 100ms

#### Resource Limits
- Memory tracking: Active monitoring
- CPU limits: Configurable per extension
- Disk usage: Tracked and limited

## Security Test Coverage

### Tenant Isolation
- ✅ Data segregation between tenants
- ✅ Extension loading with tenant context
- ✅ Cross-tenant access prevention
- ✅ Resource isolation boundaries
- ✅ Configuration isolation

### Permission Enforcement
- ✅ Data access permission validation
- ✅ Plugin access permission enforcement
- ✅ System access permission controls
- ✅ Network access permission limits
- ✅ Runtime permission validation

### Security Boundaries
- ✅ Extension sandbox boundaries
- ✅ Resource limit enforcement
- ✅ File system access restrictions
- ✅ Database access boundaries
- ✅ Cross-extension isolation

## Troubleshooting

### Common Issues

#### Import Errors
Ensure the src directory is in Python path:
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
```

#### Async Test Issues
Use `pytest-asyncio` and mark async tests:
```python
@pytest.mark.asyncio
async def test_async_function():
    # Test async functionality
```

#### Mock Setup Issues
Verify mock objects have correct spec:
```python
router = Mock(spec=PluginRouter)
router.dispatch = AsyncMock(return_value="result")
```

#### Performance Test Variability
Performance tests include reasonable tolerances:
- Use relative comparisons when possible
- Allow for system load variations
- Focus on order-of-magnitude correctness

### Debug Mode
Run tests with additional debugging:
```bash
pytest tests/unit/extensions/ -v -s --tb=long
```

## Contributing

When adding new tests:

1. **Follow naming conventions**: `test_*.py` files, `Test*` classes, `test_*` methods
2. **Use appropriate fixtures**: Leverage existing fixtures for consistency
3. **Add proper documentation**: Include docstrings explaining test purpose
4. **Consider test categories**: Place tests in appropriate directories
5. **Mock external dependencies**: Use mocks for database, network, file system
6. **Test error conditions**: Include negative test cases
7. **Performance considerations**: Add performance tests for new features

### Test Quality Guidelines

- **Isolation**: Tests should not depend on each other
- **Repeatability**: Tests should produce consistent results
- **Clarity**: Test names and structure should be self-documenting
- **Coverage**: Aim for high code coverage with meaningful tests
- **Efficiency**: Tests should run as quickly as possible while being thorough

## Continuous Integration

These tests are designed to run in CI/CD environments:
- No external dependencies required
- Deterministic results
- Reasonable execution time
- Clear pass/fail criteria
- Comprehensive coverage of requirements

The test suite validates all requirements from the specification:
- **Requirement 8.1**: Extension security and isolation ✅
- **Requirement 8.2**: Tenant isolation and permissions ✅  
- **Requirement 8.3**: Resource limits and monitoring ✅
- **Requirement 8.4**: Performance and scaling characteristics ✅