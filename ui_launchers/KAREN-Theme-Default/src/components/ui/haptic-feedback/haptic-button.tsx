"use client";

import React from 'react';
import { useHaptic } from './use-haptic';
import { HapticButtonProps } from './types';
import { cn } from '@/lib/utils';
import { Button } from './button';  // Assuming the Button component is imported like this

export function HapticButton({
  children,
  hapticPattern = 'light',
  hapticEnabled = true,
  onClick,
  className,
  ariaLabel = 'Haptic Button',  // Added a default for aria-label
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
      aria-label={ariaLabel}  // Ensures the button is accessible
      {...props}
    >
      {children}
    </Button>
  );
}
