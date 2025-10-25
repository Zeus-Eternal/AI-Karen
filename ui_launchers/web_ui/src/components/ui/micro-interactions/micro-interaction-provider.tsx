'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { MicroInteractionConfig } from './types';

interface MicroInteractionContextType extends MicroInteractionConfig {
  updateConfig: (config: Partial<MicroInteractionConfig>) => void;
}

const MicroInteractionContext = createContext<MicroInteractionContextType | undefined>(undefined);

export function useMicroInteractions() {
  const context = useContext(MicroInteractionContext);
  if (context === undefined) {
    throw new Error('useMicroInteractions must be used within a MicroInteractionProvider');
  }
  return context;
}

interface MicroInteractionProviderProps {
  children: React.ReactNode;
  defaultConfig?: Partial<MicroInteractionConfig>;
}

export function MicroInteractionProvider({ 
  children, 
  defaultConfig = {} 
}: MicroInteractionProviderProps) {
  const [config, setConfig] = useState<MicroInteractionConfig>({
    reducedMotion: false,
    enableHaptics: true,
    animationDuration: 'normal',
    ...defaultConfig
  });

  useEffect(() => {
    // Check for reduced motion preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleChange = (e: MediaQueryListEvent) => {
      setConfig(prev => ({ ...prev, reducedMotion: e.matches }));
    };

    setConfig(prev => ({ ...prev, reducedMotion: mediaQuery.matches }));
    mediaQuery.addEventListener('change', handleChange);

    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const updateConfig = (newConfig: Partial<MicroInteractionConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  };

  const value = {
    ...config,
    updateConfig
  };

  return (
    <MicroInteractionContext.Provider value={value}>
      {children}
    </MicroInteractionContext.Provider>
  );
}