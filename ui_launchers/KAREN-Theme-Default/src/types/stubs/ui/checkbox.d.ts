declare module '@/components/ui/checkbox' {
  import type { DetailedHTMLProps, FC, InputHTMLAttributes } from 'react';

  export type CheckboxProps = DetailedHTMLProps<InputHTMLAttributes<HTMLInputElement>, HTMLInputElement> & {
    label?: string;
    onCheckedChange?: (checked: boolean | 'indeterminate') => void;
  };

  export const Checkbox: FC<CheckboxProps>;
}
