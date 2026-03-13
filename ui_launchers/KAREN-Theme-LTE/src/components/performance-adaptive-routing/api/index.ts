/**
 * Performance Adaptive Routing API
 * API integration layer for fetching performance data and routing information
 */

import {
  Provider,
  PerformanceMetrics,
  RoutingDecision,
  RoutingAnalytics,
  Anomaly,
  PerformanceAlert,
  RoutingStrategy,
  AdaptiveRoutingConfig,
  TimeRange,
  ProviderPerformance,
} from '../types';

interface ApiErrorPayload {
  message?: string;
  error?: string;
  details?: unknown;
  [key: string]: unknown;
}

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api';
const API_VERSION = 'v1';
const API_ENDPOINT = `${API_BASE_URL}/performance-adaptive-routing/${API_VERSION}`;

// Error handling
class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Request utilities
const createHeaders = (contentType: string = 'application/json'): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': contentType,
  };

  // Add authentication token if available
  const token = localStorage.getItem('auth_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
};

const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    let errorMessage = 'An error occurred';
    let errorDetails: unknown;

    try {
      const errorData = (await response.json()) as ApiErrorPayload;
      errorMessage = (typeof errorData.message === 'string' && errorData.message)
        || (typeof errorData.error === 'string' && errorData.error)
        || errorMessage;
      errorDetails = errorData.details ?? errorData;
    } catch {
      errorMessage = response.statusText || errorMessage;
    }

    throw new ApiError(
      errorMessage,
      response.status,
      response.status.toString(),
      errorDetails
    );
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return (await response.json()) as T;
  }

  return (await response.text()) as T;
};

const makeRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const url = `${API_ENDPOINT}${endpoint}`;
  const config: RequestInit = {
    headers: createHeaders(),
    ...options,
  };

  try {
    const response = await fetch(url, config);
    return await handleResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Network error occurred', 0, 'NETWORK_ERROR', error);
  }
};

// API Methods
export const performanceAdaptiveRoutingApi = {
  // Providers
  async getProviders(): Promise<Provider[]> {
    return makeRequest('/providers');
  },

  async getProvider(providerId: string): Promise<Provider> {
    return makeRequest(`/providers/${providerId}`);
  },

  async enableProvider(providerId: string): Promise<void> {
    return makeRequest(`/providers/${providerId}/enable`, {
      method: 'POST',
    });
  },

  async disableProvider(providerId: string, reason: string): Promise<void> {
    return makeRequest(`/providers/${providerId}/disable`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },

  // Performance Metrics
  async getMetrics(
    providerId?: string,
    timeRange?: TimeRange
  ): Promise<PerformanceMetrics[]> {
    const params = new URLSearchParams();
    
    if (providerId) {
      params.append('providerId', providerId);
    }
    
    if (timeRange) {
      params.append('start', timeRange.start.toISOString());
      params.append('end', timeRange.end.toISOString());
    }

    const query = params.toString();
    return makeRequest(`/metrics${query ? `?${query}` : ''}`);
  },

  async getProviderPerformance(providerId: string): Promise<ProviderPerformance> {
    return makeRequest(`/providers/${providerId}/performance`);
  },

  async compareProviders(providerIds: string[]): Promise<ProviderPerformance[]> {
    return makeRequest('/providers/compare', {
      method: 'POST',
      body: JSON.stringify({ providerIds }),
    });
  },

  // Routing Decisions
  async getRoutingDecisions(timeRange?: TimeRange): Promise<RoutingDecision[]> {
    const params = new URLSearchParams();
    
    if (timeRange) {
      params.append('start', timeRange.start.toISOString());
      params.append('end', timeRange.end.toISOString());
    }

    const query = params.toString();
    return makeRequest(`/routing/decisions${query ? `?${query}` : ''}`);
  },

  async getRoutingDecision(decisionId: string): Promise<RoutingDecision> {
    return makeRequest(`/routing/decisions/${decisionId}`);
  },

  async overrideRouting(
    requestId: string,
    providerId: string,
    reason: string
  ): Promise<void> {
    return makeRequest('/routing/override', {
      method: 'POST',
      body: JSON.stringify({ requestId, providerId, reason }),
    });
  },

  // Analytics
  async getAnalytics(period: string): Promise<RoutingAnalytics[]> {
    return makeRequest(`/analytics?period=${period}`);
  },

  async getPerformanceTrends(
    metric: string,
    timeRange: TimeRange
  ): Promise<Record<string, unknown>> {
    const params = new URLSearchParams();
    params.append('metric', metric);
    params.append('start', timeRange.start.toISOString());
    params.append('end', timeRange.end.toISOString());

    return makeRequest(`/analytics/trends?${params.toString()}`);
  },

  async getAnomalies(timeRange?: TimeRange): Promise<Anomaly[]> {
    const params = new URLSearchParams();
    
    if (timeRange) {
      params.append('start', timeRange.start.toISOString());
      params.append('end', timeRange.end.toISOString());
    }

    const query = params.toString();
    return makeRequest(`/analytics/anomalies${query ? `?${query}` : ''}`);
  },

  // Alerts
  async getAlerts(): Promise<PerformanceAlert[]> {
    return makeRequest('/alerts');
  },

  async acknowledgeAlert(alertId: string, userId: string): Promise<void> {
    return makeRequest(`/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ userId }),
    });
  },

  async resolveAlert(alertId: string, resolution: string): Promise<void> {
    return makeRequest(`/alerts/${alertId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution }),
    });
  },

  // Strategies
  async getStrategies(): Promise<RoutingStrategy[]> {
    return makeRequest('/strategies');
  },

  async getStrategy(strategyId: string): Promise<RoutingStrategy> {
    return makeRequest(`/strategies/${strategyId}`);
  },

  async updateStrategy(
    strategyId: string,
    strategy: Partial<RoutingStrategy>
  ): Promise<RoutingStrategy> {
    return makeRequest(`/strategies/${strategyId}`, {
      method: 'PUT',
      body: JSON.stringify(strategy),
    });
  },

  async setActiveStrategy(strategyId: string): Promise<void> {
    return makeRequest(`/strategies/${strategyId}/activate`, {
      method: 'POST',
    });
  },

  // Configuration
  async getConfig(): Promise<AdaptiveRoutingConfig> {
    return makeRequest('/config');
  },

  async updateConfig(config: Partial<AdaptiveRoutingConfig>): Promise<AdaptiveRoutingConfig> {
    return makeRequest('/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  },

  // Export
  async exportMetrics(
    providerId?: string,
    timeRange?: TimeRange
  ): Promise<Blob> {
    const params = new URLSearchParams();
    
    if (providerId) {
      params.append('providerId', providerId);
    }
    
    if (timeRange) {
      params.append('start', timeRange.start.toISOString());
      params.append('end', timeRange.end.toISOString());
    }

    const response = await fetch(`${API_ENDPOINT}/export/metrics?${params.toString()}`, {
      headers: createHeaders(),
    });

    if (!response.ok) {
      throw new ApiError('Failed to export metrics', response.status);
    }

    return response.blob();
  },

  async exportAnalytics(period: string): Promise<Blob> {
    const response = await fetch(`${API_ENDPOINT}/export/analytics?period=${period}`, {
      headers: createHeaders(),
    });

    if (!response.ok) {
      throw new ApiError('Failed to export analytics', response.status);
    }

    return response.blob();
  },

  // Real-time updates (WebSocket)
  createWebSocketConnection(): WebSocket {
    const token = localStorage.getItem('auth_token');
    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/performance-adaptive-routing/${API_VERSION}/ws`;
    
    const ws = new WebSocket(token ? `${wsUrl}?token=${token}` : wsUrl);
    return ws;
  },
};

// Utility functions
export const createWebSocketManager = () => {
  let ws: WebSocket | null = null;
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 5;
  const reconnectDelay = 1000;

  const connect = <T = unknown>(
    onMessage: (data: T) => void,
    onError?: (error: Event) => void,
    onClose?: (event: CloseEvent) => void
  ) => {
    try {
      ws = performanceAdaptiveRoutingApi.createWebSocketConnection();
      
      ws.onopen = () => {
        reconnectAttempts = 0;
        console.log('WebSocket connection established');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as T;
          onMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };

      ws.onclose = (event) => {
        console.log('WebSocket connection closed:', event);
        onClose?.(event);
        
        // Attempt to reconnect
        if (reconnectAttempts < maxReconnectAttempts) {
          setTimeout(() => {
            reconnectAttempts++;
            connect(onMessage, onError, onClose);
          }, reconnectDelay * Math.pow(2, reconnectAttempts));
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  };

  const disconnect = () => {
    if (ws) {
      ws.close();
      ws = null;
    }
  };

  const send = (data: unknown) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  };

  return {
    connect,
    disconnect,
    send,
    isConnected: () => ws?.readyState === WebSocket.OPEN,
  };
};

// Error handling utilities
export const isApiError = (error: unknown): error is ApiError => {
  return error instanceof ApiError;
};

export const getErrorMessage = (error: unknown): string => {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unknown error occurred';
};

export const getErrorCode = (error: unknown): string | undefined => {
  if (isApiError(error)) {
    return error.code;
  }
  return undefined;
};

export default performanceAdaptiveRoutingApi;
