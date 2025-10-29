# Health Monitoring Test Suite

This directory contains comprehensive tests for the extension service health monitoring system. The test suite covers unit tests, integration tests, performance testing, and chaos engineering scenarios.

## Test Structure

```
tests/health/
├── README.md                           # This file
├── conftest.py                         # Shared fixtures and configuration
├── run_health_monitoring_tests.py      # Test runner script
├── unit/
│   └── test_extension_service_monitor.py    # Unit tests for core components
├── integration/
│   └── test_service_recovery_mechanisms.py  # Integration tests for recovery
├── performance/
│   └── test_health_check_performance.py     # Load and performance tests
└── chaos/
    └── test_chaos_engineering_scenarios.py  # Chaos engineering tests
```

## Test Categories

### 1. Unit Tests (`tests/unit/health/`)

Tests individual components of the health monitoring system:

- **ExtensionServiceMonitor** core functionality
- Health check execution logic
- Service status tracking
- Failure detection and counting
- Recovery attempt triggering
- Status reporting and calculations

**Key Test Cases:**
- Service monitor initialization
- Extension manager health checks (success/failure)
- Extension health checks (healthy/degraded/unhealthy)
- Failure count increment and reset
- Recovery attempt triggering at thresholds
- Overall health calculation algorithms
- Exception handling in health checks

### 2. Integration Tests (`tests/integration/health/`)

Tests complete recovery workflows and service interactions:

- **End-to-end recovery scenarios**
- Service failure detection and automatic recovery
- Partial system recovery (some services failing)
- Recovery timeout handling
- Cascading failure recovery
- Recovery within monitoring loops
- Recovery state persistence
- Concurrent recovery attempts

**Key Test Cases:**
- Complete failure detection and recovery cycle
- Extension-specific recovery mechanisms
- Partial system recovery scenarios
- Recovery timeout and slow recovery handling
- Cascading failure detection and recovery
- Recovery integration with monitoring loops
- Recovery state management and persistence
- Multiple concurrent recovery attempts

### 3. Performance Tests (`tests/performance/health/`)

Tests system performance under various load conditions:

- **Health check execution performance**
- Concurrent health check handling
- Memory usage during monitoring
- Scalability with multiple extensions
- Monitoring loop performance
- Recovery performance under load

**Key Test Cases:**
- Single health check cycle performance
- Concurrent health check load testing
- Memory usage monitoring during extended operation
- Scalability testing with varying extension counts
- Continuous monitoring loop performance
- Recovery performance under high load
- Status reporting performance with large datasets
- Thread safety and concurrent access performance

### 4. Chaos Engineering Tests (`tests/chaos/health/`)

Tests system resilience under failure conditions:

- **Random service failures**
- Network partition scenarios
- Resource exhaustion conditions
- Slow response handling
- Intermittent failure patterns
- Cascading failure scenarios
- Recovery under stress conditions

**Key Test Cases:**
- Random service failure resilience
- Network partition handling and recovery
- Resource exhaustion graceful degradation
- Slow response timeout handling
- Intermittent failure pattern detection
- Cascading failure containment
- Recovery mechanisms under stress
- Extreme failure scenario handling
- Multiple concurrent chaos conditions

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-timeout psutil

# Install coverage tools (optional)
pip install pytest-cov
```

### Quick Start

```bash
# Run all health monitoring tests
python tests/health/run_health_monitoring_tests.py

# Run specific test suite
python tests/health/run_health_monitoring_tests.py --suite unit
python tests/health/run_health_monitoring_tests.py --suite integration
python tests/health/run_health_monitoring_tests.py --suite performance
python tests/health/run_health_monitoring_tests.py --suite chaos

# Run with verbose output
python tests/health/run_health_monitoring_tests.py --verbose

# Run with coverage
python tests/health/run_health_monitoring_tests.py --coverage

# Stop on first failure
python tests/health/run_health_monitoring_tests.py --fail-fast
```

### Direct pytest Usage

```bash
# Run unit tests only
pytest tests/unit/health/ -v

# Run integration tests with timeout
pytest tests/integration/health/ -v --timeout=300

# Run performance tests (slow)
pytest tests/performance/health/ -v -m performance

# Run chaos tests (very slow)
pytest tests/chaos/health/ -v -m chaos

# Run specific test
pytest tests/unit/health/test_extension_service_monitor.py::TestExtensionServiceMonitor::test_initialization -v

# Run with coverage
pytest tests/health/ --cov=server.extension_health_monitor --cov-report=html
```

### Test Markers

Tests are marked with the following pytest markers:

- `@pytest.mark.unit` - Unit tests (fast)
- `@pytest.mark.integration` - Integration tests (medium)
- `@pytest.mark.performance` - Performance tests (slow)
- `@pytest.mark.chaos` - Chaos engineering tests (very slow)
- `@pytest.mark.slow` - All slow-running tests

```bash
# Run only fast tests
pytest tests/health/ -m "not slow"

# Run only unit and integration tests
pytest tests/health/ -m "unit or integration"

# Skip chaos tests
pytest tests/health/ -m "not chaos"
```

## Test Configuration

### Environment Variables

- `COVERAGE=true` - Enable coverage reporting
- `PYTEST_TIMEOUT=300` - Set default test timeout
- `LOG_LEVEL=DEBUG` - Set logging level for tests

### Performance Test Thresholds

The performance tests use the following thresholds:

- Single health check: < 1.0 seconds
- Concurrent health checks: < 2.0 seconds average
- Memory growth: < 100MB during extended monitoring
- Scalability: < 10ms per extension
- Recovery operations: < 100ms per service

### Chaos Test Scenarios

Chaos tests simulate various failure conditions:

- **Failure rates**: 10%, 30%, 50%, 70%, 90%
- **Network partitions**: Connection timeouts and errors
- **Resource exhaustion**: Memory and CPU constraints
- **Slow responses**: 100ms to 1000ms delays
- **Intermittent failures**: Time-based failure patterns
- **Cascading failures**: Failure propagation scenarios

## Test Data and Fixtures

### Shared Fixtures (conftest.py)

- `basic_extension_manager` - Mock extension manager for basic tests
- `failing_extension_manager` - Extension manager that simulates failures
- `multiple_extensions` - Set of mock extensions for load testing
- `performance_test_config` - Configuration for performance tests
- `chaos_test_config` - Configuration for chaos engineering tests

### Custom Assertions

- `assert_service_healthy(status, service_name)` - Assert service is healthy
- `assert_service_degraded(status, service_name)` - Assert service is degraded
- `assert_service_unhealthy(status, service_name)` - Assert service is unhealthy
- `assert_overall_health(status, expected)` - Assert overall system health

## Continuous Integration

### GitHub Actions Example

```yaml
name: Health Monitoring Tests

on: [push, pull_request]

jobs:
  health-tests:
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
          pip install pytest pytest-asyncio pytest-timeout pytest-cov psutil
      
      - name: Run unit tests
        run: python tests/health/run_health_monitoring_tests.py --suite unit --coverage
      
      - name: Run integration tests
        run: python tests/health/run_health_monitoring_tests.py --suite integration
      
      - name: Run performance tests
        run: python tests/health/run_health_monitoring_tests.py --suite performance
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
      
      - name: Upload coverage
        uses: codecov/codecov-action@v1
        if: success()
```

### Local Development Workflow

```bash
# Quick development cycle
pytest tests/unit/health/ -v --tb=short

# Before committing
python tests/health/run_health_monitoring_tests.py --suite unit --suite integration

# Full test suite (CI simulation)
python tests/health/run_health_monitoring_tests.py --coverage --fail-fast
```

## Troubleshooting

### Common Issues

1. **Tests timeout**: Increase timeout values or check for infinite loops
2. **Memory leaks**: Check for proper cleanup in fixtures and tests
3. **Flaky tests**: Add proper synchronization and retry logic
4. **Performance degradation**: Profile tests and optimize bottlenecks

### Debug Mode

```bash
# Run with debug output
python tests/health/run_health_monitoring_tests.py --verbose --no-capture

# Run single test with debugging
pytest tests/unit/health/test_extension_service_monitor.py::test_name -v -s --pdb
```

### Test Coverage

```bash
# Generate HTML coverage report
pytest tests/health/ --cov=server.extension_health_monitor --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Contributing

When adding new health monitoring tests:

1. **Follow naming conventions**: `test_<functionality>_<scenario>`
2. **Use appropriate markers**: Add `@pytest.mark.unit`, etc.
3. **Add docstrings**: Describe what the test validates
4. **Use fixtures**: Leverage shared fixtures from conftest.py
5. **Handle async properly**: Use `@pytest.mark.asyncio` for async tests
6. **Add timeouts**: Use `@pytest.mark.timeout()` for long-running tests
7. **Update documentation**: Add test descriptions to this README

### Test Template

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
@pytest.mark.unit
async def test_new_functionality(basic_extension_manager):
    """Test description of what this validates."""
    # Arrange
    monitor = ExtensionServiceMonitor(basic_extension_manager)
    
    # Act
    result = await monitor.some_method()
    
    # Assert
    assert result is not None
    assert expected_condition
```

## Requirements Coverage

This test suite covers the following requirements from the specification:

- **Requirement 5.1**: Extension service health monitoring and status reporting
- **Requirement 5.2**: Automatic service recovery and restart capabilities  
- **Requirement 5.3**: Health status dashboard and monitoring interfaces
- **Requirement 5.4**: Service availability detection and alerting
- **Requirement 5.5**: Performance monitoring and optimization recommendations

The comprehensive test coverage ensures that the health monitoring system meets all specified requirements and handles edge cases, failure scenarios, and performance constraints effectively.