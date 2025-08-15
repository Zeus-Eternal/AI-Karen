import { useCallback, useEffect, useRef } from 'react';
import { useTelemetry } from './use-telemetry';

export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  metaKey?: boolean;
  action: () => void;
  description: string;
  preventDefault?: boolean;
}

export interface KeyboardNavigationOptions {
  shortcuts?: KeyboardShortcut[];
  trapFocus?: boolean;
  autoFocus?: boolean;
  onEscape?: () => void;
  onEnter?: () => void;
  onTab?: (direction: 'forward' | 'backward') => void;
}

export const useKeyboardNavigation = (options: KeyboardNavigationOptions = {}) => {
  const { track } = useTelemetry();
  const containerRef = useRef<HTMLElement>(null);
  const focusableElementsRef = useRef<HTMLElement[]>([]);
  const currentFocusIndexRef = useRef<number>(-1);

  // Get all focusable elements within the container
  const getFocusableElements = useCallback((): HTMLElement[] => {
    if (!containerRef.current) return [];

    const focusableSelectors = [
      'button:not([disabled])',
      'input:not([disabled])',
      'textarea:not([disabled])',
      'select:not([disabled])',
      'a[href]',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]'
    ].join(', ');

    const elements = Array.from(
      containerRef.current.querySelectorAll(focusableSelectors)
    ) as HTMLElement[];

    return elements.filter(element => {
      const style = window.getComputedStyle(element);
      return style.display !== 'none' && style.visibility !== 'hidden';
    });
  }, []);

  // Update focusable elements list
  const updateFocusableElements = useCallback(() => {
    focusableElementsRef.current = getFocusableElements();
  }, [getFocusableElements]);

  // Focus management
  const focusElement = useCallback((index: number) => {
    const elements = focusableElementsRef.current;
    if (index >= 0 && index < elements.length) {
      elements[index].focus();
      currentFocusIndexRef.current = index;
      track('keyboard_navigation_focus', { elementIndex: index, elementType: elements[index].tagName });
    }
  }, [track]);

  const focusFirst = useCallback(() => {
    updateFocusableElements();
    focusElement(0);
  }, [updateFocusableElements, focusElement]);

  const focusLast = useCallback(() => {
    updateFocusableElements();
    const elements = focusableElementsRef.current;
    focusElement(elements.length - 1);
  }, [updateFocusableElements, focusElement]);

  const focusNext = useCallback(() => {
    updateFocusableElements();
    const elements = focusableElementsRef.current;
    const currentIndex = elements.indexOf(document.activeElement as HTMLElement);
    const nextIndex = currentIndex < elements.length - 1 ? currentIndex + 1 : 0;
    focusElement(nextIndex);
  }, [updateFocusableElements, focusElement]);

  const focusPrevious = useCallback(() => {
    updateFocusableElements();
    const elements = focusableElementsRef.current;
    const currentIndex = elements.indexOf(document.activeElement as HTMLElement);
    const prevIndex = currentIndex > 0 ? currentIndex - 1 : elements.length - 1;
    focusElement(prevIndex);
  }, [updateFocusableElements, focusElement]);

  // Handle keyboard events
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const { key, ctrlKey, shiftKey, altKey, metaKey } = event;

    // Handle custom shortcuts
    if (options.shortcuts) {
      for (const shortcut of options.shortcuts) {
        const keyMatches = shortcut.key.toLowerCase() === key.toLowerCase();
        const ctrlMatches = (shortcut.ctrlKey ?? false) === ctrlKey;
        const shiftMatches = (shortcut.shiftKey ?? false) === shiftKey;
        const altMatches = (shortcut.altKey ?? false) === altKey;
        const metaMatches = (shortcut.metaKey ?? false) === metaKey;

        if (keyMatches && ctrlMatches && shiftMatches && altMatches && metaMatches) {
          if (shortcut.preventDefault !== false) {
            event.preventDefault();
          }
          shortcut.action();
          track('keyboard_shortcut_used', { 
            shortcut: shortcut.key,
            description: shortcut.description 
          });
          return;
        }
      }
    }

    // Handle built-in navigation
    switch (key) {
      case 'Escape':
        if (options.onEscape) {
          event.preventDefault();
          options.onEscape();
          track('keyboard_navigation_escape');
        }
        break;

      case 'Enter':
        if (options.onEnter && !shiftKey) {
          event.preventDefault();
          options.onEnter();
          track('keyboard_navigation_enter');
        }
        break;

      case 'Tab':
        if (options.trapFocus) {
          event.preventDefault();
          if (shiftKey) {
            focusPrevious();
            options.onTab?.('backward');
          } else {
            focusNext();
            options.onTab?.('forward');
          }
          track('keyboard_navigation_tab', { direction: shiftKey ? 'backward' : 'forward' });
        }
        break;

      case 'ArrowDown':
        if (ctrlKey || altKey) {
          event.preventDefault();
          focusNext();
          track('keyboard_navigation_arrow', { direction: 'down' });
        }
        break;

      case 'ArrowUp':
        if (ctrlKey || altKey) {
          event.preventDefault();
          focusPrevious();
          track('keyboard_navigation_arrow', { direction: 'up' });
        }
        break;

      case 'Home':
        if (ctrlKey) {
          event.preventDefault();
          focusFirst();
          track('keyboard_navigation_home');
        }
        break;

      case 'End':
        if (ctrlKey) {
          event.preventDefault();
          focusLast();
          track('keyboard_navigation_end');
        }
        break;
    }
  }, [options, focusNext, focusPrevious, focusFirst, focusLast, track]);

  // Setup event listeners
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('keydown', handleKeyDown);
    
    // Auto-focus first element if requested
    if (options.autoFocus) {
      const timer = setTimeout(() => {
        focusFirst();
      }, 100);
      return () => {
        clearTimeout(timer);
        container.removeEventListener('keydown', handleKeyDown);
      };
    }

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown, options.autoFocus, focusFirst]);

  // Update focusable elements when container changes
  useEffect(() => {
    updateFocusableElements();
  }, [updateFocusableElements]);

  return {
    containerRef,
    focusFirst,
    focusLast,
    focusNext,
    focusPrevious,
    focusElement,
    updateFocusableElements,
    getFocusableElements
  };
};

// Common keyboard shortcuts for chat interface
export const createChatKeyboardShortcuts = (actions: {
  onSend?: () => void;
  onClear?: () => void;
  onAbort?: () => void;
  onFocusInput?: () => void;
  onToggleVoice?: () => void;
  onScrollToTop?: () => void;
  onScrollToBottom?: () => void;
}): KeyboardShortcut[] => [
  {
    key: 'Enter',
    action: actions.onSend || (() => {}),
    description: 'Send message'
  },
  {
    key: 'Escape',
    action: actions.onAbort || (() => {}),
    description: 'Cancel current operation'
  },
  {
    key: 'k',
    ctrlKey: true,
    action: actions.onClear || (() => {}),
    description: 'Clear conversation'
  },
  {
    key: '/',
    ctrlKey: true,
    action: actions.onFocusInput || (() => {}),
    description: 'Focus message input'
  },
  {
    key: 'm',
    ctrlKey: true,
    action: actions.onToggleVoice || (() => {}),
    description: 'Toggle voice input'
  },
  {
    key: 'Home',
    ctrlKey: true,
    action: actions.onScrollToTop || (() => {}),
    description: 'Scroll to top of conversation'
  },
  {
    key: 'End',
    ctrlKey: true,
    action: actions.onScrollToBottom || (() => {}),
    description: 'Scroll to bottom of conversation'
  }
];