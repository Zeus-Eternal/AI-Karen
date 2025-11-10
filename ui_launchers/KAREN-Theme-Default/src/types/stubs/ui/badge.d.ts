declare module '@/components/ui/badge' {
  import type { FC, HTMLAttributes } from 'react';

  export interface BadgeProps extends HTMLAttributes<HTMLDivElement> {
    variant?: string;
  }

  export const Badge: FC<BadgeProps>;
}
