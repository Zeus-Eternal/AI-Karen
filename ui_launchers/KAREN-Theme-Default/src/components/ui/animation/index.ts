// Performance-aware animation components
export { 
  default as PerformanceAwareMotion,
  usePerformanceAwareMotionValue
} from './performance-aware-motion';

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
