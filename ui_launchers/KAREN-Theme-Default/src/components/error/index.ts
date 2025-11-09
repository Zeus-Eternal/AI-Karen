// Central barrel for the Error system. Clean re-exports only.
// No side-effects, no circulars, type-safe with explicit type exports.

// Primary boundaries
export { ChatErrorBoundary } from "./ChatErrorBoundary";
export { GlobalErrorBoundary } from "./GlobalErrorBoundary";
export { ApiErrorBoundary, withApiErrorBoundary } from "./ApiErrorBoundary";
export { StreamingErrorBoundary } from "./StreamingErrorBoundary";

// Intelligent error UX
export { IntelligentErrorPanel } from "./IntelligentErrorPanel";
export type { IntelligentErrorPanelProps } from "./IntelligentErrorPanel";
export {
  withIntelligentError,
  intelligentErrorDecorator,
} from "./withIntelligentError";
export type {
  WithIntelligentErrorOptions,
  WithIntelligentErrorProps,
} from "./withIntelligentError";

// Toast rail
export { ErrorToast, ErrorToastContainer } from "./ErrorToast";
export type { ErrorToastProps, ToastContainerProps } from "./ErrorToast";

// Modern boundary variants
export { ModernErrorBoundary } from "./modern-error-boundary";

// Section-scoped boundaries & fallbacks
export * from "./section-error-boundaries";
export * from "./error-fallbacks";

// UI retry helpers
export * from "../ui/retry-components";
export { withRetry, useAsyncRetry, useRetryFetch } from "../ui/with-retry";
