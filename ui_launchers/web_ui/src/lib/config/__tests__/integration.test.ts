/**
 * Integration tests for Environment Configuration Manager
 * 
 * Tests integration with existing backend utilities and API routes
 * Requirements: 1.1, 1.2
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { getEnvironmentConfigManager, initializeEnvironmentConfigManager } from '../environment-config-manager';
import {
  getBackendBaseUrl,
  getBackendCandidates,
  withBackendPath,
  getTimeoutConfig,
  getRetryPolicy,
  getEnvironmentInfo,
  validateBackendConfiguration,
} from '../../../app/api/_utils/backend';

// Mock environment variables
const mockEnv = (env: Record<string, string>) => {
  const originalEnv = process.env;
  process.env = { ...originalEnv, ...env };
  return () => {
    process.env = originalEnv;
  };
};

describe('Environment Configuration Manager Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Backend Utilities Integration', () => {
    it('should integrate with getBackendBaseUrl', () => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'http://test-backend:9000',
      });

      // Initialize new manager to pick up environment changes
      initializeEnvironmentConfigManager();
      
      const backendUrl = getBackendBaseUrl();
      expect(backendUrl).toBe('http://test-backend:9000');

      restoreEnv();
    });

    it('should integrate with getBackendCandidates', () => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'http://primary:8000',
        KAREN_FALLBACK_BACKEND_URLS: 'http://fallback1:8000,http://fallback2:8000',
      });

      initializeEnvironmentConfigManager();
      
      const candidates = getBackendCandidates();
      expect(candidates).toContain('http://primary:8000');
      expect(candidates).toContain('http://fallback1:8000');
      expect(candidates).toContain('http://fallback2:8000');

      restoreEnv();
    });

    it('should integrate with withBackendPath', () => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'http://api-server:8080',
      });

      initializeEnvironmentConfigManager();
      
      const fullPath = withBackendPath('/api/health');
      expect(fullPath).toBe('http://api-server:8080/api/health');

      restoreEnv();
    });

    it('should integrate with getTimeoutConfig', () => {
      const restoreEnv = mockEnv({
        AUTH_TIMEOUT_MS: '60000',
        CONNECTION_TIMEOUT_MS: '45000',
      });

      initializeEnvironmentConfigManager();
      
      const timeouts = getTimeoutConfig();
      expect(timeouts.authentication).toBe(60000);
      expect(timeouts.connection).toBe(45000);

      restoreEnv();
    });

    it('should integrate with getRetryPolicy', () => {
      const restoreEnv = mockEnv({
        MAX_RETRY_ATTEMPTS: '5',
        RETRY_BASE_DELAY_MS: '2000',
      });

      initializeEnvironmentConfigManager();
      
      const retryPolicy = getRetryPolicy();
      expect(retryPolicy.maxAttempts).toBe(5);
      expect(retryPolicy.baseDelay).toBe(2000);

      restoreEnv();
    });

    it('should integrate with getEnvironmentInfo', () => {
      const restoreEnv = mockEnv({
        DOCKER_CONTAINER: 'true',
        HOSTNAME: 'docker-container-123',
      });

      initializeEnvironmentConfigManager();
      
      const envInfo = getEnvironmentInfo();
      expect(envInfo.type).toBe('docker');
      expect(envInfo.isDocker).toBe(true);

      restoreEnv();
    });

    it('should integrate with validateBackendConfiguration', () => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'http://valid-backend:8000',
        AUTH_TIMEOUT_MS: '30000',
      });

      initializeEnvironmentConfigManager();
      
      const validation = validateBackendConfiguration();
      expect(validation.isValid).toBe(true);
      expect(validation.config.primaryUrl).toBe('http://valid-backend:8000');

      restoreEnv();
    });
  });

  describe('Fallback Behavior', () => {
    it('should handle Environment Configuration Manager unavailability gracefully', () => {
      // Mock the getEnvironmentConfigManager to throw an error
      vi.doMock('../environment-config-manager', () => ({
        getEnvironmentConfigManager: () => {
          throw new Error('Manager not available');
        },
      }));

      // These should not throw and should return reasonable defaults
      expect(() => getBackendBaseUrl()).not.toThrow();
      expect(() => getBackendCandidates()).not.toThrow();
      expect(() => getTimeoutConfig()).not.toThrow();
      expect(() => getRetryPolicy()).not.toThrow();
      expect(() => getEnvironmentInfo()).not.toThrow();
      expect(() => validateBackendConfiguration()).not.toThrow();
    });
  });

  describe('Configuration Consistency', () => {
    it('should maintain consistent configuration across multiple calls', () => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'http://consistent-backend:8000',
        AUTH_TIMEOUT_MS: '45000',
      });

      initializeEnvironmentConfigManager();
      
      // Multiple calls should return consistent results
      const url1 = getBackendBaseUrl();
      const url2 = getBackendBaseUrl();
      expect(url1).toBe(url2);

      const timeout1 = getTimeoutConfig();
      const timeout2 = getTimeoutConfig();
      expect(timeout1.authentication).toBe(timeout2.authentication);

      restoreEnv();
    });

    it('should reflect environment changes after reinitialization', () => {
      // Initial configuration
      const restoreEnv1 = mockEnv({
        KAREN_BACKEND_URL: 'http://initial-backend:8000',
      });

      initializeEnvironmentConfigManager();
      const initialUrl = getBackendBaseUrl();
      expect(initialUrl).toBe('http://initial-backend:8000');

      restoreEnv1();

      // Changed configuration
      const restoreEnv2 = mockEnv({
        KAREN_BACKEND_URL: 'http://updated-backend:9000',
      });

      initializeEnvironmentConfigManager();
      const updatedUrl = getBackendBaseUrl();
      expect(updatedUrl).toBe('http://updated-backend:9000');

      restoreEnv2();
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid URLs gracefully', () => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'invalid-url',
      });

      initializeEnvironmentConfigManager();
      
      const validation = validateBackendConfiguration();
      expect(validation.isValid).toBe(false);
      expect(validation.errors.some(error => error.includes('Invalid primary backend URL'))).toBe(true);

      restoreEnv();
    });

    it('should handle missing environment variables gracefully', () => {
      const restoreEnv = mockEnv({
        // No backend URL specified
      });

      initializeEnvironmentConfigManager();
      
      // Should not throw and should provide defaults
      expect(() => getBackendBaseUrl()).not.toThrow();
      expect(() => getTimeoutConfig()).not.toThrow();
      expect(() => getRetryPolicy()).not.toThrow();

      const url = getBackendBaseUrl();
      expect(url).toBe('http://localhost:8000'); // Default for local environment

      restoreEnv();
    });
  });
});