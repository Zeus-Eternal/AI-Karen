/**
 * Comprehensive Observability Integration
 *
 * This module provides a unified interface for all observability features:
 * - Telemetry service with correlation tracking
 * - Performance monitoring with key metrics
 * - Error tracking and reporting
 * - User interaction analytics
 */

import { getTelemetryService, TelemetryService } from "./telemetry";
import {
  getPerformanceMonitor,
  PerformanceMonitor,
} from "./performanceMonitoring";
import { getErrorTracker, ErrorTracker } from "./errorTracking";
import { getUserAnalytics, UserAnalytics } from "./userAnalytics";

export interface ObservabilityConfig {
  // Telemetry configuration
  telemetry?: {
    enabled?: boolean;
    endpoint?: string;
    batchSize?: number;
    flushInterval?: number;
    debug?: boolean;
    sampling?: number;
  };

  // Performance monitoring configuration
  performance?: {
    enabled?: boolean;
    trackCoreWebVitals?: boolean;
    trackCustomMetrics?: boolean;
    trackMemoryUsage?: boolean;
  };

  // Error tracking configuration
  errorTracking?: {
    enabled?: boolean;
    endpoint?: string;
    apiKey?: string;
    captureUnhandledRejections?: boolean;
    captureConsoleErrors?: boolean;
    maxBreadcrumbs?: number;
    sampleRate?: number;
  };

  // User analytics configuration
  analytics?: {
    enabled?: boolean;
    endpoint?: string;
    apiKey?: string;
    trackPageViews?: boolean;
    trackClicks?: boolean;
    trackScrolling?: boolean;
    sampleRate?: number;
  };
}

class ObservabilityManager {
  private telemetryService: TelemetryService;
  private performanceMonitor: PerformanceMonitor;
  private errorTracker: ErrorTracker;
  private userAnalytics: UserAnalytics;
  private isInitialized = false;

  constructor(config: ObservabilityConfig = {}) {
    // Initialize all services with their respective configurations
    this.telemetryService = getTelemetryService(config.telemetry);
    this.performanceMonitor = getPerformanceMonitor();
    this.errorTracker = getErrorTracker(config.errorTracking);
    this.userAnalytics = getUserAnalytics(config.analytics);

    this.initialize();
  }

  private initialize(): void {
    if (this.isInitialized) return;

    // Set up cross-service integrations
    this.setupErrorIntegration();
    this.setupPerformanceIntegration();
    this.setupAnalyticsIntegration();

    this.isInitialized = true;
  }

  private setupErrorIntegration(): void {
    // Integrate error tracking with performance monitoring
    const originalCaptureError = this.errorTracker.captureError.bind(
      this.errorTracker
    );
    this.errorTracker.captureError = (error: Error, context: any = {}) => {
      // Add performance metrics to error context
      const performanceMetrics = this.performanceMonitor.getMetrics();
      context.performanceMetrics = performanceMetrics;

      return originalCaptureError(error, context);
    };
  }

  private setupPerformanceIntegration(): void {
    // Track performance metrics as telemetry events
    const originalMark = this.performanceMonitor.mark.bind(
      this.performanceMonitor
    );
    this.performanceMonitor.mark = (
      name: string,
      metadata?: Record<string, any>
    ) => {
      originalMark(name, metadata);

      // Also track as user analytics event
      this.userAnalytics.trackEvent("custom", {
        type: "performance_mark",
        markName: name,
        metadata,
      });
    };
  }

  private setupAnalyticsIntegration(): void {
    // Integrate analytics with error tracking
    const originalTrackEvent = this.userAnalytics.trackEvent.bind(
      this.userAnalytics
    );
    this.userAnalytics.trackEvent = (
      type: any,
      data: Record<string, any> = {}
    ) => {
      originalTrackEvent(type, data);

      // Add breadcrumb for user actions
      if (["click", "scroll", "focus", "blur"].includes(type)) {
        this.errorTracker.addBreadcrumb({
          category: "user",
          message: `User ${type} event`,
          level: "info",
          data: { eventType: type, ...data },
        });
      }
    };
  }

  // Unified API methods
  public setUser(userId: string, userData?: Record<string, any>): void {
    this.telemetryService.setUserId(userId);
    this.errorTracker.setUser(userId, userData);

    // Track user identification as analytics event
    this.userAnalytics.trackEvent("custom", {
      type: "user_identified",
      userId,
      userData,
    });
  }

  public setCorrelationId(correlationId: string): void {
    this.telemetryService.setCorrelationId(correlationId);

    // Add breadcrumb for correlation tracking
    this.errorTracker.addBreadcrumb({
      category: "custom",
      message: `Correlation ID set: ${correlationId}`,
      level: "debug",
      data: { correlationId },
    });
  }

  public trackChatInteraction(
    type: "send" | "stream_start" | "stream_complete" | "stream_abort",
    data: Record<string, any>
  ): void {
    const correlationId = data.messageId || this.generateCorrelationId();

    // Set correlation ID for this interaction
    this.setCorrelationId(correlationId);

    // Track performance marks
    switch (type) {
      case "send":
        this.performanceMonitor.mark("message_send_start", {
          messageId: data.messageId,
        });
        break;
      case "stream_start":
        this.performanceMonitor.markFirstToken();
        break;
      case "stream_complete":
        this.performanceMonitor.markStreamComplete();
        this.performanceMonitor.measure(
          "message_total_time",
          "message_send_start"
        );
        break;
    }

    // Track analytics
    switch (type) {
      case "send":
        this.userAnalytics.trackMessageSend(data as any);
        break;
      case "stream_start":
        this.userAnalytics.trackMessageStreamStart(data as any);
        break;
      case "stream_complete":
        this.userAnalytics.trackMessageStreamComplete(data as any);
        break;
      case "stream_abort":
        this.userAnalytics.trackMessageStreamAbort(data as any);
        break;
    }

    // Add breadcrumb
    this.errorTracker.addBreadcrumb({
      category: "custom",
      message: `Chat ${type}: ${data.messageId}`,
      level: "info",
      data,
    });
  }

  public trackFeatureUsage(
    featureName: string,
    featureData: Record<string, any> = {}
  ): void {
    // Track in analytics
    this.userAnalytics.trackFeatureUsage(featureName, featureData);

    // Track in telemetry
    this.telemetryService.track("feature_usage", {
      featureName,
      ...featureData,
    });

    // Add breadcrumb
    this.errorTracker.addBreadcrumb({
      category: "custom",
      message: `Feature used: ${featureName}`,
      level: "info",
      data: featureData,
    });
  }

  public startConversionFunnel(
    funnelName: string,
    steps: string[],
    metadata?: Record<string, any>
  ): void {
    const correlationId = this.generateCorrelationId();
    this.setCorrelationId(correlationId);

    // Start funnel in analytics
    this.userAnalytics.startFunnel(funnelName, steps, metadata);

    // Track in telemetry
    this.telemetryService.track(
      "funnel_started",
      {
        funnelName,
        steps,
        metadata,
      },
      correlationId
    );

    // Add breadcrumb
    this.errorTracker.addBreadcrumb({
      category: "custom",
      message: `Funnel started: ${funnelName}`,
      level: "info",
      data: { steps, metadata },
    });
  }

  public completeFunnelStep(
    funnelName: string,
    stepName: string,
    stepData?: Record<string, any>
  ): void {
    // Complete step in analytics
    this.userAnalytics.completeFunnelStep(funnelName, stepName, stepData);

    // Track performance if this is a key step
    if (
      ["signup", "login", "purchase", "complete"].includes(
        stepName.toLowerCase()
      )
    ) {
      this.performanceMonitor.mark(
        `funnel_${funnelName}_${stepName}`,
        stepData
      );
    }
  }

  public captureError(error: Error, context: Record<string, any> = {}): string {
    // Add current performance metrics to error context
    context.performanceMetrics = this.performanceMonitor.getMetrics();

    // Add current analytics stats
    context.analyticsStats = this.userAnalytics.getStats();

    return this.errorTracker.captureError(error, context);
  }

  public measurePerformance(
    operationName: string,
    operation: () => Promise<any> | any
  ): Promise<any> {
    const startMark = `${operationName}_start`;
    const endMark = `${operationName}_end`;

    this.performanceMonitor.mark(startMark);

    const executeOperation = async () => {
      try {
        const result = await Promise.resolve(operation());
        this.performanceMonitor.mark(endMark);
        const duration = this.performanceMonitor.measure(
          `${operationName}_duration`,
          startMark,
          endMark
        );

        // Track successful operation
        this.telemetryService.track("operation_complete", {
          operationName,
          duration,
          success: true,
        });

        return result;
      } catch (error) {
        this.performanceMonitor.mark(endMark);
        const duration = this.performanceMonitor.measure(
          `${operationName}_duration`,
          startMark,
          endMark
        );

        // Track failed operation
        this.telemetryService.track("operation_complete", {
          operationName,
          duration,
          success: false,
          error: error.message,
        });

        // Capture error with operation context
        this.captureError(error as Error, {
          operationName,
          duration,
          componentName: "PerformanceMeasurement",
        });

        throw error;
      }
    };

    return executeOperation();
  }

  private generateCorrelationId(): string {
    return `corr_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  public getHealthStatus(): {
    telemetry: any;
    performance: any;
    errorTracking: any;
    analytics: any;
    overall: "healthy" | "degraded" | "unhealthy";
  } {
    const telemetryStats = this.telemetryService.getStats();
    const performanceMetrics = this.performanceMonitor.getMetrics();
    const errorStats = this.errorTracker.getStats();
    const analyticsStats = this.userAnalytics.getStats();

    // Determine overall health
    let overall: "healthy" | "degraded" | "unhealthy" = "healthy";

    // Check for issues
    if (errorStats.storedReportCount > 10) {
      overall = "degraded";
    }

    if (
      performanceMetrics.memoryUsage &&
      performanceMetrics.memoryUsage > 100 * 1024 * 1024
    ) {
      // 100MB
      overall = "degraded";
    }

    if (telemetryStats.queueSize > 100) {
      overall = "unhealthy";
    }

    return {
      telemetry: telemetryStats,
      performance: performanceMetrics,
      errorTracking: errorStats,
      analytics: analyticsStats,
      overall,
    };
  }

  public async flush(): Promise<void> {
    await Promise.all([
      this.telemetryService.flush(),
      this.userAnalytics.flush(),
    ]);
  }

  public destroy(): void {
    this.telemetryService.destroy();
    this.performanceMonitor.destroy();
    this.errorTracker.destroy();
    this.userAnalytics.destroy();

    this.isInitialized = false;
  }
}

// Singleton instance
let observabilityManagerInstance: ObservabilityManager | null = null;

export const getObservabilityManager = (
  config?: ObservabilityConfig
): ObservabilityManager => {
  if (!observabilityManagerInstance) {
    observabilityManagerInstance = new ObservabilityManager(config);
  }
  return observabilityManagerInstance;
};

// Convenience functions for common operations
export const initializeObservability = (
  config?: ObservabilityConfig
): ObservabilityManager => {
  return getObservabilityManager(config);
};

export const setUser = (
  userId: string,
  userData?: Record<string, any>
): void => {
  getObservabilityManager().setUser(userId, userData);
};

export const trackChatMessage = (
  type: "send" | "stream_start" | "stream_complete" | "stream_abort",
  data: Record<string, any>
): void => {
  getObservabilityManager().trackChatInteraction(type, data);
};

export const trackFeature = (
  featureName: string,
  featureData?: Record<string, any>
): void => {
  getObservabilityManager().trackFeatureUsage(featureName, featureData);
};

export const startFunnel = (
  funnelName: string,
  steps: string[],
  metadata?: Record<string, any>
): void => {
  getObservabilityManager().startConversionFunnel(funnelName, steps, metadata);
};

export const completeFunnelStep = (
  funnelName: string,
  stepName: string,
  stepData?: Record<string, any>
): void => {
  getObservabilityManager().completeFunnelStep(funnelName, stepName, stepData);
};

export const captureError = (
  error: Error,
  context?: Record<string, any>
): string => {
  return getObservabilityManager().captureError(error, context);
};

export const measurePerformance = <T>(
  operationName: string,
  operation: () => Promise<T> | T
): Promise<T> => {
  return getObservabilityManager().measurePerformance(operationName, operation);
};

export const getHealthStatus = () => {
  return getObservabilityManager().getHealthStatus();
};

export const flushObservability = (): Promise<void> => {
  return getObservabilityManager().flush();
};

export default ObservabilityManager;
