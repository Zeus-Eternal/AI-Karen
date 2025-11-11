"use client";

import { createContext } from 'react';

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  reducedMotion: boolean;
  sidebarCollapsed: boolean;
  rightPanelView: string;
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large';
  language: string;
  notifications: {
    enabled: boolean;
    sound: boolean;
    desktop: boolean;
    email: boolean;
  };
  animations: boolean;
  autoSave: boolean;
  autoSaveInterval: number;
}

export interface PreferencesContextValue {
  preferences: UserPreferences;
  updatePreference: <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => void;
  resetPreferences: () => void;
  isLoading: boolean;
  error: string | null;
}

export const PreferencesContext = createContext<PreferencesContextValue | undefined>(undefined);
