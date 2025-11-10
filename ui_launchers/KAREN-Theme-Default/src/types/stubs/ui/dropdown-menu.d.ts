declare module '@/components/ui/dropdown-menu' {
  import type { FC, MouseEvent, ReactNode } from 'react';

  type DropdownSide = 'top' | 'bottom' | 'left' | 'right';
  type DropdownAlign = 'start' | 'center' | 'end';

  export interface DropdownMenuProps {
    children?: ReactNode;
    className?: string;
    open?: boolean;
    defaultOpen?: boolean;
    onOpenChange?: (open: boolean) => void;
  }

  export interface DropdownMenuTriggerProps {
    children?: ReactNode;
    className?: string;
    asChild?: boolean;
    onClick?: (event: MouseEvent<HTMLElement>) => void;
  }

  export interface DropdownMenuContentProps {
    children?: ReactNode;
    className?: string;
    align?: DropdownAlign;
    alignOffset?: number;
    side?: DropdownSide;
    sideOffset?: number;
    onClick?: (event: MouseEvent<HTMLElement>) => void;
  }

  export interface DropdownMenuItemProps {
    children?: ReactNode;
    className?: string;
    inset?: boolean;
    disabled?: boolean;
    onSelect?: (event: Event) => void;
    onClick?: (event: MouseEvent<HTMLElement>) => void;
    textValue?: string;
  }

  export interface DropdownMenuLabelProps {
    children?: ReactNode;
    className?: string;
    inset?: boolean;
  }

  export interface DropdownMenuSeparatorProps {
    className?: string;
  }

  export const DropdownMenu: FC<DropdownMenuProps>;
  export const DropdownMenuTrigger: FC<DropdownMenuTriggerProps>;
  export const DropdownMenuContent: FC<DropdownMenuContentProps>;
  export const DropdownMenuLabel: FC<DropdownMenuLabelProps>;
  export const DropdownMenuSeparator: FC<DropdownMenuSeparatorProps>;
  export const DropdownMenuItem: FC<DropdownMenuItemProps>;
}
