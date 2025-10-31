'use client';

import React, { useMemo, useCallback } from 'react';
import { AgCharts } from 'ag-charts-react';
import { AgChartOptions } from 'ag-charts-community';
import { WidgetBase } from '../WidgetBase';
import { Button } from '@/components/ui/button';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Download,
  TrendingUp,
  BarChart3,
  Activity
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { WidgetProps, ChartData } from '@/types/dashboard';

interface ChartWidgetProps extends WidgetProps {
  data?: {
    id: string;
    data: ChartData;
    loading: boolean;
    error?: string;
    lastUpdated: Date;
  };
}

const getChartTypeIcon = (type: string) => {
  switch (type) {
    case 'line':
      return <TrendingUp className="h-3 w-3" />;
    case 'bar':
      return <BarChart3 className="h-3 w-3" />;
    case 'area':
      return <Activity className="h-3 w-3" />;
    default:
      return <TrendingUp className="h-3 w-3" />;
  }
};

export const ChartWidget: React.FC<ChartWidgetProps> = (props) => {
  const { data: widgetData, config } = props;
  
  const chartOptions = useMemo((): AgChartOptions => {
    if (!widgetData?.data) {
      return {
        data: [],
        series: [],
      };
    }

    const chartData = widgetData.data;
    
    // Transform data for AG Charts
    const transformedData = chartData.series[0]?.data.map(point => ({
      x: chartData.xAxis?.type === 'time' ? new Date(point.x) : point.x,
      ...chartData.series.reduce((acc, series, index) => {
        const dataPoint = series.data.find(d => 
          (chartData.xAxis?.type === 'time' ? 
            new Date(d.x).getTime() === new Date(point.x).getTime() : 
            d.x === point.x)
        );
        acc[series.name] = dataPoint?.y || 0;
        return acc;
      }, {} as Record<string, number>)
    })) || [];

    const series = chartData.series.map(seriesData => {
      const baseConfig = {
        type: seriesData.type || 'line',
        xKey: 'x',
        yKey: seriesData.name,
        yName: seriesData.name,
      };

      switch (seriesData.type) {
        case 'bar':
          return {
            ...baseConfig,
            type: 'bar' as const,
          };
        case 'area':
          return {
            ...baseConfig,
            type: 'area' as const,
            fillOpacity: 0.3,
          };
        case 'line':
        default:
          return {
            ...baseConfig,
            type: 'line' as const,
            marker: {
              enabled: transformedData.length <= 50, // Show markers for smaller datasets
            },
          };
      }
    });

    return {
      data: transformedData,
      series,
      axes: [
        {
          type: chartData.xAxis?.type === 'time' ? 'time' : 
                chartData.xAxis?.type === 'number' ? 'number' : 'category',
          position: 'bottom',
          title: {
            text: chartData.xAxis?.label || '',
          },
          ...(chartData.xAxis?.type === 'time' && {
            tick: {
              count: 10,
            },
            label: {
              format: '%H:%M',
            },
          }),
        },
        {
          type: 'number',
          position: 'left',
          title: {
            text: chartData.yAxis?.label || '',
          },
          ...(chartData.yAxis?.min !== undefined && { min: chartData.yAxis.min }),
          ...(chartData.yAxis?.max !== undefined && { max: chartData.yAxis.max }),
        },
      ],
      legend: {
        enabled: chartData.series.length > 1,
        position: 'bottom',
      },
      tooltip: {
        enabled: true,
      },
      zoom: {
        enabled: true,
        axes: 'x',
      },
      animation: {
        enabled: true,
      },
      theme: {
        baseTheme: 'ag-default',
        palette: {
          fills: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
          strokes: ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0891b2'],
        },
      },
    };
  }, [widgetData?.data]);

  const handleExport = useCallback((format: 'png' | 'svg' | 'pdf') => {
    // In a real implementation, this would trigger chart export
    console.log(`Exporting chart as ${format}`);
  }, []);

  const handleZoomIn = useCallback(() => {
    // In a real implementation, this would zoom the chart
    console.log('Zoom in');
  }, []);

  const handleZoomOut = useCallback(() => {
    // In a real implementation, this would zoom out the chart
    console.log('Zoom out');
  }, []);

  const handleResetZoom = useCallback(() => {
    // In a real implementation, this would reset zoom
    console.log('Reset zoom');
  }, []);

  const handleChangeChartType = useCallback((type: 'line' | 'bar' | 'area') => {
    // In a real implementation, this would change the chart type
    console.log(`Change chart type to ${type}`);
  }, []);

  if (!widgetData?.data) {
    return (
      <WidgetBase {...props}>
        <div className="flex items-center justify-center h-full text-muted-foreground">
          No chart data available
        </div>
      </WidgetBase>
    );
  }

  return (
    <WidgetBase 
      {...props}
      className="relative"
    >
      {/* Chart Controls */}
      <div className="absolute top-2 right-2 z-10 flex gap-1">
        {/* Chart Type Selector */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 bg-background/80 backdrop-blur-sm"
            >
              {getChartTypeIcon(widgetData.data.series[0]?.type || 'line')}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-32">
            <DropdownMenuItem onClick={() => handleChangeChartType('line')}>
              <TrendingUp className="h-3 w-3 mr-2" />
              Line
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleChangeChartType('bar')}>
              <BarChart3 className="h-3 w-3 mr-2" />
              Bar
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleChangeChartType('area')}>
              <Activity className="h-3 w-3 mr-2" />
              Area
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Zoom Controls */}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomIn}
          className="h-6 w-6 p-0 bg-background/80 backdrop-blur-sm"
        >
          <ZoomIn className="h-3 w-3" />
        </Button>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomOut}
          className="h-6 w-6 p-0 bg-background/80 backdrop-blur-sm"
        >
          <ZoomOut className="h-3 w-3" />
        </Button>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={handleResetZoom}
          className="h-6 w-6 p-0 bg-background/80 backdrop-blur-sm"
        >
          <RotateCcw className="h-3 w-3" />
        </Button>

        {/* Export Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 bg-background/80 backdrop-blur-sm"
            >
              <Download className="h-3 w-3" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-32">
            <DropdownMenuItem onClick={() => handleExport('png')}>
              Export PNG
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleExport('svg')}>
              Export SVG
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => handleExport('pdf')}>
              Export PDF
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Chart Container */}
      <div className="h-full w-full pt-8">
        <AgCharts options={chartOptions} />
      </div>

      {/* Chart Summary */}
      {widgetData.data.series.length > 0 && (
        <div className="absolute bottom-2 left-2 right-2 bg-background/80 backdrop-blur-sm rounded px-2 py-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              {widgetData.data.series.length} series, {widgetData.data.series[0]?.data.length || 0} points
            </span>
            <span>
              {widgetData.data.xAxis?.type === 'time' ? 'Time Series' : 'Data Series'}
            </span>
          </div>
        </div>
      )}
    </WidgetBase>
  );
};

export default ChartWidget;