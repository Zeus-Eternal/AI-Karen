declare module '@/components/ui/input' {
  import type { DetailedHTMLProps, FC, InputHTMLAttributes } from 'react';

  export type InputProps = DetailedHTMLProps<InputHTMLAttributes<HTMLInputElement>, HTMLInputElement>;

  export const Input: FC<InputProps>;
}
