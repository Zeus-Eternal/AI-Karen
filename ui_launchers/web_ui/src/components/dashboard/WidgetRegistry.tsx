'use client';

import React from 'react';
import { 
  BarChart3, 
  Activity, 
  AlertCircle, 
  FileText,
  TrendingUp 
} from 'lucide-react';
import type { WidgetRegistry, WidgetConfig, WidgetProps } from '@/types/dashboard';

// Import actual widget components
import MetricWidget from './widgets/MetricWidget';
import StatusWidget from './widgets/StatusWidget';
import ChartWidget from './widgets/ChartWidget';
import LogWidget from './widgets/LogWidget';

// Placeholder for table widget (not implemented in this task)
const TableWidget: React.FC<WidgetProps> = ({ config }) => (
  <div className="flex items-center justify-center h-full text-muted-foreground">
    <div className="text-center">
      <AlertCircle className="h-8 w-8 mx-auto mb-2 sm:w-auto md:w-full" />
      <p className="text-sm md:text-base lg:text-lg">Table Widget</p>
      <p className="text-xs sm:text-sm md:text-base">{config.title}</p>
    </div>
  </div>
);

// Widget Registry
export const widgetRegistry: WidgetRegistry = {
  metric: {
    component: MetricWidget,
    name: 'Metric Widget',
    description: 'Display KPIs with trend indicators and threshold alerts',
    icon: 'TrendingUp',
    defaultConfig: {
      type: 'metric',
      size: 'small',
      position: { x: 0, y: 0, w: 1, h: 1 },
      config: {
        metric: 'cpu_usage',
        unit: '%',
        format: 'percentage',
        threshold: {
          warning: 70,
          critical: 90
        }
      },
      refreshInterval: 30000,
      enabled: true
    }
  },
  status: {
    component: StatusWidget,
    name: 'Status Widget',
    description: 'System health visualization with color-coded status indicators',
    icon: 'Activity',
    defaultConfig: {
      type: 'status',
      size: 'small',
      position: { x: 0, y: 0, w: 1, h: 1 },
      config: {
        service: 'api',
        showDetails: true
      },
      refreshInterval: 15000,
      enabled: true
    }
  },
  chart: {
    component: ChartWidget,
    name: 'Chart Widget',
    description: 'Interactive charts for time-series data with zoom and pan capabilities',
    icon: 'BarChart3',
    defaultConfig: {
      type: 'chart',
      size: 'medium',
      position: { x: 0, y: 0, w: 2, h: 1 },
      config: {
        chartType: 'line',
        dataSource: 'metrics',
        timeRange: '1h',
        series: []
      },
      refreshInterval: 60000,
      enabled: true
    }
  },
  log: {
    component: LogWidget,
    name: 'Log Widget',
    description: 'Real-time log streaming with filtering and search',
    icon: 'FileText',
    defaultConfig: {
      type: 'log',
      size: 'large',
      position: { x: 0, y: 0, w: 2, h: 2 },
      config: {
        source: 'application',
        level: 'info',
        maxEntries: 100,
        autoScroll: true
      },
      refreshInterval: 5000,
      enabled: true
    }
  },
  table: {
    component: TableWidget,
    name: 'Table Widget',
    description: 'Tabular data display with sorting and filtering',
    icon: 'AlertCircle',
    defaultConfig: {
      type: 'table',
      size: 'medium',
      position: { x: 0, y: 0, w: 2, h: 1 },
      config: {
        dataSource: 'api',
        columns: [],
        pagination: true,
        pageSize: 10
      },
      refreshInterval: 30000,
      enabled: true
    }
  }
};

// Helper functions
export const getWidgetComponent = (type: string) => {
  const widget = widgetRegistry[type];
  return widget?.component || null;
};

export const getWidgetDefaultConfig = (type: string): Partial<WidgetConfig> => {
  const widget = widgetRegistry[type];
  return widget?.defaultConfig || {};
};

export const getAvailableWidgetTypes = () => {
  return Object.keys(widgetRegistry);
};

export const getWidgetInfo = (type: string) => {
  const widget = widgetRegistry[type];
  if (!widget) return null;
  
  return {
    name: widget.name,
    description: widget.description,
    icon: widget.icon
  };
};

export const createWidgetConfig = (
  type: string, 
  overrides: Partial<WidgetConfig> = {}
): WidgetConfig => {
  const defaultConfig = getWidgetDefaultConfig(type);
  const id = `widget_${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  return {
    id,
    title: `${getWidgetInfo(type)?.name || 'Widget'}`,
    ...defaultConfig,
    ...overrides
  } as WidgetConfig;
};

export default widgetRegistry;