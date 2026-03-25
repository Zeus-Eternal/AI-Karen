export type MessageRole = 'user' | 'assistant' | 'system';

export interface AiData {
  keywords?: string[];
  knowledgeGraphInsights?: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  aiData?: AiData;
  imageDataUri?: string; 
  shouldAutoPlay?: boolean;
  structuredContent?: Record<string, any>;
  actions?: any[];
  metadata?: Record<string, any>;
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

// This is deprecated as the backend logic has been removed.
export interface HandleUserMessageResult {
  acknowledgement?: string;
  finalResponse: string;
  aiDataForFinalResponse?: AiData;
  suggestedNewFacts?: string[];
  proactiveSuggestion?: string;
  summaryWasGenerated?: boolean;
  generatedImageDataUri?: string;
}
