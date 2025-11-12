/**
 * Enhanced API Client
 *
 * Advanced HTTP client with comprehensive error handling, retries, and interceptors.
 * Based on requirements: 12.2, 12.3
 */
import { useAppStore } from "@/store/app-store";
import { queryClient } from "@/lib/query-client";

// Enhanced API Response types
export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
  status: "success" | "error" | "warning";
  meta?: {
    total?: number;
    page?: number;
    limit?: number;
    hasMore?: boolean;
    timestamp?: string;
    version?: string;
  };
  errors?: Array<{
    field?: string;
    message: string;
    code?: string;
  }>;
}
export interface ApiErrorInterface extends Error {
  code?: string;
  status?: number;
  details?: unknown;
  timestamp?: string;
  requestId?: string;
}

interface ApiErrorPayload {
  message?: string;
  code?: string;
  details?: unknown;
  [key: string]: unknown;
}
// Enhanced Request configuration
export interface EnhancedRequestConfig extends RequestInit {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  retryCondition?: (error: ApiError, attempt: number) => boolean;
  skipAuth?: boolean;
  skipErrorHandling?: boolean;
  skipLoading?: boolean;
  loadingKey?: string;
  optimistic?: boolean;
  invalidateQueries?: string[];
  metadata?: Record<string, unknown>;
}
// Interceptor types
export type RequestInterceptor = (
  config: EnhancedRequestConfig
) => EnhancedRequestConfig | Promise<EnhancedRequestConfig>;
export type ResponseInterceptor = (
  response: Response,
  config: EnhancedRequestConfig
) => Response | Promise<Response>;
export type ErrorInterceptor = (
  error: ApiError,
  config: EnhancedRequestConfig
) => ApiError | Promise<ApiError>;

// Request/Response logging
export interface RequestLog {
  id: string;
  method: string;
  url: string;
  timestamp: Date;
  duration?: number;
  status?: number;
  error?: string;
}

// Enhanced API Client class
export class EnhancedApiClient {
  private baseURL: string;
  private defaultTimeout = 30000;
  private defaultRetries = 3;
  private defaultRetryDelay = 1000;
  private maxRetryDelay = 30000;
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];
  private errorInterceptors: ErrorInterceptor[] = [];
  private requestLogs: Map<string, RequestLog> = new Map();
  private rateLimiters: Map<string, { count: number; resetTime: number }> =
    new Map();
  constructor(baseURL?: string) {
    this.baseURL = baseURL || this.getBaseURL();
    this.setupDefaultInterceptors();
    this.setupPerformanceMonitoring();
  }

  private isApiResponse<T>(value: unknown): value is ApiResponse<T> {
    if (!value || typeof value !== "object") {
      return false;
    }

    const candidate = value as Partial<ApiResponse<T>>;
    return "data" in candidate && typeof candidate.status === "string";
  }

  private isApiErrorPayload(value: unknown): value is ApiErrorPayload {
    if (!value || typeof value !== "object") {
      return false;
    }

    const candidate = value as ApiErrorPayload;
    const hasValidMessage =
      !("message" in candidate) || typeof candidate.message === "string";
    const hasValidCode =
      !("code" in candidate) || typeof candidate.code === "string";

    return hasValidMessage && hasValidCode;
  }

  private createSuccessResponse<T>(data: T): ApiResponse<T> {
    return {
      data,
      status: "success",
      meta: {
        timestamp: new Date().toISOString(),
      },
    };
  }
  // Get base URL from environment or current location
  private getBaseURL(): string {
    if (typeof window !== "undefined") {
      const protocol = window.location.protocol;
      const host = window.location.host;
      return `${protocol}//${host}/api`;
    }
    return process.env.NEXT_PUBLIC_API_URL || "/api";
  }
  // Setup default interceptors
  private setupDefaultInterceptors(): void {
    // Request interceptor for authentication and headers
    this.addRequestInterceptor(async (config) => {
      try {
        // Add authentication
        if (!config.skipAuth) {
          const token = this.getAuthToken();
          if (token) {
            config.headers = {
              ...config.headers,
              Authorization: `Bearer ${token}`,
            };
          }
        }
        // Add default headers
        const headers = new Headers(config.headers);
        headers.set("Content-Type", "application/json");
        headers.set("X-Client-Version", process.env.NEXT_PUBLIC_APP_VERSION || "1.0.0");
        headers.set("X-Request-ID", this.generateRequestId());
        // Add CSRF token if available
        const csrfToken = this.getCSRFToken();
        if (csrfToken) {
          headers.set("X-CSRF-Token", csrfToken);
        }
        config.headers = headers;
        return config;
      } catch {
        return config;
      }
    });

    // Request interceptor for loading states
    this.addRequestInterceptor(async (config) => {
      try {
        if (!config.skipLoading) {
          const { setLoading, setGlobalLoading } = useAppStore.getState();
          const loadingKey = config.loadingKey || "api";
          if (loadingKey === "global") {
            setGlobalLoading(true);
          } else {
            setLoading(loadingKey, true);
          }
        }
        return config;
      } catch {
        return config;
      }
    });

    // Response interceptor for authentication and error handling
    this.addResponseInterceptor(async (response, config) => {
      try {
        // Clear loading states
        if (!config.skipLoading) {
          const { setGlobalLoading, clearLoading } = useAppStore.getState();
          const loadingKey = config.loadingKey || "api";
          if (loadingKey === "global") {
            setGlobalLoading(false);
          } else {
            clearLoading(loadingKey);
          }
        }
        // Handle rate limiting
        if (response.status === 429) {
          const retryAfter = response.headers.get("Retry-After");
          if (retryAfter) {
            const endpoint = new URL(response.url).pathname;
            this.rateLimiters.set(endpoint, {
              count: 0,
              resetTime: Date.now() + parseInt(retryAfter) * 1000,
            });
          }
        }
        // Handle 401 unauthorized
        if (response.status === 401) {
          const { logout, addNotification } = useAppStore.getState();
          logout();
          addNotification({
            type: "warning",
            title: "Session Expired",
            message: "Please log in again to continue.",
          });
        }
        // Handle 403 forbidden
        if (response.status === 403) {
          const { addNotification } = useAppStore.getState();
          addNotification({
            type: "error",
            title: "Access Denied",
            message: "You do not have permission to perform this action.",
          });
        }
        return response;
      } catch {
        return response;
      }
    });

    // Error interceptor for global error handling
    this.addErrorInterceptor(async (error, config) => {
      try {
        // Clear loading states on error
        if (!config.skipLoading) {
          const { setGlobalLoading, clearLoading } = useAppStore.getState();
          const loadingKey = config.loadingKey || "api";
          if (loadingKey === "global") {
            setGlobalLoading(false);
          } else {
            clearLoading(loadingKey);
          }
        }
        if (!config.skipErrorHandling) {
          const { addNotification, setConnectionQuality } =
            useAppStore.getState();
          // Handle different error types
          switch (error.code) {
            case "NETWORK_ERROR":
              setConnectionQuality("offline");
              addNotification({
                type: "error",
                title: "Network Error",
                message: "Please check your internet connection and try again.",
              });
              break;
            case "TIMEOUT":
              addNotification({
                type: "warning",
                title: "Request Timeout",
                message:
                  "The request took too long to complete. Please try again.",
              });
              break;
            case "RATE_LIMITED":
              addNotification({
                type: "warning",
                title: "Rate Limited",
                message:
                  "Too many requests. Please wait a moment before trying again.",
              });
              break;
            default:
              if (error.status && error.status >= 500) {
                addNotification({
                  type: "error",
                  title: "Server Error",
                  message: "A server error occurred. Please try again later.",
                });
              }
          }
        }
        return error;
      } catch {
        return error;
      }
    });
  }
  // Setup performance monitoring
  private setupPerformanceMonitoring(): void {
    // Clean up old request logs every 5 minutes
    setInterval(() => {
      const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
      for (const [id, log] of this.requestLogs.entries()) {
        if (log.timestamp.getTime() < fiveMinutesAgo) {
          this.requestLogs.delete(id);
        }
      }
    }, 5 * 60 * 1000);
    // Clean up rate limiters
    setInterval(() => {
      const now = Date.now();
      for (const [endpoint, limiter] of this.rateLimiters.entries()) {
        if (now > limiter.resetTime) {
          this.rateLimiters.delete(endpoint);
        }
      }
    }, 60 * 1000);
  }
  // Add interceptors
  public addRequestInterceptor(interceptor: RequestInterceptor): void {
    this.requestInterceptors.push(interceptor);
  }
  public addResponseInterceptor(interceptor: ResponseInterceptor): void {
    this.responseInterceptors.push(interceptor);
  }
  public addErrorInterceptor(interceptor: ErrorInterceptor): void {
    this.errorInterceptors.push(interceptor);
  }
  // Check rate limiting
  private checkRateLimit(endpoint: string): boolean {
    const limiter = this.rateLimiters.get(endpoint);
    if (limiter && Date.now() < limiter.resetTime) {
      return false;
    }
    return true;
  }
  // Make HTTP request with enhanced features
  public async request<T = unknown>(
    endpoint: string,
    config: EnhancedRequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const requestId = this.generateRequestId();
    // Check rate limiting
    if (!this.checkRateLimit(endpoint)) {
      throw new ApiError(
        "Rate limited. Please try again later.",
        "RATE_LIMITED",
        429
      );
    }
    const {
      timeout = this.defaultTimeout,
      retries = this.defaultRetries,
      retryDelay = this.defaultRetryDelay,
      retryCondition = this.defaultRetryCondition,
      invalidateQueries = [],
      ...fetchConfig
    } = config;
    // Start request logging
    const requestLog: RequestLog = {
      id: requestId,
      method: fetchConfig.method || "GET",
      url,
      timestamp: new Date(),
    };
    this.requestLogs.set(requestId, requestLog);
    // Apply request interceptors
    let finalConfig = { ...fetchConfig };
    for (const interceptor of this.requestInterceptors) {
      try {
        finalConfig = await interceptor(finalConfig);
      } catch {
        // Continue with current config if interceptor fails
      }
    }
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    let lastError: ApiError | null = null;
    const startTime = Date.now();
    // Retry logic
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(url, {
          ...finalConfig,
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        // Update request log
        requestLog.duration = Date.now() - startTime;
        requestLog.status = response.status;
        // Apply response interceptors
        let finalResponse = response;
        for (const interceptor of this.responseInterceptors) {
          try {
            finalResponse = await interceptor(finalResponse, config);
          } catch {
            // Continue with current response if interceptor fails
          }
        }
        // Handle HTTP errors
        if (!finalResponse.ok) {
          const errorData = await this.parseErrorResponse(finalResponse);
          const apiError = new ApiError(
            errorData.message || `HTTP ${finalResponse.status}`,
            errorData.code,
            finalResponse.status
          );
          apiError.details = errorData.details;
          apiError.requestId = requestId;
          // Update request log
          requestLog.error = apiError.message;
          // Don't retry on client errors (4xx) unless retry condition says otherwise
          if (
            finalResponse.status >= 400 &&
            finalResponse.status < 500 &&
            !retryCondition(apiError, attempt)
          ) {
            throw apiError;
          }
          lastError = apiError;
          // Wait before retry
          if (attempt < retries && retryCondition(apiError, attempt)) {
            await this.delay(retryDelay * Math.pow(2, attempt));
            continue;
          }
          throw apiError;
        }
        // Parse successful response
        const data = await this.parseResponse<T>(finalResponse);
        // Invalidate queries if specified
        if (invalidateQueries.length > 0) {
          for (const queryKey of invalidateQueries) {
            queryClient.invalidateQueries({ queryKey: [queryKey] });
          }
        }
        return data;
      } catch (error: unknown) {
        clearTimeout(timeoutId);
        const err = error as Error;
        // Handle different error types
        if (err.name === "AbortError") {
          lastError = new ApiError("Request timeout", "TIMEOUT", 408);
        } else if (
          error instanceof TypeError &&
          err.message.includes("fetch")
        ) {
          lastError = new ApiError("Network error", "NETWORK_ERROR", 0);
        } else if (error instanceof ApiError) {
          lastError = error;
        } else {
          lastError = new ApiError(
            "An unexpected error occurred",
            "UNKNOWN_ERROR"
          );
        }
        lastError.requestId = requestId;
        lastError.timestamp = new Date().toISOString();
        // Update request log
        requestLog.duration = Date.now() - startTime;
        requestLog.error = lastError.message;
        // Check retry condition
        if (attempt < retries && retryCondition(lastError, attempt)) {
          await this.delay(
            Math.min(retryDelay * Math.pow(2, attempt), this.maxRetryDelay)
          );
          continue;
        }
      }
    }
    // Apply error interceptors
    if (lastError) {
      for (const interceptor of this.errorInterceptors) {
        try {
          lastError = await interceptor(lastError, config);
        } catch {
          // Continue with current error if interceptor fails
        }
      }
    }
    throw lastError;
  }
  // HTTP method helpers
  public async get<T = unknown>(
    endpoint: string,
    config?: EnhancedRequestConfig
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: "GET" });
  }
  public async post<T = unknown>(
    endpoint: string,
    data?: unknown,
    config?: EnhancedRequestConfig
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }
  public async put<T = unknown>(
    endpoint: string,
    data?: unknown,
    config?: EnhancedRequestConfig
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    });
  }
  public async patch<T = unknown>(
    endpoint: string,
    data?: unknown,
    config?: EnhancedRequestConfig
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  }
  public async delete<T = unknown>(
    endpoint: string,
    config?: EnhancedRequestConfig
  ): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: "DELETE" });
  }
  // Upload with progress tracking
  public async upload<T = unknown>(
    endpoint: string,
    file: File,
    config?: Omit<EnhancedRequestConfig, "body">,
    onProgress?: (progress: number) => void
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append("file", file);
    // Create XMLHttpRequest for progress tracking
    if (onProgress) {
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.upload.addEventListener("progress", (event) => {
          if (event.lengthComputable) {
            const progress = (event.loaded / event.total) * 100;
            onProgress(progress);
          }
        });
        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const parsed = JSON.parse(xhr.responseText) as unknown;
              if (this.isApiResponse<T>(parsed)) {
                resolve(parsed);
              } else {
                resolve(this.createSuccessResponse(parsed as T));
              }
            } catch {
              resolve(this.createSuccessResponse(xhr.responseText as T));
            }
          } else {
            reject(
              new ApiError(
                `Upload failed: ${xhr.statusText}`,
                "UPLOAD_ERROR",
                xhr.status
              )
            );
          }
        });
        xhr.addEventListener("error", () => {
          reject(new ApiError("Upload failed", "UPLOAD_ERROR"));
        });
        xhr.open("POST", `${this.baseURL}${endpoint}`);
        // Add auth header
        const token = this.getAuthToken();
        if (token) {
          xhr.setRequestHeader("Authorization", `Bearer ${token}`);
        }
        xhr.send(formData);
      });
    }
    // Fallback to regular request
    const requestConfig: EnhancedRequestConfig = {
      ...config,
      method: "POST",
      body: formData,
    };

    if (config?.headers) {
      const headers = new Headers(config.headers as HeadersInit);
      headers.delete("Content-Type");
      requestConfig.headers = headers;
    }

    return this.request<T>(endpoint, requestConfig);
  }
  // Default retry condition
  private defaultRetryCondition = (
    error: ApiError,
    _attempt: number
  ): boolean => {
    // Don't retry on client errors (4xx) except for specific cases
    if (error.status && error.status >= 400 && error.status < 500) {
      return error.status === 408 || error.status === 429; // Timeout or rate limited
    }
    // Retry on network errors and server errors
    return (
      error.code === "NETWORK_ERROR" ||
      error.code === "TIMEOUT" ||
      (typeof error.status === "number" && error.status >= 500)
    );
  };
  // Parse response
  private async parseResponse<T>(response: Response): Promise<ApiResponse<T>> {
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      const json = (await response.json()) as unknown;
      if (this.isApiResponse<T>(json)) {
        return json;
      }

      return this.createSuccessResponse(json as T);
    } else {
      const text = await response.text();
      return this.createSuccessResponse(text as T);
    }

    const text = await response.text();
    return {
      data: text as unknown as T,
      status: "success",
      meta: {
        timestamp: new Date().toISOString(),
      },
    };
  }

  private isApiResponseData<T>(value: unknown): value is ApiResponse<T> {
    if (typeof value !== "object" || value === null) {
      return false;
    }
    const record = value as Record<string, unknown>;
    return (
      Object.prototype.hasOwnProperty.call(record, "data") &&
      Object.prototype.hasOwnProperty.call(record, "status")
    );
  }

  // Parse error response
  private async parseErrorResponse(
    response: Response
  ): Promise<ApiErrorPayload> {
    try {
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        const json = (await response.json()) as unknown;
        if (this.isApiErrorPayload(json)) {
          return json;
        }

        if (typeof json === "string") {
          return { message: json };
        }

        return {
          message: response.statusText || "Unknown error",
          details: json,
        };
      } else {
        const text = await response.text();
        return { message: text || response.statusText };
      }

      const text = await response.text();
      return { message: text || response.statusText };
    } catch {
      return { message: response.statusText || "Unknown error" };
    }
  }
  // Utility methods
  private getAuthToken(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem("auth-token");
    }
    return null;
  }
  private getCSRFToken(): string | null {
    if (typeof window !== "undefined") {
      const meta = document.querySelector('meta[name="csrf-token"]');
      return meta ? meta.getAttribute("content") : null;
    }
    return null;
  }
  private generateRequestId(): string {
    return `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
  // Get request logs for debugging
  public getRequestLogs(): RequestLog[] {
    return Array.from(this.requestLogs.values());
  }
  // Clear request logs
  public clearRequestLogs(): void {
    this.requestLogs.clear();
  }
}
// Custom ApiError class
class ApiError extends Error {
  public code?: string;
  public status?: number;
  public details?: unknown;
  public timestamp?: string;
  public requestId?: string;
  constructor(message: string, code?: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.timestamp = new Date().toISOString();
  }
}
// Create singleton instance
export const enhancedApiClient = new EnhancedApiClient();
// React hook for enhanced API client
export function useEnhancedApiClient() {
  return enhancedApiClient;
}
