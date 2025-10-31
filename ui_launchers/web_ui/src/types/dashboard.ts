/**
 * Dashboard system type definitions
 */

export type WidgetType = 'metric' | 'chart' | 'table' | 'status' | 'log';
export type WidgetSize = 'small' | 'medium' | 'large' | 'full';
export type DashboardLayout = 'grid' | 'masonry' | 'flex';

export interface WidgetPosition {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface WidgetConfig {
  id: string;
  type: WidgetType;
  title: string;
  size: WidgetSize;
  position: WidgetPosition;
  config: Record<string, any>;
  refreshInterval?: number;
  enabled: boolean;
}

export interface DashboardConfig {
  id: string;
  name: string;
  description?: string;
  widgets: WidgetConfig[];
  layout: DashboardLayout;
  refreshInterval: number;
  filters: DashboardFilter[];
  createdAt: Date;
  updatedAt: Date;
}

export interface DashboardFilter {
  id: string;
  name: string;
  type: 'timeRange' | 'category' | 'status' | 'custom';
  value: any;
  enabled: boolean;
}

export interface WidgetData {
  id: string;
  data: any;
  loading: boolean;
  error?: string;
  lastUpdated: Date;
}

export interface WidgetProps {
  config: WidgetConfig;
  data?: WidgetData;
  onConfigChange?: (config: WidgetConfig) => void;
  onRefresh?: () => void;
  onRemove?: () => void;
  isEditing?: boolean;
}

export interface DashboardContainerProps {
  config: DashboardConfig;
  onConfigChange: (config: DashboardConfig) => void;
  isEditing?: boolean;
  className?: string;
}

export interface WidgetRegistry {
  [key: string]: {
    component: React.ComponentType<WidgetProps>;
    defaultConfig: Partial<WidgetConfig>;
    configSchema?: any;
    name: string;
    description: string;
    icon?: string;
  };
}

export interface DragItem {
  id: string;
  type: string;
  position: WidgetPosition;
}

export interface DropResult {
  draggedId: string;
  overId: string | null;
  delta: { x: number; y: number };
}

// Widget-specific data types
export interface MetricData {
  value: number;
  label: string;
  trend?: {
    direction: 'up' | 'down' | 'stable';
    percentage: number;
  };
  threshold?: {
    warning: number;
    critical: number;
  };
  unit?: string;
  format?: 'number' | 'percentage' | 'currency' | 'bytes';
}

export interface StatusData {
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  message: string;
  details?: Record<string, any>;
  lastCheck: Date;
}

export interface ChartData {
  series: Array<{
    name: string;
    data: Array<{ x: any; y: any }>;
    type?: 'line' | 'bar' | 'area';
  }>;
  xAxis?: {
    type: 'time' | 'category' | 'number';
    label?: string;
  };
  yAxis?: {
    label?: string;
    min?: number;
    max?: number;
  };
}

export interface LogData {
  entries: Array<{
    id: string;
    timestamp: Date;
    level: 'debug' | 'info' | 'warn' | 'error';
    message: string;
    source?: string;
    metadata?: Record<string, any>;
  }>;
  totalCount: number;
  hasMore: boolean;
}