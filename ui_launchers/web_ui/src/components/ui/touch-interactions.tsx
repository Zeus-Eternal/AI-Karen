'use client';

/**
 * Touch-Friendly Mobile Interactions
 * 
 * Features:
 * - Touch-optimized button sizes (44px minimum)
 * - Haptic feedback simulation
 * - Swipe gestures
 * - Long press interactions
 * - Pull-to-refresh
 * - Smooth touch animations
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion, PanInfo, useMotionValue, useTransform, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface TouchButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  onLongPress?: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  haptic?: boolean;
}

const TouchButton: React.FC<TouchButtonProps> = ({
  children,
  onClick,
  onLongPress,
  disabled = false,
  variant = 'primary',
  size = 'md',
  className,
  haptic = true
}) => {
  const [isPressed, setIsPressed] = useState(false);
  const [isLongPressed, setIsLongPressed] = useState(false);
  const longPressTimer = useRef<NodeJS.Timeout>();

  const variantClasses = {
    primary: 'bg-blue-500 hover:bg-blue-600 text-white shadow-lg',
    secondary: 'bg-gray-100 hover:bg-gray-200 text-gray-900 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-100',
    ghost: 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300',
    destructive: 'bg-red-500 hover:bg-red-600 text-white shadow-lg'
  };

  const sizeClasses = {
    sm: 'min-h-[40px] px-3 py-2 text-sm',
    md: 'min-h-[44px] px-4 py-2.5 text-base',
    lg: 'min-h-[48px] px-6 py-3 text-lg'
  };

  const triggerHaptic = useCallback(() => {
    if (haptic && 'vibrate' in navigator) {
      navigator.vibrate(10); // Short vibration
    }
  }, [haptic]);

  const handleTouchStart = useCallback(() => {
    if (disabled) return;
    
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

  const handleTouchEnd = useCallback(() => {
    setIsPressed(false);
    setIsLongPressed(false);
    
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
    }

    if (!disabled && !isLongPressed && onClick) {
      onClick();
    }
  }, [disabled, isLongPressed, onClick]);

  useEffect(() => {
    return () => {
      if (longPressTimer.current) {
        clearTimeout(longPressTimer.current);
      }
    };
  }, []);

  return (
    <motion.button
      className={cn(
        'relative rounded-xl font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed select-none',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      disabled={disabled}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onMouseDown={handleTouchStart}
      onMouseUp={handleTouchEnd}
      onMouseLeave={() => {
        setIsPressed(false);
        if (longPressTimer.current) {
          clearTimeout(longPressTimer.current);
        }
      }}
      whileTap={{ scale: 0.95 }}
      animate={{
        scale: isPressed ? 0.95 : 1,
        boxShadow: isPressed 
          ? '0 2px 8px rgba(0,0,0,0.1)' 
          : '0 4px 12px rgba(0,0,0,0.15)'
      }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
    >
      {children}
      
      {/* Long press indicator */}
      {isPressed && onLongPress && (
        <motion.div
          className="absolute inset-0 rounded-xl bg-white/20"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ duration: 0.5 }}
        />
      )}
    </motion.button>
  );
};

interface SwipeableCardProps {
  children: React.ReactNode;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  swipeThreshold?: number;
  className?: string;
}

const SwipeableCard: React.FC<SwipeableCardProps> = ({
  children,
  onSwipeLeft,
  onSwipeRight,
  swipeThreshold = 100,
  className
}) => {
  const x = useMotionValue(0);
  const opacity = useTransform(x, [-200, 0, 200], [0.5, 1, 0.5]);
  const rotate = useTransform(x, [-200, 0, 200], [-10, 0, 10]);

  const handleDragEnd = useCallback((event: any, info: PanInfo) => {
    const offset = info.offset.x;
    const velocity = info.velocity.x;

    if (Math.abs(offset) > swipeThreshold || Math.abs(velocity) > 500) {
      if (offset > 0 && onSwipeRight) {
        onSwipeRight();
      } else if (offset < 0 && onSwipeLeft) {
        onSwipeLeft();
      }
    }

    x.set(0);
  }, [x, swipeThreshold, onSwipeLeft, onSwipeRight]);

  return (
    <motion.div
      className={cn('cursor-grab active:cursor-grabbing', className)}
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

interface PullToRefreshProps {
  children: React.ReactNode;
  onRefresh: () => Promise<void>;
  refreshThreshold?: number;
  className?: string;
}

const PullToRefresh: React.FC<PullToRefreshProps> = ({
  children,
  onRefresh,
  refreshThreshold = 80,
  className
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const y = useMotionValue(0);

  const handleDrag = useCallback((event: any, info: PanInfo) => {
    const newY = Math.max(0, info.offset.y);
    y.set(newY);
    setPullDistance(newY);
  }, [y]);

  const handleDragEnd = useCallback(async (event: any, info: PanInfo) => {
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
  }, [y, refreshThreshold, isRefreshing, onRefresh]);

  const refreshProgress = Math.min(pullDistance / refreshThreshold, 1);

  return (
    <div className={cn('relative overflow-hidden', className)}>
      {/* Pull indicator */}
      <AnimatePresence>
        {pullDistance > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            className="absolute top-0 left-0 right-0 z-10 flex items-center justify-center py-4 bg-blue-50 dark:bg-blue-900/20"
          >
            <motion.div
              animate={{ rotate: refreshProgress * 360 }}
              className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full sm:w-auto md:w-full"
            />
            <span className="ml-2 text-sm text-blue-600 dark:text-blue-400 md:text-base lg:text-lg">
              {refreshProgress >= 1 ? 'Release to refresh' : 'Pull to refresh'}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Content */}
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

interface FloatingActionButtonProps {
  onClick: () => void;
  icon: React.ReactNode;
  label?: string;
  position?: 'bottom-right' | 'bottom-left' | 'bottom-center';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const FloatingActionButton: React.FC<FloatingActionButtonProps> = ({
  onClick,
  icon,
  label,
  position = 'bottom-right',
  size = 'md',
  className
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const positionClasses = {
    'bottom-right': 'bottom-6 right-6',
    'bottom-left': 'bottom-6 left-6',
    'bottom-center': 'bottom-6 left-1/2 -translate-x-1/2'
  };

  const sizeClasses = {
    sm: 'w-12 h-12',
    md: 'w-14 h-14',
    lg: 'w-16 h-16'
  };

  return (
    <motion.div
      className={cn('fixed z-50', positionClasses[position], className)}
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
          'bg-blue-500 hover:bg-blue-600 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center',
          sizeClasses[size]
        )}
        layout
      >
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ type: "spring", stiffness: 200 }}
        >
          {icon}
        </motion.div>
        
        <AnimatePresence>
          {label && isExpanded && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              className="ml-2 whitespace-nowrap text-sm font-medium md:text-base lg:text-lg"
            >
              {label}
            </motion.span>
          )}
        </AnimatePresence>
      </motion.button>
    </motion.div>
  );
};

interface TouchSliderProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  className?: string;
  trackColor?: string;
  thumbColor?: string;
}

const TouchSlider: React.FC<TouchSliderProps> = ({
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  className,
  trackColor = 'bg-gray-200',
  thumbColor = 'bg-blue-500'
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const sliderRef = useRef<HTMLDivElement>(null);

  const percentage = ((value - min) / (max - min)) * 100;

  const handlePanStart = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handlePan = useCallback((event: any, info: PanInfo) => {
    if (!sliderRef.current) return;

    const rect = sliderRef.current.getBoundingClientRect();
    const percentage = Math.max(0, Math.min(100, (info.point.x - rect.left) / rect.width * 100));
    const newValue = min + (percentage / 100) * (max - min);
    const steppedValue = Math.round(newValue / step) * step;
    
    onChange(Math.max(min, Math.min(max, steppedValue)));
  }, [min, max, step, onChange]);

  const handlePanEnd = useCallback(() => {
    setIsDragging(false);
  }, []);

  return (
    <div className={cn('relative py-4', className)}>
      <div
        ref={sliderRef}
        className={cn('h-2 rounded-full relative', trackColor)}
      >
        {/* Progress track */}
        <motion.div
          className="h-full bg-blue-500 rounded-full"
          style={{ width: `${percentage}%` }}
          layout
        />
        
        {/* Thumb */}
        <motion.div
          className={cn(
            'absolute top-1/2 w-6 h-6 rounded-full shadow-lg cursor-grab active:cursor-grabbing',
            thumbColor,
            isDragging ? 'scale-125' : 'scale-100'
          )}
          style={{ 
            left: `${percentage}%`,
            transform: 'translate(-50%, -50%)'
          }}
          drag="x"
          dragConstraints={sliderRef}
          dragElastic={0}
          onPanStart={handlePanStart}
          onPan={handlePan}
          onPanEnd={handlePanEnd}
          whileHover={{ scale: 1.1 }}
          whileDrag={{ scale: 1.25 }}
        />
      </div>
      
      {/* Value display */}
      <div className="flex justify-between text-xs text-gray-500 mt-2 sm:text-sm md:text-base">
        <span>{min}</span>
        <span className="font-medium">{value}</span>
        <span>{max}</span>
      </div>
    </div>
  );
};

interface TouchMenuProps {
  trigger: React.ReactNode;
  items: Array<{
    label: string;
    icon?: React.ReactNode;
    onClick: () => void;
    destructive?: boolean;
  }>;
  className?: string;
}

const TouchMenu: React.FC<TouchMenuProps> = ({
  trigger,
  items,
  className
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={cn('relative', className)}>
      <TouchButton
        onClick={() => setIsOpen(!isOpen)}
        variant="ghost"
        size="sm"
      >
        {trigger}
      </TouchButton>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />
            
            {/* Menu */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              className="absolute right-0 top-full mt-2 z-50 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 py-2 min-w-[200px]"
            >
              {items.map((item, index) => (
                <TouchButton
                  key={index}
                  onClick={() => {
                    item.onClick();
                    setIsOpen(false);
                  }}
                  variant="ghost"
                  className={cn(
                    'w-full justify-start px-4 py-3 text-left rounded-none hover:bg-gray-50 dark:hover:bg-gray-700',
                    item.destructive && 'text-red-600 hover:text-red-700'
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
        )}
      </AnimatePresence>
    </div>
  );
};

// Export all components
export {
  TouchButton,
  SwipeableCard,
  PullToRefresh,
  FloatingActionButton,
  TouchSlider,
  TouchMenu
};