/**
 * Animation performance optimization utilities
 */

import * as React from 'react';
import type { Variants } from 'framer-motion';

// Performance-aware animation variants for Framer Motion
export const performanceAnimationVariants = {
  // Optimized fade animations using opacity only
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: {
      duration: 0.2,
      ease: [0.4, 0, 0.2, 1], // Custom easing for smooth performance
    },
  },

  // Optimized slide animations using transform only
  slideUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1],
    },
  },

  slideDown: {
    initial: { opacity: 0, y: -20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 20 },
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1],
    },
  },

  slideLeft: {
    initial: { opacity: 0, x: 20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 },
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1],
    },
  },

  slideRight: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 20 },
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1],
    },
  },

  // Optimized scale animations
  scale: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 },
    transition: {
      duration: 0.2,
      ease: [0.4, 0, 0.2, 1],
    },
  },

  // Spring animations with performance considerations
  spring: {
    initial: { opacity: 0, scale: 0.8 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.8 },
    transition: {
      type: 'spring',
      stiffness: 300,
      damping: 30,
      mass: 0.8,
    },
  },

  // Staggered animations for lists
  stagger: {
    animate: {
      transition: {
        staggerChildren: 0.05,
        delayChildren: 0.1,
      },
    },
  },

  staggerItem: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1],
    },
  },
} as const;

// Reduced motion variants for accessibility
export const reducedMotionVariants = {
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.1 },
  },

  slideUp: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.1 },
  },

  slideDown: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.1 },
  },

  slideLeft: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.1 },
  },

  slideRight: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.1 },
  },

  scale: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.1 },
  },

  spring: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.1 },
  },

  stagger: {
    animate: {
      transition: {
        staggerChildren: 0.01,
      },
    },
  },

  staggerItem: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.1 },
  },
} as const;

// Animation performance monitor
export class AnimationPerformanceMonitor {
  private frameCount = 0;
  private lastFrameTime = 0;
  private frameTimes: number[] = [];
  private isMonitoring = false;
  private animationFrame?: number;
  private onPerformanceUpdate?: (metrics: AnimationMetrics) => void;

  constructor(onPerformanceUpdate?: (metrics: AnimationMetrics) => void) {
    this.onPerformanceUpdate = onPerformanceUpdate;
  }

  startMonitoring(): void {
    if (this.isMonitoring || typeof window === 'undefined') return;

    this.isMonitoring = true;
    this.frameCount = 0;
    this.frameTimes = [];
    this.lastFrameTime = performance.now();
    
    this.measureFrame();
  }

  stopMonitoring(): void {
    if (!this.isMonitoring) return;

    this.isMonitoring = false;
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
  }

  getMetrics(): AnimationMetrics {
    if (this.frameTimes.length === 0) {
      return {
        fps: 0,
        averageFrameTime: 0,
        maxFrameTime: 0,
        minFrameTime: 0,
        droppedFrames: 0,
        frameCount: this.frameCount,
        isSmooth: false,
      };
    }

    const averageFrameTime = this.frameTimes.reduce((sum, time) => sum + time, 0) / this.frameTimes.length;
    const maxFrameTime = Math.max(...this.frameTimes);
    const minFrameTime = Math.min(...this.frameTimes);
    const fps = 1000 / averageFrameTime;
    const droppedFrames = this.frameTimes.filter(time => time > 16.67).length; // 60fps = 16.67ms per frame
    const isSmooth = fps >= 55 && droppedFrames / this.frameTimes.length < 0.1; // Less than 10% dropped frames

    return {
      fps,
      averageFrameTime,
      maxFrameTime,
      minFrameTime,
      droppedFrames,
      frameCount: this.frameCount,
      isSmooth,
    };
  }

  private measureFrame = (): void => {
    if (!this.isMonitoring) return;

    const currentTime = performance.now();
    const frameTime = currentTime - this.lastFrameTime;

    if (this.frameCount > 0) { // Skip first frame
      this.frameTimes.push(frameTime);
      
      // Keep only last 60 frames for rolling average
      if (this.frameTimes.length > 60) {
        this.frameTimes.shift();
      }

      // Report metrics every 30 frames
      if (this.frameCount % 30 === 0 && this.onPerformanceUpdate) {
        this.onPerformanceUpdate(this.getMetrics());
      }
    }

    this.lastFrameTime = currentTime;
    this.frameCount++;

    this.animationFrame = requestAnimationFrame(this.measureFrame);
  };
}

// CSS optimization utilities
export const animationCSS = {
  // Enable GPU acceleration
  gpuAcceleration: {
    transform: 'translateZ(0)',
    willChange: 'transform, opacity',
  },

  // Optimize for animations
  optimizeForAnimation: {
    willChange: 'transform, opacity',
    backfaceVisibility: 'hidden' as const,
    perspective: 1000,
  },

  // Remove will-change after animation
  removeWillChange: {
    willChange: 'auto',
  },

  // Contain layout and paint
  containment: {
    contain: 'layout style paint',
  },

  // Force layer creation
  forceLayer: {
    transform: 'translateZ(0)',
    isolation: 'isolate' as const,
  },
} as const;

// Performance-aware animation hooks
export function useAnimationPerformance() {
  const [metrics, setMetrics] = React.useState<AnimationMetrics | null>(null);
  const [isMonitoring, setIsMonitoring] = React.useState(false);
  const [history, setHistory] = React.useState<AnimationMetrics[]>([]);
  const monitorRef = React.useRef<AnimationPerformanceMonitor | null>(null);

  const handleMetricsUpdate = React.useCallback((nextMetrics: AnimationMetrics) => {
    setMetrics(nextMetrics);
    setHistory((prev) => [...prev.slice(-19), nextMetrics]);
  }, []);

  React.useEffect(() => {
    monitorRef.current = new AnimationPerformanceMonitor(handleMetricsUpdate);

    return () => {
      monitorRef.current?.stopMonitoring();
    };
  }, [handleMetricsUpdate]);

  const startMonitoring = React.useCallback(() => {
    monitorRef.current?.startMonitoring();
    setIsMonitoring(true);
  }, []);

  const stopMonitoring = React.useCallback(() => {
    monitorRef.current?.stopMonitoring();
    setIsMonitoring(false);
  }, []);

  const getCurrentMetrics = React.useCallback(() => {
    return monitorRef.current?.getMetrics() || null;
  }, []);

  return {
    metrics,
    history,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    getCurrentMetrics,
  };
}

// Hook for performance-aware animations
export interface AnimationPerformanceOptions {
  reducedMotion?: boolean;
  enableHardwareDetection?: boolean;
}

export type PerformanceMetrics = AnimationMetrics;

export function usePerformanceAwareAnimation(
  options: boolean | AnimationPerformanceOptions = {}
) {
  const normalizedOptions =
    typeof options === 'boolean' ? { reducedMotion: options } : options;
  const { reducedMotion = false, enableHardwareDetection = true } =
    normalizedOptions;

  const variants = reducedMotion ? reducedMotionVariants : performanceAnimationVariants;
  
  const [shouldUseGPU, setShouldUseGPU] = React.useState(true);
  const [animationQuality, setAnimationQuality] = React.useState<'high' | 'medium' | 'low'>('high');

  // Detect performance capabilities
  React.useEffect(() => {
    if (!enableHardwareDetection || typeof window === 'undefined') return;

    // Simple performance detection
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    const hasWebGL = !!gl;
    
    // Check for hardware acceleration
    let hasHardwareAcceleration = false;
    if (hasWebGL && gl) {
      try {
        const renderer = (gl as WebGLRenderingContext).getParameter((gl as WebGLRenderingContext).RENDERER);
        hasHardwareAcceleration = typeof renderer === 'string' && renderer.indexOf('Software') === -1;
      } catch {
        hasHardwareAcceleration = false;
      }
    }
    
    setShouldUseGPU(hasHardwareAcceleration);
    
    // Adjust animation quality based on device capabilities
    if (!hasHardwareAcceleration) {
      setAnimationQuality('low');
    } else if (navigator.hardwareConcurrency && navigator.hardwareConcurrency < 4) {
      setAnimationQuality('medium');
    }
  }, [enableHardwareDetection]);

  const getOptimizedVariant = React.useCallback(
    (variantName: keyof typeof performanceAnimationVariants): Variants => {
      const baseVariant = variants[variantName] as Variants & {
        transition?: { duration?: number };
      };

      if (animationQuality === 'low') {
        return {
          ...baseVariant,
          transition: {
            ...baseVariant.transition,
            duration: (baseVariant.transition?.duration || 0.3) * 0.5, // Faster animations
          },
        } as Variants;
      }

      if (animationQuality === 'medium') {
        return {
          ...baseVariant,
          transition: {
            ...baseVariant.transition,
            duration: (baseVariant.transition?.duration || 0.3) * 0.75, // Slightly faster
          },
        } as Variants;
      }

      return baseVariant;
    },
    [variants, animationQuality],
  );

  const getOptimizedCSS = React.useCallback(() => {
    if (!shouldUseGPU) {
      return {};
    }
    
    return animationQuality === 'high' 
      ? animationCSS.optimizeForAnimation 
      : animationCSS.gpuAcceleration;
  }, [shouldUseGPU, animationQuality]);

  return {
    variants,
    shouldUseGPU,
    animationQuality,
    getOptimizedVariant,
    getOptimizedCSS,
  };
}

// Utility to apply will-change property dynamically
export function useWillChange<TElement extends HTMLElement = HTMLElement>() {
  const [willChangeProperties, setWillChangeProperties] = React.useState<string[]>([]);
  const elementRef = React.useRef<TElement | null>(null);

  const addWillChange = React.useCallback((properties: string[]) => {
    setWillChangeProperties(prev => Array.from(new Set([...prev, ...properties])));
  }, []);

  const removeWillChange = React.useCallback((properties: string[]) => {
    setWillChangeProperties(prev => prev.filter(prop => !properties.includes(prop)));
  }, []);

  const clearWillChange = React.useCallback(() => {
    setWillChangeProperties([]);
  }, []);

  React.useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const willChangeValue = willChangeProperties.length > 0 
      ? willChangeProperties.join(', ') 
      : 'auto';
    
    element.style.willChange = willChangeValue;
  }, [willChangeProperties]);

  return {
    elementRef,
    addWillChange,
    removeWillChange,
    clearWillChange,
    willChangeProperties,
  };
}

// Types
export interface AnimationMetrics {
  fps: number;
  averageFrameTime: number;
  maxFrameTime: number;
  minFrameTime: number;
  droppedFrames: number;
  frameCount: number;
  isSmooth: boolean;
}

// Performance thresholds
export const ANIMATION_PERFORMANCE_THRESHOLDS = {
  EXCELLENT_FPS: 58,
  GOOD_FPS: 50,
  POOR_FPS: 30,
  MAX_FRAME_TIME: 16.67, // 60fps
  ACCEPTABLE_FRAME_TIME: 20, // 50fps
  POOR_FRAME_TIME: 33.33, // 30fps
} as const;

// Singleton animation performance monitor
export const animationPerformanceMonitor = new AnimationPerformanceMonitor();

const animationPerformance = {
  performanceAnimationVariants,
  reducedMotionVariants,
  animationCSS,
  useAnimationPerformance,
  usePerformanceAwareAnimation,
  useWillChange,
  animationPerformanceMonitor,
};

export default animationPerformance;
