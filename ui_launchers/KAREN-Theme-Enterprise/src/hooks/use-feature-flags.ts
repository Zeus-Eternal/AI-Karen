/**
 * Hook for using feature flags in components
 */

import { useMemo } from 'react';
import { getFeatureFlagsWithDefaults, isFeatureEnabled, getCurrentDeploymentPhase, type FeatureFlags } from '@/lib/feature-flags';

/**
 * Hook to get all feature flags
 */
export function useFeatureFlags(): FeatureFlags {
  return useMemo(() => getFeatureFlagsWithDefaults(), []);
}

/**
 * Hook to check if a specific feature is enabled
 */
export function useFeatureFlag(feature: keyof FeatureFlags): boolean {
  return useMemo(() => isFeatureEnabled(feature), [feature]);
}

/**
 * Hook to get current deployment phase
 */
export function useDeploymentPhase(): 'none' | 'phase1' | 'phase2' | 'phase3' | 'phase4' {
  return useMemo(() => getCurrentDeploymentPhase(), []);
}

/**
 * Hook to conditionally render components based on feature flags
 */
export function useConditionalComponent<T>(
  feature: keyof FeatureFlags,
  modernComponent: T,
  legacyComponent: T
): T {
  const isEnabled = useFeatureFlag(feature);
  return isEnabled ? modernComponent : legacyComponent;
}

/**
 * Hook to get feature-aware class names
 */
export function useFeatureClasses(
  feature: keyof FeatureFlags,
  modernClasses: string,
  legacyClasses: string = ''
): string {
  const isEnabled = useFeatureFlag(feature);
  return isEnabled ? modernClasses : legacyClasses;
}