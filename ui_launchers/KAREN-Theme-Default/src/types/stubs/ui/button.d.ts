declare module '@/components/ui/button' {
  import type {
    ButtonHTMLAttributes,
    DetailedHTMLProps,
    ForwardRefExoticComponent,
    ReactNode,
    RefAttributes,
  } from 'react'

  export interface ButtonProps
    extends DetailedHTMLProps<ButtonHTMLAttributes<HTMLButtonElement>, HTMLButtonElement> {
    variant?: string
    size?: string
    asChild?: boolean
    icon?: ReactNode
  }

  export const buttonVariants: Record<string, unknown>

  export const Button: ForwardRefExoticComponent<ButtonProps & RefAttributes<HTMLButtonElement>>
}
