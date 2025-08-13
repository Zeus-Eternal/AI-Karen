// Configuration management for shared UI components
// Provides default configurations and environment-specific overrides

import { ComponentConfig } from './interfaces';
import { KarenSettings } from './types';

// Default component configuration
export const DEFAULT_COMPONENT_CONFIG: ComponentConfig = {
  apiBaseUrl: process.env.KAREN_API_URL || 'http://localhost:8000',
  enableVoice: true,
  enableAnalytics: true,
  defaultTheme: 'light',
  maxMessageHistory: 1000,
  autoSaveSettings: true,
  debugMode: process.env.NODE_ENV === 'development'
};

// Default Karen settings
export const DEFAULT_KAREN_SETTINGS: KarenSettings = {
  memoryDepth: 'medium',
  personalityTone: 'friendly',
  personalityVerbosity: 'balanced',
  personalFacts: [],
  notifications: {
    enabled: true,
    alertOnNewInsights: true,
    alertOnSummaryReady: true
  },
  ttsVoiceURI: null,
  customPersonaInstructions: '',
  temperatureUnit: 'C',
  weatherService: 'wttr_in',
  weatherApiKey: null,
  defaultWeatherLocation: null,
  activeListenMode: false
};

// Environment-specific configurations
export const DEVELOPMENT_CONFIG: Partial<ComponentConfig> = {
  debugMode: true,
  apiBaseUrl: 'http://localhost:8000',
  enableAnalytics: false
};

export const PRODUCTION_CONFIG: Partial<ComponentConfig> = {
  debugMode: false,
  enableAnalytics: true,
  autoSaveSettings: true
};

export const TEST_CONFIG: Partial<ComponentConfig> = {
  debugMode: true,
  enableVoice: false,
  enableAnalytics: false,
  apiBaseUrl: 'http://localhost:3001',
  maxMessageHistory: 10
};

// Framework-specific configurations
export const REACT_CONFIG: Partial<ComponentConfig> = {
  // React-specific overrides
};

export const STREAMLIT_CONFIG: Partial<ComponentConfig> = {
  enableVoice: false, // Streamlit has limited voice support
  defaultTheme: 'light' // Streamlit themes are more limited
};

export const TAURI_CONFIG: Partial<ComponentConfig> = {
  // Tauri-specific overrides
  enableAnalytics: true // Desktop app can have more detailed analytics
};

// Configuration factory
export function createConfig(
  framework: 'react' | 'streamlit' | 'tauri',
  environment: 'development' | 'production' | 'test' = 'production',
  overrides: Partial<ComponentConfig> = {}
): ComponentConfig {
  let config = { ...DEFAULT_COMPONENT_CONFIG };
  
  // Apply environment-specific config
  switch (environment) {
    case 'development':
      config = { ...config, ...DEVELOPMENT_CONFIG };
      break;
    case 'production':
      config = { ...config, ...PRODUCTION_CONFIG };
      break;
    case 'test':
      config = { ...config, ...TEST_CONFIG };
      break;
  }
  
  // Apply framework-specific config
  switch (framework) {
    case 'react':
      config = { ...config, ...REACT_CONFIG };
      break;
    case 'streamlit':
      config = { ...config, ...STREAMLIT_CONFIG };
      break;
    case 'tauri':
      config = { ...config, ...TAURI_CONFIG };
      break;
  }
  
  // Apply custom overrides
  config = { ...config, ...overrides };
  
  return config;
}

// Configuration validation
export function validateConfig(config: ComponentConfig): string[] {
  const errors: string[] = [];
  
  if (!config.apiBaseUrl || typeof config.apiBaseUrl !== 'string') {
    errors.push('apiBaseUrl is required and must be a string');
  }
  
  if (config.apiBaseUrl && !isValidUrl(config.apiBaseUrl)) {
    errors.push('apiBaseUrl must be a valid URL');
  }
  
  if (typeof config.enableVoice !== 'boolean') {
    errors.push('enableVoice must be a boolean');
  }
  
  if (typeof config.enableAnalytics !== 'boolean') {
    errors.push('enableAnalytics must be a boolean');
  }
  
  if (!config.defaultTheme || typeof config.defaultTheme !== 'string') {
    errors.push('defaultTheme is required and must be a string');
  }
  
  if (typeof config.maxMessageHistory !== 'number' || config.maxMessageHistory <= 0) {
    errors.push('maxMessageHistory must be a positive number');
  }
  
  if (typeof config.autoSaveSettings !== 'boolean') {
    errors.push('autoSaveSettings must be a boolean');
  }
  
  if (typeof config.debugMode !== 'boolean') {
    errors.push('debugMode must be a boolean');
  }
  
  return errors;
}

// Helper function to check if URL is valid
function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

// Configuration constants
export const STORAGE_KEYS = {
  SETTINGS: 'karen-settings',
  THEME: 'karen-theme',
  MESSAGES: 'karen-messages',
  PLUGINS: 'karen-plugins',
  MEMORY: 'karen-memory',
  ANALYTICS: 'karen-analytics'
} as const;

export const API_ENDPOINTS = {
  CHAT: '/api/ai/conversation-processing',
  MEMORY_STORE: '/api/memory/store',
  MEMORY_QUERY: '/api/memory/query',
  MEMORY_CONTEXT: '/api/memory/context',
  MEMORY_STATS: '/api/memory/stats',
  PLUGINS_LIST: '/api/plugins',
  PLUGINS_EXECUTE: '/api/plugins/execute',
  PLUGINS_INFO: '/api/plugins',
  PLUGINS_VALIDATE: '/api/plugins/validate',
  ANALYTICS_TRACK: '/api/analytics/track',
  ANALYTICS_METRICS: '/api/analytics/metrics',
  ANALYTICS_EXPORT: '/api/analytics/export'
} as const;

export const THEME_NAMES = {
  LIGHT: 'light',
  DARK: 'dark',
  HIGH_CONTRAST: 'high-contrast',
  CUSTOM: 'custom'
} as const;

export const COMPONENT_TYPES = {
  CHAT: 'chat',
  SETTINGS: 'settings',
  PLUGINS: 'plugins',
  MEMORY: 'memory',
  ANALYTICS: 'analytics'
} as const;

export const EVENT_TYPES = {
  MESSAGE_SENT: 'message_sent',
  MESSAGE_RECEIVED: 'message_received',
  RECORDING_STARTED: 'recording_started',
  RECORDING_STOPPED: 'recording_stopped',
  SETTINGS_CHANGED: 'settings_changed',
  SETTINGS_SAVED: 'settings_saved',
  THEME_CHANGED: 'theme_changed',
  PLUGIN_EXECUTED: 'plugin_executed',
  MEMORY_STORED: 'memory_stored',
  MEMORY_QUERIED: 'memory_queried',
  ERROR_OCCURRED: 'error_occurred'
} as const;

// Feature flags for gradual rollout
export const FEATURE_FLAGS = {
  VOICE_INPUT: 'voice_input',
  MEMORY_VISUALIZATION: 'memory_visualization',
  ADVANCED_ANALYTICS: 'advanced_analytics',
  PLUGIN_MARKETPLACE: 'plugin_marketplace',
  REAL_TIME_COLLABORATION: 'real_time_collaboration',
  CUSTOM_THEMES: 'custom_themes',
  EXPORT_CONVERSATIONS: 'export_conversations',
  CONVERSATION_SEARCH: 'conversation_search'
} as const;

// Default feature flag states
export const DEFAULT_FEATURE_FLAGS: Record<string, boolean> = {
  [FEATURE_FLAGS.VOICE_INPUT]: true,
  [FEATURE_FLAGS.MEMORY_VISUALIZATION]: false,
  [FEATURE_FLAGS.ADVANCED_ANALYTICS]: false,
  [FEATURE_FLAGS.PLUGIN_MARKETPLACE]: false,
  [FEATURE_FLAGS.REAL_TIME_COLLABORATION]: false,
  [FEATURE_FLAGS.CUSTOM_THEMES]: true,
  [FEATURE_FLAGS.EXPORT_CONVERSATIONS]: true,
  [FEATURE_FLAGS.CONVERSATION_SEARCH]: false
};

// Performance configuration
export const PERFORMANCE_CONFIG = {
  DEBOUNCE_DELAY: 300,
  THROTTLE_LIMIT: 100,
  MAX_CONCURRENT_REQUESTS: 5,
  REQUEST_TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
  CACHE_TTL: 300000, // 5 minutes
  MAX_CACHE_SIZE: 100
} as const;

// Accessibility configuration
export const ACCESSIBILITY_CONFIG = {
  HIGH_CONTRAST_RATIO: 4.5,
  FOCUS_OUTLINE_WIDTH: '2px',
  KEYBOARD_NAV_DELAY: 100,
  SCREEN_READER_DELAY: 500,
  ANIMATION_DURATION: 200,
  REDUCED_MOTION: false
} as const;

// Security configuration
export const SECURITY_CONFIG = {
  MAX_MESSAGE_LENGTH: 10000,
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_FILE_TYPES: [
    'text/plain',
    'text/markdown',
    'application/json',
    'image/png',
    'image/jpeg',
    'image/gif',
    'image/webp'
  ],
  SANITIZE_HTML: true,
  VALIDATE_URLS: true,
  RATE_LIMIT_REQUESTS: 100,
  RATE_LIMIT_WINDOW: 60000 // 1 minute
} as const;