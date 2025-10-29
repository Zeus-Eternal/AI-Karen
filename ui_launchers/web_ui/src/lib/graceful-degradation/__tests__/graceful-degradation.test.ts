/**
 * Test suite for graceful degradation system
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { 
  FeatureFlagManager,
  CacheManager,
  ExtensionDataCache
} from '../index';
import { EnhancedBackendService } from '../enhanced-backend-service';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn()
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

describe('FeatureFlagManager', () => {
  let manager: FeatureFlagManager;

  beforeEach(() => {
    vi.clearAllMocks();
    manager = new FeatureFlagManager();
  });

  it('should initialize with default flags', () => {
    expect(manager.isEnabled('extensionSystem')).toBe(true);
    expect(manager.isEnabled('backgroundTasks')).toBe(true);
    expect(manager.isEnabled('modelProviderIntegration')).toBe(true);
  });

  it('should respect flag dependencies', () => {
    manager.setFlag('extensionSystem', false);
    expect(manager.isEnabled('backgroundTasks')).toBe(false);
    expect(manager.isEnabled('modelProviderIntegration')).toBe(false);
  });

  it('should handle service errors by disabling flags', () => {
    manager.handleServiceError('extension-api', new Error('Service down'));
    expect(manager.isEnabled('extensionSystem')).toBe(false);
  });

  it('should handle service recovery by enabling flags', () => {
    manager.setFlag('extensionSystem', false);
    manager.handleServiceRecovery('extension-api');
    expect(manager.isEnabled('extensionSystem')).toBe(true);
  });

  it('should get correct fallback behavior', () => {
    expect(manager.getFallbackBehavior('backgroundTasks')).toBe('hide');
    expect(manager.getFallbackBehavior('modelProviderIntegration')).toBe('cache');
  });

  it('should notify listeners on flag changes', () => {
    const callback = vi.fn();
    const unsubscribe = manager.onFlagChange('extensionSystem', callback);

    manager.setFlag('extensionSystem', false);
    expect(callback).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'extensionSystem', enabled: false })
    );

    unsubscribe();
    manager.setFlag('extensionSystem', true);
    expect(callback).toHaveBeenCalledTimes(1);
  });
});

describe('CacheManager', () => {
  let cache: CacheManager;

  beforeEach(() => {
    vi.clearAllMocks();
    cache = new CacheManager(false); // Disable persistent storage for tests
  });

  it('should store and retrieve data', () => {
    const testData = { id: 1, name: 'test' };
    cache.set('test-key', testData);
    
    expect(cache.get('test-key')).toEqual(testData);
    expect(cache.has('test-key')).toBe(true);
  });

  it('should respect TTL and expire entries', async () => {
    const testData = { id: 1, name: 'test' };
    cache.set('test-key', testData, { ttl: 100 }); // 100ms TTL
    
    expect(cache.get('test-key')).toEqual(testData);
    
    // Wait for expiration
    await new Promise(resolve => setTimeout(resolve, 150));
    
    expect(cache.get('test-key')).toBeNull();
    expect(cache.has('test-key')).toBe(false);
  });

  it('should return stale data when requested', async () => {
    const testData = { id: 1, name: 'test' };
    cache.set('test-key', testData, { ttl: 50 }); // Shorter TTL
    
    // Wait for expiration
    await new Promise(resolve => setTimeout(resolve, 100));
    
    expect(cache.get('test-key')).toBeNull();
    expect(cache.getStale('test-key')).toEqual(testData);
  });

  it('should clean up expired entries', async () => {
    cache.set('key1', 'data1', { ttl: 100 });
    cache.set('key2', 'data2', { ttl: 200 });
    cache.set('key3', 'data3', { ttl: 300 });
    
    expect(cache.size()).toBe(3);
    
    // Wait for some to expire
    await new Promise(resolve => setTimeout(resolve, 150));
    
    const removedCount = cache.cleanup();
    expect(removedCount).toBe(1);
    expect(cache.size()).toBe(2);
  });

  it('should provide cache statistics', () => {
    cache.set('key1', 'data1');
    cache.set('key2', 'data2');
    
    const stats = cache.getStats();
    expect(stats.totalEntries).toBe(2);
    expect(stats.totalSize).toBeGreaterThan(0);
    expect(stats.newestEntry).toBeInstanceOf(Date);
  });
});

describe('ExtensionDataCache', () => {
  let cache: ExtensionDataCache;

  beforeEach(() => {
    vi.clearAllMocks();
    cache = new ExtensionDataCache();
  });

  it('should cache extension list', () => {
    const extensions = [
      { name: 'ext1', version: '1.0.0' },
      { name: 'ext2', version: '2.0.0' }
    ];
    
    cache.cacheExtensionList(extensions);
    expect(cache.getCachedExtensionList()).toEqual(extensions);
  });

  it('should cache extension health', () => {
    const health = { status: 'healthy', uptime: 1000 };
    
    cache.cacheExtensionHealth('test-ext', health);
    expect(cache.getCachedExtensionHealth('test-ext')).toEqual(health);
  });

  it('should cache background tasks', () => {
    const tasks = [
      { id: 'task1', status: 'running' },
      { id: 'task2', status: 'completed' }
    ];
    
    cache.cacheBackgroundTasks(tasks);
    expect(cache.getCachedBackgroundTasks()).toEqual(tasks);
  });

  it('should cache model providers', () => {
    const providers = [
      { id: 'openai', name: 'OpenAI' },
      { id: 'anthropic', name: 'Anthropic' }
    ];
    
    cache.cacheModelProviders(providers);
    expect(cache.getCachedModelProviders()).toEqual(providers);
  });

  it('should return stale data when fresh data is unavailable', async () => {
    const extensions = [{ name: 'ext1', version: '1.0.0' }];
    
    // Set with very short TTL
    cache.set('extensions-list', extensions, { ttl: 50 });
    
    // Wait for cache to expire
    await new Promise(resolve => setTimeout(resolve, 100));
    
    expect(cache.getCachedExtensionList()).toBeNull();
    expect(cache.getStaleExtensionList()).toEqual(extensions);
  });
});

describe('EnhancedBackendService', () => {
  let service: EnhancedBackendService;
  let mockOriginalService: any;

  beforeEach(() => {
    vi.clearAllMocks();
    mockOriginalService = {
      makeRequest: vi.fn()
    };
    service = new EnhancedBackendService(mockOriginalService);
  });

  it('should make successful requests', async () => {
    const mockData = { id: 1, name: 'test' };
    mockOriginalService.makeRequest.mockResolvedValue(mockData);

    const result = await service.makeEnhancedRequest({
      endpoint: '/api/test',
      enableCaching: false
    });

    expect(result).toEqual(mockData);
    expect(mockOriginalService.makeRequest).toHaveBeenCalledWith('/api/test', {});
  });

  it('should handle authentication errors with fallback', async () => {
    const authError = new Error('Unauthorized');
    (authError as any).status = 401;
    
    mockOriginalService.makeRequest.mockRejectedValue(authError);

    const fallbackData = { fallback: true };
    const result = await service.makeEnhancedRequest({
      endpoint: '/api/extensions/',
      fallbackData,
      enableCaching: false
    });

    expect(result).toEqual(fallbackData);
  });

  it('should retry on service unavailable errors', async () => {
    const serviceError = new Error('Service Unavailable');
    (serviceError as any).status = 503;
    
    mockOriginalService.makeRequest
      .mockRejectedValueOnce(serviceError)
      .mockRejectedValueOnce(serviceError)
      .mockResolvedValue({ success: true });

    const result = await service.makeEnhancedRequest({
      endpoint: '/api/test',
      enableCaching: false
    });

    expect(result).toEqual({ success: true });
    expect(mockOriginalService.makeRequest).toHaveBeenCalledTimes(3);
  });

  it('should use cached data when service is disabled', async () => {
    // Mock feature flag as disabled
    const manager = new FeatureFlagManager();
    manager.setFlag('extensionSystem', false);

    const cachedData = { cached: true };
    const cache = new ExtensionDataCache();
    cache.set('test-key', cachedData);

    const result = await service.makeEnhancedRequest({
      endpoint: '/api/extensions/',
      cacheKey: 'test-key',
      serviceName: 'extension-api'
    });

    expect(result).toEqual(cachedData);
    expect(mockOriginalService.makeRequest).not.toHaveBeenCalled();
  });

  it('should provide convenience methods for common endpoints', async () => {
    const mockExtensions = [{ name: 'ext1' }];
    mockOriginalService.makeRequest.mockResolvedValue(mockExtensions);

    const extensions = await service.getExtensions();
    expect(extensions).toEqual(mockExtensions);
    expect(mockOriginalService.makeRequest).toHaveBeenCalledWith('/api/extensions/', {});
  });

  it('should track service health', async () => {
    const error = new Error('Service Error');
    mockOriginalService.makeRequest.mockRejectedValue(error);

    try {
      await service.makeEnhancedRequest({
        endpoint: '/api/test',
        serviceName: 'test-service',
        enableCaching: false
      });
    } catch (e) {
      // Expected to throw
    }

    const healthStatus = service.getServiceHealthStatus();
    expect(healthStatus['test-service']).toBeDefined();
    expect(healthStatus['test-service'].isHealthy).toBe(false);
    expect(healthStatus['test-service'].consecutiveFailures).toBeGreaterThan(0);
  });
});

describe('Integration Tests', () => {
  it('should handle complete service failure gracefully', async () => {
    const manager = new FeatureFlagManager();
    const cache = new ExtensionDataCache();
    
    // Cache some data
    const cachedExtensions = [{ name: 'cached-ext', version: '1.0.0' }];
    cache.cacheExtensionList(cachedExtensions);
    
    // Simulate service failure
    manager.handleServiceError('extension-api', new Error('Complete failure'));
    
    // Feature should be disabled
    expect(manager.isEnabled('extensionSystem')).toBe(false);
    
    // Should still be able to get cached data
    expect(cache.getStaleExtensionList()).toEqual(cachedExtensions);
  });

  it('should recover from service failures', () => {
    const manager = new FeatureFlagManager();
    
    // Simulate failure and recovery
    manager.handleServiceError('extension-api', new Error('Temporary failure'));
    expect(manager.isEnabled('extensionSystem')).toBe(false);
    
    manager.handleServiceRecovery('extension-api');
    expect(manager.isEnabled('extensionSystem')).toBe(true);
  });
});