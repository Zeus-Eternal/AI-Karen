"use client";

import * as React from 'react';
import { motion } from 'framer-motion';
import { SkeletonProps } from './types';
import { useMicroInteractions } from '../micro-interactions/micro-interaction-context';
import { cn } from '@/lib/utils';

const shimmerVariants = {
  animate: {
    backgroundPosition: ['200% 0', '-200% 0'],
  },
  transition: {
    duration: 2,
    repeat: Infinity,
    ease: 'linear',
  }
};

const pulseVariants = {
  animate: {
    opacity: [0.5, 1, 0.5],
  },
  transition: {
    duration: 1.5,
    repeat: Infinity,
    ease: 'easeInOut',
  }
};

export function Skeleton({ 
  className,
  width,
  height,
  variant = 'default',
  animated = true,
  children,
  ...props 
}: SkeletonProps) {
  const { reducedMotion } = useMicroInteractions();
  
  const baseClasses = cn(
    'bg-muted',
    {
      'rounded-md': variant === 'default',
      'rounded-lg': variant === 'rounded',
      'rounded-full': variant === 'circular',
    },
    className
  );

  const style = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  };

  if (!animated || reducedMotion) {
    return (
      <div 
        className={baseClasses}
        style={style}
        {...props}
      >
        {children}
      </div>
    );
  }

  return (
    <motion.div
      className={cn(
        baseClasses,
        'bg-gradient-to-r from-muted via-muted-foreground/10 to-muted bg-[length:200%_100%]'
      )}
      style={style}
      variants={shimmerVariants}
      animate="animate"
      {...props}
    >
      {children}
    </motion.div>
  );
}