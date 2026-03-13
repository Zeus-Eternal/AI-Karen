/**
 * Feature Flags Module
 * Provides feature flag management for the application
 */

export interface FeatureFlags {
  // Chat features
  'chat.streaming': boolean;
  'chat.tools': boolean;
  'chat.edit': boolean;
  'chat.quick_actions': boolean;
  
  // Copilot features
  'copilot.enabled': boolean;
  
  // Voice features
  'voice.input': boolean;
  'voice.output': boolean;
  
  // Attachment features
  'attachments.enabled': boolean;
  
  // UI features
  'emoji.picker': boolean;
  'analytics.detailed': boolean;
  
  // Security features
  'security.sanitization': boolean;
  'security.rbac': boolean;
  
  // Performance features
  'performance.virtualization': boolean;
  
  // Accessibility features
  'accessibility.enhanced': boolean;
  
  // Telemetry features
  'telemetry.enabled': boolean;
  
  // Debug features
  'debug.mode': boolean;
}

// Default feature flags
const defaultFeatureFlags: FeatureFlags = {
  'chat.streaming': true,
  'chat.tools': true,
  'chat.edit': false,
  'chat.quick_actions': false,
  'copilot.enabled': true,
  'voice.input': false,
  'voice.output': false,
  'attachments.enabled': true,
  'emoji.picker': true,
  'analytics.detailed': false,
  'security.sanitization': true,
  'security.rbac': false,
  'performance.virtualization': false,
  'accessibility.enhanced': true,
  'telemetry.enabled': true,
  'debug.mode': false,
};

type DeploymentPhase = 'none' | 'phase1' | 'phase2' | 'phase3' | 'phase4';

/**
 * Get feature flags with defaults applied
 */
export function getFeatureFlagsWithDefaults(): FeatureFlags {
  try {
    // Try to load from environment variables
    const envFlags = loadFromEnvironment();
    
    // Try to load from localStorage
    const localFlags = loadFromLocalStorage();
    
    // Merge with defaults
    return {
      ...defaultFeatureFlags,
      ...localFlags,
      ...envFlags,
    };
  } catch (error) {
    console.warn('Failed to load feature flags, using defaults:', error);
    return defaultFeatureFlags;
  }
}

/**
 * Check if a specific feature is enabled
 */
export function isFeatureEnabled(feature: keyof FeatureFlags): boolean {
  const flags = getFeatureFlagsWithDefaults();
  return flags[feature] ?? false;
}

/**
 * Get current deployment phase
 */
export function getCurrentDeploymentPhase(): DeploymentPhase {
  try {
    const phase = process.env.NEXT_PUBLIC_DEPLOYMENT_PHASE || 
                 localStorage.getItem('karen-deployment-phase') || 
                 'none';
    
    return phase as DeploymentPhase;
  } catch (error) {
    console.warn('Failed to get deployment phase:', error);
    return 'none';
  }
}

/**
 * Load feature flags from environment variables
 */
function loadFromEnvironment(): Partial<FeatureFlags> {
  const flags: Partial<FeatureFlags> = {};
  
  // Check environment variables for feature flags
  Object.keys(defaultFeatureFlags).forEach(key => {
    const envKey = `NEXT_PUBLIC_FEATURE_${key.toUpperCase().replace('.', '_')}`;
    const envValue = process.env[envKey];
    
    if (envValue !== undefined) {
      flags[key as keyof FeatureFlags] = envValue === 'true' || envValue === '1';
    }
  });
  
  return flags;
}

/**
 * Load feature flags from localStorage
 */
function loadFromLocalStorage(): Partial<FeatureFlags> {
  try {
    const stored = localStorage.getItem('karen-feature-flags');
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.warn('Failed to load feature flags from localStorage:', error);
  }
  
  return {};
}

/**
 * Save feature flags to localStorage
 */
export function saveFeatureFlags(flags: Partial<FeatureFlags>): void {
  try {
    const currentFlags = getFeatureFlagsWithDefaults();
    const updatedFlags = { ...currentFlags, ...flags };
    localStorage.setItem('karen-feature-flags', JSON.stringify(updatedFlags));
  } catch (error) {
    console.warn('Failed to save feature flags to localStorage:', error);
  }
}

/**
 * Set a specific feature flag
 */
export function setFeatureFlag(feature: keyof FeatureFlags, enabled: boolean): void {
  saveFeatureFlags({ [feature]: enabled });
}

/**
 * Reset all feature flags to defaults
 */
export function resetFeatureFlags(): void {
  try {
    localStorage.removeItem('karen-feature-flags');
  } catch (error) {
    console.warn('Failed to reset feature flags:', error);
  }
}

/**
 * Get all feature flags as a key-value object for debugging
 */
export function getFeatureFlagSummary(): Record<string, boolean> {
  const flags = getFeatureFlagsWithDefaults();
  const summary: Record<string, boolean> = {};
  
  Object.entries(flags).forEach(([key, value]) => {
    summary[key] = value;
  });
  
  return summary;
}