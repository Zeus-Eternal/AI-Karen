
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import MetricWidget from '../MetricWidget';
import type { WidgetConfig, MetricData } from '@/types/dashboard';

// Mock the WidgetBase component
vi.mock('../../WidgetBase', () => ({
  WidgetBase: ({ children, ...props }: any) => (
    <div data-testid="widget-base" {...props}>
      {children}
    </div>
  ),
}));

const mockConfig: WidgetConfig = {
  id: 'test-metric-widget',
  type: 'metric',
  title: 'CPU Usage',
  size: 'small',
  position: { x: 0, y: 0, w: 1, h: 1 },
  config: {
    dataSource: 'system-metrics',
    metric: 'cpu_usage',
    format: 'percentage',
    unit: '%',
    thresholds: {
      warning: 70,
      critical: 90,
    },
    showTrend: true,
  },
  refreshInterval: 30000,
  enabled: true,
};

const mockMetricData: MetricData = {
  value: 65.5,
  label: 'CPU Usage',
  trend: {
    direction: 'up',
    percentage: 5.2,
  },
  threshold: {
    warning: 70,
    critical: 90,
  },
  unit: '%',
  format: 'percentage',
};

const mockWidgetData = {
  id: 'test-metric-widget',
  data: mockMetricData,
  loading: false,
  lastUpdated: new Date(),
};

describe('MetricWidget', () => {
  const mockProps = {
    config: mockConfig,
    data: mockWidgetData,
    onConfigChange: vi.fn(),
    onRefresh: vi.fn(),
    onRemove: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();

  it('renders metric widget with data', () => {
    render(<MetricWidget {...mockProps} />);
    
    expect(screen.getByText('65.5%')).toBeInTheDocument();
    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('+5.2%')).toBeInTheDocument();
    expect(screen.getByText('vs last period')).toBeInTheDocument();

  it('displays threshold indicators', () => {
    render(<MetricWidget {...mockProps} />);
    
    expect(screen.getByText('Thresholds:')).toBeInTheDocument();
    expect(screen.getByText('70.0%')).toBeInTheDocument();
    expect(screen.getByText('90.0%')).toBeInTheDocument();

  it('shows warning status when value exceeds warning threshold', () => {
    const warningData = {
      ...mockWidgetData,
      data: {
        ...mockMetricData,
        value: 75,
      },
    };

    render(<MetricWidget {...mockProps} data={warningData} />);
    
    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(screen.getByText('75.0%')).toBeInTheDocument();

  it('shows critical status when value exceeds critical threshold', () => {
    const criticalData = {
      ...mockWidgetData,
      data: {
        ...mockMetricData,
        value: 95,
      },
    };

    render(<MetricWidget {...mockProps} data={criticalData} />);
    
    expect(screen.getByText('Critical')).toBeInTheDocument();
    expect(screen.getByText('95.0%')).toBeInTheDocument();

  it('formats values correctly based on format type', () => {
    const currencyData = {
      ...mockWidgetData,
      data: {
        ...mockMetricData,
        value: 1234.56,
        format: 'currency' as const,
        unit: undefined,
      },
    };

    render(<MetricWidget {...mockProps} data={currencyData} />);
    
    expect(screen.getByText('$1,234.56')).toBeInTheDocument();

  it('formats bytes correctly', () => {
    const bytesData = {
      ...mockWidgetData,
      data: {
        ...mockMetricData,
        value: 1073741824, // 1GB in bytes
        format: 'bytes' as const,
        unit: undefined,
      },
    };

    render(<MetricWidget {...mockProps} data={bytesData} />);
    
    expect(screen.getByText('1.0 GB')).toBeInTheDocument();

  it('shows trend indicator with correct direction', () => {
    const downTrendData = {
      ...mockWidgetData,
      data: {
        ...mockMetricData,
        trend: {
          direction: 'down' as const,
          percentage: -3.1,
        },
      },
    };

    render(<MetricWidget {...mockProps} data={downTrendData} />);
    
    expect(screen.getByText('-3.1%')).toBeInTheDocument();

  it('handles stable trend', () => {
    const stableTrendData = {
      ...mockWidgetData,
      data: {
        ...mockMetricData,
        trend: {
          direction: 'stable' as const,
          percentage: 0,
        },
      },
    };

    render(<MetricWidget {...mockProps} data={stableTrendData} />);
    
    expect(screen.getByText('0.0%')).toBeInTheDocument();

  it('renders without trend when trend data is not available', () => {
    const noTrendData = {
      ...mockWidgetData,
      data: {
        ...mockMetricData,
        trend: undefined,
      },
    };

    render(<MetricWidget {...mockProps} data={noTrendData} />);
    
    expect(screen.queryByText('vs last period')).not.toBeInTheDocument();

  it('renders without thresholds when threshold data is not available', () => {
    const noThresholdData = {
      ...mockWidgetData,
      data: {
        ...mockMetricData,
        threshold: undefined,
      },
    };

    render(<MetricWidget {...mockProps} data={noThresholdData} />);
    
    expect(screen.queryByText('Thresholds:')).not.toBeInTheDocument();

  it('shows no data message when data is not available', () => {
    render(<MetricWidget {...mockProps} data={undefined} />);
    
    expect(screen.getByText('No metric data available')).toBeInTheDocument();

  it('handles custom units correctly', () => {
    const customUnitData = {
      ...mockWidgetData,
      data: {
        ...mockMetricData,
        value: 150,
        format: 'number' as const,
        unit: 'req/s',
      },
    };

    render(<MetricWidget {...mockProps} data={customUnitData} />);
    
    expect(screen.getByText('150 req/s')).toBeInTheDocument();

  it('passes props correctly to WidgetBase', () => {
    render(<MetricWidget {...mockProps} />);
    
    const widgetBase = screen.getByTestId('widget-base');
    expect(widgetBase).toBeInTheDocument();

