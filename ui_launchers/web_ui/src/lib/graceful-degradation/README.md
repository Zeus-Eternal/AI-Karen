# Graceful Degradation System

This system provides comprehensive graceful degradation capabilities for the extension system, handling service failures, authentication errors, and network issues while maintaining core functionality.

## Overview

The graceful degradation system consists of several key components:

1. **Feature Flags** - Control which features are enabled/disabled
2. **Cache Management** - Store and serve cached data when services are unavailable
3. **Fallback UI Components** - Provide user-friendly error states
4. **Progressive Enhancement** - Gradually enhance functionality as services become available
5. **Enhanced Backend Service** - Wrap existing services with graceful degradation

## Quick Start

### 1. Initialize the System

```typescript
import { initGracefulDegradation } from './lib/graceful-degradation/init';

// Initialize early in your app
initGracefulDegradation({
  enableCaching: true,
  enableGlobalErrorHandling: true,
  developmentMode: process.env.NODE_ENV === 'development'
});
```

### 2. Use Graceful Backend Hooks

```typescript
import { useModelProviders } from './lib/graceful-degradation/use-graceful-backend';

function MyComponent() {
  const {
    data: providers,
    isLoading,
    error,
    isStale,
    retry
  } = useModelProviders();

  if (isLoading) return <div>Loading...</div>;
  if (error && !providers) return <div>Error: {error.message}</div>;
  
  return (
    <div>
      {isStale && <div className="warning">Using cached data</div>}
      {providers.map(provider => (
        <div key={provider.id}>{provider.name}</div>
      ))}
    </div>
  );
}
```

### 3. Wrap Components with Progressive Enhancement

```typescript
import { ProgressiveFeature } from './lib/graceful-degradation';

function MyFeature() {
  return (
    <ProgressiveFeature
      featureName="modelProviderIntegration"
      fallbackComponent={<div>Feature unavailable</div>}
    >
      <ModelProviderIntegration />
    </ProgressiveFeature>
  );
}
```

## Fixing the 4xx/5xx Errors

The system automatically handles the KarenBackendService 4xx/5xx errors you're experiencing:

### Before (Causing Errors)
```typescript
// This causes 4xx/5xx errors when backend is unavailable
const loadProviderModelSuggestions = async () => {
  const response = await karenBackendService.makeRequest('/api/models/providers/');
  return response; // Throws error on 403/503
};
```

### After (With Graceful Degradation)
```typescript
import { useModelProviders } from './lib/graceful-degradation/use-graceful-backend';

function ModelProviderIntegration() {
  const {
    data: providers,
    isLoading,
    error,
    isStale,
    retry
  } = useModelProviders();

  // Automatically handles 403/503 errors with cached data or fallbacks
  const loadProviderModelSuggestions = () => {
    return providers || []; // Never throws, always returns data
  };

  return (
    <div>
      {error && (
        <div className="error-banner">
          Service temporarily unavailable. Showing cached data.
          <button onClick={retry}>Retry</button>
        </div>
      )}
      {/* Your existing UI code */}
    </div>
  );
}
```

## Feature Flags

Control which features are available:

```typescript
import { featureFlagManager, useFeatureFlag } from './lib/graceful-degradation';

// Check if a feature is enabled
const isEnabled = featureFlagManager.isEnabled('modelProviderIntegration');

// Use in React components
function MyComponent() {
  const { isEnabled, fallbackBehavior } = useFeatureFlag('modelProviderIntegration');
  
  if (!isEnabled) {
    switch (fallbackBehavior) {
      case 'hide': return null;
      case 'cache': return <CachedVersion />;
      case 'disable': return <DisabledMessage />;
      default: return null;
    }
  }
  
  return <FullFeature />;
}
```

## Cache Management

Store and retrieve cached data:

```typescript
import { extensionCache } from './lib/graceful-degradation';

// Cache data
extensionCache.cacheModelProviders(providers);

// Retrieve cached data
const cachedProviders = extensionCache.getCachedModelProviders();

// Get stale data when fresh data is unavailable
const staleProviders = extensionCache.getStaleModelProviders();
```

## Fallback UI Components

Provide user-friendly error states:

```typescript
import { ServiceUnavailable, ExtensionUnavailable } from './lib/graceful-degradation';

function MyComponent() {
  if (serviceError) {
    return (
      <ServiceUnavailable
        serviceName="Model Provider Integration"
        error={serviceError}
        onRetry={handleRetry}
      />
    );
  }
  
  if (extensionError) {
    return (
      <ExtensionUnavailable
        serviceName="Extension System"
        extensionName="Model Provider"
        error={extensionError}
        fallbackData={cachedData}
        showFallbackData={true}
      />
    );
  }
  
  return <NormalComponent />;
}
```

## Enhanced Backend Service

Wrap your existing backend service:

```typescript
import { EnhancedBackendService } from './lib/graceful-degradation';

const enhancedService = new EnhancedBackendService(karenBackendService);

// Make requests with automatic error handling and caching
const data = await enhancedService.makeEnhancedRequest({
  endpoint: '/api/extensions/',
  cacheKey: 'extensions-list',
  enableCaching: true,
  useStaleOnError: true,
  fallbackData: []
});
```

## Development Mode

Enable development helpers:

```typescript
// In development, access debugging tools
window.gracefulDegradation.simulateFailure('extension-api');
window.gracefulDegradation.simulateRecovery('extension-api');
window.gracefulDegradation.getSystemHealth();
window.gracefulDegradation.clearCache();
```

## Configuration Options

```typescript
initGracefulDegradation({
  enableCaching: true,                    // Enable data caching
  cacheCleanupInterval: 5 * 60 * 1000,   // Cache cleanup interval
  enableGlobalErrorHandling: true,        // Auto-handle errors
  developmentMode: false,                 // Enable dev helpers
  logLevel: 'info',                       // Logging level
  featureFlags: {                         // Initial feature flag states
    modelProviderIntegration: {
      enabled: true,
      fallbackBehavior: 'cache'
    },
    extensionSystem: {
      enabled: true,
      fallbackBehavior: 'disable'
    }
  }
});
```

## Available Hooks

- `useModelProviders()` - Get model providers with graceful degradation
- `useExtensions()` - Get extensions with graceful degradation
- `useBackgroundTasks()` - Get background tasks with graceful degradation
- `useExtensionHealth(name)` - Get extension health with graceful degradation
- `useSystemHealth()` - Monitor overall system health
- `useGracefulDegradation(feature)` - Handle feature degradation in components
- `useGracefulBackend(endpoint, options)` - Make graceful backend requests

## Error Handling

The system automatically handles:

- **403 Forbidden** - Disables auth features, uses cached data
- **503 Service Unavailable** - Retries with exponential backoff, uses cached data
- **Network Errors** - Uses cached data, shows appropriate UI
- **Timeout Errors** - Retries and falls back to cached data

## Best Practices

1. **Always provide fallback data** for critical features
2. **Use appropriate cache TTL** based on data freshness requirements
3. **Show clear UI indicators** when using cached or stale data
4. **Provide retry mechanisms** for users to attempt recovery
5. **Monitor system health** to proactively address issues
6. **Test degradation scenarios** to ensure graceful behavior

## Testing

```typescript
import { describe, it, expect } from 'vitest';
import { FeatureFlagManager } from './lib/graceful-degradation';

describe('Graceful Degradation', () => {
  it('should handle service failures gracefully', () => {
    const manager = new FeatureFlagManager();
    manager.handleServiceError('extension-api', new Error('Service down'));
    expect(manager.isEnabled('extensionSystem')).toBe(false);
  });
});
```

## Migration Guide

To migrate existing components:

1. **Wrap API calls** with graceful backend hooks
2. **Add fallback UI** for error states
3. **Enable caching** for frequently accessed data
4. **Test degradation scenarios** to ensure proper behavior
5. **Monitor and adjust** feature flags based on service health

This system ensures your application remains functional even when backend services experience issues, providing a better user experience and reducing support burden.