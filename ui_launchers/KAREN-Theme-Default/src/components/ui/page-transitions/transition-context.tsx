"use client";

import { createContext, useContext } from 'react';

import type { TransitionConfig } from './types';

export interface TransitionContextType {
  config: TransitionConfig;
  updateConfig: (newConfig: Partial<TransitionConfig>) => void;
}

export const TransitionContext = createContext<TransitionContextType | undefined>(undefined);

export function useTransitionContext(): TransitionContextType {
  const context = useContext(TransitionContext);
  if (context === undefined) {
    throw new Error('useTransitionContext must be used within a TransitionProvider');
  }
  return context;
}
