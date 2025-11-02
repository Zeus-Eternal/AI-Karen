"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';
import { MotionConfig } from 'framer-motion';
import { useUIStore, selectAnimationState } from '../store';

interface MotionContextValue {
  reducedMotion: boolean;
  animationsEnabled: boolean;
  setReducedMotion: (reduced: boolean) => void;
  setAnimationsEnabled: (enabled: boolean) => void;
  transitionConfig: {
    duration: number;
    ease: 'linear' | readonly [0.4, 0, 0.2, 1];
  };
}

const MotionContext = createContext<MotionContextValue | undefined>(undefined);

interface MotionProviderProps {
  children: React.ReactNode;
  defaultReducedMotion?: boolean;
  defaultAnimationsEnabled?: boolean;
}

export function MotionProvider({
  children,
  defaultReducedMotion = false,
  defaultAnimationsEnabled = true,
}: MotionProviderProps) {
  const { reducedMotion, setReducedMotion: setStoreReducedMotion } = useUIStore(selectAnimationState);
  const [animationsEnabled, setAnimationsEnabled] = useState(defaultAnimationsEnabled);
  const [mounted, setMounted] = useState(false);

  // Detect system reduced motion preference
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      setStoreReducedMotion(e.matches);
    };

    // Set initial reduced motion preference
    if (!mounted) {
      setStoreReducedMotion(mediaQuery?.matches || defaultReducedMotion);
    }
    
    // Listen for changes
    mediaQuery?.addEventListener('change', handleChange);
    
    return () => mediaQuery?.removeEventListener('change', handleChange);
  }, [defaultReducedMotion, setStoreReducedMotion, mounted]);

  useEffect(() => {
    setMounted(true);
  }, []);

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
      <MotionConfig {...motionConfig}>
        {children}
      </MotionConfig>
    </MotionContext.Provider>
  );
}

export function useMotion() {
  const context = useContext(MotionContext);
  if (context === undefined) {
    throw new Error('useMotion must be used within a MotionProvider');
  }
  return context;
}

// Convenience hook for getting animation variants based on preferences
export function useAnimationVariants() {
  const { reducedMotion, animationsEnabled } = useMotion();
  
  const getVariants = (variants: Record<string, any>) => {
    if (reducedMotion || !animationsEnabled) {
      // Return variants with no animation
      const staticVariants: Record<string, any> = {};
      Object.keys(variants).forEach(key => {
        staticVariants[key] = {
          ...variants[key],
          transition: { duration: 0 },
        };

      return staticVariants;
    }
    return variants;
  };

  const getTransition = (transition: any = {}) => {
    if (reducedMotion || !animationsEnabled) {
      return { duration: 0 };
    }
    return transition;
  };

  return {
    getVariants,
    getTransition,
    shouldAnimate: !reducedMotion && animationsEnabled,
  };
}