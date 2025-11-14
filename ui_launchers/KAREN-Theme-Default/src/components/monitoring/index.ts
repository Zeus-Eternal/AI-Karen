/**
 * Monitoring dashboard components exports - Production Grade
 * Comprehensive monitoring, health tracking, and diagnostic components
 */

// ============================================================================
// Shared Types
// ============================================================================
export * from "./types";

// ============================================================================
// Component Exports
// ============================================================================

// Authentication Metrics
export { AuthenticationMetricsDisplay } from "./AuthenticationMetricsDisplay";
export type { AuthenticationMetricsDisplayProps } from "./AuthenticationMetricsDisplay";

// Connection Status
export { ConnectionStatusIndicator } from "./ConnectionStatusIndicator";
export type { ConnectionStatusIndicatorProps } from "./ConnectionStatusIndicator";

// Error Metrics
export { ErrorRateDisplay } from "./ErrorRateDisplay";
export type { ErrorRateDisplayProps } from "./ErrorRateDisplay";

// Performance Metrics
export { PerformanceMetricsDisplay } from "./PerformanceMetricsDisplay";
export type { PerformanceMetricsDisplayProps } from "./PerformanceMetricsDisplay";

// Real-Time Monitoring Dashboard
export { RealTimeMonitoringDashboard } from "./RealTimeMonitoringDashboard";
export type { RealTimeMonitoringDashboardProps } from "./RealTimeMonitoringDashboard";

// Extension Monitoring Dashboard
export { default as ExtensionMonitoringDashboard } from "./ExtensionMonitoringDashboard";
export type {
  AuthMetrics,
  ServiceHealthItem,
  ServiceHealthMetrics,
  EndpointPerfItem,
  ApiPerformanceMetrics,
  Severity,
  ActiveAlert,
  DashboardData,
} from "./ExtensionMonitoringDashboard";

// Health Dashboard (Capital H)
export { default as HealthDashboard } from "./HealthDashboard";
export type {
  HealthDashboardProps,
} from "./HealthDashboard";
export type { ServiceHealth, BackendHealthData } from "@/types/health";

// Endpoint Status Dashboard
export { EndpointStatusDashboard, default as EndpointStatusDashboardDefault } from "./endpoint-status-dashboard";
export type { EndpointStatusDashboardProps } from "./endpoint-status-dashboard";

// Endpoint Status Indicator
export { EndpointStatusIndicator, default as EndpointStatusIndicatorDefault } from "./endpoint-status-indicator";
export type { EndpointStatusIndicatorProps } from "./endpoint-status-indicator";

// Health Dashboard (lowercase h) - Alternative implementation
export { HealthDashboard as HealthDashboardAlt, default as HealthDashboardAltDefault } from "./health-dashboard";
export type { HealthDashboardProps as HealthDashboardAltProps } from "./health-dashboard";

// Monitoring Status
export { MonitoringStatus, default as MonitoringStatusDefault } from "./monitoring-status";
export type { MonitoringStatusProps } from "./monitoring-status";
