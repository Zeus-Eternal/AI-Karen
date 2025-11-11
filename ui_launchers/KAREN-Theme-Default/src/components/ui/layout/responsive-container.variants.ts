import { cva, type VariantProps } from 'class-variance-authority';

export const responsiveContainerVariants = cva(
  'w-full',
  {
    variants: {
      size: {
        xs: 'max-w-xs',
        sm: 'max-w-sm',
        md: 'max-w-md',
        lg: 'max-w-lg',
        xl: 'max-w-xl',
        '2xl': 'max-w-2xl',
        full: 'max-w-full',
        screen: 'max-w-screen',
      },
      center: {
        true: 'mx-auto',
        false: '',
      },
      fluid: {
        true: 'max-w-none',
        false: '',
      },
      containerQueries: {
        true: 'container-responsive',
        false: '',
      },
      responsive: {
        true: 'responsive-container',
        false: '',
      },
    },
    defaultVariants: {
      size: 'full',
      center: false,
      fluid: false,
      containerQueries: false,
      responsive: false,
    },
  }
);

export type ResponsiveContainerVariants = VariantProps<typeof responsiveContainerVariants>;
