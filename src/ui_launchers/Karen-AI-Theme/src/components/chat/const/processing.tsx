import type { ReactNode } from "react";
import {
  AlertCircle,
  Bot,
  BrainCircuit,
  CheckCircle2,
  Clock,
  Database,
  Loader2,
  RadioTower,
  Route,
  Save,
  ShieldCheck,
  Sparkles,
  Split,
  Wrench,
  Zap,
} from "lucide-react";

export const DEFAULT_PROCESSING_MESSAGE = "Karen is processing your request...";
export const STREAMING_ERROR_MESSAGE = "Connection issue. Please try again.";
export const STREAM_TIMEOUT_MESSAGE = "Request timed out. Please try again.";

export type ProcessingRuntimeMetadata = {
  stage?: string | null;
  node?: string | null;
  event_type?: string | null;
  status?: string | null;
  message?: string | null;
  requested_provider?: string | null;
  requested_model?: string | null;
  actual_provider?: string | null;
  actual_model?: string | null;
  provider?: string | null;
  model?: string | null;
  fallback_next?: string | null;
  runtime_engine?: string | null;
  response_source?: string | null;
  degraded_mode?: boolean | null;
  degradation_reason?: string | null;
  fallback_level?: number | null;
  memory_recall_count?: number | null;
  capsule_count?: number | null;
  tool_count?: number | null;
  tool_name?: string | null;
  plugin_name?: string | null;
  specialist?: string | null;
  latency_ms?: number | null;
  correlation_id?: string | null;
  llm?: ProcessingRuntimeMetadata | null;
  runtime?: ProcessingRuntimeMetadata | null;
  metadata?: ProcessingRuntimeMetadata | null;
  [key: string]: unknown;
};

export type ProcessingStatusKey =
  | "request_received" | "runtime_mode_check" | "auth_context_resolved" | "session_loaded" | "conversation_loaded"
  | "context_assembly" | "cortex_start" | "cortex_complete" | "memory_recall_start" | "memory_recall_complete"
  | "capsule_recall_start" | "capsule_recall_complete" | "provider_selection_start" | "provider_selected"
  | "provider_unavailable" | "provider_failed" | "provider_retry" | "fallback_started" | "fallback_succeeded"
  | "langgraph_start" | "langgraph_node" | "medusa_start" | "medusa_specialist_start" | "tool_call_start"
  | "tool_call_complete" | "generation_start" | "response_started" | "streaming_tokens" | "persistence_start"
  | "persistence_complete" | "memory_writeback_start" | "memory_writeback_complete" | "post_processing"
  | "completed" | "failed" | "cancelled" | "degraded" | "degraded_live" | "emergency_static";

export type ChatProcessingState = "idle"|"queued"|"preparing"|"authenticating"|"context"|"cortex"|"retrieving_memory"|"routing"|"deep_reasoning"|"medusa"|"calling_tool"|"generating"|"streaming"|"persisting"|"finalizing"|"complete"|"error"|"degraded";
export type ChatStreamingPhase = "idle"|"connecting"|"connected"|"receiving"|"reconnecting"|"complete"|"error";
export type ChatProcessingDisplay = { label: string; description: string; icon: ReactNode; toneClassName: string; isBusy: boolean; };
export type ChatStreamingDisplay = { label: string; description: string; icon: ReactNode; toneClassName: string; isActive: boolean; };

export const PROCESSING_STATE_LABELS: Record<ChatProcessingState, string> = { idle:"Ready",queued:"Queued",preparing:"Preparing request",authenticating:"Checking access",context:"Building context",cortex:"Routing intent",retrieving_memory:"Recalling memory",routing:"Selecting model",deep_reasoning:"Deep reasoning",medusa:"Specialist agents",calling_tool:"Using tools",generating:"Generating",streaming:"Streaming",persisting:"Saving",finalizing:"Finalizing",complete:"Complete",error:"Error",degraded:"Degraded" };
export const PROCESSING_STATE_DESCRIPTIONS: Record<ChatProcessingState, string> = { idle:"Karen is ready for the next message.",queued:"Your request is waiting for the runtime.",preparing:"Karen is creating the runtime request and attaching trace metadata.",authenticating:"Karen is verifying session, tenant, and RBAC context.",context:"Karen is assembling profile, conversation, files, and prompt context.",cortex:"Karen is classifying intent and deciding routing policy through CORTEX.",retrieving_memory:"Karen is retrieving governed memory and capsule context.",routing:"Karen is checking provider/model availability and fallback policy.",deep_reasoning:"Karen is running the deep reasoning workflow.",medusa:"Karen is coordinating specialist agents.",calling_tool:"Karen is executing approved tools, plugins, or MCP calls.",generating:"Karen is waiting for the selected model to generate a response.",streaming:"Karen is receiving response tokens.",persisting:"Karen is saving the conversation, metadata, and approved memory candidates.",finalizing:"Karen is sanitizing the response and preparing final metadata.",complete:"The response completed successfully.",error:"The request failed before a complete response was produced.",degraded:"Karen continued through a backend-reported degraded runtime path." };
export const STREAMING_PHASE_LABELS: Record<ChatStreamingPhase, string> = { idle:"Idle",connecting:"Connecting",connected:"Connected",receiving:"Receiving",reconnecting:"Reconnecting",complete:"Complete",error:"Stream error" };
export const STREAMING_PHASE_DESCRIPTIONS: Record<ChatStreamingPhase, string> = { idle:"No active stream.",connecting:"Opening the chat stream.",connected:"The stream is connected.",receiving:"Receiving response tokens.",reconnecting:"Attempting to reconnect the stream.",complete:"The stream completed.",error:"The stream failed." };
export const BUSY_PROCESSING_STATES = new Set<ChatProcessingState>(["queued","preparing","authenticating","context","cortex","retrieving_memory","routing","deep_reasoning","medusa","calling_tool","generating","streaming","persisting","finalizing"]);
export const ACTIVE_STREAMING_PHASES = new Set<ChatStreamingPhase>(["connecting","connected","receiving","reconnecting"]);
export const PROCESSING_STATUS_ALIASES: Record<string, ProcessingStatusKey> = { initializing:"request_received",processing:"context_assembly",routing:"provider_selection_start",streaming:"streaming_tokens",done:"completed",error:"failed",fallback:"fallback_started" };
const STATUS_TO_STATE: Record<ProcessingStatusKey, ChatProcessingState> = { request_received:"preparing",runtime_mode_check:"preparing",auth_context_resolved:"authenticating",session_loaded:"preparing",conversation_loaded:"preparing",context_assembly:"context",cortex_start:"cortex",cortex_complete:"cortex",memory_recall_start:"retrieving_memory",memory_recall_complete:"retrieving_memory",capsule_recall_start:"retrieving_memory",capsule_recall_complete:"retrieving_memory",provider_selection_start:"routing",provider_selected:"routing",provider_unavailable:"routing",provider_failed:"routing",provider_retry:"routing",fallback_started:"degraded",fallback_succeeded:"degraded",langgraph_start:"deep_reasoning",langgraph_node:"deep_reasoning",medusa_start:"medusa",medusa_specialist_start:"medusa",tool_call_start:"calling_tool",tool_call_complete:"calling_tool",generation_start:"generating",response_started:"generating",streaming_tokens:"streaming",persistence_start:"persisting",persistence_complete:"persisting",memory_writeback_start:"persisting",memory_writeback_complete:"persisting",post_processing:"finalizing",completed:"complete",failed:"error",cancelled:"complete",degraded:"degraded",degraded_live:"degraded",emergency_static:"degraded" };
const isRecord=(v:unknown):v is Record<string,unknown>=>Boolean(v&&typeof v==="object"&&!Array.isArray(v));
const toCleanString=(v:unknown)=>typeof v==="string"?v.trim():String(v??"").trim();
const toFiniteNumber=(v:unknown)=>typeof v==="number"&&Number.isFinite(v)?v:(typeof v==="string"&&v.trim()&&Number.isFinite(Number(v))?Number(v):null);
export const normalizeProcessingStatusKey=(status:unknown):string=>{ if(status==null) return ""; if(typeof status==="string") return status.trim().toLowerCase().replace(/[\s-]+/g,"_"); if(isRecord(status)){ const p=status.value??status.status??status.event_type??status.phase??status.stage??status.state??status.type??status.node??status.message; if(typeof p==="string") return p.trim().toLowerCase().replace(/[\s-]+/g,"_"); } return String(status).trim().toLowerCase().replace(/[\s-]+/g,"_"); };
const isProcessingStatusKey=(k:string):k is ProcessingStatusKey=>k in STATUS_TO_STATE;
export const normalizeProcessingStatus=(status:unknown):ProcessingStatusKey|null=>{ const k=normalizeProcessingStatusKey(status); if(!k) return null; if(isProcessingStatusKey(k)) return k; if(k in PROCESSING_STATUS_ALIASES) return PROCESSING_STATUS_ALIASES[k]; if(k.includes("fallback")&&k.includes("success")) return "fallback_succeeded"; if(k.includes("provider")&&k.includes("unavailable")) return "provider_unavailable"; if(k.includes("provider")) return "provider_selection_start"; if(k.includes("stream")||k.includes("token")) return "streaming_tokens"; if(k.includes("complete")||k.includes("done")) return "completed"; if(k.includes("error")||k.includes("fail")) return "failed"; if(k.includes("generat")) return "generation_start"; return null; };
const getRuntimeMetadata=(context?:ProcessingRuntimeMetadata):ProcessingRuntimeMetadata=>{ if(!context||!isRecord(context)) return {}; const llm=isRecord(context.llm)?context.llm:{}; const metadata=isRecord(context.metadata)?context.metadata:{}; const runtime=isRecord(context.runtime)?context.runtime:{}; return {...context,...metadata,...runtime,...llm}; };
const formatProviderLabel=(provider:unknown)=>{ const raw=toCleanString(provider).toLowerCase(); if(!raw) return ""; if(raw.includes("transformers")) return "Transformers"; if(raw.includes("ollama")) return "Ollama"; if(raw.includes("vllm")) return "vLLM"; return raw.replace(/[_-]/g," ").replace(/\b[a-z]/g,c=>c.toUpperCase()); };
const formatProviderModel=(p:unknown,m:unknown)=>{ const pl=formatProviderLabel(p); const ml=toCleanString(m); return pl&&ml?`${pl}/${ml}`:pl||ml; };

export function normalizeProcessingState(state: ChatProcessingState | ProcessingStatusKey | string | null | undefined): ChatProcessingState { const n=normalizeProcessingStatusKey(state||"idle"); if(n in PROCESSING_STATE_LABELS) return n as ChatProcessingState; const s=normalizeProcessingStatus(n); return s?STATUS_TO_STATE[s]:"idle"; }
export function normalizeStreamingPhase(phase: ChatStreamingPhase | string | null | undefined): ChatStreamingPhase { const n=normalizeProcessingStatusKey(phase||"idle"); if(n in STREAMING_PHASE_LABELS) return n as ChatStreamingPhase; if(n.includes("reconnect")) return "reconnecting"; if(n.includes("connect")) return "connecting"; if(n.includes("receive")||n.includes("stream")||n.includes("token")) return "receiving"; if(n.includes("complete")||n.includes("done")||n.includes("success")) return "complete"; if(n.includes("error")||n.includes("fail")) return "error"; return "idle"; }
export function isBusyProcessingState(state: ChatProcessingState | ProcessingStatusKey | string | null | undefined): boolean { return BUSY_PROCESSING_STATES.has(normalizeProcessingState(state)); }
export function isActiveStreamingPhase(phase: ChatStreamingPhase | string | null | undefined): boolean { return ACTIVE_STREAMING_PHASES.has(normalizeStreamingPhase(phase)); }
export function getProcessingIcon(state: ChatProcessingState): ReactNode { switch(state){case"queued":return <Clock className="h-3.5 w-3.5"/>;case"preparing":return <Wrench className="h-3.5 w-3.5"/>;case"authenticating":return <ShieldCheck className="h-3.5 w-3.5"/>;case"context":return <Sparkles className="h-3.5 w-3.5"/>;case"cortex":return <BrainCircuit className="h-3.5 w-3.5"/>;case"retrieving_memory":return <Database className="h-3.5 w-3.5"/>;case"routing":return <RadioTower className="h-3.5 w-3.5"/>;case"deep_reasoning":return <Route className="h-3.5 w-3.5"/>;case"medusa":return <Split className="h-3.5 w-3.5"/>;case"calling_tool":return <Zap className="h-3.5 w-3.5"/>;case"generating":case"streaming":case"finalizing":return <Loader2 className="h-3.5 w-3.5 animate-spin"/>;case"persisting":return <Save className="h-3.5 w-3.5"/>;case"complete":return <CheckCircle2 className="h-3.5 w-3.5"/>;case"error":case"degraded":return <AlertCircle className="h-3.5 w-3.5"/>;default:return <Bot className="h-3.5 w-3.5"/>;} }
export function getStreamingIcon(phase: ChatStreamingPhase): ReactNode { switch(phase){case"connecting":case"connected":case"receiving":case"reconnecting":return <Loader2 className="h-3.5 w-3.5 animate-spin"/>;case"complete":return <CheckCircle2 className="h-3.5 w-3.5"/>;case"error":return <AlertCircle className="h-3.5 w-3.5"/>;default:return <Bot className="h-3.5 w-3.5"/>;} }
export const getProcessingToneClassName=(s:ChatProcessingState)=>s==="error"?"border-destructive/30 bg-destructive/10 text-destructive":s==="degraded"?"border-yellow-500/30 bg-yellow-500/10 text-yellow-700 dark:text-yellow-300":s==="complete"?"border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300":s==="idle"?"border-border bg-muted/40 text-muted-foreground":"border-primary/30 bg-primary/10 text-primary";
export const getStreamingToneClassName=(p:ChatStreamingPhase)=>p==="error"?"border-destructive/30 bg-destructive/10 text-destructive":p==="complete"?"border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300":p==="idle"?"border-border bg-muted/40 text-muted-foreground":"border-primary/30 bg-primary/10 text-primary";
export const getProcessingDisplay=(state:ChatProcessingState|ProcessingStatusKey|string|null|undefined):ChatProcessingDisplay=>{const n=normalizeProcessingState(state);return{label:PROCESSING_STATE_LABELS[n],description:PROCESSING_STATE_DESCRIPTIONS[n],icon:getProcessingIcon(n),toneClassName:getProcessingToneClassName(n),isBusy:BUSY_PROCESSING_STATES.has(n)}};
export const getStreamingDisplay=(phase:ChatStreamingPhase|string|null|undefined):ChatStreamingDisplay=>{const n=normalizeStreamingPhase(phase);return{label:STREAMING_PHASE_LABELS[n],description:STREAMING_PHASE_DESCRIPTIONS[n],icon:getStreamingIcon(n),toneClassName:getStreamingToneClassName(n),isActive:ACTIVE_STREAMING_PHASES.has(n)}};
export const getProcessingStatusVariantMessages=(status:unknown,context?:ProcessingRuntimeMetadata):string[]=>{const n=normalizeProcessingStatus(status); if(!n)return []; return [resolveProcessingStatusMessage(n,undefined,0,context)];};
export const getProcessingStatusMessageVariant=(status:unknown,variantIndex=0,context?:ProcessingRuntimeMetadata):string|null=>{const m=getProcessingStatusVariantMessages(status,context); if(!m.length) return null; return m[Math.abs(Math.trunc(variantIndex))%m.length];};
export const resolveProcessingStatusMessage=(status:unknown,fallbackMessage?:string,_variantIndex=0,context?:ProcessingRuntimeMetadata):string=>{const runtime=getRuntimeMetadata(context); const n=normalizeProcessingStatus(status??runtime.status??runtime.stage??runtime.event_type); if(typeof runtime.message==="string"&&runtime.message.trim()) return runtime.message.trim(); if(!n) return fallbackMessage?.trim()||DEFAULT_PROCESSING_MESSAGE; const requestedRuntime=formatProviderModel(runtime.requested_provider??runtime.provider,runtime.requested_model??runtime.model); const actualRuntime=formatProviderModel(runtime.actual_provider??runtime.provider,runtime.actual_model??runtime.model); const fallbackNext=formatProviderLabel(runtime.fallback_next); const memoryCount=toFiniteNumber(runtime.memory_recall_count); switch(n){case"request_received":return"Received your message and opened a traced runtime request.";case"runtime_mode_check":return"Checking runtime mode, maintenance state, and degraded capability flags.";case"context_assembly":return"Assembling profile, conversation, files, and prompt context.";case"cortex_start":return"Running CORTEX intent classification and policy routing.";case"memory_recall_start":return"Retrieving governed short-term, episodic, and long-term memory.";case"memory_recall_complete":return memoryCount!=null?`Memory recall complete. Retrieved ${Math.max(0,Math.floor(memoryCount))} relevant item(s).`:"Memory recall complete.";case"provider_selection_start":return requestedRuntime?`Checking requested runtime ${requestedRuntime}.`:"Selecting an available provider and model.";case"provider_unavailable":return requestedRuntime?`${requestedRuntime} is unavailable. Checking fallback options.`:"Requested provider is unavailable. Checking fallback options.";case"fallback_started":return fallbackNext?`Trying fallback provider ${fallbackNext}.`:"Trying the next backend-approved fallback provider.";case"fallback_succeeded":return actualRuntime?`Recovered through ${actualRuntime}.`:"Recovered through a live fallback provider.";case"generation_start":return actualRuntime?`${actualRuntime} is generating the answer.`:"The selected model is generating the answer.";case"response_started":return"The response stream has started.";case"streaming_tokens":return"Receiving response tokens.";case"post_processing":return"Sanitizing output and preparing final response metadata.";case"persistence_start":return"Saving conversation, runtime metadata, and audit trail.";case"completed":return"Response complete.";case"failed":return"Processing failed before a complete response was produced.";default:return fallbackMessage?.trim()||DEFAULT_PROCESSING_MESSAGE;} };
