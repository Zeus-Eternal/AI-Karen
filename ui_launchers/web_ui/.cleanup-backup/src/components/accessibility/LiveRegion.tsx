'use client';

import React, { useEffect, useRef } from 'react';
import { cn } from '../../lib/utils';

interface LiveRegionProps {
  children?: React.ReactNode;
  message?: string;
  politeness?: 'polite' | 'assertive' | 'off';
  atomic?: boolean;
  relevant?: 'additions' | 'removals' | 'text' | 'all';
  className?: string;
  id?: string;
}

export function LiveRegion({
  children,
  message,
  politeness = 'polite',
  atomic = true,
  relevant = 'all',
  className,
  id,
}: LiveRegionProps) {
  const regionRef = useRef<HTMLDivElement>(null);
  const previousMessage = useRef<string>('');

  // Update the live region when message changes
  useEffect(() => {
    if (message && message !== previousMessage.current && regionRef.current) {
      // Clear the region first to ensure screen readers pick up the change
      regionRef.current.textContent = '';
      
      // Add the new message after a brief delay
      setTimeout(() => {
        if (regionRef.current) {
          regionRef.current.textContent = message;
        }
      }, 100);
      
      previousMessage.current = message;
    }
  }, [message]);

  return (
    <div
      ref={regionRef}
      id={id}
      aria-live={politeness}
      aria-atomic={atomic}
      aria-relevant={relevant}
      className={cn(
        // Screen reader only styles
        'sr-only absolute',
        'w-px h-px p-0 m-[-1px]',
        'overflow-hidden',
        'clip-[rect(0,0,0,0)]',
        'whitespace-nowrap',
        'border-0',
        className
      )}
    >
      {children || message}
    </div>
  );
}

// Hook for managing live region announcements
export function useLiveRegion(politeness: 'polite' | 'assertive' = 'polite') {
  const regionRef = useRef<HTMLDivElement>(null);

  const announce = React.useCallback((message: string) => {
    if (regionRef.current) {
      // Clear first
      regionRef.current.textContent = '';
      
      // Then announce
      setTimeout(() => {
        if (regionRef.current) {
          regionRef.current.textContent = message;
        }
      }, 100);
    }
  }, []);

  const LiveRegionComponent = React.useCallback(
    ({ className }: { className?: string }) => (
      <div
        ref={regionRef}
        aria-live={politeness}
        aria-atomic="true"
        className={cn(
          'sr-only absolute w-px h-px p-0 m-[-1px] overflow-hidden clip-[rect(0,0,0,0)] whitespace-nowrap border-0',
          className
        )}
      />
    ),
    [politeness]
  );

  return { announce, LiveRegionComponent };
}

export default LiveRegion;