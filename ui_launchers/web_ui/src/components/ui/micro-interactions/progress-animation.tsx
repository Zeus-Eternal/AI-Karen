'use client';


import { motion } from 'framer-motion';
import { ProgressAnimationProps } from './types';
import { useMicroInteractions } from './micro-interaction-provider';
import { cn } from '@/lib/utils';

const sizeClasses = {
  sm: 'h-2',
  md: 'h-3',
  lg: 'h-4'
};

const circularSizes = {
  sm: 'w-8 h-8',
  md: 'w-12 h-12',
  lg: 'w-16 h-16'
};

export function ProgressAnimation({ 
  progress,
  variant = 'linear',
  size = 'md',
  showPercentage = false,
  animated = true,
  className 
}: ProgressAnimationProps) {
  const { reducedMotion } = useMicroInteractions();
  
  // Clamp progress between 0 and 100
  const clampedProgress = Math.max(0, Math.min(100, progress));
  
  const animationProps = {
    transition: {
      duration: reducedMotion || !animated ? 0 : 0.5,
      ease: "easeInOut" as const
    }
  };

  if (variant === 'circular') {
    const radius = size === 'sm' ? 14 : size === 'md' ? 20 : 28;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (clampedProgress / 100) * circumference;

    return (
      <div className={cn("relative inline-flex items-center justify-center", className)}>
        <svg 
          className={cn(circularSizes[size], "transform -rotate-90")}
          viewBox="0 0 64 64"
        >
          {/* Background circle */}
          <circle
            cx="32"
            cy="32"
            r={radius}
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth="4"
          />
          {/* Progress circle */}
          <motion.circle
            cx="32"
            cy="32"
            r={radius}
            fill="none"
            stroke="hsl(var(--primary))"
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            {...animationProps}
          />
        </svg>
        {showPercentage && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-medium sm:text-sm md:text-base">
              {Math.round(clampedProgress)}%
            </span>
          </div>
        )}
      </div>
    );
  }

  if (variant === 'dots') {
    const totalDots = 10;
    const activeDots = Math.round((clampedProgress / 100) * totalDots);

    return (
      <div className={cn("flex items-center space-x-1", className)}>
        {Array.from({ length: totalDots }, (_, i) => (
          <motion.div
            key={i}
            className={cn(
              "rounded-full",
              size === 'sm' && "w-2 h-2",
              size === 'md' && "w-3 h-3",
              size === 'lg' && "w-4 h-4"
            )}
            initial={{ backgroundColor: "hsl(var(--muted))" }}
            animate={{
              backgroundColor: i < activeDots 
                ? "hsl(var(--primary))" 
                : "hsl(var(--muted))"
            }}
            transition={{
              ...animationProps.transition,
              delay: animated && !reducedMotion ? i * 0.1 : 0
            }}
          />
        ))}
        {showPercentage && (
          <span className="ml-2 text-sm font-medium md:text-base lg:text-lg">
            {Math.round(clampedProgress)}%
          </span>
        )}
      </div>
    );
  }

  // Linear progress bar (default)
  return (
    <div className={cn("w-full", className)}>
      <div className={cn(
        "bg-muted rounded-full overflow-hidden",
        sizeClasses[size]
      )}>
        <motion.div
          className="h-full bg-primary rounded-full"
          initial={{ width: "0%" }}
          animate={{ width: `${clampedProgress}%` }}
          {...animationProps}
        />
      </div>
      {showPercentage && (
        <div className="mt-1 text-right">
          <span className="text-sm font-medium text-muted-foreground md:text-base lg:text-lg">
            {Math.round(clampedProgress)}%
          </span>
        </div>
      )}
    </div>
  );
}