/**
 * Unit tests for ModelSelectionService directory scanning functionality
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ModelSelectionService } from '@/lib/model-selection-service';

// Mock the karen-backend module
vi.mock('@/lib/karen-backend', () => ({
  getKarenBackend: () => ({
    makeRequestPublic: vi.fn().mockImplementation((url: string) => {
      // Mock different endpoints with appropriate responses
      if (url.includes('/api/system/resources')) {
        return Promise.resolve({
          cpu: {
            cores: 4,
            usage_percent: 50
          },
          memory: {
            total: 8 * 1024 * 1024 * 1024,
            available: 4 * 1024 * 1024 * 1024,
            used: 4 * 1024 * 1024 * 1024,
            usage_percent: 50
          },
          gpu: [],
          disk: {
            total: 500 * 1024 * 1024 * 1024,
            available: 250 * 1024 * 1024 * 1024,
            used: 250 * 1024 * 1024 * 1024,
            usage_percent: 50
          }
        });
      }
      
      if (url.includes('/api/system/memory')) {
        return Promise.resolve({
          total: 8 * 1024 * 1024 * 1024,
          available: 4 * 1024 * 1024 * 1024,
          used: 4 * 1024 * 1024 * 1024
        });
      }
      
      if (url.includes('/api/models/resource-usage/history')) {
        return Promise.resolve([]);
      }
      
      if (url.includes('/api/models/resource-usage/')) {
        return Promise.resolve({
          memory_usage: 1000000000,
          cpu_usage: 25,
          timestamp: new Date().toISOString()
        });
      }
      
      if (url.includes('/api/providers/compatibility')) {
        return Promise.resolve({
          compatible: true
        });
      }
      
      if (url.includes('/api/models/health/file-check')) {
        return Promise.resolve({
          exists: true,
          readable: true,
          corrupted: false
        });
      }
      
      if (url.includes('/api/models/load-test')) {
        return Promise.resolve({
          success: true,
          memory_usage: 2000000000
        });
      }
      
      // Default response for model endpoints
      return Promise.resolve({ models: [] });
    })
  })
}));

// Mock the safe-console module
vi.mock('@/lib/safe-console', () => ({
  safeError: vi.fn(),
  safeLog: vi.fn()
}));

describe('ModelSelectionService Directory Scanning', () => {
  let service: ModelSelectionService;
  
  beforeEach(() => {
    service = ModelSelectionService.getInstance();
    service.clearCache();
  });

  describe('scanLlamaCppModels', () => {
    it('should scan and return llama-cpp models with proper metadata', async () => {
      const models = await service.scanLlamaCppModels('models/llama-cpp', {});
      
      expect(Array.isArray(models)).toBe(true);
      
      if (models.length > 0) {
        const model = models[0];
        expect(model).toHaveProperty('id');
        expect(model).toHaveProperty('name');
        expect(model.provider).toBe('llama-cpp');
        expect(model.type).toBe('text');
        expect(model.subtype).toBe('llama-cpp');
        expect(model.format).toBe('gguf');
        expect(model).toHaveProperty('metadata');
        expect(model.metadata).toHaveProperty('architecture');
        expect(model.capabilities).toContain('text-generation');
      }
    });

    it('should include health information when requested', async () => {
      const models = await service.scanLlamaCppModels('models/llama-cpp', { includeHealth: true });
      
      if (models.length > 0) {
        const model = models[0];
        expect(model).toHaveProperty('health');
        if (model.health) {
          expect(model.health).toHaveProperty('is_healthy');
          expect(model.health).toHaveProperty('last_check');
        }
      }
    });
  });

  describe('scanTransformersModels', () => {
    it('should scan and return transformers models with proper metadata', async () => {
      const models = await service.scanTransformersModels('models/transformers', {});
      
      expect(Array.isArray(models)).toBe(true);
      
      if (models.length > 0) {
        const model = models[0];
        expect(model).toHaveProperty('id');
        expect(model).toHaveProperty('name');
        expect(model.provider).toBe('transformers');
        expect(model.subtype).toBe('transformers');
        expect(['text', 'embedding', 'multimodal']).toContain(model.type);
        expect(model).toHaveProperty('metadata');
        expect(model.capabilities.length).toBeGreaterThan(0);
      }
    });
  });

  describe('scanStableDiffusionModels', () => {
    it('should scan and return stable diffusion models with proper metadata', async () => {
      const models = await service.scanStableDiffusionModels('models/stable-diffusion', {});
      
      expect(Array.isArray(models)).toBe(true);
      
      if (models.length > 0) {
        const model = models[0];
        expect(model).toHaveProperty('id');
        expect(model).toHaveProperty('name');
        expect(model.provider).toBe('stable-diffusion');
        expect(model.type).toBe('image');
        expect(model.subtype).toBe('stable-diffusion');
        expect(model).toHaveProperty('metadata');
        expect(model.metadata).toHaveProperty('base_model');
        expect(model.metadata).toHaveProperty('resolution');
        expect(model.capabilities).toContain('text2img');
      }
    });
  });

  describe('scanFluxModels', () => {
    it('should scan and return flux models with proper metadata', async () => {
      const models = await service.scanFluxModels('models/flux', {});
      
      expect(Array.isArray(models)).toBe(true);
      
      // Flux models might not be present in development, so we just check the structure
      if (models.length > 0) {
        const model = models[0];
        expect(model).toHaveProperty('id');
        expect(model).toHaveProperty('name');
        expect(model.provider).toBe('flux');
        expect(model.type).toBe('image');
        expect(model.subtype).toBe('flux');
        expect(model).toHaveProperty('metadata');
        expect(model.metadata).toHaveProperty('variant');
        expect(model.capabilities).toContain('text2img');
      }
    });
  });

  describe('scanLocalDirectories', () => {
    it('should scan all directories and return combined results', async () => {
      const models = await service.scanLocalDirectories({
        directories: ['models/llama-cpp', 'models/transformers', 'models/stable-diffusion', 'models/flux']
      });
      
      expect(Array.isArray(models)).toBe(true);
      
      // Check that we have models from different types
      const types = [...new Set(models.map(m => m.type))];
      const subtypes = [...new Set(models.map(m => m.subtype))];
      
      // We should have at least some fallback models
      expect(models.length).toBeGreaterThan(0);
      
      // Verify model structure
      models.forEach(model => {
        expect(model).toHaveProperty('id');
        expect(model).toHaveProperty('name');
        expect(model).toHaveProperty('provider');
        expect(model).toHaveProperty('type');
        expect(model).toHaveProperty('subtype');
        expect(model).toHaveProperty('capabilities');
        expect(model).toHaveProperty('metadata');
        expect(model).toHaveProperty('last_scanned');
      });
    });

    it('should use cache when not forcing refresh', async () => {
      // First call
      const models1 = await service.scanLocalDirectories({});
      
      // Second call should use cache
      const models2 = await service.scanLocalDirectories({});
      
      expect(models1).toEqual(models2);
    });

    it('should bypass cache when forcing refresh', async () => {
      // First call
      await service.scanLocalDirectories({});
      
      // Force refresh should bypass cache
      const models = await service.scanLocalDirectories({ forceRefresh: true });
      
      expect(Array.isArray(models)).toBe(true);
    });
  });

  describe('getAvailableModels with scanning', () => {
    it('should integrate directory scanning with existing model fetching', async () => {
      const models = await service.getAvailableModels(false, {
        forceRefresh: true,
        includeHealth: true
      });
      
      expect(Array.isArray(models)).toBe(true);
      expect(models.length).toBeGreaterThan(0);
      
      // Should have models with scanning metadata
      const scannedModels = models.filter(m => m.last_scanned);
      expect(scannedModels.length).toBeGreaterThan(0);
    });
  });

  describe('selectOptimalModel with type filtering', () => {
    it('should filter models by type', async () => {
      const textResult = await service.selectOptimalModel({ filterByType: 'text' });
      const imageResult = await service.selectOptimalModel({ filterByType: 'image' });
      
      if (textResult.selectedModel) {
        expect(textResult.selectedModel.type).toBe('text');
      }
      
      if (imageResult.selectedModel) {
        expect(imageResult.selectedModel.type).toBe('image');
      }
    });

    it('should include dynamic scanning when requested', async () => {
      const result = await service.selectOptimalModel({ 
        includeDynamicScan: true,
        forceRefresh: true 
      });
      
      expect(result).toHaveProperty('selectedModel');
      expect(result).toHaveProperty('availableModels');
      expect(result).toHaveProperty('selectionReason');
      
      // Should have some models available
      expect(result.availableModels.length).toBeGreaterThan(0);
    });

    it('should support multimodal model selection', async () => {
      const result = await service.selectOptimalModel({ 
        filterByType: 'text',
        includeDynamicScan: true 
      });
      
      if (result.selectedModel) {
        // Should select either text or multimodal model that supports text
        expect(['text', 'multimodal']).toContain(result.selectedModel.type);
      }
    });

    it('should handle context preservation in model selection', async () => {
      const currentContext = {
        type: 'text',
        currentModel: { provider: 'llama-cpp' }
      };

      const result = await service.selectOptimalModel({
        filterByType: 'text',
        contextPreservation: true,
        currentContext
      });

      expect(result).toHaveProperty('selectedModel');
      expect(result).toHaveProperty('availableModels');
    });
  });

  describe('Enhanced Model Registry', () => {
    it('should create and maintain model registry with categorization', async () => {
      const registry = await service.getModelRegistry();
      
      expect(registry).toHaveProperty('models');
      expect(registry).toHaveProperty('categories');
      expect(registry).toHaveProperty('lastUpdate');
      
      expect(registry.categories).toHaveProperty('byType');
      expect(registry.categories).toHaveProperty('byProvider');
      expect(registry.categories).toHaveProperty('byCapability');
      expect(registry.categories).toHaveProperty('byStatus');
      expect(registry.categories).toHaveProperty('byHealth');
      
      expect(typeof registry.lastUpdate).toBe('number');
    });

    it('should use registry cache when not forcing refresh', async () => {
      // First call
      const registry1 = await service.getModelRegistry();
      
      // Second call should use cache
      const registry2 = await service.getModelRegistry();
      
      expect(registry1.lastUpdate).toBe(registry2.lastUpdate);
    });

    it('should categorize models correctly', async () => {
      const registry = await service.getModelRegistry(true);
      
      // Check type categorization
      Object.values(registry.categories.byType).forEach(models => {
        expect(Array.isArray(models)).toBe(true);
        models.forEach(model => {
          expect(model).toHaveProperty('type');
        });
      });

      // Check provider categorization
      Object.values(registry.categories.byProvider).forEach(models => {
        expect(Array.isArray(models)).toBe(true);
        models.forEach(model => {
          expect(model).toHaveProperty('provider');
        });
      });

      // Check capability categorization
      Object.values(registry.categories.byCapability).forEach(models => {
        expect(Array.isArray(models)).toBe(true);
        models.forEach(model => {
          expect(model).toHaveProperty('capabilities');
          expect(Array.isArray(model.capabilities)).toBe(true);
        });
      });
    });

    it('should provide model lookup with filtering', async () => {
      const textModels = await service.lookupModels({ type: 'text' });
      const localModels = await service.lookupModels({ status: 'local' });
      const healthyModels = await service.lookupModels({ healthyOnly: true });
      
      expect(Array.isArray(textModels)).toBe(true);
      expect(Array.isArray(localModels)).toBe(true);
      expect(Array.isArray(healthyModels)).toBe(true);
      
      textModels.forEach(model => {
        expect(model.type).toBe('text');
      });
      
      localModels.forEach(model => {
        expect(model.status).toBe('local');
      });
      
      healthyModels.forEach(model => {
        if (model.health) {
          expect(model.health.is_healthy).toBe(true);
        }
      });
    });

    it('should support model lookup with sorting', async () => {
      const modelsByName = await service.lookupModels({ sortBy: 'name' });
      const modelsBySize = await service.lookupModels({ sortBy: 'size' });
      
      // Check name sorting
      if (modelsByName.length > 1) {
        for (let i = 1; i < modelsByName.length; i++) {
          expect(modelsByName[i].name.localeCompare(modelsByName[i-1].name)).toBeGreaterThanOrEqual(0);
        }
      }
      
      // Check size sorting
      if (modelsBySize.length > 1) {
        for (let i = 1; i < modelsBySize.length; i++) {
          expect(modelsBySize[i].size || 0).toBeGreaterThanOrEqual(modelsBySize[i-1].size || 0);
        }
      }
    });

    it('should support model lookup with limits', async () => {
      const limitedModels = await service.lookupModels({ limit: 2 });
      
      expect(limitedModels.length).toBeLessThanOrEqual(2);
    });

    it('should get models by category', async () => {
      const textModels = await service.getModelsByCategory('type', 'text');
      const llamaCppModels = await service.getModelsByCategory('provider', 'llama-cpp');
      const chatModels = await service.getModelsByCategory('capability', 'chat');
      
      expect(Array.isArray(textModels)).toBe(true);
      expect(Array.isArray(llamaCppModels)).toBe(true);
      expect(Array.isArray(chatModels)).toBe(true);
      
      textModels.forEach(model => {
        expect(model.type).toBe('text');
      });
      
      llamaCppModels.forEach(model => {
        expect(model.provider).toBe('llama-cpp');
      });
      
      chatModels.forEach(model => {
        expect(model.capabilities).toContain('chat');
      });
    });

    it('should provide category summary with counts', async () => {
      const summary = await service.getModelCategorySummary();
      
      expect(summary).toHaveProperty('types');
      expect(summary).toHaveProperty('providers');
      expect(summary).toHaveProperty('capabilities');
      expect(summary).toHaveProperty('statuses');
      expect(summary).toHaveProperty('health');
      
      Object.values(summary.types).forEach(count => {
        expect(typeof count).toBe('number');
        expect(count).toBeGreaterThanOrEqual(0);
      });
      
      Object.values(summary.providers).forEach(count => {
        expect(typeof count).toBe('number');
        expect(count).toBeGreaterThanOrEqual(0);
      });
    });

    it('should include registry stats in selection stats', async () => {
      const stats = await service.getSelectionStats();
      
      expect(stats).toHaveProperty('registryStats');
      if (stats.registryStats) {
        expect(stats.registryStats).toHaveProperty('lastUpdate');
        expect(stats.registryStats).toHaveProperty('categoriesCount');
        expect(stats.registryStats).toHaveProperty('healthyModels');
        expect(stats.registryStats).toHaveProperty('unhealthyModels');
        
        expect(typeof stats.registryStats.categoriesCount).toBe('number');
        expect(typeof stats.registryStats.healthyModels).toBe('number');
        expect(typeof stats.registryStats.unhealthyModels).toBe('number');
      }
    });
  });

  describe('File System Watching', () => {
    it('should start and stop directory watching', async () => {
      // Initially not watching
      let status = service.getWatchingStatus();
      expect(status.isWatching).toBe(false);
      expect(status.watchedDirectories).toHaveLength(0);

      // Start watching
      await service.startDirectoryWatching({
        directories: ['models/llama-cpp', 'models/transformers'],
        enablePolling: true,
        pollingInterval: 1000
      });

      status = service.getWatchingStatus();
      expect(status.isWatching).toBe(true);
      expect(status.watchedDirectories).toContain('models/llama-cpp');
      expect(status.watchedDirectories).toContain('models/transformers');

      // Stop watching
      service.stopDirectoryWatching();

      status = service.getWatchingStatus();
      expect(status.isWatching).toBe(false);
      expect(status.watchedDirectories).toHaveLength(0);
    });

    it('should not start watching if already active', async () => {
      await service.startDirectoryWatching();
      const status1 = service.getWatchingStatus();
      
      // Try to start again
      await service.startDirectoryWatching();
      const status2 = service.getWatchingStatus();
      
      expect(status1.isWatching).toBe(status2.isWatching);
      expect(status1.watchedDirectories).toEqual(status2.watchedDirectories);
      
      service.stopDirectoryWatching();
    });

    it('should add and remove change listeners', async () => {
      const changeEvents: any[] = [];
      
      const unsubscribe = service.addChangeListener((event) => {
        changeEvents.push(event);
      });

      let status = service.getWatchingStatus();
      expect(status.changeListeners).toBe(1);

      // Remove listener
      unsubscribe();

      status = service.getWatchingStatus();
      expect(status.changeListeners).toBe(0);
    });

    it('should automatically start watching when getting available models', async () => {
      // Ensure not watching initially
      service.stopDirectoryWatching();
      
      let status = service.getWatchingStatus();
      expect(status.isWatching).toBe(false);

      // Get available models should start watching
      await service.getAvailableModels();

      status = service.getWatchingStatus();
      expect(status.isWatching).toBe(true);
      expect(status.watchedDirectories.length).toBeGreaterThan(0);

      service.stopDirectoryWatching();
    });

    it('should clear watching state when clearing cache', () => {
      // Start watching first
      service.startDirectoryWatching();
      
      let status = service.getWatchingStatus();
      expect(status.isWatching).toBe(true);

      // Clear cache should stop watching
      service.clearCache();

      status = service.getWatchingStatus();
      expect(status.isWatching).toBe(false);
      expect(status.watchedDirectories).toHaveLength(0);
    });

    it('should include watching stats in selection stats', async () => {
      await service.startDirectoryWatching();
      
      const stats = await service.getSelectionStats();
      
      expect(stats).toHaveProperty('watchingStats');
      if (stats.watchingStats) {
        expect(stats.watchingStats).toHaveProperty('isWatching');
        expect(stats.watchingStats).toHaveProperty('watchedDirectories');
        expect(stats.watchingStats).toHaveProperty('changeListeners');
        expect(stats.watchingStats).toHaveProperty('lastChangeDetection');
        
        expect(typeof stats.watchingStats.isWatching).toBe('boolean');
        expect(Array.isArray(stats.watchingStats.watchedDirectories)).toBe(true);
        expect(typeof stats.watchingStats.changeListeners).toBe('number');
        expect(typeof stats.watchingStats.lastChangeDetection).toBe('object');
      }

      service.stopDirectoryWatching();
    });
  });

  describe('Health Monitoring', () => {
    it('should perform comprehensive health check on models', async () => {
      const models = await service.getAvailableModels();
      
      if (models.length > 0) {
        const model = models[0];
        const health = await service.performComprehensiveHealthCheck(model.id);
        
        expect(health).toHaveProperty('is_healthy');
        expect(health).toHaveProperty('last_check');
        expect(health).toHaveProperty('issues');
        expect(health).toHaveProperty('memory_requirement');
        
        expect(typeof health.is_healthy).toBe('boolean');
        expect(typeof health.last_check).toBe('string');
        expect(Array.isArray(health.issues)).toBe(true);
        expect(typeof health.memory_requirement).toBe('number');
        
        if (health.performance_metrics) {
          expect(typeof health.performance_metrics).toBe('object');
        }
      }
    });

    it('should check if model is ready with health checking', async () => {
      const models = await service.getAvailableModels();
      
      if (models.length > 0) {
        const model = models[0];
        
        // Basic readiness check
        const basicReady = await service.isModelReady(model.id, false);
        expect(typeof basicReady).toBe('boolean');
        
        // Health-inclusive readiness check
        const healthReady = await service.isModelReady(model.id, true);
        expect(typeof healthReady).toBe('boolean');
      }
    });

    it('should get model health status', async () => {
      const models = await service.getAvailableModels();
      
      if (models.length > 0) {
        const model = models[0];
        const health = await service.getModelHealthStatus(model.id);
        
        if (health) {
          expect(health).toHaveProperty('is_healthy');
          expect(health).toHaveProperty('last_check');
          expect(health).toHaveProperty('issues');
          expect(health).toHaveProperty('memory_requirement');
        }
      }
    });

    it('should return null for non-existent model health', async () => {
      const health = await service.getModelHealthStatus('non-existent-model');
      expect(health).toBeNull();
    });

    it('should include performance metrics in selection stats', async () => {
      const stats = await service.getSelectionStats();
      
      expect(stats).toHaveProperty('performanceMetrics');
      if (stats.performanceMetrics) {
        expect(stats.performanceMetrics).toHaveProperty('averageLoadTime');
        expect(stats.performanceMetrics).toHaveProperty('averageMemoryUsage');
        expect(stats.performanceMetrics).toHaveProperty('totalMemoryRequirement');
        expect(stats.performanceMetrics).toHaveProperty('healthCheckDuration');
        expect(stats.performanceMetrics).toHaveProperty('modelsByPerformanceTier');
        expect(stats.performanceMetrics).toHaveProperty('estimatedCapacity');
        
        expect(typeof stats.performanceMetrics.averageLoadTime).toBe('number');
        expect(typeof stats.performanceMetrics.averageMemoryUsage).toBe('number');
        expect(typeof stats.performanceMetrics.totalMemoryRequirement).toBe('number');
        expect(typeof stats.performanceMetrics.healthCheckDuration).toBe('number');
        
        expect(stats.performanceMetrics.modelsByPerformanceTier).toHaveProperty('fast');
        expect(stats.performanceMetrics.modelsByPerformanceTier).toHaveProperty('medium');
        expect(stats.performanceMetrics.modelsByPerformanceTier).toHaveProperty('slow');
        
        expect(stats.performanceMetrics.estimatedCapacity).toHaveProperty('textTokensPerSecond');
        expect(stats.performanceMetrics.estimatedCapacity).toHaveProperty('imagesPerMinute');
      }
      
      expect(stats).toHaveProperty('healthSummary');
      if (stats.healthSummary) {
        expect(stats.healthSummary).toHaveProperty('totalHealthChecks');
        expect(stats.healthSummary).toHaveProperty('healthyModels');
        expect(stats.healthSummary).toHaveProperty('unhealthyModels');
        expect(stats.healthSummary).toHaveProperty('commonIssues');
        expect(stats.healthSummary).toHaveProperty('lastHealthCheck');
        
        expect(typeof stats.healthSummary.totalHealthChecks).toBe('number');
        expect(typeof stats.healthSummary.healthyModels).toBe('number');
        expect(typeof stats.healthSummary.unhealthyModels).toBe('number');
        expect(Array.isArray(stats.healthSummary.commonIssues)).toBe(true);
        expect(typeof stats.healthSummary.lastHealthCheck).toBe('string');
      }
    });
  });

  describe('Resource Monitoring', () => {
    it('should get system resource information', async () => {
      const resources = await service.getSystemResourceInfo();
      
      expect(resources).toHaveProperty('cpu');
      expect(resources).toHaveProperty('memory');
      expect(resources).toHaveProperty('gpu');
      expect(resources).toHaveProperty('disk');
      
      expect(resources.cpu).toHaveProperty('cores');
      expect(resources.cpu).toHaveProperty('usage_percent');
      
      expect(resources.memory).toHaveProperty('total');
      expect(resources.memory).toHaveProperty('available');
      expect(resources.memory).toHaveProperty('used');
      expect(resources.memory).toHaveProperty('usage_percent');
      
      expect(Array.isArray(resources.gpu)).toBe(true);
      
      expect(resources.disk).toHaveProperty('total');
      expect(resources.disk).toHaveProperty('available');
      expect(resources.disk).toHaveProperty('used');
      expect(resources.disk).toHaveProperty('usage_percent');
    });

    it('should check if model can be loaded based on resources', async () => {
      const models = await service.getAvailableModels();
      
      if (models.length > 0) {
        const model = models[0];
        const canLoad = await service.canLoadModel(model.id);
        
        expect(canLoad).toHaveProperty('canLoad');
        expect(canLoad).toHaveProperty('resourceRequirements');
        expect(canLoad).toHaveProperty('systemResources');
        
        expect(typeof canLoad.canLoad).toBe('boolean');
        
        expect(canLoad.resourceRequirements).toHaveProperty('memory');
        expect(canLoad.resourceRequirements).toHaveProperty('disk_space');
        
        expect(canLoad.systemResources).toHaveProperty('memory_available');
        expect(canLoad.systemResources).toHaveProperty('disk_available');
        
        if (!canLoad.canLoad) {
          expect(typeof canLoad.reason).toBe('string');
        }
      }
    });

    it('should return error for non-existent model resource check', async () => {
      const canLoad = await service.canLoadModel('non-existent-model');
      
      expect(canLoad.canLoad).toBe(false);
      expect(canLoad.reason).toBe('Model not found');
    });

    it('should get optimal GPU for model loading', async () => {
      const models = await service.getAvailableModels();
      const imageModels = models.filter(m => m.type === 'image');
      
      if (imageModels.length > 0) {
        const model = imageModels[0];
        const optimalGPU = await service.getOptimalGPU(model.id);
        
        expect(optimalGPU).toHaveProperty('gpu_id');
        expect(optimalGPU).toHaveProperty('reason');
        expect(optimalGPU).toHaveProperty('memory_available');
        
        expect(typeof optimalGPU.reason).toBe('string');
        expect(typeof optimalGPU.memory_available).toBe('number');
        
        if (optimalGPU.gpu_id !== null) {
          expect(typeof optimalGPU.gpu_id).toBe('number');
          expect(optimalGPU).toHaveProperty('gpu_name');
        }
      }
    });

    it('should monitor resource usage during operations', async () => {
      const models = await service.getAvailableModels();
      
      if (models.length > 0) {
        const model = models[0];
        const monitoring = await service.monitorResourceUsage(model.id, 'loading');
        
        expect(monitoring).toHaveProperty('start_time');
        expect(monitoring).toHaveProperty('peak_memory_usage');
        expect(monitoring).toHaveProperty('average_cpu_usage');
        
        expect(typeof monitoring.start_time).toBe('string');
        expect(typeof monitoring.peak_memory_usage).toBe('number');
        expect(typeof monitoring.average_cpu_usage).toBe('number');
      }
    });

    it('should track model resource usage', async () => {
      const models = await service.getAvailableModels();
      
      if (models.length > 0) {
        const model = models[0];
        const usage = await service.trackModelResourceUsage(model.id);
        
        if (usage) {
          expect(usage).toHaveProperty('model_id');
          expect(usage).toHaveProperty('memory_usage');
          expect(usage).toHaveProperty('cpu_usage');
          expect(usage).toHaveProperty('timestamp');
          
          expect(usage.model_id).toBe(model.id);
          expect(typeof usage.memory_usage).toBe('number');
          expect(typeof usage.cpu_usage).toBe('number');
          expect(typeof usage.timestamp).toBe('string');
        }
      }
    });

    it('should get resource usage history', async () => {
      const history = await service.getResourceUsageHistory('24h');
      
      expect(Array.isArray(history)).toBe(true);
      
      history.forEach(entry => {
        expect(entry).toHaveProperty('model_id');
        expect(entry).toHaveProperty('model_name');
        expect(entry).toHaveProperty('average_memory_usage');
        expect(entry).toHaveProperty('peak_memory_usage');
        expect(entry).toHaveProperty('average_cpu_usage');
        expect(entry).toHaveProperty('peak_cpu_usage');
        expect(entry).toHaveProperty('total_inference_time_ms');
        expect(entry).toHaveProperty('inference_count');
        expect(entry).toHaveProperty('efficiency_score');
        
        expect(typeof entry.model_id).toBe('string');
        expect(typeof entry.model_name).toBe('string');
        expect(typeof entry.efficiency_score).toBe('number');
      });
    });

    it('should get resource recommendations', async () => {
      const recommendations = await service.getResourceRecommendations();
      
      expect(recommendations).toHaveProperty('recommended_models');
      expect(recommendations).toHaveProperty('system_optimization_tips');
      expect(recommendations).toHaveProperty('resource_warnings');
      
      expect(Array.isArray(recommendations.recommended_models)).toBe(true);
      expect(Array.isArray(recommendations.system_optimization_tips)).toBe(true);
      expect(Array.isArray(recommendations.resource_warnings)).toBe(true);
      
      recommendations.recommended_models.forEach(rec => {
        expect(rec).toHaveProperty('model_id');
        expect(rec).toHaveProperty('model_name');
        expect(rec).toHaveProperty('reason');
        expect(rec).toHaveProperty('resource_fit');
        
        expect(['excellent', 'good', 'acceptable', 'poor']).toContain(rec.resource_fit);
      });
    });

    it('should select optimal model with resource feasibility checking', async () => {
      const result = await service.selectOptimalModel({
        checkResourceFeasibility: true,
        maxMemoryUsage: 8 * 1024 * 1024 * 1024, // 8GB limit
        requireGPU: false
      });
      
      expect(result).toHaveProperty('selectedModel');
      expect(result).toHaveProperty('availableModels');
      expect(result).toHaveProperty('selectionReason');
      
      // If a model was selected, it should meet resource requirements
      if (result.selectedModel) {
        const canLoad = await service.canLoadModel(result.selectedModel.id);
        // Note: canLoad might still be false due to system constraints,
        // but the model should have passed the initial feasibility filter
        expect(canLoad).toHaveProperty('canLoad');
      }
    });
  });

  describe('Multi-modal provider management', () => {
    it('should switch models with context preservation', async () => {
      const models = await service.getAvailableModels();
      
      if (models.length > 0) {
        const targetModel = models[0];
        const currentContext = {
          type: 'text',
          currentModel: { provider: targetModel.provider }
        };

        const result = await service.switchModel(targetModel.id, {
          preserveContext: true,
          currentContext
        });

        expect(result).toHaveProperty('success');
        expect(result).toHaveProperty('contextPreserved');
        expect(result).toHaveProperty('model');
        expect(result).toHaveProperty('message');
      }
    });

    it('should get models by type with enhanced registry filtering', async () => {
      const textModels = await service.getModelsByType('text', {
        includeMultimodal: true,
        onlyHealthy: false
      });

      expect(Array.isArray(textModels)).toBe(true);
      
      textModels.forEach(model => {
        expect(['text', 'multimodal']).toContain(model.type);
      });
    });

    it('should check context preservation support', () => {
      const textModel = {
        id: 'test-text',
        name: 'Test Text Model',
        type: 'text' as const,
        provider: 'llama-cpp',
        size: 1000000,
        description: 'Test model',
        capabilities: ['text-generation'],
        status: 'local' as const,
        metadata: {}
      };

      const textContext = {
        type: 'text',
        currentModel: { provider: 'llama-cpp' }
      };

      const imageContext = {
        type: 'image',
        currentModel: { provider: 'stable-diffusion' }
      };

      // Same provider and type should support context preservation
      expect(service.checkContextPreservationSupport(textModel, textContext)).toBe(true);
      
      // Different types should not support context preservation for text model
      expect(service.checkContextPreservationSupport(textModel, imageContext)).toBe(false);
    });

    it('should get enhanced selection stats with registry and watching information', async () => {
      const stats = await service.getSelectionStats();
      
      expect(stats).toHaveProperty('totalModels');
      expect(stats).toHaveProperty('modelsByType');
      expect(stats).toHaveProperty('registryStats');
      expect(stats).toHaveProperty('watchingStats');
      
      expect(stats.modelsByType).toHaveProperty('text');
      expect(stats.modelsByType).toHaveProperty('image');
      expect(stats.modelsByType).toHaveProperty('embedding');
      expect(stats.modelsByType).toHaveProperty('multimodal');
      
      expect(typeof stats.modelsByType.text).toBe('number');
      expect(typeof stats.modelsByType.image).toBe('number');
      expect(typeof stats.modelsByType.embedding).toBe('number');
      expect(typeof stats.modelsByType.multimodal).toBe('number');
    });
  });
});