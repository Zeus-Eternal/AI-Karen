/**
 * AI Provider Registry
 * Manages multiple AI providers with fallback and load balancing
 */

import { z } from 'zod';

// Provider configuration types
export interface AIProviderConfig {
  id: string;
  name: string;
  type: 'cloud' | 'local';
  apiKey?: string;
  endpoint?: string;
  model: string;
  maxTokens?: number;
  temperature?: number;
  enabled: boolean;
  priority: number; // Lower number = higher priority
  rateLimit?: {
    requestsPerMinute: number;
    requestsPerHour: number;
    requestsPerDay: number;
  };
  features: {
    streaming: boolean;
    functionCalling: boolean;
    vision: boolean;
    embedding: boolean;
    fineTuning: boolean;
  };
}

// Cloud provider configurations
export const CLOUD_PROVIDERS: Record<string, Omit<AIProviderConfig, 'type'>> = {
  // OpenAI GPT-4
  openai_gpt4: {
    id: 'openai_gpt4',
    name: 'OpenAI GPT-4',
    apiKey: process.env.OPENAI_API_KEY,
    endpoint: 'https://api.openai.com/v1',
    model: 'gpt-4-turbo-preview',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: !!process.env.OPENAI_API_KEY,
    priority: 1,
    rateLimit: {
      requestsPerMinute: 3500,
      requestsPerHour: 9000,
      requestsPerDay: 10000,
    },
    features: {
      streaming: true,
      functionCalling: true,
      vision: true,
      embedding: true,
      fineTuning: true,
    },
  },
  
  // OpenAI GPT-3.5
  openai_gpt35: {
    id: 'openai_gpt35',
    name: 'OpenAI GPT-3.5 Turbo',
    apiKey: process.env.OPENAI_API_KEY,
    endpoint: 'https://api.openai.com/v1',
    model: 'gpt-3.5-turbo',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: !!process.env.OPENAI_API_KEY,
    priority: 2,
    rateLimit: {
      requestsPerMinute: 3500,
      requestsPerHour: 9000,
      requestsPerDay: 10000,
    },
    features: {
      streaming: true,
      functionCalling: true,
      vision: false,
      embedding: true,
      fineTuning: true,
    },
  },
  
  // Anthropic Claude 3
  anthropic_claude3: {
    id: 'anthropic_claude3',
    name: 'Anthropic Claude 3 Opus',
    apiKey: process.env.ANTHROPIC_API_KEY,
    endpoint: 'https://api.anthropic.com/v1',
    model: 'claude-3-opus-20240229',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: !!process.env.ANTHROPIC_API_KEY,
    priority: 1,
    rateLimit: {
      requestsPerMinute: 1000,
      requestsPerHour: 5000,
      requestsPerDay: 10000,
    },
    features: {
      streaming: true,
      functionCalling: true,
      vision: true,
      embedding: false,
      fineTuning: false,
    },
  },
  
  // Google Gemini Pro
  google_gemini: {
    id: 'google_gemini',
    name: 'Google Gemini Pro',
    apiKey: process.env.GOOGLE_AI_API_KEY,
    endpoint: 'https://generativelanguage.googleapis.com/v1',
    model: 'gemini-pro',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: !!process.env.GOOGLE_AI_API_KEY,
    priority: 2,
    rateLimit: {
      requestsPerMinute: 60,
      requestsPerHour: 1000,
      requestsPerDay: 1500,
    },
    features: {
      streaming: true,
      functionCalling: true,
      vision: true,
      embedding: true,
      fineTuning: false,
    },
  },
  
  // AWS Bedrock
  aws_bedrock: {
    id: 'aws_bedrock',
    name: 'AWS Bedrock Claude',
    apiKey: process.env.AWS_ACCESS_KEY_ID,
    endpoint: 'https://bedrock-runtime.us-east-1.amazonaws.com',
    model: 'anthropic.claude-3-sonnet-20240229-v1:0',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: !!(process.env.AWS_ACCESS_KEY_ID && process.env.AWS_SECRET_ACCESS_KEY),
    priority: 2,
    rateLimit: {
      requestsPerMinute: 1000,
      requestsPerHour: 10000,
      requestsPerDay: 50000,
    },
    features: {
      streaming: true,
      functionCalling: true,
      vision: true,
      embedding: true,
      fineTuning: false,
    },
  },
  
  // Azure OpenAI
  azure_openai: {
    id: 'azure_openai',
    name: 'Azure OpenAI GPT-4',
    apiKey: process.env.AZURE_OPENAI_API_KEY,
    endpoint: process.env.AZURE_OPENAI_ENDPOINT,
    model: 'gpt-4',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: !!(process.env.AZURE_OPENAI_API_KEY && process.env.AZURE_OPENAI_ENDPOINT),
    priority: 2,
    rateLimit: {
      requestsPerMinute: 300,
      requestsPerHour: 3000,
      requestsPerDay: 30000,
    },
    features: {
      streaming: true,
      functionCalling: true,
      vision: true,
      embedding: true,
      fineTuning: true,
    },
  },
  
  // Cohere
  cohere: {
    id: 'cohere',
    name: 'Cohere Command',
    apiKey: process.env.COHERE_API_KEY,
    endpoint: 'https://api.cohere.ai/v1',
    model: 'command',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: !!process.env.COHERE_API_KEY,
    priority: 3,
    rateLimit: {
      requestsPerMinute: 1000,
      requestsPerHour: 10000,
      requestsPerDay: 1000,
    },
    features: {
      streaming: true,
      functionCalling: false,
      vision: false,
      embedding: true,
      fineTuning: true,
    },
  },
  
  // z.ai
  zhipuai: {
    id: 'zhipuai',
    name: 'Zhipu AI GLM',
    apiKey: process.env.ZHIPUAI_API_KEY,
    endpoint: 'https://open.bigmodel.cn/api/paas/v4',
    model: 'glm-4',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: !!process.env.ZHIPUAI_API_KEY,
    priority: 3,
    rateLimit: {
      requestsPerMinute: 1000,
      requestsPerHour: 10000,
      requestsPerDay: 50000,
    },
    features: {
      streaming: true,
      functionCalling: true,
      vision: true,
      embedding: true,
      fineTuning: false,
    },
  },
  
  // Mistral AI
  mistral: {
    id: 'mistral',
    name: 'Mistral Large',
    apiKey: process.env.MISTRAL_API_KEY,
    endpoint: 'https://api.mistral.ai/v1',
    model: 'mistral-large-latest',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: !!process.env.MISTRAL_API_KEY,
    priority: 3,
    rateLimit: {
      requestsPerMinute: 1000,
      requestsPerHour: 10000,
      requestsPerDay: 10000,
    },
    features: {
      streaming: true,
      functionCalling: true,
      vision: false,
      embedding: true,
      fineTuning: true,
    },
  },
  
  // Perplexity
  perplexity: {
    id: 'perplexity',
    name: 'Perplexity',
    apiKey: process.env.PERPLEXITY_API_KEY,
    endpoint: 'https://api.perplexity.ai',
    model: 'llama-3-70b-instruct',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: !!process.env.PERPLEXITY_API_KEY,
    priority: 3,
    rateLimit: {
      requestsPerMinute: 1000,
      requestsPerHour: 10000,
      requestsPerDay: 10000,
    },
    features: {
      streaming: true,
      functionCalling: false,
      vision: false,
      embedding: false,
      fineTuning: false,
    },
  },
  
  // Groq
  groq: {
    id: 'groq',
    name: 'Groq Llama',
    apiKey: process.env.GROQ_API_KEY,
    endpoint: 'https://api.groq.com/openai/v1',
    model: 'llama3-70b-8192',
    maxTokens: 8192,
    temperature: 0.7,
    enabled: !!process.env.GROQ_API_KEY,
    priority: 2,
    rateLimit: {
      requestsPerMinute: 1000,
      requestsPerHour: 10000,
      requestsPerDay: 10000,
    },
    features: {
      streaming: true,
      functionCalling: true,
      vision: false,
      embedding: false,
      fineTuning: false,
    },
  },
  
  // Replicate
  replicate: {
    id: 'replicate',
    name: 'Replicate Llama',
    apiKey: process.env.REPLICATE_API_KEY,
    endpoint: 'https://api.replicate.com/v1',
    model: 'meta/meta-llama-3-70b-instruct',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: !!process.env.REPLICATE_API_KEY,
    priority: 3,
    rateLimit: {
      requestsPerMinute: 1000,
      requestsPerHour: 10000,
      requestsPerDay: 10000,
    },
    features: {
      streaming: false,
      functionCalling: false,
      vision: false,
      embedding: false,
      fineTuning: false,
    },
  },
};

// Local provider configurations
export const LOCAL_PROVIDERS: Record<string, Omit<AIProviderConfig, 'type'>> = {
  // Ollama
  ollama: {
    id: 'ollama',
    name: 'Ollama Local',
    endpoint: process.env.OLLAMA_ENDPOINT || 'http://localhost:11434',
    model: process.env.OLLAMA_MODEL || 'llama3',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: true,
    priority: 4,
    features: {
      streaming: true,
      functionCalling: false,
      vision: true,
      embedding: false,
      fineTuning: false,
    },
  },
  
  // LM Studio
  lmstudio: {
    id: 'lmstudio',
    name: 'LM Studio Local',
    endpoint: process.env.LMSTUDIO_ENDPOINT || 'http://localhost:1234',
    model: process.env.LMSTUDIO_MODEL || 'local-model',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: true,
    priority: 4,
    features: {
      streaming: true,
      functionCalling: false,
      vision: false,
      embedding: false,
      fineTuning: false,
    },
  },
  
  // LocalAI
  localai: {
    id: 'localai',
    name: 'LocalAI',
    endpoint: process.env.LOCALAI_ENDPOINT || 'http://localhost:8080',
    model: process.env.LOCALAI_MODEL || 'gpt-3.5-turbo',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: true,
    priority: 4,
    features: {
      streaming: true,
      functionCalling: true,
      vision: false,
      embedding: true,
      fineTuning: false,
    },
  },
  
  // GPT4All
  gpt4all: {
    id: 'gpt4all',
    name: 'GPT4All',
    endpoint: process.env.GPT4ALL_ENDPOINT || 'http://localhost:4891',
    model: process.env.GPT4ALL_MODEL || 'ggml-gpt4all-j',
    maxTokens: 4096,
    temperature: 0.7,
    enabled: true,
    priority: 5,
    features: {
      streaming: false,
      functionCalling: false,
      vision: false,
      embedding: false,
      fineTuning: false,
    },
  },
};

// Combined provider registry
export const ALL_PROVIDERS: Record<string, AIProviderConfig> = {
  ...Object.fromEntries(
    Object.entries(CLOUD_PROVIDERS).map(([key, config]) => [key, { ...config, type: 'cloud' as const }])
  ),
  ...Object.fromEntries(
    Object.entries(LOCAL_PROVIDERS).map(([key, config]) => [key, { ...config, type: 'local' as const }])
  ),
};

// Get enabled providers sorted by priority
export function getEnabledProviders(): AIProviderConfig[] {
  return Object.values(ALL_PROVIDERS)
    .filter(provider => provider.enabled)
    .sort((a, b) => a.priority - b.priority);
}

// Get provider by ID
export function getProviderById(id: string): AIProviderConfig | undefined {
  return ALL_PROVIDERS[id];
}

// Get providers that support specific features
export function getProvidersByFeature(feature: keyof AIProviderConfig['features']): AIProviderConfig[] {
  return getEnabledProviders().filter(provider => provider.features[feature]);
}

// Provider status tracking
export interface ProviderStatus {
  id: string;
  STATUS?: 'active' | 'inactive' | 'maintenance' | 'error';  // Added STATUS property for backwards compatibility
  status?: 'active' | 'inactive' | 'maintenance' | 'error';  // Added status property
  healthy: boolean;
  lastCheck: Date;
  responseTime?: number;
  errorCount: number;
  lastError?: string;
}

// Provider registry class
class ProviderRegistry {
  public status: Map<string, ProviderStatus> = new Map();
  
  public constructor() {
    // Initialize status for all enabled providers
    this.initializeStatus();
  }
  
  public initializeStatus(): void {
    // Initialize status for all enabled providers
    getEnabledProviders().forEach(provider => {
      this.status.set(provider.id, {
        id: provider.id,
        healthy: true,
        lastCheck: new Date(),
        errorCount: 0,
      });
    });
  }
  
  // Get current status of all providers
  public getAllStatus(): ProviderStatus[] {
    return Array.from(this.status.values());
  }
  
  // Get healthy providers sorted by priority
  public getHealthyProviders(): AIProviderConfig[] {
    return getEnabledProviders()
      .filter(provider => {
        const status = this.status.get(provider.id);
        return status?.healthy !== false;
      })
      .sort((a, b) => a.priority - b.priority);
  }
  
  // Update provider status
  public updateStatus(id: string, update: Partial<ProviderStatus>): void {
    const current = this.status.get(id);
    if (current) {
      this.status.set(id, {
        ...current,
        ...update,
        lastCheck: new Date(),
      });
    }
  }
  
  // Mark provider as unhealthy
  public markUnhealthy(id: string, error?: string): void {
    const current = this.status.get(id);
    if (current) {
      this.status.set(id, {
        ...current,
        healthy: false,
        lastCheck: new Date(),
        errorCount: current.errorCount + 1,
        lastError: error,
      });
    }
  }
  
  // Mark provider as healthy
  public markHealthy(id: string, responseTime?: number): void {
    const current = this.status.get(id);
    if (current) {
      this.status.set(id, {
        ...current,
        healthy: true,
        lastCheck: new Date(),
        responseTime,
      });
    }
  }
}

// Global provider registry instance
const providerRegistryInstance = new ProviderRegistry();

// Export functions instead of instance for Next.js compatibility
export const providerRegistry = {
  getAllStatus: () => providerRegistryInstance.getAllStatus(),
  getHealthyProviders: () => providerRegistryInstance.getHealthyProviders(),
  updateStatus: (id: string, update: Partial<ProviderStatus>) => providerRegistryInstance.updateStatus(id, update),
  markUnhealthy: (id: string, error?: string) => providerRegistryInstance.markUnhealthy(id, error),
  markHealthy: (id: string, responseTime?: number) => providerRegistryInstance.markHealthy(id, responseTime),
};
