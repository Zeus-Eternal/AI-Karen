"use client";

import React, { useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';

import type { CardHoverAnimation, CardHoverEffect, InteractiveCardProps } from './types';
import { animationVariants, reducedMotionVariants } from './animation-variants';
import { triggerHapticFeedback } from './haptic-feedback';
import { useMicroInteractions } from './micro-interaction-provider';
import { cn } from '@/lib/utils';

const isCardHoverAnimation = (
  effect: CardHoverEffect | undefined
): effect is CardHoverAnimation => effect !== undefined && effect !== 'none';

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

    const hoverVariant = useMemo(() => {
      if (!hoverEffect) return undefined;
      return isCardHoverAnimation(hoverEffect) ? hoverEffect : undefined;
    }, [hoverEffect]);

    const variants = useMemo(() => {
      if (!hoverVariant) return undefined;
      return (reducedMotion
        ? reducedMotionVariants.card[hoverVariant]
        : animationVariants.card[hoverVariant]);
    }, [hoverVariant, reducedMotion]);

    const handleClick = useCallback(
      (event: React.MouseEvent<HTMLDivElement>) => {
        if (!interactive) return;

        if (enableHaptics) {
          triggerHapticFeedback('light');
        }

        onClick?.(event);
      },
      [enableHaptics, interactive, onClick]
    );

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
