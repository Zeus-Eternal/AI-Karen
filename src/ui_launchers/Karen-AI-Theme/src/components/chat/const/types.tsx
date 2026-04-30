import type { SuggestedAction } from '@/lib/agent-ui/service';

// -----------------------------------------------------------------------------
// Shared primitive aliases
// -----------------------------------------------------------------------------

export type JsonObject = Record<string, unknown>;

export type ChatMessageRole = 'user' | 'assistant';

export type ChatMessageStatus =
  | 'pending'
  | 'streaming'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type ConnectionHealth = 'excellent' | 'good' | 'poor' | 'critical';

export type ChatResponseMode = 'streaming_first' | 'auto' | 'non_streaming';

export type ChatTransport = 'sse' | 'json' | 'unknown';

export type StreamEventType = 'status' | 'content' | 'complete' | 'error';

export type RuntimeEngine =
  | 'vllm'
  | 'transformers'
  | 'ollama'
  | 'gemini'
  | 'zai'
  | 'openai'
  | 'anthropic'
  | 'external_api'
  | 'none'
  | 'unknown'
  | string;

export type ResponseSource =
  | 'live_model'
  | 'degraded_live_model'
  | 'deterministic_fallback'
  | 'emergency_static'
  | 'runtime_control_plane'
  | 'requested_model'
  | 'unknown'
  | string;

export type ProviderId =
  | 'builtin_vllm'
  | 'transformers'
  | 'ollama'
  | 'gemini'
  | 'zai'
  | 'openai'
  | 'anthropic'
  | 'emergency_static'
  | 'system'
  | 'unknown'
  | string;

// -----------------------------------------------------------------------------
// Runtime truth / provider metadata
// -----------------------------------------------------------------------------

export interface ChatRuntimeMetadata {
  requested_provider?: ProviderId | null;
  requestedProvider?: ProviderId | null;
  requested_model?: string | null;
  requestedModel?: string | null;

  actual_provider?: ProviderId | null;
  actualProvider?: ProviderId | null;
  actual_model?: string | null;
  actualModel?: string | null;

  provider?: ProviderId | null;
  model?: string | null;
  model_name?: string | null;

  runtime_engine?: RuntimeEngine | null;
  runtimeEngine?: RuntimeEngine | null;

  response_source?: ResponseSource | null;
  responseSource?: ResponseSource | null;
  source?: ResponseSource | string | null;

  fallback_level?: number | string | null;
  fallbackLevel?: number | string | null;
  used_fallback?: boolean | string | number | null;
  usedFallback?: boolean | string | number | null;

  degraded_mode?: boolean | string | number | null;
  degradedMode?: boolean | string | number | null;
  degradation_reason?: string | null;
  degradationReason?: string | null;
  fallback_reason?: string | null;
  failure_reason?: string | null;

  provider_health?: string | JsonObject | null;
  providerHealth?: string | JsonObject | null;
  provider_error?: string | JsonObject | null;
  providerError?: string | JsonObject | null;

  provider_streaming_supported?: boolean | string | number | null;
  providerStreamingSupported?: boolean | string | number | null;
  provider_streaming_used?: boolean | string | number | null;
  providerStreamingUsed?: boolean | string | number | null;
  streaming_fallback_reason?: string | null;
  streamingFallbackReason?: string | null;

  requested_response_mode?: ChatResponseMode | string | null;
  requestedResponseMode?: ChatResponseMode | string | null;
  actual_response_mode?: ChatResponseMode | string | null;
  actualResponseMode?: ChatResponseMode | string | null;
  transport?: ChatTransport | string | null;
  response_transport?: ChatTransport | string | null;

  latency_ms?: number | string | null;
  latencyMs?: number | string | null;
  processing_time?: number | string | null;
  processing_time_ms?: number | string | null;
  speed?: string | number | null;

  status?: string | null;
  status_message?: string | null;
  statusMessage?: string | null;

  correlation_id?: string | null;
  correlationId?: string | null;
  request_id?: string | null;
  requestId?: string | null;
  conversation_id?: string | null;
  conversationId?: string | null;
  session_id?: string | null;
  sessionId?: string | null;

  llm?: LlmRuntimeMetadata | null;
  runtime?: JsonObject | null;

  [key: string]: unknown;
}

export interface LlmRuntimeMetadata {
  requested_provider?: ProviderId | null;
  requestedProvider?: ProviderId | null;
  requested_model?: string | null;
  requestedModel?: string | null;

  actual_provider?: ProviderId | null;
  actualProvider?: ProviderId | null;
  provider?: ProviderId | null;

  actual_model?: string | null;
  actualModel?: string | null;
  model?: string | null;
  model_name?: string | null;

  runtime_engine?: RuntimeEngine | null;
  runtimeEngine?: RuntimeEngine | null;

  response_source?: ResponseSource | null;
  responseSource?: ResponseSource | null;
  source?: ResponseSource | string | null;

  is_degraded?: boolean | string | number | null;
  degraded_mode?: boolean | string | number | null;
  failure_reason?: string | null;
  fallback_level?: number | string | null;

  provider_streaming_supported?: boolean | string | number | null;
  provider_streaming_used?: boolean | string | number | null;
  streaming_fallback_reason?: string | null;

  latency_ms?: number | string | null;

  [key: string]: unknown;
}

export interface NormalizedChatRuntimeMetadata {
  requestedProvider: string;
  requestedModel: string;
  actualProvider: string;
  actualModel: string;
  runtimeEngine: string;
  responseSource: string;
  fallbackLevel: number | null;
  degradedMode: boolean;
  degradationReason: string;
  providerStreamingSupported: boolean | null;
  providerStreamingUsed: boolean | null;
  streamingFallbackReason: string;
  requestedResponseMode: string;
  actualResponseMode: string;
  transport: string;
  latencyMs: number | null;
  correlationId: string;
}

export interface ProviderSelectionMetadata {
  requestedProvider?: ProviderId | null;
  requestedModel?: string | null;
  actualProvider?: ProviderId | null;
  actualModel?: string | null;
  runtimeEngine?: RuntimeEngine | null;
  responseSource?: ResponseSource | null;
  fallbackLevel?: number | null;
  degradedMode?: boolean;
  degradationReason?: string | null;
  providerHealth?: string | JsonObject | null;
  providerError?: string | JsonObject | null;
}

// -----------------------------------------------------------------------------
// Chat Message Types
// -----------------------------------------------------------------------------

export interface ChatMessage {
  id: string;
  role: ChatMessageRole;
  content: string;
  timestamp: Date;
  status: ChatMessageStatus;
  actions?: SuggestedAction[];
  metadata?: ChatRuntimeMetadata;
  structuredContent?: JsonObject;
}

// -----------------------------------------------------------------------------
// Assist Response Types
// -----------------------------------------------------------------------------

export interface AssistResponse {
  answer: string;
  structured_content?: JsonObject;
  actions?: SuggestedAction[];
  metadata?: ChatRuntimeMetadata;
  correlation_id?: string;
}

// -----------------------------------------------------------------------------
// Streaming response/event types
// -----------------------------------------------------------------------------

export interface StreamingEventPayload {
  type: StreamEventType | string;
  content?: string;
  correlation_id?: string;
  correlationId?: string;
  metadata?: ChatRuntimeMetadata;
  error?: string;
  done?: boolean;
  [key: string]: unknown;
}

export interface StreamingCompleteEventPayload extends StreamingEventPayload {
  type: 'complete';
  metadata: ChatRuntimeMetadata;
}

export interface StreamingContentEventPayload extends StreamingEventPayload {
  type: 'content';
  content: string;
}

export interface StreamingStatusEventPayload extends StreamingEventPayload {
  type: 'status';
  content?: string;
  metadata?: ChatRuntimeMetadata & {
    status?: string | null;
    status_message?: string | null;
  };
}

export interface StreamingErrorEventPayload extends StreamingEventPayload {
  type: 'error';
  content?: string;
  error?: string;
  metadata?: ChatRuntimeMetadata & {
    error_type?: string;
  };
}

// -----------------------------------------------------------------------------
// Model Settings Types
// -----------------------------------------------------------------------------

export interface ModelDetails {
  id: string;
  name: string;
  source?: string;
  runtime_engine?: RuntimeEngine | string;
  response_source?: ResponseSource | string;
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
  [key: string]: unknown;
}

export interface ProviderDetails {
  id: ProviderId;
  display_name: string;
  description?: string;
  provider_type?: string;
  runtime_engine?: RuntimeEngine | string;
  compatible_api?: string;
  selectable?: boolean;
  enabled?: boolean;
  healthy?: boolean;
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
  fallback_eligible?: boolean;
  timeout_seconds?: number;
  health?: ProviderHealthDetails | null;
  models: ModelDetails[];
  metadata?: JsonObject;
}

export interface ModelSettingsResponse {
  selected_provider: ProviderId;
  selected_model: string;
  response_mode?: ChatResponseMode | string;
  streaming_enabled?: boolean;
  providers: ProviderDetails[];
}

// -----------------------------------------------------------------------------
// Streaming Metrics Types
// -----------------------------------------------------------------------------

export interface StreamingMetrics {
  chunksReceived: number;
  totalBytes: number;
  connectionHealth: ConnectionHealth;
  lastChunkTime: number;
  startedAt?: number;
  completedAt?: number;
  providerStreamingSupported?: boolean | null;
  providerStreamingUsed?: boolean | null;
  transport?: ChatTransport | string;
}

// -----------------------------------------------------------------------------
// User Preferences Types
// -----------------------------------------------------------------------------

export interface UserPreferences {
  preferredAddressName: string;
  fullName: string;
  displayName: string | null;
  firstNameOption: string | null;
  shouldPromptForPreferredName: boolean;
  recentMessages: Array<{
    role: string;
    content: string;
  }>;
}

// -----------------------------------------------------------------------------
// Session/history shared types
// -----------------------------------------------------------------------------

export interface ChatSessionSummary {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  isActive: boolean;
  lastMessage?: string;
}