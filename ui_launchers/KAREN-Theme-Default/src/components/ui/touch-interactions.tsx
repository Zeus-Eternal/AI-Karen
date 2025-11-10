"use client";

import * as React from "react";
import {
  AnimatePresence,
  motion,
  type PanInfo,
  useMotionValue,
  useTransform,
} from "framer-motion";

import { cn } from "@/lib/utils";
import type {
  FloatingActionButtonProps,
  PullToRefreshProps,
  SwipeableCardProps,
  TouchButtonProps,
  TouchMenuProps,
  TouchSliderProps,
} from "./types";

const BUTTON_VARIANTS: Record<NonNullable<TouchButtonProps["variant"]>, string> = {
  primary: "bg-blue-500 hover:bg-blue-600 text-white shadow-lg",
  secondary:
    "bg-gray-100 hover:bg-gray-200 text-gray-900 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-100",
  ghost:
    "hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300",
  destructive: "bg-red-500 hover:bg-red-600 text-white shadow-lg",
};

const BUTTON_SIZES: Record<NonNullable<TouchButtonProps["size"]>, string> = {
  sm: "min-h-[40px] px-3 py-2 text-sm",
  md: "min-h-[44px] px-4 py-2.5 text-base",
  lg: "min-h-[48px] px-6 py-3 text-lg",
};

const FAB_POSITIONS: Record<NonNullable<FloatingActionButtonProps["position"]>, string> = {
  "bottom-right": "bottom-6 right-6",
  "bottom-left": "bottom-6 left-6",
  "bottom-center": "bottom-6 left-1/2 -translate-x-1/2",
};

const FAB_SIZES: Record<NonNullable<FloatingActionButtonProps["size"]>, string> = {
  sm: "w-12 h-12",
  md: "w-14 h-14",
  lg: "w-16 h-16",
};

const SLIDER_TRACK_COLOR = "bg-gray-200";
const SLIDER_THUMB_COLOR = "bg-blue-500";

export const TouchButton: React.FC<TouchButtonProps> = ({
  children,
  onClick,
  onLongPress,
  disabled = false,
  variant = "primary",
  size = "md",
  className,
  haptic = true,
}) => {
  const [isPressed, setIsPressed] = React.useState(false);
  const [isLongPressed, setIsLongPressed] = React.useState(false);
  const longPressTimer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const triggerHaptic = React.useCallback(() => {
    if (!haptic) {
      return;
    }

    if (typeof navigator !== "undefined" && "vibrate" in navigator) {
      navigator.vibrate(10);
    }
  }, [haptic]);

  const handleTouchStart = React.useCallback(() => {
    if (disabled) {
      return;
    }

    setIsPressed(true);
    triggerHaptic();

    if (onLongPress) {
      longPressTimer.current = setTimeout(() => {
        setIsLongPressed(true);
        onLongPress();
        triggerHaptic();
      }, 500);
    }
  }, [disabled, onLongPress, triggerHaptic]);

  const clearTimer = React.useCallback(() => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  }, []);

  const handleTouchEnd = React.useCallback(() => {
    setIsPressed(false);
    setIsLongPressed(false);
    clearTimer();

    if (!disabled && !isLongPressed) {
      onClick?.();
    }
  }, [clearTimer, disabled, isLongPressed, onClick]);

  React.useEffect(() => clearTimer, [clearTimer]);

  return (
    <motion.button
      className={cn(
        "relative select-none rounded-xl font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        BUTTON_VARIANTS[variant],
        BUTTON_SIZES[size],
        className,
      )}
      disabled={disabled}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onMouseDown={handleTouchStart}
      onMouseUp={handleTouchEnd}
      onMouseLeave={() => {
        setIsPressed(false);
        clearTimer();
      }}
      whileTap={{ scale: 0.95 }}
      animate={{
        scale: isPressed ? 0.95 : 1,
        boxShadow: isPressed ? "0 2px 8px rgba(0,0,0,0.1)" : "0 4px 12px rgba(0,0,0,0.15)",
      }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      type="button"
    >
      {children}

      {isPressed && onLongPress ? (
        <motion.div
          className="absolute inset-0 rounded-xl bg-white/20"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.5 }}
        />
      ) : null}
    </motion.button>
  );
};

export const SwipeableCard: React.FC<SwipeableCardProps> = ({
  children,
  onSwipeLeft,
  onSwipeRight,
  swipeThreshold = 100,
  className,
}) => {
  const x = useMotionValue(0);
  const opacity = useTransform(x, [-200, 0, 200], [0.5, 1, 0.5]);
  const rotate = useTransform(x, [-200, 0, 200], [-10, 0, 10]);

  const handleDragEnd = React.useCallback(
    (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
      const offset = info.offset.x;
      const velocity = info.velocity.x;

      if (Math.abs(offset) > swipeThreshold || Math.abs(velocity) > 500) {
        if (offset > 0) {
          onSwipeRight?.();
        } else if (offset < 0) {
          onSwipeLeft?.();
        }
      }

      x.set(0);
    },
    [onSwipeLeft, onSwipeRight, swipeThreshold, x],
  );

  return (
    <motion.div
      className={cn("cursor-grab active:cursor-grabbing", className)}
      style={{ x, opacity, rotate }}
      drag="x"
      dragConstraints={{ left: -200, right: 200 }}
      dragElastic={0.2}
      onDragEnd={handleDragEnd}
      whileDrag={{ scale: 1.02 }}
    >
      {children}
    </motion.div>
  );
};

export const PullToRefresh: React.FC<PullToRefreshProps> = ({
  children,
  onRefresh,
  refreshThreshold = 80,
  className,
}) => {
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [pullDistance, setPullDistance] = React.useState(0);
  const y = useMotionValue(0);

  const handleDrag = React.useCallback(
    (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
      const newY = Math.max(0, info.offset.y);
      y.set(newY);
      setPullDistance(newY);
    },
    [y],
  );

  const handleDragEnd = React.useCallback(
    async (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
      if (info.offset.y > refreshThreshold && !isRefreshing) {
        setIsRefreshing(true);
        try {
          await onRefresh();
        } finally {
          setIsRefreshing(false);
        }
      }

      y.set(0);
      setPullDistance(0);
    },
    [isRefreshing, onRefresh, refreshThreshold, y],
  );

  const refreshProgress = Math.min(pullDistance / refreshThreshold, 1);

  return (
    <div className={cn("relative overflow-hidden", className)}>
      <AnimatePresence>
        {pullDistance > 0 ? (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            className="absolute top-0 left-0 right-0 z-10 flex items-center justify-center bg-blue-50 py-4 dark:bg-blue-900/20"
          >
            <motion.div
              animate={{ rotate: refreshProgress * 360 }}
              className="h-6 w-6 rounded-full border-2 border-blue-500 border-t-transparent"
            />
            <span className="ml-2 text-sm text-blue-600 dark:text-blue-400 md:text-base lg:text-lg">
              {refreshProgress >= 1 ? "Release to refresh" : "Pull to refresh"}
            </span>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <motion.div
        style={{ y }}
        drag="y"
        dragConstraints={{ top: 0, bottom: 0 }}
        dragElastic={0.2}
        onDrag={handleDrag}
        onDragEnd={handleDragEnd}
        className="min-h-full"
      >
        {children}
      </motion.div>
    </div>
  );
};

export const FloatingActionButton: React.FC<FloatingActionButtonProps> = ({
  onClick,
  icon,
  label,
  position = "bottom-right",
  size = "md",
  className,
}) => {
  const [isExpanded, setIsExpanded] = React.useState(false);

  return (
    <motion.div
      className={cn("fixed z-50", FAB_POSITIONS[position], className)}
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      <motion.button
        onClick={onClick}
        onHoverStart={() => setIsExpanded(true)}
        onHoverEnd={() => setIsExpanded(false)}
        className={cn(
          "flex items-center justify-center rounded-full bg-blue-500 text-white shadow-lg transition-all duration-200 hover:bg-blue-600 hover:shadow-xl",
          FAB_SIZES[size],
        )}
        layout
        type="button"
      >
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ type: "spring", stiffness: 200 }}
        >
          {icon}
        </motion.div>

        <AnimatePresence>
          {label && isExpanded ? (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              className="ml-2 whitespace-nowrap text-sm font-medium md:text-base lg:text-lg"
            >
              {label}
            </motion.span>
          ) : null}
        </AnimatePresence>
      </motion.button>
    </motion.div>
  );
};

export const TouchSlider: React.FC<TouchSliderProps> = ({
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  className,
  trackColor = SLIDER_TRACK_COLOR,
  thumbColor = SLIDER_THUMB_COLOR,
}) => {
  const [isDragging, setIsDragging] = React.useState(false);
  const sliderRef = React.useRef<HTMLDivElement | null>(null);

  const percentage = React.useMemo(() => ((value - min) / (max - min)) * 100, [max, min, value]);

  const updateValueFromPoint = React.useCallback(
    (pointX: number) => {
      if (!sliderRef.current) {
        return;
      }

      const rect = sliderRef.current.getBoundingClientRect();
      const nextPercentage = Math.max(0, Math.min(100, ((pointX - rect.left) / rect.width) * 100));
      const rawValue = min + (nextPercentage / 100) * (max - min);
      const steppedValue = Math.round(rawValue / step) * step;

      onChange(Math.max(min, Math.min(max, steppedValue)));
    },
    [max, min, onChange, step],
  );

  return (
    <div className={cn("relative py-4", className)}>
      <div ref={sliderRef} className={cn("relative h-2 rounded-full", trackColor)}>
        <motion.div
          className="h-full rounded-full bg-blue-500"
          style={{ width: `${percentage}%` }}
          layout
        />

        <motion.div
          className={cn(
            "absolute top-1/2 h-6 w-6 cursor-grab rounded-full shadow-lg active:cursor-grabbing",
            thumbColor,
            isDragging ? "scale-125" : "scale-100",
          )}
          style={{ left: `${percentage}%`, transform: "translate(-50%, -50%)" }}
          drag="x"
          dragConstraints={sliderRef}
          dragElastic={0}
          onPanStart={() => setIsDragging(true)}
          onPan={(_, info) => {
            setIsDragging(true);
            updateValueFromPoint(info.point.x);
          }}
          onPanEnd={() => setIsDragging(false)}
          whileHover={{ scale: 1.1 }}
          whileDrag={{ scale: 1.25 }}
        />
      </div>

      <div className="mt-2 flex justify-between text-xs text-gray-500 sm:text-sm md:text-base">
        <span>{min}</span>
        <span className="font-medium">{value}</span>
        <span>{max}</span>
      </div>
    </div>
  );
};

export const TouchMenu: React.FC<TouchMenuProps> = ({ trigger, items, className }) => {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div className={cn("relative", className)}>
      <TouchButton onClick={() => setIsOpen((open) => !open)} variant="ghost" size="sm">
        {trigger}
      </TouchButton>

      <AnimatePresence>
        {isOpen ? (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              className="absolute right-0 top-full z-50 mt-2 min-w-[200px] rounded-xl border border-gray-200 bg-white py-2 shadow-lg dark:border-gray-700 dark:bg-gray-800"
            >
              {items.map((item) => (
                <TouchButton
                  key={item.label}
                  onClick={() => {
                    item.onClick();
                    setIsOpen(false);
                  }}
                  variant="ghost"
                  className={cn(
                    "w-full justify-start rounded-none px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700",
                    item.destructive ? "text-red-600 hover:text-red-700" : undefined,
                  )}
                >
                  <div className="flex items-center gap-3">
                    {item.icon}
                    <span>{item.label}</span>
                  </div>
                </TouchButton>
              ))}
            </motion.div>
          </>
        ) : null}
      </AnimatePresence>
    </div>
  );
};

export const touchInteractions = {
  TouchButton,
  SwipeableCard,
  PullToRefresh,
  FloatingActionButton,
  TouchSlider,
  TouchMenu,
};

export default touchInteractions;
