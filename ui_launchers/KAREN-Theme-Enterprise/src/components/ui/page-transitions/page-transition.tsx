"use client";

import * as React from 'react';
import { motion } from 'framer-motion';
import { PageTransitionProps } from './types';
import { transitionVariants, reducedMotionVariants } from './transition-variants';
import { useMicroInteractions } from '../micro-interactions/micro-interaction-context';
import { cn } from '@/lib/utils';

export function PageTransition({
  children,
  variant = 'fade',
  duration = 0.3,
  className,
  onTransitionComplete
}: PageTransitionProps) {
  const { reducedMotion } = useMicroInteractions();
  
  const variants = reducedMotion 
    ? reducedMotionVariants[variant]
    : transitionVariants[variant];

  const transition = {
    duration: reducedMotion ? 0.1 : duration,
    ease: "easeInOut" as const
  };

  return (
    <motion.div
      className={cn('w-full h-full', className)}
      initial="initial"
      animate="animate"
      exit="exit"
      variants={variants}
      transition={transition}
      onAnimationComplete={onTransitionComplete}
    >
      {children}
    </motion.div>
  );
}