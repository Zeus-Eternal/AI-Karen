/**
 * Card UI Component
 * 
 * Reusable card component for displaying content in containers.
 */

import React from 'react';
import { cn } from '@/lib/utils';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: string;
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode;
}

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export interface CardDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode;
}

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(({
  children,
  className = '',
  style,
  variant,
  ...props
}, ref) => {
  const variantClasses = variant === 'glass'
    ? 'backdrop-blur-md bg-[color-mix(in srgb,var(--component-card-background) 70%,transparent)]'
    : 'bg-[var(--component-card-background)]';

  return (
    <div
      ref={ref}
      className={cn(
        'relative flex flex-col rounded-[var(--component-card-border-radius,var(--radius-lg))]',
        'border border-[var(--component-card-border)] shadow-[var(--component-card-shadow)]',
        'text-[var(--component-card-foreground)] transition-shadow [transition-duration:var(--duration-fast)] [transition-timing-function:var(--ease-standard)]',
        'focus-within:ring-2 focus-within:ring-[var(--component-card-ring)] focus-within:ring-offset-2',
        'focus-within:ring-offset-[var(--component-card-ring-offset,var(--color-neutral-50))]',
        variantClasses,
        className,
      )}
      style={style}
      {...props}
    >
      {children}
    </div>
  );
});
Card.displayName = 'Card';

export const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ children, className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'px-[var(--space-lg)] py-[var(--space-md)]',
        'border-b border-[var(--component-card-border)]',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  ),
);
CardHeader.displayName = 'CardHeader';

export const CardTitle = React.forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ children, className = '', ...props }, ref) => (
    <h3
      ref={ref}
      className={cn(
        'font-semibold',
        'text-[var(--text-lg)] leading-[var(--line-height-snug)]',
        'text-[var(--component-card-foreground)]',
        className,
      )}
      {...props}
    >
      {children}
    </h3>
  ),
);
CardTitle.displayName = 'CardTitle';

export const CardContent = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ children, className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'px-[var(--space-lg)] py-[var(--space-md)]',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  ),
);
CardContent.displayName = 'CardContent';

export const CardDescription = React.forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ children, className = '', ...props }, ref) => (
    <p
      ref={ref}
      className={cn(
        'text-[var(--text-sm)] leading-[var(--line-height-normal)]',
        'text-[var(--component-card-muted-foreground,var(--color-neutral-600))]',
        className,
      )}
      {...props}
    >
      {children}
    </p>
  ),
);
CardDescription.displayName = 'CardDescription';

export const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ children, className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'px-[var(--space-lg)] py-[var(--space-md)]',
        'border-t border-[var(--component-card-border)]',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  ),
);
CardFooter.displayName = 'CardFooter';
