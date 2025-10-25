'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { HapticContextType, HapticProviderProps, HapticPattern } from './types';
import { isHapticSupported, isHapticEnabled, setHapticEnabled, triggerHapticFeedback } from './haptic-utils';

const HapticContext = createContext<HapticContextType | undefined>(undefined);

export function useHapticContext() {
  const context = useContext(HapticContext);
  if (context === undefined) {
    throw new Error('useHapticContext must be used within a HapticProvider');
  }
  return context;
}

export function HapticProvider({ 
  children, 
  defaultEnabled = true 
}: HapticProviderProps) {
  const [enabled, setEnabled] = useState(defaultEnabled);
  const [supported, setSupported] = useState(false);

  useEffect(() => {
    // Check if haptic feedback is supported
    setSupported(isHapticSupported());
    
    // Load user preference
    setEnabled(isHapticEnabled());
  }, []);

  const handleSetEnabled = (newEnabled: boolean) => {
    setEnabled(newEnabled);
    setHapticEnabled(newEnabled);
  };

  const trigger = (pattern: HapticPattern) => {
    if (enabled && supported) {
      triggerHapticFeedback(pattern);
    }
  };

  const value: HapticContextType = {
    enabled,
    supported,
    setEnabled: handleSetEnabled,
    trigger
  };

  return (
    <HapticContext.Provider value={value}>
      {children}
    </HapticContext.Provider>
  );
}