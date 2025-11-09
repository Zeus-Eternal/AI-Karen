/**
 * Performance Components Index - Production Grade
 *
 * Centralized export hub for all performance monitoring,
 * analytics, optimization, and resource-tracking components.
 * Keeps imports clean across the admin and analytics UIs.
 */

// ============================================================================
// Component Exports
// ============================================================================

// Performance Alert System
export { PerformanceAlertSystem } from "./PerformanceAlertSystem";
export type {
  AlertLevel,
  PerformanceAlert,
  AlertRule,
  PerformanceAlertSystemProps,
} from "./PerformanceAlertSystem";

// Performance Analytics Dashboard
export { PerformanceAnalyticsDashboard } from "./PerformanceAnalyticsDashboard";
export type {
  PerformanceAnalyticsDashboardProps,
} from "./PerformanceAnalyticsDashboard";

// Performance Optimization Dashboard
export { PerformanceOptimizationDashboard } from "./PerformanceOptimizationDashboard";
export type {
  PerformanceOptimizationDashboardProps,
} from "./PerformanceOptimizationDashboard";

// Resource Monitoring Dashboard
export { ResourceMonitoringDashboard } from "./ResourceMonitoringDashboard";
export type {
  ResourceMetrics,
  ResourceAlert,
  ScalingRecommendation,
  CapacityPlan,
  ResourceMonitoringDashboardProps,
} from "./ResourceMonitoringDashboard";

// Performance Dashboard
export { default as PerformanceDashboard } from "./PerformanceDashboard";
export type {
  PerformanceMetrics as DashboardPerformanceMetrics,
} from "./PerformanceDashboard";

// Performance Monitor
export { PerformanceMonitor, default as PerformanceMonitorDefault } from "./performance-monitor";
export type {
  PerformanceMetrics as MonitorPerformanceMetrics,
  PerformanceMonitorProps,
} from "./performance-monitor";

// ============================================================================
// Service Exports
// ============================================================================

export { performanceMonitor } from "@/services/performance-monitor";
export { performanceOptimizer } from "@/services/performance-optimizer";
export { resourceMonitor } from "@/services/resource-monitor";
export { performanceProfiler } from "@/services/performance-profiler";

// ============================================================================
// Type Exports from Services
// ============================================================================

export type { PerformanceMetrics, PerformanceEvent } from "@/services/performance-monitor";
export type { OptimizationSuggestion, OptimizationResult } from "@/services/performance-optimizer";
export type { ResourceStats, ResourceUsageDetail } from "@/services/resource-monitor";
export type { ProfilingData, ProfilingReport } from "@/services/performance-profiler";
