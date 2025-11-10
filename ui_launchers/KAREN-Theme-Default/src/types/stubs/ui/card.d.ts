declare module '@/components/ui/card' {
  import type { FC, HTMLAttributes, ReactNode } from 'react';

  export interface CardProps extends HTMLAttributes<HTMLDivElement> {
    children?: ReactNode;
  }

  export const Card: FC<CardProps>;
  export const CardHeader: FC<HTMLAttributes<HTMLDivElement>>;
  export const CardContent: FC<HTMLAttributes<HTMLDivElement>>;
  export const CardFooter: FC<HTMLAttributes<HTMLDivElement>>;
  export const CardTitle: FC<HTMLAttributes<HTMLHeadingElement>>;
  export const CardDescription: FC<HTMLAttributes<HTMLParagraphElement>>;
}
