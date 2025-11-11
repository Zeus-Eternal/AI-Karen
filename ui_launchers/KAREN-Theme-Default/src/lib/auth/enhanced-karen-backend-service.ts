/**
 * Enhanced KarenBackendService with Extension Authentication
 * 
 * Extends the existing KarenBackendService with proper authentication handling
 * for extension API calls, automatic retry logic, and comprehensive error handling.
 * 
 * Requirements addressed:
 * - 3.1: Extension integration service error handling
 * - 3.2: Extension API calls with proper authentication
 * - 3.3: Authentication failures and retry logic
 * - 3.4: Network errors and exponential backoff
 * - 3.5: Request interceptor for automatic token injection
 */

import { getExtensionAuthManager, ExtensionAuthManager } from './extension-auth-manager';
import { logger } from '@/lib/logger';
import { getConnectionManager, ConnectionError, ErrorCategory } from '@/lib/connection/connection-manager';
import { getTimeoutManager, OperationType } from '@/lib/connection/timeout-manager';

// Request configuration interface
export interface RequestConfig {
  timeout?: number;
  retryAttempts?: number;
  exponentialBackoff?: boolean;
  skipAuth?: boolean;
  requireAuth?: boolean;
}

// Response interface
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
  retryCount?: number;
  duration?: number;
}

// Error types for extension API calls
export class ExtensionApiError extends Error {
  public status: number;
  public category: ErrorCategory;
  public retryable: boolean;
  public originalError?: unknown;

  constructor(
    message: string,
    status: number,
    category: ErrorCategory = ErrorCategory.HTTP_ERROR,
    retryable: boolean = false,
    originalError?: unknown
  ) {
    super(message);
    this.name = 'ExtensionApiError';
    this.status = status;
    this.category = category;
    this.retryable = retryable;
    this.originalError = originalError;
  }

  static fromConnectionError(error: ConnectionError): ExtensionApiError {
    return new ExtensionApiError(
      error.message,
      error.statusCode || 0,
      error.category,
      error.retryable,
      error
    );
  }

  static isRetryableStatus(status: number): boolean {
    return [408, 429, 500, 502, 503, 504].includes(status);
  }
}

/**
 * Enhanced KarenBackendService with Extension Authentication
 * 
 * Provides authenticated API calls for extension endpoints with automatic
 * token refresh, retry logic, and comprehensive error handling.
 */
export class EnhancedKarenBackendService {
  private authManager: ExtensionAuthManager;
  private connectionManager = getConnectionManager();
  private timeoutManager = getTimeoutManager();
  private readonly maxRetries = 3;
  private readonly baseRetryDelay = 1000; // 1 second

  constructor() {
    this.authManager = getExtensionAuthManager();
  }

  /**
   * Make an authenticated request to extension endpoints
   */
  async makeAuthenticatedRequest<T = any>(
    endpoint: string,
    options: RequestInit = {},
    config: RequestConfig = {}
  ): Promise<T> {
    const {
      timeout,
      retryAttempts = this.maxRetries,
      exponentialBackoff = true,
      skipAuth = false,
      requireAuth = true,
    } = config;

    let lastError: ExtensionApiError | null = null;

    for (let attempt = 1; attempt <= retryAttempts + 1; attempt++) {
      try {
        // Get authentication headers if not skipping auth
        let headers: Record<string, string> = {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          ...((options.headers as Record<string, string>) || {}),
        };

        if (!skipAuth) {
          try {
            const authHeaders = await this.authManager.getAuthHeaders();
            headers = { ...headers, ...authHeaders };
          } catch (authError) {
            if (requireAuth) {
              throw new ExtensionApiError(
                'Failed to get authentication headers',
                401,
                ErrorCategory.CONFIGURATION_ERROR,
                false,
                authError
              );
            }
            logger.warn('Failed to get auth headers, proceeding without authentication:', authError);
          }
        }

        // Determine timeout
        const requestTimeout = timeout || this.timeoutManager.getTimeout(
          endpoint.includes('/background-tasks') 
            ? OperationType.BACKGROUND_TASK 
            : OperationType.API_REQUEST
        );

        // Make the request using connection manager
        const result = await this.connectionManager.makeRequest(
          endpoint,
          {
            ...options,
            headers,
            credentials: 'include',
          },
          {
            timeout: requestTimeout,
            retryAttempts: 0, // We handle retries at this level
            exponentialBackoff: false,
          }
        );

        logger.debug(`Extension API request successful: ${endpoint}`, {
          status: result.status,
          attempt,
          duration: result.duration,
        });

        return result.data as T;
      } catch (error) {
        lastError = this.handleRequestError(error, endpoint, attempt);

        // Handle authentication errors specifically
        if (lastError.status === 403 || lastError.status === 401) {
          if (attempt < retryAttempts + 1 && !skipAuth) {
            logger.warn(
              `Authentication failed for ${endpoint} (attempt ${attempt}), refreshing token...`
            );
            
            try {
              // Force token refresh and retry
              await this.authManager.forceRefresh();
              continue;
            } catch (refreshError) {
              logger.error('Token refresh failed:', refreshError);
              // Continue to retry logic below
            }
          } else {
            throw new ExtensionApiError(
              `Authentication failed after ${attempt} attempts`,
              lastError.status,
              ErrorCategory.HTTP_ERROR,
              false,
              lastError
            );
          }
        }

        // Handle service unavailable errors
        if (lastError.status === 503) {
          if (attempt < retryAttempts + 1) {
            const delay = exponentialBackoff 
              ? this.baseRetryDelay * Math.pow(2, attempt - 1)
              : this.baseRetryDelay;
            
            logger.warn(
              `Service unavailable for ${endpoint} (attempt ${attempt}), retrying in ${delay}ms...`
            );
            
            await this.delay(delay);
            continue;
          } else {
            throw new ExtensionApiError(
              `Service unavailable after ${attempt} attempts`,
              503,
              ErrorCategory.HTTP_ERROR,
              true,
              lastError
            );
          }
        }

        // Handle other retryable errors
        if (lastError.retryable && attempt < retryAttempts + 1) {
          const delay = exponentialBackoff 
            ? this.baseRetryDelay * Math.pow(2, attempt - 1)
            : this.baseRetryDelay;
          
          logger.warn(
            `Request failed for ${endpoint} (attempt ${attempt}):`,
            lastError.message,
            `Retrying in ${delay}ms...`
          );
          
          await this.delay(delay);
          continue;
        }

        // Non-retryable error or max retries exceeded
        break;
      }
    }

    // All retries exhausted
    logger.error(
      `Request failed for ${endpoint} after ${retryAttempts + 1} attempts:`,
      lastError?.message || 'Unknown error'
    );

    throw lastError || new ExtensionApiError(
      'Request failed for unknown reason',
      0,
      ErrorCategory.UNKNOWN_ERROR,
      false
    );
  }

  /**
   * Handle request errors and convert to ExtensionApiError
   */
  private handleRequestError(
    error: Error,
    _endpoint: string,
    _attempt: number
  ): ExtensionApiError {
    if (error instanceof ConnectionError) {
      return ExtensionApiError.fromConnectionError(error);
    }

    if (error instanceof ExtensionApiError) {
      return error;
    }

    // Handle fetch errors
    if (error instanceof TypeError) {
      return new ExtensionApiError(
        'Network error: Unable to connect to extension service',
        0,
        ErrorCategory.NETWORK_ERROR,
        true,
        error
      );
    }

    // Handle timeout errors
    if (error.name === 'AbortError') {
      return new ExtensionApiError(
        'Request timeout',
        408,
        ErrorCategory.TIMEOUT_ERROR,
        true,
        error
      );
    }

    // Handle HTTP errors
    if ((error as any).status) {
      const status = (error as any).status;
      const isRetryable = ExtensionApiError.isRetryableStatus(status);
      return new ExtensionApiError(
        error.message || `HTTP ${status}`,
        status,
        ErrorCategory.HTTP_ERROR,
        isRetryable,
        error
      );
    }

    // Generic error
    return new ExtensionApiError(
      error.message || 'Unknown error occurred',
      0,
      ErrorCategory.UNKNOWN_ERROR,
      true,
      error
    );
  }

  /**
   * Delay utility for retry logic
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Get extensions list with authentication
   */
  async getExtensions(): Promise<unknown[]> {
    try {
      return await this.makeAuthenticatedRequest('/api/extensions/');
    } catch (error) {
      logger.error('Failed to get extensions:', error);
      throw error;
    }
  }

  /**
   * Get background tasks with authentication
   */
  async getBackgroundTasks(extensionName?: string): Promise<unknown[]> {
    try {
      const params = extensionName ? `?extension_name=${encodeURIComponent(extensionName)}` : '';
      return await this.makeAuthenticatedRequest(`/api/extensions/background-tasks/${params}`);
    } catch (error) {
      logger.error('Failed to get background tasks:', error);
      throw error;
    }
  }

  /**
   * Register background task with authentication
   */
  async registerBackgroundTask(taskData: unknown): Promise<unknown> {
    try {
      return await this.makeAuthenticatedRequest(
        '/api/extensions/background-tasks/',
        {
          method: 'POST',
          body: JSON.stringify(taskData),
        }
      );
    } catch (error) {
      logger.error('Failed to register background task:', error);
      throw error;
    }
  }

  /**
   * Load extension with authentication
   */
  async loadExtension(extensionName: string): Promise<unknown> {
    try {
      return await this.makeAuthenticatedRequest(
        `/api/extensions/${encodeURIComponent(extensionName)}/load`,
        {
          method: 'POST',
        }
      );
    } catch (error) {
      logger.error(`Failed to load extension ${extensionName}:`, error);
      throw error;
    }
  }

  /**
   * Unload extension with authentication
   */
  async unloadExtension(extensionName: string): Promise<unknown> {
    try {
      return await this.makeAuthenticatedRequest(
        `/api/extensions/${encodeURIComponent(extensionName)}/unload`,
        {
          method: 'POST',
        }
      );
    } catch (error) {
      logger.error(`Failed to unload extension ${extensionName}:`, error);
      throw error;
    }
  }

  /**
   * Get extension health status
   */
  async getExtensionHealth(): Promise<unknown> {
    try {
      return await this.makeAuthenticatedRequest('/api/extensions/health', {}, {
        requireAuth: false, // Health checks might not require auth
        retryAttempts: 1, // Fewer retries for health checks
      });
    } catch (error) {
      logger.warn('Extension health check failed:', error);
      return {
        status: 'unhealthy',
        error: error instanceof ExtensionApiError ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Check authentication status
   */
  async checkAuthStatus(): Promise<boolean> {
    return this.authManager.isAuthenticated();
  }

  /**
   * Clear authentication state
   */
  clearAuth(): void {
    this.authManager.clearAuth();
  }

  /**
   * Get current authentication state
   */
  getAuthState() {
    return this.authManager.getAuthState();
  }
}

// Global instance
let enhancedKarenBackendService: EnhancedKarenBackendService | null = null;

/**
 * Get the global enhanced Karen backend service instance
 */
export function getEnhancedKarenBackendService(): EnhancedKarenBackendService {
  if (!enhancedKarenBackendService) {
    enhancedKarenBackendService = new EnhancedKarenBackendService();
  }
  return enhancedKarenBackendService;
}

/**
 * Initialize a new enhanced Karen backend service instance
 */
export function initializeEnhancedKarenBackendService(): EnhancedKarenBackendService {
  enhancedKarenBackendService = new EnhancedKarenBackendService();
  return enhancedKarenBackendService;
}