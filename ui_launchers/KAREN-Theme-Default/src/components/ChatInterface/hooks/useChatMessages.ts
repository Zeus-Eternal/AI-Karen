"use client";

import React, { useCallback, useRef } from "react";
import { useToast } from "@/hooks/use-toast";
import { useHooks } from "@/hooks/use-hooks";
import { getConfigManager } from "@/lib/endpoint-config";
import { sanitizeInput } from "@/lib/utils";
import { safeError, safeWarn, safeInfo, safeDebug } from "@/lib/safe-console";
import { ChatMessage, ChatSettings } from "../types";

type MessageMetadata = Record<string, unknown> & {
  origin?: string;
  endpoint?: string;
  model?: string;
  tokens?: number;
  cost?: number;
  confidence?: number;
  latencyMs?: number;
};

interface BackendChatRuntimeRequest {
  message: string;
  conversation_id?: string;
  stream: boolean;
  context: Record<string, unknown>;
  tools?: string[];
  memory_context?: string;
  user_preferences: {
    model: string;
    temperature: number;
    max_tokens: number;
    enable_suggestions: boolean;
    preferred_llm_provider?: string;
    preferred_model?: string;
  };
  platform: string;
  model: string;
  provider?: string;
  temperature: number;
  max_tokens: number;
}

export const useChatMessages = (
  messages: ChatMessage[],
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>,
  isTyping: boolean,
  setIsTyping: React.Dispatch<React.SetStateAction<boolean>>,
  settings: ChatSettings,
  sessionId: string | null,
  conversationId: string | null,
  user: unknown,
  useCopilotKit: boolean,
  enableCodeAssistance: boolean,
  enableContextualHelp: boolean,
  enableDocGeneration: boolean,
  maxMessages: number = 1000,
  onMessageSent?: (message: ChatMessage) => void,
  onMessageReceived?: (message: ChatMessage) => void
) => {
  const { triggerHooks } = useHooks();
  const { toast } = useToast();
  const configManager = getConfigManager();
  const abortControllerRef = useRef<AbortController | null>(null);

  // Core message sending logic with full streaming support
  const sendMessage = useCallback(
    async (
      content: string,
      type: ChatMessage["type"] = "text",
      options: {
        language?: string;
        context?: unknown;
        enableAnalysis?: boolean;
      } = {}
    ) => {
      // Early validation to prevent errors
      if (!content?.trim() || isTyping) {
        safeWarn("SendMessage called with invalid parameters:", {
          content: !!content,
          isTyping,
        });
        return;
      }

      // Wrap the entire function in a try-catch to prevent unhandled errors
      try {
        const sanitizedContent = sanitizeInput(content.trim());
        const userMessage: ChatMessage = {
          id: `msg_${Date.now()}_user`,
          role: "user",
          content: sanitizedContent,
          timestamp: new Date(),
          type,
          language: options.language || settings.language,
        };

        // Abort any ongoing requests
        abortControllerRef.current?.abort();
        setIsTyping(false);

        // Add user message
        setMessages((prev) => {
          const newMessages = [...prev, userMessage];
          // Limit messages if maxMessages is set
          return maxMessages && newMessages.length > maxMessages
            ? newMessages.slice(-maxMessages)
            : newMessages;
        });

        setIsTyping(true);

        // Trigger hooks
        await triggerHooks(
          "chat_message_sent",
          {
            messageId: userMessage.id,
            content:
              sanitizedContent.substring(0, 100) +
              (sanitizedContent.length > 100 ? "..." : ""),
            type,
            language: options.language,
            userId: user?.user_id,
            sessionId,
            conversationId,
          },
          { userId: user?.user_id }
        );

        if (onMessageSent) {
          onMessageSent(userMessage);
        }

        // Create assistant message placeholder
        const assistantId = `msg_${Date.now()}_assistant`;
        const placeholder: ChatMessage = {
          id: assistantId,
          role: "assistant",
          content: "",
          timestamp: new Date(),
          type: type === "code" ? "code" : "text",
          status: "generating",
          metadata: {
            model: settings.model,
          },
        };

        setMessages((prev) => [...prev, placeholder]);

        const baseUrl = configManager.getBackendUrl();
        const trimmedBaseUrl = baseUrl.replace(/\/+$/, "");
        const joinBackendPath = (path: string) =>
          trimmedBaseUrl ? `${trimmedBaseUrl}${path}` : path;

        const streamingEnabled = !!settings.enableStreaming;
        const chatRuntimePath = streamingEnabled
          ? "/api/chat/runtime/stream"
          : "/api/chat/runtime";
        const fallbackPath = useCopilotKit
          ? "/copilot/assist"
          : "/api/ai/conversation-processing";

        // Force proxy usage in browser environment for better reliability
        const useProxy = typeof window !== 'undefined' ? true : 
          (process.env.NEXT_PUBLIC_USE_PROXY ?? "true").toLowerCase() !== "false";
        
        const proxyUrlFor = (path: string) =>
          `/api/chat/proxy?path=${encodeURIComponent(path)}`;

        const chatRuntimeUrl = useProxy
          ? proxyUrlFor(chatRuntimePath)
          : joinBackendPath(chatRuntimePath);
        const fallbackUrl = useProxy
          ? proxyUrlFor(fallbackPath)
          : joinBackendPath(fallbackPath);

        // Debug logging for URL resolution
        safeDebug("🔍 useChatMessages: URL resolution", {
          useProxy,
          chatRuntimePath,
          fallbackPath,
          chatRuntimeUrl,
          fallbackUrl,
          baseUrl: trimmedBaseUrl,
        });
        let activeEndpoint = chatRuntimeUrl;

        try {
          const controller = new AbortController();
          abortControllerRef.current = controller;
          const startTime = performance.now();

          // Derive preferred provider/model for routing hints
          let selectedProvider: string | undefined;
          let selectedModelOnly: string | undefined;
          if (settings.model.includes(":")) {
            const [prov, ...rest] = settings.model.split(":");
            selectedProvider =
              prov === "local"
                ? "llamacpp"
                : prov === "llama-cpp"
                ? "llamacpp"
                : prov;
            selectedModelOnly = rest.join(":");
          }

          const originalContext = options.context;
          const { tools: contextTools, ...contextWithoutTools } =
            originalContext || {};
          const normalizedTools = Array.isArray(contextTools)
            ? contextTools.filter(
                (tool): tool is string => typeof tool === "string"
              )
            : undefined;

          const llmPreferences = {
            preferred_llm_provider: selectedProvider,
            preferred_model: selectedModelOnly || settings.model,
          };

          const runtimeContext: Record<string, unknown> = {
            type,
            language: options.language || settings.language,
            session_id: sessionId,
            conversation_id: conversationId,
            user_id: user?.user_id,
            platform: "web",
            enable_analysis: options.enableAnalysis || enableCodeAssistance,
            conversation_history: messages.map((m) => ({
              role: m.role,
              content: m.content,
            })),
            user_settings: {
              model: settings.model,
              temperature: settings.temperature,
              max_tokens: settings.maxTokens,
              language: settings.language,
              enable_suggestions: settings.enableSuggestions,
            },
            llm_preferences: llmPreferences,
            copilot_features: {
              code_assistance: enableCodeAssistance,
              contextual_help: enableContextualHelp,
              doc_generation: enableDocGeneration,
            },
            ...contextWithoutTools,
          };

          const chatRuntimePayload: BackendChatRuntimeRequest = {
            message: sanitizedContent,
            conversation_id: conversationId || undefined,
            stream: streamingEnabled,
            context: runtimeContext,
            tools: normalizedTools,
            memory_context: sessionId || conversationId || undefined,
            user_preferences: {
              model: settings.model,
              temperature: settings.temperature,
              max_tokens: settings.maxTokens,
              enable_suggestions: settings.enableSuggestions,
              ...llmPreferences,
            },
            platform: "web",
            model: settings.model,
            provider: selectedProvider,
            temperature: settings.temperature,
            max_tokens: settings.maxTokens,
          };

          const legacyPayload = useCopilotKit
            ? {
                // CopilotKit payload format (fallback)
                message: sanitizedContent,
                session_id: sessionId,
                conversation_id: conversationId,
                stream: settings.enableStreaming,
                model: settings.model,
                temperature: settings.temperature,
                max_tokens: settings.maxTokens,
                type,
                language: options.language || settings.language,
                context: originalContext,
                user_id: user?.user_id,
                enable_analysis: options.enableAnalysis || enableCodeAssistance,
                enable_suggestions: settings.enableSuggestions,
                copilot_features: {
                  code_assistance: enableCodeAssistance,
                  contextual_help: enableContextualHelp,
                  doc_generation: enableDocGeneration,
                },
                llm_preferences: llmPreferences,
              }
            : {
                // AI Orchestrator payload format (fallback)
                prompt: sanitizedContent,
                conversation_history: messages.map((m) => ({
                  role: m.role,
                  content: m.content,
                })),
                user_settings: {
                  model: settings.model,
                  temperature: settings.temperature,
                  max_tokens: settings.maxTokens,
                  language: settings.language,
                  enable_suggestions: settings.enableSuggestions,
                },
                context: {
                  type,
                  language: options.language || settings.language,
                  session_id: sessionId,
                  conversation_id: conversationId,
                  user_id: user?.user_id,
                  platform: "web",
                  enable_analysis:
                    options.enableAnalysis || enableCodeAssistance,
                  ...originalContext,
                },
                session_id: sessionId,
                include_memories: true,
                include_insights: true,
                llm_preferences: llmPreferences,
              };

          // Get authentication headers
          const authToken =
            localStorage.getItem("karen_access_token") ||
            sessionStorage.getItem("kari_session_token");
          const headers = {
            "Content-Type": "application/json",
            Accept: streamingEnabled
              ? "text/event-stream, application/json"
              : "application/json",
            ...(authToken && { Authorization: `Bearer ${authToken}` }),
            ...(user?.user_id && { "X-User-ID": user.user_id }),
            "X-Session-ID": sessionId || "",
            "X-Conversation-ID": conversationId || "",
          };

          // Debug logging to diagnose connection issues
          safeInfo("🔍 useChatMessages: Preparing chat runtime request", {
            primary: chatRuntimeUrl,
            fallback: fallbackUrl,
            streaming: streamingEnabled,
          });

          safeDebug("🔍 useChatMessages: Primary payload preview", {
            model: chatRuntimePayload.model,
            provider: chatRuntimePayload.provider,
            conversation_id: chatRuntimePayload.conversation_id,
            stream: chatRuntimePayload.stream,
          });

          const executeRequest = async (url: string, body: unknown) => {
            safeDebug("🔍 useChatMessages: Executing request", {
              url,
              method: "POST",
              bodyKeys: Object.keys(body),
              headersKeys: Object.keys(headers),
            });

            return fetch(url, {
              method: "POST",
              headers,
              body: JSON.stringify(body),
              signal: controller.signal,
              // Add additional fetch options for better reliability
              cache: 'no-cache',
              credentials: 'same-origin',
            });
          };

          let response: Response;
          let responseOrigin: "chat-runtime" | "copilot" | "ai-orchestrator" =
            "chat-runtime";

          try {
            response = await executeRequest(chatRuntimeUrl, chatRuntimePayload);
            if (!response.ok) {
              const errorText = await response.text().catch(() => "");
              const error = new Error(
                `Chat runtime HTTP ${response.status}: ${response.statusText}${
                  errorText ? ` - ${errorText}` : ""
                }`
              );
              (error as unknown).status = response.status;
              (error as unknown).statusText = response.statusText;
              (error as unknown).endpoint = chatRuntimeUrl;
              throw error;
            }
            responseOrigin = "chat-runtime";
          } catch (primaryError) {
            safeWarn(
              "🔍 useChatMessages: Chat runtime request failed, attempting fallback",
              {
                endpoint: chatRuntimeUrl,
                error:
                  primaryError instanceof Error
                    ? primaryError.message
                    : String(primaryError),
                errorType: primaryError instanceof Error ? primaryError.name : 'Unknown',
                stack: primaryError instanceof Error ? primaryError.stack : undefined,
              }
            );

            activeEndpoint = fallbackUrl;
            try {
              response = await executeRequest(fallbackUrl, legacyPayload);
            } catch (fallbackNetworkError) {
              safeError("🔍 useChatMessages: Fallback network request failed", {
                endpoint: fallbackUrl,
                error: fallbackNetworkError instanceof Error ? fallbackNetworkError.message : String(fallbackNetworkError),
                errorType: fallbackNetworkError instanceof Error ? fallbackNetworkError.name : 'Unknown',
              });
              throw fallbackNetworkError;
            }

            if (!response.ok) {
              const fallbackBody = await response.text().catch(() => "");
              safeError("🔍 useChatMessages: Fallback request failed", {
                status: response.status,
                statusText: response.statusText,
                endpoint: fallbackUrl,
                body: fallbackBody,
              });

              throw new Error(
                `HTTP ${response.status}: ${response.statusText}${
                  fallbackBody ? ` - ${fallbackBody}` : ""
                }`
              );
            }

            responseOrigin = useCopilotKit ? "copilot" : "ai-orchestrator";
          }

          // Enhanced diagnostic logging for response
          safeDebug("🔍 useChatMessages: Response received", {
            status: response.status,
            statusText: response.statusText,
            url: response.url || activeEndpoint,
            ok: response.ok,
            headers: Array.from(response.headers.entries()).reduce(
              (acc, [key, value]) => ({ ...acc, [key]: value }),
              {}
            ),
            contentType: response.headers.get("content-type"),
            timestamp: new Date().toISOString(),
            origin: responseOrigin,
          });

          if (!response.body) {
            safeError("🔍 useChatMessages: No response body received");
            throw new Error("No response body");
          }

          // Handle streaming or complete response
          let fullText = "";
          let metadata: MessageMetadata = {};

          const ct = response.headers.get("content-type") || "";
          const isStream =
            settings.enableStreaming &&
            (ct.includes("text/event-stream") ||
              ct.includes("text/stream") ||
              ct.includes("application/stream+json"));

          const fallbackHeader = response.headers.get("x-fallback");
          const fallbackReason = response.headers.get("x-fallback-reason");
          const upstreamStatus = response.headers.get("x-proxy-upstream-status");

          if (fallbackHeader) {
            let fallbackBody: unknown = null;

            if (!isStream) {
              try {
                const clone = response.clone();
                fallbackBody = await clone.json();
              } catch {
                try {
                  fallbackBody = await response.clone().text();
                } catch {
                  fallbackBody = null;
                }
              }
            }

            safeWarn("🔍 useChatMessages: Received fallback chat payload", {
              header: fallbackHeader,
              reason: fallbackReason,
              upstreamStatus,
              origin: responseOrigin,
              endpoint: activeEndpoint,
              isStream,
            });

            const fallbackMessage =
              typeof fallbackBody === "object" && fallbackBody !== null
                ? (() => {
                    const recordBody = fallbackBody as Record<string, unknown>;
                    if (typeof recordBody.response === "string") {
                      return recordBody.response;
                    }
                    if (typeof recordBody.message === "string") {
                      return recordBody.message;
                    }
                    return undefined;
                  })()
                : undefined;

            const fallbackError = new Error(
              fallbackMessage ||
                "AI services returned a fallback payload instead of an LLM response."
            );
            fallbackError.name = "LLMFallbackResponseError";
            (fallbackError as Error & {
              details?: Record<string, unknown>;
            }).details = {
              header: fallbackHeader,
              reason: fallbackReason,
              upstreamStatus,
              origin: responseOrigin,
              endpoint: activeEndpoint,
              body: fallbackBody,
              isStream,
            };

            throw fallbackError;
          }

          if (isStream) {
            // Handle streaming response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
              const { value, done } = await reader.read();
              if (done) break;

              buffer += decoder.decode(value || new Uint8Array(), { stream: true });
              const lines = buffer.split("\n");
              buffer = lines.pop() || "";

              for (const rawLine of lines) {
                const line = rawLine.replace(/\r$/, "");
                const trimmed = line.trim();
                if (!trimmed || trimmed === "data: [DONE]" || trimmed === "[DONE]") {
                  continue;
                }

                let data = trimmed;
                if (trimmed.startsWith("data:")) {
                  data = trimmed.replace(/^data:\s*/, "");
                }

                try {
                  const json = JSON.parse(data);
                  const jsonType = (json as unknown)?.type;

                  if (
                    jsonType !== "token" &&
                    jsonType !== "delta" &&
                    (json.event === "meta" ||
                      jsonType === "meta" ||
                      json.kind === "metadata" ||
                      json.metadata ||
                      json.meta ||
                      json.data ||
                      json.usage ||
                      json.model)
                    ) {
                      const usage = json.usage || json.token_usage || {};
                      const baseMeta =
                        (json.metadata || json.meta || json.data || {}) as Partial<MessageMetadata>;
                      const metaUpdate: Partial<MessageMetadata> = { ...baseMeta };
                      if ((json as unknown).kire_metadata && !metaUpdate.kire)
                        metaUpdate.kire = (json as unknown).kire_metadata;
                      if (json.model && !metaUpdate.model) metaUpdate.model = json.model;
                    if (typeof json.confidence === "number")
                      metaUpdate.confidence = json.confidence;
                    if (
                      usage.total_tokens ||
                      (usage.prompt_tokens && usage.completion_tokens)
                    ) {
                      metaUpdate.tokens =
                        usage.total_tokens ||
                        usage.prompt_tokens + usage.completion_tokens;
                    }
                    if (
                      typeof metaUpdate.total_tokens === "number" &&
                      metaUpdate.tokens === undefined
                    ) {
                      metaUpdate.tokens = metaUpdate.total_tokens;
                    }
                    if (
                      typeof (metaUpdate as unknown).totalTokens === "number" &&
                      metaUpdate.tokens === undefined
                    ) {
                      metaUpdate.tokens = (metaUpdate as unknown).totalTokens;
                    }
                    if (json.cost !== undefined) metaUpdate.cost = json.cost;
                    if (metaUpdate.origin === undefined) metaUpdate.origin = responseOrigin;
                    if (metaUpdate.endpoint === undefined)
                      metaUpdate.endpoint = activeEndpoint;
                    metadata = { ...metadata, ...metaUpdate };
                  }

                  if (
                    typeof json === "string" ||
                    json.delta ||
                    json.content ||
                    json.text ||
                    json.answer ||
                    (jsonType === "token" && json.data)
                  ) {
                    const tokenData =
                      jsonType === "token" && typeof json.data === "object"
                        ? typeof json.data.token === "string"
                          ? json.data.token
                          : typeof json.data.delta === "string"
                          ? json.data.delta
                          : typeof json.data.content === "string"
                          ? json.data.content
                          : typeof json.data.text === "string"
                          ? json.data.text
                          : typeof json.data.answer === "string"
                          ? json.data.answer
                          : ""
                        : "";

                    const newContent =
                      (typeof json === "string" && json) ||
                      (typeof json.delta === "string" && json.delta) ||
                      (json.content as string | undefined) ||
                      (json.text as string | undefined) ||
                      (json.answer as string | undefined) ||
                      tokenData ||
                      "";
                    if (newContent) {
                      fullText += newContent;
                      setMessages((prev) =>
                        prev.map((m) =>
                          m.id === assistantId ? { ...m, content: fullText } : m
                        )
                      );
                    }
                  }
                } catch {
                  if (!data.startsWith("{")) {
                    fullText += data;
                    setMessages((prev) =>
                      prev.map((m) =>
                        m.id === assistantId ? { ...m, content: fullText } : m
                      )
                    );
                  }
                }
              }
            }

            const tail = (buffer || "").trim();
            if (tail && tail !== "data: [DONE]") {
              const data = tail.startsWith("data:")
                ? tail.replace(/^data:\s*/, "")
                : tail;
              try {
                const json = JSON.parse(data);
                const jsonTypeTail = (json as unknown)?.type;

                if (
                  typeof json === "string" ||
                  json.content ||
                  json.text ||
                  json.answer ||
                  (jsonTypeTail === "token" && json.data)
                ) {
                  const tokenDataTail =
                    jsonTypeTail === "token" && typeof json.data === "object"
                      ? typeof json.data.token === "string"
                        ? json.data.token
                        : typeof json.data.delta === "string"
                        ? json.data.delta
                        : typeof json.data.content === "string"
                        ? json.data.content
                        : typeof json.data.text === "string"
                        ? json.data.text
                        : typeof json.data.answer === "string"
                        ? json.data.answer
                        : ""
                      : "";

                  const newContent =
                    (typeof json === "string" && json) ||
                    (json.content as string | undefined) ||
                    (json.text as string | undefined) ||
                    (json.answer as string | undefined) ||
                    tokenDataTail ||
                    "";
                  if (newContent) {
                    fullText += newContent;
                    setMessages((prev) =>
                      prev.map((m) =>
                        m.id === assistantId ? { ...m, content: fullText } : m
                      )
                    );
                  }
                }

                if (
                  jsonTypeTail !== "token" &&
                  jsonTypeTail !== "delta" &&
                  (json.metadata ||
                    json.meta ||
                    json.data ||
                    json.usage ||
                    json.model)
                ) {
                  const usage = json.usage || json.token_usage || {};
                  const baseMeta =
                    (json.metadata || json.meta || json.data || {}) as Partial<MessageMetadata>;
                  const metaUpdate: Partial<MessageMetadata> = { ...baseMeta };
                  if ((json as unknown).kire_metadata && !metaUpdate.kire)
                    metaUpdate.kire = (json as unknown).kire_metadata;
                  if (json.model && !metaUpdate.model) metaUpdate.model = json.model;
                  if (
                    usage.total_tokens ||
                    (usage.prompt_tokens && usage.completion_tokens)
                  ) {
                    metaUpdate.tokens =
                      usage.total_tokens ||
                      usage.prompt_tokens + usage.completion_tokens;
                  }
                  if (
                    typeof metaUpdate.total_tokens === "number" &&
                    metaUpdate.tokens === undefined
                  ) {
                    metaUpdate.tokens = metaUpdate.total_tokens;
                  }
                  if (
                    typeof (metaUpdate as unknown).totalTokens === "number" &&
                    metaUpdate.tokens === undefined
                  ) {
                    metaUpdate.tokens = (metaUpdate as unknown).totalTokens;
                  }
                  if (json.cost !== undefined) metaUpdate.cost = json.cost;
                  if (metaUpdate.origin === undefined)
                    metaUpdate.origin = responseOrigin;
                  if (metaUpdate.endpoint === undefined)
                    metaUpdate.endpoint = activeEndpoint;
                  metadata = { ...metadata, ...metaUpdate };
                }
              } catch {
                fullText += data;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId ? { ...m, content: fullText } : m
                  )
                );
              }
            }
          } else {
            // Handle non-streaming response (JSON or text)
            const ct2 = response.headers.get("content-type") || "";
            if (ct2.includes("application/json")) {
              const result = await response.json();

              const degraded = Boolean(
                (result?.ai_data &&
                  typeof result.ai_data === "object" &&
                  ((result.ai_data as Record<string, unknown>).degraded_mode ===
                    true ||
                    (result.ai_data as Record<string, unknown>).status ===
                      "degraded")) ||
                  (result?.metadata &&
                    typeof result.metadata === "object" &&
                    (result.metadata as Record<string, unknown>).degraded_mode ===
                      true) ||
                  (result as Record<string, unknown>)?.degraded_mode === true
              );

              if (degraded) {
                safeWarn("🔍 useChatMessages: Received degraded AI response", {
                  origin: responseOrigin,
                  endpoint: activeEndpoint,
                  upstreamStatus,
                  reason:
                    (result?.ai_data as Record<string, unknown>)?.reason ||
                    fallbackReason,
                });

                const degradedMessage =
                  (result?.response && typeof result.response === "string"
                    ? result.response
                    : result?.message && typeof result.message === "string"
                    ? result.message
                    : "The AI service is currently unavailable.") ??
                  "The AI service is currently unavailable.";

                const degradeError = new Error(degradedMessage);
                degradeError.name = "LLMFallbackResponseError";
                (degradeError as Error & {
                  details?: Record<string, unknown>;
                }).details = {
                  header: fallbackHeader,
                  reason:
                    (result?.ai_data as Record<string, unknown>)?.reason ||
                    fallbackReason,
                  upstreamStatus,
                  origin: responseOrigin,
                  endpoint: activeEndpoint,
                  body: result,
                  degraded: true,
                };

                throw degradeError;
              }

              fullText =
                result.answer ||
                result.content ||
                result.text ||
                result.message ||
                result.response ||
                "";
                const usage = result.usage || result.token_usage || {};
                const baseMetadata =
                  (result.metadata || result.meta || {}) as Partial<MessageMetadata>;
                metadata = {
                  ...baseMetadata,
                  ...(result.kire_metadata ? { kire: result.kire_metadata } : {}),
                  model:
                    typeof result.model === "string" && result.model.length > 0
                      ? result.model
                      : (baseMetadata.model ?? undefined),
                  tokens:
                    typeof usage.total_tokens === "number"
                      ? usage.total_tokens
                      : usage.prompt_tokens && usage.completion_tokens
                      ? usage.prompt_tokens + usage.completion_tokens
                      : baseMetadata.tokens,
                  cost:
                    typeof result.cost === "number"
                      ? result.cost
                      : (baseMetadata.cost ?? undefined),
                  confidence:
                    typeof result.confidence === "number"
                      ? result.confidence
                      : (baseMetadata.confidence ?? undefined),
                } as MessageMetadata;
            } else {
              fullText = await response.text();
            }
          }
        }

        metadata = {
          ...metadata,
          origin: metadata.origin ?? responseOrigin,
          endpoint: metadata.endpoint ?? activeEndpoint,
        };

        // Calculate final metrics
        const latency = Math.round(performance.now() - startTime);

        safeDebug("🔍 useChatMessages: Response processing completed:", {
          fullTextLength: fullText.length,
          fullTextPreview:
            fullText.substring(0, 100) + (fullText.length > 100 ? "..." : ""),
          latencyMs: latency,
          metadata,
          hasMetadata: !!metadata,
          metadataKeys: metadata ? Object.keys(metadata) : [],
          modelFromMetadata: metadata.model,
          modelFromSettings: settings.model,
          finalModel:
            typeof metadata.model === "string" && metadata.model.length > 0
              ? metadata.model
              : settings.model,
        });

        // Create final message
        const finalMessage: ChatMessage = {
          ...placeholder,
          content: fullText.trim(),
          status: "completed",
          metadata: {
            ...metadata,
            latencyMs: latency,
            model:
              typeof metadata.model === "string" && metadata.model.length > 0
                ? metadata.model
                : settings.model,
            tokens:
              typeof metadata.tokens === "number"
                ? metadata.tokens
                : Math.ceil(fullText.length / 4),
            cost:
              typeof metadata.cost === "number" ? metadata.cost : 0,
            origin: metadata.origin ?? responseOrigin,
            endpoint: metadata.endpoint ?? activeEndpoint,
          },
        };

        safeDebug("🔍 useChatMessages: Final message created:", {
          messageId: finalMessage.id,
          contentLength: finalMessage.content.length,
          status: finalMessage.status,
          model: finalMessage.metadata?.model,
          latencyMs: finalMessage.metadata?.latencyMs,
          tokens: finalMessage.metadata?.tokens,
        });

        // Update message
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? finalMessage : m))
        );

        // Trigger hooks
        await triggerHooks(
          "chat_message_received",
          {
            messageId: assistantId,
            confidence: finalMessage.metadata?.confidence,
            type: finalMessage.type,
            latencyMs: latency,
            model: settings.model,
            userId: user?.user_id,
            sessionId,
            conversationId,
          },
          { userId: user?.user_id }
        );

        if (onMessageReceived) {
          onMessageReceived(finalMessage);
        }

        safeInfo("🔍 useChatMessages: Message successfully processed and stored:", {
          messageId: assistantId,
          totalMessages: messages.length + 1,
          success: true,
          timestamp: new Date().toISOString(),
        });

          // Generate artifacts for certain message types
          if (
            finalMessage.type === "code" ||
            finalMessage.type === "analysis" ||
            finalMessage.content.includes("```")
          ) {
            // TODO: Implement artifact generation
            safeDebug(
              "🔍 useChatMessages: Should generate artifacts for message:",
              finalMessage.id
            );
          }
        } catch (error) {
          if ((error as unknown)?.name === "AbortError") {
            setIsTyping(false);
            return;
          }

          // Prevent console error interceptor issues by using structured logging
          const errorDetails = {
            name: (error as unknown)?.name || "UnknownError",
            message: (error as unknown)?.message || "Unknown error occurred",
            stack: (error as unknown)?.stack,
            cause: (error as unknown)?.cause,
            timestamp: new Date().toISOString(),
            context: {
              sessionId,
              conversationId,
              userId: user?.user_id,
              endpoint: activeEndpoint,
              primaryEndpoint: chatRuntimeUrl,
              fallbackEndpoint: fallbackUrl,
              messageType: type,
            },
          };

          // Use safe console to avoid interceptor issues
          safeError("Chat error occurred", errorDetails, {
            skipInProduction: false,
            useStructuredLogging: true,
          });

          const isFallbackError =
            (error as Error)?.name === "LLMFallbackResponseError";
          const fallbackDetails = isFallbackError
            ? ((error as Error & { details?: Record<string, unknown> }).details ??
              null)
            : null;
          const fallbackDetailsRecord = fallbackDetails as
            | Record<string, unknown>
            | null;

          // Provide more specific error messages
          let errorContent =
            "I apologize, but I encountered an error processing your request. Please try again.";
          let errorTitle = "Chat Error";

          if (isFallbackError) {
            const fallbackBody = fallbackDetailsRecord?.["body"];
            const fallbackMessage =
              fallbackBody &&
              typeof fallbackBody === "object" &&
              (fallbackBody as Record<string, unknown>).response
                ? String(
                    (fallbackBody as Record<string, unknown>).response as string
                  )
                : error instanceof Error && error.message
                ? error.message
                : null;
            errorContent =
              fallbackMessage ||
              "The AI service is currently unavailable. Please try again once connectivity is restored.";
            errorTitle = "AI Service Unavailable";
          } else if (
            error instanceof TypeError &&
            error.message.includes("Failed to fetch")
          ) {
            errorContent =
              "Unable to connect to the AI service. Please check if the backend is running and try again.";
            errorTitle = "Connection Error";

            // Test basic connectivity (use Next proxy to avoid CORS in browser)
            safeInfo("Testing backend connectivity...");
            fetch("/api/health")
              .then((response) => {
                safeInfo("Backend health check:", response.status);
                if (response.ok) {
                  safeInfo(
                    "Backend is accessible, but chat endpoint may have issues"
                  );
                }
              })
              .catch((healthError) => {
                safeError("Backend health check failed:", healthError);
              });
          }

          const errorMetadata = {
            ...(isFallbackError
              ? {
                  degraded: true,
                  fallback: {
                    header: fallbackDetailsRecord?.["header"],
                    reason: fallbackDetailsRecord?.["reason"],
                    upstreamStatus: fallbackDetailsRecord?.["upstreamStatus"],
                    origin: fallbackDetailsRecord?.["origin"],
                    endpoint: fallbackDetailsRecord?.["endpoint"],
                  },
                }
              : {}),
          } as Record<string, unknown>;

          const errorMessage: ChatMessage = {
            id: assistantId,
            role: "assistant",
            content: errorContent,
            timestamp: new Date(),
            type: "text",
            status: "error",
            metadata: errorMetadata,
          };

          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? errorMessage : m))
          );

          const toastDescription = isFallbackError
            ? ((fallbackDetailsRecord?.["reason"] as string) || errorContent)
            : error instanceof Error
            ? error.message
            : "Failed to get AI response";

          toast({
            variant: "destructive",
            title: errorTitle,
            description: toastDescription,
          });
        } finally {
          setIsTyping(false);
        }
      } catch (outerError) {
        // Catch any unhandled errors in the sendMessage function
        safeError(
          "Critical error in sendMessage",
          {
            error: outerError,
            message: (outerError as unknown)?.message,
            stack: (outerError as unknown)?.stack,
            timestamp: new Date().toISOString(),
          },
          {
            skipInProduction: false,
            useStructuredLogging: true,
          }
        );

        setIsTyping(false);

        toast({
          variant: "destructive",
          title: "Critical Error",
          description:
            "An unexpected error occurred. Please refresh the page and try again.",
        });
      }
    },
    [
      messages,
      isTyping,
      settings,
      sessionId,
      conversationId,
      user?.user_id,
      triggerHooks,
      onMessageSent,
      onMessageReceived,
      useCopilotKit,
      enableCodeAssistance,
      enableContextualHelp,
      enableDocGeneration,
      maxMessages,
      toast,
      configManager,
      setIsTyping,
      setMessages,
    ]
  );

  // Message actions
  const handleMessageAction = useCallback(
    async (messageId: string, action: string) => {
      const message = messages.find((m) => m.id === messageId);
      if (!message) return;

      switch (action) {
        case "copy":
          try {
            await navigator.clipboard.writeText(message.content);
            toast({
              title: "Copied",
              description: "Message copied to clipboard",
            });
          } catch (error) {
            safeError("Failed to copy to clipboard:", error);
            toast({
              title: "Copy Failed",
              description: "Unable to copy to clipboard. Please try again.",
              variant: "destructive",
            });
          }
          break;

        case "rate_up":
        case "rate_down": {
          const rating = action === "rate_up" ? "up" : "down";
          setMessages((prev) =>
            prev.map((m) =>
              m.id === messageId
                ? { ...m, metadata: { ...m.metadata, rating } }
                : m
            )
          );

          await triggerHooks(
            "chat_message_rated",
            {
              messageId,
              rating,
              userId: user?.user_id,
            },
            { userId: user?.user_id }
          );

          toast({
            title: "Feedback Recorded",
            description: `Message rated ${rating}`,
          });
          break;
        }

        case "regenerate": {
          if (message.role === "assistant") {
            const userMessage =
              messages[messages.findIndex((m) => m.id === messageId) - 1];
            if (userMessage) {
              sendMessage(userMessage.content, userMessage.type);
            }
          }
          break;
        }

        case "select":
          // Selection is handled in useChatState
          safeDebug("Message selection should be handled in useChatState");
          break;
      }
    },
    [messages, toast, triggerHooks, user?.user_id, sendMessage, setMessages]
  );

  // Clear messages
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, [setMessages]);

  // Add message directly
  const addMessage = useCallback(
    (message: ChatMessage) => {
      setMessages((prev) => [...prev, message]);
    },
    [setMessages]
  );

  // Update message
  const updateMessage = useCallback(
    (messageId: string, updates: Partial<ChatMessage>) => {
      setMessages((prev) =>
        prev.map((msg) => (msg.id === messageId ? { ...msg, ...updates } : msg))
      );
    },
    [setMessages]
  );

  return {
    messages,
    isTyping,
    sendMessage,
    handleMessageAction,
    clearMessages,
    addMessage,
    updateMessage,
  };
};
