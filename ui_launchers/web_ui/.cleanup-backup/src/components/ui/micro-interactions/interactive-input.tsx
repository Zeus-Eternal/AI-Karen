'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Input } from '@/components/ui/input';
import { InteractiveInputProps } from './types';
import { animationVariants, reducedMotionVariants } from './animation-variants';
import { triggerHapticFeedback } from './haptic-feedback';
import { useMicroInteractions } from './micro-interaction-provider';
import { cn } from '@/lib/utils';

export const InteractiveInput = React.forwardRef<HTMLInputElement, InteractiveInputProps>(
  ({ 
    error = false,
    success = false,
    animationVariant = 'default',
    hapticFeedback = true,
    onFocus,
    onBlur,
    className,
    ...props 
  }, ref) => {
    const { reducedMotion, enableHaptics } = useMicroInteractions();
    const [isFocused, setIsFocused] = useState(false);
    const [shouldShake, setShouldShake] = useState(false);
    
    const variants = reducedMotion 
      ? reducedMotionVariants.input[animationVariant]
      : animationVariants.input[animationVariant];

    // Trigger shake animation when error state changes to true
    useEffect(() => {
      if (error && animationVariant === 'shake') {
        setShouldShake(true);
        if (hapticFeedback && enableHaptics) {
          triggerHapticFeedback('error');
        }
        // Reset shake state after animation
        const timer = setTimeout(() => setShouldShake(false), 500);
        return () => clearTimeout(timer);
      }
    }, [error, animationVariant, hapticFeedback, enableHaptics]);

    // Trigger success haptic feedback
    useEffect(() => {
      if (success && hapticFeedback && enableHaptics) {
        triggerHapticFeedback('success');
      }
    }, [success, hapticFeedback, enableHaptics]);

    const handleFocus = (event: React.FocusEvent<HTMLInputElement>) => {
      setIsFocused(true);
      if (hapticFeedback && enableHaptics) {
        triggerHapticFeedback('light');
      }
      onFocus?.(event);
    };

    const handleBlur = (event: React.FocusEvent<HTMLInputElement>) => {
      setIsFocused(false);
      onBlur?.(event);
    };

    const getAnimationState = () => {
      if (shouldShake && animationVariant === 'shake') return 'error';
      if (error) return 'error';
      if (success) return 'success';
      if (isFocused) return 'focus';
      return 'idle';
    };

    const MotionInput = motion(Input);

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
      <MotionInput
        ref={ref}
        className={cn(
          "transition-colors duration-200",
          error && "border-destructive focus-visible:ring-destructive",
          success && "border-green-500 focus-visible:ring-green-500",
          className
        )}
        variants={variants}
        animate={getAnimationState()}
        onFocus={handleFocus}
        onBlur={handleBlur}
        {...filteredProps}
      />
    );
  }
);

InteractiveInput.displayName = 'InteractiveInput';