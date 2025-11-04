/**
 * Model Selection Service
 *
 * Implements intelligent model selection with priority order:
 * 1. Last selected model (from user preferences)
 * 2. Default model (from configuration)
 * 3. First available model (from discovered models)
 */

import { Model, ModelLibraryResponse } from "@/lib/model-utils";
import { getKarenBackend } from "@/lib/karen-backend";
import { safeError, safeLog } from "@/lib/safe-console";

export interface ModelSelectionPreferences {
  lastSelectedModel?: string;
  defaultModel?: string;
  preferredProviders?: string[];
  preferLocal?: boolean;
  autoSelectFallback?: boolean;
}

export interface ModelSelectionResult {
  selectedModel: Model | null;
  selectionReason:
    | "last_selected"
    | "default"
    | "first_available"
    | "none_available";
  availableModels: Model[];
  fallbackUsed: boolean;
}

export class ModelSelectionService {
  private static instance: ModelSelectionService;
  private cachedModels: Model[] = [];
  private lastFetchTime: number = 0;
  private readonly CACHE_DURATION = 30000; // 30 seconds
  private changeListeners: Array<(event: any) => void> = [];

  static getInstance(): ModelSelectionService {
    if (!ModelSelectionService.instance) {
      ModelSelectionService.instance = new ModelSelectionService();
    }
    return ModelSelectionService.instance;
  }

  /**
   * Get available models with caching
   */
  async getAvailableModels(forceRefresh = false): Promise<Model[]> {
    const now = Date.now();

    // Check if we should use cached models
    if (
      !forceRefresh &&
      this.cachedModels.length > 0 &&
      now - this.lastFetchTime < this.CACHE_DURATION
    ) {
      return this.cachedModels;
    }

    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic<ModelLibraryResponse>(
        "/api/models/library"
      );
      
      this.cachedModels = response.models || [];
      this.lastFetchTime = now;

      safeLog(
        `ModelSelectionService: Loaded ${this.cachedModels.length} models`
      );
      return this.cachedModels;
    } catch (error) {
      safeError("ModelSelectionService: Failed to fetch models:", error);
      return this.cachedModels; // Return cached models if available
    }
  }

  /**
   * Get user preferences for model selection
   */
  async getUserPreferences(): Promise<ModelSelectionPreferences> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic<ModelSelectionPreferences>(
        "/api/user/preferences/models"
      );
      return response || {};
    } catch (error) {
      safeError(
        "ModelSelectionService: Failed to get user preferences:",
        error
      );
      return {};
    }
  }

  /**
   * Save user preferences for model selection
   */
  async saveUserPreferences(
    preferences: Partial<ModelSelectionPreferences>
  ): Promise<void> {
    try {
      const backend = getKarenBackend();
      await backend.makeRequestPublic("/api/user/preferences/models", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(preferences),
      });

      safeLog("ModelSelectionService: Saved user preferences");
    } catch (error) {
      safeError(
        "ModelSelectionService: Failed to save user preferences:",
        error
      );
    }
  }

  /**
   * Get system default model configuration
   */
  async getDefaultModelConfig(): Promise<{ defaultModel?: string }> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic<{ defaultModel?: string }>(
        "/api/system/config/models"
      );
      return response || {};
    } catch (error) {
      safeError(
        "ModelSelectionService: Failed to get default model config:",
        error
      );
      return {};
    }
  }

  /**
   * Select the best model based on priority order
   */
  async selectOptimalModel(
    options: {
      filterByCapability?: string;
      filterByType?: "text" | "image" | "embedding" | "multimodal";
      preferLocal?: boolean;
      forceRefresh?: boolean;
    } = {}
  ): Promise<ModelSelectionResult> {
    const {
      filterByCapability,
      filterByType,
      preferLocal = true,
      forceRefresh = false,
    } = options;

    // Get available models
    const allModels = await this.getAvailableModels(forceRefresh);

    // Filter models by capability if specified
    let availableModels = allModels;
    if (filterByCapability) {
      availableModels = allModels.filter((model) =>
        model.capabilities?.includes(filterByCapability)
      );
    }

    // Filter by type if specified
    if (filterByType) {
      availableModels = availableModels.filter((model) => {
        // Support both exact type match and multimodal models
        if (model.type === filterByType) return true;
        if (model.type === "multimodal" && filterByType !== "multimodal") {
          // Check if multimodal model supports the requested type
          return (
            model.capabilities?.includes(`${filterByType}-generation`) ||
            model.capabilities?.includes(filterByType)
          );
        }
        return false;
      });

    }

    // Filter by status (only local/available models, exclude downloading)
    availableModels = availableModels.filter(
      (model) => model.status === "local" || model.status === "available"
    );

    if (availableModels.length === 0) {
      return {
        selectedModel: null,
        selectionReason: "none_available",
        availableModels: [],
        fallbackUsed: false,
      };
    }

    // Get user preferences and system config
    const [userPreferences, systemConfig] = await Promise.all([
      this.getUserPreferences(),
      this.getDefaultModelConfig(),
    ]);

    // Priority 1: Last selected model
    if (userPreferences.lastSelectedModel) {
      const lastSelectedModel = availableModels.find(
        (model) => model.id === userPreferences.lastSelectedModel
      );

      if (lastSelectedModel) {
        safeLog(
          `ModelSelectionService: Selected last used model: ${lastSelectedModel.id}`
        );
        return {
          selectedModel: lastSelectedModel,
          selectionReason: "last_selected",
          availableModels,
          fallbackUsed: false,
        };
      }
    }

    // Priority 2: Default model from system configuration
    const defaultModelId =
      userPreferences.defaultModel || systemConfig.defaultModel;
    if (defaultModelId) {
      const defaultModel = availableModels.find(
        (model) => model.id === defaultModelId
      );

      if (defaultModel) {
        safeLog(
          `ModelSelectionService: Selected default model: ${defaultModel.id}`
        );
        return {
          selectedModel: defaultModel,
          selectionReason: "default",
          availableModels,
          fallbackUsed: false,
        };
      }
    }

    // Priority 3: First available model with preference logic
    // Sort by priority, health, type compatibility, and performance
    const sortedModels = [...availableModels].sort((a, b) => {
      // First by type compatibility (exact type match preferred)
      if (filterByType) {
        const aExactMatch = a.type === filterByType ? 1 : 0;
        const bExactMatch = b.type === filterByType ? 1 : 0;
        if (aExactMatch !== bExactMatch) return bExactMatch - aExactMatch;
      }

      // Then by local status if preferLocal is true
      if (preferLocal) {
        const localA = a.status === "local" ? 1 : 0;
        const localB = b.status === "local" ? 1 : 0;
        if (localA !== localB) return localB - localA;
      }

      // Finally by size (smaller first for better performance)
      return (a.size || 0) - (b.size || 0);
    });

    let firstAvailableModel = sortedModels[0];

    // Prefer models from preferred providers
    if (userPreferences.preferredProviders?.length) {
      const preferredModel = sortedModels.find((model) =>
        userPreferences.preferredProviders!.includes(model.provider || "")
      );
      if (preferredModel) {
        firstAvailableModel = preferredModel;
      }
    }

    safeLog(
      `ModelSelectionService: Selected first available model: ${
        firstAvailableModel.id
      } (type: ${firstAvailableModel.type || "unknown"})`
    );
    return {
      selectedModel: firstAvailableModel,
      selectionReason: "first_available",
      availableModels,
      fallbackUsed: false,
    };
  }

  /**
   * Update the last selected model in user preferences
   */
  async updateLastSelectedModel(modelId: string): Promise<void> {
    const preferences = await this.getUserPreferences();
    await this.saveUserPreferences({
      ...preferences,
      lastSelectedModel: modelId,
    });

  }

  /**
   * Set the default model for the user
   */
  async setDefaultModel(modelId: string): Promise<void> {
    const preferences = await this.getUserPreferences();
    await this.saveUserPreferences({
      ...preferences,
      defaultModel: modelId,
    });

  }

  /**
   * Get model by ID
   */
  async getModelById(modelId: string): Promise<Model | null> {
    const models = await this.getAvailableModels();
    return models.find(model => model.id === modelId) || null;
  }

  /**
   * Check if model is ready for use
   */
  async isModelReady(modelId: string): Promise<boolean> {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic<{ ready: boolean }>(`/api/models/${modelId}/status`);
      return response.ready === true;
    } catch (error) {
      safeError(`ModelSelectionService: Failed to check model readiness for ${modelId}:`, error);
      return false;
    }
  }

  /**
   * Get selection statistics
   */
  async getSelectionStats(): Promise<{
    totalModels: number;
    localModels: number;
    availableModels: number;
    downloadingModels: number;
    lastUpdated: string;
    lastSelectedModel?: string;
    scanStats?: {
      scanDuration?: number;
      directoriesScanned?: number;
      filesProcessed?: number;
      errors?: string[];
    };
  }> {
    const models = await this.getAvailableModels();
    const preferences = await this.getUserPreferences();
    
    return {
      totalModels: models.length,
      localModels: models.filter(m => m.status === 'local').length,
      availableModels: models.filter(m => m.status === 'available').length,
      downloadingModels: models.filter(m => m.status === 'downloading').length,
      lastUpdated: new Date(this.lastFetchTime).toISOString(),
      lastSelectedModel: preferences.lastSelectedModel,
      scanStats: {
        scanDuration: 0,
        directoriesScanned: 1,
        filesProcessed: models.length,
        errors: []
      }
    };
  }

  /**
   * Switch to a different model
   */
  async switchModel(modelId: string, options: {
    preserveContext?: boolean;
    forceSwitch?: boolean;
  } = {}): Promise<{
    success: boolean;
    previousModel?: string;
    newModel: string;
    switchTime: number;
    message?: string;
  }> {
    const startTime = Date.now();
    
    try {
      // Get current preferences to track previous model
      const preferences = await this.getUserPreferences();
      const previousModel = preferences.lastSelectedModel;
      
      // Verify the target model exists and is available
      const targetModel = await this.getModelById(modelId);
      if (!targetModel) {
        throw new Error(`Model ${modelId} not found`);
      }
      
      if (targetModel.status !== 'local' && targetModel.status !== 'available') {
        throw new Error(`Model ${modelId} is not available (status: ${targetModel.status})`);
      }
      
      // Update the last selected model
      await this.updateLastSelectedModel(modelId);
      
      const switchTime = Date.now() - startTime;
      
      safeLog(`ModelSelectionService: Switched from ${previousModel || 'none'} to ${modelId} in ${switchTime}ms`);
      
      return {
        success: true,
        previousModel,
        newModel: modelId,
        switchTime,
        message: `Successfully switched to ${targetModel.name || modelId}`
      };
      
    } catch (error) {
      const switchTime = Date.now() - startTime;
      safeError(`ModelSelectionService: Failed to switch to model ${modelId}:`, error);
      
      return {
        success: false,
        newModel: modelId,
        switchTime,
        message: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Scan local directories for models (fallback method)
   */
  async scanLocalDirectories(options: {
    forceRefresh?: boolean;
    includeHealth?: boolean;
  } = {}): Promise<Model[]> {
    // This is a fallback method that returns cached models
    // In a real implementation, this would scan local directories
    return this.getAvailableModels(options.forceRefresh);
  }

  /**
   * Get model category summary
   */
  async getModelCategorySummary(): Promise<{
    categories: Array<{
      name: string;
      count: number;
      types: string[];
    }>;
  }> {
    const models = await this.getAvailableModels();
    const categoryMap = new Map<string, { count: number; types: Set<string> }>();
    
    models.forEach(model => {
      const category = model.type || 'unknown';
      if (!categoryMap.has(category)) {
        categoryMap.set(category, { count: 0, types: new Set() });
      }
      const categoryData = categoryMap.get(category)!;
      categoryData.count++;
      if (model.type) {
        categoryData.types.add(model.type);
      }
    });

    const categories = Array.from(categoryMap.entries()).map(([name, data]) => ({
      name,
      count: data.count,
      types: Array.from(data.types)
    }));
    
    return { categories };
  }

  /**
   * Get model registry information
   */
  async getModelRegistry(): Promise<{
    providers: string[];
    totalModels: number;
    lastSync: string;
    scanMetadata?: {
      scanDuration?: number;
      directoriesScanned?: number;
      filesProcessed?: number;
      errors?: string[];
    };
  }> {
    const models = await this.getAvailableModels();
    const providers = [...new Set(models.map(m => m.provider).filter(Boolean))];
    
    return {
      providers,
      totalModels: models.length,
      lastSync: new Date(this.lastFetchTime).toISOString(),
      scanMetadata: {
        scanDuration: 0,
        directoriesScanned: 1,
        filesProcessed: models.length,
        errors: []
      }
    };
  }

  /**
   * Add change listener for model updates
   */
  addChangeListener(listener: (event: any) => void): () => void {
    this.changeListeners.push(listener);
    
    // Return unsubscribe function
    return () => {
      const index = this.changeListeners.indexOf(listener);
      if (index > -1) {
        this.changeListeners.splice(index, 1);
      }
    };
  }

  /**
   * Notify change listeners
   */
  private notifyChangeListeners(event: any): void {
    this.changeListeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        safeError('ModelSelectionService: Change listener error:', error);
      }
    });

  }

  /**
   * Clear model selection cache
   */
  clearCache(): void {
    this.cachedModels = [];
    this.lastFetchTime = 0;
  }
}

// Export singleton instance
export const modelSelectionService = ModelSelectionService.getInstance();
