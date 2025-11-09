import React from 'react';

import { ButtonProps } from '@/components/ui/button';
import { InputProps } from '@/components/ui/input';
import { Variants } from 'framer-motion';

export interface MicroInteractionConfig {
  reducedMotion: boolean;
  enableHaptics: boolean;
  animationDuration: 'fast' | 'normal' | 'slow';
}

export interface InteractiveButtonProps extends ButtonProps {
  loading?: boolean;
  hapticFeedback?: boolean;
  animationVariant?: 'default' | 'bounce' | 'scale' | 'slide';
  loadingText?: string;
}

export interface InteractiveInputProps extends InputProps {
  error?: boolean;
  success?: boolean;
  animationVariant?: 'default' | 'glow' | 'shake';
  hapticFeedback?: boolean;
}

export interface InteractiveCardProps extends React.HTMLAttributes<HTMLDivElement> {
  interactive?: boolean;
  variant?: 'default' | 'elevated' | 'outlined' | 'glass';
  hoverEffect?: 'lift' | 'glow' | 'scale' | 'none';
  clickEffect?: 'press' | 'ripple' | 'none';
  children: React.ReactNode;
}

export interface LoadingSpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'dots' | 'pulse' | 'bars';
  color?: 'primary' | 'secondary' | 'muted';
  className?: string;
}

export interface ProgressAnimationProps {
  progress: number;
  variant?: 'linear' | 'circular' | 'dots';
  size?: 'sm' | 'md' | 'lg';
  showPercentage?: boolean;
  animated?: boolean;
  className?: string;
}

export interface AnimationVariants {
  button: {
    default: Variants;
    bounce: Variants;
    scale: Variants;
    slide: Variants;
  };
  input: {
    default: Variants;
    glow: Variants;
    shake: Variants;
  };
  card: {
    lift: Variants;
    glow: Variants;
    scale: Variants;
  };
}