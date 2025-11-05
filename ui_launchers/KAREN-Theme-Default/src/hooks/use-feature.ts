'use client';

import { useCallback, useMemo } from 'react';
import { safeError, safeWarn } from '@/lib/safe-console';
import { loadConfigFromEnvironment, loadConfigFromStorage, mergeWithEnvironmentDefaults, validateFeatureFlagConfig } from '@/lib/featureFlagConfig';
import { useTelemetry } from '@/hooks/use-telemetry';

export type FeatureFlag = 
  | 'chat.streaming'
  | 'chat.tools'
  | 'chat.edit'
  | 'chat.quick_actions'
  | 'copilot.enabled'
  | 'voice.input'
  | 'voice.output'
  | 'attachments.enabled'
  | 'emoji.picker'
  | 'analytics.detailed'
  | 'security.sanitization'
  | 'security.rbac'
  | 'performance.virtualization'
  | 'accessibility.enhanced'
  | 'telemetry.enabled'
  | 'debug.mode';

// Cache for resolved feature flags to avoid repeated computation
let resolvedFlags: Record<FeatureFlag, boolean> | null = null;
let lastResolvedTime = 0;
const CACHE_DURATION = 60000; // 1 minute cache

const resolveFeatureFlags = (): Record<FeatureFlag, boolean> => {
  const now = Date.now();
  
  // Return cached flags if still valid
  if (resolvedFlags && (now - lastResolvedTime) < CACHE_DURATION) {
    return resolvedFlags;
  }

  try {
    // Load from various sources with precedence
    const envFlags = loadConfigFromEnvironment();
    const storedFlags = loadConfigFromStorage();
    
    // Merge with environment defaults
    const mergedFlags = mergeWithEnvironmentDefaults({
      ...storedFlags,
      ...envFlags
    });

    // Validate the final configuration
    const validation = validateFeatureFlagConfig(mergedFlags);
    
    if (!validation.isValid) {
      safeError('Invalid feature flag configuration:', validation.errors);
      // Fall back to safe defaults
      resolvedFlags = mergeWithEnvironmentDefaults({});
    } else {
      if (validation.warnings.length > 0) {
        safeWarn('Feature flag configuration warnings:', validation.warnings);
      }
      resolvedFlags = mergedFlags;
    }

    lastResolvedTime = now;
    return resolvedFlags;
    
  } catch (error) {
    safeError('Failed to resolve feature flags:', error);
    // Fall back to safe defaults
    resolvedFlags = mergeWithEnvironmentDefaults({});
    lastResolvedTime = now;
    return resolvedFlags;
  }
};

export const useFeature = (flag?: string): boolean => {
  const { track } = useTelemetry();
  
  const flags = useMemo(() => resolveFeatureFlags(), []);
  
  const checkFeature = useCallback((flagName: string): boolean => {
    if (!flagName) {
      return false;
    }

    const isEnabled = flags[flagName as FeatureFlag] ?? false;
    
    // Track feature flag usage (with sampling to avoid spam)
    if (Math.random() < 0.01) { // 1% sampling
      track('feature_flag_checked', {
        flag: flagName,
        enabled: isEnabled,
        source: 'useFeature'
      });
    }

    return isEnabled;
  }, [flags, track]);

  return checkFeature(flag || '');
};

// Hook for getting multiple feature flags at once
export const useFeatures = (flags: FeatureFlag[]): Record<FeatureFlag, boolean> => {
  const { track } = useTelemetry();
  
  const resolvedFlags = useMemo(() => resolveFeatureFlags(), []);
  
  return useMemo(() => {
    const result: Record<FeatureFlag, boolean> = {} as Record<FeatureFlag, boolean>;
    
    flags.forEach(flag => {
      result[flag] = resolvedFlags[flag] ?? false;
    });

    // Track batch feature flag check
    track('feature_flags_batch_checked', {
      flags: flags,
      results: result,
      source: 'useFeatures'
    });

    return result;
  }, [flags, resolvedFlags, track]);
};

// Hook for getting all feature flags
export const useAllFeatures = (): Record<FeatureFlag, boolean> => {
  return useMemo(() => resolveFeatureFlags(), []);
};

// Utility function to check feature flag outside of React components
export const isFeatureEnabled = (flag: FeatureFlag): boolean => {
  const flags = resolveFeatureFlags();
  return flags[flag] ?? false;
};

// Utility function to invalidate the feature flag cache
export const invalidateFeatureFlagCache = (): void => {
  resolvedFlags = null;
  lastResolvedTime = 0;
};

export default useFeature;
