/**
 * Authentication Test Utilities
 * 
 * Provides utilities for testing authentication with admin@example.com/password123 credentials
 * and database connectivity validation.
 * 
 * Requirements: 4.1, 4.2, 4.3
 */
import { getConnectionManager } from '@/lib/connection/connection-manager';
import { getTimeoutManager, OperationType } from '@/lib/connection/timeout-manager';
export interface TestCredentials {
  email: string;
  password: string;
  totp_code?: string;
}
export interface DatabaseConnectivityResult {
  isConnected: boolean;
  responseTime: number;
  error?: string;
  timestamp: Date;
}
export interface AuthenticationTestResult {
  success: boolean;
  user?: {
    user_id: string;
    email: string;
    roles: string[];
    tenant_id: string;
    role: string;
  };
  error?: string;
  responseTime: number;
  retryCount: number;
  databaseConnectivity: DatabaseConnectivityResult;
}
/**
 * Default test credentials for database authentication testing
 */
export const TEST_CREDENTIALS: TestCredentials = {
  email: 'admin@example.com',
  password: 'password123',
};
/**
 * Test database connectivity by attempting to validate session
 */
export async function testDatabaseConnectivity(): Promise<DatabaseConnectivityResult> {
  const startTime = Date.now();
  const connectionManager = getConnectionManager();
  const timeoutManager = getTimeoutManager();
  try {
    const result = await connectionManager.makeRequest('/api/auth/validate-session', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      credentials: 'include',
    }, {
      timeout: timeoutManager.getTimeout(OperationType.SESSION_VALIDATION),
      retryAttempts: 1,
      exponentialBackoff: false,

    const responseTime = Date.now() - startTime;
    return {
      isConnected: true,
      responseTime,
      timestamp: new Date(),
    };
  } catch (error: any) {
    const responseTime = Date.now() - startTime;
    return {
      isConnected: false,
      responseTime,
      error: error.message || 'Database connectivity test failed',
      timestamp: new Date(),
    };
  }
}
/**
 * Test authentication with admin@example.com/password123 credentials
 */
export async function testDatabaseAuthentication(
  credentials: TestCredentials = TEST_CREDENTIALS
): Promise<AuthenticationTestResult> {
  const connectionManager = getConnectionManager();
  const timeoutManager = getTimeoutManager();
  const startTime = Date.now();
  // First test database connectivity
  const databaseConnectivity = await testDatabaseConnectivity();
  try {
    const requestBody = {
      email: credentials.email,
      password: credentials.password,
      ...(credentials.totp_code && { totp_code: credentials.totp_code })
    };
    const result = await connectionManager.makeRequest('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(requestBody),
      credentials: 'include',
    }, {
      timeout: timeoutManager.getTimeout(OperationType.AUTHENTICATION),
      retryAttempts: 2,
      exponentialBackoff: true,

    const responseTime = Date.now() - startTime;
    const userData = result.data.user || result.data.user_data;
    if (!userData) {
      return {
        success: false,
        error: 'No user data in authentication response',
        responseTime,
        retryCount: result.retryCount,
        databaseConnectivity,
      };
    }
    return {
      success: true,
      user: {
        user_id: userData.user_id,
        email: userData.email,
        roles: userData.roles || [],
        tenant_id: userData.tenant_id,
        role: userData.role || determineUserRole(userData.roles || []),
      },
      responseTime,
      retryCount: result.retryCount,
      databaseConnectivity,
    };
  } catch (error: any) {
    const responseTime = Date.now() - startTime;
    return {
      success: false,
      error: error.message || 'Authentication test failed',
      responseTime,
      retryCount: error.retryCount || 0,
      databaseConnectivity,
    };
  }
}
/**
 * Test authentication flow with proper error messages for database connection failures
 */
export async function testAuthenticationWithDatabaseValidation(
  credentials: TestCredentials = TEST_CREDENTIALS
): Promise<AuthenticationTestResult & { errorCategory?: string }> {
  const result = await testDatabaseAuthentication(credentials);
  // Add enhanced error categorization
  if (!result.success && result.error) {
    let errorCategory = 'unknown';
    if (result.error.includes('network') || result.error.includes('connection')) {
      errorCategory = 'network';
    } else if (result.error.includes('timeout')) {
      errorCategory = 'timeout';
    } else if (result.error.includes('database') || result.error.includes('Database')) {
      errorCategory = 'database';
    } else if (result.error.includes('401') || result.error.includes('Unauthorized')) {
      errorCategory = 'credentials';
    }
    return {
      ...result,
      errorCategory,
      error: getDatabaseAuthErrorMessage(result.error, errorCategory),
    };
  }
  return result;
}
/**
 * Get user-friendly error messages for database authentication failures
 */
function getDatabaseAuthErrorMessage(originalError: string, category: string): string {
  switch (category) {
    case 'network':
      return 'Unable to connect to authentication database. Please check your network connection.';
    case 'timeout':
      return 'Database authentication is taking longer than expected. Please try again.';
    case 'database':
      return 'Authentication database is temporarily unavailable. Please try again later.';
    case 'credentials':
      return 'Invalid credentials. Please verify your email and password.';
    default:
      return `Authentication failed: ${originalError}`;
  }
}
/**
 * Helper function to determine primary role from roles array
 */
function determineUserRole(roles: string[]): string {
  if (roles.includes('super_admin')) return 'super_admin';
  if (roles.includes('admin')) return 'admin';
  return 'user';
}
/**
 * Validate that test credentials work with the actual database
 */
export async function validateTestCredentials(): Promise<{
  valid: boolean;
  message: string;
  details?: AuthenticationTestResult;
}> {
  try {
    const result = await testAuthenticationWithDatabaseValidation();
    if (result.success) {
      return {
        valid: true,
        message: `Test credentials validated successfully. User: ${result.user?.email}, Role: ${result.user?.role}`,
        details: result,
      };
    } else {
      return {
        valid: false,
        message: `Test credentials validation failed: ${result.error}`,
        details: result,
      };
    }
  } catch (error: any) {
    return {
      valid: false,
      message: `Test credentials validation error: ${error.message}`,
    };
  }
}
/**
 * Create a test user session for integration testing
 */
export async function createTestSession(
  credentials: TestCredentials = TEST_CREDENTIALS
): Promise<{
  success: boolean;
  sessionData?: any;
  error?: string;
}> {
  try {
    const authResult = await testDatabaseAuthentication(credentials);
    if (authResult.success && authResult.user) {
      // Session should be automatically created by the login process
      return {
        success: true,
        sessionData: {
          userId: authResult.user.user_id,
          email: authResult.user.email,
          roles: authResult.user.roles,
          tenantId: authResult.user.tenant_id,
          role: authResult.user.role,
        },
      };
    } else {
      return {
        success: false,
        error: authResult.error || 'Failed to create test session',
      };
    }
  } catch (error: any) {
    return {
      success: false,
      error: error.message || 'Test session creation failed',
    };
  }
}
/**
 * Clean up test session
 */
export async function cleanupTestSession(): Promise<void> {
  const connectionManager = getConnectionManager();
  try {
    await connectionManager.makeRequest('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    }, {
      timeout: 5000,
      retryAttempts: 1,

  } catch (error) {
    // Ignore cleanup errors
  }
}
/**
 * Test suite helper for database authentication testing
 */
export class DatabaseAuthTestSuite {
  private testResults: AuthenticationTestResult[] = [];
  async runBasicAuthTest(): Promise<AuthenticationTestResult> {
    const result = await testDatabaseAuthentication();
    this.testResults.push(result);
    return result;
  }
  async runAuthTestWithInvalidCredentials(): Promise<AuthenticationTestResult> {
    const invalidCredentials = {
      email: 'invalid@example.com',
      password: 'wrongpassword',
    };
    const result = await testDatabaseAuthentication(invalidCredentials);
    this.testResults.push(result);
    return result;
  }
  async runDatabaseConnectivityTest(): Promise<DatabaseConnectivityResult> {
    return await testDatabaseConnectivity();
  }
  getTestResults(): AuthenticationTestResult[] {
    return [...this.testResults];
  }
  generateTestReport(): {
    totalTests: number;
    successfulTests: number;
    failedTests: number;
    averageResponseTime: number;
    databaseConnectivityStatus: boolean;
  } {
    const totalTests = this.testResults.length;
    const successfulTests = this.testResults.filter(r => r.success).length;
    const failedTests = totalTests - successfulTests;
    const averageResponseTime = totalTests > 0 
      ? this.testResults.reduce((sum, r) => sum + r.responseTime, 0) / totalTests 
      : 0;
    const databaseConnectivityStatus = this.testResults.length > 0 
      ? this.testResults[this.testResults.length - 1].databaseConnectivity.isConnected 
      : false;
    return {
      totalTests,
      successfulTests,
      failedTests,
      averageResponseTime,
      databaseConnectivityStatus,
    };
  }
  reset(): void {
    this.testResults = [];
  }
}
