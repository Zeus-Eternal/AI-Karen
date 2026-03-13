/**
 * Focus Management and Visual Indicators System
 * Comprehensive focus management and visual indicators for WCAG 2.1 AA compliance
 */

'use client';

import React, { useEffect, useCallback, useMemo, useRef, useState } from 'react';
import { useAccessibility } from '@/contexts/AccessibilityContext';

// Focus indicator styles
export interface FocusIndicatorStyles {
  outline: string;
  outlineOffset: string;
  boxShadow?: string;
  backgroundColor?: string;
  borderColor?: string;
  borderWidth?: string;
  borderStyle?: string;
}

const DEFAULT_FOCUS_STYLES: FocusIndicatorStyles = {
  outline: '2px solid var(--focus-color, #2563eb)',
  outlineOffset: '2px',
  boxShadow: '0 0 0 2px var(--focus-color, #2563eb)',
};

// Focus trap configuration
export interface FocusTrapConfig {
  container: HTMLElement;
  initialFocus?: HTMLElement;
  restoreFocus?: HTMLElement;
  escapeKey?: () => void;
  onActivate?: () => void;
  onDeactivate?: () => void;
}

// Focus history entry
interface FocusHistoryEntry {
  element: HTMLElement;
  timestamp: number;
}

// Focus management hook
export function useFocusManagement() {
  const { state, setFocusElement, announceToScreenReader } = useAccessibility();
  const focusHistoryRef = useRef<FocusHistoryEntry[]>([]);
  const activeFocusTrapRef = useRef<FocusTrapConfig | null>(null);
  const [focusedElement, setFocusedElement] = useState<HTMLElement | null>(null);

  // Track focus changes
  useEffect(() => {
    const handleFocusIn = (event: FocusEvent) => {
      const element = event.target as HTMLElement;
      setFocusedElement(element);
      setFocusElement(element);
      
      // Add to focus history
      focusHistoryRef.current.push({
        element,
        timestamp: Date.now(),
      });
      
      // Keep only last 50 focus events
      if (focusHistoryRef.current.length > 50) {
        focusHistoryRef.current = focusHistoryRef.current.slice(-50);
      }
      
      // Announce focus change for screen readers if needed
      if (state.preferences.announceChanges && state.preferences.screenReaderOptimized) {
        const role = element.getAttribute('role');
        const label = element.getAttribute('aria-label') || element.textContent || '';
        
        if (role && label) {
          announceToScreenReader(`Focused on ${role}: ${label}`);
        }
      }
    };

    const handleFocusOut = () => {
      setFocusedElement(null);
    };

    document.addEventListener('focusin', handleFocusIn);
    document.addEventListener('focusout', handleFocusOut);

    return () => {
      document.removeEventListener('focusin', handleFocusIn);
      document.removeEventListener('focusout', handleFocusOut);
    };
  }, [state.preferences.announceChanges, state.preferences.screenReaderOptimized, setFocusElement, announceToScreenReader]);

  // Apply focus indicators
  useEffect(() => {
    if (!state.preferences.focusVisible) return;

    const style = document.createElement('style');
    style.id = 'focus-indicators';
    style.textContent = `
      /* Focus indicators for keyboard navigation */
      :focus-visible {
        outline: 2px solid var(--focus-color, #2563eb);
        outline-offset: 2px;
      }
      
      /* High contrast focus indicators */
      .high-contrast :focus-visible {
        outline: 3px solid #ffffff;
        outline-offset: 2px;
        background-color: #000000;
        color: #ffffff;
      }
      
      /* Skip links focus */
      .skip-link:focus {
        top: 6px;
        outline: 2px solid var(--focus-color, #2563eb);
        outline-offset: 2px;
      }
      
      /* Interactive elements focus */
      button:focus-visible,
      input:focus-visible,
      select:focus-visible,
      textarea:focus-visible,
      a:focus-visible,
      [role="button"]:focus-visible,
      [role="link"]:focus-visible,
      [role="menuitem"]:focus-visible,
      [role="option"]:focus-visible,
      [role="tab"]:focus-visible {
        outline: 2px solid var(--focus-color, #2563eb);
        outline-offset: 2px;
        box-shadow: 0 0 0 2px var(--focus-color, #2563eb);
      }
      
      /* Reduced motion focus */
      .reduced-motion *:focus-visible {
        transition: none !important;
      }
      
      /* Large text focus */
      .large-text :focus-visible {
        outline-width: 3px;
        outline-offset: 3px;
      }
    `;

    document.head.appendChild(style);

    return () => {
      const existingStyle = document.getElementById('focus-indicators');
      if (existingStyle) {
        document.head.removeChild(existingStyle);
      }
    };
  }, [state.preferences.focusVisible, state.preferences.highContrast, state.preferences.largeText, state.preferences.reducedMotion]);

  // Focus element programmatically
  const focusElement = useCallback((element: HTMLElement | string, options: {
    scrollIntoView?: boolean;
    preventScroll?: boolean;
    announce?: boolean;
  } = {}) => {
    const { scrollIntoView = true, preventScroll = false, announce = true } = options;
    
    let targetElement: HTMLElement | null = null;
    
    if (typeof element === 'string') {
      targetElement = document.querySelector(element) as HTMLElement;
    } else {
      targetElement = element;
    }
    
    if (!targetElement) {
      console.warn('Element not found for focus:', element);
      return false;
    }
    
    try {
      targetElement.focus({ preventScroll });
      
      if (scrollIntoView && !preventScroll) {
        targetElement.scrollIntoView({
          behavior: state.preferences.reducedMotion ? 'auto' : 'smooth',
          block: 'nearest',
          inline: 'nearest',
        });
      }
      
      if (announce && state.preferences.announceChanges) {
        const label = targetElement.getAttribute('aria-label') || targetElement.textContent || '';
        if (label) {
          announceToScreenReader(`Focused on ${label}`);
        }
      }
      
      return true;
    } catch (error) {
      console.error('Failed to focus element:', error);
      return false;
    }
  }, [state.preferences.reducedMotion, state.preferences.announceChanges, announceToScreenReader]);

  // Create focus trap
  const createFocusTrap = useCallback((config: FocusTrapConfig) => {
    const { container, initialFocus, restoreFocus, escapeKey, onActivate, onDeactivate } = config;
    
    // Store previous focus
    const previousFocus = document.activeElement as HTMLElement;
    
    // Get all focusable elements
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"]), [contenteditable="true"], summary, audio[controls], video[controls], [role="button"], [role="link"], [role="menuitem"], [role="option"], [role="tab"], [role="treeitem"]'
    ) as NodeListOf<HTMLElement>;
    
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];
    
    // Handle keydown events
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        if (event.shiftKey) {
          // Shift + Tab
          if (document.activeElement === firstFocusable) {
            event.preventDefault();
            lastFocusable?.focus();
          }
        } else {
          // Tab
          if (document.activeElement === lastFocusable) {
            event.preventDefault();
            firstFocusable?.focus();
          }
        }
      } else if (event.key === 'Escape' && escapeKey) {
        event.preventDefault();
        escapeKey();
        destroyFocusTrap();
      }
    };
    
    // Activate focus trap
    const activateFocusTrap = () => {
      // Set initial focus
      if (initialFocus) {
        initialFocus.focus();
      } else if (firstFocusable) {
        firstFocusable.focus();
      }
      
      // Add event listener
      container.addEventListener('keydown', handleKeyDown);
      
      // Set active trap
      activeFocusTrapRef.current = config;
      
      // Announce to screen readers
      if (state.preferences.announceChanges) {
        announceToScreenReader('Entered new interactive area');
      }
      
      onActivate?.();
    };
    
    // Destroy focus trap
    const destroyFocusTrap = () => {
      // Remove event listener
      container.removeEventListener('keydown', handleKeyDown);
      
      // Restore focus
      if (restoreFocus) {
        restoreFocus.focus();
      } else if (previousFocus && document.contains(previousFocus)) {
        previousFocus.focus();
      }
      
      // Clear active trap
      activeFocusTrapRef.current = null;
      
      // Announce to screen readers
      if (state.preferences.announceChanges) {
        announceToScreenReader('Exited interactive area');
      }
      
      onDeactivate?.();
    };
    
    // Activate immediately
    activateFocusTrap();
    
    return {
      destroy: destroyFocusTrap,
      update: (newConfig: Partial<FocusTrapConfig>) => {
        Object.assign(config, newConfig);
      },
    };
  }, [state.preferences.announceChanges, announceToScreenReader]);

  // Get focus history
  const getFocusHistory = useCallback(() => {
    return [...focusHistoryRef.current];
  }, []);

  // Clear focus history
  const clearFocusHistory = useCallback(() => {
    focusHistoryRef.current = [];
  }, []);

  // Get last focused element
  const getLastFocusedElement = useCallback(() => {
    const history = focusHistoryRef.current;
    return history.length > 0 ? history[history.length - 1]?.element ?? null : null;
  }, []);

  // Check if element is focused
  const isElementFocused = useCallback((element: HTMLElement) => {
    return document.activeElement === element;
  }, []);

  // Get current focus trap
  const getCurrentFocusTrap = useCallback(() => {
    return activeFocusTrapRef.current;
  }, []);

  return {
    focusedElement,
    focusElement,
    createFocusTrap,
    getFocusHistory,
    clearFocusHistory,
    getLastFocusedElement,
    isElementFocused,
    getCurrentFocusTrap,
  };
}

// Focus indicator component
export interface FocusIndicatorProps {
  children: React.ReactNode;
  styles?: Partial<FocusIndicatorStyles>;
  className?: string;
  disabled?: boolean;
}

export function FocusIndicator({ children, styles, className = '', disabled = false }: FocusIndicatorProps) {
  const { state } = useAccessibility();
  const [isFocused, setIsFocused] = React.useState(false);
  const elementRef = React.useRef<HTMLDivElement>(null);

  const focusStyles = useMemo(() => ({
    ...DEFAULT_FOCUS_STYLES,
    ...styles,
  }), [styles]);

  // Apply focus styles when focused
  useEffect(() => {
    if (!elementRef.current || disabled || !state.preferences.focusVisible) return;

    const element = elementRef.current;
    
    const handleFocus = () => setIsFocused(true);
    const handleBlur = () => setIsFocused(false);

    element.addEventListener('focus', handleFocus);
    element.addEventListener('blur', handleBlur);

    return () => {
      element.removeEventListener('focus', handleFocus);
      element.removeEventListener('blur', handleBlur);
    };
  }, [disabled, state.preferences.focusVisible]);

  // Apply styles to element
  useEffect(() => {
    if (!elementRef.current || disabled || !isFocused) return;

    const element = elementRef.current;
    const toKebabCase = (value: string) => value.replace(/[A-Z]/g, match => `-${match.toLowerCase()}`);
    
    Object.entries(focusStyles).forEach(([property, value]) => {
      if (value) {
        element.style.setProperty(toKebabCase(property), String(value));
      }
    });

    return () => {
      // Clean up styles
      Object.keys(focusStyles).forEach(property => {
        element.style.removeProperty(toKebabCase(property));
      });
    };
  }, [isFocused, focusStyles, disabled]);

  return React.createElement('div', {
    ref: elementRef,
    className: `focus-indicator ${className}`,
    tabIndex: disabled ? -1 : 0,
  }, children);
}

// Focus visible hook
export function useFocusVisible() {
  const [isFocusVisible, setIsFocusVisible] = React.useState(false);
  const { state } = useAccessibility();

  useEffect(() => {
    if (!state.preferences.focusVisible) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab') {
        setIsFocusVisible(true);
      }
    };

    const handleMouseDown = () => {
      setIsFocusVisible(false);
    };

    const handleTouchStart = () => {
      setIsFocusVisible(false);
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('touchstart', handleTouchStart);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('touchstart', handleTouchStart);
    };
  }, [state.preferences.focusVisible]);

  return isFocusVisible;
}

// Focus sentinel component for focus management
export interface FocusSentinelProps {
  onFocus: () => void;
  className?: string;
}

export function FocusSentinel({ onFocus, className = '' }: FocusSentinelProps) {
  const sentinelRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    sentinel.tabIndex = -1;
    sentinel.setAttribute('aria-hidden', 'true');
    sentinel.style.position = 'absolute';
    sentinel.style.left = '-10000px';
    sentinel.style.width = '1px';
    sentinel.style.height = '1px';
    sentinel.style.overflow = 'hidden';
  }, []);

  return React.createElement('div', {
    ref: sentinelRef,
    className: `focus-sentinel ${className}`,
    onFocus,
    tabIndex: -1,
    'aria-hidden': 'true',
  });
}

// Skip links container component
export interface SkipLinksProps {
  links: Array<{
    href: string;
    label: string;
    className?: string;
  }>;
  className?: string;
}

export function SkipLinks({ links, className = '' }: SkipLinksProps) {
  const { state } = useAccessibility();

  if (!state.preferences.skipLinks) return null;

  return React.createElement('div', {
    className: `skip-links ${className}`,
  }, 
    links.map((link, index) => 
      React.createElement('a', {
        key: index,
        href: link.href,
        className: `skip-link ${link.className || ''}`,
        onClick: (e: React.MouseEvent) => {
          e.preventDefault();
          const targetId = link.href.replace('#', '');
          const targetElement = document.getElementById(targetId);
          
          if (targetElement) {
            const focusableElement = targetElement.querySelector(
              'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"]), [contenteditable="true"]'
            ) as HTMLElement;
            
            if (focusableElement) {
              focusableElement.focus();
            } else {
              targetElement.scrollIntoView();
              targetElement.setAttribute('tabindex', '-1');
              targetElement.focus();
              setTimeout(() => {
                targetElement.removeAttribute('tabindex');
              }, 1000);
            }
          }
        },
      }, link.label)
    )
  );
}
