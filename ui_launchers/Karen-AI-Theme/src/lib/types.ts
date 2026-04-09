export type MessageRole = 'user' | 'assistant' | 'system';

export interface AiData {
  keywords?: string[];
  knowledgeGraphInsights?: string;
}

import type { SuggestedAction } from '@/lib/agent-ui/service';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  aiData?: AiData;
  imageDataUri?: string;
  shouldAutoPlay?: boolean;
  structuredContent?: Record<string, unknown>;
  actions?: SuggestedAction[];
  metadata?: Record<string, unknown>;
  status?: 'pending' | 'streaming' | 'completed' | 'failed';
}

// Settings types
export type MemoryDepth = "short" | "medium" | "long";
export type PersonalityTone = "neutral" | "friendly" | "formal" | "humorous";
export type PersonalityVerbosity = "concise" | "balanced" | "detailed";
export type TemperatureUnit = 'C' | 'F';
export type WeatherServiceOption = 'wttr_in' | 'custom_api';

export interface NotificationPreferences {
  enabled: boolean;
  alertOnNewInsights: boolean;
  alertOnSummaryReady: boolean;
}

export interface ApiKeys {
  imageGen?: string | null;
  videoGen?: string | null;
  webSearch?: string | null;
  vectorDb?: string | null;
}

export interface KarenSettings {
  apiKeys: ApiKeys;
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

export interface MessageResponse {
  id: string;
  role: string;
  content: string;
  timestamp: string;
  metadata: Record<string, unknown>;
  function_call?: Record<string, unknown>;
  function_response?: Record<string, unknown>;
  ui_source?: string;
  ai_confidence?: number;
  processing_time_ms?: number;
  tokens_used?: number;
  model_used?: string;
  user_feedback?: string;
  structured_content?: Record<string, unknown>;
  actions?: Array<{
    type: string;
    description?: string;
    confidence?: number;
  }>;
  edited: boolean;
  edit_history: unknown[];
}

export interface ConversationResponse {
  id: string;
  user_id: string;
  title?: string;
  messages: MessageResponse[];
  metadata: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_at?: string;
  session_id?: string;
  ui_context: Record<string, any>;
  ai_insights: Record<string, any>;
  user_settings: Record<string, any>;
  summary?: string;
  tags: string[];
  last_ai_response_id?: string;
  status: string;
  priority: string;
  context_memories: any[];
  proactive_suggestions: string[];
}
