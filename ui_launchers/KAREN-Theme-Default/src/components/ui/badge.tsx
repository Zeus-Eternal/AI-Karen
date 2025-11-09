/**
 * Badge UI Component
 * 
 * Reusable badge component for displaying status indicators and labels.
 */

import React from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'outline' | 'secondary' | 'destructive';
  onClick?: () => void;
  title?: string;
}

export const Badge: React.FC<BadgeProps> = ({ 
  children, 
  className = '', 
  variant = 'default',
  onClick,
  title 
}) => {
  const baseClasses = [
    'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium',
    'transition-colors [transition-duration:var(--duration-fast)] [transition-timing-function:var(--ease-standard)]',
    'tracking-[var(--letter-spacing-tight)]',
  ].join(' ');

  const variantClasses: Record<Required<BadgeProps>['variant'], string> = {
    default: [
      'bg-[var(--component-badge-default-background)]',
      'text-[var(--component-badge-default-foreground)]',
      'border-[var(--component-badge-default-border,transparent)]',
    ].join(' '),
    outline: [
      'bg-[var(--component-badge-outline-background,transparent)]',
      'text-[var(--component-badge-outline-foreground)]',
      'border-[var(--component-badge-outline-border,var(--color-neutral-400))]',
    ].join(' '),
    secondary: [
      'bg-[var(--component-badge-secondary-background)]',
      'text-[var(--component-badge-secondary-foreground)]',
      'border-[var(--component-badge-secondary-border,transparent)]',
    ].join(' '),
    destructive: [
      'bg-[var(--component-badge-destructive-background)]',
      'text-[var(--component-badge-destructive-foreground)]',
      'border-[var(--component-badge-destructive-border,transparent)]',
    ].join(' '),
  };

  const Component = onClick ? 'button' : 'span';

  return (
    <Component
      className={cn(baseClasses, variantClasses[variant], className)}
      onClick={onClick}
      title={title}
    >
      {children}
    </Component>
  );
};
