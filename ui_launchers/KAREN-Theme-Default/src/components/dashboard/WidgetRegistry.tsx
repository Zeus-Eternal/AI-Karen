// ui_launchers/KAREN-Theme-Default/src/components/dashboard/WidgetRegistry.tsx
"use client";

import {
  AlertCircle,
  TrendingUp,
  Activity,
  BarChart3,
  FileText,
  type LucideIcon,
} from "lucide-react";
import type { ComponentType } from "react";
import type { WidgetRegistry as WidgetRegistryType, WidgetConfig, WidgetProps } from "@/types/dashboard";

// Actual widget components
import MetricWidget from "./widgets/MetricWidget";
import StatusWidget from "./widgets/StatusWidget";
import ChartWidget from "./widgets/ChartWidget";
import LogWidget from "./widgets/LogWidget";
import TableWidget from "./widgets/TableWidget";

/* -----------------------------------------------------------------------------
 * Icon resolution (typed, safe fallback)
 * ---------------------------------------------------------------------------*/
const ICONS: Record<string, LucideIcon> = {
  TrendingUp,
  Activity,
  BarChart3,
  FileText,
  AlertCircle,
};

export const resolveIcon = (iconName?: string): LucideIcon => {
  if (!iconName) return AlertCircle;
  return ICONS[iconName] ?? AlertCircle;
};

/* -----------------------------------------------------------------------------
 * Safe ID generator (crypto RNG first, fallback to time+rand)
 * ---------------------------------------------------------------------------*/
const genId = (prefix: string) => {
  try {
    return `${prefix}_${crypto.randomUUID()}`;
  } catch {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
  }
};

/* -----------------------------------------------------------------------------
 * Widget Registry (typed, satisfies)
 * ---------------------------------------------------------------------------*/
export const widgetRegistry = {
  metric: {
    component: MetricWidget,
    name: "Metric Widget",
    description: "Display KPIs with trend indicators and threshold alerts",
    icon: "TrendingUp",
    defaultConfig: {
      type: "metric",
      size: "small",
      position: { x: 0, y: 0, w: 1, h: 1 },
      config: {
        type: "metric",
        metric: "cpu_usage",
        unit: "%",
        format: "percentage",
        threshold: { warning: 70, critical: 90 },
      },
      refreshInterval: 30_000,
      enabled: true,
    },
  },
  status: {
    component: StatusWidget,
    name: "Status Widget",
    description:
      "System health visualization with color-coded status indicators",
    icon: "Activity",
    defaultConfig: {
      type: "status",
      size: "small",
      position: { x: 0, y: 0, w: 1, h: 1 },
      config: {
        type: "status",
        service: "api",
        showDetails: true,
      },
      refreshInterval: 15_000,
      enabled: true,
    },
  },
  chart: {
    component: ChartWidget,
    name: "Chart Widget",
    description:
      "Interactive charts for time-series data with zoom and pan capabilities",
    icon: "BarChart3",
    defaultConfig: {
      type: "chart",
      size: "medium",
      position: { x: 0, y: 0, w: 2, h: 1 },
      config: {
        type: "chart",
        chartType: "line",
        dataSource: "metrics",
        timeRange: "1h",
        series: [],
      },
      refreshInterval: 60_000,
      enabled: true,
    },
  },
  log: {
    component: LogWidget,
    name: "Log Widget",
    description: "Real-time log streaming with filtering and search",
    icon: "FileText",
    defaultConfig: {
      type: "log",
      size: "large",
      position: { x: 0, y: 0, w: 2, h: 2 },
      config: {
        type: "log",
        source: "application",
        level: "info",
        maxEntries: 100,
        autoScroll: true,
      },
      refreshInterval: 5_000,
      enabled: true,
    },
  },
  table: {
    component: TableWidget,
    name: "Table Widget",
    description: "Tabular data display with sorting and filtering",
    icon: "AlertCircle",
    defaultConfig: {
      type: "table",
      size: "medium",
      position: { x: 0, y: 0, w: 2, h: 1 },
      config: {
        type: "table",
        dataSource: "api",
        columns: [],
        pagination: true,
        pageSize: 10,
      },
      refreshInterval: 30_000,
      enabled: true,
    },
  },
} satisfies WidgetRegistryType;

/* -----------------------------------------------------------------------------
 * Helpers (typed, null-safe)
 * ---------------------------------------------------------------------------*/
export type WidgetTypeKey = keyof typeof widgetRegistry;

export const getWidgetComponent = (type: string): ComponentType<WidgetProps> | null => {
  const widget = widgetRegistry[type as WidgetTypeKey];
  return (widget?.component as ComponentType<WidgetProps>) ?? null;
};

export const getWidgetDefaultConfig = (type: string): Partial<WidgetConfig> => {
  const widget = (widgetRegistry as Record<string, (typeof widgetRegistry)[WidgetTypeKey]>)[type];
  return widget?.defaultConfig ?? {};
};

export const getAvailableWidgetTypes = (): WidgetTypeKey[] => {
  return Object.keys(widgetRegistry) as WidgetTypeKey[];
};

export const getWidgetInfo = (type: string) => {
  const widget = (widgetRegistry as Record<string, (typeof widgetRegistry)[WidgetTypeKey]>)[type];
  if (!widget) return null;
  return {
    name: widget.name,
    description: widget.description,
    icon: widget.icon,
    Icon: resolveIcon(widget.icon),
  };
};

export const createWidgetConfig = (
  type: string,
  overrides: Partial<WidgetConfig> = {}
): WidgetConfig => {
  const defaults = getWidgetDefaultConfig(type);
  const info = getWidgetInfo(type);
  const id = genId(`widget_${type}`);

  return {
    id,
    title: info?.name ?? "Widget",
    ...defaults,
    ...overrides,
  } as WidgetConfig;
};

export type { WidgetRegistryType as WidgetRegistry };
export default widgetRegistry;
