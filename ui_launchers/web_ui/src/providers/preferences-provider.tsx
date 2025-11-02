"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useUIStore, selectPreferencesState } from '../store';
interface UserPreferences {
  // Theme preferences
  theme: 'light' | 'dark' | 'system';
  // Animation preferences
  reducedMotion: boolean;
  // Layout preferences
  sidebarCollapsed: boolean;
  rightPanelView: string;
  // Accessibility preferences
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large';
  // Language preferences
  language: string;
  // Notification preferences
  notifications: {
    enabled: boolean;
    sound: boolean;
    desktop: boolean;
    email: boolean;
  };
  // Performance preferences
  animations: boolean;
  autoSave: boolean;
  autoSaveInterval: number; // in seconds
}
interface PreferencesContextValue {
  preferences: UserPreferences;
  updatePreference: <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => void;
  resetPreferences: () => void;
  isLoading: boolean;
  error: string | null;
}
const PreferencesContext = createContext<PreferencesContextValue | undefined>(undefined);
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
interface PreferencesProviderProps {
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
      } catch (err) {
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
    } catch (err) {
      setError('Failed to save preferences');
    }
  }, [preferences, storageKey, mounted]);
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
  }, [mounted, preferences.reducedMotion]);
  const updatePreference = <K extends keyof UserPreferences>(
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
  };
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
export function usePreferences() {
  const context = useContext(PreferencesContext);
  if (context === undefined) {
    throw new Error('usePreferences must be used within a PreferencesProvider');
  }
  return context;
}
// Convenience hooks for specific preferences
export function useThemePreference() {
  const { preferences, updatePreference } = usePreferences();
  return {
    theme: preferences.theme,
    setTheme: (theme: 'light' | 'dark' | 'system') => updatePreference('theme', theme),
  };
}
export function useAnimationPreference() {
  const { preferences, updatePreference } = usePreferences();
  return {
    reducedMotion: preferences.reducedMotion,
    animations: preferences.animations,
    setReducedMotion: (reduced: boolean) => updatePreference('reducedMotion', reduced),
    setAnimations: (enabled: boolean) => updatePreference('animations', enabled),
  };
}
export function useAccessibilityPreference() {
  const { preferences, updatePreference } = usePreferences();
  return {
    highContrast: preferences.highContrast,
    fontSize: preferences.fontSize,
    reducedMotion: preferences.reducedMotion,
    setHighContrast: (enabled: boolean) => updatePreference('highContrast', enabled),
    setFontSize: (size: 'small' | 'medium' | 'large') => updatePreference('fontSize', size),
    setReducedMotion: (reduced: boolean) => updatePreference('reducedMotion', reduced),
  };
}
