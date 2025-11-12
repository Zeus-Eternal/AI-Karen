// apps/web/src/lib/graceful/model-provider-integration.tsx
"use client";

import React from "react";
import {
  DegradedModeBanner,
  ServiceUnavailable,
} from "@/lib/graceful-degradation/fallback-ui";
import {
  useModelProviders,
  useGracefulDegradation,
} from "@/lib/graceful-degradation/use-graceful-backend";
import { Button } from "@/components/ui/button";
import { withGracefulDegradation } from "./graceful-utils";

/**
 * Fixed Model Provider Integration
 * - Caching on
 * - Stale-on-error fallback
 * - Degraded banner when from cache / stale / flag disabled / error
 */
export function FixedModelProviderIntegration() {
  const {
    data: providers,
    isLoading,
    error,
    isStale,
    isFromCache,
    retry,
    refresh,
  } = useModelProviders({
    enableCaching: true,
    useStaleOnError: true,
    maxStaleAge: 60 * 60 * 1000, // 1 hour
  });

  const {
    isEnabled,
    showDegradedBanner,
    dismissBanner,
    forceRetry,
  } = useGracefulDegradation("modelProviderIntegration");

  const shouldShowBanner =
    !isEnabled || showDegradedBanner || Boolean(isStale || isFromCache || error);

  return (
    <div className="model-provider-integration space-y-4">
      {shouldShowBanner && (
        <DegradedModeBanner
          affectedServices={[
            "Model Provider Integration",
            ...(isFromCache ? ["Using Cached Data"] : []),
            ...(isStale ? ["Stale Cache Window"] : []),
            ...(error ? ["Recent Request Errors"] : []),
          ]}
          onDismiss={dismissBanner}
          showDetails
        />
      )}

      {isLoading && !providers && (
        <div className="flex items-center justify-center p-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500" />
          <span className="ml-2">Loading model providers…</span>
        </div>
      )}

      {error && !providers && (
        <ServiceUnavailable
          serviceName="Model Provider Integration"
          error={error}
          onRetry={retry}
          showRetry
        >
          <div className="mt-4 flex gap-2">
            <Button
              onClick={forceRetry}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Force Retry
            </Button>
            <Button
              onClick={retry}
              variant="secondary"
              className="px-4 py-2"
            >
              Try Again
            </Button>
          </div>
        </ServiceUnavailable>
      )}

      {providers && providers.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">
              Model Providers
              {isStale && (
                <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                  Stale (serving cached)
                </span>
              )}
              {isFromCache && (
                <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  From Cache
                </span>
              )}
            </h3>
            <Button onClick={refresh} variant="link" className="text-sm">
              Refresh
            </Button>
          </div>

          <div className="grid gap-4">
            {providers.map((provider: unknown) => (
              <div
                key={provider.id ?? provider.name}
                className="p-4 border rounded-lg hover:border-gray-300"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{provider.name}</h4>
                    {provider.description && (
                      <p className="text-sm text-gray-600">{provider.description}</p>
                    )}
                  </div>
                  <div
                    className={`px-2 py-1 rounded text-xs ${
                      provider.status === "active"
                        ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {provider.status ?? "unknown"}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {providers && providers.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No model providers available.
        </div>
      )}
    </div>
  );
}

/**
 * HOC to wrap any component with graceful degradation
 */
export const GracefulModelProviderIntegration = withGracefulDegradation(
  FixedModelProviderIntegration,
  "modelProviderIntegration"
);

export default GracefulModelProviderIntegration;
