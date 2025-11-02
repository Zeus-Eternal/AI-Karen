// API types for extension services

export interface ExtensionAPIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    total?: number;
    page?: number;
    limit?: number;
  };
}

export interface ExtensionAPIRequest {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  endpoint: string;
  data?: any;
  params?: Record<string, any>;
  headers?: Record<string, string>;
}

export interface ExtensionQueryParams {
  page?: number;
  limit?: number;
  search?: string;
  category?: string;
  type?: string;
  enabled?: boolean;
  sort?: string;
  order?: 'asc' | 'desc';
}

export interface ExtensionInstallRequest {
  extensionId: string;
  version?: string;
  config?: Record<string, any>;
  permissions?: string[];
}

export interface ExtensionUpdateRequest {
  extensionId: string;
  version?: string;
  config?: Record<string, any>;
}

export interface ExtensionConfigRequest {
  extensionId: string;
  settings: Record<string, any>;
  validate?: boolean;
}

export interface ExtensionControlRequest {
  extensionId: string;
  action: string;
  params?: Record<string, any>;
}

// WebSocket event types for real-time updates
export interface ExtensionWebSocketEvent {
  type: 'extension_status' | 'extension_installed' | 'extension_updated' | 'extension_error';
  extensionId: string;
  data: any;
  timestamp: string;
}

// Cache configuration
export interface ExtensionCacheConfig {
  extensions: { ttl: number };
  providers: { ttl: number };
  models: { ttl: number };
  settings: { ttl: number };
  health: { ttl: number };
}

export const DEFAULT_CACHE_CONFIG: ExtensionCacheConfig = {
  extensions: { ttl: 300000 }, // 5 minutes
  providers: { ttl: 600000 }, // 10 minutes
  models: { ttl: 900000 }, // 15 minutes
  settings: { ttl: 60000 }, // 1 minute
  health: { ttl: 30000 }, // 30 seconds
};