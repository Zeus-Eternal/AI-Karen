"use client";

import React, { useEffect, useState, useCallback } from 'react';
import { useAccessibility } from '../../providers/accessibility-hooks';
import {
  AccessibilityEnhancementsContext,
  AccessibilityEnhancementsContextValue,
} from './AccessibilityEnhancementsContext';

interface AccessibilityEnhancementsProviderProps {
  children: React.ReactNode;
}

export function AccessibilityEnhancementsProvider({ children }: AccessibilityEnhancementsProviderProps) {
  const { settings, updateSetting, announce } = useAccessibility();
  const [focusRingVisible, setFocusRingVisible] = useState(true);
  const [keyboardNavigationEnabled, setKeyboardNavigationEnabled] = useState(true);
  const [textScale, setTextScale] = useState(1);

  // Apply text scaling
  useEffect(() => {
    if (typeof document === 'undefined') return;

    const root = document.documentElement;
    root.style.setProperty('--accessibility-text-scale', textScale.toString());
  }, [textScale]);

  // Apply color blindness filters
  useEffect(() => {
    if (typeof document === 'undefined') return;

    const root = document.documentElement;
    const filterClass = `color-blindness-${settings.colorBlindnessSupport}`;
    
    // Remove existing filter classes
    root.classList.remove('color-blindness-protanopia', 'color-blindness-deuteranopia', 'color-blindness-tritanopia');
    
    if (settings.colorBlindnessSupport !== 'none') {
      root.classList.add(filterClass);
    }
  }, [settings.colorBlindnessSupport]);

  // Keyboard navigation detection
  useEffect(() => {
    if (typeof document === 'undefined') return;

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
  }, []);

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
