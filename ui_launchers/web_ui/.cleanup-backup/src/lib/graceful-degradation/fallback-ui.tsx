/**
 * Fallback UI components for when extensions are unavailable
 */

import React from 'react';
import { AlertTriangle, Wifi, RefreshCw, Settings } from 'lucide-react';

export interface FallbackUIProps {
  serviceName: string;
  error?: Error | string;
  onRetry?: () => void;
  showRetry?: boolean;
  children?: React.ReactNode;
}

export interface ServiceUnavailableProps extends FallbackUIProps {
  lastSuccessfulConnection?: Date;
  estimatedRecoveryTime?: Date;
}

export interface ExtensionUnavailableProps extends FallbackUIProps {
  extensionName: string;
  fallbackData?: any;
  showFallbackData?: boolean;
}

// Generic service unavailable component
export function ServiceUnavailable({
  serviceName,
  error,
  onRetry,
  showRetry = true,
  lastSuccessfulConnection,
  estimatedRecoveryTime,
  children
}: ServiceUnavailableProps) {
  const errorMessage = typeof error === 'string' ? error : error?.message || 'Service temporarily unavailable';

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-gray-50 dark:bg-gray-800 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
      <div className="flex items-center mb-4">
        <Wifi className="w-8 h-8 text-gray-400 mr-3" />
        <div>
          <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300">
            {serviceName} Unavailable
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {errorMessage}
          </p>
        </div>
      </div>

      {lastSuccessfulConnection && (
        <p className="text-xs text-gray-400 mb-2">
          Last connected: {lastSuccessfulConnection.toLocaleString()}
        </p>
      )}

      {estimatedRecoveryTime && (
        <p className="text-xs text-gray-400 mb-4">
          Estimated recovery: {estimatedRecoveryTime.toLocaleString()}
        </p>
      )}

      {showRetry && onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry Connection
        </button>
      )}

      {children && (
        <div className="mt-4 w-full">
          {children}
        </div>
      )}
    </div>
  );
}

// Extension-specific unavailable component
export function ExtensionUnavailable({
  serviceName,
  extensionName,
  error,
  onRetry,
  showRetry = true,
  fallbackData,
  showFallbackData = false,
  children
}: ExtensionUnavailableProps) {
  const errorMessage = typeof error === 'string' ? error : error?.message || 'Extension temporarily unavailable';

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
      <div className="flex items-center mb-3">
        <AlertTriangle className="w-6 h-6 text-yellow-500 mr-2" />
        <div>
          <h4 className="text-md font-medium text-yellow-700 dark:text-yellow-300">
            {extensionName} Extension Unavailable
          </h4>
          <p className="text-sm text-yellow-600 dark:text-yellow-400">
            {errorMessage}
          </p>
        </div>
      </div>

      {showFallbackData && fallbackData && (
        <div className="w-full mb-3 p-3 bg-white dark:bg-gray-800 rounded border">
          <p className="text-xs text-gray-500 mb-2">Showing cached data:</p>
          <div className="text-sm">
            {typeof fallbackData === 'object' ? (
              <pre className="text-xs overflow-auto">
                {JSON.stringify(fallbackData, null, 2)}
              </pre>
            ) : (
              <span>{String(fallbackData)}</span>
            )}
          </div>
        </div>
      )}

      <div className="flex space-x-2">
        {showRetry && onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center px-3 py-1 bg-yellow-500 text-white rounded text-sm hover:bg-yellow-600 transition-colors"
          >
            <RefreshCw className="w-3 h-3 mr-1" />
            Retry
          </button>
        )}
        
        <button
          onClick={() => window.location.reload()}
          className="flex items-center px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600 transition-colors"
        >
          <Settings className="w-3 h-3 mr-1" />
          Reload Page
        </button>
      </div>

      {children && (
        <div className="mt-3 w-full">
          {children}
        </div>
      )}
    </div>
  );
}

// Loading state with timeout fallback
export function LoadingWithFallback({
  serviceName,
  timeout = 10000,
  onTimeout,
  children
}: {
  serviceName: string;
  timeout?: number;
  onTimeout?: () => void;
  children?: React.ReactNode;
}) {
  const [hasTimedOut, setHasTimedOut] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setHasTimedOut(true);
      onTimeout?.();
    }, timeout);

    return () => clearTimeout(timer);
  }, [timeout, onTimeout]);

  if (hasTimedOut) {
    return (
      <ServiceUnavailable
        serviceName={serviceName}
        error="Service is taking longer than expected to respond"
        onRetry={() => {
          setHasTimedOut(false);
          window.location.reload();
        }}
      >
        {children}
      </ServiceUnavailable>
    );
  }

  return (
    <div className="flex items-center justify-center p-6">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      <span className="ml-3 text-gray-600 dark:text-gray-400">
        Loading {serviceName}...
      </span>
    </div>
  );
}

// Degraded mode banner
export function DegradedModeBanner({
  affectedServices,
  onDismiss,
  showDetails = false
}: {
  affectedServices: string[];
  onDismiss?: () => void;
  showDetails?: boolean;
}) {
  const [isExpanded, setIsExpanded] = React.useState(showDetails);

  return (
    <div className="bg-yellow-100 dark:bg-yellow-900/30 border-l-4 border-yellow-500 p-4 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <AlertTriangle className="w-5 h-5 text-yellow-500 mr-2" />
          <div>
            <h4 className="text-sm font-medium text-yellow-700 dark:text-yellow-300">
              System Running in Degraded Mode
            </h4>
            <p className="text-sm text-yellow-600 dark:text-yellow-400">
              Some features may be limited or unavailable
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-yellow-600 hover:text-yellow-700 text-sm underline"
          >
            {isExpanded ? 'Hide Details' : 'Show Details'}
          </button>
          
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-yellow-600 hover:text-yellow-700"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="mt-3 pt-3 border-t border-yellow-200 dark:border-yellow-800">
          <p className="text-sm text-yellow-700 dark:text-yellow-300 mb-2">
            Affected services:
          </p>
          <ul className="list-disc list-inside text-sm text-yellow-600 dark:text-yellow-400">
            {affectedServices.map((service, index) => (
              <li key={index}>{service}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// Progressive enhancement wrapper
export function ProgressiveEnhancement({
  featureName,
  fallbackComponent,
  enhancedComponent,
  loadingComponent,
  errorComponent
}: {
  featureName: string;
  fallbackComponent: React.ReactNode;
  enhancedComponent: React.ReactNode;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
}) {
  const [isEnhanced, setIsEnhanced] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    // Simulate feature detection/loading
    const checkFeature = async () => {
      try {
        setIsLoading(true);
        // Add actual feature detection logic here
        await new Promise(resolve => setTimeout(resolve, 1000));
        setIsEnhanced(true);
        setError(null);
      } catch (err) {
        setError(err as Error);
        setIsEnhanced(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkFeature();
  }, [featureName]);

  if (isLoading) {
    return loadingComponent || (
      <div className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded h-20"></div>
    );
  }

  if (error) {
    return errorComponent || (
      <ServiceUnavailable
        serviceName={featureName}
        error={error}
        onRetry={() => window.location.reload()}
      />
    );
  }

  return isEnhanced ? enhancedComponent : fallbackComponent;
}