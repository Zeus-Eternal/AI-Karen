/**
 * Provider Status Hook
 * Monitors LLM provider health, performance metrics, and real-time status
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  LLMProvider, 
  ProviderStatus, 
  ProviderHealthCheck, 
  ChatError,
  ConnectionStatus,
  ProviderCapabilities,
  ProviderConfigSchema,
  AuthType
} from '@/types/chat';
import { chatService } from '@/services/chatService';

interface UseProviderStatusReturn {
  // Status state
  providerStatuses: Record<string, LLMProvider>;
  healthChecks: Record<string, ProviderHealthCheck>;
  connectionStatus: ConnectionStatus;
  loading: boolean;
  error: ChatError | null;
  
  // Status actions
  testProviderConnection: (providerId: string, config?: Record<string, unknown>) => Promise<ConnectionTestResult>;
  startHealthMonitoring: (providerIds: string[]) => void;
  stopHealthMonitoring: () => void;
  refreshProviderStatus: (providerId: string) => Promise<void>;
  resetError: () => void;
}

interface ConnectionTestResult {
  success: boolean;
  responseTime?: number;
  error?: string;
  details?: Record<string, unknown>;
}

interface ProviderMetrics {
  responseTime: number;
  errorRate: number;
  uptime: number;
  lastCheck: Date;
  requestCount: number;
  successCount: number;
}

const HEALTH_CHECK_INTERVAL = 30000; // 30 seconds
const DEFAULT_PROVIDER_CAPABILITIES: ProviderCapabilities = {
  textGeneration: true,
  streaming: true,
  functionCalling: false,
  imageGeneration: false,
  voiceInput: false,
  voiceOutput: false,
  fileUpload: false,
  codeExecution: false,
  webSearch: false,
  memory: false,
  vision: false,
  contextWindow: 0,
  maxTokens: 0
};

const DEFAULT_PROVIDER_CONFIG_SCHEMA: ProviderConfigSchema = {
  type: 'object',
  properties: {},
  required: []
};

export const useProviderStatus = (): UseProviderStatusReturn => {
  const [providerStatuses, setProviderStatuses] = useState<Record<string, LLMProvider>>({} as Record<string, LLMProvider>);
  const [healthChecks, setHealthChecks] = useState<Record<string, ProviderHealthCheck>>({});
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    isConnected: false,
    isConnecting: false,
    isReconnecting: false,
    connectionAttempts: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ChatError | null>(null);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const metricsRef = useRef<Record<string, ProviderMetrics>>({});

  // Test provider connection
  const testProviderConnection = useCallback(async (
    providerId: string, 
    config?: Record<string, unknown>
  ): Promise<ConnectionTestResult> => {
    void config;
    const startTime = Date.now();
    
    try {
      setConnectionStatus(prev => ({
        ...prev,
        isConnecting: true,
        connectionAttempts: prev.connectionAttempts + 1
      }));

      // Test connection via API
      const result = await chatService.testProviderConnection(providerId);
      
      const responseTime = Date.now() - startTime;
      
      if (result.success) {
        setConnectionStatus({
          isConnected: true,
          isConnecting: false,
          isReconnecting: false,
          connectionAttempts: 0,
          lastConnected: new Date()
        });

        // Update provider status
        setProviderStatuses(prev => {
          const existing = prev[providerId];
          if (existing) {
            const updated = { ...existing, status: ProviderStatus.ACTIVE };
            return { ...prev, [providerId]: updated };
          }
          const newProvider: LLMProvider = {
            id: providerId,
            name: providerId,
            displayName: providerId,
            description: '',
            version: '1.0.0',
            capabilities: DEFAULT_PROVIDER_CAPABILITIES,
            models: [],
            configSchema: DEFAULT_PROVIDER_CONFIG_SCHEMA,
            status: ProviderStatus.ACTIVE,
            authType: AuthType.API_KEY,
            requiredConfig: []
          };
          return { ...prev, [providerId]: newProvider };
        });

        // Update metrics
        const metrics = metricsRef.current[providerId] || {
          responseTime: 0,
          errorRate: 0,
          uptime: 1,
          lastCheck: new Date(),
          requestCount: 0,
          successCount: 0
        };

        metricsRef.current[providerId] = {
          ...metrics,
          responseTime: (metrics.responseTime * 0.8) + (responseTime * 0.2),
          requestCount: metrics.requestCount + 1,
          successCount: metrics.successCount + 1,
          errorRate: (metrics.requestCount + 1) > 0 
            ? (metrics.requestCount - metrics.successCount) / (metrics.requestCount + 1)
            : 0,
          uptime: metrics.uptime * 0.95 + 0.05,
          lastCheck: new Date()
        };

        return {
          success: true,
          responseTime,
          details: result.data as Record<string, unknown>
        };
      } else {
        throw new Error(result.error || 'Connection test failed');
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Connection test failed';
      
      setConnectionStatus({
        isConnected: false,
        isConnecting: false,
        isReconnecting: connectionStatus.connectionAttempts > 0,
        connectionAttempts: connectionStatus.connectionAttempts + 1,
        error: errorMessage
      });

      // Update provider status
      setProviderStatuses(prev => {
        const existing = prev[providerId];
        if (existing) {
          const updated = { ...existing, status: ProviderStatus.ERROR };
          return { ...prev, [providerId]: updated };
        }
        const newProvider: LLMProvider = {
          id: providerId,
          name: providerId,
          displayName: providerId,
          description: '',
          version: '1.0.0',
          capabilities: DEFAULT_PROVIDER_CAPABILITIES,
          models: [],
          configSchema: DEFAULT_PROVIDER_CONFIG_SCHEMA,
          status: ProviderStatus.ERROR,
          authType: AuthType.API_KEY,
          requiredConfig: []
        };
        return { ...prev, [providerId]: newProvider };
      });
      // Update metrics
      const metrics = metricsRef.current[providerId] || {
        responseTime: 0,
        errorRate: 0,
        uptime: 1,
        lastCheck: new Date(),
        requestCount: 0,
        successCount: 0
      };

      metricsRef.current[providerId] = {
        ...metrics,
        requestCount: metrics.requestCount + 1,
        errorRate: (metrics.requestCount + 1) > 0 
          ? (metrics.requestCount - metrics.successCount + 1) / (metrics.requestCount + 1)
          : 1,
        uptime: metrics.uptime * 0.9,
        lastCheck: new Date()
      };

      return {
        success: false,
        error: errorMessage
      };
    }
  }, [connectionStatus]);

  // Refresh provider status
  const refreshProviderStatus = useCallback(async (providerId: string) => {
    setLoading(true);
    setError(null);

    try {
      const startTime = Date.now();
      const result = await chatService.testProviderConnection(providerId);
      const responseTime = Date.now() - startTime;

      const healthCheck: ProviderHealthCheck = {
        status: result.success ? 'healthy' : 'unhealthy',
        lastChecked: new Date(),
        responseTime,
        errorRate: metricsRef.current[providerId]?.errorRate || 0,
        uptime: metricsRef.current[providerId]?.uptime || 0,
        issues: result.success ? [] : [result.error || 'Connection failed']
      };

      setHealthChecks(prev => ({
        ...prev,
        [providerId]: healthCheck
      }));
    } catch (err) {
      const errorObj = {
        code: 'PROVIDER_STATUS_ERROR',
        message: err instanceof Error ? err.message : 'Failed to refresh provider status',
        details: { providerId },
        timestamp: new Date(),
        context: { provider: providerId }
      };
      setError(errorObj);
    } finally {
      setLoading(false);
    }
  }, []);

  // Start health monitoring for multiple providers
  const startHealthMonitoring = useCallback((providerIds: string[]) => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Initial health check
    providerIds.forEach(async (providerId) => {
      await refreshProviderStatus(providerId);
    });

    // Set up interval for periodic checks
    intervalRef.current = setInterval(async () => {
      for (const providerId of providerIds) {
        try {
          await refreshProviderStatus(providerId);
        } catch (err) {
          console.error(`Health check failed for provider ${providerId}:`, err);
        }
      }
    }, HEALTH_CHECK_INTERVAL);
  }, [refreshProviderStatus]);

  // Stop health monitoring
  const stopHealthMonitoring = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Reset error
  const resetError = useCallback(() => {
    setError(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopHealthMonitoring();
    };
  }, [stopHealthMonitoring]);

  return {
    providerStatuses,
    healthChecks,
    connectionStatus,
    loading,
    error,
    testProviderConnection,
    startHealthMonitoring,
    stopHealthMonitoring,
    refreshProviderStatus,
    resetError
  };
};
