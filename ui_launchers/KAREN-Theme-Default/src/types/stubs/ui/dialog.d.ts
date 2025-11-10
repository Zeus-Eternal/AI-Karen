declare module '@/components/ui/dialog' {
  import type { FC, ReactNode } from 'react';

  export interface DialogProps {
    open?: boolean;
    defaultOpen?: boolean;
    onOpenChange?: (open: boolean) => void;
    children?: ReactNode;
  }

  export interface DialogTriggerProps {
    children?: ReactNode;
    asChild?: boolean;
    className?: string;
  }

  export interface DialogContentProps {
    children?: ReactNode;
    className?: string;
    onOpenAutoFocus?: (event: unknown) => void;
  }

  export interface DialogSectionProps {
    children?: ReactNode;
    className?: string;
  }

  export const Dialog: FC<DialogProps>;
  export const DialogTrigger: FC<DialogTriggerProps>;
  export const DialogContent: FC<DialogContentProps>;
  export const DialogHeader: FC<DialogSectionProps>;
  export const DialogTitle: FC<DialogSectionProps>;
  export const DialogDescription: FC<DialogSectionProps>;
  export const DialogFooter: FC<DialogSectionProps>;
  export const DialogClose: FC<DialogTriggerProps>;
}
