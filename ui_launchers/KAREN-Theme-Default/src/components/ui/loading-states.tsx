"use client";

/**
 * Enhanced Loading States with Smooth Animations
 * 
 * Features:
 * - Skeleton loaders with shimmer effects
 * - Pulse animations
 * - Smooth transitions
 * - Mobile-optimized sizes
 * - Customizable variants
 */

import * as React from 'react';
import { motion } from 'framer-motion';
import { Loader2, Bot, Sparkles, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  className 
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8'
  };

  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      className={cn(sizeClasses[size], className)}
    >
      <Loader2 className="h-full w-full" />
    </motion.div>
  );
};

export interface SkeletonProps {
  className?: string;
  animate?: boolean;
}

const Skeleton: React.FC<SkeletonProps> = ({ 
  className, 
  animate = true 
}) => {
  return (
    <div
      className={cn(
        "rounded-md bg-gray-200 dark:bg-gray-700",
        animate && "animate-pulse",
        className
      )}
    />
  );
};

const MessageSkeleton: React.FC<{ isUser?: boolean }> = ({ isUser = false }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 mb-6 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar Skeleton */}
      <Skeleton className="flex-shrink-0 w-8 h-8 rounded-full " />
      
      {/* Message Content Skeleton */}
      <div className={`flex-1 max-w-[75%] ${isUser ? 'text-right' : 'text-left'}`}>
        <div className="space-y-2">
          <Skeleton className="h-4 w-3/4 " />
          <Skeleton className="h-4 w-1/2 " />
          <Skeleton className="h-4 w-2/3 " />
        </div>
      </div>
    </motion.div>
  );
};

const ChatLoadingSkeleton: React.FC = () => {
  return (
    <div className="space-y-6 p-4 sm:p-4 md:p-6">
      <MessageSkeleton />
      <MessageSkeleton isUser />
      <MessageSkeleton />
      <div className="flex gap-3">
        <Skeleton className="flex-shrink-0 w-8 h-8 rounded-full " />
        <div className="flex-1">
          <div className="inline-block p-4 rounded-2xl bg-gray-100 dark:bg-gray-800 sm:p-4 md:p-6">
            <div className="flex items-center gap-2">
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
                className="w-2 h-2 bg-gray-400 rounded-full "
              />
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 1.5, delay: 0.2 }}
                className="w-2 h-2 bg-gray-400 rounded-full "
              />
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 1.5, delay: 0.4 }}
                className="w-2 h-2 bg-gray-400 rounded-full "
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export interface PulseLoaderProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'blue' | 'green' | 'purple' | 'gray';
  className?: string;
}

const PulseLoader: React.FC<PulseLoaderProps> = ({ 
  size = 'md', 
  color = 'blue',
  className 
}) => {
  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4'
  };

  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-emerald-500',
    purple: 'bg-purple-500',
    gray: 'bg-gray-500'
  };

  return (
    <div className={cn("flex items-center gap-1", className)}>
      {[0, 0.2, 0.4].map((delay, index) => (
        <motion.div
          key={index}
          animate={{ scale: [1, 1.5, 1], opacity: [0.7, 1, 0.7] }}
          transition={{ 
            repeat: Infinity, 
            duration: 1.5, 
            delay,
            ease: "easeInOut"
          }}
          className={cn(
            "rounded-full",
            sizeClasses[size],
            colorClasses[color]
          )}
        />
      ))}
    </div>
  );
};

export interface ShimmerProps {
  className?: string;
  children?: React.ReactNode;
}

const Shimmer: React.FC<ShimmerProps> = ({ className, children }) => {
  return (
    <div className={cn("relative overflow-hidden", className)}>
      {children}
      <motion.div
        className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent"
        animate={{ translateX: ['0%', '200%'] }}
        transition={{ 
          repeat: Infinity, 
          duration: 2, 
          ease: "linear",
          repeatDelay: 1
        }}
      />
    </div>
  );
};

export interface LoadingCardProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  className?: string;
}

const LoadingCard: React.FC<LoadingCardProps> = ({
  title = "Loading...",
  description = "Please wait while we process your request",
  icon,
  className
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        "flex flex-col items-center justify-center p-8 bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700",
        className
      )}
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        className="mb-4"
      >
        {icon || <Sparkles className="h-8 w-8 text-blue-500 " />}
      </motion.div>
      
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
        {title}
      </h3>
      
      <p className="text-sm text-gray-500 text-center max-w-sm md:text-base lg:text-lg">
        {description}
      </p>
      
      <div className="mt-4">
        <PulseLoader color="blue" />
      </div>
    </motion.div>
  );
};

export interface ProgressBarProps {
  progress: number;
  className?: string;
  showPercentage?: boolean;
  color?: 'blue' | 'green' | 'purple';
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  className,
  showPercentage = true,
  color = 'blue'
}) => {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-emerald-500',
    purple: 'bg-purple-500'
  };

  return (
    <div className={cn("w-full", className)}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300 md:text-base lg:text-lg">
          Processing...
        </span>
        {showPercentage && (
          <span className="text-sm text-gray-500 md:text-base lg:text-lg">
            {Math.round(progress)}%
          </span>
        )}
      </div>
      
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
        <motion.div
          className={cn("h-2 rounded-full", colorClasses[color])}
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
    </div>
  );
};

export interface FloatingDotsProps {
  className?: string;
  color?: 'blue' | 'green' | 'purple' | 'gray';
}

const FloatingDots: React.FC<FloatingDotsProps> = ({ 
  className,
  color = 'blue'
}) => {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-emerald-500',
    purple: 'bg-purple-500',
    gray: 'bg-gray-500'
  };

  return (
    <div className={cn("flex items-center justify-center gap-2", className)}>
      {[0, 0.3, 0.6].map((delay, index) => (
        <motion.div
          key={index}
          animate={{ 
            y: [-4, 4, -4],
            opacity: [0.5, 1, 0.5]
          }}
          transition={{ 
            repeat: Infinity, 
            duration: 1.5, 
            delay,
            ease: "easeInOut"
          }}
          className={cn(
            "w-2 h-2 rounded-full",
            colorClasses[color]
          )}
        />
      ))}
    </div>
  );
};

export interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
  className?: string;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  isVisible,
  message = "Loading...",
  className
}) => {
  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className={cn(
        "fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center",
        className
      )}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-2xl max-w-sm mx-4 sm:p-4 md:p-6"
      >
        <div className="flex flex-col items-center">
          <LoadingSpinner size="lg" className="mb-4 text-blue-500" />
          <p className="text-gray-900 dark:text-gray-100 font-medium">
            {message}
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
};

// Export all components
export {
};