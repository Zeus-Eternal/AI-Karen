/**
 * Safe console utilities to prevent Next.js console interceptor issues
 */

export interface SafeConsoleOptions {
  skipInProduction?: boolean;
  useStructuredLogging?: boolean;
}

class SafeConsole {
  private static instance: SafeConsole;
  private originalConsole: Console;

  constructor() {
    this.originalConsole = { ...console };
  }

  static getInstance(): SafeConsole {
    if (!SafeConsole.instance) {
      SafeConsole.instance = new SafeConsole();
    }
    return SafeConsole.instance;
  }

  /**
   * Safe error logging that prevents console interceptor issues
   */
  safeError(
    message: string,
    error?: unknown,
    options: SafeConsoleOptions = {}
  ) {
    const { skipInProduction = false, useStructuredLogging = true } = options;

    // Skip in production if requested
    if (skipInProduction && process.env.NODE_ENV === "production") {
      return;
    }

    try {
      if (useStructuredLogging && error) {
        // Use structured logging to avoid interceptor issues
        // Type guard for error object
        const errorObj = error as Error | { name?: string; message?: string; stack?: string } | null;
        
        const errorName = errorObj?.name || "Unknown";
        const errorMessage = errorObj?.message || "No message";
        const errorStack = errorObj?.stack;
        
        const errorData = {
          message,
          error: {
            name: errorName,
            message: errorMessage,
            stack: errorStack,
          },
          timestamp: new Date().toISOString(),
          environment: process.env.NODE_ENV,
        };

        // Use original console methods to bypass interceptors
        this.originalConsole.error(
          "🚨 Safe Console Error:",
          JSON.stringify(errorData, null, 2)
        );
      } else {
        this.originalConsole.error(message, error);
      }
    } catch (consoleError) {
      // Fallback if even safe logging fails
      try {
        this.originalConsole.warn("Console error occurred:", message);
      } catch {
        // Last resort - do nothing to prevent infinite loops
      }
    }
  }

  /**
   * Safe warning logging
   */
  safeWarn(message: string, data?: unknown) {
    try {
      this.originalConsole.warn(message, data);
    } catch {
      // Silently fail to prevent issues
    }
  }

  /**
   * Safe info logging
   */
  safeInfo(message: string, data?: unknown) {
    try {
      this.originalConsole.info(message, data);
    } catch {
      // Silently fail to prevent issues
    }
  }

  /**
   * Safe debug logging (only in development)
   */
  safeDebug(message: string, data?: unknown) {
    if (process.env.NODE_ENV === "development") {
      try {
        this.originalConsole.debug(message, data);
      } catch {
        // Silently fail to prevent issues
      }
    }
  }
}

// Export singleton instance
export const safeConsole = SafeConsole.getInstance();

// Export convenience functions
export const safeError = (
  message: string,
  error?: unknown,
  options?: SafeConsoleOptions
) => safeConsole.safeError(message, error, options);

export const safeWarn = (message: string, data?: unknown) =>
  safeConsole.safeWarn(message, data);

export const safeInfo = (message: string, data?: unknown) =>
  safeConsole.safeInfo(message, data);

export const safeDebug = (message: string, data?: unknown) =>
  safeConsole.safeDebug(message, data);

// Alias for safeInfo for convenience
export const safeLog = (message: string, data?: unknown) =>
  safeConsole.safeInfo(message, data);
