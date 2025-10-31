/**
 * Enhanced Badge Component
 * 
 * Extended badge component with design token integration and modern styling.
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

// Enhanced badge variants using design tokens
export const enhancedBadgeVariants = cva(
  [
    'inline-flex items-center gap-[var(--space-xs)]',
    'rounded-[var(--radius-full)] border',
    'px-[var(--space-sm)] py-[var(--space-3xs)]',
    'text-[var(--text-xs)] font-semibold',
    'transition-all duration-[var(--duration-fast)] ease-[var(--ease-standard)]',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'select-none',
  ],
  {
    variants: {
      variant: {
        default: [
          'border-transparent bg-[var(--color-primary-500)] text-[var(--color-primary-50)]',
          'hover:bg-[var(--color-primary-600)]',
          'dark:bg-[var(--color-primary-400)] dark:text-[var(--color-primary-950)]',
          'dark:hover:bg-[var(--color-primary-300)]',
        ],
        secondary: [
          'border-transparent bg-[var(--color-secondary-100)] text-[var(--color-secondary-900)]',
          'hover:bg-[var(--color-secondary-200)]',
          'dark:bg-[var(--color-secondary-800)] dark:text-[var(--color-secondary-100)]',
          'dark:hover:bg-[var(--color-secondary-700)]',
        ],
        destructive: [
          'border-transparent bg-[var(--color-error-500)] text-[var(--color-error-50)]',
          'hover:bg-[var(--color-error-600)]',
          'dark:bg-[var(--color-error-400)] dark:text-[var(--color-error-950)]',
          'dark:hover:bg-[var(--color-error-300)]',
        ],
        success: [
          'border-transparent bg-[var(--color-success-500)] text-[var(--color-success-50)]',
          'hover:bg-[var(--color-success-600)]',
          'dark:bg-[var(--color-success-400)] dark:text-[var(--color-success-950)]',
          'dark:hover:bg-[var(--color-success-300)]',
        ],
        warning: [
          'border-transparent bg-[var(--color-warning-500)] text-[var(--color-warning-50)]',
          'hover:bg-[var(--color-warning-600)]',
          'dark:bg-[var(--color-warning-400)] dark:text-[var(--color-warning-950)]',
          'dark:hover:bg-[var(--color-warning-300)]',
        ],
        info: [
          'border-transparent bg-[var(--color-info-500)] text-[var(--color-info-50)]',
          'hover:bg-[var(--color-info-600)]',
          'dark:bg-[var(--color-info-400)] dark:text-[var(--color-info-950)]',
          'dark:hover:bg-[var(--color-info-300)]',
        ],
        outline: [
          'border-[var(--color-neutral-300)] bg-transparent text-[var(--color-neutral-900)]',
          'hover:bg-[var(--color-neutral-100)] hover:border-[var(--color-neutral-400)]',
          'dark:border-[var(--color-neutral-700)] dark:text-[var(--color-neutral-100)]',
          'dark:hover:bg-[var(--color-neutral-800)] dark:hover:border-[var(--color-neutral-600)]',
        ],
        ghost: [
          'border-transparent bg-transparent text-[var(--color-neutral-700)]',
          'hover:bg-[var(--color-neutral-100)] hover:text-[var(--color-neutral-900)]',
          'dark:text-[var(--color-neutral-300)] dark:hover:bg-[var(--color-neutral-800)]',
          'dark:hover:text-[var(--color-neutral-100)]',
        ],
      },
      size: {
        sm: [
          'px-[var(--space-xs)] py-[var(--space-3xs)]',
          'text-[var(--text-xs)]',
          'gap-[var(--space-3xs)]',
        ],
        md: [
          'px-[var(--space-sm)] py-[var(--space-2xs)]',
          'text-[var(--text-xs)]',
          'gap-[var(--space-xs)]',
        ],
        lg: [
          'px-[var(--space-md)] py-[var(--space-xs)]',
          'text-[var(--text-sm)]',
          'gap-[var(--space-xs)]',
        ],
      },
      interactive: {
        true: [
          'cursor-pointer',
          'hover:shadow-[var(--shadow-xs)]',
          'active:scale-95',
          'focus:ring-[var(--focus-ring-color)]',
        ],
        false: '',
      },
      dot: {
        true: 'pl-[var(--space-xs)]',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      interactive: false,
      dot: false,
    },
  }
);

export interface EnhancedBadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof enhancedBadgeVariants> {
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  onRemove?: () => void;
  removable?: boolean;
  dotColor?: string;
}

export const EnhancedBadge = React.forwardRef<HTMLDivElement, EnhancedBadgeProps>(
  ({ 
    className, 
    variant, 
    size, 
    interactive, 
    dot, 
    leftIcon, 
    rightIcon, 
    onRemove, 
    removable = false,
    dotColor,
    children, 
    onClick,
    ...props 
  }, ref) => {
    const isInteractive = interactive || !!onClick || removable;
    
    return (
      <div
        className={cn(
          enhancedBadgeVariants({ 
            variant, 
            size, 
            interactive: isInteractive, 
            dot: dot || !!dotColor, 
            className 
          })
        )}
        ref={ref}
        onClick={onClick}
        role={isInteractive ? 'button' : undefined}
        tabIndex={isInteractive ? 0 : undefined}
        onKeyDown={isInteractive ? (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onClick?.(e as any);
          }
        } : undefined}
        {...props}
      >
        {(dot || dotColor) && (
          <span 
            className={cn(
              'h-2 w-2 rounded-full',
              dotColor ? '' : 'bg-current'
            )}
            style={dotColor ? { backgroundColor: dotColor } : undefined}
            aria-hidden="true"
          />
        )}
        
        {leftIcon && (
          <span className="flex-shrink-0" aria-hidden="true">
            {leftIcon}
          </span>
        )}
        
        <span className="truncate">
          {children}
        </span>
        
        {rightIcon && !removable && (
          <span className="flex-shrink-0" aria-hidden="true">
            {rightIcon}
          </span>
        )}
        
        {removable && (
          <button
            type="button"
            className={cn(
              'flex-shrink-0 ml-1 rounded-full',
              'hover:bg-black/10 dark:hover:bg-white/10',
              'focus:outline-none focus:ring-1 focus:ring-current',
              'transition-colors duration-[var(--duration-fast)]',
              'p-0.5'
            )}
            onClick={(e) => {
              e.stopPropagation();
              onRemove?.();
            }}
            aria-label="Remove"
          >
            <svg
              className="h-3 w-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>
    );
  }
);

EnhancedBadge.displayName = 'EnhancedBadge';

// Badge group component for managing multiple badges
export interface EnhancedBadgeGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  spacing?: 'sm' | 'md' | 'lg';
  wrap?: boolean;
}

export const EnhancedBadgeGroup = React.forwardRef<HTMLDivElement, EnhancedBadgeGroupProps>(
  ({ className, children, spacing = 'md', wrap = true, ...props }, ref) => {
    const spacingClasses = {
      sm: 'gap-[var(--space-xs)]',
      md: 'gap-[var(--space-sm)]',
      lg: 'gap-[var(--space-md)]',
    };

    return (
      <div
        className={cn(
          'flex items-center',
          spacingClasses[spacing],
          wrap && 'flex-wrap',
          className
        )}
        ref={ref}
        {...props}
      >
        {children}
      </div>
    );
  }
);

EnhancedBadgeGroup.displayName = 'EnhancedBadgeGroup';