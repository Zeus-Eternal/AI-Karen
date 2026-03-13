import { cva } from 'class-variance-authority';

export const enhancedCardVariants = cva(
  [
    'rounded-[var(--radius-lg)] border',
    'transition-all [transition-duration:var(--duration-fast)] [transition-timing-function:var(--ease-standard)]',
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

export const enhancedCardDescriptionVariants = cva(
  [
    'text-[var(--text-sm)]',
    'text-[var(--color-neutral-600)] dark:text-[var(--color-neutral-400)]',
    'leading-relaxed',
  ]
);

export const enhancedCardContentVariants = cva(
  [
    'p-[var(--space-lg)] pt-0',
  ]
);

export const enhancedCardFooterVariants = cva(
  [
    'flex items-center p-[var(--space-lg)] pt-0',
  ]
);
