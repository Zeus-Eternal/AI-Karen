import { vi } from 'vitest';
import {
  FeatureFlagTester,
  getFeatureFlagTester,
  resetFeatureFlagTester,
  featureFlagTestUtils
} from '../featureFlagTesting';
import { FeatureFlag } from '@/hooks/use-feature';

// Mock console methods
const consoleSpy = {
  log: vi.spyOn(console, 'log').mockImplementation(() => {}),
  warn: vi.spyOn(console, 'warn').mockImplementation(() => {}),
};

describe('FeatureFlagTester', () => {
  let tester: FeatureFlagTester;

  beforeEach(() => {
    tester = new FeatureFlagTester();
    consoleSpy.log.mockClear();
    consoleSpy.warn.mockClear();
  });

  afterAll(() => {
    consoleSpy.log.mockRestore();
    consoleSpy.warn.mockRestore();
  });

  describe('overrides', () => {
    it('should set and get overrides', () => {
      const override = {
        flag: 'chat.streaming' as FeatureFlag,
        value: false,
        reason: 'Test override'
      };

      tester.setOverride(override);

      expect(tester.getOverride('chat.streaming')).toBe(false);
      expect(tester.hasOverride('chat.streaming')).toBe(true);
    });

    it('should remove overrides', () => {
      const override = {
        flag: 'chat.streaming' as FeatureFlag,
        value: false,
        reason: 'Test override'
      };

      tester.setOverride(override);
      tester.removeOverride('chat.streaming');

      expect(tester.getOverride('chat.streaming')).toBeNull();
      expect(tester.hasOverride('chat.streaming')).toBe(false);
    });

    it('should clear all overrides', () => {
      tester.setOverride({
        flag: 'chat.streaming' as FeatureFlag,
        value: false,
        reason: 'Test override 1'
      });

      tester.setOverride({
        flag: 'voice.input' as FeatureFlag,
        value: true,
        reason: 'Test override 2'
      });

      expect(tester.getActiveOverrides()).toHaveLength(2);

      tester.clearOverrides();

      expect(tester.getActiveOverrides()).toHaveLength(0);
    });

    it('should handle expired overrides', () => {
      const pastDate = new Date(Date.now() - 1000);
      const override = {
        flag: 'chat.streaming' as FeatureFlag,
        value: false,
        reason: 'Expired override',
        expiresAt: pastDate
      };

      tester.setOverride(override);

      expect(consoleSpy.warn).toHaveBeenCalledWith(
        "Override for flag 'chat.streaming' has expired"
      );
      expect(tester.getOverride('chat.streaming')).toBeNull();
    });

    it('should automatically remove expired overrides on access', () => {
      const futureDate = new Date(Date.now() + 1000);
      const override = {
        flag: 'chat.streaming' as FeatureFlag,
        value: false,
        reason: 'Future override',
        expiresAt: futureDate
      };

      tester.setOverride(override);
      expect(tester.getOverride('chat.streaming')).toBe(false);

      // Manually expire the override
      override.expiresAt = new Date(Date.now() - 1000);
      tester.setOverride(override);

      expect(tester.getOverride('chat.streaming')).toBeNull();
    });

    it('should get only active overrides', () => {
      const activeOverride = {
        flag: 'chat.streaming' as FeatureFlag,
        value: false,
        reason: 'Active override'
      };

      const expiredOverride = {
        flag: 'voice.input' as FeatureFlag,
        value: true,
        reason: 'Expired override',
        expiresAt: new Date(Date.now() - 1000)
      };

      tester.setOverride(activeOverride);
      // Don't set expired override as it would be rejected

      const activeOverrides = tester.getActiveOverrides();
      expect(activeOverrides).toHaveLength(1);
      expect(activeOverrides[0].flag).toBe('chat.streaming');
    });
  });

  describe('analytics', () => {
    it('should track usage analytics', () => {
      tester.trackUsage('chat.streaming', true, 'test-context');

      const analytics = tester.getAnalytics('chat.streaming');
      expect(analytics).toBeDefined();
      expect(analytics!.flag).toBe('chat.streaming');
      expect(analytics!.enabled).toBe(true);
      expect(analytics!.usageCount).toBe(1);
      expect(analytics!.contexts).toContain('test-context');
    });

    it('should accumulate usage analytics', () => {
      tester.trackUsage('chat.streaming', true, 'context-1');
      tester.trackUsage('chat.streaming', false, 'context-2');

      const analytics = tester.getAnalytics('chat.streaming');
      expect(analytics!.usageCount).toBe(2);
      expect(analytics!.enabled).toBe(false); // Last value
      expect(analytics!.contexts).toEqual(['context-1', 'context-2']);
    });

    it('should track performance metrics', () => {
      tester.trackUsage('chat.streaming', true);
      tester.trackPerformance('chat.streaming', 5.5);
      tester.trackPerformance('chat.streaming', 3.5);

      const analytics = tester.getAnalytics('chat.streaming');
      expect(analytics!.performance).toBeDefined();
      expect(analytics!.performance!.totalChecks).toBe(2);
      expect(analytics!.performance!.averageCheckTime).toBe(4.5);
    });

    it('should respect sampling rate', () => {
      const testerWithSampling = new FeatureFlagTester({
        analytics: {
          trackUsage: true,
          trackPerformance: true,
          sampleRate: 0 // Never sample
        }
      });

      testerWithSampling.trackUsage('chat.streaming', true);

      const analytics = testerWithSampling.getAnalytics('chat.streaming');
      expect(analytics).toBeNull();
    });

    it('should generate usage report', () => {
      tester.trackUsage('chat.streaming', true);
      tester.trackUsage('voice.input', false);
      tester.trackPerformance('chat.streaming', 5.0);
      tester.trackPerformance('voice.input', 0); // No performance data for voice.input

      tester.setOverride({
        flag: 'debug.mode' as FeatureFlag,
        value: true,
        reason: 'Test override'
      });

      const report = tester.generateUsageReport();

      expect(report.totalFlags).toBe(2);
      expect(report.activeFlags).toBe(2);
      expect(report.overriddenFlags).toBe(1);
      expect(report.mostUsedFlags).toHaveLength(2);
      expect(report.performanceMetrics.averageCheckTime).toBe(2.5); // (5.0 + 0) / 2
    });

    it('should export analytics data', () => {
      tester.trackUsage('chat.streaming', true);
      tester.setOverride({
        flag: 'debug.mode' as FeatureFlag,
        value: true,
        reason: 'Test override'
      });

      const exported = tester.exportAnalytics();
      const data = JSON.parse(exported);

      expect(data).toHaveProperty('timestamp');
      expect(data).toHaveProperty('environment');
      expect(data).toHaveProperty('overrides');
      expect(data).toHaveProperty('analytics');
      expect(data).toHaveProperty('report');
    });

    it('should reset analytics', () => {
      tester.trackUsage('chat.streaming', true);
      expect(tester.getAllAnalytics()).toHaveLength(1);

      tester.resetAnalytics();
      expect(tester.getAllAnalytics()).toHaveLength(0);
    });
  });

  describe('configuration', () => {
    it('should initialize with custom config', () => {
      const customTester = new FeatureFlagTester({
        analytics: {
          trackUsage: false,
          trackPerformance: false,
          sampleRate: 0.5
        },
        environment: 'staging'
      });

      customTester.trackUsage('chat.streaming', true);
      expect(customTester.getAnalytics('chat.streaming')).toBeNull();
    });

    it('should apply initial overrides from config', () => {
      const customTester = new FeatureFlagTester({
        overrides: [{
          flag: 'chat.streaming',
          value: false,
          reason: 'Initial override'
        }]
      });

      expect(customTester.getOverride('chat.streaming')).toBe(false);
    });
  });
});

describe('global tester', () => {
  beforeEach(() => {
    resetFeatureFlagTester();
  });

  it('should create and reuse global tester', () => {
    const tester1 = getFeatureFlagTester();
    const tester2 = getFeatureFlagTester();

    expect(tester1).toBe(tester2);
  });

  it('should reset global tester', () => {
    const tester1 = getFeatureFlagTester();
    resetFeatureFlagTester();
    const tester2 = getFeatureFlagTester();

    expect(tester1).not.toBe(tester2);
  });
});

describe('featureFlagTestUtils', () => {
  beforeEach(() => {
    resetFeatureFlagTester();
  });

  it('should create test config', () => {
    const config = featureFlagTestUtils.createTestConfig({
      'chat.streaming': false,
      'voice.input': true
    });

    expect(config.overrides).toHaveLength(2);
    expect(config.environment).toBe('test');
    expect(config.analytics.trackUsage).toBe(true);
  });

  it('should create temporary overrides', () => {
    const overrides = featureFlagTestUtils.createTemporaryOverrides({
      'chat.streaming': false
    }, 5000);

    expect(overrides).toHaveLength(1);
    expect(overrides[0].expiresAt).toBeDefined();
    expect(overrides[0].expiresAt!.getTime()).toBeGreaterThan(Date.now());
  });

  it('should mock and restore flags', () => {
    const tester = getFeatureFlagTester();

    featureFlagTestUtils.mockFlags({
      'chat.streaming': false,
      'voice.input': true
    });

    expect(tester.getOverride('chat.streaming')).toBe(false);
    expect(tester.getOverride('voice.input')).toBe(true);

    featureFlagTestUtils.restoreFlags();

    expect(tester.getOverride('chat.streaming')).toBeNull();
    expect(tester.getOverride('voice.input')).toBeNull();
  });

  it('should assert flag usage', () => {
    const tester = getFeatureFlagTester();

    expect(featureFlagTestUtils.assertFlagUsed('chat.streaming')).toBe(false);

    tester.trackUsage('chat.streaming', true);

    expect(featureFlagTestUtils.assertFlagUsed('chat.streaming')).toBe(true);
    expect(featureFlagTestUtils.getFlagUsageCount('chat.streaming')).toBe(1);
  });
});