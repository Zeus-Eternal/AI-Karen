
export type MessageRole = 'user' | 'assistant' | 'system';

export interface AiData {
  keywords?: string[];
  knowledgeGraphInsights?: string;
  confidence?: number;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  aiData?: AiData;
  shouldAutoPlay?: boolean;
  widget?: string;
}

// Settings types
export type MemoryDepth = "short" | "medium" | "long";
export type PersonalityTone = "neutral" | "friendly" | "formal" | "humorous";
export type PersonalityVerbosity = "concise" | "balanced" | "detailed";
export type TemperatureUnit = 'C' | 'F';
export type WeatherServiceOption = 'wttr_in' | 'openweather' | 'custom_api';

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
  activeListenMode: boolean; // Added active listen mode
}

// Type for the return value of handleUserMessage
export interface HandleUserMessageResult {
  acknowledgement?: string;
  finalResponse: string;
  aiDataForFinalResponse?: AiData;
  suggestedNewFacts?: string[];
  proactiveSuggestion?: string;
  summaryWasGenerated?: boolean;
  widget?: string;
}
