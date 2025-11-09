"use client";

import React from 'react';
import { Skeleton } from './skeleton';
import { SkeletonText } from './skeleton-text';
import { SkeletonAvatar } from './skeleton-avatar';
import { SkeletonButton } from './skeleton-button';
import { SkeletonCardProps } from './types';
import { cn } from '@/lib/utils';

export function SkeletonCard({ 
  className,
  animated = true,
  showImage = true,
  showAvatar = false,
  showActions = true,
  imageHeight = '12rem'
}: SkeletonCardProps) {
  return (
    <div className={cn('rounded-lg border bg-card p-6 space-y-4', className)}>
      {/* Image placeholder */}
      {showImage && (
        <Skeleton
          height={imageHeight}
          variant="rounded"
          animated={animated}
        />
      )}
      
      {/* Header with optional avatar */}
      <div className="flex items-start space-x-4">
        {showAvatar && (
          <SkeletonAvatar size="md" animated={animated} />
        )}
        <div className="flex-1 space-y-2">
          <Skeleton height="1.5rem" width="60%" animated={animated} />
          <Skeleton height="1rem" width="40%" animated={animated} />
        </div>
      </div>
      
      {/* Content */}
      <div className="space-y-3">
        <SkeletonText 
          lines={3} 
          variant="paragraph" 
          animated={animated}
        />
      </div>
      
      {/* Actions */}
      {showActions && (
        <div className="flex justify-between items-center pt-4">
          <div className="flex space-x-2">
            <SkeletonButton size="sm" animated={animated} />
            <SkeletonButton size="sm" variant="outline" animated={animated} />
          </div>
          <Skeleton height="1rem" width="4rem" animated={animated} />
        </div>
      )}
    </div>
  );
}