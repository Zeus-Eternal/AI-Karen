import React from 'react';
import { CopilotErrorFallback } from './copilot-error-fallback';

/**
 * Hook to create an error fallback component
 */
export function useCopilotErrorFallback() {
  const ErrorFallbackComponent = ({ error, onRetry }: { error: Error; onRetry?: () => void }) => (
    <CopilotErrorFallback error={error} onRetry={onRetry} />
  );
  ErrorFallbackComponent.displayName = 'ErrorFallbackComponent';
  
  return ErrorFallbackComponent;
}

// Set display name for hook
(useCopilotErrorFallback as unknown as React.NamedExoticComponent).displayName = 'useCopilotErrorFallback';

// Set display name for hook
(useCopilotErrorFallback as unknown as React.NamedExoticComponent).displayName = 'useCopilotErrorFallback';