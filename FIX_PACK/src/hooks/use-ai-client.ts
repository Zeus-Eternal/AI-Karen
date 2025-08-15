# Path: ui_launchers/web_ui/src/hooks/use-ai-client.ts

'use client';

import { useState, useCallback, useEffect, useMemo } from 'react';
import { AIClient, getAIClient, createAIClient, AIClientConfig } from '@/services/ai-client';
import { AIMessage, AIStreamResponse } from '@/services/ai-provider';
import { useFeature } from '@/hooks/use-feature';
import { useTelemetry } from '@/hooks/use-telemetry';

interface UseAIClientOptions {
  defaultProvider?: string;
  enableFallback?: boolean;
  timeout?: number;
}

interface AIClientState {
  isInitialized: boolean;
  availableProviders: string[];
  currentProvider: string;
  capabilities: any;
  error: string | null;
}

interface AIClientActions {
  sendMessage: (
    messages: AIMessage[],
    sessionId?: string,
    conversationId?: string,
    options?: {
      provider?: string;
      temperature?: number;
      maxTokens?: number;
      model?: string;
    }
  ) => Promise<any>;
  
  streamMessage: (
    messages: AIMessage[],
    sessionId?: string,
    conversationId?: string,
    options?: {
      provider?: string;
      temperature?: number;
      maxTokens?: number;
      model?: string;
      onChunk?: (chunk: AIStreamResponse) => void;
      onError?: (error: Error) => void;
      signal?: AbortSignal;
    }
  ) => Promise<void>;
  
  switchProvider: (providerName: string) => void;
  getProviderCapabilities: (providerName?: string) => any;
  refreshProviders: () => void;
}

export const useAIClient = (options: UseAIClientOptions = {}): AIClientState & AIClientActions => {
  const { defaultProvider = 'custom', enableFallback = true, timeout = 30000 } = options;
  
  const [state, setState] = useState<AIClientState>({
    isInitialized: false,
    availableProviders: [],
    currentProvider: defaultProvider,
    capabilities: null,
    error: null
  });

  const { track } = useTelemetry();
  
  // Feature flags for different providers
  const openaiEnabled = useFeature('providers.openai');
  const customEnabled = useFeature('providers.custom');
  const claudeEnabled = useFeature('providers.claude');

  // AI Client configuration
  const clientConfig = useMemo((): AIClientConfig => {
    const providers = [];

    // Add custom provider (always available)
    if (customEnabled) {
      providers.push({
        name: 'custom',
        endpoint: '/api/chat',
        streaming: true,
        headers: {}
      });
    }

    // Add OpenAI provider if enabled and configured
    if (openaiEnabled) {
      const openaiKey = process.env.NEXT_PUBLIC_OPENAI_API_KEY;
      if (openaiKey) {
        providers.push({
          name: 'openai',
          endpoint: 'https://api.openai.com/v1/chat/completions',
          apiKey: openaiKey,
          model: 'gpt-4',
          streaming: true,
          temperature: 0.7,
          maxTokens: 2000
        });
      }
    }

    // Add Claude provider if enabled (placeholder)
    if (claudeEnabled) {
      providers.push({
        name: 'claude',
        endpoint: 'https://api.anthropic.com/v1/messages',
        apiKey: process.env.NEXT_PUBLIC_CLAUDE_API_KEY,
        model: 'claude-3-sonnet-20240229',
        streaming: true
      });
    }

    return {
      defaultProvider: providers.find(p => p.name === defaultProvider)?.name || providers[0]?.name || 'custom',
      providers,
      fallbackProviders: enableFallback ? providers.slice(1).map(p => p.name) : [],
      timeout
    };
  }, [defaultProvider, enableFallback, timeout, openaiEnabled, customEnabled, claudeEnabled]);

  // Initialize AI client
  useEffect(() => {
    try {
      if (clientConfig.providers.length === 0) {
        setState(prev => ({
          ...prev,
          error: 'No AI providers configured',
          isInitialized: false
        }));
        return;
      }

      const client = createAIClient(clientConfig);
      
      setState(prev => ({
        ...prev,
        isInitialized: true,
        availableProviders: client.getAvailableProviders(),
        currentProvider: clientConfig.defaultProvider,
        capabilities: client.getProviderCapabilities(),
        error: null
      }));

      track('ai_client_initialized', {
        defaultProvider: clientConfig.defaultProvider,
        availableProviders: client.getAvailableProviders(),
        fallbackEnabled: enableFallback
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to initialize AI client';
      
      setState(prev => ({
        ...prev,
        error: errorMessage,
        isInitialized: false
      }));

      track('ai_client_init_error', {
        error: errorMessage
      });
    }
  }, [clientConfig, enableFallback, track]);

  // Send message function
  const sendMessage = useCallback(async (
    messages: AIMessage[],
    sessionId?: string,
    conversationId?: string,
    options: {
      provider?: string;
      temperature?: number;
      maxTokens?: number;
      model?: string;
    } = {}
  ) => {
    if (!state.isInitialized) {
      throw new Error('AI client not initialized');
    }

    const client = getAIClient();
    const startTime = Date.now();

    try {
      const response = await client.sendMessage(messages, sessionId, conversationId, {
        provider: options.provider || state.currentProvider,
        temperature: options.temperature,
        maxTokens: options.maxTokens,
        model: options.model
      });

      track('ai_client_message_success', {
        provider: options.provider || state.currentProvider,
        messageCount: messages.length,
        latencyMs: Date.now() - startTime
      });

      return response;
    } catch (error) {
      track('ai_client_message_error', {
        provider: options.provider || state.currentProvider,
        error: error instanceof Error ? error.message : 'Unknown error',
        latencyMs: Date.now() - startTime
      });
      throw error;
    }
  }, [state.isInitialized, state.currentProvider, track]);

  // Stream message function
  const streamMessage = useCallback(async (
    messages: AIMessage[],
    sessionId?: string,
    conversationId?: string,
    options: {
      provider?: string;
      temperature?: number;
      maxTokens?: number;
      model?: string;
      onChunk?: (chunk: AIStreamResponse) => void;
      onError?: (error: Error) => void;
      signal?: AbortSignal;
    } = {}
  ) => {
    if (!state.isInitialized) {
      throw new Error('AI client not initialized');
    }

    const client = getAIClient();
    const startTime = Date.now();

    try {
      await client.streamMessage(messages, sessionId, conversationId, {
        provider: options.provider || state.currentProvider,
        temperature: options.temperature,
        maxTokens: options.maxTokens,
        model: options.model,
        onChunk: options.onChunk,
        onError: options.onError,
        signal: options.signal
      });

      track('ai_client_stream_success', {
        provider: options.provider || state.currentProvider,
        messageCount: messages.length,
        latencyMs: Date.now() - startTime
      });
    } catch (error) {
      track('ai_client_stream_error', {
        provider: options.provider || state.currentProvider,
        error: error instanceof Error ? error.message : 'Unknown error',
        latencyMs: Date.now() - startTime
      });
      throw error;
    }
  }, [state.isInitialized, state.currentProvider, track]);

  // Switch provider function
  const switchProvider = useCallback((providerName: string) => {
    if (!state.isInitialized) {
      return;
    }

    const client = getAIClient();
    
    if (!client.isProviderAvailable(providerName)) {
      setState(prev => ({
        ...prev,
        error: `Provider ${providerName} is not available`
      }));
      return;
    }

    setState(prev => ({
      ...prev,
      currentProvider: providerName,
      capabilities: client.getProviderCapabilities(providerName),
      error: null
    }));

    track('ai_provider_switched', {
      fromProvider: state.currentProvider,
      toProvider: providerName
    });
  }, [state.isInitialized, state.currentProvider, track]);

  // Get provider capabilities
  const getProviderCapabilities = useCallback((providerName?: string) => {
    if (!state.isInitialized) {
      return null;
    }

    const client = getAIClient();
    return client.getProviderCapabilities(providerName);
  }, [state.isInitialized]);

  // Refresh providers
  const refreshProviders = useCallback(() => {
    if (!state.isInitialized) {
      return;
    }

    const client = getAIClient();
    
    setState(prev => ({
      ...prev,
      availableProviders: client.getAvailableProviders(),
      capabilities: client.getProviderCapabilities(prev.currentProvider)
    }));

    track('ai_providers_refreshed', {
      availableProviders: client.getAvailableProviders()
    });
  }, [state.isInitialized, track]);

  return {
    ...state,
    sendMessage,
    streamMessage,
    switchProvider,
    getProviderCapabilities,
    refreshProviders
  };
};

export default useAIClient;