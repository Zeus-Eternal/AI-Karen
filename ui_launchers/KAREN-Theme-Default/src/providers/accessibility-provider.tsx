"use client";

import React, { useEffect, useState, useCallback } from 'react';
import { useUIStore, selectAnimationState } from '../store';
import {
  AccessibilityContext,
  type AccessibilityContextValue,
  type AccessibilitySettings,
} from './accessibility-context';
const defaultSettings: AccessibilitySettings = {
  highContrast: false,
  fontSize: 'medium',
  lineHeight: 'normal',
  reducedMotion: false,
  focusVisible: true,
  keyboardNavigation: true,
  announcements: true,
  verboseDescriptions: false,
  colorBlindnessSupport: 'none',
};
export interface AccessibilityProviderProps {
  children: React.ReactNode;
  storageKey?: string;
}
export function AccessibilityProvider({
  children,
  storageKey = 'accessibility-settings',
}: AccessibilityProviderProps) {
  const { reducedMotion, setReducedMotion } = useUIStore(selectAnimationState);
  const [settings, setSettings] = useState<AccessibilitySettings>(defaultSettings);
  const [isScreenReaderActive, setIsScreenReaderActive] = useState(false);
  const [mounted, setMounted] = useState(false);
  // Load settings from localStorage on mount
  useEffect(() => {
    const loadSettings = () => {
      try {
        const stored = localStorage.getItem(storageKey);
        if (stored) {
          const parsedSettings = JSON.parse(stored) as Partial<AccessibilitySettings>;
          const mergedSettings = { ...defaultSettings, ...parsedSettings };
          return mergedSettings;
        }
      } catch (error) {
        console.error('[AccessibilityProvider] Failed to parse stored settings:', error);
      }
      return defaultSettings;
    };

    const timer = setTimeout(() => {
      const loadedSettings = loadSettings();
      setSettings(loadedSettings);
      setReducedMotion(loadedSettings.reducedMotion);
      setMounted(true);
    }, 0);

    return () => clearTimeout(timer);
  }, [storageKey, setReducedMotion]);

  // Save settings to localStorage
  useEffect(() => {
    if (!mounted) return;
    try {
      localStorage.setItem(storageKey, JSON.stringify(settings));
    } catch (error) {
      console.error('[AccessibilityProvider] Failed to save settings to localStorage:', error);
      if (error instanceof Error && error.name === 'QuotaExceededError') {
        console.warn('[AccessibilityProvider] localStorage quota exceeded');
      }
    }
  }, [settings, storageKey, mounted]);
  // Sync reduced motion with UI store - use callback to avoid setState in effect
  const syncReducedMotion = useCallback(() => {
    if (mounted && settings.reducedMotion !== reducedMotion) {
      setSettings(prev => ({ ...prev, reducedMotion }));
    }
  }, [reducedMotion, mounted, settings.reducedMotion]);

  useEffect(() => {
    const timer = setTimeout(() => {
      syncReducedMotion();
    }, 0);

    return () => clearTimeout(timer);
  }, [syncReducedMotion]);
  // Define updateSetting callback
  const updateSetting = useCallback(<K extends keyof AccessibilitySettings>(
    key: K,
    value: AccessibilitySettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    // Sync specific settings with UI store
    if (key === 'reducedMotion') {
      setReducedMotion(value as boolean);
    }
  }, [setReducedMotion]);

  // Detect system preferences
  useEffect(() => {
    if (!mounted || typeof window === 'undefined' || !window.matchMedia) return;
    // Detect reduced motion
    const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleReducedMotionChange = (e: MediaQueryListEvent) => {
      updateSetting('reducedMotion', e.matches);
    };
    reducedMotionQuery?.addEventListener('change', handleReducedMotionChange);
    // Detect high contrast
    const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
    const handleHighContrastChange = (e: MediaQueryListEvent) => {
      updateSetting('highContrast', e.matches);
    };
    highContrastQuery?.addEventListener('change', handleHighContrastChange);
    // Detect screen reader
    const detectScreenReader = () => {
      // Check for common screen reader indicators
      const hasScreenReader = 
        navigator.userAgent.includes('NVDA') ||
        navigator.userAgent.includes('JAWS') ||
        navigator.userAgent.includes('VoiceOver') ||
        window.speechSynthesis?.speaking ||
        document.querySelector('[aria-live]') !== null;
      setIsScreenReaderActive(hasScreenReader);
    };
    detectScreenReader();
    // Set initial values if not already set - use setTimeout to avoid setState in effect
    if (settings.reducedMotion !== reducedMotionQuery?.matches) {
      setTimeout(() => updateSetting('reducedMotion', reducedMotionQuery?.matches || false), 0);
    }
    if (settings.highContrast !== highContrastQuery?.matches) {
      setTimeout(() => updateSetting('highContrast', highContrastQuery?.matches || false), 0);
    }
    return () => {
      reducedMotionQuery?.removeEventListener('change', handleReducedMotionChange);
      highContrastQuery?.removeEventListener('change', handleHighContrastChange);
    };
  }, [mounted, settings.reducedMotion, settings.highContrast, updateSetting]);
  // Apply accessibility settings to document
  useEffect(() => {
    if (!mounted) return;
    const root = document.documentElement;
    // Apply font size
    root.style.setProperty('--accessibility-font-size', {
      'small': '0.875rem',
      'medium': '1rem',
      'large': '1.125rem',
      'extra-large': '1.25rem',
    }[settings.fontSize]);
    // Apply line height
    root.style.setProperty('--accessibility-line-height', {
      'normal': '1.5',
      'relaxed': '1.625',
      'loose': '1.75',
    }[settings.lineHeight]);
    // Apply high contrast
    if (settings.highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }
    // Apply color blindness support
    root.setAttribute('data-color-blindness', settings.colorBlindnessSupport);
    // Apply focus visible
    if (settings.focusVisible) {
      root.classList.add('focus-visible');
    } else {
      root.classList.remove('focus-visible');
    }
  }, [settings, mounted]);
  const resetSettings = () => {
    setSettings(defaultSettings);
    setReducedMotion(defaultSettings.reducedMotion);
  };
  // Announce messages to screen readers
  const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (!settings.announcements || !mounted) return;
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    document.body.appendChild(announcement);
    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  };
  const contextValue: AccessibilityContextValue = {
    settings,
    updateSetting,
    resetSettings,
    isScreenReaderActive,
    announce,
  };
  return (
    <AccessibilityContext.Provider value={contextValue}>
      {children}
    </AccessibilityContext.Provider>
  );
}
// Hooks moved to separate file for React Fast Refresh compatibility
