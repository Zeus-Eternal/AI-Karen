// Performance-aware animation components
export { 
  default as PerformanceAwareMotion,
  FadeMotion,
  SlideUpMotion,
  SlideDownMotion,
  SlideLeftMotion,
  SlideRightMotion,
  ScaleMotion,
  SpringMotion,
  StaggeredMotion,
  StaggeredItem,
  PerformanceAnimatePresence,
  usePerformanceAwareMotionValue
} from './performance-aware-motion';

export { default as AnimationMonitor } from './animation-monitor';

// Re-export animation utilities
export {
  performanceAnimationVariants,
  reducedMotionVariants,
  AnimationPerformanceMonitor,
  animationCSS,
  useAnimationPerformance,
  usePerformanceAwareAnimation,
  useWillChange,
  animationPerformanceMonitor,
  ANIMATION_PERFORMANCE_THRESHOLDS
} from '@/utils/animation-performance';

// Re-export types
export type {
  AnimationMetrics
} from '@/utils/animation-performance';