import type { ReactNode } from 'react';
import type { HTMLMotionProps } from 'framer-motion';

export type TransitionVariant = 
  | 'fade'
  | 'slide-left'
  | 'slide-right'
  | 'slide-up'
  | 'slide-down'
  | 'scale'
  | 'rotate'
  | 'flip';

export interface TransitionConfig {
  variant: TransitionVariant;
  duration: number;
  ease: string | number[];
  delay?: number;
}

export interface PageTransitionProps {
  children: ReactNode;
  variant?: TransitionVariant;
  duration?: number;
  className?: string;
  onTransitionComplete?: () => void;
}

export interface RouteTransitionProps {
  children: ReactNode;
  routeKey: string;
  variant?: TransitionVariant;
  duration?: number;
  className?: string;
}

export interface TransitionProviderProps {
  children: ReactNode;
  defaultConfig?: Partial<TransitionConfig>;
}

type MotionVariants = NonNullable<HTMLMotionProps<'div'>['variants']>;
type VariantState = NonNullable<MotionVariants[keyof MotionVariants]>;

export type TransitionVariants = Record<
  string,
  {
    initial: VariantState;
    animate: VariantState;
    exit: VariantState;
  }
>;
