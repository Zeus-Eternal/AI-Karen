'use client';

import React, { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/utils';

export interface AnimatedNumberProps extends React.HTMLAttributes<HTMLSpanElement> {
  value: number;
  duration?: number;
  formatFn?: (value: number) => string;
}

export function AnimatedNumber({
  value,
  duration = 1000,
  formatFn = (v) => v.toLocaleString(),
  className,
  ...props
}: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = useState(value);
  const [isAnimating, setIsAnimating] = useState(false);
  const animationRef = useRef<number>();
  const startValueRef = useRef(value);
  const startTimeRef = useRef<number>();

  useEffect(() => {
    if (value === displayValue) return;

    setIsAnimating(true);
    startValueRef.current = displayValue;
    startTimeRef.current = undefined;

    const animate = (timestamp: number) => {
      if (!startTimeRef.current) {
        startTimeRef.current = timestamp;
      }

      const progress = Math.min((timestamp - startTimeRef.current) / duration, 1);

      // Easing function (ease-out-cubic)
      const easeOut = 1 - Math.pow(1 - progress, 3);

      const currentValue = startValueRef.current + (value - startValueRef.current) * easeOut;
      setDisplayValue(Math.round(currentValue));

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      } else {
        setDisplayValue(value);
        setIsAnimating(false);
      }
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [value, duration]);

  return (
    <span
      className={cn(
        'inline-block tabular-nums transition-transform duration-100',
        isAnimating && 'scale-110',
        className
      )}
      {...props}
    >
      {formatFn(displayValue)}
    </span>
  );
}

export default AnimatedNumber;
