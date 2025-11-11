import { generateUUID } from "./uuid";
import { webUIConfig } from "./config";
import { logger } from "./logger";
import { getPerformanceMonitor } from "./performance-monitor";
import { getStoredApiKey } from "./secure-api-key";
import { errorHandler, type ErrorInfo } from "./error-handler";
import type { ApiError } from "./api-client";
import { getExtensionAuthManager } from "./auth/extension-auth-manager";
import {
  /** * AI Karen Backend Integration Layer * Connects the web UI with existing AI Karen backend services */ ChatMessage,
  KarenSettings,
  HandleUserMessageResult,
} from "./types";
import {
  ExtensionAuthErrorFactory,
  extensionAuthErrorHandler,
  type ExtensionAuthError,
} from "./auth/extension-auth-errors";
import { extensionAuthRecoveryManager } from "./auth/extension-auth-recovery";
import {
  isExtensionFeatureAvailable,
  getExtensionFallbackData,
} from "./auth/extension-auth-degradation";
export const SESSION_ID_KEY = "auth_session_id";
export function initializeSessionId(): string {
  if (typeof window === "undefined") return "";
  let sessionId = localStorage.getItem(SESSION_ID_KEY);
  if (!sessionId) {
    sessionId = generateUUID();
    localStorage.setItem(SESSION_ID_KEY, sessionId);
  }
  return sessionId;
}
// Error handling types
export interface WebUIErrorResponse {
  error: string;
  message: string;
  type: string;
  details?: Record<string, unknown>;
  request_id?: string;
  timestamp: string;
}
// Custom error class for structured error handling
class APIError extends Error {
  public status: number;
  public details?: WebUIErrorResponse;
  public isRetryable: boolean;
  public errorInfo?: ErrorInfo;
  constructor(
    message: string,
    status: number,
    details?: WebUIErrorResponse,
    isRetryable: boolean = false
  ) {
    super(message);
    this.name = "APIError";
    this.status = status;
    this.details = details;
    this.isRetryable = isRetryable;
  }
  static isRetryableStatus(status: number): boolean {
    return [408, 429, 500, 502, 503, 504].includes(status);
  }
  static fromResponse(response: Response, errorData?: unknown): APIError {
    const isRetryable = APIError.isRetryableStatus(response.status);

    // Type guard to ensure errorData matches WebUIErrorResponse structure
    const details: WebUIErrorResponse | undefined =
      errorData &&
      typeof errorData === "object" &&
      errorData !== null &&
      "error" in errorData &&
      "message" in errorData &&
      "type" in errorData
        ? (errorData as WebUIErrorResponse)
        : undefined;

    return new APIError(
      `HTTP ${response.status}: ${response.statusText}`,
      response.status,
      details,
      isRetryable
    );
  }
}
// Backend service configuration
export interface BackendConfig {
  baseUrl: string;
  apiKey?: string;
  timeout: number;
}
export interface OfflineRequest {
  endpoint: string;
  options: RequestInit;
  useCache: boolean;
  cacheTtl: number;
  maxRetries: number;
  retryDelay: number;
}
// Memory service types
export interface MemoryEntry {
  id: string;
  content: string;
  metadata: Record<string, unknown>;
  timestamp: number;
  similarity_score?: number;
  tags: string[];
  user_id?: string;
  session_id?: string;
}
export interface MemoryQuery {
  text: string;
  user_id?: string;
  session_id?: string;
  tags?: string[];
  metadata_filter?: Record<string, unknown>;
  time_range?: [Date, Date];
  top_k?: number;
  similarity_threshold?: number;
}
// Plugin service types
export interface PluginInfo {
  name: string;
  description: string;
  category: string;
  enabled: boolean;
  version: string;
  parameters?: Record<string, unknown>;
}
export interface PluginExecutionResult {
  success: boolean;
  result?: unknown;
  stdout?: string;
  stderr?: string;
  error?: string;
  plugin_name: string;
  timestamp: string;
}
// Analytics service types
export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_sessions: number;
  total_requests: number;
  error_rate: number;
  response_time_avg: number;
  uptime_hours: number;
  timestamp: string;
}
export interface UsageAnalytics {
  total_interactions: number;
  unique_users: number;
  popular_features: Array<{
    name: string;
    usage_count: number;
  }>;
  peak_hours: number[];
  user_satisfaction: number;
  time_range: string;
  timestamp: string;
}
// --- Authentication Types ---
export interface LoginResult {
  token: string;
  user_id: string;
  roles: string[];
}
export interface CurrentUser {
  user_id: string;
  roles: string[];
}
// --- Extension Types ---
export interface ExtensionInfo {
  name: string;
  version: string;
  display_name: string;
  description: string;
  status: string;
  capabilities: Record<string, unknown>;
  loaded_at: string | null;
}
export interface BackgroundTaskInfo {
  task_id: string;
  name: string;
  extension_name: string;
  status: string;
  created_at: string;
  last_run: string | null;
  next_run: string | null;
}
export interface ExtensionListResponse {
  extensions: Record<string, ExtensionInfo> | ExtensionInfo[];
  total: number;
  user_context?: {
    user_id: string;
    tenant_id: string;
  };
  message?: string;
}
export interface BackgroundTaskListResponse {
  tasks: BackgroundTaskInfo[];
  total: number;
  extension_name?: string;
  message?: string;
}
export interface BackgroundTaskRegistrationResponse {
  task_id: string;
  message: string;
  status: string;
}
class KarenBackendService {
  private config: BackendConfig;
  private cache: Map<
    string,
    { data: unknown; timestamp: number; ttl: number }
  > = new Map();
  private debugLogging: boolean;
  private requestLogging: boolean;
  private performanceMonitoring: boolean;
  private logLevel: string;
  private offlineQueue: OfflineRequest[] = [];
  private failureCount = 0;
  private circuitOpenUntil = 0;
  constructor(config: Partial<BackendConfig> = {}) {
    // Force empty baseUrl in browser to ensure Next.js API routes are used
    const baseUrl =
      typeof window !== "undefined"
        ? ""
        : config.baseUrl || webUIConfig.backendUrl;
    this.config = {
      baseUrl,
      apiKey: config.apiKey || getStoredApiKey() || webUIConfig.apiKey,
      timeout: config.timeout || webUIConfig.apiTimeout,
    };
    // Initialize configuration from webUIConfig
    this.debugLogging = webUIConfig.debugLogging;
    this.requestLogging = webUIConfig.requestLogging;
    this.performanceMonitoring = webUIConfig.performanceMonitoring;
    this.logLevel = webUIConfig.logLevel;
    // Log the configuration in a gated way
    logger.info("KarenBackendService initialized with config:", {
      baseUrl: this.config.baseUrl,
      webUIConfigBackendUrl: webUIConfig.backendUrl,
      timeout: this.config.timeout,
      hasApiKey: !!this.config.apiKey,
      debugLogging: this.debugLogging,
      requestLogging: this.requestLogging,
      performanceMonitoring: this.performanceMonitoring,
      logLevel: this.logLevel,
      fallbackUrls: webUIConfig.fallbackBackendUrls,
      windowLocation:
        typeof window !== "undefined" ? window.location.href : "server-side",
    });

    if (typeof window !== "undefined") {
      window.addEventListener("online", this.replayOfflineQueue);
    }
  }
  /**
   * Check if endpoint is an extension API endpoint that requires special authentication
   */
  private isExtensionEndpoint(endpoint: string): boolean {
    return (
      endpoint.startsWith("/api/extensions") ||
      endpoint.includes("/background-tasks") ||
      endpoint.includes("extension")
    );
  }
  /**
   * Get authentication headers with extension-specific handling
   */
  private async getAuthHeaders(
    endpoint: string
  ): Promise<Record<string, string>> {
    const headers: Record<string, string> = {};
    // For extension endpoints, try to use extension auth manager
    if (this.isExtensionEndpoint(endpoint)) {
      try {
        const extensionAuthManager = getExtensionAuthManager();
        const extensionHeaders = await extensionAuthManager.getAuthHeaders();
        Object.assign(headers, extensionHeaders);
        if (this.debugLogging) {
          logger.debug("Using extension auth headers for request");
        }
        return headers;
      } catch (error) {
        logger.warn(
          "Failed to get extension auth headers, falling back to standard auth:",
          error
        );
      }
    }
    // Standard authentication fallback
    const sessionToken = this.getStoredSessionToken();
    if (sessionToken) {
      headers["Authorization"] = `Bearer ${sessionToken}`;
      if (this.debugLogging) {
        logger.debug("Using session token for authentication");
      }
    } else if (this.config.apiKey) {
      headers["X-API-KEY"] = this.config.apiKey;
      if (this.debugLogging) {
        logger.debug("Using API key for authentication");
      }
    } else {
      if (this.debugLogging) {
        logger.debug("No authentication credentials available");
      }
    }
    return headers;
  }
  /**
   * Handle authentication failures with comprehensive extension error handling
   */
  private async handleAuthFailure(
    endpoint: string,
    response: Response,
    attempt: number,
    maxRetries: number
  ): Promise<boolean> {
    // Handle extension endpoint authentication failures with comprehensive error handling
    if (
      this.isExtensionEndpoint(endpoint) &&
      (response.status === 401 || response.status === 403)
    ) {
      try {
        // Create appropriate extension auth error
        let authError: ExtensionAuthError;
        if (response.status === 401) {
          authError = ExtensionAuthErrorFactory.createTokenExpiredError({
            endpoint,
            attempt: attempt + 1,
            maxRetries,
            httpStatus: response.status,
          });
        } else {
          authError = ExtensionAuthErrorFactory.createPermissionDeniedError({
            endpoint,
            attempt: attempt + 1,
            maxRetries,
            httpStatus: response.status,
          });
        }
        // Attempt recovery using the recovery manager
        const recoveryResult =
          await extensionAuthRecoveryManager.attemptRecovery(
            authError,
            endpoint,
            this.getOperationFromEndpoint(endpoint)
          );
        // Return true if recovery was successful and we should retry
        return recoveryResult.success && attempt < maxRetries;
      } catch (recoveryError) {
        logger.error("Extension auth recovery failed:", recoveryError);
        // Create a recovery failure error
        const recoveryFailureError =
          ExtensionAuthErrorFactory.createRefreshFailedError({
            endpoint,
            attempt: attempt + 1,
            maxRetries,
            originalError: recoveryError,
          });

        // Handle the recovery failure
        extensionAuthErrorHandler.handleError(recoveryFailureError);
      }
    }
    // Standard authentication failure handling
    if (response.status === 401) {
      try {
        const meResp = await fetch(`${this.config.baseUrl}/api/auth/me`, {
          headers: await this.getAuthHeaders("/api/auth/me"),
        });

        if (meResp.status === 401 && typeof window !== "undefined") {
          window.location.assign("/login");
        }
      } catch {
        // ignore secondary auth errors
      }
    }
    return false; // No retry
  }
  /**
   * Extract operation name from endpoint for error context
   */
  private getOperationFromEndpoint(endpoint: string): string {
    if (endpoint.includes("/extensions/")) {
      if (endpoint.includes("/background-tasks")) {
        return "background_tasks";
      }
      return "extension_list";
    }
    if (endpoint.includes("/extension")) {
      return "extension_status";
    }
    return "extension_operation";
  }
  /**
   * Handle extension-specific errors with fallback data
   */
  private async handleExtensionError(
    endpoint: string,
    response: Response,
    errorDetails?: WebUIErrorResponse
  ): Promise<unknown | null> {
    try {
      const operation = this.getOperationFromEndpoint(endpoint);
      // Check if the feature is still available in degraded mode
      if (!isExtensionFeatureAvailable(operation)) {
        logger.info(
          `Extension feature ${operation} not available in current degradation state`
        );
        return getExtensionFallbackData(operation);
      }
      // Create appropriate extension auth error based on status
      let authError: ExtensionAuthError;
      switch (response.status) {
        case 401:
          authError = ExtensionAuthErrorFactory.createTokenExpiredError({
            endpoint,
            httpStatus: response.status,
            errorDetails,
          });

          break;
        case 403:
          authError = ExtensionAuthErrorFactory.createPermissionDeniedError({
            endpoint,
            httpStatus: response.status,
            errorDetails,
          });

          break;
        case 503:
          authError = ExtensionAuthErrorFactory.createServiceUnavailableError({
            endpoint,
            httpStatus: response.status,
            errorDetails,
          });

          break;
        default:
          authError = ExtensionAuthErrorFactory.createFromHttpStatus(
            response.status,
            errorDetails?.message,
            { endpoint, errorDetails }
          );
      }
      // Attempt recovery
      const recoveryResult = await extensionAuthRecoveryManager.attemptRecovery(
        authError,
        endpoint,
        operation
      );
      // Return fallback data if available
      if (recoveryResult.fallbackData) {
        logger.info(`Using fallback data for ${endpoint}:`, {
          strategy: recoveryResult.strategy,
          message: recoveryResult.message,
        });

        return recoveryResult.fallbackData;
      }
      // If no fallback data but recovery was successful, return null to allow retry
      if (recoveryResult.success) {
        return null;
      }
      // Try to get cached or static fallback data
      const fallbackData = getExtensionFallbackData(operation);
      if (fallbackData) {
        logger.info(`Using static fallback data for ${endpoint}`);
        return fallbackData;
      }
      return null;
    } catch (error) {
      logger.error("Error in extension error handling:", error);
      return null;
    }
  }
  /**
   * Request interceptor for automatic token injection and preprocessing
   */
  private async interceptRequest(
    endpoint: string,
    options: RequestInit
  ): Promise<RequestInit> {
    const interceptedOptions = { ...options };
    // Ensure headers object exists
    if (!interceptedOptions.headers) {
      interceptedOptions.headers = {};
    }
    // Add authentication headers
    const authHeaders = await this.getAuthHeaders(endpoint);
    interceptedOptions.headers = {
      ...interceptedOptions.headers,
      ...authHeaders,
    };
    // Add correlation ID if not present
    const headers = interceptedOptions.headers as Record<string, string>;
    if (!headers["X-Correlation-ID"]) {
      headers["X-Correlation-ID"] =
        globalThis.crypto?.randomUUID?.() ??
        Math.random().toString(36).slice(2);
    }
    // Add client identification for extension endpoints
    if (this.isExtensionEndpoint(endpoint)) {
      headers["X-Client-Type"] = "karen-backend-service";
      headers["X-Extension-Request"] = "true";
    }
    // Ensure credentials are included for same-origin requests
    if (!interceptedOptions.credentials && typeof window !== "undefined") {
      interceptedOptions.credentials = "include";
    }
    if (this.debugLogging) {
      logger.debug("Request intercepted:", {
        endpoint,
        method: interceptedOptions.method || "GET",
        hasAuth: !!headers["Authorization"],
        correlationId: headers["X-Correlation-ID"],
      });
    }
    return interceptedOptions;
  }
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    useCache: boolean = false,
    cacheTtl: number = webUIConfig.cacheTtl,
    maxRetries: number = webUIConfig.maxRetries,
    retryDelay: number = webUIConfig.retryDelay,
    safeFallback?: T
  ): Promise<T> {
    const isAbsoluteEndpoint = /^https?:\/\//i.test(endpoint);
    // ALWAYS force empty baseUrl in browser to ensure Next.js API routes are used
    const baseUrl = typeof window !== "undefined" ? "" : this.config.baseUrl;
    const primaryUrl = isAbsoluteEndpoint ? endpoint : `${baseUrl}${endpoint}`;
    // Debug logging for URL construction
    if (this.requestLogging && typeof window !== "undefined") {
      logger.debug(`Making request to: ${primaryUrl}`);
    }
    const cacheKey = `${primaryUrl}:${JSON.stringify(options)}`;
    // Determine per-request timeout based on endpoint type
    const isLongEndpoint =
      !isAbsoluteEndpoint &&
      /^\/api\/(models|providers|health)(\/|$)/.test(endpoint);
    const REQUEST_SHORT_TIMEOUT = this.config.timeout;
    const env =
      typeof process === "object" && process.env ? process.env : undefined;
    const envLongTimeout =
      env && env.NEXT_PUBLIC_API_LONG_TIMEOUT_MS
        ? Number(env.NEXT_PUBLIC_API_LONG_TIMEOUT_MS)
        : env && env.KAREN_API_LONG_TIMEOUT_MS
        ? Number(env.KAREN_API_LONG_TIMEOUT_MS)
        : NaN;
    const REQUEST_LONG_TIMEOUT =
      Number.isFinite(envLongTimeout) && envLongTimeout > 0
        ? envLongTimeout
        : Math.max(REQUEST_SHORT_TIMEOUT, 120000);
    const perRequestTimeout = isLongEndpoint
      ? REQUEST_LONG_TIMEOUT
      : REQUEST_SHORT_TIMEOUT;
    // Circuit breaker check
    const now = Date.now();
    if (this.circuitOpenUntil > now) {
      if (this.requestLogging) {
        console.warn(
          `[CIRCUIT] Skipping request to ${endpoint} - open until ${new Date(
            this.circuitOpenUntil
          ).toISOString()}`
        );
      }
      if (safeFallback !== undefined) {
        return safeFallback;
      }
      throw new APIError(
        "Service unavailable",
        503,
        {
          error: "Circuit breaker open",
          message: "Service temporarily unavailable",
          type: "CIRCUIT_OPEN",
          timestamp: new Date().toISOString(),
        },
        false
      );
    }
    // Check cache first
    if (useCache && this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey)!;
      if (Date.now() - cached.timestamp < cached.ttl) {
        return cached.data as T;
      }
      this.cache.delete(cacheKey);
    }
    // Use request interceptor for automatic token injection and preprocessing
    const interceptedOptions = await this.interceptRequest(endpoint, options);
    const headers = interceptedOptions.headers as Record<string, string>;
    const correlationId = headers["X-Correlation-ID"];
    let lastError: Error | null = null;
    // Log request if enabled
    if (this.requestLogging) {
      let bodyLog: unknown;
      if (options.body) {
        try {
          bodyLog = JSON.parse(options.body as string);
        } catch {
          bodyLog = "[non-JSON body]";
        }
      }
      logger.info(`[REQUEST] ${options.method || "GET"} ${primaryUrl}`, {
        headers: this.debugLogging
          ? headers
          : {
              "Content-Type": headers["Content-Type"],
              Authorization: headers["Authorization"] ? "[REDACTED]" : "none",
            },
        body: bodyLog,
        correlationId,
        timeoutMs: perRequestTimeout,
      });
    }
    const performanceStart = this.performanceMonitoring ? performance.now() : 0;
    // Candidate base URLs (primary + configured fallbacks)
    let candidateBases: string[] = [];
    if (!isAbsoluteEndpoint) {
      // If baseUrl is empty, we're using Next.js API routes - no fallbacks needed
      if (this.config.baseUrl === "") {
        candidateBases = [""];
      } else {
        const set = new Set<string>();
        set.add(this.config.baseUrl);
        for (const u of webUIConfig.fallbackBackendUrls) {
          if (u && u !== this.config.baseUrl) set.add(u);
        }
        // REMOVED: Direct backend fallbacks in browser to prevent bypassing Next.js API routes
        // All browser requests should go through Next.js API routes to avoid rate limiting
        // and ensure proper authentication header forwarding
        candidateBases = Array.from(set);
        // Debug logging for fallback URLs in browser
        if (this.requestLogging && typeof window !== "undefined") {
          logger.debug("Browser fallback bases configured", { candidateBases });
        }
      }
    }
    // Retry logic for transient failures
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        let response: Response | null = null;
        let lastFetchError: unknown = null;
        if (isAbsoluteEndpoint) {
          // Single absolute URL request
          try {
            const controller = new AbortController();
            const timeoutId = setTimeout(
              () => controller.abort(),
              perRequestTimeout
            );
            response = await fetch(primaryUrl, {
              ...interceptedOptions,
              signal: controller.signal,
            });
            clearTimeout(timeoutId);
          } catch (fetchErr) {
            lastFetchError = fetchErr;
          }
        } else {
          // Try primary then fallbacks for this attempt
          for (const base of candidateBases) {
            const url = `${base}${endpoint}`;
            try {
              const controller = new AbortController();
              const timeoutId = setTimeout(
                () => controller.abort(),
                perRequestTimeout
              );
              response = await fetch(url, {
                ...interceptedOptions,
                signal: controller.signal,
              });
              clearTimeout(timeoutId);
              if (response && response.ok) {
                // If fallback succeeded, promote it to primary for future requests
                if (base !== this.config.baseUrl) {
                  if (this.requestLogging) {
                    logger.debug("Promoting fallback base to primary", { base });
                  }
                  this.config.baseUrl = base;
                }
                break;
              }
              // Non-OK responses are handled below
            } catch (fetchErr) {
              lastFetchError = fetchErr;
              if (this.requestLogging) {
                console.warn(
                  `[NETWORK] ${url} failed:`,
                  (fetchErr as Error)?.message || fetchErr
                );
              }
              // Try next candidate
              continue;
            }
          }
        }
        // If no response obtained from any candidate, throw network error
        if (!response) {
          throw lastFetchError || new Error("Network error");
        }
        if (!response.ok) {
          // Reduce noise for expected health and extension auth failures
          const isHealthCheck =
            endpoint.includes("/health") ||
            endpoint.includes("/api/plugins") ||
            endpoint.includes("/analytics/system");

          const isExtensionAuthError =
            this.isExtensionEndpoint(endpoint) &&
            [401, 403].includes(response.status);

          if (isHealthCheck) {
            logger.warn("KarenBackendService 4xx/5xx", {
              status: response.status,
              url: response.url,
            });
          } else if (isExtensionAuthError) {
            logger.warn("KarenBackendService extension auth failure", {
              status: response.status,
              url: response.url,
              endpoint,
            });
          } else {
            // Rate-limit repetitive retryable errors (like 504) to avoid console spam
            const rateLimitKey = `status_${response.status}_${endpoint}`;
            const isRetryable = APIError.isRetryableStatus(response.status);
            if (isRetryable) {
              logger.error(
                "KarenBackendService 4xx/5xx",
                { status: response.status, url: response.url },
                { rateLimitKey, rateLimitMs: 5000 }
              );
            } else {
              logger.error("KarenBackendService 4xx/5xx", {
                status: response.status,
                url: response.url,
              });
            }
          }
          // Try to parse structured error response
          let errorDetails: WebUIErrorResponse | undefined;
          try {
            const ct = response.headers.get("content-type") || "";
            if (ct.includes("application/json")) {
              const errorData = await response.json();
              if (errorData && typeof errorData === "object") {
                errorDetails = errorData as WebUIErrorResponse;
              }
            } else {
              const text = await response.text();
              errorDetails = {
                error: text || response.statusText,
                message: text || response.statusText,
                type: "HTTP_ERROR",
                timestamp: new Date().toISOString(),
              };
            }
          } catch {
            // If we can't parse the error response, create a basic one
            errorDetails = {
              error: response.statusText,
              message: `HTTP ${response.status}: ${response.statusText}`,
              type: "HTTP_ERROR",
              timestamp: new Date().toISOString(),
            };
          }
          const apiError = APIError.fromResponse(response, errorDetails);
          // Handle extension endpoint errors with comprehensive error handling
          if (
            this.isExtensionEndpoint(endpoint) &&
            (response.status === 401 ||
              response.status === 403 ||
              response.status === 503)
          ) {
            const fallbackData = await this.handleExtensionError(
              endpoint,
              response,
              errorDetails
            );
            if (fallbackData !== null) {
              return fallbackData as T;
            }
          }
          // Public fallback for read-only model endpoints when unauthorized/forbidden
          if (
            (response.status === 401 || response.status === 403) &&
            endpoint.startsWith("/api/models/")
          ) {
            try {
              const publicEndpoint = endpoint.replace(
                "/api/models/",
                "/api/models/public/"
              );
              if (publicEndpoint !== endpoint) {
                if (this.requestLogging) {
                  logger.debug("Attempting public model fallback", {
                    publicEndpoint,
                  });
                }
                const controller = new AbortController();
                const timeoutId = setTimeout(
                  () => controller.abort(),
                  perRequestTimeout
                );
                const publicResp = await fetch(
                  `${this.config.baseUrl}${publicEndpoint}`,
                  {
                    ...interceptedOptions,
                    signal: controller.signal,
                  }
                );
                clearTimeout(timeoutId);
                if (publicResp.ok) {
                  const ct = publicResp.headers.get("content-type") || "";
                  const data = ct.includes("application/json")
                    ? await publicResp.json()
                    : await publicResp.text();
                  return data as T;
                }
              }
            } catch {
              // ignore and fall through to normal handling
            }
          }
          // Handle authentication failures with extension-specific retry logic
          const shouldRetryAuth = await this.handleAuthFailure(
            endpoint,
            response,
            attempt,
            maxRetries
          );
          if (shouldRetryAuth) {
            // Wait a bit before retrying with fresh auth
            await this.sleep(500);
            continue;
          }
          // Don't retry non-retryable errors
          if (!apiError.isRetryable || attempt === maxRetries) {
            apiError.errorInfo = errorHandler.handleApiError(
              this.toApiError(apiError, endpoint),
              endpoint
            );
            throw apiError;
          }
          lastError = apiError;
          console.warn(
            `Request failed (attempt ${attempt + 1}/${maxRetries + 1}):`,
            apiError.message
          );
          // Wait before retrying with exponential backoff
          // Use longer delays for rate limiting (429) and service unavailable (503) errors
          let baseDelay = retryDelay;
          if (response.status === 429) {
            baseDelay = retryDelay * 3; // Rate limiting
          } else if (response.status === 503) {
            baseDelay = retryDelay * 2; // Service unavailable
          }
          // Apply exponential backoff for extension endpoints
          const backoffMultiplier = this.isExtensionEndpoint(endpoint)
            ? Math.pow(2, attempt)
            : Math.pow(1.5, attempt);
          const delay = baseDelay * backoffMultiplier;
          if (this.debugLogging) {
            console.log(
              `Retrying ${endpoint} in ${delay}ms (attempt ${attempt + 1}/${
                maxRetries + 1
              })`
            );
          }
          await this.sleep(delay);
          continue;
        }
        const contentType = response.headers.get("content-type") || "";
        let data: unknown = null;
        if (contentType.includes("application/json")) {
          try {
            const text = await response.text();
            if (text.trim() === "") {
              // Handle empty JSON responses gracefully
              data =
                response.status >= 400
                  ? { error: "Empty response from server" }
                  : {};
            } else {
              data = JSON.parse(text);
            }
          } catch (parsingError) {
            if (this.debugLogging) {
              logger.debug("Failed to parse JSON response", {
                endpoint,
                error: parsingError,
              });
            }
            data =
              response.status >= 400 ? { error: "Invalid JSON response" } : {};
          }
        } else {
          const text = await response.text();
          data = text ? { body: text } : null;
        }
        const responseTime = this.performanceMonitoring
          ? performance.now() - performanceStart
          : 0;
        // Record performance metrics
        if (this.performanceMonitoring) {
          const performanceMonitor = getPerformanceMonitor();
          performanceMonitor.recordRequest(
            endpoint,
            options.method || "GET",
            performanceStart,
            performance.now(),
            response.status,
            JSON.stringify(data).length
          );
          if (responseTime > 5000) {
            // Log slow requests (>5s)
            console.warn(
              `[PERFORMANCE] Slow request detected: ${endpoint} took ${responseTime.toFixed(
                2
              )}ms`
            );
          }
        }
        // Log response if enabled
        if (this.requestLogging) {
          console.log(
            `[RESPONSE] ${response.status} ${options.method || "GET"} ${
              response.url
            }`,
            {
              status: response.status,
              responseTime: this.performanceMonitoring
                ? `${responseTime.toFixed(2)}ms`
                : undefined,
              dataSize: JSON.stringify(data).length,
              cached: useCache,
              correlationId,
            }
          );
        }
        // Cache successful responses
        if (useCache) {
          this.cache.set(cacheKey, {
            data,
            timestamp: Date.now(),
            ttl: cacheTtl,
          });
        }
        this.failureCount = 0;
        this.circuitOpenUntil = 0;
        return data as T;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        // Handle network errors and timeouts
        if (error instanceof Error) {
          if (error.name === "AbortError") {
            lastError = new APIError(
              "Request timeout",
              408,
              {
                error: "Request timeout",
                message: "The request took too long to complete",
                type: "TIMEOUT_ERROR",
                timestamp: new Date().toISOString(),
              },
              true
            );
          } else if (error instanceof TypeError) {
            const online =
              typeof navigator === "undefined" ? true : navigator.onLine;
            if (!online) {
              lastError = new APIError(
                "Offline",
                0,
                {
                  error: "Offline",
                  message: "You appear to be offline. Request queued.",
                  type: "NETWORK_ERROR",
                  timestamp: new Date().toISOString(),
                },
                false
              );
              this.enqueueOfflineRequest({
                endpoint,
                options,
                useCache,
                cacheTtl,
                maxRetries,
                retryDelay,
              });
            } else {
              lastError = new APIError(
                "Network error",
                0,
                {
                  error: "Network error",
                  message: "Unable to connect to the backend service",
                  type: "NETWORK_ERROR",
                  timestamp: new Date().toISOString(),
                },
                true
              );
            }
          }
        }
        // Don't retry if it's not a retryable error or we've exhausted retries
        if (
          !(lastError instanceof APIError && lastError.isRetryable) ||
          attempt === maxRetries
        ) {
          // Record performance metrics for failed requests
          if (this.performanceMonitoring && lastError instanceof APIError) {
            const performanceMonitor = getPerformanceMonitor();
            performanceMonitor.recordRequest(
              endpoint,
              options.method || "GET",
              performanceStart,
              performance.now(),
              lastError.status,
              0,
              lastError.message
            );
          }
          if (lastError instanceof APIError) {
            lastError.errorInfo = errorHandler.handleApiError(
              this.toApiError(lastError, endpoint),
              endpoint
            );
          }
          this.failureCount++;
          if (this.failureCount >= webUIConfig.circuitBreakerThreshold) {
            this.circuitOpenUntil =
              Date.now() + webUIConfig.circuitBreakerResetTime;
            if (this.requestLogging) {
              logger.error(
                `[CIRCUIT] Opened for ${webUIConfig.circuitBreakerResetTime}ms after ${this.failureCount} failures`,
                undefined
              );
            }
          }
          logger.error(
            `Backend request failed for ${endpoint} after ${
              attempt + 1
            } attempts:`,
            lastError
          );
          if (safeFallback !== undefined) {
            return safeFallback;
          }
          throw lastError;
        }
        console.warn(
          `Request failed (attempt ${attempt + 1}/${maxRetries + 1}):`,
          lastError.message
        );
        // Wait before retrying with exponential backoff
        // Use longer delays for rate limiting errors
        const baseDelay =
          lastError instanceof APIError && lastError.status === 429
            ? retryDelay * 3
            : retryDelay;
        await this.sleep(baseDelay * Math.pow(2, attempt));
      }
    }
    // This should never be reached, but just in case
    if (lastError instanceof APIError && !lastError.errorInfo) {
      lastError.errorInfo = errorHandler.handleApiError(
        this.toApiError(lastError, endpoint),
        endpoint
      );
    }
    this.failureCount++;
    if (this.failureCount >= webUIConfig.circuitBreakerThreshold) {
      this.circuitOpenUntil = Date.now() + webUIConfig.circuitBreakerResetTime;
      if (this.requestLogging) {
        logger.error(
          `[CIRCUIT] Opened for ${webUIConfig.circuitBreakerResetTime}ms after ${this.failureCount} failures`,
          undefined
        );
      }
    }
    if (safeFallback !== undefined) {
      return safeFallback;
    }
    throw lastError || new Error("Unknown error occurred");
  }
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
  private enqueueOfflineRequest(req: OfflineRequest): void {
    this.offlineQueue.push(req);
  }
  private replayOfflineQueue = async (): Promise<void> => {
    const queued = [...this.offlineQueue];
    this.offlineQueue = [];
    for (const req of queued) {
      try {
        await this.makeRequest(
          req.endpoint,
          req.options,
          req.useCache,
          req.cacheTtl,
          req.maxRetries,
          req.retryDelay
        );
      } catch (err) {
        logger.error("Queued request failed:", err);
      }
    }
  };
  public getOfflineQueueSize(): number {
    return this.offlineQueue.length;
  }
  private toApiError(error: APIError, endpoint: string): ApiError {
    return {
      name: "ApiError",
      message: error.message,
      status: error.status,
      endpoint,
      isNetworkError:
        error.details?.type === "NETWORK_ERROR" || error.status === 0,
      isCorsError: error.details?.type === "CORS_ERROR" || false,
      isTimeoutError: error.details?.type === "TIMEOUT_ERROR" || false,
      originalError: error,
    } as ApiError;
  }
  // Session token management
  private getStoredSessionToken(): string | null {
    if (typeof window === "undefined") return null;
    try {
      // First try to get the token from AuthContext (localStorage)
      const authToken = localStorage.getItem("karen_access_token");
      if (authToken && authToken !== "null" && authToken !== "undefined") {
        if (this.debugLogging) {
          console.log(
            "Found auth token in localStorage:",
            authToken.substring(0, 50) + "..."
          );
        }
        return authToken;
      }
      // Fallback to the old sessionStorage token
      const sessionToken = sessionStorage.getItem("kari_session_token");
      if (
        sessionToken &&
        sessionToken !== "null" &&
        sessionToken !== "undefined"
      ) {
        if (this.debugLogging) {
          console.log(
            "Found auth token in sessionStorage:",
            sessionToken.substring(0, 50) + "..."
          );
        }
        return sessionToken;
      }
      if (this.debugLogging) {
        console.log("No auth token found in storage");
      }
      return null;
    } catch (storageError) {
      if (this.debugLogging) {
        logger.debug("Failed to access session storage", { storageError });
      }
      return null;
    }
  }
  private storeSessionToken(token: string): void {
    try {
      // Store in localStorage to match AuthContext behavior
      localStorage.setItem("karen_access_token", token);
      // Also keep the old sessionStorage for backward compatibility
      sessionStorage.setItem("kari_session_token", token);
    } catch (storageError) {
      if (this.debugLogging) {
        logger.debug("Failed to store session token", { storageError });
      }
    }
  }
  private clearSessionToken(): void {
    try {
      // Clear from both storage locations
      localStorage.removeItem("karen_access_token");
      localStorage.removeItem("karen_refresh_token");
      sessionStorage.removeItem("kari_session_token");
    } catch (storageError) {
      if (this.debugLogging) {
        logger.debug("Failed to clear session token", { storageError });
      }
    }
  }
  private getSessionId(): string {
    return initializeSessionId();
  }
  // Check authentication status without automatic login attempts
  private async ensureAuthenticated(): Promise<boolean> {
    // Check if we already have a valid session token
    const existingToken = this.getStoredSessionToken();
    if (existingToken) {
      try {
        // Verify the token is still valid with a short timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
        await this.makeRequest("/api/auth/me", {
          headers: { Authorization: `Bearer ${existingToken}` },
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        if (this.debugLogging) {
          logger.debug("Existing session token verified successfully.");
        }
        return true;
      } catch (error) {
        if (this.debugLogging) {
          logger.debug("Existing session token validation failed.", { error });
        }
        // Token is invalid, clear it
        this.clearSessionToken();
      }
    }
    // Try to check for HttpOnly cookie session without token
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
      await this.makeRequest("/api/auth/validate-session", {
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (this.debugLogging) {
        logger.debug("HttpOnly session validation succeeded.");
      }
      return true;
    } catch (error) {
      if (this.debugLogging) {
        logger.debug("HttpOnly session validation failed.", { error });
      }
    }
    return false;
  }
  // Memory Service Integration
  async storeMemory(
    content: string,
    metadata: Record<string, unknown> = {},
    tags: string[] = [],
    userId?: string,
    sessionId?: string
  ): Promise<string | null> {
    const sid = sessionId ?? this.getSessionId();
    try {
      // Check authentication status before attempting to store memory
      const isAuthenticated = await this.ensureAuthenticated();
      if (!isAuthenticated) {
        return null;
      }
      // Prepare the request payload for the secure memory endpoint
      const requestPayload = {
        user_id: userId || sid || "anonymous",
        org_id: null,
        text: content,
        tags: tags || [],
        importance: 5,
        decay: "short",
        session_id: sid,
        metadata: metadata || {},
      };
      logger.info("Storing memory with payload:", requestPayload);
      // Use the secure memory storage endpoint with proper authentication
      const response = await this.makeRequest<{ memory_id: string }>(
        "/api/memory/commit",
        {
          method: "POST",
          body: JSON.stringify(requestPayload),
        }
      );

      logger.info("Memory store response:", response);
      return response.memory_id;
    } catch (error) {
      if (error instanceof APIError) {
        // Handle authentication errors gracefully without retry
        if (error.status === 401) {
          this.clearSessionToken();
          return null;
        } else if (error.details?.type === "SERVICE_UNAVAILABLE") {
          return null;
        } else if (error.details?.type === "VALIDATION_ERROR") {
          return null;
        }
      }
      logger.error("Failed to store memory:", error);
      return null;
    }
  }
  async queryMemories(query: MemoryQuery): Promise<MemoryEntry[]> {
    try {
      // Check authentication status before querying memories
      const isAuthenticated = await this.ensureAuthenticated();
      if (!isAuthenticated) {
        return [];
      }
      // Transform the query to match the backend format
      const sid = query.session_id ?? this.getSessionId();
      const backendQuery = {
        user_id: query.user_id || sid || "anonymous",
        org_id: null,
        query: query.text,
        top_k: query.top_k || 12,
        session_id: sid,
      };
      const response = await this.makeRequest<{ memories: MemoryEntry[] }>(
        "/api/memory/search",
        {
          method: "POST",
          body: JSON.stringify(backendQuery),
        }
      );
      // Transform the response to match the expected format
      const memories = (response.memories || []).map((mem) => ({
        id: mem.id,
        content: mem.content,
        metadata: mem.metadata || {},
        timestamp: mem.timestamp,
        similarity_score: mem.similarity_score,
        tags: mem.tags || [],
        user_id: mem.user_id,
        session_id: mem.session_id,
      }));
      return memories;
    } catch (error) {
      if (error instanceof APIError) {
        if (error.details?.type === "MEMORY_ERROR") {
          logger.warn("Memory service error:", error.details);
          return []; // Return empty array for graceful degradation
        } else if (error.details?.type === "SERVICE_UNAVAILABLE") {
          logger.warn("Memory service unavailable, using cache if available");
          // Try to return cached results or empty array
          return this.getCachedMemories(query) || [];
        }
      }
      logger.error("Failed to query memories:", error);
      return [];
    }
  }
  private getCachedMemories(query: MemoryQuery): MemoryEntry[] | null {
    // Simple cache lookup for memory queries
    const cacheKey = `memory:${JSON.stringify(query)}`;
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return (cached.data as { memories?: MemoryEntry[] })?.memories || [];
    }
    return null;
  }
  async getMemoryStats(userId?: string): Promise<Record<string, unknown>> {
    try {
      const params = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
      return await this.makeRequest<Record<string, unknown>>(
        `/api/memory/stats${params}`,
        {},
        true
      );
    } catch (error) {
      if (error instanceof APIError) {
        if (error.details?.type === "SERVICE_UNAVAILABLE") {
          return { total_memories: 0, last_updated: new Date().toISOString() };
        }
      }
      logger.error("Failed to get memory stats:", error);
      return {};
    }
  }
  // Plugin Service Integration
  async getAvailablePlugins(): Promise<PluginInfo[]> {
    const cacheKey = "/api/plugins:{}";
    const cached = this.cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return (cached.data as { plugins?: PluginInfo[] })?.plugins || [];
    }
    try {
      const response = await this.makeRequest<{ plugins: PluginInfo[] }>(
        "/api/plugins",
        {},
        false
      );
      this.cache.set(cacheKey, {
        data: response,
        timestamp: Date.now(),
        ttl: webUIConfig.cacheTtl,
      });

      return response.plugins || [];
    } catch (error) {
      if (
        error instanceof APIError &&
        error.details?.type === "SERVICE_UNAVAILABLE"
      ) {
        if (cached) {
          return (cached.data as { plugins?: PluginInfo[] })?.plugins || [];
        }
      }
      logger.error("Failed to get available plugins:", error);
      return [];
    }
  }
  async executePlugin(
    pluginName: string,
    parameters: Record<string, unknown> = {},
    userId?: string
  ): Promise<PluginExecutionResult> {
    try {
      return await this.makeRequest<PluginExecutionResult>(
        "/api/plugins/execute",
        {
          method: "POST",
          body: JSON.stringify({
            plugin_name: pluginName,
            parameters,
            user_id: userId,
          }),
        }
      );
    } catch (error) {
      let errorMessage = "Unknown error";
      if (error instanceof APIError) {
        if (error.details?.type === "PLUGIN_ERROR") {
          errorMessage = error.details.message || "Plugin execution failed";
        } else if (error.details?.type === "SERVICE_UNAVAILABLE") {
          errorMessage = "Plugin service is temporarily unavailable";
        } else if (error.details?.type === "VALIDATION_ERROR") {
          errorMessage = "Invalid plugin parameters";
        } else {
          errorMessage = error.message;
        }
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }
      logger.error(`Failed to execute plugin ${pluginName}:`, error);
      return {
        success: false,
        error: errorMessage,
        plugin_name: pluginName,
        timestamp: new Date().toISOString(),
      };
    }
  }
  // Analytics Service Integration
  async getSystemMetrics(): Promise<SystemMetrics> {
    try {
      // Try public endpoint first, then fall back to authenticated endpoint
      try {
        return await this.makeRequestPublic<SystemMetrics>(
          "/api/analytics/usage",
          {},
          true,
          60000
        );
      } catch (publicError) {
        if (this.debugLogging) {
          logger.debug("Public analytics endpoint failed", { publicError });
        }
        // If public endpoint fails, try authenticated endpoint
        return await this.makeRequest<SystemMetrics>(
          "/api/web/analytics/system",
          {},
          true,
          60000
        );
      }
    } catch (error) {
      // Silently handle authentication errors in health monitoring
      if (error instanceof Error && error.message.includes("401")) {
        // Authentication required - use fallback data
      } else {
        console.error(
          "System metrics unavailable:",
          (error as Error)?.message || error
        );
      }
      // Return mock data as fallback
      return {
        cpu_usage: 45.2,
        memory_usage: 68.5,
        disk_usage: 32.1,
        active_sessions: 12,
        total_requests: 1547,
        error_rate: 0.02,
        response_time_avg: 0.3,
        uptime_hours: 168.5,
        timestamp: new Date().toISOString(),
      };
    }
  }
  async getUsageAnalytics(timeRange: string = "24h"): Promise<UsageAnalytics> {
    try {
      return await this.makeRequest<UsageAnalytics>(
        `/api/analytics/usage?range=${timeRange}`,
        {},
        true
      );
    } catch (error) {
      logger.error("Failed to get usage analytics:", error);
      // Return mock data as fallback
      return {
        total_interactions: 234,
        unique_users: 18,
        popular_features: [
          { name: "Chat", usage_count: 156 },
          { name: "Memory", usage_count: 89 },
          { name: "Plugins", usage_count: 67 },
        ],
        peak_hours: [9, 14, 16, 20],
        user_satisfaction: 4.2,
        time_range: timeRange,
        timestamp: new Date().toISOString(),
      };
    }
  }
  // Health Check
  async healthCheck(): Promise<{
    status: "healthy" | "degraded" | "error";
    services: Record<string, unknown>;
    timestamp: string;
  }> {
    try {
      // Try different possible health check endpoints
      const healthEndpoints = [
        "/api/health",
        "/health",
        "/api/status",
        "/status",
        "/api/ping",
        "/ping",
      ];
      logger.info(
        "🏥 Starting health check, trying endpoints:",
        healthEndpoints
      );
      for (const endpoint of healthEndpoints) {
        try {
          logger.info(`🏥 Trying health endpoint: ${endpoint}`);
          const result = await this.makeRequest<{
            status: "healthy" | "degraded" | "error";
            services: Record<string, unknown>;
            timestamp: string;
          }>(endpoint, {}, false);
          logger.info(`🏥 Health endpoint ${endpoint} succeeded:`, result);
          return result;
        } catch (error) {
          logger.warn(
            `🏥 Health endpoint ${endpoint} failed:`,
            error instanceof Error ? error.message : error
          );
          continue;
        }
      }
      // If all health endpoints fail, backend is likely running but doesn't support health checks
      // Return degraded status instead of error to indicate basic connectivity
      logger.info(
        "🏥 Backend is running but health endpoints are not available - using degraded mode"
      );
      return {
        status: "degraded",
        services: {
          backend: {
            status: "degraded",
            message: "Backend running but health checks not supported",
            connectivity: "available",
          },
        },
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      logger.error("Health check failed:", error);
      return {
        status: "error",
        services: {
          backend: {
            status: "error",
            error: error instanceof Error ? error.message : "Unknown error",
          },
        },
        timestamp: new Date().toISOString(),
      };
    }
  }
  // Enhanced Chat Integration with Memory
  async processUserMessage(
    message: string,
    conversationHistory: ChatMessage[],
    settings: KarenSettings,
    userId?: string,
    sessionId?: string,
    llmPreferences?: {
      preferredLLMProvider?: string;
      preferredModel?: string;
    },
    tools?: Record<string, (...args: unknown[]) => unknown>
  ): Promise<HandleUserMessageResult> {
    const requestId = `req_${Date.now()}_${Math.random()
      .toString(36)
      .substr(2, 9)}`;
    const sid = sessionId ?? this.getSessionId();
    try {
      // Ensure we're authenticated before processing the message
      const isAuthenticated = await this.ensureAuthenticated();
      if (!isAuthenticated) {
        // Continue processing without memory features rather than failing completely
      }
      // Log request for debugging
      logger.info(`[${requestId}] Processing user message:`, {
        message:
          message.substring(0, 100) + (message.length > 100 ? "..." : ""),
        userId,
        sessionId: sid,
        historyLength: conversationHistory.length,
      });

      // First, query relevant memories
      const relevantMemories = await this.queryMemories({
        text: message,
        user_id: userId,
        session_id: sid,
        top_k: 5,
        similarity_threshold: 0.7,
      });

      // Use the secure AI orchestrator endpoint with proper authentication
      const startTime = Date.now();
      const aiResponse = await this.makeRequest<{
        response: string;
        requires_plugin: boolean;
        plugin_to_execute?: string;
        plugin_parameters?: Record<string, unknown>;
        memory_to_store?: Record<string, unknown>;
        suggested_actions?: string[];
        ai_data?: Record<string, unknown>;
        proactive_suggestion?: string;
      }>("/api/ai/conversation-processing", {
        method: "POST",
        body: JSON.stringify({
          prompt: message,
          conversation_history: conversationHistory.map((msg) => ({
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp.toISOString(),
          })),
          user_settings: settings,
          session_id: sid,
          context: {
            relevant_memories: relevantMemories.map((mem) => ({
              content: mem.content,
              similarity_score: mem.similarity_score,
              tags: mem.tags,
            })),
            user_id: userId,
            session_id: sid,
            tools: tools ? Object.keys(tools) : undefined,
          },
          include_memories: true,
          include_insights: true,
          // Include LLM preferences for proper fallback hierarchy
          llm_preferences: {
            preferred_llm_provider:
              llmPreferences?.preferredLLMProvider || "llama-cpp",
            preferred_model:
              llmPreferences?.preferredModel || "llama3.2:latest",
          },
        }),
      });

      // Transform the AI orchestrator response to match the expected HandleUserMessageResult format
      const response: HandleUserMessageResult = {
        finalResponse: aiResponse.response,
        aiDataForFinalResponse: aiResponse.ai_data,
        suggestedNewFacts: aiResponse.suggested_actions,
        proactiveSuggestion: aiResponse.proactive_suggestion,
      };
      const responseTime = Date.now() - startTime;
      // Log successful response for debugging
      logger.info(`[${requestId}] Chat processing successful:`, {
        responseTime: `${responseTime}ms`,
        responseLength: response.finalResponse?.length || 0,
        hasAiData: !!response.aiDataForFinalResponse,
        hasSuggestions: !!response.suggestedNewFacts,
        hasProactiveSuggestion: !!response.proactiveSuggestion,
      });

      // Store the conversation in memory if successful
      if (response.finalResponse) {
        const conversationText = `User: ${message}\nAssistant: ${response.finalResponse}`;
        await this.storeMemory(
          conversationText,
          {
            type: "conversation",
            user_message: message,
            assistant_response: response.finalResponse,
            request_id: requestId,
          },
          ["conversation", "chat"],
          userId,
          sid
        );
      }
      return response;
    } catch (error) {
      logger.error(`[${requestId}] Failed to process user message:`, error);
      // Handle different error types with specific fallback responses
      if (error instanceof APIError) {
        if (error.details?.type === "CHAT_PROCESSING_ERROR") {
          logger.warn(`[${requestId}] Chat processing error:`, error.details);
          return {
            finalResponse:
              "I'm having trouble processing your message right now. Could you try rephrasing it or asking something else?",
          };
        } else if (error.details?.type === "SERVICE_UNAVAILABLE") {
          logger.warn(`[${requestId}] AI service unavailable:`, error.details);
          return {
            finalResponse:
              "My AI services are temporarily unavailable. Please try again in a few minutes, and I'll be ready to help you.",
          };
        } else if (error.details?.type === "VALIDATION_ERROR") {
          logger.warn(`[${requestId}] Validation error:`, error.details);
          return {
            finalResponse:
              "I noticed there might be an issue with your message format. Could you try asking your question in a different way?",
          };
        } else if (error.details?.type === "TIMEOUT_ERROR") {
          logger.warn(`[${requestId}] Request timeout:`, error.details);
          return {
            finalResponse:
              "Your request is taking longer than expected to process. Please try again with a shorter message or try again in a moment.",
          };
        } else if (error.details?.type === "NETWORK_ERROR") {
          logger.warn(`[${requestId}] Network error:`, error.details);
          return {
            finalResponse:
              "I'm having trouble connecting to my backend services. Please check your internet connection and try again.",
          };
        } else if (error.status === 429) {
          logger.warn(`[${requestId}] Rate limit exceeded:`, error.details);
          return {
            finalResponse:
              "I'm receiving a lot of requests right now. Please wait a moment before sending another message.",
          };
        } else if (error.status >= 500) {
          logger.warn(`[${requestId}] Server error:`, error.details);
          return {
            finalResponse:
              "I'm experiencing some technical difficulties. Please try again in a few minutes.",
          };
        }
      }
      // Generic fallback response for unknown errors
      return {
        finalResponse:
          "I'm having trouble connecting to my backend services right now. Please try again in a moment.",
      };
    }
  }
  // User Management Integration
  async getUserProfile(userId: string): Promise<{
    id: string;
    username: string;
    roles: string[];
    preferences: Record<string, unknown>;
    created_at: string;
    last_active: string;
  } | null> {
    try {
      return await this.makeRequest(
        `/api/users/${encodeURIComponent(userId)}`,
        {},
        true
      );
    } catch (error) {
      if (error instanceof APIError) {
        if (error.status === 404) {
          return null;
        } else if (error.details?.type === "SERVICE_UNAVAILABLE") {
          return null;
        }
      }
      logger.error("Failed to get user profile:", error);
      return null;
    }
  }
  async updateUserPreferences(
    userId: string,
    preferences: Record<string, unknown>
  ): Promise<boolean> {
    try {
      await this.makeRequest(
        `/api/users/${encodeURIComponent(userId)}/preferences`,
        {
          method: "PUT",
          body: JSON.stringify(preferences),
        }
      );
      return true;
    } catch (error) {
      if (error instanceof APIError) {
        if (error.details?.type === "VALIDATION_ERROR") {
          return false;
        } else if (error.details?.type === "SERVICE_UNAVAILABLE") {
          return false;
        }
      }
      logger.error("Failed to update user preferences:", error);
      return false;
    }
  }
  // --- Authentication ---
  async login(email: string, password: string): Promise<LoginResult> {
    // Backend expects an `email` field for authentication
    return await this.makeRequest<LoginResult>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }
  async getCurrentUser(token: string): Promise<CurrentUser | null> {
    try {
      return await this.makeRequest<CurrentUser>("/api/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch {
      return null;
    }
  }
  async updateCredentials(
    token: string,
    newUsername?: string,
    newPassword?: string
  ): Promise<LoginResult> {
    return await this.makeRequest<LoginResult>("/api/auth/update_credentials", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        new_username: newUsername,
        new_password: newPassword,
      }),
    });
  }
  // Clear cache
  clearCache(): void {
    this.cache.clear();
  }
  // Get cache stats
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
    };
  }
  // Public makeRequest method for external use
  async makeRequestPublic<T>(
    endpoint: string,
    options: RequestInit = {},
    useCache: boolean = false,
    cacheTtl: number = webUIConfig.cacheTtl,
    maxRetries: number = webUIConfig.maxRetries,
    retryDelay: number = webUIConfig.retryDelay,
    safeFallback?: T
  ): Promise<T> {
    return this.makeRequest<T>(
      endpoint,
      options,
      useCache,
      cacheTtl,
      maxRetries,
      retryDelay,
      safeFallback
    );
  }
  getBaseUrl(): string {
    // Always return empty string in browser to ensure Next.js API routes are used
    return typeof window !== "undefined" ? "" : this.config.baseUrl;
  }
  /**
   * Force re-initialization of baseUrl for browser environment
   */
  ensureBrowserConfig(): void {
    if (typeof window !== "undefined") {
      this.config.baseUrl = "";
      if (this.requestLogging) {
        logger.info(
          "🔄 KarenBackendService: Forced browser configuration (empty baseUrl)"
        );
      }
    }
  }
  // --- Extension API Methods ---
  /**
   * Get list of available extensions with authentication
   */
  async getExtensions(): Promise<ExtensionInfo[]> {
    try {
      const response = await this.makeRequest<{ extensions: ExtensionInfo[] }>(
        "/api/extensions/"
      );
      return response.extensions || [];
    } catch (error) {
      logger.error("Failed to get extensions:", error);
      if (error instanceof APIError && error.status === 403) {
        logger.warn("Extension access forbidden - check authentication");
      }
      throw error;
    }
  }
  /**
   * Get background tasks for extensions with authentication
   */
  async getExtensionBackgroundTasks(
    extensionName?: string
  ): Promise<BackgroundTaskInfo[]> {
    try {
      const params = extensionName
        ? `?extension_name=${encodeURIComponent(extensionName)}`
        : "";
      const response = await this.makeRequest<{ tasks: BackgroundTaskInfo[] }>(
        `/api/extensions/background-tasks/${params}`
      );
      return response.tasks || [];
    } catch (error) {
      logger.error("Failed to get extension background tasks:", error);
      if (error instanceof APIError && error.status === 403) {
        logger.warn(
          "Extension background task access forbidden - check authentication"
        );
      }
      throw error;
    }
  }
  /**
   * Register a background task for an extension with authentication
   */
  async registerExtensionBackgroundTask(taskData: {
    name: string;
    extension_name: string;
    schedule?: string;
    enabled?: boolean;
    metadata?: Record<string, unknown>;
  }): Promise<{ task_id: string; message: string; status: string }> {
    try {
      return await this.makeRequest("/api/extensions/background-tasks/", {
        method: "POST",
        body: JSON.stringify(taskData),
        headers: { "Content-Type": "application/json" },
      });
    } catch (error) {
      logger.error("Failed to register extension background task:", error);
      if (error instanceof APIError && error.status === 403) {
        logger.warn(
          "Extension background task registration forbidden - check authentication"
        );
      }
      throw error;
    }
  }
  /**
   * Load an extension with authentication
   */
  async loadExtension(
    extensionName: string
  ): Promise<{ message: string; status: string }> {
    try {
      return await this.makeRequest(
        `/api/extensions/${encodeURIComponent(extensionName)}/load`,
        {
          method: "POST",
        }
      );
    } catch (error) {
      logger.error(`Failed to load extension ${extensionName}:`, error);
      if (error instanceof APIError && error.status === 403) {
        logger.warn(
          `Extension load forbidden for ${extensionName} - check authentication`
        );
      }
      throw error;
    }
  }
  /**
   * Unload an extension with authentication
   */
  async unloadExtension(
    extensionName: string
  ): Promise<{ message: string; status: string }> {
    try {
      return await this.makeRequest(
        `/api/extensions/${encodeURIComponent(extensionName)}/unload`,
        {
          method: "POST",
        }
      );
    } catch (error) {
      logger.error(`Failed to unload extension ${extensionName}:`, error);
      if (error instanceof APIError && error.status === 403) {
        logger.warn(
          `Extension unload forbidden for ${extensionName} - check authentication`
        );
      }
      throw error;
    }
  }
  /**
   * Get extension health status
   */
  async getExtensionHealth(): Promise<{
    status: string;
    services: Record<string, unknown>;
    overall_health: string;
    monitoring_active: boolean;
  }> {
    try {
      return await this.makeRequest(
        "/api/extensions/health",
        {},
        false,
        5000,
        1
      ); // Shorter cache and fewer retries for health checks
    } catch (error) {
      logger.warn("Extension health check failed:", error);
      return {
        status: "unhealthy",
        services: {},
        overall_health: "unknown",
        monitoring_active: false,
      };
    }
  }
  /**
   * Check extension authentication status
   */
  async checkExtensionAuthStatus(): Promise<boolean> {
    try {
      const extensionAuthManager = getExtensionAuthManager();
      return extensionAuthManager.isAuthenticated();
    } catch (error) {
      logger.warn("Failed to check extension auth status:", error);
      return false;
    }
  }
  /**
   * Clear extension authentication state
   */
  clearExtensionAuth(): void {
    try {
      const extensionAuthManager = getExtensionAuthManager();
      extensionAuthManager.clearAuth();
      logger.info("Extension authentication state cleared");
    } catch (error) {
      logger.warn("Failed to clear extension auth:", error);
    }
  }
  // --- Extension API Methods ---
  /**
   * List all available extensions
   */
  async listExtensions(): Promise<ExtensionListResponse> {
    try {
      const response = await this.makeRequest<ExtensionListResponse>(
        "/api/extensions/",
        {
          method: "GET",
        },
        false, // useCache
        webUIConfig.cacheTtl,
        webUIConfig.maxRetries,
        webUIConfig.retryDelay,
        {
          extensions: [],
          total: 0,
          message: "Extension list temporarily unavailable",
        }
      );
      return response;
    } catch (error) {
      logger.error("Failed to list extensions:", error);
      return {
        extensions: [],
        total: 0,
        message: "Extension list temporarily unavailable",
      };
    }
  }
  /**
   * List background tasks for extensions
   */
  async listBackgroundTasks(
    extensionName?: string
  ): Promise<BackgroundTaskListResponse> {
    try {
      const queryParams = extensionName
        ? `?extension_name=${encodeURIComponent(extensionName)}`
        : "";
      const response = await this.makeRequest<BackgroundTaskListResponse>(
        `/api/extensions/background-tasks/${queryParams}`,
        {
          method: "GET",
        },
        false, // useCache
        webUIConfig.cacheTtl,
        webUIConfig.maxRetries,
        webUIConfig.retryDelay,
        {
          tasks: [],
          total: 0,
          extension_name: extensionName,
          message: "Background tasks temporarily unavailable",
        }
      );
      return response;
    } catch (error) {
      logger.error("Failed to list background tasks:", error);
      return {
        tasks: [],
        total: 0,
        extension_name: extensionName,
        message: "Background tasks temporarily unavailable",
      };
    }
  }
  /**
   * Register a new background task
   */
  async registerBackgroundTask(
    taskData: Record<string, unknown>
  ): Promise<BackgroundTaskRegistrationResponse> {
    try {
      const response =
        await this.makeRequest<BackgroundTaskRegistrationResponse>(
          "/api/extensions/background-tasks/",
          {
            method: "POST",
            body: JSON.stringify(taskData),
          },
          false, // useCache
          webUIConfig.cacheTtl,
          webUIConfig.maxRetries,
          webUIConfig.retryDelay,
          {
            task_id: "fallback-task-id",
            message: "Background task registration temporarily unavailable",
            status: "unavailable",
          }
        );
      return response;
    } catch (error) {
      logger.error("Failed to register background task:", error);
      return {
        task_id: "fallback-task-id",
        message: "Background task registration temporarily unavailable",
        status: "unavailable",
      };
    }
  }
  /**
   * Get extension status and health information
   */
  async getExtensionStatus(
    extensionName?: string
  ): Promise<Record<string, unknown>> {
    try {
      const endpoint = extensionName
        ? `/api/extensions/${encodeURIComponent(extensionName)}/status`
        : "/api/extensions/status";
      const response = await this.makeRequest<Record<string, unknown>>(
        endpoint,
        {
          method: "GET",
        },
        true, // useCache for status checks
        30000, // 30 second cache
        2, // fewer retries for status checks
        1000,
        {
          status: "unknown",
          message: "Extension status temporarily unavailable",
        }
      );
      return response;
    } catch (error) {
      logger.error("Failed to get extension status:", error);
      return {
        status: "unknown",
        message: "Extension status temporarily unavailable",
      };
    }
  }
}
// Global instance
let karenBackend: KarenBackendService | null = null;
export function getKarenBackend(): KarenBackendService {
  if (!karenBackend) {
    karenBackend = new KarenBackendService();
  }
  // Ensure browser configuration is applied
  if (typeof window !== "undefined") {
    karenBackend.ensureBrowserConfig();
  }
  return karenBackend;
}
export function initializeKarenBackend(
  config?: Partial<BackendConfig>
): KarenBackendService {
  karenBackend = new KarenBackendService(config);
  return karenBackend;
}
export { KarenBackendService, APIError };
