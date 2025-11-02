import {
import { extensionAuthRecoveryManager } from "../extension-auth-recovery";
import { getExtensionAuthManager } from "../extension-auth-manager";
import { vi, describe, it, beforeEach, expect } from "vitest";
/**
 * Integration Tests for Extension Authentication Error Handling System
 *
 * Tests the complete flow from error detection through recovery and degradation.
 */


  ExtensionAuthErrorFactory,
  ExtensionAuthRecoveryStrategy,
  extensionAuthErrorHandler,
} from "../extension-auth-errors";

  ExtensionFeatureLevel,
  extensionAuthDegradationManager,
} from "../extension-auth-degradation";





// Mock the extension auth manager
vi.mock("../extension-auth-manager");
const mockGetExtensionAuthManager = vi.mocked(getExtensionAuthManager);

// Mock the main error handler
vi.mock("@/lib/error-handler", () => ({
  errorHandler: {
    showSuccess: vi.fn(),
    showWarning: vi.fn(),
    showErrorToast: vi.fn(),
  },
}));

describe("Extension Authentication Error Handling Integration", () => {
  let mockAuthManager: any;

  beforeEach(() => {
    // Reset all managers
    extensionAuthDegradationManager.restoreFullFunctionality();
    extensionAuthDegradationManager.clearCache();
    extensionAuthRecoveryManager.clearRecoveryHistory();
    extensionAuthRecoveryManager.cancelAllRecoveries();
    extensionAuthErrorHandler.clearErrorHistory();

    mockAuthManager = {
      forceRefresh: vi.fn(),
      clearAuth: vi.fn(),
    };
    mockGetExtensionAuthManager.mockReturnValue(mockAuthManager);
  });

  describe("Token Expired Error Flow", () => {
    it("should handle successful token refresh and restore functionality", async () => {
      // Simulate token expired error
      const error = ExtensionAuthErrorFactory.createTokenExpiredError({
        endpoint: "/api/extensions/",
        operation: "extension_list",
      });

      // Mock successful token refresh
      mockAuthManager.forceRefresh.mockResolvedValue("new-access-token");

      // Process the error through the complete system
      const errorInfo = extensionAuthErrorHandler.handleError(error);
      const recoveryResult = await extensionAuthRecoveryManager.attemptRecovery(
        error,
        "/api/extensions/",
        "extension_list"
      );

      // Verify error was handled correctly
      expect(errorInfo.category).toBe("token_expired");
      expect(errorInfo.retry_possible).toBe(true);
      expect(errorInfo.user_action_required).toBe(false);

      // Verify recovery was successful
      expect(recoveryResult.success).toBe(true);
      expect(recoveryResult.strategy).toBe(
        ExtensionAuthRecoveryStrategy.RETRY_WITH_REFRESH
      );
      expect(recoveryResult.requiresUserAction).toBe(false);

      // Verify token refresh was called
      expect(mockAuthManager.forceRefresh).toHaveBeenCalled();

      // Verify functionality remains available
      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_list")
      ).toBe(true);
    });

    it("should handle failed token refresh and apply degradation", async () => {
      // Simulate token expired error
      const error = ExtensionAuthErrorFactory.createTokenExpiredError({
        endpoint: "/api/extensions/",
        operation: "extension_list",
      });

      // Mock failed token refresh
      mockAuthManager.forceRefresh.mockResolvedValue(null);

      // Process the error through the complete system
      const recoveryResult = await extensionAuthRecoveryManager.attemptRecovery(
        error,
        "/api/extensions/",
        "extension_list"
      );

      // Verify recovery failed but provided guidance
      expect(recoveryResult.success).toBe(false);
      expect(recoveryResult.requiresUserAction).toBe(true);
      expect(recoveryResult.message).toContain("user authentication required");
    });
  });

  describe("Permission Denied Error Flow", () => {
    it("should apply readonly degradation and provide fallback data", async () => {
      // Simulate permission denied error
      const error = ExtensionAuthErrorFactory.createPermissionDeniedError({
        endpoint: "/api/extensions/",
        operation: "extension_install",
      });

      // Process the error through the complete system
      const errorInfo = extensionAuthErrorHandler.handleError(error);
      const recoveryResult = await extensionAuthRecoveryManager.attemptRecovery(
        error,
        "/api/extensions/",
        "extension_install"
      );

      // Verify error was handled correctly
      expect(errorInfo.category).toBe("permission_denied");
      expect(errorInfo.retry_possible).toBe(false);
      expect(errorInfo.user_action_required).toBe(true);

      // Verify degradation was applied
      const degradationState =
        extensionAuthDegradationManager.getDegradationState();
      expect(degradationState.level).toBe(ExtensionFeatureLevel.READONLY);

      // Verify recovery provided fallback
      expect(recoveryResult.success).toBe(true);
      expect(recoveryResult.strategy).toBe(
        ExtensionAuthRecoveryStrategy.FALLBACK_TO_READONLY
      );
      expect(recoveryResult.fallbackData).toBeDefined();

      // Verify write features are disabled but read features remain
      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_install")
      ).toBe(false);
      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_list")
      ).toBe(true);
    });
  });

  describe("Service Unavailable Error Flow", () => {
    it("should use cached data when available", async () => {
      // Cache some data first
      extensionAuthDegradationManager.cacheData(
        "extension_list",
        { extensions: [{ name: "cached-extension" }] },
        "test-cache"
      );

      // Simulate service unavailable error
      const error = ExtensionAuthErrorFactory.createServiceUnavailableError({
        endpoint: "/api/extensions/",
        operation: "extension_list",
      });

      // Process the error through the complete system
      const recoveryResult = await extensionAuthRecoveryManager.attemptRecovery(
        error,
        "/api/extensions/",
        "extension_list"
      );

      // Verify degradation was applied
      const degradationState =
        extensionAuthDegradationManager.getDegradationState();
      expect(degradationState.level).toBe(ExtensionFeatureLevel.CACHED);

      // Verify recovery used cached data
      expect(recoveryResult.success).toBe(true);
      expect(recoveryResult.strategy).toBe(
        ExtensionAuthRecoveryStrategy.FALLBACK_TO_CACHED
      );
      expect(recoveryResult.fallbackData).toEqual({
        extensions: [{ name: "cached-extension" }],
      });

      // Verify cached features are available
      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_list")
      ).toBe(true);
    });

    it("should use static fallback when no cached data available", async () => {
      // Simulate service unavailable error without cached data
      const error = ExtensionAuthErrorFactory.createServiceUnavailableError({
        endpoint: "/api/extensions/",
        operation: "extension_list",
      });

      // Process the error through the complete system
      const recoveryResult = await extensionAuthRecoveryManager.attemptRecovery(
        error,
        "/api/extensions/",
        "extension_list"
      );

      // Verify recovery used static fallback
      expect(recoveryResult.success).toBe(true);
      expect(recoveryResult.fallbackData).toBeDefined();
      expect(recoveryResult.fallbackData.message).toContain(
        "temporarily unavailable"
      );
    });
  });

  describe("Configuration Error Flow", () => {
    it("should disable all features and require admin intervention", async () => {
      // Simulate configuration error
      const error = ExtensionAuthErrorFactory.createConfigurationError({
        endpoint: "/api/extensions/",
        operation: "extension_list",
      });

      // Process the error through the complete system
      const errorInfo = extensionAuthErrorHandler.handleError(error);
      const recoveryResult = await extensionAuthRecoveryManager.attemptRecovery(
        error,
        "/api/extensions/",
        "extension_list"
      );

      // Verify error was handled as critical
      expect(errorInfo.category).toBe("configuration_error");
      expect(errorInfo.severity).toBe("critical");
      expect(errorInfo.user_action_required).toBe(true);

      // Verify all features are disabled
      const degradationState =
        extensionAuthDegradationManager.getDegradationState();
      expect(degradationState.level).toBe(ExtensionFeatureLevel.DISABLED);

      // Verify no recovery is possible
      expect(recoveryResult.success).toBe(false);
      expect(recoveryResult.strategy).toBe(
        ExtensionAuthRecoveryStrategy.NO_RECOVERY
      );
      expect(recoveryResult.requiresUserAction).toBe(true);

      // Verify all features are unavailable
      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_list")
      ).toBe(false);
      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_install")
      ).toBe(false);
      expect(
        extensionAuthDegradationManager.isFeatureAvailable("background_tasks")
      ).toBe(false);
    });
  });

  describe("Network Error Flow", () => {
    it("should apply graceful degradation with retry capability", async () => {
      // Simulate network error
      const error = ExtensionAuthErrorFactory.createNetworkError({
        endpoint: "/api/extensions/",
        operation: "extension_list",
      });

      // Process the error through the complete system
      const errorInfo = extensionAuthErrorHandler.handleError(error);
      const recoveryResult = await extensionAuthRecoveryManager.attemptRecovery(
        error,
        "/api/extensions/",
        "extension_list"
      );

      // Verify error is retryable
      expect(errorInfo.retry_possible).toBe(true);
      expect(errorInfo.user_action_required).toBe(false);

      // Verify graceful degradation was applied
      expect(recoveryResult.success).toBe(true);
      expect(recoveryResult.strategy).toBe(
        ExtensionAuthRecoveryStrategy.GRACEFUL_DEGRADATION
      );
      expect(recoveryResult.fallbackData).toBeDefined();

      // Verify some features remain available
      const degradationState =
        extensionAuthDegradationManager.getDegradationState();
      expect(degradationState.level).toBe(ExtensionFeatureLevel.CACHED);
    });
  });

  describe("Multiple Error Scenarios", () => {
    it("should handle cascading errors appropriately", async () => {
      // First error: token expired
      const tokenError = ExtensionAuthErrorFactory.createTokenExpiredError();
      mockAuthManager.forceRefresh.mockRejectedValue(
        new Error("Refresh failed")
      );

      await extensionAuthRecoveryManager.attemptRecovery(
        tokenError,
        "/api/extensions/",
        "extension_list"
      );

      // Second error: service unavailable
      const serviceError =
        ExtensionAuthErrorFactory.createServiceUnavailableError();
      await extensionAuthRecoveryManager.attemptRecovery(
        serviceError,
        "/api/extensions/",
        "extension_list"
      );

      // Verify error history is maintained
      const errorHistory = extensionAuthErrorHandler.getErrorHistory();
      expect(errorHistory.length).toBe(2);

      // Verify recovery statistics
      const recoveryStats =
        extensionAuthRecoveryManager.getRecoveryStatistics();
      expect(recoveryStats.totalAttempts).toBe(2);
    });

    it("should detect systemic issues with multiple errors", async () => {
      // Generate multiple errors quickly
      for (let i = 0; i < 5; i++) {
        const error = ExtensionAuthErrorFactory.createNetworkError();
        extensionAuthErrorHandler.handleError(error);
      }

      // Verify systemic issue detection
      expect(extensionAuthErrorHandler.detectSystemicIssue()).toBe(true);
    });
  });

  describe("Recovery and Restoration Flow", () => {
    it("should restore full functionality after successful recovery", async () => {
      // Apply degradation due to error
      const error = ExtensionAuthErrorFactory.createPermissionDeniedError();
      extensionAuthDegradationManager.applyDegradation(error);

      // Verify degradation is active
      expect(extensionAuthDegradationManager.getDegradationState().level).toBe(
        ExtensionFeatureLevel.READONLY
      );

      // Simulate successful authentication restoration
      extensionAuthDegradationManager.restoreFullFunctionality();

      // Verify full functionality is restored
      const state = extensionAuthDegradationManager.getDegradationState();
      expect(state.level).toBe(ExtensionFeatureLevel.FULL);
      expect(state.affectedFeatures).toHaveLength(0);
      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_install")
      ).toBe(true);
    });
  });

  describe("Feature Availability During Degradation", () => {
    it("should correctly determine feature availability at different degradation levels", () => {
      // Test full functionality
      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_list")
      ).toBe(true);
      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_install")
      ).toBe(true);

      // Apply limited degradation
      const tokenError = ExtensionAuthErrorFactory.createTokenExpiredError();
      extensionAuthDegradationManager.applyDegradation(tokenError);

      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_list")
      ).toBe(true); // high priority
      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_install")
      ).toBe(false); // low priority

      // Apply readonly degradation
      const permissionError =
        ExtensionAuthErrorFactory.createPermissionDeniedError();
      extensionAuthDegradationManager.applyDegradation(permissionError);

      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_list")
      ).toBe(true); // read-only
      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_install")
      ).toBe(false); // requires write

      // Apply disabled degradation
      const configError = ExtensionAuthErrorFactory.createConfigurationError();
      extensionAuthDegradationManager.applyDegradation(configError);

      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_list")
      ).toBe(false);
      expect(
        extensionAuthDegradationManager.isFeatureAvailable("extension_install")
      ).toBe(false);
    });
  });
});
