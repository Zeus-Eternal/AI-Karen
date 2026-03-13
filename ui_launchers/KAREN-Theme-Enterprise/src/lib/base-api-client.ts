/**
 * Unified API Client
 * 
 * Comprehensive HTTP client with error handling, retries, and interceptors.
 * Combines functionality from multiple API clients into a single unified source.
 */

import axios, { AxiosInstance } from 'axios'
import { QueryClient } from '@tanstack/react-query'
import type { Conversation, ConversationResponse } from '@/types/chat'

// API Types for Copilot and Memory operations
export interface CopilotAssistRequest {
  user_id: string;
  org_id?: string;
  prompt: string;
  context?: Record<string, unknown>;
  conversation_history?: Array<{ role: string; content: string }>;
}

export interface CopilotAssistResponse {
  response: string;
  requires_plugin: boolean;
  suggested_actions: string[];
  ai_data?: {
    degraded_mode?: boolean;
    reason?: string;
    timestamp?: string;
    [key: string]: unknown;
  };
  proactive_suggestion?: string | null;
  correlation_id?: string;
}

export interface MemorySearchRequest {
  user_id: string;
  org_id?: string;
  query: string;
  top_k?: number;
}

export interface MemorySearchResponse {
  hits: Array<{
    id: string;
    text: string;
    preview?: string;
    score: number;
    tags: string[];
    recency?: string;
    meta: Record<string, any>;
    importance: number;
    decay_tier: string;
    created_at: string;
    updated_at?: string;
    user_id: string;
    org_id?: string;
  }>;
  total_found: number;
  query_time_ms: number;
  correlation_id: string;
}

export interface MemoryCommitRequest {
  user_id: string;
  org_id?: string;
  text: string;
  tags?: string[];
  importance?: number;
  decay?: string;
}

export interface MemoryCommitResponse {
  id: string;
  success: boolean;
  message: string;
  correlation_id: string;
}

type ImportMetaWithEnv = ImportMeta & {
  env?: Record<string, string | undefined>
}

const resolveBaseUrl = (): string => {
  // Try to get VITE_API_URL from import.meta.env
  let metaEnv: string | undefined;
  if (typeof import.meta !== 'undefined' && import.meta.env) {
    metaEnv = import.meta.env.VITE_API_URL;
  }
  
  if (metaEnv && metaEnv.length > 0) {
    return metaEnv
  }

  const processEnv = typeof process !== 'undefined' ? process.env?.NEXT_PUBLIC_API_URL : undefined
  if (processEnv && processEnv.length > 0) {
    return processEnv
  }

  // Check for KAREN_BACKEND_URL as fallback
  const karenBackendUrl = typeof process !== 'undefined' ? process.env?.NEXT_PUBLIC_KAREN_BACKEND_URL : undefined
  if (karenBackendUrl && karenBackendUrl.length > 0) {
    return karenBackendUrl
  }

  return 'http://localhost:8000'
}

const BASE_URL = resolveBaseUrl()

// Create axios instance with default config
export const axiosApiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for adding auth token
axiosApiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
axiosApiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API Types
export interface ChatRequest {
  message: string
  conversation_id?: string
  context?: Record<string, unknown>
}

export interface ChatResponse {
  response: string
  conversation_id: string
  metadata?: Record<string, unknown>
}

export interface Plugin {
  id: string
  name: string
  description: string
  enabled: boolean
  version: string
  category: string
}

export interface SystemHealth {
  status: string
  version: string
  uptime: number
  components: Record<string, { status: string; latency?: number }>
}

// API Functions using axios
export const chatAPI = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const { data } = await axiosApiClient.post('/api/chat/message', request)
    return data
  },

  getConversations: async (): Promise<Conversation[]> => {
    const { data } = await axiosApiClient.get('/api/chat/conversations')
    return data
  },

  getConversation: async (id: string): Promise<ConversationResponse> => {
    const { data } = await axiosApiClient.get(`/api/chat/conversations/${id}`)
    return data
  },

  deleteConversation: async (id: string): Promise<void> => {
    await axiosApiClient.delete(`/api/chat/conversations/${id}`)
  },
}

export const pluginAPI = {
  list: async (): Promise<Plugin[]> => {
    const { data } = await axiosApiClient.get('/api/plugins')
    return data
  },

  get: async (id: string): Promise<Plugin> => {
    const { data } = await axiosApiClient.get(`/api/plugins/${id}`)
    return data
  },

  toggle: async (id: string, enabled: boolean): Promise<Plugin> => {
    const { data } = await axiosApiClient.patch(`/api/plugins/${id}`, { enabled })
    return data
  },

  execute: async (id: string, payload: unknown): Promise<unknown> => {
    const { data } = await axiosApiClient.post(`/api/plugins/${id}/execute`, payload)
    return data
  },
}

export const systemAPI = {
  health: async (): Promise<SystemHealth> => {
    const { data } = await axiosApiClient.get('/api/system/health')
    return data
  },

  metrics: async (): Promise<unknown> => {
    const { data } = await axiosApiClient.get('/api/system/metrics')
    return data
  },

  settings: async (): Promise<Record<string, unknown>> => {
    const { data} = await axiosApiClient.get('/api/system/settings')
    return data
  },

  updateSettings: async (settings: Record<string, unknown>): Promise<void> => {
    await axiosApiClient.put('/api/system/settings', settings)
  },
}

export const analyticsAPI = {
  getStats: async (): Promise<unknown> => {
    const { data } = await axiosApiClient.get('/api/analytics/stats')
    return data
  },

  getUsage: async (period: string = '7d'): Promise<unknown> => {
    const { data } = await axiosApiClient.get(`/api/analytics/usage?period=${period}`)
    return data
  },
}

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

interface ErrorResponseData {
  message?: string;
  code?: string;
  details?: unknown;
  [key: string]: unknown;
}

interface ParsedErrorResponse {
  message?: string;
  code?: string;
  details?: unknown;
}

// Enhanced Request configuration
export interface EnhancedRequestConfig extends RequestInit {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  retryCondition?: (error: InternalApiError, attempt: number) => boolean;
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
  error: InternalApiError,
  config: EnhancedRequestConfig
) => InternalApiError | Promise<InternalApiError>;

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

// Custom ApiError class
class InternalApiError extends Error {
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

// Export ApiError interface for backward compatibility
export interface ApiError extends ApiErrorInterface {}

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
  private storeCallbacks: {
    setLoading?: (key: string, loading: boolean) => void;
    setGlobalLoading?: (loading: boolean) => void;
    clearLoading?: (key: string) => void;
    logout?: () => void;
    addNotification?: (notification: {
      id: string;
      type: "warning" | "error" | "success" | "info";
      title: string;
      message: string;
      timestamp: Date;
      read: boolean;
      actions?: { label: string; action: () => void; }[]
    }) => void;
    setConnectionQuality?: (quality: 'good' | 'poor' | 'offline') => void;
  } = {};
  private queryClientCallback?: () => QueryClient;
   
  // Static properties to store callbacks
  private static storeCallbacks: {
    setLoading?: (key: string, loading: boolean) => void;
    setGlobalLoading?: (loading: boolean) => void;
    clearLoading?: (key: string) => void;
    logout?: () => void;
    addNotification?: (notification: {
      id: string;
      type: "warning" | "error" | "success" | "info";
      title: string;
      message: string;
      timestamp: Date;
      read: boolean;
      actions?: { label: string; action: () => void; }[]
    }) => void;
    setConnectionQuality?: (quality: 'good' | 'poor' | 'offline') => void;
  } = {};
  private static queryClientCallback?: () => QueryClient;
   
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

  private isErrorResponseData(value: unknown): value is ErrorResponseData {
    if (!value || typeof value !== "object") {
      return false;
    }

    const candidate = value as ErrorResponseData;
    const hasValidMessage =
      !("message" in candidate) || typeof candidate.message === "string";
    const hasValidCode =
      !("code" in candidate) || typeof candidate.code === "string";

    return hasValidMessage && hasValidCode;
  }

  private normalizeErrorResponse(
    payload: ErrorResponseData
  ): ParsedErrorResponse {
    const normalized: ParsedErrorResponse = {};

    if (typeof payload.message === "string") {
      normalized.message = payload.message;
    }

    if (typeof payload.code === "string") {
      normalized.code = payload.code;
    }

    if ("details" in payload) {
      normalized.details = payload.details;
    }

    return normalized;
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
      return `${protocol}//${host}`;
    }
    // Use backend URL with fallback to frontend API routes
    return process.env.NEXT_PUBLIC_KAREN_BACKEND_URL ||
           process.env.NEXT_PUBLIC_API_URL ||
           process.env.NEXT_PUBLIC_API_BASE_URL ||
           "http://localhost:8000";
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

    // Response interceptor for authentication and error handling
    this.addResponseInterceptor(async (response, config) => {
      try {
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
          const { logout, addNotification } = this.storeCallbacks;
          logout?.();
          addNotification?.({
            id: Date.now().toString(),
            type: "warning",
            title: "Session Expired",
            message: "Please log in again to continue.",
            timestamp: new Date(),
            read: false
          });
        }
        // Handle 403 forbidden
        if (response.status === 403) {
          const { addNotification } = this.storeCallbacks;
          addNotification?.({
            id: Date.now().toString(),
            type: "error",
            title: "Access Denied",
            message: "You do not have permission to perform this action.",
            timestamp: new Date(),
            read: false
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
        if (!config.skipErrorHandling) {
          const { addNotification, setConnectionQuality } = this.storeCallbacks;
          // Handle different error types
          switch (error.code) {
            case "NETWORK_ERROR":
              setConnectionQuality?.("offline");
              addNotification?.({
                id: Date.now().toString(),
                type: "error",
                title: "Network Error",
                message: "Please check your internet connection and try again.",
                timestamp: new Date(),
                read: false
              });
              break;
            case "TIMEOUT":
              addNotification?.({
                id: Date.now().toString(),
                type: "warning",
                title: "Request Timeout",
                message:
                  "The request took too long to complete. Please try again.",
                timestamp: new Date(),
                read: false
              });
              break;
            case "RATE_LIMITED":
              addNotification?.({
                id: Date.now().toString(),
                type: "warning",
                title: "Rate Limited",
                message:
                  "Too many requests. Please wait a moment before trying again.",
                timestamp: new Date(),
                read: false
              });
              break;
            default:
              if (error.status && error.status >= 500) {
                addNotification?.({
                  id: Date.now().toString(),
                  type: "error",
                  title: "Server Error",
                  message: "A server error occurred. Please try again later.",
                  timestamp: new Date(),
                  read: false
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
   
  // Set store callbacks to avoid circular dependencies
  public setStoreCallbacks(callbacks: {
    setLoading?: (key: string, loading: boolean) => void;
    setGlobalLoading?: (loading: boolean) => void;
    clearLoading?: (key: string) => void;
    logout?: () => void;
    addNotification?: (notification: {
      id: string;
      type: "warning" | "error" | "success" | "info";
      title: string;
      message: string;
      timestamp: Date;
      read: boolean;
      actions?: { label: string; action: () => void; }[]
    }) => void;
    setConnectionQuality?: (quality: 'good' | 'poor' | 'offline') => void;
  }): void {
    this.storeCallbacks = callbacks;
  }
   
  // Set query client callback to avoid circular dependencies
  public setQueryClientCallback(callback: () => QueryClient): void {
    this.queryClientCallback = callback;
  }
   
  // Static methods to set callbacks
  public static setStoreCallbacks(callbacks: {
    setLoading?: (key: string, loading: boolean) => void;
    setGlobalLoading?: (loading: boolean) => void;
    clearLoading?: (key: string) => void;
    logout?: () => void;
    addNotification?: (notification: {
      id: string;
      type: "warning" | "error" | "success" | "info";
      title: string;
      message: string;
      timestamp: Date;
      read: boolean;
      actions?: { label: string; action: () => void; }[]
    }) => void;
    setConnectionQuality?: (quality: 'good' | 'poor' | 'offline') => void;
  }): void {
    EnhancedApiClient.storeCallbacks = callbacks;
  }
   
  public static setQueryClientCallback(callback: () => QueryClient): void {
    EnhancedApiClient.queryClientCallback = callback;
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
      throw new InternalApiError(
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
    let lastError: InternalApiError | null = null;
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
          const apiError: InternalApiError = new InternalApiError(
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
            const queryClientCallback = this.queryClientCallback || EnhancedApiClient.queryClientCallback;
            if (queryClientCallback) {
              const client = queryClientCallback();
              client.invalidateQueries({ queryKey: [queryKey] });
            }
          }
        }
        return data;
      } catch (error: unknown) {
        clearTimeout(timeoutId);
        const err = error as Error;
        // Handle different error types
        if (err.name === "AbortError") {
          lastError = new InternalApiError("Request timeout", "TIMEOUT", 408);
        } else if (
          error instanceof TypeError &&
          err.message.includes("fetch")
        ) {
          lastError = new InternalApiError("Network error", "NETWORK_ERROR", 0);
        } else if (error instanceof InternalApiError) {
          lastError = error;
        } else {
          lastError = new InternalApiError(
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
              new InternalApiError(
                `Upload failed: ${xhr.statusText}`,
                "UPLOAD_ERROR",
                xhr.status
              )
            );
          }
        });
        xhr.addEventListener("error", () => {
          reject(new InternalApiError("Upload failed", "UPLOAD_ERROR"));
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

  // Copilot operations for EnhancedApiClient
  public async copilotAssist(request: CopilotAssistRequest): Promise<CopilotAssistResponse> {
    const response = await this.post<CopilotAssistResponse>('/api/ai/conversation-processing', request);
    return response.data;
  }

  // Memory operations for EnhancedApiClient
  public async memorySearch(request: MemorySearchRequest): Promise<MemorySearchResponse> {
    const response = await this.post<MemorySearchResponse>('/api/memory/search', request);
    return response.data;
  }

  public async memoryCommit(request: MemoryCommitRequest): Promise<MemoryCommitResponse> {
    const response = await this.post<MemoryCommitResponse>('/api/memory/commit', request);
    return response.data;
  }

  public async memoryUpdate(memoryId: string, updates: Partial<MemoryCommitRequest>): Promise<MemoryCommitResponse> {
    const response = await this.put<MemoryCommitResponse>(`/api/memory/${memoryId}`, updates);
    return response.data;
  }

  public async memoryDelete(memoryId: string, options: { user_id: string; org_id?: string; hard_delete?: boolean }): Promise<{ success: boolean; correlation_id: string }> {
    const response = await this.delete<{ success: boolean; correlation_id: string }>(`/api/memory/${memoryId}`, {
      body: JSON.stringify(options)
    });
    return response.data;
  }

  public async batchMemoryOperations(operations: Array<{ type: string; data: unknown }>): Promise<Array<{ success: boolean; result?: unknown; error?: string }>> {
    const response = await this.post<Array<{ success: boolean; result?: unknown; error?: string }>>('/api/memory/batch', { operations });
    return response.data;
  }

  public async healthCheck(): Promise<unknown> {
    const response = await this.get<unknown>('/api/health');
    return response.data;
  }

  // Default retry condition
  private defaultRetryCondition = (
    error: InternalApiError,
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
  ): Promise<ParsedErrorResponse> {
    try {
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        const json = (await response.json()) as unknown;
        if (this.isErrorResponseData(json)) {
          return this.normalizeErrorResponse(json);
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
    } catch {
      return { message: response.statusText || "Unknown error" };
    }
  }

  // Utility methods
  private getAuthToken(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem("karen_access_token");
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

// API Response types (for backward compatibility)
export interface RequestConfig extends RequestInit {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  skipAuth?: boolean;
  skipErrorHandling?: boolean;
}

// Interceptor types (for backward compatibility)
export type RequestInterceptorCompat = (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
export type ResponseInterceptorCompat = (response: Response) => Response | Promise<Response>;
export type ErrorInterceptorCompat = (error: ApiError) => ApiError | Promise<ApiError>;

// API Client class (for backward compatibility)
export class ApiClient {
  private baseURL: string;
  private defaultTimeout = 30000;
  private defaultRetries = 3;
  private defaultRetryDelay = 1000;
  private requestInterceptors: RequestInterceptorCompat[] = [];
  private responseInterceptors: ResponseInterceptorCompat[] = [];
  private errorInterceptors: ErrorInterceptorCompat[] = [];
  private storeCallbacks: {
    logout?: () => void;
    addNotification?: (notification: { type: string; title: string; message: string }) => void;
  } = {};

  constructor(baseURL?: string) {
    this.baseURL = baseURL || this.getBaseURL();
    this.setupDefaultInterceptors();
  }

  // Get base URL from environment or current location
  private getBaseURL(): string {
    if (typeof window !== 'undefined') {
      return `${window.location.protocol}//${window.location.host}/api`;
    }
    return process.env.NEXT_PUBLIC_API_URL || '/api';
  }

  // Setup default interceptors
  private setupDefaultInterceptors(): void {
    // Request interceptor for authentication
    this.addRequestInterceptor(async (config) => {
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
      config.headers = {
        'Content-Type': 'application/json',
        ...config.headers,
      };

      return config;
    });

    // Response interceptor for error handling
    this.addResponseInterceptor(async (response) => {
      // Handle 401 unauthorized
      if (response.status === 401) {
        // Only access the store on the client side
        if (typeof window !== 'undefined') {
          this.storeCallbacks.logout?.();
          this.storeCallbacks.addNotification?.({
            type: 'warning',
            title: 'Session Expired',
            message: 'Please log in again to continue.',
          });
        }
      }

      return response;
    });

    // Error interceptor for global error handling
    this.addErrorInterceptor(async (error) => {
      if (!error.code) {
        // Only access the store on the client side
        if (typeof window !== 'undefined') {
          // Handle network errors
          if (error.message.includes('fetch')) {
            this.storeCallbacks.addNotification?.({
              type: 'error',
              title: 'Network Error',
              message: 'Please check your internet connection and try again.',
            });
          }
        }
      }

      return error;
    });
  }

  // Add request interceptor
  public addRequestInterceptor(interceptor: RequestInterceptorCompat): void {
    this.requestInterceptors.push(interceptor);
  }

  // Add response interceptor
  public addResponseInterceptor(interceptor: ResponseInterceptorCompat): void {
    this.responseInterceptors.push(interceptor);
  }

  // Add error interceptor
  public addErrorInterceptor(interceptor: ErrorInterceptorCompat): void {
    this.errorInterceptors.push(interceptor);
  }

  // Set store callbacks to avoid circular dependency
  public setStoreCallbacks(callbacks: {
    logout?: () => void;
    addNotification?: (notification: { type: string; title: string; message: string }) => void;
  }): void {
    this.storeCallbacks = callbacks;
  }

  // Make HTTP request
  public async request<T = unknown>(
    endpoint: string,
    config: RequestConfig = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    const {
      timeout = this.defaultTimeout,
      retries = this.defaultRetries,
      retryDelay = this.defaultRetryDelay,
      skipErrorHandling = false,
      ...fetchConfig
    } = config;

    // Apply request interceptors
    let finalConfig = { ...fetchConfig };
    for (const interceptor of this.requestInterceptors) {
      finalConfig = await interceptor(finalConfig);
    }

    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    let lastError: ApiError | null = null;

    // Retry logic
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(url, {
          ...finalConfig,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        // Apply response interceptors
        let finalResponse = response;
        for (const interceptor of this.responseInterceptors) {
          finalResponse = await interceptor(finalResponse);
        }

        // Handle HTTP errors
        if (!finalResponse.ok) {
          const errorData = await this.parseErrorResponse(finalResponse);
          const apiError: ApiError = {
            name: "ApiError",
            message: errorData.message || `HTTP ${finalResponse.status}`,
            code: errorData.code,
            status: finalResponse.status,
            details: errorData.details,
          };

          // Don't retry on client errors (4xx)
          if (finalResponse.status >= 400 && finalResponse.status < 500) {
            throw apiError;
          }

          lastError = apiError;
          
          // Wait before retry
          if (attempt < retries) {
            await this.delay(retryDelay * Math.pow(2, attempt));
            continue;
          }
          
          throw apiError;
        }

        // Parse successful response
        const data = await this.parseResponse<T>(finalResponse);
        return data;

      } catch (error: unknown) {
        clearTimeout(timeoutId);

        const err = error as Error & { name?: string; code?: string };
        
        // Handle abort error (timeout)
        if (err.name === 'AbortError') {
          lastError = {
            name: 'ApiError',
            message: 'Request timeout',
            code: 'TIMEOUT',
            status: 408,
          };
        } else if (error instanceof TypeError && err.message.includes('fetch')) {
          // Network error
          lastError = {
            name: 'ApiError',
            message: 'Network error',
            code: 'NETWORK_ERROR',
            status: 0,
          };
        } else if (err.message || err.code) {
          // API error
          lastError = err as ApiError;
        } else {
          // Unknown error
          lastError = {
            name: 'ApiError',
            message: 'An unexpected error occurred',
            code: 'UNKNOWN_ERROR',
          };
        }

        // Don't retry on certain errors
        const errorObj = error as { code?: string; status?: number };
        if (errorObj.code === 'TIMEOUT' || (errorObj.status && errorObj.status >= 400 && errorObj.status < 500)) {
          break;
        }

        // Wait before retry
        if (attempt < retries) {
          await this.delay(retryDelay * Math.pow(2, attempt));
          continue;
        }
      }
    }

    // Apply error interceptors
    if (lastError && !skipErrorHandling) {
      for (const interceptor of this.errorInterceptors) {
        lastError = await interceptor(lastError);
      }
    }

    throw lastError;
  }

  // HTTP method helpers
  public async get<T = unknown>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'GET' });
  }

  public async post<T = unknown>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  public async put<T = unknown>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  public async patch<T = unknown>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...config,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  public async delete<T = unknown>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...config, method: 'DELETE' });
  }

  // Upload file
  public async upload<T = unknown>(
    endpoint: string,
    file: File,
    config?: Omit<RequestConfig, 'body'>
  ): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<T>(endpoint, {
      ...config,
      method: 'POST',
      body: formData,
      headers: {
        // Don't set Content-Type for FormData, let browser set it
        ...config?.headers,
      },
    });
  }

  // Parse response
  private async parseResponse<T>(response: Response): Promise<ApiResponse<T>> {
    const contentType = response.headers.get('content-type');
    
    if (contentType && contentType.includes('application/json')) {
      const json = await response.json();
      
      // Handle different response formats
      if (json.data !== undefined) {
        return json as ApiResponse<T>;
      } else {
        return {
          data: json as T,
          status: 'success',
        };
      }
    } else {
      const text = await response.text();
      return {
        data: text as T,
        status: 'success',
      };
    }
  }

  // Parse error response
  private async parseErrorResponse(response: Response): Promise<{ message?: string; code?: string; details?: unknown }> {
    try {
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        const jsonData = await response.json();
        return jsonData as { message?: string; code?: string; details?: unknown };
      } else {
        const text = await response.text();
        return { message: text || response.statusText };
      }
    } catch {
      return { message: response.statusText || 'Unknown error' };
    }
  }

  // Get authentication token
  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('karen_access_token');
    }
    return null;
  }

  // Delay helper
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Copilot operations
  public async copilotAssist(request: CopilotAssistRequest): Promise<CopilotAssistResponse> {
    const response = await this.post<CopilotAssistResponse>('/api/ai/conversation-processing', request);
    return response.data;
  }

  // Memory operations
  public async memorySearch(request: MemorySearchRequest): Promise<MemorySearchResponse> {
    const response = await this.post<MemorySearchResponse>('/api/memory/search', request);
    return response.data;
  }

  public async memoryCommit(request: MemoryCommitRequest): Promise<MemoryCommitResponse> {
    const response = await this.post<MemoryCommitResponse>('/api/memory/commit', request);
    return response.data;
  }

  public async memoryUpdate(memoryId: string, updates: Partial<MemoryCommitRequest>): Promise<MemoryCommitResponse> {
    const response = await this.put<MemoryCommitResponse>(`/api/memory/${memoryId}`, updates);
    return response.data;
  }

  public async memoryDelete(memoryId: string, options: { user_id: string; org_id?: string; hard_delete?: boolean }): Promise<{ success: boolean; correlation_id: string }> {
    const response = await this.delete<{ success: boolean; correlation_id: string }>(`/api/memory/${memoryId}`, {
      body: JSON.stringify(options)
    });
    return response.data;
  }

  public async batchMemoryOperations(operations: Array<{ type: string; data: unknown }>): Promise<Array<{ success: boolean; result?: unknown; error?: string }>> {
    const response = await this.post<Array<{ success: boolean; result?: unknown; error?: string }>>('/api/memory/batch', { operations });
    return response.data;
  }

  public async healthCheck(): Promise<unknown> {
    const response = await this.get<unknown>('/api/health');
    return response.data;
  }

  // Cache management methods for compatibility
  public clearCaches(): void {
    // Implementation would depend on actual caching mechanism
    // This is a placeholder for compatibility
  }

  public getEndpointStats(): Record<string, unknown> {
    // Implementation would depend on actual stats collection
    // This is a placeholder for compatibility
    return {};
  }
}

// Create singleton instances
export const enhancedApiClient = new EnhancedApiClient();
export const apiClient = new ApiClient();

// React hooks for API clients
export function useEnhancedApiClient() {
  return enhancedApiClient;
}

export function useApiClient() {
  return apiClient;
}

// Backwards compatibility helper for modules expecting getApiClient()
export function getApiClient() {
  return apiClient;
}

// Utility functions for common API patterns
export const api = {
  // Authentication
  auth: {
    login: (credentials: { email: string; password: string }) =>
      apiClient.post('/auth/login', credentials),
    logout: () => apiClient.post('/auth/logout'),
    refresh: () => apiClient.post('/auth/refresh'),
    me: () => apiClient.get('/auth/me'),
  },

  // Dashboard
  dashboard: {
    getMetrics: () => apiClient.get('/dashboard/metrics'),
    getHealth: () => apiClient.get('/system/health'),
  },

  // Chat
  chat: {
    getConversations: () => apiClient.get('/chat/conversations'),
    getConversation: (id: string) => apiClient.get(`/chat/conversations/${id}`),
    sendMessage: (conversationId: string, message: string) =>
      apiClient.post(`/chat/conversations/${conversationId}/messages`, { message }),
  },

  // Memory
  memory: {
    getAnalytics: () => apiClient.get('/memory/analytics'),
    search: (query: string) => apiClient.post('/memory/search', { query }),
    getNetwork: () => apiClient.get('/memory/network'),
  },

  // Plugins
  plugins: {
    getInstalled: () => apiClient.get('/plugins'),
    getMarketplace: () => apiClient.get('/plugins/marketplace'),
    install: (pluginId: string) => apiClient.post(`/plugins/${pluginId}/install`),
    uninstall: (pluginId: string) => apiClient.delete(`/plugins/${pluginId}`),
  },

  // Providers
  providers: {
    getList: () => apiClient.get('/providers'),
    getProvider: (id: string) => apiClient.get(`/providers/${id}`),
    updateProvider: (id: string, config: Record<string, unknown>) => apiClient.put(`/providers/${id}`, config),
  },

  // Users
  users: {
    getList: () => apiClient.get('/users'),
    getUser: (id: string) => apiClient.get(`/users/${id}`),
    updateUser: (id: string, data: unknown) => apiClient.put(`/users/${id}`, data),
  },

  // System
  system: {
    getHealth: () => apiClient.get('/system/health'),
    getMetrics: () => apiClient.get('/system/metrics'),
    getLogs: () => apiClient.get('/system/logs'),
  },
};

// Default export for backward compatibility
export default apiClient;
