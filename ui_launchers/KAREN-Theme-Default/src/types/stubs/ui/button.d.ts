declare module '@/components/ui/button' {
  import type {
    ButtonHTMLAttributes,
    DetailedHTMLProps,
    ForwardRefExoticComponent,
    ReactNode,
    RefAttributes,
  } from 'react';

  export type ButtonVariant =
    | 'default'
    | 'secondary'
    | 'destructive'
    | 'outline'
    | 'ghost'
    | 'link';

  export type ButtonSize = 'sm' | 'md' | 'lg' | 'icon' | 'icon-sm' | 'icon-lg';

  export interface ButtonProps
    extends DetailedHTMLProps<ButtonHTMLAttributes<HTMLButtonElement>, HTMLButtonElement> {
    variant?: ButtonVariant;
    size?: ButtonSize;
    icon?: ReactNode;
    asChild?: boolean;
  }

  export const buttonVariants: (options?: {
    variant?: ButtonVariant;
    size?: ButtonSize;
    className?: string;
  }) => string;

  export const Button: ForwardRefExoticComponent<ButtonProps & RefAttributes<HTMLButtonElement>>;
}
