// Chat message types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
  aiData?: {
    knowledgeGraphInsights?: string;
    keywords?: string[];
    confidence?: number;
    modality?: string;
    pluginId?: string;
    intent?: string;
  };
  shouldAutoPlay?: boolean;
}

// Settings types
export interface KarenSettings {
  apiKey?: string;
  userId?: string;
  sessionId?: string;
  activeListenMode: boolean;
  notifications: {
    enabled: boolean;
    alertOnSummaryReady: boolean;
    alertOnNewInsights: boolean;
  };
  personalFacts: string[];
  ttsVoiceURI?: string;
  customPersonaInstructions?: string;
  voiceSettings: {
    rate: number;
    pitch: number;
    volume: number;
  };
  behavior: {
    responseStyle: 'concise' | 'detailed' | 'conversational';
    maxResponseLength: number;
    enableProactiveSuggestions: boolean;
  };
  privacy: {
    enableAnalytics: boolean;
    enableCrashReporting: boolean;
    enablePersonalization: boolean;
  };
}

// API response types
export interface HandleUserMessageResult {
  acknowledgement?: string;
  finalResponse: string;
  proactiveSuggestion?: string;
  aiDataForFinalResponse?: ChatMessage['aiData'];
  summaryWasGenerated?: boolean;
  suggestedNewFacts?: string[];
}

// Plugin types
export interface Plugin {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  version: string;
  category: string;
  icon?: string;
  config?: Record<string, unknown>;
}

// Memory types
export interface MemoryItem {
  id: string;
  content: string;
  type: 'fact' | 'preference' | 'context';
  confidence: number;
  lastAccessed: string;
  relevanceScore: number;
  semanticCluster: string;
  relationships: string[];
  timestamp: number;
  userId: string;
  sessionId?: string;
  tenantId?: string;
}

// File types
export interface FileItem {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadedAt: Date;
  uploadedBy: string;
  path: string;
  permissions: {
    read: boolean;
    write: boolean;
    delete: boolean;
    share: boolean;
  };
  metadata?: Record<string, unknown>;
}

// Performance types
export interface PerformanceMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta?: number;
}

// API types
export interface ApiResponse<T = unknown> {
  data: T;
  status: number;
  headers: Headers;
  ok: boolean;
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  headers?: Record<string, string>;
  body?: BodyInit | Record<string, unknown>;
  params?: Record<string, unknown>;
  timeout?: number;
  signal?: AbortSignal;
}

export interface BaseApiErrorOptions {
  message: string;
  status: number;
  code?: string;
  details?: unknown;
}

// AI personality and memory types
export type MemoryDepth = 'short' | 'medium' | 'long';
export type PersonalityTone = 'neutral' | 'friendly' | 'formal' | 'humorous';
export type PersonalityVerbosity = 'concise' | 'balanced' | 'detailed';

// Weather and service types
export type TemperatureUnit = 'C' | 'F';
export type WeatherServiceOption = 'wttr_in' | 'custom_api';
