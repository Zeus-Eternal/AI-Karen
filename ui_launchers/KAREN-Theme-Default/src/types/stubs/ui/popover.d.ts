declare module '@/components/ui/popover' {
  import type { FC, ReactNode } from 'react';

  type PopoverSide = 'top' | 'bottom' | 'left' | 'right';
  type PopoverAlign = 'start' | 'center' | 'end';

  export interface PopoverProps {
    children?: ReactNode;
    open?: boolean;
    defaultOpen?: boolean;
    onOpenChange?: (open: boolean) => void;
  }

  export interface PopoverTriggerProps {
    children?: ReactNode;
    asChild?: boolean;
    className?: string;
  }

  export interface PopoverContentProps {
    children?: ReactNode;
    className?: string;
    align?: PopoverAlign;
    side?: PopoverSide;
    sideOffset?: number;
  }

  export const Popover: FC<PopoverProps>;
  export const PopoverTrigger: FC<PopoverTriggerProps>;
  export const PopoverContent: FC<PopoverContentProps>;
}
