import React, { createContext, useContext } from 'react';

export interface CopilotKitConfig {
  apiKey?: string;
  baseUrl: string;
  fallbackUrls: string[];
  features: {
    codeCompletion: boolean;
    contextualSuggestions: boolean;
    debuggingAssistance: boolean;
    documentationGeneration: boolean;
    chatAssistance: boolean;
  };
  models: {
    completion: string;
    chat: string;
    embedding: string;
  };
  endpoints: {
    assist: string;
    suggestions: string;
    analyze: string;
    docs: string;
  };
}

export interface CopilotSuggestion {
  id?: string;
  title?: string;
  description?: string;
  [key: string]: unknown;
}

export interface CopilotContextType {
  config: CopilotKitConfig;
  isEnabled: boolean;
  isLoading: boolean;
  error: string | null;
  updateConfig: (newConfig: Partial<CopilotKitConfig>) => void;
  toggleFeature: (feature: keyof CopilotKitConfig['features']) => void;
  getSuggestions: (context: string, type?: string) => Promise<CopilotSuggestion[]>;
  analyzeCode: (code: string, language: string) => Promise<unknown>;
  generateDocumentation: (code: string, language: string) => Promise<string>;
}

export const CopilotContext = createContext<CopilotContextType | null>(null);

export const useCopilotKit = (): CopilotContextType => {
  const context = useContext(CopilotContext);
  if (!context) {
    throw new Error('useCopilotKit must be used within a CopilotKitProvider');
  }
  return context;
};
