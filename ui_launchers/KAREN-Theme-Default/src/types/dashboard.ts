/**
 * Dashboard system type definitions
 *
 * This module defines all types related to the dashboard system including widgets,
 * layouts, filters, and data structures for visualizations.
 */

/**
 * Supported widget types for dashboard components
 */
export type WidgetType = 'metric' | 'chart' | 'table' | 'status' | 'log';

/**
 * Widget size presets for responsive layouts
 */
export type WidgetSize = 'small' | 'medium' | 'large' | 'full';

/**
 * Dashboard layout strategies
 */
export type DashboardLayout = 'grid' | 'masonry' | 'flex';

/**
 * Grid position for widget placement
 */
export interface WidgetPosition {
  /** X coordinate in grid units */
  x: number;
  /** Y coordinate in grid units */
  y: number;
  /** Width in grid units */
  w: number;
  /** Height in grid units */
  h: number;
}

/**
 * Type-safe configuration for different widget types
 */
export type WidgetConfigData =
  | { type: 'metric'; threshold?: number; target?: number; decimals?: number }
  | { type: 'chart'; chartType: 'line' | 'bar' | 'area' | 'pie'; stacked?: boolean }
  | { type: 'table'; pageSize?: number; sortable?: boolean; exportable?: boolean }
  | { type: 'status'; checkInterval?: number; alertThreshold?: 'warning' | 'critical' }
  | { type: 'log'; maxEntries?: number; levels?: Array<'info' | 'warn' | 'error'>; sources?: string[] }
  | { type: string; [key: string]: unknown }; // Extensible for custom widgets

/**
 * Widget configuration including position, type, and widget-specific settings
 */
export interface WidgetConfig {
  id: string;
  type: WidgetType;
  title: string;
  size: WidgetSize;
  position: WidgetPosition;
  config: WidgetConfigData;
  refreshInterval?: number;
  enabled: boolean;
}
/**
 * Dashboard configuration including all widgets, layout, and filters
 */
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

/**
 * Filter value types based on filter type
 */
export type DashboardFilterValue =
  | { type: 'timeRange'; value: { start: Date; end: Date } }
  | { type: 'category'; value: string | string[] }
  | { type: 'status'; value: 'healthy' | 'warning' | 'critical' | 'unknown' | Array<'healthy' | 'warning' | 'critical' | 'unknown'> }
  | { type: 'custom'; value: string | number | boolean | Record<string, unknown> };

/**
 * Dashboard filter for data filtering
 */
export interface DashboardFilter {
  id: string;
  name: string;
  type: 'timeRange' | 'category' | 'status' | 'custom';
  value: DashboardFilterValue['value'];
  enabled: boolean;
}

/**
 * Union type for all possible widget data shapes
 */
export type WidgetDataValue = MetricData | ChartData | TableData | StatusData | LogData | unknown;

/**
 * Container for widget data with loading and error states
 */
export interface WidgetData {
  id: string;
  data: WidgetDataValue;
  loading: boolean;
  error?: string;
  lastUpdated: Date;
}
/**
 * Props for widget components
 */
export interface WidgetProps {
  config: WidgetConfig;
  data?: WidgetData;
  onConfigChange?: (config: WidgetConfig) => void;
  onRefresh?: () => void;
  onRemove?: () => void;
  isEditing?: boolean;
}

/**
 * Props for dashboard container component
 */
export interface DashboardContainerProps {
  config: DashboardConfig;
  onConfigChange: (config: DashboardConfig) => void;
  isEditing?: boolean;
  className?: string;
}

/**
 * JSON Schema type for widget configuration validation
 */
export interface JsonSchema {
  type: 'object' | 'string' | 'number' | 'boolean' | 'array';
  properties?: Record<string, JsonSchema>;
  required?: string[];
  items?: JsonSchema;
  enum?: unknown[];
  minimum?: number;
  maximum?: number;
  pattern?: string;
  description?: string;
}

/**
 * Registry of available widget types and their configurations
 */
export interface WidgetRegistry {
  [key: string]: {
    component: React.ComponentType<WidgetProps>;
    defaultConfig: Partial<WidgetConfig>;
    configSchema?: JsonSchema;
    name: string;
    description: string;
    icon?: string;
  };
}
/**
 * Drag and drop item representation
 */
export interface DragItem {
  id: string;
  type: string;
  position: WidgetPosition;
}

/**
 * Result of a drag and drop operation
 */
export interface DropResult {
  draggedId: string;
  overId: string | null;
  delta: { x: number; y: number };
}

// ─────────────────────────────────────────────────────────────────────
// Widget-specific data types
// ─────────────────────────────────────────────────────────────────────

/**
 * Data for metric display widgets showing single values with trends
 */
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

/**
 * Data for status indicator widgets
 */
export interface StatusData {
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  message: string;
  details?: Record<string, string | number | boolean>;
  lastCheck: Date;
}

/**
 * Chart data point with flexible x/y values
 */
export interface ChartDataPoint {
  x: number | string | Date;
  y: number;
  label?: string;
}

/**
 * Data for chart visualization widgets
 */
export interface ChartData {
  series: Array<{
    name: string;
    data: ChartDataPoint[];
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

/**
 * Data for table display widgets
 */
export interface TableData {
  columns: Array<{
    id: string;
    label: string;
    sortable?: boolean;
    type?: 'string' | 'number' | 'date' | 'boolean';
  }>;
  rows: Array<Record<string, string | number | boolean | Date>>;
  totalCount: number;
  hasMore: boolean;
}

/**
 * Data for log viewer widgets
 */
export interface LogData {
  entries: Array<{
    id: string;
    timestamp: Date;
    level: 'info' | 'warn' | 'error';
    message: string;
    source?: string;
    metadata?: Record<string, string | number | boolean>;
  }>;
  totalCount: number;
  hasMore: boolean;
}
