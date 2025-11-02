/**
 * Tests for HealthDashboard component
 * 
 * Tests health monitoring display, real-time updates,
 * endpoint management, and user interactions.
 */


import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import HealthDashboard from '../HealthDashboard';

// Mock the health monitor
const mockHealthMonitor = {
  getActiveEndpoint: vi.fn(),
  getAllEndpoints: vi.fn(),
  isMonitoringActive: vi.fn(),
  startMonitoring: vi.fn(),
  stopMonitoring: vi.fn(),
  forceFailover: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
};

vi.mock('../../../lib/connection/health-monitor', () => ({
  getHealthMonitor: vi.fn(() => mockHealthMonitor),
  HealthEventType: {
    HEALTH_CHECK_SUCCESS: 'health_check_success',
    HEALTH_CHECK_FAILURE: 'health_check_failure',
    ENDPOINT_FAILOVER: 'endpoint_failover',
    ENDPOINT_RECOVERY: 'endpoint_recovery',
    MONITORING_STARTED: 'monitoring_started',
    MONITORING_STOPPED: 'monitoring_stopped',
  },
}));

// Mock fetch
global.fetch = vi.fn();

// Mock Lucide React icons
vi.mock('lucide-react', () => ({
  RefreshCw: ({ className }: { className?: string }) => <div className={className} data-testid="refresh-icon" />,
  Activity: ({ className }: { className?: string }) => <div className={className} data-testid="activity-icon" />,
  AlertTriangle: ({ className }: { className?: string }) => <div className={className} data-testid="alert-icon" / role="alert">,
  CheckCircle: ({ className }: { className?: string }) => <div className={className} data-testid="check-icon" />,
  XCircle: ({ className }: { className?: string }) => <div className={className} data-testid="x-icon" />,
  Clock: ({ className }: { className?: string }) => <div className={className} data-testid="clock-icon" />,
}));

const mockHealthData = {
  status: 'healthy',
  timestamp: '2024-01-01T12:00:00Z',
  response_time_ms: 150,
  services: {
    database: {
      status: 'healthy',
      response_time_ms: 50,
      last_check: '2024-01-01T12:00:00Z',
    },
    redis: {
      status: 'healthy',
      response_time_ms: 25,
      last_check: '2024-01-01T12:00:00Z',
    },
    ai_providers: {
      status: 'degraded',
      response_time_ms: 200,
      last_check: '2024-01-01T12:00:00Z',
    },
    system_resources: {
      status: 'healthy',
      response_time_ms: 10,
      last_check: '2024-01-01T12:00:00Z',
    },
  },
  summary: {
    healthy_services: 3,
    degraded_services: 1,
    unhealthy_services: 0,
    total_services: 4,
  },
};

const mockEndpoints = [
  {
    url: 'http://localhost:8000',
    priority: 1,
    isActive: true,
    health: {
      isHealthy: true,
      uptime: 99.5,
      averageResponseTime: 120,
    },
  },
  {
    url: 'http://localhost:8001',
    priority: 2,
    isActive: false,
    health: {
      isHealthy: true,
      uptime: 95.0,
      averageResponseTime: 180,
    },
  },
];

describe('HealthDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mock responses
    mockHealthMonitor.getActiveEndpoint.mockReturnValue('http://localhost:8000');
    mockHealthMonitor.getAllEndpoints.mockReturnValue(mockEndpoints);
    mockHealthMonitor.isMonitoringActive.mockReturnValue(false);
    mockHealthMonitor.forceFailover.mockReturnValue(true);
    
    (global.fetch as Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockHealthData),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('should render health dashboard with title', async () => {
      render(<HealthDashboard />);
      
      expect(screen.getByText('Health Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Start Monitoring')).toBeInTheDocument();
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });

    it('should show loading state initially', () => {
      render(<HealthDashboard />);
      
      expect(screen.getByText('Loading health data...')).toBeInTheDocument();
    });

    it('should display health data after loading', async () => {
      render(<HealthDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Healthy')).toBeInTheDocument();
        expect(screen.getByText('150ms')).toBeInTheDocument();
      });
    });

    it('should display service details', async () => {
      render(<HealthDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Database')).toBeInTheDocument();
        expect(screen.getByText('Redis')).toBeInTheDocument();
        expect(screen.getByText('Ai Providers')).toBeInTheDocument();
        expect(screen.getByText('System Resources')).toBeInTheDocument();
      });
    });

    it('should display endpoint information', async () => {
      render(<HealthDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Backend Endpoints')).toBeInTheDocument();
        expect(screen.getByText('http://localhost:8000')).toBeInTheDocument();
        expect(screen.getByText('http://localhost:8001')).toBeInTheDocument();
        expect(screen.getByText('Active')).toBeInTheDocument();
      });
    });
  });

  describe('Health Status Display', () => {
    it('should display correct status colors and icons', async () => {
      render(<HealthDashboard />);
      
      await waitFor(() => {
        // Should show healthy status with check icon
        expect(screen.getAllByTestId('check-icon')).toHaveLength(4); // Overall + 3 healthy services
        
        // Should show degraded status with alert icon for AI providers
        expect(screen.getByTestId('alert-icon')).toBeInTheDocument();
      });
    });

    it('should display service summary correctly', async () => {
      render(<HealthDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument(); // Healthy services
        expect(screen.getByText('1')).toBeInTheDocument(); // Degraded services
        expect(screen.getByText('0')).toBeInTheDocument(); // Unhealthy services
        expect(screen.getByText('4')).toBeInTheDocument(); // Total services
      });
    });

    it('should format response times correctly', async () => {
      render(<HealthDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Response Time: 150ms')).toBeInTheDocument();
        expect(screen.getByText('Response Time: 50ms')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when fetch fails', async () => {
      (global.fetch as Mock).mockRejectedValue(new Error('Network error'));
      
      render(<HealthDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText(/Error: Network error/)).toBeInTheDocument();
      });
    });

    it('should display error when no active endpoint', async () => {
      mockHealthMonitor.getActiveEndpoint.mockReturnValue(null);
      
      render(<HealthDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText(/Error: No active endpoint available/)).toBeInTheDocument();
      });
    });

    it('should display error when API returns error status', async () => {
      (global.fetch as Mock).mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });
      
      render(<HealthDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText(/Error: Health check failed: 500 Internal Server Error/)).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    it('should start monitoring when button is clicked', async () => {
      render(<HealthDashboard />);
      
      const startButton = screen.getByText('Start Monitoring');
      fireEvent.click(startButton);
      
      expect(mockHealthMonitor.startMonitoring).toHaveBeenCalled();
    });

    it('should stop monitoring when button is clicked', async () => {
      mockHealthMonitor.isMonitoringActive.mockReturnValue(true);
      
      render(<HealthDashboard />);
      
      await waitFor(() => {
        const stopButton = screen.getByText('Stop Monitoring');
        fireEvent.click(stopButton);
        
        expect(mockHealthMonitor.stopMonitoring).toHaveBeenCalled();
      });
    });

    it('should refresh data when refresh button is clicked', async () => {
      render(<HealthDashboard />);
      
      await waitFor(() => {
        const refreshButton = screen.getByText('Refresh');
        fireEvent.click(refreshButton);
        
        expect(global.fetch).toHaveBeenCalledTimes(2); // Initial + manual refresh
      });
    });

    it('should force failover when switch button is clicked', async () => {
      render(<HealthDashboard />);
      
      await waitFor(() => {
        const switchButton = screen.getByText('Switch To');
        fireEvent.click(switchButton);
        
        expect(mockHealthMonitor.forceFailover).toHaveBeenCalledWith('http://localhost:8001');
      });
    });
  });

  describe('Event Handling', () => {
    it('should register event listeners on mount', () => {
      render(<HealthDashboard />);
      
      expect(mockHealthMonitor.addEventListener).toHaveBeenCalledTimes(6);
      expect(mockHealthMonitor.addEventListener).toHaveBeenCalledWith(
        'health_check_success',
        expect.any(Function)
      );
      expect(mockHealthMonitor.addEventListener).toHaveBeenCalledWith(
        'endpoint_failover',
        expect.any(Function)
      );
    });

    it('should remove event listeners on unmount', () => {
      const { unmount } = render(<HealthDashboard />);
      
      unmount();
      
      expect(mockHealthMonitor.removeEventListener).toHaveBeenCalledTimes(6);
    });

    it('should handle failover events', async () => {
      let eventHandler: Function;
      mockHealthMonitor.addEventListener.mockImplementation((eventType, handler) => {
        if (eventType === 'endpoint_failover') {
          eventHandler = handler;
        }
      });
      
      render(<HealthDashboard />);
      
      // Simulate failover event
      act(() => {
        eventHandler({
          type: 'endpoint_failover',
          timestamp: new Date(),
          endpoint: 'http://localhost:8001',
          data: { from: 'http://localhost:8000', to: 'http://localhost:8001' },
        });
      });
      
      await waitFor(() => {
        expect(mockHealthMonitor.getAllEndpoints).toHaveBeenCalledTimes(2); // Initial + after event
      });
    });
  });

  describe('Auto Refresh', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should auto-refresh data at specified interval', async () => {
      render(<HealthDashboard autoRefresh={true} refreshInterval={5000} />);
      
      // Initial fetch
      expect(global.fetch).toHaveBeenCalledTimes(1);
      
      // Fast-forward time
      act(() => {
        vi.advanceTimersByTime(5000);
      });
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(2);
      });
    });

    it('should not auto-refresh when disabled', async () => {
      render(<HealthDashboard autoRefresh={false} />);
      
      // Initial fetch
      expect(global.fetch).toHaveBeenCalledTimes(1);
      
      // Fast-forward time
      act(() => {
        vi.advanceTimersByTime(30000);
      });
      
      // Should not have additional fetches
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('Recent Events Display', () => {
    it('should display recent events when available', async () => {
      let eventHandler: Function;
      mockHealthMonitor.addEventListener.mockImplementation((eventType, handler) => {
        if (eventType === 'health_check_success') {
          eventHandler = handler;
        }
      });
      
      render(<HealthDashboard />);
      
      // Simulate health check success event
      act(() => {
        eventHandler({
          type: 'health_check_success',
          timestamp: new Date(),
          endpoint: 'http://localhost:8000',
        });
      });
      
      await waitFor(() => {
        expect(screen.getByText('Recent Events')).toBeInTheDocument();
        expect(screen.getByText('health check success')).toBeInTheDocument();
      });
    });

    it('should limit events to last 10', async () => {
      let eventHandler: Function;
      mockHealthMonitor.addEventListener.mockImplementation((eventType, handler) => {
        if (eventType === 'health_check_success') {
          eventHandler = handler;
        }
      });
      
      render(<HealthDashboard />);
      
      // Simulate 15 events
      for (let i = 0; i < 15; i++) {
        act(() => {
          eventHandler({
            type: 'health_check_success',
            timestamp: new Date(),
            endpoint: 'http://localhost:8000',
          });
        });
      }
      
      await waitFor(() => {
        const eventElements = screen.getAllByText('health check success');
        expect(eventElements).toHaveLength(10); // Should be limited to 10
      });
    });
  });
});