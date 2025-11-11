"use client";

import React, { useCallback, useEffect, useState } from 'react';
import { useUIStore, selectPreferencesState } from '../store';
import {
  PreferencesContext,
  type PreferencesContextValue,
  type UserPreferences,
} from './preferences-context';
const defaultPreferences: UserPreferences = {
  theme: 'system',
  reducedMotion: false,
  sidebarCollapsed: false,
  rightPanelView: 'dashboard',
  highContrast: false,
  fontSize: 'medium',
  language: 'en',
  notifications: {
    enabled: true,
    sound: true,
    desktop: true,
    email: false,
  },
  animations: true,
  autoSave: true,
  autoSaveInterval: 30,
};
export interface PreferencesProviderProps {
  children: React.ReactNode;
  storageKey?: string;
}
export function PreferencesProvider({
  children,
  storageKey = 'user-preferences',
}: PreferencesProviderProps) {
  const { theme, reducedMotion, setTheme, setReducedMotion } = useUIStore(selectPreferencesState);
  const [preferences, setPreferences] = useState<UserPreferences>(defaultPreferences);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  // Load preferences from localStorage on mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const stored = localStorage.getItem(storageKey);
        if (stored) {
          const parsedPreferences = JSON.parse(stored) as Partial<UserPreferences>;
          const mergedPreferences = { ...defaultPreferences, ...parsedPreferences };
          setPreferences(mergedPreferences);
          // Sync with UI store
          setTheme(mergedPreferences.theme);
          setReducedMotion(mergedPreferences.reducedMotion);
        } else {
          // Initialize with defaults and sync with UI store
          setPreferences(defaultPreferences);
          setTheme(defaultPreferences.theme);
          setReducedMotion(defaultPreferences.reducedMotion);
        }
      } catch (error) {
        console.error('[PreferencesProvider] Failed to load preferences', error);
        setError('Failed to load preferences');
      } finally {
        setIsLoading(false);
        setMounted(true);
      }
    };
    loadPreferences();
  }, [storageKey, setTheme, setReducedMotion]);
  // Sync UI store changes back to preferences
  useEffect(() => {
    if (!mounted) return;
    setPreferences(prev => ({
      ...prev,
      theme,
      reducedMotion,
    }));
  }, [theme, reducedMotion, mounted]);
  // Save preferences to localStorage whenever they change
  useEffect(() => {
    if (!mounted) return;
    try {
      localStorage.setItem(storageKey, JSON.stringify(preferences));
    } catch (error) {
      console.error('[PreferencesProvider] Failed to save preferences', error);
      setError('Failed to save preferences');
    }
  }, [preferences, storageKey, mounted]);
  const updatePreference = useCallback(<K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value,
    }));
    // Sync specific preferences with UI store
    if (key === 'theme') {
      setTheme(value as 'light' | 'dark' | 'system');
    } else if (key === 'reducedMotion') {
      setReducedMotion(value as boolean);
    }
  }, [setTheme, setReducedMotion]);
  // Detect system preferences
  useEffect(() => {
    if (!mounted || typeof window === 'undefined' || !window.matchMedia) return;
    // Detect reduced motion preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleReducedMotionChange = (e: MediaQueryListEvent) => {
      if (preferences.reducedMotion !== e.matches) {
        updatePreference('reducedMotion', e.matches);
      }
    };
    // Set initial reduced motion preference if not explicitly set
    if (preferences.reducedMotion !== mediaQuery?.matches) {
      updatePreference('reducedMotion', mediaQuery?.matches || false);
    }
    mediaQuery?.addEventListener('change', handleReducedMotionChange);
    return () => mediaQuery?.removeEventListener('change', handleReducedMotionChange);
  }, [mounted, preferences.reducedMotion, updatePreference]);
  const resetPreferences = () => {
    setPreferences(defaultPreferences);
    setTheme(defaultPreferences.theme);
    setReducedMotion(defaultPreferences.reducedMotion);
    setError(null);
  };
  const contextValue: PreferencesContextValue = {
    preferences,
    updatePreference,
    resetPreferences,
    isLoading,
    error,
  };
  return (
    <PreferencesContext.Provider value={contextValue}>
      {children}
    </PreferencesContext.Provider>
  );
}
