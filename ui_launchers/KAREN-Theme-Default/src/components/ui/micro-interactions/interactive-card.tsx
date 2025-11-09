"use client";

import React from 'react';
import { motion } from 'framer-motion';
import type { InteractiveCardProps } from './types';
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
    
    type CardHoverVariant = Exclude<NonNullable<InteractiveCardProps['hoverEffect']>, 'none'>;
    const hoverVariant: CardHoverVariant | undefined =
      hoverEffect && hoverEffect !== 'none' ? hoverEffect : undefined;

    const variants = hoverVariant
      ? (reducedMotion
          ? reducedMotionVariants.card[hoverVariant]
          : animationVariants.card[hoverVariant])
      : undefined;

    const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
      if (!interactive) return;
      
      // Trigger haptic feedback
      if (enableHaptics) {
        triggerHapticFeedback('light');
      }
      
      onClick?.(event);
    };

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
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

InteractiveCard.displayName = 'InteractiveCard';