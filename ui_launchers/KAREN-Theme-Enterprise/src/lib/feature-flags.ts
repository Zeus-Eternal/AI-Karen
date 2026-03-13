/**
 * Feature Flags for UI Modernization
 * Enables gradual rollout of modern UI components
 */

export interface FeatureFlags {
  // Phase 1: Foundation
  MODERN_DESIGN_TOKENS: boolean;
  MODERN_LAYOUT_SYSTEM: boolean;
  PERFORMANCE_MONITORING: boolean;
  CONTAINER_QUERIES: boolean;
  
  // Phase 2: Components
  MODERN_COMPONENTS: boolean;
  MICRO_INTERACTIONS: boolean;
  ANIMATION_SYSTEM: boolean;
  COMPOUND_PATTERNS: boolean;
  
  // Phase 3: Enhanced Features
  ENHANCED_ACCESSIBILITY: boolean;
  MODERN_ERROR_HANDLING: boolean;
  LAZY_LOADING: boolean;
  PERFORMANCE_OPTIMIZATIONS: boolean;
  
  // Phase 4: Full Integration
  FULL_MODERNIZATION: boolean;
  ALL_MODERN_COMPONENTS: boolean;
  COMPLETE_INTEGRATION: boolean;
}

export const defaultFlags: FeatureFlags = {
  // Phase 1: Foundation
  MODERN_DESIGN_TOKENS: false,
  MODERN_LAYOUT_SYSTEM: false,
  PERFORMANCE_MONITORING: false,
  CONTAINER_QUERIES: false,
  
  // Phase 2: Components
  MODERN_COMPONENTS: false,
  MICRO_INTERACTIONS: false,
  ANIMATION_SYSTEM: false,
  COMPOUND_PATTERNS: false,
  
  // Phase 3: Enhanced Features
  ENHANCED_ACCESSIBILITY: false,
  MODERN_ERROR_HANDLING: false,
  LAZY_LOADING: false,
  PERFORMANCE_OPTIMIZATIONS: false,
  
  // Phase 4: Full Integration
  FULL_MODERNIZATION: false,
  ALL_MODERN_COMPONENTS: false,
  COMPLETE_INTEGRATION: false,
};

/**
 * Get feature flags from environment variables
 */
export function getFeatureFlags(): FeatureFlags {
  return {
    // Phase 1: Foundation
    MODERN_DESIGN_TOKENS: process.env.NEXT_PUBLIC_MODERN_DESIGN_TOKENS === 'true',
    MODERN_LAYOUT_SYSTEM: process.env.NEXT_PUBLIC_MODERN_LAYOUT_SYSTEM === 'true',
    PERFORMANCE_MONITORING: process.env.NEXT_PUBLIC_PERFORMANCE_MONITORING === 'true',
    CONTAINER_QUERIES: process.env.NEXT_PUBLIC_CONTAINER_QUERIES === 'true',
    
    // Phase 2: Components
    MODERN_COMPONENTS: process.env.NEXT_PUBLIC_MODERN_COMPONENTS === 'true',
    MICRO_INTERACTIONS: process.env.NEXT_PUBLIC_MICRO_INTERACTIONS === 'true',
    ANIMATION_SYSTEM: process.env.NEXT_PUBLIC_ANIMATION_SYSTEM === 'true',
    COMPOUND_PATTERNS: process.env.NEXT_PUBLIC_COMPOUND_PATTERNS === 'true',
    
    // Phase 3: Enhanced Features
    ENHANCED_ACCESSIBILITY: process.env.NEXT_PUBLIC_ENHANCED_ACCESSIBILITY === 'true',
    MODERN_ERROR_HANDLING: process.env.NEXT_PUBLIC_MODERN_ERROR_HANDLING === 'true',
    LAZY_LOADING: process.env.NEXT_PUBLIC_LAZY_LOADING === 'true',
    PERFORMANCE_OPTIMIZATIONS: process.env.NEXT_PUBLIC_PERFORMANCE_OPTIMIZATIONS === 'true',
    
    // Phase 4: Full Integration
    FULL_MODERNIZATION: process.env.NEXT_PUBLIC_FULL_MODERNIZATION === 'true',
    ALL_MODERN_COMPONENTS: process.env.NEXT_PUBLIC_ALL_MODERN_COMPONENTS === 'true',
    COMPLETE_INTEGRATION: process.env.NEXT_PUBLIC_COMPLETE_INTEGRATION === 'true',
  };
}

/**
 * Get feature flags with fallback to defaults
 */
export function getFeatureFlagsWithDefaults(): FeatureFlags {
  const envFlags = getFeatureFlags();
  return { ...defaultFlags, ...envFlags };
}

/**
 * Check if a specific feature is enabled
 */
export function isFeatureEnabled(feature: keyof FeatureFlags): boolean {
  const flags = getFeatureFlagsWithDefaults();
  return flags[feature];
}

/**
 * Get deployment phase based on enabled flags
 */
export function getCurrentDeploymentPhase(): 'none' | 'phase1' | 'phase2' | 'phase3' | 'phase4' {
  const flags = getFeatureFlagsWithDefaults();
  
  if (flags.FULL_MODERNIZATION) {
    return 'phase4';
  } else if (flags.ENHANCED_ACCESSIBILITY) {
    return 'phase3';
  } else if (flags.MODERN_COMPONENTS) {
    return 'phase2';
  } else if (flags.MODERN_DESIGN_TOKENS) {
    return 'phase1';
  }
  
  return 'none';
}

/**
 * Feature flag presets for different deployment phases
 */
export const PHASE_PRESETS: Record<string, Partial<FeatureFlags>> = {
  phase1: {
    MODERN_DESIGN_TOKENS: true,
    MODERN_LAYOUT_SYSTEM: true,
    PERFORMANCE_MONITORING: true,
    CONTAINER_QUERIES: true,
  },
  
  phase2: {
    MODERN_DESIGN_TOKENS: true,
    MODERN_LAYOUT_SYSTEM: true,
    PERFORMANCE_MONITORING: true,
    CONTAINER_QUERIES: true,
    MODERN_COMPONENTS: true,
    MICRO_INTERACTIONS: true,
    ANIMATION_SYSTEM: true,
    COMPOUND_PATTERNS: true,
  },
  
  phase3: {
    MODERN_DESIGN_TOKENS: true,
    MODERN_LAYOUT_SYSTEM: true,
    PERFORMANCE_MONITORING: true,
    CONTAINER_QUERIES: true,
    MODERN_COMPONENTS: true,
    MICRO_INTERACTIONS: true,
    ANIMATION_SYSTEM: true,
    COMPOUND_PATTERNS: true,
    ENHANCED_ACCESSIBILITY: true,
    MODERN_ERROR_HANDLING: true,
    LAZY_LOADING: true,
    PERFORMANCE_OPTIMIZATIONS: true,
  },
  
  phase4: {
    MODERN_DESIGN_TOKENS: true,
    MODERN_LAYOUT_SYSTEM: true,
    PERFORMANCE_MONITORING: true,
    CONTAINER_QUERIES: true,
    MODERN_COMPONENTS: true,
    MICRO_INTERACTIONS: true,
    ANIMATION_SYSTEM: true,
    COMPOUND_PATTERNS: true,
    ENHANCED_ACCESSIBILITY: true,
    MODERN_ERROR_HANDLING: true,
    LAZY_LOADING: true,
    PERFORMANCE_OPTIMIZATIONS: true,
    FULL_MODERNIZATION: true,
    ALL_MODERN_COMPONENTS: true,
    COMPLETE_INTEGRATION: true,
  },
};

/**
 * Apply a phase preset
 */
export function applyPhasePreset(phase: keyof typeof PHASE_PRESETS): FeatureFlags {
  const preset = PHASE_PRESETS[phase];
  return { ...defaultFlags, ...preset };
}