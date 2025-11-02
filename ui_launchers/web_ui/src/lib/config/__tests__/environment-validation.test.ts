/**
 * Environment Variable Validation Tests
 * 
 * Tests for environment variable validation script functionality,
 * migration recommendations, and configuration consistency checks.
 * 
 * Requirements: 1.2, 1.4
 */

import { EnvironmentConfigManager } from '../environment-config-manager';

// Mock process.env for testing
const originalEnv = process.env;

describe('Environment Variable Validation', () => {
  beforeEach(() => {
    // Reset process.env
    process.env = { ...originalEnv };

  afterEach(() => {
    process.env = originalEnv;

  describe('Configuration Validation', () => {
    test('should validate correct standardized configuration', () => {
      process.env.KAREN_BACKEND_URL = 'http://localhost:8000';
      process.env.NEXT_PUBLIC_KAREN_BACKEND_URL = 'http://localhost:8000';
      process.env.AUTH_TIMEOUT_MS = '45000';
      process.env.MAX_RETRY_ATTEMPTS = '3';

      const manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.isValid).toBe(true);
      expect(validation.errors).toHaveLength(0);

    test('should detect invalid URL formats', () => {
      process.env.KAREN_BACKEND_URL = 'invalid-url';

      const manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('Invalid primary backend URL: invalid-url');

    test('should validate timeout values are within reasonable ranges', () => {
      process.env.AUTH_TIMEOUT_MS = '500'; // Too low

      const manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings).toContain(
        'Authentication timeout is very low (500ms), consider increasing it'
      );

    test('should validate retry configuration', () => {
      process.env.MAX_RETRY_ATTEMPTS = '15'; // Too high

      const manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings).toContain(
        'Max retry attempts is very high (15), this may cause long delays'
      );


  describe('Environment-Specific Validation', () => {
    test('should validate production environment requirements', () => {
      process.env.NODE_ENV = 'production';
      process.env.KAREN_BACKEND_URL = 'http://localhost:8000'; // Localhost in production

      const manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings).toContain(
        'Production environment without high availability fallback URLs configured'
      );

    test('should validate Docker environment configuration', () => {
      process.env.DOCKER_CONTAINER = 'true';
      process.env.KAREN_BACKEND_URL = 'http://localhost:8000';

      const manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings).toContain(
        'Docker environment with localhost network mode may cause connectivity issues'
      );

    test('should validate external access configuration', () => {
      // Mock window.location for external access detection
      Object.defineProperty(window, 'location', {
        value: {
          hostname: '192.168.1.100',
          port: '8010',
        },
        writable: true,

      process.env.KAREN_BACKEND_URL = 'http://localhost:8000';

      const manager = new EnvironmentConfigManager();
      const envInfo = manager.getEnvironmentInfo();

      expect(envInfo.networkMode).toBe('external');


  describe('Migration Recommendations', () => {
    test('should provide comprehensive migration recommendations', () => {
      process.env.API_BASE_URL = 'http://legacy:8000';
      process.env.NEXT_PUBLIC_API_BASE_URL = 'http://legacy-client:8000';
      process.env.BACKEND_PORT = '9000';

      const manager = new EnvironmentConfigManager();
      const recommendations = manager.getMigrationRecommendations();

      expect(recommendations).toHaveLength(3);
      
      expect(recommendations).toContainEqual({
        from: 'API_BASE_URL',
        to: 'KAREN_BACKEND_URL',
        action: 'Rename environment variable for server-side backend URL',

      expect(recommendations).toContainEqual({
        from: 'NEXT_PUBLIC_API_BASE_URL',
        to: 'NEXT_PUBLIC_KAREN_BACKEND_URL',
        action: 'Rename environment variable for client-side backend URL',

      expect(recommendations).toContainEqual({
        from: 'BACKEND_PORT',
        to: 'KAREN_BACKEND_PORT',
        action: 'Rename environment variable for backend port (optional, defaults to 8000)',


    test('should not provide recommendations when using standardized variables', () => {
      process.env.KAREN_BACKEND_URL = 'http://standardized:8000';
      process.env.NEXT_PUBLIC_KAREN_BACKEND_URL = 'http://standardized:8000';

      const manager = new EnvironmentConfigManager();
      const recommendations = manager.getMigrationRecommendations();

      expect(recommendations).toHaveLength(0);


  describe('Environment Variable Mapping', () => {
    test('should provide complete environment variable mapping', () => {
      process.env.KAREN_BACKEND_URL = 'http://server:8000';
      process.env.NEXT_PUBLIC_KAREN_BACKEND_URL = 'http://client:8000';
      process.env.KAREN_FALLBACK_BACKEND_URLS = 'http://fallback1:8000,http://fallback2:8000';
      process.env.KAREN_CONTAINER_BACKEND_HOST = 'api';

      const manager = new EnvironmentConfigManager();
      const mapping = manager.getEnvironmentVariableMapping();

      expect(mapping).toHaveProperty('Backend URL (Server-side)');
      expect(mapping).toHaveProperty('Backend URL (Client-side)');
      expect(mapping).toHaveProperty('Fallback URLs');
      expect(mapping).toHaveProperty('Container Backend Host');

      expect(mapping['Backend URL (Server-side)']).toEqual({
        current: 'http://server:8000',
        standardized: 'KAREN_BACKEND_URL',
        deprecated: undefined,

      expect(mapping['Fallback URLs']).toEqual({
        current: 'http://fallback1:8000,http://fallback2:8000',
        standardized: 'KAREN_FALLBACK_BACKEND_URLS',


    test('should identify deprecated variables in mapping', () => {
      process.env.API_BASE_URL = 'http://legacy:8000';
      delete process.env.KAREN_BACKEND_URL;

      const manager = new EnvironmentConfigManager();
      const mapping = manager.getEnvironmentVariableMapping();

      expect(mapping['Backend URL (Server-side)']).toEqual({
        current: 'http://legacy:8000',
        standardized: 'KAREN_BACKEND_URL',
        deprecated: 'API_BASE_URL',



  describe('Fallback URL Generation', () => {
    test('should generate appropriate fallback URLs for different environments', () => {
      process.env.KAREN_BACKEND_URL = 'http://primary:8000';
      process.env.KAREN_FALLBACK_BACKEND_URLS = 'http://explicit-fallback:8000';

      const manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.fallbackUrls).toContain('http://explicit-fallback:8000');
      expect(config.fallbackUrls).toContain('http://localhost:8000');
      expect(config.fallbackUrls).toContain('http://127.0.0.1:8000');

    test('should include Docker-specific fallback URLs in Docker environment', () => {
      process.env.DOCKER_CONTAINER = 'true';
      process.env.KAREN_BACKEND_URL = 'http://primary:8000';

      const manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.fallbackUrls).toContain('http://backend:8000');
      expect(config.fallbackUrls).toContain('http://ai-karen-api:8000');
      expect(config.fallbackUrls).toContain('http://api:8000');
      expect(config.fallbackUrls).toContain('http://host.docker.internal:8000');

    test('should include high availability URLs in production', () => {
      process.env.NODE_ENV = 'production';
      process.env.KAREN_BACKEND_URL = 'http://primary:8000';
      process.env.KAREN_HA_BACKEND_URLS = 'http://ha1:8000,http://ha2:8000';

      const manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.fallbackUrls).toContain('http://ha1:8000');
      expect(config.fallbackUrls).toContain('http://ha2:8000');


  describe('Configuration Consistency', () => {
    test('should detect and warn about conflicting configurations', () => {
      process.env.KAREN_BACKEND_URL = 'http://standardized:8000';
      process.env.API_BASE_URL = 'http://different:8000';

      const manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings).toContain(
        'Conflicting backend URLs: KAREN_BACKEND_URL and API_BASE_URL have different values'
      );

    test('should validate URL normalization', () => {
      process.env.KAREN_BACKEND_URL = 'http://example:8000///';

      const manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.primaryUrl).toBe('http://example:8000');

    test('should validate fallback URL parsing', () => {
      process.env.KAREN_FALLBACK_BACKEND_URLS = 'http://fallback1:8000/, http://fallback2:8000///, http://fallback3:8000';

      const manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.fallbackUrls).toContain('http://fallback1:8000');
      expect(config.fallbackUrls).toContain('http://fallback2:8000');
      expect(config.fallbackUrls).toContain('http://fallback3:8000');


  describe('Timeout and Retry Configuration Validation', () => {
    test('should validate timeout configuration values', () => {
      process.env.AUTH_TIMEOUT_MS = '45000';
      process.env.CONNECTION_TIMEOUT_MS = '30000';
      process.env.SESSION_VALIDATION_TIMEOUT_MS = '30000';

      const manager = new EnvironmentConfigManager();
      const timeouts = manager.getTimeoutConfig();

      expect(timeouts.authentication).toBe(45000);
      expect(timeouts.connection).toBe(30000);
      expect(timeouts.sessionValidation).toBe(30000);

    test('should validate retry policy configuration', () => {
      process.env.MAX_RETRY_ATTEMPTS = '3';
      process.env.RETRY_BASE_DELAY_MS = '1000';
      process.env.RETRY_MAX_DELAY_MS = '10000';
      process.env.ENABLE_EXPONENTIAL_BACKOFF = 'true';

      const manager = new EnvironmentConfigManager();
      const retryPolicy = manager.getRetryPolicy();

      expect(retryPolicy.maxAttempts).toBe(3);
      expect(retryPolicy.baseDelay).toBe(1000);
      expect(retryPolicy.maxDelay).toBe(10000);
      expect(retryPolicy.jitterEnabled).toBe(true);

    test('should use default values when configuration is not provided', () => {
      // Clear all timeout/retry environment variables
      delete process.env.AUTH_TIMEOUT_MS;
      delete process.env.MAX_RETRY_ATTEMPTS;
      delete process.env.RETRY_BASE_DELAY_MS;

      const manager = new EnvironmentConfigManager();
      const timeouts = manager.getTimeoutConfig();
      const retryPolicy = manager.getRetryPolicy();

      expect(timeouts.authentication).toBe(45000); // Default increased timeout
      expect(retryPolicy.maxAttempts).toBe(3); // Default retry attempts
      expect(retryPolicy.baseDelay).toBe(1000); // Default base delay


