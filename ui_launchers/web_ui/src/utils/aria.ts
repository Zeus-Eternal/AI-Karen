/**
 * ARIA Utilities for Enhanced Accessibility
 * Provides comprehensive ARIA attribute management and utilities
 */

export interface AriaLabelProps {
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
}

export interface AriaStateProps {
  'aria-expanded'?: boolean;
  'aria-selected'?: boolean;
  'aria-checked'?: boolean | 'mixed';
  'aria-pressed'?: boolean;
  'aria-current'?: boolean | 'page' | 'step' | 'location' | 'date' | 'time';
  'aria-disabled'?: boolean;
  'aria-hidden'?: boolean;
  'aria-busy'?: boolean;
  'aria-invalid'?: boolean | 'grammar' | 'spelling';
  'aria-required'?: boolean;
  'aria-haspopup'?: boolean | 'menu' | 'listbox' | 'tree' | 'grid' | 'dialog';
}

export interface AriaRelationshipProps {
  'aria-owns'?: string;
  'aria-controls'?: string;
  'aria-activedescendant'?: string;
  'aria-flowto'?: string;
  'aria-details'?: string;
}

export interface AriaLiveProps {
  'aria-live'?: 'off' | 'polite' | 'assertive';
  'aria-atomic'?: boolean;
  'aria-relevant'?: 'additions' | 'removals' | 'text' | 'all' | 'additions text' | 'additions removals' | 'text removals' | 'additions text removals';
}

export interface AriaGridProps {
  'aria-rowcount'?: number;
  'aria-colcount'?: number;
  'aria-rowindex'?: number;
  'aria-colindex'?: number;
  'aria-rowspan'?: number;
  'aria-colspan'?: number;
}

export type AriaProps = AriaLabelProps & 
  AriaStateProps & 
  AriaRelationshipProps & 
  AriaLiveProps & 
  AriaGridProps & {
    role?: string;
    tabIndex?: number;
  };

/**
 * Generate unique IDs for ARIA relationships
 */
let idCounter = 0;
export const generateAriaId = (prefix: string = 'aria'): string => {
  return `${prefix}-${++idCounter}-${Date.now()}`;
};

/**
 * Create ARIA label attributes with fallback logic
 */
export const createAriaLabel = (
  label?: string,
  labelledBy?: string,
  describedBy?: string
): AriaLabelProps => {
  const props: AriaLabelProps = {};
  
  if (labelledBy) {
    props['aria-labelledby'] = labelledBy;
  } else if (label) {
    props['aria-label'] = label;
  }
  
  if (describedBy) {
    props['aria-describedby'] = describedBy;
  }
  
  return props;
};

/**
 * Create ARIA live region attributes
 */
export const createAriaLive = (
  level: 'off' | 'polite' | 'assertive' = 'polite',
  atomic: boolean = false,
  relevant: 'additions' | 'removals' | 'text' | 'all' | 'additions text' | 'additions removals' | 'text removals' | 'additions text removals' = 'additions text'
): AriaLiveProps => ({
  'aria-live': level,
  'aria-atomic': atomic,
  'aria-relevant': relevant,
});

/**
 * Create ARIA attributes for interactive elements
 */
export const createInteractiveAria = (
  expanded?: boolean,
  selected?: boolean,
  pressed?: boolean,
  current?: boolean | 'page' | 'step' | 'location' | 'date' | 'time',
  disabled?: boolean
): AriaStateProps => {
  const props: AriaStateProps = {};
  
  if (expanded !== undefined) props['aria-expanded'] = expanded;
  if (selected !== undefined) props['aria-selected'] = selected;
  if (pressed !== undefined) props['aria-pressed'] = pressed;
  if (current !== undefined) props['aria-current'] = current;
  if (disabled !== undefined) props['aria-disabled'] = disabled;
  
  return props;
};

/**
 * Create ARIA attributes for form elements
 */
export const createFormAria = (
  invalid?: boolean | 'grammar' | 'spelling',
  required?: boolean,
  describedBy?: string,
  errorId?: string
): AriaStateProps & AriaLabelProps => {
  const props: AriaStateProps & AriaLabelProps = {};
  
  if (invalid !== undefined) props['aria-invalid'] = invalid;
  if (required !== undefined) props['aria-required'] = required;
  
  if (invalid && errorId) {
    props['aria-describedby'] = describedBy ? `${describedBy} ${errorId}` : errorId;
  } else if (describedBy) {
    props['aria-describedby'] = describedBy;
  }
  
  return props;
};

/**
 * Create ARIA attributes for grid/table elements
 */
export const createGridAria = (
  rowIndex?: number,
  colIndex?: number,
  rowSpan?: number,
  colSpan?: number,
  rowCount?: number,
  colCount?: number
): AriaGridProps => {
  const props: AriaGridProps = {};
  
  if (rowIndex !== undefined) props['aria-rowindex'] = rowIndex;
  if (colIndex !== undefined) props['aria-colindex'] = colIndex;
  if (rowSpan !== undefined) props['aria-rowspan'] = rowSpan;
  if (colSpan !== undefined) props['aria-colspan'] = colSpan;
  if (rowCount !== undefined) props['aria-rowcount'] = rowCount;
  if (colCount !== undefined) props['aria-colcount'] = colCount;
  
  return props;
};

/**
 * Create ARIA attributes for navigation elements
 */
export const createNavigationAria = (
  current?: boolean | 'page' | 'step' | 'location' | 'date' | 'time',
  expanded?: boolean,
  hasPopup?: boolean | 'menu' | 'listbox' | 'tree' | 'grid' | 'dialog'
): AriaStateProps & { 'aria-haspopup'?: boolean | string } => {
  const props: AriaStateProps & { 'aria-haspopup'?: boolean | string } = {};
  
  if (current !== undefined) props['aria-current'] = current;
  if (expanded !== undefined) props['aria-expanded'] = expanded;
  if (hasPopup !== undefined) props['aria-haspopup'] = hasPopup;
  
  return props;
};

/**
 * Create ARIA attributes for modal/dialog elements
 */
export const createModalAria = (
  labelledBy?: string,
  describedBy?: string,
  modal: boolean = true
): AriaLabelProps & { 'aria-modal'?: boolean } => ({
  ...createAriaLabel(undefined, labelledBy, describedBy),
  'aria-modal': modal,
});

/**
 * Create ARIA attributes for loading states
 */
export const createLoadingAria = (
  busy: boolean = true,
  label: string = 'Loading...',
  live: 'polite' | 'assertive' = 'polite'
): AriaStateProps & AriaLiveProps & AriaLabelProps => ({
  'aria-busy': busy,
  'aria-label': label,
  'aria-live': live,
});

/**
 * Merge multiple ARIA prop objects
 */
export const mergeAriaProps = (...ariaProps: (AriaProps | undefined)[]): AriaProps => {
  return ariaProps.reduce((merged: AriaProps, props) => {
    if (!props) return merged;
    return { ...merged, ...props };
  }, {} as AriaProps);
};

/**
 * Validate ARIA attributes for common issues
 */
export const validateAriaProps = (props: AriaProps): string[] => {
  const warnings: string[] = [];
  
  // Check for conflicting label attributes
  if (props['aria-label'] && props['aria-labelledby']) {
    warnings.push('Both aria-label and aria-labelledby are present. aria-labelledby takes precedence.');
  }
  
  // Check for invalid role combinations
  if (props.role === 'button' && props['aria-pressed'] === undefined && props['aria-expanded'] === undefined) {
    // This is fine for regular buttons
  }
  
  // Check for missing required attributes
  if (props.role === 'tab' && props['aria-selected'] === undefined) {
    warnings.push('Tab role requires aria-selected attribute.');
  }
  
  if (props.role === 'tabpanel' && !props['aria-labelledby']) {
    warnings.push('Tabpanel role should have aria-labelledby pointing to the associated tab.');
  }
  
  return warnings;
};

/**
 * Common ARIA role constants
 */
export const ARIA_ROLES = {
  // Landmark roles
  BANNER: 'banner',
  MAIN: 'main',
  NAVIGATION: 'navigation',
  COMPLEMENTARY: 'complementary',
  CONTENTINFO: 'contentinfo',
  SEARCH: 'search',
  REGION: 'region',
  
  // Widget roles
  BUTTON: 'button',
  CHECKBOX: 'checkbox',
  RADIO: 'radio',
  SLIDER: 'slider',
  SPINBUTTON: 'spinbutton',
  TEXTBOX: 'textbox',
  COMBOBOX: 'combobox',
  LISTBOX: 'listbox',
  OPTION: 'option',
  TAB: 'tab',
  TABPANEL: 'tabpanel',
  TABLIST: 'tablist',
  MENU: 'menu',
  MENUITEM: 'menuitem',
  MENUBAR: 'menubar',
  TREE: 'tree',
  TREEITEM: 'treeitem',
  GRID: 'grid',
  GRIDCELL: 'gridcell',
  ROW: 'row',
  COLUMNHEADER: 'columnheader',
  ROWHEADER: 'rowheader',
  
  // Document structure roles
  ARTICLE: 'article',
  DOCUMENT: 'document',
  HEADING: 'heading',
  LIST: 'list',
  LISTITEM: 'listitem',
  TABLE: 'table',
  
  // Live region roles
  ALERT: 'alert',
  ALERTDIALOG: 'alertdialog',
  LOG: 'log',
  MARQUEE: 'marquee',
  STATUS: 'status',
  TIMER: 'timer',
  
  // Window roles
  DIALOG: 'dialog',
  TOOLTIP: 'tooltip',
} as const;

export type AriaRole = typeof ARIA_ROLES[keyof typeof ARIA_ROLES];
