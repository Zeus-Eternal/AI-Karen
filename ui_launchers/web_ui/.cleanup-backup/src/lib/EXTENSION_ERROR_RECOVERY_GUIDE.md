# Extension Error Recovery Integration Guide

This guide explains how the extension error recovery system works and how to integrate it with your application.

## Problem

The frontend is getting a 403 Forbidden error when trying to access `/api/extensions`, which causes the extension integration to fail and show errors in the console.

## Solution

The error recovery system provides multiple layers of fallback handling:

### 1. Immediate Fix (extension-403-fix.ts)

This patches the global `fetch` function to intercept 403 errors for extension endpoints and provide fallback data:

```typescript
// Automatically applied when imported
import './lib/extension-403-fix';
```

### 2. Comprehensive Error Recovery (error-recovery-integration-example.ts)

This provides a more sophisticated error recovery system that integrates with the backend error recovery service:

```typescript
import { enhancedErrorHandler } from './lib/error-recovery-integration-example';

// Handle errors with automatic recovery
const result = await enhancedErrorHandler.handleHttpError(403, '/api/extensions', 'extension_list');
```

### 3. Extension-Specific Error Handling (extension-error-integration.ts)

This provides specialized handling for extension authentication errors:

```typescript
import { handleExtensionError } from './lib/extension-error-integration';

const result = handleExtensionError(403, '/api/extensions', 'extension_list');
// Returns appropriate fallback data or retry instructions
```

## How It Works

1. **Error Detection**: When a 403 error occurs on an extension endpoint, the system detects it
2. **Fallback Data**: Provides appropriate fallback data that matches the expected API format
3. **User Notification**: Informs the user that extensions are running in read-only mode
4. **Graceful Degradation**: The UI continues to work with limited functionality

## Fallback Data Format

For the main `/api/extensions` endpoint, the system returns:

```json
{
  "extensions": {
    "readonly-mode": {
      "id": "readonly-mode",
      "name": "readonly-mode",
      "display_name": "Extensions (Read-Only Mode)",
      "description": "Extension features are available in read-only mode...",
      "status": "readonly",
      "capabilities": {
        "provides_ui": true,
        "provides_api": false,
        "provides_background_tasks": false,
        "provides_webhooks": false
      }
    }
  },
  "total": 1,
  "message": "Extension features are available in read-only mode",
  "access_level": "readonly",
  "available_features": ["view", "status"],
  "restricted_features": ["install", "configure", "manage", "execute"],
  "fallback_mode": true
}
```

## Integration Steps

### Step 1: Import the Error Recovery System

Add this to your main application file or where you initialize services:

```typescript
// Import the comprehensive error recovery system
import './lib/error-recovery-integration-example';

// Or just the immediate 403 fix
import './lib/extension-403-fix';
```

### Step 2: Update KarenBackend Service (if needed)

The KarenBackend service already has extension error handling built-in. If you need to enhance it:

```typescript
// In your KarenBackend makeRequest method
if (!response.ok && response.status === 403 && url.includes('/api/extensions')) {
  // Use the global error handler if available
  if (typeof window !== 'undefined' && (window as any).extensionErrorIntegration) {
    const result = (window as any).extensionErrorIntegration.handleExtensionError(
      response.status, 
      url, 
      operation
    );
    
    if (result && result.fallback_data) {
      return result.fallback_data;
    }
  }
}
```

### Step 3: Handle UI Updates

Update your extension UI components to handle read-only mode:

```typescript
// Check if extensions are in fallback mode
if (extensionData.fallback_mode || extensionData.access_level === 'readonly') {
  // Show read-only UI
  // Disable certain actions
  // Display appropriate messages
}
```

## Testing

You can test the error recovery system:

```typescript
import { testExtensionErrorRecovery } from './lib/test-extension-error-recovery';

// Run in development mode
const testResults = testExtensionErrorRecovery();
console.log('Error recovery test results:', testResults);
```

## Configuration

The system can be configured through the extension auth degradation manager:

```typescript
import { extensionAuthDegradationManager } from './lib/auth/extension-auth-degradation';

// Register custom feature configurations
extensionAuthDegradationManager.registerFeature({
  name: 'custom_feature',
  displayName: 'Custom Feature',
  priority: 5,
  requiresAuth: true,
  requiresWrite: false,
  fallbackAvailable: true,
  cacheSupported: true
});
```

## Monitoring

The system provides monitoring capabilities:

```typescript
// Get current degradation state
const state = extensionAuthDegradationManager.getDegradationState();

// Get cache statistics
const cacheStats = extensionAuthDegradationManager.getCacheStats();

// Get error statistics
const errorStats = getExtensionAuthErrorHandler().getErrorStatistics();
```

## Troubleshooting

### Issue: Still getting 403 errors

1. Make sure the error recovery system is imported early in your application
2. Check that the fetch patch is applied: `console.log(window.fetch.toString())`
3. Verify the extension endpoints are being detected correctly

### Issue: Fallback data not matching expected format

1. Update the fallback data in `extension-auth-degradation.ts`
2. Ensure the data structure matches what your UI components expect
3. Test with the test utility to verify the data format

### Issue: UI not updating for read-only mode

1. Check that your components handle the `fallback_mode` and `access_level` properties
2. Update your UI to show appropriate messages for read-only mode
3. Disable actions that require write permissions

## Next Steps

1. **Import the error recovery system** in your main application file
2. **Test the integration** to ensure it works with your specific setup
3. **Update UI components** to handle read-only mode gracefully
4. **Monitor the system** to ensure it's working as expected
5. **Customize fallback data** if needed to match your UI requirements

The system is designed to be backward-compatible and should not break existing functionality while providing graceful degradation for extension features.