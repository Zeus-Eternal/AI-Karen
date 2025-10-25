/**
 * Integration tests for the complete monitoring system
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RealTimeMonitoringDashboard } from '../RealTimeMonitoringDashboard';
import { useSystemHealth } from '../../../hooks/useSystemHealth';
import * as loggingModule from '../../../lib/logging';

// Mock the logging module
jest.mock('../../../lib/logging', () => ({
  connectivityLogger: {
    logConnectivity: jest.fn(),
    logError: jest.fn(),
    logAuthentication: jest.fn(),
    logPerformance: jest.fn()
  },
  performanceTracker: {
    getPerformanceStats: jest.fn(() => ({
      count: 150,
      averageTime: 1200,
      minTime: 200,
      maxTime: 4000,
      p95Time: 2800,
      p99Time: 3500
    })),
    getRecentMetrics: jest.fn(() => []),
    trackOperation: jest.fn(),
    trackNetworkRequest: jest.fn(() => ({
      start: jest.fn(),
      end: jest.fn(() => ({ duration: 1200, responseTime: 1200 }))
    }))
  },
  correlationTracker: {
    getCurrentCorrelationId: jest.fn(() => 'test-correlation-id'),
    generateCorrelationId: jest.fn(() => 'new-correlation-id'),
    withCorrelationAsync: jest.fn((id, fn) => fn())
  }
}));

// Mock fetch
global.fetch = jest.fn();

// Test component that uses the monitoring system
const TestMonitoringApp: React.FC = () => {
  const [alerts, setAlerts] = React.useState<Array<{ type: string; message: string; severity: string }>>([]);
  const [healthChanges, setHealthChanges] = React.useState(0);

  const handleHealthChange = React.useCallback((health: any) => {
    setHealthChanges(prev => prev + 1);
  }, []);

  const handleAlert = React.useCallback((alert: any) => {
    setAlerts(prev => [...prev, alert]);
  }, []);

  return (
    <div>
      <div data-testid="health-changes">Health Changes: {healthChanges}</div>
      <div data-testid="alerts-count">Alerts: {alerts.length}</div>
      {alerts.map((alert, index) => (
        <div key={index} data-testid={`alert-${index}`}>
          {alert.type}: {alert.message} ({alert.severity})
        </div>
      ))}
      <RealTimeMonitoringDashboard
        config={{
          refreshInterval: 1000,
          enableRealTimeUpdates: true,
          showDetailedMetrics: true,
          alertThresholds: {
            responseTime: 2000,
            errorRate: 3,
            authFailureRate: 10
          }
        }}
        onHealthChange={handleHealthChange}
        onAlert={handleAlert}
      />
    </div>
  );
};

describe('Monitoring System Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    
    // Mock successful health check responses
    (global.fetch as jest.Mock).mockImplementation((url) => {
      if (url.includes('/api/health/backend')) {
        return Promise.resolve({ ok: true, status: 200 });
      }
      if (url.includes('/api/health/database')) {
        return Promise.resolve({ ok: true, status: 200 });
      }
      if (url.includes('/api/health/auth')) {
        return Promise.resolve({ ok: true, status: 200 });
      }
      return Promise.reject(new Error('Not found'));
    });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('End-to-End Monitoring Flow', () => {
    it('should render complete monitoring dashboard with all components', async () => {
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();
      });
      
      // Check all major components are rendered
      expect(screen.getByText('Backend API')).toBeInTheDocument();
      expect(screen.getByText('Database')).toBeInTheDocument();
      expect(screen.getByText('Authentication')).toBeInTheDocument();
      expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
      expect(screen.getByText('Error Metrics')).toBeInTheDocument();
      expect(screen.getByText('Authentication Metrics')).toBeInTheDocument();
    });

    it('should track health changes over time', async () => {
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByTestId('health-changes')).toHaveTextContent('Health Changes: 1');
      });
      
      // Trigger manual refresh
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);
      
      await waitFor(() => {
        expect(screen.getByTestId('health-changes')).toHaveTextContent('Health Changes: 2');
      });
    });

    it('should generate alerts based on thresholds', async () => {
      // Mock high response time to trigger alert
      (loggingModule.performanceTracker.getPerformanceStats as jest.Mock).mockReturnValue({
        count: 100,
        averageTime: 3000, // Above threshold of 2000
        p95Time: 4000,
        p99Time: 5000
      });
      
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByTestId('alerts-count')).toHaveTextContent('Alerts: 1');
      });
      
      expect(screen.getByTestId('alert-0')).toHaveTextContent('performance: High response time');
    });

    it('should handle real-time updates', async () => {
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();
      });
      
      const initialHealthChanges = screen.getByTestId('health-changes').textContent;
      
      // Fast-forward time to trigger auto-refresh
      jest.advanceTimersByTime(1000);
      
      await waitFor(() => {
        const currentHealthChanges = screen.getByTestId('health-changes').textContent;
        expect(currentHealthChanges).not.toBe(initialHealthChanges);
      });
    });
  });

  describe('Logging Integration', () => {
    it('should log health check activities', async () => {
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();
      });
      
      expect(loggingModule.connectivityLogger.logConnectivity).toHaveBeenCalledWith(
        'debug',
        'System health check completed',
        expect.objectContaining({
          url: '/api/health',
          method: 'GET',
          statusCode: 200
        })
      );
    });

    it('should log errors when health checks fail', async () => {
      // Mock fetch to fail
      (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));
      
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();
      });
      
      expect(loggingModule.connectivityLogger.logError).toHaveBeenCalledWith(
        'Failed to check system health',
        expect.any(Error),
        'connectivity'
      );
    });
  });

  describe('Performance Tracking Integration', () => {
    it('should integrate with performance tracker for real metrics', async () => {
      const mockStats = {
        count: 250,
        averageTime: 1800,
        p95Time: 2500,
        p99Time: 3200
      };
      
      (loggingModule.performanceTracker.getPerformanceStats as jest.Mock).mockReturnValue(mockStats);
      
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
      });
      
      // Should display the real performance data
      expect(screen.getByText('1.80s')).toBeInTheDocument(); // Average time
      expect(screen.getByText('2.50s')).toBeInTheDocument(); // P95 time
      expect(screen.getByText('3.20s')).toBeInTheDocument(); // P99 time
    });

    it('should track dashboard rendering performance', async () => {
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();
      });
      
      // Performance tracking should be called for various operations
      expect(loggingModule.performanceTracker.getPerformanceStats).toHaveBeenCalled();
    });
  });

  describe('Error Handling and Recovery', () => {
    it('should handle partial health check failures gracefully', async () => {
      // Mock some health checks to fail
      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url.includes('/api/health/backend')) {
          return Promise.resolve({ ok: true, status: 200 });
        }
        if (url.includes('/api/health/database')) {
          return Promise.reject(new Error('Database connection failed'));
        }
        if (url.includes('/api/health/auth')) {
          return Promise.resolve({ ok: false, status: 503 });
        }
        return Promise.reject(new Error('Not found'));
      });
      
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();
      });
      
      // Should still render the dashboard
      expect(screen.getByText('Backend API')).toBeInTheDocument();
      expect(screen.getByText('Database')).toBeInTheDocument();
      expect(screen.getByText('Authentication')).toBeInTheDocument();
    });

    it('should recover from temporary failures', async () => {
      let callCount = 0;
      
      // Mock fetch to fail first, then succeed
      (global.fetch as jest.Mock).mockImplementation((url) => {
        callCount++;
        if (callCount <= 3) {
          return Promise.reject(new Error('Temporary failure'));
        }
        return Promise.resolve({ ok: true, status: 200 });
      });
      
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();
      });
      
      // Trigger refresh to test recovery
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();
      });
      
      // Should have logged both failures and recovery
      expect(loggingModule.connectivityLogger.logError).toHaveBeenCalled();
    });
  });

  describe('User Interactions', () => {
    it('should handle auto-refresh toggle', async () => {
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByText('Auto-refresh ON')).toBeInTheDocument();
      });
      
      const autoRefreshButton = screen.getByText('Auto-refresh ON');
      fireEvent.click(autoRefreshButton);
      
      expect(screen.getByText('Auto-refresh OFF')).toBeInTheDocument();
      
      // Should not auto-refresh when disabled
      const initialHealthChanges = screen.getByTestId('health-changes').textContent;
      
      jest.advanceTimersByTime(2000);
      
      await waitFor(() => {
        const currentHealthChanges = screen.getByTestId('health-changes').textContent;
        expect(currentHealthChanges).toBe(initialHealthChanges);
      });
    });

    it('should handle manual refresh', async () => {
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByText('Refresh')).toBeInTheDocument();
      });
      
      const initialHealthChanges = screen.getByTestId('health-changes').textContent;
      
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);
      
      await waitFor(() => {
        const currentHealthChanges = screen.getByTestId('health-changes').textContent;
        expect(currentHealthChanges).not.toBe(initialHealthChanges);
      });
    });
  });

  describe('Responsive Behavior', () => {
    it('should adapt to different screen sizes', async () => {
      // Mock window.innerWidth for responsive testing
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });
      
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();
      });
      
      // Should render all components regardless of screen size
      expect(screen.getByText('Backend API')).toBeInTheDocument();
      expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', async () => {
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /System Health Dashboard/i })).toBeInTheDocument();
      });
      
      expect(screen.getByRole('button', { name: /Refresh/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Auto-refresh/i })).toBeInTheDocument();
    });

    it('should support keyboard navigation', async () => {
      render(<TestMonitoringApp />);
      
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();
      });
      
      const refreshButton = screen.getByRole('button', { name: /Refresh/i });
      const autoRefreshButton = screen.getByRole('button', { name: /Auto-refresh/i });
      
      expect(refreshButton).toBeInTheDocument();
      expect(autoRefreshButton).toBeInTheDocument();
      
      // Both buttons should be focusable
      refreshButton.focus();
      expect(document.activeElement).toBe(refreshButton);
      
      autoRefreshButton.focus();
      expect(document.activeElement).toBe(autoRefreshButton);
    });
  });
});