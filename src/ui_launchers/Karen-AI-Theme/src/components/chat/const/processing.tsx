import type { ReactNode } from "react";
import {
  AlertCircle,
  Bot,
  BrainCircuit,
  CheckCircle2,
  Clock,
  Loader2,
  RadioTower,
  Sparkles,
  Wrench,
  Zap,
} from "lucide-react";

export const DEFAULT_PROCESSING_MESSAGE = "Karen is working on your request...";
export const STREAMING_ERROR_MESSAGE = "Connection issue - please try again";
export const STREAM_TIMEOUT_MESSAGE = "Request timed out - please try again";

// -----------------------------------------------------------------------------
// Processing status messages
// -----------------------------------------------------------------------------

export const PROCESSING_STATUS_MESSAGE_VARIANTS: Record<string, string[]> = {
  initializing: [
    "Karen is preparing your workspace...",
    "Karen is initializing the request pipeline...",
  ],
  processing: [
    "Karen is analyzing your message...",
    "Karen is understanding what you need...",
  ],
  extracting_context: [
    "Karen is retrieving relevant context and memories...",
    "Karen is gathering useful conversation context...",
  ],
  provider_selection: [
    "Karen is selecting the best available provider...",
    "Karen is checking provider availability...",
  ],
  provider_selected: [
    "Karen selected a live provider...",
    "Karen found a provider that can answer...",
  ],
  provider_unavailable: [
    "Karen could not reach the requested provider...",
    "The requested provider is unavailable, Karen is checking fallbacks...",
  ],
  fallback_started: [
    "Karen is trying a fallback provider...",
    "Karen is recovering through an available provider...",
  ],
  fallback_succeeded: [
    "Karen recovered through a live fallback provider...",
    "Karen found a working fallback provider...",
  ],
  generating_response: [
    "Karen is generating a response...",
    "Karen is drafting your answer...",
  ],
  streaming: [
    "Karen is composing the response...",
    "Karen is streaming the response...",
  ],
  executing_tools: [
    "Karen is executing tools and integrations...",
    "Karen is running supporting tasks...",
  ],
  recording_memory: [
    "Karen is recording insights from this conversation...",
    "Karen is saving useful context for next time...",
  ],
  post_processing: [
    "Karen is finalizing the response...",
    "Karen is polishing the final output...",
  ],
  retrying: [
    "Karen is retrying with an alternative provider...",
    "Karen is recovering from a temporary issue...",
  ],
  degraded: [
    "Karen is running in degraded mode...",
    "Karen is operating with limited capabilities...",
  ],
  degraded_live: [
    "Karen is answering through a degraded live provider...",
    "Karen is using a limited live fallback path...",
  ],
  emergency_static: [
    "Karen is using the emergency fallback response...",
    "All live providers are unavailable, Karen is using a safe fallback reply...",
  ],
  completed: ["Response complete."],
  failed: ["Processing failed. Retrying or falling back..."],
  cancelled: ["Request was cancelled."],
};

// -----------------------------------------------------------------------------
// Chat processing / streaming presentation
// -----------------------------------------------------------------------------

export type ChatProcessingState =
  | "idle"
  | "queued"
  | "preparing"
  | "thinking"
  | "routing"
  | "retrieving_memory"
  | "calling_tool"
  | "streaming"
  | "finalizing"
  | "complete"
  | "error"
  | "degraded";

export type ChatStreamingPhase =
  | "idle"
  | "connecting"
  | "connected"
  | "receiving"
  | "reconnecting"
  | "complete"
  | "error";

export type ChatProcessingDisplay = {
  label: string;
  description: string;
  icon: ReactNode;
  toneClassName: string;
  isBusy: boolean;
};

export type ChatStreamingDisplay = {
  label: string;
  description: string;
  icon: ReactNode;
  toneClassName: string;
  isActive: boolean;
};

export const PROCESSING_STATE_LABELS: Record<ChatProcessingState, string> = {
  idle: "Ready",
  queued: "Queued",
  preparing: "Preparing",
  thinking: "Thinking",
  routing: "Routing",
  retrieving_memory: "Recalling memory",
  calling_tool: "Using tool",
  streaming: "Responding",
  finalizing: "Finalizing",
  complete: "Complete",
  error: "Error",
  degraded: "Degraded",
};

export const PROCESSING_STATE_DESCRIPTIONS: Record<ChatProcessingState, string> = {
  idle: "Karen is ready for the next message.",
  queued: "Your request is waiting for the runtime.",
  preparing: "Karen is preparing the request context.",
  thinking: "Karen is reasoning through the request.",
  routing: "Karen is selecting the backend execution path.",
  retrieving_memory: "Karen is checking relevant memory and context.",
  calling_tool: "Karen is waiting for a backend tool or plugin.",
  streaming: "Karen is streaming the response.",
  finalizing: "Karen is finalizing metadata, persistence, and response state.",
  complete: "The response completed successfully.",
  error: "The request failed before a complete response was produced.",
  degraded: "Karen continued with a backend-reported degraded runtime path.",
};

export const STREAMING_PHASE_LABELS: Record<ChatStreamingPhase, string> = {
  idle: "Idle",
  connecting: "Connecting",
  connected: "Connected",
  receiving: "Receiving",
  reconnecting: "Reconnecting",
  complete: "Complete",
  error: "Stream error",
};

export const STREAMING_PHASE_DESCRIPTIONS: Record<ChatStreamingPhase, string> = {
  idle: "No active stream.",
  connecting: "Opening the chat stream.",
  connected: "The stream is connected.",
  receiving: "Receiving response tokens.",
  reconnecting: "Attempting to reconnect the stream.",
  complete: "The stream completed.",
  error: "The stream failed.",
};

export const BUSY_PROCESSING_STATES = new Set<ChatProcessingState>([
  "queued",
  "preparing",
  "thinking",
  "routing",
  "retrieving_memory",
  "calling_tool",
  "streaming",
  "finalizing",
]);

export const ACTIVE_STREAMING_PHASES = new Set<ChatStreamingPhase>([
  "connecting",
  "connected",
  "receiving",
  "reconnecting",
]);

export const normalizeProcessingStatusKey = (status: unknown): string => {
  if (status == null) return "";

  if (typeof status === "string") {
    return status.trim().toLowerCase().replace(/[\s-]+/g, "_");
  }

  if (typeof status === "object" && status !== null && "value" in status) {
    const value = (status as { value?: unknown }).value;

    if (typeof value === "string") {
      return value.trim().toLowerCase().replace(/[\s-]+/g, "_");
    }
  }

  return String(status).trim().toLowerCase().replace(/[\s-]+/g, "_");
};

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
};

const toCleanString = (value: unknown): string => {
  return typeof value === "string" ? value.trim() : String(value ?? "").trim();
};

const formatProviderLabel = (provider: unknown): string => {
  const normalized = normalizeProcessingStatusKey(provider).replace(/_/g, " ");

  if (!normalized) {
    return "";
  }

  if (normalized === "builtin vllm" || normalized === "vllm") return "vLLM";
  if (normalized === "builtin transformers" || normalized === "transformers") return "Transformers";
  if (normalized === "ollama") return "Ollama";
  if (normalized === "openai compatible") return "OpenAI-compatible provider";
  if (normalized === "emergency static") return "emergency fallback";

  return normalized;
};

export function normalizeProcessingState(
  state: ChatProcessingState | string | null | undefined,
): ChatProcessingState {
  const normalized = String(state || "idle")
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_");

  if (normalized in PROCESSING_STATE_LABELS) {
    return normalized as ChatProcessingState;
  }

  if (normalized.includes("memory") || normalized.includes("recall")) {
    return "retrieving_memory";
  }

  if (normalized.includes("tool") || normalized.includes("plugin")) {
    return "calling_tool";
  }

  if (normalized.includes("stream") || normalized.includes("token")) {
    return "streaming";
  }

  if (normalized.includes("route") || normalized.includes("provider")) {
    return "routing";
  }

  if (normalized.includes("degraded") || normalized.includes("fallback")) {
    return "degraded";
  }

  if (normalized.includes("error") || normalized.includes("fail")) {
    return "error";
  }

  if (normalized.includes("complete") || normalized.includes("done")) {
    return "complete";
  }

  if (normalized.includes("think") || normalized.includes("reason")) {
    return "thinking";
  }

  return "idle";
}

export function normalizeStreamingPhase(
  phase: ChatStreamingPhase | string | null | undefined,
): ChatStreamingPhase {
  const normalized = String(phase || "idle")
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_");

  if (normalized in STREAMING_PHASE_LABELS) {
    return normalized as ChatStreamingPhase;
  }

  if (normalized.includes("connect") && normalized.includes("re")) {
    return "reconnecting";
  }

  if (normalized.includes("connect")) {
    return "connecting";
  }

  if (normalized.includes("receive") || normalized.includes("stream") || normalized.includes("token")) {
    return "receiving";
  }

  if (normalized.includes("complete") || normalized.includes("done")) {
    return "complete";
  }

  if (normalized.includes("error") || normalized.includes("fail")) {
    return "error";
  }

  return "idle";
}

export function isBusyProcessingState(state: ChatProcessingState | string | null | undefined): boolean {
  return BUSY_PROCESSING_STATES.has(normalizeProcessingState(state));
}

export function isActiveStreamingPhase(phase: ChatStreamingPhase | string | null | undefined): boolean {
  return ACTIVE_STREAMING_PHASES.has(normalizeStreamingPhase(phase));
}

export function getProcessingIcon(state: ChatProcessingState): ReactNode {
  switch (state) {
    case "queued":
      return <Clock className="h-3.5 w-3.5" />;
    case "preparing":
      return <Wrench className="h-3.5 w-3.5" />;
    case "thinking":
      return <BrainCircuit className="h-3.5 w-3.5" />;
    case "routing":
      return <RadioTower className="h-3.5 w-3.5" />;
    case "retrieving_memory":
      return <Sparkles className="h-3.5 w-3.5" />;
    case "calling_tool":
      return <Zap className="h-3.5 w-3.5" />;
    case "streaming":
      return <Loader2 className="h-3.5 w-3.5 animate-spin" />;
    case "finalizing":
      return <Loader2 className="h-3.5 w-3.5 animate-spin" />;
    case "complete":
      return <CheckCircle2 className="h-3.5 w-3.5" />;
    case "error":
      return <AlertCircle className="h-3.5 w-3.5" />;
    case "degraded":
      return <AlertCircle className="h-3.5 w-3.5" />;
    case "idle":
    default:
      return <Bot className="h-3.5 w-3.5" />;
  }
}

export function getStreamingIcon(phase: ChatStreamingPhase): ReactNode {
  switch (phase) {
    case "connecting":
    case "connected":
    case "receiving":
    case "reconnecting":
      return <Loader2 className="h-3.5 w-3.5 animate-spin" />;
    case "complete":
      return <CheckCircle2 className="h-3.5 w-3.5" />;
    case "error":
      return <AlertCircle className="h-3.5 w-3.5" />;
    case "idle":
    default:
      return <Bot className="h-3.5 w-3.5" />;
  }
}

export function getProcessingToneClassName(state: ChatProcessingState): string {
  switch (state) {
    case "error":
      return "border-destructive/30 bg-destructive/10 text-destructive";
    case "degraded":
      return "border-yellow-500/30 bg-yellow-500/10 text-yellow-700 dark:text-yellow-300";
    case "complete":
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300";
    case "idle":
      return "border-border bg-muted/40 text-muted-foreground";
    default:
      return "border-primary/30 bg-primary/10 text-primary";
  }
}

export function getStreamingToneClassName(phase: ChatStreamingPhase): string {
  switch (phase) {
    case "error":
      return "border-destructive/30 bg-destructive/10 text-destructive";
    case "complete":
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300";
    case "idle":
      return "border-border bg-muted/40 text-muted-foreground";
    default:
      return "border-primary/30 bg-primary/10 text-primary";
  }
}

export function getProcessingDisplay(
  state: ChatProcessingState | string | null | undefined,
): ChatProcessingDisplay {
  const normalized = normalizeProcessingState(state);

  return {
    label: PROCESSING_STATE_LABELS[normalized],
    description: PROCESSING_STATE_DESCRIPTIONS[normalized],
    icon: getProcessingIcon(normalized),
    toneClassName: getProcessingToneClassName(normalized),
    isBusy: BUSY_PROCESSING_STATES.has(normalized),
  };
}

export function getStreamingDisplay(
  phase: ChatStreamingPhase | string | null | undefined,
): ChatStreamingDisplay {
  const normalized = normalizeStreamingPhase(phase);

  return {
    label: STREAMING_PHASE_LABELS[normalized],
    description: STREAMING_PHASE_DESCRIPTIONS[normalized],
    icon: getStreamingIcon(normalized),
    toneClassName: getStreamingToneClassName(normalized),
    isActive: ACTIVE_STREAMING_PHASES.has(normalized),
  };
}

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
    case "provider_selection":
      return actualProvider
        ? `Karen is checking ${actualProvider}...`
        : requestedProvider
          ? `Karen is checking ${requestedProvider}...`
          : "Karen is checking the selected provider...";
    case "provider_failed":
      return fallbackNext
        ? `Karen is switching from ${requestedProvider || "the requested provider"} to ${fallbackNext}...`
        : `Karen is switching away from ${requestedProvider || "the requested provider"}...`;
    case "fallback_started":
    case "fallback_succeeded":
      return actualProvider
        ? `${actualProvider} is live. Karen is generating a response...`
        : "Karen found a live fallback provider...";
    case "generating_response":
      return actualProvider
        ? `${actualProvider} is generating a response...`
        : "Karen is generating a response...";
    case "streaming":
      return actualProvider
        ? `${actualProvider} is streaming the response...`
        : "Karen is streaming the response...";
    case "retrying":
      return fallbackNext
        ? `Karen is retrying with ${fallbackNext}...`
        : "Karen is retrying with a live fallback...";
    case "degraded":
      return actualProvider
        ? `Karen is running in degraded mode with ${actualProvider}...`
        : "Karen is running in degraded mode...";
    case "degraded_live":
      return actualProvider
        ? `${actualProvider} is answering through a degraded live path...`
        : "Karen is answering through a degraded live path...";
    case "post_processing":
      return actualProvider
        ? `${actualProvider} is finalizing the response...`
        : "Karen is finalizing the response...";
    case "completed":
      return actualProvider
        ? `Response complete from ${actualProvider}.`
        : source
          ? `Response complete from ${source}.`
          : "Response complete.";
    case "failed":
      return fallbackNext
        ? `Karen could not use ${requestedProvider || "the requested provider"} and will try ${fallbackNext}...`
        : "Karen is handling a failed request...";
    case "cancelled":
      return "Request was cancelled.";
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

  if (typeof fallbackMessage === "string" && fallbackMessage.trim()) {
    return fallbackMessage.trim();
  }

  if (statusKey) {
    return `Karen is ${statusKey.replace(/_/g, " ")}...`;
  }

  return DEFAULT_PROCESSING_MESSAGE;
};
