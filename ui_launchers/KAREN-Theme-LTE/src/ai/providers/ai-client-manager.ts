/**
 * AI Client Manager
 * Handles provider selection, failover, and load balancing
 */

import { z } from 'zod';
import { 
  getEnabledProviders, 
  getProvidersByFeature, 
  providerRegistry, 
  ALL_PROVIDERS,
  type AIProviderConfig,
  type ProviderStatus 
} from './provider-registry';

// Request/Response types
export interface AIRequest {
  messages: Array<{
    role: 'user' | 'assistant' | 'system';
    content: string;
  }>;
  tools?: any[];
  temperature?: number;
  maxTokens?: number;
  stream?: boolean;
  userId?: string;
  sessionId?: string;
  metadata?: Record<string, any>;
}

export interface AIResponse {
  content: string;
  role: 'assistant';
  toolCalls?: any[];
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  model: string;
  provider: string;
  responseTime?: number;
  cached?: boolean;
}

export interface AIStreamChunk {
  content?: string;
  delta?: string;
  toolCalls?: any[];
  done?: boolean;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

// Cache interface
export interface CacheEntry {
  key: string;
  response: AIResponse;
  timestamp: Date;
  ttl: number;
  provider: string;
}

// Rate limiting interface
export interface RateLimitInfo {
  requestsRemaining: number;
  resetTime: Date;
  limit: number;
  window: 'minute' | 'hour' | 'day';
}

// Error types
export class AIProviderError extends Error {
  constructor(
    message: string,
    public providerId: string,
    public statusCode?: number,
    public retryable: boolean = true
  ) {
    super(message);
    this.name = 'AIProviderError';
  }
}

export class AIRateLimitError extends AIProviderError {
  constructor(
    message: string,
    providerId: string,
    public resetTime?: Date,
    public limitInfo?: RateLimitInfo
  ) {
    super(message, providerId, 429, false);
    this.name = 'AIRateLimitError';
  }
}

// Client manager class
export class AIClientManager {
  public cache: Map<string, CacheEntry> = new Map();
  public rateLimits: Map<string, RateLimitInfo> = new Map();
  public requestCounts: Map<string, number[]> = new Map();
  
  constructor() {
    // Clean up expired cache entries every 5 minutes
    setInterval(() => this.cleanupCache(), 5 * 60 * 1000);
    // Clean up old request counts every hour
    setInterval(() => this.cleanupRequestCounts(), 60 * 60 * 1000);
  }
  
  // Main completion method with automatic provider selection and failover
  async complete(request: AIRequest): Promise<AIResponse> {
    const cacheKey = this.getCacheKey(request);
    
    // Check cache first
    const cached = this.getFromCache(cacheKey);
    if (cached) {
      return { ...cached.response, cached: true };
    }
    
    // Get providers that support required features
    const requiredFeatures = this.getRequiredFeatures(request);
    let providers = requiredFeatures.length > 0 
      ? getProvidersByFeature(requiredFeatures[0] as keyof AIProviderConfig['features'])
      : getEnabledProviders();
    
    // Filter by healthy providers
    providers = providers.filter(provider => {
      const status = providerRegistry.getAllStatus().find(s => s.id === provider.id);
      return status?.healthy !== false;
    });
    
    if (providers.length === 0) {
      throw new Error('No healthy AI providers available');
    }
    
    // Try providers in order of priority
    let lastError: Error | null = null;
    
    for (const provider of providers) {
      try {
        // Check rate limits
        if (this.isRateLimited(provider.id)) {
          console.warn(`Provider ${provider.id} is rate limited, trying next...`);
          continue;
        }
        
        // Make request
        const response = await this.makeRequest(provider, request);
        
        // Mark provider as healthy
        providerRegistry.markHealthy(provider.id, response.responseTime);
        
        // Cache response
        this.setCache(cacheKey, response, provider.id);
        
        // Update request counts
        this.updateRequestCount(provider.id);
        
        return {
          ...response,
          provider: provider.id,
          cached: false,
        };
      } catch (error) {
        lastError = error as Error;
        console.error(`Provider ${provider.id} failed:`, error);
        
        // Mark provider as unhealthy if it's a retryable error
        if (error instanceof AIProviderError && error.retryable) {
          providerRegistry.markUnhealthy(provider.id, error.message);
        }
        
        // If it's a rate limit error, update rate limit info
        if (error instanceof AIRateLimitError) {
          this.updateRateLimit(provider.id, error.limitInfo);
        }
        
        // Continue to next provider
        continue;
      }
    }
    
    // All providers failed
    throw lastError || new Error('All AI providers failed');
  }
  
  // Streaming completion method
  async *completeStream(request: AIRequest): AsyncGenerator<AIStreamChunk> {
    const providers = getEnabledProviders().filter(provider => 
      provider.features.streaming && provider.enabled
    );
    
    if (providers.length === 0) {
      throw new Error('No streaming providers available');
    }
    
    // Try providers in order of priority
    for (const provider of providers) {
      try {
        if (this.isRateLimited(provider.id)) {
          continue;
        }
        
        for await (const chunk of this.makeStreamRequest(provider, request)) {
          yield chunk;
        }
        
        providerRegistry.markHealthy(provider.id);
        this.updateRequestCount(provider.id);
        return;
      } catch (error) {
        console.error(`Streaming provider ${provider.id} failed:`, error);
        
        if (error instanceof AIProviderError && error.retryable) {
          providerRegistry.markUnhealthy(provider.id, error.message);
        }
        
        continue;
      }
    }
    
    throw new Error('All streaming providers failed');
  }
  
  // Make request to specific provider
  private async makeRequest(provider: AIProviderConfig, request: AIRequest): Promise<AIResponse> {
    const startTime = Date.now();
    
    switch (provider.id) {
      case 'openai_gpt4':
      case 'openai_gpt35':
        return this.makeOpenAIRequest(provider, request);
      
      case 'anthropic_claude3':
        return this.makeAnthropicRequest(provider, request);
      
      case 'google_gemini':
        return this.makeGoogleRequest(provider, request);
      
      case 'aws_bedrock':
        return this.makeAWSRequest(provider, request);
      
      case 'azure_openai':
        return this.makeAzureRequest(provider, request);
      
      case 'cohere':
        return this.makeCohereRequest(provider, request);
      
      case 'zhipuai':
        return this.makeZhipuRequest(provider, request);
      
      case 'mistral':
        return this.makeMistralRequest(provider, request);
      
      case 'perplexity':
        return this.makePerplexityRequest(provider, request);
      
      case 'groq':
        return this.makeGroqRequest(provider, request);
      
      case 'replicate':
        return this.makeReplicateRequest(provider, request);
      
      case 'ollama':
      case 'lmstudio':
      case 'localai':
      case 'gpt4all':
        return this.makeLocalRequest(provider, request);
      
      default:
        throw new Error(`Unknown provider: ${provider.id}`);
    }
  }
  
  // Make streaming request to specific provider
  private async *makeStreamRequest(provider: AIProviderConfig, request: AIRequest): AsyncGenerator<AIStreamChunk> {
    switch (provider.id) {
      case 'openai_gpt4':
      case 'openai_gpt35':
        yield* this.makeOpenAIStream(provider, request);
        break;
      
      case 'anthropic_claude3':
        yield* this.makeAnthropicStream(provider, request);
        break;
      
      case 'google_gemini':
        yield* this.makeGoogleStream(provider, request);
        break;
      
      case 'ollama':
      case 'lmstudio':
      case 'localai':
        yield* this.makeLocalStream(provider, request);
        break;
      
      default:
        throw new Error(`Streaming not supported for provider: ${provider.id}`);
    }
  }
  
  // Provider-specific implementations (simplified for brevity)
  private async makeOpenAIRequest(provider: AIProviderConfig, request: AIRequest): Promise<AIResponse> {
    const response = await fetch(`${provider.endpoint}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${provider.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: provider.model,
        messages: request.messages,
        temperature: request.temperature || provider.temperature,
        max_tokens: request.maxTokens || provider.maxTokens,
        stream: false,
        tools: request.tools,
      }),
    });
    
    if (!response.ok) {
      if (response.status === 429) {
        throw new AIRateLimitError('OpenAI rate limit exceeded', provider.id);
      }
      throw new AIProviderError(`OpenAI API error: ${response.statusText}`, provider.id, response.status);
    }
    
    const data = await response.json();
    const choice = data.choices[0];
    
    return {
      content: choice.message.content,
      role: 'assistant',
      toolCalls: choice.message.tool_calls,
      usage: data.usage,
      model: data.model,
      provider: provider.id,
    };
  }
  
  private async makeAnthropicRequest(provider: AIProviderConfig, request: AIRequest): Promise<AIResponse> {
    const response = await fetch(`${provider.endpoint}/messages`, {
      method: 'POST',
      headers: {
        'x-api-key': provider.apiKey!,
        'Content-Type': 'application/json',
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: provider.model,
        messages: request.messages,
        max_tokens: request.maxTokens || provider.maxTokens,
        temperature: request.temperature || provider.temperature,
        tools: request.tools,
      }),
    });
    
    if (!response.ok) {
      if (response.status === 429) {
        throw new AIRateLimitError('Anthropic rate limit exceeded', provider.id);
      }
      throw new AIProviderError(`Anthropic API error: ${response.statusText}`, provider.id, response.status);
    }
    
    const data = await response.json();
    const content = data.content[0];
    
    return {
      content: content.text,
      role: 'assistant',
      toolCalls: content.tool_calls?.map((tc: any) => ({
        id: tc.id,
        type: tc.type,
        function: tc.function,
      })),
      usage: data.usage,
      model: data.model,
      provider: provider.id,
    };
  }
  
  private async makeGoogleRequest(provider: AIProviderConfig, request: AIRequest): Promise<AIResponse> {
    // Implementation for Google Gemini
    const response = await fetch(`${provider.endpoint}/models/${provider.model}:generateContent`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${provider.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        contents: request.messages.map(msg => ({
          role: msg.role === 'assistant' ? 'model' : msg.role,
          parts: [{ text: msg.content }],
        })),
        generationConfig: {
          temperature: request.temperature || provider.temperature,
          maxOutputTokens: request.maxTokens || provider.maxTokens,
        },
        tools: request.tools,
      }),
    });
    
    if (!response.ok) {
      if (response.status === 429) {
        throw new AIRateLimitError('Google rate limit exceeded', provider.id);
      }
      throw new AIProviderError(`Google API error: ${response.statusText}`, provider.id, response.status);
    }
    
    const data = await response.json();
    const candidate = data.candidates[0];
    
    return {
      content: candidate.content.parts[0].text,
      role: 'assistant',
      usage: data.usageMetadata,
      model: provider.model,
      provider: provider.id,
    };
  }
  
  // Placeholder implementations for other providers
  private async makeAWSRequest(provider: AIProviderConfig, request: AIRequest): Promise<AIResponse> {
    throw new Error('AWS provider not implemented yet');
  }
  
  private async makeAzureRequest(provider: AIProviderConfig, request: AIRequest): Promise<AIResponse> {
    throw new Error('Azure provider not implemented yet');
  }
  
  private async makeCohereRequest(provider: AIProviderConfig, request: AIRequest): Promise<AIResponse> {
    throw new Error('Cohere provider not implemented yet');
  }
  
  private async makeZhipuRequest(provider: AIProviderConfig, request: AIRequest): Promise<AIResponse> {
    throw new Error('Zhipu provider not implemented yet');
  }
  
  private async makeMistralRequest(provider: AIProviderConfig, request: AIRequest): Promise<AIResponse> {
    throw new Error('Mistral provider not implemented yet');
  }
  
  private async makePerplexityRequest(provider: AIProviderConfig, request: AIRequest): Promise<AIResponse> {
    throw new Error('Perplexity provider not implemented yet');
  }
  
  private async makeGroqRequest(provider: AIProviderConfig, request: AIRequest): Promise<AIResponse> {
    throw new Error('Groq provider not implemented yet');
  }
  
  private async makeReplicateRequest(provider: AIProviderConfig, request: AIRequest): Promise<AIResponse> {
    throw new Error('Replicate provider not implemented yet');
  }
  
  private async makeLocalRequest(provider: AIProviderConfig, request: AIRequest): Promise<AIResponse> {
    const response = await fetch(`${provider.endpoint}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: provider.model,
        messages: request.messages,
        temperature: request.temperature || provider.temperature,
        max_tokens: request.maxTokens || provider.maxTokens,
        stream: false,
      }),
    });
    
    if (!response.ok) {
      throw new AIProviderError(`Local provider error: ${response.statusText}`, provider.id, response.status);
    }
    
    const data = await response.json();
    const choice = data.choices[0];
    
    return {
      content: choice.message.content,
      role: 'assistant',
      usage: data.usage,
      model: provider.model,
      provider: provider.id,
    };
  }
  
  // Streaming implementations
  private async *makeOpenAIStream(provider: AIProviderConfig, request: AIRequest): AsyncGenerator<AIStreamChunk> {
    const response = await fetch(`${provider.endpoint}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${provider.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: provider.model,
        messages: request.messages,
        temperature: request.temperature || provider.temperature,
        max_tokens: request.maxTokens || provider.maxTokens,
        stream: true,
        tools: request.tools,
      }),
    });
    
    if (!response.ok) {
      throw new AIProviderError(`OpenAI streaming error: ${response.statusText}`, provider.id, response.status);
    }
    
    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body reader');
    
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            yield { done: true };
            return;
          }
          
          try {
            const parsed = JSON.parse(data);
            const delta = parsed.choices[0]?.delta;
            
            if (delta?.content) {
              yield { content: delta.content };
            }
            
            if (delta?.tool_calls) {
              yield { toolCalls: delta.tool_calls };
            }
            
            if (parsed.usage) {
              yield { usage: parsed.usage, done: true };
            }
          } catch (e) {
            // Ignore parsing errors
          }
        }
      }
    }
  }
  
  private async *makeAnthropicStream(provider: AIProviderConfig, request: AIRequest): AsyncGenerator<AIStreamChunk> {
    // Implementation for Anthropic streaming
    throw new Error('Anthropic streaming not implemented yet');
  }
  
  private async *makeGoogleStream(provider: AIProviderConfig, request: AIRequest): AsyncGenerator<AIStreamChunk> {
    // Implementation for Google streaming
    throw new Error('Google streaming not implemented yet');
  }
  
  private async *makeLocalStream(provider: AIProviderConfig, request: AIRequest): AsyncGenerator<AIStreamChunk> {
    // Implementation for local provider streaming
    throw new Error('Local streaming not implemented yet');
  }
  
  // Utility methods
  private getRequiredFeatures(request: AIRequest): Array<keyof AIProviderConfig['features']> {
    const features: Array<keyof AIProviderConfig['features']> = [];
    
    if (request.stream) features.push('streaming');
    if (request.tools && request.tools.length > 0) features.push('functionCalling');
    
    return features;
  }
  
  private getCacheKey(request: AIRequest): string {
    const key = {
      messages: request.messages,
      temperature: request.temperature,
      maxTokens: request.maxTokens,
      tools: request.tools,
    };
    return btoa(JSON.stringify(key));
  }
  
  private getFromCache(key: string): CacheEntry | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    if (Date.now() - entry.timestamp.getTime() > entry.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return entry;
  }
  
  private setCache(key: string, response: AIResponse, providerId: string, ttl: number = 5 * 60 * 1000): void {
    this.cache.set(key, {
      key,
      response,
      timestamp: new Date(),
      ttl,
      provider: providerId,
    });
  }
  
  public cleanupCache(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp.getTime() > entry.ttl) {
        this.cache.delete(key);
      }
    }
  }
  
  public isRateLimited(providerId: string): boolean {
    const limit = this.rateLimits.get(providerId);
    if (!limit) return false;
    
    return Date.now() < limit.resetTime.getTime() && limit.requestsRemaining <= 0;
  }
  
  public updateRateLimit(providerId: string, info?: RateLimitInfo): void {
    if (info) {
      this.rateLimits.set(providerId, info);
    }
  }
  
  public updateRequestCount(providerId: string): void {
    const now = Date.now();
    const counts = this.requestCounts.get(providerId) || [];
    counts.push(now);
    
    // Keep only requests from the last hour
    const oneHourAgo = now - 60 * 60 * 1000;
    const recent = counts.filter(timestamp => timestamp > oneHourAgo);
    
    this.requestCounts.set(providerId, recent);
  }
  
  public cleanupRequestCounts(): void {
    const now = Date.now();
    const oneHourAgo = now - 60 * 60 * 1000;
    
    for (const [providerId, counts] of this.requestCounts.entries()) {
      const recent = counts.filter(timestamp => timestamp > oneHourAgo);
      this.requestCounts.set(providerId, recent);
    }
  }
}

// Global client manager instance
const aiClientManagerInstance = new AIClientManager();

// Export functions instead of instance for Next.js compatibility
export const aiClientManager = {
  complete: (request: AIRequest) => aiClientManagerInstance.complete(request),
  completeStream: (request: AIRequest) => aiClientManagerInstance.completeStream(request),
  isRateLimited: (providerId: string) => aiClientManagerInstance.isRateLimited(providerId),
  updateRateLimit: (providerId: string, info?: RateLimitInfo) => aiClientManagerInstance.updateRateLimit(providerId, info),
  updateRequestCount: (providerId: string) => aiClientManagerInstance.updateRequestCount(providerId),
  cleanupCache: () => aiClientManagerInstance.cleanupCache(),
  cleanupRequestCounts: () => aiClientManagerInstance.cleanupRequestCounts(),
};