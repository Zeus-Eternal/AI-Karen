declare module '@/components/ui/progress' {
  import type { FC, HTMLAttributes } from 'react';

  export interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
    value?: number;
  }

  export const Progress: FC<ProgressProps>;
}
