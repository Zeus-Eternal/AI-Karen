import * as React from 'react';

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
      });

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
