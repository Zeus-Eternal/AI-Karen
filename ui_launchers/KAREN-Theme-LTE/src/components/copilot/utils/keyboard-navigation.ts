import { useRef, useEffect } from 'react';

/**
 * Keyboard Navigation Utilities for CoPilot Components
 *
 * This file provides utilities and hooks for implementing comprehensive
 * keyboard navigation support in compliance with WCAG 2.1 AA guidelines.
 */

/**
 * Keyboard navigation keys
 */
export const KeyboardKeys = {
  TAB: 'Tab',
  ENTER: 'Enter',
  SPACE: ' ',
  ESCAPE: 'Escape',
  ARROW_UP: 'ArrowUp',
  ARROW_DOWN: 'ArrowDown',
  ARROW_LEFT: 'ArrowLeft',
  ARROW_RIGHT: 'ArrowRight',
  HOME: 'Home',
  END: 'End',
  PAGE_UP: 'PageUp',
  PAGE_DOWN: 'PageDown',
  FOCUS_FIRST: 'a', // Shortcut to focus first interactive element
  FOCUS_LAST: 'z', // Shortcut to focus last interactive element
  SEARCH: 'f', // Shortcut to open search
  HELP: '?', // Shortcut to open help
} as const;

/**
 * Keyboard event modifier keys
 */
export const ModifierKeys = {
  ALT: 'Alt',
  CONTROL: 'Control',
  SHIFT: 'Shift',
  META: 'Meta', // Command key on Mac, Windows key on Windows
} as const;

/**
 * Creates a keyboard event handler with common patterns
 */
export const createKeyboardHandler = (
  keyMap: Record<string, (e: KeyboardEvent) => void>,
  options: {
    preventDefault?: boolean;
    stopPropagation?: boolean;
    requireModifiers?: string[];
  } = {}
) => {
  const {
    preventDefault = true,
    stopPropagation = false,
    requireModifiers = []
  } = options;

  return (e: KeyboardEvent) => {
    const key = e.key;

    // Check if required modifiers are pressed
    const modifiersPressed = requireModifiers.every(modifier =>
      e.getModifierState(modifier as 'Alt' | 'Control' | 'Shift' | 'Meta')
    );

    if (key in keyMap && modifiersPressed) {
      if (preventDefault) {
        e.preventDefault();
      }

      if (stopPropagation) {
        e.stopPropagation();
      }

      const handler = keyMap[key];
      if (handler) {
        handler(e);
      }
    }
  };
};

/**
 * Creates a React keyboard event handler with common patterns
 */
export const createReactKeyboardHandler = (
  keyMap: Record<string, (e: React.KeyboardEvent) => void>,
  options: {
    preventDefault?: boolean;
    stopPropagation?: boolean;
    requireModifiers?: string[];
  } = {}
) => {
  const {
    preventDefault = true,
    stopPropagation = false,
    requireModifiers = []
  } = options;

  return (e: React.KeyboardEvent) => {
    const key = e.key;

    // Check if required modifiers are pressed
    const modifiersPressed = requireModifiers.every(modifier =>
      e.getModifierState(modifier as 'Alt' | 'Control' | 'Shift' | 'Meta')
    );

    if (key in keyMap && modifiersPressed) {
      if (preventDefault) {
        e.preventDefault();
      }

      if (stopPropagation) {
        e.stopPropagation();
      }

      const handler = keyMap[key];
      if (handler) {
        handler(e);
      }
    }
  };
};

/**
 * Trap focus within a container element
 */
export const trapFocus = (container: HTMLElement) => {
  const focusableElements = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  ) as NodeListOf<HTMLElement>;

  if (focusableElements.length === 0) return;

  const firstElement = focusableElements[0] ?? null;
  const lastElement = focusableElements[focusableElements.length - 1] ?? null;

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key !== KeyboardKeys.TAB) return;

    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        e.preventDefault();
        lastElement?.focus();
      }
    } else {
      if (document.activeElement === lastElement) {
        e.preventDefault();
        firstElement?.focus();
      }
    }
  };

  container.addEventListener('keydown', handleKeyDown);

  // Return a function to remove the event listener
  return () => {
    container.removeEventListener('keydown', handleKeyDown);
  };
};

/**
 * Announce to screen readers
 */
export const announceToScreenReader = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.style.position = 'absolute';
  announcement.style.left = '-10000px';
  announcement.style.width = '1px';
  announcement.style.height = '1px';
  announcement.style.overflow = 'hidden';
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

/**
 * Set up roving tabindex for keyboard navigation in a list
 */
export const setupRovingTabindex = (
  container: HTMLElement,
  options: {
    orientation?: 'horizontal' | 'vertical';
    loop?: boolean;
    initialIndex?: number;
  } = {}
) => {
  const {
    orientation = 'vertical',
    loop = true,
    initialIndex = 0
  } = options;
  
  const focusableElements = container.querySelectorAll(
    '[role="option"], [role="listitem"], [role="menuitem"], [role="tab"]'
  ) as NodeListOf<HTMLElement>;
  
  if (focusableElements.length === 0) return;
  
  let currentIndex = initialIndex;
  
  // Set initial tabindex
  focusableElements.forEach((el, index) => {
    el.setAttribute('tabindex', index === currentIndex ? '0' : '-1');
  });
  
  const handleKeyDown = (e: KeyboardEvent) => {
    const isVerticalKey = e.key === KeyboardKeys.ARROW_DOWN || e.key === KeyboardKeys.ARROW_UP;
    const isHorizontalKey = e.key === KeyboardKeys.ARROW_RIGHT || e.key === KeyboardKeys.ARROW_LEFT;
    
    if ((orientation === 'vertical' && isVerticalKey) || 
        (orientation === 'horizontal' && isHorizontalKey)) {
      e.preventDefault();
      
      const isNextKey = orientation === 'vertical' 
        ? e.key === KeyboardKeys.ARROW_DOWN 
        : e.key === KeyboardKeys.ARROW_RIGHT;
        
      let newIndex;
      if (isNextKey) {
        newIndex = currentIndex + 1;
        if (newIndex >= focusableElements.length) {
          newIndex = loop ? 0 : currentIndex;
        }
      } else {
        newIndex = currentIndex - 1;
        if (newIndex < 0) {
          newIndex = loop ? focusableElements.length - 1 : currentIndex;
        }
      }
      
      // Update tabindex and focus
      const currentElement = focusableElements[currentIndex];
      const newElement = focusableElements[newIndex];
      if (currentElement) {
        currentElement.setAttribute('tabindex', '-1');
      }
      if (newElement) {
        newElement.setAttribute('tabindex', '0');
        newElement.focus();
      }
      currentIndex = newIndex;
    }
  };
  
  container.addEventListener('keydown', handleKeyDown);
  
  // Return a function to remove the event listener
  return () => {
    container.removeEventListener('keydown', handleKeyDown);
  };
};

/**
 * Add keyboard navigation instructions to a container
 */
export const addKeyboardInstructions = (container: HTMLElement, instructions: string) => {
  const instructionsElement = document.createElement('div');
  instructionsElement.id = 'keyboard-instructions';
  instructionsElement.className = 'sr-only';
  instructionsElement.textContent = instructions;
  instructionsElement.style.display = 'none';
  
  container.setAttribute('aria-describedby', instructionsElement.id);
  container.appendChild(instructionsElement);
  
  // Return a function to remove the instructions
  return () => {
    container.removeAttribute('aria-describedby');
    container.removeChild(instructionsElement);
  };
};

/**
 * Hook for managing keyboard focus
 */
export const useKeyboardFocus = () => {
  const lastFocusedElementRef = useRef<HTMLElement | null>(null);
  
  const saveFocus = () => {
    lastFocusedElementRef.current = document.activeElement as HTMLElement;
  };
  
  const restoreFocus = () => {
    if (lastFocusedElementRef.current) {
      lastFocusedElementRef.current.focus();
    }
  };
  
  return { saveFocus, restoreFocus };
};

/**
 * Hook for keyboard shortcuts
 */
export const useKeyboardShortcuts = (
  shortcuts: Array<{
    keys: string[];
    modifiers?: string[];
    callback: (e: KeyboardEvent) => void;
    description: string;
  }>
) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger shortcuts when user is typing in input fields
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement
      ) {
        return;
      }
      
      for (const shortcut of shortcuts) {
        const { keys, modifiers = [], callback } = shortcut;
        
        // Check if the pressed key matches
        const keyMatch = keys.includes(e.key);
        
        // Check if all required modifiers are pressed
        const modifiersMatch = modifiers.every(modifier =>
          e.getModifierState(modifier as 'Alt' | 'Control' | 'Shift' | 'Meta')
        );
        
        // Check if no extra modifiers are pressed
        const noExtraModifiers = Object.values(ModifierKeys)
          .filter(mod => !modifiers.includes(mod))
          .every(mod => !e.getModifierState(mod));
        
        if (keyMatch && modifiersMatch && noExtraModifiers) {
          e.preventDefault();
          callback(e);
          break;
        }
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [shortcuts]);
};