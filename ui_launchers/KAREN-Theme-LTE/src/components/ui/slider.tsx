/**
 * Slider Component - Simple slider component
 */
import React from 'react';
import { cn } from '@/lib/utils';

export interface SliderProps {
  className?: string;
  children?: React.ReactNode;
  min?: number;
  max?: number;
  step?: number;
  value?: number | number[];
  onChange?: (value: number | number[]) => void;
  disabled?: boolean;
}

export const Slider: React.FC<SliderProps> = ({
  className,
  children,
  min = 0,
  max = 100,
  step = 1,
  value = 50,
  onChange,
  disabled = false
}) => {
  const inputValue = Array.isArray(value) ? value[0] ?? 50 : value;
  
  return (
    <div className={cn('w-full', className)}>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={inputValue}
        onChange={(e) => onChange?.(Number(e.target.value))}
        disabled={disabled}
        className="w-full"
      />
      {children}
    </div>
  );
};

export default Slider;
