"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAccessibility } from '../../providers/accessibility-hooks';

interface AccessibilityEnhancementsContextValue {
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

const AccessibilityEnhancementsContext = createContext<AccessibilityEnhancementsContextValue | undefined>(undefined);

interface AccessibilityEnhancementsProviderProps {
  children: React.ReactNode;
}

export function AccessibilityEnhancementsProvider({ children }: AccessibilityEnhancementsProviderProps) {
  const { settings, updateSetting, announce } = useAccessibility();
  const [focusRingVisible, setFocusRingVisible] = useState(true);
  const [keyboardNavigationEnabled, setKeyboardNavigationEnabled] = useState(true);
  const [textScale, setTextScale] = useState(1);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Apply text scaling
  useEffect(() => {
    if (!mounted) return;
    
    const root = document.documentElement;
    root.style.setProperty('--accessibility-text-scale', textScale.toString());
  }, [textScale, mounted]);

  // Apply color blindness filters
  useEffect(() => {
    if (!mounted) return;
    
    const root = document.documentElement;
    const filterClass = `color-blindness-${settings.colorBlindnessSupport}`;
    
    // Remove existing filter classes
    root.classList.remove('color-blindness-protanopia', 'color-blindness-deuteranopia', 'color-blindness-tritanopia');
    
    if (settings.colorBlindnessSupport !== 'none') {
      root.classList.add(filterClass);
    }
  }, [settings.colorBlindnessSupport, mounted]);

  // Keyboard navigation detection
  useEffect(() => {
    if (!mounted) return;
    
    let isUsingKeyboard = false;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        isUsingKeyboard = true;
        setFocusRingVisible(true);
      }
    };

    const handleMouseDown = () => {
      isUsingKeyboard = false;
      setFocusRingVisible(false);
    };

    const handleFocus = () => {
      if (isUsingKeyboard) {
        setFocusRingVisible(true);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('focus', handleFocus, true);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('focus', handleFocus, true);
    };
  }, [mounted]);

  const toggleHighContrast = useCallback(() => {
    updateSetting('highContrast', !settings.highContrast);
  }, [settings.highContrast, updateSetting]);

  const announceMessage = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    announce(message, priority);
  }, [announce]);

  const setColorBlindnessFilter = useCallback((filter: 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia') => {
    updateSetting('colorBlindnessSupport', filter);
  }, [updateSetting]);

  const contextValue: AccessibilityEnhancementsContextValue = {
    highContrastMode: settings.highContrast,
    toggleHighContrast,
    focusRingVisible,
    setFocusRingVisible,
    announceMessage,
    keyboardNavigationEnabled,
    setKeyboardNavigationEnabled,
    reducedMotion: settings.reducedMotion,
    textScale,
    setTextScale,
    colorBlindnessFilter: settings.colorBlindnessSupport,
    setColorBlindnessFilter,
  };

  return (
    <AccessibilityEnhancementsContext.Provider value={contextValue}>
      {children}
    </AccessibilityEnhancementsContext.Provider>
  );
}

export function useAccessibilityEnhancements() {
  const context = useContext(AccessibilityEnhancementsContext);
  if (context === undefined) {
    throw new Error('useAccessibilityEnhancements must be used within an AccessibilityEnhancementsProvider');
  }
  return context;
}
