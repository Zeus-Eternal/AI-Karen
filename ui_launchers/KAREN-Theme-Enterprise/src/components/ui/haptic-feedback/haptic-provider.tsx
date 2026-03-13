"use client";

import { useMemo, useState } from 'react';
import { HapticContextType, HapticProviderProps, HapticPattern } from './types';
import { HapticContext } from './context';
import { isHapticSupported, isHapticEnabled, setHapticEnabled, triggerHapticFeedback } from './haptic-utils';

export function HapticProvider({
  children,
  defaultEnabled = true
}: HapticProviderProps) {
  const supported = useMemo(() => isHapticSupported(), []);
  const [enabled, setEnabled] = useState(() => isHapticEnabled(defaultEnabled));

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
