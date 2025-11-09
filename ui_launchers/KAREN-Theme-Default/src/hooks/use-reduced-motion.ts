"use client";

import { useState, useEffect } from 'react';

/**
 * Hook to detect user's reduced motion preference
 * 
 * This hook checks the user's system preference for reduced motion
 * and provides a boolean value that can be used to disable or simplify animations.
 * 
 * @returns boolean indicating if reduced motion is preferred
 */
export function useReducedMotion(): boolean {
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    // Check if we're in a browser environment
    if (typeof window === 'undefined') {
      return;
    }

    // Check for prefers-reduced-motion media query
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    
    // Set initial value
    setReducedMotion(mediaQuery.matches);

    // Listen for changes
    const handleChange = (event: MediaQueryListEvent) => {
      setReducedMotion(event.matches);
    };

    // Add event listener
    mediaQuery.addEventListener('change', handleChange);

    // Cleanup
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  return reducedMotion;
}

/**
 * Hook to get animation duration based on reduced motion preference
 * 
 * @param normalDuration - Duration in seconds for normal motion
 * @param reducedDuration - Duration in seconds for reduced motion (default: 0.01)
 * @returns Duration value to use for animations
 */
export function useAnimationDuration(
  normalDuration: number, 
  reducedDuration: number = 0.01
): number {
  const reducedMotion = useReducedMotion();
  return reducedMotion ? reducedDuration : normalDuration;
}

/**
 * Hook to get animation variants based on reduced motion preference
 * 
 * @param normalVariants - Animation variants for normal motion
 * @param reducedVariants - Animation variants for reduced motion
 * @returns Variants object to use for animations
 */
export function useAnimationVariants<T>(
  normalVariants: T,
  reducedVariants: T
): T {
  const reducedMotion = useReducedMotion();
  return reducedMotion ? reducedVariants : normalVariants;
}