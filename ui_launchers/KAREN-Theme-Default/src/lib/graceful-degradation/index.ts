"use client";

/**
 * Graceful degradation system for extension features
 *
 * - Solid re-exports (types + values) from submodules
 * - SSR-safe initialization with disposer
 * - Unhandled rejection mapper -> feature flag auto-disable
 * - Cache maintenance with interval
 * - Progressive enhancement helpers (HOC + hook)
 * - System health snapshot + testing utilities
 */

import * as React from "react";
import { featureFlagManager as _ffm } from "./feature-flags";
import { extensionCache as sharedExtensionCache } from "./cache-manager";
// @ts-expect-error -- JSX module is handled by the UI bundler configuration
import { ProgressiveEnhancement as ProgressiveEnhancementComponent } from "./fallback-ui";

/* ----------------------------------------
 * Re-exports: Feature Flags
 * -------------------------------------- */
export type { FeatureFlag } from "./feature-flags";
export {
  featureFlagManager,
  useFeatureFlag,
  withFeatureFlag,
} from "./feature-flags";

/* ----------------------------------------
 * Re-exports: Fallback UI components
 * -------------------------------------- */
// @ts-expect-error -- JSX module is handled by the UI bundler configuration
export {
  ServiceUnavailable,
  ExtensionUnavailable,
  LoadingWithFallback,
  DegradedModeBanner,
  // also export the base component; HOC provided below
  ProgressiveEnhancement,
} from "./fallback-ui";

/* ----------------------------------------
 * Re-exports: Cache Management
 * -------------------------------------- */
export type { CacheEntry, CacheOptions } from "./cache-manager";
export {
  extensionCache,
  generalCache,
  CacheManager,
  ExtensionDataCache,
  CacheAwareDataFetcher,
} from "./cache-manager";

/* ----------------------------------------
 * Progressive enhancement helpers in this module
 * -------------------------------------- */

/**
 * Tiny HOC over the ProgressiveEnhancement component for convenience.
 */
export function withProgressiveEnhancement(opts: {
  featureName: string;
  fallbackComponent: React.ReactNode;
  enhancedComponent: React.ReactNode;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
}) {
  const {
    featureName,
    fallbackComponent,
    enhancedComponent,
    loadingComponent,
    errorComponent,
  } = opts;

  // SSR-safe handling: fallback when SSR, dynamic when client-side
  if (typeof window === "undefined") {
    return React.createElement(React.Fragment, null, fallbackComponent);
  }

  return React.createElement(ProgressiveEnhancementComponent, {
    featureName,
    fallbackComponent,
    enhancedComponent,
    loadingComponent,
    errorComponent
  });
}

/**
 * Progressive data hook: fetches data with cache + optional stale fallback,
 * gated behind an optional feature flag. Designed for graceful degradation.
 */
export function useProgressiveData<T>({
  key,
  fetcher,
  ttl = 5 * 60 * 1000,
  useStaleOnError = true,
  maxStaleAge = 60 * 60 * 1000,
  flagName, // optional: if provided, honors feature flag enablement
}: {
  key: string;
  fetcher: () => Promise<T>;
  ttl?: number;
  useStaleOnError?: boolean;
  maxStaleAge?: number;
  flagName?: string;
}) {
  const [data, setData] = React.useState<T | null>(null);
  const [error, setError] = React.useState<Error | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [fromCache, setFromCache] = React.useState<boolean>(false);

  const canRun = React.useMemo(() => {
    if (!flagName) return true;
    return _ffm.isEnabled(flagName);
  }, [flagName]);

  React.useEffect(() => {
    let alive = true;

    async function run() {
      setLoading(true);
      setError(null);
      setFromCache(false);

      if (!canRun) {
        // Respect disabled feature flag -> try stale cache if available
        const stale = sharedExtensionCache.getStale<T>(key, maxStaleAge);
        if (alive) {
          if (stale) {
            setData(stale);
            setFromCache(true);
          } else {
            setData(null);
          }
          setLoading(false);
        }
        return;
      }

      // Try fresh cache first
      let fresh: T | null = null;
      try {
        fresh = sharedExtensionCache.get<T>(key);
      } catch (err) {
        console.error("Error fetching from cache:", err);
        setError(new Error("Cache fetch failed"));
      }
      if (fresh && alive) {
        setData(fresh);
        setFromCache(true);
        setLoading(false);
        return;
      }

      try {
        const result = await fetcher();
        if (!alive) return;
        sharedExtensionCache.set<T>(key, result, { ttl });
        setData(result);
        setFromCache(false);
      } catch (e: unknown) {
        if (!alive) return;
        setError(e instanceof Error ? e : new Error(String(e)));

        if (useStaleOnError) {
          const stale = sharedExtensionCache.getStale<T>(key, maxStaleAge);
          if (stale) {
            setData(stale);
            setFromCache(true);
          } else {
            setData(null);
          }
        } else {
          setData(null);
        }
      } finally {
        if (alive) setLoading(false);
      }
    }

    run();
    return () => {
      alive = false;
    };
  }, [key, ttl, useStaleOnError, maxStaleAge, fetcher, canRun]);

  return { data, error, loading, fromCache };
}

/* ----------------------------------------
 * Integration & Orchestration
 * -------------------------------------- */

/**
 * Initialize the graceful degradation system.
 * - Attaches a global unhandledrejection listener that maps known service errors to flags
 * - Starts a cache cleanup interval
 * - Returns a disposer to unhook everything
 */
export function initializeGracefulDegradation() {
  if (typeof window === "undefined") {
    // SSR: no-op — return a dummy disposer
    return () => void 0;
  }

  const rejectionHandler = (event: PromiseRejectionEvent) => {
    const error: unknown = event?.reason;
    const errorObj = error as { message?: string };
    const msg = (errorObj?.message || "").toString();

    // Map common failure signatures -> feature flags
    if (
      msg.includes("extension") ||
      msg.includes("403") ||
      msg.includes("503") ||
      msg.includes("/api/extensions") ||
      msg.toLowerCase().includes("service unavailable") ||
      msg.toLowerCase().includes("network error") ||
      msg.toLowerCase().includes("timeout")
    ) {
      if (msg.includes("background-task")) {
        _ffm.handleServiceError("background-tasks", error);
      }
      if (msg.includes("model-provider")) {
        _ffm.handleServiceError("model-provider", error);
      }
      if (msg.includes("/api/extensions")) {
        _ffm.handleServiceError("extension-api", error);
      }
      if (msg.includes("health")) {
        _ffm.handleServiceError("extension-health", error);
      }
      if (msg.toLowerCase().includes("auth")) {
        _ffm.handleServiceError("extension-auth", error);
      }
    }
  };

  window.addEventListener("unhandledrejection", rejectionHandler);

  // periodic cache cleanup
  const intervalId = window.setInterval(() => {
    try {
      sharedExtensionCache.cleanup();
    } catch {
      /* ignore */
    }
  }, 5 * 60 * 1000); // every 5 minutes

  // Disposer
  return () => {
    try {
      window.removeEventListener("unhandledrejection", rejectionHandler);
      window.clearInterval(intervalId);
    } catch {
      /* ignore */
    }
  };
}

/**
 * System health snapshot for diagnostics / banner UIs
 */
export function getSystemHealthStatus() {
  const flags = _ffm.getAllFlags();
  const cacheStats = sharedExtensionCache.getStats();
  const enabledFeatures = flags.filter((f) => f.enabled).length;
  const totalFeatures = flags.length;

  return {
    features: {
      enabled: enabledFeatures,
      total: totalFeatures,
      healthPercentage: totalFeatures === 0 ? 100 : (enabledFeatures / totalFeatures) * 100,
    },
    cache: cacheStats,
    degradedServices: flags.filter((f) => !f.enabled).map((f) => f.name),
    timestamp: new Date().toISOString(),
  };
}

/**
 * Force purge all extension cache entries
 */
export function refreshAllCachedData() {
  sharedExtensionCache.clear();
}

/**
 * Development mode helper — enables all flags (use in dev-only toggles/tools)
 */
export function enableDevelopmentMode() {
  _ffm.getAllFlags().forEach((flag) => {
    _ffm.setFlag(flag.name, true);
  });
  return {
    message: "Development mode enabled: all feature flags set to true",
    snapshot: getSystemHealthStatus(),
  };
}

/**
 * Simulate failure/recovery for testing degraded paths
 */
export function simulateServiceFailure(serviceName: string) {
  console.warn(`Simulating failure for service: ${serviceName}`);
  _ffm.handleServiceError(serviceName, new Error(`Simulated failure for ${serviceName}`));
}

export function simulateServiceRecovery(serviceName: string) {
  console.info(`Simulating recovery for service: ${serviceName}`);
  _ffm.handleServiceRecovery(serviceName);
}

/* ----------------------------------------
 * Default configuration (exported constant)
 * -------------------------------------- */
export const defaultGracefulDegradationConfig = {
  cacheEnabled: true,
  cacheTTL: 5 * 60 * 1000, // 5 minutes
  maxStaleAge: 60 * 60 * 1000, // 1 hour
  autoRecoveryEnabled: true,
  developmentMode: process.env.NODE_ENV === "development",
};
