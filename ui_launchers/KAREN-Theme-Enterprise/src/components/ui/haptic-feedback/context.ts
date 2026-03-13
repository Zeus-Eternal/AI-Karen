"use client";

import { createContext, useContext } from 'react';
import { HapticContextType } from './types';

const HapticContext = createContext<HapticContextType | undefined>(undefined);

function useHapticContext() {
  const context = useContext(HapticContext);
  if (context === undefined) {
    throw new Error('useHapticContext must be used within a HapticProvider');
  }
  return context;
}

export { HapticContext, useHapticContext };
