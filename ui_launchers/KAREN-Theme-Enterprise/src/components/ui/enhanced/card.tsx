/**
 * Enhanced Card Component
 * 
 * Extended card component with design token integration and modern styling.
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */

import * as React from 'react';
import { type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import {
  enhancedCardVariants,
  enhancedCardHeaderVariants,
  enhancedCardTitleVariants,
  enhancedCardDescriptionVariants,
  enhancedCardContentVariants,
  enhancedCardFooterVariants,
} from './card-variants';

export type EnhancedCardProps = React.HTMLAttributes<HTMLDivElement> &
  VariantProps<typeof enhancedCardVariants> & { asChild?: boolean };

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

export type EnhancedCardHeaderProps = React.HTMLAttributes<HTMLDivElement> &
  VariantProps<typeof enhancedCardHeaderVariants>;

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

export type EnhancedCardTitleProps = React.HTMLAttributes<HTMLHeadingElement> &
  VariantProps<typeof enhancedCardTitleVariants> & {
    as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
  };

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

export type EnhancedCardDescriptionProps = React.HTMLAttributes<HTMLParagraphElement>;

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

export type EnhancedCardContentProps = React.HTMLAttributes<HTMLDivElement>;

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

export type EnhancedCardFooterProps = React.HTMLAttributes<HTMLDivElement>;

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
