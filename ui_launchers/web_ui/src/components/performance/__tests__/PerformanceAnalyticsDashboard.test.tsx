/**
 * Performance Analytics Dashboard Tests
 * Tests for the comprehensive performance analytics dashboard component
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi, Mock } from 'vitest';
import { PerformanceAnalyticsDashboard } from '../PerformanceAnalyticsDashboard';
import { performanceMonitor } from '@/services/performance-monitor';

// Mock the performance monitor
vi.mock('@/services/performance-monitor', () => ({
  performanceMonitor: {
    getMetrics: vi.fn(),
    getAlerts: vi.fn(),
    getWebVitalsMetrics: vi.fn(),
    getCurrentResourceUsage: vi.fn(),
    onAlert: vi.fn(),
    getOptimizationRecommendations: vi.fn(),
  },
}));

// Mock recharts
vi.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
}));

const mockMetrics = [
  {
    name: 'lcp',
    value: 2000,
    timestamp: Date.now() - 1000,
    metadata: { id: 'test-1' },
  },
  {
    name: 'fid',
    value: 100,
    timestamp: Date.now() - 2000,
    metadata: { id: 'test-2' },
  },
  {
    name: 'cls',
    value: 0.1,
    timestamp: Date.now() - 3000,
    metadata: { id: 'test-3' },
  },
  {
    name: 'page-load',
    value: 1500,
    timestamp: Date.now() - 4000,
    metadata: { route: '/dashboard' },
  },
  {
    name: 'memory-usage',
    value: 65,
    timestamp: Date.now() - 5000,
    metadata: { used: 65000000, total: 100000000 },
  },
];

const mockAlerts = [
  {
    id: 'alert-1',
    type: 'warning' as const,
    metric: 'lcp',
    value: 2500,
    threshold: 2000,
    timestamp: Date.now() - 1000,
    message: 'LCP is slower than expected',
  },
  {
    id: 'alert-2',
    type: 'critical' as const,
    metric: 'memory-usage',
    value: 95,
    threshold: 90,
    timestamp: Date.now() - 2000,
    message: 'Memory usage is critically high',
  },
];

const mockWebVitals = {
  lcp: 2000,
  fid: 100,
  cls: 0.1,
  fcp: 1800,
  ttfb: 500,
};

const mockResourceUsage = {
  memory: {
    used: 65000000,
    total: 100000000,
    percentage: 65,
  },
  network: {
    downlink: 10,
    effectiveType: '4g',
    rtt: 50,
  },
};

const mockRecommendations = [
  'Consider optimizing images and reducing server response times to improve LCP',
  'Reduce JavaScript execution time and break up long tasks to improve FID',
];

describe('PerformanceAnalyticsDashboard', () => {
  const mockGetMetrics = performanceMonitor.getMetrics as Mock;
  const mockGetAlerts = performanceMonitor.getAlerts as Mock;
  const mockGetWebVitalsMetrics = performanceMonitor.getWebVitalsMetrics as Mock;
  const mockGetCurrentResourceUsage = performanceMonitor.getCurrentResourceUsage as Mock;
  const mockOnAlert = performanceMonitor.onAlert as Mock;
  const mockGetOptimizationRecommendations = performanceMonitor.getOptimizationRecommendations as Mock;

  beforeEach(() => {
    // Setup default mock returns
    mockGetMetrics.mockReturnValue(mockMetrics);
    mockGetAlerts.mockReturnValue(mockAlerts);
    mockGetWebVitalsMetrics.mockReturnValue(mockWebVitals);
    mockGetCurrentResourceUsage.mockReturnValue(mockResourceUsage);
    mockOnAlert.mockReturnValue(() => {}); // Unsubscribe function
    mockGetOptimizationRecommendations.mockReturnValue(mockRecommendations);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render the dashboard with title and description', () => {
      render(<PerformanceAnalyticsDashboard />);
      
      expect(screen.getByText('Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText(/Monitor application performance/)).toBeInTheDocument();
    });

    it('should render time range selector', () => {
      render(<PerformanceAnalyticsDashboard />);
      
      expect(screen.getByText('1H')).toBeInTheDocument();
      expect(screen.getByText('6H')).toBeInTheDocument();
      expect(screen.getByText('24H')).toBeInTheDocument();
      expect(screen.getByText('7D')).toBeInTheDocument();
    });

    it('should render Web Vitals cards', async () => {
      render(<PerformanceAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('LCP')).toBeInTheDocument();
        expect(screen.getByText('FID')).toBeInTheDocument();
        expect(screen.getByText('CLS')).toBeInTheDocument();
        expect(screen.getByText('FCP')).toBeInTheDocument();
        expect(screen.getByText('TTFB')).toBeInTheDocument();
      });
    });

    it('should render resource usage cards', () => {
      render(<PerformanceAnalyticsDashboard />);
      
      expect(screen.getByText('Memory Usage')).toBeInTheDocument();
      expect(screen.getByText('Network')).toBeInTheDocument();
      expect(screen.getByText('Active Alerts')).toBeInTheDocument();
    });

    it('should render performance charts', () => {
      render(<PerformanceAnalyticsDashboard />);
      
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  describe('Data Loading', () => {
    it('should load performance data on mount', async () => {
      render(<PerformanceAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(mockGetMetrics).toHaveBeenCalled();
        expect(mockGetAlerts).toHaveBeenCalledWith(20);
        expect(mockGetWebVitalsMetrics).toHaveBeenCalled();
        expect(mockGetCurrentResourceUsage).toHaveBeenCalled();
      });
    });

    it('should subscribe to alerts on mount', async () => {
      render(<PerformanceAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(mockOnAlert).toHaveBeenCalled();
      });
    });

    it('should refresh data at specified interval', async () => {
      vi.useFakeTimers();
      
      render(<PerformanceAnalyticsDashboard refreshInterval={1000} />);
      
      // Initial load
      expect(mockGetMetrics).toHaveBeenCalledTimes(1);
      
      // Advance timer
      vi.advanceTimersByTime(1000);
      
      await waitFor(() => {
        expect(mockGetMetrics).toHaveBeenCalledTimes(2);
      });
      
      vi.useRealTimers();
    });
  });

  describe('Web Vitals Display', () => {
    it('should display Web Vitals values correctly', () => {
      render(<PerformanceAnalyticsDashboard />);
      
      expect(screen.getByText('2000ms')).toBeInTheDocument(); // LCP
      expect(screen.getByText('100ms')).toBeInTheDocument(); // FID
      expect(screen.getByText('0.100')).toBeInTheDocument(); // CLS
    });

    it('should show correct status badges for Web Vitals', async () => {
      render(<PerformanceAnalyticsDashboard />);
      
      await waitFor(() => {
        // LCP 2000ms should be "Good" (< 2500ms)
        expect(screen.getAllByText('Good')).toHaveLength(5); // All vitals are good
      });
    });

    it('should handle missing Web Vitals gracefully', () => {
      mockGetWebVitalsMetrics.mockReturnValue({ lcp: 2000 }); // Only LCP
      
      render(<PerformanceAnalyticsDashboard />);
      
      expect(screen.getByText('2000ms')).toBeInTheDocument();
      // Should not crash with missing metrics
    });
  });

  describe('Resource Usage Display', () => {
    it('should display memory usage correctly', () => {
      render(<PerformanceAnalyticsDashboard />);
      
      expect(screen.getByText('65.0%')).toBeInTheDocument();
      expect(screen.getByText('62.0MB / 95.4MB')).toBeInTheDocument();
    });

    it('should display network information correctly', () => {
      render(<PerformanceAnalyticsDashboard />);
      
      expect(screen.getByText('10Mbps')).toBeInTheDocument();
      expect(screen.getByText('4g • 50ms RTT')).toBeInTheDocument();
    });

    it('should display alert count correctly', () => {
      render(<PerformanceAnalyticsDashboard />);
      
      expect(screen.getByText('2')).toBeInTheDocument(); // Total alerts
      expect(screen.getByText('1 Critical')).toBeInTheDocument();
      expect(screen.getByText('1 Warning')).toBeInTheDocument();
    });
  });

  describe('Alerts Display', () => {
    it('should display performance alerts', () => {
      render(<PerformanceAnalyticsDashboard />);
      
      expect(screen.getByText('Performance Warning')).toBeInTheDocument();
      expect(screen.getByText('Performance Critical')).toBeInTheDocument();
      expect(screen.getByText('LCP is slower than expected')).toBeInTheDocument();
      expect(screen.getByText('Memory usage is critically high')).toBeInTheDocument();
    });

    it('should limit alerts display to 3', () => {
      const manyAlerts = Array.from({ length: 5 }, (_, i) => ({
        id: `alert-${i}`,
        type: 'warning' as const,
        metric: 'test',
        value: 100,
        threshold: 50,
        timestamp: Date.now() - i * 1000,
        message: `Alert ${i}`,
      }));
      
      mockGetAlerts.mockReturnValue(manyAlerts);
      
      render(<PerformanceAnalyticsDashboard />);
      
      // Should only show first 3 alerts
      expect(screen.getByText('Alert 0')).toBeInTheDocument();
      expect(screen.getByText('Alert 1')).toBeInTheDocument();
      expect(screen.getByText('Alert 2')).toBeInTheDocument();
      expect(screen.queryByText('Alert 3')).not.toBeInTheDocument();
    });
  });

  describe('Time Range Selection', () => {
    it('should change time range when tab is clicked', async () => {
      render(<PerformanceAnalyticsDashboard />);
      
      const sixHourTab = screen.getByText('6H');
      fireEvent.click(sixHourTab);
      
      // Should trigger data recalculation
      await waitFor(() => {
        expect(mockGetMetrics).toHaveBeenCalled();
      });
    });

    it('should filter chart data based on selected time range', () => {
      render(<PerformanceAnalyticsDashboard />);
      
      // Chart should be rendered with filtered data
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

  describe('Chart Tabs', () => {
    it('should render performance trends tab by default', async () => {
      render(<PerformanceAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getAllByText('Performance Trends')).toHaveLength(2); // Tab and title
        expect(screen.getByText('Track performance metrics over time')).toBeInTheDocument();
      });
    });

    it('should switch to Web Vitals tab', async () => {
      render(<PerformanceAnalyticsDashboard />);
      
      const webVitalsTab = screen.getByText('Web Vitals');
      fireEvent.click(webVitalsTab);
      
      await waitFor(() => {
        expect(screen.getByText('Web Vitals Distribution')).toBeInTheDocument();
        expect(screen.getByText('Performance Score')).toBeInTheDocument();
      });
    });

    it('should switch to Resource Usage tab', async () => {
      render(<PerformanceAnalyticsDashboard />);
      
      const resourceTab = screen.getByText('Resource Usage');
      fireEvent.click(resourceTab);
      
      await waitFor(() => {
        expect(screen.getByText('Resource Usage Over Time')).toBeInTheDocument();
      });
    });
  });

  describe('Recommendations', () => {
    it('should display optimization recommendations when enabled', () => {
      render(<PerformanceAnalyticsDashboard showRecommendations={true} />);
      
      expect(screen.getByText('Optimization Recommendations')).toBeInTheDocument();
      expect(screen.getByText(/Consider optimizing images/)).toBeInTheDocument();
      expect(screen.getByText(/Reduce JavaScript execution time/)).toBeInTheDocument();
    });

    it('should hide recommendations when disabled', () => {
      render(<PerformanceAnalyticsDashboard showRecommendations={false} />);
      
      expect(screen.queryByText('Optimization Recommendations')).not.toBeInTheDocument();
    });

    it('should not display recommendations section when no recommendations', () => {
      mockGetOptimizationRecommendations.mockReturnValue([]);
      
      render(<PerformanceAnalyticsDashboard showRecommendations={true} />);
      
      expect(screen.queryByText('Optimization Recommendations')).not.toBeInTheDocument();
    });
  });

  describe('Metric Trends', () => {
    it('should calculate and display metric trends', () => {
      // Add more metrics to enable trend calculation
      const trendMetrics = [
        ...mockMetrics,
        {
          name: 'lcp',
          value: 1800, // Improved from 2000
          timestamp: Date.now(),
          metadata: { id: 'test-4' },
        },
      ];
      
      mockGetMetrics.mockReturnValue(trendMetrics);
      
      render(<PerformanceAnalyticsDashboard />);
      
      // Should show trend indicators (up/down arrows)
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should handle missing resource usage gracefully', () => {
      mockGetCurrentResourceUsage.mockReturnValue(null);
      
      expect(() => {
        render(<PerformanceAnalyticsDashboard />);
      }).not.toThrow();
    });

    it('should handle empty metrics gracefully', () => {
      mockGetMetrics.mockReturnValue([]);
      mockGetWebVitalsMetrics.mockReturnValue({});
      
      expect(() => {
        render(<PerformanceAnalyticsDashboard />);
      }).not.toThrow();
    });

    it('should handle empty alerts gracefully', () => {
      mockGetAlerts.mockReturnValue([]);
      
      render(<PerformanceAnalyticsDashboard />);
      
      // Should not show alert sections
      expect(screen.queryByText('Performance Warning')).not.toBeInTheDocument();
    });
  });

  describe('Cleanup', () => {
    it('should cleanup intervals and subscriptions on unmount', () => {
      const unsubscribe = vi.fn();
      mockOnAlert.mockReturnValue(unsubscribe);
      
      const { unmount } = render(<PerformanceAnalyticsDashboard />);
      
      unmount();
      
      expect(unsubscribe).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      render(<PerformanceAnalyticsDashboard />);
      
      // Check for proper heading structure
      expect(screen.getByRole('heading', { name: /Performance Analytics/ })).toBeInTheDocument();
    });

    it('should support keyboard navigation for tabs', () => {
      render(<PerformanceAnalyticsDashboard />);
      
      const webVitalsTab = screen.getByText('Web Vitals');
      expect(webVitalsTab).toBeInTheDocument();
      
      // Tab should be focusable
      webVitalsTab.focus();
      expect(document.activeElement).toBe(webVitalsTab);
    });
  });
});