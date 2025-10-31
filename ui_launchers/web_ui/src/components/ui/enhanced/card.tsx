/**
 * Enhanced Card Component
 * 
 * Extended card component with design token integration and modern styling.
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

// Enhanced card variants using design tokens
export const enhancedCardVariants = cva(
  [
    'rounded-[var(--radius-lg)] border',
    'transition-all duration-[var(--duration-fast)] ease-[var(--ease-standard)]',
    'will-change-transform',
  ],
  {
    variants: {
      variant: {
        default: [
          'bg-[var(--color-neutral-50)] border-[var(--color-neutral-200)]',
          'shadow-[var(--shadow-xs)]',
          'dark:bg-[var(--color-neutral-900)] dark:border-[var(--color-neutral-800)]',
        ],
        elevated: [
          'bg-[var(--color-neutral-50)] border-[var(--color-neutral-300)]',
          'shadow-[var(--shadow-md)]',
          'dark:bg-[var(--color-neutral-900)] dark:border-[var(--color-neutral-700)]',
        ],
        outlined: [
          'bg-transparent border-2 border-dashed border-[var(--color-neutral-300)]',
          'dark:border-[var(--color-neutral-700)]',
        ],
        glass: [
          'bg-[var(--glass-background)] border-[var(--color-neutral-300)]',
          'backdrop-blur-[var(--backdrop-blur-lg)] shadow-[var(--shadow-md)]',
          'dark:bg-[var(--glass-background)] dark:border-[var(--color-neutral-700)]',
        ],
      },
      interactive: {
        true: [
          'cursor-pointer',
          'hover:shadow-[var(--shadow-sm)] hover:-translate-y-0.5',
          'active:translate-y-0 active:shadow-[var(--shadow-xs)]',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring-color)]',
        ],
        false: '',
      },
      padding: {
        none: 'p-0',
        sm: 'p-[var(--space-sm)]',
        md: 'p-[var(--space-md)]',
        lg: 'p-[var(--space-lg)]',
        xl: 'p-[var(--space-xl)]',
      },
    },
    defaultVariants: {
      variant: 'default',
      interactive: false,
      padding: 'none',
    },
  }
);

export interface EnhancedCardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof enhancedCardVariants> {
  asChild?: boolean;
}

export const EnhancedCard = React.forwardRef<HTMLDivElement, EnhancedCardProps>(
  ({ className, variant, interactive, padding, asChild = false, ...props }, ref) => {
    const Comp = asChild ? 'div' : 'div';
    
    return (
      <Comp
        className={cn(enhancedCardVariants({ variant, interactive, padding, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);

EnhancedCard.displayName = 'EnhancedCard';

// Enhanced Card Header
export const enhancedCardHeaderVariants = cva(
  [
    'flex flex-col space-y-[var(--space-xs)]',
    'p-[var(--space-lg)]',
  ],
  {
    variants: {
      bordered: {
        true: 'border-b border-[var(--color-neutral-200)] dark:border-[var(--color-neutral-800)]',
        false: '',
      },
    },
    defaultVariants: {
      bordered: false,
    },
  }
);

export interface EnhancedCardHeaderProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof enhancedCardHeaderVariants> {}

export const EnhancedCardHeader = React.forwardRef<HTMLDivElement, EnhancedCardHeaderProps>(
  ({ className, bordered, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(enhancedCardHeaderVariants({ bordered, className }))}
      {...props}
    />
  )
);

EnhancedCardHeader.displayName = 'EnhancedCardHeader';

// Enhanced Card Title
export const enhancedCardTitleVariants = cva(
  [
    'font-semibold leading-none tracking-tight',
    'text-[var(--color-neutral-900)] dark:text-[var(--color-neutral-100)]',
  ],
  {
    variants: {
      size: {
        sm: 'text-[var(--text-sm)]',
        md: 'text-[var(--text-base)]',
        lg: 'text-[var(--text-lg)]',
        xl: 'text-[var(--text-xl)]',
      },
    },
    defaultVariants: {
      size: 'lg',
    },
  }
);

export interface EnhancedCardTitleProps
  extends React.HTMLAttributes<HTMLHeadingElement>,
    VariantProps<typeof enhancedCardTitleVariants> {
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

export const EnhancedCardTitle = React.forwardRef<HTMLHeadingElement, EnhancedCardTitleProps>(
  ({ className, size, as: Comp = 'h3', ...props }, ref) => (
    <Comp
      ref={ref}
      className={cn(enhancedCardTitleVariants({ size, className }))}
      {...props}
    />
  )
);

EnhancedCardTitle.displayName = 'EnhancedCardTitle';

// Enhanced Card Description
export const enhancedCardDescriptionVariants = cva(
  [
    'text-[var(--text-sm)]',
    'text-[var(--color-neutral-600)] dark:text-[var(--color-neutral-400)]',
    'leading-relaxed',
  ]
);

export interface EnhancedCardDescriptionProps
  extends React.HTMLAttributes<HTMLParagraphElement> {}

export const EnhancedCardDescription = React.forwardRef<HTMLParagraphElement, EnhancedCardDescriptionProps>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn(enhancedCardDescriptionVariants(), className)}
      {...props}
    />
  )
);

EnhancedCardDescription.displayName = 'EnhancedCardDescription';

// Enhanced Card Content
export const enhancedCardContentVariants = cva(
  [
    'p-[var(--space-lg)] pt-0',
  ]
);

export interface EnhancedCardContentProps
  extends React.HTMLAttributes<HTMLDivElement> {}

export const EnhancedCardContent = React.forwardRef<HTMLDivElement, EnhancedCardContentProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(enhancedCardContentVariants(), className)}
      {...props}
    />
  )
);

EnhancedCardContent.displayName = 'EnhancedCardContent';

// Enhanced Card Footer
export const enhancedCardFooterVariants = cva(
  [
    'flex items-center p-[var(--space-lg)] pt-0',
  ]
);

export interface EnhancedCardFooterProps
  extends React.HTMLAttributes<HTMLDivElement> {}

export const EnhancedCardFooter = React.forwardRef<HTMLDivElement, EnhancedCardFooterProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(enhancedCardFooterVariants(), className)}
      {...props}
    />
  )
);

EnhancedCardFooter.displayName = 'EnhancedCardFooter';