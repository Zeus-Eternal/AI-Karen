/**
 * AG-UI Error Handler with Fallback Strategies
 * 
 * Provides error handling and fallback mechanisms for AG-UI components
 * including graceful degradation to simplified interfaces.
 */
import { GridApi } from 'ag-grid-community';
export enum AGUIErrorType {
  GRID_LOAD_ERROR = 'grid_load_error',
  GRID_RENDER_ERROR = 'grid_render_error',
  CHART_RENDER_ERROR = 'chart_render_error',
  DATA_FETCH_ERROR = 'data_fetch_error',
  COMPONENT_CRASH = 'component_crash',
  MEMORY_ERROR = 'memory_error',
  TIMEOUT_ERROR = 'timeout_error'
}
export enum FallbackStrategy {
  SIMPLE_TABLE = 'simple_table',
  CACHED_DATA = 'cached_data',
  LOADING_STATE = 'loading_state',
  ERROR_MESSAGE = 'error_message',
  RETRY_MECHANISM = 'retry_mechanism'
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
export class AGUIErrorHandler {
  private static instance: AGUIErrorHandler;
  private errorCache: Map<string, any> = new Map();
  private circuitBreakers: Map<string, CircuitBreakerState> = new Map();
  private retryAttempts: Map<string, number> = new Map();
  // Configuration
  private readonly maxRetries = 3;
  private readonly circuitBreakerThreshold = 5;
  private readonly circuitBreakerTimeout = 60000; // 1 minute
  private readonly cacheTimeout = 300000; // 5 minutes
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
    components.forEach(component => {
      this.circuitBreakers.set(component, {
        isOpen: false,
        failureCount: 0,
        lastFailureTime: 0,
        halfOpenAttempts: 0


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
      retryCount: this.getRetryCount('grid')
    };
    // Check circuit breaker
    if (this.isCircuitBreakerOpen('grid')) {
      return this.createSimpleTableFallback(context);
    }
    // Record failure
    this.recordFailure('grid');
    // Try recovery strategies based on error type
    switch (context.errorType) {
      case AGUIErrorType.GRID_LOAD_ERROR:
        return await this.handleGridLoadError(context);
      case AGUIErrorType.GRID_RENDER_ERROR:
        return await this.handleGridRenderError(context);
      case AGUIErrorType.DATA_FETCH_ERROR:
        return await this.handleDataFetchError(context);
      default:
        return this.createSimpleTableFallback(context);
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
      timestamp: new Date().toISOString(),
      retryCount: this.getRetryCount('chart')
    };
    // Check circuit breaker
    if (this.isCircuitBreakerOpen('chart')) {
      return this.createSimpleChartFallback(context);
    }
    // Record failure
    this.recordFailure('chart');
    // Try recovery strategies
    switch (context.errorType) {
      case AGUIErrorType.CHART_RENDER_ERROR:
        return await this.handleChartRenderError(context);
      case AGUIErrorType.DATA_FETCH_ERROR:
        return await this.handleDataFetchError(context);
      default:
        return this.createSimpleChartFallback(context);
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
      timestamp: new Date().toISOString(),
      retryCount: this.getRetryCount(component)
    };
    // Check circuit breaker
    if (this.isCircuitBreakerOpen(component)) {
      return this.createErrorMessageFallback(context);
    }
    // Record failure
    this.recordFailure(component);
    // Try cached data first
    const cachedResponse = this.getCachedResponse(component, data);
    if (cachedResponse) {
      return cachedResponse;
    }
    // Return appropriate fallback
    return this.createErrorMessageFallback(context);
  }
  private classifyGridError(error: Error): AGUIErrorType {
    const message = error.message.toLowerCase();
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
    const message = error.message.toLowerCase();
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
    const message = error.message.toLowerCase();
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
  private async handleGridLoadError(context: AGUIErrorContext): Promise<FallbackResponse> {
    // Try to use cached data
    const cacheKey = `grid_data_${JSON.stringify(context.columns)}`;
    const cachedData = this.errorCache.get(cacheKey);
    if (cachedData && this.isCacheValid(cachedData.timestamp)) {
      return {
        strategy: FallbackStrategy.CACHED_DATA,
        component: null, // Use original grid with cached data
        data: cachedData.data,
        columns: cachedData.columns || context.columns || [],
        message: 'Using cached data due to loading error',
        retryAvailable: true,
        degradedFeatures: ['real-time-updates']
      };
    }
    // Fallback to simple table
    return this.createSimpleTableFallback(context);
  }
  private async handleGridRenderError(context: AGUIErrorContext): Promise<FallbackResponse> {
    // Try with simplified column definitions
    const simplifiedColumns = this.simplifyColumns(context.columns || []);
    if (simplifiedColumns.length > 0 && context.retryCount < this.maxRetries) {
      return {
        strategy: FallbackStrategy.RETRY_MECHANISM,
        component: null, // Retry with original grid
        data: context.data || [],
        columns: simplifiedColumns,
        message: 'Retrying with simplified columns',
        retryAvailable: true,
        degradedFeatures: ['advanced-filtering', 'custom-renderers', 'complex-sorting']
      };
    }
    return this.createSimpleTableFallback(context);
  }
  private async handleChartRenderError(context: AGUIErrorContext): Promise<FallbackResponse> {
    // Try with simplified chart configuration
    if (context.retryCount < this.maxRetries) {
      return {
        strategy: FallbackStrategy.RETRY_MECHANISM,
        component: null, // Retry with simplified chart
        data: this.simplifyChartData(context.data || []),
        columns: [],
        message: 'Retrying with simplified chart configuration',
        retryAvailable: true,
        degradedFeatures: ['animations', 'advanced-tooltips', 'interactive-features']
      };
    }
    return this.createSimpleChartFallback(context);
  }
  private async handleDataFetchError(context: AGUIErrorContext): Promise<FallbackResponse> {
    // Try cached data first
    const cacheKey = `${context.component}_data`;
    const cachedData = this.errorCache.get(cacheKey);
    if (cachedData && this.isCacheValid(cachedData.timestamp)) {
      return {
        strategy: FallbackStrategy.CACHED_DATA,
        component: null,
        data: cachedData.data,
        columns: cachedData.columns || [],
        message: 'Using cached data due to fetch error',
        retryAvailable: true,
        degradedFeatures: ['real-time-updates']
      };
    }
    // Show loading state with retry option
    return {
      strategy: FallbackStrategy.LOADING_STATE,
      component: null,
      data: [],
      columns: [],
      message: 'Data fetch failed. Click to retry.',
      retryAvailable: true,
      degradedFeatures: []
    };
  }
  private createSimpleTableFallback(context: AGUIErrorContext): FallbackResponse {
    return {
      strategy: FallbackStrategy.SIMPLE_TABLE,
      component: null, // Will be handled by the consuming component
      data: context.data || [],
      columns: this.extractSimpleColumns(context.data || []),
      message: 'Grid failed to load. Using simple table view.',
      retryAvailable: true,
      degradedFeatures: ['sorting', 'filtering', 'pagination', 'cell-editing']
    };
  }
  private createSimpleChartFallback(context: AGUIErrorContext): FallbackResponse {
    return {
      strategy: FallbackStrategy.SIMPLE_TABLE,
      component: null, // Will show data as table instead of chart
      data: context.data || [],
      columns: this.extractSimpleColumns(context.data || []),
      message: 'Chart failed to render. Showing data as table.',
      retryAvailable: true,
      degradedFeatures: ['visualization', 'interactivity', 'animations']
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
      degradedFeatures: ['all-features']
    };
  }
  private simplifyColumns(columns: any[]): any[] {
    return columns.map(col => ({
      field: col.field,
      headerName: col.headerName || col.field,
      sortable: false,
      filter: false,
      resizable: true,
      cellRenderer: undefined // Remove custom renderers
    }));
  }
  private simplifyChartData(data: any[]): any[] {
    // Limit data points to prevent rendering issues
    const maxPoints = 100;
    if (data.length > maxPoints) {
      return data.slice(0, maxPoints);
    }
    return data;
  }
  private extractSimpleColumns(data: any[]): any[] {
    if (!data || data.length === 0) {
      return [{ field: 'message', headerName: 'Status' }];
    }
    const firstRow = data[0];
    return Object.keys(firstRow).map(key => ({
      field: key,
      headerName: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }));
  }
  private isCircuitBreakerOpen(component: string): boolean {
    const breaker = this.circuitBreakers.get(component);
    if (!breaker) return false;
    if (breaker.isOpen) {
      // Check if we should try half-open state
      const now = Date.now();
      if (now - breaker.lastFailureTime > this.circuitBreakerTimeout) {
        breaker.isOpen = false;
        breaker.halfOpenAttempts = 0;
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
    // Increment retry count
    const currentRetries = this.retryAttempts.get(component) || 0;
    this.retryAttempts.set(component, currentRetries + 1);
  }
  private recordSuccess(component: string): void {
    const breaker = this.circuitBreakers.get(component);
    if (breaker) {
      breaker.failureCount = 0;
      breaker.isOpen = false;
      breaker.halfOpenAttempts = 0;
    }
    // Reset retry count
    this.retryAttempts.set(component, 0);
  }
  private getRetryCount(component: string): number {
    return this.retryAttempts.get(component) || 0;
  }
  private getCachedResponse(component: string, data?: any): FallbackResponse | null {
    const cacheKey = `${component}_fallback`;
    const cached = this.errorCache.get(cacheKey);
    if (cached && this.isCacheValid(cached.timestamp)) {
      return cached.response;
    }
    return null;
  }
  private isCacheValid(timestamp: string): boolean {
    const cacheTime = new Date(timestamp).getTime();
    const now = Date.now();
    return (now - cacheTime) < this.cacheTimeout;
  }
  /**
   * Cache successful data for fallback use
   */
  public cacheData(component: string, data: any[], columns?: any[]): void {
    const cacheKey = `${component}_data`;
    this.errorCache.set(cacheKey, {
      data,
      columns,
      timestamp: new Date().toISOString()

  }
  /**
   * Clear error state and reset circuit breaker
   */
  public resetComponent(component: string): void {
    this.recordSuccess(component);
    // Clear related cache entries
    const keysToDelete = Array.from(this.errorCache.keys())
      .filter(key => key.includes(component));
    keysToDelete.forEach(key => this.errorCache.delete(key));
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
      isHealthy: !breaker?.isOpen && (breaker?.failureCount || 0) < this.circuitBreakerThreshold,
      failureCount: breaker?.failureCount || 0,
      circuitBreakerOpen: breaker?.isOpen || false,
      lastFailureTime: breaker?.lastFailureTime || null
    };
  }
}
// Export singleton instance
export const agUIErrorHandler = AGUIErrorHandler.getInstance();
