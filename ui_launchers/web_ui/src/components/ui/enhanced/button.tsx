/**
 * Enhanced Button Component
 * 
 * Extended button component with design token integration and modern styling.
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

import React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

// Enhanced button variants using design tokens
export const enhancedButtonVariants = cva(
  [
    'inline-flex items-center justify-center gap-2',
    'rounded-[var(--radius-md)] font-medium',
    'transition-all [transition-duration:var(--duration-fast)] [transition-timing-function:var(--ease-standard)]',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring-color)] focus-visible:ring-offset-2',
    'disabled:opacity-60 disabled:cursor-not-allowed disabled:pointer-events-none',
    'select-none touch-manipulation',
    'will-change-transform',
  ],
  {
    variants: {
      variant: {
        default: [
          'bg-[var(--color-primary-500)] text-[var(--color-primary-50)]',
          'hover:bg-[var(--color-primary-600)] hover:shadow-[var(--shadow-sm)]',
          'active:bg-[var(--color-primary-700)] active:scale-[0.98]',
          'dark:bg-[var(--color-primary-400)] dark:text-[var(--color-primary-950)]',
          'dark:hover:bg-[var(--color-primary-300)]',
        ],
        destructive: [
          'bg-[var(--color-error-500)] text-[var(--color-error-50)]',
          'hover:bg-[var(--color-error-600)] hover:shadow-[var(--shadow-sm)]',
          'active:bg-[var(--color-error-700)] active:scale-[0.98]',
          'dark:bg-[var(--color-error-400)] dark:text-[var(--color-error-950)]',
        ],
        outline: [
          'border border-[var(--color-neutral-300)] bg-transparent',
          'text-[var(--color-neutral-900)] hover:bg-[var(--color-neutral-100)]',
          'hover:border-[var(--color-neutral-400)] hover:shadow-[var(--shadow-xs)]',
          'active:bg-[var(--color-neutral-200)] active:scale-[0.98]',
          'dark:border-[var(--color-neutral-700)] dark:text-[var(--color-neutral-100)]',
          'dark:hover:bg-[var(--color-neutral-800)] dark:hover:border-[var(--color-neutral-600)]',
        ],
        secondary: [
          'bg-[var(--color-secondary-100)] text-[var(--color-secondary-900)]',
          'hover:bg-[var(--color-secondary-200)] hover:shadow-[var(--shadow-sm)]',
          'active:bg-[var(--color-secondary-300)] active:scale-[0.98]',
          'dark:bg-[var(--color-secondary-800)] dark:text-[var(--color-secondary-100)]',
          'dark:hover:bg-[var(--color-secondary-700)]',
        ],
        ghost: [
          'bg-transparent text-[var(--color-neutral-700)]',
          'hover:bg-[var(--color-neutral-100)] hover:text-[var(--color-neutral-900)]',
          'active:bg-[var(--color-neutral-200)] active:scale-[0.98]',
          'dark:text-[var(--color-neutral-300)] dark:hover:bg-[var(--color-neutral-800)]',
          'dark:hover:text-[var(--color-neutral-100)]',
        ],
        link: [
          'bg-transparent text-[var(--color-primary-600)] underline-offset-4',
          'hover:text-[var(--color-primary-700)] hover:underline',
          'active:text-[var(--color-primary-800)]',
          'dark:text-[var(--color-primary-400)] dark:hover:text-[var(--color-primary-300)]',
        ],
      },
      size: {
        sm: [
          'h-8 px-[var(--space-sm)] text-[var(--text-sm)]',
          'gap-[var(--space-xs)]',
        ],
        md: [
          'h-10 px-[var(--space-md)] text-[var(--text-sm)]',
          'gap-[var(--space-xs)]',
        ],
        lg: [
          'h-12 px-[var(--space-lg)] text-[var(--text-base)]',
          'gap-[var(--space-sm)]',
        ],
        xl: [
          'h-14 px-[var(--space-xl)] text-[var(--text-lg)]',
          'gap-[var(--space-sm)]',
        ],
        icon: [
          'h-10 w-10 p-0',
        ],
        'icon-sm': [
          'h-8 w-8 p-0',
        ],
        'icon-lg': [
          'h-12 w-12 p-0',
        ],
      },
      loading: {
        true: 'cursor-wait',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      loading: false,
    },
  }
);

export interface EnhancedButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof enhancedButtonVariants> {
  asChild?: boolean;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  loadingText?: string;
}

export const EnhancedButton = React.forwardRef<HTMLButtonElement, EnhancedButtonProps>(
  ({ 
    className, 
    variant, 
    size, 
    asChild = false, 
    loading = false,
    leftIcon,
    rightIcon,
    loadingText,
    children,
    disabled,
    ...props 
  }, ref) => {
    const Comp = asChild ? Slot : 'button';
    
    const isDisabled = disabled || loading;
    
    // When using asChild, we need to handle the content differently
    if (asChild) {
      return (
        <Comp
          className={cn(enhancedButtonVariants({ variant, size, loading, className }))}
          ref={ref}
          {...props}
        >
          {children}
        </Comp>
      );
    }

    return (
      <Comp
        className={cn(enhancedButtonVariants({ variant, size, loading, className }))}
        ref={ref}
        disabled={isDisabled}
        aria-disabled={isDisabled}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin h-4 w-4 "
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {!loading && leftIcon && leftIcon}
        <span className={loading ? 'opacity-70' : ''}>
          {loading && loadingText ? loadingText : children}
        </span>
        {!loading && rightIcon && rightIcon}
      </Comp>
    );
  }
);

EnhancedButton.displayName = 'EnhancedButton';
