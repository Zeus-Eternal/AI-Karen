/**
 * Integration tests for KarenBackendService authentication enhancements
 * 
 * Tests the enhanced authentication handling for extension endpoints.
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { KarenBackendService } from '../karen-backend';

// Mock the extension auth manager
vi.mock('../auth/extension-auth-manager', () => ({
  getExtensionAuthManager: () => ({
    getAuthHeaders: vi.fn().mockResolvedValue({
      'Authorization': 'Bearer extension-token',
      'Content-Type': 'application/json',
      'X-Client-Type': 'extension-integration',
    }),
    forceRefresh: vi.fn().mockResolvedValue('new-token'),
    isAuthenticated: vi.fn().mockReturnValue(true),
    clearAuth: vi.fn(),
  }),
}));

// Mock other dependencies
vi.mock('../logger', () => ({
  logger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
  },
}));

vi.mock('../config', () => ({
  webUIConfig: {
    backendUrl: '',
    apiTimeout: 5000,
    cacheTtl: 300000,
    maxRetries: 2,
    retryDelay: 100,
    debugLogging: false,
    requestLogging: false,
    performanceMonitoring: false,
    logLevel: 'info',
    fallbackBackendUrls: [],
    circuitBreakerThreshold: 5,
    circuitBreakerResetTime: 60000,
  },
}));

vi.mock('../performance-monitor', () => ({
  getPerformanceMonitor: () => ({
    recordRequest: vi.fn(),
  }),
}));

vi.mock('../secure-api-key', () => ({
  getStoredApiKey: () => null,
}));

vi.mock('../error-handler', () => ({
  errorHandler: {
    handleApiError: vi.fn((error) => ({ handled: true, error })),
  },
}));

describe('KarenBackendService Authentication Integration', () => {
  let service: KarenBackendService;

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    service = new KarenBackendService();
    
    // Mock localStorage for browser environment
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,


  test('should successfully call extension API with authentication', async () => {
    // Mock successful response
    vi.mocked(global.fetch).mockResolvedValue(
      new Response(JSON.stringify({ extensions: [{ name: 'test-extension' }] }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      })
    );

    const result = await service.getExtensions();

    expect(result).toEqual([{ name: 'test-extension' }]);
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/extensions/',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer extension-token',
          'X-Client-Type': 'extension-integration',
        }),
      })
    );

  test('should handle authentication status check', async () => {
    const isAuthenticated = await service.checkExtensionAuthStatus();
    expect(isAuthenticated).toBe(true);

  test('should clear extension authentication', () => {
    service.clearExtensionAuth();
    // Should not throw

  test('should register background tasks with proper payload', async () => {
    vi.mocked(global.fetch).mockResolvedValue(
      new Response(JSON.stringify({ 
        task_id: 'test-task', 
        message: 'Success', 
        status: 'registered' 
      }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      })
    );

    const taskData = {
      name: 'test-task',
      extension_name: 'test-extension',
      schedule: '0 0 * * *',
      enabled: true,
    };

    const result = await service.registerExtensionBackgroundTask(taskData);

    expect(result.task_id).toBe('test-task');
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/extensions/background-tasks/',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(taskData),
        headers: expect.objectContaining({
          'Authorization': 'Bearer extension-token',
        }),
      })
    );

  test('should get extension health status', async () => {
    vi.mocked(global.fetch).mockResolvedValue(
      new Response(JSON.stringify({ 
        status: 'healthy',
        services: {},
        overall_health: 'healthy',
        monitoring_active: true,
      }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      })
    );

    const result = await service.getExtensionHealth();

    expect(result.status).toBe('healthy');
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/extensions/health',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer extension-token',
        }),
      })
    );

  test('should handle extension health check failures gracefully', async () => {
    vi.mocked(global.fetch).mockRejectedValue(new Error('Network error'));

    const result = await service.getExtensionHealth();

    expect(result.status).toBe('unhealthy');
    expect(result.overall_health).toBe('unknown');

  test('should load and unload extensions', async () => {
    vi.mocked(global.fetch).mockResolvedValue(
      new Response(JSON.stringify({ 
        message: 'Success', 
        status: 'loaded' 
      }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      })
    );

    const loadResult = await service.loadExtension('test-extension');
    expect(loadResult.status).toBe('loaded');

    const unloadResult = await service.unloadExtension('test-extension');
    expect(unloadResult.status).toBe('loaded'); // Same mock response

    expect(global.fetch).toHaveBeenCalledTimes(2);

