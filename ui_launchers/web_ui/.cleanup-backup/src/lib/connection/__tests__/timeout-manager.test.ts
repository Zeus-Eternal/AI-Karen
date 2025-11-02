/**
 * Unit tests for TimeoutManager
 * 
 * Tests timeout configuration management, validation,
 * and different operation type handling.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  TimeoutManager,
  getTimeoutManager,
  initializeTimeoutManager,
  OperationType,
} from '../timeout-manager';

// Mock process.env
const originalEnv = process.env;

describe('TimeoutManager', () => {
  let timeoutManager: TimeoutManager;

  beforeEach(() => {
    // Reset environment variables
    process.env = { ...originalEnv };
    timeoutManager = new TimeoutManager();
  });

  afterEach(() => {
    process.env = originalEnv;
    vi.restoreAllMocks();
  });

  describe('Default Configuration', () => {
    it('should load default timeout values', () => {
      const timeouts = timeoutManager.getAllTimeouts();

      expect(timeouts.connection).toBe(30000);
      expect(timeouts.authentication).toBe(45000); // Increased from 15s
      expect(timeouts.sessionValidation).toBe(30000);
      expect(timeouts.healthCheck).toBe(10000);
      expect(timeouts.database).toBe(30000);
    });

    it('should load timeout values from environment variables', () => {
      process.env.CONNECTION_TIMEOUT_MS = '20000';
      process.env.AUTH_TIMEOUT_MS = '60000';
      process.env.HEALTH_CHECK_TIMEOUT_MS = '5000';

      const manager = new TimeoutManager();
      const timeouts = manager.getAllTimeouts();

      expect(timeouts.connection).toBe(20000);
      expect(timeouts.authentication).toBe(60000);
      expect(timeouts.healthCheck).toBe(5000);
    });

    it('should ignore invalid environment variable values', () => {
      process.env.CONNECTION_TIMEOUT_MS = 'invalid';
      process.env.AUTH_TIMEOUT_MS = '-1000';
      process.env.HEALTH_CHECK_TIMEOUT_MS = '0';

      const manager = new TimeoutManager();
      const timeouts = manager.getAllTimeouts();

      // Should use defaults for invalid values
      expect(timeouts.connection).toBe(30000);
      expect(timeouts.authentication).toBe(45000);
      expect(timeouts.healthCheck).toBe(10000);
    });
  });

  describe('Timeout Retrieval', () => {
    it('should get timeout for specific operation types', () => {
      expect(timeoutManager.getTimeout(OperationType.CONNECTION)).toBe(30000);
      expect(timeoutManager.getTimeout(OperationType.AUTHENTICATION)).toBe(45000);
      expect(timeoutManager.getTimeout(OperationType.SESSION_VALIDATION)).toBe(30000);
      expect(timeoutManager.getTimeout(OperationType.HEALTH_CHECK)).toBe(10000);
      expect(timeoutManager.getTimeout(OperationType.DATABASE)).toBe(30000);
    });

    it('should get custom timeout with default fallback', () => {
      expect(timeoutManager.getCustomTimeout('custom-operation')).toBe(30000); // Falls back to connection timeout
      expect(timeoutManager.getCustomTimeout('custom-operation', 15000)).toBe(15000); // Uses provided default
    });

    it('should get custom timeout after setting it', () => {
      timeoutManager.setCustomTimeout('my-operation', 25000);
      expect(timeoutManager.getCustomTimeout('my-operation')).toBe(25000);
    });
  });

  describe('Timeout Configuration', () => {
    it('should set timeout for specific operation types', () => {
      timeoutManager.setTimeout(OperationType.CONNECTION, 40000);
      expect(timeoutManager.getTimeout(OperationType.CONNECTION)).toBe(40000);
    });

    it('should throw error for invalid timeout values', () => {
      expect(() => {
        timeoutManager.setTimeout(OperationType.CONNECTION, 0);
      }).toThrow('Timeout must be positive, got: 0');

      expect(() => {
        timeoutManager.setTimeout(OperationType.CONNECTION, -1000);
      }).toThrow('Timeout must be positive, got: -1000');
    });

    it('should set custom timeout', () => {
      timeoutManager.setCustomTimeout('file-upload', 120000);
      expect(timeoutManager.getCustomTimeout('file-upload')).toBe(120000);
    });

    it('should throw error for invalid custom timeout values', () => {
      expect(() => {
        timeoutManager.setCustomTimeout('operation', 0);
      }).toThrow('Timeout must be positive, got: 0');
    });

    it('should update multiple timeouts at once', () => {
      timeoutManager.updateTimeouts({
        connection: 25000,
        authentication: 50000,
        healthCheck: 8000,
      });

      expect(timeoutManager.getTimeout(OperationType.CONNECTION)).toBe(25000);
      expect(timeoutManager.getTimeout(OperationType.AUTHENTICATION)).toBe(50000);
      expect(timeoutManager.getTimeout(OperationType.HEALTH_CHECK)).toBe(8000);
      // Other timeouts should remain unchanged
      expect(timeoutManager.getTimeout(OperationType.SESSION_VALIDATION)).toBe(30000);
    });

    it('should ignore invalid values in batch update', () => {
      const originalConnection = timeoutManager.getTimeout(OperationType.CONNECTION);
      
      timeoutManager.updateTimeouts({
        connection: -1000, // Invalid
        authentication: 50000, // Valid
      });

      expect(timeoutManager.getTimeout(OperationType.CONNECTION)).toBe(originalConnection);
      expect(timeoutManager.getTimeout(OperationType.AUTHENTICATION)).toBe(50000);
    });

    it('should reset to default values', () => {
      timeoutManager.setTimeout(OperationType.CONNECTION, 40000);
      timeoutManager.setCustomTimeout('custom', 15000);

      timeoutManager.resetToDefaults();

      expect(timeoutManager.getTimeout(OperationType.CONNECTION)).toBe(30000);
      expect(timeoutManager.getCustomTimeout('custom')).toBe(30000); // Falls back to default
    });
  });

  describe('Scaled Timeouts', () => {
    it('should scale timeout based on complexity factor', () => {
      const baseTimeout = timeoutManager.getTimeout(OperationType.CONNECTION);
      
      expect(timeoutManager.getScaledTimeout(OperationType.CONNECTION, 1)).toBe(baseTimeout);
      expect(timeoutManager.getScaledTimeout(OperationType.CONNECTION, 2)).toBe(baseTimeout * 2);
      expect(timeoutManager.getScaledTimeout(OperationType.CONNECTION, 0.5)).toBe(baseTimeout * 0.5);
    });

    it('should enforce minimum timeout of 1 second', () => {
      expect(timeoutManager.getScaledTimeout(OperationType.CONNECTION, 0.01)).toBe(1000);
    });

    it('should handle very small complexity factors', () => {
      expect(timeoutManager.getScaledTimeout(OperationType.CONNECTION, 0)).toBe(1000);
      expect(timeoutManager.getScaledTimeout(OperationType.CONNECTION, -1)).toBe(1000);
    });
  });

  describe('Database Timeouts', () => {
    it('should get different timeouts for database operations', () => {
      const baseTimeout = timeoutManager.getTimeout(OperationType.DATABASE);
      
      expect(timeoutManager.getDatabaseTimeout('query')).toBe(baseTimeout);
      expect(timeoutManager.getDatabaseTimeout('connection')).toBe(baseTimeout * 0.5);
      expect(timeoutManager.getDatabaseTimeout('transaction')).toBe(baseTimeout * 2);
    });

    it('should default to query timeout', () => {
      const baseTimeout = timeoutManager.getTimeout(OperationType.DATABASE);
      expect(timeoutManager.getDatabaseTimeout()).toBe(baseTimeout);
    });
  });

  describe('Authentication Timeouts', () => {
    it('should get different timeouts for authentication phases', () => {
      const authTimeout = timeoutManager.getTimeout(OperationType.AUTHENTICATION);
      const sessionTimeout = timeoutManager.getTimeout(OperationType.SESSION_VALIDATION);
      
      expect(timeoutManager.getAuthTimeout('login')).toBe(authTimeout);
      expect(timeoutManager.getAuthTimeout('validation')).toBe(sessionTimeout);
      expect(timeoutManager.getAuthTimeout('refresh')).toBe(Math.round(authTimeout * 0.7));
    });

    it('should default to login timeout', () => {
      const authTimeout = timeoutManager.getTimeout(OperationType.AUTHENTICATION);
      expect(timeoutManager.getAuthTimeout()).toBe(authTimeout);
    });
  });

  describe('Configuration Validation', () => {
    it('should validate correct configuration', () => {
      const validation = timeoutManager.validateConfiguration();
      
      expect(validation.isValid).toBe(true);
      expect(validation.errors).toHaveLength(0);
    });

    it('should detect invalid timeout values', () => {
      // Directly modify the internal timeouts to test validation
      (timeoutManager as any).timeouts.connection = -1000;
      
      const validation = timeoutManager.validateConfiguration();
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('connection timeout must be positive, got: -1000');
    });

    it('should warn about very low timeout values', () => {
      timeoutManager.setTimeout(OperationType.CONNECTION, 500);
      
      const validation = timeoutManager.validateConfiguration();
      
      expect(validation.warnings).toContain('connection timeout is very low (500ms), consider increasing it');
    });

    it('should warn about very high timeout values', () => {
      timeoutManager.setTimeout(OperationType.CONNECTION, 400000);
      
      const validation = timeoutManager.validateConfiguration();
      
      expect(validation.warnings).toContain('connection timeout is very high (400000ms), consider reducing it');
    });

    it('should warn about logical inconsistencies', () => {
      timeoutManager.setTimeout(OperationType.HEALTH_CHECK, 40000);
      timeoutManager.setTimeout(OperationType.CONNECTION, 30000);
      
      const validation = timeoutManager.validateConfiguration();
      
      expect(validation.warnings).toContain('Health check timeout is higher than connection timeout, this may cause issues');
    });

    it('should validate custom timeouts', () => {
      // Directly modify the internal custom timeouts to test validation
      (timeoutManager as any).customTimeouts.set('invalid-operation', -500);
      
      const validation = timeoutManager.validateConfiguration();
      
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain("Custom timeout 'invalid-operation' must be positive, got: -500");
    });
  });

  describe('AbortController Creation', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should create AbortController with timeout', () => {
      const { controller, timeoutId, timeout } = timeoutManager.createAbortController(OperationType.CONNECTION);
      
      expect(controller).toBeInstanceOf(AbortController);
      expect(controller.signal.aborted).toBe(false);
      expect(timeout).toBe(30000);
      expect(timeoutId).toBeDefined();
    });

    it('should create AbortController with custom timeout', () => {
      const { controller, timeout } = timeoutManager.createAbortController(OperationType.CONNECTION, 15000);
      
      expect(controller.signal.aborted).toBe(false);
      expect(timeout).toBe(15000);
    });

    it('should abort controller after timeout', () => {
      const { controller } = timeoutManager.createAbortController(OperationType.HEALTH_CHECK);
      
      expect(controller.signal.aborted).toBe(false);
      
      // Fast-forward time
      vi.advanceTimersByTime(10000);
      
      expect(controller.signal.aborted).toBe(true);
    });

    it('should create scaled AbortController', () => {
      const { controller, timeout } = timeoutManager.createScaledAbortController(OperationType.CONNECTION, 2);
      
      expect(controller.signal.aborted).toBe(false);
      expect(timeout).toBe(60000); // 30000 * 2
    });
  });

  describe('Configuration Summary', () => {
    it('should provide complete configuration summary', () => {
      timeoutManager.setCustomTimeout('file-upload', 120000);
      
      const summary = timeoutManager.getConfigurationSummary();
      
      expect(summary.timeouts).toEqual(timeoutManager.getAllTimeouts());
      expect(summary.customTimeouts).toEqual({ 'file-upload': 120000 });
      expect(summary.validation).toEqual(timeoutManager.validateConfiguration());
    });
  });

  describe('Singleton Pattern', () => {
    it('should return same instance from getTimeoutManager', () => {
      const manager1 = getTimeoutManager();
      const manager2 = getTimeoutManager();
      expect(manager1).toBe(manager2);
    });

    it('should create new instance with initializeTimeoutManager', () => {
      const manager1 = getTimeoutManager();
      const manager2 = initializeTimeoutManager();
      expect(manager1).not.toBe(manager2);
      
      // Subsequent calls should return the new instance
      const manager3 = getTimeoutManager();
      expect(manager2).toBe(manager3);
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing process.env gracefully', () => {
      const originalProcess = global.process;
      // @ts-ignore
      global.process = undefined;
      
      const manager = new TimeoutManager();
      const timeouts = manager.getAllTimeouts();
      
      // Should use default values
      expect(timeouts.connection).toBe(30000);
      expect(timeouts.authentication).toBe(45000);
      
      global.process = originalProcess;
    });

    it('should handle empty environment variables', () => {
      process.env.CONNECTION_TIMEOUT_MS = '';
      process.env.AUTH_TIMEOUT_MS = '   ';
      
      const manager = new TimeoutManager();
      const timeouts = manager.getAllTimeouts();
      
      // Should use defaults for empty values
      expect(timeouts.connection).toBe(30000);
      expect(timeouts.authentication).toBe(45000);
    });
  });
});