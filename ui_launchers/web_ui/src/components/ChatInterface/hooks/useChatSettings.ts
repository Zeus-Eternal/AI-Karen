"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { ChatSettings } from "../types";
import { safeDebug, safeError, safeWarn } from "@/lib/safe-console";
import { modelSelectionService } from "@/lib/model-selection-service";
import { getModelSelectorValue } from "@/lib/model-utils";

const defaultSettings: ChatSettings = {
  model: "local:tinyllama-1.1b",
  temperature: 0.7,
  maxTokens: 2000,
  enableStreaming: true,
  enableSuggestions: true,
  enableCodeAnalysis: true,
  enableVoiceInput: false,
  theme: "auto",
  language: "javascript",
  autoSave: true,
  showTimestamps: true,
  enableNotifications: true,
};

export const useChatSettings = (
  initialSettings: Partial<ChatSettings> = {},
  onSettingsChange?: (settings: ChatSettings) => void
) => {
  const [settings, setSettings] = useState<ChatSettings>({
    ...defaultSettings,
    ...initialSettings,
  });
  const hasInitializedModel = useRef(false);
  const initialModelRef = useRef(initialSettings.model);

  const updateSettings = useCallback(
    (newSettings: Partial<ChatSettings>) => {
      safeDebug('🔍 useChatSettings: Settings change triggered:', {
        previousModel: settings.model,
        newModel: newSettings.model,
        fullNewSettings: newSettings,
        hasModelChange: newSettings.model !== undefined && newSettings.model !== settings.model
      });

      const updatedSettings = { ...settings, ...newSettings };
      setSettings(updatedSettings);

      // Log model selection details
      if (newSettings.model && newSettings.model !== settings.model) {
        safeDebug('🔍 useChatSettings: Model selection changed:', {
          from: settings.model,
          to: newSettings.model,
          modelFormat: typeof newSettings.model,
          modelLength: newSettings.model.length,
          modelComponents: newSettings.model.split(':'),
          timestamp: new Date().toISOString()
        });
      }

      if (onSettingsChange) {
        onSettingsChange(updatedSettings);
      }
    },
    [settings, onSettingsChange]
  );

  const resetSettings = useCallback(() => {
    setSettings(defaultSettings);
    if (onSettingsChange) {
      onSettingsChange(defaultSettings);
    }
  }, [onSettingsChange]);

  useEffect(() => {
    if (hasInitializedModel.current) {
      return;
    }

    if (initialModelRef.current) {
      hasInitializedModel.current = true;
      return;
    }

    let cancelled = false;

    const initializeModelSelection = async () => {
      try {
        const result = await modelSelectionService.selectOptimalModel({
          filterByCapability: "chat",
          filterByType: "text",
          preferLocal: true,
        });

        if (cancelled) {
          return;
        }

        if (!result.selectedModel) {
          hasInitializedModel.current = true;
          return;
        }

        const selectedValue = getModelSelectorValue(result.selectedModel);
        if (!selectedValue || selectedValue === settings.model) {
          hasInitializedModel.current = true;
          return;
        }

        safeDebug("🔍 useChatSettings: Auto-selected initial chat model", {
          model: selectedValue,
          reason: result.selectionReason,
        });

        hasInitializedModel.current = true;

        const updatedSettings = { ...settings, model: selectedValue };
        setSettings(updatedSettings);
        if (onSettingsChange) {
          onSettingsChange(updatedSettings);
        }

        if (result.selectedModel.id) {
          modelSelectionService.updateLastSelectedModel(result.selectedModel.id).catch((error) => {
            safeWarn("🔍 useChatSettings: Unable to persist last selected model", error);
          });
        }
      } catch (error) {
        if (!cancelled) {
          safeError("🔍 useChatSettings: Failed to auto-select default model", error);
        }
        hasInitializedModel.current = true;
      }
    };

    initializeModelSelection();

    return () => {
      cancelled = true;
    };
  }, [onSettingsChange, settings]);

  return {
    settings,
    updateSettings,
    resetSettings,
  };
};