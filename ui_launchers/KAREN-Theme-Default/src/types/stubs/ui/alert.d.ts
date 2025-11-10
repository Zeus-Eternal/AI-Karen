declare module '@/components/ui/alert' {
  import type { FC, HTMLAttributes } from 'react';

  export const Alert: FC<HTMLAttributes<HTMLDivElement>>;
  export const AlertTitle: FC<HTMLAttributes<HTMLParagraphElement>>;
  export const AlertDescription: FC<HTMLAttributes<HTMLDivElement>>;
}
