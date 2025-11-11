"use client";

/**
 * Initialization script for graceful degradation system
 * Call early in the application lifecycle (e.g., in your root layout/client entry).
 */

import {
  featureFlagManager,
  extensionCache,
  initializeGracefulDegradation,
  defaultGracefulDegradationConfig,
} from "./index";
import { setupGlobalErrorHandling } from "./use-graceful-backend";

export interface GracefulDegradationConfig {
  enableCaching?: boolean;
  cacheCleanupInterval?: number;
  enableGlobalErrorHandling?: boolean;
  developmentMode?: boolean;
  logLevel?: "debug" | "warn" | "error" | ""; // extended to include "debug"
  featureFlags?: {
    [key: string]: {
      enabled?: boolean;
      fallbackBehavior?: "hide" | "disable" | "cache" | "mock";
    };
  };
}

let isInitialized = false;
let disposeCore: (() => void) | null = null;
let cacheCleanupTimer: number | null = null;
let healthCheckTimer: number | null = null;
let fetchPatched = false;
let originalFetch: typeof window.fetch | null = null;
let currentConfig: GracefulDegradationConfig & typeof defaultGracefulDegradationConfig =
  { ...defaultGracefulDegradationConfig };

export function initGracefulDegradation(config: GracefulDegradationConfig = {}) {
  if (isInitialized) return;

  currentConfig = {
    ...defaultGracefulDegradationConfig,
    ...config,
  };

  try {
    // Initialize core degradation system (returns disposer)
    disposeCore = initializeGracefulDegradation();

    // Set up global error handling (unless explicitly disabled)
    if (currentConfig.enableGlobalErrorHandling !== false) {
      setupGlobalErrorHandling?.();
    }

    // Configure feature flags (enable + fallback behaviors)
    if (currentConfig.featureFlags) {
      Object.entries(currentConfig.featureFlags).forEach(([flagName, cfg]) => {
        if (cfg.enabled !== undefined) {
          featureFlagManager.setFlag(flagName, cfg.enabled);
        }
        if (cfg.fallbackBehavior) {
          featureFlagManager.updateFlag(flagName, { fallbackBehavior: cfg.fallbackBehavior });
        }
      });
    }

    // Cache cleanup loop
    if (currentConfig.enableCaching !== false && typeof window !== "undefined") {
      const cleanupInterval = currentConfig.cacheCleanupInterval ?? 5 * 60 * 1000; // 5 min
      cacheCleanupTimer = window.setInterval(() => {
        const removedCount = extensionCache.cleanup();
        if (removedCount > 0 && currentConfig.logLevel === "debug") {
          // eslint-disable-next-line no-console
          console.debug(`[graceful] Cache cleanup removed ${removedCount} expired entries`);
        }
      }, cleanupInterval);
    }

    // Development helpers
    if (currentConfig.developmentMode) {
      enableDevelopmentMode();
    }

    // Periodic health checks + service recovery monitoring
    setupPeriodicHealthChecks();
    setupServiceRecoveryMonitoring();

    isInitialized = true;
  } catch (err) {
    // Surface and rethrow – upstream can decide how to handle
    // eslint-disable-next-line no-console
    console.error("[graceful] Initialization failed:", err);
    throw err;
  }
}

/** Expose init state */
export { isInitialized };

/** Teardown (for HMR/unmount) */
export function teardownGracefulDegradation() {
  try {
    if (disposeCore) {
      disposeCore();
      disposeCore = null;
    }
  } catch {
    /* ignore */
  }

  if (cacheCleanupTimer) {
    window.clearInterval(cacheCleanupTimer);
    cacheCleanupTimer = null;
  }
  if (healthCheckTimer) {
    window.clearInterval(healthCheckTimer);
    healthCheckTimer = null;
  }
  if (fetchPatched && originalFetch) {
    window.fetch = originalFetch;
    fetchPatched = false;
    originalFetch = null;
  }
  isInitialized = false;
}

/* =========================
 * Internal helpers
 * ======================= */

function enableDevelopmentMode() {
  // Enable all flags in dev
  featureFlagManager.getAllFlags().forEach((flag) => {
    featureFlagManager.setFlag(flag.name, true);
  });

  // Add dev helpers to window
  if (typeof window !== "undefined") {
    (window as { gracefulDegradation?: unknown } & Window).gracefulDegradation = {
      featureFlagManager,
      extensionCache,
      simulateFailure: (serviceName: string) => {
        featureFlagManager.handleServiceError(
          serviceName,
          new Error(`Simulated failure for ${serviceName}`),
        );
      },
      simulateRecovery: (serviceName: string) => {
        featureFlagManager.handleServiceRecovery(serviceName);
      },
      getSystemHealth: () => {
        const flags = featureFlagManager.getAllFlags();
        const cacheStats = extensionCache.getStats();
        return {
          features: flags.map((f) => ({
            name: f.name,
            enabled: f.enabled,
            fallbackBehavior: f.fallbackBehavior,
          })),
          cache: cacheStats,
          timestamp: new Date().toISOString(),
        };
      },
      clearCache: () => extensionCache.clear(),
    };
  }
}

function setupPeriodicHealthChecks() {
  if (typeof window === "undefined") return;
  // Every 2 minutes, try to recover disabled services (lightweight probe)
  healthCheckTimer = window.setInterval(() => {
    const flags = featureFlagManager.getAllFlags();
    const disabled = flags.filter((f) => !f.enabled);
    if (disabled.length > 0 && currentConfig.logLevel === "debug") {
      // eslint-disable-next-line no-console
      console.debug(
        "[graceful] Disabled services detected:",
        disabled.map((f) => f.name),
      );
    }
    disabled.forEach((flag) => {
      if (flag.fallbackBehavior === "cache" || flag.fallbackBehavior === "disable") {
        attemptServiceRecovery(flag.name).catch(() => {
          /* keep disabled */
        });
      }
    });
  }, 2 * 60 * 1000);
}

function setupServiceRecoveryMonitoring() {
  if (typeof window === "undefined" || fetchPatched) return;

  originalFetch = window.fetch.bind(window);

  // Patch fetch to observe successful requests and flip flags back on after N successes
  const successCount: Record<string, number> = {};
  const THRESHOLD = 3;

  window.fetch = async (...args: Parameters<typeof fetch>): Promise<Response> => {
    const res = await (originalFetch as typeof fetch)(...args);
    try {
      if (res.ok) {
        const url = String(args[0] ?? "");
        const serviceName = getServiceNameFromUrl(url);
        if (serviceName) {
          successCount[serviceName] = (successCount[serviceName] || 0) + 1;
          if (successCount[serviceName] >= THRESHOLD) {
            const featureName = getFeatureNameFromService(serviceName);
            if (!featureFlagManager.isEnabled(featureName)) {
              featureFlagManager.handleServiceRecovery(serviceName);
              if (currentConfig.logLevel === "debug") {
                // eslint-disable-next-line no-console
                console.debug(`[graceful] Auto-recovered feature '${featureName}' via fetch monitor`);
              }
            }
            successCount[serviceName] = 0;
          }
        }
      }
    } catch {
      /* non-fatal */
    }
    return res;
  };

  fetchPatched = true;
}

/** Attempt a lightweight health check for a given feature flag name. */
async function attemptServiceRecovery(flagName: string) {
  const serviceName = getServiceNameFromFlag(flagName);
  const endpoint = getHealthEndpointForService(serviceName);
  if (!endpoint) return;

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 5000); // 5s

  try {
    const res = await fetch(endpoint, { method: "GET", signal: controller.signal });
    if (res.ok) {
      featureFlagManager.setFlag(flagName, true);
      if (currentConfig.logLevel === "debug") {
        // eslint-disable-next-line no-console
        console.debug(`[graceful] '${flagName}' re-enabled after successful health check`);
      }
    }
  } catch {
    // keep disabled
  } finally {
    window.clearTimeout(timeoutId);
  }
}

/** Map URLs to service names used by the feature flags. */
function getServiceNameFromUrl(url: string): string | null {
  try {
    // Allow relative/absolute
    const u = new URL(url, typeof window !== "undefined" ? window.location.origin : "http://localhost");
    const p = u.pathname;
    if (p.includes("/api/extensions")) return "extension-api";
    if (p.includes("/api/models")) return "model-provider";
    if (p.includes("/api/health")) return "extension-health";
    if (p.includes("background-task")) return "background-tasks";
    return null;
  } catch {
    return null;
  }
}

function getFeatureNameFromService(serviceName: string): string {
  const map: Record<string, string> = {
    "extension-api": "extensionSystem",
    "model-provider": "modelProviderIntegration",
    "extension-health": "extensionHealth",
    "background-tasks": "backgroundTasks",
  };
  return map[serviceName] || "extensionSystem";
}

function getServiceNameFromFlag(flagName: string): string {
  const map: Record<string, string> = {
    extensionSystem: "extension-api",
    modelProviderIntegration: "model-provider",
    extensionHealth: "extension-health",
    backgroundTasks: "background-tasks",
  };
  return map[flagName] || "extension-api";
}

function getHealthEndpointForService(serviceName: string): string | null {
  const map: Record<string, string> = {
    "extension-api": "/api/extensions/health",
    "model-provider": "/api/models/health",
    "extension-health": "/api/health",
    "background-tasks": "/api/extensions/background-tasks/health",
  };
  return map[serviceName] ?? null;
}

/* =========================
 * Auto-initialize in browser
 * ======================= */

if (typeof window !== "undefined" && !isInitialized) {
  const boot = () => {
    try {
      initGracefulDegradation();
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("[graceful] Auto-init error:", err);
    }
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    // DOM already ready
    setTimeout(boot, 0);
  }
}
