/**
 * Endpoint Configuration
 * Centralized configuration for all API endpoints
 */

export interface EndpointConfig {
  baseUrl: string;
  timeout: number;
  retries: number;
  headers?: Record<string, string>;
}

export interface EndpointPaths {
  // Auth endpoints
  login: string;
  logout: string;
  register: string;
  refresh: string;
  profile: string;
  
  // Chat endpoints
  chat: string;
  chatHistory: string;
  chatStream: string;
  
  // Memory endpoints
  memories: string;
  memorySearch: string;
  memoryCreate: string;
  memoryUpdate: string;
  memoryDelete: string;
  
  // File endpoints
  files: string;
  fileUpload: string;
  fileDownload: string;
  fileDelete: string;
  
  // Analytics endpoints
  analytics: string;
  userEngagement: string;
  performance: string;
  
  // Plugin endpoints
  plugins: string;
  pluginInstall: string;
  pluginUninstall: string;
  pluginConfig: string;
  
  // Settings endpoints
  settings: string;
  preferences: string;
  
  // Health and status
  health: string;
  status: string;
  version: string;
}

export class EndpointManager {
  private config: EndpointConfig;
  private paths: EndpointPaths;

  constructor(config?: Partial<EndpointConfig>) {
    this.config = {
      baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || '/api',
      timeout: 10000,
      retries: 3,
      ...config,
    };

    this.paths = {
      // Auth endpoints
      login: '/auth/login',
      logout: '/auth/logout',
      register: '/auth/register',
      refresh: '/auth/refresh',
      profile: '/auth/profile',
      
      // Chat endpoints
      chat: '/chat',
      chatHistory: '/chat/history',
      chatStream: '/chat/stream',
      
      // Memory endpoints
      memories: '/memory',
      memorySearch: '/memory/search',
      memoryCreate: '/memory',
      memoryUpdate: '/memory/:id',
      memoryDelete: '/memory/:id',
      
      // File endpoints
      files: '/files',
      fileUpload: '/files/upload',
      fileDownload: '/files/:id/download',
      fileDelete: '/files/:id',
      
      // Analytics endpoints
      analytics: '/analytics',
      userEngagement: '/analytics/engagement',
      performance: '/analytics/performance',
      
      // Plugin endpoints
      plugins: '/plugins',
      pluginInstall: '/plugins/install',
      pluginUninstall: '/plugins/:id/uninstall',
      pluginConfig: '/plugins/:id/config',
      
      // Settings endpoints
      settings: '/settings',
      preferences: '/settings/preferences',
      
      // Health and status
      health: '/health',
      status: '/status',
      version: '/version',
    };
  }

  /**
   * Get full URL for an endpoint path
   */
  getUrl(path: keyof EndpointPaths, params?: Record<string, string>): string {
    const endpointPath = this.paths[path];
    let fullPath = endpointPath;

    // Replace path parameters
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        fullPath = fullPath.replace(`:${key}`, value);
      });
    }

    return `${this.config.baseUrl}${fullPath}`;
  }

  /**
   * Get endpoint configuration
   */
  getConfig(): EndpointConfig {
    return { ...this.config };
  }

  /**
   * Update endpoint configuration
   */
  updateConfig(newConfig: Partial<EndpointConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Get all endpoint paths
   */
  getPaths(): EndpointPaths {
    return { ...this.paths };
  }

  /**
   * Check if endpoint requires authentication
   */
  requiresAuth(path: keyof EndpointPaths): boolean {
    const publicEndpoints = [
      'health',
      'status',
      'version',
      'login',
      'register',
    ];

    return !publicEndpoints.includes(path);
  }

  /**
   * Get HTTP method for an endpoint
   */
  getHttpMethod(path: keyof EndpointPaths): 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' {
    const methodMap: Partial<Record<keyof EndpointPaths, 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'>> = {
      login: 'POST',
      logout: 'POST',
      register: 'POST',
      refresh: 'POST',
      chat: 'POST',
      chatStream: 'POST',
      memoryCreate: 'POST',
      memoryUpdate: 'PUT',
      memoryDelete: 'DELETE',
      fileUpload: 'POST',
      fileDownload: 'GET',
      fileDelete: 'DELETE',
      pluginInstall: 'POST',
      pluginUninstall: 'DELETE',
      pluginConfig: 'GET',
    };

    return methodMap[path] || 'GET';
  }

  /**
   * Get cache configuration for an endpoint
   */
  getCacheConfig(path: keyof EndpointPaths): { ttl: number; enabled: boolean } {
    const cacheConfig: Partial<Record<keyof EndpointPaths, { ttl: number; enabled: boolean }>> = {
      health: { ttl: 30, enabled: true },
      status: { ttl: 30, enabled: true },
      version: { ttl: 3600, enabled: true },
      profile: { ttl: 300, enabled: true },
      plugins: { ttl: 600, enabled: true },
      settings: { ttl: 300, enabled: true },
      preferences: { ttl: 300, enabled: true },
    };

    return cacheConfig[path] || { ttl: 0, enabled: false };
  }
}

// Default endpoint manager instance
export const endpointManager = new EndpointManager();

// Environment-specific configurations
export const getEndpointConfig = (): EndpointConfig => {
  const isDevelopment = process.env.NODE_ENV === 'development';
  const isTest = process.env.NODE_ENV === 'test';

  if (isTest) {
    return {
      baseUrl: 'http://localhost:3001/api',
      timeout: 5000,
      retries: 1,
    };
  }

  if (isDevelopment) {
    return {
      baseUrl: 'http://localhost:9002/api',
      timeout: 10000,
      retries: 3,
    };
  }

  // Production
  return {
    baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || '/api',
    timeout: 15000,
    retries: 3,
    headers: {
      'X-Client-Version': process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
    },
  };
};

// Initialize endpoint manager with environment config
endpointManager.updateConfig(getEndpointConfig());

// Utility functions for common endpoint operations
export const endpoints = {
  // Auth
  login: (params?: Record<string, string>) => endpointManager.getUrl('login', params),
  logout: (params?: Record<string, string>) => endpointManager.getUrl('logout', params),
  register: (params?: Record<string, string>) => endpointManager.getUrl('register', params),
  refresh: (params?: Record<string, string>) => endpointManager.getUrl('refresh', params),
  profile: (params?: Record<string, string>) => endpointManager.getUrl('profile', params),
  
  // Chat
  chat: (params?: Record<string, string>) => endpointManager.getUrl('chat', params),
  chatHistory: (params?: Record<string, string>) => endpointManager.getUrl('chatHistory', params),
  chatStream: (params?: Record<string, string>) => endpointManager.getUrl('chatStream', params),
  
  // Memory
  memories: (params?: Record<string, string>) => endpointManager.getUrl('memories', params),
  memorySearch: (params?: Record<string, string>) => endpointManager.getUrl('memorySearch', params),
  memoryCreate: (params?: Record<string, string>) => endpointManager.getUrl('memoryCreate', params),
  memoryUpdate: (id: string) => endpointManager.getUrl('memoryUpdate', { id }),
  memoryDelete: (id: string) => endpointManager.getUrl('memoryDelete', { id }),
  
  // Files
  files: (params?: Record<string, string>) => endpointManager.getUrl('files', params),
  fileUpload: (params?: Record<string, string>) => endpointManager.getUrl('fileUpload', params),
  fileDownload: (id: string) => endpointManager.getUrl('fileDownload', { id }),
  fileDelete: (id: string) => endpointManager.getUrl('fileDelete', { id }),
  
  // Analytics
  analytics: (params?: Record<string, string>) => endpointManager.getUrl('analytics', params),
  userEngagement: (params?: Record<string, string>) => endpointManager.getUrl('userEngagement', params),
  performance: (params?: Record<string, string>) => endpointManager.getUrl('performance', params),
  
  // Plugins
  plugins: (params?: Record<string, string>) => endpointManager.getUrl('plugins', params),
  pluginInstall: (params?: Record<string, string>) => endpointManager.getUrl('pluginInstall', params),
  pluginUninstall: (id: string) => endpointManager.getUrl('pluginUninstall', { id }),
  pluginConfig: (id: string) => endpointManager.getUrl('pluginConfig', { id }),
  
  // Settings
  settings: (params?: Record<string, string>) => endpointManager.getUrl('settings', params),
  preferences: (params?: Record<string, string>) => endpointManager.getUrl('preferences', params),
  
  // Health and status
  health: (params?: Record<string, string>) => endpointManager.getUrl('health', params),
  status: (params?: Record<string, string>) => endpointManager.getUrl('status', params),
  version: (params?: Record<string, string>) => endpointManager.getUrl('version', params),
};