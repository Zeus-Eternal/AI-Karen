declare module '@/components/ui/alert' {
  import type * as React from 'react'

  export type AlertVariant = 'default' | 'destructive'

  export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
    variant?: AlertVariant
  }

  export interface AlertTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {}

  export interface AlertDescriptionProps extends React.HTMLAttributes<HTMLDivElement> {}

  export const Alert: React.ForwardRefExoticComponent<
    AlertProps & React.RefAttributes<HTMLDivElement>
  >
  export const AlertTitle: React.ForwardRefExoticComponent<
    AlertTitleProps & React.RefAttributes<HTMLHeadingElement>
  >
  export const AlertDescription: React.ForwardRefExoticComponent<
    AlertDescriptionProps & React.RefAttributes<HTMLDivElement>
  >
}
