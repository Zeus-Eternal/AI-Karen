import { useState, useEffect, useCallback } from 'react';
import { useTelemetry } from './use-telemetry';
import { generateAccessibleColorScheme, checkColorContrast } from '@/utils/colorContrast';

export interface AccessibilityPreferences {
  highContrast: boolean;
  reducedMotion: boolean;
  largeText: boolean;
  focusVisible: boolean;
  screenReaderOptimized: boolean;
  colorBlindFriendly: boolean;
}

export interface AccessibilityState extends AccessibilityPreferences {
  colorScheme: Record<string, string>;
  fontSize: number;
  isSystemDarkMode: boolean;
  isSystemHighContrast: boolean;
  isSystemReducedMotion: boolean;
}

const DEFAULT_PREFERENCES: AccessibilityPreferences = {
  highContrast: false,
  reducedMotion: false,
  largeText: false,
  focusVisible: true,
  screenReaderOptimized: false,
  colorBlindFriendly: false
};

const STORAGE_KEY = 'accessibility-preferences';

export const useAccessibility = () => {
  const { track } = useTelemetry();
  const [preferences, setPreferences] = useState<AccessibilityPreferences>(DEFAULT_PREFERENCES);
  const [isSystemDarkMode, setIsSystemDarkMode] = useState(false);
  const [isSystemHighContrast, setIsSystemHighContrast] = useState(false);
  const [isSystemReducedMotion, setIsSystemReducedMotion] = useState(false);

  // Load preferences from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setPreferences({ ...DEFAULT_PREFERENCES, ...parsed });
      }
    } catch (error) {
      console.warn('Failed to load accessibility preferences:', error);
    }
  }, []);

  // Save preferences to localStorage
  const savePreferences = useCallback((newPreferences: AccessibilityPreferences) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newPreferences));
      setPreferences(newPreferences);
      track('accessibility_preferences_updated', newPreferences);
    } catch (error) {
      console.warn('Failed to save accessibility preferences:', error);
    }
  }, [track]);

  // Detect system preferences
  useEffect(() => {
    const updateSystemPreferences = () => {
      // Dark mode detection
      const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
      setIsSystemDarkMode(darkModeQuery.matches);

      // High contrast detection
      const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
      setIsSystemHighContrast(highContrastQuery.matches);

      // Reduced motion detection
      const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      setIsSystemReducedMotion(reducedMotionQuery.matches);

      // Auto-enable preferences based on system settings
      if (highContrastQuery.matches && !preferences.highContrast) {
        updatePreference('highContrast', true);
      }

      if (reducedMotionQuery.matches && !preferences.reducedMotion) {
        updatePreference('reducedMotion', true);
      }
    };

    updateSystemPreferences();

    // Listen for system preference changes
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const handleDarkModeChange = (e: MediaQueryListEvent) => {
      setIsSystemDarkMode(e.matches);
    };

    const handleHighContrastChange = (e: MediaQueryListEvent) => {
      setIsSystemHighContrast(e.matches);
      if (e.matches) {
        updatePreference('highContrast', true);
      }
    };

    const handleReducedMotionChange = (e: MediaQueryListEvent) => {
      setIsSystemReducedMotion(e.matches);
      if (e.matches) {
        updatePreference('reducedMotion', true);
      }
    };

    darkModeQuery.addEventListener('change', handleDarkModeChange);
    highContrastQuery.addEventListener('change', handleHighContrastChange);
    reducedMotionQuery.addEventListener('change', handleReducedMotionChange);

    return () => {
      darkModeQuery.removeEventListener('change', handleDarkModeChange);
      highContrastQuery.removeEventListener('change', handleHighContrastChange);
      reducedMotionQuery.removeEventListener('change', handleReducedMotionChange);
    };
  }, [preferences]);

  // Update individual preference
  const updatePreference = useCallback((
    key: keyof AccessibilityPreferences, 
    value: boolean
  ) => {
    const newPreferences = { ...preferences, [key]: value };
    savePreferences(newPreferences);
  }, [preferences, savePreferences]);

  // Toggle preference
  const togglePreference = useCallback((key: keyof AccessibilityPreferences) => {
    updatePreference(key, !preferences[key]);
  }, [preferences, updatePreference]);

  // Reset to defaults
  const resetPreferences = useCallback(() => {
    savePreferences(DEFAULT_PREFERENCES);
  }, [savePreferences]);

  // Generate color scheme based on preferences
  const colorScheme = generateAccessibleColorScheme(
    isSystemDarkMode,
    preferences.highContrast || isSystemHighContrast
  );

  // Calculate font size based on preferences
  const fontSize = preferences.largeText ? 18 : 16;

  // Apply CSS classes based on preferences
  useEffect(() => {
    const root = document.documentElement;
    const body = document.body;

    // High contrast mode
    if (preferences.highContrast || isSystemHighContrast) {
      body.classList.add('high-contrast');
    } else {
      body.classList.remove('high-contrast');
    }

    // Reduced motion
    if (preferences.reducedMotion || isSystemReducedMotion) {
      body.classList.add('reduce-motion');
    } else {
      body.classList.remove('reduce-motion');
    }

    // Large text
    if (preferences.largeText) {
      body.classList.add('large-text');
      root.style.fontSize = '18px';
    } else {
      body.classList.remove('large-text');
      root.style.fontSize = '16px';
    }

    // Focus visible
    if (preferences.focusVisible) {
      body.classList.add('focus-visible-enabled');
    } else {
      body.classList.remove('focus-visible-enabled');
    }

    // Screen reader optimized
    if (preferences.screenReaderOptimized) {
      body.classList.add('screen-reader-optimized');
    } else {
      body.classList.remove('screen-reader-optimized');
    }

    // Color blind friendly
    if (preferences.colorBlindFriendly) {
      body.classList.add('color-blind-friendly');
    } else {
      body.classList.remove('color-blind-friendly');
    }

    // Apply color scheme CSS variables
    Object.entries(colorScheme).forEach(([key, value]) => {
      root.style.setProperty(`--color-${key}`, value);
    });

  }, [preferences, colorScheme, isSystemDarkMode, isSystemHighContrast, isSystemReducedMotion]);

  // Validate color contrast
  const validateContrast = useCallback((foreground: string, background: string) => {
    return checkColorContrast(foreground, background, fontSize, preferences.largeText);
  }, [fontSize, preferences.largeText]);

  // Get accessible CSS classes
  const getAccessibleClasses = useCallback((baseClasses: string = '') => {
    const classes = [baseClasses];

    if (preferences.highContrast || isSystemHighContrast) {
      classes.push('high-contrast');
    }

    if (preferences.reducedMotion || isSystemReducedMotion) {
      classes.push('reduce-motion');
    }

    if (preferences.largeText) {
      classes.push('large-text');
    }

    if (preferences.focusVisible) {
      classes.push('focus-visible-enabled');
    }

    if (preferences.screenReaderOptimized) {
      classes.push('screen-reader-optimized');
    }

    if (preferences.colorBlindFriendly) {
      classes.push('color-blind-friendly');
    }

    return classes.filter(Boolean).join(' ');
  }, [preferences, isSystemHighContrast, isSystemReducedMotion]);

  // Get accessible button props
  const getAccessibleButtonProps = useCallback((baseProps: any = {}) => {
    return {
      ...baseProps,
      className: getAccessibleClasses(baseProps.className),
      style: {
        minHeight: '44px',
        minWidth: '44px',
        fontSize: `${fontSize}px`,
        ...baseProps.style
      }
    };
  }, [getAccessibleClasses, fontSize]);

  // Get accessible input props
  const getAccessibleInputProps = useCallback((baseProps: any = {}) => {
    return {
      ...baseProps,
      className: getAccessibleClasses(baseProps.className),
      style: {
        minHeight: '44px',
        fontSize: `${fontSize}px`,
        ...baseProps.style
      }
    };
  }, [getAccessibleClasses, fontSize]);

  const state: AccessibilityState = {
    ...preferences,
    colorScheme,
    fontSize,
    isSystemDarkMode,
    isSystemHighContrast,
    isSystemReducedMotion
  };

  return {
    // State
    ...state,
    
    // Actions
    updatePreference,
    togglePreference,
    resetPreferences,
    
    // Utilities
    validateContrast,
    getAccessibleClasses,
    getAccessibleButtonProps,
    getAccessibleInputProps
  };
};