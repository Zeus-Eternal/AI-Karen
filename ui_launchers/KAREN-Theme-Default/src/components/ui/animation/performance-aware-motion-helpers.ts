"use client";

import * as React from 'react';
import type { MotionProps } from 'framer-motion';

import { useReducedMotion } from '@/hooks/use-reduced-motion';
import {
  usePerformanceAwareAnimation,
  performanceAnimationVariants,
} from '@/utils/animation-performance';

export interface PerformanceAwareMotionProps extends Omit<MotionProps, 'variants'> {
  variant?: keyof typeof performanceAnimationVariants;
  children: React.ReactNode;
  enableGPU?: boolean;
  optimizeForPerformance?: boolean;
  className?: string;
}

export type AnimationStartHandler = NonNullable<MotionProps['onAnimationStart']>;
export type AnimationCompleteHandler = NonNullable<MotionProps['onAnimationComplete']>;

export interface StaggeredMotionProps {
  children: React.ReactNode;
  staggerDelay?: number;
  className?: string;
  optimizeForPerformance?: boolean;
}

export interface PerformanceAnimatePresenceProps {
  children: React.ReactNode;
  mode?: 'wait' | 'sync' | 'popLayout';
  optimizeForPerformance?: boolean;
}

export function usePerformanceAwareMotionValue() {
  const reducedMotion = useReducedMotion();
  const { shouldUseGPU, animationQuality } = usePerformanceAwareAnimation(reducedMotion);

  const createOptimizedTransition = React.useCallback((baseDuration: number = 0.3) => {
    if (reducedMotion) {
      return { duration: 0.1 };
    }

    const durationMultiplier =
      animationQuality === 'low' ? 0.5 : animationQuality === 'medium' ? 0.75 : 1;

    return {
      duration: baseDuration * durationMultiplier,
      ease: [0.4, 0, 0.2, 1],
    };
  }, [reducedMotion, animationQuality]);

  const createOptimizedSpring = React.useCallback(() => {
    if (reducedMotion) {
      return { duration: 0.1 };
    }

    const springConfig = {
      high: { stiffness: 300, damping: 30, mass: 0.8 },
      medium: { stiffness: 250, damping: 25, mass: 1 },
      low: { stiffness: 200, damping: 20, mass: 1.2 },
    } as const;

    return {
      type: 'spring' as const,
      ...springConfig[animationQuality],
    };
  }, [reducedMotion, animationQuality]);

  return {
    shouldUseGPU,
    animationQuality,
    createOptimizedTransition,
    createOptimizedSpring,
  };
}
