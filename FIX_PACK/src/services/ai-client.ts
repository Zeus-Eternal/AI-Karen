# Path: ui_launchers/web_ui/src/services/ai-client.ts

'use client';

import { 
  AIProvider, 
  AIProviderFactory, 
  AIProviderConfig, 
  AIProviderRequest, 
  AIProviderResponse,
  AIMessage,
  AIStreamResponse
} from './ai-provider';
import { useTelemetry } from '@/hooks/use-telemetry';

export interface AIClientConfig {
  defaultProvider: string;
  providers: AIProviderConfig[];
  fallbackProviders?: string[];
  retryAttempts?: number;
  timeout?: number;
}

export interface SendMessageOptions {
  provider?: string;
  stream?: boolean;
  temperature?: number;
  maxTokens?: number;
  model?: string;
  onChunk?: (chunk: AIStreamResponse) => void;
  onError?: (error: Error) => void;
  signal?: AbortSignal;
}

export class AIClient {
  private providers: Map<string, AIProvider> = new Map();
  private config: AIClientConfig;
  private telemetry: ReturnType<typeof useTelemetry>;

  constructor(config: AIClientConfig) {
    this.config = config;
    this.telemetry = useTelemetry();
    this.initializeProviders();
  }

  private initializeProviders() {
    for (const providerConfig of this.config.providers) {
      try {
        const provider = AIProviderFactory.createProvider(providerConfig);
        this.providers.set(providerConfig.name, provider);
        
        this.telemetry.track('ai_provider_initialized', {
          provider: providerConfig.name,
          capabilities: provider.getCapabilities()
        });
      } catch (error) {
        console.error(`Failed to initialize provider ${providerConfig.name}:`, error);
        
        this.telemetry.track('ai_provider_init_error', {
          provider: providerConfig.name,
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }
  }

  async sendMessage(
    messages: AIMessage[],
    sessionId?: string,
    conversationId?: string,
    options: SendMessageOptions = {}
  ): Promise<AIProviderResponse> {
    const providerName = options.provider || this.config.defaultProvider;
    const provider = this.providers.get(providerName);

    if (!provider) {
      throw new Error(`Provider ${providerName} not found or not initialized`);
    }

    const request: AIProviderRequest = {
      messages,
      sessionId,
      conversationId,
      stream: false,
      temperature: options.temperature,
      maxTokens: options.maxTokens,
      model: options.model
    };

    const startTime = Date.now();

    try {
      const response = await this.executeWithTimeout(
        () => provider.sendMessage(request),
        this.config.timeout || 30000
      );

      this.telemetry.track('ai_client_message_sent', {
        provider: providerName,
        messageCount: messages.length,
        latencyMs: Date.now() - startTime,
        success: true
      });

      return response;
    } catch (error) {
      this.telemetry.track('ai_client_message_error', {
        provider: providerName,
        error: error instanceof Error ? error.message : 'Unknown error',
        latencyMs: Date.now() - startTime
      });

      // Try fallback providers if configured
      if (this.config.fallbackProviders && this.config.fallbackProviders.length > 0) {
        return this.tryFallbackProviders(request, error as Error);
      }

      throw error;
    }
  }

  async streamMessage(
    messages: AIMessage[],
    sessionId?: string,
    conversationId?: string,
    options: SendMessageOptions = {}
  ): Promise<void> {
    const providerName = options.provider || this.config.defaultProvider;
    const provider = this.providers.get(providerName);

    if (!provider) {
      throw new Error(`Provider ${providerName} not found or not initialized`);
    }

    const capabilities = provider.getCapabilities();
    if (!capabilities.streaming) {
      throw new Error(`Provider ${providerName} does not support streaming`);
    }

    const request: AIProviderRequest = {
      messages,
      sessionId,
      conversationId,
      stream: true,
      temperature: options.temperature,
      maxTokens: options.maxTokens,
      model: options.model
    };

    const startTime = Date.now();

    try {
      await provider.streamMessage(
        request,
        (chunk) => {
          options.onChunk?.(chunk);
          
          if (chunk.done) {
            this.telemetry.track('ai_client_stream_completed', {
              provider: providerName,
              messageCount: messages.length,
              latencyMs: Date.now() - startTime
            });
          }
        },
        (error) => {
          this.telemetry.track('ai_client_stream_error', {
            provider: providerName,
            error: error.message,
            latencyMs: Date.now() - startTime
          });
          options.onError?.(error);
        },
        options.signal
      );
    } catch (error) {
      this.telemetry.track('ai_client_stream_error', {
        provider: providerName,
        error: error instanceof Error ? error.message : 'Unknown error',
        latencyMs: Date.now() - startTime
      });

      throw error;
    }
  }

  private async tryFallbackProviders(
    request: AIProviderRequest,
    originalError: Error
  ): Promise<AIProviderResponse> {
    if (!this.config.fallbackProviders) {
      throw originalError;
    }

    for (const fallbackProviderName of this.config.fallbackProviders) {
      const fallbackProvider = this.providers.get(fallbackProviderName);
      
      if (!fallbackProvider) {
        continue;
      }

      try {
        this.telemetry.track('ai_client_fallback_attempt', {
          originalProvider: this.config.defaultProvider,
          fallbackProvider: fallbackProviderName,
          originalError: originalError.message
        });

        const response = await this.executeWithTimeout(
          () => fallbackProvider.sendMessage(request),
          this.config.timeout || 30000
        );

        this.telemetry.track('ai_client_fallback_success', {
          fallbackProvider: fallbackProviderName
        });

        return response;
      } catch (fallbackError) {
        this.telemetry.track('ai_client_fallback_error', {
          fallbackProvider: fallbackProviderName,
          error: fallbackError instanceof Error ? fallbackError.message : 'Unknown error'
        });
        
        continue;
      }
    }

    // If all fallbacks failed, throw the original error
    throw originalError;
  }

  private async executeWithTimeout<T>(
    operation: () => Promise<T>,
    timeoutMs: number
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`Operation timed out after ${timeoutMs}ms`));
      }, timeoutMs);

      operation()
        .then(resolve)
        .catch(reject)
        .finally(() => clearTimeout(timeout));
    });
  }

  getProviderCapabilities(providerName?: string): any {
    const name = providerName || this.config.defaultProvider;
    const provider = this.providers.get(name);
    return provider?.getCapabilities() || null;
  }

  getAvailableProviders(): string[] {
    return Array.from(this.providers.keys());
  }

  isProviderAvailable(providerName: string): boolean {
    return this.providers.has(providerName);
  }

  updateProviderConfig(providerName: string, config: Partial<AIProviderConfig>) {
    const provider = this.providers.get(providerName);
    if (provider) {
      // Update the provider's config
      Object.assign((provider as any).config, config);
      
      this.telemetry.track('ai_provider_config_updated', {
        provider: providerName,
        updatedFields: Object.keys(config)
      });
    }
  }

  addProvider(config: AIProviderConfig) {
    try {
      const provider = AIProviderFactory.createProvider(config);
      this.providers.set(config.name, provider);
      
      this.telemetry.track('ai_provider_added', {
        provider: config.name,
        capabilities: provider.getCapabilities()
      });
    } catch (error) {
      this.telemetry.track('ai_provider_add_error', {
        provider: config.name,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  removeProvider(providerName: string) {
    const removed = this.providers.delete(providerName);
    
    if (removed) {
      this.telemetry.track('ai_provider_removed', {
        provider: providerName
      });
    }
    
    return removed;
  }
}

// Singleton instance for global use
let aiClientInstance: AIClient | null = null;

export const createAIClient = (config: AIClientConfig): AIClient => {
  aiClientInstance = new AIClient(config);
  return aiClientInstance;
};

export const getAIClient = (): AIClient => {
  if (!aiClientInstance) {
    throw new Error('AI Client not initialized. Call createAIClient first.');
  }
  return aiClientInstance;
};

export default AIClient;