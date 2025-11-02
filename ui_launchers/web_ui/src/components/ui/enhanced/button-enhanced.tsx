"use client";

import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

/**
 * Enhanced Button Component
 * 
 * Extends the base shadcn/ui button with design token integration,
 * loading states, and enhanced accessibility features.
 * 
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

const buttonVariants = cva(
  [
    // Base styles using design tokens
    'inline-flex items-center justify-center gap-2',
    'whitespace-nowrap rounded-md text-sm font-medium',
    'transition-colors focus-visible:outline-none focus-visible:ring-2',
    'focus-visible:ring-ring focus-visible:ring-offset-2',
    'disabled:pointer-events-none disabled:opacity-50',
    'relative overflow-hidden',
    
    // Enhanced interaction styles
    'transform transition-all duration-200 ease-out',
    'hover:scale-[1.02] active:scale-[0.98]',
    'focus-visible:ring-offset-background',
    
    // Design token integration
    '[&:not(:disabled)]:hover:shadow-md',
    '[&:not(:disabled)]:active:shadow-sm',
  ],
  {
    variants: {
      variant: {
        default: [
          'bg-primary text-primary-foreground',
          'hover:bg-primary/90',
          'shadow-sm hover:shadow-md',
        ],
        destructive: [
          'bg-destructive text-destructive-foreground',
          'hover:bg-destructive/90',
          'shadow-sm hover:shadow-md',
        ],
        outline: [
          'border border-input bg-background',
          'hover:bg-accent hover:text-accent-foreground',
          'hover:border-accent-foreground/20',
        ],
        secondary: [
          'bg-secondary text-secondary-foreground',
          'hover:bg-secondary/80',
          'shadow-sm hover:shadow-md',
        ],
        ghost: [
          'hover:bg-accent hover:text-accent-foreground',
          'hover:shadow-sm',
        ],
        link: [
          'text-primary underline-offset-4',
          'hover:underline hover:text-primary/80',
          'shadow-none hover:shadow-none',
          'transform-none hover:scale-100 active:scale-100',
        ],
        // New enhanced variants
        gradient: [
          'bg-gradient-to-r from-primary to-secondary',
          'text-primary-foreground',
          'hover:from-primary/90 hover:to-secondary/90',
          'shadow-lg hover:shadow-xl',
        ],
        glass: [
          'bg-background/80 backdrop-blur-sm',
          'border border-border/50',
          'hover:bg-background/90 hover:border-border',
          'shadow-sm hover:shadow-md',
        ],
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        xl: 'h-12 rounded-lg px-10 text-base',
        icon: 'h-10 w-10',
        'icon-sm': 'h-8 w-8',
        'icon-lg': 'h-12 w-12',
      },
      loading: {
        true: 'cursor-not-allowed',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
      loading: false,
    },
  }
);

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

export { ButtonEnhanced, buttonVariants };