/**
 * Development Mode Authentication Support
 *
 * Provides development-specific authentication features including mock authentication,
 * hot reload support, and automatic environment detection.
 *
 * Requirements addressed:
 * - 6.1: Development mode authentication with local credentials
 * - 6.2: Hot reload support without authentication issues
 * - 6.3: Mock authentication for testing
 * - 6.4: Detailed logging for debugging
 * - 6.5: Environment-specific configuration adaptation
 */

import { logger } from "@/lib/logger";

const getEnvVar = (key: string): string | undefined => {
  if (typeof process !== "undefined" && process.env && key in process.env) {
    return process.env[key];
  }
  return undefined;
};

const NODE_ENV = getEnvVar("NODE_ENV") ?? "production";
const DEV_FEATURE_FLAG = (
  getEnvVar("NEXT_PUBLIC_ENABLE_DEVELOPMENT_FEATURES") || ""
).toLowerCase();
const GLOBAL_DEVELOPMENT_FEATURES_ENABLED =
  DEV_FEATURE_FLAG === "true" && NODE_ENV !== "production";

export const isDevelopmentFeaturesEnabled = (): boolean =>
  GLOBAL_DEVELOPMENT_FEATURES_ENABLED;

// Development user interface
export interface DevelopmentUser {
  user_id: string;
  tenant_id: string;
  roles: string[];
  permissions: string[];
  email: string;
  name: string;
}

// Development authentication configuration
export interface DevelopmentAuthConfig {
  enabled: boolean;
  bypassAuth: boolean;
  mockAuthEnabled: boolean;
  hotReloadSupport: boolean;
  debugLogging: boolean;
  autoTokenRefresh: boolean;
  tokenExpiryHours: number;
  defaultUser: string;
}

// Mock authentication response
export interface MockAuthResponse {
  access_token: string;
  refresh_token?: string;
  expires_in: number;
  token_type: string;
  user: DevelopmentUser;
}

// Hot reload detection interface
export interface HotReloadInfo {
  isHotReload: boolean;
  reloadSource: string;
  timestamp: number;
}

/**
 * Development Authentication Manager
 *
 * Handles development-specific authentication scenarios including mock users,
 * hot reload support, and automatic environment detection.
 */
export class DevelopmentAuthManager {
  private config: DevelopmentAuthConfig;
  private mockUsers: Map<string, DevelopmentUser>;
  private developmentTokens: Map<string, string>;
  private hotReloadListeners: Set<() => void>;

  constructor(config?: Partial<DevelopmentAuthConfig>) {
    const overrides = config ?? {};
    const featuresEnabled = isDevelopmentFeaturesEnabled();
    const environmentEnabled =
      featuresEnabled && this.isDevelopmentEnvironment();

    this.config = {
      enabled: environmentEnabled,
      bypassAuth: environmentEnabled && (overrides.bypassAuth ?? true),
      mockAuthEnabled:
        environmentEnabled && (overrides.mockAuthEnabled ?? true),
      hotReloadSupport:
        environmentEnabled && (overrides.hotReloadSupport ?? true),
      debugLogging: environmentEnabled && (overrides.debugLogging ?? true),
      autoTokenRefresh:
        environmentEnabled && (overrides.autoTokenRefresh ?? true),
      tokenExpiryHours: overrides.tokenExpiryHours ?? 24,
      defaultUser: overrides.defaultUser ?? "dev-user",
    };

    this.mockUsers = new Map();
    this.developmentTokens = new Map();
    this.hotReloadListeners = new Set();

    this.initializeMockUsers();
    this.setupHotReloadSupport();

    if (this.config.debugLogging) {
      logger.debug("Development authentication manager initialized", {
        config: this.config,
        mockUsers: Array.from(this.mockUsers.keys()),
      });
    } else if (!featuresEnabled) {
      logger.info(
        "Development authentication disabled for production environment"
      );
    }
  }

  /**
   * Check if running in development environment
   */
  private isDevelopmentEnvironment(): boolean {
    if (typeof window === "undefined") return false;

    const indicators = [
      process.env.NODE_ENV === "development",
      window.location.hostname === "localhost",
      window.location.hostname === "127.0.0.1",
      window.location.hostname.endsWith(".local"),
      window.location.port !== "" && parseInt(window.location.port) >= 3000,
      window.location.search.includes("dev=true"),
      window.location.search.includes("development=true"),
      // Check for development build indicators
      document.querySelector('script[src*="webpack"]') !== null,
      document.querySelector('script[src*="vite"]') !== null,
      // Check for hot reload indicators
      (window as any).__webpack_dev_server__ !== undefined,
      (window as any).__vite_plugin_react_preamble_installed__ !== undefined,
    ];

    return indicators.some(Boolean);
  }

  /**
   * Initialize mock users for development testing
   */
  private initializeMockUsers(): void {
    if (!this.config.enabled) {
      logger.debug("Development auth disabled - mock users not registered");
      return;
    }

    const mockUsers: DevelopmentUser[] = [
      {
        user_id: "dev-user",
        tenant_id: "dev-tenant",
        roles: ["admin", "user", "developer"],
        permissions: [
          "extension:*",
          "extension:read",
          "extension:write",
          "extension:admin",
          "extension:background_tasks",
          "extension:configure",
          "extension:install",
          "extension:health",
          "extension:metrics",
        ],
        email: "dev@localhost",
        name: "Development User",
      },
      {
        user_id: "test-user",
        tenant_id: "test-tenant",
        roles: ["user"],
        permissions: ["extension:read", "extension:write"],
        email: "test@localhost",
        name: "Test User",
      },
      {
        user_id: "admin-user",
        tenant_id: "admin-tenant",
        roles: ["admin", "super_admin"],
        permissions: ["extension:*"],
        email: "admin@localhost",
        name: "Admin User",
      },
      {
        user_id: "readonly-user",
        tenant_id: "readonly-tenant",
        roles: ["user"],
        permissions: ["extension:read"],
        email: "readonly@localhost",
        name: "Read-Only User",
      },
      {
        user_id: "hot-reload-user",
        tenant_id: "hot-reload-tenant",
        roles: ["developer", "admin"],
        permissions: ["extension:*", "hot_reload:*"],
        email: "hotreload@localhost",
        name: "Hot Reload User",
      },
    ];

    mockUsers.forEach((user) => {
      this.mockUsers.set(user.user_id, user);
    });

    if (this.config.debugLogging) {
      logger.debug("Mock users initialized", {
        userCount: this.mockUsers.size,
        users: Array.from(this.mockUsers.keys()),
      });
    }
  }

  /**
   * Setup hot reload support
   */
  private setupHotReloadSupport(): void {
    if (
      !this.config.enabled ||
      !this.config.hotReloadSupport ||
      typeof window === "undefined"
    ) {
      return;
    }

    // Listen for hot reload events
    if ((window as any).module?.hot) {
      (window as any).module.hot.accept(() => {
        this.handleHotReload("webpack-hmr");
      });
    }

    // Listen for Vite HMR events
    if ((window as any).__vite_plugin_react_preamble_installed__) {
      window.addEventListener("vite:beforeUpdate", () => {
        this.handleHotReload("vite-hmr");
      });
    }

    // Listen for manual reload events
    window.addEventListener("beforeunload", () => {
      this.preserveAuthStateForReload();
    });

    // Restore auth state after reload
    window.addEventListener("load", () => {
      this.restoreAuthStateAfterReload();
    });

    if (this.config.debugLogging) {
      logger.debug("Hot reload support configured");
    }
  }

  /**
   * Handle hot reload events
   */
  private handleHotReload(source: string): void {
    if (this.config.debugLogging) {
      logger.debug("Hot reload detected", { source, timestamp: Date.now() });
    }

    // Notify listeners
    this.hotReloadListeners.forEach((listener) => {
      try {
        listener();
      } catch (error) {
        logger.warn("Hot reload listener error:", error);
      }
    });

    // Preserve authentication state
    this.preserveAuthStateForReload();
  }

  /**
   * Preserve authentication state for hot reload
   */
  private preserveAuthStateForReload(): void {
    try {
      const authState = {
        developmentTokens: Array.from(this.developmentTokens.entries()),
        timestamp: Date.now(),
        config: this.config,
      };

      sessionStorage.setItem(
        "dev_auth_hot_reload_state",
        JSON.stringify(authState)
      );

      if (this.config.debugLogging) {
        logger.debug("Authentication state preserved for hot reload");
      }
    } catch (error) {
      logger.warn("Failed to preserve auth state for hot reload:", error);
    }
  }

  /**
   * Restore authentication state after hot reload
   */
  private restoreAuthStateAfterReload(): void {
    try {
      const savedState = sessionStorage.getItem("dev_auth_hot_reload_state");
      if (!savedState) return;

      const authState = JSON.parse(savedState);

      // Check if state is recent (within 5 minutes)
      if (Date.now() - authState.timestamp > 5 * 60 * 1000) {
        sessionStorage.removeItem("dev_auth_hot_reload_state");
        return;
      }

      // Restore development tokens
      this.developmentTokens = new Map(authState.developmentTokens);

      // Clean up
      sessionStorage.removeItem("dev_auth_hot_reload_state");

      if (this.config.debugLogging) {
        logger.debug("Authentication state restored after hot reload", {
          tokenCount: this.developmentTokens.size,
        });
      }
    } catch (error) {
      logger.warn("Failed to restore auth state after hot reload:", error);
    }
  }

  private assertEnabled(action: string): void {
    if (!this.config.enabled) {
      throw new Error(
        `Development authentication is disabled (attempted to ${action}).`
      );
    }
  }

  /**
   * Get development authentication headers
   */
  async getDevelopmentAuthHeaders(
    userId?: string
  ): Promise<Record<string, string>> {
    this.assertEnabled("get development auth headers");

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
      "X-Client-Type": "extension-integration-dev",
      "X-Development-Mode": "true",
    };

    if (this.config.bypassAuth) {
      headers["X-Skip-Auth"] = "dev";
    }

    if (userId) {
      headers["X-Mock-User-ID"] = userId;

      const user = this.mockUsers.get(userId);
      if (user) {
        headers["X-Mock-Tenant-ID"] = user.tenant_id;
        headers["X-Mock-Roles"] = user.roles.join(",");
        headers["X-Mock-Permissions"] = user.permissions.join(",");
      }
    }

    // Add hot reload detection headers
    const hotReloadInfo = this.detectHotReload();
    if (hotReloadInfo.isHotReload) {
      headers["X-Hot-Reload"] = "true";
      headers["X-Hot-Reload-Source"] = hotReloadInfo.reloadSource;
    }

    // Get or create development token
    const token = await this.getDevelopmentToken(
      userId || this.config.defaultUser
    );
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
  }

  /**
   * Get development token for user
   */
  async getDevelopmentToken(userId: string): Promise<string | null> {
    this.assertEnabled("get development token");

    // Check if we have a cached token
    const cachedToken = this.developmentTokens.get(userId);
    if (cachedToken && this.isTokenValid(cachedToken)) {
      return cachedToken;
    }

    // Create new development token
    try {
      const token = await this.createDevelopmentToken(userId);
      if (token) {
        this.developmentTokens.set(userId, token);
        return token;
      }
    } catch (error) {
      if (this.config.debugLogging) {
        logger.warn("Failed to create development token:", error);
      }
    }

    return null;
  }

  /**
   * Create development token
   */
  private async createDevelopmentToken(userId: string): Promise<string | null> {
    this.assertEnabled("create development token");

    const user = this.mockUsers.get(userId);
    if (!user) {
      logger.warn("Unknown development user:", userId);
      return null;
    }

    try {
      // Create a mock JWT token for development
      const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
      const payload = btoa(
        JSON.stringify({
          user_id: user.user_id,
          tenant_id: user.tenant_id,
          roles: user.roles,
          permissions: user.permissions,
          token_type: "development",
          dev_mode: true,
          exp:
            Math.floor(Date.now() / 1000) + this.config.tokenExpiryHours * 3600,
          iat: Math.floor(Date.now() / 1000),
          iss: "kari-extension-dev-system",
        })
      );
      const signature = btoa("dev-signature"); // Mock signature for development

      const token = `${header}.${payload}.${signature}`;

      if (this.config.debugLogging) {
        logger.debug("Created development token", {
          userId,
          tokenLength: token.length,
        });
      }

      return token;
    } catch (error) {
      logger.error("Failed to create development token:", error);
      return null;
    }
  }

  /**
   * Check if token is valid
   */
  private isTokenValid(token: string): boolean {
    try {
      const parts = token.split(".");
      if (parts.length !== 3) return false;

      const payload = JSON.parse(atob(parts[1]));
      const exp = payload.exp * 1000; // Convert to milliseconds

      return Date.now() < exp;
    } catch (error) {
      return false;
    }
  }

  /**
   * Detect hot reload scenario
   */
  private detectHotReload(): HotReloadInfo {
    if (typeof window === "undefined") {
      return { isHotReload: false, reloadSource: "", timestamp: 0 };
    }

    const indicators = [
      {
        check: (window as any).__webpack_dev_server__ !== undefined,
        source: "webpack-dev-server",
      },
      {
        check:
          (window as any).__vite_plugin_react_preamble_installed__ !==
          undefined,
        source: "vite-hmr",
      },
      {
        check: document.querySelector('script[src*="webpack"]') !== null,
        source: "webpack",
      },
      {
        check: document.querySelector('script[src*="vite"]') !== null,
        source: "vite",
      },
      {
        check: window.location.search.includes("hot=true"),
        source: "manual-hot",
      },
    ];

    for (const indicator of indicators) {
      if (indicator.check) {
        return {
          isHotReload: true,
          reloadSource: indicator.source,
          timestamp: Date.now(),
        };
      }
    }

    return { isHotReload: false, reloadSource: "", timestamp: 0 };
  }

  /**
   * Mock authentication for testing
   */
  async mockAuthenticate(userId: string): Promise<MockAuthResponse | null> {
    this.assertEnabled("perform mock authentication");

    if (!this.config.mockAuthEnabled) {
      throw new Error("Mock authentication is disabled");
    }

    const user = this.mockUsers.get(userId);
    if (!user) {
      throw new Error(`Unknown mock user: ${userId}`);
    }

    const token = await this.createDevelopmentToken(userId);
    if (!token) {
      throw new Error("Failed to create development token");
    }

    const response: MockAuthResponse = {
      access_token: token,
      expires_in: this.config.tokenExpiryHours * 3600,
      token_type: "Bearer",
      user,
    };

    if (this.config.debugLogging) {
      logger.debug("Mock authentication successful", {
        userId,
        user: user.name,
      });
    }

    return response;
  }

  /**
   * Get list of available mock users
   */
  getMockUsers(): DevelopmentUser[] {
    return Array.from(this.mockUsers.values());
  }

  /**
   * Switch to different mock user
   */
  async switchMockUser(userId: string): Promise<MockAuthResponse | null> {
    this.assertEnabled("switch mock user");

    if (!this.mockUsers.has(userId)) {
      throw new Error(`Unknown mock user: ${userId}`);
    }

    // Clear existing token for this user
    this.developmentTokens.delete(userId);

    // Create new authentication
    return this.mockAuthenticate(userId);
  }

  /**
   * Add hot reload listener
   */
  addHotReloadListener(listener: () => void): () => void {
    if (!this.config.enabled) {
      return () => undefined;
    }

    this.hotReloadListeners.add(listener);

    // Return cleanup function
    return () => {
      this.hotReloadListeners.delete(listener);
    };
  }

  /**
   * Clear all development authentication state
   */
  clearDevelopmentAuth(): void {
    this.developmentTokens.clear();

    try {
      sessionStorage.removeItem("dev_auth_hot_reload_state");
    } catch (error) {
      // Ignore storage errors
    }

    if (this.config.debugLogging) {
      logger.debug("Development authentication state cleared");
    }
  }

  /**
   * Get development authentication status
   */
  getDevelopmentStatus(): {
    enabled: boolean;
    environment: string;
    mockUsers: number;
    cachedTokens: number;
    hotReloadSupported: boolean;
    config: DevelopmentAuthConfig;
  } {
    return {
      enabled: this.config.enabled,
      environment: process.env.NODE_ENV || "unknown",
      mockUsers: this.mockUsers.size,
      cachedTokens: this.developmentTokens.size,
      hotReloadSupported: this.config.hotReloadSupport,
      config: { ...this.config },
    };
  }

  /**
   * Update development configuration
   */
  updateConfig(updates: Partial<DevelopmentAuthConfig>): void {
    if (!isDevelopmentFeaturesEnabled()) {
      logger.warn(
        "Attempted to update development auth configuration while features are disabled"
      );
      return;
    }

    this.config = { ...this.config, ...updates };

    if (this.config.debugLogging) {
      logger.debug("Development auth configuration updated", { updates });
    }
  }

  /**
   * Check if development mode is enabled
   */
  isEnabled(): boolean {
    return this.config.enabled;
  }
}

// Global development auth manager instance
let developmentAuthManager: DevelopmentAuthManager | null = null;

/**
 * Get the global development authentication manager
 */
export function getDevelopmentAuthManager(): DevelopmentAuthManager {
  if (!developmentAuthManager) {
    developmentAuthManager = new DevelopmentAuthManager();
  }
  return developmentAuthManager;
}

/**
 * Initialize development authentication manager with custom config
 */
export function initializeDevelopmentAuthManager(
  config?: Partial<DevelopmentAuthConfig>
): DevelopmentAuthManager {
  developmentAuthManager = new DevelopmentAuthManager(config);
  return developmentAuthManager;
}

/**
 * Reset development authentication manager (useful for testing)
 */
export function resetDevelopmentAuthManager(): void {
  developmentAuthManager = null;
}
