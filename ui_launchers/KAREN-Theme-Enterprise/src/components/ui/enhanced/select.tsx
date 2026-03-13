/**
 * Enhanced Select Component
 * 
 * Extended select component with design token integration and modern styling.
 * Based on requirements: 1.1, 1.2, 1.3, 11.4
 */
import * as React from 'react';
import * as SelectPrimitive from '@radix-ui/react-select';
import { Check, ChevronDown, ChevronUp } from 'lucide-react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
// Enhanced select trigger variants using design tokens
const enhancedSelectTriggerVariants = cva(
  [
    'flex h-10 w-full items-center justify-between',
    'rounded-[var(--radius-md)] border border-[var(--color-neutral-300)]',
    'bg-[var(--color-neutral-50)] px-[var(--space-sm)] py-[var(--space-xs)]',
    'text-[var(--text-sm)] text-[var(--color-neutral-900)]',
    'ring-offset-[var(--color-neutral-50)]',
    'transition-all [transition-duration:var(--duration-fast)] [transition-timing-function:var(--ease-standard)]',
    '-[var(--color-neutral-500)]',
    'focus:outline-none focus:ring-2 focus:ring-[var(--focus-ring-color)] focus:ring-offset-2',
    'focus:border-[var(--color-primary-400)]',
    'disabled:cursor-not-allowed disabled:opacity-50',
    'dark:border-[var(--color-neutral-700)] dark:bg-[var(--color-neutral-900)]',
    'dark:text-[var(--color-neutral-100)] dark:ring-offset-[var(--color-neutral-900)]',
    'dark:-[var(--color-neutral-400)]',
    'dark:focus:border-[var(--color-primary-500)]',
    '[&>span]:line-clamp-1',
  ],
  {
    variants: {
      size: {
        sm: [
          'h-8 px-[var(--space-xs)] text-[var(--text-xs)]',
        ],
        md: [
          'h-10 px-[var(--space-sm)] text-[var(--text-sm)]',
        ],
        lg: [
          'h-12 px-[var(--space-md)] text-[var(--text-base)]',
        ],
      },
      variant: {
        default: '',
        filled: [
          'bg-[var(--color-neutral-100)] border-transparent',
          'focus:bg-[var(--color-neutral-50)] focus:border-[var(--color-primary-400)]',
          'dark:bg-[var(--color-neutral-800)] dark:focus:bg-[var(--color-neutral-900)]',
        ],
        ghost: [
          'border-transparent bg-transparent',
          'focus:border-[var(--color-primary-400)] focus:bg-[var(--color-neutral-50)]',
          'dark:focus:bg-[var(--color-neutral-900)]',
        ],
      },
      state: {
        default: '',
        error: [
          'border-[var(--color-error-400)] focus:ring-[var(--color-error-400)]',
          'dark:border-[var(--color-error-500)]',
        ],
        success: [
          'border-[var(--color-success-400)] focus:ring-[var(--color-success-400)]',
          'dark:border-[var(--color-success-500)]',
        ],
        warning: [
          'border-[var(--color-warning-400)] focus:ring-[var(--color-warning-400)]',
          'dark:border-[var(--color-warning-500)]',
        ],
      },
    },
    defaultVariants: {
      size: 'md',
      variant: 'default',
      state: 'default',
    },
  }
);
interface EnhancedSelectTriggerProps
  extends React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>,
    VariantProps<typeof enhancedSelectTriggerVariants> {}
export const EnhancedSelectTrigger = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Trigger>,
  EnhancedSelectTriggerProps
>(({ className, size, variant, state, children, ...props }, ref) => (
  <SelectPrimitive.Trigger
    ref={ref}
    className={cn(enhancedSelectTriggerVariants({ size, variant, state, className }))}
    {...props}
   aria-label="Select option">
    {children}
    <SelectPrimitive.Icon asChild aria-label="Select option">
      <ChevronDown className="h-4 w-4 opacity-50 " />
    </SelectPrimitive.Icon>
  </SelectPrimitive.Trigger>
));
EnhancedSelectTrigger.displayName = SelectPrimitive.Trigger.displayName;
// Enhanced select scroll buttons
export const EnhancedSelectScrollUpButton = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.ScrollUpButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollUpButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollUpButton
    ref={ref}
    className={cn(
      'flex cursor-default items-center justify-center py-1',
      className
    )}
    {...props}
   aria-label="Select option">
    <ChevronUp className="h-4 w-4 " />
  </SelectPrimitive.ScrollUpButton>
));
EnhancedSelectScrollUpButton.displayName = SelectPrimitive.ScrollUpButton.displayName;
export const EnhancedSelectScrollDownButton = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.ScrollDownButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollDownButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollDownButton
    ref={ref}
    className={cn(
      'flex cursor-default items-center justify-center py-1',
      className
    )}
    {...props}
   aria-label="Select option">
    <ChevronDown className="h-4 w-4 " />
  </SelectPrimitive.ScrollDownButton>
));
EnhancedSelectScrollDownButton.displayName = SelectPrimitive.ScrollDownButton.displayName;
// Enhanced select content
export const EnhancedSelectContent = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Content>
>(({ className, children, position = 'popper', ...props }, ref) => (
  <SelectPrimitive.Portal aria-label="Select option">
    <SelectPrimitive.Content
      ref={ref}
      className={cn(
        'relative z-50 max-h-96 min-w-[8rem] overflow-hidden',
        'rounded-[var(--radius-md)] border border-[var(--color-neutral-200)]',
        'bg-[var(--color-neutral-50)] text-[var(--color-neutral-900)]',
        'shadow-[var(--shadow-md)]',
        'data-[state=open]:animate-in data-[state=closed]:animate-out',
        'data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
        'data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95',
        'data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2',
        'data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
        'dark:border-[var(--color-neutral-800)] dark:bg-[var(--color-neutral-900)]',
        'dark:text-[var(--color-neutral-100)]',
        position === 'popper' &&
          'data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1',
        className
      )}
      position={position}
      {...props}
     aria-label="Close">
      <EnhancedSelectScrollUpButton />
      <SelectPrimitive.Viewport
        className={cn(
          'p-1',
          position === 'popper' &&
            'h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)]'
        )}
       aria-label="Select option">
        {children}
      </SelectPrimitive.Viewport>
      <EnhancedSelectScrollDownButton />
    </SelectPrimitive.Content>
  </SelectPrimitive.Portal>
));
EnhancedSelectContent.displayName = SelectPrimitive.Content.displayName;
// Enhanced select label
export const EnhancedSelectLabel = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Label>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Label
    ref={ref}
    className={cn(
      'py-[var(--space-xs)] pl-8 pr-2',
      'text-[var(--text-sm)] font-semibold',
      'text-[var(--color-neutral-700)] dark:text-[var(--color-neutral-300)]',
      className
    )}
    {...props} />
));
EnhancedSelectLabel.displayName = SelectPrimitive.Label.displayName;
// Enhanced select item
export const EnhancedSelectItem = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Item>
>(({ className, children, ...props }, ref) => (
  <SelectPrimitive.Item
    ref={ref}
    className={cn(
      'relative flex w-full cursor-default select-none items-center',
      'rounded-[var(--radius-sm)] py-[var(--space-xs)] pl-8 pr-2',
      'text-[var(--text-sm)] outline-none',
      'transition-colors [transition-duration:var(--duration-fast)]',
      'focus:bg-[var(--color-primary-100)] focus:text-[var(--color-primary-900)]',
      'data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
      'dark:focus:bg-[var(--color-primary-800)] dark:focus:text-[var(--color-primary-100)]',
      className
    )}
    {...props}
   aria-label="Select option">
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center ">
      <SelectPrimitive.ItemIndicator aria-label="Select option">
        <Check className="h-4 w-4 " />
      </SelectPrimitive.ItemIndicator>
    </span>
    <SelectPrimitive.ItemText aria-label="Select option">{children}</SelectPrimitive.ItemText>
  </SelectPrimitive.Item>
));
EnhancedSelectItem.displayName = SelectPrimitive.Item.displayName;
// Enhanced select separator
export const EnhancedSelectSeparator = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Separator
    ref={ref}
    className={cn(
      '-mx-1 my-1 h-px bg-[var(--color-neutral-200)]',
      'dark:bg-[var(--color-neutral-800)]',
      className
    )}
    {...props} />
));
EnhancedSelectSeparator.displayName = SelectPrimitive.Separator.displayName;
// Enhanced select value
export const EnhancedSelectValue = SelectPrimitive.Value;
// Main enhanced select component
interface EnhancedSelectProps {
  children: React.ReactNode;
  label?: string;
  helperText?: string;
  errorText?: string;
  required?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'filled' | 'ghost';
  state?: 'default' | 'error' | 'success' | 'warning';
  placeholder?: string;
  value?: string;
  onValueChange?: (value: string) => void;
  disabled?: boolean;
}
export const EnhancedSelect = React.forwardRef<
  HTMLDivElement,
  EnhancedSelectProps
>(({ 
  children, 
  label, 
  helperText, 
  errorText, 
  required, 
  size = 'md',
  variant = 'default',
  state = 'default',
  placeholder,
  ...props 
}, ref) => {
  const generatedId = React.useId();
  const selectId = `select-${generatedId}`;
  const hasError = state === 'error' || !!errorText;
  const actualState = hasError ? 'error' : state;
  return (
    <div ref={ref} className="w-full">
      {label && (
        <label 
          htmlFor={selectId}
          className={cn(
            'block text-[var(--text-sm)] font-medium mb-[var(--space-xs)]',
            'text-[var(--color-neutral-700)] dark:text-[var(--color-neutral-300)]',
            hasError && 'text-[var(--color-error-600)] dark:text-[var(--color-error-400)]'
          )}
        >
          {label}
          {required && (
            <span className="text-[var(--color-error-500)] ml-1" aria-label="required">
              *
            </span>
          )}
        </label>
      )}
      <SelectPrimitive.Root {...props} aria-label="Select option">
        <EnhancedSelectTrigger 
          id={selectId}
          size={size}
          variant={variant}
          state={actualState}
          aria-invalid={hasError}
          aria-describedby={
            hasError && errorText 
              ? `${selectId}-error` 
              : helperText 
              ? `${selectId}-helper` 
              : undefined
          }
        >
          <EnhancedSelectValue placeholder={placeholder} />
        </EnhancedSelectTrigger>
        <EnhancedSelectContent>
          {children}
        </EnhancedSelectContent>
      </SelectPrimitive.Root>
      {(errorText || helperText) && (
        <p
          id={hasError ? `${selectId}-error` : `${selectId}-helper`}
          className={cn(
            'mt-[var(--space-xs)] text-[var(--text-xs)]',
            hasError 
              ? 'text-[var(--color-error-600)] dark:text-[var(--color-error-400)]'
              : 'text-[var(--color-neutral-600)] dark:text-[var(--color-neutral-400)]'
          )}
          role={hasError ? 'alert' : undefined}
        >
          {errorText || helperText}
        </p>
      )}
    </div>
  );
});

EnhancedSelect.displayName = 'EnhancedSelect';
