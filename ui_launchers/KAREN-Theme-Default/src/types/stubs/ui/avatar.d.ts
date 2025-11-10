declare module '@/components/ui/avatar' {
  import type { FC, HTMLAttributes } from 'react';

  export const Avatar: FC<HTMLAttributes<HTMLDivElement>>;
  export const AvatarImage: FC<HTMLAttributes<HTMLImageElement>>;
  export const AvatarFallback: FC<HTMLAttributes<HTMLDivElement>>;
}
