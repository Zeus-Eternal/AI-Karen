// ui_launchers/KAREN-Theme-Default/src/hooks/useModelSelection.ts
import { useState, useEffect, useCallback } from 'react';
import { Model } from '@/lib/model-utils';
import { modelSelectionService, ModelSelectionResult } from '@/lib/model-selection-service';
import { getKarenBackend } from '@/lib/karen-backend';
import { safeError, safeLog } from '@/lib/safe-console';

interface UseModelSelectionOptions {
  autoSelect?: boolean;
  preferLocal?: boolean;
  filterByCapability?: string;
  onModelSelected?: (model: Model | null, reason: string) => void;
}

interface UseModelSelectionReturn {
  models: Model[];
  selectedModel: string | null;
  selectedModelInfo: Model | null;
  setSelectedModel: (modelId: string | null) => void;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  getSelectedModelInfo: () => Model | null;
  selectionReason: string | null;
  isModelReady: boolean;
  setAsDefault: () => Promise<void>;
}

/**
 * Enhanced hook for managing model selection with intelligent priority-based selection
 * 
 * Priority order:
 * 1. Last selected model (from user preferences)
 * 2. Default model (from configuration) 
 * 3. First available model (with preference logic)
 */
export function useModelSelection(options: UseModelSelectionOptions = {}): UseModelSelectionReturn {
  const { 
    autoSelect = true, 
    preferLocal = true, 
    filterByCapability,
    onModelSelected 
  } = options;
  
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModelState] = useState<string | null>(null);
  const [selectedModelInfo, setSelectedModelInfo] = useState<Model | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectionReason, setSelectionReason] = useState<string | null>(null);
  const [isModelReady, setIsModelReady] = useState(false);

  const performModelSelection = useCallback(async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const result: ModelSelectionResult = await modelSelectionService.selectOptimalModel({
        filterByCapability,
        preferLocal,
        forceRefresh
      });

      setModels(result.availableModels);
      
      if (result.selectedModel) {
        setSelectedModelState(result.selectedModel.id);
        setSelectedModelInfo(result.selectedModel);
        setSelectionReason(result.selectionReason);
        setIsModelReady(await modelSelectionService.isModelReady(result.selectedModel.id));
        
        // Update last selected model in preferences
        await modelSelectionService.updateLastSelectedModel(result.selectedModel.id);
        
        // Notify callback
        onModelSelected?.(result.selectedModel, result.selectionReason);
        
        safeLog('Model selected:', {
          id: result.selectedModel.id,
          name: result.selectedModel.name,
          reason: result.selectionReason,
          ready: isModelReady
        });
      } else {
        setSelectedModelState(null);
        setSelectedModelInfo(null);
        setSelectionReason('none_available');
        setIsModelReady(false);
        
        onModelSelected?.(null, 'none_available');
      }
      
    } catch (err) {
      safeError('Failed to perform model selection:', err);
      setError(err instanceof Error ? err.message : 'Failed to select model');
    } finally {
      setLoading(false);
    }
  }, [filterByCapability, preferLocal, onModelSelected]);

  const setSelectedModel = useCallback(async (modelId: string | null) => {
    if (modelId) {
      const model = await modelSelectionService.getModelById(modelId);
      if (model) {
        setSelectedModelState(modelId);
        setSelectedModelInfo(model);
        setSelectionReason('user_selected');
        setIsModelReady(await modelSelectionService.isModelReady(modelId));
        
        // Update last selected model in preferences
        await modelSelectionService.updateLastSelectedModel(modelId);
        
        onModelSelected?.(model, 'user_selected');
        
        safeLog('User selected model:', modelId);
      } else {
        safeError('Model not found:', modelId);
      }
    } else {
      setSelectedModelState(null);
      setSelectedModelInfo(null);
      setSelectionReason(null);
      setIsModelReady(false);
      
      onModelSelected?.(null, 'user_deselected');
    }
  }, [onModelSelected]);

  const refresh = useCallback(async () => {
    modelSelectionService.clearCache();
    await performModelSelection(true);
  }, [performModelSelection]);

  const getSelectedModelInfo = useCallback((): Model | null => {
    return selectedModelInfo;
  }, [selectedModelInfo]);

  const setAsDefault = useCallback(async () => {
    if (selectedModel) {
      await modelSelectionService.setDefaultModel(selectedModel);
      safeLog('Set as default model:', selectedModel);
    }
  }, [selectedModel]);

  // Initial model selection
  useEffect(() => {
    if (autoSelect) {
      performModelSelection();
    }
  }, [autoSelect, performModelSelection]);

  // Validate selected model still exists after model list updates
  useEffect(() => {
    if (selectedModel && models.length > 0) {
      const modelExists = models.some(model => model.id === selectedModel);
      if (!modelExists) {
        safeLog('Selected model no longer available, reselecting...');
        performModelSelection();
      }
    }
  }, [selectedModel, models, performModelSelection]);

  return {
    models,
    selectedModel,
    selectedModelInfo,
    setSelectedModel,
    loading,
    error,
    refresh,
    getSelectedModelInfo,
    selectionReason,
    isModelReady,
    setAsDefault,
  };
}

/**
 * Hook for managing model actions (download, remove, etc.)
 */
export function useModelActions() {
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  
  const downloadModel = useCallback(async (modelId: string): Promise<void> => {
    try {
      setActionLoading(prev => ({ ...prev, [modelId]: true }));
      
      const backend = getKarenBackend();
      await backend.makeRequestPublic<void>(`/api/models/${modelId}/download`, {
        method: 'POST'
      });
      
    } catch (err) {
      safeError('Failed to download model:', err);
      throw err;
    } finally {
      setActionLoading(prev => ({ ...prev, [modelId]: false }));
    }
  }, []);

  const removeModel = useCallback(async (modelId: string): Promise<void> => {
    try {
      setActionLoading(prev => ({ ...prev, [modelId]: true }));
      
      const backend = getKarenBackend();
      await backend.makeRequestPublic<void>(`/api/models/${modelId}`, {
        method: 'DELETE'
      });
      
    } catch (err) {
      safeError('Failed to remove model:', err);
      throw err;
    } finally {
      setActionLoading(prev => ({ ...prev, [modelId]: false }));
    }
  }, []);

  const getModelInfo = useCallback(async (modelId: string): Promise<Model> => {
    try {
      const backend = getKarenBackend();
      const response = await backend.makeRequestPublic<Model>(`/api/models/${modelId}`);
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
