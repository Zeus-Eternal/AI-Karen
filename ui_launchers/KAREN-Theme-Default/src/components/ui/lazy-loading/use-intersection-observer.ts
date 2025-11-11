"use client";

import { useCallback, useEffect, useRef, useState, type RefObject } from 'react';

export interface IntersectionObserverOptions {
  threshold?: number | number[];
  rootMargin?: string;
  root?: Element | null;
  triggerOnce?: boolean;
  skip?: boolean;
}

export interface UseIntersectionObserverReturn {
  ref: RefObject<HTMLElement>;
  isIntersecting: boolean;
  entry: IntersectionObserverEntry | null;
}

export function useIntersectionObserver(
  options: IntersectionObserverOptions = {}
): UseIntersectionObserverReturn {
  const {
    threshold = 0,
    rootMargin = '0px',
    root = null,
    triggerOnce = false,
    skip = false,
  } = options;

  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null);
  const [isIntersecting, setIsIntersecting] = useState(false);
  const elementRef = useRef<HTMLElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    const element = elementRef.current;

    if (!element || skip) return;

    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    observerRef.current = new IntersectionObserver(
      ([observerEntry]) => {
        setEntry(observerEntry);
        setIsIntersecting(observerEntry.isIntersecting);

        if (observerEntry.isIntersecting && triggerOnce && observerRef.current) {
          observerRef.current.disconnect();
        }
      },
      {
        threshold,
        rootMargin,
        root,
      }
    );

    observerRef.current.observe(element);

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [threshold, rootMargin, root, triggerOnce, skip]);

  return {
    ref: elementRef,
    isIntersecting,
    entry,
  };
}

export function useMultipleIntersectionObserver(
  elements: (HTMLElement | null)[],
  options: IntersectionObserverOptions = {}
): {
  isIntersecting: (element: HTMLElement | null) => boolean;
  getEntry: (element: HTMLElement | null) => IntersectionObserverEntry | null;
  entries: IntersectionObserverEntry[];
} {
  const [entries, setEntries] = useState<Map<HTMLElement, IntersectionObserverEntry>>(new Map());
  const observerRef = useRef<IntersectionObserver | null>(null);

  const updateEntry = useCallback((observerEntry: IntersectionObserverEntry) => {
    setEntries((previousEntries) => new Map(previousEntries.set(observerEntry.target as HTMLElement, observerEntry)));
  }, []);

  useEffect(() => {
    const validElements = elements.filter((element): element is HTMLElement => element !== null);

    if (validElements.length === 0) return;

    observerRef.current = new IntersectionObserver(
      (observerEntries) => {
        observerEntries.forEach(updateEntry);
      },
      options
    );

    validElements.forEach((element) => {
      observerRef.current?.observe(element);
    });

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [elements, options, updateEntry]);

  const isIntersecting = useCallback(
    (element: HTMLElement | null) => {
      if (!element) return false;
      return entries.get(element)?.isIntersecting ?? false;
    },
    [entries]
  );

  const getEntry = useCallback(
    (element: HTMLElement | null) => {
      if (!element) return null;
      return entries.get(element) ?? null;
    },
    [entries]
  );

  return {
    isIntersecting,
    getEntry,
    entries: Array.from(entries.values()),
  };
}

export default useIntersectionObserver;
