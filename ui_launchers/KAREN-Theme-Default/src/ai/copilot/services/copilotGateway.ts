import {
  CopilotBackendConfig,
  CopilotBackendRequest,
  CopilotBackendResponse,
  MemoryQuery,
  MemoryResult,
  MemoryOperation,
  PluginExecutionRequest,
  PluginExecutionResponse,
  LNMSelectionRequest,
  LNMSelectionResponse,
  PluginManifest,
  LNMInfo,
  SecurityContext,
  UITelemetryEvent,
  PerformanceMetric,
  ErrorReport
} from '../types/backend';

/**
 * CopilotGateway - Service for all backend communication
 * Handles requests to KAREN's CORTEX engine, MemoryManager/NeuroVault, and Prompt-First Plugin Engine
 */
export class CopilotGateway {
  private config: CopilotBackendConfig;
  private correlationId: string;
  private telemetryQueue: UITelemetryEvent[] = [];
  private performanceQueue: PerformanceMetric[] = [];
  private errorQueue: ErrorReport[] = [];
  private isStaticExport: boolean;
  private telemetrySuppressedReason: string | null = null;
  private lastTelemetryFailureAt: number | null = null;
  private readonly telemetryFailureCooldownMs = 30000;

  constructor(config: CopilotBackendConfig) {
    this.config = config;
    this.correlationId = config.correlationId || this.generateCorrelationId();
    // Check if we're in a static export environment
    this.isStaticExport = this.detectStaticExport();
  }

  /**
   * Detect if we're in a static export environment
   */
  private detectStaticExport(): boolean {
    // Check multiple indicators of static export environment
    return typeof window === 'undefined' ||
           process.env.NEXT_PHASE === 'phase-production-build' ||
           process.env.NEXT_PUBLIC_VERCEL_ENV === 'production' ||
           (typeof window !== 'undefined' && window.location.protocol === 'file:') ||
           (typeof window !== 'undefined' && !navigator.onLine);
  }

  /**
   * Generate a unique correlation ID for request tracing
   */
  private generateCorrelationId(): string {
    return `copilot_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get the current correlation ID
   */
  public getCorrelationId(): string {
    return this.correlationId;
  }

  /**
   * Update the correlation ID (typically at session start)
   */
  public updateCorrelationId(correlationId?: string): void {
    this.correlationId = correlationId || this.generateCorrelationId();
  }

  /**
   * Send a message to the backend for processing
   */
  public async sendMessage(request: CopilotBackendRequest): Promise<CopilotBackendResponse> {
    const startTime = Date.now();
    const traceId = this.generateCorrelationId();

    try {
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': this.correlationId,
          'X-Trace-ID': traceId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Record performance metric
      this.recordPerformanceMetric({
        metricName: 'copilot_chat_request',
        value: Date.now() - startTime,
        unit: 'ms',
        userId: this.config.userId,
        sessionId: this.config.sessionId
      });

      return data;
    } catch (error) {
      // Record error
      this.recordError({
        error: error instanceof Error ? error : new Error(String(error)),
        userId: this.config.userId,
        sessionId: this.config.sessionId
      });

      throw error;
    }
  }

  /**
   * Query the memory system
   */
  public async queryMemory(query: MemoryQuery): Promise<MemoryResult[]> {
    const startTime = Date.now();

    try {
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/memory/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': this.correlationId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify(query)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Record performance metric
      this.recordPerformanceMetric({
        metricName: 'memory_query',
        value: Date.now() - startTime,
        unit: 'ms',
        userId: this.config.userId,
        sessionId: this.config.sessionId
      });

      return data;
    } catch (error) {
      // Record error
      this.recordError({
        error: error instanceof Error ? error : new Error(String(error)),
        userId: this.config.userId,
        sessionId: this.config.sessionId
      });

      throw error;
    }
  }

  /**
   * Store a memory item
   */
  public async storeMemory(operation: MemoryOperation): Promise<{ id: string }> {
    const startTime = Date.now();

    try {
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/memory/store`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': this.correlationId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify(operation)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Record performance metric
      this.recordPerformanceMetric({
        metricName: 'memory_store',
        value: Date.now() - startTime,
        unit: 'ms',
        userId: this.config.userId,
        sessionId: this.config.sessionId
      });

      return data;
    } catch (error) {
      // Record error
      this.recordError({
        error: error instanceof Error ? error : new Error(String(error)),
        userId: this.config.userId,
        sessionId: this.config.sessionId
      });

      throw error;
    }
  }

  /**
   * Execute a plugin action
   */
  public async executePlugin(request: PluginExecutionRequest): Promise<PluginExecutionResponse> {
    const startTime = Date.now();

    try {
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/plugins/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': this.correlationId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Record performance metric
      this.recordPerformanceMetric({
        metricName: 'plugin_execution',
        value: Date.now() - startTime,
        unit: 'ms',
        userId: this.config.userId,
        sessionId: this.config.sessionId
      });

      return data;
    } catch (error) {
      // Record error
      this.recordError({
        error: error instanceof Error ? error : new Error(String(error)),
        userId: this.config.userId,
        sessionId: this.config.sessionId
      });

      throw error;
    }
  }

  /**
   * Get available plugins
   */
  public async getAvailablePlugins(): Promise<PluginManifest[]> {
    try {
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/plugins`, {
        method: 'GET',
        headers: {
          'X-Correlation-ID': this.correlationId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Record error
      this.recordError({
        error: error instanceof Error ? error : new Error(String(error)),
        userId: this.config.userId,
        sessionId: this.config.sessionId
      });

      throw error;
    }
  }

  /**
   * Select an LNM (Local Neural Model)
   */
  public async selectLNM(request: LNMSelectionRequest): Promise<LNMSelectionResponse> {
    const startTime = Date.now();

    try {
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/lnm/select`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': this.correlationId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Record performance metric
      this.recordPerformanceMetric({
        metricName: 'lnm_selection',
        value: Date.now() - startTime,
        unit: 'ms',
        userId: this.config.userId,
        sessionId: this.config.sessionId
      });

      return data;
    } catch (error) {
      // Record error
      this.recordError({
        error: error instanceof Error ? error : new Error(String(error)),
        userId: this.config.userId,
        sessionId: this.config.sessionId
      });

      throw error;
    }
  }

  /**
   * Get available LNMs
   */
  public async getAvailableLNMs(): Promise<LNMInfo[]> {
    try {
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/lnm`, {
        method: 'GET',
        headers: {
          'X-Correlation-ID': this.correlationId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Record error
      this.recordError({
        error: error instanceof Error ? error : new Error(String(error)),
        userId: this.config.userId,
        sessionId: this.config.sessionId
      });

      throw error;
    }
  }

  /**
   * Get user security context
   */
  public async getSecurityContext(): Promise<SecurityContext> {
    try {
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/security/context`, {
        method: 'GET',
        headers: {
          'X-Correlation-ID': this.correlationId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      // Record error
      this.recordError({
        error: error instanceof Error ? error : new Error(String(error)),
        userId: this.config.userId,
        sessionId: this.config.sessionId
      });

      throw error;
    }
  }

  /**
   * Record a UI telemetry event
   */
  public recordTelemetryEvent(event: Omit<UITelemetryEvent, 'timestamp'>): void {
    const telemetryEvent: UITelemetryEvent = {
      ...event,
      timestamp: new Date(),
      userId: this.config.userId,
      sessionId: this.config.sessionId
    } as UITelemetryEvent;

    this.telemetryQueue.push(telemetryEvent);
    
    // If queue gets too large, flush it
    if (this.telemetryQueue.length > 10) {
      this.flushTelemetryEvents();
    }
  }

  /**
   * Record a performance metric
   */
  public recordPerformanceMetric(metric: Omit<PerformanceMetric, 'timestamp'>): void {
    const performanceMetric: PerformanceMetric = {
      ...metric,
      timestamp: new Date(),
      userId: this.config.userId,
      sessionId: this.config.sessionId
    } as PerformanceMetric;

    this.performanceQueue.push(performanceMetric);
    
    // If queue gets too large, flush it
    if (this.performanceQueue.length > 10) {
      this.flushPerformanceMetrics();
    }
  }

  /**
   * Record an error
   */
  public recordError(error: Omit<ErrorReport, 'timestamp'>): void {
    const errorReport: ErrorReport = {
      ...error,
      timestamp: new Date(),
      userId: this.config.userId,
      sessionId: this.config.sessionId
    } as ErrorReport;

    this.errorQueue.push(errorReport);
    
    // If queue gets too large, flush it
    if (this.errorQueue.length > 5) {
      this.flushErrors();
    }
  }

  /**
   * Flush telemetry events to the backend
   */
  public async flushTelemetryEvents(): Promise<void> {
    // Skip telemetry flushing during static export, offline, or invalid base URL
    if (this.telemetryQueue.length === 0 || !this.canSendTelemetry()) return;

    const events = [...this.telemetryQueue];
    this.telemetryQueue = [];

    try {
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/telemetry/events`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': this.correlationId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify({ events })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      this.lastTelemetryFailureAt = null;
    } catch (error) {
      // If telemetry fails, store events for later retry instead of keeping them in memory
      this.markTelemetryFailure(error);
      this.storeTelemetryForRetry(events);
    }
  }

  /**
   * Flush performance metrics to the backend
   */
  public async flushPerformanceMetrics(): Promise<void> {
    // Skip performance metrics flushing during static export, offline, or invalid base URL
    if (this.performanceQueue.length === 0 || !this.canSendTelemetry()) return;

    const metrics = [...this.performanceQueue];
    this.performanceQueue = [];

    try {
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/telemetry/performance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': this.correlationId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify({ metrics })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      this.lastTelemetryFailureAt = null;
    } catch (error) {
      // If telemetry fails, store metrics for later retry instead of keeping them in memory
      this.markTelemetryFailure(error);
      this.storePerformanceMetricsForRetry(metrics);
    }
  }

  /**
   * Flush errors to the backend
   */
  public async flushErrors(): Promise<void> {
    // Skip error flushing during static export, offline, or invalid base URL
    if (this.errorQueue.length === 0 || !this.canSendTelemetry()) return;

    const errors = [...this.errorQueue];
    this.errorQueue = [];

    try {
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/telemetry/errors`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': this.correlationId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify({ errors })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      this.lastTelemetryFailureAt = null;
    } catch (error) {
      // If error reporting fails, store in localStorage for later retry
      // instead of keeping in memory queue
      this.storeErrorsForRetry(errors);
      this.markTelemetryFailure(error);
    }
  }

  /**
   * Check if the client is online
   */
  private isOnline(): boolean {
    return typeof window !== 'undefined' && navigator.onLine;
  }

  /**
   * Determine if telemetry can be sent without spamming the console when misconfigured.
   */
  private canSendTelemetry(): boolean {
    if (this.isStaticExport) return false;
    if (!this.isOnline()) return false;
    if (this.lastTelemetryFailureAt && Date.now() - this.lastTelemetryFailureAt < this.telemetryFailureCooldownMs) {
      this.logTelemetrySuppression('recent_failure_backoff');
      return false;
    }
    if (!this.config.baseUrl) {
      this.logTelemetrySuppression('missing_base_url');
      return false;
    }

    try {
      // Validate that baseUrl can compose into a valid URL (supports relative paths)
      new URL(this.config.baseUrl, typeof window !== 'undefined' ? window.location.origin : 'http://localhost');
    } catch (error) {
      this.logTelemetrySuppression('invalid_base_url', error);
      return false;
    }

    this.telemetrySuppressedReason = null;
    this.lastTelemetryFailureAt = null;
    return true;
  }

  /**
   * Log telemetry suppression reasons only once.
   */
  private logTelemetrySuppression(reason: string, error?: unknown): void {
    if (this.telemetrySuppressedReason === reason) return;
    this.telemetrySuppressedReason = reason;
    console.debug(`Skipping telemetry send (${reason}).`, error);
  }

  /**
   * Mark a telemetry failure and start a short cooldown to avoid repeated fetch attempts.
   */
  private markTelemetryFailure(error: unknown): void {
    this.lastTelemetryFailureAt = Date.now();
    this.logTelemetrySuppression('recent_failure_backoff', error);
  }

  /**
   * Store telemetry events in localStorage for later retry
   */
  private storeTelemetryForRetry(events: UITelemetryEvent[]): void {
    if (typeof window === 'undefined') return;
    
    try {
      const storedEvents = JSON.parse(localStorage.getItem('karen_telemetry_queue') || '[]');
      const updatedEvents = [...storedEvents, ...events];
      // Limit stored events to prevent localStorage bloat
      const limitedEvents = updatedEvents.slice(-100);
      localStorage.setItem('karen_telemetry_queue', JSON.stringify(limitedEvents));
    } catch (e) {
      console.error('Failed to store telemetry events for retry:', e);
    }
  }

  /**
   * Store performance metrics in localStorage for later retry
   */
  private storePerformanceMetricsForRetry(metrics: PerformanceMetric[]): void {
    if (typeof window === 'undefined') return;
    
    try {
      const storedMetrics = JSON.parse(localStorage.getItem('karen_performance_queue') || '[]');
      const updatedMetrics = [...storedMetrics, ...metrics];
      // Limit stored metrics to prevent localStorage bloat
      const limitedMetrics = updatedMetrics.slice(-100);
      localStorage.setItem('karen_performance_queue', JSON.stringify(limitedMetrics));
    } catch (e) {
      console.error('Failed to store performance metrics for retry:', e);
    }
  }

  /**
   * Store errors in localStorage for later retry
   */
  private storeErrorsForRetry(errors: ErrorReport[]): void {
    if (typeof window === 'undefined') return;
    
    try {
      const storedErrors = JSON.parse(localStorage.getItem('karen_error_queue') || '[]');
      const updatedErrors = [...storedErrors, ...errors];
      // Limit stored errors to prevent localStorage bloat
      const limitedErrors = updatedErrors.slice(-100);
      localStorage.setItem('karen_error_queue', JSON.stringify(limitedErrors));
    } catch (e) {
      console.error('Failed to store errors for retry:', e);
    }
  }

  /**
   * Retry sending stored telemetry events with exponential backoff
   */
  public async retryStoredTelemetryEvents(): Promise<void> {
    if (typeof window === 'undefined' || !this.canSendTelemetry()) return;
    
    let storedEvents: UITelemetryEvent[] = [];
    try {
      storedEvents = JSON.parse(localStorage.getItem('karen_telemetry_queue') || '[]');
      if (storedEvents.length === 0) return;
      
      // Get retry count from localStorage, default to 0
      const retryCount = parseInt(localStorage.getItem('karen_telemetry_retry_count') || '0', 10);
      
      // Calculate exponential backoff delay (max 30 seconds)
      const maxDelayMs = 30000;
      const delayMs = Math.min(Math.pow(2, retryCount) * 1000, maxDelayMs);
      
      // Wait for the backoff delay
      await new Promise(resolve => setTimeout(resolve, delayMs));
      
      // Clear localStorage before attempting to send
      localStorage.removeItem('karen_telemetry_queue');
      localStorage.removeItem('karen_telemetry_retry_count');
      
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/telemetry/events`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': this.correlationId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify({ events: storedEvents })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      this.lastTelemetryFailureAt = null;
    } catch (error) {
      this.markTelemetryFailure(error);
      // Increment retry count and put events back in localStorage for later retry
      const retryCount = parseInt(localStorage.getItem('karen_telemetry_retry_count') || '0', 10);
      localStorage.setItem('karen_telemetry_retry_count', (retryCount + 1).toString());
      this.storeTelemetryForRetry(storedEvents);
    }
  }

  /**
   * Retry sending stored performance metrics with exponential backoff
   */
  public async retryStoredPerformanceMetrics(): Promise<void> {
    if (typeof window === 'undefined' || !this.canSendTelemetry()) return;
    
    let storedMetrics: PerformanceMetric[] = [];
    try {
      storedMetrics = JSON.parse(localStorage.getItem('karen_performance_queue') || '[]');
      if (storedMetrics.length === 0) return;
      
      // Get retry count from localStorage, default to 0
      const retryCount = parseInt(localStorage.getItem('karen_performance_retry_count') || '0', 10);
      
      // Calculate exponential backoff delay (max 30 seconds)
      const maxDelayMs = 30000;
      const delayMs = Math.min(Math.pow(2, retryCount) * 1000, maxDelayMs);
      
      // Wait for backoff delay
      await new Promise(resolve => setTimeout(resolve, delayMs));
      
      // Clear localStorage before attempting to send
      localStorage.removeItem('karen_performance_queue');
      localStorage.removeItem('karen_performance_retry_count');
      
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/telemetry/performance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': this.correlationId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify({ metrics: storedMetrics })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      this.lastTelemetryFailureAt = null;
    } catch (error) {
      this.markTelemetryFailure(error);
      // Increment retry count and put metrics back in localStorage for later retry
      const retryCount = parseInt(localStorage.getItem('karen_performance_retry_count') || '0', 10);
      localStorage.setItem('karen_performance_retry_count', (retryCount + 1).toString());
      this.storePerformanceMetricsForRetry(storedMetrics);
    }
  }

  /**
   * Retry sending stored errors with exponential backoff
   */
  public async retryStoredErrors(): Promise<void> {
    if (typeof window === 'undefined' || !this.canSendTelemetry()) return;
    
    let storedErrors: ErrorReport[] = [];
    try {
      storedErrors = JSON.parse(localStorage.getItem('karen_error_queue') || '[]');
      if (storedErrors.length === 0) return;
      
      // Get retry count from localStorage, default to 0
      const retryCount = parseInt(localStorage.getItem('karen_error_retry_count') || '0', 10);
      
      // Calculate exponential backoff delay (max 30 seconds)
      const maxDelayMs = 30000;
      const delayMs = Math.min(Math.pow(2, retryCount) * 1000, maxDelayMs);
      
      // Wait for backoff delay
      await new Promise(resolve => setTimeout(resolve, delayMs));
      
      // Clear localStorage before attempting to send
      localStorage.removeItem('karen_error_queue');
      localStorage.removeItem('karen_error_retry_count');
      
      // Ensure baseUrl doesn't end with slash and path doesn't start with slash
      const baseUrl = this.config.baseUrl.replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/telemetry/errors`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': this.correlationId,
          ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
        },
        body: JSON.stringify({ errors: storedErrors })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      this.lastTelemetryFailureAt = null;
    } catch (error) {
      this.markTelemetryFailure(error);
      // Increment retry count and put errors back in localStorage for later retry
      const retryCount = parseInt(localStorage.getItem('karen_error_retry_count') || '0', 10);
      localStorage.setItem('karen_error_retry_count', (retryCount + 1).toString());
      this.storeErrorsForRetry(storedErrors);
    }
  }

  /**
   * Flush all pending telemetry, metrics, and errors
   */
  public async flushAll(): Promise<void> {
    // Skip all flushing during static export, offline, or invalid base URL
    if (!this.canSendTelemetry()) return;
    
    // Try to send any stored data first
    await Promise.all([
      this.retryStoredTelemetryEvents(),
      this.retryStoredPerformanceMetrics(),
      this.retryStoredErrors()
    ]);
    
    // Then flush any pending data
    await Promise.all([
      this.flushTelemetryEvents(),
      this.flushPerformanceMetrics(),
      this.flushErrors()
    ]);
  }
}
