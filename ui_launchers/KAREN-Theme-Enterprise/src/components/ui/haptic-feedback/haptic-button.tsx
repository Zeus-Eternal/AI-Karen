"use client";

import * as React from 'react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

import { useHaptic } from './use-haptic';
import type { HapticButtonProps } from './types';

export function HapticButton({
  children,
  hapticPattern = 'light',
  hapticEnabled = true,
  onClick,
  className,
  ariaLabel = 'Haptic button',
  ...props
}: HapticButtonProps) {
  const { triggerHaptic } = useHaptic();

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    // Trigger haptic feedback before the click handler
    if (hapticEnabled) {
      triggerHaptic(hapticPattern);
    }
    
    // Call the original onClick handler if provided
    onClick?.(event);
  };

  return (
    <Button
      className={cn(
        'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
        'bg-primary text-primary-foreground hover:bg-primary/90',
        'h-10 px-4 py-2',
        className
      )}
      onClick={handleClick}
      aria-label={ariaLabel}
      {...props}
    >
      {children}
    </Button>
  );
}
