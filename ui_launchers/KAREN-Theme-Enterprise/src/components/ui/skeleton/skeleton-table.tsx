"use client";

import * as React from 'react';
import { Skeleton } from './skeleton';
import { SkeletonTableProps } from './types';
import { cn } from '@/lib/utils';

export function SkeletonTable({ 
  rows = 5,
  columns = 4,
  className,
  animated = true,
  showHeader = true
}: SkeletonTableProps) {
  return (
    <div className={cn('w-full', className)}>
      <div className="rounded-md border">
        {/* Table Header */}
        {showHeader && (
          <div className="border-b bg-muted/50 p-4 sm:p-4 md:p-6">
            <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
              {Array.from({ length: columns }, (_, index) => (
                <Skeleton
                  key={`header-${index}`}
                  height="1rem"
                  width="80%"
                  animated={animated}
                />
              ))}
            </div>
          </div>
        )}
        
        {/* Table Body */}
        <div className="divide-y">
          {Array.from({ length: rows }, (_, rowIndex) => (
            <div key={`row-${rowIndex}`} className="p-4 sm:p-4 md:p-6">
              <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
                {Array.from({ length: columns }, (_, colIndex) => {
                  // Vary the width of skeleton items to make it look more natural
                  const widths = ['100%', '75%', '90%', '60%'];
                  const width = widths[colIndex % widths.length];
                  
                  return (
                    <Skeleton
                      key={`cell-${rowIndex}-${colIndex}`}
                      height="1rem"
                      width={width}
                      animated={animated}
                    />
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}