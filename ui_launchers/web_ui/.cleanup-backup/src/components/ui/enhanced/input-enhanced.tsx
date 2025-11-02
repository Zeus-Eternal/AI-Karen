'use client';

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { Eye, EyeOff, AlertCircle, CheckCircle2 } from 'lucide-react';

/**
 * Enhanced Input Component
 * 
 * Extends the base shadcn/ui input with design token integration,
 * validation states, icons, and enhanced accessibility features.
 * 
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

const inputVariants = cva(
  [
    // Base styles using design tokens
    'flex h-10 w-full rounded-md border border-input',
    'bg-background px-3 py-2 text-sm',
    'ring-offset-background file:border-0 file:bg-transparent',
    'file:text-sm file:font-medium placeholder:text-muted-foreground',
    'focus-visible:outline-none focus-visible:ring-2',
    'focus-visible:ring-ring focus-visible:ring-offset-2',
    'disabled:cursor-not-allowed disabled:opacity-50',
    
    // Enhanced interaction styles
    'transition-all duration-200 ease-out',
    'hover:border-border/80 focus-visible:border-ring',
  ],
  {
    variants: {
      variant: {
        default: '',
        filled: [
          'bg-muted border-transparent',
          'hover:bg-muted/80 focus-visible:bg-background',
        ],
        ghost: [
          'border-transparent bg-transparent',
          'hover:bg-muted/50 focus-visible:bg-background',
          'focus-visible:border-input',
        ],
      },
      inputSize: {
        sm: 'h-8 px-2 text-xs',
        default: 'h-10 px-3 text-sm',
        lg: 'h-12 px-4 text-base',
      },
      state: {
        default: '',
        error: [
          'border-destructive focus-visible:ring-destructive',
          'text-destructive placeholder:text-destructive/60',
        ],
        success: [
          'border-success focus-visible:ring-success',
          'text-success',
        ],
        warning: [
          'border-warning focus-visible:ring-warning',
          'text-warning',
        ],
      },
    },
    defaultVariants: {
      variant: 'default',
      inputSize: 'default',
      state: 'default',
    },
  }
);

const inputWrapperVariants = cva(
  [
    'relative flex items-center',
  ],
  {
    variants: {
      hasLeftIcon: {
        true: '',
        false: '',
      },
      hasRightIcon: {
        true: '',
        false: '',
      },
    },
  }
);

export interface InputEnhancedProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  error?: string;
  success?: string;
  warning?: string;
  helperText?: string;
  label?: string;
  showPasswordToggle?: boolean;
  containerClassName?: string;
}

const InputEnhanced = React.forwardRef<HTMLInputElement, InputEnhancedProps>(
  (
    {
      className,
      variant,
      inputSize,
      state,
      type = 'text',
      leftIcon,
      rightIcon,
      error,
      success,
      warning,
      helperText,
      label,
      showPasswordToggle = false,
      containerClassName,
      id,
      ...props
    },
    ref
  ) => {
    const [showPassword, setShowPassword] = React.useState(false);
    const [internalId] = React.useState(() => id || `input-${Math.random().toString(36).substr(2, 9)}`);
    
    // Determine state based on props
    const currentState = error ? 'error' : success ? 'success' : warning ? 'warning' : state;
    
    // Determine input type
    const inputType = showPasswordToggle && type === 'password' 
      ? (showPassword ? 'text' : 'password')
      : type;

    // Status icon
    const StatusIcon = currentState === 'error' 
      ? AlertCircle 
      : currentState === 'success' 
      ? CheckCircle2 
      : null;

    // Helper text content
    const helperContent = error || success || warning || helperText;

    return (
      <div className={cn('space-y-2', containerClassName)}>
        {label && (
          <label
            htmlFor={internalId}
            className={cn(
              'text-sm font-medium leading-none',
              'peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
              currentState === 'error' && 'text-destructive',
              currentState === 'success' && 'text-success',
              currentState === 'warning' && 'text-warning'
            )}
          >
            {label}
          </label>
        )}
        
        <div className={cn(inputWrapperVariants({ 
          hasLeftIcon: !!leftIcon, 
          hasRightIcon: !!(rightIcon || StatusIcon || showPasswordToggle) 
        }))}>
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
              <div className="h-4 w-4 flex items-center justify-center">
                {leftIcon}
              </div>
            </div>
          )}
          
          <input
            type={inputType}
            id={internalId}
            className={cn(
              inputVariants({ variant, inputSize, state: currentState }),
              leftIcon && 'pl-10',
              (rightIcon || StatusIcon || showPasswordToggle) && 'pr-10',
              className
            )}
            ref={ref}
            aria-invalid={currentState === 'error'}
            aria-describedby={helperContent ? `${internalId}-helper` : undefined}
            {...props}
          />
          
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
            {StatusIcon && (
              <StatusIcon 
                className={cn(
                  'h-4 w-4',
                  currentState === 'error' && 'text-destructive',
                  currentState === 'success' && 'text-success',
                  currentState === 'warning' && 'text-warning'
                )}
                aria-hidden="true"
              />
            )}
            
            {showPasswordToggle && type === 'password' && (
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className={cn(
                  'text-muted-foreground hover:text-foreground',
                  'focus-visible:outline-none focus-visible:ring-2',
                  'focus-visible:ring-ring focus-visible:ring-offset-2',
                  'rounded-sm p-0.5 transition-colors'
                )}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={-1}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            )}
            
            {rightIcon && !StatusIcon && (
              <div className="text-muted-foreground">
                <div className="h-4 w-4 flex items-center justify-center">
                  {rightIcon}
                </div>
              </div>
            )}
          </div>
        </div>
        
        {helperContent && (
          <p
            id={`${internalId}-helper`}
            className={cn(
              'text-xs leading-relaxed',
              currentState === 'error' && 'text-destructive',
              currentState === 'success' && 'text-success',
              currentState === 'warning' && 'text-warning',
              !currentState && 'text-muted-foreground'
            )}
            role={currentState === 'error' ? 'alert' : undefined}
          >
            {helperContent}
          </p>
        )}
      </div>
    );
  }
);

InputEnhanced.displayName = 'InputEnhanced';

export { InputEnhanced, inputVariants };