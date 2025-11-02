import {
/**
 * Tests for Extension Authentication Graceful Degradation
 */


  ExtensionAuthDegradationManager,
  ExtensionFeatureLevel,
  extensionAuthDegradationManager
} from '../extension-auth-degradation';

  ExtensionAuthErrorFactory,
  ExtensionAuthRecoveryStrategy
} from '../extension-auth-errors';

describe('ExtensionAuthDegradationManager', () => {
  let manager: ExtensionAuthDegradationManager;

  beforeEach(() => {
    manager = ExtensionAuthDegradationManager.getInstance();
    manager.restoreFullFunctionality();
    manager.clearCache();
  });

  describe('applyDegradation', () => {
    it('should apply readonly degradation for permission denied error', () => {
      const error = ExtensionAuthErrorFactory.createPermissionDeniedError();
      const state = manager.applyDegradation(error);

      expect(state.level).toBe(ExtensionFeatureLevel.READONLY);
      expect(state.reason).toBe('Authentication permissions insufficient');
      expect(state.affectedFeatures.length).toBeGreaterThan(0);
      expect(state.availableFeatures.length).toBeGreaterThan(0);
    });

    it('should apply cached degradation for service unavailable error', () => {
      const error = ExtensionAuthErrorFactory.createServiceUnavailableError();
      const state = manager.applyDegradation(error);

      expect(state.level).toBe(ExtensionFeatureLevel.CACHED);
      expect(state.recoveryEstimate).toBeDefined();
    });

    it('should apply limited degradation for token expired error', () => {
      const error = ExtensionAuthErrorFactory.createTokenExpiredError();
      const state = manager.applyDegradation(error);

      expect(state.level).toBe(ExtensionFeatureLevel.LIMITED);
      expect(state.recoveryEstimate).toBeDefined();
    });

    it('should apply disabled degradation for configuration error', () => {
      const error = ExtensionAuthErrorFactory.createConfigurationError();
      const state = manager.applyDegradation(error);

      expect(state.level).toBe(ExtensionFeatureLevel.DISABLED);
      expect(state.recoveryEstimate).toBeUndefined();
    });
  });

  describe('restoreFullFunctionality', () => {
    it('should restore full functionality', () => {
      // First apply degradation
      const error = ExtensionAuthErrorFactory.createPermissionDeniedError();
      manager.applyDegradation(error);

      // Then restore
      const state = manager.restoreFullFunctionality();

      expect(state.level).toBe(ExtensionFeatureLevel.FULL);
      expect(state.affectedFeatures).toHaveLength(0);
      expect(state.availableFeatures.length).toBeGreaterThan(0);
      expect(state.userMessage).toBe('All extension features are now available');
    });
  });

  describe('isFeatureAvailable', () => {
    it('should return true for all features in full mode', () => {
      expect(manager.isFeatureAvailable('extension_list')).toBe(true);
      expect(manager.isFeatureAvailable('extension_install')).toBe(true);
      expect(manager.isFeatureAvailable('background_tasks')).toBe(true);
    });

    it('should restrict write features in readonly mode', () => {
      const error = ExtensionAuthErrorFactory.createPermissionDeniedError();
      manager.applyDegradation(error);

      expect(manager.isFeatureAvailable('extension_list')).toBe(true); // read-only
      expect(manager.isFeatureAvailable('extension_install')).toBe(false); // requires write
      expect(manager.isFeatureAvailable('extension_status')).toBe(true); // read-only
    });

    it('should only allow high priority features in limited mode', () => {
      const error = ExtensionAuthErrorFactory.createTokenExpiredError();
      manager.applyDegradation(error);

      expect(manager.isFeatureAvailable('extension_list')).toBe(true); // priority 10
      expect(manager.isFeatureAvailable('extension_install')).toBe(false); // priority 5
      expect(manager.isFeatureAvailable('background_tasks')).toBe(true); // priority 8
    });

    it('should only allow cached features in cached mode', () => {
      const error = ExtensionAuthErrorFactory.createServiceUnavailableError();
      manager.applyDegradation(error);

      // Cache some data first
      manager.cacheData('extension_list', { extensions: [] }, 'test');

      expect(manager.isFeatureAvailable('extension_list')).toBe(true); // cached
      expect(manager.isFeatureAvailable('extension_install')).toBe(false); // not cacheable
    });

    it('should return false for all features in disabled mode', () => {
      const error = ExtensionAuthErrorFactory.createConfigurationError();
      manager.applyDegradation(error);

      expect(manager.isFeatureAvailable('extension_list')).toBe(false);
      expect(manager.isFeatureAvailable('extension_install')).toBe(false);
      expect(manager.isFeatureAvailable('background_tasks')).toBe(false);
    });
  });

  describe('getFallbackData', () => {
    it('should return cached data when available', () => {
      const testData = { extensions: [{ name: 'test' }] };
      manager.cacheData('extension_list', testData, 'test');

      const fallback = manager.getFallbackData('extension_list');
      expect(fallback).toEqual(testData);
    });

    it('should return static fallback when no cached data', () => {
      const fallback = manager.getFallbackData('extension_list');
      expect(fallback).toBeDefined();
      expect(fallback.extensions).toEqual([]);
      expect(fallback.message).toBe('Extension list temporarily unavailable');
    });

    it('should return null for non-fallback features', () => {
      manager.registerFeature({
        name: 'test_feature',
        displayName: 'Test Feature',
        description: 'Test',
        requiresAuth: true,
        requiresWrite: false,
        fallbackAvailable: false,
        cacheSupported: false,
        priority: 5
      });

      const fallback = manager.getFallbackData('test_feature');
      expect(fallback).toBeNull();
    });
  });

  describe('cacheData', () => {
    it('should cache data with default TTL', () => {
      const testData = { test: 'data' };
      manager.cacheData('test_key', testData, 'test_source');

      const cached = manager.getCachedData('test_key');
      expect(cached).toEqual(testData);
    });

    it('should cache data with custom TTL', () => {
      const testData = { test: 'data' };
      const customTTL = 1000; // 1 second
      manager.cacheData('test_key', testData, 'test_source', customTTL);

      const cached = manager.getCachedData('test_key');
      expect(cached).toEqual(testData);
    });

    it('should evict expired data', async () => {
      const testData = { test: 'data' };
      const shortTTL = 10; // 10ms
      manager.cacheData('test_key', testData, 'test_source', shortTTL);

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 20));

      const cached = manager.getCachedData('test_key');
      expect(cached).toBeNull();
    });
  });

  describe('hasCachedData', () => {
    it('should return true when cached data exists', () => {
      manager.cacheData('test_key', { test: 'data' }, 'test');
      expect(manager.hasCachedData('test_key')).toBe(true);
    });

    it('should return false when no cached data exists', () => {
      expect(manager.hasCachedData('nonexistent_key')).toBe(false);
    });
  });

  describe('clearCache', () => {
    it('should clear all cached data', () => {
      manager.cacheData('key1', { data: 1 }, 'test');
      manager.cacheData('key2', { data: 2 }, 'test');

      expect(manager.hasCachedData('key1')).toBe(true);
      expect(manager.hasCachedData('key2')).toBe(true);

      manager.clearCache();

      expect(manager.hasCachedData('key1')).toBe(false);
      expect(manager.hasCachedData('key2')).toBe(false);
    });
  });

  describe('getCacheStats', () => {
    it('should return correct cache statistics', () => {
      manager.cacheData('key1', { data: 1 }, 'source1');
      manager.cacheData('key2', { data: 2 }, 'source2');

      const stats = manager.getCacheStats();
      expect(stats.size).toBe(2);
      expect(stats.entries).toHaveLength(2);
      expect(stats.entries[0].key).toBeDefined();
      expect(stats.entries[0].age).toBeGreaterThanOrEqual(0);
      expect(stats.entries[0].source).toBeDefined();
    });
  });

  describe('registerFeature', () => {
    it('should register custom feature configuration', () => {
      const customFeature = {
        name: 'custom_feature',
        displayName: 'Custom Feature',
        description: 'A custom feature',
        requiresAuth: true,
        requiresWrite: true,
        fallbackAvailable: true,
        cacheSupported: true,
        priority: 6
      };

      manager.registerFeature(customFeature);

      const config = manager.getFeatureConfig('custom_feature');
      expect(config).toEqual(customFeature);
    });
  });

  describe('getFeatureConfig', () => {
    it('should return feature configuration', () => {
      const config = manager.getFeatureConfig('extension_list');
      expect(config).toBeDefined();
      expect(config?.name).toBe('extension_list');
      expect(config?.displayName).toBe('Extension List');
    });

    it('should return undefined for non-existent feature', () => {
      const config = manager.getFeatureConfig('nonexistent_feature');
      expect(config).toBeUndefined();
    });
  });

  describe('getAllFeatureConfigs', () => {
    it('should return all feature configurations', () => {
      const configs = manager.getAllFeatureConfigs();
      expect(configs.length).toBeGreaterThan(0);
      expect(configs.some(c => c.name === 'extension_list')).toBe(true);
      expect(configs.some(c => c.name === 'background_tasks')).toBe(true);
    });
  });
});

describe('Global degradation manager instance', () => {
  it('should provide singleton instance', () => {
    const instance1 = ExtensionAuthDegradationManager.getInstance();
    const instance2 = ExtensionAuthDegradationManager.getInstance();
    expect(instance1).toBe(instance2);
  });

  it('should be accessible via exported constant', () => {
    expect(extensionAuthDegradationManager).toBeInstanceOf(ExtensionAuthDegradationManager);
  });
});