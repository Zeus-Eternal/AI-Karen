'use client';

import React from 'react';
import { Skeleton } from './skeleton';
import { SkeletonAvatarProps } from './types';
import { cn } from '@/lib/utils';

const sizeClasses = {
  xs: 'w-6 h-6',
  sm: 'w-8 h-8',
  md: 'w-10 h-10',
  lg: 'w-12 h-12',
  xl: 'w-16 h-16'
};

export function SkeletonAvatar({ 
  size = 'md',
  className,
  animated = true
}: SkeletonAvatarProps) {
  return (
    <Skeleton
      className={cn(sizeClasses[size], className)}
      variant="circular"
      animated={animated}
    />
  );
}