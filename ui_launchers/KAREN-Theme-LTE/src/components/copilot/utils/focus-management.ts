/**
 * Focus Management Utilities
 * 
 * This module provides utilities for managing focus in the application,
 * including focus trapping, visible focus indicators, and focus restoration.
 */

/**
 * Types for focus management
 */
export interface FocusElement {
  element: HTMLElement;
  index: number;
}

export interface FocusTrapOptions {
  initialFocus?: HTMLElement | null;
  returnFocus?: HTMLElement | null;
  escapeDeactivates?: boolean;
  clickOutsideDeactivates?: boolean;
  onDeactivate?: () => void;
}

/**
 * Get all focusable elements within a container
 */
export const getFocusableElements = (container: HTMLElement): HTMLElement[] => {
  if (!container) return [];
  
  const focusableSelectors = [
    'a[href]',
    'button:not([disabled])',
    'textarea:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]'
  ];
  
  return Array.from(container.querySelectorAll(focusableSelectors.join(', ')));
};

/**
 * Get the first focusable element within a container
 */
export const getFirstFocusableElement = (container: HTMLElement): HTMLElement | null => {
  const focusableElements = getFocusableElements(container);
  return focusableElements.length > 0 ? (focusableElements[0] ?? null) : null;
};

/**
 * Get the last focusable element within a container
 */
export const getLastFocusableElement = (container: HTMLElement): HTMLElement | null => {
  const focusableElements = getFocusableElements(container);
  return focusableElements.length > 0 ? (focusableElements[focusableElements.length - 1] ?? null) : null;
};

/**
 * Check if an element is focusable
 */
export const isFocusable = (element: HTMLElement): boolean => {
  if (!element || ('disabled' in element && element.disabled)) return false;
  
  const focusableSelectors = [
    'a[href]',
    'button:not([disabled])',
    'textarea:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]'
  ];
  
  return focusableSelectors.some(selector => element.matches(selector));
};

/**
 * Focus an element with a delay to ensure it's rendered
 */
export const focusWithDelay = (element: HTMLElement, delay = 50): void => {
  setTimeout(() => {
    element?.focus();
  }, delay);
};

/**
 * Create a focus trap within a container
 */
export const createFocusTrap = (
  container: HTMLElement,
  options: FocusTrapOptions = {}
) => {
  const {
    initialFocus = null,
    returnFocus = null,
    escapeDeactivates = true,
    clickOutsideDeactivates = false,
    onDeactivate = () => {}
  } = options;
  
  const previousActiveElement: HTMLElement | null = document.activeElement as HTMLElement;
  let focusableElements: HTMLElement[] = [];
  let firstFocusableElement: HTMLElement | null = null;
  let lastFocusableElement: HTMLElement | null = null;
  
  // Initialize the focus trap
  const activate = () => {
    // Get all focusable elements
    focusableElements = getFocusableElements(container);

    if (focusableElements.length === 0) return;

    firstFocusableElement = focusableElements[0] ?? null;
    lastFocusableElement = focusableElements[focusableElements.length - 1] ?? null;

    // Set initial focus
    const elementToFocus = initialFocus || firstFocusableElement;
    if (elementToFocus) {
      focusWithDelay(elementToFocus);
    }

    // Add event listeners
    document.addEventListener('keydown', handleKeyDown);
    if (clickOutsideDeactivates) {
      document.addEventListener('mousedown', handleMouseDown);
    }
  };
  
  // Handle keydown events for focus trapping
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Tab') {
      if (focusableElements.length === 0) return;
      
      if (e.shiftKey) {
        // Shift + Tab: Move focus backward
        if (document.activeElement === firstFocusableElement) {
          e.preventDefault();
          lastFocusableElement?.focus();
        }
      } else {
        // Tab: Move focus forward
        if (document.activeElement === lastFocusableElement) {
          e.preventDefault();
          firstFocusableElement?.focus();
        }
      }
    } else if (e.key === 'Escape' && escapeDeactivates) {
      deactivate();
    }
  };
  
  // Handle mouse down events for click outside deactivation
  const handleMouseDown = (e: MouseEvent) => {
    if (!container.contains(e.target as Node)) {
      deactivate();
    }
  };
  
  // Deactivate the focus trap
  const deactivate = () => {
    // Remove event listeners
    document.removeEventListener('keydown', handleKeyDown);
    document.removeEventListener('mousedown', handleMouseDown);
    
    // Return focus to the previous element
    const elementToReturnTo = returnFocus || previousActiveElement;
    if (elementToReturnTo) {
      focusWithDelay(elementToReturnTo);
    }
    
    // Call deactivate callback
    onDeactivate();
  };
  
  // Update the focus trap (e.g., when content changes)
  const update = () => {
    focusableElements = getFocusableElements(container);

    if (focusableElements.length === 0) return;

    firstFocusableElement = focusableElements[0] ?? null;
    lastFocusableElement = focusableElements[focusableElements.length - 1] ?? null;
  };
  
  return {
    activate,
    deactivate,
    update
  };
};

/**
 * React hook for focus trapping
 */
import { useEffect, useRef } from 'react';

export const useFocusTrap = (
  isActive: boolean,
  options: FocusTrapOptions = {}
) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const trapRef = useRef<{
    activate: () => void;
    deactivate: () => void;
    update: () => void;
  } | null>(null);
  
  useEffect(() => {
    if (!isActive || !containerRef.current) {
      if (trapRef.current) {
        trapRef.current.deactivate();
        trapRef.current = null;
      }
      return;
    }
    
    // Create and activate the focus trap
    trapRef.current = createFocusTrap(containerRef.current, options);
    trapRef.current.activate();
    
    // Clean up on unmount or when isActive changes
    return () => {
      if (trapRef.current) {
        trapRef.current.deactivate();
        trapRef.current = null;
      }
    };
  }, [isActive, options]);
  
  return {
    containerRef,
    update: () => {
      if (trapRef.current) {
        trapRef.current.update();
      }
    }
  };
};

/**
 * Add visible focus indicators to the document
 */
export const addVisibleFocusIndicators = () => {
  if (typeof document === 'undefined') return;
  
  // Check if we already added the style
  const existingStyle = document.getElementById('copilot-focus-indicators');
  if (existingStyle) return;
  
  const style = document.createElement('style');
  style.id = 'copilot-focus-indicators';
  style.textContent = `
    /* Visible focus indicators */
    *:focus {
      outline: 2px solid var(--copilot-color-primary, #3b82f6) !important;
      outline-offset: 2px !important;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Remove focus outline for mouse users */
    *:focus:not(:focus-visible) {
      outline: none !important;
      box-shadow: none !important;
    }
    
    /* Ensure focus is visible for keyboard users */
    *:focus-visible {
      outline: 2px solid var(--copilot-color-primary, #3b82f6) !important;
      outline-offset: 2px !important;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* High contrast mode focus indicators */
    @media (prefers-contrast: high) {
      *:focus-visible {
        outline: 3px solid currentColor !important;
        outline-offset: 2px !important;
        box-shadow: none !important;
      }
    }
  `;
  
  document.head.appendChild(style);
};

/**
 * Remove visible focus indicators from the document
 */
export const removeVisibleFocusIndicators = () => {
  if (typeof document === 'undefined') return;
  
  const style = document.getElementById('copilot-focus-indicators');
  if (style) {
    document.head.removeChild(style);
  }
};

/**
 * React hook for managing focus restoration
 */
export const useFocusRestore = (isActive: boolean) => {
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isActive) {
      // Store the currently focused element
      previousFocusRef.current = document.activeElement as HTMLElement;

      return () => {
        // Restore focus to the previously focused element
        if (previousFocusRef.current) {
          focusWithDelay(previousFocusRef.current);
        }
      };
    }
    return undefined;
  }, [isActive]);

  return {
    restoreFocus: () => {
      if (previousFocusRef.current) {
        focusWithDelay(previousFocusRef.current);
      }
    }
  };
};

/**
 * Move focus to the next element in the tab order
 */
export const moveToNextFocus = (container?: HTMLElement): void => {
  const focusableElements = container 
    ? getFocusableElements(container)
    : getFocusableElements(document.body);
    
  if (focusableElements.length === 0) return;
  
  const currentIndex = focusableElements.findIndex(
    element => element === document.activeElement
  );
  
  const nextIndex = (currentIndex + 1) % focusableElements.length;
  focusableElements[nextIndex]?.focus();
};

/**
 * Move focus to the previous element in the tab order
 */
export const moveToPreviousFocus = (container?: HTMLElement): void => {
  const focusableElements = container 
    ? getFocusableElements(container)
    : getFocusableElements(document.body);
    
  if (focusableElements.length === 0) return;
  
  const currentIndex = focusableElements.findIndex(
    element => element === document.activeElement
  );
  
  const previousIndex = currentIndex <= 0 
    ? focusableElements.length - 1 
    : currentIndex - 1;
    
  focusableElements[previousIndex]?.focus();
};
