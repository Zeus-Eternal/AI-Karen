declare module '@/components/ui/dropdown-menu' {
  import type {
    FC,
    HTMLAttributes,
    MouseEvent,
    ReactNode,
  } from 'react'

  type DropdownSide = 'top' | 'bottom' | 'left' | 'right'
  type DropdownAlign = 'start' | 'center' | 'end'

  export interface DropdownMenuProps {
    children?: ReactNode
    className?: string
    open?: boolean
    defaultOpen?: boolean
    onOpenChange?: (open: boolean) => void
  }

  export interface DropdownMenuTriggerProps {
    children?: ReactNode
    className?: string
    asChild?: boolean
    onClick?: (event: MouseEvent<HTMLElement>) => void
  }

  export interface DropdownMenuContentProps {
    children?: ReactNode
    className?: string
    align?: DropdownAlign
    alignOffset?: number
    side?: DropdownSide
    sideOffset?: number
    onClick?: (event: MouseEvent<HTMLElement>) => void
  }

  export interface DropdownMenuItemProps {
    children?: ReactNode
    className?: string
    inset?: boolean
    disabled?: boolean
    onSelect?: (event: Event) => void
    onClick?: (event: MouseEvent<HTMLElement>) => void
    textValue?: string
  }

  export interface DropdownMenuCheckboxItemProps
    extends DropdownMenuItemProps {
    checked?: boolean | 'indeterminate'
    onCheckedChange?: (checked: boolean) => void
  }

  export interface DropdownMenuRadioItemProps
    extends DropdownMenuItemProps {
    value: string
  }

  export interface DropdownMenuLabelProps {
    children?: ReactNode
    className?: string
    inset?: boolean
  }

  export interface DropdownMenuSeparatorProps {
    className?: string
  }

  export const DropdownMenu: FC<DropdownMenuProps>
  export const DropdownMenuTrigger: FC<DropdownMenuTriggerProps>
  export const DropdownMenuContent: FC<DropdownMenuContentProps>
  export const DropdownMenuLabel: FC<DropdownMenuLabelProps>
  export const DropdownMenuSeparator: FC<DropdownMenuSeparatorProps>
  export const DropdownMenuItem: FC<DropdownMenuItemProps>
  export const DropdownMenuCheckboxItem: FC<DropdownMenuCheckboxItemProps>
  export const DropdownMenuRadioItem: FC<DropdownMenuRadioItemProps>
  export const DropdownMenuGroup: FC<DropdownMenuProps>
  export const DropdownMenuPortal: FC<DropdownMenuProps>
  export const DropdownMenuSub: FC<DropdownMenuProps>
  export const DropdownMenuSubTrigger: FC<DropdownMenuItemProps>
  export const DropdownMenuSubContent: FC<DropdownMenuContentProps>
  export const DropdownMenuRadioGroup: FC<{ value?: string; onValueChange?: (value: string) => void; children?: ReactNode }>
  export const DropdownMenuShortcut: FC<HTMLAttributes<HTMLSpanElement>>
}
