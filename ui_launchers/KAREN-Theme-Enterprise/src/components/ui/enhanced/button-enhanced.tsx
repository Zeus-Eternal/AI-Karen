"use client";

import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';
import { buttonVariants } from './button-enhanced-variants';

/**
 * Enhanced Button Component
 * 
 * Extends the base shadcn/ui button with design token integration,
 * loading states, and enhanced accessibility features.
 * 
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */


export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
  loadingText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const ButtonEnhanced = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      loading = false,
      loadingText,
      leftIcon,
      rightIcon,
      asChild = false,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const Comp = asChild ? Slot : 'button';
    const isDisabled = disabled || loading;

    return (
      <Comp
        className={cn(buttonVariants({ variant, size, loading, className }))}
        ref={ref}
        disabled={isDisabled}
        aria-disabled={isDisabled}
        {...props}
      >
        {loading && (
          <Loader2 
            className="h-4 w-4 animate-spin " 
            aria-hidden="true"
          />
        )}
        {!loading && leftIcon && (
          <span className="inline-flex shrink-0" aria-hidden="true">
            {leftIcon}
          </span>
        )}
        <span className={cn(loading && 'opacity-70')}>
          {loading && loadingText ? loadingText : children}
        </span>
        {!loading && rightIcon && (
          <span className="inline-flex shrink-0" aria-hidden="true">
            {rightIcon}
          </span>
        )}
        
        {/* Screen reader loading announcement */}
        {loading && (
          <span className="sr-only">
            {loadingText || 'Loading...'}
          </span>
        )}
      </Comp>
    );
  }
);

ButtonEnhanced.displayName = 'ButtonEnhanced';

export { ButtonEnhanced };
