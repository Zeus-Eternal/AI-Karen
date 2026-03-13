import { cva } from 'class-variance-authority';

export const inputVariants = cva(
  [
    // Base styles using design tokens
    'flex h-10 w-full rounded-md border border-input',
    'bg-background px-3 py-2 text-sm',
    'ring-offset-background file:border-0 file:bg-transparent',
    'file:text-sm file:font-medium -muted-foreground',
    'focus-visible:outline-none focus-visible:ring-2',
    'focus-visible:ring-ring focus-visible:ring-offset-2',
    'disabled:cursor-not-allowed disabled:opacity-50',
    // Enhanced interaction styles
    'transition-all duration-200 ease-out',
    'hover:border-border/80 focus-visible:border-ring',
  ],
  {
    variants: {
      variant: {
        default: '',
        filled: [
          'bg-muted border-transparent',
          'hover:bg-muted/80 focus-visible:bg-background',
        ],
        ghost: [
          'border-transparent bg-transparent',
          'hover:bg-muted/50 focus-visible:bg-background',
          'focus-visible:border-input',
        ],
      },
      inputSize: {
        sm: 'h-8 px-2 text-xs',
        default: 'h-10 px-3 text-sm',
        lg: 'h-12 px-4 text-base',
      },
      state: {
        default: '',
        error: [
          'border-destructive focus-visible:ring-destructive',
          'text-destructive -destructive/60',
        ],
        success: [
          'border-success focus-visible:ring-success',
          'text-success',
        ],
        warning: [
          'border-warning focus-visible:ring-warning',
          'text-warning',
        ],
      },
    },
    defaultVariants: {
      variant: 'default',
      inputSize: 'default',
      state: 'default',
    },
  }
);

