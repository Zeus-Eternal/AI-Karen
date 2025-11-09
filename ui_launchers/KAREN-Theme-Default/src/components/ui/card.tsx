/**
 * Card UI Component
 * 
 * Reusable card component for displaying content in containers.
 */

import React from 'react';
import { cn } from '@/lib/utils';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  role?: string;
  'aria-label'?: string;
  variant?: string;
  onClick?: () => void;
}

export interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
}

export interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export interface CardDescriptionProps {
  children: React.ReactNode;
  className?: string;
}

export interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  className = '', 
  style,
  role,
  'aria-label': ariaLabel,
  variant,
  onClick 
}) => {
  const variantClasses = variant === 'glass'
    ? 'backdrop-blur-md bg-[color-mix(in srgb,var(--component-card-background) 70%,transparent)]'
    : 'bg-[var(--component-card-background)]';

  return (
    <div
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
      role={role}
      aria-label={ariaLabel}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<CardHeaderProps> = ({ children, className = '' }) => {
  return (
    <div
      className={cn(
        'px-[var(--space-lg)] py-[var(--space-md)]',
        'border-b border-[var(--component-card-border)]',
        className,
      )}
    >
      {children}
    </div>
  );
};

export const CardTitle: React.FC<CardTitleProps> = ({ children, className = '' }) => {
  return (
    <h3
      className={cn(
        'font-semibold',
        'text-[var(--text-lg)] leading-[var(--line-height-snug)]',
        'text-[var(--component-card-foreground)]',
        className,
      )}
    >
      {children}
    </h3>
  );
};

export const CardContent: React.FC<CardContentProps> = ({ children, className = '' }) => {
  return (
    <div
      className={cn(
        'px-[var(--space-lg)] py-[var(--space-md)]',
        className,
      )}
    >
      {children}
    </div>
  );
};

export const CardDescription: React.FC<CardDescriptionProps> = ({ children, className = '' }) => {
  return (
    <p
      className={cn(
        'text-[var(--text-sm)] leading-[var(--line-height-normal)]',
        'text-[var(--component-card-muted-foreground,var(--color-neutral-600))]',
        className,
      )}
    >
      {children}
    </p>
  );
};

export const CardFooter: React.FC<CardFooterProps> = ({ children, className = '' }) => {
  return (
    <div
      className={cn(
        'px-[var(--space-lg)] py-[var(--space-md)]',
        'border-t border-[var(--component-card-border)]',
        className,
      )}
    >
      {children}
    </div>
  );
};
