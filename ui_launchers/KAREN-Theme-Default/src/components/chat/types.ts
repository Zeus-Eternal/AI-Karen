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
    suggestions?: unknown[];
    analysis?: unknown;
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

export interface ChatSettings {
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

export interface ChatAnalytics {
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

export interface ChatInterfaceProps {
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