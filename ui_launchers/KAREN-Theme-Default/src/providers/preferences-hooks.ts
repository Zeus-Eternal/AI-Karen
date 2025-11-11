import { useContext } from 'react';
import { PreferencesContext } from './preferences-context';
import type { UserPreferences } from './preferences-context';

export function usePreferences() {
  const context = useContext(PreferencesContext);
  if (context === undefined) {
    throw new Error('usePreferences must be used within a PreferencesProvider');
  }
  return context;
}

export function useThemePreference() {
  const { preferences, updatePreference } = usePreferences();

  return {
    theme: preferences.theme,
    setTheme: (theme: UserPreferences['theme']) => updatePreference('theme', theme),
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
    setFontSize: (size: UserPreferences['fontSize']) => updatePreference('fontSize', size),
    setReducedMotion: (reduced: boolean) => updatePreference('reducedMotion', reduced),
  };
}
