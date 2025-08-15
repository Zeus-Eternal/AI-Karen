import React from 'react';
import { screen } from '@testing-library/react';
import { renderWithFeatureFlags, featureFlagTestHelpers, commonFeatureFlagScenarios } from '../featureFlagTestHelpers';
import { useFeature } from '@/hooks/use-feature';

// Mock telemetry hook
import { vi } from 'vitest';
vi.mock('@/hooks/use-telemetry', () => ({
  useTelemetry: () => ({
    track: vi.fn(),
    startSpan: vi.fn(() => ({ end: vi.fn() })),
    setCorrelationId: vi.fn(),
    flush: vi.fn()
  })
}));

// Test component that uses feature flags
const TestComponent: React.FC = () => {
  const streamingEnabled = useFeature('chat.streaming');
  const voiceEnabled = useFeature('voice.input');
  
  return (
    <div>
      <div data-testid="streaming">{streamingEnabled ? 'enabled' : 'disabled'}</div>
      <div data-testid="voice">{voiceEnabled ? 'enabled' : 'disabled'}</div>
    </div>
  );
};

describe('featureFlagTestHelpers', () => {
  beforeEach(() => {
    featureFlagTestHelpers.setup();
  });

  afterEach(() => {
    featureFlagTestHelpers.cleanup();
  });

  describe('renderWithFeatureFlags', () => {
    it('should render component with feature flags', () => {
      renderWithFeatureFlags(<TestComponent />, {
        flags: {
          'chat.streaming': true,
          'voice.input': false
        }
      });

      expect(screen.getByTestId('streaming')).toHaveTextContent('enabled');
      expect(screen.getByTestId('voice')).toHaveTextContent('disabled');
    });

    it('should allow updating flags during test', () => {
      const { updateFlags } = renderWithFeatureFlags(<TestComponent />, {
        flags: {
          'chat.streaming': false,
          'voice.input': false
        }
      });

      expect(screen.getByTestId('streaming')).toHaveTextContent('disabled');

      updateFlags({ 'chat.streaming': true });

      expect(screen.getByTestId('streaming')).toHaveTextContent('enabled');
    });

    it('should allow restoring flags', () => {
      const { updateFlags, restoreFlags } = renderWithFeatureFlags(<TestComponent />, {
        flags: {
          'chat.streaming': true
        }
      });

      updateFlags({ 'chat.streaming': false });
      expect(screen.getByTestId('streaming')).toHaveTextContent('disabled');

      restoreFlags();
      expect(screen.getByTestId('streaming')).toHaveTextContent('enabled');
    });
  });

  describe('createScenario', () => {
    it('should create a test scenario', () => {
      const scenario = featureFlagTestHelpers.createScenario('test scenario', {
        'chat.streaming': true,
        'voice.input': false
      });

      expect(scenario.name).toBe('test scenario');
      expect(scenario.flags).toEqual({
        'chat.streaming': true,
        'voice.input': false
      });
      expect(typeof scenario.setup).toBe('function');
      expect(typeof scenario.cleanup).toBe('function');
    });
  });

  describe('testFlagCombinations', () => {
    it('should create test structure for flag combinations', () => {
      const testFn = vi.fn();
      const combinations = [
        {
          name: 'all enabled',
          flags: { 'chat.streaming': true, 'voice.input': true }
        },
        {
          name: 'all disabled',
          flags: { 'chat.streaming': false, 'voice.input': false }
        }
      ];

      // This function creates describe blocks, so we can't test it directly
      // Instead, we test that it doesn't throw and is a function
      expect(() => {
        featureFlagTestHelpers.testFlagCombinations(testFn, combinations);
      }).not.toThrow();
      
      expect(typeof featureFlagTestHelpers.testFlagCombinations).toBe('function');
    });
  });

  describe('assertFlagsUsed', () => {
    it('should assert that flags were used', () => {
      renderWithFeatureFlags(<TestComponent />, {
        flags: { 'chat.streaming': true }
      });

      // The component should have checked the flag
      expect(() => {
        featureFlagTestHelpers.assertFlagsUsed(['chat.streaming']);
      }).not.toThrow();
    });

    it('should assert that flags were not used', () => {
      renderWithFeatureFlags(<TestComponent />, {
        flags: { 'chat.streaming': true }
      });

      // The component should not have checked this flag
      expect(() => {
        featureFlagTestHelpers.assertFlagsNotUsed(['debug.mode']);
      }).not.toThrow();
    });
  });

  describe('getUsageStats', () => {
    it('should return usage statistics', () => {
      renderWithFeatureFlags(<TestComponent />, {
        flags: { 'chat.streaming': true }
      });

      const stats = featureFlagTestHelpers.getUsageStats();

      expect(stats).toHaveProperty('totalFlags');
      expect(stats).toHaveProperty('activeFlags');
      expect(stats).toHaveProperty('overriddenFlags');
      expect(stats).toHaveProperty('mostUsedFlags');
      expect(stats).toHaveProperty('performanceMetrics');
    });
  });
});

describe('commonFeatureFlagScenarios', () => {
  it('should provide common scenarios', () => {
    expect(commonFeatureFlagScenarios.allEnabled).toBeDefined();
    expect(commonFeatureFlagScenarios.allDisabled).toBeDefined();
    expect(commonFeatureFlagScenarios.productionSafe).toBeDefined();
    expect(commonFeatureFlagScenarios.developmentMode).toBeDefined();
    expect(commonFeatureFlagScenarios.minimalFeatures).toBeDefined();
  });

  it('should have security flags enabled in production safe scenario', () => {
    const { flags } = commonFeatureFlagScenarios.productionSafe;
    
    expect(flags['security.sanitization']).toBe(true);
    expect(flags['security.rbac']).toBe(true);
    expect(flags['debug.mode']).toBe(false);
    expect(flags['analytics.detailed']).toBe(false);
  });

  it('should have debug features enabled in development mode', () => {
    const { flags } = commonFeatureFlagScenarios.developmentMode;
    
    expect(flags['debug.mode']).toBe(true);
    expect(flags['analytics.detailed']).toBe(true);
  });

  it('should have only essential features in minimal scenario', () => {
    const { flags } = commonFeatureFlagScenarios.minimalFeatures;
    
    expect(flags['chat.streaming']).toBe(true);
    expect(flags['security.sanitization']).toBe(true);
    expect(flags['security.rbac']).toBe(true);
    
    // Should not have optional features
    expect(flags['voice.input']).toBeUndefined();
    expect(flags['attachments.enabled']).toBeUndefined();
  });
});