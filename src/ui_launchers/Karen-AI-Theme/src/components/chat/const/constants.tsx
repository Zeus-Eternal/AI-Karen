// Chat Interface Constants

export const DEFAULT_PROCESSING_MESSAGE = 'Karen is working on your request...';
export const STREAMING_ERROR_MESSAGE = 'Connection issue - please try again';
export const STREAM_TIMEOUT_MESSAGE = 'Request timed out - please try again';

// -----------------------------------------------------------------------------
// Processing status messages
// -----------------------------------------------------------------------------

export const PROCESSING_STATUS_MESSAGE_VARIANTS: Record<string, string[]> = {
  initializing: [
    'Karen is preparing your workspace...',
    'Karen is initializing the request pipeline...',
  ],
  processing: [
    'Karen is analyzing your message...',
    'Karen is understanding what you need...',
  ],
  extracting_context: [
    'Karen is retrieving relevant context and memories...',
    'Karen is gathering useful conversation context...',
  ],
  provider_selection: [
    'Karen is selecting the best available provider...',
    'Karen is checking provider availability...',
  ],
  provider_selected: [
    'Karen selected a live provider...',
    'Karen found a provider that can answer...',
  ],
  provider_unavailable: [
    'Karen could not reach the requested provider...',
    'The requested provider is unavailable, Karen is checking fallbacks...',
  ],
  fallback_started: [
    'Karen is trying a fallback provider...',
    'Karen is recovering through an available provider...',
  ],
  fallback_succeeded: [
    'Karen recovered through a live fallback provider...',
    'Karen found a working fallback provider...',
  ],
  generating_response: [
    'Karen is generating a response...',
    'Karen is drafting your answer...',
  ],
  streaming: [
    'Karen is composing the response...',
    'Karen is streaming the response...',
  ],
  executing_tools: [
    'Karen is executing tools and integrations...',
    'Karen is running supporting tasks...',
  ],
  recording_memory: [
    'Karen is recording insights from this conversation...',
    'Karen is saving useful context for next time...',
  ],
  post_processing: [
    'Karen is finalizing the response...',
    'Karen is polishing the final output...',
  ],
  retrying: [
    'Karen is retrying with an alternative provider...',
    'Karen is recovering from a temporary issue...',
  ],
  degraded: [
    'Karen is running in degraded mode...',
    'Karen is operating with limited capabilities...',
  ],
  degraded_live: [
    'Karen is answering through a degraded live provider...',
    'Karen is using a limited live fallback path...',
  ],
  emergency_static: [
    'Karen is using the emergency fallback response...',
    'All live providers are unavailable, Karen is using a safe fallback reply...',
  ],
  completed: ['Response complete.'],
  failed: ['Processing failed. Retrying or falling back...'],
  cancelled: ['Request was cancelled.'],
};

export const normalizeProcessingStatusKey = (status: unknown): string => {
  if (status == null) return '';

  if (typeof status === 'string') {
    return status.trim().toLowerCase().replace(/[\s-]+/g, '_');
  }

  if (typeof status === 'object' && status !== null && 'value' in status) {
    const value = (status as { value?: unknown }).value;

    if (typeof value === 'string') {
      return value.trim().toLowerCase().replace(/[\s-]+/g, '_');
    }
  }

  return String(status).trim().toLowerCase().replace(/[\s-]+/g, '_');
};

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
};

const toCleanString = (value: unknown): string => {
  return typeof value === 'string' ? value.trim() : String(value ?? '').trim();
};

const formatProviderLabel = (provider: unknown): string => {
  const normalized = normalizeProcessingStatusKey(provider).replace(/_/g, ' ');

  if (!normalized) {
    return '';
  }

  if (normalized === 'builtin vllm' || normalized === 'vllm') return 'vLLM';
  if (normalized === 'builtin transformers' || normalized === 'transformers') return 'Transformers';
  if (normalized === 'ollama') return 'Ollama';
  if (normalized === 'openai compatible') return 'OpenAI-compatible provider';
  if (normalized === 'emergency static') return 'emergency fallback';

  return normalized;
};

const buildLiveProcessingMessage = (
  statusKey: string,
  context?: Record<string, unknown>,
): string | null => {
  const llm = isRecord(context?.llm) ? context.llm : context;
  const requestedProvider = formatProviderLabel(
    llm?.requested_provider || llm?.provider || context?.requested_provider,
  );
  const actualProvider = formatProviderLabel(
    llm?.actual_provider || llm?.provider || context?.actual_provider,
  );
  const fallbackNext = formatProviderLabel(
    llm?.fallback_next || context?.fallback_next,
  );
  const source = toCleanString(
    llm?.response_source || context?.response_source,
  );

  switch (statusKey) {
    case 'provider_selection':
      return actualProvider
        ? `Karen is checking ${actualProvider}...`
        : requestedProvider
          ? `Karen is checking ${requestedProvider}...`
          : 'Karen is checking the selected provider...';
    case 'provider_failed':
      return fallbackNext
        ? `Karen is switching from ${requestedProvider || 'the requested provider'} to ${fallbackNext}...`
        : `Karen is switching away from ${requestedProvider || 'the requested provider'}...`;
    case 'fallback_started':
    case 'fallback_succeeded':
      return actualProvider
        ? `${actualProvider} is live. Karen is generating a response...`
        : 'Karen found a live fallback provider...';
    case 'generating_response':
      return actualProvider
        ? `${actualProvider} is generating a response...`
        : 'Karen is generating a response...';
    case 'streaming':
      return actualProvider
        ? `${actualProvider} is streaming the response...`
        : 'Karen is streaming the response...';
    case 'retrying':
      return fallbackNext
        ? `Karen is retrying with ${fallbackNext}...`
        : 'Karen is retrying with a live fallback...';
    case 'degraded':
      return actualProvider
        ? `Karen is running in degraded mode with ${actualProvider}...`
        : 'Karen is running in degraded mode...';
    case 'degraded_live':
      return actualProvider
        ? `${actualProvider} is answering through a degraded live path...`
        : 'Karen is answering through a degraded live path...';
    case 'post_processing':
      return actualProvider
        ? `${actualProvider} is finalizing the response...`
        : 'Karen is finalizing the response...';
    case 'completed':
      return actualProvider
        ? `Response complete from ${actualProvider}.`
        : source
          ? `Response complete from ${source}.`
          : 'Response complete.';
    case 'failed':
      return fallbackNext
        ? `Karen could not use ${requestedProvider || 'the requested provider'} and will try ${fallbackNext}...`
        : 'Karen is handling a failed request...';
    case 'cancelled':
      return 'Request was cancelled.';
    default:
      return null;
  }
};

export const resolveProcessingStatusMessage = (
  status: unknown,
  fallbackMessage?: string,
  variantIndex: number = 0,
  context?: Record<string, unknown>,
): string => {
  const statusKey = normalizeProcessingStatusKey(status);
  const liveMessage = buildLiveProcessingMessage(statusKey, context);

  if (liveMessage) {
    return liveMessage;
  }

  const variants = PROCESSING_STATUS_MESSAGE_VARIANTS[statusKey];

  if (variants && variants.length > 0) {
    return variants[Math.abs(variantIndex) % variants.length];
  }

  if (typeof fallbackMessage === 'string' && fallbackMessage.trim()) {
    return fallbackMessage.trim();
  }

  if (statusKey) {
    return `Karen is ${statusKey.replace(/_/g, ' ')}...`;
  }

  return DEFAULT_PROCESSING_MESSAGE;
};

// -----------------------------------------------------------------------------
// Chat response mode / streaming constants
// -----------------------------------------------------------------------------

export const CHAT_RESPONSE_MODE = {
  STREAMING_FIRST: 'streaming_first',
  AUTO: 'auto',
  NON_STREAMING: 'non_streaming',
} as const;

export type ChatResponseMode =
  (typeof CHAT_RESPONSE_MODE)[keyof typeof CHAT_RESPONSE_MODE];

export const CHAT_RESPONSE_MODE_LABELS: Record<ChatResponseMode, string> = {
  [CHAT_RESPONSE_MODE.STREAMING_FIRST]: 'Streaming first',
  [CHAT_RESPONSE_MODE.AUTO]: 'Auto',
  [CHAT_RESPONSE_MODE.NON_STREAMING]: 'Non-streaming JSON',
};

export const CHAT_RESPONSE_MODE_DESCRIPTIONS: Record<ChatResponseMode, string> = {
  [CHAT_RESPONSE_MODE.STREAMING_FIRST]:
    'Recommended. Karen streams status updates and live content when the provider supports it.',
  [CHAT_RESPONSE_MODE.AUTO]:
    'Karen chooses the best response mode based on provider and client capability.',
  [CHAT_RESPONSE_MODE.NON_STREAMING]:
    'Karen waits for the full response before returning JSON. Useful for legacy clients and debugging.',
};

export const DEFAULT_CHAT_RESPONSE_MODE: ChatResponseMode =
  CHAT_RESPONSE_MODE.STREAMING_FIRST;

export const CHAT_TRANSPORT = {
  SSE: 'sse',
  JSON: 'json',
  UNKNOWN: 'unknown',
} as const;

export type ChatTransport = (typeof CHAT_TRANSPORT)[keyof typeof CHAT_TRANSPORT];

export const STREAM_EVENT_TYPE = {
  STATUS: 'status',
  CONTENT: 'content',
  COMPLETE: 'complete',
  ERROR: 'error',
  DONE: '[DONE]',
} as const;

export type StreamEventType =
  (typeof STREAM_EVENT_TYPE)[keyof typeof STREAM_EVENT_TYPE];

export const STREAMING_FALLBACK_REASON_LABELS: Record<string, string> = {
  admin_disabled_streaming: 'Streaming disabled by admin setting',
  provider_does_not_support_token_streaming:
    'Provider does not support token streaming',
  provider_unavailable: 'Requested provider unavailable',
  requested_provider_unavailable: 'Requested provider unavailable',
  requested_provider_failed_or_placeholder:
    'Requested provider failed or returned unusable content',
  all_live_providers_unavailable: 'All live providers unavailable',
  stream_error: 'Streaming connection error',
};

// -----------------------------------------------------------------------------
// Provider/runtime identity constants
// -----------------------------------------------------------------------------
//
// These labels are display-only.
// Do not use these maps to rewrite provider IDs sent to or received from backend.
// Backend provider identity remains the source of truth.

export const PROVIDER_ID = {
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

export type ProviderId = (typeof PROVIDER_ID)[keyof typeof PROVIDER_ID];

export const RUNTIME_ENGINE = {
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

export type RuntimeEngine =
  (typeof RUNTIME_ENGINE)[keyof typeof RUNTIME_ENGINE];

export const PROVIDER_DISPLAY_LABELS: Record<string, string> = {
  [PROVIDER_ID.BUILTIN_VLLM]: 'vLLM',
  [PROVIDER_ID.TRANSFORMERS]: 'Transformers',
  [PROVIDER_ID.OLLAMA]: 'Ollama',
  [PROVIDER_ID.GEMINI]: 'Gemini',
  [PROVIDER_ID.ZAI]: 'Z.AI',
  [PROVIDER_ID.OPENAI]: 'OpenAI',
  [PROVIDER_ID.ANTHROPIC]: 'Anthropic',
  [PROVIDER_ID.EMERGENCY_STATIC]: 'Emergency Static',
  [PROVIDER_ID.SYSTEM]: 'System',
  [PROVIDER_ID.UNKNOWN]: 'Unknown',
};

export const RUNTIME_ENGINE_DISPLAY_LABELS: Record<string, string> = {
  [RUNTIME_ENGINE.VLLM]: 'vLLM',
  [RUNTIME_ENGINE.TRANSFORMERS]: 'Transformers',
  [RUNTIME_ENGINE.OLLAMA]: 'Ollama',
  [RUNTIME_ENGINE.GEMINI]: 'Gemini',
  [RUNTIME_ENGINE.ZAI]: 'Z.AI',
  [RUNTIME_ENGINE.OPENAI]: 'OpenAI',
  [RUNTIME_ENGINE.ANTHROPIC]: 'Anthropic',
  [RUNTIME_ENGINE.EXTERNAL_API]: 'External API',
  [RUNTIME_ENGINE.NONE]: 'None',
  [RUNTIME_ENGINE.UNKNOWN]: 'Unknown',
};

export const RESPONSE_SOURCE = {
  LIVE_MODEL: 'live_model',
  DEGRADED_LIVE_MODEL: 'degraded_live_model',
  DETERMINISTIC_FALLBACK: 'deterministic_fallback',
  EMERGENCY_STATIC: 'emergency_static',
  RUNTIME_CONTROL_PLANE: 'runtime_control_plane',
  REQUESTED_MODEL: 'requested_model',
  UNKNOWN: 'unknown',
} as const;

export type ResponseSource =
  (typeof RESPONSE_SOURCE)[keyof typeof RESPONSE_SOURCE];

export const RESPONSE_SOURCE_DISPLAY_LABELS: Record<string, string> = {
  [RESPONSE_SOURCE.LIVE_MODEL]: 'Live model',
  [RESPONSE_SOURCE.DEGRADED_LIVE_MODEL]: 'Degraded live model',
  [RESPONSE_SOURCE.DETERMINISTIC_FALLBACK]: 'Deterministic fallback',
  [RESPONSE_SOURCE.EMERGENCY_STATIC]: 'Emergency static',
  [RESPONSE_SOURCE.RUNTIME_CONTROL_PLANE]: 'Runtime control plane',
  [RESPONSE_SOURCE.REQUESTED_MODEL]: 'Requested model',
  [RESPONSE_SOURCE.UNKNOWN]: 'Unknown',
};

export const DEGRADED_REASON_LABELS: Record<string, string> = {
  requested_provider_unavailable: 'Requested provider unavailable',
  requested_provider_failed_or_placeholder:
    'Requested provider failed or returned unusable content',
  builtin_vllm_unavailable: 'Built-in vLLM unavailable',
  provider_unavailable: 'Provider unavailable',
  provider_timeout: 'Provider timed out',
  missing_api_key: 'Missing API key',
  model_unavailable: 'Model unavailable',
  all_live_providers_unavailable: 'All live providers unavailable',
  runtime_control_plane_unavailable: 'Runtime control plane unavailable',
};

// -----------------------------------------------------------------------------
// Metadata normalization helpers
// -----------------------------------------------------------------------------

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

const toStringValue = (value: unknown, fallback: string = ''): string => {
  if (typeof value === 'string') {
    return value.trim() || fallback;
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  return fallback;
};

const toBooleanValue = (
  value: unknown,
  fallback: boolean | null = null,
): boolean | null => {
  if (typeof value === 'boolean') {
    return value;
  }

  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase();

    if (['true', '1', 'yes', 'y', 'enabled'].includes(normalized)) {
      return true;
    }

    if (['false', '0', 'no', 'n', 'disabled'].includes(normalized)) {
      return false;
    }
  }

  if (typeof value === 'number') {
    return value !== 0;
  }

  return fallback;
};

const toNumberValue = (
  value: unknown,
  fallback: number | null = null,
): number | null => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value);

    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return fallback;
};

const getNestedRecord = (
  metadata: Record<string, unknown>,
  key: string,
): Record<string, unknown> => {
  const value = metadata[key];

  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }

  return {};
};

export const getProviderDisplayLabel = (providerId: unknown): string => {
  const normalized = toStringValue(providerId, PROVIDER_ID.UNKNOWN);

  return PROVIDER_DISPLAY_LABELS[normalized] || normalized;
};

export const getRuntimeEngineDisplayLabel = (runtimeEngine: unknown): string => {
  const normalized = toStringValue(runtimeEngine, RUNTIME_ENGINE.UNKNOWN);

  return RUNTIME_ENGINE_DISPLAY_LABELS[normalized] || normalized;
};

export const getResponseSourceDisplayLabel = (responseSource: unknown): string => {
  const normalized = toStringValue(responseSource, RESPONSE_SOURCE.UNKNOWN);

  return RESPONSE_SOURCE_DISPLAY_LABELS[normalized] || normalized;
};

export const getDegradationReasonLabel = (reason: unknown): string => {
  const normalized = toStringValue(reason);

  if (!normalized) {
    return '';
  }

  return DEGRADED_REASON_LABELS[normalized] || normalized.replace(/_/g, ' ');
};

export const getStreamingFallbackReasonLabel = (reason: unknown): string => {
  const normalized = toStringValue(reason);

  if (!normalized) {
    return '';
  }

  return (
    STREAMING_FALLBACK_REASON_LABELS[normalized] || normalized.replace(/_/g, ' ')
  );
};

export const isLiveResponseSource = (responseSource: unknown): boolean => {
  return toStringValue(responseSource) === RESPONSE_SOURCE.LIVE_MODEL;
};

export const isEmergencyStaticResponse = (responseSource: unknown): boolean => {
  return toStringValue(responseSource) === RESPONSE_SOURCE.EMERGENCY_STATIC;
};

export const hasProviderFallback = (
  requestedProvider: unknown,
  actualProvider: unknown,
): boolean => {
  const requested = toStringValue(requestedProvider);
  const actual = toStringValue(actualProvider);

  return Boolean(requested && actual && requested !== actual);
};

/**
 * Normalizes backend metadata without changing backend provider identity.
 *
 * This helper intentionally does not rewrite provider IDs:
 * - builtin_vllm stays builtin_vllm
 * - transformers stays transformers
 * - ollama stays ollama
 *
 * Display labels are handled separately through PROVIDER_DISPLAY_LABELS.
 */
export const normalizeChatRuntimeMetadata = (
  rawMetadata: unknown,
): NormalizedChatRuntimeMetadata => {
  const metadata =
    rawMetadata && typeof rawMetadata === 'object' && !Array.isArray(rawMetadata)
      ? (rawMetadata as Record<string, unknown>)
      : {};

  const llm = getNestedRecord(metadata, 'llm');
  const runtime = getNestedRecord(metadata, 'runtime');
  const provider = getNestedRecord(metadata, 'provider');

  const requestedProvider = toStringValue(
    metadata.requested_provider ??
      metadata.requestedProvider ??
      llm.requested_provider ??
      llm.requestedProvider ??
      metadata.provider_requested ??
      metadata.provider,
    '',
  );

  const requestedModel = toStringValue(
    metadata.requested_model ??
      metadata.requestedModel ??
      llm.requested_model ??
      llm.requestedModel ??
      metadata.model_requested ??
      metadata.model,
    '',
  );

  const actualProvider = toStringValue(
    metadata.actual_provider ??
      metadata.actualProvider ??
      llm.actual_provider ??
      llm.actualProvider ??
      llm.provider ??
      provider.actual_provider ??
      provider.id ??
      metadata.provider,
    requestedProvider || PROVIDER_ID.UNKNOWN,
  );

  const actualModel = toStringValue(
    metadata.actual_model ??
      metadata.actualModel ??
      llm.actual_model ??
      llm.actualModel ??
      llm.model_name ??
      llm.model ??
      provider.actual_model ??
      metadata.model,
    requestedModel,
  );

  const runtimeEngine = toStringValue(
    metadata.runtime_engine ??
      metadata.runtimeEngine ??
      llm.runtime_engine ??
      llm.runtimeEngine ??
      runtime.runtime_engine ??
      runtime.engine,
    actualProvider || RUNTIME_ENGINE.UNKNOWN,
  );

  const responseSource = toStringValue(
    metadata.response_source ??
      metadata.responseSource ??
      llm.response_source ??
      llm.responseSource ??
      llm.source ??
      metadata.source,
    RESPONSE_SOURCE.UNKNOWN,
  );

  const degradedMode =
    toBooleanValue(
      metadata.degraded_mode ??
        metadata.degradedMode ??
        llm.degraded_mode ??
        llm.is_degraded ??
        metadata.is_degraded,
      false,
    ) ?? false;

  return {
    requestedProvider,
    requestedModel,
    actualProvider,
    actualModel,
    runtimeEngine,
    responseSource,
    fallbackLevel: toNumberValue(
      metadata.fallback_level ??
        metadata.fallbackLevel ??
        llm.fallback_level ??
        llm.fallbackLevel,
      null,
    ),
    degradedMode,
    degradationReason: toStringValue(
      metadata.degradation_reason ??
        metadata.degradationReason ??
        metadata.fallback_reason ??
        llm.degradation_reason ??
        llm.failure_reason,
      '',
    ),
    providerStreamingSupported: toBooleanValue(
      metadata.provider_streaming_supported ??
        metadata.providerStreamingSupported ??
        llm.provider_streaming_supported,
      null,
    ),
    providerStreamingUsed: toBooleanValue(
      metadata.provider_streaming_used ??
        metadata.providerStreamingUsed ??
        llm.provider_streaming_used,
      null,
    ),
    streamingFallbackReason: toStringValue(
      metadata.streaming_fallback_reason ??
        metadata.streamingFallbackReason ??
        llm.streaming_fallback_reason,
      '',
    ),
    requestedResponseMode: toStringValue(
      metadata.requested_response_mode ??
        metadata.requestedResponseMode ??
        llm.requested_response_mode,
      '',
    ),
    actualResponseMode: toStringValue(
      metadata.actual_response_mode ??
        metadata.actualResponseMode ??
        llm.actual_response_mode,
      '',
    ),
    transport: toStringValue(
      metadata.transport ?? metadata.response_transport ?? llm.transport,
      '',
    ),
    latencyMs: toNumberValue(
      metadata.latency_ms ??
        metadata.latencyMs ??
        metadata.processing_time_ms ??
        llm.latency_ms,
      null,
    ),
    correlationId: toStringValue(
      metadata.correlation_id ?? metadata.correlationId ?? runtime.correlation_id,
      '',
    ),
  };
};

// -----------------------------------------------------------------------------
// UI Constants
// -----------------------------------------------------------------------------

export const MAX_RECENT_MESSAGES = 6;
export const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes
export const RENEWAL_INTERVAL = 5 * 60 * 1000; // 5 minutes
export const CLEANUP_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours
export const INACTIVE_THRESHOLD = 7 * 24 * 60 * 60 * 1000; // 7 days
export const STICK_TO_BOTTOM_THRESHOLD = 120; // pixels
