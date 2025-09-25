"use client";

import { useState, useCallback } from "react";
import { ChatSettings } from "../types";

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

  const updateSettings = useCallback(
    (newSettings: Partial<ChatSettings>) => {
      console.log('🔍 useChatSettings: Settings change triggered:', {
        previousModel: settings.model,
        newModel: newSettings.model,
        fullNewSettings: newSettings,
        hasModelChange: newSettings.model !== undefined && newSettings.model !== settings.model
      });

      const updatedSettings = { ...settings, ...newSettings };
      setSettings(updatedSettings);

      // Log model selection details
      if (newSettings.model && newSettings.model !== settings.model) {
        console.log('🔍 useChatSettings: Model selection changed:', {
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

  return {
    settings,
    updateSettings,
    resetSettings,
  };
};