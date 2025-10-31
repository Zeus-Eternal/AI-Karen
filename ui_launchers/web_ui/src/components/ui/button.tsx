/**
 * Button UI Component
 * 
 * Reusable button component with various styles and sizes.
 */

import React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const baseButtonClasses = [
  'inline-flex items-center justify-center gap-[var(--space-xs)] rounded-[var(--radius-md)] border font-medium',
  'transition-[color,background-color,border-color,box-shadow,transform] duration-[var(--duration-fast)] ease-[var(--ease-standard)]',
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
  'disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed',
  'active:scale-95 sm:active:scale-100',
];

export const buttonVariants = cva(
  baseButtonClasses.join(' '),
  {
    variants: {
      variant: {
        default: [
          'bg-[var(--component-button-default-background)]',
          'text-[var(--component-button-default-foreground)]',
          'border-[var(--component-button-default-border,transparent)]',
          'shadow-[var(--component-button-default-shadow,var(--shadow-sm))]',
          'hover:bg-[var(--component-button-default-hover)]',
          'focus-visible:ring-[var(--component-button-default-ring)]',
          'focus-visible:ring-offset-[var(--component-button-default-ring-offset,var(--color-neutral-50))]',
        ].join(' '),
        secondary: [
          'bg-[var(--component-button-secondary-background)]',
          'text-[var(--component-button-secondary-foreground)]',
          'border-[var(--component-button-secondary-border,transparent)]',
          'shadow-[var(--component-button-secondary-shadow,var(--shadow-xs))]',
          'hover:bg-[var(--component-button-secondary-hover)]',
          'focus-visible:ring-[var(--component-button-secondary-ring,var(--component-button-default-ring))]',
          'focus-visible:ring-offset-[var(--component-button-secondary-ring-offset,var(--color-neutral-50))]',
        ].join(' '),
        destructive: [
          'bg-[var(--component-button-destructive-background)]',
          'text-[var(--component-button-destructive-foreground,var(--color-neutral-50))]',
          'border-[var(--component-button-destructive-border,transparent)]',
          'shadow-[var(--component-button-destructive-shadow,var(--shadow-sm))]',
          'hover:bg-[var(--component-button-destructive-hover)]',
          'focus-visible:ring-[var(--component-button-destructive-ring,var(--component-button-default-ring))]',
          'focus-visible:ring-offset-[var(--component-button-destructive-ring-offset,var(--color-neutral-50))]',
        ].join(' '),
        outline: [
          'bg-[var(--component-button-outline-background,transparent)]',
          'text-[var(--component-button-outline-foreground,var(--color-neutral-900))]',
          'border-[var(--component-button-outline-border,var(--color-neutral-300))]',
          'shadow-[var(--component-button-outline-shadow,var(--shadow-xs))]',
          'hover:bg-[var(--component-button-outline-hover,var(--color-neutral-200))]',
          'focus-visible:ring-[var(--component-button-outline-ring,var(--component-button-default-ring))]',
          'focus-visible:ring-offset-[var(--component-button-outline-ring-offset,var(--color-neutral-50))]',
        ].join(' '),
        ghost: [
          'bg-[var(--component-button-ghost-background,transparent)]',
          'text-[var(--component-button-ghost-foreground,var(--color-neutral-900))]',
          'border-[var(--component-button-ghost-border,transparent)]',
          'shadow-[var(--component-button-ghost-shadow,var(--shadow-xs))]',
          'hover:bg-[var(--component-button-ghost-hover,var(--color-neutral-100))]',
          'focus-visible:ring-[var(--component-button-ghost-ring,var(--component-button-default-ring))]',
          'focus-visible:ring-offset-[var(--component-button-ghost-ring-offset,var(--color-neutral-50))]',
        ].join(' '),
        link: [
          'bg-[var(--component-button-link-background,transparent)]',
          'text-[var(--component-button-link-foreground,var(--color-primary-600))]',
          'border-[var(--component-button-link-border,transparent)]',
          'hover:text-[var(--component-button-link-hover,var(--color-primary-500))]',
          'focus-visible:ring-[var(--component-button-link-ring,var(--component-button-default-ring))]',
          'focus-visible:ring-offset-[var(--component-button-link-ring-offset,var(--color-neutral-50))]',
          'underline-offset-[var(--space-2xs)] hover:underline',
        ].join(' '),
      },
      size: {
        sm: 'h-8 px-3 py-1.5 text-sm',
        md: 'h-10 px-4 py-2 text-sm',
        lg: 'h-11 px-6 py-3 text-base',
        icon: 'h-8 w-8 p-0',
        'icon-sm': 'h-8 w-8 p-0',
        'icon-lg': 'h-12 w-12 p-0',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';