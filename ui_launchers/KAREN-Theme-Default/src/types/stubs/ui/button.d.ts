declare module '@/components/ui/button' {
  import type { ButtonHTMLAttributes, DetailedHTMLProps, FC, ReactNode } from 'react';

  export type ButtonProps = DetailedHTMLProps<ButtonHTMLAttributes<HTMLButtonElement>, HTMLButtonElement> & {
    variant?: string;
    size?: string;
    icon?: ReactNode;
  };

  export const Button: FC<ButtonProps>;
}
