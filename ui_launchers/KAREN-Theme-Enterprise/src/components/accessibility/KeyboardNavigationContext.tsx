"use client";

import { createContext, useContext, useEffect, useRef } from "react";

export interface KeyboardNavigationContextValue {
  currentFocusIndex: number;
  totalItems: number;
  moveNext: () => void;
  movePrevious: () => void;
  moveFirst: () => void;
  moveLast: () => void;
  moveTo: (index: number) => void;
  registerNavigationContainer: (element: HTMLElement) => (() => void) | void;
  unregisterNavigationContainer: () => void;
  enabled: boolean;
  setEnabled: (enabled: boolean) => void;
}

export const KeyboardNavigationContext = createContext<
  KeyboardNavigationContextValue | undefined
>(undefined);

export function useKeyboardNavigationContext() {
  const context = useContext(KeyboardNavigationContext);
  if (context === undefined) {
    throw new Error(
      "useKeyboardNavigationContext must be used within a KeyboardNavigationProvider",
    );
  }
  return context;
}

export function useNavigationContainer() {
  const { registerNavigationContainer, unregisterNavigationContainer } =
    useKeyboardNavigationContext();
  const containerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) {
      return;
    }

    const cleanup = registerNavigationContainer(element);
    return () => {
      if (typeof cleanup === "function") {
        cleanup();
      }
      unregisterNavigationContainer();
    };
  }, [registerNavigationContainer, unregisterNavigationContainer]);

  return containerRef;
}

export function useNavigationItem(index: number) {
  const { currentFocusIndex, moveTo } = useKeyboardNavigationContext();
  const isActive = currentFocusIndex === index;

  const itemProps = {
    "data-keyboard-nav-item": true,
    "data-nav-index": index,
    tabIndex: isActive ? 0 : -1,
    onClick: () => moveTo(index),
    onFocus: () => moveTo(index),
  } as const;

  return {
    isActive,
    itemProps,
  };
}
