"use client";

import React from 'react';
import { Skeleton } from './skeleton';
import { SkeletonTextProps } from './types';
import { cn } from '@/lib/utils';

const variantStyles = {
  paragraph: {
    height: '1rem',
    spacing: 'space-y-2'
  },
  heading: {
    height: '1.5rem',
    spacing: 'space-y-3'
  },
  caption: {
    height: '0.875rem',
    spacing: 'space-y-1'
  }
};

export function SkeletonText({ 
  lines = 3,
  className,
  animated = true,
  variant = 'paragraph'
}: SkeletonTextProps) {
  const { height, spacing } = variantStyles[variant];
  
  return (
    <div className={cn(spacing, className)}>
      {Array.from({ length: lines }, (_, index) => {
        // Make the last line shorter to simulate natural text flow
        const isLastLine = index === lines - 1;
        const width = isLastLine && lines > 1 ? '75%' : '100%';
        
        return (
          <Skeleton
            key={index}
            height={height}
            width={width}
            animated={animated}
          />
        );
      })}
    </div>
  );
}