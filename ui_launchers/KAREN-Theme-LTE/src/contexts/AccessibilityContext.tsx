"use client"

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { auditLogger } from '@/lib/audit-logger';
import { generateId } from '@/lib/id-generator';

// Accessibility preferences interface
export interface AccessibilityPreferences {
  // Visual preferences
  highContrast: boolean;
  largeText: boolean;
  reducedMotion: boolean;
  focusVisible: boolean;
  
  // Navigation preferences
  keyboardNavigation: boolean;
  skipLinks: boolean;
  
  // Screen reader preferences
  screenReaderOptimized: boolean;
  announceChanges: boolean;
  
  // Voice control preferences
  voiceControl: boolean;
  voiceCommands: boolean;
  
  // Testing preferences
  accessibilityTesting: boolean;
  showAccessibilityMenu: boolean;
}

// Accessibility state interface
export interface AccessibilityState {
  preferences: AccessibilityPreferences;
  currentFocusElement: Element | null;
  focusTrapActive: boolean;
  keyboardUser: boolean;
  screenReaderActive: boolean;
  voiceControlActive: boolean;
  announcements: Array<{ message: string; priority: 'polite' | 'assertive'; timestamp: string }>;
  violations: Array<{ message: string; priority: 'polite' | 'assertive'; timestamp: string; type: string; severity: string; }>;
  complianceScore: number;
}

// Accessibility context interface
export interface AccessibilityViolation {
  message: string;
  priority: 'polite' | 'assertive';
  timestamp: string;
  type: string;
  severity: string;
}

export interface AccessibilityContextType {
  state: AccessibilityState;
  updatePreferences: (preferences: Partial<AccessibilityPreferences>) => void;
  setFocusElement: (element: Element | null) => void;
  setFocusTrap: (active: boolean) => void;
  announceToScreenReader: (message: string, priority?: 'polite' | 'assertive') => void;
  clearAnnouncements: () => void;
  addViolation: (violation: Omit<AccessibilityViolation, 'timestamp'>) => void;
  clearViolations: () => void;
  updateComplianceScore: (score: number) => void;
  toggleVoiceControl: () => void;
  resetPreferences: () => void;
}

// Default preferences
const defaultPreferences: AccessibilityPreferences = {
  highContrast: false,
  largeText: false,
  reducedMotion: false,
  focusVisible: true,
  keyboardNavigation: true,
  skipLinks: true,
  screenReaderOptimized: true,
  announceChanges: true,
  voiceControl: false,
  voiceCommands: false,
  accessibilityTesting: false,
  showAccessibilityMenu: true,
};

// Default state
const defaultState: AccessibilityState = {
  preferences: defaultPreferences,
  currentFocusElement: null,
  focusTrapActive: false,
  keyboardUser: false,
  screenReaderActive: false,
  voiceControlActive: false,
  announcements: [],
  violations: [],
  complianceScore: 0,
};

// Create context
const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

// Accessibility provider component
export function AccessibilityProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AccessibilityState>(defaultState);
  const [isClient, setIsClient] = useState(false);

  // Toggle voice control (moved here to be available for keyboard event handler)
  const toggleVoiceControl = useCallback(() => {
    setState(prev => ({
      ...prev,
      voiceControlActive: !prev.voiceControlActive,
      preferences: {
        ...prev.preferences,
        voiceControl: !prev.voiceControlActive,
      },
    }));
  }, []);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Load preferences from localStorage on mount
  useEffect(() => {
    if (isClient && typeof window !== 'undefined') {
      try {
        const savedPreferences = localStorage.getItem('accessibility-preferences');
        if (savedPreferences) {
          const parsed = JSON.parse(savedPreferences);
          setState(prev => ({
            ...prev,
            preferences: { ...defaultPreferences, ...parsed },
          }));
        }
      } catch (error) {
        console.error('Failed to load accessibility preferences:', error);
      }
    }
  }, [isClient]);

  // Save preferences to localStorage when they change
  useEffect(() => {
    if (isClient && typeof window !== 'undefined') {
      try {
        localStorage.setItem('accessibility-preferences', JSON.stringify(state.preferences));
      } catch (error) {
        console.error('Failed to save accessibility preferences:', error);
      }
    }
  }, [state.preferences, isClient]);

  // Detect keyboard navigation
  useEffect(() => {
    if (!isClient) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Detect if user is navigating with keyboard
      if (event.key === 'Tab') {
        setState(prev => ({ ...prev, keyboardUser: true }));
      }
      
      // Handle accessibility shortcuts
      if (event.altKey) {
        switch (event.key) {
          case 'a':
            event.preventDefault();
            setState(prev => ({
              ...prev,
              preferences: { ...prev.preferences, showAccessibilityMenu: !prev.preferences.showAccessibilityMenu },
            }));
            break;
          case 'h':
            event.preventDefault();
            setState(prev => ({
              ...prev,
              preferences: { ...prev.preferences, highContrast: !prev.preferences.highContrast },
            }));
            break;
          case 'l':
            event.preventDefault();
            setState(prev => ({
              ...prev,
              preferences: { ...prev.preferences, largeText: !prev.preferences.largeText },
            }));
            break;
          case 'm':
            event.preventDefault();
            setState(prev => ({
              ...prev,
              preferences: { ...prev.preferences, reducedMotion: !prev.preferences.reducedMotion },
            }));
            break;
          case 'v':
            event.preventDefault();
            toggleVoiceControl();
            break;
        }
      }
    };

    const handleMouseDown = () => {
      setState(prev => ({ ...prev, keyboardUser: false }));
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, [isClient, toggleVoiceControl]);

  // Detect screen reader
  useEffect(() => {
    if (isClient && typeof window !== 'undefined') {
      // Basic screen reader detection
      const screenReaderTest = window.speechSynthesis;
      const isScreenReaderActive = !!screenReaderTest;
      
      setState(prev => ({ ...prev, screenReaderActive: isScreenReaderActive }));
    }
  }, [isClient]);

  // Apply accessibility preferences to document
  useEffect(() => {
    if (isClient && typeof document !== 'undefined') {
      const root = document.documentElement;
      
      // Apply high contrast
      if (state.preferences.highContrast) {
        root.classList.add('high-contrast');
      } else {
        root.classList.remove('high-contrast');
      }
      
      // Apply large text
      if (state.preferences.largeText) {
        root.classList.add('large-text');
      } else {
        root.classList.remove('large-text');
      }
      
      // Apply reduced motion
      if (state.preferences.reducedMotion) {
        root.classList.add('reduced-motion');
      } else {
        root.classList.remove('reduced-motion');
      }
      
      // Apply focus visible
      if (state.preferences.focusVisible) {
        root.classList.add('focus-visible-enabled');
      } else {
        root.classList.remove('focus-visible-enabled');
      }
      
      // Apply keyboard navigation
      if (state.preferences.keyboardNavigation) {
        root.setAttribute('data-keyboard-nav', 'true');
      } else {
        root.removeAttribute('data-keyboard-nav');
      }
      
      // Apply screen reader optimization
      if (state.preferences.screenReaderOptimized) {
        root.setAttribute('data-screen-reader', 'optimized');
      } else {
        root.removeAttribute('data-screen-reader');
      }
    }
  }, [state.preferences, isClient]);

  // Update preferences
  const updatePreferences = useCallback((newPreferences: Partial<AccessibilityPreferences>) => {
    setState(prev => ({
      ...prev,
      preferences: { ...prev.preferences, ...newPreferences },
    }));
    
    // Log preference changes
    auditLogger.log('INFO', 'ACCESSIBILITY_PREFERENCE_CHANGED', {
      preferences: newPreferences,
      timestamp: new Date().toISOString(),
    });
  }, []);

  // Set focus element
  const setFocusElement = useCallback((element: Element | null) => {
    setState(prev => ({ ...prev, currentFocusElement: element }));
  }, []);

  // Set focus trap
  const setFocusTrap = useCallback((active: boolean) => {
    setState(prev => ({ ...prev, focusTrapActive: active }));
  }, []);

  // Announce to screen reader
  const announceToScreenReader = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    setState(prev => ({
      ...prev,
      announcements: [...prev.announcements, { message, priority, timestamp: generateId('announcement') }],
    }));

    // Create live region for screen reader announcements
    if (isClient && typeof document !== 'undefined') {
      const liveRegion = document.createElement('div');
      liveRegion.setAttribute('aria-live', priority);
      liveRegion.setAttribute('aria-atomic', 'true');
      liveRegion.style.position = 'absolute';
      liveRegion.style.left = '-10000px';
      liveRegion.style.width = '1px';
      liveRegion.style.height = '1px';
      liveRegion.style.overflow = 'hidden';
      liveRegion.textContent = message;
      
      document.body.appendChild(liveRegion);
      
      // Remove after announcement
      setTimeout(() => {
        document.body.removeChild(liveRegion);
      }, 1000);
    }
  }, [isClient]);

  // Clear announcements
  const clearAnnouncements = useCallback(() => {
    setState(prev => ({ ...prev, announcements: [] }));
  }, []);

  // Add violation
  const addViolation = useCallback((violation: Omit<AccessibilityViolation, 'timestamp'>) => {
    setState(prev => ({
      ...prev,
      violations: [...prev.violations, { ...violation, timestamp: generateId('violation') }],
    }));
  }, []);

  // Clear violations
  const clearViolations = useCallback(() => {
    setState(prev => ({ ...prev, violations: [] }));
  }, []);

  // Update compliance score
  const updateComplianceScore = useCallback((score: number) => {
    setState(prev => ({ ...prev, complianceScore: score }));
  }, []);

  // Reset preferences
  const resetPreferences = useCallback(() => {
    setState(prev => ({
      ...prev,
      preferences: defaultPreferences,
    }));
    
    auditLogger.log('INFO', 'ACCESSIBILITY_PREFERENCES_RESET', {
      timestamp: new Date().toISOString(),
    });
  }, []);

  const contextValue: AccessibilityContextType = {
    state,
    updatePreferences,
    setFocusElement,
    setFocusTrap,
    announceToScreenReader,
    clearAnnouncements,
    addViolation,
    clearViolations,
    updateComplianceScore,
    toggleVoiceControl,
    resetPreferences,
  };

  return (
    <AccessibilityContext.Provider value={contextValue}>
      {children}
    </AccessibilityContext.Provider>
  );
}

// Hook to use accessibility context
export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
}

// Export context for testing
export { AccessibilityContext };
