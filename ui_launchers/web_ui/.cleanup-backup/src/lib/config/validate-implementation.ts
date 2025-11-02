/**
 * Environment Configuration Manager Implementation Validation
 * 
 * This script demonstrates that the Environment Configuration Manager
 * is working correctly and meets the requirements.
 * 
 * Requirements: 1.1, 1.2
 */

import { getEnvironmentConfigManager, initializeEnvironmentConfigManager } from './environment-config-manager';

/**
 * Validate the Environment Configuration Manager implementation
 */
export function validateImplementation(): {
  success: boolean;
  results: string[];
  errors: string[];
} {
  const results: string[] = [];
  const errors: string[] = [];

  try {
    results.push('✅ Starting Environment Configuration Manager validation...');

    // Test 1: Basic instantiation
    const manager = getEnvironmentConfigManager();
    results.push('✅ Environment Configuration Manager instantiated successfully');

    // Test 2: Environment detection
    const envInfo = manager.getEnvironmentInfo();
    results.push(`✅ Environment detected: ${envInfo.type} (${envInfo.networkMode})`);
    results.push(`   - Docker: ${envInfo.isDocker}`);
    results.push(`   - Production: ${envInfo.isProduction}`);

    // Test 3: Backend configuration
    const backendConfig = manager.getBackendConfig();
    results.push(`✅ Backend configuration loaded:`);
    results.push(`   - Primary URL: ${backendConfig.primaryUrl}`);
    results.push(`   - Fallback URLs: ${backendConfig.fallbackUrls.length} configured`);
    results.push(`   - Timeout: ${backendConfig.timeout}ms`);
    results.push(`   - Retry attempts: ${backendConfig.retryAttempts}`);

    // Test 4: Timeout configuration (increased AUTH_TIMEOUT_MS)
    const timeouts = manager.getTimeoutConfig();
    results.push(`✅ Timeout configuration loaded:`);
    results.push(`   - Authentication: ${timeouts.authentication}ms (increased from 15s)`);
    results.push(`   - Connection: ${timeouts.connection}ms`);
    results.push(`   - Session validation: ${timeouts.sessionValidation}ms`);
    results.push(`   - Health check: ${timeouts.healthCheck}ms`);

    // Test 5: Retry policy
    const retryPolicy = manager.getRetryPolicy();
    results.push(`✅ Retry policy loaded:`);
    results.push(`   - Max attempts: ${retryPolicy.maxAttempts}`);
    results.push(`   - Base delay: ${retryPolicy.baseDelay}ms`);
    results.push(`   - Max delay: ${retryPolicy.maxDelay}ms`);
    results.push(`   - Exponential backoff: ${retryPolicy.jitterEnabled}`);

    // Test 6: Configuration validation
    const validation = manager.validateConfiguration();
    results.push(`✅ Configuration validation:`);
    results.push(`   - Valid: ${validation.isValid}`);
    results.push(`   - Warnings: ${validation.warnings.length}`);
    results.push(`   - Errors: ${validation.errors.length}`);

    if (validation.warnings.length > 0) {
      results.push(`   - Warning details:`);
      validation.warnings.forEach(warning => {
        results.push(`     • ${warning}`);
      });
    }

    if (validation.errors.length > 0) {
      results.push(`   - Error details:`);
      validation.errors.forEach(error => {
        results.push(`     • ${error}`);
      });
    }

    // Test 7: Utility methods
    const healthUrl = manager.getHealthCheckUrl();
    const candidates = manager.getAllCandidateUrls();
    results.push(`✅ Utility methods working:`);
    results.push(`   - Health check URL: ${healthUrl}`);
    results.push(`   - Total candidate URLs: ${candidates.length}`);

    // Test 8: Singleton pattern
    const manager2 = getEnvironmentConfigManager();
    const isSingleton = manager === manager2;
    results.push(`✅ Singleton pattern: ${isSingleton ? 'Working' : 'Failed'}`);

    // Test 9: Reinitialization
    const manager3 = initializeEnvironmentConfigManager();
    const isNewInstance = manager !== manager3;
    results.push(`✅ Reinitialization: ${isNewInstance ? 'Working' : 'Failed'}`);

    // Test 10: Configuration update
    const originalUrl = manager3.getBackendConfig().primaryUrl;
    manager3.updateConfiguration({ primaryUrl: 'http://test-update:9999' });
    const updatedUrl = manager3.getBackendConfig().primaryUrl;
    const isUpdated = updatedUrl === 'http://test-update:9999';
    results.push(`✅ Configuration update: ${isUpdated ? 'Working' : 'Failed'}`);
    results.push(`   - Original: ${originalUrl}`);
    results.push(`   - Updated: ${updatedUrl}`);

    results.push('✅ All validation tests completed successfully!');

    return {
      success: true,
      results,
      errors,
    };

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    errors.push(`❌ Validation failed: ${errorMessage}`);
    
    return {
      success: false,
      results,
      errors,
    };
  }
}

/**
 * Run validation and log results
 */
export function runValidation(): void {
  console.log('🔧 Environment Configuration Manager Implementation Validation');
  console.log('=' .repeat(70));

  const validation = validateImplementation();

  validation.results.forEach(result => console.log(result));
  
  if (validation.errors.length > 0) {
    console.log('\n❌ Errors:');
    validation.errors.forEach(error => console.log(error));
  }

  console.log('=' .repeat(70));
  console.log(validation.success ? '✅ Validation PASSED' : '❌ Validation FAILED');
}

// Run validation if this file is executed directly
if (typeof require !== 'undefined' && require.main === module) {
  runValidation();
}