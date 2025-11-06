// Central barrel for the Error system. Clean re-exports only.
// No side-effects, no circulars, type-safe with explicit type exports.

// Primary boundaries
export { ChatErrorBoundary } from './ChatErrorBoundary';
export { GlobalErrorBoundary, withGlobalErrorBoundary } from './GlobalErrorBoundary';
export { ApiErrorBoundary, withApiErrorBoundary } from './ApiErrorBoundary';
export { StreamingErrorBoundary } from './StreamingErrorBoundary';
export { ErrorBoundary } from './ErrorBoundary';

// Intelligent error UX
export { IntelligentErrorPanel } from './IntelligentErrorPanel';
export type { IntelligentErrorPanelProps } from './IntelligentErrorPanel';
export {
  withIntelligentError,
  intelligentErrorDecorator,
} from './withIntelligentError';
export type {
  WithIntelligentErrorOptions,
  WithIntelligentErrorProps,
} from './withIntelligentError';

// Toast rail
export { ErrorToast, ErrorToastContainer } from './ErrorToast';
export type { ErrorToastProps, ToastContainerProps } from './ErrorToast';

// Modern boundary variants
export { ModernErrorBoundary } from './modern-error-boundary';

// Section-scoped boundaries & fallbacks
export * from './section-error-boundaries';
export * from './error-fallbacks';
export { SimpleErrorFallback } from './SimpleErrorFallback';

// Error tracking and analytics
export { default as ErrorAnalyticsDashboard } from './ErrorAnalyticsDashboard';
export { ErrorTracker } from './ErrorTracker';
export type { ErrorTrackerProps, TrackedError } from './ErrorTracker';

// UI retry helpers
export * from '../ui/retry-components';
export { withRetry, useAsyncRetry, useRetryFetch } from '../ui/with-retry';
