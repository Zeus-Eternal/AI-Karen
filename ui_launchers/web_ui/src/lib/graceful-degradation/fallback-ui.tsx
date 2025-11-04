"use client";

import React from "react";
import { AlertTriangle, Wifi, RefreshCw, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";

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
  fallbackData?: unknown;
  showFallbackData?: boolean;
}

/** Utility: SSR-safe reload */
function safeReload() {
  if (typeof window !== "undefined") window.location.reload();
}

/** Utility: normalize error text */
function toErrorText(err?: Error | string, fallback = "Temporarily unavailable"): string {
  if (!err) return fallback;
  return typeof err === "string" ? err : err.message || fallback;
}

/** Generic service unavailable component */
export function ServiceUnavailable({
  serviceName,
  error,
  onRetry,
  showRetry = true,
  lastSuccessfulConnection,
  estimatedRecoveryTime,
  children,
}: ServiceUnavailableProps) {
  const errorMessage = toErrorText(error, "Service temporarily unavailable");

  return (
    <section
      role="status"
      aria-live="polite"
      className="flex flex-col items-center justify-center p-6 bg-gray-50 dark:bg-gray-800 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600"
      data-testid="service-unavailable"
    >
      <div className="flex items-start mb-4 w-full max-w-xl">
        <Wifi className="w-8 h-8 text-gray-400 mr-3 mt-0.5" aria-hidden />
        <div>
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
            {serviceName} Unavailable
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">{errorMessage}</p>
        </div>
      </div>

      <div className="w-full max-w-xl space-y-1">
        {lastSuccessfulConnection && (
          <p className="text-xs text-gray-500">
            Last connected: {lastSuccessfulConnection.toLocaleString()}
          </p>
        )}
        {estimatedRecoveryTime && (
          <p className="text-xs text-gray-500">
            Estimated recovery: {estimatedRecoveryTime.toLocaleString()}
          </p>
        )}
      </div>

      {showRetry && onRetry && (
        <div className="mt-4">
          <Button
            onClick={onRetry}
            className="flex items-center"
            aria-label={`Retry ${serviceName}`}
            data-testid="retry-button"
          >
            <RefreshCw className="w-4 h-4 mr-2" aria-hidden />
            Retry
          </Button>
        </div>
      )}

      {children && <div className="mt-4 w-full max-w-xl">{children}</div>}
    </section>
  );
}

/** Extension-specific unavailable component */
export function ExtensionUnavailable({
  serviceName,
  extensionName,
  error,
  onRetry,
  showRetry = true,
  fallbackData,
  showFallbackData = false,
  children,
}: ExtensionUnavailableProps) {
  const errorMessage = toErrorText(error, "Extension temporarily unavailable");

  return (
    <section
      role="status"
      aria-live="polite"
      className="flex flex-col items-center justify-center p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800"
      data-testid="extension-unavailable"
    >
      <div className="flex items-start mb-3 w-full max-w-xl">
        <AlertTriangle className="w-6 h-6 text-yellow-600 mr-2 mt-0.5" aria-hidden />
        <div>
          <h4 className="text-md font-semibold text-yellow-800 dark:text-yellow-200">
            {extensionName} Extension Unavailable
          </h4>
          <p className="text-sm text-yellow-700 dark:text-yellow-300">{errorMessage}</p>
          <p className="text-xs text-yellow-700/80 dark:text-yellow-300/80 mt-1">
            Affected service: <span className="font-medium">{serviceName}</span>
          </p>
        </div>
      </div>

      {showFallbackData && typeof fallbackData !== "undefined" && (
        <div className="w-full max-w-xl mb-3 p-3 bg-white dark:bg-gray-800 rounded border border-yellow-200 dark:border-yellow-800">
          <p className="text-xs text-gray-500 mb-2">Showing cached data:</p>
          <div className="text-sm">
            {typeof fallbackData === "object" ? (
              <pre className="text-xs overflow-auto max-h-64">
                {JSON.stringify(fallbackData, null, 2)}
              </pre>
            ) : (
              <span>{String(fallbackData)}</span>
            )}
          </div>
        </div>
      )}

      <div className="flex items-center space-x-2">
        {showRetry && onRetry && (
          <Button
            onClick={onRetry}
            variant="default"
            className="flex items-center bg-yellow-600 hover:bg-yellow-700"
            aria-label={`Retry ${extensionName}`}
          >
            <RefreshCw className="w-3 h-3 mr-1" aria-hidden />
            Retry
          </Button>
        )}
        <Button
          onClick={safeReload}
          variant="secondary"
          className="flex items-center"
          aria-label="Reload page"
        >
          <Settings className="w-3 h-3 mr-1" aria-hidden />
          Reload
        </Button>
      </div>

      {children && <div className="mt-3 w-full max-w-xl">{children}</div>}
    </section>
  );
}

/** Loading state with timeout fallback */
export function LoadingWithFallback({
  serviceName,
  timeout = 10000,
  onTimeout,
  children,
}: {
  serviceName: string;
  timeout?: number;
  onTimeout?: () => void;
  children?: React.ReactNode;
}) {
  const [hasTimedOut, setHasTimedOut] = React.useState(false);

  React.useEffect(() => {
    const t = setTimeout(() => {
      setHasTimedOut(true);
      onTimeout?.();
    }, timeout);
    return () => clearTimeout(t);
  }, [timeout, onTimeout]);

  if (hasTimedOut) {
    return (
      <ServiceUnavailable
        serviceName={serviceName}
        error="Service is taking longer than expected to respond"
        onRetry={() => {
          setHasTimedOut(false);
          safeReload();
        }}
      >
        {children}
      </ServiceUnavailable>
    );
  }

  return (
    <div
      className="flex items-center justify-center p-6"
      role="status"
      aria-live="polite"
      data-testid="loading-fallback"
    >
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" aria-hidden />
      <span className="ml-3 text-gray-600 dark:text-gray-400">
        Loading {serviceName}…
      </span>
    </div>
  );
}

/** Degraded mode banner */
export function DegradedModeBanner({
  affectedServices,
  onDismiss,
  showDetails = false,
  title = "Degraded Mode Active",
  subtitle = "Some services are experiencing issues. We’re serving cached data where possible.",
}: {
  affectedServices: string[];
  onDismiss?: () => void;
  showDetails?: boolean;
  title?: string;
  subtitle?: string;
}) {
  const [isExpanded, setIsExpanded] = React.useState(showDetails);

  return (
    <aside
      className="bg-yellow-100 dark:bg-yellow-900/30 border-l-4 border-yellow-500 p-4 mb-4 rounded"
      role="alert"
      data-testid="degraded-banner"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start">
          <AlertTriangle className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" aria-hidden />
          <div>
            <h4 className="text-sm font-semibold text-yellow-800 dark:text-yellow-200">
              {title}
            </h4>
            <p className="text-sm text-yellow-700 dark:text-yellow-300">{subtitle}</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="link"
            onClick={() => setIsExpanded((v) => !v)}
            className="text-yellow-700 hover:text-yellow-800 text-sm underline"
            aria-expanded={isExpanded}
            aria-controls="degraded-details"
          >
            {isExpanded ? "Hide Details" : "Show Details"}
          </Button>

          {onDismiss && (
            <Button
              variant="ghost"
              onClick={onDismiss}
              aria-label="Dismiss degraded mode banner"
            >
              ×
            </Button>
          )}
        </div>
      </div>

      {isExpanded && (
        <div
          id="degraded-details"
          className="mt-3 pt-3 border-t border-yellow-300 dark:border-yellow-800"
        >
          <p className="text-sm text-yellow-800 dark:text-yellow-200 mb-2">
            Affected services:
          </p>
          <ul className="list-disc list-inside text-sm text-yellow-700 dark:text-yellow-300">
            {affectedServices.map((service) => (
              <li key={service}>{service}</li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  );
}

/** Progressive enhancement wrapper */
export function ProgressiveEnhancement({
  featureName,
  fallbackComponent,
  enhancedComponent,
  loadingComponent,
  errorComponent,
  detect = async () => {
    // TODO: plug real detection; default to “available” after 600ms
    await new Promise((r) => setTimeout(r, 600));
    return true;
  },
}: {
  featureName: string;
  fallbackComponent: React.ReactNode;
  enhancedComponent: React.ReactNode;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  detect?: () => Promise<boolean>;
}) {
  const [isEnhanced, setIsEnhanced] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setIsLoading(true);
        const ok = await detect();
        if (!mounted) return;
        setIsEnhanced(ok);
        setError(null);
      } catch (err) {
        if (!mounted) return;
        setError(err as Error);
        setIsEnhanced(false);
      } finally {
        if (mounted) setIsLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [featureName, detect]);

  if (isLoading) {
    return (
      loadingComponent || (
        <div
          className="animate-pulse bg-gray-200 dark:bg-gray-700 rounded h-20"
          aria-busy="true"
        />
      )
    );
  }

  if (error) {
    return (
      errorComponent || (
        <ServiceUnavailable
          serviceName={featureName}
          error={error}
          onRetry={safeReload}
        />
      )
    );
  }

  return <>{isEnhanced ? enhancedComponent : fallbackComponent}</>;
}
