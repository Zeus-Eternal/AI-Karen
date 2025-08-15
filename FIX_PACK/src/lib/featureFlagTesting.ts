'use client';

import { FeatureFlag } from '@/hooks/use-feature';

export interface FeatureFlagOverride {
  flag: FeatureFlag;
  value: boolean;
  reason?: string;
  expiresAt?: Date;
}

export interface FeatureFlagTestConfig {
  overrides: FeatureFlagOverride[];
  analytics: {
    trackUsage: boolean;
    trackPerformance: boolean;
    sampleRate: number;
  };
  environment: 'test' | 'development' | 'staging' | 'production';
}

export interface FeatureFlagUsageAnalytics {
  flag: FeatureFlag;
  enabled: boolean;
  usageCount: number;
  lastUsed: Date;
  contexts: string[];
  performance?: {
    averageCheckTime: number;
    totalChecks: number;
  };
}

/**
 * Feature flag testing utilities
 */
export class FeatureFlagTester {
  private overrides: Map<FeatureFlag, FeatureFlagOverride> = new Map();
  private analytics: Map<FeatureFlag, FeatureFlagUsageAnalytics> = new Map();
  private config: FeatureFlagTestConfig;

  constructor(config: Partial<FeatureFlagTestConfig> = {}) {
    this.config = {
      overrides: [],
      analytics: {
        trackUsage: true,
        trackPerformance: true,
        sampleRate: 1.0
      },
      environment: 'test',
      ...config
    };

    // Apply initial overrides
    this.config.overrides.forEach(override => {
      this.setOverride(override);
    });
  }

  /**
   * Set a feature flag override for testing
   */
  setOverride(override: FeatureFlagOverride): void {
    // Check if override has expired
    if (override.expiresAt && override.expiresAt < new Date()) {
      console.warn(`Override for flag '${override.flag}' has expired`);
      return;
    }

    this.overrides.set(override.flag, override);
    
    if (this.config.analytics.trackUsage) {
      this.trackOverrideSet(override);
    }
  }

  /**
   * Remove a feature flag override
   */
  removeOverride(flag: FeatureFlag): void {
    const removed = this.overrides.delete(flag);
    
    if (removed && this.config.analytics.trackUsage) {
      this.trackOverrideRemoved(flag);
    }
  }

  /**
   * Clear all overrides
   */
  clearOverrides(): void {
    const clearedFlags = Array.from(this.overrides.keys());
    this.overrides.clear();
    
    if (this.config.analytics.trackUsage) {
      this.trackOverridesCleared(clearedFlags);
    }
  }

  /**
   * Get the override value for a flag, if any
   */
  getOverride(flag: FeatureFlag): boolean | null {
    const override = this.overrides.get(flag);
    
    if (!override) {
      return null;
    }

    // Check if override has expired
    if (override.expiresAt && override.expiresAt < new Date()) {
      this.removeOverride(flag);
      return null;
    }

    return override.value;
  }

  /**
   * Check if a flag has an override
   */
  hasOverride(flag: FeatureFlag): boolean {
    return this.overrides.has(flag);
  }

  /**
   * Get all active overrides
   */
  getActiveOverrides(): FeatureFlagOverride[] {
    const now = new Date();
    return Array.from(this.overrides.values()).filter(override => 
      !override.expiresAt || override.expiresAt > now
    );
  }

  /**
   * Track feature flag usage for analytics
   */
  trackUsage(flag: FeatureFlag, enabled: boolean, context?: string): void {
    if (!this.config.analytics.trackUsage) {
      return;
    }

    // Sample based on configured rate
    if (Math.random() > this.config.analytics.sampleRate) {
      return;
    }

    const existing = this.analytics.get(flag);
    const now = new Date();

    if (existing) {
      existing.usageCount++;
      existing.lastUsed = now;
      existing.enabled = enabled;
      
      if (context && !existing.contexts.includes(context)) {
        existing.contexts.push(context);
      }
    } else {
      this.analytics.set(flag, {
        flag,
        enabled,
        usageCount: 1,
        lastUsed: now,
        contexts: context ? [context] : [],
        performance: this.config.analytics.trackPerformance ? {
          averageCheckTime: 0,
          totalChecks: 0
        } : undefined
      });
    }
  }

  /**
   * Track performance metrics for flag checks
   */
  trackPerformance(flag: FeatureFlag, checkTime: number): void {
    if (!this.config.analytics.trackPerformance) {
      return;
    }

    const analytics = this.analytics.get(flag);
    if (analytics && analytics.performance) {
      const { averageCheckTime, totalChecks } = analytics.performance;
      const newTotal = totalChecks + 1;
      const newAverage = (averageCheckTime * totalChecks + checkTime) / newTotal;
      
      analytics.performance.averageCheckTime = newAverage;
      analytics.performance.totalChecks = newTotal;
    }
  }

  /**
   * Get usage analytics for a specific flag
   */
  getAnalytics(flag: FeatureFlag): FeatureFlagUsageAnalytics | null {
    return this.analytics.get(flag) || null;
  }

  /**
   * Get usage analytics for all flags
   */
  getAllAnalytics(): FeatureFlagUsageAnalytics[] {
    return Array.from(this.analytics.values());
  }

  /**
   * Generate a usage report
   */
  generateUsageReport(): {
    totalFlags: number;
    activeFlags: number;
    overriddenFlags: number;
    mostUsedFlags: FeatureFlagUsageAnalytics[];
    performanceMetrics: {
      averageCheckTime: number;
      slowestFlags: { flag: FeatureFlag; time: number }[];
    };
  } {
    const allAnalytics = this.getAllAnalytics();
    const activeFlags = allAnalytics.filter(a => a.usageCount > 0);
    const overriddenFlags = this.getActiveOverrides();

    // Sort by usage count
    const mostUsed = [...allAnalytics]
      .sort((a, b) => b.usageCount - a.usageCount)
      .slice(0, 10);

    // Performance metrics
    const performanceData = allAnalytics
      .filter(a => a.performance)
      .map(a => ({
        flag: a.flag,
        time: a.performance!.averageCheckTime
      }));

    const averageCheckTime = performanceData.length > 0
      ? performanceData.reduce((sum, p) => sum + p.time, 0) / performanceData.length
      : 0;

    const slowestFlags = performanceData
      .sort((a, b) => b.time - a.time)
      .slice(0, 5);

    return {
      totalFlags: allAnalytics.length,
      activeFlags: activeFlags.length,
      overriddenFlags: overriddenFlags.length,
      mostUsedFlags: mostUsed,
      performanceMetrics: {
        averageCheckTime,
        slowestFlags
      }
    };
  }

  /**
   * Export analytics data for external analysis
   */
  exportAnalytics(): string {
    const report = this.generateUsageReport();
    const data = {
      timestamp: new Date().toISOString(),
      environment: this.config.environment,
      config: this.config,
      overrides: this.getActiveOverrides(),
      analytics: this.getAllAnalytics(),
      report
    };

    return JSON.stringify(data, null, 2);
  }

  /**
   * Reset all analytics data
   */
  resetAnalytics(): void {
    this.analytics.clear();
  }

  private trackOverrideSet(override: FeatureFlagOverride): void {
    console.log(`Feature flag override set: ${override.flag} = ${override.value}`, {
      reason: override.reason,
      expiresAt: override.expiresAt
    });
  }

  private trackOverrideRemoved(flag: FeatureFlag): void {
    console.log(`Feature flag override removed: ${flag}`);
  }

  private trackOverridesCleared(flags: FeatureFlag[]): void {
    console.log(`All feature flag overrides cleared`, { flags });
  }
}

/**
 * Global feature flag tester instance
 */
let globalTester: FeatureFlagTester | null = null;

/**
 * Get or create the global feature flag tester
 */
export const getFeatureFlagTester = (config?: Partial<FeatureFlagTestConfig>): FeatureFlagTester => {
  if (!globalTester) {
    globalTester = new FeatureFlagTester(config);
  }
  return globalTester;
};

/**
 * Reset the global feature flag tester
 */
export const resetFeatureFlagTester = (): void => {
  globalTester = null;
};

/**
 * Test utilities for feature flags
 */
export const featureFlagTestUtils = {
  /**
   * Create a test configuration with common overrides
   */
  createTestConfig: (overrides: Partial<Record<FeatureFlag, boolean>> = {}): FeatureFlagTestConfig => ({
    overrides: Object.entries(overrides).map(([flag, value]) => ({
      flag: flag as FeatureFlag,
      value,
      reason: 'Test override'
    })),
    analytics: {
      trackUsage: true,
      trackPerformance: true,
      sampleRate: 1.0
    },
    environment: 'test'
  }),

  /**
   * Create temporary overrides that expire after a duration
   */
  createTemporaryOverrides: (
    overrides: Partial<Record<FeatureFlag, boolean>>,
    durationMs: number = 60000
  ): FeatureFlagOverride[] => {
    const expiresAt = new Date(Date.now() + durationMs);
    return Object.entries(overrides).map(([flag, value]) => ({
      flag: flag as FeatureFlag,
      value,
      reason: 'Temporary test override',
      expiresAt
    }));
  },

  /**
   * Mock feature flag values for testing
   */
  mockFlags: (flags: Partial<Record<FeatureFlag, boolean>>): void => {
    const tester = getFeatureFlagTester();
    Object.entries(flags).forEach(([flag, value]) => {
      tester.setOverride({
        flag: flag as FeatureFlag,
        value,
        reason: 'Mock for testing'
      });
    });
  },

  /**
   * Restore original feature flag values
   */
  restoreFlags: (): void => {
    const tester = getFeatureFlagTester();
    tester.clearOverrides();
  },

  /**
   * Assert that a flag was used during a test
   */
  assertFlagUsed: (flag: FeatureFlag): boolean => {
    const tester = getFeatureFlagTester();
    const analytics = tester.getAnalytics(flag);
    return analytics !== null && analytics.usageCount > 0;
  },

  /**
   * Get usage count for a flag
   */
  getFlagUsageCount: (flag: FeatureFlag): number => {
    const tester = getFeatureFlagTester();
    const analytics = tester.getAnalytics(flag);
    return analytics?.usageCount || 0;
  }
};