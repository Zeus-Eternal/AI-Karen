/**
 * Unit tests for ConfigManager class
 * Tests configuration management, environment detection, and endpoint validation
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ConfigManager, getConfigManager, initializeConfigManager } from '../endpoint-config';

// Mock environment variables
const mockEnv = {
  KAREN_BACKEND_URL: 'http://localhost:8000',
  KAREN_ENVIRONMENT: 'local',
  KAREN_NETWORK_MODE: 'localhost',
  KAREN_FALLBACK_BACKEND_URLS: 'http://127.0.0.1:8000,http://localhost:8001',
  KAREN_CORS_ORIGINS: 'http://localhost:9002,http://127.0.0.1:9002',
  KAREN_HEALTH_CHECK_ENABLED: 'true',
  KAREN_HEALTH_CHECK_INTERVAL: '30000',
  KAREN_HEALTH_CHECK_TIMEOUT: '5000',
  KAREN_CONTAINER_BACKEND_HOST: 'backend',
  KAREN_CONTAINER_BACKEND_PORT: '8000',
  KAREN_EXTERNAL_HOST: '10.105.235.209',
  KAREN_EXTERNAL_BACKEND_PORT: '8000',
};

// Mock fetch for endpoint validation
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock performance.now
global.performance = {
  now: vi.fn(() => Date.now()),
} as any;

// Mock window object for browser environment tests
const mockWindow = {
  location: {
    hostname: 'localhost',
    href: 'http://localhost:9002',
    origin: 'http://localhost:9002',
  },
};

describe('ConfigManager', () => {
  let originalProcess: any;
  let originalWindow: any;

  beforeEach(() => {
    // Mock process.env
    originalProcess = global.process;
    global.process = {
      env: { ...mockEnv },
    } as any;

    // Mock window
    originalWindow = global.window;
    global.window = mockWindow as any;

    // Reset fetch mock
    mockFetch.mockReset();
    
    // Clear any existing singleton
    (getConfigManager as any).configManager = null;
  });

  afterEach(() => {
    // Restore original globals
    global.process = originalProcess;
    global.window = originalWindow;
    vi.clearAllMocks();
  });

  describe('Configuration Loading', () => {
    it('should load default configuration when no environment variables are set', () => {
      global.process.env = {};
      
      const config = new ConfigManager();
      const configuration = config.getConfiguration();

      expect(configuration.backendUrl).toBe('http://localhost:8000');
      expect(configuration.environment).toBe('local');
      expect(configuration.networkMode).toBe('localhost');
      expect(configuration.healthCheckEnabled).toBe(true);
      expect(configuration.healthCheckInterval).toBe(30000);
      expect(configuration.healthCheckTimeout).toBe(5000);
    });

    it('should load configuration from environment variables', () => {
      const config = new ConfigManager();
      const configuration = config.getConfiguration();

      expect(configuration.backendUrl).toBe('http://localhost:8000');
      expect(configuration.environment).toBe('local');
      expect(configuration.networkMode).toBe('localhost');
      expect(configuration.fallbackUrls).toEqual(['http://127.0.0.1:8000', 'http://localhost:8001']);
      expect(configuration.corsOrigins).toEqual(['http://localhost:9002', 'http://127.0.0.1:9002']);
      expect(configuration.healthCheckEnabled).toBe(true);
      expect(configuration.healthCheckInterval).toBe(30000);
      expect(configuration.healthCheckTimeout).toBe(5000);
    });

    it('should parse boolean environment variables correctly', () => {
      global.process.env.KAREN_HEALTH_CHECK_ENABLED = 'false';
      
      const config = new ConfigManager();
      const configuration = config.getConfiguration();

      expect(configuration.healthCheckEnabled).toBe(false);
    });

    it('should parse number environment variables correctly', () => {
      global.process.env.KAREN_HEALTH_CHECK_INTERVAL = '60000';
      global.process.env.KAREN_HEALTH_CHECK_TIMEOUT = '10000';
      
      const config = new ConfigManager();
      const configuration = config.getConfiguration();

      expect(configuration.healthCheckInterval).toBe(60000);
      expect(configuration.healthCheckTimeout).toBe(10000);
    });

    it('should handle invalid number environment variables with defaults', () => {
      global.process.env.KAREN_HEALTH_CHECK_INTERVAL = 'invalid';
      global.process.env.KAREN_HEALTH_CHECK_TIMEOUT = 'also-invalid';
      
      const config = new ConfigManager();
      const configuration = config.getConfiguration();

      expect(configuration.healthCheckInterval).toBe(30000);
      expect(configuration.healthCheckTimeout).toBe(5000);
    });

    it('should generate default fallback URLs when not provided', () => {
      global.process.env.KAREN_FALLBACK_BACKEND_URLS = '';
      global.process.env.KAREN_BACKEND_URL = 'http://example.com:8000';
      
      const config = new ConfigManager();
      const configuration = config.getConfiguration();

      expect(configuration.fallbackUrls).toContain('http://localhost:8000');
      expect(configuration.fallbackUrls).toContain('http://127.0.0.1:8000');
    });
  });

  describe('Environment Detection', () => {
    it('should detect localhost environment correctly', () => {
      global.window.location.hostname = 'localhost';
      
      const config = new ConfigManager();
      const envInfo = config.getEnvironmentInfo();

      expect(envInfo.networkMode).toBe('localhost');
      expect(envInfo.environment).toBe('local');
      expect(envInfo.isDocker).toBe(false);
      expect(envInfo.isExternal).toBe(false);
    });

    it('should detect Docker environment correctly', () => {
      global.process.env.DOCKER_CONTAINER = 'true';
      
      const config = new ConfigManager();
      const envInfo = config.getEnvironmentInfo();

      expect(envInfo.networkMode).toBe('container');
      expect(envInfo.environment).toBe('docker');
      expect(envInfo.isDocker).toBe(true);
    });

    it('should detect external IP environment correctly', () => {
      global.window.location.hostname = '10.105.235.209';
      
      const config = new ConfigManager();
      const envInfo = config.getEnvironmentInfo();

      expect(envInfo.networkMode).toBe('external');
      expect(envInfo.isExternal).toBe(true);
    });

    it('should detect Docker environment from hostname', () => {
      global.window.location.hostname = 'docker-container-123';
      
      const config = new ConfigManager();
      const envInfo = config.getEnvironmentInfo();

      expect(envInfo.networkMode).toBe('container');
      expect(envInfo.environment).toBe('docker');
    });

    it('should detect external environment from non-localhost hostname', () => {
      global.window.location.hostname = 'example.com';
      
      const config = new ConfigManager();
      const envInfo = config.getEnvironmentInfo();

      expect(envInfo.networkMode).toBe('external');
      expect(envInfo.isExternal).toBe(true);
    });
  });

  describe('Backend URL Adjustment', () => {
    it('should adjust backend URL for container environment', () => {
      global.process.env.DOCKER_CONTAINER = 'true';
      global.process.env.KAREN_CONTAINER_BACKEND_HOST = 'backend-service';
      global.process.env.KAREN_CONTAINER_BACKEND_PORT = '9000';
      
      const config = new ConfigManager();
      
      expect(config.getBackendUrl()).toBe('http://backend-service:9000');
    });

    it('should adjust backend URL for external environment', () => {
      global.window.location.hostname = '10.105.235.209';
      global.process.env.KAREN_EXTERNAL_HOST = '10.105.235.209';
      global.process.env.KAREN_EXTERNAL_BACKEND_PORT = '8000';
      
      const config = new ConfigManager();
      
      expect(config.getBackendUrl()).toBe('http://10.105.235.209:8000');
    });

    it('should use current hostname for external environment when no external host is configured', () => {
      global.window.location.hostname = '192.168.1.100';
      global.process.env.KAREN_EXTERNAL_HOST = '';
      global.process.env.KAREN_EXTERNAL_BACKEND_PORT = '8000';
      
      const config = new ConfigManager();
      
      expect(config.getBackendUrl()).toBe('http://192.168.1.100:8000');
    });

    it('should keep localhost configuration for localhost environment', () => {
      global.window.location.hostname = 'localhost';
      
      const config = new ConfigManager();
      
      expect(config.getBackendUrl()).toBe('http://localhost:8000');
    });
  });

  describe('Endpoint Methods', () => {
    it('should return correct endpoint URLs', () => {
      const config = new ConfigManager();

      expect(config.getBackendUrl()).toBe('http://localhost:8000');
      expect(config.getAuthEndpoint()).toBe('http://localhost:8000/api/auth');
      expect(config.getChatEndpoint()).toBe('http://localhost:8000/api/chat');
      expect(config.getMemoryEndpoint()).toBe('http://localhost:8000/api/memory');
      expect(config.getPluginsEndpoint()).toBe('http://localhost:8000/api/plugins');
      expect(config.getHealthEndpoint()).toBe('http://localhost:8000/health');
    });

    it('should return fallback URLs', () => {
      const config = new ConfigManager();
      const fallbackUrls = config.getFallbackUrls();

      expect(fallbackUrls).toEqual(['http://127.0.0.1:8000', 'http://localhost:8001']);
    });
  });

  describe('Endpoint Validation', () => {
    it('should validate endpoints successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
      });

      const config = new ConfigManager();
      const results = await config.validateEndpoints();

      expect(results).toHaveLength(3); // primary + 2 fallbacks
      expect(results[0].isValid).toBe(true);
      expect(results[0].endpoint).toBe('http://localhost:8000');
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/health',
        expect.objectContaining({
          method: 'GET',
          headers: { 'Accept': 'application/json' },
        })
      );
    });

    it('should handle validation failures', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const config = new ConfigManager();
      const results = await config.validateEndpoints();

      expect(results[0].isValid).toBe(false);
      expect(results[0].error).toBe('Network error');
    });

    it('should handle HTTP error responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      const config = new ConfigManager();
      const results = await config.validateEndpoints();

      expect(results[0].isValid).toBe(false);
      expect(results[0].error).toBe('HTTP 500: Internal Server Error');
    });

    it('should handle timeout errors', async () => {
      const abortError = new Error('AbortError');
      abortError.name = 'AbortError';
      mockFetch.mockRejectedValueOnce(abortError);

      const config = new ConfigManager();
      const results = await config.validateEndpoints();

      expect(results[0].isValid).toBe(false);
      expect(results[0].error).toBe('Request timeout');
    });

    it('should cache validation results', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
      });

      const config = new ConfigManager();
      
      // First call
      await config.validateEndpoints();
      
      // Second call should use cache
      await config.validateEndpoints();

      // Should only call fetch once per endpoint due to caching
      expect(mockFetch).toHaveBeenCalledTimes(3); // primary + 2 fallbacks
    });
  });

  describe('Configuration Updates', () => {
    it('should update configuration correctly', () => {
      const config = new ConfigManager();
      
      config.updateConfiguration({
        backendUrl: 'http://new-backend:8000',
        healthCheckInterval: 60000,
      });

      const configuration = config.getConfiguration();
      expect(configuration.backendUrl).toBe('http://new-backend:8000');
      expect(configuration.healthCheckInterval).toBe(60000);
    });

    it('should clear validation cache when configuration changes', () => {
      const config = new ConfigManager();
      
      // Add something to cache
      config.getValidationCacheStats();
      
      config.updateConfiguration({ backendUrl: 'http://new-backend:8000' });
      
      const stats = config.getValidationCacheStats();
      expect(stats.size).toBe(0);
    });

    it('should re-detect environment when backend URL changes', () => {
      const config = new ConfigManager();
      
      config.updateConfiguration({ backendUrl: 'http://external-host:8000' });
      
      // Should trigger environment re-detection
      const envInfo = config.getEnvironmentInfo();
      expect(envInfo).toBeDefined();
    });
  });

  describe('Validation Cache', () => {
    it('should provide cache statistics', () => {
      const config = new ConfigManager();
      const stats = config.getValidationCacheStats();

      expect(stats).toHaveProperty('size');
      expect(stats).toHaveProperty('keys');
      expect(Array.isArray(stats.keys)).toBe(true);
    });

    it('should clear validation cache', () => {
      const config = new ConfigManager();
      
      config.clearValidationCache();
      
      const stats = config.getValidationCacheStats();
      expect(stats.size).toBe(0);
    });
  });

  describe('Singleton Pattern', () => {
    it('should return the same instance from getConfigManager', () => {
      const instance1 = getConfigManager();
      const instance2 = getConfigManager();

      expect(instance1).toBe(instance2);
    });

    it('should create new instance with initializeConfigManager', () => {
      const instance1 = getConfigManager();
      const instance2 = initializeConfigManager();

      expect(instance1).not.toBe(instance2);
    });
  });

  describe('Server Environment', () => {
    it('should handle server environment without window object', () => {
      global.window = undefined as any;
      
      const config = new ConfigManager();
      const envInfo = config.getEnvironmentInfo();

      expect(envInfo.networkMode).toBe('localhost');
      expect(envInfo.environment).toBe('local');
    });

    it('should handle server environment without process object', () => {
      global.process = undefined as any;
      
      const config = new ConfigManager();
      const configuration = config.getConfiguration();

      expect(configuration.backendUrl).toBe('http://localhost:8000');
      expect(configuration.environment).toBe('local');
    });
  });
});