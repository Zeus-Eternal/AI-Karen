// Performance-aware animation components
export { default as PerformanceAwareMotion } from './performance-aware-motion';
export { usePerformanceAwareMotionValue } from './performance-aware-motion-helpers';

export { 
  default as AnimationMonitor 
} from './animation-monitor';

// Re-export animation utilities
export {
  performanceAnimationVariants,
  reducedMotionVariants,
  animationCSS,
  useAnimationPerformance,
  usePerformanceAwareAnimation,
  useWillChange,
  animationPerformanceMonitor
} from '@/utils/animation-performance';

// Re-export types
export type {
  AnimationMetrics,
  PerformanceMetrics,
  AnimationPerformanceOptions
} from '@/utils/animation-performance';
