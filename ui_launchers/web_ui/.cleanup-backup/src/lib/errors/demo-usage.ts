/**
 * Demo usage examples for the comprehensive error handling system
 * Requirements: 1.3, 2.3, 3.3, 4.3
 */

import { 
  handleError, 
  withErrorHandling, 
  withRetry,
  ErrorCategory,
  ErrorSeverity 
} from './index';

/**
 * Example 1: Basic error handling with categorization
 */
export async function basicErrorHandlingExample() {
  try {
    // Simulate a network error
    throw new Error('ECONNREFUSED: Connection refused');
  } catch (error) {
    const result = await handleError(error as Error, {
      enableRecovery: true,
      enableLogging: true,
      context: { operation: 'api-call', endpoint: '/api/users' }
    });

    console.log('Error Category:', result.categorizedError.category);
    console.log('User Message:', result.userMessage);
    console.log('Should Retry:', result.shouldRetry);
    console.log('Recovery Action:', result.recoveryResult?.actionTaken);

    return result;
  }
}

/**
 * Example 2: Automatic retry with error handling
 */
export async function retryExample() {
  let attemptCount = 0;
  
  const unstableOperation = async () => {
    attemptCount++;
    console.log(`Attempt ${attemptCount}`);
    
    if (attemptCount < 3) {
      throw new Error('ETIMEDOUT: Network timeout');
    }
    
    return { success: true, data: 'Operation completed' };
  };

  try {
    const result = await withRetry(unstableOperation, {
      maxRetryAttempts: 5,
      context: { operation: 'data-fetch' }
    });
    
    console.log('Success after retries:', result);
    return result;
  } catch (error) {
    console.log('Failed after all retries:', error);
    throw error;
  }
}

/**
 * Example 3: Function wrapper with error handling
 */
export const authenticatedApiCall = withErrorHandling(async (endpoint: string, data?: any) => {
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
export async function validateConfiguration(config: any) {
  try {
    if (!config.backendUrl) {
      throw new Error('Invalid backend URL configuration');
    }
    
    if (!config.apiKey) {
      throw new Error('Missing environment variable: API_KEY');
    }
    
    // Simulate URL validation
    try {
      new URL(config.backendUrl);
    } catch {
      throw new Error('Invalid URL format in configuration');
    }
    
    return { valid: true, config };
  } catch (error) {
    const result = await handleError(error as Error, {
      enableRecovery: false, // Configuration errors usually need manual intervention
      context: { operation: 'config-validation', config }
    });
    
    console.log('Configuration Error:', result.userMessage);
    console.log('Requires User Action:', result.requiresUserAction);
    
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
  
  async createUser(userData: any) {
    return this.handleServiceError(async () => {
      // Simulate validation
      if (!userData.email) {
        throw new Error('Validation error: Email is required');
      }
      
      if (!userData.email.includes('@')) {
        throw new Error('Validation error: Invalid email format');
      }
      
      // Simulate database call
      const dbResult = await databaseOperation(`INSERT INTO users (email, name) VALUES ('${userData.email}', '${userData.name}')`);
      
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
  console.log('=== Comprehensive Error Handling Demo ===\n');
  
  // Example 1: Basic error handling
  console.log('1. Basic Error Handling:');
  try {
    await basicErrorHandlingExample();
  } catch (error) {
    console.log('Handled gracefully\n');
  }
  
  // Example 2: Retry logic
  console.log('2. Retry Logic:');
  try {
    await retryExample();
  } catch (error) {
    console.log('Failed after retries\n');
  }
  
  // Example 3: Authenticated API call
  console.log('3. Authenticated API Call:');
  try {
    const result = await authenticatedApiCall('/api/data');
    console.log('API Success:', result);
  } catch (error) {
    console.log('API Failed:', error);
  }
  console.log();
  
  // Example 4: Database operation
  console.log('4. Database Operation:');
  try {
    const result = await databaseOperation('SELECT * FROM users');
    console.log('DB Success:', result);
  } catch (error) {
    console.log('DB Failed:', error);
  }
  console.log();
  
  // Example 5: Configuration validation
  console.log('5. Configuration Validation:');
  try {
    await validateConfiguration({ backendUrl: 'invalid-url' });
  } catch (error) {
    console.log('Config validation failed as expected\n');
  }
  
  // Example 6: Service class usage
  console.log('6. Service Class Usage:');
  const userService = new UserService();
  try {
    const user = await userService.getUser('123');
    console.log('User Service Success:', user);
  } catch (error) {
    console.log('User Service Failed:', error);
  }
  
  console.log('\n=== Demo Complete ===');
}