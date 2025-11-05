"use client";

import React from 'react';
import { Skeleton } from './skeleton';
import { SkeletonButtonProps } from './types';
import { cn } from '@/lib/utils';

const sizeClasses = {
  xs: 'h-6 px-2',
  sm: 'h-8 px-3',
  md: 'h-10 px-4',
  lg: 'h-11 px-6',
  xl: 'h-12 px-8'
};

const variantClasses = {
  default: 'bg-muted',
  outline: 'bg-transparent border border-muted',
  ghost: 'bg-muted/50'
};

export function SkeletonButton({ 
  size = 'md',
  variant = 'default',
  className,
  animated = true,
  width = '5rem'
}: SkeletonButtonProps) {
  const baseClasses = cn(
    'inline-flex items-center justify-center rounded-md',
    sizeClasses[size],
    variantClasses[variant],
    className
  );

  return (
    <Skeleton
      className={baseClasses}
      width={width}
      variant="rounded"
      animated={animated}
    />
  );
}