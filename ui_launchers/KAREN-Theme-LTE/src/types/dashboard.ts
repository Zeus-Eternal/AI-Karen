/**
 * Dashboard Types
 * 
 * Type definitions for dashboard components and functionality
 */

export interface TimeRange {
  start: Date;
  end: Date;
  preset?: 'last-hour' | 'last-day' | 'last-week' | 'last-month' | 'custom';
}

export interface DashboardFilter {
  id: string;
  name: string;
  type: string;
  value: unknown;
  enabled: boolean;
}

export interface DashboardWidget {
  id: string;
  type: string;
  title: string;
  position: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  config: Record<string, unknown>;
  data?: unknown;
}

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  layout: 'grid' | 'masonry' | 'flex';
  widgets: DashboardWidget[];
  filters: DashboardFilter[];
  timeRange: TimeRange;
  isDefault?: boolean;
  isPublic?: boolean;
  owner?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface DashboardMetrics {
  totalViews: number;
  uniqueUsers: number;
  averageSessionDuration: number;
  bounceRate: number;
  conversionRate: number;
  revenue?: number;
  customMetrics?: Record<string, number>;
}

export interface DashboardAnalytics {
  metrics: DashboardMetrics;
  trends: Array<{
    metric: string;
    value: number;
    change: number;
    changePercent: number;
    period: string;
  }>;
  topPages: Array<{
    page: string;
    views: number;
    uniqueViews: number;
  }>;
  userSegments: Array<{
    segment: string;
    count: number;
    percentage: number;
  }>;
}

export interface DashboardTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  thumbnail?: string;
  layout: 'grid' | 'masonry' | 'flex';
  widgets: Omit<DashboardWidget, 'id'>[];
  tags: string[];
  isPremium?: boolean;
}

export interface DashboardShare {
  id: string;
  dashboardId: string;
  sharedBy: string;
  sharedWith: string;
  permissions: 'view' | 'edit' | 'admin';
  expiresAt?: Date;
  createdAt: Date;
}

export interface DashboardExport {
  format: 'json' | 'csv' | 'pdf' | 'png';
  includeData: boolean;
  includeFilters: boolean;
  dateRange?: TimeRange;
}

export interface DashboardImport {
  file: File;
  mergeStrategy: 'replace' | 'merge' | 'append';
  validateBeforeImport: boolean;
}