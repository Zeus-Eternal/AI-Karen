declare module '@/components/ui/collapsible' {
  import type { FC, ReactNode } from 'react';

  export interface CollapsibleProps {
    open?: boolean;
    defaultOpen?: boolean;
    onOpenChange?: (open: boolean) => void;
    children?: ReactNode;
    className?: string;
  }

  export interface CollapsibleTriggerProps {
    children?: ReactNode;
    className?: string;
    asChild?: boolean;
  }

  export interface CollapsibleContentProps {
    children?: ReactNode;
    className?: string;
  }

  export const Collapsible: FC<CollapsibleProps>;
  export const CollapsibleTrigger: FC<CollapsibleTriggerProps>;
  export const CollapsibleContent: FC<CollapsibleContentProps>;
}
