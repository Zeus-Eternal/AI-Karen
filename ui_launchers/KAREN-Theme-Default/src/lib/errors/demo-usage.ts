// ui_launchers/KAREN-Theme-Default/src/lib/errors/demo-usage.ts
/**
 * Demo usage examples for the comprehensive error handling system
 * Requirements: 1.3, 2.3, 3.3, 4.3
 */
import { handleError, withErrorHandling, withRetry } from './index';
/**
 * Example 1: Basic error handling with categorization
 */
export async function basicErrorHandlingExample() {
  return handleError(new Error('ECONNREFUSED: Connection refused'), {
    enableRecovery: true,
    enableLogging: true,
    context: { operation: 'api-call', endpoint: '/api/users' }
  });
}
/**
 * Example 2: Automatic retry with error handling
 */
export async function retryExample() {
  let attemptCount = 0;
  const unstableOperation = async () => {
    attemptCount++;
    if (attemptCount < 3) {
      throw new Error('ETIMEDOUT: Network timeout');
    }
    return { success: true, data: 'Operation completed' };
  };
  return withRetry(unstableOperation, {
    maxRetryAttempts: 5,
    context: { operation: 'data-fetch' }
  });
}
/**
 * Example 3: Function wrapper with error handling
 */
export const authenticatedApiCall = withErrorHandling(async (endpoint: string, data?: unknown) => {
  // Simulate authentication check
  const isAuthenticated = Math.random() > 0.3;
  if (!isAuthenticated) {
    throw new Error('Session expired - please log in again');
  }
  // Simulate network call
  const networkSuccess = Math.random() > 0.2;
  if (!networkSuccess) {
    throw new Error('ECONNREFUSED: Connection refused');
  }
  return {
    success: true,
    endpoint,
    data: data || 'API response data'
  };
}, {
  maxRetryAttempts: 3,
  enableRecovery: true,
  context: { type: 'authenticated-api-call' }
});
/**
 * Example 4: Database operation with error handling
 */
export const databaseOperation = withErrorHandling(async (query: string) => {
  // Simulate database connection issues
  const connectionSuccess = Math.random() > 0.4;
  if (!connectionSuccess) {
    throw new Error('Database connection pool exhausted');
  }
  // Simulate query execution
  const querySuccess = Math.random() > 0.1;
  if (!querySuccess) {
    throw new Error('Query timeout after 30 seconds');
  }
  return {
    success: true,
    query,
    results: ['row1', 'row2', 'row3']
  };
}, {
  maxRetryAttempts: 5,
  enableRecovery: true,
  context: { type: 'database-operation' }
});
/**
 * Example 5: Configuration validation with error handling
 */
export async function validateConfiguration(config: Record<string, unknown>) {
  try {
    if (!config.backendUrl) {
      throw new Error('Invalid backend URL configuration');
    }
    if (!config.apiKey) {
      throw new Error('Missing environment variable: API_KEY');
    }
    try {
      new URL(config.backendUrl as string);
    } catch {
      throw new Error('Invalid URL format in configuration');
    }
    return { valid: true, config };
  } catch (error) {
    await handleError(error as Error, {
      enableRecovery: false,
      context: { operation: 'config-validation', config }
    });
    throw error;
  }
}
/**
 * Example 6: Comprehensive error handling in a service class
 */
export class UserService {
  private handleServiceError = withErrorHandling.bind(null);
  async getUser(userId: string) {
    return this.handleServiceError(async () => {
      // Simulate validation
      if (!userId) {
        throw new Error('Validation error: User ID is required');
      }
      // Simulate database call
      const dbResult = await databaseOperation(`SELECT * FROM users WHERE id = ${userId}`);
      // Simulate API call for additional data
      const apiResult = await authenticatedApiCall(`/api/users/${userId}/profile`);
      return {
        user: dbResult.results[0],
        profile: apiResult.data
      };
    }, {
      maxRetryAttempts: 3,
      context: { service: 'UserService', method: 'getUser', userId }
    })();
  }
  async createUser(userData: unknown) {
    return this.handleServiceError(async () => {
      // Type guard for userData
      const { email, name } = userData as {
        email?: string;
        name?: string;
      };
      
      // Simulate validation
      if (!email) {
        throw new Error('Validation error: Email is required');
      }
      if (!email.includes('@')) {
        throw new Error('Validation error: Invalid email format');
      }
      // Simulate database call
      await databaseOperation(
        `INSERT INTO users (email, name) VALUES ('${email}', '${name || 'Unknown'}')`
      );
      return {
        success: true,
        userId: 'new-user-id',
        message: 'User created successfully'
      };
    }, {
      maxRetryAttempts: 2,
      context: { service: 'UserService', method: 'createUser', userData }
    })();
  }
}
/**
 * Example usage of all the above
 */
export async function demonstrateErrorHandling() {
  // Example 1: Basic error handling
  try {
    await basicErrorHandlingExample();
  } catch (error) {
    console.error('Error handling example failed', error);
  }
  // Example 2: Retry logic
  try {
    await retryExample();
  } catch (error) {
    console.error('Retry logic failed', error);
  }
  // Example 3: Authenticated API call
  try {
    await authenticatedApiCall('/api/data');
  } catch (error) {
    console.error('API call failed', error);
  }
  // Example 4: Database operation
  try {
    await databaseOperation('SELECT * FROM users');
  } catch (error) {
    console.error('Database operation failed', error);
  }
  // Example 5: Configuration validation
  try {
    await validateConfiguration({ backendUrl: 'invalid-url' });
  } catch (error) {
    console.error('Configuration validation failed', error);
  }
  // Example 6: Service class usage
  const userService = new UserService();
  try {
    await userService.getUser('123');
  } catch (error) {
    console.error('Service method failed', error);
  }
}
