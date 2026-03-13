/**
 * Agent Selection API Service
 * Handles all API communications for the agent selection system
 */

import { BaseApiClient } from '@/lib/base-api-client';
import {
  Agent,
  AgentFilters,
  AgentSortOptions,
  AgentListResponse,
  AgentRecommendation,
  AgentComparison,
  AgentSelectionContext,
  AgentConfigurationValues,
  AgentRating
} from '../types';

// Define ApiResponse interface locally since it's not exported from base-api-client
interface ApiResponse<T = any> {
  data: T;
  status: number;
  headers: Headers;
  ok: boolean;
}

// Create a dedicated API client for agent selection
const agentApiClient = new BaseApiClient({
  baseUrl: process.env.NEXT_PUBLIC_AGENT_API_BASE_URL || '/api/agents',
  timeout: 30000, // 30 seconds timeout for agent operations
  defaultHeaders: {
    'X-Agent-Client': 'karen-theme-default',
  },
});

/**
 * Agent Selection API Service
 */
export class AgentApiService {
  /**
   * Fetch agents with optional filters and sorting
   */
  static async fetchAgents(
    filters?: AgentFilters,
    sort?: AgentSortOptions,
    page: number = 1,
    pageSize: number = 20
  ): Promise<ApiResponse<AgentListResponse>> {
    const params: Record<string, any> = {
      page,
      pageSize,
    };

    // Add filters to params
    if (filters) {
      if (filters.status && filters.status.length > 0) {
        params.status = filters.status.join(',');
      }
      if (filters.type && filters.type.length > 0) {
        params.type = filters.type.join(',');
      }
      if (filters.capabilities && filters.capabilities.length > 0) {
        params.capabilities = filters.capabilities.join(',');
      }
      if (filters.specializations && filters.specializations.length > 0) {
        params.specializations = filters.specializations.join(',');
      }
      if (filters.tags && filters.tags.length > 0) {
        params.tags = filters.tags.join(',');
      }
      if (filters.developer && filters.developer.length > 0) {
        params.developer = filters.developer.join(',');
      }
      if (filters.rating) {
        params.minRating = filters.rating.min;
        params.maxRating = filters.rating.max;
      }
      if (filters.pricing && filters.pricing.length > 0) {
        params.pricing = filters.pricing.join(',');
      }
      if (filters.performance) {
        if (filters.performance.minSuccessRate) {
          params.minSuccessRate = filters.performance.minSuccessRate;
        }
        if (filters.performance.maxResponseTime) {
          params.maxResponseTime = filters.performance.maxResponseTime;
        }
      }
      if (filters.search) {
        params.search = filters.search;
      }
      if (filters.includeDeprecated !== undefined) {
        params.includeDeprecated = filters.includeDeprecated;
      }
      if (filters.includeBeta !== undefined) {
        params.includeBeta = filters.includeBeta;
      }
    }

    // Add sorting to params
    if (sort) {
      params.sortBy = sort.field;
      params.sortOrder = sort.direction;
    }

    return agentApiClient.get<AgentListResponse>('/', { params });
  }

  /**
   * Fetch a single agent by ID
   */
  static async fetchAgent(agentId: string): Promise<ApiResponse<Agent>> {
    return agentApiClient.get<Agent>(`/${agentId}`);
  }

  /**
   * Get agent recommendations based on context
   */
  static async getRecommendations(
    context: AgentSelectionContext
  ): Promise<ApiResponse<AgentRecommendation[]>> {
    return agentApiClient.post<AgentRecommendation[]>('/recommendations', context);
  }

  /**
   * Compare multiple agents
   */
  static async compareAgents(
    agentIds: string[]
  ): Promise<ApiResponse<AgentComparison>> {
    return agentApiClient.post<AgentComparison>('/compare', { agentIds });
  }

  /**
   * Get agent configuration schema
   */
  static async getAgentConfiguration(
    agentId: string
  ): Promise<ApiResponse<any[]>> {
    return agentApiClient.get<any[]>(`/${agentId}/configuration`);
  }

  /**
   * Validate agent configuration
   */
  static async validateAgentConfiguration(
    agentId: string,
    configuration: AgentConfigurationValues
  ): Promise<ApiResponse<{ valid: boolean; errors?: string[] }>> {
    return agentApiClient.post<{ valid: boolean; errors?: string[] }>(
      `/${agentId}/configuration/validate`,
      configuration
    );
  }

  /**
   * Test agent with configuration
   */
  static async testAgent(
    agentId: string,
    configuration: AgentConfigurationValues,
    testData?: any
  ): Promise<ApiResponse<{ success: boolean; result?: any; error?: string }>> {
    return agentApiClient.post<{ success: boolean; result?: any; error?: string }>(
      `/${agentId}/test`,
      { configuration, testData }
    );
  }

  /**
   * Get agent performance metrics
   */
  static async getAgentPerformanceMetrics(
    agentId: string,
    timeRange?: { start: Date; end: Date }
  ): Promise<ApiResponse<any>> {
    const params: Record<string, any> = {};
    
    if (timeRange) {
      params.startTime = timeRange.start.toISOString();
      params.endTime = timeRange.end.toISOString();
    }

    return agentApiClient.get<any>(`/${agentId}/performance`, { params });
  }

  /**
   * Get agent usage statistics
   */
  static async getAgentUsageStatistics(
    agentId: string,
    timeRange?: { start: Date; end: Date }
  ): Promise<ApiResponse<any>> {
    const params: Record<string, any> = {};
    
    if (timeRange) {
      params.startTime = timeRange.start.toISOString();
      params.endTime = timeRange.end.toISOString();
    }

    return agentApiClient.get<any>(`/${agentId}/usage`, { params });
  }

  /**
   * Rate an agent
   */
  static async rateAgent(
    agentId: string,
    rating: Omit<AgentRating, 'userId' | 'timestamp'>
  ): Promise<ApiResponse<AgentRating>> {
    return agentApiClient.post<AgentRating>(`/${agentId}/ratings`, rating);
  }

  /**
   * Get agent ratings and reviews
   */
  static async getAgentRatings(
    agentId: string,
    page: number = 1,
    pageSize: number = 10
  ): Promise<ApiResponse<{
    ratings: AgentRating[];
    total: number;
    average: number;
    distribution: Record<number, number>;
  }>> {
    return agentApiClient.get<any>(`/${agentId}/ratings`, {
      params: { page, pageSize }
    });
  }

  /**
   * Search agents by capability
   */
  static async searchAgentsByCapability(
    capability: string,
    filters?: AgentFilters,
    sort?: AgentSortOptions
  ): Promise<ApiResponse<AgentListResponse>> {
    const params: Record<string, any> = {
      capability,
    };

    // Add filters to params
    if (filters) {
      if (filters.status && filters.status.length > 0) {
        params.status = filters.status.join(',');
      }
      if (filters.type && filters.type.length > 0) {
        params.type = filters.type.join(',');
      }
      if (filters.rating) {
        params.minRating = filters.rating.min;
        params.maxRating = filters.rating.max;
      }
    }

    // Add sorting to params
    if (sort) {
      params.sortBy = sort.field;
      params.sortOrder = sort.direction;
    }

    return agentApiClient.get<AgentListResponse>('/search/by-capability', { params });
  }

  /**
   * Search agents by specialization
   */
  static async searchAgentsBySpecialization(
    specialization: string,
    filters?: AgentFilters,
    sort?: AgentSortOptions
  ): Promise<ApiResponse<AgentListResponse>> {
    const params: Record<string, any> = {
      specialization,
    };

    // Add filters to params
    if (filters) {
      if (filters.status && filters.status.length > 0) {
        params.status = filters.status.join(',');
      }
      if (filters.type && filters.type.length > 0) {
        params.type = filters.type.join(',');
      }
      if (filters.rating) {
        params.minRating = filters.rating.min;
        params.maxRating = filters.rating.max;
      }
    }

    // Add sorting to params
    if (sort) {
      params.sortBy = sort.field;
      params.sortOrder = sort.direction;
    }

    return agentApiClient.get<AgentListResponse>('/search/by-specialization', { params });
  }

  /**
   * Get popular agents
   */
  static async getPopularAgents(
    limit: number = 10,
    timeRange?: { start: Date; end: Date }
  ): Promise<ApiResponse<Agent[]>> {
    const params: Record<string, any> = {
      limit,
    };
    
    if (timeRange) {
      params.startTime = timeRange.start.toISOString();
      params.endTime = timeRange.end.toISOString();
    }

    return agentApiClient.get<Agent[]>('/popular', { params });
  }

  /**
   * Get recently updated agents
   */
  static async getRecentlyUpdatedAgents(
    limit: number = 10
  ): Promise<ApiResponse<Agent[]>> {
    return agentApiClient.get<Agent[]>('/recent', {
      params: { limit }
    });
  }

  /**
   * Get agent categories and specializations
   */
  static async getAgentCategories(): Promise<ApiResponse<{
    capabilities: string[];
    specializations: string[];
    tags: string[];
    developers: string[];
  }>> {
    return agentApiClient.get<any>('/categories');
  }

  /**
   * Create a WebSocket connection for real-time agent updates
   */
  static createWebSocketConnection(): WebSocket {
    const wsUrl = process.env.NEXT_PUBLIC_AGENT_WS_URL || 
                  `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/agents/ws`;
    
    const ws = new WebSocket(wsUrl);
    
    return ws;
  }

  /**
   * Subscribe to real-time agent updates
   */
  static subscribeToAgentUpdates(
    callback: (event: any) => void
  ): () => void {
    const ws = this.createWebSocketConnection();
    
    ws.onopen = () => {
      console.log('Agent updates WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const agentEvent = JSON.parse(event.data);
        callback(agentEvent);
      } catch (error) {
        console.error('Error parsing agent update event:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('Agent updates WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('Agent updates WebSocket disconnected');
    };
    
    // Return unsubscribe function
    return () => {
      ws.close();
    };
  }

  /**
   * Export agent data
   */
  static async exportAgents(
    filters?: AgentFilters,
    format: 'json' | 'csv' | 'xlsx' = 'json'
  ): Promise<ApiResponse<Blob>> {
    const params: Record<string, any> = {
      format,
    };

    // Add filters to params
    if (filters) {
      if (filters.status && filters.status.length > 0) {
        params.status = filters.status.join(',');
      }
      if (filters.type && filters.type.length > 0) {
        params.type = filters.type.join(',');
      }
      if (filters.capabilities && filters.capabilities.length > 0) {
        params.capabilities = filters.capabilities.join(',');
      }
    }

    return agentApiClient.get<Blob>('/export', { params });
  }

  /**
   * Get agent health status
   */
  static async getAgentHealthStatus(
    agentId: string
  ): Promise<ApiResponse<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    checks: Array<{
      name: string;
      status: 'pass' | 'fail' | 'warn';
      message?: string;
    }>;
    lastCheck: Date;
  }>> {
    return agentApiClient.get<any>(`/${agentId}/health`);
  }

  /**
   * Get agent logs
   */
  static async getAgentLogs(
    agentId: string,
    level: 'debug' | 'info' | 'warn' | 'error' = 'info',
    limit: number = 100
  ): Promise<ApiResponse<Array<{
    timestamp: Date;
    level: string;
    message: string;
    metadata?: any;
  }>>> {
    return agentApiClient.get<any>(`/${agentId}/logs`, {
      params: { level, limit }
    });
  }
}

// Export the default API client for advanced usage
export { agentApiClient };

// Export convenience functions for common operations
export const agentApi = {
  fetchAgents: AgentApiService.fetchAgents,
  fetchAgent: AgentApiService.fetchAgent,
  getRecommendations: AgentApiService.getRecommendations,
  compareAgents: AgentApiService.compareAgents,
  getAgentConfiguration: AgentApiService.getAgentConfiguration,
  validateAgentConfiguration: AgentApiService.validateAgentConfiguration,
  testAgent: AgentApiService.testAgent,
  getAgentPerformanceMetrics: AgentApiService.getAgentPerformanceMetrics,
  getAgentUsageStatistics: AgentApiService.getAgentUsageStatistics,
  rateAgent: AgentApiService.rateAgent,
  getAgentRatings: AgentApiService.getAgentRatings,
  searchAgentsByCapability: AgentApiService.searchAgentsByCapability,
  searchAgentsBySpecialization: AgentApiService.searchAgentsBySpecialization,
  getPopularAgents: AgentApiService.getPopularAgents,
  getRecentlyUpdatedAgents: AgentApiService.getRecentlyUpdatedAgents,
  getAgentCategories: AgentApiService.getAgentCategories,
  subscribeToAgentUpdates: AgentApiService.subscribeToAgentUpdates,
  exportAgents: AgentApiService.exportAgents,
  getAgentHealthStatus: AgentApiService.getAgentHealthStatus,
  getAgentLogs: AgentApiService.getAgentLogs,
};