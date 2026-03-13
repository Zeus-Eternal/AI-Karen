/**
 * Screen Reader Compatibility System
 * Comprehensive ARIA management and screen reader optimization for WCAG 2.1 AA compliance
 */

'use client';

import React, { useEffect, useCallback, useRef } from 'react';
import { useAccessibility } from '@/contexts/AccessibilityContext';

// ARIA property interfaces
export interface ARIAProperties {
  // Widget attributes
  'aria-activedescendant'?: string;
  'aria-autocomplete'?: 'inline' | 'list' | 'both' | 'none';
  'aria-busy'?: boolean;
  'aria-checked'?: boolean | 'mixed';
  'aria-current'?: boolean | string;
  'aria-disabled'?: boolean;
  'aria-expanded'?: boolean;
  'aria-grabbed'?: boolean;
  'aria-hidden'?: boolean;
  'aria-invalid'?: boolean | 'grammar' | 'spelling';
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-live'?: 'off' | 'polite' | 'assertive';
  'aria-orientation'?: 'horizontal' | 'vertical';
  'aria-pressed'?: boolean | 'mixed';
  'aria-readonly'?: boolean;
  'aria-required'?: boolean;
  'aria-selected'?: boolean;
  'aria-sort'?: 'none' | 'ascending' | 'descending' | 'other';
  'aria-valuemax'?: number;
  'aria-valuemin'?: number;
  'aria-valuenow'?: number;
  'aria-valuetext'?: string;
  
  // Relationship attributes
  'aria-controls'?: string;
  'aria-describedby'?: string;
  'aria-details'?: string;
  'aria-errormessage'?: string;
  'aria-flowto'?: string;
  'aria-owns'?: string;
  'aria-posinset'?: number;
  'aria-setsize'?: number;
  
  // Live region attributes
  'aria-atomic'?: boolean;
  'aria-relevant'?: 'additions' | 'removals' | 'text' | 'all' | 'additions text';
  
  // Drag and drop attributes
  'aria-dropeffect'?: 'none' | 'copy' | 'move' | 'link' | 'execute' | 'popup' | 'all';
  
  // Widget structure
  'aria-colcount'?: number;
  'aria-colindex'?: number;
  'aria-colspan'?: number;
  'aria-rowcount'?: number;
  'aria-rowindex'?: number;
  'aria-rowspan'?: number;
  'aria-level'?: number;
  'aria-multiselectable'?: boolean;
  'aria-placeholder'?: string;
  'aria-roledescription'?: string;
}

// Screen reader announcement interface
export interface ScreenReaderAnnouncement {
  message: string;
  priority: 'polite' | 'assertive';
  timeout?: number;
  clearPrevious?: boolean;
}

// ARIA role types
export type ARIARole = 
  | 'alert'
  | 'alertdialog'
  | 'application'
  | 'article'
  | 'banner'
  | 'button'
  | 'cell'
  | 'checkbox'
  | 'columnheader'
  | 'combobox'
  | 'complementary'
  | 'contentinfo'
  | 'definition'
  | 'dialog'
  | 'directory'
  | 'document'
  | 'feed'
  | 'figure'
  | 'form'
  | 'grid'
  | 'gridcell'
  | 'group'
  | 'heading'
  | 'img'
  | 'link'
  | 'list'
  | 'listbox'
  | 'listitem'
  | 'log'
  | 'main'
  | 'marquee'
  | 'math'
  | 'menu'
  | 'menubar'
  | 'menuitem'
  | 'menuitemcheckbox'
  | 'menuitemradio'
  | 'navigation'
  | 'none'
  | 'note'
  | 'option'
  | 'presentation'
  | 'progressbar'
  | 'radio'
  | 'radiogroup'
  | 'region'
  | 'row'
  | 'rowgroup'
  | 'rowheader'
  | 'scrollbar'
  | 'search'
  | 'searchbox'
  | 'separator'
  | 'slider'
  | 'spinbutton'
  | 'status'
  | 'switch'
  | 'tab'
  | 'table'
  | 'tablist'
  | 'tabpanel'
  | 'term'
  | 'textbox'
  | 'timer'
  | 'toolbar'
  | 'tooltip'
  | 'tree'
  | 'treegrid'
  | 'treeitem';

// ARIA management hook
export function useARIA() {
  const { state, announceToScreenReader } = useAccessibility();
  const liveRegionRef = useRef<HTMLElement | null>(null);

  // Initialize live regions
  useEffect(() => {
    if (typeof document === 'undefined') return;

    // Create live regions if they don't exist
    if (!liveRegionRef.current) {
      const politeRegion = document.createElement('div');
      politeRegion.setAttribute('aria-live', 'polite');
      politeRegion.setAttribute('aria-atomic', 'true');
      politeRegion.style.position = 'absolute';
      politeRegion.style.left = '-10000px';
      politeRegion.style.width = '1px';
      politeRegion.style.height = '1px';
      politeRegion.style.overflow = 'hidden';
      politeRegion.id = 'screen-reader-polite';

      const assertiveRegion = document.createElement('div');
      assertiveRegion.setAttribute('aria-live', 'assertive');
      assertiveRegion.setAttribute('aria-atomic', 'true');
      assertiveRegion.style.position = 'absolute';
      assertiveRegion.style.left = '-10000px';
      assertiveRegion.style.width = '1px';
      assertiveRegion.style.height = '1px';
      assertiveRegion.style.overflow = 'hidden';
      assertiveRegion.id = 'screen-reader-assertive';

      document.body.appendChild(politeRegion);
      document.body.appendChild(assertiveRegion);

      liveRegionRef.current = politeRegion;
    }

    return () => {
      // Clean up live regions
      const politeRegion = document.getElementById('screen-reader-polite');
      const assertiveRegion = document.getElementById('screen-reader-assertive');
      
      if (politeRegion) document.body.removeChild(politeRegion);
      if (assertiveRegion) document.body.removeChild(assertiveRegion);
    };
  }, []);

  // Announce to screen reader
  const announce = useCallback((announcement: ScreenReaderAnnouncement) => {
    if (!state.preferences.screenReaderOptimized) return;

    const { message, priority = 'polite', timeout = 1000, clearPrevious = false } = announcement;
    
    announceToScreenReader(message, priority);

    // Also use live regions for announcements
    const regionId = priority === 'assertive' ? 'screen-reader-assertive' : 'screen-reader-polite';
    const region = document.getElementById(regionId);
    
    if (region) {
      if (clearPrevious) {
        region.textContent = '';
      }
      
      region.textContent = message;
      
      // Clear after timeout
      if (timeout > 0) {
        setTimeout(() => {
          region.textContent = '';
        }, timeout);
      }
    }
  }, [state.preferences.screenReaderOptimized, announceToScreenReader]);

  // Set ARIA attributes on element
  const setARIA = useCallback((element: HTMLElement, properties: ARIAProperties) => {
    Object.entries(properties).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        element.setAttribute(key, String(value));
      } else {
        element.removeAttribute(key);
      }
    });
  }, []);

  // Remove ARIA attributes from element
  const removeARIA = useCallback((element: HTMLElement, attributes: string[]) => {
    attributes.forEach(attr => {
      element.removeAttribute(attr);
    });
  }, []);

  // Set ARIA role
  const setRole = useCallback((element: HTMLElement, role: ARIARole | null) => {
    if (role) {
      element.setAttribute('role', role);
    } else {
      element.removeAttribute('role');
    }
  }, []);

  // Create accessible label
  const createLabel = useCallback((text: string, options: {
    visual?: boolean;
    ariaLabel?: boolean;
    ariaLabelledby?: string;
  } = {}): { element: HTMLElement; id: string } => {
    const { visual = true, ariaLabel = true, ariaLabelledby } = options;
    
    const id = `label-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const element = document.createElement('span');
    element.id = id;
    element.textContent = text;
    
    if (!visual) {
      element.style.position = 'absolute';
      element.style.left = '-10000px';
      element.style.width = '1px';
      element.style.height = '1px';
      element.style.overflow = 'hidden';
    }
    
    if (ariaLabel && !ariaLabelledby) {
      element.setAttribute('aria-label', text);
    }
    
    return { element, id };
  }, []);

  // Create accessible description
  const createDescription = useCallback((text: string, options: {
    visual?: boolean;
  } = {}): { element: HTMLElement; id: string } => {
    const { visual = true } = options;
    
    const id = `description-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const element = document.createElement('span');
    element.id = id;
    element.textContent = text;
    
    if (!visual) {
      element.style.position = 'absolute';
      element.style.left = '-10000px';
      element.style.width = '1px';
      element.style.height = '1px';
      element.style.overflow = 'hidden';
    }
    
    return { element, id };
  }, []);

  // Mark element as current for screen readers
  const markCurrent = useCallback((element: HTMLElement, isCurrent: boolean = true) => {
    if (isCurrent) {
      element.setAttribute('aria-current', 'true');
      announce({
        message: `${element.textContent || element.getAttribute('aria-label')} is now current`,
        priority: 'polite',
      });
    } else {
      element.removeAttribute('aria-current');
    }
  }, [announce]);

  // Update progress for screen readers
  const updateProgress = useCallback((element: HTMLElement, current: number, total: number, label?: string) => {
    const percentage = Math.round((current / total) * 100);
    
    setARIA(element, {
      'aria-valuenow': current,
      'aria-valuemax': total,
      'aria-valuetext': `${percentage}% complete${label ? ` - ${label}` : ''}`,
    });
    
    announce({
      message: `Progress: ${percentage}% complete${label ? ` - ${label}` : ''}`,
      priority: 'polite',
    });
  }, [setARIA, announce]);

  // Announce list changes
  const announceListChange = useCallback((action: 'add' | 'remove' | 'update', itemText: string, listLength: number) => {
    const messages = {
      add: `Added: ${itemText}. ${listLength} items in list.`,
      remove: `Removed: ${itemText}. ${listLength} items in list.`,
      update: `Updated: ${itemText}. ${listLength} items in list.`,
    };
    
    announce({
      message: messages[action],
      priority: 'polite',
    });
  }, [announce]);

  // Announce status changes
  const announceStatusChange = useCallback((status: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    const priority = type === 'error' ? 'assertive' : 'polite';
    
    announce({
      message: `Status: ${status}`,
      priority,
    });
  }, [announce]);

  // Create accessible table headers
  const createTableHeaders = useCallback((headers: string[]) => {
    return headers.map((header, index) => ({
      id: `header-${index}`,
      text: header,
      scope: 'col' as const,
      ariaLabel: header,
    }));
  }, []);

  // Create accessible tree structure
  const createTreeItem = useCallback((
    label: string,
    level: number,
    expanded: boolean = false,
    hasChildren: boolean = false
  ) => {
    const id = `tree-item-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      id,
      label,
      level,
      expanded,
      hasChildren,
      ariaAttributes: {
        'aria-level': level,
        'aria-expanded': hasChildren ? expanded : undefined,
        'aria-selected': false,
        role: 'treeitem',
      } as ARIAProperties,
    };
  }, []);

  return {
    announce,
    setARIA,
    removeARIA,
    setRole,
    createLabel,
    createDescription,
    markCurrent,
    updateProgress,
    announceListChange,
    announceStatusChange,
    createTableHeaders,
    createTreeItem,
  };
}

// Screen reader detection hook
export function useScreenReaderDetection() {
  const [isScreenReaderActive, setIsScreenReaderActive] = React.useState(false);
  const { updatePreferences } = useAccessibility();

  useEffect(() => {
    // Detect screen reader using various methods
    const detectScreenReader = () => {
      // Method 1: Check for speech synthesis
      if ('speechSynthesis' in window) {
        const synth = window.speechSynthesis;
        if (synth.getVoices().length > 0) {
          setIsScreenReaderActive(true);
          updatePreferences({ screenReaderOptimized: true });
          return;
        }
      }

      // Method 2: Check for common screen reader indicators
      const hasScreenReaderIndicator =
        document.querySelector('[aria-live]') !== null ||
        document.querySelector('.sr-only') !== null ||
        document.querySelector('.visually-hidden') !== null;

      if (hasScreenReaderIndicator) {
        setIsScreenReaderActive(true);
        updatePreferences({ screenReaderOptimized: true });
        return;
      }

      // Method 3: Check for reduced motion preference (often used with screen readers)
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReducedMotion) {
        setIsScreenReaderActive(true);
        updatePreferences({ screenReaderOptimized: true });
        return;
      }

      // Method 4: Check for high contrast preference
      const prefersHighContrast = window.matchMedia('(prefers-contrast: high)').matches;
      if (prefersHighContrast) {
        setIsScreenReaderActive(true);
        updatePreferences({ screenReaderOptimized: true });
        return;
      }
    };

    // Initial detection
    detectScreenReader();

    // Listen for voice changes
    if ('speechSynthesis' in window) {
      const handleVoicesChanged = () => {
        detectScreenReader();
      };
      
      window.speechSynthesis.addEventListener('voiceschanged', handleVoicesChanged);
      
      return () => {
        window.speechSynthesis.removeEventListener('voiceschanged', handleVoicesChanged);
      };
    }
    
    // Return a cleanup function for the case when speechSynthesis is not available
    return () => {};
  }, [updatePreferences]);

  return isScreenReaderActive;
}

// Accessible component props
export interface AccessibleComponentProps {
  // ARIA properties
  aria?: ARIAProperties;
  role?: ARIARole;
  
  // Label and description
  label?: string;
  labelledBy?: string;
  describedBy?: string;
  
  // Screen reader only content
  screenReaderOnly?: boolean;
  
  // Live region
  live?: 'off' | 'polite' | 'assertive';
  atomic?: boolean;
  relevant?: 'additions' | 'removals' | 'text' | 'all' | 'additions text';
  
  // Focus management
  tabIndex?: number;
  focusable?: boolean;
  
  // State
  current?: boolean;
  busy?: boolean;
  disabled?: boolean;
  invalid?: boolean;
  required?: boolean;
  selected?: boolean;
  expanded?: boolean;
  pressed?: boolean | 'mixed';
  checked?: boolean | 'mixed';
  
  // Value
  valueMin?: number;
  valueMax?: number;
  valueNow?: number;
  valueText?: string;
  
  // Other
  hidden?: boolean;
}

// Hook to apply accessibility props to elements
export function useAccessibleProps(props: AccessibleComponentProps) {
  const { setARIA, setRole } = useARIA();
  const elementRef = React.useRef<HTMLElement>(null);

  // Apply accessibility props to element
  const applyProps = useCallback((element: HTMLElement) => {
    if (!element) return;

    // Set role
    if (props.role) {
      setRole(element, props.role);
    }

    // Set ARIA properties
    const ariaProps: ARIAProperties = {
      ...props.aria,
    };

    // Map common props to ARIA attributes
    if (props.label) ariaProps['aria-label'] = props.label;
    if (props.labelledBy) ariaProps['aria-labelledby'] = props.labelledBy;
    if (props.describedBy) ariaProps['aria-describedby'] = props.describedBy;
    if (props.live) ariaProps['aria-live'] = props.live;
    if (props.atomic) ariaProps['aria-atomic'] = props.atomic;
    if (props.relevant) ariaProps['aria-relevant'] = props.relevant;
    if (props.current !== undefined) ariaProps['aria-current'] = props.current;
    if (props.busy !== undefined) ariaProps['aria-busy'] = props.busy;
    if (props.disabled !== undefined) ariaProps['aria-disabled'] = props.disabled;
    if (props.invalid !== undefined) ariaProps['aria-invalid'] = props.invalid;
    if (props.required !== undefined) ariaProps['aria-required'] = props.required;
    if (props.selected !== undefined) ariaProps['aria-selected'] = props.selected;
    if (props.expanded !== undefined) ariaProps['aria-expanded'] = props.expanded;
    if (props.pressed !== undefined) ariaProps['aria-pressed'] = props.pressed;
    if (props.checked !== undefined) ariaProps['aria-checked'] = props.checked;
    if (props.valueMin !== undefined) ariaProps['aria-valuemin'] = props.valueMin;
    if (props.valueMax !== undefined) ariaProps['aria-valuemax'] = props.valueMax;
    if (props.valueNow !== undefined) ariaProps['aria-valuenow'] = props.valueNow;
    if (props.valueText) ariaProps['aria-valuetext'] = props.valueText;
    if (props.hidden !== undefined) ariaProps['aria-hidden'] = props.hidden;

    setARIA(element, ariaProps);

    // Set tabindex
    if (props.tabIndex !== undefined) {
      element.tabIndex = props.tabIndex;
    } else if (props.focusable === false) {
      element.tabIndex = -1;
    }

    // Screen reader only styling
    if (props.screenReaderOnly) {
      element.style.position = 'absolute';
      element.style.left = '-10000px';
      element.style.width = '1px';
      element.style.height = '1px';
      element.style.overflow = 'hidden';
      element.style.clip = 'rect(0, 0, 0, 0)';
      element.style.whiteSpace = 'nowrap';
    }

    if (elementRef) {
      (elementRef as React.MutableRefObject<HTMLElement | null>).current = element;
    }
  }, [props, setARIA, setRole]);

  return {
    elementRef,
    applyProps,
  };
}