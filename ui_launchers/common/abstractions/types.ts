// Shared type definitions for all UI launchers
// These types are framework-agnostic and can be used across React and Tauri

export type MessageRole = 'user' | 'assistant' | 'system';
export type MemoryDepth = "short" | "medium" | "long";
export type PersonalityTone = "neutral" | "friendly" | "formal" | "humorous";
export type PersonalityVerbosity = "concise" | "balanced" | "detailed";
export type TemperatureUnit = 'C' | 'F';
export type WeatherServiceOption = 'wttr_in' | 'openweather' | 'custom_api';

export interface AiData {
  keywords?: string[];
  knowledgeGraphInsights?: string;
  confidence?: number;
  reasoning?: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  aiData?: AiData;
  shouldAutoPlay?: boolean;
  attachments?: MessageAttachment[];
}

export interface MessageAttachment {
  id: string;
  name: string;
  size: string;
  type: string;
  url?: string;
}

export interface NotificationPreferences {
  enabled: boolean;
  alertOnNewInsights: boolean;
  alertOnSummaryReady: boolean;
}

export interface KarenSettings {
  memoryDepth: MemoryDepth;
  personalityTone: PersonalityTone;
  personalityVerbosity: PersonalityVerbosity;
  personalFacts: string[];
  notifications: NotificationPreferences;
  ttsVoiceURI: string | null;
  customPersonaInstructions: string;
  temperatureUnit: TemperatureUnit;
  weatherService: WeatherServiceOption;
  weatherApiKey: string | null;
  defaultWeatherLocation: string | null;
  activeListenMode: boolean;
}

export interface HandleUserMessageResult {
  acknowledgement?: string;
  finalResponse: string;
  aiDataForFinalResponse?: AiData;
  suggestedNewFacts?: string[];
  proactiveSuggestion?: string;
  summaryWasGenerated?: boolean;
}

// Component state interfaces
export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  isRecording: boolean;
  input: string;
  settings: KarenSettings;
}

export interface SettingsState {
  settings: KarenSettings;
  isDirty: boolean;
  isLoading: boolean;
  errors: Record<string, string>;
}

// Event interfaces
export interface ChatEvent {
  type: 'message_sent' | 'message_received' | 'recording_started' | 'recording_stopped' | 'settings_changed';
  payload: unknown;
  timestamp: Date;
}

export interface SettingsEvent {
  type: 'setting_changed' | 'settings_saved' | 'settings_reset';
  payload: unknown;
  timestamp: Date;
}

// Theme interfaces
export interface ThemeColors {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  error: string;
  warning: string;
  success: string;
  info: string;
}

export interface ThemeSpacing {
  xs: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
  xxl: string;
}

export interface ThemeTypography {
  fontFamily: string;
  fontSize: {
    xs: string;
    sm: string;
    base: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  fontWeight: {
    light: number;
    normal: number;
    medium: number;
    semibold: number;
    bold: number;
  };
  lineHeight: {
    tight: number;
    normal: number;
    relaxed: number;
  };
}

export interface Theme {
  name: string;
  colors: ThemeColors;
  spacing: ThemeSpacing;
  typography: ThemeTypography;
  borderRadius: string;
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}

// Plugin interfaces
export interface PluginInfo {
  name: string;
  description: string;
  version: string;
  category: string;
  enabled: boolean;
  parameters: Record<string, unknown>;
  author: string;
}

export interface PluginExecutionRequest {
  pluginName: string;
  parameters: Record<string, unknown>;
  userId?: string;
  sessionId?: string;
  timeout?: number;
}

export interface PluginExecutionResult {
  success: boolean;
  result?: unknown;
  stdout?: string;
  stderr?: string;
  error?: string;
  executionTime: number;
  timestamp: Date;
}

// Memory interfaces
export interface MemoryEntry {
  id: string;
  content: string;
  metadata: Record<string, unknown>;
  tags: string[];
  userId?: string;
  sessionId?: string;
  timestamp: Date;
  similarityScore?: number;
}

export interface MemoryQuery {
  text: string;
  userId?: string;
  sessionId?: string;
  tags?: string[];
  topK?: number;
  similarityThreshold?: number;
  timeRange?: [Date, Date];
}

// Analytics interfaces
export interface AnalyticsEvent {
  id: string;
  userId?: string;
  eventType: string;
  eventData: Record<string, unknown>;
  timestamp: Date;
}

export interface AnalyticsMetrics {
  totalMessages: number;
  totalSessions: number;
  averageSessionLength: number;
  topPlugins: Array<{ name: string; usage: number }>;
  userEngagement: {
    dailyActiveUsers: number;
    weeklyActiveUsers: number;
    monthlyActiveUsers: number;
  };
}