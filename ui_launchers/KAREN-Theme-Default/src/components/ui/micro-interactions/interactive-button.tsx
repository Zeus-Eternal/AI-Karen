"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "./loading-spinner";
import { InteractiveButtonProps } from "./types";
import { animationVariants, reducedMotionVariants } from "./animation-variants";
import { triggerHapticFeedback } from "./haptic-feedback";
import { useMicroInteractions } from "./micro-interaction-context";
import { cn } from "@/lib/utils";

// Create MotionButton outside of component to avoid recreation during render
const MotionButton = motion(Button);

export const InteractiveButton = React.forwardRef<
  HTMLButtonElement,
  InteractiveButtonProps
>(
  (
    {
      children,
      loading = false,
      hapticFeedback = true,
      animationVariant = "default",
      loadingText,
      onClick,
      disabled,
      className,
      ...props
    },
    ref
  ) => {
    const { reducedMotion, enableHaptics } = useMicroInteractions();

    const variants = reducedMotion
      ? reducedMotionVariants.button[animationVariant]
      : animationVariants.button[animationVariant];

    const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
      if (loading || disabled) return;

      // Trigger haptic feedback
      if (hapticFeedback && enableHaptics) {
        triggerHapticFeedback("light");
      }

      onClick?.(event);
    };

    // Filter out props that conflict with Framer Motion - remove unused variables
    const filteredProps = React.useMemo(() => {
      const {
        onDrag: _onDrag,
        onDragEnd: _onDragEnd,
        onDragStart: _onDragStart,
        draggable: _draggable,
        onAnimationStart: _onAnimationStart,
        onAnimationEnd: _onAnimationEnd,
        onAnimationIteration: _onAnimationIteration,
        ...rest
      } = props;
      return rest;
    }, [props]);

    return (
      <MotionButton
        ref={ref}
        className={cn(
          "relative overflow-hidden",
          loading && "pointer-events-none",
          className
        )}
        variants={variants}
        initial="idle"
        whileHover={!loading && !disabled ? "hover" : "idle"}
        whileTap={!loading && !disabled ? "tap" : "idle"}
        animate={loading ? "loading" : "idle"}
        onClick={handleClick}
        disabled={disabled || loading}
        {...filteredProps}
      >
        <span
          className={cn(
            "flex items-center justify-center gap-2 transition-opacity duration-200",
            loading && "opacity-0"
          )}
        >
          {children}
        </span>

        {loading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <LoadingSpinner size="sm" className="mr-2" />
            {loadingText && (
              <span className="text-sm md:text-base lg:text-lg">
                {loadingText}
              </span>
            )}
          </div>
        )}
      </MotionButton>
    );
  }
);

InteractiveButton.displayName = "InteractiveButton";
