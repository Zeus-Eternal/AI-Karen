'use client';

import * as React from 'react';

export interface KeyboardNavigationOptions {
  enableArrowKeys?: boolean;
  enableTabTrapping?: boolean;
  enableEscapeKey?: boolean;
  enableEnterKey?: boolean;
  enableHomeEndKeys?: boolean;
  focusableSelector?: string;
  onEscape?: () => void;
  onEnter?: (element: HTMLElement) => void;
  onArrowUp?: (currentElement: HTMLElement, previousElement?: HTMLElement) => void;
  onArrowDown?: (currentElement: HTMLElement, nextElement?: HTMLElement) => void;
  onArrowLeft?: (currentElement: HTMLElement, previousElement?: HTMLElement) => void;
  onArrowRight?: (currentElement: HTMLElement, nextElement?: HTMLElement) => void;
  onHome?: (firstElement: HTMLElement) => void;
  onEnd?: (lastElement: HTMLElement) => void;
}

export class KeyboardNavigationManager {
  private container: HTMLElement;
  private options: KeyboardNavigationOptions;
  private focusableElements: HTMLElement[] = [];
  private currentFocusIndex = -1;
  private keydownHandler: (event: KeyboardEvent) => void;

  constructor(container: HTMLElement, options: KeyboardNavigationOptions = {}) {
    this.container = container;
    this.options = {
      enableArrowKeys: true,
      enableTabTrapping: false,
      enableEscapeKey: true,
      enableEnterKey: true,
      enableHomeEndKeys: true,
      focusableSelector: 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      ...options
    };

    this.keydownHandler = this.handleKeyDown.bind(this);
    this.updateFocusableElements();
    this.attachEventListeners();
  }

  private updateFocusableElements(): void {
    const elements = this.container.querySelectorAll(this.options.focusableSelector!);
    this.focusableElements = Array.from(elements).filter(
      (element) => !element.hasAttribute('disabled') && 
                   element.getAttribute('tabindex') !== '-1'
    ) as HTMLElement[];
  }

  private getCurrentFocusIndex(): number {
    const activeElement = document.activeElement as HTMLElement;
    return this.focusableElements.indexOf(activeElement);
  }

  private focusElement(index: number): void {
    if (index >= 0 && index < this.focusableElements.length) {
      this.focusableElements[index].focus();
      this.currentFocusIndex = index;
    }
  }

  private handleKeyDown(event: KeyboardEvent): void {
    if (!this.container.contains(document.activeElement as Node)) {
      return;
    }

    this.updateFocusableElements();
    this.currentFocusIndex = this.getCurrentFocusIndex();

    switch (event.key) {
      case 'Escape':
        if (this.options.enableEscapeKey && this.options.onEscape) {
          event.preventDefault();
          this.options.onEscape();
        }
        break;

      case 'Enter':
        if (this.options.enableEnterKey && this.options.onEnter) {
          event.preventDefault();
          this.options.onEnter(document.activeElement as HTMLElement);
        }
        break;

      case 'ArrowUp':
        if (this.options.enableArrowKeys) {
          event.preventDefault();
          const prevIndex = this.currentFocusIndex > 0 ? this.currentFocusIndex - 1 : this.focusableElements.length - 1;
          if (this.options.onArrowUp) {
            this.options.onArrowUp(
              this.focusableElements[this.currentFocusIndex],
              this.focusableElements[prevIndex]
            );
          } else {
            this.focusElement(prevIndex);
          }
        }
        break;

      case 'ArrowDown':
        if (this.options.enableArrowKeys) {
          event.preventDefault();
          const nextIndex = this.currentFocusIndex < this.focusableElements.length - 1 ? this.currentFocusIndex + 1 : 0;
          if (this.options.onArrowDown) {
            this.options.onArrowDown(
              this.focusableElements[this.currentFocusIndex],
              this.focusableElements[nextIndex]
            );
          } else {
            this.focusElement(nextIndex);
          }
        }
        break;

      case 'ArrowLeft':
        if (this.options.enableArrowKeys && this.options.onArrowLeft) {
          event.preventDefault();
          const prevIndex = this.currentFocusIndex > 0 ? this.currentFocusIndex - 1 : this.focusableElements.length - 1;
          this.options.onArrowLeft(
            this.focusableElements[this.currentFocusIndex],
            this.focusableElements[prevIndex]
          );
        }
        break;

      case 'ArrowRight':
        if (this.options.enableArrowKeys && this.options.onArrowRight) {
          event.preventDefault();
          const nextIndex = this.currentFocusIndex < this.focusableElements.length - 1 ? this.currentFocusIndex + 1 : 0;
          this.options.onArrowRight(
            this.focusableElements[this.currentFocusIndex],
            this.focusableElements[nextIndex]
          );
        }
        break;

      case 'Home':
        if (this.options.enableHomeEndKeys) {
          event.preventDefault();
          if (this.options.onHome) {
            this.options.onHome(this.focusableElements[0]);
          } else {
            this.focusElement(0);
          }
        }
        break;

      case 'End':
        if (this.options.enableHomeEndKeys) {
          event.preventDefault();
          const lastIndex = this.focusableElements.length - 1;
          if (this.options.onEnd) {
            this.options.onEnd(this.focusableElements[lastIndex]);
          } else {
            this.focusElement(lastIndex);
          }
        }
        break;

      case 'Tab':
        if (this.options.enableTabTrapping) {
          event.preventDefault();
          if (event.shiftKey) {
            // Shift+Tab - go to previous element
            const prevIndex = this.currentFocusIndex > 0 ? this.currentFocusIndex - 1 : this.focusableElements.length - 1;
            this.focusElement(prevIndex);
          } else {
            // Tab - go to next element
            const nextIndex = this.currentFocusIndex < this.focusableElements.length - 1 ? this.currentFocusIndex + 1 : 0;
            this.focusElement(nextIndex);
          }
        }
        break;
    }
  }

  private attachEventListeners(): void {
    this.container.addEventListener('keydown', this.keydownHandler);
  }

  public destroy(): void {
    this.container.removeEventListener('keydown', this.keydownHandler);
  }

  public focusFirst(): void {
    this.updateFocusableElements();
    this.focusElement(0);
  }

  public focusLast(): void {
    this.updateFocusableElements();
    this.focusElement(this.focusableElements.length - 1);
  }

  public refresh(): void {
    this.updateFocusableElements();
  }
}

// React hook for keyboard navigation
export function useKeyboardNavigation(
  containerRef: React.RefObject<HTMLElement>,
  options: KeyboardNavigationOptions = {}
) {
  const managerRef = React.useRef<KeyboardNavigationManager | null>(null);

  React.useEffect(() => {
    if (containerRef.current) {
      managerRef.current = new KeyboardNavigationManager(containerRef.current, options);
      
      return () => {
        if (managerRef.current) {
          managerRef.current.destroy();
        }
      };
    }
  }, [containerRef, options]);

  const focusFirst = React.useCallback(() => {
    managerRef.current?.focusFirst();
  }, []);

  const focusLast = React.useCallback(() => {
    managerRef.current?.focusLast();
  }, []);

  const refresh = React.useCallback(() => {
    managerRef.current?.refresh();
  }, []);

  return { focusFirst, focusLast, refresh };
}

// Utility functions for common keyboard navigation patterns
export const KeyboardUtils = {
  // Trap focus within a container
  trapFocus(container: HTMLElement): () => void {
    const manager = new KeyboardNavigationManager(container, {
      enableTabTrapping: true,
      enableArrowKeys: false
    });

    return () => manager.destroy();
  },

  // Create a roving tabindex pattern for lists/grids
  createRovingTabindex(container: HTMLElement, itemSelector: string): () => void {
    const items = container.querySelectorAll(itemSelector) as NodeListOf<HTMLElement>;
    let currentIndex = 0;

    // Set initial tabindex values
    items.forEach((item, index) => {
      item.setAttribute('tabindex', index === 0 ? '0' : '-1');
    });

    const handleKeyDown = (event: KeyboardEvent) => {
      if (!container.contains(event.target as Node)) return;

      let newIndex = currentIndex;

      switch (event.key) {
        case 'ArrowDown':
        case 'ArrowRight':
          event.preventDefault();
          newIndex = (currentIndex + 1) % items.length;
          break;
        case 'ArrowUp':
        case 'ArrowLeft':
          event.preventDefault();
          newIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
          break;
        case 'Home':
          event.preventDefault();
          newIndex = 0;
          break;
        case 'End':
          event.preventDefault();
          newIndex = items.length - 1;
          break;
        default:
          return;
      }

      // Update tabindex values
      items[currentIndex].setAttribute('tabindex', '-1');
      items[newIndex].setAttribute('tabindex', '0');
      items[newIndex].focus();
      currentIndex = newIndex;
    };

    const handleClick = (event: Event) => {
      const clickedItem = (event.target as HTMLElement).closest(itemSelector) as HTMLElement;
      if (clickedItem && container.contains(clickedItem)) {
        const newIndex = Array.from(items).indexOf(clickedItem);
        if (newIndex !== -1) {
          items[currentIndex].setAttribute('tabindex', '-1');
          items[newIndex].setAttribute('tabindex', '0');
          currentIndex = newIndex;
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    container.addEventListener('click', handleClick);

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
      container.removeEventListener('click', handleClick);
    };
  },

  // Announce changes to screen readers
  announceToScreenReader(message: string, priority: 'polite' | 'assertive' = 'polite'): void {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  },

  // Focus management for modals/dialogs
  manageFocusForModal(modal: HTMLElement): () => void {
    const previouslyFocused = document.activeElement as HTMLElement;
    
    // Focus the modal or first focusable element
    const firstFocusable = modal.querySelector(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as HTMLElement;
    
    if (firstFocusable) {
      firstFocusable.focus();
    } else {
      modal.focus();
    }

    // Trap focus within modal
    const cleanup = KeyboardUtils.trapFocus(modal);

    return () => {
      cleanup();
      // Restore focus to previously focused element
      if (previouslyFocused && document.body.contains(previouslyFocused)) {
        previouslyFocused.focus();
      }
    };
  }
};

export default KeyboardNavigationManager;
