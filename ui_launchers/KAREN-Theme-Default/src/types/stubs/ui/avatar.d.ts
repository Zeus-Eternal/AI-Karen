declare module '@/components/ui/avatar' {
  import type { FC, HTMLAttributes, ImgHTMLAttributes } from 'react';

  export const Avatar: FC<HTMLAttributes<HTMLDivElement>>;
  export const AvatarImage: FC<ImgHTMLAttributes<HTMLImageElement>>;
  export const AvatarFallback: FC<HTMLAttributes<HTMLDivElement>>;
}
