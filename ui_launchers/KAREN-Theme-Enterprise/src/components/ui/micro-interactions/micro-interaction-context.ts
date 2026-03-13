"use client";

import { createContext, useContext } from 'react';

import type { MicroInteractionConfig } from './types';

export interface MicroInteractionContextType extends MicroInteractionConfig {
  updateConfig: (config: Partial<MicroInteractionConfig>) => void;
}

export const MicroInteractionContext = createContext<MicroInteractionContextType | undefined>(undefined);

export function useMicroInteractions(): MicroInteractionContextType {
  const context = useContext(MicroInteractionContext);
  if (context === undefined) {
    throw new Error('useMicroInteractions must be used within a MicroInteractionProvider');
  }
  return context;
}
