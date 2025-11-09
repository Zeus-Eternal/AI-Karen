/**
 * Enhanced Input Component
 * 
 * Extended input component with design token integration and modern styling.
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
// Enhanced input variants using design tokens
export const enhancedInputVariants = cva(
  [
    'flex w-full rounded-[var(--radius-md)]',
    'border border-[var(--color-neutral-300)]',
    'bg-[var(--color-neutral-50)] px-[var(--space-sm)] py-[var(--space-xs)]',
    'text-[var(--text-sm)] text-[var(--color-neutral-900)]',
    'ring-offset-[var(--color-neutral-50)]',
    'transition-all [transition-duration:var(--duration-fast)] [transition-timing-function:var(--ease-standard)]',
    'file:border-0 file:bg-transparent file:text-[var(--text-sm)] file:font-medium',
    '-[var(--color-neutral-500)]',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring-color)] focus-visible:ring-offset-2',
    'focus-visible:border-[var(--color-primary-400)]',
    'disabled:cursor-not-allowed disabled:opacity-50',
    'dark:border-[var(--color-neutral-700)] dark:bg-[var(--color-neutral-900)]',
    'dark:text-[var(--color-neutral-100)] dark:ring-offset-[var(--color-neutral-900)]',
    'dark:-[var(--color-neutral-400)]',
    'dark:focus-visible:border-[var(--color-primary-500)]',
  ],
  {
    variants: {
      size: {
        sm: [
          'h-8 px-[var(--space-xs)] text-[var(--text-xs)]',
        ],
        md: [
          'h-10 px-[var(--space-sm)] text-[var(--text-sm)]',
        ],
        lg: [
          'h-12 px-[var(--space-md)] text-[var(--text-base)]',
        ],
      },
      variant: {
        default: '',
        filled: [
          'bg-[var(--color-neutral-100)] border-transparent',
          'focus-visible:bg-[var(--color-neutral-50)] focus-visible:border-[var(--color-primary-400)]',
          'dark:bg-[var(--color-neutral-800)] dark:focus-visible:bg-[var(--color-neutral-900)]',
        ],
        ghost: [
          'border-transparent bg-transparent',
          'focus-visible:border-[var(--color-primary-400)] focus-visible:bg-[var(--color-neutral-50)]',
          'dark:focus-visible:bg-[var(--color-neutral-900)]',
        ],
      },
      state: {
        default: '',
        error: [
          'border-[var(--color-error-400)] focus-visible:ring-[var(--color-error-400)]',
          'dark:border-[var(--color-error-500)]',
        ],
        success: [
          'border-[var(--color-success-400)] focus-visible:ring-[var(--color-success-400)]',
          'dark:border-[var(--color-success-500)]',
        ],
        warning: [
          'border-[var(--color-warning-400)] focus-visible:ring-[var(--color-warning-400)]',
          'dark:border-[var(--color-warning-500)]',
        ],
      },
    },
    defaultVariants: {
      size: 'md',
      variant: 'default',
      state: 'default',
    },
  }
);
export interface EnhancedInputProps
  extends Omit<React.ComponentProps<'input'>, 'size'>,
    VariantProps<typeof enhancedInputVariants> {
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  helperText?: string;
  errorText?: string;
  label?: string;
  required?: boolean;
}
export const EnhancedInput = React.forwardRef<HTMLInputElement, EnhancedInputProps>(
  ({ 
    className, 
    type = 'text', 
    size, 
    variant, 
    state, 
    leftIcon, 
    rightIcon, 
    helperText, 
    errorText, 
    label, 
    required,
    id,
    ...props 
  }, ref) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    const hasError = state === 'error' || !!errorText;
    const actualState = hasError ? 'error' : state;
    return (
      <div className="w-full">
        {label && (
          <label 
            htmlFor={inputId}
            className={cn(
              'block text-[var(--text-sm)] font-medium mb-[var(--space-xs)]',
              'text-[var(--color-neutral-700)] dark:text-[var(--color-neutral-300)]',
              hasError && 'text-[var(--color-error-600)] dark:text-[var(--color-error-400)]'
            )}
          >
            {label}
            {required && (
              <span className="text-[var(--color-error-500)] ml-1" aria-label="required">
                *
              </span>
            )}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-[var(--space-sm)] top-1/2 -translate-y-1/2 text-[var(--color-neutral-500)] dark:text-[var(--color-neutral-400)]">
              {leftIcon}
            </div>
          )}
          <input
            type={type}
            id={inputId}
            className={cn(
              enhancedInputVariants({ size, variant, state: actualState }),
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              className
            )}
            ref={ref}
            aria-invalid={hasError}
            aria-describedby={
              hasError && errorText 
                ? `${inputId}-error` 
                : helperText 
                ? `${inputId}-helper` 
                : undefined
            }
            {...props} />
          {rightIcon && (
            <div className="absolute right-[var(--space-sm)] top-1/2 -translate-y-1/2 text-[var(--color-neutral-500)] dark:text-[var(--color-neutral-400)]">
              {rightIcon}
            </div>
          )}
        </div>
        {(errorText || helperText) && (
          <p
            id={hasError ? `${inputId}-error` : `${inputId}-helper`}
            className={cn(
              'mt-[var(--space-xs)] text-[var(--text-xs)]',
              hasError 
                ? 'text-[var(--color-error-600)] dark:text-[var(--color-error-400)]'
                : 'text-[var(--color-neutral-600)] dark:text-[var(--color-neutral-400)]'
            )}
            role={hasError ? 'alert' : undefined}
          >
            {errorText || helperText}
          </p>
        )}
      </div>
    );
  }
);
EnhancedInput.displayName = 'EnhancedInput';
