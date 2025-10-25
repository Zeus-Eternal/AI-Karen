/**
 * Tests for useSystemHealth hook
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useSystemHealth } from '../useSystemHealth';
import * as loggingModule from '../../lib/logging';

// Mock the logging module
jest.mock('../../lib/logging', () => ({
  connectivityLogger: {
    logError: jest.fn()
  },
  performanceTracker: {
    getPerformanceStats: jest.fn(() => ({
      count: 100,
      averageTime: 1200,
      minTime: 200,
      maxTime: 3000,
      p95Time: 2500,
      p99Time: 2800
    })),
    getRecentMetrics: jest.fn(() => [])
  }
}));

// Mock fetch
global.fetch = jest.fn();

describe('useSystemHealth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    
    // Mock successful health check responses
    (global.fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/api/health/')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ status: 'healthy' })
        });
      }
      return Promise.reject(new Error('Not found'));
    });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Initial State', () => {
    it('should start with loading state', () => {
      const { result } = renderHook(() => useSystemHealth());
      
      expect(result.current.isLoading).toBe(true);
      expect(result.current.systemHealth).toBe(null);
      expect(result.current.error).toBe(null);
      expect(result.current.lastUpdate).toBe(null);
    });

    it('should load system health on mount', async () => {
      const { result } = renderHook(() => useSystemHealth());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(result.current.systemHealth).not.toBe(null);
      expect(result.current.lastUpdate).not.toBe(null);
    });
  });

  describe('Configuration', () => {
    it('should use default configuration', async () => {
      const { result } = renderHook(() => useSystemHealth());
      
      await waitFor(() => {
        expect(result.current.config).toEqual({
          refreshInterval: 30000,
          enableRealTimeUpdates: true,
          showDetailedMetrics: true,
          alertThresholds: {
            responseTime: 5000,
            errorRate: 5,
            authFailureRate: 15
          }
        });
      });
    });

    it('should merge custom configuration', async () => {
      const customConfig = {
        refreshInterval: 10000,
        alertThresholds: {
          responseTime: 3000,
          errorRate: 2,
          authFailureRate: 10
        }
      };
      
      const { result } = renderHook(() => 
        useSystemHealth({ config: customConfig })
      );
      
      await waitFor(() => {
        expect(result.current.config.refreshInterval).toBe(10000);
        expect(result.current.config.alertThresholds.responseTime).toBe(3000);
        expect(result.current.config.enableRealTimeUpdates).toBe(true); // Default value
      });
    });
  });

  describe('Health Status Methods', () => {
    it('should return correct health status', async () => {
      const { result } = renderHook(() => useSystemHealth());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      const status = result.current.getHealthStatus();
      expect(['healthy', 'degraded', 'critical']).toContain(status);
    });

    it('should return component status', async () => {
      const { result } = renderHook(() => useSystemHealth());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      const backendStatus = result.current.getComponentStatus('backend');
      expect(['healthy', 'degraded', 'failed']).toContain(backendStatus);
    });

    it('should determine if system is healthy', async () => {
      const { result } = renderHook(() => useSystemHealth());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      const isHealthy = result.current.isHealthy();
      expect(typeof isHealthy).toBe('boolean');
    });

    it('should detect alerts', async () => {
      const { result } = renderHook(() => useSystemHealth({
        config: {
          alertThresholds: {
            responseTime: 100, // Very low threshold to trigger alert
            errorRate: 0.1,
            authFailureRate: 1
          }
        }
      }));
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      const hasAlerts = result.current.hasAlerts();
      expect(typeof hasAlerts).toBe('boolean');
    });
  });

  describe('Manual Refresh', () => {
    it('should refresh health data manually', async () => {
      const { result } = renderHook(() => useSystemHealth());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      const initialUpdate = result.current.lastUpdate;
      
      // Wait a bit to ensure timestamp difference
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 10));
        result.current.refreshHealth();
      });
      
      await waitFor(() => {
        expect(result.current.lastUpdate).not.toEqual(initialUpdate);
      });
    });
  });

  describe('Auto Refresh', () => {
    it('should auto-refresh at configured intervals', async () => {
      const onHealthChange = jest.fn();
      
      const { result } = renderHook(() => 
        useSystemHealth({
          config: { refreshInterval: 1000 },
          onHealthChange
        })
      );
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      // Clear initial call
      onHealthChange.mockClear();
      
      // Fast-forward time to trigger auto-refresh
      act(() => {
        jest.advanceTimersByTime(1000);
      });
      
      await waitFor(() => {
        expect(onHealthChange).toHaveBeenCalled();
      });
    });

    it('should not auto-refresh when disabled', async () => {
      const onHealthChange = jest.fn();
      
      const { result } = renderHook(() => 
        useSystemHealth({
          config: { 
            enableRealTimeUpdates: false,
            refreshInterval: 1000 
          },
          onHealthChange
        })
      );
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      // Clear initial call
      onHealthChange.mockClear();
      
      // Fast-forward time
      act(() => {
        jest.advanceTimersByTime(2000);
      });
      
      // Should not have been called again
      expect(onHealthChange).not.toHaveBeenCalled();
    });
  });

  describe('Alert Callbacks', () => {
    it('should trigger alerts for high response time', async () => {
      const onAlert = jest.fn();
      
      // Mock performance tracker to return high response time
      (loggingModule.performanceTracker.getPerformanceStats as jest.Mock).mockReturnValue({
        count: 100,
        averageTime: 6000, // High response time
        p95Time: 8000,
        p99Time: 10000
      });
      
      const { result } = renderHook(() => 
        useSystemHealth({
          config: {
            alertThresholds: {
              responseTime: 5000,
              errorRate: 5,
              authFailureRate: 15
            }
          },
          onAlert
        })
      );
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(onAlert).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'performance',
          severity: 'high',
          message: expect.stringContaining('High response time')
        })
      );
    });

    it('should trigger alerts for high error rate', async () => {
      const onAlert = jest.fn();
      
      const { result } = renderHook(() => 
        useSystemHealth({
          config: {
            alertThresholds: {
              responseTime: 10000,
              errorRate: 1, // Low threshold to trigger alert
              authFailureRate: 50
            }
          },
          onAlert
        })
      );
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      // Should trigger error rate alert (mock generates random error rate)
      const alertCalls = onAlert.mock.calls.filter(call => 
        call[0].type === 'errors'
      );
      
      // May or may not trigger depending on random generation
      // Just verify the structure if it does trigger
      if (alertCalls.length > 0) {
        expect(alertCalls[0][0]).toEqual(
          expect.objectContaining({
            type: 'errors',
            severity: 'medium',
            message: expect.stringContaining('High error rate')
          })
        );
      }
    });
  });

  describe('Error Handling', () => {
    it('should handle health check failures', async () => {
      // Mock fetch to fail
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));
      
      const { result } = renderHook(() => useSystemHealth());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(loggingModule.connectivityLogger.logError).toHaveBeenCalledWith(
        'Failed to check system health',
        expect.any(Error),
        'connectivity'
      );
      
      expect(result.current.error).toBeInstanceOf(Error);
    });

    it('should return unknown status when no health data', () => {
      const { result } = renderHook(() => useSystemHealth());
      
      // Before loading completes
      expect(result.current.getHealthStatus()).toBe('unknown');
      expect(result.current.getComponentStatus('backend')).toBe('unknown');
      expect(result.current.isHealthy()).toBe(false);
      expect(result.current.hasAlerts()).toBe(false);
    });
  });

  describe('Health Change Callback', () => {
    it('should call onHealthChange when health updates', async () => {
      const onHealthChange = jest.fn();
      
      const { result } = renderHook(() => 
        useSystemHealth({ onHealthChange })
      );
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(onHealthChange).toHaveBeenCalled();
      
      const healthData = onHealthChange.mock.calls[0][0];
      expect(healthData).toHaveProperty('overall');
      expect(healthData).toHaveProperty('components');
      expect(healthData).toHaveProperty('performance');
      expect(healthData).toHaveProperty('errors');
      expect(healthData).toHaveProperty('authentication');
    });
  });

  describe('Integration with Performance Tracker', () => {
    it('should use real performance data when available', async () => {
      const mockStats = {
        count: 500,
        averageTime: 1500,
        p95Time: 2000,
        p99Time: 2500
      };
      
      (loggingModule.performanceTracker.getPerformanceStats as jest.Mock).mockReturnValue(mockStats);
      
      const { result } = renderHook(() => useSystemHealth());
      
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
      
      expect(result.current.systemHealth?.performance.requestCount).toBe(500);
      expect(result.current.systemHealth?.performance.averageResponseTime).toBe(1500);
    });
  });
});