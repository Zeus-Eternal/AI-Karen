"use client";

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';

import { Input } from '@/components/ui/input';
import type { InteractiveInputProps } from './types';
import { animationVariants, reducedMotionVariants } from './animation-variants';
import { triggerHapticFeedback } from './haptic-feedback';
import { useMicroInteractions } from './micro-interaction-context';
import { cn } from '@/lib/utils';

const MotionInput = motion(Input);

const motionConflictKeys = [
  'onDrag',
  'onDragEnd',
  'onDragStart',
  'draggable',
  'onAnimationStart',
  'onAnimationEnd',
  'onAnimationIteration',
] as const;

type MotionConflictKey = (typeof motionConflictKeys)[number];

const sanitizeMotionProps = <T extends Record<string, unknown>>(props: T) => {
  const clone = { ...props } as Record<string, unknown>;
  for (const key of motionConflictKeys) {
    if (key in clone) {
      delete clone[key];
    }
  }
  return clone as Omit<T, MotionConflictKey>;
};

export const InteractiveInput = React.forwardRef<HTMLInputElement, InteractiveInputProps>(
  ({ 
    error = false,
    success = false,
    animationVariant = 'default',
    hapticFeedback = true,
    onFocus,
    onBlur,
    className,
    ...restProps
  }, ref) => {
    const { reducedMotion, enableHaptics } = useMicroInteractions();
    const [isFocused, setIsFocused] = useState(false);
    const [shouldShake, setShouldShake] = useState(false);

    const variants = useMemo(
      () =>
        reducedMotion
          ? reducedMotionVariants.input[animationVariant]
          : animationVariants.input[animationVariant],
      [animationVariant, reducedMotion]
    );

    // Trigger shake animation when error state changes to true
    useEffect(() => {
      let startTimer: ReturnType<typeof setTimeout> | null = null;
      let resetTimer: ReturnType<typeof setTimeout> | null = null;

      if (error && animationVariant === 'shake') {
        if (hapticFeedback && enableHaptics) {
          triggerHapticFeedback('error');
        }
        startTimer = setTimeout(() => {
          setShouldShake(true);
          resetTimer = setTimeout(() => setShouldShake(false), 500);
        }, 0);
      }

      return () => {
        if (startTimer) clearTimeout(startTimer);
        if (resetTimer) clearTimeout(resetTimer);
      };
    }, [error, animationVariant, hapticFeedback, enableHaptics]);

    // Trigger success haptic feedback
    useEffect(() => {
      if (success && hapticFeedback && enableHaptics) {
        triggerHapticFeedback('success');
      }
    }, [success, hapticFeedback, enableHaptics]);

    const handleFocus = useCallback(
      (event: React.FocusEvent<HTMLInputElement>) => {
        setIsFocused(true);
        if (hapticFeedback && enableHaptics) {
          triggerHapticFeedback('light');
        }
        onFocus?.(event);
      },
      [enableHaptics, hapticFeedback, onFocus]
    );

    const handleBlur = useCallback(
      (event: React.FocusEvent<HTMLInputElement>) => {
        setIsFocused(false);
        onBlur?.(event);
      },
      [onBlur]
    );

    const animationState = useMemo(() => {
      if (shouldShake && animationVariant === 'shake') return 'error';
      if (error) return 'error';
      if (success) return 'success';
      if (isFocused) return 'focus';
      return 'idle';
    }, [animationVariant, error, isFocused, shouldShake, success]);

    const filteredProps = useMemo(() => {
      const nativeProps = restProps as React.ComponentPropsWithoutRef<'input'>;
      return sanitizeMotionProps(nativeProps);
    }, [restProps]);

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
        animate={animationState}
        onFocus={handleFocus}
        onBlur={handleBlur}
        {...filteredProps}
      />
    );
  }
);

InteractiveInput.displayName = 'InteractiveInput';
