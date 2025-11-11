import type { ReactNode } from 'react';

import type { ButtonProps } from '@/components/ui/button';
import type { InputProps } from '@/components/ui/input-types';
import type { HTMLMotionProps, Variants } from 'framer-motion';

export type AnimationSpeed = 'fast' | 'normal' | 'slow';

export type MicroInteractionType =
  | 'button'
  | 'input'
  | 'card'
  | 'loading-spinner'
  | 'progress';

export type ButtonAnimationVariant = 'default' | 'bounce' | 'scale' | 'slide';
export type InputAnimationVariant = 'default' | 'glow' | 'shake';
export type CardHoverAnimation = 'lift' | 'glow' | 'scale';
export type CardHoverEffect = CardHoverAnimation | 'none';
export type CardClickEffect = 'press' | 'ripple' | 'none';

export interface MicroInteractionConfig {
  reducedMotion: boolean;
  enableHaptics: boolean;
  animationDuration: AnimationSpeed;
}

export interface InteractiveButtonProps extends ButtonProps {
  loading?: boolean;
  hapticFeedback?: boolean;
  animationVariant?: ButtonAnimationVariant;
  loadingText?: string;
}

export interface InteractiveInputProps extends InputProps {
  error?: boolean;
  success?: boolean;
  animationVariant?: InputAnimationVariant;
  hapticFeedback?: boolean;
}

export interface InteractiveCardProps
  extends Omit<HTMLMotionProps<'div'>, 'children'> {
  interactive?: boolean;
  variant?: 'default' | 'elevated' | 'outlined' | 'glass';
  hoverEffect?: CardHoverEffect;
  clickEffect?: CardClickEffect;
  children: ReactNode;
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
  button: Record<ButtonAnimationVariant, Variants>;
  input: Record<InputAnimationVariant, Variants>;
  card: Record<CardHoverAnimation, Variants>;
}
