'use client';


import { motion } from 'framer-motion';
import { LoadingSpinnerProps } from './types';
import { useMicroInteractions } from './micro-interaction-provider';
import { cn } from '@/lib/utils';

const sizeClasses = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12'
};

const colorClasses = {
  primary: 'text-primary',
  secondary: 'text-secondary',
  muted: 'text-muted-foreground'
};

export function LoadingSpinner({ 
  size = 'md',
  variant = 'default',
  color = 'primary',
  className 
}: LoadingSpinnerProps) {
  const { reducedMotion } = useMicroInteractions();

  const spinAnimation = {
    animate: {
      rotate: reducedMotion ? 0 : 360,
    },
    transition: {
      duration: reducedMotion ? 0 : 1,
      repeat: reducedMotion ? 0 : Infinity,
      ease: "linear" as const
    }
  };

  const pulseAnimation = {
    animate: {
      scale: reducedMotion ? 1 : [1, 1.2, 1],
      opacity: reducedMotion ? 1 : [1, 0.7, 1],
    },
    transition: {
      duration: reducedMotion ? 0 : 1.5,
      repeat: reducedMotion ? 0 : Infinity,
      ease: "easeInOut" as const
    }
  };

  const dotsAnimation = {
    animate: {
      y: reducedMotion ? 0 : [-4, 4, -4],
    },
    transition: {
      duration: reducedMotion ? 0 : 0.6,
      repeat: reducedMotion ? 0 : Infinity,
      ease: "easeInOut" as const
    }
  };

  const barsAnimation = {
    animate: {
      scaleY: reducedMotion ? 1 : [1, 2, 1],
    },
    transition: {
      duration: reducedMotion ? 0 : 0.8,
      repeat: reducedMotion ? 0 : Infinity,
      ease: "easeInOut" as const
    }
  };

  if (variant === 'dots') {
    return (
      <div className={cn("flex items-center space-x-1", className)}>
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className={cn(
              "rounded-full bg-current",
              sizeClasses[size],
              colorClasses[color]
            )}
            {...dotsAnimation}
            transition={{
              ...dotsAnimation.transition,
              delay: i * 0.2
            }}
          />
        ))}
      </div>
    );
  }

  if (variant === 'pulse') {
    return (
      <motion.div
        className={cn(
          "rounded-full bg-current",
          sizeClasses[size],
          colorClasses[color],
          className
        )}
        {...pulseAnimation}
      />
    );
  }

  if (variant === 'bars') {
    return (
      <div className={cn("flex items-center space-x-1", className)}>
        {[0, 1, 2, 3].map((i) => (
          <motion.div
            key={i}
            className={cn(
              "bg-current rounded-sm",
              size === 'xs' && "w-0.5 h-3",
              size === 'sm' && "w-0.5 h-4",
              size === 'md' && "w-1 h-6",
              size === 'lg' && "w-1 h-8",
              size === 'xl' && "w-1.5 h-12",
              colorClasses[color]
            )}
            {...barsAnimation}
            transition={{
              ...barsAnimation.transition,
              delay: i * 0.1
            }}
          />
        ))}
      </div>
    );
  }

  // Default spinner
  return (
    <motion.div
      className={cn(
        "border-2 border-current border-t-transparent rounded-full",
        sizeClasses[size],
        colorClasses[color],
        className
      )}
      {...spinAnimation}
    />
  );
}