/**
 * Hot Reload Authentication Support
 *
 * Provides seamless authentication during hot reload scenarios to prevent
 * authentication issues during development.
 *
 * Requirements addressed:
 * - 6.2: Hot reload support without authentication issues
 * - 6.4: Detailed logging for debugging extension issues
 */

import { logger } from "@/lib/logger";
import {
  getDevelopmentAuthManager,
  isDevelopmentFeaturesEnabled,
} from "./development-auth";

// Hot reload state interface
export interface HotReloadAuthState {
  tokens: Record<string, string>;
  currentUser: string;
  timestamp: number;
  sessionId: string;
}

// Hot reload event interface
export interface HotReloadEvent {
  type: "webpack" | "vite" | "manual";
  timestamp: number;
  source: string;
}

/**
 * Hot Reload Authentication Manager
 *
 * Manages authentication state preservation and restoration during hot reload
 * scenarios to ensure seamless development experience.
 */
export class HotReloadAuthManager {
  private static readonly STORAGE_KEY = "kari_hot_reload_auth_state";
  private static readonly SESSION_ID_KEY = "kari_hot_reload_session_id";
  private static readonly MAX_STATE_AGE_MS = 5 * 60 * 1000; // 5 minutes

  private sessionId: string;
  private _isHotReloadActive: boolean = false;
  private hotReloadListeners: Set<(event: HotReloadEvent) => void> = new Set();
  private preservedState: HotReloadAuthState | null = null;

  constructor() {
    this.sessionId = this.getOrCreateSessionId();

    const devFeaturesEnabled = isDevelopmentFeaturesEnabled();

    if (devFeaturesEnabled) {
      this.setupHotReloadDetection();
      this.restoreStateIfNeeded();
    }

    logger.debug("Hot reload auth manager initialized", {
      sessionId: this.sessionId,
      hasPreservedState: !!this.preservedState,
      devFeaturesEnabled,
    });
  }

  /**
   * Get or create session ID for hot reload tracking
   */
  private getOrCreateSessionId(): string {
    if (typeof window === "undefined") return "server-session";

    try {
      let sessionId = sessionStorage.getItem(
        HotReloadAuthManager.SESSION_ID_KEY
      );
      if (!sessionId) {
        sessionId = `hr_${Date.now()}_${Math.random()
          .toString(36)
          .substring(2, 15)}`;
        sessionStorage.setItem(HotReloadAuthManager.SESSION_ID_KEY, sessionId);
      }
      return sessionId;
    } catch (error) {
      logger.warn("Failed to manage session ID:", error);
      return `hr_fallback_${Date.now()}`;
    }
  }

  /**
   * Setup hot reload detection for various development servers
   */
  private setupHotReloadDetection(): void {
    if (typeof window === "undefined" || !isDevelopmentFeaturesEnabled())
      return;

    // Webpack Hot Module Replacement
    if (
      (
        window as unknown as {
          module?: {
            hot?: {
              accept: (callback: () => void) => void;
              dispose: (callback: () => void) => void;
            };
          };
        }
      ).module?.hot
    ) {
      const hotModule = (
        window as unknown as {
          module: {
            hot: {
              accept: (callback: () => void) => void;
              dispose: (callback: () => void) => void;
            };
          };
        }
      ).module.hot;
      hotModule.accept(() => {
        this.handleHotReload({
          type: "webpack",
          timestamp: Date.now(),
          source: "webpack-hmr",
        });
      });

      hotModule.dispose(() => {
        this.preserveAuthState();
      });
    }

    // Vite Hot Module Replacement
    if (
      (
        window as unknown as {
          __vite_plugin_react_preamble_installed__?: boolean;
        }
      ).__vite_plugin_react_preamble_installed__
    ) {
      window.addEventListener("vite:beforeUpdate", () => {
        this.handleHotReload({
          type: "vite",
          timestamp: Date.now(),
          source: "vite-hmr",
        });
      });

      window.addEventListener("vite:afterUpdate", () => {
        this.restoreStateIfNeeded();
      });
    }

    // Generic beforeunload for any hot reload scenario
    window.addEventListener("beforeunload", () => {
      if (this.isHotReloadScenario()) {
        this.preserveAuthState();
      }
    });

    // Page load restoration
    window.addEventListener("load", () => {
      this.restoreStateIfNeeded();
    });

    // Manual hot reload detection via URL parameters
    if (window.location.search.includes("hot_reload=true")) {
      this.handleHotReload({
        type: "manual",
        timestamp: Date.now(),
        source: "url-parameter",
      });
    }

    logger.debug("Hot reload detection configured");
  }
  /**
   * Check if current scenario is a hot reload
   */
  private isHotReloadScenario(): boolean {
    if (typeof window === "undefined" || !isDevelopmentFeaturesEnabled())
      return false;

    const indicators = [
      // Webpack dev server
      (window as unknown as { __webpack_dev_server__?: unknown })
        .__webpack_dev_server__ !== undefined,
      // Vite HMR
      (
        window as unknown as {
          __vite_plugin_react_preamble_installed__?: boolean;
        }
      ).__vite_plugin_react_preamble_installed__ !== undefined,
      // Development server ports
      ["3000", "3001", "8000", "8001", "8010", "8020", "5173", "5174"].includes(
        window.location.port
      ),
      // Development hostnames
      ["localhost", "127.0.0.1"].includes(window.location.hostname),
      // Hot reload URL parameter
      window.location.search.includes("hot_reload=true"),
      // Development environment
      process.env.NODE_ENV === "development",
    ];

    return indicators.some(Boolean);
  }

  /**
   * Handle hot reload event
   */
  private handleHotReload(event: HotReloadEvent): void {
    if (!isDevelopmentFeaturesEnabled()) {
      return;
    }

    this._isHotReloadActive = true;

    logger.debug("Hot reload detected", event);

    // Preserve current authentication state
    this.preserveAuthState();

    // Notify listeners
    this.hotReloadListeners.forEach((listener) => {
      try {
        listener(event);
      } catch (error) {
        logger.warn("Hot reload listener error:", error);
      }
    });

    // Set flag to restore state after reload
    try {
      sessionStorage.setItem("kari_hot_reload_pending", "true");
    } catch (error) {
      logger.warn("Failed to set hot reload pending flag:", error);
    }
  }

  /**
   * Preserve authentication state for hot reload
   */
  private preserveAuthState(): void {
    if (typeof window === "undefined" || !isDevelopmentFeaturesEnabled())
      return;

    try {
      getDevelopmentAuthManager();

      // Collect current authentication state
      const authState: HotReloadAuthState = {
        tokens: this.collectCurrentTokens(),
        currentUser: this.getCurrentUser(),
        timestamp: Date.now(),
        sessionId: this.sessionId,
      };

      // Store in session storage for persistence across hot reloads
      sessionStorage.setItem(
        HotReloadAuthManager.STORAGE_KEY,
        JSON.stringify(authState)
      );

      this.preservedState = authState;

      logger.debug("Authentication state preserved for hot reload", {
        tokenCount: Object.keys(authState.tokens).length,
        currentUser: authState.currentUser,
        sessionId: authState.sessionId,
      });
    } catch (error) {
      logger.error("Failed to preserve auth state for hot reload:", error);
    }
  }

  /**
   * Collect current authentication tokens
   */
  private collectCurrentTokens(): Record<string, string> {
    const tokens: Record<string, string> = {};

    if (!isDevelopmentFeaturesEnabled()) {
      return tokens;
    }

    try {
      // Extension auth tokens
      const extensionToken = localStorage.getItem(
        "karen_extension_access_token"
      );
      if (extensionToken) {
        tokens.extension_access = extensionToken;
      }

      const extensionRefreshToken = localStorage.getItem(
        "karen_extension_refresh_token"
      );
      if (extensionRefreshToken) {
        tokens.extension_refresh = extensionRefreshToken;
      }

      // Main auth tokens
      const mainToken = localStorage.getItem("karen_access_token");
      if (mainToken) {
        tokens.main_access = mainToken;
      }

      const sessionToken = sessionStorage.getItem("kari_session_token");
      if (sessionToken) {
        tokens.session = sessionToken;
      }

      // Development tokens from development auth manager
      const devAuthManager = getDevelopmentAuthManager();
      if (devAuthManager.isEnabled()) {
        const devStatus = devAuthManager.getDevelopmentStatus();
        if (devStatus.cachedTokens > 0) {
          tokens.development = "dev-tokens-preserved";
        }
      }
    } catch (error) {
      logger.warn("Error collecting tokens:", error);
    }

    return tokens;
  }

  /**
   * Get current user identifier
   */
  private getCurrentUser(): string {
    if (!isDevelopmentFeaturesEnabled()) {
      return "unknown-user";
    }

    try {
      // Try to get user from various sources
      const sources = [
        () => localStorage.getItem("current_user_id"),
        () => sessionStorage.getItem("current_user_id"),
        () => {
          const token = localStorage.getItem("karen_access_token");
          if (token) {
            const payload = JSON.parse(atob(token.split(".")[1]));
            return payload.user_id;
          }
          return null;
        },
        () => "dev-user", // Fallback for development
      ];

      for (const source of sources) {
        const userId = source();
        if (userId && userId !== "null" && userId !== "undefined") {
          return userId;
        }
      }

      return "unknown-user";
    } catch (error) {
      logger.warn("Error getting current user:", error);
      return "unknown-user";
    }
  }

  /**
   * Restore authentication state after hot reload
   */
  private restoreStateIfNeeded(): void {
    if (typeof window === "undefined" || !isDevelopmentFeaturesEnabled())
      return;

    try {
      // Check if hot reload restoration is pending
      const isPending =
        sessionStorage.getItem("kari_hot_reload_pending") === "true";
      if (!isPending) return;

      // Get preserved state
      const stateJson = sessionStorage.getItem(
        HotReloadAuthManager.STORAGE_KEY
      );
      if (!stateJson) {
        logger.debug("No preserved auth state found for hot reload");
        return;
      }

      const state: HotReloadAuthState = JSON.parse(stateJson);

      // Check if state is recent enough
      const stateAge = Date.now() - state.timestamp;
      if (stateAge > HotReloadAuthManager.MAX_STATE_AGE_MS) {
        logger.debug("Preserved auth state too old, discarding", {
          ageMs: stateAge,
        });
        this.cleanupHotReloadState();
        return;
      }

      // Check session ID match
      if (state.sessionId !== this.sessionId) {
        logger.debug("Session ID mismatch, not restoring state", {
          preserved: state.sessionId,
          current: this.sessionId,
        });
        return;
      }

      // Restore tokens
      this.restoreTokens(state.tokens);

      // Update preserved state
      this.preservedState = state;

      logger.debug("Authentication state restored after hot reload", {
        tokenCount: Object.keys(state.tokens).length,
        currentUser: state.currentUser,
        stateAge: stateAge,
      });

      // Clean up
      this.cleanupHotReloadState();
    } catch (error) {
      logger.error("Failed to restore auth state after hot reload:", error);
      this.cleanupHotReloadState();
    }
  }

  /**
   * Restore authentication tokens
   */
  private restoreTokens(tokens: Record<string, string>): void {
    try {
      // Restore extension tokens
      if (tokens.extension_access) {
        localStorage.setItem(
          "karen_extension_access_token",
          tokens.extension_access
        );
      }

      if (tokens.extension_refresh) {
        localStorage.setItem(
          "karen_extension_refresh_token",
          tokens.extension_refresh
        );
      }

      // Restore main auth tokens
      if (tokens.main_access) {
        localStorage.setItem("karen_access_token", tokens.main_access);
      }

      if (tokens.session) {
        sessionStorage.setItem("kari_session_token", tokens.session);
      }

      // Restore development tokens if applicable
      if (tokens.development) {
        const devAuthManager = getDevelopmentAuthManager();
        if (devAuthManager.isEnabled()) {
          // Development tokens are handled by the development auth manager
          logger.debug(
            "Development tokens restoration handled by dev auth manager"
          );
        }
      }

      logger.debug("Tokens restored successfully", {
        restoredCount: Object.keys(tokens).length,
      });
    } catch (error) {
      logger.error("Failed to restore tokens:", error);
    }
  }

  /**
   * Clean up hot reload state
   */
  private cleanupHotReloadState(): void {
    try {
      sessionStorage.removeItem(HotReloadAuthManager.STORAGE_KEY);
      sessionStorage.removeItem("kari_hot_reload_pending");
      this.preservedState = null;
      this._isHotReloadActive = false;
    } catch (error) {
      logger.warn("Failed to cleanup hot reload state:", error);
    }
  }

  /**
   * Add hot reload event listener
   */
  addHotReloadListener(listener: (event: HotReloadEvent) => void): () => void {
    this.hotReloadListeners.add(listener);

    return () => {
      this.hotReloadListeners.delete(listener);
    };
  }

  /**
   * Check if hot reload is currently active
   */
  isHotReloadActive(): boolean {
    return this._isHotReloadActive;
  }

  /**
   * Get preserved authentication state
   */
  getPreservedState(): HotReloadAuthState | null {
    return this.preservedState;
  }

  /**
   * Force preservation of current auth state
   */
  forcePreserveState(): void {
    this.preserveAuthState();
  }

  /**
   * Force restoration of preserved state
   */
  forceRestoreState(): void {
    this.restoreStateIfNeeded();
  }

  /**
   * Get hot reload status information
   */
  getStatus(): {
    sessionId: string;
    isActive: boolean;
    hasPreservedState: boolean;
    isHotReloadScenario: boolean;
    listenerCount: number;
  } {
    return {
      sessionId: this.sessionId,
      isActive: this._isHotReloadActive,
      hasPreservedState: !!this.preservedState,
      isHotReloadScenario: this.isHotReloadScenario(),
      listenerCount: this.hotReloadListeners.size,
    };
  }
}

// Global hot reload auth manager instance
let hotReloadAuthManager: HotReloadAuthManager | null = null;

/**
 * Get the global hot reload authentication manager
 */
export function getHotReloadAuthManager(): HotReloadAuthManager {
  if (!hotReloadAuthManager) {
    hotReloadAuthManager = new HotReloadAuthManager();
  }
  return hotReloadAuthManager;
}

/**
 * Initialize hot reload authentication manager
 */
export function initializeHotReloadAuthManager(): HotReloadAuthManager {
  hotReloadAuthManager = new HotReloadAuthManager();
  return hotReloadAuthManager;
}

/**
 * Reset hot reload authentication manager (useful for testing)
 */
export function resetHotReloadAuthManager(): void {
  hotReloadAuthManager = null;
}
