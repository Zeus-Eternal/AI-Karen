declare module '@/components/ui/label' {
  import type { DetailedHTMLProps, FC, LabelHTMLAttributes } from 'react';

  export type LabelProps = DetailedHTMLProps<LabelHTMLAttributes<HTMLLabelElement>, HTMLLabelElement> & {
    required?: boolean;
  };

  export const Label: FC<LabelProps>;
}
