/**
 * Feature flags system for extension availability and graceful degradation
 */

export interface FeatureFlag {
  name: string;
  enabled: boolean;
  fallbackBehavior: "hide" | "disable" | "cache" | "mock";
  description?: string;
  dependencies?: string[];
}

export interface ExtensionFeatureFlags {
  extensionSystem: FeatureFlag;
  backgroundTasks: FeatureFlag;
  modelProviderIntegration: FeatureFlag;
  extensionHealth: FeatureFlag;
  extensionAuth: FeatureFlag;
}

export class FeatureFlagManager {
  private flags: Map<string, FeatureFlag> = new Map();
  private listeners: Map<string, ((flag: FeatureFlag) => void)[]> = new Map();

  constructor() {
    this.initializeDefaultFlags();
    this.loadFlagsFromStorage();
  }

  private initializeDefaultFlags(): void {
    const defaultFlags: ExtensionFeatureFlags = {
      extensionSystem: {
        name: "extensionSystem",
        enabled: true,
        fallbackBehavior: "disable",
        description: "Core extension system functionality",
        dependencies: [],
      },
      backgroundTasks: {
        name: "backgroundTasks",
        enabled: true,
        fallbackBehavior: "hide",
        description: "Extension background task management",
        dependencies: ["extensionSystem"],
      },
      modelProviderIntegration: {
        name: "modelProviderIntegration",
        enabled: true,
        fallbackBehavior: "cache",
        description: "Model provider integration features",
        dependencies: ["extensionSystem"],
      },
      extensionHealth: {
        name: "extensionHealth",
        enabled: true,
        fallbackBehavior: "mock",
        description: "Extension health monitoring",
        dependencies: ["extensionSystem"],
      },
      extensionAuth: {
        name: "extensionAuth",
        enabled: true,
        fallbackBehavior: "disable",
        description: "Extension authentication system",
        dependencies: [],
      },
    };

    Object.values(defaultFlags).forEach((flag) => {
      this.flags.set(flag.name, flag);
    });
  }

  private loadFlagsFromStorage(): void {
    try {
      const stored = localStorage.getItem("extension-feature-flags");
      if (stored) {
        const storedFlags = JSON.parse(stored);
        Object.entries(storedFlags).forEach(([name, flag]) => {
          if (this.flags.has(name)) {
            this.flags.set(name, {
              ...this.flags.get(name)!,
              ...(flag as Partial<FeatureFlag>),
            });
          }
        });
      }
    } catch (error) {
      console.warn("Failed to load feature flags from storage:", error);
    }
  }

  private saveFlagsToStorage(): void {
    try {
      const flagsObject = Object.fromEntries(this.flags);
      localStorage.setItem(
        "extension-feature-flags",
        JSON.stringify(flagsObject)
      );
    } catch (error) {
      console.warn("Failed to save feature flags to storage:", error);
    }
  }

  isEnabled(flagName: string): boolean {
    const flag = this.flags.get(flagName);
    if (!flag) {
      console.warn(`Feature flag '${flagName}' not found, defaulting to false`);
      return false;
    }

    // Check dependencies
    if (flag.dependencies) {
      for (const dependency of flag.dependencies) {
        if (!this.isEnabled(dependency)) {
          return false;
        }
      }
    }

    return flag.enabled;
  }

  getFlag(flagName: string): FeatureFlag | undefined {
    return this.flags.get(flagName);
  }

  setFlag(flagName: string, enabled: boolean): void {
    const flag = this.flags.get(flagName);
    if (flag) {
      flag.enabled = enabled;
      this.flags.set(flagName, flag);
      this.saveFlagsToStorage();
      this.notifyListeners(flagName, flag);
    }
  }

  updateFlag(flagName: string, updates: Partial<FeatureFlag>): void {
    const flag = this.flags.get(flagName);
    if (flag) {
      const updatedFlag = { ...flag, ...updates };
      this.flags.set(flagName, updatedFlag);
      this.saveFlagsToStorage();
      this.notifyListeners(flagName, updatedFlag);
    }
  }

  getFallbackBehavior(flagName: string): "hide" | "disable" | "cache" | "mock" {
    const flag = this.flags.get(flagName);
    return flag?.fallbackBehavior || "disable";
  }

  getAllFlags(): FeatureFlag[] {
    return Array.from(this.flags.values());
  }

  onFlagChange(
    flagName: string,
    callback: (flag: FeatureFlag) => void
  ): () => void {
    if (!this.listeners.has(flagName)) {
      this.listeners.set(flagName, []);
    }
    this.listeners.get(flagName)!.push(callback);

    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(flagName);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
      }
    };
  }

  private notifyListeners(flagName: string, flag: FeatureFlag): void {
    const callbacks = this.listeners.get(flagName);
    if (callbacks) {
      callbacks.forEach((callback) => {
        try {
          callback(flag);
        } catch (error) {
          console.error(
            `Error in feature flag listener for '${flagName}':`,
            error
          );
        }
      });
    }
  }

  // Auto-disable flags based on service health
  handleServiceError(serviceName: string, error: any): void {
    const flagMappings: Record<string, string> = {
      "extension-api": "extensionSystem",
      "background-tasks": "backgroundTasks",
      "model-provider": "modelProviderIntegration",
      "extension-health": "extensionHealth",
      "extension-auth": "extensionAuth",
    };

    const flagName = flagMappings[serviceName];
    if (flagName) {
      console.warn(
        `Service '${serviceName}' error detected, disabling feature flag '${flagName}'`
      );
      this.setFlag(flagName, false);
    }
  }

  // Re-enable flags when services recover
  handleServiceRecovery(serviceName: string): void {
    const flagMappings: Record<string, string> = {
      "extension-api": "extensionSystem",
      "background-tasks": "backgroundTasks",
      "model-provider": "modelProviderIntegration",
      "extension-health": "extensionHealth",
      "extension-auth": "extensionAuth",
    };

    const flagName = flagMappings[serviceName];
    if (flagName) {
      console.info(
        `Service '${serviceName}' recovered, re-enabling feature flag '${flagName}'`
      );
      this.setFlag(flagName, true);
    }
  }
}

// Global feature flag manager instance
export const featureFlagManager = new FeatureFlagManager();

// React hook for using feature flags
import React from "react";

export function useFeatureFlag(flagName: string) {
  const [flag, setFlag] = React.useState<FeatureFlag | undefined>(
    featureFlagManager.getFlag(flagName)
  );

  React.useEffect(() => {
    const unsubscribe = featureFlagManager.onFlagChange(flagName, setFlag);
    return unsubscribe;
  }, [flagName]);

  return {
    isEnabled: flag?.enabled || false,
    fallbackBehavior: flag?.fallbackBehavior || "disable",
    flag,
  };
}

// Helper functions for common patterns
export function withFeatureFlag<T>(
  flagName: string,
  component: T,
  fallback?: T
): T | null {
  const isEnabled = featureFlagManager.isEnabled(flagName);

  if (isEnabled) {
    return component;
  }

  const behavior = featureFlagManager.getFallbackBehavior(flagName);

  switch (behavior) {
    case "hide":
      return null;
    case "disable":
      return fallback || null;
    case "cache":
    case "mock":
      return fallback || component;
    default:
      return null;
  }
}
