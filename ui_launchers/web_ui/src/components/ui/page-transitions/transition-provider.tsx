'use client';

import React, { createContext, useContext } from 'react';
import { TransitionConfig, TransitionProviderProps } from './types';

interface TransitionContextType {
  config: TransitionConfig;
  updateConfig: (newConfig: Partial<TransitionConfig>) => void;
}

const TransitionContext = createContext<TransitionContextType | undefined>(undefined);

export function useTransitionContext() {
  const context = useContext(TransitionContext);
  if (context === undefined) {
    throw new Error('useTransitionContext must be used within a TransitionProvider');
  }
  return context;
}

export function TransitionProvider({ 
  children, 
  defaultConfig = {} 
}: TransitionProviderProps) {
  const [config, setConfig] = React.useState<TransitionConfig>({
    variant: 'fade',
    duration: 0.3,
    ease: [0.4, 0, 0.2, 1],
    delay: 0,
    ...defaultConfig
  });

  const updateConfig = (newConfig: Partial<TransitionConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  };

  const value = {
    config,
    updateConfig
  };

  return (
    <TransitionContext.Provider value={value}>
      {children}
    </TransitionContext.Provider>
  );
}