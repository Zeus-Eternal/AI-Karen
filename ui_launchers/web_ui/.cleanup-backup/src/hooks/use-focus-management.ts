/**
 * Focus Management Hook
 * Provides comprehensive focus management for modals, dialogs, and complex components
 */

import { useCallback, useEffect, useRef, useState } from 'react';

export interface FocusableElement extends HTMLElement {
  focus(): void;
}

export interface FocusManagementOptions {
  /** Whether focus management is enabled */
  enabled?: boolean;
  /** Whether to restore focus when component unmounts */
  restoreFocus?: boolean;
  /** Whether to trap focus within the container */
  trapFocus?: boolean;
  /** Initial element to focus (selector or element) */
  initialFocus?: string | HTMLElement | null;
  /** Fallback element to focus if initialFocus is not found */
  fallbackFocus?: string | HTMLElement | null;
  /** Elements to exclude from focus trap (selectors) */
  excludeFromTrap?: string[];
  /** Callback when focus enters the container */
  onFocusEnter?: () => void;
  /** Callback when focus leaves the container */
  onFocusLeave?: () => void;
}

/**
 * Hook for managing focus within a container
 */
export const useFocusManagement = <T extends HTMLElement = HTMLElement>(
  options: FocusManagementOptions = {}
) => {
  const {
    enabled = true,
    restoreFocus = true,
    trapFocus = false,
    initialFocus,
    fallbackFocus,
    excludeFromTrap = [],
    onFocusEnter,
    onFocusLeave,
  } = options;

  const containerRef = useRef<T | null>(null);
  const previouslyFocusedElement = useRef<HTMLElement | null>(null);
  const [isActive, setIsActive] = useState(false);

  // Get all focusable elements within the container
  const getFocusableElements = useCallback((): FocusableElement[] => {
    if (!containerRef.current) return [];

    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]',
      'audio[controls]',
      'video[controls]',
      'iframe',
      'object',
      'embed',
      'area[href]',
      'summary',
    ].join(', ');

    const elements = Array.from(
      containerRef.current.querySelectorAll<FocusableElement>(focusableSelectors)
    );

    // Filter out excluded elements
    return elements.filter(element => {
      // Check if element is visible and not disabled
      if (element.offsetParent === null) return false;
      if (element.hasAttribute('disabled')) return false;
      if (element.getAttribute('aria-hidden') === 'true') return false;

      // Check exclude list
      return !excludeFromTrap.some(selector => element.matches(selector));
    });
  }, [excludeFromTrap]);

  // Focus the first focusable element
  const focusFirst = useCallback(() => {
    const focusableElements = getFocusableElements();
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
      return true;
    }
    return false;
  }, [getFocusableElements]);

  // Focus the last focusable element
  const focusLast = useCallback(() => {
    const focusableElements = getFocusableElements();
    if (focusableElements.length > 0) {
      focusableElements[focusableElements.length - 1].focus();
      return true;
    }
    return false;
  }, [getFocusableElements]);

  // Focus a specific element by selector or element reference
  const focusElement = useCallback((target: string | HTMLElement | null) => {
    const container = containerRef.current;
    if (!target || !container) return false;

    let element: HTMLElement | null = null;

    if (typeof target === 'string') {
      element = container.querySelector(target);
    } else {
      element = target;
    }

    if (element && typeof element.focus === 'function') {
      element.focus();
      return true;
    }

    return false;
  }, []);

  // Initialize focus when component becomes active
  const initializeFocus = useCallback(() => {
    const container = containerRef.current;
    if (!enabled || !container) return;

    // Store previously focused element for restoration
    if (restoreFocus) {
      previouslyFocusedElement.current = document.activeElement as HTMLElement;
    }

    // Focus initial element
    let focused = false;

    if (initialFocus) {
      focused = focusElement(initialFocus);
    }

    if (!focused && fallbackFocus) {
      focused = focusElement(fallbackFocus);
    }

    if (!focused) {
      focused = focusFirst();
    }

    // If still no focus, focus the container itself
    if (!focused && container.tabIndex >= 0) {
      container.focus();
    }

    setIsActive(true);
    onFocusEnter?.();
  }, [
    enabled,
    restoreFocus,
    initialFocus,
    fallbackFocus,
    focusElement,
    focusFirst,
    onFocusEnter,
  ]);

  // Restore focus when component becomes inactive
  const restorePreviousFocus = useCallback(() => {
    if (restoreFocus && previouslyFocusedElement.current) {
      try {
        previouslyFocusedElement.current.focus();
      } catch (error) {
        // Element might no longer exist or be focusable
        console.warn('Could not restore focus to previous element:', error);
      }
    }

    setIsActive(false);
    onFocusLeave?.();
  }, [restoreFocus, onFocusLeave]);

  // Handle tab key for focus trapping
  const handleTabKey = useCallback((event: KeyboardEvent) => {
    if (!trapFocus || !enabled || event.key !== 'Tab') return;

    const focusableElements = getFocusableElements();
    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    const activeElement = document.activeElement as HTMLElement;

    if (event.shiftKey) {
      // Shift + Tab: moving backwards
      if (activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      }
    } else {
      // Tab: moving forwards
      if (activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }
  }, [trapFocus, enabled, getFocusableElements]);

  // Handle focus events
  const handleFocus = useCallback((event: FocusEvent) => {
    const container = containerRef.current;
    if (!enabled || !container) return;

    const target = event.target as HTMLElement;

    // Check if focus is entering the container
    if (container.contains(target) && !isActive) {
      setIsActive(true);
      onFocusEnter?.();
    }
  }, [enabled, isActive, onFocusEnter]);

  const handleBlur = useCallback((event: FocusEvent) => {
    const container = containerRef.current;
    if (!enabled || !container) return;

    const relatedTarget = event.relatedTarget as HTMLElement;

    // Check if focus is leaving the container entirely
    if (!relatedTarget || !container.contains(relatedTarget)) {
      if (trapFocus) {
        // For focus trap, prevent focus from leaving
        event.preventDefault();
        const focusableElements = getFocusableElements();
        if (focusableElements.length > 0) {
          focusableElements[0].focus();
        }
      } else {
        setIsActive(false);
        onFocusLeave?.();
      }
    }
  }, [enabled, trapFocus, getFocusableElements, onFocusLeave]);

  // Set up event listeners
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !enabled) return;

    container.addEventListener('keydown', handleTabKey);
    container.addEventListener('focus', handleFocus, true);
    container.addEventListener('blur', handleBlur, true);

    return () => {
      container.removeEventListener('keydown', handleTabKey);
      container.removeEventListener('focus', handleFocus, true);
      container.removeEventListener('blur', handleBlur, true);
    };
  }, [handleTabKey, handleFocus, handleBlur, enabled]);

  // Initialize focus when enabled
  useEffect(() => {
    if (enabled) {
      initializeFocus();
    } else {
      restorePreviousFocus();
    }

    // Cleanup on unmount
    return () => {
      if (enabled) {
        restorePreviousFocus();
      }
    };
  }, [enabled, initializeFocus, restorePreviousFocus]);

  return {
    containerRef,
    isActive,
    initializeFocus,
    restorePreviousFocus,
    focusFirst,
    focusLast,
    focusElement,
    getFocusableElements,
    containerProps: {
      ref: (node: T | null) => {
        containerRef.current = node;
      },
      tabIndex: trapFocus ? -1 : undefined,
    },
  };
};

/**
 * Hook for focus trap specifically designed for modals and dialogs
 */
export const useFocusTrap = <T extends HTMLElement = HTMLElement>(
  isOpen: boolean,
  options: Omit<FocusManagementOptions, 'trapFocus'> = {}
) => {
  return useFocusManagement<T>({
    ...options,
    enabled: isOpen,
    trapFocus: true,
    restoreFocus: true,
  });
};

/**
 * Hook for managing focus restoration
 */
export const useFocusRestore = () => {
  const previouslyFocusedElement = useRef<HTMLElement | null>(null);

  const saveFocus = useCallback(() => {
    previouslyFocusedElement.current = document.activeElement as HTMLElement;
  }, []);

  const restoreFocus = useCallback(() => {
    if (previouslyFocusedElement.current) {
      try {
        previouslyFocusedElement.current.focus();
      } catch (error) {
        console.warn('Could not restore focus:', error);
      }
    }
  }, []);

  return {
    saveFocus,
    restoreFocus,
  };
};

/**
 * Hook for managing visible focus indicators
 */
export const useFocusVisible = () => {
  const [isFocusVisible, setIsFocusVisible] = useState(false);
  const [hadKeyboardEvent, setHadKeyboardEvent] = useState(false);

  useEffect(() => {
    const handleKeyDown = () => {
      setHadKeyboardEvent(true);
    };

    const handleMouseDown = () => {
      setHadKeyboardEvent(false);
    };

    const handleFocus = () => {
      setIsFocusVisible(hadKeyboardEvent);
    };

    const handleBlur = () => {
      setIsFocusVisible(false);
    };

    document.addEventListener('keydown', handleKeyDown, true);
    document.addEventListener('mousedown', handleMouseDown, true);
    document.addEventListener('focus', handleFocus, true);
    document.addEventListener('blur', handleBlur, true);

    return () => {
      document.removeEventListener('keydown', handleKeyDown, true);
      document.removeEventListener('mousedown', handleMouseDown, true);
      document.removeEventListener('focus', handleFocus, true);
      document.removeEventListener('blur', handleBlur, true);
    };
  }, [hadKeyboardEvent]);

  return {
    isFocusVisible,
    focusVisibleProps: {
      'data-focus-visible': isFocusVisible,
    },
  };
};

export default useFocusManagement;
