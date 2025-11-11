"use client";

import { Variants } from "framer-motion";

// ============================================================================
// TRANSITION TYPES
// ============================================================================

export type TransitionType = 
  | "slide" 
  | "fade" 
  | "scale" 
  | "flip" 
  | "push" 
  | "cover";

export type TransitionDirection = 
  | "left" 
  | "right" 
  | "up" 
  | "down";

// ============================================================================
// PANEL TRANSITION VARIANTS
// ============================================================================

/**
 * Slide transition variants
 */
export const slideVariants: Record<TransitionDirection, Variants> = {
  left: {
    closed: { x: "-100%", opacity: 0 },
    open: { x: 0, opacity: 1 },
    initial: { x: 20, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: -20, opacity: 0 },
  },
  right: {
    closed: { x: "100%", opacity: 0 },
    open: { x: 0, opacity: 1 },
    initial: { x: -20, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: 20, opacity: 0 },
  },
  up: {
    closed: { y: "-100%", opacity: 0 },
    open: { y: 0, opacity: 1 },
    initial: { y: 20, opacity: 0 },
    animate: { y: 0, opacity: 1 },
    exit: { y: -20, opacity: 0 },
  },
  down: {
    closed: { y: "100%", opacity: 0 },
    open: { y: 0, opacity: 1 },
    initial: { y: -20, opacity: 0 },
    animate: { y: 0, opacity: 1 },
    exit: { y: 20, opacity: 0 },
  },
};

/**
 * Fade transition variants
 */
export const fadeVariants: Variants = {
  closed: { opacity: 0 },
  open: { opacity: 1 },
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

/**
 * Scale transition variants
 */
export const scaleVariants: Variants = {
  closed: { 
    scale: 0.8, 
    opacity: 0,
    transformOrigin: "center",
  },
  open: { 
    scale: 1, 
    opacity: 1,
    transformOrigin: "center",
  },
  initial: { 
    scale: 0.95, 
    opacity: 0,
    transformOrigin: "center",
  },
  animate: { 
    scale: 1, 
    opacity: 1,
    transformOrigin: "center",
  },
  exit: { 
    scale: 0.95, 
    opacity: 0,
    transformOrigin: "center",
  },
};

/**
 * Flip transition variants
 */
export const flipVariants: Record<TransitionDirection, Variants> = {
  left: {
    closed: { rotateY: -90, opacity: 0, transformOrigin: "left" },
    open: { rotateY: 0, opacity: 1, transformOrigin: "left" },
    initial: { rotateY: 15, opacity: 0, transformOrigin: "left" },
    animate: { rotateY: 0, opacity: 1, transformOrigin: "left" },
    exit: { rotateY: -15, opacity: 0, transformOrigin: "left" },
  },
  right: {
    closed: { rotateY: 90, opacity: 0, transformOrigin: "right" },
    open: { rotateY: 0, opacity: 1, transformOrigin: "right" },
    initial: { rotateY: -15, opacity: 0, transformOrigin: "right" },
    animate: { rotateY: 0, opacity: 1, transformOrigin: "right" },
    exit: { rotateY: 15, opacity: 0, transformOrigin: "right" },
  },
  up: {
    closed: { rotateX: -90, opacity: 0, transformOrigin: "top" },
    open: { rotateX: 0, opacity: 1, transformOrigin: "top" },
    initial: { rotateX: 15, opacity: 0, transformOrigin: "top" },
    animate: { rotateX: 0, opacity: 1, transformOrigin: "top" },
    exit: { rotateX: -15, opacity: 0, transformOrigin: "top" },
  },
  down: {
    closed: { rotateX: 90, opacity: 0, transformOrigin: "bottom" },
    open: { rotateX: 0, opacity: 1, transformOrigin: "bottom" },
    initial: { rotateX: -15, opacity: 0, transformOrigin: "bottom" },
    animate: { rotateX: 0, opacity: 1, transformOrigin: "bottom" },
    exit: { rotateX: 15, opacity: 0, transformOrigin: "bottom" },
  },
};

/**
 * Push transition variants (content pushes in from direction)
 */
export const pushVariants: Record<TransitionDirection, Variants> = {
  left: {
    closed: { x: "-100%", opacity: 0 },
    open: { x: 0, opacity: 1 },
    initial: { x: "100%", opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: "-100%", opacity: 0 },
  },
  right: {
    closed: { x: "100%", opacity: 0 },
    open: { x: 0, opacity: 1 },
    initial: { x: "-100%", opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: "100%", opacity: 0 },
  },
  up: {
    closed: { y: "-100%", opacity: 0 },
    open: { y: 0, opacity: 1 },
    initial: { y: "100%", opacity: 0 },
    animate: { y: 0, opacity: 1 },
    exit: { y: "-100%", opacity: 0 },
  },
  down: {
    closed: { y: "100%", opacity: 0 },
    open: { y: 0, opacity: 1 },
    initial: { y: "-100%", opacity: 0 },
    animate: { y: 0, opacity: 1 },
    exit: { y: "100%", opacity: 0 },
  },
};

/**
 * Cover transition variants (content covers from direction)
 */
export const coverVariants: Record<TransitionDirection, Variants> = {
  left: {
    closed: { x: "-100%", opacity: 1, zIndex: 10 },
    open: { x: 0, opacity: 1, zIndex: 10 },
    initial: { x: "-100%", opacity: 1, zIndex: 10 },
    animate: { x: 0, opacity: 1, zIndex: 10 },
    exit: { x: "-100%", opacity: 1, zIndex: 10 },
  },
  right: {
    closed: { x: "100%", opacity: 1, zIndex: 10 },
    open: { x: 0, opacity: 1, zIndex: 10 },
    initial: { x: "100%", opacity: 1, zIndex: 10 },
    animate: { x: 0, opacity: 1, zIndex: 10 },
    exit: { x: "100%", opacity: 1, zIndex: 10 },
  },
  up: {
    closed: { y: "-100%", opacity: 1, zIndex: 10 },
    open: { y: 0, opacity: 1, zIndex: 10 },
    initial: { y: "-100%", opacity: 1, zIndex: 10 },
    animate: { y: 0, opacity: 1, zIndex: 10 },
    exit: { y: "-100%", opacity: 1, zIndex: 10 },
  },
  down: {
    closed: { y: "100%", opacity: 1, zIndex: 10 },
    open: { y: 0, opacity: 1, zIndex: 10 },
    initial: { y: "100%", opacity: 1, zIndex: 10 },
    animate: { y: 0, opacity: 1, zIndex: 10 },
    exit: { y: "100%", opacity: 1, zIndex: 10 },
  },
};

// ============================================================================
// TRANSITION CONFIGURATIONS
// ============================================================================

/**
 * Spring transition configuration
 */
export const springTransition = {
  type: "spring" as const,
  stiffness: 300,
  damping: 30,
  mass: 0.8,
};

/**
 * Smooth transition configuration
 */
export const smoothTransition = {
  type: "tween" as const,
  ease: "easeInOut" as const,
  duration: 0.3,
};

/**
 * Fast transition configuration
 */
export const fastTransition = {
  type: "tween" as const,
  ease: "easeOut" as const,
  duration: 0.2,
};

/**
 * Slow transition configuration
 */
export const slowTransition = {
  type: "tween" as const,
  ease: "easeInOut" as const,
  duration: 0.5,
};

/**
 * Reduced motion transition configuration
 */
export const reducedMotionTransition = {
  duration: 0.01,
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Get transition variants based on type and direction
 */
export function getTransitionVariants(
  type: TransitionType,
  direction: TransitionDirection = "right"
): Variants {
  switch (type) {
    case "slide":
      return slideVariants[direction];
    case "fade":
      return fadeVariants;
    case "scale":
      return scaleVariants;
    case "flip":
      return flipVariants[direction];
    case "push":
      return pushVariants[direction];
    case "cover":
      return coverVariants[direction];
    default:
      return slideVariants[direction];
  }
}

/**
 * Apply transition configuration to variants
 */
export function applyTransitionConfig(
  variants: Variants,
  transitionConfig: unknown
): Variants {
  const enhancedVariants: Variants = {};
  
  Object.keys(variants).forEach((key) => {
    const variant = variants[key];
    if (typeof variant === 'object' && variant !== null) {
      enhancedVariants[key] = {
        ...variant,
        transition: {
          ...transitionConfig,
          ...(variant as unknown).transition,
        },
      };
    } else {
      enhancedVariants[key] = variant;
    }
  });

  return enhancedVariants;
}

/**
 * Create reduced motion variants from normal variants
 */
export function createReducedMotionVariants(variants: Variants): Variants {
  const reducedVariants: Variants = {};

  Object.keys(variants).forEach((key) => {
    const variant = variants[key];
    if (typeof variant === 'object' && variant !== null) {
      reducedVariants[key] = {
        opacity: (variant as unknown).opacity ?? 1,
        transition: reducedMotionTransition,
      };
    } else {
      reducedVariants[key] = variant;
    }
  });
  return reducedVariants;
}