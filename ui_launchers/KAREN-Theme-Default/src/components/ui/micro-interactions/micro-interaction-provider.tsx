"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import type { MicroInteractionConfig } from './types';

export interface MicroInteractionContextType extends MicroInteractionConfig {
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

export interface MicroInteractionProviderProps {
  children: React.ReactNode;
  defaultConfig?: Partial<MicroInteractionConfig>;
}

export function MicroInteractionProvider({
  children,
  defaultConfig = {},
}: MicroInteractionProviderProps) {
  const [config, setConfig] = useState<MicroInteractionConfig>(() => ({
    reducedMotion: false,
    enableHaptics: true,
    animationDuration: 'normal',
    ...defaultConfig,
  }));

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) {
      return undefined;
    }

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    const updateReducedMotion = (matches: boolean) => {
      setConfig(prev => ({ ...prev, reducedMotion: matches }));
    };

    updateReducedMotion(mediaQuery.matches);

    const handleChange = (event: MediaQueryListEvent) => {
      updateReducedMotion(event.matches);
    };

    if (typeof mediaQuery.addEventListener === 'function') {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }

    mediaQuery.addListener(handleChange);
    return () => mediaQuery.removeListener(handleChange);
  }, []);

  const updateConfig = useCallback((newConfig: Partial<MicroInteractionConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  }, []);

  const value = useMemo(
    () => ({
      ...config,
      updateConfig,
    }),
    [config, updateConfig]
  );

  return (
    <MicroInteractionContext.Provider value={value}>
      {children}
    </MicroInteractionContext.Provider>
  );
}
