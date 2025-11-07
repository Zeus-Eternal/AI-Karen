# CORTEX Routing Tests

Comprehensive test suite for the CORTEX routing system, covering intent classification, task type detection, RBAC enforcement, and routing policies.

## Test Coverage

### Intent Classification Tests (`TestIntentClassification`)
- Greeting detection
- Code generation intent
- Routing control commands
- Empty query handling
- Confidence score validation
- Accuracy by complexity level

### Task Classification Tests (`TestTaskClassification`)
- Code task detection
- Chat task detection
- Reasoning task detection
- Capability mapping

### Cache Key Generation Tests (`TestCacheKeyGeneration`)
- Query fingerprint inclusion
- User ID inclusion
- Uniqueness across scenarios

### RBAC Enforcement Tests (`TestRBACEnforcement`)
- Routing permission existence
- Role-based restrictions

### Fallback Chain Tests (`TestFallbackChains`)
- Provider health fallback
- Degraded mode fallback

### Routing Policy Tests (`TestRoutingPolicies`)
- Privacy-first policy
- Performance-first policy
- Cost-optimized policy
- Balanced policy
- Policy validation

### Security Protection Tests (`TestSecurityProtection`)
- Malicious input handling
- Prompt injection detection

### Edge Case Tests (`TestEdgeCases`)
- Empty strings
- Very long inputs
- Emoji handling
- Non-English queries

### Accuracy Target Tests (`TestAccuracyTargets`)
- Intent accuracy ≥92% target
- Task accuracy validation

## Running Tests

### Run all routing tests:
```bash
pytest tests/routing/ -v
```

### Run specific test classes:
```bash
# Intent classification only
pytest tests/routing/test_cortex_routing.py::TestIntentClassification -v

# RBAC tests only
pytest tests/routing/test_cortex_routing.py::TestRBACEnforcement -v

# Accuracy validation
pytest tests/routing/test_cortex_routing.py::TestAccuracyTargets -v
```

### Run tests with markers:
```bash
# Routing tests only
pytest -m routing -v

# RBAC tests only
pytest -m rbac -v

# Integration tests (require external services)
pytest -m integration -v
```

### Run tests with coverage:
```bash
pytest tests/routing/ --cov=src/ai_karen_engine/routing --cov-report=html
```

### Run tests in parallel (if pytest-xdist installed):
```bash
pytest tests/routing/ -n auto
```

## Test Data

Tests use the gold test set located at:
```
data/cortex_routing_gold_test_set.json
```

This dataset contains 47 comprehensive test cases covering:
- All task types (code, chat, analysis, reasoning, etc.)
- Routing control commands
- Security tests (injection, jailbreak, SQL injection)
- Edge cases (empty, long, emoji, non-English)
- Multiple complexity levels (low, medium, high, edge_case)

## Dependencies

### Required:
- pytest ≥6.0
- pytest-asyncio (for async tests)

### Optional (for enhanced testing):
- pytest-cov (coverage reporting)
- pytest-xdist (parallel execution)
- pytest-timeout (test timeouts)
- pytest-benchmark (performance benchmarking)

### Install test dependencies:
```bash
pip install pytest pytest-asyncio pytest-cov pytest-xdist pytest-timeout
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines with automatic:
- Accuracy validation
- RBAC enforcement checks
- Security protection verification
- Cache key uniqueness validation

### GitHub Actions example:
```yaml
- name: Run CORTEX routing tests
  run: |
    pytest tests/routing/ -v --junitxml=test-results/routing-tests.xml
```

### Expected Test Execution Time:
- Unit tests: ~5 seconds
- Integration tests: ~30 seconds
- Full suite: ~45 seconds

## Test Results

Test results are reported in multiple formats:
- Console output (verbose)
- JUnit XML (for CI integration)
- HTML coverage report (if pytest-cov enabled)

### Interpreting Results:

**✅ PASS**: All assertions passed
**⚠️  WARN**: Test passed but generated warning (e.g., accuracy below target)
**❌ FAIL**: Test assertions failed
**⏭️  SKIP**: Test skipped (missing dependencies or data)

## Troubleshooting

### "Gold test set not found"
Ensure `data/cortex_routing_gold_test_set.json` exists in project root.

### "Module not found" errors
Install ai_karen_engine dependencies or run from project root:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
pytest tests/routing/
```

### "RBAC middleware not available"
Some tests require full system dependencies. Run with `-v` to see which tests are skipped.

### Slow test execution
Use parallel execution:
```bash
pytest tests/routing/ -n auto
```

## Contributing

When adding new routing features:
1. Add corresponding test cases to `test_cortex_routing.py`
2. Update gold test set if new intent/task types added
3. Ensure tests pass locally before committing
4. Verify CI pipeline passes

### Test Naming Convention:
- `test_<feature>` - Basic functionality test
- `test_<feature>_edge_case` - Edge case handling
- `test_<feature>_error` - Error condition handling
- `test_<feature>_performance` - Performance characteristic

## Performance Benchmarks

Target latencies (p95):
- Intent classification: ≤35ms
- Task type classification: ≤50ms
- Cache key generation: ≤1ms
- Policy evaluation: ≤10ms

Run performance tests:
```bash
pytest tests/routing/test_cortex_routing.py -m performance --benchmark-only
```

## Related Documentation

- [CORTEX Production Readiness](../../CORTEX_PRODUCTION_READINESS.md)
- [Routing Accuracy Report](../../ROUTING_ACCURACY_REPORT.md)
- [CORTEX Validation Summary](../../CORTEX_VALIDATION_SUMMARY.md)
- [Gold Test Set](../../data/cortex_routing_gold_test_set.json)

## Support

For issues or questions about tests:
1. Check test output for specific failure messages
2. Review related documentation
3. Consult CORTEX architecture documentation
4. Open issue with test output and environment details
