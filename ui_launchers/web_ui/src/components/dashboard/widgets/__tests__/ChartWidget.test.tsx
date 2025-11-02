
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import ChartWidget from '../ChartWidget';
import type { WidgetConfig, ChartData } from '@/types/dashboard';

// Mock AG Charts
vi.mock('ag-charts-react', () => ({
  AgCharts: ({ options }: any) => (
    <div data-testid="ag-charts" data-options={JSON.stringify(options)}>
    </div>
  ),
}));

// Mock the WidgetBase component
vi.mock('../../WidgetBase', () => ({
  WidgetBase: ({ children, ...props }: any) => (
    <div data-testid="widget-base" {...props}>
      {children}
    </div>
  ),
}));

const mockConfig: WidgetConfig = {
  id: 'test-chart-widget',
  type: 'chart',
  title: 'CPU Usage Over Time',
  size: 'medium',
  position: { x: 0, y: 0, w: 2, h: 1 },
  config: {
    dataSource: 'metrics-api',
    chartType: 'line',
    timeRange: '24h',
    series: ['cpu_usage', 'memory_usage'],
    showLegend: true,
    enableZoom: true,
  },
  refreshInterval: 60000,
  enabled: true,
};

const mockChartData: ChartData = {
  series: [
    {
      name: 'cpu_usage',
      data: [
        { x: '2024-01-01T10:00:00Z', y: 45 },
        { x: '2024-01-01T11:00:00Z', y: 52 },
        { x: '2024-01-01T12:00:00Z', y: 38 },
      ],
      type: 'line',
    },
    {
      name: 'memory_usage',
      data: [
        { x: '2024-01-01T10:00:00Z', y: 65 },
        { x: '2024-01-01T11:00:00Z', y: 70 },
        { x: '2024-01-01T12:00:00Z', y: 68 },
      ],
      type: 'line',
    },
  ],
  xAxis: {
    type: 'time',
    label: 'Time',
  },
  yAxis: {
    label: 'Usage (%)',
    min: 0,
    max: 100,
  },
};

const mockWidgetData = {
  id: 'test-chart-widget',
  data: mockChartData,
  loading: false,
  lastUpdated: new Date(),
};

describe('ChartWidget', () => {
  const mockProps = {
    config: mockConfig,
    data: mockWidgetData,
    onConfigChange: vi.fn(),
    onRefresh: vi.fn(),
    onRemove: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();

  it('renders chart widget with data', () => {
    render(<ChartWidget {...mockProps} />);
    
    expect(screen.getByTestId('ag-charts')).toBeInTheDocument();
    expect(screen.getByText('Mock Chart')).toBeInTheDocument();

  it('displays chart controls', () => {
    render(<ChartWidget {...mockProps} />);
    
    // Should have zoom controls
    const zoomInButton = screen.getByRole('button', { name: /zoom in/i });
    const zoomOutButton = screen.getByRole('button', { name: /zoom out/i });
    const resetZoomButton = screen.getByRole('button', { name: /reset zoom/i });
    
    expect(zoomInButton).toBeInTheDocument();
    expect(zoomOutButton).toBeInTheDocument();
    expect(resetZoomButton).toBeInTheDocument();

  it('displays chart summary information', () => {
    render(<ChartWidget {...mockProps} />);
    
    expect(screen.getByText('2 series, 3 points')).toBeInTheDocument();
    expect(screen.getByText('Time Series')).toBeInTheDocument();

  it('handles zoom controls', () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    
    render(<ChartWidget {...mockProps} />);
    
    const zoomInButton = screen.getByRole('button', { name: /zoom in/i });
    const zoomOutButton = screen.getByRole('button', { name: /zoom out/i });
    const resetZoomButton = screen.getByRole('button', { name: /reset zoom/i });
    
    fireEvent.click(zoomInButton);
    expect(consoleSpy).toHaveBeenCalledWith('Zoom in');
    
    fireEvent.click(zoomOutButton);
    expect(consoleSpy).toHaveBeenCalledWith('Zoom out');
    
    fireEvent.click(resetZoomButton);
    expect(consoleSpy).toHaveBeenCalledWith('Reset zoom');
    
    consoleSpy.mockRestore();

  it('configures AG Charts options correctly', () => {
    render(<ChartWidget {...mockProps} />);
    
    const chartElement = screen.getByTestId('ag-charts');
    const optionsData = JSON.parse(chartElement.getAttribute('data-options') || '{}');
    
    expect(optionsData.data).toHaveLength(3); // 3 data points
    expect(optionsData.series).toHaveLength(2); // 2 series
    expect(optionsData.axes).toHaveLength(2); // x and y axes
    expect(optionsData.legend.enabled).toBe(true);
    expect(optionsData.zoom.enabled).toBe(true);

  it('handles different chart types', () => {
    const barChartData = {
      ...mockWidgetData,
      data: {
        ...mockChartData,
        series: [
          {
            ...mockChartData.series[0],
            type: 'bar' as const,
          },
        ],
      },
    };

    render(<ChartWidget {...mockProps} data={barChartData} />);
    
    const chartElement = screen.getByTestId('ag-charts');
    const optionsData = JSON.parse(chartElement.getAttribute('data-options') || '{}');
    
    expect(optionsData.series[0].type).toBe('bar');

  it('handles area chart type', () => {
    const areaChartData = {
      ...mockWidgetData,
      data: {
        ...mockChartData,
        series: [
          {
            ...mockChartData.series[0],
            type: 'area' as const,
          },
        ],
      },
    };

    render(<ChartWidget {...mockProps} data={areaChartData} />);
    
    const chartElement = screen.getByTestId('ag-charts');
    const optionsData = JSON.parse(chartElement.getAttribute('data-options') || '{}');
    
    expect(optionsData.series[0].type).toBe('area');
    expect(optionsData.series[0].fillOpacity).toBe(0.3);

  it('configures time axis correctly', () => {
    render(<ChartWidget {...mockProps} />);
    
    const chartElement = screen.getByTestId('ag-charts');
    const optionsData = JSON.parse(chartElement.getAttribute('data-options') || '{}');
    
    const xAxis = optionsData.axes.find((axis: any) => axis.position === 'bottom');
    expect(xAxis.type).toBe('time');
    expect(xAxis.title.text).toBe('Time');

  it('configures y-axis with min/max values', () => {
    render(<ChartWidget {...mockProps} />);
    
    const chartElement = screen.getByTestId('ag-charts');
    const optionsData = JSON.parse(chartElement.getAttribute('data-options') || '{}');
    
    const yAxis = optionsData.axes.find((axis: any) => axis.position === 'left');
    expect(yAxis.type).toBe('number');
    expect(yAxis.title.text).toBe('Usage (%)');
    expect(yAxis.min).toBe(0);
    expect(yAxis.max).toBe(100);

  it('shows legend when multiple series', () => {
    render(<ChartWidget {...mockProps} />);
    
    const chartElement = screen.getByTestId('ag-charts');
    const optionsData = JSON.parse(chartElement.getAttribute('data-options') || '{}');
    
    expect(optionsData.legend.enabled).toBe(true);

  it('hides legend for single series', () => {
    const singleSeriesData = {
      ...mockWidgetData,
      data: {
        ...mockChartData,
        series: [mockChartData.series[0]],
      },
    };

    render(<ChartWidget {...mockProps} data={singleSeriesData} />);
    
    const chartElement = screen.getByTestId('ag-charts');
    const optionsData = JSON.parse(chartElement.getAttribute('data-options') || '{}');
    
    expect(optionsData.legend.enabled).toBe(false);

  it('shows no data message when data is not available', () => {
    render(<ChartWidget {...mockProps} data={undefined} />);
    
    expect(screen.getByText('No chart data available')).toBeInTheDocument();

  it('handles empty data gracefully', () => {
    const emptyData = {
      ...mockWidgetData,
      data: {
        series: [],
        xAxis: { type: 'time' as const },
        yAxis: { label: 'Value' },
      },
    };

    render(<ChartWidget {...mockProps} data={emptyData} />);
    
    const chartElement = screen.getByTestId('ag-charts');
    const optionsData = JSON.parse(chartElement.getAttribute('data-options') || '{}');
    
    expect(optionsData.data).toEqual([]);
    expect(optionsData.series).toEqual([]);

  it('displays correct summary for non-time series', () => {
    const categoryData = {
      ...mockWidgetData,
      data: {
        ...mockChartData,
        xAxis: {
          type: 'category' as const,
          label: 'Category',
        },
      },
    };

    render(<ChartWidget {...mockProps} data={categoryData} />);
    
    expect(screen.getByText('Data Series')).toBeInTheDocument();

  it('passes props correctly to WidgetBase', () => {
    render(<ChartWidget {...mockProps} />);
    
    const widgetBase = screen.getByTestId('widget-base');
    expect(widgetBase).toBeInTheDocument();

