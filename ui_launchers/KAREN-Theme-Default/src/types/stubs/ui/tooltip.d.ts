declare module '@/components/ui/tooltip' {
  import type { FC, ReactNode } from 'react';

  export interface TooltipProps {
    children?: ReactNode;
    className?: string;
    align?: 'start' | 'center' | 'end';
    side?: 'top' | 'bottom' | 'left' | 'right';
    delayDuration?: number;
  }

  export const TooltipProvider: FC<TooltipProps>;
  export const Tooltip: FC<TooltipProps>;
  export const TooltipTrigger: FC<TooltipProps & { asChild?: boolean }>;
  export const TooltipContent: FC<TooltipProps>;
}
