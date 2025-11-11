"use client";

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useReducedMotion } from '@/hooks/use-reduced-motion';
import {
  usePerformanceAwareAnimation,
  performanceAnimationVariants,
  reducedMotionVariants,
  useWillChange
} from '@/utils/animation-performance';
import {
  AnimationCompleteHandler,
  AnimationStartHandler,
  PerformanceAnimatePresenceProps,
  PerformanceAwareMotionProps,
  StaggeredMotionProps,
} from './performance-aware-motion-helpers';

export const PerformanceAwareMotion: React.FC<PerformanceAwareMotionProps> = ({
  variant = 'fade',
  children,
  enableGPU = true,
  optimizeForPerformance = true,
  className = '',
  ...motionProps
}) => {
  const reducedMotion = useReducedMotion();
  const { getOptimizedVariant, getOptimizedCSS, shouldUseGPU } = usePerformanceAwareAnimation(reducedMotion);
  const { elementRef, addWillChange, clearWillChange } = useWillChange<HTMLDivElement>();

  // Get the appropriate variant based on reduced motion preference
  const animationVariant = getOptimizedVariant(variant);
  
  // Combine CSS optimizations
  const optimizedCSS = React.useMemo(() => {
    const baseCSS = optimizeForPerformance && enableGPU && shouldUseGPU 
      ? getOptimizedCSS() 
      : {};
    
    return {
      ...baseCSS,
      className,
    };
  }, [optimizeForPerformance, enableGPU, shouldUseGPU, getOptimizedCSS, className]);

  // Handle animation lifecycle for will-change optimization
  const handleAnimationStart = React.useCallback<AnimationStartHandler>((event) => {
    if (optimizeForPerformance) {
      addWillChange(['transform', 'opacity']);
    }
    motionProps.onAnimationStart?.(event);
  }, [optimizeForPerformance, addWillChange, motionProps]);

  const handleAnimationComplete = React.useCallback<AnimationCompleteHandler>((definition) => {
    if (optimizeForPerformance) {
      clearWillChange();
    }
    motionProps.onAnimationComplete?.(definition);
  }, [optimizeForPerformance, clearWillChange, motionProps]);

  return (
    <motion.div
      ref={elementRef}
      variants={animationVariant}
      initial="initial"
      animate="animate"
      exit="exit"
      {...optimizedCSS}
      {...motionProps}
      onAnimationStart={handleAnimationStart}
      onAnimationComplete={handleAnimationComplete}
    >
      {children}
    </motion.div>
  );
};

// Specialized components for common animation patterns
export const FadeMotion: React.FC<Omit<PerformanceAwareMotionProps, 'variant'>> = (props) => (
  <PerformanceAwareMotion variant="fade" {...props} />
);

export const SlideUpMotion: React.FC<Omit<PerformanceAwareMotionProps, 'variant'>> = (props) => (
  <PerformanceAwareMotion variant="slideUp" {...props} />
);

export const SlideDownMotion: React.FC<Omit<PerformanceAwareMotionProps, 'variant'>> = (props) => (
  <PerformanceAwareMotion variant="slideDown" {...props} />
);

export const SlideLeftMotion: React.FC<Omit<PerformanceAwareMotionProps, 'variant'>> = (props) => (
  <PerformanceAwareMotion variant="slideLeft" {...props} />
);

export const SlideRightMotion: React.FC<Omit<PerformanceAwareMotionProps, 'variant'>> = (props) => (
  <PerformanceAwareMotion variant="slideRight" {...props} />
);

export const ScaleMotion: React.FC<Omit<PerformanceAwareMotionProps, 'variant'>> = (props) => (
  <PerformanceAwareMotion variant="scale" {...props} />
);

export const SpringMotion: React.FC<Omit<PerformanceAwareMotionProps, 'variant'>> = (props) => (
  <PerformanceAwareMotion variant="spring" {...props} />
);

// Staggered animation container
// eslint-disable-next-line react-refresh/only-export-components
export interface StaggeredMotionProps {
  children: React.ReactNode;
  staggerDelay?: number;
  className?: string;
  optimizeForPerformance?: boolean;
}

export const StaggeredMotion: React.FC<StaggeredMotionProps> = ({
  children,
  staggerDelay = 0.05,
  className = '',
  optimizeForPerformance = true,
}) => {
  const reducedMotion = useReducedMotion();
  const { shouldUseGPU, getOptimizedCSS } = usePerformanceAwareAnimation(reducedMotion);

  const staggerVariants = React.useMemo(() => {
    if (reducedMotion) {
      return reducedMotionVariants.stagger;
    }

    return {
      animate: {
        transition: {
          staggerChildren: staggerDelay,
          delayChildren: 0.1,
        },
      },
    };
  }, [reducedMotion, staggerDelay]);

  const optimizedCSS = React.useMemo(() => {
    return optimizeForPerformance && shouldUseGPU ? getOptimizedCSS() : {};
  }, [optimizeForPerformance, shouldUseGPU, getOptimizedCSS]);

  return (
    <motion.div
      variants={staggerVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={className}
      style={optimizedCSS}
    >
      {children}
    </motion.div>
  );
};

// Staggered item component
export const StaggeredItem: React.FC<{
  children: React.ReactNode;
  className?: string;
  optimizeForPerformance?: boolean;
}> = ({ children, className = '', optimizeForPerformance = true }) => {
  const reducedMotion = useReducedMotion();
  const { shouldUseGPU, getOptimizedCSS } = usePerformanceAwareAnimation(reducedMotion);
  const { elementRef, addWillChange, clearWillChange } = useWillChange<HTMLDivElement>();

  const itemVariants = reducedMotion 
    ? reducedMotionVariants.staggerItem 
    : performanceAnimationVariants.staggerItem;

  const optimizedCSS = React.useMemo(() => {
    return optimizeForPerformance && shouldUseGPU ? getOptimizedCSS() : {};
  }, [optimizeForPerformance, shouldUseGPU, getOptimizedCSS]);

  const handleAnimationStart = React.useCallback(() => {
    if (optimizeForPerformance) {
      addWillChange(['transform', 'opacity']);
    }
  }, [optimizeForPerformance, addWillChange]);

  const handleAnimationComplete = React.useCallback(() => {
    if (optimizeForPerformance) {
      clearWillChange();
    }
  }, [optimizeForPerformance, clearWillChange]);

  return (
    <motion.div
      ref={elementRef}
      variants={itemVariants}
      className={className}
      style={optimizedCSS}
      onAnimationStart={handleAnimationStart}
      onAnimationComplete={handleAnimationComplete}
    >
      {children}
    </motion.div>
  );
};

// Performance-aware AnimatePresence wrapper
export const PerformanceAnimatePresence: React.FC<PerformanceAnimatePresenceProps> = ({
  children,
  mode = 'wait',
}) => {
  const reducedMotion = useReducedMotion();

  // Disable complex animations in reduced motion mode
  const presenceMode = reducedMotion ? 'sync' : mode;

  return (
    <AnimatePresence mode={presenceMode}>
      {children}
    </AnimatePresence>
  );
};

export default PerformanceAwareMotion;
