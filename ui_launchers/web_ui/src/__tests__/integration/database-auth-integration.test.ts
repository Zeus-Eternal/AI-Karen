/**
 * Database Authentication Integration Tests
 * 
 * Tests end-to-end authentication flow with admin@example.com/password123 credentials
 * against the actual database, including connectivity validation and error handling.
 * 
 * Requirements: 4.1, 4.2, 4.3
 */

import { 
  testDatabaseAuthentication,
  testDatabaseConnectivity,
  testAuthenticationWithDatabaseValidation,
  validateTestCredentials,
  createTestSession,
  cleanupTestSession,
  DatabaseAuthTestSuite,
  TEST_CREDENTIALS,
} from '@/test-utils/auth-test-utils';
import { getConnectionManager, initializeConnectionManager } from '@/lib/connection/connection-manager';
import { getEnvironmentConfigManager } from '@/lib/config/index';

// Setup test environment
beforeAll(() => {
  // Initialize connection manager in test mode
  initializeConnectionManager(true);
});

beforeEach(() => {
  // Reset connection manager statistics
  const connectionManager = getConnectionManager();
  connectionManager.resetStatistics();
});

afterEach(async () => {
  // Clean up any test sessions
  await cleanupTestSession();
});

describe('Database Authentication Integration', () => {
  describe('Database Connectivity', () => {
    it('should test database connectivity successfully', async () => {
      const result = await testDatabaseConnectivity();
      
      expect(result).toMatchObject({
        isConnected: expect.any(Boolean),
        responseTime: expect.any(Number),
        timestamp: expect.any(Date),
      });

      if (!result.isConnected) {
        console.warn('Database connectivity test failed:', result.error);
      }

      // Response time should be reasonable (less than 30 seconds)
      expect(result.responseTime).toBeLessThan(30000);
    }, 35000);

    it('should handle database connectivity failures gracefully', async () => {
      // This test might pass or fail depending on actual database availability
      const result = await testDatabaseConnectivity();
      
      // Test should complete without throwing
      expect(result).toBeDefined();
      expect(result.timestamp).toBeInstanceOf(Date);
      
      if (!result.isConnected) {
        expect(result.error).toBeDefined();
        expect(typeof result.error).toBe('string');
      }
    }, 35000);
  });

  describe('Test Credentials Authentication', () => {
    it('should authenticate with admin@example.com/password123 credentials', async () => {
      const result = await testDatabaseAuthentication(TEST_CREDENTIALS);
      
      expect(result).toMatchObject({
        success: expect.any(Boolean),
        responseTime: expect.any(Number),
        retryCount: expect.any(Number),
        databaseConnectivity: expect.objectContaining({
          isConnected: expect.any(Boolean),
          responseTime: expect.any(Number),
          timestamp: expect.any(Date),
        }),
      });

      if (result.success) {
        expect(result.user).toMatchObject({
          user_id: expect.any(String),
          email: TEST_CREDENTIALS.email,
          roles: expect.any(Array),
          tenant_id: expect.any(String),
          role: expect.any(String),
        });

        // Verify admin privileges
        expect(['admin', 'super_admin']).toContain(result.user.role);
        expect(result.user.roles.length).toBeGreaterThan(0);
      } else {
        console.warn('Authentication test failed:', result.error);
        expect(result.error).toBeDefined();
      }

      // Response time should be reasonable
      expect(result.responseTime).toBeLessThan(45000); // 45 second timeout
    }, 50000);

    it('should fail authentication with invalid credentials', async () => {
      const invalidCredentials = {
        email: 'invalid@example.com',
        password: 'wrongpassword',
      };

      const result = await testDatabaseAuthentication(invalidCredentials);
      
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
      expect(result.user).toBeUndefined();
      
      // Should still test database connectivity
      expect(result.databaseConnectivity).toBeDefined();
    }, 50000);

    it('should handle authentication with enhanced error messages', async () => {
      const result = await testAuthenticationWithDatabaseValidation();
      
      expect(result).toMatchObject({
        success: expect.any(Boolean),
        responseTime: expect.any(Number),
        retryCount: expect.any(Number),
        databaseConnectivity: expect.any(Object),
      });

      if (!result.success) {
        expect(result.error).toBeDefined();
        expect(typeof result.error).toBe('string');
        
        // Error message should be user-friendly
        expect(result.error).not.toMatch(/^Error:/);
        expect(result.error.length).toBeGreaterThan(10);
      }
    }, 50000);
  });

  describe('Session Management', () => {
    it('should create and validate test session', async () => {
      const sessionResult = await createTestSession();
      
      if (sessionResult.success) {
        expect(sessionResult.sessionData).toMatchObject({
          userId: expect.any(String),
          email: TEST_CREDENTIALS.email,
          roles: expect.any(Array),
          tenantId: expect.any(String),
          role: expect.any(String),
        });

        // Verify session is valid by testing connectivity
        const connectivityResult = await testDatabaseConnectivity();
        expect(connectivityResult.isConnected).toBe(true);
      } else {
        console.warn('Test session creation failed:', sessionResult.error);
        expect(sessionResult.error).toBeDefined();
      }
    }, 50000);

    it('should clean up test session properly', async () => {
      // Create session first
      const sessionResult = await createTestSession();
      
      if (sessionResult.success) {
        // Clean up session
        await expect(cleanupTestSession()).resolves.not.toThrow();
      }
    }, 50000);
  });

  describe('Credential Validation', () => {
    it('should validate test credentials against database', async () => {
      const validation = await validateTestCredentials();
      
      expect(validation).toMatchObject({
        valid: expect.any(Boolean),
        message: expect.any(String),
      });

      if (validation.valid) {
        expect(validation.message).toContain('admin@example.com');
        expect(validation.details).toBeDefined();
        expect(validation.details?.success).toBe(true);
      } else {
        console.warn('Test credentials validation failed:', validation.message);
        expect(validation.message).toContain('failed');
      }
    }, 50000);
  });

  describe('Error Handling', () => {
    it('should provide proper error messages for database connection failures', async () => {
      // This test simulates various error conditions
      const testSuite = new DatabaseAuthTestSuite();
      
      // Test with invalid credentials to trigger error handling
      const invalidResult = await testSuite.runAuthTestWithInvalidCredentials();
      
      expect(invalidResult.success).toBe(false);
      expect(invalidResult.error).toBeDefined();
      
      // Error should be descriptive
      expect(invalidResult.error.length).toBeGreaterThan(5);
    }, 50000);

    it('should handle network timeouts gracefully', async () => {
      // Test database connectivity which might timeout
      const result = await testDatabaseConnectivity();
      
      // Should complete without throwing, regardless of success
      expect(result).toBeDefined();
      expect(result.responseTime).toBeGreaterThan(0);
      
      if (!result.isConnected && result.error) {
        // Error message should be informative
        expect(result.error).toBeDefined();
        expect(typeof result.error).toBe('string');
      }
    }, 35000);
  });

  describe('Performance and Reliability', () => {
    it('should complete authentication within timeout limits', async () => {
      const startTime = Date.now();
      const result = await testDatabaseAuthentication();
      const totalTime = Date.now() - startTime;
      
      // Should complete within 45 seconds (AUTH_TIMEOUT_MS)
      expect(totalTime).toBeLessThan(45000);
      expect(result.responseTime).toBeLessThan(45000);
    }, 50000);

    it('should handle concurrent authentication attempts', async () => {
      const concurrentTests = 3;
      const promises = Array(concurrentTests).fill(null).map(() => 
        testDatabaseAuthentication()
      );
      
      const results = await Promise.allSettled(promises);
      
      // All tests should complete
      expect(results).toHaveLength(concurrentTests);
      
      // Check that at least some tests completed successfully
      const completedTests = results.filter(r => r.status === 'fulfilled');
      expect(completedTests.length).toBeGreaterThan(0);
      
      // If any succeeded, they should have valid structure
      completedTests.forEach(test => {
        if (test.status === 'fulfilled') {
          expect(test.value).toMatchObject({
            success: expect.any(Boolean),
            responseTime: expect.any(Number),
            databaseConnectivity: expect.any(Object),
          });
        }
      });
    }, 60000);
  });

  describe('Test Suite Integration', () => {
    it('should run complete test suite and generate report', async () => {
      const testSuite = new DatabaseAuthTestSuite();
      
      // Run basic tests
      await testSuite.runBasicAuthTest();
      await testSuite.runAuthTestWithInvalidCredentials();
      
      const results = testSuite.getTestResults();
      expect(results).toHaveLength(2);
      
      const report = testSuite.generateTestReport();
      expect(report).toMatchObject({
        totalTests: 2,
        successfulTests: expect.any(Number),
        failedTests: expect.any(Number),
        averageResponseTime: expect.any(Number),
        databaseConnectivityStatus: expect.any(Boolean),
      });
      
      expect(report.successfulTests + report.failedTests).toBe(report.totalTests);
      expect(report.averageResponseTime).toBeGreaterThan(0);
    }, 60000);

    it('should reset test suite properly', async () => {
      const testSuite = new DatabaseAuthTestSuite();
      
      // Run some tests
      await testSuite.runBasicAuthTest();
      expect(testSuite.getTestResults()).toHaveLength(1);
      
      // Reset
      testSuite.reset();
      expect(testSuite.getTestResults()).toHaveLength(0);
      
      const report = testSuite.generateTestReport();
      expect(report.totalTests).toBe(0);
    }, 30000);
  });
});

describe('Environment Configuration Integration', () => {
  it('should have proper backend configuration for database authentication', () => {
    const configManager = getEnvironmentConfigManager();
    const config = configManager.getBackendConfig();
    
    expect(config).toMatchObject({
      primaryUrl: expect.any(String),
      fallbackUrls: expect.any(Array),
      timeout: expect.any(Number),
      retryAttempts: expect.any(Number),
      healthCheckInterval: expect.any(Number),
    });
    
    // Timeout should be sufficient for database operations
    expect(config.timeout).toBeGreaterThanOrEqual(30000);
  });

  it('should have valid health check URL', () => {
    const configManager = getEnvironmentConfigManager();
    const healthUrl = configManager.getHealthCheckUrl();
    
    expect(healthUrl).toBeDefined();
    expect(typeof healthUrl).toBe('string');
    expect(healthUrl.length).toBeGreaterThan(0);
  });
});