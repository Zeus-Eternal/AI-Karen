'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useState } from 'react';
import { TransitionVariant } from './types';

interface UsePageTransitionOptions {
  variant?: TransitionVariant;
  duration?: number;
  onTransitionStart?: () => void;
  onTransitionComplete?: () => void;
}

export function usePageTransition(options: UsePageTransitionOptions = {}) {
  const router = useRouter();
  const [isTransitioning, setIsTransitioning] = useState(false);
  
  const {
    variant = 'fade',
    duration = 300,
    onTransitionStart,
    onTransitionComplete
  } = options;

  const navigateWithTransition = useCallback(
    (href: string, replace = false) => {
      if (isTransitioning) return;
      
      setIsTransitioning(true);
      onTransitionStart?.();
      
      // Start the transition
      setTimeout(() => {
        if (replace) {
          router.replace(href);
        } else {
          router.push(href);
        }
        
        // Complete the transition
        setTimeout(() => {
          setIsTransitioning(false);
          onTransitionComplete?.();
        }, duration);
      }, duration / 2);
    },
    [router, isTransitioning, duration, onTransitionStart, onTransitionComplete]
  );

  const prefetchWithTransition = useCallback(
    (href: string) => {
      router.prefetch(href);
    },
    [router]
  );

  return {
    navigateWithTransition,
    prefetchWithTransition,
    isTransitioning,
    variant,
    duration
  };
}