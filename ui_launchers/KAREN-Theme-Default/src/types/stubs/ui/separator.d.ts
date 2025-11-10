declare module '@/components/ui/separator' {
  import type { FC, HTMLAttributes } from 'react'

  export interface SeparatorProps extends HTMLAttributes<HTMLDivElement> {
    orientation?: 'horizontal' | 'vertical'
    decorative?: boolean
  }

  export const Separator: FC<SeparatorProps>
}
