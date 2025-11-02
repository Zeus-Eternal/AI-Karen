/**
 * Extension Error Recovery Integration Example
 *
 * Shows how to integrate the comprehensive error recovery manager
 * with the existing frontend error handling system.
 */

import { logger } from "./logger";
import { errorHandler } from "./error-handler";
import { getExtensionAuthErrorHandler } from "./auth/extension-auth-error-handler";
import { handleExtensionError, shouldUseExtensionFallback } from "./extension-error-integration";
import "./extension-403-fix"; // Import the 403 fix to ensure it's loaded

// Types for the error recovery system
interface RecoveryResult {
  success: boolean;
  strategy: string;
  message: string;
  fallback_data?: any;
  retry_after?: number;
  requires_user_action: boolean;
  escalated: boolean;
}

interface ErrorRecoveryRequest {
  type: "http" | "network" | "service" | "auth";
  status_code?: number;
  endpoint: string;
  operation: string;
  message: string;
  context?: Record<string, any>;
  service_name?: string;
}

/**
 * Enhanced error handler that integrates with the backend error recovery system
 */
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
    context: Record<string, any> = {}
  ): Promise<any> {
    try {
      logger.info(`Attempting error recovery for HTTP ${status} at ${url}`);

      // Special handling for extension API errors
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
          user_agent: navigator.userAgent,
        },
      };

      const response = await fetch(`${this.recoveryEndpoint}/handle-error`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ error_data: recoveryRequest }),

      if (!response.ok) {
        logger.warn(`Error recovery service unavailable: ${response.status}`);
        return this.handleFallback(status, url, operation);
      }

      const result = await response.json();
      const recoveryResult: RecoveryResult = result.recovery_result;

      logger.info(
        `Error recovery result: ${
          recoveryResult.success ? "SUCCESS" : "FAILED"
        } - ${recoveryResult.message}`
      );

      if (recoveryResult.success) {
        if (recoveryResult.fallback_data) {
          // Use fallback data
          logger.info("Using fallback data from error recovery");
          return recoveryResult.fallback_data;
        } else {
          // Recovery successful, can retry original request
          logger.info("Error recovery successful, can retry original request");
          return { retry: true, delay: recoveryResult.retry_after || 0 };
        }
      } else {
        if (recoveryResult.requires_user_action) {
          // Show user-friendly error message
          errorHandler.showWarning("Action Required", recoveryResult.message);
        } else if (recoveryResult.fallback_data) {
          // Use fallback data even if recovery "failed"
          logger.info("Using fallback data despite recovery failure");
          return recoveryResult.fallback_data;
        } else if (recoveryResult.retry_after) {
          // Retry after delay
          logger.info(`Will retry after ${recoveryResult.retry_after} seconds`);
          return { retry: true, delay: recoveryResult.retry_after };
        }

        // No recovery possible
        return this.handleFallback(status, url, operation);
      }
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
    context: Record<string, any> = {}
  ): Promise<any> {
    // Use the dedicated extension error handler
    const extensionErrorResult = handleExtensionError(status, url, operation);

    logger.info(`Extension API error handled: ${extensionErrorResult.message}`);

    // Return the result in the expected format
    if (extensionErrorResult.fallback_data) {
      return { fallback_data: extensionErrorResult.fallback_data };
    }

    if (extensionErrorResult.retry) {
      return {
        retry: true,
        delay: extensionErrorResult.delay || 0,
      };
    }

    if (extensionErrorResult.requires_login) {
      return { requires_login: true };
    }

    // Use the standard fallback for other cases
    return this.handleFallback(status, url, operation);
  }

  /**
   * Handle authentication errors specifically
   */
  async handleAuthError(
    endpoint: string,
    operation: string = "authentication",
    context: Record<string, any> = {}
  ): Promise<any> {
    try {
      logger.info(`Attempting auth error recovery for ${endpoint}`);

      const response = await fetch(
        `${this.recoveryEndpoint}/handle-auth-error`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
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
        }
      );

      if (!response.ok) {
        logger.warn(
          `Auth error recovery service unavailable: ${response.status}`
        );
        return { requires_login: true };
      }

      const result = await response.json();
      const recoveryResult: RecoveryResult = result.recovery_result;

      if (recoveryResult.success) {
        logger.info("Auth error recovery successful");
        return { retry: true, delay: recoveryResult.retry_after || 0 };
      } else if (recoveryResult.requires_user_action) {
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
    context: Record<string, any> = {}
  ): Promise<any> {
    try {
      logger.info(`Attempting network error recovery for ${endpoint}`);

      const response = await fetch(
        `${this.recoveryEndpoint}/handle-network-error`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            error_data: {
              endpoint,
              operation,
              message: errorMessage,
              context: {
                ...context,
                timestamp: new Date().toISOString(),
                connection_type:
                  (navigator as any).connection?.effectiveType || "unknown",
              },
            },
          }),
        }
      );

      if (!response.ok) {
        logger.warn(
          `Network error recovery service unavailable: ${response.status}`
        );
        return { retry: true, delay: 5 }; // Simple fallback retry
      }

      const result = await response.json();
      const recoveryResult: RecoveryResult = result.recovery_result;

      if (recoveryResult.retry_after) {
        logger.info(
          `Network error recovery suggests retry after ${recoveryResult.retry_after} seconds`
        );
        return { retry: true, delay: recoveryResult.retry_after };
      } else if (recoveryResult.fallback_data) {
        logger.info("Using fallback data for network error");
        return recoveryResult.fallback_data;
      }

      return { retry: false };
    } catch (error) {
      logger.error("Network error recovery failed:", error);
      return { retry: true, delay: 5 }; // Simple fallback retry
    }
  }

  /**
   * Get error recovery system status
   */
  async getRecoveryStatus(): Promise<any> {
    try {
      const response = await fetch(`${this.recoveryEndpoint}/status`);
      if (!response.ok) {
        return {
          available: false,
          message: "Error recovery service unavailable",
        };
      }
      return await response.json();
    } catch (error) {
      logger.error("Failed to get recovery status:", error);
      return {
        available: false,
        message: "Error recovery service unavailable",
      };
    }
  }

  /**
   * Fallback error handling when recovery system is unavailable
   */
  private handleFallback(status: number, url: string, operation: string): any {
    logger.warn(`Using fallback error handling for ${status} at ${url}`);

    // Simple fallback logic based on status code
    if (status === 401 || status === 403) {
      return { requires_login: true };
    } else if (status >= 500) {
      return { retry: true, delay: 10 }; // Retry server errors after 10 seconds
    } else if (status === 429) {
      return { retry: true, delay: 60 }; // Retry rate limited requests after 1 minute
    } else {
      // For other 4xx errors, show generic error
      errorHandler.showWarning(
        "Request Failed",
        `The request failed with status ${status}. Please try again.`
      );
      return { retry: false };
    }
  }
}

// Export singleton instance
export const enhancedErrorHandler = EnhancedErrorHandler.getInstance();

/**
 * Enhanced fetch wrapper that automatically handles errors with recovery
 */
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
        // Handle HTTP errors through recovery system
        const recoveryResult = await enhancedErrorHandler.handleHttpError(
          response.status,
          url,
          operation,
          { attempt, maxRetries }
        );

        if (recoveryResult.retry && attempt < maxRetries) {
          if (recoveryResult.delay > 0) {
            logger.info(
              `Retrying request after ${recoveryResult.delay} seconds`
            );
            await new Promise((resolve) =>
              setTimeout(resolve, recoveryResult.delay * 1000)
            );
          }
          continue; // Retry the request
        } else if (recoveryResult.fallback_data) {
          // Return a mock response with fallback data
          return new Response(JSON.stringify(recoveryResult.fallback_data), {
            status: 200,
            headers: { "Content-Type": "application/json" },

        } else if (recoveryResult.requires_login) {
          throw new Error("Authentication required");
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      }

      return response;
    } catch (error) {
      lastError = error as Error;

      if (attempt < maxRetries) {
        // Handle network errors through recovery system
        const recoveryResult = await enhancedErrorHandler.handleNetworkError(
          url,
          lastError.message,
          operation,
          { attempt, maxRetries }
        );

        if (recoveryResult.retry) {
          if (recoveryResult.delay > 0) {
            logger.info(
              `Retrying request after ${recoveryResult.delay} seconds due to network error`
            );
            await new Promise((resolve) =>
              setTimeout(resolve, recoveryResult.delay * 1000)
            );
          }
          continue; // Retry the request
        } else if (recoveryResult.fallback_data) {
          // Return a mock response with fallback data
          return new Response(JSON.stringify(recoveryResult.fallback_data), {
            status: 200,
            headers: { "Content-Type": "application/json" },

        }
      }
    }
  }

  // All retries exhausted
  throw lastError || new Error("Request failed after all retries");
}

/**
 * Example usage in existing code
 */
export function integrateWithExistingErrorHandling() {
  // Example of how to integrate with existing KarenBackendService
  const originalFetch = window.fetch;

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    try {
      const url = typeof input === "string" ? input : input.toString();

      // Use enhanced fetch for API calls
      if (url.includes("/api/")) {
        return await fetchWithRecovery(url, init, "api_call");
      }

      // Use original fetch for other requests
      return await originalFetch(input, init);
    } catch (error) {
      logger.error("Enhanced fetch failed:", error);
      throw error;
    }
  };
}

/**
 * Integrate with KarenBackend service specifically for extension errors
 */
export function integrateWithKarenBackend() {
  // This would be called by the KarenBackend service when it encounters errors
  const errorHandler = enhancedErrorHandler;

  // Export a function that KarenBackend can use
  (window as any).handleKarenBackendError = async (
    status: number,
    url: string,
    operation: string = "api_call",
    context: Record<string, any> = {}
  ) => {
    return await errorHandler.handleHttpError(status, url, operation, context);
  };

  logger.info("KarenBackend error integration enabled");
}

// Auto-initialize integration
if (typeof window !== "undefined") {
  // Always integrate with KarenBackend for extension error handling
  integrateWithKarenBackend();

  // Check if error recovery system is available
  enhancedErrorHandler
    .getRecoveryStatus()
    .then((status) => {
      if (status.available !== false) {
        logger.info(
          "Error recovery system is available, integrating with existing error handling"
        );
        // Enable automatic integration for extension errors
        integrateWithExistingErrorHandling();
      } else {
        logger.warn(
          "Error recovery system is not available, using fallback error handling"
        );
      }
    })
    .catch((error) => {
      logger.warn("Could not check error recovery system status:", error);

}
