// ui_launchers/KAREN-Theme-Default/src/components/performance/index.ts
/**
 * Performance Components Index
 * 
 * Centralized export hub for all performance monitoring,
 * analytics, optimization, and resource-tracking components.
 * Keeps imports clean across the admin and analytics UIs.
 */

// ---- Dashboards & Analytics ----
export { PerformanceAnalyticsDashboard } from "./PerformanceAnalyticsDashboard";
export { PerformanceAlertSystem } from "./PerformanceAlertSystem";
export { PerformanceOptimizationDashboard } from "./PerformanceOptimizationDashboard";
export { ResourceMonitoringDashboard } from "./ResourceMonitoringDashboard";

// ---- Services ----
export { performanceMonitor } from "@/services/performance-monitor";
export { performanceOptimizer } from "@/services/performance-optimizer";
export { resourceMonitor } from "@/services/resource-monitor";
export { performanceProfiler } from "@/services/performance-profiler";

// ---- Types ----
export type { PerformanceMetrics, PerformanceEvent } from "@/services/performance-monitor";
export type { OptimizationSuggestion, OptimizationResult } from "@/services/performance-optimizer";
export type { ResourceStats, ResourceUsageDetail } from "@/services/resource-monitor";
export type { ProfilingData, ProfilingReport } from "@/services/performance-profiler";
