/**
 * Model Selection Service
 * Intelligent model selection with caching and preferences
 */

import { Model, ModelSelectionCriteria, getAvailableModels, getOptimalModel } from './model-utils';

export interface ModelSelectionResult {
  selectedModel: Model | null;
  availableModels: Model[];
  selectionReason: string;
}

export interface ModelPreferences {
  defaultModelId?: string;
  lastSelectedModelId?: string;
  preferredProviders?: string[];
  excludedModels?: string[];
}

class ModelSelectionService {
  private cache = new Map<string, Model[]>();
  private preferences: ModelPreferences = {};
  private cacheTimeout = 5 * 60 * 1000; // 5 minutes
  private lastCacheUpdate = 0;

  /**
   * Select optimal model based on criteria
   */
  async selectOptimalModel(criteria: ModelSelectionCriteria = {}): Promise<ModelSelectionResult> {
    try {
      const cacheKey = this.getCacheKey(criteria);
      let availableModels = this.getCachedModels(cacheKey);

      if (!availableModels) {
        availableModels = await getAvailableModels(criteria);
        this.setCachedModels(cacheKey, availableModels);
      }

      // Apply user preferences
      const filteredModels = this.applyPreferences(availableModels);
      
      // Get optimal model
      const selectedModel = await getOptimalModel({ ...criteria, preferLocal: criteria.preferLocal });
      
      let selectionReason = 'auto_selection';
      
      if (selectedModel) {
        if (this.preferences.lastSelectedModelId === selectedModel.id) {
          selectionReason = 'last_selected';
        } else if (this.preferences.defaultModelId === selectedModel.id) {
          selectionReason = 'default_model';
        } else if (selectedModel.isLocal) {
          selectionReason = 'local_preference';
        } else {
          selectionReason = 'capability_match';
        }
      } else {
        selectionReason = 'none_available';
      }

      return {
        selectedModel,
        availableModels: filteredModels,
        selectionReason
      };
    } catch (error) {
      console.error('Failed to select optimal model:', error);
      return {
        selectedModel: null,
        availableModels: [],
        selectionReason: 'error'
      };
    }
  }

  /**
   * Get model by ID
   */
  async getModelById(id: string): Promise<Model | null> {
    try {
      const response = await fetch(`/api/models/${id}`);
      if (!response.ok) {
        return null;
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to get model by ID:', error);
      return null;
    }
  }

  /**
   * Check if model is ready
   */
  async isModelReady(modelId: string): Promise<boolean> {
    try {
      const response = await fetch(`/api/models/${modelId}/ready`);
      if (!response.ok) {
        return false;
      }
      const data = await response.json();
      return data.ready || false;
    } catch (error) {
      console.error('Failed to check model readiness:', error);
      return false;
    }
  }

  /**
   * Update last selected model
   */
  async updateLastSelectedModel(modelId: string): Promise<void> {
    try {
      this.preferences.lastSelectedModelId = modelId;
      await this.savePreferences();
    } catch (error) {
      console.error('Failed to update last selected model:', error);
    }
  }

  /**
   * Set default model
   */
  async setDefaultModel(model: Model): Promise<void> {
    try {
      this.preferences.defaultModelId = model.id;
      await this.savePreferences();
    } catch (error) {
      console.error('Failed to set default model:', error);
    }
  }

  /**
   * Clear cache
   */
  clearCache(): void {
    this.cache.clear();
    this.lastCacheUpdate = 0;
  }

  /**
   * Get cached models
   */
  private getCachedModels(key: string): Model[] | null {
    const cached = this.cache.get(key);
    if (!cached || Date.now() - this.lastCacheUpdate > this.cacheTimeout) {
      return null;
    }
    return cached;
  }

  /**
   * Set cached models
   */
  private setCachedModels(key: string, models: Model[]): void {
    this.cache.set(key, models);
    this.lastCacheUpdate = Date.now();
  }

  /**
   * Get cache key
   */
  private getCacheKey(criteria: ModelSelectionCriteria): string {
    return JSON.stringify({
      filterByCapability: criteria.filterByCapability,
      preferLocal: criteria.preferLocal,
      forceRefresh: criteria.forceRefresh
    });
  }

  /**
   * Apply user preferences to model list
   */
  private applyPreferences(models: Model[]): Model[] {
    return models.filter(model => {
      // Exclude models that user has excluded
      if (this.preferences.excludedModels?.includes(model.id)) {
        return false;
      }
      
      // If user has preferred providers, prioritize them
      if (this.preferences.preferredProviders && this.preferences.preferredProviders.length > 0) {
        return this.preferences.preferredProviders.includes(model.provider);
      }
      
      return true;
    });
  }

  /**
   * Load preferences from storage
   */
  private async loadPreferences(): Promise<void> {
    try {
      const stored = localStorage.getItem('karen-model-preferences');
      if (stored) {
        this.preferences = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load model preferences:', error);
    }
  }

  /**
   * Save preferences to storage
   */
  private async savePreferences(): Promise<void> {
    try {
      localStorage.setItem('karen-model-preferences', JSON.stringify(this.preferences));
    } catch (error) {
      console.error('Failed to save model preferences:', error);
    }
  }
}

// Create singleton instance
export const modelSelectionService = new ModelSelectionService();

// Initialize preferences on load
modelSelectionService['loadPreferences']();