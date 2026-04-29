import type { ChatMessage, MessageResponse } from '@/lib/types';

type PrimitiveMetadataValue = string | number | boolean | null | undefined;

type SuggestedAction = {
  type: string;
  params?: Record<string, PrimitiveMetadataValue>;
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

const BUILTIN_TRANSFORMERS_PROVIDER = 'builtin_transformers';
const BUILTIN_VLLM_PROVIDER = 'builtin_vllm';
const OPENAI_COMPATIBLE_PROVIDER = 'openai_compatible';
const LOCAL_GGUF_PROVIDER = 'local_gguf';
const FALLBACK_PROVIDER = 'fallback';
const SYSTEM_PROVIDER = 'system';

const BUILTIN_PROVIDER_ALIASES: Record<string, string> = {
  transformers: BUILTIN_TRANSFORMERS_PROVIDER,
  'builtin-transformers': BUILTIN_TRANSFORMERS_PROVIDER,
  builtin_transformers: BUILTIN_TRANSFORMERS_PROVIDER,
  'hf-transformers': BUILTIN_TRANSFORMERS_PROVIDER,
  hf_transformers: BUILTIN_TRANSFORMERS_PROVIDER,
  huggingface: BUILTIN_TRANSFORMERS_PROVIDER,
  'hugging-face': BUILTIN_TRANSFORMERS_PROVIDER,
  hugging_face: BUILTIN_TRANSFORMERS_PROVIDER,

  vllm: BUILTIN_VLLM_PROVIDER,
  'builtin-vllm': BUILTIN_VLLM_PROVIDER,
  builtin_vllm: BUILTIN_VLLM_PROVIDER,
  'nano-vllm': BUILTIN_VLLM_PROVIDER,
  nano_vllm: BUILTIN_VLLM_PROVIDER,
};

const EXTERNAL_ENDPOINT_PROVIDER_ALIASES: Record<string, string> = {
  'openai-compatible': OPENAI_COMPATIBLE_PROVIDER,
  openai_compatible: OPENAI_COMPATIBLE_PROVIDER,
  openaicompatible: OPENAI_COMPATIBLE_PROVIDER,
  'openai-compatible-endpoint': OPENAI_COMPATIBLE_PROVIDER,
  openai_compatible_endpoint: OPENAI_COMPATIBLE_PROVIDER,

  'local-gguf': LOCAL_GGUF_PROVIDER,
  local_gguf: LOCAL_GGUF_PROVIDER,
  gguf: LOCAL_GGUF_PROVIDER,
  'gguf-endpoint': LOCAL_GGUF_PROVIDER,
  gguf_endpoint: LOCAL_GGUF_PROVIDER,
};

const LEGACY_CORE_RUNTIME_ALIASES = new Set([
  // 'ollama' removed - it's a valid external provider, not legacy
  'llamacpp',
  'llama_cpp',
  'llama-cpp',
  'llama.cpp',
  'llama cpp',
  'llama',
  'llamacpp_optimized',
  'llama-cpp-optimized',
]);

const LOCAL_FALLBACK_SOURCES = new Set([
  'chat_orchestrator_local_fallback',
  'configured_fallback_provider',
  'runtime_error_fallback',
  'degraded_fallback_llm',
  'emergency_fallback',
  'lite_assistant_fallback',
  'fallback_runtime',
  'provider_router_fallback',
  'vllm_fallback',
  'builtin_vllm_fallback',
]);

const INTERNAL_STRUCTURED_CONTENT_KEYS = new Set([
  'memory_classification',
  'classified_memories',
  'curated_writeback_candidates',
  'memoryClassification',
  'classifiedMemories',
  'curatedWritebackCandidates',
]);

const KAREN_FALLBACK_MODEL_IDS = new Set([
  'kari-fallback-v1',
  'karen-fallback-v1',
  'local-fallback',
  'emergency-fallback',
  'lite-assistant-fallback',
  'builtin-vllm-fallback',
]);

const toCleanString = (value?: unknown): string => {
  return String(value ?? '').trim();
};

const toProviderKey = (value?: unknown): string => {
  return toCleanString(value).toLowerCase().replace(/\s+/g, '-');
};

const isRecord = (value: unknown): value is Record<string, any> => {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
};

const firstNonEmpty = (...values: unknown[]): string => {
  for (const value of values) {
    const cleaned = toCleanString(value);

    if (cleaned) {
      return cleaned;
    }
  }

  return '';
};

export const normalizeProviderName = (provider?: string | null): string => {
  const raw = toCleanString(provider);
  const key = toProviderKey(raw);

  if (!key) {
    return '';
  }

  if (BUILTIN_PROVIDER_ALIASES[key]) {
    return BUILTIN_PROVIDER_ALIASES[key];
  }

  if (EXTERNAL_ENDPOINT_PROVIDER_ALIASES[key]) {
    return EXTERNAL_ENDPOINT_PROVIDER_ALIASES[key];
  }

  if (key === FALLBACK_PROVIDER) {
    return FALLBACK_PROVIDER;
  }

  if (key === SYSTEM_PROVIDER) {
    return SYSTEM_PROVIDER;
  }

  if (LEGACY_CORE_RUNTIME_ALIASES.has(key)) {
    return key;
  }

  return key.replace(/-/g, '_');
};

export const isBuiltInRuntimeProvider = (provider?: string | null): boolean => {
  const normalized = normalizeProviderName(provider);
  return normalized === BUILTIN_TRANSFORMERS_PROVIDER || normalized === BUILTIN_VLLM_PROVIDER;
};

export const isTransformersRuntimeProvider = (provider?: string | null): boolean => {
  return normalizeProviderName(provider) === BUILTIN_TRANSFORMERS_PROVIDER;
};

export const isVllmRuntimeProvider = (provider?: string | null): boolean => {
  return normalizeProviderName(provider) === BUILTIN_VLLM_PROVIDER;
};

export const isLegacyRuntimeProvider = (provider?: string | null): boolean => {
  const rawKey = toProviderKey(provider);
  const normalized = normalizeProviderName(provider);
  return LEGACY_CORE_RUNTIME_ALIASES.has(rawKey) || LEGACY_CORE_RUNTIME_ALIASES.has(normalized);
};

export const isLocalRuntimeProvider = (provider?: string | null): boolean => {
  return isBuiltInRuntimeProvider(provider);
};

export const isExternalGgufProvider = (provider?: string | null): boolean => {
  return normalizeProviderName(provider) === LOCAL_GGUF_PROVIDER;
};

export const isOpenAiCompatibleProvider = (provider?: string | null): boolean => {
  return normalizeProviderName(provider) === OPENAI_COMPATIBLE_PROVIDER;
};

export const isExternalEndpointProvider = (provider?: string | null): boolean => {
  const normalized = normalizeProviderName(provider);
  return normalized === OPENAI_COMPATIBLE_PROVIDER || normalized === LOCAL_GGUF_PROVIDER || normalized === 'openai';
};

export const getRuntimeDisplayName = (
  provider?: string | null,
  displayName?: string | null,
): string => {
  const normalized = normalizeProviderName(provider);
  const explicit = toCleanString(displayName);

  if (normalized === BUILTIN_TRANSFORMERS_PROVIDER) {
    return 'Transformers';
  }

  if (normalized === BUILTIN_VLLM_PROVIDER) {
    return 'vLLM';
  }

  if (normalized === OPENAI_COMPATIBLE_PROVIDER) {
    return explicit || 'OpenAI-Compatible Endpoint';
  }

  if (normalized === LOCAL_GGUF_PROVIDER) {
    return explicit || 'GGUF External Endpoint';
  }

  if (normalized === FALLBACK_PROVIDER) {
    return 'Local Emergency Fallback';
  }

  if (normalized === SYSTEM_PROVIDER) {
    return 'Runtime Control';
  }

  if (isLegacyRuntimeProvider(provider)) {
    return `Legacy External Runtime (${toCleanString(provider) || normalized})`;
  }

  return explicit || toCleanString(provider) || normalized;
};

export const getRuntimeGroupLabel = (provider?: string | null): string => {
  const normalized = normalizeProviderName(provider);

  if (normalized === BUILTIN_TRANSFORMERS_PROVIDER || normalized === BUILTIN_VLLM_PROVIDER) {
    return 'Built-in Runtime';
  }

  if (normalized === OPENAI_COMPATIBLE_PROVIDER || normalized === 'openai') {
    return 'External Endpoint';
  }

  if (normalized === LOCAL_GGUF_PROVIDER) {
    return 'External GGUF';
  }

  if (normalized === FALLBACK_PROVIDER) {
    return 'Fallback';
  }

  if (normalized === SYSTEM_PROVIDER) {
    return 'System';
  }

  if (isLegacyRuntimeProvider(provider)) {
    return 'Legacy External Runtime';
  }

  return 'Custom';
};

export const normalizeModelName = (model?: string | null): string => {
  const value = toCleanString(model).toLowerCase();

  if (!value) {
    return '';
  }

  const withoutProvider = value.includes(':') ? value.split(':').pop() || value : value;

  return withoutProvider
    .replace(/\.(gguf|bin|safetensors)$/i, '')
    .replace(/_/g, '-')
    .trim();
};

export const getDisplayModelName = (
  modelId?: string | null,
  modelName?: string | null,
): string => {
  const explicitName = toCleanString(modelName);

  if (explicitName) {
    return explicitName;
  }

  const rawModelId = toCleanString(modelId);

  if (!rawModelId) {
    return '';
  }

  return rawModelId
    .split(':')
    .pop()
    ?.split('/')
    .pop()
    ?.replace(/\.(gguf|bin|safetensors)$/i, '')
    .replace(/[-_]/g, ' ')
    .trim() || rawModelId;
};

const getFriendlyProviderLabel = (
  provider?: string | null,
): string => {
  return getRuntimeDisplayName(provider, provider);
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

const isLocalFallbackSource = (llm: Record<string, any>): boolean => {
  const source = toCleanString(llm?.source);
  const fallbackLevel = toCleanString(llm?.fallback_level).toLowerCase();
  const provider = normalizeProviderName(llm?.provider);
  const model = normalizeModelName(llm?.model_id || llm?.model_name);

  return (
    LOCAL_FALLBACK_SOURCES.has(source) ||
    fallbackLevel === 'local' ||
    fallbackLevel === 'emergency' ||
    fallbackLevel === 'degraded' ||
    provider === FALLBACK_PROVIDER ||
    model === 'kari-fallback-v1' ||
    model === 'karen-fallback-v1' ||
    model === 'emergency-fallback' ||
    model === 'lite-assistant-fallback'
  );
};

const isKnownRuntimeControlMode = (mode?: string | null): boolean => {
  const runtimeMode = toCleanString(mode);
  return runtimeMode === 'maintenance' || runtimeMode === 'emergency_fallback' || runtimeMode === 'degraded';
};

const reasonLooksUnavailable = (reason?: string | null): boolean => {
  const lower = toCleanString(reason).toLowerCase();

  return (
    lower.includes('unavailable') ||
    lower.includes('connection refused') ||
    lower.includes('connection reset') ||
    lower.includes('timeout') ||
    lower.includes('timed out') ||
    lower.includes('host.docker.internal') ||
    lower.includes('172.17.0.1') ||
    lower.includes('127.0.0.1') ||
    lower.includes('localhost') ||
    lower.includes('loopback') ||
    lower.includes('econnrefused') ||
    lower.includes('enetunreach') ||
    lower.includes('service not ready') ||
    lower.includes('provider not ready') ||
    lower.includes('model not loaded') ||
    lower.includes('model load failed')
  );
};

const reasonLooksRateLimited = (reason?: string | null): boolean => {
  const lower = toCleanString(reason).toLowerCase();

  return (
    lower.includes('rate limit') ||
    lower.includes('ratelimit') ||
    lower.includes('too many requests') ||
    lower.includes('429') ||
    lower.includes('quota') ||
    lower.includes('insufficient balance') ||
    lower.includes('resource package')
  );
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

export const sanitizeStructuredContent = (
  structuredContent?: Record<string, any> | null,
): Record<string, any> => {
  const source = isRecord(structuredContent) ? structuredContent : {};

  return Object.fromEntries(
    Object.entries(source).filter(([key]) => !INTERNAL_STRUCTURED_CONTENT_KEYS.has(key)),
  );
};

export const deriveDegradedPresentation = (
  metadata?: Record<string, any>,
): DegradedPresentation => {
  const safeMetadata = isRecord(metadata) ? metadata : {};
  const llm = isRecord(safeMetadata?.llm) ? safeMetadata.llm : {};

  const failureCategory = toCleanString(safeMetadata?.failure_category || llm?.failure_category);
  const isSafetyBlocked = failureCategory === 'safety_blocked';

  const usedFallback =
    safeMetadata?.orchestrator?.used_fallback === true ||
    llm?.used_fallback === true ||
    llm?.is_fallback === true;

  const localFallbackSource = isLocalFallbackSource(llm);

  const requestedProvider = toCleanString(llm?.requested_provider);
  const requestedModel = toCleanString(llm?.requested_model);
  const actualProvider = toCleanString(llm?.provider);
  const actualModelId = toCleanString(llm?.model_id);
  const actualModel = getFriendlyModelLabel(llm?.model_id, llm?.model_name);

  const normalizedActualProvider = normalizeProviderName(actualProvider);
  const normalizedRequestedProvider = normalizeProviderName(requestedProvider);
  const normalizedRequestedModel = normalizeModelName(requestedModel);
  const normalizedActualModel = normalizeModelName(llm?.model_id || llm?.model_name || actualModel);

  const isLegacyMismatch =
    isLegacyRuntimeProvider(requestedProvider) || isLegacyRuntimeProvider(actualProvider);

  const providerChanged = Boolean(
    normalizedRequestedProvider &&
      normalizedActualProvider &&
      normalizedRequestedProvider !== normalizedActualProvider,
  );

  const modelChanged = Boolean(
    normalizedRequestedModel &&
      normalizedActualModel &&
      normalizedRequestedModel !== normalizedActualModel,
  );

  const preferredFailureReason = toCleanString(llm?.preferred_failure_reason);
  const failureReason = toCleanString(
    preferredFailureReason ||
      llm?.failure_reason ||
      safeMetadata?.failure_reason ||
      safeMetadata?.error,
  );

  const isDegraded =
    safeMetadata?.degraded_mode === true ||
    llm?.is_degraded === true ||
    usedFallback ||
    localFallbackSource ||
    providerChanged ||
    modelChanged ||
    isLegacyMismatch ||
    isKnownRuntimeControlMode(safeMetadata?.mode);

  const hasLlmInfo = Boolean(llm && (llm.provider || llm.model_id || llm.model_name));

  const isExternalGgufBackedFallback =
    normalizedActualProvider === FALLBACK_PROVIDER &&
    actualModelId.toLowerCase().startsWith(`${LOCAL_GGUF_PROVIDER}:`);

  const actualProviderLabel = isExternalGgufBackedFallback
    ? 'GGUF External Endpoint'
    : getFriendlyProviderLabel(actualProvider);

  const fallbackTargetLabel = getFallbackTargetLabel(actualProviderLabel, actualModel);

  const selectedRuntimeUnavailable =
    Boolean(requestedProvider) && reasonLooksUnavailable(failureReason);

  const providerOrModelChanged = providerChanged || modelChanged || isLegacyMismatch;

  const degradedStatusLabel = isSafetyBlocked
    ? 'provider policy block'
    : reasonLooksRateLimited(failureReason)
      ? `${requestedProvider || 'provider'} rate limited`
      : selectedRuntimeUnavailable
        ? `${requestedProvider || 'provider'} unavailable`
        : isLegacyMismatch
          ? 'legacy runtime'
          : providerOrModelChanged
            ? 'provider fallback'
            : isDegraded
              ? 'degraded mode'
              : '';

  const degradedBannerText = isSafetyBlocked
    ? 'Provider policy blocked this response.'
    : isLegacyMismatch
      ? 'A legacy runtime was requested. Core llama.cpp/Ollama aliases are no longer normalized into local_gguf. Configure that service as an explicit external endpoint.'
      : selectedRuntimeUnavailable
        ? `Selected runtime is unavailable from the API container, so Karen switched to ${fallbackTargetLabel}.`
        : requestedProvider && isExternalGgufBackedFallback && normalizedRequestedProvider === LOCAL_GGUF_PROVIDER
          ? `${getFriendlyProviderLabel(requestedProvider)} primary path failed, recovered via explicit GGUF external fallback path${actualModel ? ` (${actualModel})` : ''}.`
          : requestedProvider && actualProvider && providerOrModelChanged
            ? `${getFriendlyProviderLabel(requestedProvider)} failed, switched to ${fallbackTargetLabel}.`
            : requestedProvider && reasonLooksRateLimited(failureReason)
              ? `${getFriendlyProviderLabel(requestedProvider)} rate limited, switched to ${fallbackTargetLabel}.`
              : failureReason
                ? failureReason
                : isDegraded
                  ? `Requested provider ${requestedProvider || 'primary'} was unavailable; Karen continued in degraded mode.`
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
    isLocalFallbackSource: localFallbackSource,
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
  const safeMetadata = isRecord(metadata) ? metadata : {};
  const llm = isRecord(safeMetadata?.llm) ? safeMetadata.llm : {};
  const degraded = deriveDegradedPresentation(safeMetadata);
  const usage = isRecord(llm?.usage) ? llm.usage : {};

  const promptTokens = Number(usage.prompt_tokens || 0);
  const completionTokens = Number(usage.completion_tokens || 0);
  const totalTokens = Number(usage.total_tokens || 0);

  const hasMetadataDetails = Boolean(safeMetadata && Object.keys(safeMetadata).length > 0);
  const providerLabel = degraded.providerDisplayName;
  const modelLabel = degraded.modelDisplayName;
  const modelTitle = toCleanString(llm?.model_id || llm?.model_name);
  const sourceLabel = toCleanString(llm?.source || 'direct');

  const speedLabel = llm?.tokens_per_second
    ? `${Number(llm.tokens_per_second).toFixed(2)} tok/s`
    : 'N/A';

  const latencyLabel =
    typeof llm?.duration === 'number'
      ? `${llm.duration.toFixed(2)}s`
      : typeof safeMetadata?.total_ms === 'number'
        ? `${(safeMetadata.total_ms / 1000).toFixed(2)}s`
        : 'N/A';

  const engineHeaderLabel = providerLabel;
  const showStatusRow = degraded.shouldRenderDegradedState;
  const statusLabel = degraded.detailsStatusLabel;
  const showFallbackRow = degraded.shouldRenderFallbackDetails;
  const fallbackLabel = degraded.fallbackDetailsText;
  const showReasonRow = Boolean(degraded.failureReason);
  const reasonLabel = degraded.failureReason;
  const showTokensRow = Boolean(llm?.usage);

  const tokensLabel = promptTokens || completionTokens
    ? `${promptTokens}i + ${completionTokens}o`
    : totalTokens
      ? `${totalTokens} total`
      : 'N/A';

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
  const safeMetadata = isRecord(metadata) ? metadata : {};
  const llm = isRecord(safeMetadata?.llm) ? safeMetadata.llm : {};
  const degraded = deriveDegradedPresentation(safeMetadata);

  const hasMetadataDetails = Boolean(safeMetadata && Object.keys(safeMetadata).length > 0);
  const hasLlmInfo = degraded.hasLlmInfo;

  const shouldRenderBadge =
    hasLlmInfo || hasMetadataDetails || safeMetadata?.degraded_mode === true;

  const providerLabel = degraded.providerDisplayName;
  const modelLabel = degraded.modelDisplayName;

  const durationLabel =
    typeof llm?.duration === 'number'
      ? `${llm.duration.toFixed(1)}s`
      : typeof safeMetadata?.total_ms === 'number'
        ? `${(safeMetadata.total_ms / 1000).toFixed(1)}s`
        : '';

  const speedLabel = llm?.tokens_per_second
    ? `${Number(llm.tokens_per_second).toFixed(2)} tok/s`
    : '';

  const statusLabel = degraded.shouldRenderDegradedState
    ? degraded.degradedStatusLabel || 'degraded mode'
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
  const normalized = toCleanString(status).toLowerCase();

  if (normalized === 'failed') {
    return 'failed';
  }

  if (normalized === 'pending') {
    return 'pending';
  }

  if (normalized === 'streaming') {
    return 'streaming';
  }

  return 'completed';
};

const ensureLlmMetadata = (
  metadata: Record<string, any>,
  raw: BackendChatEnvelope,
): Record<string, any> => {
  const llm = isRecord(metadata.llm) ? { ...metadata.llm } : {};

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
  const runtimeMode = toCleanString(raw.mode || metadata.mode);

  if (!runtimeMode) {
    return metadata;
  }

  metadata.mode = runtimeMode;
  metadata.runtime = {
    ...(isRecord(metadata.runtime) ? metadata.runtime : {}),
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

  const llm = isRecord(metadata.llm) ? { ...metadata.llm } : {};

  llm.provider = llm.provider || SYSTEM_PROVIDER;
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
    llm.used_fallback = true;
    llm.fallback_level = runtimeMode === 'maintenance' ? 'maintenance' : 'emergency';
    llm.failure_reason = firstNonEmpty(raw.reason, raw.support_hint, raw.message);
    llm.routing_rationale =
      runtimeMode === 'maintenance'
        ? 'Karen is in planned maintenance mode.'
        : 'Karen is serving the emergency fallback response.';
  } else if (runtimeMode === 'degraded') {
    metadata.degraded_mode = true;
    llm.is_degraded = true;
    llm.used_fallback = true;
    llm.fallback_level = llm.fallback_level || 'degraded';
    llm.failure_reason = llm.failure_reason || toCleanString(raw.reason);
  }

  metadata.llm = llm;
  return metadata;
};

const mergeRequestedRuntimeMetadata = (
  metadata: Record<string, any>,
  options?: {
    requestedProvider?: string;
    requestedModel?: string;
  },
): Record<string, any> => {
  const requestedProvider = toCleanString(options?.requestedProvider);
  const requestedModel = toCleanString(options?.requestedModel);

  if (!requestedProvider && !requestedModel) {
    return metadata;
  }

  const llm = isRecord(metadata.llm) ? { ...metadata.llm } : {};

  if (requestedProvider && !llm.requested_provider) {
    llm.requested_provider = requestedProvider;
  }

  if (requestedModel && !llm.requested_model) {
    llm.requested_model = requestedModel;
  }

  metadata.llm = llm;
  return metadata;
};

const ensureLegacyRuntimeWarning = (
  metadata: Record<string, any>,
): Record<string, any> => {
  const llm = isRecord(metadata.llm) ? { ...metadata.llm } : {};
  const requestedProvider = toCleanString(llm.requested_provider);
  const actualProvider = toCleanString(llm.provider);

  if (!isLegacyRuntimeProvider(requestedProvider) && !isLegacyRuntimeProvider(actualProvider)) {
    return metadata;
  }

  metadata.degraded_mode = true;
  metadata.orchestrator = {
    ...(isRecord(metadata.orchestrator) ? metadata.orchestrator : {}),
    used_fallback: true,
  };

  llm.is_degraded = true;
  llm.used_fallback = true;
  llm.failure_category = llm.failure_category || 'legacy_runtime_removed';
  llm.failure_reason =
    llm.failure_reason ||
    'Legacy core runtimes are no longer normalized into local_gguf. Use builtin_transformers, builtin_vllm, openai_compatible, or an explicit local_gguf endpoint.';

  metadata.llm = llm;
  return metadata;
};

const ensureProviderMismatchMetadata = (
  metadata: Record<string, any>,
  raw: BackendChatEnvelope,
): Record<string, any> => {
  const llm = isRecord(metadata.llm) ? { ...metadata.llm } : {};

  const requestedProvider = normalizeProviderName(llm.requested_provider);
  const requestedModel = normalizeModelName(llm.requested_model);
  const actualProvider = normalizeProviderName(llm.provider);
  const actualModel = normalizeModelName(llm.model_id || llm.model_name);

  const providerChanged = Boolean(
    requestedProvider &&
      actualProvider &&
      requestedProvider !== actualProvider,
  );

  const modelChanged = Boolean(
    requestedModel &&
      actualModel &&
      requestedModel !== actualModel,
  );

  const fallbackUsed =
    raw.used_fallback === true ||
    metadata.orchestrator?.used_fallback === true ||
    llm.is_degraded === true ||
    llm.used_fallback === true ||
    llm.is_fallback === true ||
    isLocalFallbackSource(llm);

  const unavailableFailure = reasonLooksUnavailable(llm.failure_reason || metadata.failure_reason);
  const rateLimitFailure = reasonLooksRateLimited(llm.failure_reason || metadata.failure_reason);

  const isActuallyDegraded =
    fallbackUsed ||
    providerChanged ||
    modelChanged ||
    unavailableFailure ||
    rateLimitFailure ||
    isKnownRuntimeControlMode(metadata.mode);

  if (!isActuallyDegraded) {
    if (Object.keys(llm).length > 0) {
      metadata.llm = llm;
    }

    return metadata;
  }

  metadata.degraded_mode = true;
  metadata.orchestrator = {
    ...(isRecord(metadata.orchestrator) ? metadata.orchestrator : {}),
    used_fallback: true,
  };

  llm.is_degraded = true;
  llm.used_fallback = true;

  if (!llm.failure_category) {
    if (rateLimitFailure) {
      llm.failure_category = 'rate_limited';
    } else if (unavailableFailure) {
      llm.failure_category = 'provider_unavailable';
    } else if (providerChanged || modelChanged) {
      llm.failure_category = 'provider_fallback';
    } else {
      llm.failure_category = 'degraded_runtime';
    }
  }

  if (!llm.failure_reason && providerChanged) {
    const friendlyRequested = getFriendlyProviderLabel(llm.requested_provider);
    const friendlyActual = getFriendlyProviderLabel(llm.provider);

    llm.failure_reason =
      `Selected provider ${friendlyRequested} was unavailable; Karen continued with ${friendlyActual}.`;
  }

  if (!llm.failure_reason && modelChanged) {
    const requestedLabel = getFriendlyModelLabel(llm.requested_model, llm.requested_model);
    const actualLabel = getFriendlyModelLabel(llm.model_id, llm.model_name);

    llm.failure_reason =
      `Selected model ${requestedLabel} was unavailable; Karen continued with ${actualLabel}.`;
  }

  if (!llm.failure_reason && unavailableFailure) {
    llm.failure_reason = 'Selected provider was unavailable; Karen continued with a fallback runtime.';
  }

  if (!llm.failure_reason && rateLimitFailure) {
    llm.failure_reason = 'Selected provider was rate limited or quota blocked; Karen continued with a fallback runtime.';
  }

  metadata.llm = llm;
  return metadata;
};

const ensurePersistenceMetadata = (
  metadata: Record<string, any>,
): Record<string, any> => {
  const existingPersistence = isRecord(metadata.persistence) ? metadata.persistence : {};

  metadata.persistence = {
    canonical_store: existingPersistence.canonical_store || 'postgres',
    assistant_persisted:
      existingPersistence.assistant_persisted ??
      Boolean(metadata.assistant_message_id),
    ...existingPersistence,
  };

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
  const correlationId = firstNonEmpty(
    raw.correlation_id,
    raw.request_id,
    raw.response_id,
    isRecord(raw.metadata) ? raw.metadata.correlation_id : undefined,
    `assistant-${Date.now()}`,
  );

  const metadata: Record<string, any> = isRecord(raw.metadata) ? { ...raw.metadata } : {};

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
      ...(isRecord(metadata.orchestrator) ? metadata.orchestrator : {}),
      used_fallback: raw.used_fallback,
    };
  }

  ensurePersistenceMetadata(metadata);
  ensureLlmMetadata(metadata, raw);
  ensureRuntimeModeMetadata(metadata, raw);
  mergeRequestedRuntimeMetadata(metadata, options);
  ensureLegacyRuntimeWarning(metadata);
  ensureProviderMismatchMetadata(metadata, raw);

  const fallbackAnswer =
    firstNonEmpty(raw.message) ||
    (toCleanString(raw.mode) === 'maintenance'
      ? 'Karen is temporarily unavailable while scheduled maintenance is in progress.'
      : toCleanString(raw.mode) === 'emergency_fallback'
        ? 'Karen is temporarily unavailable. Please try again shortly.'
        : 'Karen returned an empty response.');

  return {
    answer: answer || sanitizeChatContent(fallbackAnswer),
    structuredContent: sanitizeStructuredContent(
      raw.structured_content || raw.structuredContent || {},
    ),
    actions: Array.isArray(raw.actions) ? raw.actions : [],
    metadata,
    correlationId,
  };
}

export function normalizeConversationMessage(
  message: MessageResponse,
): ChatMessage {
  const metadata: Record<string, any> = isRecord(message.metadata) ? { ...message.metadata } : {};

  if (message.ui_source && !metadata.ui_source) {
    metadata.ui_source = message.ui_source;
  }

  if (typeof message.processing_time_ms === 'number' && metadata.total_ms == null) {
    metadata.total_ms = message.processing_time_ms;
  }

  if (message.model_used || typeof message.tokens_used === 'number') {
    metadata.llm = {
      ...(isRecord(metadata.llm) ? metadata.llm : {}),
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
    actions: Array.isArray(message.actions) ? message.actions : [],
    metadata,
  };
}