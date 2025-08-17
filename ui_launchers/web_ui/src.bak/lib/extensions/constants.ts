// Extension management constants

export const EXTENSION_CATEGORIES = {
  PLUGINS: 'Plugins' as const,
  EXTENSIONS: 'Extensions' as const,
} as const;

export const PLUGIN_PROVIDER_TYPES = {
  LLM: 'llm' as const,
  VOICE: 'voice' as const,
  VIDEO: 'video' as const,
  SERVICE: 'service' as const,
} as const;

export const EXTENSION_SUBMENUS = {
  AGENTS: 'agents' as const,
  AUTOMATIONS: 'automations' as const,
  SYSTEM: 'system' as const,
} as const;

export const SYSTEM_EXTENSION_CATEGORIES = {
  ANALYTICS: 'analytics' as const,
  AUTOMATION: 'automation' as const,
  COMMUNICATION: 'communication' as const,
  DEVELOPMENT: 'development' as const,
  INTEGRATION: 'integration' as const,
  PRODUCTIVITY: 'productivity' as const,
  SECURITY: 'security' as const,
  EXPERIMENTAL: 'experimental' as const,
} as const;

export const NAVIGATION_LEVELS = {
  CATEGORY: 'category' as const,
  SUBMENU: 'submenu' as const,
  ITEMS: 'items' as const,
  SETTINGS: 'settings' as const,
} as const;

export const HEALTH_STATUS = {
  HEALTHY: 'healthy' as const,
  WARNING: 'warning' as const,
  ERROR: 'error' as const,
  UNKNOWN: 'unknown' as const,
} as const;

export const LIFECYCLE_STATUS = {
  INSTALLED: 'installed' as const,
  ENABLED: 'enabled' as const,
  DISABLED: 'disabled' as const,
  UPDATING: 'updating' as const,
  ERROR: 'error' as const,
} as const;

export const EXTENSION_EVENTS = {
  INSTALL: 'install' as const,
  UNINSTALL: 'uninstall' as const,
  ENABLE: 'enable' as const,
  DISABLE: 'disable' as const,
  CONFIGURE: 'configure' as const,
  ERROR: 'error' as const,
} as const;

export const ERROR_TYPES = {
  NETWORK: 'network' as const,
  AUTHENTICATION: 'authentication' as const,
  VALIDATION: 'validation' as const,
  PERMISSION: 'permission' as const,
  RESOURCE: 'resource' as const,
} as const;

export const AUTH_TYPES = {
  API_KEY: 'api_key' as const,
  OAUTH: 'oauth' as const,
  NONE: 'none' as const,
} as const;

export const SETTING_TYPES = {
  NUMBER: 'number' as const,
  STRING: 'string' as const,
  BOOLEAN: 'boolean' as const,
  SELECT: 'select' as const,
  MULTISELECT: 'multiselect' as const,
} as const;

export const CONTROL_TYPES = {
  BUTTON: 'button' as const,
  TOGGLE: 'toggle' as const,
  SLIDER: 'slider' as const,
} as const;

// Default values
export const DEFAULT_PAGINATION = {
  page: 1,
  limit: 20,
} as const;

export const DEFAULT_RESOURCE_LIMITS = {
  max_memory: 512, // MB
  max_cpu: 50, // percentage
  max_storage: 1024, // MB
  max_network: 1024, // KB/s
} as const;

export const DEFAULT_RATE_LIMITS = {
  requests_per_minute: 60,
  burst: 10,
} as const;

// API endpoints
export const API_ENDPOINTS = {
  EXTENSIONS: '/api/extensions',
  PLUGINS: '/api/plugins',
  PROVIDERS: '/api/llm/providers',
  LLM_PROFILES: '/api/llm/profiles',
  MODELS: '/api/models',
  MARKETPLACE: '/api/marketplace',
  HEALTH: '/api/health',
  SETTINGS: '/api/settings',
  CONTROLS: '/api/controls',
} as const;

// WebSocket events
export const WS_EVENTS = {
  EXTENSION_STATUS: 'extension_status',
  EXTENSION_INSTALLED: 'extension_installed',
  EXTENSION_UPDATED: 'extension_updated',
  EXTENSION_ERROR: 'extension_error',
} as const;

// UI constants
export const UI_CONSTANTS = {
  SIDEBAR_WIDTH: 320,
  CARD_MIN_HEIGHT: 120,
  ANIMATION_DURATION: 200,
  DEBOUNCE_DELAY: 300,
  TOAST_DURATION: 5000,
} as const;

// Color scheme for health status
export const HEALTH_COLORS = {
  healthy: 'text-green-600 bg-green-50 border-green-200',
  warning: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  error: 'text-red-600 bg-red-50 border-red-200',
  unknown: 'text-gray-600 bg-gray-50 border-gray-200',
} as const;

// Icons for different types
export const EXTENSION_ICONS = {
  // Plugin provider types
  llm: 'Brain',
  voice: 'Mic',
  video: 'Video',
  service: 'Settings',
  
  // System extension categories
  analytics: 'BarChart3',
  automation: 'Zap',
  communication: 'MessageSquare',
  development: 'Code',
  integration: 'Link',
  productivity: 'CheckSquare',
  security: 'Shield',
  experimental: 'Flask',
  
  // General
  plugin: 'Puzzle',
  extension: 'Package',
  agent: 'Bot',
  workflow: 'GitBranch',
} as const;