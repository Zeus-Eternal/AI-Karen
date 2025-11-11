/**
 * Extension Error Recovery Integration Example (production-ready)
 *
 * Wires the comprehensive recovery manager into your frontend:
 * - HTTP / network / auth recovery via backend orchestrator
 * - Specialized handling for /api/extensions
 * - Safe fallbacks, structured retries, SSR guards, idempotency
 */

import { logger } from "./logger";
import { errorHandler } from "./error-handler";
// Remove unused import to avoid bundle bloat
// import { getExtensionAuthErrorHandler } from "./auth/extension-auth-error-handler";
import { handleExtensionError } from "./extension-error-integration";
import "./extension-403-fix"; // keep the hotfix loaded early

type FetchArgs = Parameters<typeof fetch>;

// ---------- Types ----------
export type RecoveryAction =
  | { retry: true; delay: number }
  | { fallback_data: unknown }
  | { requires_login: true }
  | { retry: false };

export type HandleKarenBackendErrorFn = (
  status: number,
  url: string,
  operation?: string,
  context?: Record<string, unknown>
) => Promise<RecoveryAction>;

export interface RecoveryResult {
  success: boolean;
  strategy: string;
  message: string;
  fallback_data?: unknown;
  retry_after?: number; // seconds
  requires_user_action: boolean;
  escalated: boolean;
}

export interface ErrorRecoveryRequest {
  type: "http" | "network" | "service" | "auth";
  status_code?: number;
  endpoint: string;
  operation: string;
  message: string;
  context?: Record<string, unknown>;
  service_name?: string;
}

// ---------- Utils ----------
function isBrowser(): boolean {
  return typeof window !== "undefined" && typeof document !== "undefined";
}

type NavigatorWithConnection = Navigator & {
  connection?: {
    effectiveType?: string;
  };
};

type RecoveryWindow = Window & {
  __RECOVERY_FETCH_WRAP__?: boolean;
  handleKarenBackendError?: HandleKarenBackendErrorFn;
};

// ---------- Enhanced Error Handler ----------
export class EnhancedErrorHandler {
  private static instance: EnhancedErrorHandler;
  private recoveryEndpoint = "/api/extension-error-recovery";

  static getInstance(): EnhancedErrorHandler {
    if (!EnhancedErrorHandler.instance) {
      EnhancedErrorHandler.instance = new EnhancedErrorHandler();
    }
    return EnhancedErrorHandler.instance;
  }

  /**
   * Handle HTTP errors with automatic recovery
   */
  async handleHttpError(
    status: number,
    url: string,
    operation: string = "api_call",
    context: Record<string, unknown> = {}
  ): Promise<RecoveryAction> {
    try {
      logger.info(`Attempting error recovery for HTTP ${status} at ${url}`);

      // Specialized routing for Extensions API
      if (url.includes("/api/extensions")) {
        return this.handleExtensionApiError(status, url, operation, context);
      }

      const recoveryRequest: ErrorRecoveryRequest = {
        type: "http",
        status_code: status,
        endpoint: url,
        operation,
        message: `HTTP ${status} error`,
        context: {
          ...context,
          timestamp: new Date().toISOString(),
          user_agent: isBrowser() ? navigator.userAgent : "server",
        },
      };

      const response = await fetch(`${this.recoveryEndpoint}/handle-error`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ error_data: recoveryRequest }),
      });

      if (!response.ok) {
        logger.warn(`Error recovery service unavailable: ${response.status}`);
        return this.handleFallback(status, url, operation);
      }

      const result = (await response.json()) as { recovery_result: RecoveryResult };
      const recoveryResult = result.recovery_result;

      logger.info(
        `Error recovery result: ${recoveryResult.success ? "SUCCESS" : "FAILED"} - ${recoveryResult.message}`
      );

      if (recoveryResult.success) {
        if (recoveryResult.fallback_data) {
          logger.info("Using fallback data from error recovery");
          return { fallback_data: recoveryResult.fallback_data };
        }
        logger.info("Error recovery successful, can retry original request");
        return { retry: true, delay: recoveryResult.retry_after || 0 };
      }

      // Recovery failed — pick best available action
      if (recoveryResult.requires_user_action) {
        errorHandler.showWarning("Action Required", recoveryResult.message);
        return { retry: false };
      }
      if (recoveryResult.fallback_data) {
        logger.info("Using fallback data despite recovery failure");
        return { fallback_data: recoveryResult.fallback_data };
      }
      if (recoveryResult.retry_after) {
        logger.info(`Will retry after ${recoveryResult.retry_after} seconds`);
        return { retry: true, delay: recoveryResult.retry_after };
      }

      return this.handleFallback(status, url, operation);
    } catch (error) {
      logger.error("Error recovery system failed:", error);
      return this.handleFallback(status, url, operation);
    }
  }

  /**
   * Handle extension API errors with specialized recovery
   */
  async handleExtensionApiError(
    status: number,
    url: string,
    operation: string,
    _context: Record<string, unknown> = {}
  ): Promise<RecoveryAction> {
    const extensionErrorResult = handleExtensionError(status, url, operation);
    logger.info(`Extension API error handled: ${extensionErrorResult.message}`);

    if (extensionErrorResult.fallback_data) {
      return { fallback_data: extensionErrorResult.fallback_data };
    }
    if (extensionErrorResult.retry) {
      return { retry: true, delay: extensionErrorResult.delay || 0 };
    }
    if (extensionErrorResult.requires_login) {
      return { requires_login: true };
    }
    return { retry: false };
  }

  /**
   * Handle authentication errors specifically
   */
  async handleAuthError(
    endpoint: string,
    operation: string = "authentication",
    context: Record<string, unknown> = {}
  ): Promise<{ retry: true; delay: number } | { requires_login: true }> {
    try {
      logger.info(`Attempting auth error recovery for ${endpoint}`);

      const response = await fetch(`${this.recoveryEndpoint}/handle-auth-error`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          error_data: {
            endpoint,
            operation,
            context: {
              ...context,
              timestamp: new Date().toISOString(),
            },
          },
        }),
      });

      if (!response.ok) {
        logger.warn(`Auth error recovery service unavailable: ${response.status}`);
        return { requires_login: true };
      }

      const result = (await response.json()) as { recovery_result: RecoveryResult };
      const recoveryResult = result.recovery_result;

      if (recoveryResult.success) {
        logger.info("Auth error recovery successful");
        return { retry: true, delay: recoveryResult.retry_after || 0 };
      }
      if (recoveryResult.requires_user_action) {
        logger.info("Auth error requires user action");
        return { requires_login: true };
      }
      return { requires_login: true };
    } catch (error) {
      logger.error("Auth error recovery failed:", error);
      return { requires_login: true };
    }
  }

  /**
   * Handle network errors with retry logic
   */
  async handleNetworkError(
    endpoint: string,
    errorMessage: string,
    operation: string = "network_request",
    context: Record<string, unknown> = {}
  ): Promise<RecoveryAction> {
    try {
      logger.info(`Attempting network error recovery for ${endpoint}`);

      const response = await fetch(`${this.recoveryEndpoint}/handle-network-error`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          error_data: {
            endpoint,
            operation,
            message: errorMessage,
            context: {
              ...context,
              timestamp: new Date().toISOString(),
              connection_type: isBrowser()
                ? (navigator as NavigatorWithConnection).connection?.effectiveType ?? "unknown"
                : "server",
            },
          },
        }),
      });

      if (!response.ok) {
        logger.warn(`Network error recovery service unavailable: ${response.status}`);
        return { retry: true, delay: 5 };
      }

      const result = (await response.json()) as { recovery_result: RecoveryResult };
      const recoveryResult = result.recovery_result;

      if (recoveryResult.retry_after) {
        logger.info(`Network recovery suggests retry after ${recoveryResult.retry_after} seconds`);
        return { retry: true, delay: recoveryResult.retry_after };
      }
      if (recoveryResult.fallback_data) {
        logger.info("Using fallback data for network error");
        return { fallback_data: recoveryResult.fallback_data };
      }
      return { retry: false };
    } catch (error) {
      logger.error("Network error recovery failed:", error);
      return { retry: true, delay: 5 };
    }
  }

  /**
   * Get error recovery system status
   */
  async getRecoveryStatus(): Promise<{ available: boolean; message?: string } & Record<string, unknown>> {
    try {
      const response = await fetch(`${this.recoveryEndpoint}/status`);
      if (!response.ok) {
        return { available: false, message: "Error recovery service unavailable" };
      }
      const payload = await response.json();
      return { available: true, ...payload };
    } catch (error) {
      logger.error("Failed to get recovery status:", error);
      return { available: false, message: "Error recovery service unavailable" };
    }
  }

  /**
   * Fallback error handling when recovery system is unavailable
   */
  private handleFallback(
    status: number,
    url: string,
    _operation: string
  ):
    | { requires_login: true }
    | { retry: true; delay: number }
    | { retry: false } {
    logger.warn(`Using fallback error handling for ${status} at ${url}`);

    if (status === 401 || status === 403) {
      return { requires_login: true };
    }
    if (status >= 500) {
      return { retry: true, delay: 10 };
    }
    if (status === 429) {
      return { retry: true, delay: 60 };
    }
    errorHandler.showWarning(
      "Request Failed",
      `The request failed with status ${status}. Please try again.`
    );
    return { retry: false };
  }
}

// Export singleton instance
export const enhancedErrorHandler = EnhancedErrorHandler.getInstance();

// ---------- Enhanced Fetch Wrapper ----------
export async function fetchWithRecovery(
  url: string,
  options: RequestInit = {},
  operation: string = "api_call",
  maxRetries: number = 3
): Promise<Response> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);

      if (!response.ok) {
        const rr = await enhancedErrorHandler.handleHttpError(response.status, url, operation, {
          attempt,
          maxRetries,
        });

        if ("retry" in rr && rr.retry && attempt < maxRetries) {
          if (rr.delay > 0) {
            logger.info(`Retrying request after ${rr.delay} seconds`);
            await new Promise((res) => setTimeout(res, rr.delay * 1000));
          }
          continue;
        } else if ("fallback_data" in rr) {
          return new Response(JSON.stringify(rr.fallback_data), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        } else if ("requires_login" in rr && rr.requires_login) {
          throw new Error("Authentication required");
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      }

      return response;
    } catch (error: unknown) {
      lastError = error as Error;

      if (attempt < maxRetries) {
        const errorMessage = lastError instanceof Error
          ? lastError.message
          : lastError
            ? String(lastError)
            : 'Unknown error';

        const rr = await enhancedErrorHandler.handleNetworkError(
          url,
          errorMessage,
          operation,
          { attempt, maxRetries }
        );

        if ("retry" in rr && rr.retry) {
          if (rr.delay > 0) {
            logger.info(`Retrying request after ${rr.delay} seconds due to network error`);
            await new Promise((res) => setTimeout(res, rr.delay * 1000));
          }
          continue;
        } else if ("fallback_data" in rr) {
          return new Response(JSON.stringify(rr.fallback_data), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
      }
    }
  }

  // All retries exhausted
  throw lastError || new Error("Request failed after all retries");
}

// ---------- Integrations ----------
export function integrateWithExistingErrorHandling(): void {
  if (!isBrowser()) return;

  // Idempotent guard
  const __key = "__RECOVERY_FETCH_WRAP__";
  const win = window as unknown as RecoveryWindow & Record<string, unknown>;
  if (win[__key]) return;

  const originalFetch = window.fetch.bind(window);

  window.fetch = async (...args: FetchArgs) => {
    const [input, init] = args;
    const url = typeof input === "string"
      ? input
      : input instanceof URL
        ? input.toString()
        : (input as Request).url;

    try {
      // Use enhanced pipeline for all API calls
      if (url.includes("/api/")) {
        return await fetchWithRecovery(url, init, "api_call");
      }
      // Non-API → pass through
      return await originalFetch(input, init);
    } catch (error) {
      logger.error("Enhanced fetch failed:", error);
      throw error;
    }
  };

  flagStore[__key] = true;
  logger.info("Integrated enhanced fetch with recovery pipeline");
}

export function integrateWithKarenBackend(): void {
  if (!isBrowser()) return;

  const win = window as unknown as RecoveryWindow & Record<string, unknown>;
  win.handleKarenBackendError = async (
    status: number,
    url: string,
    operation: string = "api_call",
    context: Record<string, unknown> = {}
  ) => {
    return await enhancedErrorHandler.handleHttpError(status, url, operation, context);
  };

  logger.info("KarenBackend error integration enabled");
}

// ---------- Auto-init ----------
if (isBrowser()) {
  // Always enable KarenBackend bridge for extension errors
  integrateWithKarenBackend();

  // Probe recovery status, then opt-in to global fetch wrapping if available
  enhancedErrorHandler
    .getRecoveryStatus()
    .then((status) => {
      if (status.available !== false) {
        logger.info("Error recovery system available; integrating with fetch");
        integrateWithExistingErrorHandling();
      } else {
        logger.warn("Error recovery system not available; using fallback handling");
      }
    })
    .catch((error) => {
      logger.warn("Could not check error recovery system status:", error);
    });
}
