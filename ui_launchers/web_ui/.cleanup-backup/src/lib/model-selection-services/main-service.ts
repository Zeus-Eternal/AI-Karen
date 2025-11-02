/**
 * Main Model Selection Service - Orchestrates all modular services
 */

import type { Model, ModelLibraryResponse } from "../model-utils";
import { getKarenBackend } from "../karen-backend";

// Import modular services
import { ModelHealthMonitor } from "./health-monitor";
import { ResourceMonitor } from "./resource-monitor";
import { ModelScanner } from "./model-scanner";
import { BaseModelService } from "./base-service";
import { 
  ModelSelectionPreferences,
  ModelSelectionResult,
  ModelRegistry,
  ModelCategories,
  DirectoryWatchOptions,
  FileSystemChangeEvent,
  SelectOptimalModelOptions,
  ModelSwitchOptions,
  ModelSwitchResult,
  ModelsByTypeOptions,
  ModelSelectionStats
} from "./types";

export class ModelSelectionService extends BaseModelService {
  private static instance: ModelSelectionService;
  
  // Modular services
  private healthMonitor: ModelHealthMonitor;
  private resourceMonitor: ResourceMonitor;
  private modelScanner: ModelScanner;
  
  // Core state
  private cachedModels: Model[] = [];
  private modelRegistry: ModelRegistry | null = null;
  private lastFetchTime: number = 0;
  
  // File system watching
  private isWatching: boolean = false;
  private watchedDirectories: Set<string> = new Set();
  private changeListeners: Set<(event: FileSystemChangeEvent) => void> = new Set();
  private debounceTimers: Map<string, NodeJS.Timeout> = new Map();
  private lastChangeDetection: Map<string, number> = new Map();
  private pollingInterval: NodeJS.Timeout | null = null;

  private constructor() {
    super('ModelSelectionService');
    this.healthMonitor = new ModelHealthMonitor('ModelHealthMonitor');
    this.resourceMonitor = new ResourceMonitor('ResourceMonitor');
    this.modelScanner = new ModelScanner('ModelScanner', this.healthMonitor);
  }

  static getInstance(): ModelSelectionService {
    if (!ModelSelectionService.instance) {
      ModelSelectionService.instance = new ModelSelectionService();
    }
    return ModelSelectionService.instance;
  }

  // Export the modular services for direct access if needed
  get health() { return this.healthMonitor; }
  get resources() { return this.resourceMonitor; }
  get scanner() { return this.modelScanner; }

  // Core model selection methods
  async selectOptimalModel(options: SelectOptimalModelOptions = {}): Promise<ModelSelectionResult> {
    const {
      filterByCapability,
      filterByType,
      preferLocal = true,
      forceRefresh = false,
      includeDynamicScan = true,
      checkResourceFeasibility = true
    } = options;

    try {
      // Get available models with optional dynamic scanning
      const models = await this.getAvailableModels(forceRefresh, includeDynamicScan);
      
      // Filter models based on criteria
      let filteredModels = models;
      
      if (filterByType) {
        filteredModels = filteredModels.filter(model => 
          model.type === filterByType || 
          (model.type === 'multimodal' && model.capabilities?.includes(`${filterByType}-generation`))
        );
      }
      
      if (filterByCapability) {
        filteredModels = filteredModels.filter(model => 
          model.capabilities?.includes(filterByCapability)
        );
      }

      // Check resource feasibility if requested
      if (checkResourceFeasibility) {
        const feasibleModels = [];
        for (const model of filteredModels) {
          const canLoad = await this.resourceMonitor.canLoadModel(model);
          if (canLoad.canLoad) {
            feasibleModels.push(model);
          }
        }
        filteredModels = feasibleModels;
      }

      // Apply selection priority logic
      const preferences = await this.getPreferences();
      let selectedModel: Model | null = null;
      let selectionReason: ModelSelectionResult['selectionReason'] = 'none_available';

      // 1. Try last selected model
      if (preferences.lastSelectedModel) {
        const lastModel = filteredModels.find(m => m.id === preferences.lastSelectedModel);
        if (lastModel) {
          selectedModel = lastModel;
          selectionReason = 'last_selected';
        }
      }

      // 2. Try default model
      if (!selectedModel && preferences.defaultModel) {
        const defaultModel = filteredModels.find(m => m.id === preferences.defaultModel);
        if (defaultModel) {
          selectedModel = defaultModel;
          selectionReason = 'default';
        }
      }

      // 3. Select first available with preference logic
      if (!selectedModel && filteredModels.length > 0) {
        if (preferLocal) {
          // Prefer local models
          const localModels = filteredModels.filter(m => m.status === 'local');
          if (localModels.length > 0) {
            selectedModel = localModels[0];
          } else {
            selectedModel = filteredModels[0];
          }
        } else {
          selectedModel = filteredModels[0];
        }
        selectionReason = 'first_available';
      }

      return {
        selectedModel,
        selectionReason,
        availableModels: filteredModels,
        fallbackUsed: false
      };

    } catch (error) {
      console.error('Failed to select optimal model:', error);
      return {
        selectedModel: null,
        selectionReason: 'none_available',
        availableModels: [],
        fallbackUsed: false
      };
    }
  }

  async getAvailableModels(forceRefresh = false, includeDynamicScan = true): Promise<Model[]> {
    const now = Date.now();
    const cacheExpired = now - this.lastFetchTime > this.CACHE_DURATION;

    if (!forceRefresh && !cacheExpired && this.cachedModels.length > 0) {
      return this.cachedModels;
    }

    try {
      let models: Model[] = [];

      if (includeDynamicScan) {
        // Use dynamic scanning
        models = await this.modelScanner.scanLocalDirectories();
      } else {
        // Fallback to API
        const backend = getKarenBackend();
        const response = await backend.makeRequestPublic<ModelLibraryResponse>('/api/models/library');
        models = response?.models || [];
      }

      // Update health status for all models
      for (const model of models) {
        model.health = await this.healthMonitor.performComprehensiveHealthCheck(model);
      }

      this.cachedModels = models;
      this.lastFetchTime = now;
      
      return models;
    } catch (error) {
      console.error('Failed to get available models:', error);
      return this.cachedModels; // Return cached models as fallback
    }
  }

  async getModelById(modelId: string): Promise<Model | null> {
    const models = await this.getAvailableModels();
    return models.find(model => model.id === modelId) || null;
  }

  async isModelReady(modelId: string): Promise<boolean> {
    const model = await this.getModelById(modelId);
    if (!model) return false;
    
    return model.status === 'local' && (!model.health || model.health.is_healthy);
  }

  async switchModel(modelId: string, options: ModelSwitchOptions = {}): Promise<ModelSwitchResult> {
    const { preserveContext = true, forceSwitch = false } = options;
    
    try {
      const model = await this.getModelById(modelId);
      if (!model) {
        return {
          success: false,
          model: null,
          contextPreserved: false,
          message: 'Model not found'
        };
      }

      // Check if model can be loaded
      const canLoad = await this.resourceMonitor.canLoadModel(model);
      if (!canLoad.canLoad && !forceSwitch) {
        return {
          success: false,
          model: null,
          contextPreserved: false,
          message: canLoad.reason || 'Cannot load model'
        };
      }

      // Update last selected model
      await this.updateLastSelectedModel(modelId);

      return {
        success: true,
        model,
        contextPreserved: preserveContext,
        message: 'Model switched successfully'
      };

    } catch (error) {
      return {
        success: false,
        model: null,
        contextPreserved: false,
        message: error instanceof Error ? error.message : 'Failed to switch model'
      };
    }
  }

  // Model registry and categorization methods
  async getModelRegistry(): Promise<ModelRegistry> {
    if (!this.modelRegistry) {
      const models = await this.getAvailableModels();
      this.modelRegistry = this.buildModelRegistry(models);
    }
    return this.modelRegistry;
  }

  private buildModelRegistry(models: Model[]): ModelRegistry {
    const categories: ModelCategories = {
      byType: {},
      byProvider: {},
      byCapability: {},
      byStatus: {},
      byHealth: {}
    };

    // Categorize models
    models.forEach(model => {
      // By type
      const type = model.type || 'unknown';
      if (!categories.byType[type]) categories.byType[type] = [];
      categories.byType[type].push(model);

      // By provider
      if (!categories.byProvider[model.provider]) categories.byProvider[model.provider] = [];
      categories.byProvider[model.provider].push(model);

      // By capabilities
      model.capabilities?.forEach(capability => {
        if (!categories.byCapability[capability]) categories.byCapability[capability] = [];
        categories.byCapability[capability].push(model);
      });

      // By status
      if (!categories.byStatus[model.status]) categories.byStatus[model.status] = [];
      categories.byStatus[model.status].push(model);

      // By health
      const healthStatus = model.health?.is_healthy ? 'healthy' : 'unhealthy';
      if (!categories.byHealth[healthStatus]) categories.byHealth[healthStatus] = [];
      categories.byHealth[healthStatus].push(model);
    });

    return {
      models,
      categories,
      lastUpdate: Date.now(),
      scanMetadata: {
        last_scan: new Date().toISOString(),
        scan_version: '2.0',
        directories_scanned: ['models/llama-cpp', 'models/transformers', 'models/stable-diffusion', 'models/flux'],
        total_models_found: models.length,
        scan_duration_ms: 0
      }
    };
  }

  async getModelsByType(type: 'text' | 'image' | 'embedding' | 'multimodal', options: ModelsByTypeOptions = {}): Promise<Model[]> {
    const registry = await this.getModelRegistry();
    let models = registry.categories.byType[type] || [];

    if (options.includeMultimodal && type !== 'multimodal') {
      const multimodalModels = registry.categories.byType['multimodal'] || [];
      const relevantMultimodal = multimodalModels.filter(model => 
        model.capabilities?.includes(`${type}-generation`) || model.capabilities?.includes(type)
      );
      models = [...models, ...relevantMultimodal];
    }

    if (options.filterByCapability) {
      models = models.filter(model => model.capabilities?.includes(options.filterByCapability!));
    }

    if (options.onlyHealthy) {
      models = models.filter(model => !model.health || model.health.is_healthy);
    }

    // Sort models
    if (options.sortBy) {
      models.sort((a, b) => {
        switch (options.sortBy) {
          case 'name':
            return a.name.localeCompare(b.name);
          case 'size':
            return (a.size || 0) - (b.size || 0);
          case 'performance':
            // Sort by performance metrics if available
            const aPerf = a.health?.performance_metrics?.inference_speed || 0;
            const bPerf = b.health?.performance_metrics?.inference_speed || 0;
            return Number(bPerf) - Number(aPerf);
          case 'health':
            const aHealthy = a.health?.is_healthy ? 1 : 0;
            const bHealthy = b.health?.is_healthy ? 1 : 0;
            return bHealthy - aHealthy;
          default:
            return 0;
        }
      });
    }

    return models;
  }

  async getModelCategorySummary(): Promise<any> {
    const registry = await this.getModelRegistry();
    
    return {
      types: Object.fromEntries(
        Object.entries(registry.categories.byType).map(([type, models]) => [type, models.length])
      ),
      providers: Object.fromEntries(
        Object.entries(registry.categories.byProvider).map(([provider, models]) => [provider, models.length])
      ),
      status: Object.fromEntries(
        Object.entries(registry.categories.byStatus).map(([status, models]) => [status, models.length])
      ),
      health: Object.fromEntries(
        Object.entries(registry.categories.byHealth).map(([health, models]) => [health, models.length])
      )
    };
  }

  // Statistics and monitoring methods
  async getSelectionStats(): Promise<ModelSelectionStats> {
    const models = await this.getAvailableModels();
    const preferences = await this.getPreferences();
    const registry = await this.getModelRegistry();

    const stats: ModelSelectionStats = {
      totalModels: models.length,
      readyModels: models.filter(m => m.status === 'local' && (!m.health || m.health.is_healthy)).length,
      localModels: models.filter(m => m.status === 'local').length,
      cloudModels: models.filter(m => m.status === 'available').length,
      lastSelectedModel: preferences.lastSelectedModel,
      defaultModel: preferences.defaultModel,
      modelsByType: {
        text: models.filter(m => m.type === 'text').length,
        image: models.filter(m => m.type === 'image').length,
        embedding: models.filter(m => m.type === 'embedding').length,
        multimodal: models.filter(m => m.type === 'multimodal').length
      },
      registryStats: {
        lastUpdate: new Date(registry.lastUpdate).toISOString(),
        categoriesCount: Object.keys(registry.categories.byType).length,
        healthyModels: registry.categories.byHealth['healthy']?.length || 0,
        unhealthyModels: registry.categories.byHealth['unhealthy']?.length || 0
      },
      watchingStats: {
        isWatching: this.isWatching,
        watchedDirectories: Array.from(this.watchedDirectories),
        changeListeners: this.changeListeners.size,
        lastChangeDetection: Object.fromEntries(this.lastChangeDetection)
      }
    };

    return stats;
  }

  // File system watching methods
  async startDirectoryWatching(options: DirectoryWatchOptions = {}): Promise<void> {
    const {
      directories = ['models/llama-cpp', 'models/transformers', 'models/stable-diffusion', 'models/flux'],
      debounceMs = 1000,
      enablePolling = true,
      pollingInterval = 30000
    } = options;

    if (this.isWatching) {
      return; // Already watching
    }

    this.isWatching = true;
    directories.forEach(dir => this.watchedDirectories.add(dir));

    // Set up polling as a fallback
    if (enablePolling) {
      this.pollingInterval = setInterval(async () => {
        await this.checkForDirectoryChanges();
      }, pollingInterval);
    }
  }

  async stopDirectoryWatching(): Promise<void> {
    this.isWatching = false;
    this.watchedDirectories.clear();
    this.changeListeners.clear();
    
    // Clear debounce timers
    this.debounceTimers.forEach(timer => clearTimeout(timer));
    this.debounceTimers.clear();
    
    // Clear polling interval
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  addChangeListener(listener: (event: FileSystemChangeEvent) => void): () => void {
    this.changeListeners.add(listener);
    
    // Return unsubscribe function
    return () => {
      this.changeListeners.delete(listener);
    };
  }

  private async checkForDirectoryChanges(): Promise<void> {
    for (const directory of this.watchedDirectories) {
      const lastCheck = this.lastChangeDetection.get(directory) || 0;
      const now = Date.now();
      
      // Simple change detection - in a real implementation, this would check file timestamps
      if (now - lastCheck > 30000) { // Check every 30 seconds
        this.lastChangeDetection.set(directory, now);
        
        // Notify listeners of potential changes
        const event: FileSystemChangeEvent = {
          type: 'modified',
          path: directory,
          directory,
          timestamp: now
        };
        
        this.changeListeners.forEach(listener => {
          try {
            listener(event);
          } catch (error) {
            console.error('Error in change listener:', error);
          }
        });
      }
    }
  }

  // Utility methods
  clearCache(): void {
    this.cachedModels = [];
    this.modelRegistry = null;
    this.lastFetchTime = 0;
  }

  async updateLastSelectedModel(modelId: string): Promise<void> {
    const preferences = await this.getPreferences();
    preferences.lastSelectedModel = modelId;
    await this.savePreferences(preferences);
  }

  async setDefaultModel(modelId: string): Promise<void> {
    const preferences = await this.getPreferences();
    preferences.defaultModel = modelId;
    await this.savePreferences(preferences);
  }

  private async getPreferences(): Promise<ModelSelectionPreferences> {
    // In a real implementation, this would load from storage
    return {
      lastSelectedModel: undefined,
      defaultModel: undefined,
      preferredProviders: [],
      preferLocal: true,
      autoSelectFallback: true
    };
  }

  private async savePreferences(preferences: ModelSelectionPreferences): Promise<void> {
    // In a real implementation, this would save to storage
    console.log('Saving preferences:', preferences);
  }
}