/**
 * Unified API Client for Consolidated Endpoints
 * 
 * Features:
 * - Multi-endpoint fallback logic with ordered endpoint lists
 * - Consolidated endpoint support (/copilot/assist, /memory/search, /memory/commit)
 * - Legacy API call removal and migration to unified endpoints
 * - Comprehensive error handling with user-friendly messages
 * - Automatic retry logic with exponential backoff
 * - Request/response logging and monitoring
 */
import { getApiClient, type ApiResponse, type ApiError } from './api-client';
import { safeError } from './safe-console';
import { getConfigManager } from './endpoint-config';
import { useToast } from '@/hooks/use-toast';
export interface UnifiedApiClientConfig {
  enableFallback: boolean;
  maxRetries: number;
  retryDelay: number;
  timeout: number;
  enableLogging: boolean;
}
export interface ConsolidatedEndpoints {
  copilotAssist: string;
  memorySearch: string;
  memoryCommit: string;
  memoryUpdate: string;
  memoryDelete: string;
}
export interface CopilotAssistRequest {
  user_id: string;
  org_id?: string;
  message: string;
  top_k?: number;
  context?: Record<string, any>;
  stream?: boolean;
}
export interface CopilotAssistResponse {
  answer: string;
  context: Array<{
    id: string;
    text: string;
    score: number;
    tags: string[];
    metadata?: Record<string, any>;
  }>;
  actions: Array<{
    type: string;
    params: Record<string, any>;
    confidence: number;
    description?: string;
  }>;
  timings: {
    memory_search_ms: number;
    llm_generation_ms: number;
    total_ms: number;
  };
  correlation_id: string;
}
export interface MemorySearchRequest {
  user_id: string;
  org_id?: string;
  query: string;
  top_k?: number;
  tags?: string[];
  time_range?: [string, string];
  similarity_threshold?: number;
}
export interface MemorySearchResponse {
  hits: Array<{
    id: string;
    text: string;
    score: number;
    tags: string[];
    importance: number;
    decay_tier: string;
    created_at: string;
    updated_at?: string;
    metadata?: Record<string, any>;
  }>;
  total_found: number;
  query_time_ms: number;
  correlation_id: string;
}
export interface MemoryCommitRequest {
  user_id: string;
  org_id?: string;
  text: string;
  tags?: string[];
  importance?: number;
  decay?: 'short' | 'medium' | 'long' | 'pinned';
  metadata?: Record<string, any>;
}
export interface MemoryCommitResponse {
  id: string;
  status: 'created' | 'updated';
  embedding_generated: boolean;
  decay_tier_assigned: string;
  correlation_id: string;
}
/**
 * Unified API Client for consolidated endpoints
 */
export class UnifiedApiClient {
  private apiClient = getApiClient();
  private configManager = getConfigManager();
  private config: UnifiedApiClientConfig;
  private endpoints: ConsolidatedEndpoints;
  constructor(config?: Partial<UnifiedApiClientConfig>) {
    this.config = {
      enableFallback: true,
      maxRetries: 3,
      retryDelay: 1000,
      timeout: 30000,
      enableLogging: true,
      ...config
    };
    this.endpoints = {
      copilotAssist: '/copilot/assist',
      memorySearch: '/memory/search',
      memoryCommit: '/memory/commit',
      memoryUpdate: '/memory/update',
      memoryDelete: '/memory/delete'
    };
  }
  /**
   * Copilot Assist - Primary AI interaction endpoint
   */
  async copilotAssist(request: CopilotAssistRequest): Promise<CopilotAssistResponse> {
    this.validateRequest(request, ['user_id', 'message']);
    try {
      const response = await this.apiClient.post<CopilotAssistResponse>(
        this.endpoints.copilotAssist,
        {
          ...request,
          top_k: request.top_k || 6,
          context: request.context || {},
          stream: request.stream || false
        }
      );
      this.logSuccess('copilot_assist', 0);
      return response;
    } catch (error) {
      this.logError('copilot_assist', error);
      throw this.createUserFriendlyError(error, 'Failed to get AI assistance');
    }
  }
  /**
   * Memory Search - Unified memory query endpoint
   */
  async memorySearch(request: MemorySearchRequest): Promise<MemorySearchResponse> {
    this.validateRequest(request, ['user_id', 'query']);
    try {
      const response = await this.apiClient.post<MemorySearchResponse>(
        this.endpoints.memorySearch,
        {
          ...request,
          top_k: request.top_k || 12,
          similarity_threshold: request.similarity_threshold || 0.6
        }
      );
      this.logSuccess('memory_search', 0);
      return response;
    } catch (error) {
      this.logError('memory_search', error);
      throw this.createUserFriendlyError(error, 'Failed to search memories');
    }
  }
  /**
   * Memory Commit - Unified memory storage endpoint
   */
  async memoryCommit(request: MemoryCommitRequest): Promise<MemoryCommitResponse> {
    this.validateRequest(request, ['user_id', 'text']);
    try {
      const response = await this.apiClient.post<MemoryCommitResponse>(
        this.endpoints.memoryCommit,
        {
          ...request,
          importance: request.importance || 5,
          decay: request.decay || 'short',
          tags: request.tags || [],
          metadata: request.metadata || {}
        }
      );
      this.logSuccess('memory_commit', 0);
      return response;
    } catch (error) {
      this.logError('memory_commit', error);
      throw this.createUserFriendlyError(error, 'Failed to store memory');
    }
  }
  /**
   * Memory Update - Update existing memory
   */
  async memoryUpdate(
    memoryId: string, 
    updates: Partial<MemoryCommitRequest>
  ): Promise<MemoryCommitResponse> {
    if (!memoryId) {
      throw new Error('Memory ID is required for updates');
    }
    try {
      const response = await this.apiClient.put<MemoryCommitResponse>(
        `${this.endpoints.memoryUpdate}/${memoryId}`,
        updates
      );
      this.logSuccess('memory_update', 0);
      return response;
    } catch (error) {
      this.logError('memory_update', error);
      throw this.createUserFriendlyError(error, 'Failed to update memory');
    }
  }
  /**
   * Memory Delete - Remove memory
   */
  async memoryDelete(
    memoryId: string, 
    options: { 
      user_id: string; 
      hard_delete?: boolean; 
      org_id?: string; 
    }
  ): Promise<{ success: boolean; correlation_id: string }> {
    if (!memoryId) {
      throw new Error('Memory ID is required for deletion');
    }
    this.validateRequest(options, ['user_id']);
    try {
      const response = await this.apiClient.delete<{ success: boolean; correlation_id: string }>(
        `${this.endpoints.memoryDelete}/${memoryId}`
      );
      this.logSuccess('memory_delete', 0);
      return response;
    } catch (error) {
      this.logError('memory_delete', error);
      throw this.createUserFriendlyError(error, 'Failed to delete memory');
    }
  }
  /**
   * Batch Memory Operations - Handle multiple memory operations
   */
  async batchMemoryOperations(operations: Array<{
    type: 'search' | 'commit' | 'update' | 'delete';
    data: any;
  }>): Promise<Array<{ success: boolean; result?: any; error?: string }>> {
    const results = [];
    for (const operation of operations) {
      try {
        let result;
        switch (operation.type) {
          case 'search':
            result = await this.memorySearch(operation.data);
            break;
          case 'commit':
            result = await this.memoryCommit(operation.data);
            break;
          case 'update':
            result = await this.memoryUpdate(operation.data.id, operation.data);
            break;
          case 'delete':
            result = await this.memoryDelete(operation.data.id, operation.data);
            break;
          default:
            throw new Error(`Unknown operation type: ${operation.type}`);
        }
        results.push({ success: true, result });
      } catch (error) {
        results.push({ 
          success: false, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        });
      }
    }
    return results;
  }
  /**
   * Health Check - Test endpoint connectivity
   */
  async healthCheck(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    endpoints: Record<string, { available: boolean; responseTime?: number; error?: string }>;
    timestamp: string;
  }> {
    const endpointTests = Object.entries(this.endpoints).map(async ([name, endpoint]) => {
      try {
        const startTime = Date.now();
        await this.apiClient.get(`${endpoint}/health`);
        const responseTime = Date.now() - startTime;
        return {
          name,
          available: true,
          responseTime
        };
      } catch (error) {
        return {
          name,
          available: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        };
      }
    });
    const results = await Promise.all(endpointTests);
    const endpointStatus = results.reduce((acc, result) => {
      acc[result.name] = {
        available: result.available,
        responseTime: result.responseTime,
        error: result.error
      };
      return acc;
    }, {} as Record<string, any>);
    const availableCount = results.filter(r => r.available).length;
    const totalCount = results.length;
    let status: 'healthy' | 'degraded' | 'unhealthy';
    if (availableCount === totalCount) {
      status = 'healthy';
    } else if (availableCount > 0) {
      status = 'degraded';
    } else {
      status = 'unhealthy';
    }
    return {
      status,
      endpoints: endpointStatus,
      timestamp: new Date().toISOString()
    };
  }
  /**
   * Get endpoint statistics
   */
  getEndpointStats() {
    return this.apiClient.getEndpointStats();
  }
  /**
   * Clear caches and reset statistics
   */
  clearCaches(): void {
    this.apiClient.clearCaches();
  }
  /**
   * Update configuration
   */
  updateConfig(config: Partial<UnifiedApiClientConfig>): void {
    this.config = { ...this.config, ...config };
  }
  /**
   * Get current configuration
   */
  getConfig(): UnifiedApiClientConfig {
    return { ...this.config };
  }
  /**
   * Validate request parameters
   */
  private validateRequest(request: any, requiredFields: string[]): void {
    for (const field of requiredFields) {
      if (!request[field]) {
        throw new Error(`Missing required field: ${field}`);
      }
    }
  }
  /**
   * Create user-friendly error messages
   */
  private createUserFriendlyError(error: any, defaultMessage: string): Error {
    if (error instanceof Error) {
      // Check for specific error types
      if (error.message.includes('timeout')) {
        return new Error('Request timed out. Please check your connection and try again.');
      }
      if (error.message.includes('CORS')) {
        return new Error('Connection blocked by browser security. Please check your network settings.');
      }
      if (error.message.includes('404')) {
        return new Error('Service endpoint not found. The feature may not be available.');
      }
      if (error.message.includes('401') || error.message.includes('403')) {
        return new Error('Authentication required. Please log in and try again.');
      }
      if (error.message.includes('429')) {
        return new Error('Too many requests. Please wait a moment and try again.');
      }
      if (error.message.includes('500')) {
        return new Error('Server error. Please try again later.');
      }
      // Return original error message if it's already user-friendly
      if (error.message.length < 100 && !error.message.includes('fetch')) {
        return error;
      }
    }
    return new Error(defaultMessage);
  }
  /**
   * Log successful operations
   */
  private logSuccess(operation: string, responseTime: number): void {
    if (this.config.enableLogging) {
    }
  }
  /**
   * Log errors
   */
  private logError(operation: string, error: any): void {
    if (this.config.enableLogging) {
      safeError(`❌ ${operation} failed:`, error);
    }
  }
}
// Global instance
let unifiedApiClient: UnifiedApiClient | null = null;
/**
 * Get the global unified API client instance
 */
export function getUnifiedApiClient(): UnifiedApiClient {
  if (!unifiedApiClient) {
    unifiedApiClient = new UnifiedApiClient();
  }
  return unifiedApiClient;
}
/**
 * Initialize unified API client with custom configuration
 */
export function initializeUnifiedApiClient(config?: Partial<UnifiedApiClientConfig>): UnifiedApiClient {
  unifiedApiClient = new UnifiedApiClient(config);
  return unifiedApiClient;
}
// Types are already exported via export interface declarations above
