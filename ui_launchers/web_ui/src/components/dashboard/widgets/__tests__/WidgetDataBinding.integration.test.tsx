import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import MetricWidget from '../MetricWidget';
import StatusWidget from '../StatusWidget';
import ChartWidget from '../ChartWidget';
import LogWidget from '../LogWidget';
import type { WidgetConfig, MetricData, StatusData, ChartData, LogData } from '@/types/dashboard';

// Mock AG Charts
vi.mock('ag-charts-react', () => ({
  AgCharts: ({ options }: any) => (
    <div data-testid="ag-charts" data-options={JSON.stringify(options)}>
      Mock Chart
    </div>
  ),
}));

// Mock react-window
vi.mock('react-window', () => ({
  FixedSizeList: ({ children, itemData, itemCount }: any) => (
    <div data-testid="virtual-list">
      {Array.from({ length: Math.min(itemCount, 3) }, (_, index) => (
        <div key={index}>
          {children({ index, style: {}, data: itemData })}
        </div>
      ))}
    </div>
  ),
}));

// Mock the WidgetBase component
vi.mock('../../WidgetBase', () => ({
  WidgetBase: ({ children, loading, error, ...props }: any) => (
    <div data-testid="widget-base" data-loading={loading} data-error={error} {...props}>
      {loading ? <div>Loading...</div> : error ? <div>Error: {error}</div> : children}
    </div>
  ),
}));

// Mock WebSocket for real-time updates
class MockWebSocket {
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  
  constructor(public url: string) {
    setTimeout(() => {
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }
  
  send(data: string) {
    // Mock send
  }
  
  close() {
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }
  
  // Helper method to simulate receiving messages
  simulateMessage(data: any) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }));
    }
  }
}

// Replace global WebSocket
(global as any).WebSocket = MockWebSocket;

describe('Widget Data Binding Integration Tests', () => {
  let queryClient: QueryClient;
  let mockWebSocket: MockWebSocket;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    
    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  const renderWithQueryClient = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    );
  };

  describe('MetricWidget Data Binding', () => {
    const metricConfig: WidgetConfig = {
      id: 'metric-1',
      type: 'metric',
      title: 'CPU Usage',
      size: 'small',
      position: { x: 0, y: 0, w: 1, h: 1 },
      config: {
        dataSource: 'system-metrics',
        metric: 'cpu_usage',
        format: 'percentage',
        thresholds: { warning: 70, critical: 90 },
      },
      refreshInterval: 1000,
      enabled: true,
    };

    it('handles loading state correctly', () => {
      const loadingData = {
        id: 'metric-1',
        data: {} as MetricData,
        loading: true,
        lastUpdated: new Date(),
      };

      renderWithQueryClient(
        <MetricWidget config={metricConfig} data={loadingData} />
      );

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('handles error state correctly', () => {
      const errorData = {
        id: 'metric-1',
        data: {} as MetricData,
        loading: false,
        error: 'Failed to fetch metric data',
        lastUpdated: new Date(),
      };

      renderWithQueryClient(
        <MetricWidget config={metricConfig} data={errorData} />
      );

      expect(screen.getByText('Error: Failed to fetch metric data')).toBeInTheDocument();
    });

    it('updates data in real-time', async () => {
      let currentData = {
        id: 'metric-1',
        data: {
          value: 45,
          label: 'CPU Usage',
          format: 'percentage' as const,
        },
        loading: false,
        lastUpdated: new Date(),
      };

      const { rerender } = renderWithQueryClient(
        <MetricWidget config={metricConfig} data={currentData} />
      );

      expect(screen.getByText('45.0%')).toBeInTheDocument();

      // Simulate real-time update
      currentData = {
        ...currentData,
        data: {
          ...currentData.data,
          value: 75,
        },
        lastUpdated: new Date(),
      };

      rerender(
        <QueryClientProvider client={queryClient}>
          <MetricWidget config={metricConfig} data={currentData} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('75.0%')).toBeInTheDocument();
      });
    });

    it('triggers threshold alerts on data changes', async () => {
      let currentData = {
        id: 'metric-1',
        data: {
          value: 65,
          label: 'CPU Usage',
          format: 'percentage' as const,
          threshold: { warning: 70, critical: 90 },
        },
        loading: false,
        lastUpdated: new Date(),
      };

      const { rerender } = renderWithQueryClient(
        <MetricWidget config={metricConfig} data={currentData} />
      );

      expect(screen.queryByText('Warning')).not.toBeInTheDocument();

      // Update to warning threshold
      currentData = {
        ...currentData,
        data: {
          ...currentData.data,
          value: 75,
        },
      };

      rerender(
        <QueryClientProvider client={queryClient}>
          <MetricWidget config={metricConfig} data={currentData} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Warning')).toBeInTheDocument();
      });
    });
  });

  describe('StatusWidget Data Binding', () => {
    const statusConfig: WidgetConfig = {
      id: 'status-1',
      type: 'status',
      title: 'API Status',
      size: 'small',
      position: { x: 0, y: 0, w: 1, h: 1 },
      config: {
        service: 'api-server',
        checkInterval: 1000,
      },
      refreshInterval: 1000,
      enabled: true,
    };

    it('updates status changes in real-time', async () => {
      let currentData = {
        id: 'status-1',
        data: {
          status: 'healthy' as const,
          message: 'All systems operational',
          lastCheck: new Date(),
        },
        loading: false,
        lastUpdated: new Date(),
      };

      const { rerender } = renderWithQueryClient(
        <StatusWidget config={statusConfig} data={currentData} />
      );

      expect(screen.getByText('Healthy')).toBeInTheDocument();
      expect(screen.getByText('All systems operational')).toBeInTheDocument();

      // Simulate status change to warning
      currentData = {
        ...currentData,
        data: {
          ...currentData.data,
          status: 'warning',
          message: 'High response time detected',
        },
      };

      rerender(
        <QueryClientProvider client={queryClient}>
          <StatusWidget config={statusConfig} data={currentData} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Warning')).toBeInTheDocument();
        expect(screen.getByText('High response time detected')).toBeInTheDocument();
      });
    });
  });

  describe('ChartWidget Data Binding', () => {
    const chartConfig: WidgetConfig = {
      id: 'chart-1',
      type: 'chart',
      title: 'Performance Chart',
      size: 'medium',
      position: { x: 0, y: 0, w: 2, h: 1 },
      config: {
        dataSource: 'metrics-api',
        chartType: 'line',
        series: ['cpu', 'memory'],
      },
      refreshInterval: 1000,
      enabled: true,
    };

    it('updates chart data in real-time', async () => {
      let currentData = {
        id: 'chart-1',
        data: {
          series: [
            {
              name: 'cpu',
              data: [
                { x: '10:00', y: 45 },
                { x: '10:01', y: 50 },
              ],
            },
          ],
          xAxis: { type: 'category' as const },
          yAxis: { label: 'Usage (%)' },
        },
        loading: false,
        lastUpdated: new Date(),
      };

      const { rerender } = renderWithQueryClient(
        <ChartWidget config={chartConfig} data={currentData} />
      );

      expect(screen.getByTestId('ag-charts')).toBeInTheDocument();

      // Add new data point
      currentData = {
        ...currentData,
        data: {
          ...currentData.data,
          series: [
            {
              name: 'cpu',
              data: [
                { x: '10:00', y: 45 },
                { x: '10:01', y: 50 },
                { x: '10:02', y: 55 },
              ],
            },
          ],
        },
      };

      rerender(
        <QueryClientProvider client={queryClient}>
          <ChartWidget config={chartConfig} data={currentData} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        const chartElement = screen.getByTestId('ag-charts');
        const optionsData = JSON.parse(chartElement.getAttribute('data-options') || '{}');
        expect(optionsData.data).toHaveLength(3);
      });
    });
  });

  describe('LogWidget Data Binding', () => {
    const logConfig: WidgetConfig = {
      id: 'log-1',
      type: 'log',
      title: 'Application Logs',
      size: 'large',
      position: { x: 0, y: 0, w: 2, h: 2 },
      config: {
        logSource: 'application',
        levels: ['info', 'warn', 'error'],
        maxEntries: 100,
      },
      refreshInterval: 1000,
      enabled: true,
    };

    it('streams new log entries in real-time', async () => {
      let currentData = {
        id: 'log-1',
        data: {
          entries: [
            {
              id: '1',
              timestamp: new Date('2024-01-01T10:00:00Z'),
              level: 'info' as const,
              message: 'Application started',
              source: 'app',
            },
          ],
          totalCount: 1,
          hasMore: false,
        },
        loading: false,
        lastUpdated: new Date(),
      };

      const { rerender } = renderWithQueryClient(
        <LogWidget config={logConfig} data={currentData} />
      );

      expect(screen.getByText('Application started')).toBeInTheDocument();
      expect(screen.getByText('1 of 1 entries')).toBeInTheDocument();

      // Add new log entry
      currentData = {
        ...currentData,
        data: {
          entries: [
            ...currentData.data.entries,
            {
              id: '2',
              timestamp: new Date('2024-01-01T10:01:00Z'),
              level: 'warn' as const,
              message: 'High memory usage',
              source: 'monitor',
            },
          ],
          totalCount: 2,
          hasMore: false,
        },
      };

      rerender(
        <QueryClientProvider client={queryClient}>
          <LogWidget config={logConfig} data={currentData} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('High memory usage')).toBeInTheDocument();
        expect(screen.getByText('2 of 2 entries')).toBeInTheDocument();
      });
    });
  });

  describe('WebSocket Real-time Updates', () => {
    it('handles WebSocket connection and data updates', async () => {
      // This would be a more complex test in a real implementation
      // For now, we'll test the basic WebSocket mock functionality
      
      const ws = new MockWebSocket('ws://localhost:8080/widgets');
      let receivedData: any = null;
      
      ws.onmessage = (event) => {
        receivedData = JSON.parse(event.data);
      };

      await waitFor(() => {
        expect(ws.onopen).toBeDefined();
      });

      // Simulate receiving widget data update
      act(() => {
        ws.simulateMessage({
          type: 'widget_update',
          widgetId: 'metric-1',
          data: {
            value: 85,
            label: 'CPU Usage',
            format: 'percentage',
          },
        });
      });

      await waitFor(() => {
        expect(receivedData).toEqual({
          type: 'widget_update',
          widgetId: 'metric-1',
          data: {
            value: 85,
            label: 'CPU Usage',
            format: 'percentage',
          },
        });
      });
    });
  });

  describe('Error Recovery', () => {
    it('recovers from network errors', async () => {
      const metricConfig: WidgetConfig = {
        id: 'metric-1',
        type: 'metric',
        title: 'CPU Usage',
        size: 'small',
        position: { x: 0, y: 0, w: 1, h: 1 },
        config: {},
        refreshInterval: 1000,
        enabled: true,
      };

      let hasError = true;
      let currentData = {
        id: 'metric-1',
        data: {} as MetricData,
        loading: false,
        error: hasError ? 'Network error' : undefined,
        lastUpdated: new Date(),
      };

      const { rerender } = renderWithQueryClient(
        <MetricWidget config={metricConfig} data={currentData} />
      );

      expect(screen.getByText('Error: Network error')).toBeInTheDocument();

      // Simulate error recovery
      hasError = false;
      currentData = {
        id: 'metric-1',
        data: {
          value: 45,
          label: 'CPU Usage',
          format: 'percentage' as const,
        },
        loading: false,
        error: undefined,
        lastUpdated: new Date(),
      };

      rerender(
        <QueryClientProvider client={queryClient}>
          <MetricWidget config={metricConfig} data={currentData} />
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('45.0%')).toBeInTheDocument();
        expect(screen.queryByText('Error: Network error')).not.toBeInTheDocument();
      });
    });
  });
});