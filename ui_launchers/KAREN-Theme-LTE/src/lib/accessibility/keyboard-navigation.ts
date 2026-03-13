/**
 * Keyboard Navigation System
 * Comprehensive keyboard navigation and focus management for WCAG 2.1 AA compliance
 */

'use client';

import React, { useEffect, useCallback, useRef } from 'react';
import { useAccessibility } from '@/contexts/AccessibilityContext';

// Keyboard navigation options
export interface KeyboardNavigationOptions {
  // Focus management
  trapFocus?: boolean;
  restoreFocus?: boolean;
  initialFocus?: HTMLElement | string;
  finalFocus?: HTMLElement | string;
  
  // Navigation behavior
  cyclic?: boolean;
  escapeKey?: () => void;
  enterKey?: () => void;
  arrowKeys?: {
    horizontal?: (direction: 'left' | 'right') => void;
    vertical?: (direction: 'up' | 'down') => void;
  };
  
  // Custom key handlers
  keyHandlers?: Record<string, (event: KeyboardEvent) => void>;
  
  // Focus indicators
  showFocusRing?: boolean;
  focusOutlineStyle?: React.CSSProperties;
  
  // Skip links
  enableSkipLinks?: boolean;
  skipLinkTargets?: string[];
}

// Focusable elements selector
const FOCUSABLE_ELEMENTS_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
  '[contenteditable="true"]',
  'summary',
  'audio[controls]',
  'video[controls]',
  '[role="button"]:not([disabled])',
  '[role="link"]',
  '[role="menuitem"]',
  '[role="option"]',
  '[role="tab"]',
  '[role="treeitem"]',
].join(', ');

// Get all focusable elements within a container
export function getFocusableElements(container: Element = document.documentElement): HTMLElement[] {
  return Array.from(container.querySelectorAll(FOCUSABLE_ELEMENTS_SELECTOR)) as HTMLElement[];
}

// Get the first focusable element
export function getFirstFocusableElement(container: Element = document.documentElement): HTMLElement | null {
  const elements = getFocusableElements(container);
  return elements.length > 0 ? elements[0] ?? null : null;
}

// Get the last focusable element
export function getLastFocusableElement(container: Element = document.documentElement): HTMLElement | null {
  const elements = getFocusableElements(container);
  return elements.length > 0 ? elements[elements.length - 1] ?? null : null;
}

// Check if an element is focusable
export function isFocusable(element: Element): boolean {
  return element.matches(FOCUSABLE_ELEMENTS_SELECTOR);
}

// Check if an element is visible
export function isVisible(element: Element): boolean {
  const style = window.getComputedStyle(element);
  return style.display !== 'none' && 
         style.visibility !== 'hidden' && 
         style.opacity !== '0' &&
         (element as HTMLElement).offsetWidth > 0 &&
         (element as HTMLElement).offsetHeight > 0;
}

// Get visible focusable elements
export function getVisibleFocusableElements(container: Element = document.documentElement): HTMLElement[] {
  return getFocusableElements(container).filter(isVisible);
}

// Focus trap hook
export function useFocusTrap(options: KeyboardNavigationOptions = {}) {
  const containerRef = useRef<HTMLElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const { setFocusTrap, announceToScreenReader } = useAccessibility();

  // Set initial focus
  const setInitialFocus = useCallback(() => {
    if (!containerRef.current) return;

    let targetElement: HTMLElement | null = null;

    if (options.initialFocus) {
      if (typeof options.initialFocus === 'string') {
        targetElement = containerRef.current.querySelector(options.initialFocus) as HTMLElement;
      } else {
        targetElement = options.initialFocus;
      }
    }

    if (!targetElement) {
      targetElement = getFirstFocusableElement(containerRef.current);
    }

    if (targetElement) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      targetElement.focus();
      announceToScreenReader('Focus moved to new section');
    }
  }, [options.initialFocus, announceToScreenReader]);

  // Restore focus
  const restoreFocus = useCallback(() => {
    if (options.finalFocus) {
      if (typeof options.finalFocus === 'string') {
        const targetElement = document.querySelector(options.finalFocus) as HTMLElement;
        if (targetElement) {
          targetElement.focus();
        }
      } else {
        options.finalFocus.focus();
      }
    } else if (previousFocusRef.current && isVisible(previousFocusRef.current)) {
      previousFocusRef.current.focus();
    }
  }, [options.finalFocus]);

  // Handle keyboard navigation within trap
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (!containerRef.current) return;

    const focusableElements = getVisibleFocusableElements(containerRef.current);
    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    const currentElement = document.activeElement as HTMLElement;

    // Handle Tab key
    if (event.key === 'Tab') {
      if (event.shiftKey) {
        // Shift + Tab (previous)
        if (currentElement === firstElement) {
          event.preventDefault();
          lastElement?.focus();
        }
      } else {
        // Tab (next)
        if (currentElement === lastElement) {
          event.preventDefault();
          firstElement?.focus();
        }
      }
    }

    // Handle Escape key
    if (event.key === 'Escape' && options.escapeKey) {
      event.preventDefault();
      options.escapeKey();
    }

    // Handle Enter key
    if (event.key === 'Enter' && options.enterKey) {
      if (currentElement && isFocusable(currentElement)) {
        event.preventDefault();
        options.enterKey();
      }
    }

    // Handle arrow keys
    if (options.arrowKeys) {
      if (event.key === 'ArrowLeft' && options.arrowKeys.horizontal) {
        event.preventDefault();
        options.arrowKeys.horizontal('left');
      } else if (event.key === 'ArrowRight' && options.arrowKeys.horizontal) {
        event.preventDefault();
        options.arrowKeys.horizontal('right');
      } else if (event.key === 'ArrowUp' && options.arrowKeys.vertical) {
        event.preventDefault();
        options.arrowKeys.vertical('up');
      } else if (event.key === 'ArrowDown' && options.arrowKeys.vertical) {
        event.preventDefault();
        options.arrowKeys.vertical('down');
      }
    }

    // Handle custom key handlers
    if (options.keyHandlers && options.keyHandlers[event.key]) {
      event.preventDefault();
      options.keyHandlers[event.key]?.(event);
    }
  }, [options]);

  // Setup focus trap
  useEffect(() => {
    if (!options.trapFocus || !containerRef.current) return;

    setFocusTrap(true);
    setInitialFocus();

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      setFocusTrap(false);
      
      if (options.restoreFocus) {
        restoreFocus();
      }
    };
  }, [options.trapFocus, handleKeyDown, setInitialFocus, restoreFocus, setFocusTrap, options.restoreFocus]);

  return {
    containerRef,
    setInitialFocus,
    restoreFocus,
  };
}

// Keyboard navigation hook
export function useKeyboardNavigation(options: KeyboardNavigationOptions = {}) {
  const { state, announceToScreenReader } = useAccessibility();

  // Handle global keyboard shortcuts
  useEffect(() => {
    if (!state.preferences.keyboardNavigation) return;

    const handleGlobalKeyDown = (event: KeyboardEvent) => {
      // Skip if focus is in input field
      const activeElement = document.activeElement;
      if (activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        (activeElement as HTMLElement).contentEditable === 'true'
      )) {
        return;
      }

      // Alt + S: Skip to main content
      if (event.altKey && event.key === 's') {
        event.preventDefault();
        const mainContent = document.querySelector('main, [role="main"], #main');
        if (mainContent) {
          const firstFocusable = getFirstFocusableElement(mainContent);
          if (firstFocusable) {
            firstFocusable.focus();
            announceToScreenReader('Skipped to main content');
          }
        }
      }

      // Alt + N: Navigate to navigation
      if (event.altKey && event.key === 'n') {
        event.preventDefault();
        const navigation = document.querySelector('nav, [role="navigation"], #navigation');
        if (navigation) {
          const firstFocusable = getFirstFocusableElement(navigation);
          if (firstFocusable) {
            firstFocusable.focus();
            announceToScreenReader('Navigated to navigation menu');
          }
        }
      }

      // Alt + F: Navigate to search
      if (event.altKey && event.key === 'f') {
        event.preventDefault();
        const search = document.querySelector('input[type="search"], [role="search"], #search');
        if (search) {
          (search as HTMLElement).focus();
          announceToScreenReader('Focused on search field');
        }
      }

      // Alt + H: Navigate to help
      if (event.altKey && event.key === 'h') {
        event.preventDefault();
        const help = document.querySelector('[role="help"], #help, .help');
        if (help) {
          const firstFocusable = getFirstFocusableElement(help);
          if (firstFocusable) {
            firstFocusable.focus();
            announceToScreenReader('Navigated to help section');
          }
        }
      }
    };

    document.addEventListener('keydown', handleGlobalKeyDown);

    return () => {
      document.removeEventListener('keydown', handleGlobalKeyDown);
    };
  }, [state.preferences.keyboardNavigation, announceToScreenReader]);

  // Focus management utilities
  const focusElement = useCallback((selector: string | HTMLElement) => {
    let element: HTMLElement | null = null;
    
    if (typeof selector === 'string') {
      element = document.querySelector(selector) as HTMLElement;
    } else {
      element = selector;
    }

    if (element && isFocusable(element) && isVisible(element)) {
      element.focus();
      return true;
    }
    
    return false;
  }, []);

  const focusNext = useCallback((container?: Element) => {
    const focusableElements = getVisibleFocusableElements(container);
    const currentIndex = focusableElements.indexOf(document.activeElement as HTMLElement);
    
    if (currentIndex < focusableElements.length - 1) {
      focusableElements[currentIndex + 1]?.focus();
      return true;
    } else if (options.cyclic && focusableElements.length > 0) {
      focusableElements[0]?.focus();
      return true;
    }
    
    return false;
  }, [options.cyclic]);

  const focusPrevious = useCallback((container?: Element) => {
    const focusableElements = getVisibleFocusableElements(container);
    const currentIndex = focusableElements.indexOf(document.activeElement as HTMLElement);
    
    if (currentIndex > 0) {
      focusableElements[currentIndex - 1]?.focus();
      return true;
    } else if (options.cyclic && focusableElements.length > 0) {
      focusableElements[focusableElements.length - 1]?.focus();
      return true;
    }
    
    return false;
  }, [options.cyclic]);

  const focusFirst = useCallback((container?: Element) => {
    const firstElement = getFirstFocusableElement(container);
    if (firstElement) {
      firstElement.focus();
      return true;
    }
    return false;
  }, []);

  const focusLast = useCallback((container?: Element) => {
    const lastElement = getLastFocusableElement(container);
    if (lastElement) {
      lastElement.focus();
      return true;
    }
    return false;
  }, []);

  return {
    focusElement,
    focusNext,
    focusPrevious,
    focusFirst,
    focusLast,
    getFocusableElements,
    getVisibleFocusableElements,
    isFocusable,
    isVisible,
  };
}

// Skip link component props
export interface SkipLinkProps {
  href: string;
  children: React.ReactNode;
  className?: string;
}

// Skip link component for keyboard navigation
export function SkipLink({ href, children, className = '' }: SkipLinkProps) {
  const handleClick = useCallback((event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    const targetId = href.replace('#', '');
    const targetElement = document.getElementById(targetId);
    
    if (targetElement) {
      const firstFocusable = getFirstFocusableElement(targetElement);
      if (firstFocusable) {
        firstFocusable.focus();
      } else {
        targetElement.scrollIntoView();
        targetElement.setAttribute('tabindex', '-1');
        targetElement.focus();
        setTimeout(() => {
          targetElement.removeAttribute('tabindex');
        }, 1000);
      }
    }
  }, [href]);

  return React.createElement('a', {
    href,
    onClick: handleClick,
    className: `skip-link ${className}`,
    style: {
      position: 'absolute',
      top: '-40px',
      left: '6px',
      background: 'var(--background)',
      color: 'var(--foreground)',
      padding: '8px',
      textDecoration: 'none',
      borderRadius: '4px',
      zIndex: 10000,
      transition: 'top 0.3s',
    },
    onFocus: (e) => {
      (e.target as HTMLElement).style.top = '6px';
    },
    onBlur: (e) => {
      (e.target as HTMLElement).style.top = '-40px';
    },
  }, children);
}