import { useCallback, useEffect, useState, useRef } from 'react';
import { NetworkResilience, RetryOptions, NetworkRequest, CircuitBreakerState } from '../lib/networkResilience';

export interface NetworkStatus {
  isOnline: boolean;
  circuitBreakerState: CircuitBreakerState;
  failureCount: number;
  lastFailureTime: number;
  connectionInfo: any;
}

export interface UseNetworkResilienceOptions {
  failureThreshold?: number;
  recoveryTimeout?: number;
  correlationId?: string;
  onOnlineStatusChange?: (online: boolean) => void;
  onCircuitBreakerStateChange?: (state: CircuitBreakerState) => void;
}

export interface UseNetworkResilienceReturn {
  networkStatus: NetworkStatus;
  fetchWithResilience: (request: NetworkRequest, retryOptions?: RetryOptions) => Promise<Response>;
  healthCheck: (url: string, timeout?: number) => Promise<boolean>;
  resetCircuitBreaker: () => void;
  isOnline: boolean;
  circuitBreakerState: CircuitBreakerState;
}

export const useNetworkResilience = (
  options: UseNetworkResilienceOptions = {}
): UseNetworkResilienceReturn => {
  const {
    failureThreshold,
    recoveryTimeout,
    correlationId,
    onOnlineStatusChange,
    onCircuitBreakerStateChange,
  } = options;

  const networkResilienceRef = useRef<NetworkResilience>();
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus>(() => ({
    isOnline: navigator.onLine,
    circuitBreakerState: CircuitBreakerState.CLOSED,
    failureCount: 0,
    lastFailureTime: 0,
    connectionInfo: null,
  }));

  // Initialize network resilience instance
  useEffect(() => {
    networkResilienceRef.current = new NetworkResilience({
      failureThreshold,
      recoveryTimeout,
      correlationId,
    });

    // Set up online status listener
    const unsubscribeOnline = networkResilienceRef.current.onOnlineStatusChange((online) => {
      setNetworkStatus(prev => ({ ...prev, isOnline: online }));
      onOnlineStatusChange?.(online);
    });

    // Update initial status
    const updateStatus = () => {
      if (networkResilienceRef.current) {
        const status = networkResilienceRef.current.getNetworkStatus();
        setNetworkStatus({
          isOnline: status.isOnline,
          circuitBreakerState: status.circuitBreaker.state,
          failureCount: status.circuitBreaker.failureCount,
          lastFailureTime: status.circuitBreaker.lastFailureTime,
          connectionInfo: status.connection,
        });
      }
    };

    updateStatus();

    // Set up periodic status updates
    const statusInterval = setInterval(updateStatus, 5000);

    return () => {
      unsubscribeOnline();
      clearInterval(statusInterval);
      networkResilienceRef.current?.destroy();
    };
  }, [failureThreshold, recoveryTimeout, correlationId, onOnlineStatusChange]);

  // Monitor circuit breaker state changes
  useEffect(() => {
    if (onCircuitBreakerStateChange) {
      onCircuitBreakerStateChange(networkStatus.circuitBreakerState);
    }
  }, [networkStatus.circuitBreakerState, onCircuitBreakerStateChange]);

  const fetchWithResilience = useCallback(
    async (request: NetworkRequest, retryOptions?: RetryOptions): Promise<Response> => {
      if (!networkResilienceRef.current) {
        throw new Error('Network resilience not initialized');
      }

      try {
        const response = await networkResilienceRef.current.fetchWithResilience(
          request,
          { ...retryOptions, correlationId }
        );

        // Update status after successful request
        const status = networkResilienceRef.current.getNetworkStatus();
        setNetworkStatus(prev => ({
          ...prev,
          circuitBreakerState: status.circuitBreaker.state,
          failureCount: status.circuitBreaker.failureCount,
          lastFailureTime: status.circuitBreaker.lastFailureTime,
        }));

        return response;
      } catch (error) {
        // Update status after failed request
        if (networkResilienceRef.current) {
          const status = networkResilienceRef.current.getNetworkStatus();
          setNetworkStatus(prev => ({
            ...prev,
            circuitBreakerState: status.circuitBreaker.state,
            failureCount: status.circuitBreaker.failureCount,
            lastFailureTime: status.circuitBreaker.lastFailureTime,
          }));
        }
        throw error;
      }
    },
    [correlationId]
  );

  const healthCheck = useCallback(
    async (url: string, timeout?: number): Promise<boolean> => {
      if (!networkResilienceRef.current) {
        return false;
      }
      return networkResilienceRef.current.healthCheck(url, timeout);
    },
    []
  );

  const resetCircuitBreaker = useCallback(() => {
    if (networkResilienceRef.current) {
      networkResilienceRef.current.resetCircuitBreaker();
      const status = networkResilienceRef.current.getNetworkStatus();
      setNetworkStatus(prev => ({
        ...prev,
        circuitBreakerState: status.circuitBreaker.state,
        failureCount: status.circuitBreaker.failureCount,
        lastFailureTime: status.circuitBreaker.lastFailureTime,
      }));
    }
  }, []);

  return {
    networkStatus,
    fetchWithResilience,
    healthCheck,
    resetCircuitBreaker,
    isOnline: networkStatus.isOnline,
    circuitBreakerState: networkStatus.circuitBreakerState,
  };
};

export default useNetworkResilience;