import { useState, useEffect, useCallback } from 'react';
import { Model, ModelLibraryResponse } from '@/lib/model-utils';
import { getKarenBackend } from '@/lib/karen-backend';
import { safeError } from '@/lib/safe-console';

interface UseModelSelectionOptions {
  autoSelectFirst?: boolean;
  preferLocal?: boolean;
  filterByCapability?: string;
}

interface UseModelSelectionReturn {
  models: Model[];
  selectedModel: string | null;
  setSelectedModel: (modelId: string | null) => void;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  getSelectedModelInfo: () => Model | null;
}

/**
 * Hook for managing model selection state and data fetching
 */
export function useModelSelection(options: UseModelSelectionOptions = {}): UseModelSelectionReturn {
  const { autoSelectFirst = false, preferLocal = true, filterByCapability } = options;
  
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchModels = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic<ModelLibraryResponse>('/api/models/library');
      
      let filteredModels = response.models || [];
      
      // Filter by capability if specified
      if (filterByCapability) {
        filteredModels = filteredModels.filter(model => 
          model.capabilities.includes(filterByCapability)
        );
      }
      
      setModels(filteredModels);
      
      // Auto-select first model if requested and no model is currently selected
      if (autoSelectFirst && !selectedModel && filteredModels.length > 0) {
        let modelToSelect = filteredModels[0];
        
        // Prefer local models if available
        if (preferLocal) {
          const localModel = filteredModels.find(m => m.status === 'local');
          if (localModel) {
            modelToSelect = localModel;
          }
        }
        
        setSelectedModel(modelToSelect.id);
      }
      
    } catch (err) {
      safeError('Failed to fetch models:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch models');
    } finally {
      setLoading(false);
    }
  }, [autoSelectFirst, selectedModel, preferLocal, filterByCapability]);

  const refresh = useCallback(async () => {
    await fetchModels();
  }, [fetchModels]);

  const getSelectedModelInfo = useCallback((): Model | null => {
    if (!selectedModel) return null;
    return models.find(model => model.id === selectedModel) || null;
  }, [selectedModel, models]);

  // Initial fetch
  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  // Validate selected model still exists after model list updates
  useEffect(() => {
    if (selectedModel && models.length > 0) {
      const modelExists = models.some(model => model.id === selectedModel);
      if (!modelExists) {
        setSelectedModel(null);
      }
    }
  }, [selectedModel, models]);

  return {
    models,
    selectedModel,
    setSelectedModel,
    loading,
    error,
    refresh,
    getSelectedModelInfo,
  };
}

/**
 * Hook for managing model actions (download, remove, etc.)
 */
export function useModelActions() {
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  
  const downloadModel = useCallback(async (modelId: string) => {
    try {
      setActionLoading(prev => ({ ...prev, [modelId]: true }));
      
      const backend = getKarenBackend();
      await backend.makeRequestPublic(`/api/models/${modelId}/download`, {
        method: 'POST',
      });
      
      // TODO: Handle download progress updates
      
    } catch (err) {
      safeError('Failed to download model:', err);
      throw err;
    } finally {
      setActionLoading(prev => ({ ...prev, [modelId]: false }));
    }
  }, []);

  const removeModel = useCallback(async (modelId: string) => {
    try {
      setActionLoading(prev => ({ ...prev, [modelId]: true }));
      
      const backend = getKarenBackend();
      await backend.makeRequestPublic(`/api/models/${modelId}`, {
        method: 'DELETE',
      });
      
    } catch (err) {
      safeError('Failed to remove model:', err);
      throw err;
    } finally {
      setActionLoading(prev => ({ ...prev, [modelId]: false }));
    }
  }, []);

  const getModelInfo = useCallback(async (modelId: string) => {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic(`/api/models/${modelId}`);
      return response;
    } catch (err) {
      safeError('Failed to get model info:', err);
      throw err;
    }
  }, []);

  return {
    downloadModel,
    removeModel,
    getModelInfo,
    actionLoading,
  };
}