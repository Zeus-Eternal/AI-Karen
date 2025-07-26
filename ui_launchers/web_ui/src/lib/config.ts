/**
 * Configuration management for AI Karen Web UI
 * Handles environment variables and runtime configuration
 */

export interface WebUIConfig {
  // Backend configuration
  backendUrl: string;
  apiKey?: string;
  apiTimeout: number;
  maxRetries: number;
  retryDelay: number;
  cacheTtl: number;

  // Logging and debugging
  debugLogging: boolean;
  requestLogging: boolean;
  performanceMonitoring: boolean;
  logLevel: 'error' | 'warn' | 'info' | 'debug';

  // Feature flags
  enablePlugins: boolean;
  enableMemory: boolean;
  enableExperimentalFeatures: boolean;
  enableVoice: boolean;
  enableExtensions: boolean;

  // Health checks
  healthCheckInterval: number;
  healthCheckTimeout: number;
  enableHealthChecks: boolean;

  // CORS configuration
  corsOrigins: string[];

  // Performance
  enableServiceWorker: boolean;
}

/**
 * Parse boolean environment variable with default fallback
 */
function parseBooleanEnv(value: string | undefined, defaultValue: boolean): boolean {
  if (!value) return defaultValue;
  return value.toLowerCase() === 'true';
}

/**
 * Parse number environment variable with default fallback
 */
function parseNumberEnv(value: string | undefined, defaultValue: number): number {
  if (!value) return defaultValue;
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? defaultValue : parsed;
}

/**
 * Parse array environment variable (comma-separated) with default fallback
 */
function parseArrayEnv(value: string | undefined, defaultValue: string[]): string[] {
  if (!value) return defaultValue;
  return value.split(',').map(item => item.trim()).filter(Boolean);
}

/**
 * Get the current web UI configuration from environment variables
 */
export function getWebUIConfig(): WebUIConfig {
  return {
    // Backend configuration
    backendUrl: process.env.KAREN_BACKEND_URL || 'http://localhost:8000',
    apiKey: process.env.KAREN_API_KEY,
    apiTimeout: parseNumberEnv(process.env.KAREN_API_TIMEOUT, 30000),
    maxRetries: parseNumberEnv(process.env.KAREN_API_MAX_RETRIES, 3),
    retryDelay: parseNumberEnv(process.env.KAREN_API_RETRY_DELAY, 1000),
    cacheTtl: parseNumberEnv(process.env.KAREN_API_CACHE_TTL, 300000),

    // Logging and debugging
    debugLogging: parseBooleanEnv(process.env.KAREN_DEBUG_LOGGING, false),
    requestLogging: parseBooleanEnv(process.env.KAREN_ENABLE_REQUEST_LOGGING, false),
    performanceMonitoring: parseBooleanEnv(process.env.KAREN_ENABLE_PERFORMANCE_MONITORING, false),
    logLevel: (process.env.KAREN_LOG_LEVEL as 'error' | 'warn' | 'info' | 'debug') || 'info',

    // Feature flags
    enablePlugins: parseBooleanEnv(process.env.KAREN_ENABLE_PLUGINS, true),
    enableMemory: parseBooleanEnv(process.env.KAREN_ENABLE_MEMORY, true),
    enableExperimentalFeatures: parseBooleanEnv(process.env.KAREN_ENABLE_EXPERIMENTAL_FEATURES, false),
    enableVoice: parseBooleanEnv(process.env.KAREN_ENABLE_VOICE, false),
    enableExtensions: parseBooleanEnv(process.env.KAREN_ENABLE_EXTENSIONS, false),

    // Health checks
    healthCheckInterval: parseNumberEnv(process.env.KAREN_HEALTH_CHECK_INTERVAL, 30000),
    healthCheckTimeout: parseNumberEnv(process.env.KAREN_HEALTH_CHECK_TIMEOUT, 5000),
    enableHealthChecks: parseBooleanEnv(process.env.KAREN_ENABLE_HEALTH_CHECKS, true),

    // CORS configuration
    corsOrigins: parseArrayEnv(process.env.KAREN_CORS_ORIGINS, ['http://localhost:9002']),

    // Performance
    enableServiceWorker: parseBooleanEnv(process.env.KAREN_ENABLE_SERVICE_WORKER, false),
  };
}

/**
 * Validate configuration and log warnings for potential issues
 */
export function validateConfig(config: WebUIConfig): { isValid: boolean; warnings: string[] } {
  const warnings: string[] = [];
  let isValid = true;

  // Validate backend URL
  try {
    new URL(config.backendUrl);
  } catch {
    warnings.push(`Invalid backend URL: ${config.backendUrl}`);
    isValid = false;
  }

  // Validate timeout values
  if (config.apiTimeout < 1000) {
    warnings.push(`API timeout is very low (${config.apiTimeout}ms), consider increasing it`);
  }

  if (config.apiTimeout > 120000) {
    warnings.push(`API timeout is very high (${config.apiTimeout}ms), consider reducing it`);
  }

  // Validate retry configuration
  if (config.maxRetries > 10) {
    warnings.push(`Max retries is very high (${config.maxRetries}), this may cause long delays`);
  }

  if (config.retryDelay < 100) {
    warnings.push(`Retry delay is very low (${config.retryDelay}ms), this may overwhelm the server`);
  }

  // Validate health check configuration
  if (config.enableHealthChecks) {
    if (config.healthCheckInterval < 5000) {
      warnings.push(`Health check interval is very low (${config.healthCheckInterval}ms), this may impact performance`);
    }

    if (config.healthCheckTimeout > config.healthCheckInterval) {
      warnings.push(`Health check timeout (${config.healthCheckTimeout}ms) is greater than interval (${config.healthCheckInterval}ms)`);
    }
  }

  // Validate CORS origins
  for (const origin of config.corsOrigins) {
    if (origin !== '*') {
      try {
        new URL(origin);
      } catch {
        warnings.push(`Invalid CORS origin: ${origin}`);
      }
    }
  }

  return { isValid, warnings };
}

/**
 * Log configuration information (for debugging)
 */
export function logConfigInfo(config: WebUIConfig): void {
  if (!config.debugLogging) return;

  console.group('🔧 AI Karen Web UI Configuration');
  console.log('Backend URL:', config.backendUrl);
  console.log('API Timeout:', `${config.apiTimeout}ms`);
  console.log('Max Retries:', config.maxRetries);
  console.log('Cache TTL:', `${config.cacheTtl}ms`);
  console.log('Debug Logging:', config.debugLogging);
  console.log('Request Logging:', config.requestLogging);
  console.log('Performance Monitoring:', config.performanceMonitoring);
  console.log('Log Level:', config.logLevel);
  console.log('Features:', {
    plugins: config.enablePlugins,
    memory: config.enableMemory,
    experimental: config.enableExperimentalFeatures,
    voice: config.enableVoice,
    extensions: config.enableExtensions,
  });
  console.log('Health Checks:', {
    enabled: config.enableHealthChecks,
    interval: `${config.healthCheckInterval}ms`,
    timeout: `${config.healthCheckTimeout}ms`,
  });
  console.log('CORS Origins:', config.corsOrigins);
  console.groupEnd();

  // Validate and show warnings
  const { warnings } = validateConfig(config);
  if (warnings.length > 0) {
    console.group('⚠️ Configuration Warnings');
    warnings.forEach(warning => console.warn(warning));
    console.groupEnd();
  }
}

/**
 * Get runtime environment information
 */
export function getRuntimeInfo() {
  return {
    nodeEnv: process.env.NODE_ENV || 'development',
    isDevelopment: process.env.NODE_ENV === 'development',
    isProduction: process.env.NODE_ENV === 'production',
    port: process.env.PORT || '9002',
    timestamp: new Date().toISOString(),
    userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'server',
    url: typeof window !== 'undefined' ? window.location.href : 'server',
  };
}

// Export singleton config instance
export const webUIConfig = getWebUIConfig();

// Validate and log configuration on module load
if (typeof window !== 'undefined') {
  // Only run in browser environment
  const { isValid, warnings } = validateConfig(webUIConfig);
  
  if (!isValid) {
    console.error('❌ Invalid AI Karen Web UI configuration detected!');
    warnings.forEach(warning => console.error(`  - ${warning}`));
  }
  
  logConfigInfo(webUIConfig);
}