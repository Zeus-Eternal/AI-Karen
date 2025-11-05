"use client";

import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { useKeyboardNavigation } from '../../hooks/use-keyboard-navigation';

interface KeyboardNavigationContextValue {
  // Navigation state
  currentFocusIndex: number;
  totalItems: number;
  
  // Navigation methods
  moveNext: () => void;
  movePrevious: () => void;
  moveFirst: () => void;
  moveLast: () => void;
  moveTo: (index: number) => void;
  
  // Registration methods
  registerNavigationContainer: (element: HTMLElement) => (() => void) | void;
  unregisterNavigationContainer: () => void;
  
  // Settings
  enabled: boolean;
  setEnabled: (enabled: boolean) => void;
}

const KeyboardNavigationContext = createContext<KeyboardNavigationContextValue | undefined>(undefined);

interface KeyboardNavigationProviderProps {
  children: React.ReactNode;
  enabled?: boolean;
  loop?: boolean;
  orientation?: 'horizontal' | 'vertical' | 'both';
}

export function KeyboardNavigationProvider({
  children,
  enabled: initialEnabled = true,
  loop = true,
  orientation = 'vertical',
}: KeyboardNavigationProviderProps) {
  const [enabled, setEnabled] = useState(initialEnabled);
  const [itemCount, setItemCount] = useState(0);
  const containerRef = useRef<HTMLElement | null>(null);

  const {
    activeIndex,
    moveNext,
    movePrevious,
    moveFirst,
    moveLast,
    setActiveIndex,
  } = useKeyboardNavigation(itemCount, {
    enabled,
    loop,
    orientation,
    onActiveChange: (index) => {
      // Announce navigation changes to screen readers
      if (enabled && containerRef.current) {
        const items = containerRef.current.querySelectorAll('[role="option"], [role="menuitem"], [role="tab"], [role="gridcell"], [data-keyboard-nav-item]');
        const currentItem = items[index] as HTMLElement;
        if (currentItem) {
          const label = currentItem.getAttribute('aria-label') || 
                       currentItem.textContent || 
                       `Item ${index + 1}`;
          
          // Create a temporary announcement
          const announcement = document.createElement('div');
          announcement.setAttribute('aria-live', 'polite');
          announcement.setAttribute('aria-atomic', 'true');
          announcement.className = 'sr-only';
          announcement.textContent = `${label}, ${index + 1} of ${itemCount}`;
          
          document.body.appendChild(announcement);
          setTimeout(() => {
            document.body.removeChild(announcement);
          }, 1000);
        }
      }
    },
  });

  const registerNavigationContainer = React.useCallback((element: HTMLElement) => {
    containerRef.current = element;
    
    // Count navigable items
    const updateItemCount = () => {
      if (element) {
        const items = element.querySelectorAll('[role="option"], [role="menuitem"], [role="tab"], [role="gridcell"], [data-keyboard-nav-item]');
        setItemCount(items.length);
      }
    };

    updateItemCount();

    // Set up mutation observer to track changes
    const observer = new MutationObserver(updateItemCount);
    observer.observe(element, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['role', 'data-keyboard-nav-item'],
    });

    return () => {
      observer.disconnect();
    };
  }, []);

  const unregisterNavigationContainer = React.useCallback(() => {
    containerRef.current = null;
    setItemCount(0);
  }, []);

  const contextValue: KeyboardNavigationContextValue = {
    currentFocusIndex: activeIndex,
    totalItems: itemCount,
    moveNext,
    movePrevious,
    moveFirst,
    moveLast,
    moveTo: setActiveIndex,
    registerNavigationContainer,
    unregisterNavigationContainer,
    enabled,
    setEnabled,
  };

  return (
    <KeyboardNavigationContext.Provider value={contextValue}>
      {children}
    </KeyboardNavigationContext.Provider>
  );
}

export function useKeyboardNavigationContext() {
  const context = useContext(KeyboardNavigationContext);
  if (context === undefined) {
    throw new Error('useKeyboardNavigationContext must be used within a KeyboardNavigationProvider');
  }
  return context;
}

// Hook for registering navigation containers
export function useNavigationContainer() {
  const { registerNavigationContainer, unregisterNavigationContainer } = useKeyboardNavigationContext();
  const containerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const element = containerRef.current;
    if (element) {
      const cleanup = registerNavigationContainer(element);
      return () => {
        if (typeof cleanup === 'function') {
          cleanup();
        }
        unregisterNavigationContainer();
      };
    }
  }, [registerNavigationContainer, unregisterNavigationContainer]);

  return containerRef;
}

// Hook for navigation items
export function useNavigationItem(index: number) {
  const { currentFocusIndex, moveTo } = useKeyboardNavigationContext();
  const isActive = currentFocusIndex === index;

  const itemProps = {
    'data-keyboard-nav-item': true,
    'data-nav-index': index,
    tabIndex: isActive ? 0 : -1,
    onClick: () => moveTo(index),
    onFocus: () => moveTo(index),
  };

  return {
    isActive,
    itemProps,
  };
}

export default KeyboardNavigationProvider;
