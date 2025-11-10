declare module '@/components/ui/textarea' {
  import type { DetailedHTMLProps, FC, TextareaHTMLAttributes } from 'react';

  export type TextareaProps = DetailedHTMLProps<TextareaHTMLAttributes<HTMLTextAreaElement>, HTMLTextAreaElement>;

  export const Textarea: FC<TextareaProps>;
}
