/**
 * Test for timeout configuration management
 * 
 * Verifies that AUTH_TIMEOUT_MS has been increased from 15s to 45s
 * and that different operation types have appropriate timeout settings.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  TimeoutManager,
  getTimeoutManager,
  OperationType,
} from '../timeout-manager';

// Mock process.env
const originalEnv = process.env;

describe('Timeout Configuration Management', () => {
  beforeEach(() => {
    // Reset environment variables
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe('AUTH_TIMEOUT_MS Configuration', () => {
    it('should use 45 seconds as default authentication timeout (increased from 15s)', () => {
      const timeoutManager = new TimeoutManager();
      const authTimeout = timeoutManager.getTimeout(OperationType.AUTHENTICATION);
      
      expect(authTimeout).toBe(45000); // 45 seconds
    });

    it('should respect AUTH_TIMEOUT_MS environment variable', () => {
      process.env.AUTH_TIMEOUT_MS = '60000';
      
      const timeoutManager = new TimeoutManager();
      const authTimeout = timeoutManager.getTimeout(OperationType.AUTHENTICATION);
      
      expect(authTimeout).toBe(60000);
    });

    it('should fall back to default when AUTH_TIMEOUT_MS is invalid', () => {
      process.env.AUTH_TIMEOUT_MS = 'invalid';
      
      const timeoutManager = new TimeoutManager();
      const authTimeout = timeoutManager.getTimeout(OperationType.AUTHENTICATION);
      
      expect(authTimeout).toBe(45000); // Should use default
    });
  });

  describe('Different Operation Type Timeouts', () => {
    it('should have appropriate timeouts for different operation types', () => {
      const timeoutManager = new TimeoutManager();
      
      expect(timeoutManager.getTimeout(OperationType.CONNECTION)).toBe(30000); // 30s
      expect(timeoutManager.getTimeout(OperationType.AUTHENTICATION)).toBe(45000); // 45s (increased)
      expect(timeoutManager.getTimeout(OperationType.SESSION_VALIDATION)).toBe(30000); // 30s
      expect(timeoutManager.getTimeout(OperationType.HEALTH_CHECK)).toBe(10000); // 10s
      expect(timeoutManager.getTimeout(OperationType.DATABASE)).toBe(30000); // 30s
    });

    it('should allow custom timeout configuration via environment variables', () => {
      process.env.CONNECTION_TIMEOUT_MS = '25000';
      process.env.AUTH_TIMEOUT_MS = '50000';
      process.env.SESSION_VALIDATION_TIMEOUT_MS = '35000';
      process.env.HEALTH_CHECK_TIMEOUT_MS = '8000';
      process.env.DATABASE_TIMEOUT_MS = '40000';
      
      const timeoutManager = new TimeoutManager();
      
      expect(timeoutManager.getTimeout(OperationType.CONNECTION)).toBe(25000);
      expect(timeoutManager.getTimeout(OperationType.AUTHENTICATION)).toBe(50000);
      expect(timeoutManager.getTimeout(OperationType.SESSION_VALIDATION)).toBe(35000);
      expect(timeoutManager.getTimeout(OperationType.HEALTH_CHECK)).toBe(8000);
      expect(timeoutManager.getTimeout(OperationType.DATABASE)).toBe(40000);
    });
  });

  describe('Database Operation Timeouts', () => {
    it('should provide different timeouts for database operation types', () => {
      const timeoutManager = new TimeoutManager();
      const baseTimeout = timeoutManager.getTimeout(OperationType.DATABASE);
      
      expect(timeoutManager.getDatabaseTimeout('connection')).toBe(baseTimeout * 0.5);
      expect(timeoutManager.getDatabaseTimeout('query')).toBe(baseTimeout);
      expect(timeoutManager.getDatabaseTimeout('transaction')).toBe(baseTimeout * 2);
    });
  });

  describe('Authentication Phase Timeouts', () => {
    it('should provide different timeouts for authentication phases', () => {
      const timeoutManager = new TimeoutManager();
      const authTimeout = timeoutManager.getTimeout(OperationType.AUTHENTICATION);
      const sessionTimeout = timeoutManager.getTimeout(OperationType.SESSION_VALIDATION);
      
      expect(timeoutManager.getAuthTimeout('login')).toBe(authTimeout);
      expect(timeoutManager.getAuthTimeout('validation')).toBe(sessionTimeout);
      expect(timeoutManager.getAuthTimeout('refresh')).toBe(Math.round(authTimeout * 0.7));
    });
  });

  describe('AbortController Integration', () => {
    it('should create AbortController with correct authentication timeout', () => {
      const timeoutManager = new TimeoutManager();
      const { timeout } = timeoutManager.createAbortController(OperationType.AUTHENTICATION);
      
      expect(timeout).toBe(45000); // Should use the increased timeout
    });

    it('should create AbortController with custom timeout', () => {
      process.env.AUTH_TIMEOUT_MS = '60000';
      
      const timeoutManager = new TimeoutManager();
      const { timeout } = timeoutManager.createAbortController(OperationType.AUTHENTICATION);
      
      expect(timeout).toBe(60000);
    });
  });

  describe('Singleton Pattern', () => {
    it('should maintain consistent timeout configuration across singleton instances', () => {
      const manager1 = getTimeoutManager();
      const manager2 = getTimeoutManager();
      
      expect(manager1).toBe(manager2);
      expect(manager1.getTimeout(OperationType.AUTHENTICATION)).toBe(45000);
      
      // Create new instance directly to test new configuration
      process.env.AUTH_TIMEOUT_MS = '55000';
      const newManager = new TimeoutManager();
      expect(newManager.getTimeout(OperationType.AUTHENTICATION)).toBe(55000);
    });
  });

  describe('Configuration Validation', () => {
    it('should validate that authentication timeout is reasonable for database operations', () => {
      const timeoutManager = new TimeoutManager();
      const validation = timeoutManager.validateConfiguration();
      
      expect(validation.isValid).toBe(true);
      
      // Check that authentication timeout is sufficient for database operations
      const authTimeout = timeoutManager.getTimeout(OperationType.AUTHENTICATION);
      expect(authTimeout).toBeGreaterThanOrEqual(30000); // At least 30 seconds
      expect(authTimeout).toBeLessThanOrEqual(120000); // Not more than 2 minutes
    });

    it('should warn about very low authentication timeouts', () => {
      process.env.AUTH_TIMEOUT_MS = '500'; // Very low timeout (below 1000ms)
      
      const timeoutManager = new TimeoutManager();
      const validation = timeoutManager.validateConfiguration();
      
      expect(validation.warnings.some(warning => 
        warning.includes('authentication timeout is very low')
      )).toBe(true);
    });

    it('should warn about very high authentication timeouts', () => {
      process.env.AUTH_TIMEOUT_MS = '400000'; // Very high timeout (above 5 minutes)
      
      const timeoutManager = new TimeoutManager();
      const validation = timeoutManager.validateConfiguration();
      
      expect(validation.warnings.some(warning => 
        warning.includes('authentication timeout is very high')
      )).toBe(true);
    });
  });
});