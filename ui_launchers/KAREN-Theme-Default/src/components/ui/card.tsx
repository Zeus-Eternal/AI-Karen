/**
 * Card UI Component
 *
 * Reusable card component for displaying content in containers.
 * Enhanced with modern aesthetics, hover effects, and production-ready features.
 */

import * as React from 'react';
import { cn } from '@/lib/utils';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'outlined' | 'elevated';
  hoverable?: boolean;
  pressable?: boolean;
  loading?: boolean;
  _headerAction?: React.ReactNode;
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  action?: React.ReactNode;
  separator?: boolean;
}

export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode;
  subtitle?: string;
  truncate?: boolean;
}

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export interface CardDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode;
  muted?: boolean;
  truncate?: boolean;
}

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  separator?: boolean;
  actions?: React.ReactNode;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(({
  children,
  className = '',
  style,
  variant = 'default',
  hoverable = false,
  pressable = false,
  loading = false,
  _headerAction,
  ...props
}, ref) => {
  const variantClasses = React.useMemo(() => {
    switch (variant) {
      case 'glass':
        return 'backdrop-blur-md bg-[color-mix(in srgb,var(--component-card-background) 70%,transparent)] border-transparent';
      case 'outlined':
        return 'bg-background border-border shadow-none';
      case 'elevated':
        return 'bg-background border-border shadow-lg';
      default:
        return 'bg-[var(--component-card-background)] border-[var(--component-card-border)] shadow-[var(--component-card-shadow)]';
    }
  }, [variant]);

  return (
    <div
      ref={ref}
      className={cn(
        'relative flex flex-col rounded-[var(--component-card-border-radius,var(--radius-lg))]',
        'text-[var(--component-card-foreground)] transition-all duration-300 ease-in-out',
        'focus-within:ring-2 focus-within:ring-[var(--component-card-ring)] focus-within:ring-offset-2',
        'focus-within:ring-offset-[var(--component-card-ring-offset,var(--color-neutral-50))]',
        variantClasses,
        hoverable && 'hover:shadow-md hover:border-primary/20',
        pressable && 'active:scale-[0.98] active:shadow-inner',
        loading && 'opacity-70 pointer-events-none',
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
  ({ children, className = '', action, separator = true, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'px-[var(--space-lg)] py-[var(--space-md)]',
        separator && 'border-b border-[var(--component-card-border)]',
        className,
      )}
      {...props}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {children}
        </div>
        {action && (
          <div className="ml-4 flex-shrink-0">
            {action}
          </div>
        )}
      </div>
    </div>
  ),
);
CardHeader.displayName = 'CardHeader';

export const CardTitle = React.forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ children, className = '', subtitle, truncate = false, ...props }, ref) => (
    <div>
      <h3
        ref={ref}
        className={cn(
          'font-semibold',
          'text-[var(--text-lg)] leading-[var(--line-height-snug)]',
          'text-[var(--component-card-foreground)]',
          truncate && 'truncate',
          className,
        )}
        {...props}
      >
        {children}
      </h3>
      {subtitle && (
        <p className="text-sm text-muted-foreground mt-1">
          {subtitle}
        </p>
      )}
    </div>
  ),
);
CardTitle.displayName = 'CardTitle';

export const CardContent = React.forwardRef<HTMLDivElement, CardContentProps>(
  ({ children, className = '', padding = 'lg', ...props }, ref) => {
    const paddingClasses = React.useMemo(() => {
      switch (padding) {
        case 'none': return '';
        case 'sm': return 'px-[var(--space-md)] py-[var(--space-sm)]';
        case 'md': return 'px-[var(--space-lg)] py-[var(--space-md)]';
        case 'lg': return 'px-[var(--space-lg)] py-[var(--space-md)]';
      }
    }, [padding]);

    return (
      <div
        ref={ref}
        className={cn(paddingClasses, className)}
        {...props}
      >
        {children}
      </div>
    );
  },
);
CardContent.displayName = 'CardContent';

export const CardDescription = React.forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ children, className = '', muted = true, truncate = false, ...props }, ref) => (
    <p
      ref={ref}
      className={cn(
        'text-[var(--text-sm)] leading-[var(--line-height-normal)]',
        muted ? 'text-[var(--component-card-muted-foreground,var(--color-neutral-600))]' : 'text-foreground',
        truncate && 'truncate',
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
  ({ children, className = '', separator = true, actions, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'px-[var(--space-lg)] py-[var(--space-md)]',
        separator && 'border-t border-[var(--component-card-border)]',
        className,
      )}
      {...props}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          {children}
        </div>
        {actions && (
          <div className="ml-4 flex-shrink-0">
            {actions}
          </div>
        )}
      </div>
    </div>
  ),
);
CardFooter.displayName = 'CardFooter';

// Card with built-in header action
export const CardWithHeader = React.forwardRef<HTMLDivElement, Omit<CardProps, 'children'> & {
  title: React.ReactNode;
  description?: React.ReactNode;
  headerAction?: React.ReactNode;
  children: React.ReactNode;
}>(({
  title,
  description,
  headerAction,
  children,
  className,
  variant = 'default',
  hoverable = false,
  ...props
}, ref) => (
  <Card ref={ref} className={className} variant={variant} hoverable={hoverable} {...props}>
    <CardHeader action={headerAction}>
      <CardTitle>{title}</CardTitle>
      {description && (
        <CardDescription>{description}</CardDescription>
      )}
    </CardHeader>
    <CardContent>
      {children}
    </CardContent>
  </Card>
));

CardWithHeader.displayName = 'CardWithHeader';
