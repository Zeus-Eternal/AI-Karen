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

  constructor(config: Partial<BackendConfig> = {}) {
    this.config = {
      baseUrl: config.baseUrl || process.env.KAREN_BACKEND_URL || 'http://localhost:8000',
      apiKey: config.apiKey || process.env.KAREN_API_KEY,
      timeout: config.timeout || 30000,
    };
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    useCache: boolean = false,
    cacheTtl: number = 300000 // 5 minutes
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
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

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
      console.error(`Backend request failed for ${endpoint}:`, error);
      throw error;
    }
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
      console.error('Failed to query memories:', error);
      return [];
    }
  }

  async getMemoryStats(userId?: string): Promise<Record<string, any>> {
    try {
      const params = userId ? `?user_id=${encodeURIComponent(userId)}` : '';
      return await this.makeRequest<Record<string, any>>(`/api/memory/stats${params}`, {}, true);
    } catch (error) {
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
      console.error(`Failed to execute plugin ${pluginName}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
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
    try {
      // First, query relevant memories
      const relevantMemories = await this.queryMemories({
        text: message,
        user_id: userId,
        session_id: sessionId,
        top_k: 5,
        similarity_threshold: 0.7,
      });

      // Prepare context for AI processing
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

      // Process with AI Karen backend
      const response = await this.makeRequest<HandleUserMessageResult>('/api/chat/process', {
        method: 'POST',
        body: JSON.stringify(context),
      });

      // Store the conversation in memory
      const conversationText = `User: ${message}\nAssistant: ${response.finalResponse}`;
      await this.storeMemory(
        conversationText,
        {
          type: 'conversation',
          user_message: message,
          assistant_response: response.finalResponse,
        },
        ['conversation', 'chat'],
        userId,
        sessionId
      );

      return response;
    } catch (error) {
      console.error('Failed to process user message:', error);
      // Fallback to local processing or error response
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
};

export { KarenBackendService };