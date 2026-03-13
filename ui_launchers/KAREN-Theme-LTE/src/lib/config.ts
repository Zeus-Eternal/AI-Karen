/**
 * Application Configuration
 * Centralized configuration for the KAREN Theme Default application
 */

export interface AppConfig {
  // Application metadata
  name: string;
  version: string;
  description: string;
  author: string;
  
  // API configuration
  api: {
    baseUrl: string;
    timeout: number;
    retries: number;
    enableRetry: boolean;
  };
  
  // Feature flags
  features: {
    enableVoiceInput: boolean;
    enableVoiceOutput: boolean;
    enableMemoryManagement: boolean;
    enableFileManagement: boolean;
    enableAnalytics: boolean;
    enablePlugins: boolean;
    enablePerformanceMonitoring: boolean;
    enableAccessibilityFeatures: boolean;
    enableOfflineMode: boolean;
    enableRealTimeUpdates: boolean;
  };
  
  // UI configuration
  ui: {
    theme: {
      defaultTheme: 'light' | 'dark' | 'system';
      enableCustomThemes: boolean;
      enableThemeAnimation: boolean;
    };
    layout: {
      sidebarWidth: number;
      sidebarCollapsedWidth: number;
      headerHeight: number;
      footerHeight: number;
      enableResizableSidebar: boolean;
    };
    animations: {
      enableAnimations: boolean;
      animationDuration: number;
      enableReducedMotion: boolean;
    };
  };
  
  // Performance configuration
  performance: {
    enableLazyLoading: boolean;
    enableCodeSplitting: boolean;
    enableCaching: boolean;
    cacheTimeout: number;
    enableServiceWorker: boolean;
    enablePerformanceMonitoring: boolean;
    bundleAnalysisEnabled: boolean;
  };
  
  // Security configuration
  security: {
    enableCSRFProtection: boolean;
    enableXSSProtection: boolean;
    enableContentSecurityPolicy: boolean;
    sessionTimeout: number;
    enableRateLimiting: boolean;
  };
  
  // Accessibility configuration
  accessibility: {
    enableScreenReaderSupport: boolean;
    enableKeyboardNavigation: boolean;
    enableHighContrastMode: boolean;
    enableFocusManagement: boolean;
    wcagLevel: 'AA' | 'AAA';
  };
  
  // Development configuration
  development: {
    enableDebugMode: boolean;
    enableDevTools: boolean;
    enableHotReload: boolean;
    enableSourceMaps: boolean;
    logLevel: 'error' | 'warn' | 'info' | 'debug';
  };
}

/**
 * Default application configuration
 */
export const defaultConfig: AppConfig = {
  // Application metadata
  name: 'KAREN AI',
  version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  description: 'Intelligent AI assistant with modern interface',
  author: 'KAREN Development Team',
  
  // API configuration
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || '/api',
    timeout: 10000,
    retries: 3,
    enableRetry: true,
  },
  
  // Feature flags
  features: {
    enableVoiceInput: process.env.NEXT_PUBLIC_ENABLE_VOICE_INPUT !== 'false',
    enableVoiceOutput: process.env.NEXT_PUBLIC_ENABLE_VOICE_OUTPUT !== 'false',
    enableMemoryManagement: process.env.NEXT_PUBLIC_ENABLE_MEMORY_MANAGEMENT !== 'false',
    enableFileManagement: process.env.NEXT_PUBLIC_ENABLE_FILE_MANAGEMENT !== 'false',
    enableAnalytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS !== 'false',
    enablePlugins: process.env.NEXT_PUBLIC_ENABLE_PLUGINS !== 'false',
    enablePerformanceMonitoring: process.env.NEXT_PUBLIC_ENABLE_PERFORMANCE_MONITORING !== 'false',
    enableAccessibilityFeatures: process.env.NEXT_PUBLIC_ENABLE_ACCESSIBILITY !== 'false',
    enableOfflineMode: process.env.NEXT_PUBLIC_ENABLE_OFFLINE_MODE !== 'false',
    enableRealTimeUpdates: process.env.NEXT_PUBLIC_ENABLE_REAL_TIME_UPDATES !== 'false',
  },
  
  // UI configuration
  ui: {
    theme: {
      defaultTheme: (process.env.NEXT_PUBLIC_DEFAULT_THEME as 'light' | 'dark' | 'system') || 'system',
      enableCustomThemes: true,
      enableThemeAnimation: true,
    },
    layout: {
      sidebarWidth: 256,
      sidebarCollapsedWidth: 64,
      headerHeight: 64,
      footerHeight: 48,
      enableResizableSidebar: true,
    },
    animations: {
      enableAnimations: process.env.NEXT_PUBLIC_ENABLE_ANIMATIONS !== 'false',
      animationDuration: 300,
      enableReducedMotion: false,
    },
  },
  
  // Performance configuration
  performance: {
    enableLazyLoading: true,
    enableCodeSplitting: true,
    enableCaching: true,
    cacheTimeout: 300000, // 5 minutes
    enableServiceWorker: process.env.NODE_ENV === 'production',
    enablePerformanceMonitoring: true,
    bundleAnalysisEnabled: process.env.NODE_ENV === 'development',
  },
  
  // Security configuration
  security: {
    enableCSRFProtection: true,
    enableXSSProtection: true,
    enableContentSecurityPolicy: process.env.NODE_ENV === 'production',
    sessionTimeout: 3600000, // 1 hour
    enableRateLimiting: true,
  },
  
  // Accessibility configuration
  accessibility: {
    enableScreenReaderSupport: true,
    enableKeyboardNavigation: true,
    enableHighContrastMode: true,
    enableFocusManagement: true,
    wcagLevel: 'AA',
  },
  
  // Development configuration
  development: {
    enableDebugMode: process.env.NODE_ENV === 'development',
    enableDevTools: process.env.NODE_ENV === 'development',
    enableHotReload: process.env.NODE_ENV === 'development',
    enableSourceMaps: process.env.NODE_ENV === 'development',
    logLevel: (process.env.NEXT_PUBLIC_LOG_LEVEL as 'error' | 'warn' | 'info' | 'debug') || 
               (process.env.NODE_ENV === 'development' ? 'debug' : 'error'),
  },
};

/**
 * Environment-specific configurations
 */
export const getEnvironmentConfig = (): Partial<AppConfig> => {
  const isDevelopment = process.env.NODE_ENV === 'development';
  const isTest = process.env.NODE_ENV === 'test';
  const isProduction = process.env.NODE_ENV === 'production';

  if (isTest) {
    return {
      api: {
        baseUrl: 'http://localhost:3001/api',
        timeout: 5000,
        retries: 1,
        enableRetry: false,
      },
      features: {
        enableVoiceInput: false,
        enableVoiceOutput: false,
        enableMemoryManagement: false,
        enableFileManagement: false,
        enableAnalytics: false,
        enablePlugins: false,
        enablePerformanceMonitoring: false,
        enableAccessibilityFeatures: false,
        enableOfflineMode: false,
        enableRealTimeUpdates: false,
      },
      performance: {
        enableLazyLoading: false,
        enableCodeSplitting: false,
        enableCaching: false,
        cacheTimeout: 0,
        enableServiceWorker: false,
        enablePerformanceMonitoring: false,
        bundleAnalysisEnabled: false,
      },
      development: {
        enableDebugMode: false,
        enableDevTools: false,
        enableHotReload: false,
        enableSourceMaps: false,
        logLevel: 'error',
      },
    };
  }

  if (isDevelopment) {
    return {
      api: {
        baseUrl: 'http://localhost:9002/api',
        timeout: 10000,
        retries: 3,
        enableRetry: true,
      },
      development: {
        enableDebugMode: true,
        enableDevTools: true,
        enableHotReload: true,
        enableSourceMaps: true,
        logLevel: 'debug',
      },
    };
  }

  if (isProduction) {
    return {
      performance: {
        enableLazyLoading: true,
        enableCodeSplitting: true,
        enableCaching: true,
        cacheTimeout: 300000,
        enableServiceWorker: true,
        enablePerformanceMonitoring: true,
        bundleAnalysisEnabled: false,
      },
      security: {
        enableCSRFProtection: true,
        enableXSSProtection: true,
        enableContentSecurityPolicy: true,
        sessionTimeout: 3600000,
        enableRateLimiting: true,
      },
      development: {
        enableDebugMode: false,
        enableDevTools: false,
        enableHotReload: false,
        enableSourceMaps: false,
        logLevel: 'error',
      },
    };
  }

  return {};
};

/**
 * Get merged configuration
 */
export const getConfig = (): AppConfig => {
  const environmentConfig = getEnvironmentConfig();
  
  return {
    ...defaultConfig,
    ...environmentConfig,
    api: {
      ...defaultConfig.api,
      ...environmentConfig.api,
    },
    features: {
      ...defaultConfig.features,
      ...environmentConfig.features,
    },
    ui: {
      ...defaultConfig.ui,
      ...environmentConfig.ui,
      theme: {
        ...defaultConfig.ui.theme,
        ...environmentConfig.ui?.theme,
      },
      layout: {
        ...defaultConfig.ui.layout,
        ...environmentConfig.ui?.layout,
      },
      animations: {
        ...defaultConfig.ui.animations,
        ...environmentConfig.ui?.animations,
      },
    },
    performance: {
      ...defaultConfig.performance,
      ...environmentConfig.performance,
    },
    security: {
      ...defaultConfig.security,
      ...environmentConfig.security,
    },
    accessibility: {
      ...defaultConfig.accessibility,
      ...environmentConfig.accessibility,
    },
    development: {
      ...defaultConfig.development,
      ...environmentConfig.development,
    },
  };
};

/**
 * Configuration validation
 */
export const validateConfig = (config: AppConfig): boolean => {
  try {
    // Validate API configuration
    if (!config.api.baseUrl || typeof config.api.baseUrl !== 'string') {
      console.error('Invalid API base URL');
      return false;
    }

    if (config.api.timeout <= 0) {
      console.error('Invalid API timeout');
      return false;
    }

    // Validate feature flags
    Object.entries(config.features).forEach(([key, value]) => {
      if (typeof value !== 'boolean') {
        console.error(`Invalid feature flag for ${key}: expected boolean`);
      }
    });

    // Validate UI configuration
    if (config.ui.layout.sidebarWidth <= 0) {
      console.error('Invalid sidebar width');
      return false;
    }

    // Validate security configuration
    if (config.security.sessionTimeout <= 0) {
      console.error('Invalid session timeout');
      return false;
    }

    return true;
  } catch (error) {
    console.error('Configuration validation error:', error);
    return false;
  }
};

/**
 * Get configuration value with fallback
 */
export const getConfigValue = <T extends keyof AppConfig>(
  key: T,
  fallback?: AppConfig[T]
): AppConfig[T] => {
  const config = getConfig();
  return config[key] || fallback || defaultConfig[key];
};

/**
 * Check if a feature is enabled
 */
export const isFeatureEnabled = (feature: keyof AppConfig['features']): boolean => {
  const config = getConfig();
  return config.features[feature];
};

/**
 * Get API configuration
 */
export const getApiConfig = () => {
  const config = getConfig();
  return config.api;
};

/**
 * Get UI configuration
 */
export const getUiConfig = () => {
  const config = getConfig();
  return config.ui;
};

/**
 * Get performance configuration
 */
export const getPerformanceConfig = () => {
  const config = getConfig();
  return config.performance;
};

/**
 * Get security configuration
 */
export const getSecurityConfig = () => {
  const config = getConfig();
  return config.security;
};

/**
 * Get accessibility configuration
 */
export const getAccessibilityConfig = () => {
  const config = getConfig();
  return config.accessibility;
};

/**
 * Get development configuration
 */
export const getDevelopmentConfig = () => {
  const config = getConfig();
  return config.development;
};

// Export the current configuration
export const config = getConfig();