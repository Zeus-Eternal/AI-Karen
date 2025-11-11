"use client";

import React from 'react';
import { TransitionProviderProps } from './types';
import type { TransitionConfig } from './types';
import { TransitionContext, type TransitionContextType } from './transition-context';

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

  const updateConfig = React.useCallback((newConfig: Partial<TransitionConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  }, []);

  const value = React.useMemo<TransitionContextType>(
    () => ({
      config,
      updateConfig
    }),
    [config, updateConfig]
  );

  return (
    <TransitionContext.Provider value={value}>
      {children}
    </TransitionContext.Provider>
  );
}