declare module '@/components/ui/tabs' {
  import type { FC, ReactNode } from 'react';

  export interface TabsProps {
    value?: string;
    defaultValue?: string;
    onValueChange?: (value: string) => void;
    className?: string;
    children?: ReactNode;
  }

  export const Tabs: FC<TabsProps>;

  export interface TabsListProps {
    className?: string;
    title?: string;
    children?: ReactNode;
  }

  export const TabsList: FC<TabsListProps>;
  export const TabsTrigger: FC<TabsListProps & { value: string; disabled?: boolean }>;
  export const TabsContent: FC<TabsListProps & { value: string }>;
}
