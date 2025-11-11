"use client";

import { useEffect, useState } from 'react';
import { MotionConfig } from 'framer-motion';
import { useUIStore, selectAnimationState } from '../store';
import type { MotionContextValue, MotionProviderProps } from './motion-types';
import { MotionContext } from './motion-context';

export function MotionProvider({
  children,
  defaultReducedMotion = false,
  defaultAnimationsEnabled = true,
}: MotionProviderProps) {
  const { reducedMotion, setReducedMotion: setStoreReducedMotion } = useUIStore(selectAnimationState);
  const [animationsEnabled, setAnimationsEnabled] = useState(defaultAnimationsEnabled);

  // Handle hydration and detect system reduced motion preference
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      setStoreReducedMotion(e.matches);
    };

    // Set initial reduced motion preference
    setStoreReducedMotion(mediaQuery?.matches || defaultReducedMotion);
    
    // Listen for changes
    mediaQuery?.addEventListener('change', handleChange);
    
    return () => mediaQuery?.removeEventListener('change', handleChange);
  }, [defaultReducedMotion, setStoreReducedMotion]);

  // Calculate transition config based on preferences
  const transitionConfig = {
    duration: reducedMotion ? 0 : animationsEnabled ? 0.25 : 0.1,
    ease: reducedMotion ? 'linear' as const : [0.4, 0, 0.2, 1] as const,
  };

  // Global motion config for Framer Motion
  const motionConfig = {
    transition: transitionConfig,
    reducedMotion: reducedMotion ? 'always' as const : 'never' as const,
  };

  const contextValue: MotionContextValue = {
    reducedMotion,
    animationsEnabled,
    setReducedMotion: setStoreReducedMotion,
    setAnimationsEnabled,
    transitionConfig,
  };

  return (
    <MotionContext.Provider value={contextValue}>
      <MotionConfig {...motionConfig}>{children}</MotionConfig>
    </MotionContext.Provider>
  );
}
