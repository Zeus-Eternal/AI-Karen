import React, { ReactNode } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { FeatureFlagsProvider } from '@/contexts/FeatureFlagsContext';
import { FeatureFlag } from '@/hooks/use-feature';
import { featureFlagTestUtils, resetFeatureFlagTester, getFeatureFlagTester } from '@/lib/featureFlagTesting';

export interface FeatureFlagTestOptions {
  flags?: Partial<Record<FeatureFlag, boolean>>;
  persistToStorage?: boolean;
}

/**
 * Custom render function that wraps components with FeatureFlagsProvider
 */
export const renderWithFeatureFlags = (
  ui: React.ReactElement,
  options: FeatureFlagTestOptions & RenderOptions = {}
) => {
  const { flags = {}, persistToStorage = false, ...renderOptions } = options;

  // Set up flag overrides for testing
  featureFlagTestUtils.mockFlags(flags);

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <FeatureFlagsProvider 
      initialFlags={flags} 
      persistToStorage={persistToStorage}
    >
      {children}
    </FeatureFlagsProvider>
  );

  const result = render(ui, { wrapper: Wrapper, ...renderOptions });

  return {
    ...result,
    // Helper to update flags during test
    updateFlags: (newFlags: Partial<Record<FeatureFlag, boolean>>) => {
      featureFlagTestUtils.mockFlags(newFlags);
      result.rerender(ui);
    },
    // Helper to restore original flags
    restoreFlags: () => {
      featureFlagTestUtils.restoreFlags();
      result.rerender(ui);
    }
  };
};

/**
 * Test utilities for feature flag testing
 */
export const featureFlagTestHelpers = {
  /**
   * Setup function to run before each test
   */
  setup: () => {
    resetFeatureFlagTester();
  },

  /**
   * Cleanup function to run after each test
   */
  cleanup: () => {
    featureFlagTestUtils.restoreFlags();
    resetFeatureFlagTester();
  },

  /**
   * Create a test scenario with specific flags enabled/disabled
   */
  createScenario: (
    name: string,
    flags: Partial<Record<FeatureFlag, boolean>>
  ) => ({
    name,
    flags,
    setup: () => featureFlagTestUtils.mockFlags(flags),
    cleanup: () => featureFlagTestUtils.restoreFlags()
  }),

  /**
   * Test multiple flag combinations
   */
  testFlagCombinations: (
    testFn: (flags: Partial<Record<FeatureFlag, boolean>>) => void,
    combinations: Array<{
      name: string;
      flags: Partial<Record<FeatureFlag, boolean>>;
    }>
  ) => {
    combinations.forEach(({ name, flags }) => {
      describe(name, () => {
        beforeEach(() => {
          featureFlagTestUtils.mockFlags(flags);
        });

        afterEach(() => {
          featureFlagTestUtils.restoreFlags();
        });

        testFn(flags);
      });
    });
  },

  /**
   * Assert that specific flags were checked during test execution
   */
  assertFlagsUsed: (expectedFlags: FeatureFlag[]) => {
    expectedFlags.forEach(flag => {
      expect(featureFlagTestUtils.assertFlagUsed(flag)).toBe(true);
    });
  },

  /**
   * Assert that flags were not checked during test execution
   */
  assertFlagsNotUsed: (unexpectedFlags: FeatureFlag[]) => {
    unexpectedFlags.forEach(flag => {
      expect(featureFlagTestUtils.assertFlagUsed(flag)).toBe(false);
    });
  },

  /**
   * Get usage statistics for analysis
   */
  getUsageStats: () => {
    const tester = getFeatureFlagTester();
    return tester.generateUsageReport();
  }
};

/**
 * Common test scenarios for feature flags
 */
export const commonFeatureFlagScenarios = {
  allEnabled: featureFlagTestHelpers.createScenario('all features enabled', {
    'chat.streaming': true,
    'chat.tools': true,
    'chat.edit': true,
    'chat.quick_actions': true,
    'copilot.enabled': true,
    'voice.input': true,
    'voice.output': true,
    'attachments.enabled': true,
    'emoji.picker': true,
    'analytics.detailed': true,
    'performance.virtualization': true,
    'accessibility.enhanced': true,
    'telemetry.enabled': true,
    'debug.mode': true
  }),

  allDisabled: featureFlagTestHelpers.createScenario('all features disabled', {
    'chat.streaming': false,
    'chat.tools': false,
    'chat.edit': false,
    'chat.quick_actions': false,
    'copilot.enabled': false,
    'voice.input': false,
    'voice.output': false,
    'attachments.enabled': false,
    'emoji.picker': false,
    'analytics.detailed': false,
    'performance.virtualization': false,
    'accessibility.enhanced': false,
    'telemetry.enabled': false,
    'debug.mode': false
  }),

  productionSafe: featureFlagTestHelpers.createScenario('production-safe configuration', {
    'chat.streaming': true,
    'chat.tools': true,
    'chat.edit': true,
    'copilot.enabled': true,
    'voice.input': false,
    'voice.output': false,
    'attachments.enabled': false,
    'analytics.detailed': false,
    'security.sanitization': true,
    'security.rbac': true,
    'performance.virtualization': true,
    'accessibility.enhanced': true,
    'telemetry.enabled': true,
    'debug.mode': false
  }),

  developmentMode: featureFlagTestHelpers.createScenario('development mode', {
    'debug.mode': true,
    'analytics.detailed': true,
    'voice.input': true,
    'voice.output': true,
    'attachments.enabled': true
  }),

  minimalFeatures: featureFlagTestHelpers.createScenario('minimal features only', {
    'chat.streaming': true,
    'security.sanitization': true,
    'security.rbac': true
  })
};

/**
 * Performance testing utilities for feature flags
 */
export const featureFlagPerformanceHelpers = {
  /**
   * Measure the performance impact of feature flag checks
   */
  measureFlagCheckPerformance: async (
    flag: FeatureFlag,
    iterations: number = 1000
  ): Promise<{
    averageTime: number;
    minTime: number;
    maxTime: number;
    totalTime: number;
  }> => {
    const times: number[] = [];
    const { getFeatureFlagTester } = await import('@/lib/featureFlagTesting');
    const tester = getFeatureFlagTester();

    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      tester.getOverride(flag);
      const end = performance.now();
      times.push(end - start);
    }

    return {
      averageTime: times.reduce((sum, time) => sum + time, 0) / times.length,
      minTime: Math.min(...times),
      maxTime: Math.max(...times),
      totalTime: times.reduce((sum, time) => sum + time, 0)
    };
  },

  /**
   * Benchmark different flag checking strategies
   */
  benchmarkFlagStrategies: async (flags: FeatureFlag[]) => {
    const results = new Map<FeatureFlag, any>();

    for (const flag of flags) {
      const performance = await featureFlagPerformanceHelpers.measureFlagCheckPerformance(flag);
      results.set(flag, performance);
    }

    return results;
  }
};