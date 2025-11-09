/**
 * AG-UI Error Handler with Fallback Strategies
 *
 * Provides error handling and fallback mechanisms for AG-UI components
 * including graceful degradation to simplified interfaces.
 */
import type React from 'react';
import type { GridApi } from 'ag-grid-community';

export enum AGUIErrorType {
  GRID_LOAD_ERROR = 'grid_load_error',
  GRID_RENDER_ERROR = 'grid_render_error',
  CHART_RENDER_ERROR = 'chart_render_error',
  DATA_FETCH_ERROR = 'data_fetch_error',
  COMPONENT_CRASH = 'component_crash',
  MEMORY_ERROR = 'memory_error',
  TIMEOUT_ERROR = 'timeout_error',
}

export enum FallbackStrategy {
  SIMPLE_TABLE = 'simple_table',
  CACHED_DATA = 'cached_data',
  LOADING_STATE = 'loading_state',
  ERROR_MESSAGE = 'error_message',
  RETRY_MECHANISM = 'retry_mechanism',
}

export interface AGUIErrorContext {
  component: string;
  errorType: AGUIErrorType;
  originalError: Error;
  data?: any[];
  columns?: any[];
  timestamp: string;
  retryCount: number;
}

export interface FallbackResponse {
  strategy: FallbackStrategy;
  component: React.ComponentType<any> | null;
  data: any[];
  columns: any[];
  message: string;
  retryAvailable: boolean;
  degradedFeatures: string[];
}

export interface CircuitBreakerState {
  isOpen: boolean;
  failureCount: number;
  lastFailureTime: number;
  halfOpenAttempts: number;
}

export type CacheEntry<T> = {
  payload: T;
  timestamp: string; // ISO
};

export class AGUIErrorHandler {
  private static instance: AGUIErrorHandler;

  private errorCache: Map<string, CacheEntry<any>> = new Map();
  private circuitBreakers: Map<string, CircuitBreakerState> = new Map();
  private retryAttempts: Map<string, number> = new Map();

  // Configuration
  private readonly maxRetries = 3;
  private readonly circuitBreakerThreshold = 5;
  private readonly circuitBreakerTimeout = 60_000; // 1 minute
  private readonly cacheTimeout = 300_000; // 5 minutes

  private constructor() {
    this.initializeCircuitBreakers();
  }

  public static getInstance(): AGUIErrorHandler {
    if (!AGUIErrorHandler.instance) {
      AGUIErrorHandler.instance = new AGUIErrorHandler();
    }
    return AGUIErrorHandler.instance;
  }

  private initializeCircuitBreakers(): void {
    const components = ['grid', 'chart', 'analytics', 'memory'];
    const now = Date.now();
    components.forEach((component) => {
      if (!this.circuitBreakers.has(component)) {
        this.circuitBreakers.set(component, {
          isOpen: false,
          failureCount: 0,
          lastFailureTime: 0 || now,
          halfOpenAttempts: 0,
        });
      }
    });
  }

  /**
   * Handle AG-Grid specific errors
   */
  public async handleGridError(
    error: Error,
    gridApi?: GridApi,
    data?: any[],
    columns?: any[]
  ): Promise<FallbackResponse> {
    const context: AGUIErrorContext = {
      component: 'grid',
      errorType: this.classifyGridError(error),
      originalError: error,
      data,
      columns,
      timestamp: new Date().toISOString(),
      retryCount: this.getRetryCount('grid'),
    };

    // Circuit breaker
    if (this.isCircuitBreakerOpen('grid')) {
      const fb = this.createSimpleTableFallback(context);
      this.cacheFallback('grid', fb);
      return fb;
    }

    // Record failure
    this.recordFailure('grid');

    // Strategy
    switch (context.errorType) {
      case AGUIErrorType.GRID_LOAD_ERROR: {
        const fb = await this.handleGridLoadError(context);
        this.cacheFallback('grid', fb);
        return fb;
      }
      case AGUIErrorType.GRID_RENDER_ERROR: {
        const fb = await this.handleGridRenderError(context);
        this.cacheFallback('grid', fb);
        return fb;
      }
      case AGUIErrorType.DATA_FETCH_ERROR: {
        const fb = await this.handleDataFetchError(context);
        this.cacheFallback('grid', fb);
        return fb;
      }
      default: {
        const fb = this.createSimpleTableFallback(context);
        this.cacheFallback('grid', fb);
        return fb;
      }
    }
  }

  /**
   * Handle AG-Charts specific errors
   */
  public async handleChartError(
    error: Error,
    chartData?: any[],
    chartOptions?: any
  ): Promise<FallbackResponse> {
    const context: AGUIErrorContext = {
      component: 'chart',
      errorType: this.classifyChartError(error),
      originalError: error,
      data: chartData,
      columns: [],
      timestamp: new Date().toISOString(),
      retryCount: this.getRetryCount('chart'),
    };

    if (this.isCircuitBreakerOpen('chart')) {
      const fb = this.createSimpleChartFallback(context);
      this.cacheFallback('chart', fb);
      return fb;
    }

    this.recordFailure('chart');

    switch (context.errorType) {
      case AGUIErrorType.CHART_RENDER_ERROR: {
        const fb = await this.handleChartRenderError(context);
        this.cacheFallback('chart', fb);
        return fb;
      }
      case AGUIErrorType.DATA_FETCH_ERROR: {
        const fb = await this.handleDataFetchError(context);
        this.cacheFallback('chart', fb);
        return fb;
      }
      default: {
        const fb = this.createSimpleChartFallback(context);
        this.cacheFallback('chart', fb);
        return fb;
      }
    }
  }

  /**
   * Handle general component errors
   */
  public async handleComponentError(
    error: Error,
    component: string,
    data?: any
  ): Promise<FallbackResponse> {
    const context: AGUIErrorContext = {
      component,
      errorType: this.classifyGeneralError(error),
      originalError: error,
      data,
      columns: [],
      timestamp: new Date().toISOString(),
      retryCount: this.getRetryCount(component),
    };

    if (this.isCircuitBreakerOpen(component)) {
      const fb = this.createErrorMessageFallback(context);
      this.cacheFallback(component, fb);
      return fb;
    }

    this.recordFailure(component);

    // Try cached fallback first
    const cachedResponse = this.getCachedResponse(component);
    if (cachedResponse) return cachedResponse;

    const fb = this.createErrorMessageFallback(context);
    this.cacheFallback(component, fb);
    return fb;
  }

  // ---------- Classification ----------

  private classifyGridError(error: Error): AGUIErrorType {
    const message = (error.message || '').toLowerCase();
    if (message.includes('load') || message.includes('fetch')) {
      return AGUIErrorType.GRID_LOAD_ERROR;
    } else if (message.includes('render') || message.includes('display')) {
      return AGUIErrorType.GRID_RENDER_ERROR;
    } else if (message.includes('data')) {
      return AGUIErrorType.DATA_FETCH_ERROR;
    } else if (message.includes('memory') || message.includes('heap')) {
      return AGUIErrorType.MEMORY_ERROR;
    } else if (message.includes('timeout')) {
      return AGUIErrorType.TIMEOUT_ERROR;
    } else {
      return AGUIErrorType.COMPONENT_CRASH;
    }
  }

  private classifyChartError(error: Error): AGUIErrorType {
    const message = (error.message || '').toLowerCase();
    if (message.includes('render') || message.includes('draw')) {
      return AGUIErrorType.CHART_RENDER_ERROR;
    } else if (message.includes('data')) {
      return AGUIErrorType.DATA_FETCH_ERROR;
    } else if (message.includes('memory') || message.includes('heap')) {
      return AGUIErrorType.MEMORY_ERROR;
    } else if (message.includes('timeout')) {
      return AGUIErrorType.TIMEOUT_ERROR;
    } else {
      return AGUIErrorType.COMPONENT_CRASH;
    }
  }

  private classifyGeneralError(error: Error): AGUIErrorType {
    const message = (error.message || '').toLowerCase();
    if (message.includes('timeout')) {
      return AGUIErrorType.TIMEOUT_ERROR;
    } else if (message.includes('memory') || message.includes('heap')) {
      return AGUIErrorType.MEMORY_ERROR;
    } else if (message.includes('data')) {
      return AGUIErrorType.DATA_FETCH_ERROR;
    } else {
      return AGUIErrorType.COMPONENT_CRASH;
    }
  }

  // ---------- Handlers ----------

  private async handleGridLoadError(context: AGUIErrorContext): Promise<FallbackResponse> {
    const columnsKey = JSON.stringify(context.columns || []);
    const cacheKey = `grid_data_${columnsKey}`;
    const cached = this.errorCache.get(cacheKey);

    if (cached && this.isCacheValid(cached.timestamp)) {
      return {
        strategy: FallbackStrategy.CACHED_DATA,
        component: null, // Use original grid with cached data
        data: cached.payload?.data ?? [],
        columns: cached.payload?.columns ?? (context.columns || []),
        message: 'Using cached data due to loading error',
        retryAvailable: true,
        degradedFeatures: ['real-time-updates'],
      };
    }

    return this.createSimpleTableFallback(context);
  }

  private async handleGridRenderError(context: AGUIErrorContext): Promise<FallbackResponse> {
    const simplifiedColumns = this.simplifyColumns(context.columns || []);
    if (simplifiedColumns.length > 0 && context.retryCount < this.maxRetries) {
      return {
        strategy: FallbackStrategy.RETRY_MECHANISM,
        component: null, // Retry with original grid
        data: context.data || [],
        columns: simplifiedColumns,
        message: 'Retrying with simplified columns',
        retryAvailable: true,
        degradedFeatures: ['advanced-filtering', 'custom-renderers', 'complex-sorting'],
      };
    }
    return this.createSimpleTableFallback(context);
  }

  private async handleChartRenderError(context: AGUIErrorContext): Promise<FallbackResponse> {
    if (context.retryCount < this.maxRetries) {
      return {
        strategy: FallbackStrategy.RETRY_MECHANISM,
        component: null, // Retry with simplified chart
        data: this.simplifyChartData(context.data || []),
        columns: [],
        message: 'Retrying with simplified chart configuration',
        retryAvailable: true,
        degradedFeatures: ['animations', 'advanced-tooltips', 'interactive-features'],
      };
    }
    return this.createSimpleChartFallback(context);
  }

  private async handleDataFetchError(context: AGUIErrorContext): Promise<FallbackResponse> {
    const cacheKey = `${context.component}_data`;
    const cached = this.errorCache.get(cacheKey);
    if (cached && this.isCacheValid(cached.timestamp)) {
      return {
        strategy: FallbackStrategy.CACHED_DATA,
        component: null,
        data: cached.payload?.data ?? [],
        columns: cached.payload?.columns ?? [],
        message: 'Using cached data due to fetch error',
        retryAvailable: true,
        degradedFeatures: ['real-time-updates'],
      };
    }

    return {
      strategy: FallbackStrategy.LOADING_STATE,
      component: null,
      data: [],
      columns: [],
      message: 'Data fetch failed. Click to retry.',
      retryAvailable: true,
      degradedFeatures: [],
    };
  }

  // ---------- Fallback factories ----------

  private createSimpleTableFallback(context: AGUIErrorContext): FallbackResponse {
    return {
      strategy: FallbackStrategy.SIMPLE_TABLE,
      component: null, // Consuming code renders a basic table
      data: context.data || [],
      columns: this.extractSimpleColumns(context.data || []),
      message: 'Grid failed to load. Using simple table view.',
      retryAvailable: true,
      degradedFeatures: ['sorting', 'filtering', 'pagination', 'cell-editing'],
    };
  }

  private createSimpleChartFallback(context: AGUIErrorContext): FallbackResponse {
    return {
      strategy: FallbackStrategy.SIMPLE_TABLE, // Represent chart data as table
      component: null,
      data: context.data || [],
      columns: this.extractSimpleColumns(context.data || []),
      message: 'Chart failed to render. Showing data as table.',
      retryAvailable: true,
      degradedFeatures: ['visualization', 'interactivity', 'animations'],
    };
  }

  private createErrorMessageFallback(context: AGUIErrorContext): FallbackResponse {
    return {
      strategy: FallbackStrategy.ERROR_MESSAGE,
      component: null,
      data: [],
      columns: [],
      message: `${context.component} component failed to load. Please try refreshing the page.`,
      retryAvailable: true,
      degradedFeatures: ['all-features'],
    };
  }

  // ---------- Helpers ----------

  private simplifyColumns(columns: any[]): any[] {
    if (!Array.isArray(columns)) return [];
    return columns.map((col) => ({
      field: col?.field,
      headerName: col?.headerName || col?.field || 'Column',
      sortable: false,
      filter: false,
      resizable: true,
      cellRenderer: undefined, // Remove custom renderers
    }));
  }

  private simplifyChartData(data: any[]): any[] {
    const maxPoints = 100;
    if (!Array.isArray(data)) return [];
    return data.length > maxPoints ? data.slice(0, maxPoints) : data;
  }

  private extractSimpleColumns(data: any[]): any[] {
    if (!Array.isArray(data) || data.length === 0) {
      return [{ field: 'message', headerName: 'Status' }];
    }
    const firstRow = data[0] ?? {};
    return Object.keys(firstRow).map((key) => ({
      field: key,
      headerName: key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
    }));
  }

  private isCircuitBreakerOpen(component: string): boolean {
    const breaker = this.circuitBreakers.get(component);
    if (!breaker) return false;

    if (breaker.isOpen) {
      const now = Date.now();
      if (now - breaker.lastFailureTime > this.circuitBreakerTimeout) {
        // Transition to half-open
        breaker.isOpen = false;
        breaker.halfOpenAttempts = 0;
        this.circuitBreakers.set(component, breaker);
        return false;
      }
      return true;
    }
    return false;
  }

  private recordFailure(component: string): void {
    const breaker = this.circuitBreakers.get(component);
    if (!breaker) return;

    breaker.failureCount++;
    breaker.lastFailureTime = Date.now();

    if (breaker.failureCount >= this.circuitBreakerThreshold) {
      breaker.isOpen = true;
    }
    this.circuitBreakers.set(component, breaker);

    const currentRetries = this.retryAttempts.get(component) ?? 0;
    this.retryAttempts.set(component, currentRetries + 1);
  }

  private recordSuccess(component: string): void {
    const breaker = this.circuitBreakers.get(component);
    if (breaker) {
      breaker.failureCount = 0;
      breaker.isOpen = false;
      breaker.halfOpenAttempts = 0;
      this.circuitBreakers.set(component, breaker);
    }
    this.retryAttempts.set(component, 0);
  }

  private getRetryCount(component: string): number {
    return this.retryAttempts.get(component) ?? 0;
  }

  private getCachedResponse(component: string): FallbackResponse | null {
    const cacheKey = `${component}_fallback`;
    const cached = this.errorCache.get(cacheKey);
    if (cached && this.isCacheValid(cached.timestamp)) {
      return cached.payload as FallbackResponse;
    }
    return null;
  }

  private isCacheValid(timestamp: string): boolean {
    const cacheTime = new Date(timestamp).getTime();
    const now = Date.now();
    return Number.isFinite(cacheTime) && now - cacheTime < this.cacheTimeout;
  }

  private cacheFallback(component: string, response: FallbackResponse): void {
    const cacheKey = `${component}_fallback`;
    this.errorCache.set(cacheKey, {
      payload: response,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Cache successful data for fallback use
   */
  public cacheData(component: string, data: any[], columns?: any[]): void {
    const cacheKey = `${component}_data`;
    this.errorCache.set(cacheKey, {
      payload: { data, columns },
      timestamp: new Date().toISOString(),
    });
    // Success path resets breaker/retries
    this.recordSuccess(component);
  }

  /**
   * Clear error state and reset circuit breaker
   */
  public resetComponent(component: string): void {
    this.recordSuccess(component);
    // Clear related cache entries
    const keysToDelete = Array.from(this.errorCache.keys()).filter((key) =>
      key.startsWith(`${component}_`)
    );
    keysToDelete.forEach((key) => this.errorCache.delete(key));
  }

  /**
   * Get component health status
   */
  public getComponentHealth(component: string): {
    isHealthy: boolean;
    failureCount: number;
    circuitBreakerOpen: boolean;
    lastFailureTime: number | null;
  } {
    const breaker = this.circuitBreakers.get(component);
    return {
      isHealthy:
        !!breaker && !breaker.isOpen && (breaker.failureCount || 0) < this.circuitBreakerThreshold,
      failureCount: breaker?.failureCount ?? 0,
      circuitBreakerOpen: breaker?.isOpen ?? false,
      lastFailureTime: breaker?.lastFailureTime ?? null,
    };
  }
}

// Export singleton instance
export const agUIErrorHandler = AGUIErrorHandler.getInstance();
export default agUIErrorHandler;
