import { useRef, useEffect, useState, useCallback } from 'react';

interface UseIntersectionObserverOptions {
  root?: Element | null;
  rootMargin?: string;
  threshold?: number | number[];
  freezeOnceVisible?: boolean;
}

/**
 * Hook for observing element intersection with the viewport
 */
export function useIntersectionObserver(
  options: UseIntersectionObserverOptions = {}
): [
  (node: Element | null) => void,
  boolean,
  IntersectionObserverEntry | null
] {
  const {
    threshold = 0,
    root = null,
    rootMargin = '0%',
    freezeOnceVisible = false
  } = options;

  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [frozen, setFrozen] = useState(false);
  const previousRef = useRef<Element | null>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  // Clean up observer
  useEffect(() => {
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, []);

  const setRef = useCallback(
    (node: Element | null) => {
      // Clean up previous observer
      if (previousRef.current && observerRef.current) {
        observerRef.current.unobserve(previousRef.current);
      }

      // If we're frozen, don't observe new elements
      if (frozen) return;

      previousRef.current = node;

      // If there's no node, don't observe
      if (!node) return;

      // Create a new observer if needed
      if (!observerRef.current) {
        observerRef.current = new IntersectionObserver(
          (entries) => {
            const entry = entries[0];
            if (!entry) return;
            setEntry(entry);
            setIsVisible(entry.isIntersecting);

            if (freezeOnceVisible && entry.isIntersecting) {
              setFrozen(true);
              observerRef.current?.unobserve(node);
            }
          },
          { threshold, root, rootMargin }
        );
      }

      // Observe the new node
      observerRef.current.observe(node);
    },
    [threshold, root, rootMargin, freezeOnceVisible, frozen]
  );

  return [setRef, isVisible, entry];
}

export default useIntersectionObserver;