/**
 * Unit tests for Environment Configuration Manager
 * 
 * Tests configuration validation, environment detection, and URL generation
 * Requirements: 1.1, 1.2
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { EnvironmentConfigManager, getEnvironmentConfigManager, initializeEnvironmentConfigManager, type BackendConfig, type EnvironmentInfo, type ValidationResult } from '../environment-config-manager';

// Mock environment variables
const mockEnv = (env: Record<string, string>) => {
  const originalEnv = process.env;
  process.env = { ...originalEnv, ...env };
  return () => {
    process.env = originalEnv;
  };
};

// Mock window object for browser environment tests
const mockWindow = (location: Partial<Location>) => {
  const originalWindow = global.window;
  // @ts-ignore
  global.window = {
    location: {
      hostname: 'localhost',
      port: '8010',
      protocol: 'http:',
      href: 'http://localhost:8010',
      ...location,
    },
  };
  return () => {
    global.window = originalWindow;
  };
};

describe('EnvironmentConfigManager', () => {
  let manager: EnvironmentConfigManager;

  beforeEach(() => {
    // Clear any existing singleton
    vi.clearAllMocks();

  afterEach(() => {
    // Clean up environment
    vi.restoreAllMocks();

  describe('Environment Detection', () => {
    it('should detect local development environment', () => {
      const restoreEnv = mockEnv({
        NODE_ENV: 'development',
        KAREN_ENVIRONMENT: '',
        DOCKER_CONTAINER: '',
        HOSTNAME: '',

      manager = new EnvironmentConfigManager();
      const env = manager.getEnvironmentInfo();

      expect(env.type).toBe('local');
      expect(env.networkMode).toBe('localhost');
      expect(env.isDocker).toBe(false);
      expect(env.isProduction).toBe(false);

      restoreEnv();

    it('should detect Docker environment', () => {
      const restoreEnv = mockEnv({
        NODE_ENV: 'development',
        DOCKER_CONTAINER: 'true',
        HOSTNAME: 'docker-container-123',
        KAREN_CONTAINER_MODE: 'true',

      manager = new EnvironmentConfigManager();
      const env = manager.getEnvironmentInfo();

      expect(env.type).toBe('docker');
      expect(env.networkMode).toBe('container');
      expect(env.isDocker).toBe(true);
      expect(env.isProduction).toBe(false);

      restoreEnv();

    it('should detect production environment', () => {
      const restoreEnv = mockEnv({
        NODE_ENV: 'production',
        KAREN_ENVIRONMENT: 'production',

      manager = new EnvironmentConfigManager();
      const env = manager.getEnvironmentInfo();

      expect(env.type).toBe('production');
      expect(env.isProduction).toBe(true);

      restoreEnv();

    it('should detect external access', () => {
      const restoreEnv = mockEnv({
        NODE_ENV: 'development',

      const restoreWindow = mockWindow({
        hostname: '192.168.1.100',
        port: '8010',

      manager = new EnvironmentConfigManager();
      const env = manager.getEnvironmentInfo();

      expect(env.networkMode).toBe('external');
      expect(env.detectedHostname).toBe('192.168.1.100');
      expect(env.detectedPort).toBe('8010');

      restoreEnv();
      restoreWindow();


  describe('Backend Configuration', () => {
    it('should use explicit configuration when provided', () => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'http://custom-backend:9000',
        AUTH_TIMEOUT_MS: '60000',
        MAX_RETRY_ATTEMPTS: '5',

      manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.primaryUrl).toBe('http://custom-backend:9000');
      expect(config.timeout).toBe(60000);
      expect(config.retryAttempts).toBe(5);

      restoreEnv();

    it('should generate localhost URL for local environment', () => {
      const restoreEnv = mockEnv({
        NODE_ENV: 'development',
        // No explicit backend URL

      manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.primaryUrl).toBe('http://localhost:8000');

      restoreEnv();

    it('should generate container URL for Docker environment', () => {
      const restoreEnv = mockEnv({
        DOCKER_CONTAINER: 'true',
        KAREN_CONTAINER_BACKEND_HOST: 'api-service',
        KAREN_CONTAINER_BACKEND_PORT: '8080',

      manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.primaryUrl).toBe('http://api-service:8080');

      restoreEnv();

    it('should generate external URL for external access', () => {
      const restoreEnv = mockEnv({
        KAREN_EXTERNAL_HOST: '192.168.1.100',
        KAREN_EXTERNAL_BACKEND_PORT: '8000',

      const restoreWindow = mockWindow({
        hostname: '192.168.1.100',

      manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.primaryUrl).toBe('http://192.168.1.100:8000');

      restoreEnv();
      restoreWindow();

    it('should use increased authentication timeout', () => {
      const restoreEnv = mockEnv({
        AUTH_TIMEOUT_MS: '45000', // 45 seconds

      manager = new EnvironmentConfigManager();
      const timeouts = manager.getTimeoutConfig();

      expect(timeouts.authentication).toBe(45000);

      restoreEnv();


  describe('Fallback URL Generation', () => {
    it('should generate fallback URLs for localhost primary', () => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'http://localhost:8000',

      manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.fallbackUrls).toContain('http://127.0.0.1:8000');

      restoreEnv();

    it('should generate fallback URLs for custom host', () => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'http://custom-host:9000',

      manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.fallbackUrls).toContain('http://localhost:9000');
      expect(config.fallbackUrls).toContain('http://127.0.0.1:9000');

      restoreEnv();

    it('should include Docker fallbacks in Docker environment', () => {
      const restoreEnv = mockEnv({
        DOCKER_CONTAINER: 'true',
        KAREN_BACKEND_URL: 'http://localhost:8000',

      manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.fallbackUrls).toContain('http://backend:8000');
      expect(config.fallbackUrls).toContain('http://ai-karen-api:8000');
      expect(config.fallbackUrls).toContain('http://host.docker.internal:8000');

      restoreEnv();

    it('should use explicit fallback URLs when provided', () => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'http://primary:8000',
        KAREN_FALLBACK_BACKEND_URLS: 'http://fallback1:8000,http://fallback2:8000',

      manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.fallbackUrls).toContain('http://fallback1:8000');
      expect(config.fallbackUrls).toContain('http://fallback2:8000');

      restoreEnv();


  describe('Configuration Validation', () => {
    it('should validate valid configuration', () => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'http://localhost:8000',
        AUTH_TIMEOUT_MS: '30000',
        MAX_RETRY_ATTEMPTS: '3',

      manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.isValid).toBe(true);
      expect(validation.errors).toHaveLength(0);

      restoreEnv();

    it('should detect invalid primary URL', () => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'invalid-url',

      manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('Invalid primary backend URL: invalid-url');

      restoreEnv();

    it('should detect invalid fallback URLs', () => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'http://localhost:8000',
        KAREN_FALLBACK_BACKEND_URLS: 'invalid-url,http://valid:8000',

      manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.isValid).toBe(false);
      expect(validation.errors.some(error => error.includes('Invalid fallback URL'))).toBe(true);

      restoreEnv();

    it('should warn about very low timeout values', () => {
      const restoreEnv = mockEnv({
        AUTH_TIMEOUT_MS: '500', // Very low timeout

      manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings.some(warning => 
        warning.includes('Authentication timeout is very low')
      )).toBe(true);

      restoreEnv();

    it('should warn about very high timeout values', () => {
      const restoreEnv = mockEnv({
        AUTH_TIMEOUT_MS: '150000', // Very high timeout

      manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings.some(warning => 
        warning.includes('Authentication timeout is very high')
      )).toBe(true);

      restoreEnv();

    it('should warn about high retry attempts', () => {
      const restoreEnv = mockEnv({
        MAX_RETRY_ATTEMPTS: '15', // Very high retry attempts

      manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings.some(warning => 
        warning.includes('Max retry attempts is very high')
      )).toBe(true);

      restoreEnv();

    it('should warn about Docker with localhost network mode', () => {
      const restoreEnv = mockEnv({
        DOCKER_CONTAINER: 'true',
        KAREN_BACKEND_URL: 'http://localhost:8000', // Forces localhost network mode

      manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings.some(warning => 
        warning.includes('Docker environment with localhost network mode')
      )).toBe(true);

      restoreEnv();


  describe('Utility Methods', () => {
    beforeEach(() => {
      const restoreEnv = mockEnv({
        KAREN_BACKEND_URL: 'http://localhost:8000',

      manager = new EnvironmentConfigManager();
      restoreEnv();

    it('should return health check URL', () => {
      const healthUrl = manager.getHealthCheckUrl();
      expect(healthUrl).toBe('http://localhost:8000/api/health');

    it('should return all candidate URLs', () => {
      const candidates = manager.getAllCandidateUrls();
      expect(candidates[0]).toBe('http://localhost:8000'); // Primary URL first
      expect(candidates.length).toBeGreaterThan(1); // Should include fallbacks

    it('should update configuration', () => {
      const newConfig = {
        primaryUrl: 'http://updated:9000',
        timeout: 60000,
      };

      manager.updateConfiguration(newConfig);
      const config = manager.getBackendConfig();

      expect(config.primaryUrl).toBe('http://updated:9000');
      expect(config.timeout).toBe(60000);

    it('should clear validation cache', () => {
      // First validation to populate cache
      manager.validateConfiguration();
      
      // Clear cache
      manager.clearValidationCache();
      
      // This should work without throwing
      expect(() => manager.clearValidationCache()).not.toThrow();


  describe('Singleton Pattern', () => {
    it('should return same instance from getEnvironmentConfigManager', () => {
      const instance1 = getEnvironmentConfigManager();
      const instance2 = getEnvironmentConfigManager();
      
      expect(instance1).toBe(instance2);

    it('should create new instance from initializeEnvironmentConfigManager', () => {
      const instance1 = getEnvironmentConfigManager();
      const instance2 = initializeEnvironmentConfigManager();
      
      expect(instance1).not.toBe(instance2);


  describe('Retry Policy Configuration', () => {
    it('should load default retry policy', () => {
      manager = new EnvironmentConfigManager();
      const retryPolicy = manager.getRetryPolicy();

      expect(retryPolicy.maxAttempts).toBe(3);
      expect(retryPolicy.baseDelay).toBe(1000);
      expect(retryPolicy.maxDelay).toBe(10000);
      expect(retryPolicy.exponentialBase).toBe(2);
      expect(retryPolicy.jitterEnabled).toBe(true);

    it('should load custom retry policy from environment', () => {
      const restoreEnv = mockEnv({
        MAX_RETRY_ATTEMPTS: '5',
        RETRY_BASE_DELAY_MS: '2000',
        RETRY_MAX_DELAY_MS: '20000',
        RETRY_EXPONENTIAL_BASE: '3',
        ENABLE_EXPONENTIAL_BACKOFF: 'false',

      manager = new EnvironmentConfigManager();
      const retryPolicy = manager.getRetryPolicy();

      expect(retryPolicy.maxAttempts).toBe(5);
      expect(retryPolicy.baseDelay).toBe(2000);
      expect(retryPolicy.maxDelay).toBe(20000);
      expect(retryPolicy.exponentialBase).toBe(3);
      expect(retryPolicy.jitterEnabled).toBe(false);

      restoreEnv();


  describe('Timeout Configuration', () => {
    it('should load default timeout configuration', () => {
      manager = new EnvironmentConfigManager();
      const timeouts = manager.getTimeoutConfig();

      expect(timeouts.connection).toBe(30000);
      expect(timeouts.authentication).toBe(45000); // Increased from 15s
      expect(timeouts.sessionValidation).toBe(30000);
      expect(timeouts.healthCheck).toBe(10000);

    it('should load custom timeout configuration from environment', () => {
      const restoreEnv = mockEnv({
        CONNECTION_TIMEOUT_MS: '45000',
        AUTH_TIMEOUT_MS: '60000',
        SESSION_VALIDATION_TIMEOUT_MS: '40000',
        HEALTH_CHECK_TIMEOUT_MS: '15000',

      manager = new EnvironmentConfigManager();
      const timeouts = manager.getTimeoutConfig();

      expect(timeouts.connection).toBe(45000);
      expect(timeouts.authentication).toBe(60000);
      expect(timeouts.sessionValidation).toBe(40000);
      expect(timeouts.healthCheck).toBe(15000);

      restoreEnv();


