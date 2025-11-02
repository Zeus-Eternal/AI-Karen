/**
 * ARIA Helpers and Accessibility Utilities
 * 
 * Utilities for implementing ARIA attributes and accessibility features
 * following WCAG guidelines.
 * 
 * Requirements: 7.7
 */

import React from 'react';

export interface AriaLiveRegionOptions {
  politeness?: 'polite' | 'assertive' | 'off';
  atomic?: boolean;
  relevant?: 'additions' | 'removals' | 'text' | 'all';
  busy?: boolean;
}

export interface AriaDescriptionOptions {
  id?: string;
  description: string;
  element?: HTMLElement;
}

export class AriaManager {
  private static liveRegionCounter = 0;
  private static liveRegions = new Map<string, HTMLElement>();

  // Create and manage live regions for screen reader announcements
  static createLiveRegion(options: AriaLiveRegionOptions = {}): string {
    const id = `aria-live-region-${++this.liveRegionCounter}`;
    const region = document.createElement('div');
    
    region.id = id;
    region.setAttribute('aria-live', options.politeness || 'polite');
    region.setAttribute('aria-atomic', String(options.atomic !== false));
    
    if (options.relevant) {
      region.setAttribute('aria-relevant', options.relevant);
    }
    
    if (options.busy !== undefined) {
      region.setAttribute('aria-busy', String(options.busy));
    }

    // Hide visually but keep accessible to screen readers
    region.className = 'sr-only';
    region.style.cssText = `
      position: absolute !important;
      width: 1px !important;
      height: 1px !important;
      padding: 0 !important;
      margin: -1px !important;
      overflow: hidden !important;
      clip: rect(0, 0, 0, 0) !important;
      white-space: nowrap !important;
      border: 0 !important;
    `;

    document.body.appendChild(region);
    this.liveRegions.set(id, region);
    
    return id;
  }

  // Announce message to screen readers
  static announce(message: string, regionId?: string, priority: 'polite' | 'assertive' = 'polite'): void {
    let region: HTMLElement | undefined;

    if (regionId) {
      region = this.liveRegions.get(regionId);
    }

    if (!region) {
      // Create temporary region for this announcement
      const tempId = this.createLiveRegion({ politeness: priority });
      region = this.liveRegions.get(tempId);
    }

    if (region) {
      // Clear previous content
      region.textContent = '';
      
      // Add new message after a brief delay to ensure screen readers pick it up
      setTimeout(() => {
        region!.textContent = message;
      }, 100);

      // Clean up temporary regions
      if (!regionId) {
        setTimeout(() => {
          this.removeLiveRegion(region!.id);
        }, 2000);
      }
    }
  }

  // Remove a live region
  static removeLiveRegion(regionId: string): void {
    const region = this.liveRegions.get(regionId);
    if (region && region.parentNode) {
      region.parentNode.removeChild(region);
      this.liveRegions.delete(regionId);
    }
  }

  // Create describedby relationship
  static createDescription(options: AriaDescriptionOptions): string {
    const id = options.id || `aria-description-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    let descriptionElement = document.getElementById(id);
    if (!descriptionElement) {
      descriptionElement = document.createElement('div');
      descriptionElement.id = id;
      descriptionElement.className = 'sr-only';
      descriptionElement.textContent = options.description;
      document.body.appendChild(descriptionElement);
    } else {
      descriptionElement.textContent = options.description;
    }

    if (options.element) {
      const existingDescribedBy = options.element.getAttribute('aria-describedby');
      const describedByIds = existingDescribedBy ? existingDescribedBy.split(' ') : [];
      
      if (!describedByIds.includes(id)) {
        describedByIds.push(id);
        options.element.setAttribute('aria-describedby', describedByIds.join(' '));
      }
    }

    return id;
  }

  // Remove description
  static removeDescription(descriptionId: string, element?: HTMLElement): void {
    const descriptionElement = document.getElementById(descriptionId);
    if (descriptionElement && descriptionElement.parentNode) {
      descriptionElement.parentNode.removeChild(descriptionElement);
    }

    if (element) {
      const describedBy = element.getAttribute('aria-describedby');
      if (describedBy) {
        const ids = describedBy.split(' ').filter(id => id !== descriptionId);
        if (ids.length > 0) {
          element.setAttribute('aria-describedby', ids.join(' '));
        } else {
          element.removeAttribute('aria-describedby');
        }
      }
    }
  }

  // Set loading state with appropriate ARIA attributes
  static setLoadingState(element: HTMLElement, loading: boolean, loadingText = 'Loading...'): void {
    if (loading) {
      element.setAttribute('aria-busy', 'true');
      element.setAttribute('aria-live', 'polite');
      
      // Add loading text for screen readers if element is empty
      if (!element.textContent?.trim()) {
        element.setAttribute('aria-label', loadingText);
      }
    } else {
      element.removeAttribute('aria-busy');
      element.removeAttribute('aria-live');
      
      // Remove loading label if it was added
      if (element.getAttribute('aria-label') === loadingText) {
        element.removeAttribute('aria-label');
      }
    }
  }

  // Set expanded state for collapsible elements
  static setExpandedState(trigger: HTMLElement, expanded: boolean, targetId?: string): void {
    trigger.setAttribute('aria-expanded', String(expanded));
    
    if (targetId) {
      trigger.setAttribute('aria-controls', targetId);
      const target = document.getElementById(targetId);
      if (target) {
        target.setAttribute('aria-hidden', String(!expanded));
      }
    }
  }

  // Set selected state for selectable items
  static setSelectedState(element: HTMLElement, selected: boolean): void {
    element.setAttribute('aria-selected', String(selected));
    
    // Update tabindex for roving tabindex pattern
    element.setAttribute('tabindex', selected ? '0' : '-1');
  }

  // Set pressed state for toggle buttons
  static setPressedState(button: HTMLElement, pressed: boolean): void {
    button.setAttribute('aria-pressed', String(pressed));
  }

  // Create error message association
  static associateErrorMessage(input: HTMLElement, errorMessage: string, errorId?: string): string {
    const id = errorId || `error-${input.id || Date.now()}`;
    
    let errorElement = document.getElementById(id);
    if (!errorElement) {
      errorElement = document.createElement('div');
      errorElement.id = id;
      errorElement.className = 'error-message';
      errorElement.setAttribute('role', 'alert');
      errorElement.setAttribute('aria-live', 'polite');
    }
    
    errorElement.textContent = errorMessage;
    
    // Insert error element after the input
    if (!errorElement.parentNode) {
      input.parentNode?.insertBefore(errorElement, input.nextSibling);
    }

    // Associate with input
    input.setAttribute('aria-describedby', id);
    input.setAttribute('aria-invalid', 'true');

    return id;
  }

  // Clear error message association
  static clearErrorMessage(input: HTMLElement, errorId: string): void {
    const errorElement = document.getElementById(errorId);
    if (errorElement && errorElement.parentNode) {
      errorElement.parentNode.removeChild(errorElement);
    }

    input.removeAttribute('aria-describedby');
    input.removeAttribute('aria-invalid');
  }

  // Create progress announcement
  static announceProgress(current: number, total: number, operation: string): void {
    const percentage = Math.round((current / total) * 100);
    const message = `${operation} progress: ${current} of ${total} items completed (${percentage}%)`;
    this.announce(message, undefined, 'polite');
  }

  // Announce bulk operation results
  static announceBulkOperationResult(
    operation: string,
    successful: number,
    failed: number,
    total: number
  ): void {
    let message = `${operation} completed. `;
    
    if (failed === 0) {
      message += `All ${total} items processed successfully.`;
    } else {
      message += `${successful} items processed successfully, ${failed} items failed.`;
    }

    this.announce(message, undefined, 'assertive');
  }
}

// React hooks for accessibility
export function useAriaLiveRegion(options: AriaLiveRegionOptions = {}) {
  const [regionId, setRegionId] = React.useState<string | null>(null);

  React.useEffect(() => {
    const id = AriaManager.createLiveRegion(options);
    setRegionId(id);

    return () => {
      AriaManager.removeLiveRegion(id);
    };
  }, []);

  const announce = React.useCallback((message: string, priority?: 'polite' | 'assertive') => {
    if (regionId) {
      AriaManager.announce(message, regionId, priority);
    }
  }, [regionId]);

  return { announce };
}

export function useAriaDescription(description: string, elementRef: React.RefObject<HTMLElement>) {
  const [descriptionId, setDescriptionId] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (elementRef.current && description) {
      const id = AriaManager.createDescription({
        description,
        element: elementRef.current

      setDescriptionId(id);

      return () => {
        AriaManager.removeDescription(id, elementRef.current || undefined);
      };
    }
  }, [description, elementRef]);

  return descriptionId;
}

export function useLoadingState(elementRef: React.RefObject<HTMLElement>, loading: boolean, loadingText?: string) {
  React.useEffect(() => {
    if (elementRef.current) {
      AriaManager.setLoadingState(elementRef.current, loading, loadingText);
    }
  }, [loading, loadingText, elementRef]);
}

// Utility functions for common accessibility patterns
export const AccessibilityUtils = {
  // Generate unique IDs for form associations
  generateId: (prefix = 'element'): string => {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  },

  // Check if element is visible to screen readers
  isVisibleToScreenReaders: (element: HTMLElement): boolean => {
    const style = window.getComputedStyle(element);
    return !(
      element.hasAttribute('aria-hidden') ||
      style.display === 'none' ||
      style.visibility === 'hidden' ||
      element.hasAttribute('hidden')
    );
  },

  // Get accessible name for an element
  getAccessibleName: (element: HTMLElement): string => {
    // Check aria-label first
    const ariaLabel = element.getAttribute('aria-label');
    if (ariaLabel) return ariaLabel;

    // Check aria-labelledby
    const labelledBy = element.getAttribute('aria-labelledby');
    if (labelledBy) {
      const labelElement = document.getElementById(labelledBy);
      if (labelElement) return labelElement.textContent || '';
    }

    // Check associated label
    if (element.id) {
      const label = document.querySelector(`label[for="${element.id}"]`);
      if (label) return label.textContent || '';
    }

    // Check if element is inside a label
    const parentLabel = element.closest('label');
    if (parentLabel) return parentLabel.textContent || '';

    // Fall back to element text content
    return element.textContent || '';
  },

  // Validate accessibility of form fields
  validateFormAccessibility: (form: HTMLFormElement): string[] => {
    const issues: string[] = [];
    const inputs = form.querySelectorAll('input, select, textarea');

    inputs.forEach((input) => {
      const element = input as HTMLElement;
      const accessibleName = AccessibilityUtils.getAccessibleName(element);
      
      if (!accessibleName.trim()) {
        issues.push(`Form field missing accessible name: ${element.tagName.toLowerCase()}${element.id ? `#${element.id}` : ''}`);
      }

      if (element.hasAttribute('required') && !element.hasAttribute('aria-required')) {
        issues.push(`Required field missing aria-required: ${element.id || element.tagName.toLowerCase()}`);
      }

    return issues;
  },

  // Create skip link for keyboard navigation
  createSkipLink: (targetId: string, text = 'Skip to main content'): HTMLElement => {
    const skipLink = document.createElement('a');
    skipLink.href = `#${targetId}`;
    skipLink.textContent = text;
    skipLink.className = 'skip-link';
    skipLink.style.cssText = `
      position: absolute;
      top: -40px;
      left: 6px;
      background: #000;
      color: #fff;
      padding: 8px;
      text-decoration: none;
      z-index: 1000;
      border-radius: 4px;
    `;

    // Show on focus
    skipLink.addEventListener('focus', () => {
      skipLink.style.top = '6px';

    skipLink.addEventListener('blur', () => {
      skipLink.style.top = '-40px';

    return skipLink;
  }
};

export default AriaManager;