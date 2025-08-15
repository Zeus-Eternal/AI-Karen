# Path: ui_launchers/web_ui/src/services/ai-provider.ts

'use client';

import { useTelemetry } from '@/hooks/use-telemetry';

export interface AIMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  type?: 'text' | 'code' | 'command';
  metadata?: {
    confidence?: number;
    model?: string;
    latencyMs?: number;
    sources?: string[];
    reasoning?: string;
    tokens?: number;
  };
}

export interface AIStreamResponse {
  content: string;
  metadata?: {
    confidence?: number;
    model?: string;
    sources?: string[];
    reasoning?: string;
    tokens?: number;
  };
  done: boolean;
}

export interface AIProviderConfig {
  name: string;
  endpoint: string;
  apiKey?: string;
  model?: string;
  temperature?: number;
  maxTokens?: number;
  streaming?: boolean;
  headers?: Record<string, string>;
}

export interface AIProviderCapabilities {
  streaming: boolean;
  codeGeneration: boolean;
  imageGeneration: boolean;
  functionCalling: boolean;
  contextWindow: number;
  supportedModels: string[];
}

export interface AIProviderRequest {
  messages: AIMessage[];
  sessionId?: string;
  conversationId?: string;
  stream?: boolean;
  temperature?: number;
  maxTokens?: number;
  model?: string;
}

export interface AIProviderResponse {
  message: AIMessage;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  metadata?: {
    model: string;
    latencyMs: number;
    confidence?: number;
    sources?: string[];
    reasoning?: string;
  };
}

export abstract class AIProvider {
  protected config: AIProviderConfig;
  protected telemetry: ReturnType<typeof useTelemetry>;

  constructor(config: AIProviderConfig) {
    this.config = config;
    this.telemetry = useTelemetry();
  }

  abstract getCapabilities(): AIProviderCapabilities;
  abstract sendMessage(request: AIProviderRequest): Promise<AIProviderResponse>;
  abstract streamMessage(
    request: AIProviderRequest,
    onChunk: (chunk: AIStreamResponse) => void,
    onError: (error: Error) => void,
    signal?: AbortSignal
  ): Promise<void>;

  protected trackRequest(request: AIProviderRequest, startTime: number) {
    this.telemetry.track('ai_provider_request', {
      provider: this.config.name,
      model: request.model || this.config.model,
      messageCount: request.messages.length,
      streaming: request.stream,
      latencyMs: Date.now() - startTime
    });
  }

  protected trackError(error: Error, request: AIProviderRequest) {
    this.telemetry.track('ai_provider_error', {
      provider: this.config.name,
      error: error.message,
      model: request.model || this.config.model
    });
  }
}

// OpenAI Provider Implementation
export class OpenAIProvider extends AIProvider {
  getCapabilities(): AIProviderCapabilities {
    return {
      streaming: true,
      codeGeneration: true,
      imageGeneration: false,
      functionCalling: true,
      contextWindow: 128000,
      supportedModels: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']
    };
  }

  async sendMessage(request: AIProviderRequest): Promise<AIProviderResponse> {
    const startTime = Date.now();
    
    try {
      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`,
          ...this.config.headers
        },
        body: JSON.stringify({
          model: request.model || this.config.model || 'gpt-4',
          messages: request.messages.map(msg => ({
            role: msg.role,
            content: msg.content
          })),
          temperature: request.temperature ?? this.config.temperature ?? 0.7,
          max_tokens: request.maxTokens ?? this.config.maxTokens ?? 2000,
          stream: false
        })
      });

      if (!response.ok) {
        throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      const latencyMs = Date.now() - startTime;

      this.trackRequest(request, startTime);

      return {
        message: {
          id: `openai_${Date.now()}`,
          role: 'assistant',
          content: data.choices[0].message.content,
          timestamp: new Date(),
          type: 'text',
          metadata: {
            model: data.model,
            latencyMs,
            tokens: data.usage?.total_tokens
          }
        },
        usage: {
          promptTokens: data.usage?.prompt_tokens || 0,
          completionTokens: data.usage?.completion_tokens || 0,
          totalTokens: data.usage?.total_tokens || 0
        },
        metadata: {
          model: data.model,
          latencyMs
        }
      };
    } catch (error) {
      this.trackError(error as Error, request);
      throw error;
    }
  }

  async streamMessage(
    request: AIProviderRequest,
    onChunk: (chunk: AIStreamResponse) => void,
    onError: (error: Error) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const startTime = Date.now();

    try {
      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`,
          ...this.config.headers
        },
        body: JSON.stringify({
          model: request.model || this.config.model || 'gpt-4',
          messages: request.messages.map(msg => ({
            role: msg.role,
            content: msg.content
          })),
          temperature: request.temperature ?? this.config.temperature ?? 0.7,
          max_tokens: request.maxTokens ?? this.config.maxTokens ?? 2000,
          stream: true
        }),
        signal
      });

      if (!response.ok) {
        throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith('data: ')) continue;

          const data = trimmed.slice(6);
          if (data === '[DONE]') {
            onChunk({ content: '', done: true });
            break;
          }

          try {
            const parsed = JSON.parse(data);
            const content = parsed.choices?.[0]?.delta?.content || '';
            
            if (content) {
              onChunk({
                content,
                metadata: {
                  model: parsed.model
                },
                done: false
              });
            }
          } catch (e) {
            // Skip invalid JSON
          }
        }
      }

      this.trackRequest(request, startTime);
    } catch (error) {
      this.trackError(error as Error, request);
      onError(error as Error);
    }
  }
}

// Custom/Local Provider Implementation
export class CustomProvider extends AIProvider {
  getCapabilities(): AIProviderCapabilities {
    return {
      streaming: true,
      codeGeneration: true,
      imageGeneration: false,
      functionCalling: false,
      contextWindow: 4096,
      supportedModels: ['custom-model']
    };
  }

  async sendMessage(request: AIProviderRequest): Promise<AIProviderResponse> {
    const startTime = Date.now();
    
    try {
      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.config.headers
        },
        body: JSON.stringify({
          message: request.messages[request.messages.length - 1]?.content || '',
          session_id: request.sessionId,
          conversation_id: request.conversationId,
          stream: false
        })
      });

      if (!response.ok) {
        throw new Error(`Custom API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      const latencyMs = Date.now() - startTime;

      this.trackRequest(request, startTime);

      return {
        message: {
          id: `custom_${Date.now()}`,
          role: 'assistant',
          content: data.answer || data.text || data.response || '',
          timestamp: new Date(),
          type: 'text',
          metadata: {
            model: this.config.model || 'custom-model',
            latencyMs,
            confidence: data.meta?.confidence,
            sources: data.context,
            reasoning: data.meta?.reasoning
          }
        },
        metadata: {
          model: this.config.model || 'custom-model',
          latencyMs,
          confidence: data.meta?.confidence,
          sources: data.context,
          reasoning: data.meta?.reasoning
        }
      };
    } catch (error) {
      this.trackError(error as Error, request);
      throw error;
    }
  }

  async streamMessage(
    request: AIProviderRequest,
    onChunk: (chunk: AIStreamResponse) => void,
    onError: (error: Error) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const startTime = Date.now();

    try {
      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.config.headers
        },
        body: JSON.stringify({
          message: request.messages[request.messages.length - 1]?.content || '',
          session_id: request.sessionId,
          conversation_id: request.conversationId,
          stream: true
        }),
        signal
      });

      if (!response.ok) {
        throw new Error(`Custom API error: ${response.status} ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          let data = trimmed;
          if (trimmed.startsWith('data: ')) {
            data = trimmed.slice(6);
            if (data === '[DONE]') {
              onChunk({ content: '', done: true });
              break;
            }
          }

          try {
            const parsed = JSON.parse(data);
            const content = parsed.text || parsed.content || parsed.answer || '';
            
            if (content) {
              onChunk({
                content,
                metadata: {
                  model: this.config.model || 'custom-model',
                  confidence: parsed.meta?.confidence,
                  sources: parsed.context,
                  reasoning: parsed.meta?.reasoning
                },
                done: false
              });
            }
          } catch (e) {
            // Handle non-JSON streaming data
            if (!data.startsWith('{')) {
              onChunk({
                content: data,
                done: false
              });
            }
          }
        }
      }

      this.trackRequest(request, startTime);
    } catch (error) {
      this.trackError(error as Error, request);
      onError(error as Error);
    }
  }
}

// Provider Factory
export class AIProviderFactory {
  private static providers = new Map<string, new (config: AIProviderConfig) => AIProvider>();

  static registerProvider(name: string, providerClass: new (config: AIProviderConfig) => AIProvider) {
    this.providers.set(name, providerClass);
  }

  static createProvider(config: AIProviderConfig): AIProvider {
    const ProviderClass = this.providers.get(config.name);
    if (!ProviderClass) {
      throw new Error(`Unknown AI provider: ${config.name}`);
    }
    return new ProviderClass(config);
  }

  static getAvailableProviders(): string[] {
    return Array.from(this.providers.keys());
  }
}

// Register built-in providers
AIProviderFactory.registerProvider('openai', OpenAIProvider);
AIProviderFactory.registerProvider('custom', CustomProvider);

export default AIProviderFactory;