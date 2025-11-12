"use client";

import React, { useCallback, useRef } from 'react';
import { cn } from '../../lib/utils';

type PolitenessSetting = 'polite' | 'assertive';

export function useLiveRegion(politeness: PolitenessSetting = 'polite') {
  const regionRef = useRef<HTMLDivElement>(null);

  const announce = useCallback((message: string) => {
    if (regionRef.current) {
      regionRef.current.textContent = '';

      setTimeout(() => {
        if (regionRef.current) {
          regionRef.current.textContent = message;
        }
      }, 100);
    }
  }, []);

  const LiveRegionComponent = useCallback(
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
