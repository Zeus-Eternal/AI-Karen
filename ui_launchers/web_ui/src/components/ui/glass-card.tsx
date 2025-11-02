'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';

const glassCardVariants = cva(
  'glass-card transition-all duration-200',
  {
    variants: {
      intensity: {
        light: 'glass-card',
        medium: '[background:rgba(255,255,255,0.5)] dark:[background:rgba(0,0,0,0.5)]',
        strong: 'glass-card-strong',
      },
      hover: {
        true: 'hover:shadow-xl hover:scale-[1.02] cursor-pointer',
        false: '',
      },
      padding: {
        none: 'p-0',
        sm: 'p-3',
        md: 'p-4',
        lg: 'p-6',
        xl: 'p-8',
      },
    },
    defaultVariants: {
      intensity: 'light',
      hover: false,
      padding: 'md',
    },
  }
);

export interface GlassCardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof glassCardVariants> {
  children: React.ReactNode;
}

export const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, intensity, hover, padding, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(glassCardVariants({ intensity, hover, padding }), className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

GlassCard.displayName = 'GlassCard';

export default GlassCard;
