import { BaseModelService } from "./base-service";
import {
import type { Model } from "../model-utils";
/**
 * Model Registry Service
 *
 * Manages model categorization, lookup, and registry functionality.
 * Provides efficient categorization and filtering of models by various attributes.
 */



  ModelCategories,
  ModelLookupOptions,
  DirectoryWatchOptions,
} from "./types";


  ModelRegistryError,
  ErrorUtils,
} from "./errors/model-selection-errors";

// Define ModelRegistry interface locally to avoid conflicts
export interface ModelRegistryData {
  models: Model[];
  categories: ModelCategories;
  lastUpdate: number;
  scanMetadata?: any;
}

/**
 * Interface for the model registry service
 */
export interface IModelRegistry {
  updateRegistry(
    models: Model[],
    scanOptions?: DirectoryWatchOptions
  ): Promise<void>;
  getModelRegistry(forceRefresh?: boolean): Promise<ModelRegistryData>;
  lookupModels(options?: ModelLookupOptions): Promise<Model[]>;
  getModelsByCategory(category: string, value: string): Promise<Model[]>;
  getCategorySummary(): Promise<{
    totalModels: number;
    typeCount: Record<string, number>;
    providerCount: Record<string, number>;
    statusCount: Record<string, number>;
    healthCount: Record<string, number>;
  }>;
  categorizeModels(models: Model[]): ModelCategories;
  clearRegistry(): void;
}

/**
 * Model Registry Service Implementation
 */
export class ModelRegistryService
  extends BaseModelService
  implements IModelRegistry
{
  private modelRegistry: ModelRegistryData | null = null;
  protected readonly REGISTRY_CACHE_DURATION = 45000; // 45 seconds
  private readonly REGISTRY_CACHE_KEY = "model_registry";

  constructor(cacheTimeout?: number) {
    super("ModelRegistryService", cacheTimeout);
  }

  /**
   * Initialize the model registry service
   */
  async initialize(): Promise<void> {
    await super.initialize();
    this.log("Model registry service initialized");
  }

  /**
   * Update model registry with categorization
   */
  async updateRegistry(
    models: Model[],
    scanOptions?: DirectoryWatchOptions
  ): Promise<void> {
    try {
      // Create categorized model registry
      const categories = this.categorizeModels(models);
      const latestScan = this.getLatestScanStats(scanOptions);

      this.modelRegistry = {
        models,
        categories,
        lastUpdate: Date.now(),
        scanMetadata: latestScan,
      };

      // Cache the registry
      this.cache.set(this.REGISTRY_CACHE_KEY, this.modelRegistry);

      this.log(
        `Updated model registry with ${models.length} models across ${
          Object.keys(categories.byType).length
        } types`
      );
    } catch (error) {
      this.handleError(error, "updateRegistry", { modelCount: models.length });
      throw new ModelRegistryError(
        "Failed to update model registry",
        "update",
        undefined,
        ErrorUtils.createContext({ models: models.length, error })
      );
    }
  }

  /**
   * Get model registry with categorized models
   */
  async getModelRegistry(forceRefresh = false): Promise<ModelRegistryData> {
    if (!forceRefresh && this.modelRegistry) {
      const now = Date.now();
      if (now - this.modelRegistry.lastUpdate < this.REGISTRY_CACHE_DURATION) {
        return this.modelRegistry;
      }
    }

    // Try to get from cache
    const cached = this.cache.get(this.REGISTRY_CACHE_KEY) as ModelRegistryData;
    if (!forceRefresh && cached) {
      this.modelRegistry = cached;
      return cached;
    }

    // Return empty registry if no data available
    return (
      this.modelRegistry || {
        models: [],
        categories: {
          byType: {},
          byProvider: {},
          byCapability: {},
          byStatus: {},
          byHealth: {},
        },
        lastUpdate: 0,
      }
    );
  }

  /**
   * Lookup models with filtering and sorting options
   */
  async lookupModels(options: ModelLookupOptions = {}): Promise<Model[]> {
    const registry = await this.getModelRegistry();
    let models = [...registry.models];

    try {
      // Apply filters
      if (options.type) {
        models = registry.categories.byType[options.type] || [];
      }

      if (options.provider) {
        models = models.filter(
          (model) =>
            model.provider?.toLowerCase() === options.provider?.toLowerCase()
        );
      }

      if (options.capability) {
        models = models.filter((model) =>
          model.capabilities?.includes(options.capability as string)
        );
      }

      if (options.status) {
        models = models.filter((model) => model.status === options.status);
      }

      if (options.healthyOnly) {
        models = models.filter((model) => model.health?.is_healthy === true);
      }

      // Apply sorting
      if (options.sortBy) {
        models = this.sortModels(models, options.sortBy);
      }

      // Apply limit
      if (options.limit && options.limit > 0) {
        models = models.slice(0, options.limit);
      }

      this.log(
        `Lookup returned ${models.length} models with options:`,
        options
      );
      return models;
    } catch (error) {
      this.handleError(error, "lookupModels", { options });
      throw new ModelRegistryError(
        "Failed to lookup models",
        "lookup",
        undefined,
        ErrorUtils.createContext({ options, error })
      );
    }
  }

  /**
   * Get models by specific category and value
   */
  async getModelsByCategory(category: string, value: string): Promise<Model[]> {
    const registry = await this.getModelRegistry();
    let models: Model[] = [];

    try {
      switch (category) {
        case "type":
          models = registry.categories.byType[value] || [];
          break;
        case "provider":
          models = registry.categories.byProvider[value] || [];
          break;
        case "capability":
          models = registry.categories.byCapability[value] || [];
          break;
        case "status":
          models = registry.categories.byStatus[value] || [];
          break;
        case "health":
          models = registry.categories.byHealth[value] || [];
          break;
        default:
          throw new ModelRegistryError(
            `Unknown category: ${category}`,
            "category",
            undefined,
            ErrorUtils.createContext({ category, value })
          );
      }

      this.log(
        `Found ${models.length} models for category ${category}:${value}`
      );
      return models;
    } catch (error) {
      this.handleError(error, "getModelsByCategory", { category, value });
      throw new ModelRegistryError(
        "Failed to get models by category",
        "category",
        undefined,
        ErrorUtils.createContext({ category, value, error })
      );
    }
  }

  /**
   * Get summary of all categories
   */
  async getCategorySummary(): Promise<{
    totalModels: number;
    typeCount: Record<string, number>;
    providerCount: Record<string, number>;
    statusCount: Record<string, number>;
    healthCount: Record<string, number>;
  }> {
    const registry = await this.getModelRegistry();

    return {
      totalModels: registry.models.length,
      typeCount: Object.fromEntries(
        Object.entries(registry.categories.byType).map(([key, models]) => [
          key,
          models.length,
        ])
      ),
      providerCount: Object.fromEntries(
        Object.entries(registry.categories.byProvider).map(([key, models]) => [
          key,
          models.length,
        ])
      ),
      statusCount: Object.fromEntries(
        Object.entries(registry.categories.byStatus).map(([key, models]) => [
          key,
          models.length,
        ])
      ),
      healthCount: Object.fromEntries(
        Object.entries(registry.categories.byHealth).map(([key, models]) => [
          key,
          models.length,
        ])
      ),
    };
  }

  /**
   * Categorize models by various attributes
   */
  categorizeModels(models: Model[]): ModelCategories {
    const categories: ModelCategories = {
      byType: {},
      byProvider: {},
      byCapability: {},
      byStatus: {},
      byHealth: {},
    };

    models.forEach((model) => {
      // Categorize by type
      const type = model.type || "unknown";
      if (!categories.byType[type]) categories.byType[type] = [];
      categories.byType[type].push(model);

      // Categorize by provider
      const provider = model.provider || "unknown";
      if (!categories.byProvider[provider])
        categories.byProvider[provider] = [];
      categories.byProvider[provider].push(model);

      // Categorize by capabilities
      model.capabilities?.forEach((capability) => {
        if (!categories.byCapability[capability])
          categories.byCapability[capability] = [];
        categories.byCapability[capability].push(model);
      });

      // Categorize by status
      const status = model.status || "unknown";
      if (!categories.byStatus[status]) categories.byStatus[status] = [];
      categories.byStatus[status].push(model);

      // Categorize by health
      const healthStatus = model.health?.is_healthy ? "healthy" : "unhealthy";
      if (!categories.byHealth[healthStatus])
        categories.byHealth[healthStatus] = [];
      categories.byHealth[healthStatus].push(model);
    });

    return categories;
  }

  /**
   * Sort models by specified criteria
   */
  private sortModels(models: Model[], sortBy: string): Model[] {
    return [...models].sort((a, b) => {
      switch (sortBy) {
        case "name":
          return (a.name || "").localeCompare(b.name || "");
        case "size":
          return (a.size || 0) - (b.size || 0);
        case "performance":
          // Sort by health status since performance metrics aren't available on Model interface
          const aPerf = a.health?.is_healthy ? 1 : 0;
          const bPerf = b.health?.is_healthy ? 1 : 0;
          return bPerf - aPerf; // Healthy models first
        case "health":
          const aHealth = a.health?.is_healthy ? 1 : 0;
          const bHealth = b.health?.is_healthy ? 1 : 0;
          return bHealth - aHealth; // Healthy models first
        case "recent":
          // Use last_used property from Model interface, fallback to last_scanned
          const aTime = new Date(a.last_used || a.last_scanned || 0).getTime();
          const bTime = new Date(b.last_used || b.last_scanned || 0).getTime();
          return bTime - aTime; // Most recent first
        default:
          return 0;
      }
    });
  }

  /**
   * Get latest scan statistics
   */
  private getLatestScanStats(scanOptions?: DirectoryWatchOptions): any {
    // This would typically come from the scanner service
    // For now, return basic metadata
    return {
      scanTime: Date.now(),
      directories: scanOptions?.directories || [],
      totalScanned: 0,
      errors: [],
    };
  }

  /**
   * Clear the model registry
   */
  clearRegistry(): void {
    this.modelRegistry = null;
    this.cache.delete(this.REGISTRY_CACHE_KEY);
    this.log("Cleared model registry");
  }

  /**
   * Get registry service statistics
   */
  getRegistryStats(): {
    serviceName: string;
    isInitialized: boolean;
    cacheSize: number;
    hasRegistry: boolean;
    totalModels: number;
    lastUpdate: number;
  } {
    const baseStats = this.getServiceStats();

    return {
      ...baseStats,
      hasRegistry: this.modelRegistry !== null,
      totalModels: this.modelRegistry?.models.length || 0,
      lastUpdate: this.modelRegistry?.lastUpdate || 0,
    };
  }

  /**
   * Shutdown the registry service
   */
  async shutdown(): Promise<void> {
    await super.shutdown();
    this.log("Model registry service shut down");
  }
}

/**
 * Singleton instance for backward compatibility
 */
let modelRegistryInstance: ModelRegistryService | null = null;

/**
 * Get or create the model registry singleton
 */
export function getModelRegistry(cacheTimeout?: number): ModelRegistryService {
  if (!modelRegistryInstance) {
    modelRegistryInstance = new ModelRegistryService(cacheTimeout);
  }
  return modelRegistryInstance;
}

/**
 * Reset the model registry singleton (mainly for testing)
 */
export function resetModelRegistry(): void {
  if (modelRegistryInstance) {
    modelRegistryInstance.shutdown();
    modelRegistryInstance = null;
  }
}

// Export the service class as ModelRegistry for backward compatibility
export { ModelRegistryService as ModelRegistry };
