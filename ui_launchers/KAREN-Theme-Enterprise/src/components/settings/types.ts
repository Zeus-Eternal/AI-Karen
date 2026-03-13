export interface LLMProvider {
  name: string;
  description: string;
  category: string;
  requires_api_key: boolean;
  capabilities: string[];
  is_llm_provider: boolean;
  provider_type: "remote" | "local" | "hybrid";
  health_status: "healthy" | "unhealthy" | "unknown";
  error_message?: string;
  last_health_check?: number;
  cached_models_count: number;
  last_discovery?: number;
  api_base_url?: string;
  icon?: string;
  documentation_url?: string;
  pricing_info?: {
    input_cost_per_1k?: number;
    output_cost_per_1k?: number;
    currency?: string;
  };
}

export interface ModelInfo {
  id: string;
  name: string;
  family: string;
  format?: string;
  size?: number;
  parameters?: string;
  quantization?: string;
  context_length?: number;
  capabilities: string[];
  local_path?: string;
  download_url?: string;
  downloads?: number;
  likes?: number;
  provider: string;
  runtime_compatibility?: string[];
  tags?: string[];
  license?: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface LLMProfile {
  id: string;
  name: string;
  description: string;
  router_policy: "balanced" | "performance" | "cost" | "privacy" | "custom";
  providers: Record<
    string,
    {
      provider: string;
      model?: string;
      priority: number;
      max_cost_per_1k_tokens?: number;
      required_capabilities: string[];
      excluded_capabilities: string[];
    }
  >;
  fallback_provider: string;
  fallback_model?: string;
  is_valid: boolean;
  validation_errors: string[];
  created_at: number;
  updated_at: number;
  settings?: {
    temperature?: number;
    max_tokens?: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
  };
}

export interface ProviderStats {
  total_models: number;
  healthy_providers: number;
  total_providers: number;
  last_sync: number;
  degraded_mode: boolean;
}
