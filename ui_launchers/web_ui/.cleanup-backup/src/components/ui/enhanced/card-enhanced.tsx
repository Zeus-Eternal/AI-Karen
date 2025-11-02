'use client';

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

/**
 * Enhanced Card Component
 * 
 * Extends the base shadcn/ui card with design token integration,
 * multiple variants, and enhanced interaction states.
 * 
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

const cardVariants = cva(
  [
    // Base styles using design tokens
    'rounded-lg border bg-card text-card-foreground',
    'transition-all duration-200 ease-out',
    'relative overflow-hidden',
  ],
  {
    variants: {
      variant: {
        default: [
          'shadow-sm hover:shadow-md',
          'border-border',
        ],
        elevated: [
          'shadow-md hover:shadow-lg',
          'border-border/50',
        ],
        outlined: [
          'border-2 border-dashed border-border',
          'bg-background hover:bg-card',
          'shadow-none hover:shadow-sm',
        ],
        glass: [
          'bg-card/80 backdrop-blur-sm',
          'border-border/50 hover:border-border',
          'shadow-sm hover:shadow-md',
        ],
        gradient: [
          'bg-gradient-to-br from-card to-card/80',
          'border-border/30',
          'shadow-md hover:shadow-lg',
        ],
      },
      interactive: {
        true: [
          'cursor-pointer',
          'hover:scale-[1.01] active:scale-[0.99]',
          'focus-visible:outline-none focus-visible:ring-2',
          'focus-visible:ring-ring focus-visible:ring-offset-2',
          'focus-visible:ring-offset-background',
        ],
        false: '',
      },
      padding: {
        none: 'p-0',
        sm: 'p-4',
        default: 'p-6',
        lg: 'p-8',
      },
    },
    defaultVariants: {
      variant: 'default',
      interactive: false,
      padding: 'default',
    },
  }
);

const cardHeaderVariants = cva(
  [
    'flex flex-col space-y-1.5',
  ],
  {
    variants: {
      padding: {
        none: 'p-0',
        sm: 'p-4 pb-2',
        default: 'p-6 pb-4',
        lg: 'p-8 pb-6',
      },
    },
    defaultVariants: {
      padding: 'default',
    },
  }
);

const cardContentVariants = cva(
  '',
  {
    variants: {
      padding: {
        none: 'p-0',
        sm: 'p-4 pt-0',
        default: 'p-6 pt-0',
        lg: 'p-8 pt-0',
      },
    },
    defaultVariants: {
      padding: 'default',
    },
  }
);

const cardFooterVariants = cva(
  [
    'flex items-center',
  ],
  {
    variants: {
      padding: {
        none: 'p-0',
        sm: 'p-4 pt-2',
        default: 'p-6 pt-4',
        lg: 'p-8 pt-6',
      },
    },
    defaultVariants: {
      padding: 'default',
    },
  }
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {
  asChild?: boolean;
}

export interface CardHeaderProps
  extends React.HTMLAttributes<HTMLDivElement>,
    Pick<VariantProps<typeof cardHeaderVariants>, 'padding'> {}

export interface CardContentProps
  extends React.HTMLAttributes<HTMLDivElement>,
    Pick<VariantProps<typeof cardContentVariants>, 'padding'> {}

export interface CardFooterProps
  extends React.HTMLAttributes<HTMLDivElement>,
    Pick<VariantProps<typeof cardFooterVariants>, 'padding'> {}

const CardEnhanced = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, interactive, padding, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardVariants({ variant, interactive, padding, className }))}
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
      {...props}
    />
  )
);
CardEnhanced.displayName = 'CardEnhanced';

const CardHeaderEnhanced = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, padding, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardHeaderVariants({ padding, className }))}
      {...props}
    />
  )
);
CardHeaderEnhanced.displayName = 'CardHeaderEnhanced';

const CardTitleEnhanced = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      'text-2xl font-semibold leading-none tracking-tight',
      'text-card-foreground',
      className
    )}
    {...props}
  />
));
CardTitleEnhanced.displayName = 'CardTitleEnhanced';

const CardDescriptionEnhanced = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn(
      'text-sm text-muted-foreground',
      'leading-relaxed',
      className
    )}
    {...props}
  />
));
CardDescriptionEnhanced.displayName = 'CardDescriptionEnhanced';

const CardContentEnhanced = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, padding, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardContentVariants({ padding, className }))}
      {...props}
    />
  )
);
CardContentEnhanced.displayName = 'CardContentEnhanced';

const CardFooterEnhanced = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, padding, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(cardFooterVariants({ padding, className }))}
      {...props}
    />
  )
);
CardFooterEnhanced.displayName = 'CardFooterEnhanced';

export {
  CardEnhanced,
  CardHeaderEnhanced,
  CardFooterEnhanced,
  CardTitleEnhanced,
  CardDescriptionEnhanced,
  CardContentEnhanced,
  cardVariants,
};