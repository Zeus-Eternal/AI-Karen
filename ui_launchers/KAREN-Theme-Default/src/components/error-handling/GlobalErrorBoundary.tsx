// ui_launchers/KAREN-Theme-Default/src/components/error-handling/GlobalErrorBoundary.tsx
"use client";

/**
 * Global Error Boundary for Production-Grade Error Handling
 *
 * Provides comprehensive error handling with graceful degradation,
 * intelligent recovery mechanisms, and detailed error analytics.
 */

import React, { Component, ErrorInfo, ReactNode } from "react";
import {
  errorReportingService,
  type ErrorReport,
} from "../../utils/error-reporting";
import { ErrorRecoveryManager } from "../../lib/error-handling/error-recovery-manager";
import { ErrorAnalytics } from "../../lib/error-handling/error-analytics";
import { ProductionErrorFallback } from "./ProductionErrorFallback";
import {
  ErrorCategory,
  ErrorSeverity,
  type CategorizedError,
} from "../../lib/errors/error-categories";

/* ------------------------------------------------------------------ */
/* Types                                                              */
/* ------------------------------------------------------------------ */

interface PerformanceWithMemory extends Performance {
  memory?: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
  };
}

interface Props {
  children: ReactNode;
  fallbackComponent?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: ErrorInfo, report: ErrorReport) => void;
  enableRecovery?: boolean; // default: true
  enableAnalytics?: boolean; // default: true
  section?: string;
  level?: "global" | "feature" | "component";
}

export type GlobalErrorBoundaryProps = Props;

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorReport: ErrorReport | null;
  recoveryAttempts: number;
  isRecovering: boolean;
  fallbackMode: "full" | "degraded" | "minimal";
}

export interface ErrorFallbackProps {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorReport: ErrorReport | null;
  onRetry: () => void;
  onRecover: () => void;
  onReport: () => void;
  recoveryAttempts: number;
  maxRecoveryAttempts: number;
  fallbackMode: "full" | "degraded" | "minimal";
  isRecovering: boolean;
}

/* ------------------------------------------------------------------ */
/* Component                                                          */
/* ------------------------------------------------------------------ */

export class GlobalErrorBoundary extends Component<Props, State> {
  private recoveryManager: ErrorRecoveryManager;
  private analytics: ErrorAnalytics;
  private readonly maxRecoveryAttempts = 3;
  private recoveryTimeout: ReturnType<typeof setTimeout> | null = null;

  static defaultProps: Partial<Props> = {
    enableRecovery: true,
    enableAnalytics: true,
    level: "component",
  };

  constructor(props: Props) {
    super(props);

    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorReport: null,
      recoveryAttempts: 0,
      isRecovering: false,
      fallbackMode: "full",
    };

    this.recoveryManager = ErrorRecoveryManager.getInstance();

    this.analytics = new ErrorAnalytics({
      enabled: props.enableAnalytics !== false,
      section: props.section || "unknown",
    });
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      fallbackMode: "full",
    };
  }

  async componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Generate comprehensive error report
    const errorReport = await this.generateErrorReport(error, errorInfo);

    // Update state with error details
    this.setState({
      errorInfo,
      errorReport,
      fallbackMode: this.determineFallbackMode(error),
    });

    // Report error to monitoring services
    await this.reportError(error, errorInfo, errorReport);

    // Track error analytics
    this.analytics.trackError(error, errorInfo, {
      section: this.props.section,
      level: this.props.level || "component",
      recoveryAttempts: this.state.recoveryAttempts,
    });

    // Custom error handler hook
    if (this.props.onError) {
      this.props.onError(error, errorInfo, errorReport);
    }

    // Attempt automatic recovery if enabled
    if (this.props.enableRecovery !== false) {
      this.attemptRecovery();
    }
  }

  /* ---------------------------------------------- */
  /* Report / Analytics                              */
  /* ---------------------------------------------- */

  private async generateErrorReport(
    error: Error,
    errorInfo: ErrorInfo
  ): Promise<ErrorReport> {
    const safeWindow = typeof window !== "undefined" ? window : undefined;
    const safeNavigator =
      typeof navigator !== "undefined" ? navigator : ({} as Navigator);

    const report: ErrorReport = {
      id: `global-error-${Date.now()}-${Math.random()
        .toString(36)
        .slice(2, 11)}`,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo?.componentStack || undefined,
      section: this.props.section || "global",
      timestamp: new Date().toISOString(),
      url: safeWindow?.location?.href,
      userAgent: safeNavigator.userAgent,
      sessionId: this.getSessionId(),
      retryCount: this.state.recoveryAttempts,
      severity: this.determineSeverity(error),
      category: this.categorizeError(error),
      context: {
        level: this.props.level || "component",
        section: this.props.section,
        recoveryEnabled: this.props.enableRecovery !== false,
        analyticsEnabled: this.props.enableAnalytics !== false,
        userAgent: safeNavigator.userAgent,
        viewport: safeWindow
          ? {
              width: safeWindow.innerWidth,
              height: safeWindow.innerHeight,
            }
          : undefined,
        memory: this.getMemoryInfo(),
        performance: this.getPerformanceInfo(),
      },
      breadcrumbs: [], // TODO: wire actual breadcrumbs if available
    };

    return report;
  }

  private determineSeverity(error: Error): ErrorReport["severity"] {
    const message = (error.message || "").toLowerCase();
    const name = (error.name || "").toLowerCase();

    // Critical errors that break the entire application
    if (
      this.props.level === "global" ||
      message.includes("chunk") ||
      message.includes("loading") ||
      name.includes("chunkloaderror")
    ) {
      return "critical";
    }

    // High severity errors that break major features
    if (
      this.props.level === "feature" ||
      message.includes("network") ||
      message.includes("auth") ||
      message.includes("permission")
    ) {
      return "high";
    }

    // Medium severity errors that break components
    if (
      message.includes("render") ||
      message.includes("hook") ||
      this.state.recoveryAttempts > 1
    ) {
      return "medium";
    }

    return "low";
  }

  private categorizeError(error: Error): ErrorReport["category"] {
    const message = (error.message || "").toLowerCase();
    const name = (error.name || "").toLowerCase();

    if (message.includes("network") || message.includes("fetch"))
      return "network";
    if (message.includes("auth") || message.includes("token")) return "auth";
    if (message.includes("chunk") || message.includes("loading")) return "ui";
    if (name.includes("type") || name.includes("reference")) return "ui";
    return "unknown";
  }

  private determineFallbackMode(error: Error): State["fallbackMode"] {
    const severity = this.determineSeverity(error);
    const attempts = this.state.recoveryAttempts;

    if (severity === "critical" || attempts >= this.maxRecoveryAttempts)
      return "minimal";
    if (severity === "high" || attempts >= 2) return "degraded";
    return "full";
  }

  private async reportError(
    error: Error,
    errorInfo: ErrorInfo,
    errorReport: ErrorReport
  ) {
    try {
      // Primary reporting
      await errorReportingService.reportError(error, {
        componentStack: errorInfo.componentStack || undefined
      }, {
        section: this.props.section,
        retryCount: this.state.recoveryAttempts,
        level: this.props.level,
      });

      // External monitoring integrations
      await this.reportToMonitoringServices(errorReport);

      // Local storage for offline analysis
      this.storeErrorForAnalysis(errorReport);
    } catch {
      // Swallow reporting errors to avoid infinite loops
    }
  }

  private async reportToMonitoringServices(errorReport: ErrorReport) {
    // Sentry (if injected on window)
    try {
      if (typeof window !== "undefined") {
        const windowWithSentry = window as Window & {
          Sentry?: {
            captureException: (error: unknown, context?: unknown) => void;
          };
        };
        windowWithSentry.Sentry?.captureException(this.state.error, {
          tags: {
            section: errorReport.section,
            severity: errorReport.severity,
            category: errorReport.category,
          },
          extra: errorReport.context,
          fingerprint: [errorReport.message, errorReport.section],
        });
      }
    } catch {
      // no-op
    }

    // Custom monitoring endpoint
    const endpoint = process.env.NEXT_PUBLIC_ERROR_MONITORING_ENDPOINT;
    if (endpoint) {
      try {
        await fetch(endpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${
              process.env.NEXT_PUBLIC_ERROR_MONITORING_API_KEY || ""
            }`,
          },
          body: JSON.stringify(errorReport),
        });
      } catch {
        // no-op
      }
    }
  }

  private storeErrorForAnalysis(errorReport: ErrorReport) {
    try {
      if (typeof window === "undefined") return;
      const key = `error_analysis_${this.props.section || "global"}`;
      const stored = window.localStorage.getItem(key);
      const reports = stored ? JSON.parse(stored) : [];
      reports.push(errorReport);
      const recent = reports.slice(-50); // cap per section
      window.localStorage.setItem(key, JSON.stringify(recent));
    } catch {
      // no-op
    }
  }

  /* ---------------------------------------------- */
  /* Recovery                                        */
  /* ---------------------------------------------- */

  private attemptRecovery = async () => {
    if (this.state.recoveryAttempts >= this.maxRecoveryAttempts) return;

    this.setState({ isRecovering: true });

    try {
      // Create a categorized error that matches the recovery manager contract
      const categorizedError: CategorizedError = {
        category: ErrorCategory.UNKNOWN,
        severity: ErrorSeverity.MEDIUM,
        code: "UI_RECOVERY_ATTEMPT",
        message: this.state.error?.message || "unknown UI error",
        userMessage: "Attempting automatic recovery",
        retryable: true,
        maxRetries: this.maxRecoveryAttempts,
        backoffStrategy: "exponential",
        fallbackAction: "UI_RECOVERY",
        timestamp: new Date(),
        correlationId: this.state.errorReport?.id ?? undefined,
        context: {
          section: this.props.section || "unknown",
          level: this.props.level || "component",
          isRecoverable: true,
        },
      };
      const strategy = await this.recoveryManager.attemptRecovery(
        categorizedError
      );

      await this.executeRecoveryStrategy(strategy);
    } catch {
      // If strategy selection/execution fails, degrade to minimal
      this.setState({ isRecovering: false, fallbackMode: "minimal" });
    }
  };

  private getStrategyDelay(strategy: unknown): number {
    if (typeof strategy === "object" && strategy !== null) {
      const delayValue = (strategy as { delay?: unknown }).delay;
      if (typeof delayValue === "number") {
        return delayValue;
      }
    }
    return 1000;
  }

  private async executeRecoveryStrategy(strategy: unknown) {
    const delay = this.getStrategyDelay(strategy);

    this.recoveryTimeout = setTimeout(() => {
      this.setState((prev) => ({
        hasError: false,
        error: null,
        errorInfo: null,
        errorReport: null,
        recoveryAttempts: prev.recoveryAttempts + 1,
        isRecovering: false,
        fallbackMode: "full",
      }));
    }, delay);
  }

  /* ---------------------------------------------- */
  /* UI Callbacks                                    */
  /* ---------------------------------------------- */

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorReport: null,
      isRecovering: false,
      fallbackMode: "full",
    });
  };

  private handleRecover = async () => {
    await this.attemptRecovery();
  };

  private handleReport = async () => {
    if (this.state.error && this.state.errorInfo && this.state.errorReport) {
      await this.reportError(
        this.state.error,
        this.state.errorInfo,
        this.state.errorReport
      );
    }
  };

  /* ---------------------------------------------- */
  /* Utilities                                       */
  /* ---------------------------------------------- */

  private getSessionId(): string {
    if (typeof window === "undefined") return `session-${Date.now()}-ssr`;
    let sessionId = window.sessionStorage.getItem("error_session_id");
    if (!sessionId) {
      sessionId = `session-${Date.now()}-${Math.random()
        .toString(36)
        .slice(2, 11)}`;
      window.sessionStorage.setItem("error_session_id", sessionId);
    }
    return sessionId;
  }

  private getMemoryInfo(): Record<string, unknown> | undefined {
    try {
      if (typeof performance === "undefined") return undefined;
      const perf = performance as PerformanceWithMemory;
      if (perf.memory) {
        const { usedJSHeapSize, totalJSHeapSize, jsHeapSizeLimit } = perf.memory;
        return { usedJSHeapSize, totalJSHeapSize, jsHeapSizeLimit };
      }
    } catch {
      // no-op
    }
    return undefined;
  }

  private getPerformanceInfo(): Record<string, unknown> | undefined {
    try {
      if (
        typeof performance !== "undefined" &&
        "getEntriesByType" in performance
      ) {
        const nav = performance.getEntriesByType("navigation")[0] as
          | PerformanceNavigationTiming
          | undefined;
        const firstPaint =
          performance.getEntriesByName("first-paint")[0]?.startTime ?? null;
        const fcp =
          performance.getEntriesByName("first-contentful-paint")[0]
            ?.startTime ?? null;

        return nav
          ? {
              loadTime: nav.loadEventEnd - nav.loadEventStart,
              domContentLoaded:
                nav.domContentLoadedEventEnd - nav.domContentLoadedEventStart,
              firstPaint,
              firstContentfulPaint: fcp,
            }
          : { firstPaint, firstContentfulPaint: fcp };
      }
    } catch {
      // no-op
    }
    return undefined;
  }

  componentWillUnmount() {
    if (this.recoveryTimeout) clearTimeout(this.recoveryTimeout);
  }

  /* ---------------------------------------------- */
  /* Render                                          */
  /* ---------------------------------------------- */

  render() {
    if (this.state.hasError) {
      const FallbackComponent =
        this.props.fallbackComponent || ProductionErrorFallback;

      return (
        <FallbackComponent
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          errorReport={this.state.errorReport}
          onRetry={this.handleRetry}
          onRecover={this.handleRecover}
          onReport={this.handleReport}
          recoveryAttempts={this.state.recoveryAttempts}
          maxRecoveryAttempts={this.maxRecoveryAttempts}
          fallbackMode={this.state.fallbackMode}
          isRecovering={this.state.isRecovering}
        />
      );
    }
    return this.props.children;
  }
}

/* ------------------------------------------------------------------ */
/* HOC                                                                */
/* ------------------------------------------------------------------ */

export default GlobalErrorBoundary;
