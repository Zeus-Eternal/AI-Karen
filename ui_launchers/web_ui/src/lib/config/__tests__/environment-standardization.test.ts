/**
 * Environment Variable Standardization Tests
 * 
 * Tests for environment variable consistency, migration recommendations,
 * and standardized configuration validation.
 * 
 * Requirements: 1.1, 1.3
 */

import { EnvironmentConfigManager } from '../environment-config-manager';

// Mock process.env for testing
const originalEnv = process.env;

describe('Environment Variable Standardization', () => {
  let configManager: EnvironmentConfigManager;

  beforeEach(() => {
    // Reset process.env
    process.env = { ...originalEnv };
    configManager = new EnvironmentConfigManager();

  afterEach(() => {
    process.env = originalEnv;

  describe('Standardized Environment Variables', () => {
    test('should prioritize KAREN_BACKEND_URL over legacy API_BASE_URL', () => {
      process.env.KAREN_BACKEND_URL = 'http://standardized:8000';
      process.env.API_BASE_URL = 'http://legacy:8000';

      const manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.primaryUrl).toBe('http://standardized:8000');

    test('should prioritize NEXT_PUBLIC_KAREN_BACKEND_URL over legacy NEXT_PUBLIC_API_BASE_URL', () => {
      process.env.NEXT_PUBLIC_KAREN_BACKEND_URL = 'http://standardized:8000';
      process.env.NEXT_PUBLIC_API_BASE_URL = 'http://legacy:8000';

      const manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.primaryUrl).toBe('http://standardized:8000');

    test('should fall back to legacy variables when standardized ones are not set', () => {
      delete process.env.KAREN_BACKEND_URL;
      delete process.env.NEXT_PUBLIC_KAREN_BACKEND_URL;
      process.env.API_BASE_URL = 'http://legacy:8000';

      const manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.primaryUrl).toBe('http://legacy:8000');

    test('should use default localhost when no environment variables are set', () => {
      delete process.env.KAREN_BACKEND_URL;
      delete process.env.NEXT_PUBLIC_KAREN_BACKEND_URL;
      delete process.env.API_BASE_URL;
      delete process.env.NEXT_PUBLIC_API_BASE_URL;

      const manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.primaryUrl).toBe('http://localhost:8000');


  describe('Fallback URL Configuration', () => {
    test('should parse KAREN_FALLBACK_BACKEND_URLS correctly', () => {
      process.env.KAREN_BACKEND_URL = 'http://primary:8000';
      process.env.KAREN_FALLBACK_BACKEND_URLS = 'http://fallback1:8000,http://fallback2:8000,http://fallback3:8000';

      const manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.fallbackUrls).toContain('http://fallback1:8000');
      expect(config.fallbackUrls).toContain('http://fallback2:8000');
      expect(config.fallbackUrls).toContain('http://fallback3:8000');

    test('should generate Docker fallback URLs in Docker environment', () => {
      process.env.KAREN_BACKEND_URL = 'http://localhost:8000';
      process.env.DOCKER_CONTAINER = 'true';

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


  describe('Environment Variable Validation', () => {
    test('should detect conflicting environment variables', () => {
      process.env.KAREN_BACKEND_URL = 'http://standardized:8000';
      process.env.API_BASE_URL = 'http://different:8000';

      const manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings).toContain(
        'Conflicting backend URLs: KAREN_BACKEND_URL and API_BASE_URL have different values'
      );

    test('should warn about deprecated environment variables', () => {
      delete process.env.KAREN_BACKEND_URL;
      process.env.API_BASE_URL = 'http://legacy:8000';

      const manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings).toContain(
        'Using deprecated API_BASE_URL. Please migrate to KAREN_BACKEND_URL'
      );

    test('should warn about Docker environment with localhost URLs', () => {
      process.env.DOCKER_CONTAINER = 'true';
      process.env.KAREN_BACKEND_URL = 'http://localhost:8000';

      const manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings).toContain(
        'Docker environment with localhost network mode may cause connectivity issues'
      );

    test('should warn about production without high availability', () => {
      // Clear all environment variables that could provide fallbacks
      delete process.env.KAREN_HA_BACKEND_URLS;
      delete process.env.KAREN_FALLBACK_BACKEND_URLS;
      delete process.env.DOCKER_CONTAINER;
      delete process.env.KAREN_CONTAINER_MODE;
      delete process.env.HOSTNAME;
      
      process.env.NODE_ENV = 'production';
      process.env.KAREN_BACKEND_URL = 'http://single:8000';

      const manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings).toContain(
        'Production environment without high availability fallback URLs configured'
      );

    test('should warn about too many fallback URLs', () => {
      const manyUrls = Array.from({ length: 15 }, (_, i) => `http://fallback${i}:8000`).join(',');
      process.env.KAREN_FALLBACK_BACKEND_URLS = manyUrls;

      const manager = new EnvironmentConfigManager();
      const validation = manager.validateConfiguration();

      expect(validation.warnings).toContain(
        'Too many fallback URLs configured (>10), this may impact performance'
      );


  describe('Migration Recommendations', () => {
    test('should recommend migration from API_BASE_URL to KAREN_BACKEND_URL', () => {
      process.env.API_BASE_URL = 'http://legacy:8000';

      const manager = new EnvironmentConfigManager();
      const recommendations = manager.getMigrationRecommendations();

      expect(recommendations).toContainEqual({
        from: 'API_BASE_URL',
        to: 'KAREN_BACKEND_URL',
        action: 'Rename environment variable for server-side backend URL',


    test('should recommend migration from NEXT_PUBLIC_API_BASE_URL to NEXT_PUBLIC_KAREN_BACKEND_URL', () => {
      process.env.NEXT_PUBLIC_API_BASE_URL = 'http://legacy:8000';

      const manager = new EnvironmentConfigManager();
      const recommendations = manager.getMigrationRecommendations();

      expect(recommendations).toContainEqual({
        from: 'NEXT_PUBLIC_API_BASE_URL',
        to: 'NEXT_PUBLIC_KAREN_BACKEND_URL',
        action: 'Rename environment variable for client-side backend URL',


    test('should recommend migration from BACKEND_PORT to KAREN_BACKEND_PORT', () => {
      process.env.BACKEND_PORT = '9000';

      const manager = new EnvironmentConfigManager();
      const recommendations = manager.getMigrationRecommendations();

      expect(recommendations).toContainEqual({
        from: 'BACKEND_PORT',
        to: 'KAREN_BACKEND_PORT',
        action: 'Rename environment variable for backend port (optional, defaults to 8000)',


    test('should not recommend migration when standardized variables are used', () => {
      process.env.KAREN_BACKEND_URL = 'http://standardized:8000';
      process.env.NEXT_PUBLIC_KAREN_BACKEND_URL = 'http://standardized:8000';

      const manager = new EnvironmentConfigManager();
      const recommendations = manager.getMigrationRecommendations();

      expect(recommendations).toHaveLength(0);


  describe('Environment Variable Mapping', () => {
    test('should provide correct mapping for standardized variables', () => {
      process.env.KAREN_BACKEND_URL = 'http://server:8000';
      process.env.NEXT_PUBLIC_KAREN_BACKEND_URL = 'http://client:8000';

      const manager = new EnvironmentConfigManager();
      const mapping = manager.getEnvironmentVariableMapping();

      expect(mapping['Backend URL (Server-side)']).toEqual({
        current: 'http://server:8000',
        standardized: 'KAREN_BACKEND_URL',
        deprecated: undefined,

      expect(mapping['Backend URL (Client-side)']).toEqual({
        current: 'http://client:8000',
        standardized: 'NEXT_PUBLIC_KAREN_BACKEND_URL',
        deprecated: undefined,


    test('should identify deprecated variables in mapping', () => {
      process.env.API_BASE_URL = 'http://legacy:8000';
      process.env.NEXT_PUBLIC_API_BASE_URL = 'http://legacy-client:8000';

      const manager = new EnvironmentConfigManager();
      const mapping = manager.getEnvironmentVariableMapping();

      expect(mapping['Backend URL (Server-side)']).toEqual({
        current: 'http://legacy:8000',
        standardized: 'KAREN_BACKEND_URL',
        deprecated: 'API_BASE_URL',

      expect(mapping['Backend URL (Client-side)']).toEqual({
        current: 'http://legacy-client:8000',
        standardized: 'NEXT_PUBLIC_KAREN_BACKEND_URL',
        deprecated: 'NEXT_PUBLIC_API_BASE_URL',



  describe('Environment Detection', () => {
    test('should detect Docker environment correctly', () => {
      process.env.DOCKER_CONTAINER = 'true';

      const manager = new EnvironmentConfigManager();
      const envInfo = manager.getEnvironmentInfo();

      expect(envInfo.isDocker).toBe(true);
      expect(envInfo.type).toBe('docker');
      expect(envInfo.networkMode).toBe('container');

    test('should detect production environment correctly', () => {
      process.env.NODE_ENV = 'production';

      const manager = new EnvironmentConfigManager();
      const envInfo = manager.getEnvironmentInfo();

      expect(envInfo.isProduction).toBe(true);
      expect(envInfo.type).toBe('production');

    test('should detect local development environment correctly', () => {
      delete process.env.DOCKER_CONTAINER;
      process.env.NODE_ENV = 'development';

      const manager = new EnvironmentConfigManager();
      const envInfo = manager.getEnvironmentInfo();

      expect(envInfo.isDocker).toBe(false);
      expect(envInfo.isProduction).toBe(false);
      expect(envInfo.type).toBe('local');
      expect(envInfo.networkMode).toBe('localhost');


  describe('URL Normalization', () => {
    test('should remove trailing slashes from URLs', () => {
      process.env.KAREN_BACKEND_URL = 'http://example:8000/';

      const manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.primaryUrl).toBe('http://example:8000');

    test('should handle multiple trailing slashes', () => {
      process.env.KAREN_BACKEND_URL = 'http://example:8000///';

      const manager = new EnvironmentConfigManager();
      const config = manager.getBackendConfig();

      expect(config.primaryUrl).toBe('http://example:8000');


