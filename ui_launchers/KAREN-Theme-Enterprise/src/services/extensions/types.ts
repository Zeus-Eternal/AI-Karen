// API types for extension services

export interface ExtensionAPIResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: unknown;
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
  data?: unknown;
  params?: Record<string, unknown>;
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

export interface ExtensionManifestMetadata {
  name: string;
  version: string;
  display_name: string;
  description: string;
  author: string;
  license: string;
  category: string;
  tags: string[];
  api_version?: string;
  kari_min_version?: string;
  capabilities?: Record<string, boolean>;
  resources?: Record<string, number>;
  [key: string]: unknown;
}

export interface ExtensionRegistryEntry {
  name: string;
  version: string;
  status: string;
  directory: string;
  loaded_at?: number | string | null;
  error_message?: string | null;
  manifest: ExtensionManifestMetadata;
}

export interface ExtensionRegistrySummaryResponse {
  extensions: Record<string, ExtensionRegistryEntry>;
  summary: Record<string, number>;
  total_count: number;
}

export interface ExtensionHealthSummary {
  total_extensions: number;
  healthy_extensions: number;
  unhealthy_extensions: number;
  health_percentage: number;
  last_check_times: Record<string, number>;
  extension_health: Record<string, 'green' | 'yellow' | 'red'>;
}

export interface ExtensionInstallRequest {
  extensionId: string;
  version?: string;
  config?: Record<string, unknown>;
  permissions?: string[];
}

export interface ExtensionUpdateRequest {
  extensionId: string;
  version?: string;
  config?: Record<string, unknown>;
}

export interface ExtensionConfigRequest {
  extensionId: string;
  settings: Record<string, unknown>;
  validate?: boolean;
}

export interface ExtensionControlRequest {
  extensionId: string;
  action: string;
  params?: Record<string, unknown>;
}

// WebSocket event types for real-time updates
export interface ExtensionWebSocketEvent {
  type: 'extension_status' | 'extension_installed' | 'extension_updated' | 'extension_error';
  extensionId: string;
  data: unknown;
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