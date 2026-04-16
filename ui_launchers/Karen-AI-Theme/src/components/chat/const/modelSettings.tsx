import { useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { formatModelSwitchError } from '@/lib/model-switch-errors';
import type { ProviderDetails, ModelSettingsResponse } from './types';

interface ModelSettingsState {
  selected_provider: string;
  selected_model: string;
  providers: ProviderDetails[];
}

export function useModelSettings() {
  return {
    // Apply model selection
    applyModelSelection: useCallback(async (
      providerId: string,
      modelId: string,
      modelSettings: ModelSettingsState | null,
      setModelSettings: React.Dispatch<React.SetStateAction<ModelSettingsState | null>>,
      setSelectedProvider: React.Dispatch<React.SetStateAction<string>>,
      setSelectedModel: React.Dispatch<React.SetStateAction<string>>,
      setIsUpdatingModelSelection: React.Dispatch<React.SetStateAction<boolean>>,
      toast: any
    ) => {
      if (!modelSettings) {
        return;
      }

      const provider = modelSettings.providers.find((item) => item.id === providerId);
      if (!provider || !modelId) {
        return;
      }

      setIsUpdatingModelSelection(true);
      try {
        const response = await apiClient.put<ModelSettingsResponse>('/api/settings/model', {
          provider: providerId,
          model: modelId,
        });

        setModelSettings(response as ModelSettingsState);
        const allowedProviders = response.providers
          .filter((item) => item.selectable !== false)
          .map((item) => {
            const configuredModels = (item.models || []).filter((model: { id: string; name: string; source?: string }) => model.source !== 'discovered');
            return {
              ...item,
              models: configuredModels.length > 0
                ? configuredModels
                : (
                    item.selected_model || item.default_model
                      ? [{ id: item.selected_model || item.default_model || '', name: item.selected_model || item.default_model || '', source: 'saved' }]
                      : []
                  ),
            };
          });
        const resolvedProvider =
          allowedProviders.find((item) => item.id === response.selected_provider)?.id ||
          allowedProviders[0]?.id ||
          '';
        setSelectedProvider(resolvedProvider);
        setSelectedModel(
          allowedProviders.find((item) => item.id === resolvedProvider)?.selected_model ||
          allowedProviders.find((item) => item.id === resolvedProvider)?.models[0]?.id ||
          response.selected_model
        );
        toast({
          title: 'Settings applied',
          description: `Karen is now using ${modelId} via ${provider.display_name}.`,
        });
      } catch (err) {
        toast({
          title: 'Model switch failed',
          description: formatModelSwitchError(err, provider.display_name),
          variant: 'destructive',
        });
      } finally {
        setIsUpdatingModelSelection(false);
      }
    }, []),

    // Get selectable providers
    getSelectableProviders: (modelSettings: ModelSettingsState | null): ProviderDetails[] => {
      const providers = modelSettings?.providers ?? [];
      return providers
        .filter((provider) => provider.selectable !== false)
        .map((provider) => {
          const configuredModels = (provider.models || []).filter((model) => model.source !== 'discovered');
          const fallbackModelId =
            provider.selected_model ||
            provider.default_model ||
            (modelSettings?.selected_provider === provider.id
              ? modelSettings?.selected_model
              : null) ||
            '';
          return {
            ...provider,
            models: configuredModels.length > 0
              ? configuredModels
              : (
                  fallbackModelId
                    ? [{ id: fallbackModelId, name: fallbackModelId, source: 'saved' }]
                    : []
                ),
          };
       });
    },
  };
}
