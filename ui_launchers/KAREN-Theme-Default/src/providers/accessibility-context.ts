"use client";

import { createContext } from 'react';

export interface AccessibilitySettings {
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
  lineHeight: 'normal' | 'relaxed' | 'loose';
  reducedMotion: boolean;
  focusVisible: boolean;
  keyboardNavigation: boolean;
  announcements: boolean;
  verboseDescriptions: boolean;
  colorBlindnessSupport: 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia';
}

export interface AccessibilityContextValue {
  settings: AccessibilitySettings;
  updateSetting: <K extends keyof AccessibilitySettings>(
    key: K,
    value: AccessibilitySettings[K]
  ) => void;
  resetSettings: () => void;
  isScreenReaderActive: boolean;
  announce: (message: string, priority?: 'polite' | 'assertive') => void;
}

export const AccessibilityContext = createContext<AccessibilityContextValue | undefined>(undefined);
