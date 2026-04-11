import type { ChatMessage, MessageResponse } from '@/lib/types';

type SuggestedAction = {
  type: string;
  params?: Record<string, string | number | boolean | null | undefined>;
  confidence?: number;
  description?: string;
};

type BackendChatEnvelope = {
  answer?: string;
  content?: string;
  response?: string;
  mode?: string;
  message?: string;
  reason?: string;
  retry_after_seconds?: number;
  estimated_completion_time?: string | null;
  notification_supported?: boolean;
  notification_request_allowed?: boolean;
  system_status_code?: number;
  support_hint?: string;
  structured_content?: Record<string, unknown>;
  structuredContent?: Record<string, unknown>;
  actions?: SuggestedAction[];
  metadata?: Record<string, unknown>;
  correlation_id?: string;
  request_id?: string;
  response_id?: string;
  processing_time?: number;
  execution_path?: string;
  assistant_message_id?: string;
  conversation_id?: string;
  model?: string;
  usage?: Record<string, unknown>;
  used_fallback?: boolean;
  context_used?: boolean;
};

export type NormalizedChatResponse = {
  answer: string;
  structuredContent: Record<string, unknown>;
  actions: SuggestedAction[];
  metadata: Record<string, unknown>;
  correlationId: string;
};

export type DegradedPresentation = {
  hasLlmInfo: boolean;
  failureCategory: string;
  isSafetyBlocked: boolean;
  usedFallback: boolean;
  isLocalFallbackSource: boolean;
  isDegraded: boolean;
  requestedProvider: string;
  requestedModel: string;
  actualProvider: string;
  actualModel: string;
  failureReason: string;
  providerDisplayName: string;
  modelDisplayName: string;
  degradedStatusLabel: string;
  degradedBannerText: string;
  visibleDegradedNotice: string;
  detailsStatusLabel: string;
  fallbackDetailsText: string;
  shouldRenderFallbackDetails: boolean;
  shouldRenderDegradedState: boolean;
};

export type ResponseDetailsPresentation = {
  hasMetadataDetails: boolean;
  providerLabel: string;
  modelLabel: string;
  modelTitle: string;
  sourceLabel: string;
  speedLabel: string;
  latencyLabel: string;
  engineHeaderLabel: string;
  showStatusRow: boolean;
  statusLabel: string;
  showFallbackRow: boolean;
  fallbackLabel: string;
  showReasonRow: boolean;
  reasonLabel: string;
  showTokensRow: boolean;
  tokensLabel: string;
};

export type CompactBadgePresentation = {
  shouldRenderBadge: boolean;
  providerLabel: string;
  modelLabel: string;
  durationLabel: string;
  speedLabel: string;
  statusLabel: string;
  isDegraded: boolean;
};

export const normalizeProviderName = (provider?: string | null): string => {
  const value = String(provider || '').trim().toLowerCase();
  if (!value) return '';
  if (
    value === 'local' ||
    value === 'llama-cpp' ||
    value === 'llama_cpp' ||
    value === 'llama.cpp'
  ) {
    return 'llamacpp';
  }
  return value;
};

export const normalizeModelName = (model?: string | null): string => {
  const value = String(model || '').trim().toLowerCase();
  if (!value) return '';
  const withoutProvider = value.includes(':') ? value.split(':').pop() || value : value;
  return withoutProvider
    .replace(/\.(gguf|bin)$/i, '')
    .replace(/_/g, '-');
};

export const getDisplayModelName = (
  modelId?: string | null,
  modelName?: string | null,
): string => {
  const explicitName = String(modelName || '').trim();
  if (explicitName) {
    return explicitName;
  }

  const rawModelId = String(modelId || '').trim();
  if (!rawModelId) {
    return '';
  }

  return rawModelId
    .split(':')
    .pop()
    ?.split('/')
    .pop()
    ?.replace(/\.(gguf|bin)$/i, '')
    .replace(/[-_]/g, ' ')
    .trim() || rawModelId;
};

const KAREN_FALLBACK_MODEL_IDS = new Set([
  'kari-fallback-v1',
]);

const getFriendlyProviderLabel = (
  provider?: string | null,
): string => {
  const rawProvider = String(provider || '').trim();
  const normalizedProvider = normalizeProviderName(rawProvider);

  if (!normalizedProvider) {
    return '';
  }

  if (normalizedProvider === 'fallback') {
    return 'Local Emergency Fallback';
  }

  if (normalizedProvider === 'llamacpp') {
    return 'llama.cpp';
  }

  return rawProvider;
};

const getFriendlyModelLabel = (
  modelId?: string | null,
  modelName?: string | null,
): string => {
  const normalizedModel = normalizeModelName(modelId || modelName);
  if (normalizedModel && KAREN_FALLBACK_MODEL_IDS.has(normalizedModel)) {
    return 'Karen Local Fallback';
  }
  return getDisplayModelName(modelId, modelName);
};

const getFallbackTargetLabel = (
  providerLabel: string,
  modelLabel: string,
): string => {
  if (providerLabel && modelLabel) {
    return `${providerLabel} (${modelLabel})`;
  }
  return providerLabel || modelLabel || 'fallback';
};

export const sanitizeChatContent = (content?: string | null): string => {
  return String(content || '')
    .replace(/^<div class="ui-[^"]+">\s*/i, '')
    .replace(/<\/div>\s*$/i, '')
    .replace(/^<section[^>]*>\s*/i, '')
    .replace(/<\/section>\s*$/i, '')
    .replace(/^<div role="article"[^>]*>\s*/i, '')
    .replace(/<\/div>\s*$/i, '')
    .trim();
};

const INTERNAL_STRUCTURED_CONTENT_KEYS = new Set([
  'memory_classification',
  'classified_memories',
  'curated_writeback_candidates',
  'memoryClassification',
  'classifiedMemories',
  'curatedWritebackCandidates',
]);

export const sanitizeStructuredContent = (
  structuredContent?: Record<string, any> | null,
): Record<string, any> => {
  const source = structuredContent && typeof structuredContent === 'object'
    ? structuredContent
    : {};

  return Object.fromEntries(
    Object.entries(source).filter(([key]) => !INTERNAL_STRUCTURED_CONTENT_KEYS.has(key)),
  );
};

export const deriveDegradedPresentation = (
  metadata?: Record<string, any>,
): DegradedPresentation => {
  const llm = metadata?.llm || {};
  const failureCategory = String(metadata?.failure_category || llm?.failure_category || '').trim();
  const isSafetyBlocked = failureCategory === 'safety_blocked';
  const usedFallback = metadata?.orchestrator?.used_fallback === true;
  const isLocalFallbackSource =
    llm?.source === 'chat_orchestrator_local_fallback' ||
    llm?.source === 'configured_fallback_provider' ||
    llm?.source === 'runtime_error_fallback' ||
    llm?.fallback_level === 'local';
  const isDegraded =
    metadata?.degraded_mode === true ||
    llm?.is_degraded === true ||
    usedFallback ||
    isLocalFallbackSource;
  const hasLlmInfo = Boolean(llm && (llm.provider || llm.model_id));
  const requestedProvider = String(llm?.requested_provider || '').trim();
  const requestedModel = String(llm?.requested_model || '').trim();
  const actualProvider = String(llm?.provider || '').trim();
  const actualModelId = String(llm?.model_id || '').trim();
  const actualModel = getFriendlyModelLabel(llm?.model_id, llm?.model_name);
  const normalizedActualProvider = normalizeProviderName(actualProvider);
  const normalizedRequestedProvider = normalizeProviderName(requestedProvider);
  const isLlamaCppBackedFallback =
    normalizedActualProvider === 'fallback' &&
    actualModelId.toLowerCase().startsWith('llamacpp:');
  const actualProviderLabel = isLlamaCppBackedFallback
    ? 'llama.cpp'
    : getFriendlyProviderLabel(actualProvider);
  const fallbackTargetLabel = getFallbackTargetLabel(actualProviderLabel, actualModel);
  const preferredFailureReason = String(llm?.preferred_failure_reason || '').trim();
  const failureReason = String(preferredFailureReason || llm?.failure_reason || '').trim();
  const failureReasonLower = failureReason.toLowerCase();
  const normalizedRequestedModel = normalizeModelName(requestedModel);
  const normalizedActualModel = normalizeModelName(llm?.model_id || llm?.model_name || actualModel);
  const providerOrModelChanged =
    Boolean(normalizedRequestedProvider && normalizedActualProvider && normalizedRequestedProvider !== normalizedActualProvider) ||
    Boolean(normalizedRequestedModel && normalizedActualModel && normalizedRequestedModel !== normalizedActualModel);
  const degradedStatusLabel = isSafetyBlocked
    ? 'provider policy block'
    : failureReasonLower.includes('rate limit') || failureReasonLower.includes('quota')
      ? `${requestedProvider || 'provider'} rate limited`
      : failureReasonLower.includes('unavailable')
        ? `${requestedProvider || 'provider'} unavailable`
        : (isDegraded || Boolean(failureReason))
          ? 'degraded mode'
          : '';
  const degradedBannerText = isSafetyBlocked
    ? 'Provider policy blocked this response.'
    : requestedProvider && isLlamaCppBackedFallback && normalizedRequestedProvider === 'llamacpp'
      ? `${requestedProvider} primary path failed, recovered via local llama.cpp fallback path${actualModel ? ` (${actualModel})` : ''}.`
    : requestedProvider && actualProvider && providerOrModelChanged
      ? `${requestedProvider} failed, switched to ${fallbackTargetLabel}.`
      : requestedProvider && failureReasonLower.includes('rate limit')
        ? `${requestedProvider} rate limited, switched to ${fallbackTargetLabel}.`
        : requestedProvider && failureReasonLower.includes('quota')
          ? `${requestedProvider} quota exceeded, switched to ${fallbackTargetLabel}.`
          : failureReason
            ? failureReason
            : '';
  const visibleDegradedNotice = isSafetyBlocked
    ? degradedBannerText
    : degradedBannerText && failureReason && degradedBannerText !== failureReason
      ? `${degradedBannerText} Reason: ${failureReason}`
      : degradedBannerText || failureReason;
  const shouldRenderDegradedState = isDegraded || isSafetyBlocked || Boolean(visibleDegradedNotice);
  const providerDisplayName = actualProviderLabel || actualProvider || 'system';
  const modelDisplayName = isSafetyBlocked
    ? 'Safety Blocked'
    : actualModel || 'auto';
  const detailsStatusLabel = isSafetyBlocked
    ? 'Safety Blocked'
    : degradedStatusLabel || 'Degraded Mode';
  const fallbackDetailsText = degradedBannerText;
  const shouldRenderFallbackDetails = Boolean(fallbackDetailsText && !failureReason);

  return {
    hasLlmInfo,
    failureCategory,
    isSafetyBlocked,
    usedFallback,
    isLocalFallbackSource,
    isDegraded,
    requestedProvider,
    requestedModel,
    actualProvider,
    actualModel,
    failureReason,
    providerDisplayName,
    modelDisplayName,
    degradedStatusLabel,
    degradedBannerText,
    visibleDegradedNotice,
    detailsStatusLabel,
    fallbackDetailsText,
    shouldRenderFallbackDetails,
    shouldRenderDegradedState,
  };
};

export const deriveResponseDetailsPresentation = (
  metadata?: Record<string, any>,
): ResponseDetailsPresentation => {
  const llm = metadata?.llm || {};
  const degraded = deriveDegradedPresentation(metadata);
  const usage = llm?.usage || {};
  const promptTokens = Number(usage.prompt_tokens || 0);
  const completionTokens = Number(usage.completion_tokens || 0);
  const hasMetadataDetails = Boolean(metadata && Object.keys(metadata).length > 0);
  const providerLabel = degraded.providerDisplayName;
  const modelLabel = degraded.modelDisplayName;
  const modelTitle = String(llm?.model_id || '').trim();
  const sourceLabel = String(llm?.source || 'direct').trim();
  const speedLabel = llm?.tokens_per_second ? `${llm.tokens_per_second} tok/s` : 'N/A';
  const latencyLabel =
    typeof llm?.duration === 'number' ? `${llm.duration.toFixed(2)}s` : 'N/A';
  const engineHeaderLabel = providerLabel;
  const showStatusRow = degraded.shouldRenderDegradedState;
  const statusLabel = degraded.detailsStatusLabel;
  const showFallbackRow = degraded.shouldRenderFallbackDetails;
  const fallbackLabel = degraded.fallbackDetailsText;
  const showReasonRow = Boolean(degraded.failureReason);
  const reasonLabel = degraded.failureReason;
  const showTokensRow = Boolean(llm?.usage);
  const tokensLabel = `${promptTokens}i + ${completionTokens}o`;

  return {
    hasMetadataDetails,
    providerLabel,
    modelLabel,
    modelTitle,
    sourceLabel,
    speedLabel,
    latencyLabel,
    engineHeaderLabel,
    showStatusRow,
    statusLabel,
    showFallbackRow,
    fallbackLabel,
    showReasonRow,
    reasonLabel,
    showTokensRow,
    tokensLabel,
  };
};

export const deriveCompactBadgePresentation = (
  metadata?: Record<string, any>,
): CompactBadgePresentation => {
  const llm = metadata?.llm || {};
  const degraded = deriveDegradedPresentation(metadata);
  const hasMetadataDetails = Boolean(metadata && Object.keys(metadata).length > 0);
  const hasLlmInfo = degraded.hasLlmInfo;
  const shouldRenderBadge =
    hasLlmInfo || hasMetadataDetails || metadata?.degraded_mode === true;
  const providerLabel = degraded.providerDisplayName;
  const modelLabel = degraded.modelDisplayName;
  const durationLabel =
    typeof llm?.duration === 'number' ? `${llm.duration.toFixed(1)}s` : '';
  const speedLabel = llm?.tokens_per_second ? `${llm.tokens_per_second} tok/s` : '';
  const statusLabel = degraded.shouldRenderDegradedState
    ? degraded.degradedStatusLabel
    : '';

  return {
    shouldRenderBadge,
    providerLabel,
    modelLabel,
    durationLabel,
    speedLabel,
    statusLabel,
    isDegraded: degraded.shouldRenderDegradedState,
  };
};

const mapBackendStatusToMessageStatus = (
  status?: string | null,
): ChatMessage['status'] => {
  const normalized = String(status || '').trim().toLowerCase();
  if (normalized === 'failed') return 'failed';
  if (normalized === 'pending') return 'pending';
  if (normalized === 'streaming') return 'streaming';
  return 'completed';
};

const ensureLlmMetadata = (
  metadata: Record<string, any>,
  raw: BackendChatEnvelope,
): Record<string, any> => {
  const llm = { ...(metadata.llm || {}) };

  if (raw.model && !llm.model_name && !llm.model_id) {
    llm.model_name = raw.model;
  }

  if (raw.usage && !llm.usage) {
    llm.usage = raw.usage;
  }

  if (typeof raw.processing_time === 'number' && llm.duration == null) {
    llm.duration = raw.processing_time;
  }

  if (Object.keys(llm).length > 0) {
    metadata.llm = llm;
  }

  return metadata;
};

const ensureRuntimeModeMetadata = (
  metadata: Record<string, any>,
  raw: BackendChatEnvelope,
): Record<string, any> => {
  const runtimeMode = String(raw.mode || metadata.mode || '').trim();
  if (!runtimeMode) {
    return metadata;
  }

  metadata.mode = runtimeMode;
  metadata.runtime = {
    ...(metadata.runtime || {}),
    mode: runtimeMode,
    retry_after_seconds:
      raw.retry_after_seconds ?? metadata.runtime?.retry_after_seconds,
    estimated_completion_time:
      raw.estimated_completion_time ?? metadata.runtime?.estimated_completion_time,
    notification_supported:
      raw.notification_supported ?? metadata.runtime?.notification_supported,
    notification_request_allowed:
      raw.notification_request_allowed ?? metadata.runtime?.notification_request_allowed,
    system_status_code:
      raw.system_status_code ?? metadata.runtime?.system_status_code,
    support_hint: raw.support_hint ?? metadata.runtime?.support_hint,
  };

  const llm = { ...(metadata.llm || {}) };
  llm.provider = llm.provider || 'system';
  llm.source = llm.source || 'runtime_control_plane';
  llm.model_name =
    llm.model_name ||
    (runtimeMode === 'maintenance'
      ? 'Maintenance'
      : runtimeMode === 'emergency_fallback'
        ? 'Emergency Fallback'
        : runtimeMode === 'degraded'
          ? 'Degraded Mode'
          : 'Runtime Control');

  if (runtimeMode === 'maintenance' || runtimeMode === 'emergency_fallback') {
    metadata.degraded_mode = true;
    llm.is_degraded = true;
    llm.fallback_level = runtimeMode === 'maintenance' ? 'maintenance' : 'emergency';
    llm.failure_reason = String(raw.reason || raw.message || raw.support_hint || '').trim();
    llm.routing_rationale =
      runtimeMode === 'maintenance'
        ? 'Karen is in planned maintenance mode.'
        : 'Karen is serving the emergency fallback response.';
  } else if (runtimeMode === 'degraded') {
    metadata.degraded_mode = true;
    llm.is_degraded = true;
    llm.fallback_level = llm.fallback_level || 'degraded';
    // Do not mirror the primary assistant message as failure reason; that causes
    // duplicate degraded text in UI banners + message body.
    llm.failure_reason = llm.failure_reason || String(raw.reason || '').trim();
  }

  metadata.llm = llm;
  return metadata;
};

export function normalizeBackendChatResponse(
  raw: BackendChatEnvelope,
  options?: {
    requestedProvider?: string;
    requestedModel?: string;
  },
): NormalizedChatResponse {
  const answer = sanitizeChatContent(raw.answer ?? raw.content ?? raw.response);
  const runtimeMode = String(raw.mode || '').trim();
  const looksLikeCapabilityBanner =
    /^limited assistant with:/i.test(answer) ||
    /^minimal text-only assistant$/i.test(answer);
  const correlationId = String(
    raw.correlation_id ||
      raw.request_id ||
      raw.response_id ||
      raw.metadata?.correlation_id ||
      `assistant-${Date.now()}`,
  );
  const metadata: Record<string, any> = { ...(raw.metadata || {}) };

  metadata.correlation_id = metadata.correlation_id || correlationId;
  metadata.response_id = metadata.response_id || raw.response_id;
  metadata.request_id = metadata.request_id || raw.request_id;
  metadata.conversation_id = metadata.conversation_id || raw.conversation_id;
  metadata.assistant_message_id =
    metadata.assistant_message_id || raw.assistant_message_id;
  metadata.execution_path =
    metadata.execution_path || raw.execution_path || 'direct_llm';
  metadata.status = metadata.status || 'completed';

  if (typeof raw.processing_time === 'number' && metadata.total_ms == null) {
    metadata.total_ms = raw.processing_time * 1000;
  }

  if (typeof raw.context_used === 'boolean' && metadata.context_used == null) {
    metadata.context_used = raw.context_used;
  }

  if (typeof raw.used_fallback === 'boolean') {
    metadata.orchestrator = {
      ...(metadata.orchestrator || {}),
      used_fallback: raw.used_fallback,
    };
  }

  if (!metadata.persistence) {
    metadata.persistence = {
      canonical_store: 'postgres',
      assistant_persisted: Boolean(metadata.assistant_message_id),
    };
  }

  ensureLlmMetadata(metadata, raw);
  ensureRuntimeModeMetadata(metadata, raw);

  const llm = metadata.llm ? { ...metadata.llm } : {};
  const requestedProvider = normalizeProviderName(options?.requestedProvider);
  const actualProvider = normalizeProviderName(llm.provider);
  const localProviderReturned =
    Boolean(requestedProvider) &&
    requestedProvider !== 'llamacpp' &&
    actualProvider === 'llamacpp';

  if (localProviderReturned) {
    metadata.degraded_mode = true;
    metadata.orchestrator = {
      ...(metadata.orchestrator || {}),
      used_fallback: true,
    };
    llm.is_degraded = true;
    llm.fallback_level = llm.fallback_level || 'local';
    llm.source = llm.source || 'provider_selection_fallback';
    llm.requested_provider = llm.requested_provider || options?.requestedProvider;
    llm.requested_model = llm.requested_model || options?.requestedModel;
    llm.failure_reason =
      llm.failure_reason ||
      `Selected provider ${options?.requestedProvider} was unavailable; Karen continued with local llama.cpp.`;
    llm.routing_rationale =
      llm.routing_rationale ||
      `Requested provider ${options?.requestedProvider} failed, so the conversation continued in degraded mode on local llama.cpp.`;
    metadata.llm = llm;
  }

  return {
    answer:
      (looksLikeCapabilityBanner && runtimeMode === 'degraded'
        ? 'Karen is running in degraded mode right now, but can still help with brief answers. Please try your request again.'
        : answer) ||
      sanitizeChatContent(raw.message) ||
      (String(raw.mode || '').trim() === 'maintenance'
        ? 'Karen is temporarily unavailable while scheduled maintenance is in progress.'
        : String(raw.mode || '').trim() === 'emergency_fallback'
          ? 'Karen is temporarily unavailable. Please try again shortly.'
          : 'Karen returned an empty response.'),
    structuredContent: sanitizeStructuredContent(
      raw.structured_content || raw.structuredContent || {},
    ),
    actions: raw.actions || [],
    metadata,
    correlationId,
  };
}

export function normalizeConversationMessage(
  message: MessageResponse,
): ChatMessage {
  const metadata: Record<string, any> = { ...(message.metadata || {}) };

  if (message.ui_source && !metadata.ui_source) {
    metadata.ui_source = message.ui_source;
  }

  if (typeof message.processing_time_ms === 'number' && metadata.total_ms == null) {
    metadata.total_ms = message.processing_time_ms;
  }

  if (message.model_used || typeof message.tokens_used === 'number') {
    metadata.llm = {
      ...(metadata.llm || {}),
      model_name: metadata.llm?.model_name || message.model_used,
      usage:
        metadata.llm?.usage ||
        (typeof message.tokens_used === 'number'
          ? { total_tokens: message.tokens_used }
          : undefined),
    };
  }

  metadata.status = metadata.status || 'completed';

  return {
    id: message.id,
    role: message.role as ChatMessage['role'],
    content: sanitizeChatContent(message.content),
    timestamp: new Date(message.timestamp),
    status: mapBackendStatusToMessageStatus(metadata.status),
    structuredContent: sanitizeStructuredContent(message.structured_content),
    actions: message.actions,
    metadata,
  };
}
