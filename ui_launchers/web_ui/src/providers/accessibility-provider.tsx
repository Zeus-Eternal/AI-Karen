'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useUIStore, selectAnimationState } from '../store';

interface AccessibilitySettings {
  // Visual accessibility
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
  lineHeight: 'normal' | 'relaxed' | 'loose';
  
  // Motion accessibility
  reducedMotion: boolean;
  
  // Interaction accessibility
  focusVisible: boolean;
  keyboardNavigation: boolean;
  
  // Screen reader accessibility
  announcements: boolean;
  verboseDescriptions: boolean;
  
  // Color accessibility
  colorBlindnessSupport: 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia';
}

interface AccessibilityContextValue {
  settings: AccessibilitySettings;
  updateSetting: <K extends keyof AccessibilitySettings>(
    key: K,
    value: AccessibilitySettings[K]
  ) => void;
  resetSettings: () => void;
  isScreenReaderActive: boolean;
  announce: (message: string, priority?: 'polite' | 'assertive') => void;
}

const AccessibilityContext = createContext<AccessibilityContextValue | undefined>(undefined);

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

interface AccessibilityProviderProps {
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

  // Load settings from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        const parsedSettings = JSON.parse(stored) as Partial<AccessibilitySettings>;
        const mergedSettings = { ...defaultSettings, ...parsedSettings };
        setSettings(mergedSettings);
        
        // Sync with UI store
        setReducedMotion(mergedSettings.reducedMotion);
      }
    } catch (error) {
      console.error('Error loading accessibility settings:', error);
    }
    setMounted(true);
  }, [storageKey, setReducedMotion]);

  // Save settings to localStorage
  useEffect(() => {
    if (!mounted) return;
    
    try {
      localStorage.setItem(storageKey, JSON.stringify(settings));
    } catch (error) {
      console.error('Error saving accessibility settings:', error);
    }
  }, [settings, storageKey, mounted]);

  // Sync reduced motion with UI store
  useEffect(() => {
    if (mounted && settings.reducedMotion !== reducedMotion) {
      setSettings(prev => ({ ...prev, reducedMotion }));
    }
  }, [reducedMotion, mounted, settings.reducedMotion]);

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
    
    // Set initial values if not already set
    if (settings.reducedMotion !== reducedMotionQuery?.matches) {
      updateSetting('reducedMotion', reducedMotionQuery?.matches || false);
    }
    if (settings.highContrast !== highContrastQuery?.matches) {
      updateSetting('highContrast', highContrastQuery?.matches || false);
    }

    return () => {
      reducedMotionQuery?.removeEventListener('change', handleReducedMotionChange);
      highContrastQuery?.removeEventListener('change', handleHighContrastChange);
    };
  }, [mounted, settings.reducedMotion, settings.highContrast]);

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

  const updateSetting = <K extends keyof AccessibilitySettings>(
    key: K,
    value: AccessibilitySettings[K]
  ) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    
    // Sync specific settings with UI store
    if (key === 'reducedMotion') {
      setReducedMotion(value as boolean);
    }
  };

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

export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
}

// Convenience hooks
export function useAnnounce() {
  const { announce } = useAccessibility();
  return announce;
}

export function useScreenReader() {
  const { isScreenReaderActive, settings } = useAccessibility();
  return {
    isActive: isScreenReaderActive,
    verboseDescriptions: settings.verboseDescriptions,
    announcements: settings.announcements,
  };
}

export function useAccessibilitySettings() {
  const { settings, updateSetting } = useAccessibility();
  return { settings, updateSetting };
}