declare module '@/components/ui/resizable' {
  import type { FC, ReactNode } from 'react';

  export interface ResizablePanelGroupProps {
    direction?: 'horizontal' | 'vertical';
    children?: ReactNode;
    className?: string;
  }

  export interface ResizablePanelProps {
    defaultSize?: number;
    minSize?: number;
    maxSize?: number;
    children?: ReactNode;
    className?: string;
  }

  export interface ResizableHandleProps {
    withHandle?: boolean;
    className?: string;
  }

  export const ResizablePanelGroup: FC<ResizablePanelGroupProps>;
  export const ResizablePanel: FC<ResizablePanelProps>;
  export const ResizableHandle: FC<ResizableHandleProps>;
}
