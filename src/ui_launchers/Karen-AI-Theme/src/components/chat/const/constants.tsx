// Chat Interface Constants

export const CHAT_INPUT_PLACEHOLDER = "Message Karen...";
export const CHAT_INPUT_DISABLED_PLACEHOLDER =
  "Karen is processing your previous message...";

export const DEFAULT_CHAT_TITLE = "New Chat";
export const DEFAULT_SESSION_LABEL = "Current Session";

export const CHAT_SCROLL_BOTTOM_THRESHOLD_PX = 96;
export const CHAT_HISTORY_PAGE_SIZE = 30;
export const MAX_VISIBLE_SOURCES = 6;
export const MAX_VISIBLE_TOOL_EVENTS = 8;

export const USER_MESSAGE_ROLE = "user";
export const ASSISTANT_MESSAGE_ROLE = "assistant";
export const SYSTEM_MESSAGE_ROLE = "system";
export const TOOL_MESSAGE_ROLE = "tool";

export const CHAT_MESSAGE_ROLES = {
  user: USER_MESSAGE_ROLE,
  assistant: ASSISTANT_MESSAGE_ROLE,
  system: SYSTEM_MESSAGE_ROLE,
  tool: TOOL_MESSAGE_ROLE,
} as const;

export type ChatMessageRole = keyof typeof CHAT_MESSAGE_ROLES;

export const DEFAULT_PROVIDER_LABEL = "Backend selected";
export const DEFAULT_MODEL_LABEL = "Runtime selected";

export const RUNTIME_METADATA_KEYS = {
  degradedMode: "degraded_mode",
  degradationReason: "degradation_reason",
  requestedProvider: "requested_provider",
  requestedModel: "requested_model",
  actualProvider: "actual_provider",
  actualModel: "actual_model",
  runtimeEngine: "runtime_engine",
  fallbackLevel: "fallback_level",
  responseSource: "response_source",
  latencyMs: "latency_ms",
  correlationId: "correlation_id",
} as const;

export const CHAT_LOCAL_STORAGE_KEYS = {
  sidebarCollapsed: "karen.chat.sidebarCollapsed",
  activeConversationId: "karen.chat.activeConversationId",
  draftMessage: "karen.chat.draftMessage",
} as const;

// -----------------------------------------------------------------------------
// Chat response mode / streaming constants
// -----------------------------------------------------------------------------

export const CHAT_RESPONSE_MODE = {
  STREAMING_FIRST: "streaming_first",
  AUTO: "auto",
  NON_STREAMING: "non_streaming",
} as const;

export type ChatResponseMode =
  (typeof CHAT_RESPONSE_MODE)[keyof typeof CHAT_RESPONSE_MODE];

export const CHAT_RESPONSE_MODE_LABELS: Record<ChatResponseMode, string> = {
  [CHAT_RESPONSE_MODE.STREAMING_FIRST]: "Streaming first",
  [CHAT_RESPONSE_MODE.AUTO]: "Auto",
  [CHAT_RESPONSE_MODE.NON_STREAMING]: "Non-streaming JSON",
};

export const CHAT_RESPONSE_MODE_DESCRIPTIONS: Record<
  ChatResponseMode,
  string
> = {
  [CHAT_RESPONSE_MODE.STREAMING_FIRST]:
    "Recommended. Karen streams status updates and live content when the provider supports it.",
  [CHAT_RESPONSE_MODE.AUTO]:
    "Karen chooses the best response mode based on provider and client capability.",
  [CHAT_RESPONSE_MODE.NON_STREAMING]:
    "Karen waits for the full response before returning JSON. Useful for legacy clients and debugging.",
};

export const DEFAULT_CHAT_RESPONSE_MODE: ChatResponseMode =
  CHAT_RESPONSE_MODE.STREAMING_FIRST;

export const CHAT_TRANSPORT = {
  SSE: "sse",
  JSON: "json",
  UNKNOWN: "unknown",
} as const;

export type ChatTransport = (typeof CHAT_TRANSPORT)[keyof typeof CHAT_TRANSPORT];

export const STREAM_EVENT_TYPE = {
  STATUS: "status",
  CONTENT: "content",
  COMPLETE: "complete",
  ERROR: "error",
  DONE: "[DONE]",
} as const;

export type StreamEventType =
  (typeof STREAM_EVENT_TYPE)[keyof typeof STREAM_EVENT_TYPE];

export const STREAMING_FALLBACK_REASON_LABELS: Record<string, string> = {
  admin_disabled_streaming: "Streaming disabled by admin setting",
  provider_does_not_support_token_streaming:
    "Provider does not support token streaming",
  provider_unavailable: "Requested provider unavailable",
  requested_provider_unavailable: "Requested provider unavailable",
  requested_provider_failed_or_placeholder:
    "Requested provider failed or returned unusable content",
  all_live_providers_unavailable: "All live providers unavailable",
  stream_error: "Streaming connection error",
};

// -----------------------------------------------------------------------------
// Provider/runtime identity constants
// -----------------------------------------------------------------------------
//
// These labels are display-only.
// Do not use these maps to rewrite provider IDs sent to or received from backend.
// Backend provider identity remains the source of truth.

export const PROVIDER_ID = {
  BUILTIN_VLLM: "builtin_vllm",
  TRANSFORMERS: "transformers",
  OLLAMA: "ollama",
  GEMINI: "gemini",
  ZAI: "zai",
  OPENAI: "openai",
  ANTHROPIC: "anthropic",
  EMERGENCY_STATIC: "emergency_static",
  SYSTEM: "system",
  UNKNOWN: "unknown",
} as const;

export type ProviderId = (typeof PROVIDER_ID)[keyof typeof PROVIDER_ID];

export const RUNTIME_ENGINE = {
  VLLM: "vllm",
  TRANSFORMERS: "transformers",
  OLLAMA: "ollama",
  GEMINI: "gemini",
  ZAI: "zai",
  OPENAI: "openai",
  ANTHROPIC: "anthropic",
  EXTERNAL_API: "external_api",
  NONE: "none",
  UNKNOWN: "unknown",
} as const;

export type RuntimeEngine =
  (typeof RUNTIME_ENGINE)[keyof typeof RUNTIME_ENGINE];

export const PROVIDER_DISPLAY_LABELS: Record<string, string> = {
  [PROVIDER_ID.BUILTIN_VLLM]: "vLLM",
  [PROVIDER_ID.TRANSFORMERS]: "Transformers",
  [PROVIDER_ID.OLLAMA]: "Ollama",
  [PROVIDER_ID.GEMINI]: "Gemini",
  [PROVIDER_ID.ZAI]: "Z.AI",
  [PROVIDER_ID.OPENAI]: "OpenAI",
  [PROVIDER_ID.ANTHROPIC]: "Anthropic",
  [PROVIDER_ID.EMERGENCY_STATIC]: "Emergency Static",
  [PROVIDER_ID.SYSTEM]: "System",
  [PROVIDER_ID.UNKNOWN]: "Unknown",
};

export const RUNTIME_ENGINE_DISPLAY_LABELS: Record<string, string> = {
  [RUNTIME_ENGINE.VLLM]: "vLLM",
  [RUNTIME_ENGINE.TRANSFORMERS]: "Transformers",
  [RUNTIME_ENGINE.OLLAMA]: "Ollama",
  [RUNTIME_ENGINE.GEMINI]: "Gemini",
  [RUNTIME_ENGINE.ZAI]: "Z.AI",
  [RUNTIME_ENGINE.OPENAI]: "OpenAI",
  [RUNTIME_ENGINE.ANTHROPIC]: "Anthropic",
  [RUNTIME_ENGINE.EXTERNAL_API]: "External API",
  [RUNTIME_ENGINE.NONE]: "None",
  [RUNTIME_ENGINE.UNKNOWN]: "Unknown",
};

export const RESPONSE_SOURCE = {
  LIVE_MODEL: "live_model",
  DEGRADED_LIVE_MODEL: "degraded_live_model",
  DETERMINISTIC_FALLBACK: "deterministic_fallback",
  EMERGENCY_STATIC: "emergency_static",
  RUNTIME_CONTROL_PLANE: "runtime_control_plane",
  REQUESTED_MODEL: "requested_model",
  UNKNOWN: "unknown",
} as const;

export type ResponseSource =
  (typeof RESPONSE_SOURCE)[keyof typeof RESPONSE_SOURCE];

export const RESPONSE_SOURCE_DISPLAY_LABELS: Record<string, string> = {
  [RESPONSE_SOURCE.LIVE_MODEL]: "Live model",
  [RESPONSE_SOURCE.DEGRADED_LIVE_MODEL]: "Degraded live model",
  [RESPONSE_SOURCE.DETERMINISTIC_FALLBACK]: "Deterministic fallback",
  [RESPONSE_SOURCE.EMERGENCY_STATIC]: "Emergency static",
  [RESPONSE_SOURCE.RUNTIME_CONTROL_PLANE]: "Runtime control plane",
  [RESPONSE_SOURCE.REQUESTED_MODEL]: "Requested model",
  [RESPONSE_SOURCE.UNKNOWN]: "Unknown",
};

export const DEGRADED_REASON_LABELS: Record<string, string> = {
  requested_provider_unavailable: "Requested provider unavailable",
  requested_provider_failed_or_placeholder:
    "Requested provider failed or returned unusable content",
  builtin_vllm_unavailable: "Built-in vLLM unavailable",
  provider_unavailable: "Provider unavailable",
  provider_timeout: "Provider timed out",
  missing_api_key: "Missing API key",
  model_unavailable: "Model unavailable",
  all_live_providers_unavailable: "All live providers unavailable",
  runtime_control_plane_unavailable: "Runtime control plane unavailable",
  gemini_unavailable: "Gemini unavailable",
  openai_unavailable: "OpenAI unavailable",
  anthropic_unavailable: "Anthropic unavailable",
};

export const getDegradationReasonLabel = (reason: unknown): string => {
  const normalized = typeof reason === "string" ? reason.trim().toLowerCase() : String(reason ?? "").trim().toLowerCase();

  if (!normalized) {
    return "";
  }

  if (DEGRADED_REASON_LABELS[normalized]) {
    return DEGRADED_REASON_LABELS[normalized];
  }

  if (normalized.endsWith("_unavailable")) {
    return `${normalized.replace(/_unavailable$/, "").replace(/_/g, " ")} unavailable`;
  }

  return normalized.replace(/_/g, " ");
};

// -----------------------------------------------------------------------------
// Backward-safe re-exports
// -----------------------------------------------------------------------------

export {
  ACTIVE_STREAMING_PHASES,
  BUSY_PROCESSING_STATES,
  DEFAULT_PROCESSING_MESSAGE,
  STREAMING_ERROR_MESSAGE,
  STREAM_TIMEOUT_MESSAGE,
  getProcessingDisplay,
  getProcessingIcon,
  getProcessingToneClassName,
  getStreamingDisplay,
  getStreamingIcon,
  getStreamingToneClassName,
  isActiveStreamingPhase,
  isBusyProcessingState,
  normalizeProcessingState,
  normalizeProcessingStatusKey,
  normalizeStreamingPhase,
  resolveProcessingStatusMessage,
} from "./processing";

export type {
  ChatProcessingDisplay,
  ChatProcessingState,
  ChatStreamingDisplay,
  ChatStreamingPhase,
} from "./processing";

// -----------------------------------------------------------------------------
// UI Constants
// -----------------------------------------------------------------------------

export const MAX_RECENT_MESSAGES = 6;
export const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes
export const RENEWAL_INTERVAL = 5 * 60 * 1000; // 5 minutes
export const CLEANUP_INTERVAL = 24 * 60 * 60 * 1000; // 24 hours
export const INACTIVE_THRESHOLD = 7 * 24 * 60 * 60 * 1000; // 7 days
export const STICK_TO_BOTTOM_THRESHOLD = 120; // pixels
