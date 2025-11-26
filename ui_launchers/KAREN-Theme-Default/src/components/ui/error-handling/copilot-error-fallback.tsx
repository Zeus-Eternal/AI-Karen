import React from 'react';

/**
 * Fallback component for Copilot errors
 */
export function CopilotErrorFallback({
  error,
  onRetry
}: {
  error: Error;
  onRetry?: () => void;
}) {
  return (
    <div className="copilot-error-fallback">
      <div className="copilot-error-fallback__icon">⚠️</div>
      <h3 className="copilot-error-fallback__title">Copilot Error</h3>
      <p className="copilot-error-fallback__message">
        {error.message || 'An error occurred in the Copilot interface'}
      </p>
      {onRetry && (
        <button
          className="copilot-error-fallback__retry"
          onClick={onRetry}
        >
          Try Again
        </button>
      )}
    </div>
  );
}

// Set display name for component
(CopilotErrorFallback as React.ComponentType).displayName = 'CopilotErrorFallback';