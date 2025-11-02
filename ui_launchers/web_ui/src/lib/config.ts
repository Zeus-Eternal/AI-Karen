/**
 * Configuration management for AI Karen Web UI
 * Handles environment variables and runtime configuration
 */
export interface WebUIConfig {
  // Backend configuration (use Next.js API routes)
  backendUrl: string;
  apiBaseUrl: string;
  karenBackendUrl: string;
  apiKey?: string;
  apiTimeout: number;
  maxRetries: number;
  retryDelay: number;
  cacheTtl: number;
  circuitBreakerThreshold: number;
  circuitBreakerResetTime: number;
  // Environment and network configuration
  environment: 'local' | 'docker' | 'production';
  networkMode: 'localhost' | 'container' | 'external';
  fallbackBackendUrls: string[];
  // Container-specific configuration
  containerBackendHost: string;
  containerBackendPort: string;
  // External configuration
  externalHost: string;
  externalBackendPort: string;
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
  healthCheckRetries: number;
  // CORS configuration
  corsOrigins: string[];
  // Performance
  enableServiceWorker: boolean;
  // Meta bar display options
  showModelBadge: boolean;
  showLatencyBadge: boolean;
  showConfidenceBadge: boolean;
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
 * Parse environment variable with validation against allowed values
 */
function parseEnumEnv<T extends string>(
  value: string | undefined,
  allowedValues: readonly T[],
  defaultValue: T
): T {
  if (!value) return defaultValue;
  const lowerValue = value.toLowerCase() as T;
  return allowedValues.includes(lowerValue) ? lowerValue : defaultValue;
}
/**
 * Parse URL environment variable with validation
 */
function parseUrlEnv(value: string | undefined, defaultValue: string): string {
  if (!value) return defaultValue;
  try {
    new URL(value);
    return value;
  } catch {
    return defaultValue;
  }
}
/**
 * Parse host environment variable (hostname or IP)
 */
function parseHostEnv(value: string | undefined, defaultValue: string): string {
  if (!value) return defaultValue;
  // Basic validation for hostname/IP format
  const hostPattern = /^[a-zA-Z0-9.-]+$/;
  const ipPattern = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
  if (hostPattern.test(value) || ipPattern.test(value)) {
    return value;
  }
  return defaultValue;
}
/**
 * Parse port environment variable with validation
 */
function parsePortEnv(value: string | undefined, defaultValue: string): string {
  if (!value) return defaultValue;
  const port = parseInt(value, 10);
  if (isNaN(port) || port < 1 || port > 65535) {
    return defaultValue;
  }
  return value;
}
/**
 * Get fallback URLs based on primary backend URL and environment
 */
function generateFallbackUrls(primaryUrl: string, environment: string, networkMode: string): string[] {
  const fallbacks: string[] = [];
  try {
    const url = new URL(primaryUrl);
    const port = url.port || '8000';
    // Add localhost variations if not already localhost
    if (url.hostname !== 'localhost') {
      fallbacks.push(`http://localhost:${port}`);
    }
    // Add 127.0.0.1 variation
    if (url.hostname !== '127.0.0.1') {
      fallbacks.push(`http://127.0.0.1:${port}`);
    }
    // Add container networking fallback for Docker environments
    if (environment === 'docker' && !url.hostname.includes('backend')) {
      fallbacks.push(`http://backend:${port}`);
    }
    return fallbacks;
  } catch {
    // If URL parsing fails, return sensible defaults
    return ['http://localhost:8000', 'http://127.0.0.1:8000'];
  }
}
/**
 * Get the current web UI configuration from environment variables
 */
export function getWebUIConfig(): WebUIConfig {
  // Parse basic configuration first
  // Use relative URLs to go through Next.js API routes instead of direct backend calls
  // IMPORTANT: Keep this empty to ensure all requests go through Next.js API routes
  const backendUrl = '';
  const environment = parseEnumEnv(
    process.env.KAREN_ENVIRONMENT,
    ['local', 'docker', 'production'] as const,
    'local'
  );
  const networkMode = parseEnumEnv(
    process.env.KAREN_NETWORK_MODE,
    ['localhost', 'container', 'external'] as const,
    'localhost'
  );
  // When using Next.js API routes (empty backendUrl), no fallbacks are needed
  const explicitFallbacks = parseArrayEnv(process.env.KAREN_FALLBACK_BACKEND_URLS, []);
  const fallbackBackendUrls = backendUrl === '' ? [] : (
    explicitFallbacks.length > 0
      ? explicitFallbacks
      : generateFallbackUrls(backendUrl, environment, networkMode)
  );
  return {
    // Backend configuration
    backendUrl,
    apiBaseUrl: backendUrl, // Same as backendUrl for compatibility
    karenBackendUrl: backendUrl, // Same as backendUrl for compatibility
    apiKey: process.env.KAREN_API_KEY || process.env.NEXT_PUBLIC_KAREN_API_KEY,
    apiTimeout: parseNumberEnv(process.env.KAREN_API_TIMEOUT, 30000),
    maxRetries: parseNumberEnv(process.env.KAREN_API_MAX_RETRIES, 3),
    retryDelay: parseNumberEnv(process.env.KAREN_API_RETRY_DELAY, 1000),
    cacheTtl: parseNumberEnv(process.env.KAREN_API_CACHE_TTL, 300000),
    circuitBreakerThreshold: parseNumberEnv(process.env.KAREN_CB_THRESHOLD, 5),
    circuitBreakerResetTime: parseNumberEnv(process.env.KAREN_CB_RESET_TIME, 30000),
    // Environment and network configuration
    environment,
    networkMode,
    fallbackBackendUrls,
    // Container-specific configuration
    containerBackendHost: parseHostEnv(process.env.KAREN_CONTAINER_BACKEND_HOST, 'backend'),
    containerBackendPort: parsePortEnv(process.env.KAREN_CONTAINER_BACKEND_PORT, '8000'),
    // External configuration
    externalHost: parseHostEnv(process.env.KAREN_EXTERNAL_HOST, ''),
    externalBackendPort: parsePortEnv(process.env.KAREN_EXTERNAL_BACKEND_PORT, '8000'),
    // Logging and debugging
    debugLogging: parseBooleanEnv(process.env.KAREN_DEBUG_LOGGING, false),
    requestLogging: parseBooleanEnv(process.env.KAREN_ENABLE_REQUEST_LOGGING, false),
    performanceMonitoring: parseBooleanEnv(process.env.KAREN_ENABLE_PERFORMANCE_MONITORING, false),
    logLevel: parseEnumEnv(
      process.env.KAREN_LOG_LEVEL,
      ['error', 'warn', 'info', 'debug'] as const,
      'info'
    ),
    // Feature flags
    enablePlugins: parseBooleanEnv(process.env.KAREN_ENABLE_PLUGINS, true),
    enableMemory: parseBooleanEnv(process.env.KAREN_ENABLE_MEMORY, true),
    enableExperimentalFeatures: parseBooleanEnv(process.env.KAREN_ENABLE_EXPERIMENTAL_FEATURES, false),
    enableVoice: parseBooleanEnv(process.env.KAREN_ENABLE_VOICE, false),
    enableExtensions: parseBooleanEnv(process.env.KAREN_ENABLE_EXTENSIONS, false),
    // Health checks
    healthCheckInterval: parseNumberEnv(process.env.KAREN_HEALTH_CHECK_INTERVAL, 60000), // Increased to 60 seconds to avoid rate limiting
    healthCheckTimeout: parseNumberEnv(process.env.KAREN_HEALTH_CHECK_TIMEOUT, 5000),
    enableHealthChecks: parseBooleanEnv(process.env.KAREN_ENABLE_HEALTH_CHECKS, true),
    healthCheckRetries: parseNumberEnv(process.env.KAREN_HEALTH_CHECK_RETRIES, 3),
    // CORS configuration
    corsOrigins: parseArrayEnv(process.env.KARI_CORS_ORIGINS, ['http://localhost:8010','http://localhost:8020']),
    // Performance
    enableServiceWorker: parseBooleanEnv(process.env.KAREN_ENABLE_SERVICE_WORKER, false),
    // Meta bar display options
    showModelBadge: parseBooleanEnv(process.env.NEXT_PUBLIC_SHOW_MODEL_BADGE, true),
    showLatencyBadge: parseBooleanEnv(process.env.NEXT_PUBLIC_SHOW_LATENCY_BADGE, true),
    showConfidenceBadge: parseBooleanEnv(process.env.NEXT_PUBLIC_SHOW_CONFIDENCE_BADGE, true),
  };
}
/**
 * Validate configuration and log warnings for potential issues
 */
export function validateConfig(config: WebUIConfig): { isValid: boolean; warnings: string[] } {
  const warnings: string[] = [];
  let isValid = true;
  // Validate backend URL (empty string is valid for Next.js API routes)
  if (config.backendUrl !== '') {
    try {
      new URL(config.backendUrl);
    } catch {
      warnings.push(`Invalid backend URL: ${config.backendUrl}`);
      isValid = false;
    }
  }
  // Validate fallback URLs
  for (const [index, url] of config.fallbackBackendUrls.entries()) {
    try {
      new URL(url);
    } catch {
      warnings.push(`Invalid fallback backend URL[${index}]: ${url}`);
      isValid = false;
    }
  }
  // Validate environment and network mode consistency
  if (config.environment === 'docker' && config.networkMode === 'localhost') {
    warnings.push('Docker environment with localhost network mode may cause connectivity issues');
  }
  if (config.networkMode === 'external' && !config.externalHost) {
    warnings.push('External network mode specified but no external host configured');
  }
  if (config.networkMode === 'container' && !config.containerBackendHost) {
    warnings.push('Container network mode specified but no container backend host configured');
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
    if (config.healthCheckRetries > 10) {
      warnings.push(`Health check retries is very high (${config.healthCheckRetries}), this may cause delays`);
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
  // Validate port numbers
  const containerPort = parseInt(config.containerBackendPort, 10);
  if (isNaN(containerPort) || containerPort < 1 || containerPort > 65535) {
    warnings.push(`Invalid container backend port: ${config.containerBackendPort}`);
  }
  const externalPort = parseInt(config.externalBackendPort, 10);
  if (isNaN(externalPort) || externalPort < 1 || externalPort > 65535) {
    warnings.push(`Invalid external backend port: ${config.externalBackendPort}`);
  }
  return { isValid, warnings };
}
/**
 * Log configuration information (for debugging)
 */
export function logConfigInfo(config: WebUIConfig): void {
  if (!config.debugLogging) return;
  console.group('🔧 AI Karen Web UI Configuration');
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
    port: process.env.PORT || '8010',
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
    warnings.forEach(warning => console.error(`  - ${warning}`));
  }
  logConfigInfo(webUIConfig);
}
