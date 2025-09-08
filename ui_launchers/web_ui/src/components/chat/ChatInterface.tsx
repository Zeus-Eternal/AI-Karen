"use client";

import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  useMemo,
} from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  Send,
  Bot,
  Code,
  FileText,
  Lightbulb,
  Loader2,
  Sparkles,
  Settings,
  Mic,
  MicOff,
  Paperclip,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Download,
  Share,
  Maximize2,
  Minimize2,
  Zap,
  AlertCircle,
  CheckCircle,
  BarChart3,
  TrendingUp,
  Clock,
  Target,
  Brain,
  Cpu,
  Activity,
  MessageSquare,
  Eye,
  EyeOff,
} from "lucide-react";

// Context and Hooks
import { useAuth } from "@/contexts/AuthContext";
import { useHooks } from "@/contexts/HookContext";
import { useToast } from "@/hooks/use-toast";
import { useInputPreservation } from "@/hooks/use-input-preservation";

// Components
import { ChatBubble } from "@/components/chat/ChatBubble";
import EnhancedMessageBubble from "@/components/chat/EnhancedMessageBubble";
import { ChatErrorBoundary } from "@/components/error/ChatErrorBoundary";
import ModelSelector from "@/components/chat/ModelSelector";
import dynamic from "next/dynamic";
// Lazy-load Copilot features only when enabled
const CopilotTextarea = dynamic(() => import("@/components/chat/copilot/CopilotTextarea").then(m => m.CopilotTextarea), { ssr: false });
const CopilotActions = dynamic(() => import("./CopilotActions"), { ssr: false });
import {
  type CopilotAction,
  type ChatContext,
  parseSlashCommand,
} from "./CopilotActions";
const CopilotArtifacts = dynamic(() => import("./CopilotArtifacts"), { ssr: false });
import type { CopilotArtifact } from "./CopilotArtifacts";
import AnalyticsTab from "./AnalyticsTab";
import { DegradedModeBanner } from "@/components/ui/degraded-mode-banner";
import ProfileSelector from "@/components/chat/ProfileSelector";
import RoutingHistory from "@/components/chat/RoutingHistory";

// Utils and Config
import { getConfigManager } from "@/lib/endpoint-config";
import { sanitizeInput } from "@/lib/utils";
import { safeError, safeWarn, safeInfo } from "@/lib/safe-console";

// Types
export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  type?: "text" | "code" | "suggestion" | "analysis" | "documentation";
  language?: string;
  status?: "sending" | "sent" | "generating" | "completed" | "error";
  metadata?: {
    confidence?: number;
    latencyMs?: number;
    model?: string;
    sources?: string[];
    reasoning?: string;
    persona?: string;
    mood?: string;
    intent?: string;
    tokens?: number;
    cost?: number;
    suggestions?: any[];
    analysis?: any;
    rating?: "up" | "down";
    codeAnalysis?: {
      issues: Array<{
        type: string;
        severity: "error" | "warning" | "info";
        message: string;
        line?: number;
        suggestions?: string[];
      }>;
      metrics: {
        complexity: number;
        maintainability: number;
        performance: number;
      };
      suggestions: string[];
    };
  };
}

interface ChatSettings {
  model: string;
  temperature: number;
  maxTokens: number;
  enableStreaming: boolean;
  enableSuggestions: boolean;
  enableCodeAnalysis: boolean;
  enableVoiceInput: boolean;
  theme: "light" | "dark" | "auto";
  language: string;
  autoSave: boolean;
  showTimestamps: boolean;
  enableNotifications: boolean;
}

interface ChatAnalytics {
  totalMessages: number;
  userMessages: number;
  assistantMessages: number;
  averageResponseTime: number;
  averageConfidence: number;
  totalTokens: number;
  totalCost: number;
  sessionDuration: number;
  topTopics: string[];
  codeLanguages: string[];
  errorRate: number;
}

interface ChatInterfaceProps {
  // Core Props
  initialMessages?: ChatMessage[];
  onMessageSent?: (message: ChatMessage) => void;
  onMessageReceived?: (message: ChatMessage) => void;

  // CopilotKit Integration
  useCopilotKit?: boolean;
  enableCodeAssistance?: boolean;
  enableContextualHelp?: boolean;
  enableDocGeneration?: boolean;

  // UI Configuration
  className?: string;
  height?: string;
  showHeader?: boolean;
  showTabs?: boolean;
  showSettings?: boolean;
  enableVoiceInput?: boolean;
  enableFileUpload?: boolean;

  // Advanced Features
  enableAnalytics?: boolean;
  enableExport?: boolean;
  enableSharing?: boolean;
  enableCollaboration?: boolean;
  maxMessages?: number;

  // Customization
  placeholder?: string;
  welcomeMessage?: string;
  theme?: "light" | "dark" | "auto";

  // Callbacks
  onSettingsChange?: (settings: ChatSettings) => void;
  onExport?: (messages: ChatMessage[]) => void;
  onShare?: (messages: ChatMessage[]) => void;
  onAnalyticsUpdate?: (analytics: ChatAnalytics) => void;
}

const defaultSettings: ChatSettings = {
  model: "local:tinyllama-1.1b",
  temperature: 0.7,
  maxTokens: 2000,
  enableStreaming: true,
  enableSuggestions: true,
  enableCodeAnalysis: true,
  enableVoiceInput: false,
  theme: "auto",
  language: "javascript",
  autoSave: true,
  showTimestamps: true,
  enableNotifications: true,
};

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  // Core Props
  initialMessages = [],
  onMessageSent,
  onMessageReceived,

  // CopilotKit Integration
  useCopilotKit = true,
  enableCodeAssistance = true,
  enableContextualHelp = true,
  enableDocGeneration = true,

  // UI Configuration
  className = "",
  height = "600px",
  showHeader = true,
  showTabs = true,
  showSettings = true,
  enableVoiceInput = false,
  enableFileUpload = true,

  // Advanced Features
  enableAnalytics = true,
  enableExport = true,
  enableSharing = true,
  enableCollaboration = false,
  maxMessages = 1000,

  // Customization
  placeholder = "Ask me anything about code, get suggestions, or request help...",
  welcomeMessage,
  theme = "auto",

  // Callbacks
  onSettingsChange,
  onExport,
  onShare,
  onAnalyticsUpdate,
}) => {
  // Hooks
  const { user } = useAuth();
  const { triggerHooks } = useHooks();
  const { toast } = useToast();
  const configManager = getConfigManager();

  // CopilotKit Integration (conditional) - Production-ready approach
  const [copilotKit, setCopilotKit] = useState<any>(null);
  const [copilotKitError, setCopilotKitError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    if (useCopilotKit) {
      // Dynamically import CopilotKit only when needed - Production safe
      const loadCopilotKit = async () => {
        try {
          const module = await import(
            "@/components/chat/copilot/CopilotKitProvider"
          );
          if (!mounted) return; // Prevent state update if component unmounted

          if (typeof (module as any).useCopilotKit === 'function') {

            try {
              // Note: We can't call the hook here as it violates rules of hooks
              // Instead, we'll set a flag that CopilotKit is available
              setCopilotKit({
                available: true,
                config: { endpoints: { assist: "/copilot/assist" } },
              });
            } catch (hookError) {
              safeWarn("CopilotKit hook failed:", hookError);
              setCopilotKitError("CopilotKit hook not available");
            }
          } else {
            setCopilotKitError("CopilotKit hook not found in module");
          }
        } catch (importError) {
          if (!mounted) return;
          safeWarn("CopilotKit module not available:", importError);
          setCopilotKitError("CopilotKit module not found");
        }
      };

      loadCopilotKit();
    }

    return () => {
      mounted = false;
    };
  }, [useCopilotKit]);

  // State Management
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [inputValue, setInputValue] = useState("");
  const [codeValue, setCodeValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [settings, setSettings] = useState<ChatSettings>(defaultSettings);
  const [activeTab, setActiveTab] = useState<"chat" | "code" | "analytics">(
    "chat"
  );
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showRoutingHistory, setShowRoutingHistory] = useState(false);
  const [showCodePreview, setShowCodePreview] = useState(false);
  const [selectedMessages, setSelectedMessages] = useState<Set<string>>(
    new Set()
  );
  const [analytics, setAnalytics] = useState<ChatAnalytics>({
    totalMessages: 0,
    userMessages: 0,
    assistantMessages: 0,
    averageResponseTime: 0,
    averageConfidence: 0,
    totalTokens: 0,
    totalCost: 0,
    sessionDuration: 0,
    topTopics: [],
    codeLanguages: [],
    errorRate: 0,
  });
  const [sessionStartTime] = useState(Date.now());

  // Copilot state
  const [copilotArtifacts, setCopilotArtifacts] = useState<CopilotArtifact[]>(
    []
  );
  const [selectedText, setSelectedText] = useState<string>("");

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const codeTextareaRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  // Input preservation
  const { preserveInput, restoreInput, clearPreservedInput } =
    useInputPreservation("chat-interface");

  // Runtime URL configuration
  const runtimeUrl = useMemo(() => {
    const baseUrl = configManager.getBackendUrl();
    const endpoint =
      useCopilotKit && copilotKit
        ? copilotKit.config?.endpoints?.assist || "/copilot/assist"
        : "/api/ai-orchestrator/conversation-processing";
    return `${baseUrl.replace(/\/+$/, "")}${endpoint}`;
  }, [configManager, useCopilotKit, copilotKit]);

  // Chat context for copilot actions
  const chatContext = useMemo((): ChatContext => {
    const clamp = (s?: string | null, max = 200): string | undefined => {
      if (!s) return undefined;
      const t = s.trim();
      return t.length > max ? `${t.slice(0, max)}…` : t;
    };

    const containsCodeFence = (text: string) => /```[\s\S]*?```/.test(text);
    const detectFenceLanguage = (text: string): string | undefined => {
      const m = text.match(/```\s*([a-zA-Z0-9+#._-]+)/);
      return m?.[1];
    };

    const lastNonSystem = [...messages].reverse().find((m) => m.role !== "system" && m.content?.trim());
    const lastUser = [...messages].reverse().find((m) => m.role === "user" && m.content?.trim());
    const lastWithIntent = [...messages].reverse().find((m) => m.metadata?.intent);

    // Build recent messages (keep last 5, include system for full context)
    const recentMessages = messages.slice(-5).map((m) => ({
      role: m.role,
      content: m.content,
      timestamp: m.timestamp,
    }));

    // Topic heuristic: prefer explicit intent; else first few words of last content message
    const derivedTopic = (() => {
      const source = lastWithIntent?.metadata?.intent || lastNonSystem?.content || "";
      const words = source.replace(/\s+/g, " ").trim().split(" ").slice(0, 8).join(" ");
      return clamp(words, 80);
    })();

    // Intent heuristic: prefer explicit intent; else infer from slash command or keywords
    const derivedIntent = (() => {
      const explicit = lastWithIntent?.metadata?.intent;
      if (explicit) return clamp(explicit, 80);
      if (lastUser?.content) {
        const cmd = parseSlashCommand(lastUser.content);
        if (cmd) return cmd.id;
        const lc = lastUser.content.toLowerCase();
        if (/(explain|describe|what|how)/.test(lc)) return "explain";
        if (/(debug|error|fix|issue|bug)/.test(lc)) return "debug";
        if (/(refactor|improve|optimi[sz]e)/.test(lc)) return "refactor";
        if (/(test|unit test|spec)/.test(lc)) return "generate_tests";
      }
      return undefined;
    })();

    // Code context
    const anyCodeInMessages = messages.some((m) => m.type === "code" || (m.content && containsCodeFence(m.content)));
    const detectedLang = (() => {
      if (settings.language) return settings.language;
      // Try detect from last code fence
      for (const m of [...messages].reverse()) {
        if (m.content) {
          const lang = detectFenceLanguage(m.content);
          if (lang) return lang;
        }
      }
      return undefined;
    })();

    // Complexity heuristic: based on length, code presence, and errors
    const errorCount = messages.filter((m) => m.status === "error").length;
    const avgLen = messages.length
      ? Math.round(messages.reduce((sum, m) => sum + (m.content?.length || 0), 0) / messages.length)
      : 0;
    const complexity: "simple" | "medium" | "complex" = (() => {
      const longThread = messages.length > 12 || avgLen > 500;
      const mediumThread = messages.length > 5 || avgLen > 200;
      if (longThread || (anyCodeInMessages && errorCount > 0)) return "complex";
      if (mediumThread || anyCodeInMessages) return "medium";
      return "simple";
    })();

    return {
      selectedText: selectedText || undefined,
      currentFile: undefined,
      language: detectedLang,
      recentMessages,
      codeContext: {
        hasCode: !!codeValue || anyCodeInMessages,
        language: detectedLang,
        errorCount,
      },
      conversationContext: {
        topic: derivedTopic,
        intent: derivedIntent,
        complexity,
      },
    };
  }, [selectedText, settings.language, codeValue, messages]);

  // Initialize session and welcome message
  useEffect(() => {
    const initializeChat = async () => {
      if (sessionId) return;

      const newSessionId = crypto.randomUUID();
      const newConversationId = crypto.randomUUID();

      setSessionId(newSessionId);
      setConversationId(newConversationId);

      // Add welcome message if provided and no initial messages
      if (welcomeMessage && messages.length === 0) {
        const welcome: ChatMessage = {
          id: `welcome-${Date.now()}`,
          role: "assistant",
          content: welcomeMessage,
          timestamp: new Date(),
          type: "text",
          metadata: { confidence: 1.0 },
        };
        setMessages([welcome]);
      } else if (messages.length === 0) {
        // Default welcome message
        const defaultWelcome: ChatMessage = {
          id: `welcome-${Date.now()}`,
          role: "assistant",
          content: `Hello${
            user?.email ? ` ${user.email.split("@")[0]}` : ""
          }! I'm your AI assistant with advanced capabilities. I can help you with:

• **Code Development** - Write, debug, and optimize code
• **Documentation** - Generate comprehensive docs
• **Analysis** - Analyze code quality and performance
• **Suggestions** - Provide contextual recommendations

${
  useCopilotKit
    ? "🚀 **CopilotKit Enhanced** - Advanced AI features enabled!"
    : ""
}

What would you like to work on today?`,
          timestamp: new Date(),
          type: "text",
          metadata: { confidence: 1.0 },
        };
        setMessages([defaultWelcome]);
      }

      // Restore preserved input
      const preserved = restoreInput();
      if (preserved) {
        setInputValue(preserved);
      }
    };

    initializeChat();
  }, [
    sessionId,
    welcomeMessage,
    messages.length,
    restoreInput,
    user,
    useCopilotKit,
  ]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Preserve input on changes
  useEffect(() => {
    if (inputValue) {
      preserveInput(inputValue);
    }
  }, [inputValue, preserveInput]);

  // Update analytics
  useEffect(() => {
    const intents = messages
      .map((m) => m.metadata?.intent)
      .filter((v): v is string => typeof v === 'string' && v.length > 0);
    const langs = messages
      .map((m) => m.language)
      .filter((v): v is string => typeof v === 'string' && v.length > 0);

    const newAnalytics: ChatAnalytics = {
      totalMessages: messages.length,
      userMessages: messages.filter((m) => m.role === "user").length,
      assistantMessages: messages.filter((m) => m.role === "assistant").length,
      averageResponseTime:
        Math.round(
          messages.reduce((acc, m) => acc + (m.metadata?.latencyMs || 0), 0) /
            messages.filter((m) => m.metadata?.latencyMs).length
        ) || 0,
      averageConfidence:
        Math.round(
          (messages.reduce((acc, m) => acc + (m.metadata?.confidence || 0), 0) /
            messages.filter((m) => m.metadata?.confidence).length) *
            100
        ) || 0,
      totalTokens: messages.reduce(
        (acc, m) => acc + (m.metadata?.tokens || 0),
        0
      ),
      totalCost: messages.reduce((acc, m) => acc + (m.metadata?.cost || 0), 0),
      sessionDuration: Math.round((Date.now() - sessionStartTime) / 1000),
      topTopics: [...new Set(intents)].slice(0, 5),
      codeLanguages: [...new Set(langs)],
      errorRate:
        Math.round(
          (messages.filter((m) => m.status === "error").length /
            messages.length) *
            100
        ) || 0,
    };

    setAnalytics(newAnalytics);
    if (onAnalyticsUpdate) {
      onAnalyticsUpdate(newAnalytics);
    }
  }, [messages, sessionStartTime, onAnalyticsUpdate]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
      mediaRecorderRef.current?.stop();
      setIsTyping(false);
      setIsRecording(false);
    };
  }, []);

  // Core message sending logic
  const sendMessage = useCallback(
    async (
      content: string,
      type: ChatMessage["type"] = "text",
      options: {
        language?: string;
        context?: any;
        enableAnalysis?: boolean;
      } = {}
    ) => {
      // Early validation to prevent errors
      if (!content?.trim() || isTyping) {
        safeWarn('SendMessage called with invalid parameters:', { content: !!content, isTyping });
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

      setInputValue("");
      setCodeValue("");
      clearPreservedInput();
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

      try {
        const controller = new AbortController();
        abortControllerRef.current = controller;
        const startTime = performance.now();

        // Prepare request payload based on endpoint
        // Derive preferred provider/model
        let selectedProvider: string | undefined;
        let selectedModelOnly: string | undefined;
        if (settings.model.includes(":")) {
          const [prov, ...rest] = settings.model.split(":");
          selectedProvider = prov === 'local' ? 'llamacpp' : (prov === 'llama-cpp' ? 'llamacpp' : prov);
          selectedModelOnly = rest.join(":");
        }

        const payload =
          useCopilotKit && copilotKit
          ? {
                // CopilotKit payload format
                message: sanitizedContent,
                session_id: sessionId,
                conversation_id: conversationId,
                stream: settings.enableStreaming,
                model: settings.model,
                temperature: settings.temperature,
                max_tokens: settings.maxTokens,
                type,
                language: options.language || settings.language,
                context: options.context,
                user_id: user?.user_id,
                enable_analysis: options.enableAnalysis || enableCodeAssistance,
                enable_suggestions: settings.enableSuggestions,
                copilot_features: {
                  code_assistance: enableCodeAssistance,
                  contextual_help: enableContextualHelp,
                  doc_generation: enableDocGeneration,
                },
                // Provide explicit LLM preferences for routers that support them
                llm_preferences: {
                  preferred_llm_provider: selectedProvider,
                  preferred_model: selectedModelOnly || settings.model,
                },
              }
            : {
                // AI Orchestrator payload format
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
                  enable_analysis: options.enableAnalysis || enableCodeAssistance,
                  ...options.context,
                },
                session_id: sessionId,
                include_memories: true,
                include_insights: true,
                llm_preferences: {
                  preferred_llm_provider: selectedProvider,
                  preferred_model: selectedModelOnly || settings.model,
                },
              };

        // Get authentication headers
        const authToken =
          localStorage.getItem("karen_access_token") ||
          sessionStorage.getItem("kari_session_token");
        const headers = {
          "Content-Type": "application/json",
          ...(authToken && { Authorization: `Bearer ${authToken}` }),
          ...(user?.user_id && { "X-User-ID": user.user_id }),
          "X-Session-ID": sessionId || "",
          "X-Conversation-ID": conversationId || "",
        };

        // Debug logging to diagnose connection issues
        safeInfo("Sending chat request to:", runtimeUrl);
        safeInfo("Request payload:", payload);
        safeInfo("Request headers:", headers);

        const response = await fetch(runtimeUrl, {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
          signal: controller.signal,
        });

        // Production logging (only in development)
        if (process.env.NODE_ENV === "development") {
          safeInfo("Response status:", response.status);
          safeInfo("Response headers:", Object.fromEntries(response.headers.entries()));
        }

        if (!response.ok) {
          let errorDetails = "";
          try {
            const errorText = await response.text();
            errorDetails = errorText;
            if (process.env.NODE_ENV === "development") {
              safeError("Error response body:", errorText);
            }
          } catch (e) {
            safeError("Could not read error response:", e);
          }
          throw new Error(
            `HTTP ${response.status}: ${response.statusText}${
              errorDetails ? ` - ${errorDetails}` : ""
            }`
          );
        }

        if (!response.body) {
          throw new Error("No response body");
        }

        // Handle streaming or complete response
        let fullText = "";
        let metadata: any = {};

        const ct = response.headers.get("content-type") || "";
        const isStream =
          settings.enableStreaming &&
          (ct.includes("text/event-stream") ||
            ct.includes("text/stream") ||
            ct.includes("application/stream+json"));

        if (isStream) {
          // Handle streaming response
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";
          let streamDone = false;

          while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const rawLine of lines) {
              const line = rawLine.replace(/\r$/, "");
              const trimmed = line.trim();
              if (!trimmed) continue;
              if (trimmed === "data: [DONE]" || trimmed === "[DONE]") {
                streamDone = true;
                continue;
              }

              let data = trimmed;
              if (trimmed.startsWith("data:")) {
                data = trimmed.replace(/^data:\s*/, "");
              }

              try {
                const json = JSON.parse(data);

                // Merge metadata
                if (
                  json.event === "meta" ||
                  json.type === "meta" ||
                  json.kind === "metadata" ||
                  json.metadata ||
                  json.meta ||
                  json.data ||
                  json.usage ||
                  json.model
                ) {
                  const usage = json.usage || json.token_usage || {};
                  const baseMeta = json.metadata || json.meta || json.data || {};
                  const metaUpdate: any = { ...(baseMeta as any) };
                  // If KIRE metadata present under 'kire' or 'kire_metadata', keep it nested
                  if ((json as any).kire_metadata && !metaUpdate.kire) metaUpdate.kire = (json as any).kire_metadata;
                  if (json.model && !metaUpdate.model) metaUpdate.model = json.model;
                  if (typeof json.confidence === "number") metaUpdate.confidence = json.confidence;
                  if (usage.total_tokens || (usage.prompt_tokens && usage.completion_tokens)) {
                    metaUpdate.tokens = usage.total_tokens || (usage.prompt_tokens + usage.completion_tokens);
                  }
                  if (json.cost !== undefined) metaUpdate.cost = json.cost;
                  metadata = { ...metadata, ...metaUpdate };
                }

                // Content deltas
                if (
                  typeof json === "string" ||
                  json.delta ||
                  json.content ||
                  json.text ||
                  json.answer
                ) {
                  const newContent =
                    (typeof json === "string" && json) ||
                    (typeof json.delta === "string" && json.delta) ||
                    json.content ||
                    json.text ||
                    json.answer ||
                    "";
                  if (newContent) {
                    fullText += newContent;

                    // Update message in real-time
                    setMessages((prev) =>
                      prev.map((m) =>
                        m.id === assistantId ? { ...m, content: fullText } : m
                      )
                    );
                  }
                }

                if (json.done === true || json.event === "done") {
                  streamDone = true;
                }
              } catch (e) {
                // Handle non-JSON streaming data
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
          // Flush any remaining buffered data after stream ends
          const tail = (buffer || "").trim();
          if (tail && tail !== "data: [DONE]") {
            let data = tail.startsWith("data:") ? tail.replace(/^data:\s*/, "") : tail;
            try {
              const json = JSON.parse(data);
              if (
                typeof json === "string" ||
                json.content ||
                json.text ||
                json.answer
              ) {
                const newContent =
                  (typeof json === "string" && json) ||
                  json.content ||
                  json.text ||
                  json.answer ||
                  "";
                if (newContent) {
                  fullText += newContent;
                  setMessages((prev) =>
                    prev.map((m) => (m.id === assistantId ? { ...m, content: fullText } : m))
                  );
                }
              }
              if (json.metadata || json.meta || json.data || json.usage || json.model) {
                const usage = json.usage || json.token_usage || {};
                const baseMeta = json.metadata || json.meta || json.data || {};
                const metaUpdate: any = { ...(baseMeta as any) };
                if ((json as any).kire_metadata && !metaUpdate.kire) metaUpdate.kire = (json as any).kire_metadata;
                if (json.model && !metaUpdate.model) metaUpdate.model = json.model;
                if (usage.total_tokens || (usage.prompt_tokens && usage.completion_tokens)) {
                  metaUpdate.tokens = usage.total_tokens || (usage.prompt_tokens + usage.completion_tokens);
                }
                if (json.cost !== undefined) metaUpdate.cost = json.cost;
                metadata = { ...metadata, ...metaUpdate };
              }
            } catch {
              fullText += data;
              setMessages((prev) =>
                prev.map((m) => (m.id === assistantId ? { ...m, content: fullText } : m))
              );
            }
          }
        } else {
          // Handle non-streaming response (JSON or text)
          const ct2 = response.headers.get("content-type") || "";
          if (ct2.includes("application/json")) {
            const result = await response.json();
            fullText =
              result.answer ||
              result.content ||
              result.text ||
              result.message ||
              result.response ||
              "";
            const usage = result.usage || result.token_usage || {};
            metadata = {
              ...(result.metadata || result.meta || {}),
              ...(result.kire_metadata ? { kire: result.kire_metadata } : {}),
              model: result.model || (result.metadata?.model ?? result.meta?.model),
              tokens:
                usage.total_tokens ||
                (usage.prompt_tokens && usage.completion_tokens
                  ? usage.prompt_tokens + usage.completion_tokens
                  : undefined),
              cost: result.cost,
              confidence:
                typeof result.confidence === "number"
                  ? result.confidence
                  : (result.metadata?.confidence ?? result.meta?.confidence),
            } as any;
          } else {
            fullText = await response.text();
          }
        }

        // Calculate final metrics
        const latency = Math.round(performance.now() - startTime);

        // Create final message
        const finalMessage: ChatMessage = {
          ...placeholder,
          content: fullText.trim(),
          status: "completed",
          metadata: {
            ...metadata,
            latencyMs: latency,
            model: (metadata && (metadata as any).model) || settings.model,
            tokens:
              (metadata && (metadata as any).tokens) ||
              Math.ceil(fullText.length / 4),
            cost: metadata.cost || 0,
          },
        };

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

        // Generate artifacts for certain message types
        if (
          finalMessage.type === "code" ||
          finalMessage.type === "analysis" ||
          finalMessage.content.includes("```")
        ) {
          generateArtifactFromMessage(finalMessage);
        }
      } catch (error) {
        if ((error as any)?.name === "AbortError") {
          setIsTyping(false);
          return;
        }

        // Prevent console error interceptor issues by using structured logging
        const errorDetails = {
          name: (error as any)?.name || 'UnknownError',
          message: (error as any)?.message || 'Unknown error occurred',
          stack: (error as any)?.stack,
          cause: (error as any)?.cause,
          timestamp: new Date().toISOString(),
          context: {
            sessionId,
            conversationId,
            userId: user?.user_id,
            runtimeUrl,
            messageType: type,
          }
        };

        // Use safe console to avoid interceptor issues
        safeError('Chat error occurred', errorDetails, {
          skipInProduction: false,
          useStructuredLogging: true,
        });

        // Provide more specific error messages
        let errorContent =
          "I apologize, but I encountered an error processing your request. Please try again.";
        let errorTitle = "Chat Error";

        if (
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
                safeInfo("Backend is accessible, but chat endpoint may have issues");
              }
            })
            .catch((healthError) => {
              safeError("Backend health check failed:", healthError);
            });
        }

        const errorMessage: ChatMessage = {
          id: assistantId,
          role: "assistant",
          content: errorContent,
          timestamp: new Date(),
          type: "text",
          status: "error",
          metadata: {},
        };

        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? errorMessage : m))
        );

        toast({
          variant: "destructive",
          title: errorTitle,
          description:
            error instanceof Error
              ? error.message
              : "Failed to get AI response",
        });
      } finally {
        setIsTyping(false);
      }
    } catch (outerError) {
      // Catch any unhandled errors in the sendMessage function
      safeError('Critical error in sendMessage', {
        error: outerError,
        message: (outerError as any)?.message,
        stack: (outerError as any)?.stack,
        timestamp: new Date().toISOString(),
      }, {
        skipInProduction: false,
        useStructuredLogging: true,
      });
      
      setIsTyping(false);
      
      toast({
        variant: "destructive",
        title: "Critical Error",
        description: "An unexpected error occurred. Please refresh the page and try again.",
      });
    }
    },
    [
      isTyping,
      settings,
      sessionId,
      conversationId,
      user?.user_id,
      triggerHooks,
      onMessageSent,
      onMessageReceived,
      runtimeUrl,
      useCopilotKit,
      copilotKit,
      enableCodeAssistance,
      enableContextualHelp,
      enableDocGeneration,
      maxMessages,
      clearPreservedInput,
      toast,
      configManager,
    ]
  );

  // Copilot action handler
  const handleCopilotAction = useCallback(
    async (action: CopilotAction) => {
      if (isTyping) return;

      // Build context-aware prompt
      let prompt = action.prompt;

      // Add selected text if available
      if (selectedText && action.requiresSelection) {
        prompt += `\n\nSelected text:\n${selectedText}`;
      }

      // Add code context if relevant
      if (
        action.contextTypes?.includes("code") &&
        (codeValue || selectedText?.includes("function"))
      ) {
        const code = codeValue || selectedText;
        prompt += `\n\nCode context:\n\`\`\`${settings.language}\n${code}\n\`\`\``;
      }

      // Send message with appropriate type
      const messageType =
        action.category === "code"
          ? "code"
          : action.category === "docs"
          ? "documentation"
          : action.category === "analysis"
          ? "analysis"
          : "text";

      await sendMessage(prompt, messageType, {
        language: settings.language,
        enableAnalysis:
          action.category === "debug" || action.category === "analysis",
        context: {
          action: action.id,
          category: action.category,
          selectedText: selectedText || undefined,
          codeContext: codeValue || undefined,
        },
      });
    },
    [isTyping, selectedText, codeValue, settings.language, sendMessage]
  );

  // Handle form submission
  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const content = activeTab === "code" ? codeValue : inputValue;
      if (content.trim() && !isTyping) {
        // Check for slash commands first
        const slashAction = parseSlashCommand(content.trim());
        if (slashAction) {
          handleCopilotAction(slashAction);
          return;
        }

        const messageType =
          activeTab === "code" ||
          content.includes("```") ||
          content.includes("function") ||
          content.includes("class")
            ? "code"
            : "text";
        sendMessage(content, messageType, {
          language: settings.language,
          enableAnalysis: activeTab === "code" || enableCodeAssistance,
        });
      }
    },
    [
      inputValue,
      codeValue,
      activeTab,
      isTyping,
      sendMessage,
      settings.language,
      enableCodeAssistance,
      handleCopilotAction,
    ]
  );

  // Quick action handlers
  const handleQuickAction = useCallback(
    (action: string, prompt: string, type: ChatMessage["type"] = "text") => {
      if (isTyping) return;
      sendMessage(prompt, type, {
        enableAnalysis: action === "debug" || action === "analyze",
      });
    },
    [isTyping, sendMessage]
  );

  // Code analysis handler
  const handleCodeAnalysis = useCallback(async () => {
    if (!codeValue.trim() || isAnalyzing) return;

    setIsAnalyzing(true);
    try {
      const analysisPrompt = `Analyze this ${settings.language} code for issues, performance, and best practices:\n\n\`\`\`${settings.language}\n${codeValue}\n\`\`\``;
      await sendMessage(analysisPrompt, "analysis", {
        language: settings.language,
        enableAnalysis: true,
        context: { code: codeValue, analysisType: "comprehensive" },
      });
    } finally {
      setIsAnalyzing(false);
    }
  }, [codeValue, settings.language, isAnalyzing, sendMessage]);



  // Copilot artifact handlers
  const handleArtifactApprove = useCallback(
    (artifactId: string) => {
      setCopilotArtifacts((prev) =>
        prev.map((artifact) =>
          artifact.id === artifactId
            ? { ...artifact, status: "approved" as const }
            : artifact
        )
      );
      toast({
        title: "Artifact Approved",
        description: "The copilot suggestion has been approved.",
      });
    },
    [toast]
  );

  const handleArtifactReject = useCallback(
    (artifactId: string) => {
      setCopilotArtifacts((prev) =>
        prev.map((artifact) =>
          artifact.id === artifactId
            ? { ...artifact, status: "rejected" as const }
            : artifact
        )
      );
      toast({
        title: "Artifact Rejected",
        description: "The copilot suggestion has been rejected.",
      });
    },
    [toast]
  );

  const handleArtifactApply = useCallback(
    async (artifactId: string) => {
      const artifact = copilotArtifacts.find((a) => a.id === artifactId);
      if (!artifact) return;

      // Here you would implement the actual application logic
      // For now, just mark as applied
      setCopilotArtifacts((prev) =>
        prev.map((a) =>
          a.id === artifactId ? { ...a, status: "applied" as const } : a
        )
      );

      toast({
        title: "Changes Applied",
        description: `${artifact.title} has been applied successfully.`,
      });
    },
    [copilotArtifacts, toast]
  );

  // Generate artifacts from AI messages
  const generateArtifactFromMessage = useCallback((message: ChatMessage) => {
    // Extract code blocks from message content
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const matches = [...message.content.matchAll(codeBlockRegex)];

    if (matches.length > 0) {
      const newArtifacts: CopilotArtifact[] = matches.map((match, index) => {
        const language = match[1] || "text";
        const content = match[2].trim();

        // Determine artifact type based on message type and content
        let artifactType: CopilotArtifact["type"] = "code";
        if (message.type === "analysis") {
          artifactType = "analysis";
        } else if (
          content.includes("test") ||
          content.includes("describe") ||
          content.includes("it(")
        ) {
          artifactType = "test";
        } else if (
          content.includes("diff") ||
          content.includes("---") ||
          content.includes("+++")
        ) {
          artifactType = "diff";
        }

        return {
          id: `artifact_${message.id}_${index}`,
          type: artifactType,
          title: `${
            artifactType === "test"
              ? "Generated Tests"
              : artifactType === "analysis"
              ? "Code Analysis"
              : artifactType === "diff"
              ? "Code Changes"
              : "Code Suggestion"
          }`,
          description: `Generated from AI response`,
          content,
          language,
          metadata: {
            confidence: message.metadata?.confidence || 0.8,
            complexity:
              content.length > 500
                ? "high"
                : content.length > 200
                ? "medium"
                : "low",
            impact: artifactType === "diff" ? "high" : "medium",
            category: message.type || "general",
            tags: [language, artifactType, "ai-generated"],
          },
          status: "pending",
          timestamp: new Date(),
        };
      });

      setCopilotArtifacts((prev) => [...prev, ...newArtifacts]);
    }
  }, []);

  // Voice input handlers
  const startRecording = useCallback(async () => {
    if (!enableVoiceInput || isRecording) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      const chunks: BlobPart[] = [];
      mediaRecorder.ondataavailable = (event) => {
        chunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: "audio/wav" });
        // TODO: Implement speech-to-text conversion
        toast({
          title: "Voice Input",
          description: "Speech-to-text conversion would be implemented here",
        });
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Voice Input Error",
        description: "Failed to access microphone",
      });
    }
  }, [enableVoiceInput, isRecording, toast]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream
        .getTracks()
        .forEach((track) => track.stop());
      setIsRecording(false);
    }
  }, [isRecording]);

  // Message actions
  const handleMessageAction = useCallback(
    async (messageId: string, action: string) => {
      const message = messages.find((m) => m.id === messageId);
      if (!message) return;

      switch (action) {
        case "copy":
          await navigator.clipboard.writeText(message.content);
          toast({
            title: "Copied",
            description: "Message copied to clipboard",
          });
          break;

        case "rate_up":
        case "rate_down":
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

        case "regenerate":
          if (message.role === "assistant") {
            const userMessage =
              messages[messages.findIndex((m) => m.id === messageId) - 1];
            if (userMessage) {
              sendMessage(userMessage.content, userMessage.type);
            }
          }
          break;

        case "select":
          setSelectedMessages((prev) => {
            const newSet = new Set(prev);
            if (newSet.has(messageId)) {
              newSet.delete(messageId);
            } else {
              newSet.add(messageId);
            }
            return newSet;
          });
          break;
      }
    },
    [messages, toast, triggerHooks, user?.user_id, sendMessage]
  );

  // Settings handlers
  const handleSettingsChange = useCallback(
    (newSettings: Partial<ChatSettings>) => {
      const updatedSettings = { ...settings, ...newSettings };
      setSettings(updatedSettings);
      if (onSettingsChange) {
        onSettingsChange(updatedSettings);
      }
    },
    [settings, onSettingsChange]
  );

  // Export/Share handlers
  const handleExport = useCallback(() => {
    if (onExport) {
      onExport(messages);
    } else {
      const exportData = {
        messages,
        sessionId,
        conversationId,
        timestamp: new Date().toISOString(),
        settings,
        analytics,
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: "application/json",
      });

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `chat-export-${new Date().toISOString().split("T")[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }
  }, [messages, sessionId, conversationId, settings, analytics, onExport]);

  // Render components
  const renderChatTab = () => (
    <div className="flex-1 flex flex-col">
      {/* Degraded Mode Banner */}
      <div className="px-4 pt-4">
        <DegradedModeBanner
          onRetry={() => {
            // Refresh the chat interface or attempt to reconnect
            window.location.reload();
          }}
          onDismiss={() => {
            // Banner will handle its own dismissal
          }}
        />
      </div>

      {/* Profile Selector */}
      <div className="px-4 pt-2">
        <ProfileSelector />
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 px-4">
        <div
          className="space-y-4 pb-4"
          role="log"
          aria-live="polite"
          aria-relevant="additions text"
        >
          {messages.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <div className="text-lg font-medium mb-2">
                Welcome to AI Assistant
                {useCopilotKit && (
                  <Badge variant="secondary" className="ml-2 text-xs">
                    CopilotKit Enhanced
                  </Badge>
                )}
              </div>
              <div className="text-sm">
                I can help you with code, answer questions, and provide
                suggestions.
                {enableCodeAssistance &&
                  " Try asking me about code or programming concepts!"}
              </div>
            </div>
          ) : (
            messages.map((message) => {
              // Get artifacts associated with this message
              const messageArtifacts = copilotArtifacts.filter((artifact) =>
                artifact.id.includes(message.id)
              );

              return (
                <div key={message.id} className="group relative" role="listitem">
                  <EnhancedMessageBubble
                    role={message.role}
                    content={message.content}
                    type={message.type}
                    language={message.language}
                    artifacts={messageArtifacts}
                    meta={{
                      confidence: message.metadata?.confidence,
                      latencyMs: message.metadata?.latencyMs,
                      model: message.metadata?.model,
                      tokens: (message.metadata as any)?.tokens,
                      cost: (message.metadata as any)?.cost,
                      persona: message.metadata?.persona,
                      mood: message.metadata?.mood,
                      intent: message.metadata?.intent,
                      reasoning: message.metadata?.reasoning,
                      sources: message.metadata?.sources,
                    }}
                    onArtifactAction={(artifactId, actionId) => {
                      // Handle artifact actions
                      safeInfo("Artifact action:", { artifactId, actionId });
                    }}
                    onApprove={handleArtifactApprove}
                    onReject={handleArtifactReject}
                    onApply={handleArtifactApply}
                    onCopy={(content) => {
                      handleMessageAction(message.id, "copy");
                    }}
                    onRegenerate={() => {
                      handleMessageAction(message.id, "regenerate");
                    }}
                    theme={settings.theme === "dark" ? "dark" : "light"}
                  />
                </div>
              );
            })
          )}

          {isTyping && (
            <div className="flex gap-3 mb-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                <Bot className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <div className="inline-block p-3 rounded-lg bg-muted border">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-muted-foreground">
                      AI is thinking...
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={placeholder}
              disabled={isTyping}
              className="pr-20"
            />

            {/* Voice Input Button */}
            {enableVoiceInput && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-12 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
                onClick={isRecording ? stopRecording : startRecording}
                disabled={isTyping}
              >
                {isRecording ? (
                  <MicOff className="h-4 w-4 text-red-500" />
                ) : (
                  <Mic className="h-4 w-4" />
                )}
              </Button>
            )}

            {/* File Upload Button */}
            {enableFileUpload && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-6 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
                disabled={isTyping}
              >
                <Paperclip className="h-4 w-4" />
              </Button>
            )}
          </div>

          <Button
            type="submit"
            disabled={!inputValue.trim() || isTyping}
            size="sm"
          >
            {isTyping ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>

        {/* Copilot Actions and Quick Actions */}
        <div className="flex items-center justify-between mt-2">
          <CopilotActions
            onActionTriggered={handleCopilotAction}
            context={chatContext}
            disabled={isTyping}
            showShortcuts={true}
          />

          <div className="flex items-center gap-2 flex-wrap">
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleQuickAction("debug", "Help me debug this code", "code")
              }
              disabled={isTyping}
            >
              <Code className="h-3 w-3 mr-1" />
              Debug Code
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleQuickAction("explain", "Explain this concept", "text")
              }
              disabled={isTyping}
            >
              <Lightbulb className="h-3 w-3 mr-1" />
              Explain
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                handleQuickAction(
                  "docs",
                  "Generate documentation",
                  "documentation"
                )
              }
              disabled={isTyping}
            >
              <FileText className="h-3 w-3 mr-1" />
              Document
            </Button>
            {useCopilotKit && (
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  handleQuickAction("optimize", "Optimize this code", "code")
                }
                disabled={isTyping}
              >
                <Zap className="h-3 w-3 mr-1" />
                Optimize
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const renderCodeTab = () => (
    <div className="flex-1 flex flex-col">
      {/* Toolbar */}
      <div className="px-3 py-2 border-b flex items-center justify-between bg-background/50">
        <div className="flex items-center gap-2">
          <Code className="h-4 w-4" />
          <span className="font-medium">Code Assistant</span>
          {useCopilotKit && <Badge variant="secondary" className="text-[10px]">AI</Badge>}
          <Badge variant="outline" className="text-[10px]">{settings.model || 'model'}</Badge>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={settings.language}
            onChange={(e) => handleSettingsChange({ language: e.target.value })}
            className="px-2 py-1 border rounded-md text-xs"
          >
            <option value="javascript">JavaScript</option>
            <option value="typescript">TypeScript</option>
            <option value="python">Python</option>
            <option value="java">Java</option>
            <option value="cpp">C++</option>
            <option value="csharp">C#</option>
            <option value="go">Go</option>
            <option value="rust">Rust</option>
            <option value="php">PHP</option>
            <option value="ruby">Ruby</option>
          </select>
          <Button variant="ghost" size="sm" className="h-8 px-2" onClick={() => setShowCodePreview(!showCodePreview)} title={showCodePreview ? 'Hide Preview' : 'Show Preview'}>
            {showCodePreview ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Editor + Preview */}
      <div className={`grid gap-3 p-3 ${showCodePreview ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'}`}>
        <div className="flex flex-col min-h-[300px]">
          {useCopilotKit ? (
            <CopilotTextarea
              value={codeValue}
              onChange={setCodeValue}
              placeholder="Write your code here... AI will provide suggestions as you type."
              language={settings.language}
              enableSuggestions={settings.enableSuggestions}
              enableCodeAnalysis={settings.enableCodeAnalysis}
              enableDocGeneration={enableDocGeneration}
              className="flex-1"
              rows={18}
              disabled={isTyping}
            />
          ) : (
            <Textarea
              ref={codeTextareaRef}
              value={codeValue}
              onChange={(e) => setCodeValue(e.target.value)}
              placeholder="Write your code here..."
              className="flex-1 font-mono text-sm resize-none"
              rows={18}
              disabled={isTyping}
            />
          )}
          {/* Actions */}
          <div className="flex flex-wrap gap-2 mt-3">
            <Button onClick={() => sendMessage(codeValue, "code", { language: settings.language, enableAnalysis: true })} disabled={!codeValue.trim() || isTyping}>
              {isTyping ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Send className="h-4 w-4 mr-2" />}
              Send Code
            </Button>
            <Button variant="outline" onClick={handleCodeAnalysis} disabled={!codeValue.trim() || isTyping || isAnalyzing}>
              {isAnalyzing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <AlertCircle className="h-4 w-4 mr-2" />}
              Analyze
            </Button>
            <Button variant="outline" onClick={() => handleQuickAction("optimize", `Optimize this ${settings.language} code:\n\n\`\`\`${settings.language}\n${codeValue}\n\`\`\``, "code")} disabled={!codeValue.trim() || isTyping}>
              <Zap className="h-4 w-4 mr-2" />
              Optimize
            </Button>
            <Button variant="outline" onClick={() => handleQuickAction("docs", `Generate documentation for this ${settings.language} code:\n\n\`\`\`${settings.language}\n${codeValue}\n\`\`\``, "documentation")} disabled={!codeValue.trim() || isTyping}>
              <FileText className="h-4 w-4 mr-2" />
              Document
            </Button>
          </div>
        </div>

        {showCodePreview && (
          <div className="min-h-[300px] border rounded-md p-3 bg-muted/30">
            <div className="text-xs text-muted-foreground mb-2">Preview</div>
            <pre className="text-xs md:text-sm whitespace-pre-wrap font-mono overflow-auto max-h-[60vh]">{codeValue || '// Start typing code to preview here'}</pre>
          </div>
        )}
      </div>

      {/* Status bar */}
      <div className="px-3 py-2 text-[11px] md:text-xs text-muted-foreground border-t flex items-center gap-3">
        <span>Language: {settings.language}</span>
        <span>Model: {settings.model}</span>
        {isTyping && (
          <span className="inline-flex items-center gap-1">
            <Loader2 className="h-3 w-3 animate-spin" /> generating…
          </span>
        )}
      </div>
    </div>
  );

  return (
    <ChatErrorBoundary>
      <Card
        className={`flex flex-col ${className} ${
          isFullscreen ? "fixed inset-0 z-50" : ""
        }`}
        style={isFullscreen ? { height: "100vh" } : { height }}
      >
        {/* Header */}
        {showHeader && (
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                AI Assistant
                {useCopilotKit && (
                  <Badge variant="secondary" className="text-xs">
                    CopilotKit Enhanced
                  </Badge>
                )}
                <Badge variant="outline" className="text-xs">
                  Production Ready
                </Badge>
              </CardTitle>

              <div className="flex items-center gap-2">
                {selectedMessages.size > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    {selectedMessages.size} selected
                  </Badge>
                )}

                {enableExport && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleExport}
                    className="h-8 w-8 p-0"
                    title="Export Chat"
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                )}

                {/* Model selector */}
                <ModelSelector
                  value={settings.model}
                  onValueChange={(value) => handleSettingsChange({ model: value })}
                  className="w-48"
                  placeholder="Select model..."
                  showDetails={true}
                />

                {enableSharing && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onShare?.(messages)}
                    className="h-8 w-8 p-0"
                    title="Share Chat"
                  >
                    <Share className="h-4 w-4" />
                  </Button>
                )}

                {/* Routing History */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowRoutingHistory(true)}
                  className="h-8 w-8 p-0"
                  title="Routing History"
                >
                  <Activity className="h-4 w-4" />
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsFullscreen(!isFullscreen)}
                  className="h-8 w-8 p-0"
                  title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
                >
                  {isFullscreen ? (
                    <Minimize2 className="h-4 w-4" />
                  ) : (
                    <Maximize2 className="h-4 w-4" />
                  )}
                </Button>

                {showSettings && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                    title="Settings"
                  >
                    <Settings className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
        )}

        <CardContent className="flex-1 flex flex-col p-0">
          {showTabs ? (
            <Tabs
              value={activeTab}
              onValueChange={(value) => setActiveTab(value as any)}
              className="flex-1 flex flex-col"
            >
              <TabsList className="grid w-full grid-cols-3 mx-4 mt-4">
                <TabsTrigger value="chat" className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Chat
                </TabsTrigger>
                <TabsTrigger value="code" className="flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  Code
                </TabsTrigger>
                <TabsTrigger
                  value="analytics"
                  className="flex items-center gap-2"
                >
                  <BarChart3 className="h-4 w-4" />
                  Analytics
                </TabsTrigger>
              </TabsList>

              <TabsContent value="chat" className="flex-1 flex flex-col mt-0">
                {renderChatTab()}
              </TabsContent>

              <TabsContent value="code" className="flex-1 flex flex-col mt-0">
                {renderCodeTab()}
              </TabsContent>

              <TabsContent
                value="analytics"
                className="flex-1 flex flex-col mt-0"
              >
                <AnalyticsTab analytics={analytics} messages={messages} />
              </TabsContent>
            </Tabs>
          ) : (
            renderChatTab()
          )}
        </CardContent>
      </Card>
      {showRoutingHistory && (
        <RoutingHistory onClose={() => setShowRoutingHistory(false)} />
      )}
    </ChatErrorBoundary>
  );
};

// ChatInterface is already exported above as default export
