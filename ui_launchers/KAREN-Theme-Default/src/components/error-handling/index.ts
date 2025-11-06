// Error Handling System - Central Exports
// Production-grade error boundary components and utilities

// Core error boundaries
export { ErrorBoundary } from './ErrorBoundary';
export type { ErrorFallbackProps as ErrorBoundaryFallbackProps } from './ErrorBoundary';

export { GlobalErrorBoundary } from './GlobalErrorBoundary';
export type { ErrorFallbackProps as GlobalErrorFallbackProps } from './GlobalErrorBoundary';

// Error fallback UI components
export { ProductionErrorFallback } from './ProductionErrorFallback';

// Error analytics dashboard
export { ErrorAnalyticsDashboard } from './ErrorAnalyticsDashboard';
export type { ErrorAnalyticsDashboardProps } from './ErrorAnalyticsDashboard';

// Error recovery panel
export { ErrorRecoveryPanel } from './ErrorRecoveryPanel';
export type { ErrorRecoveryPanelProps } from './ErrorRecoveryPanel';

// Re-export error reporting utilities
export { default as errorReportingService } from '../../utils/error-reporting';
export type { ErrorReport, ErrorBreadcrumb, ErrorReportingConfig } from '../../utils/error-reporting';

// Re-export error analytics
export { ErrorAnalytics } from '../../lib/error-handling/error-analytics';
export type {
  ErrorAnalyticsConfig,
  ErrorMetrics,
  ErrorAnalyticsReport
} from '../../lib/error-handling/error-analytics';

// Re-export error recovery
export { ErrorRecoveryManager } from '../../lib/error-handling/error-recovery-manager';
export type {
  RecoveryAction,
  RecoveryStrategy,
  RecoveryResult
} from '../../lib/error-handling/error-recovery-manager';
