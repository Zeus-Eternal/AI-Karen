/**
 * AI Karen Backend Integration Layer
 * Connects the web UI with existing AI Karen backend services
 */

import type {
  ChatMessage,
  KarenSettings,
  HandleUserMessageResult,
  AiData
} from './types';
import { webUIConfig, type WebUIConfig } from './config';
import { getPerformanceMonitor } from './performance-monitor';
import { getStoredApiKey } from './secure-api-key';

// Error handling types
interface WebUIErrorResponse {
  error: string;
  message: string;
  type: string;
  details?: Record<string, any>;
  request_id?: string;
  timestamp: string;
}

// Custom error class for structured error handling
class APIError extends Error {
  public status: number;
  public details?: WebUIErrorResponse;
  public isRetryable: boolean;

  constructor(
    message: string,
    status: number,
    details?: WebUIErrorResponse,
    isRetryable: boolean = false
  ) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.details = details;
    this.isRetryable = isRetryable;
  }

  static isRetryableStatus(status: number): boolean {
    return [408, 429, 500, 502, 503, 504].includes(status);
  }

  static fromResponse(response: Response, errorData?: any): APIError {
    const isRetryable = APIError.isRetryableStatus(response.status);
    return new APIError(
      `HTTP ${response.status}: ${response.statusText}`,
      response.status,
      errorData,
      isRetryable
    );
  }
}

// Backend service configuration
interface BackendConfig {
  baseUrl: string;
  apiKey?: string;
  timeout: number;
}

// Memory service types
interface MemoryEntry {
  id: string;
  content: string;
  metadata: Record<string, any>;
  timestamp: number;
  similarity_score?: number;
  tags: string[];
  user_id?: string;
  session_id?: string;
}

interface MemoryQuery {
  text: string;
  user_id?: string;
  session_id?: string;
  tags?: string[];
  metadata_filter?: Record<string, any>;
  time_range?: [Date, Date];
  top_k?: number;
  similarity_threshold?: number;
}

// Plugin service types
interface PluginInfo {
  name: string;
  description: string;
  category: string;
  enabled: boolean;
  version: string;
  parameters?: Record<string, any>;
}

interface PluginExecutionResult {
  success: boolean;
  result?: any;
  stdout?: string;
  stderr?: string;
  error?: string;
  plugin_name: string;
  timestamp: string;
}

// Analytics service types
interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_sessions: number;
  total_requests: number;
  error_rate: number;
  response_time_avg: number;
  uptime_hours: number;
  timestamp: string;
}

interface UsageAnalytics {
  total_interactions: number;
  unique_users: number;
  popular_features: Array<{
    name: string;
    usage_count: number;
  }>;
  peak_hours: number[];
  user_satisfaction: number;
  time_range: string;
  timestamp: string;
}

class KarenBackendService {
  private config: BackendConfig;
  private cache: Map<string, { data: any; timestamp: number; ttl: number }> = new Map();
  private debugLogging: boolean;
  private requestLogging: boolean;
  private performanceMonitoring: boolean;
  private logLevel: string;

  constructor(config: Partial<BackendConfig> = {}) {
    this.config = {
      baseUrl: config.baseUrl || webUIConfig.backendUrl,
      apiKey: config.apiKey || getStoredApiKey() || webUIConfig.apiKey,
      timeout: config.timeout || webUIConfig.apiTimeout,
    };

    // Initialize configuration from webUIConfig
    this.debugLogging = webUIConfig.debugLogging;
    this.requestLogging = webUIConfig.requestLogging;
    this.performanceMonitoring = webUIConfig.performanceMonitoring;
    this.logLevel = webUIConfig.logLevel;

    if (this.debugLogging) {
      console.log('KarenBackendService initialized with config:', {
        baseUrl: this.config.baseUrl,
        timeout: this.config.timeout,
        hasApiKey: !!this.config.apiKey,
        debugLogging: this.debugLogging,
        requestLogging: this.requestLogging,
        performanceMonitoring: this.performanceMonitoring,
        logLevel: this.logLevel,
      });
    }
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    useCache: boolean = false,
    cacheTtl: number = webUIConfig.cacheTtl,
    maxRetries: number = webUIConfig.maxRetries,
    retryDelay: number = webUIConfig.retryDelay
  ): Promise<T> {
    const url = `${this.config.baseUrl}${endpoint}`;
    const cacheKey = `${url}:${JSON.stringify(options)}`;

    // Check cache first
    if (useCache && this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey)!;
      if (Date.now() - cached.timestamp < cached.ttl) {
        return cached.data;
      }
      this.cache.delete(cacheKey);
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    let lastError: Error | null = null;

    // Log request if enabled
    if (this.requestLogging) {
      console.log(`[REQUEST] ${options.method || 'GET'} ${url}`, {
        headers: this.debugLogging ? headers : { 'Content-Type': headers['Content-Type'] },
        body: options.body ? JSON.parse(options.body as string) : undefined,
      });
    }

    const performanceStart = this.performanceMonitoring ? performance.now() : 0;

    // Retry logic for transient failures
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

        const response = await fetch(url, {
          ...options,
          headers,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          // Try to parse structured error response
          let errorDetails: WebUIErrorResponse | undefined;
          try {
            const errorData = await response.json();
            if (errorData && typeof errorData === 'object') {
              errorDetails = errorData as WebUIErrorResponse;
            }
          } catch {
            // If we can't parse the error response, create a basic one
            errorDetails = {
              error: response.statusText,
              message: `HTTP ${response.status}: ${response.statusText}`,
              type: 'HTTP_ERROR',
              timestamp: new Date().toISOString(),
            };
          }

          const apiError = APIError.fromResponse(response, errorDetails);

          // Don't retry non-retryable errors
          if (!apiError.isRetryable || attempt === maxRetries) {
            throw apiError;
          }

          lastError = apiError;
          console.warn(`Request failed (attempt ${attempt + 1}/${maxRetries + 1}):`, apiError.message);

          // Wait before retrying with exponential backoff
          await this.sleep(retryDelay * Math.pow(2, attempt));
          continue;
        }

        const data = await response.json();
        const responseTime = this.performanceMonitoring ? performance.now() - performanceStart : 0;

        // Record performance metrics
        if (this.performanceMonitoring) {
          const performanceMonitor = getPerformanceMonitor();
          performanceMonitor.recordRequest(
            endpoint,
            options.method || 'GET',
            performanceStart,
            performance.now(),
            response.status,
            JSON.stringify(data).length
          );

          if (responseTime > 5000) { // Log slow requests (>5s)
            console.warn(`[PERFORMANCE] Slow request detected: ${endpoint} took ${responseTime.toFixed(2)}ms`);
          }
        }

        // Log response if enabled
        if (this.requestLogging) {
          console.log(`[RESPONSE] ${response.status} ${options.method || 'GET'} ${url}`, {
            status: response.status,
            responseTime: this.performanceMonitoring ? `${responseTime.toFixed(2)}ms` : undefined,
            dataSize: JSON.stringify(data).length,
            cached: useCache,
          });
        }

        // Cache successful responses
        if (useCache) {
          this.cache.set(cacheKey, {
            data,
            timestamp: Date.now(),
            ttl: cacheTtl,
          });
        }

        return data;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));

        // Handle network errors and timeouts
        if (error instanceof Error) {
          if (error.name === 'AbortError') {
            lastError = new APIError('Request timeout', 408, {
              error: 'Request timeout',
              message: 'The request took too long to complete',
              type: 'TIMEOUT_ERROR',
              timestamp: new Date().toISOString(),
            }, true);
          } else if (error.message.includes('fetch')) {
            lastError = new APIError('Network error', 0, {
              error: 'Network error',
              message: 'Unable to connect to the backend service',
              type: 'NETWORK_ERROR',
              timestamp: new Date().toISOString(),
            }, true);
          }
        }

        // Don't retry if it's not a retryable error or we've exhausted retries
        if (!(lastError instanceof APIError && lastError.isRetryable) || attempt === maxRetries) {
          // Record performance metrics for failed requests
          if (this.performanceMonitoring && lastError instanceof APIError) {
            const performanceMonitor = getPerformanceMonitor();
            performanceMonitor.recordRequest(
              endpoint,
              options.method || 'GET',
              performanceStart,
              performance.now(),
              lastError.status,
              0,
              lastError.message
            );
          }

          console.error(`Backend request failed for ${endpoint} after ${attempt + 1} attempts:`, lastError);
          throw lastError;
        }

        console.warn(`Request failed (attempt ${attempt + 1}/${maxRetries + 1}):`, lastError.message);

        // Wait before retrying with exponential backoff
        await this.sleep(retryDelay * Math.pow(2, attempt));
      }
    }

    // This should never be reached, but just in case
    throw lastError || new Error('Unknown error occurred');
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Memory Service Integration
  async storeMemory(
    content: string,
    metadata: Record<string, any> = {},
    tags: string[] = [],
    userId?: string,
    sessionId?: string
  ): Promise<string | null> {
    try {
      const response = await this.makeRequest<{ memory_id: string }>('/api/memory/store', {
        method: 'POST',
        body: JSON.stringify({
          content,
          metadata,
          tags,
          user_id: userId,
          session_id: sessionId,
        }),
      });
      return response.memory_id;
    } catch (error) {
      if (error instanceof APIError) {
        if (error.details?.type === 'SERVICE_UNAVAILABLE') {
          console.warn('Memory service unavailable, memory not stored');
          return null;
        } else if (error.details?.type === 'VALIDATION_ERROR') {
          console.warn('Memory validation failed:', error.details);
          return null;
        }
      }
      console.error('Failed to store memory:', error);
      return null;
    }
  }

  async queryMemories(query: MemoryQuery): Promise<MemoryEntry[]> {
    try {
      const response = await this.makeRequest<{ memories: MemoryEntry[] }>('/api/memory/query', {
        method: 'POST',
        body: JSON.stringify(query),
      });
      return response.memories || [];
    } catch (error) {
      if (error instanceof APIError) {
        if (error.details?.type === 'MEMORY_ERROR') {
          console.warn('Memory service error:', error.details);
          return []; // Return empty array for graceful degradation
        } else if (error.details?.type === 'SERVICE_UNAVAILABLE') {
          console.warn('Memory service unavailable, using cache if available');
          // Try to return cached results or empty array
          return this.getCachedMemories(query) || [];
        }
      }

      console.error('Failed to query memories:', error);
      return [];
    }
  }

  private getCachedMemories(query: MemoryQuery): MemoryEntry[] | null {
    // Simple cache lookup for memory queries
    const cacheKey = `memory:${JSON.stringify(query)}`;
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data.memories || [];
    }
    return null;
  }

  async getMemoryStats(userId?: string): Promise<Record<string, any>> {
    try {
      const params = userId ? `?user_id=${encodeURIComponent(userId)}` : '';
      return await this.makeRequest<Record<string, any>>(`/api/memory/stats${params}`, {}, true);
    } catch (error) {
      if (error instanceof APIError) {
        if (error.details?.type === 'SERVICE_UNAVAILABLE') {
          console.warn('Memory service unavailable, returning empty stats');
          return { total_memories: 0, last_updated: new Date().toISOString() };
        }
      }
      console.error('Failed to get memory stats:', error);
      return {};
    }
  }

  // Plugin Service Integration
  async getAvailablePlugins(): Promise<PluginInfo[]> {
    try {
      const response = await this.makeRequest<{ plugins: PluginInfo[] }>('/api/plugins/list', {}, true);
      return response.plugins || [];
    } catch (error) {
      if (error instanceof APIError) {
        if (error.details?.type === 'SERVICE_UNAVAILABLE') {
          console.warn('Plugin service unavailable, returning cached plugins if available');
          // Try to return cached results or empty array
          const cached = this.cache.get('/api/plugins/list:{}');
          if (cached) {
            return cached.data.plugins || [];
          }
        }
      }
      console.error('Failed to get available plugins:', error);
      return [];
    }
  }

  async executePlugin(
    pluginName: string,
    parameters: Record<string, any> = {},
    userId?: string
  ): Promise<PluginExecutionResult> {
    try {
      return await this.makeRequest<PluginExecutionResult>('/api/plugins/execute', {
        method: 'POST',
        body: JSON.stringify({
          plugin_name: pluginName,
          parameters,
          user_id: userId,
        }),
      });
    } catch (error) {
      let errorMessage = 'Unknown error';

      if (error instanceof APIError) {
        if (error.details?.type === 'PLUGIN_ERROR') {
          errorMessage = error.details.message || 'Plugin execution failed';
        } else if (error.details?.type === 'SERVICE_UNAVAILABLE') {
          errorMessage = 'Plugin service is temporarily unavailable';
        } else if (error.details?.type === 'VALIDATION_ERROR') {
          errorMessage = 'Invalid plugin parameters';
        } else {
          errorMessage = error.message;
        }
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }

      console.error(`Failed to execute plugin ${pluginName}:`, error);
      return {
        success: false,
        error: errorMessage,
        plugin_name: pluginName,
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Analytics Service Integration
  async getSystemMetrics(): Promise<SystemMetrics> {
    try {
      return await this.makeRequest<SystemMetrics>('/api/analytics/system-metrics', {}, true, 60000); // 1 minute cache
    } catch (error) {
      console.error('Failed to get system metrics:', error);
      // Return mock data as fallback
      return {
        cpu_usage: 45.2,
        memory_usage: 68.5,
        disk_usage: 32.1,
        active_sessions: 12,
        total_requests: 1547,
        error_rate: 0.02,
        response_time_avg: 0.3,
        uptime_hours: 168.5,
        timestamp: new Date().toISOString(),
      };
    }
  }

  async getUsageAnalytics(timeRange: string = '24h'): Promise<UsageAnalytics> {
    try {
      return await this.makeRequest<UsageAnalytics>(`/api/analytics/usage?range=${timeRange}`, {}, true);
    } catch (error) {
      console.error('Failed to get usage analytics:', error);
      // Return mock data as fallback
      return {
        total_interactions: 234,
        unique_users: 18,
        popular_features: [
          { name: 'Chat', usage_count: 156 },
          { name: 'Memory', usage_count: 89 },
          { name: 'Plugins', usage_count: 67 },
        ],
        peak_hours: [9, 14, 16, 20],
        user_satisfaction: 4.2,
        time_range: timeRange,
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Health Check
  async healthCheck(): Promise<{
    status: 'healthy' | 'degraded' | 'error';
    services: Record<string, any>;
    timestamp: string;
  }> {
    try {
      return await this.makeRequest('/api/health', {}, false);
    } catch (error) {
      console.error('Health check failed:', error);
      return {
        status: 'error',
        services: {
          backend: { status: 'error', error: error instanceof Error ? error.message : 'Unknown error' },
        },
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Enhanced Chat Integration with Memory
  async processUserMessage(
    message: string,
    conversationHistory: ChatMessage[],
    settings: KarenSettings,
    userId?: string,
    sessionId?: string
  ): Promise<HandleUserMessageResult> {
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      // Log request for debugging
      console.log(`[${requestId}] Processing user message:`, {
        message: message.substring(0, 100) + (message.length > 100 ? '...' : ''),
        userId,
        sessionId,
        historyLength: conversationHistory.length,
      });

      // First, query relevant memories
      const relevantMemories = await this.queryMemories({
        text: message,
        user_id: userId,
        session_id: sessionId,
        top_k: 5,
        similarity_threshold: 0.7,
      });

      // Prepare context for AI processing using the compatibility layer format
      const context = {
        message,
        conversation_history: conversationHistory.map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp.toISOString(),
        })),
        relevant_memories: relevantMemories.map(mem => ({
          content: mem.content,
          similarity_score: mem.similarity_score,
          tags: mem.tags,
        })),
        user_settings: settings,
        user_id: userId,
        session_id: sessionId,
      };

      // Use the compatibility layer endpoint
      const startTime = Date.now();
      const response = await this.makeRequest<HandleUserMessageResult>('/api/chat/process', {
        method: 'POST',
        body: JSON.stringify(context),
      });
      const responseTime = Date.now() - startTime;

      // Log successful response for debugging
      console.log(`[${requestId}] Chat processing successful:`, {
        responseTime: `${responseTime}ms`,
        responseLength: response.finalResponse?.length || 0,
        hasAiData: !!response.aiDataForFinalResponse,
        hasSuggestions: !!response.suggestedNewFacts,
        hasProactiveSuggestion: !!response.proactiveSuggestion,
      });

      // Store the conversation in memory if successful
      if (response.finalResponse) {
        const conversationText = `User: ${message}\nAssistant: ${response.finalResponse}`;
        await this.storeMemory(
          conversationText,
          {
            type: 'conversation',
            user_message: message,
            assistant_response: response.finalResponse,
            request_id: requestId,
          },
          ['conversation', 'chat'],
          userId,
          sessionId
        );
      }

      return response;
    } catch (error) {
      console.error(`[${requestId}] Failed to process user message:`, error);

      // Handle different error types with specific fallback responses
      if (error instanceof APIError) {
        if (error.details?.type === 'CHAT_PROCESSING_ERROR') {
          console.warn(`[${requestId}] Chat processing error:`, error.details);
          return {
            finalResponse: "I'm having trouble processing your message right now. Could you try rephrasing it or asking something else?",
          };
        } else if (error.details?.type === 'SERVICE_UNAVAILABLE') {
          console.warn(`[${requestId}] AI service unavailable:`, error.details);
          return {
            finalResponse: "My AI services are temporarily unavailable. Please try again in a few minutes, and I'll be ready to help you.",
          };
        } else if (error.details?.type === 'VALIDATION_ERROR') {
          console.warn(`[${requestId}] Validation error:`, error.details);
          return {
            finalResponse: "I noticed there might be an issue with your message format. Could you try asking your question in a different way?",
          };
        } else if (error.details?.type === 'TIMEOUT_ERROR') {
          console.warn(`[${requestId}] Request timeout:`, error.details);
          return {
            finalResponse: "Your request is taking longer than expected to process. Please try again with a shorter message or try again in a moment.",
          };
        } else if (error.details?.type === 'NETWORK_ERROR') {
          console.warn(`[${requestId}] Network error:`, error.details);
          return {
            finalResponse: "I'm having trouble connecting to my backend services. Please check your internet connection and try again.",
          };
        } else if (error.status === 429) {
          console.warn(`[${requestId}] Rate limit exceeded:`, error.details);
          return {
            finalResponse: "I'm receiving a lot of requests right now. Please wait a moment before sending another message.",
          };
        } else if (error.status >= 500) {
          console.warn(`[${requestId}] Server error:`, error.details);
          return {
            finalResponse: "I'm experiencing some technical difficulties. Please try again in a few minutes.",
          };
        }
      }

      // Generic fallback response for unknown errors
      return {
        finalResponse: "I'm having trouble connecting to my backend services right now. Please try again in a moment.",
      };
    }
  }

  // User Management Integration
  async getUserProfile(userId: string): Promise<{
    id: string;
    username: string;
    roles: string[];
    preferences: Record<string, any>;
    created_at: string;
    last_active: string;
  } | null> {
    try {
      return await this.makeRequest(`/api/users/${encodeURIComponent(userId)}`, {}, true);
    } catch (error) {
      if (error instanceof APIError) {
        if (error.status === 404) {
          console.warn(`User profile not found for user: ${userId}`);
          return null;
        } else if (error.details?.type === 'SERVICE_UNAVAILABLE') {
          console.warn('User service unavailable');
          return null;
        }
      }
      console.error('Failed to get user profile:', error);
      return null;
    }
  }

  async updateUserPreferences(
    userId: string,
    preferences: Record<string, any>
  ): Promise<boolean> {
    try {
      await this.makeRequest(`/api/users/${encodeURIComponent(userId)}/preferences`, {
        method: 'PUT',
        body: JSON.stringify(preferences),
      });
      return true;
    } catch (error) {
      if (error instanceof APIError) {
        if (error.details?.type === 'VALIDATION_ERROR') {
          console.warn('Invalid user preferences:', error.details);
          return false;
        } else if (error.details?.type === 'SERVICE_UNAVAILABLE') {
          console.warn('User service unavailable, preferences not updated');
          return false;
        }
      }
      console.error('Failed to update user preferences:', error);
      return false;
    }
  }

  // Clear cache
  clearCache(): void {
    this.cache.clear();
  }

  // Get cache stats
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
    };
  }

  // Public makeRequest method for external use
  async makeRequestPublic<T>(
    endpoint: string,
    options: RequestInit = {},
    useCache: boolean = false,
    cacheTtl: number = webUIConfig.cacheTtl,
    maxRetries: number = webUIConfig.maxRetries,
    retryDelay: number = webUIConfig.retryDelay
  ): Promise<T> {
    return this.makeRequest<T>(endpoint, options, useCache, cacheTtl, maxRetries, retryDelay);
  }
}

// Global instance
let karenBackend: KarenBackendService | null = null;

export function getKarenBackend(): KarenBackendService {
  if (!karenBackend) {
    karenBackend = new KarenBackendService();
  }
  return karenBackend;
}

export function initializeKarenBackend(config?: Partial<BackendConfig>): KarenBackendService {
  karenBackend = new KarenBackendService(config);
  return karenBackend;
}

// Export types
export type {
  BackendConfig,
  MemoryEntry,
  MemoryQuery,
  PluginInfo,
  PluginExecutionResult,
  SystemMetrics,
  UsageAnalytics,
  WebUIErrorResponse,
};

export { KarenBackendService, APIError };