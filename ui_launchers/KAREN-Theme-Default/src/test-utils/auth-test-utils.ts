/**
 * Authentication Test Utilities (Prod-Grade)
 * -----------------------------------------
 * Utilities for testing authentication and DB connectivity using
 * admin@example.com / password123 and friends.
 *
 * - Clean typings
 * - Timeouts + retries delegated to Timeout/Connection managers
 * - Useful categorization + human messages
 * - Zero side effects at import
 */

import { getConnectionManager } from '@/lib/connection/connection-manager';
import { getTimeoutManager, OperationType } from '@/lib/connection/timeout-manager';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

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

/** Expected shape from ConnectionManager.makeRequest */
interface MakeRequestSuccess<T = any> {
  data: T;
  retryCount?: number;
  status?: number;
}

// ---------------------------------------------------------------------------
// Defaults
// ---------------------------------------------------------------------------

export const TEST_CREDENTIALS: TestCredentials = {
  email: 'admin@example.com',
  password: 'password123',
};

// ---------------------------------------------------------------------------
// Connectivity
// ---------------------------------------------------------------------------

/**
 * Test database connectivity by attempting to validate session
 */
export async function testDatabaseConnectivity(): Promise<DatabaseConnectivityResult> {
  const startTime = Date.now();
  const connectionManager = getConnectionManager();
  const timeoutManager = getTimeoutManager();

  try {
    await connectionManager.makeRequest(
      '/api/auth/validate-session',
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        credentials: 'include',
      },
      {
        timeout: timeoutManager.getTimeout(OperationType.SESSION_VALIDATION),
        retryAttempts: 1,
        exponentialBackoff: false,
      },
    );

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
      error: error?.message || 'Database connectivity test failed',
      timestamp: new Date(),
    };
  }
}

// ---------------------------------------------------------------------------
// Authentication
// ---------------------------------------------------------------------------

/**
 * Test authentication with admin@example.com/password123 credentials
 */
export async function testDatabaseAuthentication(
  credentials: TestCredentials = TEST_CREDENTIALS,
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
      ...(credentials.totp_code ? { totp_code: credentials.totp_code } : {}),
    };

    const result = (await connectionManager.makeRequest(
      '/api/auth/login',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(requestBody),
        credentials: 'include',
      },
      {
        timeout: timeoutManager.getTimeout(OperationType.AUTHENTICATION),
        retryAttempts: 2,
        exponentialBackoff: true,
      },
    )) as MakeRequestSuccess;

    const responseTime = Date.now() - startTime;
    const userData = (result?.data as any)?.user || (result?.data as any)?.user_data;

    if (!userData) {
      return {
        success: false,
        error: 'No user data in authentication response',
        responseTime,
        retryCount: result?.retryCount ?? 0,
        databaseConnectivity,
      };
    }

    return {
      success: true,
      user: {
        user_id: String(userData.user_id),
        email: String(userData.email),
        roles: Array.isArray(userData.roles) ? userData.roles : [],
        tenant_id: String(userData.tenant_id ?? ''),
        role: String(userData.role ?? determineUserRole(Array.isArray(userData.roles) ? userData.roles : [])),
      },
      responseTime,
      retryCount: result?.retryCount ?? 0,
      databaseConnectivity,
    };
  } catch (error: any) {
    const responseTime = Date.now() - startTime;
    return {
      success: false,
      error: error?.message || 'Authentication test failed',
      responseTime,
      retryCount: error?.retryCount || 0,
      databaseConnectivity,
    };
  }
}

// ---------------------------------------------------------------------------
// Categorized auth + friendly messages
// ---------------------------------------------------------------------------

export async function testAuthenticationWithDatabaseValidation(
  credentials: TestCredentials = TEST_CREDENTIALS,
): Promise<AuthenticationTestResult & { errorCategory?: string }> {
  const result = await testDatabaseAuthentication(credentials);

  if (!result.success && result.error) {
    let errorCategory: 'network' | 'timeout' | 'database' | 'credentials' | 'unknown' = 'unknown';
    const msg = result.error.toLowerCase();

    if (msg.includes('network') || msg.includes('connection') || msg.includes('fetch failed')) {
      errorCategory = 'network';
    } else if (msg.includes('timeout') || msg.includes('timed out')) {
      errorCategory = 'timeout';
    } else if (msg.includes('database')) {
      errorCategory = 'database';
    } else if (msg.includes('401') || msg.includes('unauthorized') || msg.includes('invalid credentials')) {
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

function determineUserRole(roles: string[]): string {
  if (roles.includes('super_admin')) return 'super_admin';
  if (roles.includes('admin')) return 'admin';
  return 'user';
}

// ---------------------------------------------------------------------------
// Validation helpers
// ---------------------------------------------------------------------------

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
    }
    return {
      valid: false,
      message: `Test credentials validation failed: ${result.error}`,
      details: result,
    };
  } catch (error: any) {
    return {
      valid: false,
      message: `Test credentials validation error: ${error?.message ?? 'Unknown error'}`,
    };
  }
}

// ---------------------------------------------------------------------------
// Session helpers
// ---------------------------------------------------------------------------

export async function createTestSession(
  credentials: TestCredentials = TEST_CREDENTIALS,
): Promise<{
  success: boolean;
  sessionData?: any;
  error?: string;
}> {
  try {
    const authResult = await testDatabaseAuthentication(credentials);
    if (authResult.success && authResult.user) {
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
    }
    return {
      success: false,
      error: authResult.error || 'Failed to create test session',
    };
  } catch (error: any) {
    return {
      success: false,
      error: error?.message || 'Test session creation failed',
    };
  }
}

export async function cleanupTestSession(): Promise<void> {
  const connectionManager = getConnectionManager();
  try {
    await connectionManager.makeRequest(
      '/api/auth/logout',
      {
        method: 'POST',
        credentials: 'include',
      },
      {
        timeout: 5000,
        retryAttempts: 1,
        exponentialBackoff: false,
      },
    );
  } catch {
    // swallow cleanup errors
  }
}

// ---------------------------------------------------------------------------
// Suite
// ---------------------------------------------------------------------------

export class DatabaseAuthTestSuite {
  private testResults: AuthenticationTestResult[] = [];

  async runBasicAuthTest(): Promise<AuthenticationTestResult> {
    const result = await testDatabaseAuthentication();
    this.testResults.push(result);
    return result;
  }

  async runAuthTestWithInvalidCredentials(): Promise<AuthenticationTestResult> {
    const invalidCredentials: TestCredentials = {
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
    const successfulTests = this.testResults.filter((r) => r.success).length;
    const failedTests = totalTests - successfulTests;
    const averageResponseTime =
      totalTests > 0
        ? this.testResults.reduce((sum, r) => sum + r.responseTime, 0) / totalTests
        : 0;
    const databaseConnectivityStatus =
      this.testResults.length > 0
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

// ---------------------------------------------------------------------------
// Vitest helpers (optional)
// ---------------------------------------------------------------------------

export function summarizeAuth(result: AuthenticationTestResult): string {
  if (result.success) {
    return `SUCCESS in ${result.responseTime}ms (retries: ${result.retryCount}) → ${result.user?.email} [${result.user?.role}]`;
  }
  return `FAIL in ${result.responseTime}ms (retries: ${result.retryCount}) → ${result.error}`;
}
