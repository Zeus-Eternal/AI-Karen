declare module '@/components/ui/alert' {  
  import type {
    FC,
    HTMLAttributes,
    ForwardRefExoticComponent,
    RefAttributes,
  } from 'react';

  export type AlertVariant = 'default' | 'destructive';

  export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
    variant?: AlertVariant;
  }

  export const Alert: ForwardRefExoticComponent<AlertProps & RefAttributes<HTMLDivElement>>;
  export const AlertTitle: FC<HTMLAttributes<HTMLParagraphElement>>;
  export const AlertDescription: FC<HTMLAttributes<HTMLDivElement>>;
}
