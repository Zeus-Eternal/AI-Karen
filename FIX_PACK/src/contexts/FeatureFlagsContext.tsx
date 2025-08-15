'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { FeatureFlag } from '@/hooks/use-feature';
import { useTelemetry } from '@/hooks/use-telemetry';
import { 
  mergeWithEnvironmentDefaults,
  loadConfigFromEnvironment,
  loadConfigFromStorage,
  saveConfigToStorage,
  validateFeatureFlagConfig,
  createConfigUpdater
} from '@/lib/featureFlagConfig';
import { getFeatureFlagTester } from '@/lib/featureFlagTesting';

interface FeatureFlagsContextType {
  flags: Record<FeatureFlag, boolean>;
  isEnabled: (flag: FeatureFlag) => boolean;
  enable: (flag: FeatureFlag) => void;
  disable: (flag: FeatureFlag) => void;
  toggle: (flag: FeatureFlag) => void;
  setFlags: (flags: Partial<Record<FeatureFlag, boolean>>) => void;
  reset: () => void;
  validate: (flags?: Partial<Record<FeatureFlag, boolean>>) => { isValid: boolean; errors: string[]; warnings: string[] };
  updateConfig: (flags: Partial<Record<FeatureFlag, boolean>>) => Promise<boolean>;
}

export const FeatureFlagsContext = createContext<FeatureFlagsContextType | null>(null);

// Initialize flags using the configuration management system
const initializeFlags = (
  initialFlags: Partial<Record<FeatureFlag, boolean>> = {},
  persistToStorage: boolean = true
): Record<FeatureFlag, boolean> => {
  // Load from environment variables
  const envFlags = loadConfigFromEnvironment();
  
  // Load from localStorage if persistence is enabled
  let storedFlags: Partial<Record<FeatureFlag, boolean>> = {};
  if (persistToStorage) {
    storedFlags = loadConfigFromStorage() || {};
  }
  
  // Merge all configurations with proper precedence
  const mergedConfig = {
    ...envFlags,
    ...storedFlags,
    ...initialFlags
  };
  
  // Apply environment defaults and validation
  return mergeWithEnvironmentDefaults(mergedConfig);
};

interface FeatureFlagsProviderProps {
  children: ReactNode;
  initialFlags?: Partial<Record<FeatureFlag, boolean>>;
  persistToStorage?: boolean;
}

export const FeatureFlagsProvider: React.FC<FeatureFlagsProviderProps> = ({
  children,
  initialFlags = {},
  persistToStorage = true
}) => {
  const { track } = useTelemetry();
  
  // Initialize flags using the configuration management system
  const [flags, setFlagsState] = useState<Record<FeatureFlag, boolean>>(() => 
    initializeFlags(initialFlags, persistToStorage)
  );

  // Persist flags to localStorage when they change (with validation)
  useEffect(() => {
    if (persistToStorage) {
      saveConfigToStorage(flags);
    }
  }, [flags, persistToStorage]);

  // Track feature flag usage
  const trackFlagUsage = (flag: FeatureFlag, enabled: boolean, action: string) => {
    track('feature_flag_used', {
      flag,
      enabled,
      action,
      timestamp: new Date().toISOString()
    });
  };

  const isEnabled = (flag: FeatureFlag): boolean => {
    const startTime = performance.now();
    
    // Check for test overrides first
    const tester = getFeatureFlagTester();
    const override = tester.getOverride(flag);
    
    const enabled = override !== null ? override : (flags[flag] ?? false);
    
    // Track usage for analytics
    tester.trackUsage(flag, enabled, 'context-check');
    
    // Track performance
    const checkTime = performance.now() - startTime;
    tester.trackPerformance(flag, checkTime);
    
    // Track flag check (throttled to avoid spam)
    if (Math.random() < 0.01) { // 1% sampling
      trackFlagUsage(flag, enabled, 'check');
    }
    
    return enabled;
  };

  // Create configuration updater with validation
  const configUpdater = createConfigUpdater((newFlags) => {
    setFlagsState(prev => ({ ...prev, ...newFlags }));
  });

  const enable = (flag: FeatureFlag) => {
    try {
      configUpdater.updateFlag(flag, true);
      trackFlagUsage(flag, true, 'enable');
    } catch (error) {
      console.error(`Failed to enable flag '${flag}':`, error);
      throw error;
    }
  };

  const disable = (flag: FeatureFlag) => {
    try {
      configUpdater.updateFlag(flag, false);
      trackFlagUsage(flag, false, 'disable');
    } catch (error) {
      console.error(`Failed to disable flag '${flag}':`, error);
      throw error;
    }
  };

  const toggle = (flag: FeatureFlag) => {
    const newValue = !flags[flag];
    try {
      configUpdater.updateFlag(flag, newValue);
      trackFlagUsage(flag, newValue, 'toggle');
    } catch (error) {
      console.error(`Failed to toggle flag '${flag}':`, error);
      throw error;
    }
  };

  const setFlags = (newFlags: Partial<Record<FeatureFlag, boolean>>) => {
    try {
      configUpdater.updateFlags(newFlags);
      
      Object.entries(newFlags).forEach(([flag, enabled]) => {
        trackFlagUsage(flag as FeatureFlag, enabled!, 'batch_set');
      });
    } catch (error) {
      console.error('Failed to set flags:', error);
      throw error;
    }
  };

  const reset = () => {
    try {
      configUpdater.resetToDefaults();
      
      track('feature_flags_reset', {
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('Failed to reset flags:', error);
      throw error;
    }
  };

  const validate = (flagsToValidate?: Partial<Record<FeatureFlag, boolean>>) => {
    return validateFeatureFlagConfig(flagsToValidate || flags);
  };

  const updateConfig = async (newFlags: Partial<Record<FeatureFlag, boolean>>): Promise<boolean> => {
    try {
      const validation = validateFeatureFlagConfig(newFlags);
      
      if (!validation.isValid) {
        console.error('Invalid configuration:', validation.errors);
        return false;
      }

      if (validation.warnings.length > 0) {
        console.warn('Configuration warnings:', validation.warnings);
      }

      setFlags(newFlags);
      
      track('feature_flags_config_updated', {
        flags: Object.keys(newFlags),
        timestamp: new Date().toISOString()
      });

      return true;
    } catch (error) {
      console.error('Failed to update configuration:', error);
      return false;
    }
  };

  const contextValue: FeatureFlagsContextType = {
    flags,
    isEnabled,
    enable,
    disable,
    toggle,
    setFlags,
    reset,
    validate,
    updateConfig
  };

  return (
    <FeatureFlagsContext.Provider value={contextValue}>
      {children}
    </FeatureFlagsContext.Provider>
  );
};

// Utility hook for accessing feature flags context
export const useFeatureFlags = () => {
  const context = useContext(FeatureFlagsContext);
  
  if (!context) {
    throw new Error('useFeatureFlags must be used within a FeatureFlagsProvider');
  }
  
  return context;
};

// Component for conditionally rendering based on feature flags
interface FeatureGateProps {
  feature: FeatureFlag;
  fallback?: ReactNode;
  children: ReactNode;
}

export const FeatureGate: React.FC<FeatureGateProps> = ({
  feature,
  fallback = null,
  children
}) => {
  const { isEnabled } = useFeatureFlags();
  
  return isEnabled(feature) ? <>{children}</> : <>{fallback}</>;
};

export default FeatureFlagsProvider;