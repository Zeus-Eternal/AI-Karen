/**
 * Model and Provider Types
 * Aligned with backend schemas
 */

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  family: string;
  format: string;
  size: string | null;
  parameters: string | null;
  quantization: string | null;
  context_length: number | null;
  capabilities: string[];
  local_path: string | null;
  download_url: string | null;
  license: string | null;
  description: string;
}

export interface ProviderInfo {
  id: string;
  name: string;
  type: 'local' | 'cloud' | 'hybrid';
  status: 'active' | 'inactive' | 'error';
  models: ModelInfo[];
  capabilities: string[];
  configuration: Record<string, unknown>;
  health_status: 'healthy' | 'degraded' | 'unhealthy';
  last_check: string;
}

export interface ModelLibraryResponse {
  models: ModelInfo[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ProviderDiscoveryResponse {
  providers: ProviderInfo[];
  total_count: number;
  active_count: number;
  last_updated: string;
}

export interface ModelProviderSummary {
  provider_id: string;
  provider_name: string;
  model_count: number;
  active_models: number;
  status: string;
  capabilities: string[];
}
