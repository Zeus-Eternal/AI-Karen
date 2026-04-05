# Plugin Host Test Suite

This directory contains the comprehensive test suite for the Frontend Plugin Host subsystem in Karen-AI-Theme.

## Test Structure

```
tests/plugin-host/
├── manifest-validator.test.ts          # UI manifest validation tests
├── plugin-loader.test.ts               # Plugin loader component tests
├── route-injector.test.ts              # Route injector logic tests
├── permission-guard.test.ts             # Permission guard component tests
├── plugin-error-boundary.test.ts       # Error boundary component tests
├── plugin-registry.test.ts              # Plugin registry hook tests
├── weather-plugin-integration.test.ts  # End-to-end weather plugin tests
└── README.md                           # This file
```

## Test Coverage

The test suite covers all requirements specified in the Frontend Plugin Host documentation:

### ✅ **Completed Test Coverage**

1. **Manifest Validator Tests** (`manifest-validator.test.ts`)
   - ✅ Valid manifest passes validation (Property 1)
   - ✅ Invalid manifest fails validation (Property 2)
   - ✅ Legacy manifest compatibility
   - ✅ Error message accuracy
   - ✅ Type checking for all fields

2. **Plugin Loader Tests** (`plugin-loader.test.ts`)
   - ✅ Plugin registration completeness (Property 5)
   - ✅ Alias resolution consistency (Property 6)
   - ✅ Weather plugin registration
   - ✅ Import error handling
   - ✅ Normalization functions

3. **Route Injector Tests** (`route-injector.test.ts`)
   - ✅ Sidebar entries derived from sidebar.plugins zone (Property 7)
   - ✅ ViewMap completeness (Property 8)
   - ✅ Default sidebar entry for UI plugins (Property 9)
   - ✅ Sidebar entries sorted by order (Property 10)
   - ✅ Multi-plugin scenarios

4. **Permission Guard Tests** (`permission-guard.test.ts`)
   - ✅ Permission guard role intersection (Property 13)
   - ✅ Role-based visibility
   - ✅ Edge case handling
   - ✅ Real-world scenarios

5. **Plugin Error Boundary Tests** (`plugin-error-boundary.test.ts`)
   - ✅ Error boundary catches any error (Property 14)
   - ✅ Error boundary renders fallback on error
   - ✅ Error boundary resets on reload (Property 15)
   - ✅ Error boundary logs errors (Property 16)
   - ✅ Styling and UI components

6. **Plugin Registry Tests** (`plugin-registry.test.ts`)
   - ✅ GetPluginsWithUI filter correctness (Property 3)
   - ✅ GetPlugin round-trip lookup (Property 4)
   - ✅ Plugin health monitoring
   - ✅ State management
   - ✅ Error handling

7. **Weather Plugin Integration Tests** (`weather-plugin-integration.test.ts`)
   - ✅ Complete workflow testing
   - ✅ Multi-plugin environment
   - ✅ Error scenarios
   - ✅ Performance and edge cases
   - ✅ State transitions

## Testing Framework

- **Test Runner**: Vitest (configured in project)
- **React Testing**: React Testing Library for component tests
- **Mocking**: Vi.js for mocking dependencies
- **Coverage**: Comprehensive coverage of all plugin host components

## Running Tests

```bash
# Run all plugin host tests
npm test -- plugin-host

# Run specific test file
npm test -- tests/plugin-host/manifest-validator.test.ts

# Run tests with coverage
npm run test:coverage
```

## Test Organization

### Unit Tests
Each component has dedicated unit tests covering:
- Happy path scenarios
- Error conditions
- Edge cases
- Props validation
- State management

### Integration Tests
The weather plugin integration tests cover:
- End-to-end workflows
- Multi-plugin interactions
- Error propagation
- State synchronization

### Property-Based Tests
While not implemented in this suite (would require fast-check), the test structure supports property-based testing for all correctness properties defined in the design document.

## Mocking Strategy

### API Mocks
- `fetch` is mocked for all backend API calls
- Plugin catalog responses are controlled in tests
- Error scenarios are simulated with rejected promises

### Component Mocks
- React components are mocked for isolation
- Hook implementations are stubbed
- Error boundaries are tested with throwing components

### Context Mocks
- Authentication context is mocked for permission testing
- Plugin registry context is controlled for state testing

## Test Data

### Test Catalog
Tests use a consistent plugin catalog structure:
```typescript
{
  name: 'plugin-name',
  display_name: 'Plugin Display Name',
  version: '1.0.0',
  status: 'active',
  capabilities: { provides_ui: true },
  menu_contributions: [...]
}
```

### Test Manifests
UI manifest tests use both valid and invalid examples:
```typescript
{
  plugin_id: 'plugin-name',
  component: 'PluginComponent',
  slots: ['sidebar.plugins'],
  permissions: ['user', 'admin']
}
```

## Best Practices

### Test Isolation
- Each test file is independent
- Mocks are reset between tests
- No shared state between tests

### Realistic Scenarios
- Tests use real plugin data structures
- Error scenarios simulate real failures
- Performance tests handle large datasets

### Readability
- Tests are descriptive and clear
- Error messages are specific
- Test names follow conventions

## Continuous Integration

These tests are integrated into the CI/CD pipeline and run on:
- Pull requests
- Merge to main branch
- Scheduled builds

## Future Enhancements

### Property-Based Testing
Add fast-check for comprehensive property testing:
```typescript
import fc from 'fast-check';

fc.assert(
  fc.property(
    fc.record({ plugin_id: fc.string(), component: fc.string(), slots: fc.array(fc.string()), permissions: fc.array(fc.string()) }),
    (manifest) => {
      const result = validateUIManifest(manifest, 'test');
      expect(result.valid).toBe(true);
    }
  )
);
```

### Visual Testing
Add visual regression testing for UI components:
- Component snapshots
- Error boundary fallback UI
- Permission guard rendering

### E2E Testing
Add end-to-end tests with:
- Real browser interactions
- Plugin loading scenarios
- Error recovery workflows

## Debugging Tests

### Common Issues
1. **Mock setup**: Ensure all mocks are properly configured
2. **Async operations**: Use `act()` for React state updates
3. **Component rendering**: Use appropriate render methods for components vs hooks

### Debug Commands
```bash
# Run tests with verbose output
npm test -- --verbose

# Run tests with coverage
npm run test:coverage -- --reporter=verbose

# Debug specific test
npm test -- --run tests/plugin-host/manifest-validator.test.ts
```

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Add both happy path and error scenarios
3. Include descriptive test names
4. Mock all external dependencies
5. Ensure test isolation

For more information on the Frontend Plugin Host architecture, see the main documentation in `.kiro/specs/frontend-plugin-host/`.