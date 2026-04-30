export type JsonObject = Record<string, unknown>;

/*
 * These identifiers are backend/config-owned.
 *
 * Do not lock the UI to a hardcoded provider/runtime union. Karen's providers,
 * runtimes, aliases, and response sources are dynamic and should come from the
 * backend provider registry, runtime settings, and metadata contracts.
 */
export type RuntimeEngine = string;
export type ResponseSource = string;
export type ProviderId = string;
export type ChatResponseMode = string;

/*
 * Known IDs are display hints only. They help labels/tests/readability, but they
 * must never become routing authority or a frontend provider registry.
 */
export const KNOWN_RUNTIME_ENGINES = {
  VLLM: 'vllm',
  TRANSFORMERS: 'transformers',
  OLLAMA: 'ollama',
  GEMINI: 'gemini',
  ZAI: 'zai',
  OPENAI: 'openai',
  ANTHROPIC: 'anthropic',
  EXTERNAL_API: 'external_api',
  NONE: 'none',
  UNKNOWN: 'unknown',
} as const;

export const KNOWN_RESPONSE_SOURCES = {
  LIVE_MODEL: 'live_model',
  DEGRADED_LIVE_MODEL: 'degraded_live_model',
  DETERMINISTIC_FALLBACK: 'deterministic_fallback',
  EMERGENCY_STATIC: 'emergency_static',
  RUNTIME_CONTROL_PLANE: 'runtime_control_plane',
  ASSIST_REQUEST_ERROR: 'assist_request_error',
  REQUESTED_MODEL: 'requested_model',
  UNKNOWN: 'unknown',
} as const;

export const KNOWN_PROVIDER_IDS = {
  BUILTIN_VLLM: 'builtin_vllm',
  TRANSFORMERS: 'transformers',
  OLLAMA: 'ollama',
  GEMINI: 'gemini',
  ZAI: 'zai',
  OPENAI: 'openai',
  ANTHROPIC: 'anthropic',
  EMERGENCY_STATIC: 'emergency_static',
  SYSTEM: 'system',
  UNKNOWN: 'unknown',
} as const;

export const KNOWN_CHAT_RESPONSE_MODES = {
  STREAMING_FIRST: 'streaming_first',
  AUTO: 'auto',
  NON_STREAMING: 'non_streaming',
} as const;

export interface Session {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  isActive: boolean;
  lastMessage?: string;
}

/*
 * ProviderDetails mirrors backend/runtime settings for display and selection.
 * The UI may label providers for humans, but must not rewrite provider IDs.
 * Example: builtin_vllm stays builtin_vllm; display code may label it "vLLM".
 */
export interface ProviderDetails {
  id: ProviderId;
  display_name: string;
  description?: string;
  provider_type?: string;
  runtime_engine?: RuntimeEngine;
  compatible_api?: string;

  selectable?: boolean;
  enabled?: boolean;
  healthy?: boolean;
  fallback_eligible?: boolean;

  requires_api_key?: boolean;
  api_key_configured?: boolean;

  base_url?: string | null;
  default_base_url?: string | null;
  health_url?: string | null;

  default_model?: string | null;
  selected_model?: string | null;
  supports_base_url_override?: boolean;

  streaming_supported?: boolean;
  streaming_transport?: string | null;
  non_streaming_supported?: boolean;
  timeout_seconds?: number;

  health?: ProviderHealthDetails | null;
  models: ModelDetails[];
  metadata?: JsonObject;
}

export interface ModelDetails {
  id: string;
  name: string;
  source?: string;
  runtime_engine?: RuntimeEngine;
  response_source?: ResponseSource;
  is_default?: boolean;
  is_selected?: boolean;
  metadata?: JsonObject;
}

export interface ProviderHealthDetails {
  healthy?: boolean;
  status?: string;
  checked_at?: string;
  latency_ms?: number;
  error?: string | null;
  models_endpoint_ok?: boolean;
  generation_test_ok?: boolean;
  streaming_test_ok?: boolean;
  metadata?: JsonObject;
  [key: string]: unknown;
}

export interface ModelSettingsResponse {
  selected_provider: ProviderId;
  selected_model: string;
  response_mode?: ChatResponseMode;
  streaming_enabled?: boolean;
  providers: ProviderDetails[];
}