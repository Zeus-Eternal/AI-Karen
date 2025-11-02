import { Variants } from 'framer-motion';

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
  children: React.ReactNode;
  variant?: TransitionVariant;
  duration?: number;
  className?: string;
  onTransitionComplete?: () => void;
}

export interface RouteTransitionProps {
  children: React.ReactNode;
  routeKey: string;
  variant?: TransitionVariant;
  duration?: number;
  className?: string;
}

export interface TransitionProviderProps {
  children: React.ReactNode;
  defaultConfig?: Partial<TransitionConfig>;
}

export interface TransitionVariants {
  [key: string]: {
    initial: Variants['initial'];
    animate: Variants['animate'];
    exit: Variants['exit'];
  };
}