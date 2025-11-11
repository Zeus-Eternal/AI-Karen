import { createContext, useContext } from 'react';

export interface AccessibilityEnhancementsContextValue {
  // High contrast mode
  highContrastMode: boolean;
  toggleHighContrast: () => void;

  // Focus management
  focusRingVisible: boolean;
  setFocusRingVisible: (visible: boolean) => void;

  // Screen reader support
  announceMessage: (message: string, priority?: 'polite' | 'assertive') => void;

  // Keyboard navigation
  keyboardNavigationEnabled: boolean;
  setKeyboardNavigationEnabled: (enabled: boolean) => void;

  // Motion preferences
  reducedMotion: boolean;

  // Text scaling
  textScale: number;
  setTextScale: (scale: number) => void;

  // Color blindness support
  colorBlindnessFilter: 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia';
  setColorBlindnessFilter: (filter: 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia') => void;
}

export const AccessibilityEnhancementsContext = createContext<AccessibilityEnhancementsContextValue | undefined>(
  undefined,
);

export function useAccessibilityEnhancements() {
  const context = useContext(AccessibilityEnhancementsContext);
  if (context === undefined) {
    throw new Error('useAccessibilityEnhancements must be used within an AccessibilityEnhancementsProvider');
  }
  return context;
}
