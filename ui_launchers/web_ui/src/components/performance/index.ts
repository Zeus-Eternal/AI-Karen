/**
 * Performance Components Index
 * Exports all performance monitoring and analytics components
 */

import { export { PerformanceAnalyticsDashboard } from './PerformanceAnalyticsDashboard';
import { export { PerformanceAlertSystem } from './PerformanceAlertSystem';
import { export { PerformanceOptimizationDashboard } from './PerformanceOptimizationDashboard';
import { export { ResourceMonitoringDashboard } from './ResourceMonitoringDashboard';

// Re-export performance services for convenience
import { export { performanceMonitor } from '@/services/performance-monitor';
import { export { performanceOptimizer } from '@/services/performance-optimizer';
import { export { resourceMonitor } from '@/services/resource-monitor';
import { export { performanceProfiler } from '@/services/performance-profiler';

// Re-export types
export type {
import { } from '@/services/performance-monitor';

export type {
import { } from '@/services/performance-optimizer';

export type {
import { } from '@/services/resource-monitor';

export type {
import { } from '@/services/performance-profiler';