/**
 * Tests for KarenBackendService authentication enhancements
 * 
 * Tests the enhanced authentication handling for extension endpoints,
 * automatic retry logic, and request interceptor functionality.
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { KarenBackendService, APIError } from '../karen-backend';
import { getExtensionAuthManager } from '../auth/extension-auth-manager';

// Mock the extension auth manager
vi.mock('../auth/extension-auth-manager');

// Mock fetch
global.fetch = vi.fn();

// Mock logger
vi.mock('../logger', () => ({
  logger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
  },
}));

// Mock other dependencies
vi.mock('../config', () => ({
  webUIConfig: {
    backendUrl: 'http://localhost:8000',
    apiTimeout: 30000,
    cacheTtl: 300000,
    maxRetries: 3,
    retryDelay: 1000,
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

describe('KarenBackendService Authentication Enhancements', () => {
  let service: KarenBackendService;
  let mockExtensionAuthManager: any;

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup mock extension auth manager
    mockExtensionAuthManager = {
      getAuthHeaders: vi.fn(),
      forceRefresh: vi.fn(),
      isAuthenticated: vi.fn(),
      clearAuth: vi.fn(),
    };
    
    vi.mocked(getExtensionAuthManager).mockReturnValue(mockExtensionAuthManager);
    
    service = new KarenBackendService();
    
    // Mock localStorage for browser environment
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn(),
        setItem: vi.fn(),
        removeItem: vi.fn(),
      },
      writable: true,


  describe('Extension authentication integration', () => {
    test('should use extension auth manager for extension API calls', async () => {
      const mockHeaders = {
        'Authorization': 'Bearer extension-token',
        'Content-Type': 'application/json',
        'X-Client-Type': 'extension-integration',
      };
      
      mockExtensionAuthManager.getAuthHeaders.mockResolvedValue(mockHeaders);
      
      // Test that extension endpoints use the extension auth manager
      await service.getExtensions();
      
      expect(mockExtensionAuthManager.getAuthHeaders).toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/extensions/'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer extension-token',
            'X-Client-Type': 'extension-integration',
          }),
        })
      );

    test('should handle extension auth failures with retry', async () => {
      // First call fails with 403
      vi.mocked(global.fetch)
        .mockResolvedValueOnce(new Response('Forbidden', { status: 403 }))
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ extensions: [] }), {
            status: 200,
            headers: { 'content-type': 'application/json' },
          })
        );

      mockExtensionAuthManager.getAuthHeaders.mockResolvedValue({
        'Authorization': 'Bearer extension-token',

      mockExtensionAuthManager.forceRefresh.mockResolvedValue('new-token');

      // Should succeed after retry
      const result = await service.getExtensions();
      
      expect(result).toEqual([]);
      expect(mockExtensionAuthManager.forceRefresh).toHaveBeenCalled();
      expect(global.fetch).toHaveBeenCalledTimes(2);


  describe('Extension API methods', () => {
    beforeEach(() => {
      vi.mocked(global.fetch).mockResolvedValue(
        new Response(JSON.stringify({ extensions: [] }), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        })
      );

    test('should call getExtensions with proper authentication', async () => {
      mockExtensionAuthManager.getAuthHeaders.mockResolvedValue({
        'Authorization': 'Bearer test-token',

      await service.getExtensions();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/extensions/'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      );

    test('should handle 403 errors gracefully in extension methods', async () => {
      vi.mocked(global.fetch).mockResolvedValue(
        new Response('Forbidden', { status: 403 })
      );

      await expect(service.getExtensions()).rejects.toThrow();

    test('should register background tasks with proper payload', async () => {
      vi.mocked(global.fetch).mockResolvedValue(
        new Response(JSON.stringify({ task_id: 'test-task', message: 'Success', status: 'registered' }), {
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
        expect.stringContaining('/api/extensions/background-tasks/'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(taskData),
        })
      );


  describe('Service unavailable handling', () => {
    test('should retry with exponential backoff for 503 errors', async () => {
      // Mock multiple 503 responses then success
      vi.mocked(global.fetch)
        .mockResolvedValueOnce(new Response('Service Unavailable', { status: 503 }))
        .mockResolvedValueOnce(new Response('Service Unavailable', { status: 503 }))
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ extensions: [] }), {
            status: 200,
            headers: { 'content-type': 'application/json' },
          })
        );

      mockExtensionAuthManager.getAuthHeaders.mockResolvedValue({
        'Authorization': 'Bearer extension-token',

      const result = await service.getExtensions();
      
      expect(result).toEqual([]);
      expect(global.fetch).toHaveBeenCalledTimes(3);


  describe('Extension authentication status', () => {
    test('should check extension auth status', async () => {
      mockExtensionAuthManager.isAuthenticated.mockReturnValue(true);
      
      const isAuthenticated = await service.checkExtensionAuthStatus();
      
      expect(isAuthenticated).toBe(true);
      expect(mockExtensionAuthManager.isAuthenticated).toHaveBeenCalled();

    test('should clear extension auth', () => {
      service.clearExtensionAuth();
      
      expect(mockExtensionAuthManager.clearAuth).toHaveBeenCalled();


