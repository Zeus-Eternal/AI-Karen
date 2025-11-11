"use client";

import { createContext, useContext } from 'react';
import { type Transition, type Variants } from 'framer-motion';
import type { MotionContextValue } from './motion-types';
import { createStaticVariants, createTransition } from './motion-utils';

export const MotionContext = createContext<MotionContextValue | undefined>(undefined);

export function useMotion() {
  const context = useContext(MotionContext);
  if (context === undefined) {
    throw new Error('useMotion must be used within a MotionProvider');
  }
  return context;
}

export function useAnimationVariants() {
  const { reducedMotion, animationsEnabled } = useMotion();

  const getVariants = (variants: Variants): Variants => {
    if (reducedMotion || !animationsEnabled) {
      return createStaticVariants(variants);
    }
    return variants;
  };

  const getTransition = (transition?: Transition): Transition => {
    return createTransition(reducedMotion, animationsEnabled, transition);
  };

  return {
    getVariants,
    getTransition,
    shouldAnimate: !reducedMotion && animationsEnabled,
  };
}
