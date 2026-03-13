/**
 * Model Utilities
 * Utility functions for model management and operations
 */

export interface Model {
  id: string;
  name: string;
  provider: string;
  type: 'text' | 'image' | 'audio' | 'video' | 'multimodal';
  capabilities: string[];
  isLocal: boolean;
  isOnline: boolean;
  size?: number;
  version?: string;
  description?: string;
  status: 'available' | 'loading' | 'unavailable' | 'error';
  metadata?: Record<string, unknown>;
}

export interface ModelSelectionCriteria {
  filterByCapability?: string;
  preferLocal?: boolean;
  forceRefresh?: boolean;
}

export interface ModelSelectionResult {
  selectedModel: Model | null;
  availableModels: Model[];
  selectionReason: string;
}

/**
 * Get model by ID
 */
export async function getModelById(id: string): Promise<Model | null> {
  try {
    // This would typically fetch from an API or local storage
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
 * Get all available models
 */
export async function getAvailableModels(criteria?: ModelSelectionCriteria): Promise<Model[]> {
  try {
    const params = new URLSearchParams();
    if (criteria?.filterByCapability) {
      params.append('capability', criteria.filterByCapability);
    }
    if (criteria?.preferLocal !== undefined) {
      params.append('preferLocal', criteria.preferLocal.toString());
    }
    
    const response = await fetch(`/api/models?${params}`);
    if (!response.ok) {
      return [];
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to get available models:', error);
    return [];
  }
}

/**
 * Check if model is ready
 */
export async function isModelReady(modelId: string): Promise<boolean> {
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
 * Get model capabilities
 */
export function getModelCapabilities(model: Model): string[] {
  return model.capabilities || [];
}

/**
 * Check if model supports specific capability
 */
export function modelSupportsCapability(model: Model, capability: string): boolean {
  return model.capabilities.includes(capability);
}

/**
 * Filter models by capability
 */
export function filterModelsByCapability(models: Model[], capability: string): Model[] {
  return models.filter(model => modelSupportsCapability(model, capability));
}

/**
 * Sort models by preference (local first, then by name)
 */
export function sortModelsByPreference(models: Model[], preferLocal = true): Model[] {
  return [...models].sort((a, b) => {
    // Prefer local models if specified
    if (preferLocal) {
      if (a.isLocal && !b.isLocal) return -1;
      if (!a.isLocal && b.isLocal) return 1;
    }
    
    // Then sort by name
    return a.name.localeCompare(b.name);
  });
}

/**
 * Get optimal model based on criteria
 */
export async function getOptimalModel(criteria: ModelSelectionCriteria): Promise<Model | null> {
  const availableModels = await getAvailableModels(criteria);
  
  if (availableModels.length === 0) {
    return null;
  }
  
  // Sort by preference
  const sortedModels = sortModelsByPreference(availableModels, criteria.preferLocal);
  
  // Return the first model that matches all criteria
  return sortedModels.find(model => {
    if (criteria.filterByCapability && !modelSupportsCapability(model, criteria.filterByCapability)) {
      return false;
    }
    return model.status === 'available';
  }) || null;
}