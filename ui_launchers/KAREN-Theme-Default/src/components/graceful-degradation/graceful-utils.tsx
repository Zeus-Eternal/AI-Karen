"use client";

import React from "react";

import { DegradedModeBanner } from "@/lib/graceful-degradation/fallback-ui";
import { useModelProviders, useGracefulDegradation } from "@/lib/graceful-degradation/use-graceful-backend";

/**
 * HOC to wrap any component with graceful degradation
 */
export function withGracefulDegradation<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  featureName: string
) {
  return function GracefullyDegradedComponent(props: P) {
    const { isEnabled, fallbackBehavior, showDegradedBanner, dismissBanner } =
      useGracefulDegradation(featureName);

    if (!isEnabled) {
      switch (fallbackBehavior) {
        case "hide":
          return null;
        case "disable":
          return (
            <div className="p-4 bg-gray-100 rounded-lg">
              <p className="text-gray-600">This feature is currently unavailable.</p>
            </div>
          );
        case "cache":
        case "mock":
          return (
            <div className="relative">
              {showDegradedBanner && (
                <DegradedModeBanner affectedServices={[featureName]} onDismiss={dismissBanner} />
              )}
              <WrappedComponent {...props} />
            </div>
          );
        default:
          return null;
      }
    }

    return <WrappedComponent {...props} />;
  };
}

/**
 * Hook for safely loading provider model suggestions
 * (replaces a previous 4xx/5xx throw with sane fallbacks)
 */
export function useModelProviderSuggestions() {
  const { data: suggestions, isLoading, error, retry } = useModelProviders({
    enableCaching: true,
    useStaleOnError: true,
  });

  const loadProviderModelSuggestions = React.useCallback(async () => {
    try {
      return suggestions || [];
    } catch {
      return [];
    }
  }, [suggestions]);

  return {
    loadProviderModelSuggestions,
    suggestions: suggestions || [],
    isLoading,
    error,
    retry,
  };
}

/**
 * App-level initializer (lazy) — safe dynamic import
 */
export async function initializeGracefulDegradationInApp() {
  const { initGracefulDegradation } = await import("./init-graceful-degradation");
  initGracefulDegradation({
    enableCaching: true,
    enableGlobalErrorHandling: true,
    developmentMode: process.env.NODE_ENV === "development",
    logLevel: "warn",
    featureFlags: {
      modelProviderIntegration: { enabled: true, fallbackBehavior: "cache" },
      extensionSystem: { enabled: true, fallbackBehavior: "disable" },
      backgroundTasks: { enabled: true, fallbackBehavior: "hide" },
    },
  });
}
