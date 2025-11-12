"use client";

import React, { useCallback, useRef, useState } from 'react';
import { useKeyboardNavigation } from '../../hooks/use-keyboard-navigation';
import { KeyboardNavigationContext, type KeyboardNavigationContextValue } from './KeyboardNavigationContext';

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
    }
  });

  const registerNavigationContainer = useCallback((element: HTMLElement) => {
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

  const unregisterNavigationContainer = useCallback(() => {
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

export default KeyboardNavigationProvider;
