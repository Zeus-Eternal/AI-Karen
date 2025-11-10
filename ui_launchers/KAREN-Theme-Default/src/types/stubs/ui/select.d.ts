declare module '@/components/ui/select' {
  import type { FC, ReactNode } from 'react';

  export interface SelectProps {
    value?: string;
    defaultValue?: string;
    onValueChange?: (value: string) => void;
    disabled?: boolean;
    className?: string;
    id?: string;
    children?: ReactNode;
    open?: boolean;
    onOpenChange?: (open: boolean) => void;
    name?: string;
  }

  export interface SelectTriggerProps extends SelectProps {
    ariaLabel?: string;
    placeholder?: string;
  }

  export interface SelectValueProps {
    placeholder?: string;
    children?: ReactNode;
    className?: string;
  }

  export interface SelectContentProps {
    children?: ReactNode;
    className?: string;
    position?: 'popper' | 'item-aligned';
  }

  export interface SelectItemProps {
    value: string;
    children?: ReactNode;
    className?: string;
    disabled?: boolean;
    textValue?: string;
  }

  export interface SelectLabelProps {
    children?: ReactNode;
    className?: string;
  }

  export const Select: FC<SelectProps>;
  export const SelectTrigger: FC<SelectTriggerProps>;
  export const SelectValue: FC<SelectValueProps>;
  export const SelectContent: FC<SelectContentProps>;
  export const SelectGroup: FC<{ children?: ReactNode }>;
  export const SelectLabel: FC<SelectLabelProps>;
  export const SelectItem: FC<SelectItemProps>;
  export const SelectSeparator: FC<{ children?: ReactNode; className?: string }>;
}
