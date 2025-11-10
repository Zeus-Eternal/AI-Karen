declare module '@/components/ui/slider' {
  import type { FC } from 'react';

  export interface SliderProps {
    value?: number[];
    min?: number;
    max?: number;
    step?: number;
    onValueChange?: (value: number[]) => void;
    className?: string;
    id?: string;
    disabled?: boolean;
  }

  export const Slider: FC<SliderProps>;
}
