'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { InteractiveCardProps } from './types';
import { animationVariants, reducedMotionVariants } from './animation-variants';
import { triggerHapticFeedback } from './haptic-feedback';
import { useMicroInteractions } from './micro-interaction-provider';
import { cn } from '@/lib/utils';

export const InteractiveCard = React.forwardRef<HTMLDivElement, InteractiveCardProps>(
  ({ 
    children,
    interactive = false,
    variant = 'default',
    hoverEffect = 'lift',
    clickEffect = 'press',
    onClick,
    className,
    ...props 
  }, ref) => {
    const { reducedMotion, enableHaptics } = useMicroInteractions();
    
    const variants = hoverEffect === 'none' 
      ? undefined 
      : reducedMotion 
        ? reducedMotionVariants.card[hoverEffect as keyof typeof reducedMotionVariants.card]
        : animationVariants.card[hoverEffect as keyof typeof animationVariants.card];

    const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
      if (!interactive) return;
      
      // Trigger haptic feedback
      if (enableHaptics) {
        triggerHapticFeedback('light');
      }
      
      onClick?.(event);
    };

    // Filter out props that conflict with Framer Motion
    const { 
      onDrag, 
      onDragEnd, 
      onDragStart, 
      draggable,
      onAnimationStart,
      onAnimationEnd,
      onAnimationIteration,
      ...filteredProps 
    } = props;

    return (
      <motion.div
        ref={ref}
        className={cn(
          "rounded-lg border bg-card text-card-foreground transition-colors",
          {
            "modern-card": variant === "default",
            "modern-card-elevated": variant === "elevated",
            "modern-card-outlined": variant === "outlined",
            "modern-card-glass": variant === "glass",
            "cursor-pointer": interactive,
            "select-none": interactive,
          },
          className
        )}
        variants={variants}
        initial="idle"
        whileHover={interactive ? "hover" : "idle"}
        whileTap={interactive && clickEffect === 'press' ? "tap" : "idle"}
        onClick={handleClick}
        {...filteredProps}
      >
        {children}
      </motion.div>
    );
  }
);

InteractiveCard.displayName = 'InteractiveCard';