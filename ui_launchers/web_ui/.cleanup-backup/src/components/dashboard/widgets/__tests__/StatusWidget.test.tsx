import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import StatusWidget from '../StatusWidget';
import type { WidgetConfig, StatusData } from '@/types/dashboard';

// Mock the WidgetBase component
vi.mock('../../WidgetBase', () => ({
  WidgetBase: ({ children, ...props }: any) => (
    <div data-testid="widget-base" {...props}>
      {children}
    </div>
  ),
}));

const mockConfig: WidgetConfig = {
  id: 'test-status-widget',
  type: 'status',
  title: 'API Server Status',
  size: 'small',
  position: { x: 0, y: 0, w: 1, h: 1 },
  config: {
    service: 'api-server',
    endpoint: 'https://api.example.com/health',
    checkInterval: 30000,
    showDetails: true,
    showHistory: true,
  },
  refreshInterval: 30000,
  enabled: true,
};

const mockStatusData: StatusData = {
  status: 'healthy',
  message: 'All systems operational',
  lastCheck: new Date('2024-01-01T12:00:00Z'),
  details: {
    uptime: 0.999,
    cpu: 45,
    memory: 2048,
    connections: 150,
    latency: 25,
  },
};

const mockWidgetData = {
  id: 'test-status-widget',
  data: mockStatusData,
  loading: false,
  lastUpdated: new Date(),
};

describe('StatusWidget', () => {
  const mockProps = {
    config: mockConfig,
    data: mockWidgetData,
    onConfigChange: vi.fn(),
    onRefresh: vi.fn(),
    onRemove: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders status widget with healthy status', () => {
    render(<StatusWidget {...mockProps} />);
    
    expect(screen.getByText('Healthy')).toBeInTheDocument();
    expect(screen.getByText('All systems operational')).toBeInTheDocument();
    expect(screen.getByText(/Last checked:/)).toBeInTheDocument();
  });

  it('displays warning status correctly', () => {
    const warningData = {
      ...mockWidgetData,
      data: {
        ...mockStatusData,
        status: 'warning' as const,
        message: 'High CPU usage detected',
      },
    };

    render(<StatusWidget {...mockProps} data={warningData} />);
    
    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(screen.getByText('High CPU usage detected')).toBeInTheDocument();
  });

  it('displays critical status correctly', () => {
    const criticalData = {
      ...mockWidgetData,
      data: {
        ...mockStatusData,
        status: 'critical' as const,
        message: 'Service unavailable',
      },
    };

    render(<StatusWidget {...mockProps} data={criticalData} />);
    
    expect(screen.getByText('Critical')).toBeInTheDocument();
    expect(screen.getByText('Service unavailable')).toBeInTheDocument();
  });

  it('displays unknown status correctly', () => {
    const unknownData = {
      ...mockWidgetData,
      data: {
        ...mockStatusData,
        status: 'unknown' as const,
        message: 'Status check failed',
      },
    };

    render(<StatusWidget {...mockProps} data={unknownData} />);
    
    expect(screen.getByText('Unknown')).toBeInTheDocument();
    expect(screen.getByText('Status check failed')).toBeInTheDocument();
  });

  it('displays status details when available', () => {
    render(<StatusWidget {...mockProps} />);
    
    expect(screen.getByText('Details')).toBeInTheDocument();
    expect(screen.getByText('Uptime')).toBeInTheDocument();
    expect(screen.getByText('Cpu')).toBeInTheDocument();
    expect(screen.getByText('Memory')).toBeInTheDocument();
    expect(screen.getByText('Connections')).toBeInTheDocument();
  });

  it('formats detail values correctly', () => {
    render(<StatusWidget {...mockProps} />);
    
    // Uptime should be formatted as percentage
    expect(screen.getByText('99.9%')).toBeInTheDocument();
    // CPU should be formatted as number
    expect(screen.getByText('45')).toBeInTheDocument();
    // Memory should be formatted with K suffix
    expect(screen.getByText('2.0K')).toBeInTheDocument();
    // Connections should be formatted as number
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('limits displayed details to 4 items', () => {
    const manyDetailsData = {
      ...mockWidgetData,
      data: {
        ...mockStatusData,
        details: {
          uptime: 0.999,
          cpu: 45,
          memory: 2048,
          connections: 150,
          latency: 25,
          errors: 0,
          requests: 1000,
        },
      },
    };

    render(<StatusWidget {...mockProps} data={manyDetailsData} />);
    
    // Should show "+3 more details" indicator
    expect(screen.getByText('+3 more details')).toBeInTheDocument();
  });

  it('renders without details when details are not available', () => {
    const noDetailsData = {
      ...mockWidgetData,
      data: {
        ...mockStatusData,
        details: undefined,
      },
    };

    render(<StatusWidget {...mockProps} data={noDetailsData} />);
    
    expect(screen.queryByText('Details')).not.toBeInTheDocument();
  });

  it('renders without details when details object is empty', () => {
    const emptyDetailsData = {
      ...mockWidgetData,
      data: {
        ...mockStatusData,
        details: {},
      },
    };

    render(<StatusWidget {...mockProps} data={emptyDetailsData} />);
    
    expect(screen.queryByText('Details')).not.toBeInTheDocument();
  });

  it('displays status history indicators', () => {
    render(<StatusWidget {...mockProps} />);
    
    expect(screen.getByText('Status History')).toBeInTheDocument();
    // Should render 10 status history dots
    const historyDots = screen.getAllByTitle(/periods ago/);
    expect(historyDots).toHaveLength(10);
  });

  it('formats last check time correctly', () => {
    render(<StatusWidget {...mockProps} />);
    
    // Should display formatted date/time
    expect(screen.getByText(/Last checked: 1\/1\/2024/)).toBeInTheDocument();
  });

  it('shows no data message when data is not available', () => {
    render(<StatusWidget {...mockProps} data={undefined} />);
    
    expect(screen.getByText('No status data available')).toBeInTheDocument();
  });

  it('handles boolean detail values', () => {
    const booleanDetailsData = {
      ...mockWidgetData,
      data: {
        ...mockStatusData,
        details: {
          healthy: true,
          maintenance: false,
        },
      },
    };

    render(<StatusWidget {...mockProps} data={booleanDetailsData} />);
    
    expect(screen.getByText('Yes')).toBeInTheDocument();
    expect(screen.getByText('No')).toBeInTheDocument();
  });

  it('passes props correctly to WidgetBase', () => {
    render(<StatusWidget {...mockProps} />);
    
    const widgetBase = screen.getByTestId('widget-base');
    expect(widgetBase).toBeInTheDocument();
  });
});