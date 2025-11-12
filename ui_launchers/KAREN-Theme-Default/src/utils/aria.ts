/**
 * ARIA Utilities for Enhanced Accessibility
 * ----------------------------------------
 * Strongly-typed helpers to compose, validate, and merge ARIA props.
 * - Framework-agnostic TypeScript, React-friendly value shapes
 * - SSR-safe (no DOM access at import time)
 * - Opinionated validations for common pitfalls
 */

import type { AriaAttributes } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AriaRelevant = NonNullable<AriaAttributes['aria-relevant']>;

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

export type AriaRelevantValue = NonNullable<AriaAttributes['aria-relevant']>;
export type ExtendedAriaRelevantValue =
  | AriaRelevantValue
  | 'additions text removals';

export interface AriaLiveProps {
  'aria-live'?: 'off' | 'polite' | 'assertive';
  'aria-atomic'?: boolean;
  'aria-relevant'?: AriaRelevant;
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

// ---------------------------------------------------------------------------
// ID utilities (SSR-safe)
// ---------------------------------------------------------------------------

let __ariaIdCounter = 0;
/** Generate unique-ish IDs for ARIA relationships */
export const generateAriaId = (prefix: string = 'aria'): string => {
  // Math.random added to reduce collisions across islands/tests
  __ariaIdCounter += 1;
  const rand = Math.random().toString(36).slice(2, 7);
  return `${prefix}-${__ariaIdCounter}-${rand}`;
};

/** Join a list of id strings into a space-separated value */
export const joinIds = (...ids: Array<string | undefined | null>): string | undefined => {
  const list = ids.filter(Boolean).map((s) => String(s).trim()).filter(Boolean);
  return list.length ? Array.from(new Set(list)).join(' ') : undefined;
};

// ---------------------------------------------------------------------------
// Factories
// ---------------------------------------------------------------------------

/** Create ARIA label attributes with proper precedence */
export const createAriaLabel = (
  label?: string,
  labelledBy?: string,
  describedBy?: string
): AriaLabelProps => {
  const props: AriaLabelProps = {};
  if (labelledBy) props['aria-labelledby'] = labelledBy;
  else if (label) props['aria-label'] = label;
  if (describedBy) props['aria-describedby'] = describedBy;
  return props;
};

/** Create ARIA live region attributes */
export const createAriaLive = (
  level: 'off' | 'polite' | 'assertive' = 'polite',
  atomic: boolean = false,
  relevant: AriaRelevant = 'additions text'
): AriaLiveProps => ({
  'aria-live': level,
  'aria-atomic': atomic,
  'aria-relevant': relevant,
});

/** Create ARIA attributes for interactive elements */
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

/** Create ARIA attributes for form elements */
export const createFormAria = (
  invalid?: boolean | 'grammar' | 'spelling',
  required?: boolean,
  describedBy?: string,
  errorId?: string
): AriaStateProps & AriaLabelProps => {
  const props: AriaStateProps & AriaLabelProps = {} as AriaStateProps & AriaLabelProps;
  if (invalid !== undefined) props['aria-invalid'] = invalid;
  if (required !== undefined) props['aria-required'] = required;

  const composedDescribedBy = invalid && errorId ? joinIds(describedBy, errorId) : describedBy;
  if (composedDescribedBy) props['aria-describedby'] = composedDescribedBy;
  return props;
};

/** Create ARIA attributes for grid/table elements */
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

/** Create ARIA attributes for navigation elements */
export const createNavigationAria = (
  current?: boolean | 'page' | 'step' | 'location' | 'date' | 'time',
  expanded?: boolean,
  hasPopup?: boolean | 'menu' | 'listbox' | 'tree' | 'grid' | 'dialog'
): AriaStateProps => {
  const props: AriaStateProps = {};
  if (current !== undefined) props['aria-current'] = current;
  if (expanded !== undefined) props['aria-expanded'] = expanded;
  if (hasPopup !== undefined) props['aria-haspopup'] = hasPopup;
  return props;
};

/** Create ARIA attributes for modal/dialog elements */
export const createModalAria = (
  labelledBy?: string,
  describedBy?: string,
  modal: boolean = true
): AriaLabelProps & { 'aria-modal'?: boolean } => ({
  ...createAriaLabel(undefined, labelledBy, describedBy),
  'aria-modal': modal,
});

/** Create ARIA attributes for loading states */
export const createLoadingAria = (
  busy: boolean = true,
  label: string = 'Loading...',
  live: 'polite' | 'assertive' = 'polite'
): AriaStateProps & AriaLiveProps & AriaLabelProps => ({
  'aria-busy': busy,
  'aria-label': label,
  'aria-live': live,
});

// ---------------------------------------------------------------------------
// Merge & Normalize
// ---------------------------------------------------------------------------

/**
 * Merge multiple ARIA prop objects. Later objects win on key conflicts.
 * `aria-describedby` and `aria-labelledby` are concatenated intelligently.
 */
export const mergeAriaProps = (
  ...ariaProps: Array<AriaProps | undefined>
): AriaProps => {
  const merged: AriaProps = {};
  for (const props of ariaProps) {
    if (!props) continue;

    // Merge concatenated references safely
    const nextDescribedBy = joinIds(merged['aria-describedby'], props['aria-describedby']);
    const nextLabelledBy = joinIds(merged['aria-labelledby'], props['aria-labelledby']);

    Object.assign(merged, props);

    if (nextDescribedBy) merged['aria-describedby'] = nextDescribedBy;
    if (nextLabelledBy) merged['aria-labelledby'] = nextLabelledBy;
  }
  return merged;
};

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

/** Minimal role requirements map (non-exhaustive, pragmatic) */
const ROLE_REQUIREMENTS: Record<string, Array<keyof AriaProps>> = {
  tab: ['aria-selected'],
  tabpanel: ['aria-labelledby'],
  tooltip: ['aria-describedby'],
};

/** Suggested companions for certain attributes */
const SUGGESTED_COMPANIONS: Array<(p: AriaProps) => string | null> = [
  (p) => (p['aria-haspopup'] && p.role === 'button' && p['aria-expanded'] === undefined
    ? 'Button with aria-haspopup should usually reflect disclosure state via aria-expanded.'
    : null),
  (p) => (typeof p['aria-current'] !== 'undefined' && !['a', 'link', 'button', 'tab']
    .includes((p.role || '').toLowerCase())
    ? 'aria-current is typically used on navigational items (links, tabs, menu items). Ensure role is appropriate.'
    : null),
];

/**
 * Validate ARIA attributes for common issues. Returns an array of warnings.
 */
export const validateAriaProps = (props: AriaProps): string[] => {
  const warnings: string[] = [];

  // 1) Conflicting label sources
  if (props['aria-label'] && props['aria-labelledby']) {
    warnings.push('Both aria-label and aria-labelledby present. aria-labelledby takes precedence. Prefer one.');
  }

  // 2) Role-based required attributes
  if (props.role) {
    const role = props.role.toLowerCase();
    const required = ROLE_REQUIREMENTS[role];
    if (required) {
      required.forEach((k) => {
        if (props[k] === undefined || props[k] === null || props[k] === '') {
          warnings.push(`Role "${role}" should include attribute "${k}".`);
        }
      });
    }
  }

  // 3) State value sanity checks
  if (typeof props['aria-pressed'] !== 'undefined' && props.role && props.role !== 'button') {
    warnings.push('aria-pressed is generally used with role="button" (toggle button).');
  }

  if (props['aria-checked'] === 'mixed' && props.role && !['checkbox', 'menuitemcheckbox', 'treeitem']
    .includes(props.role)) {
    warnings.push('aria-checked="mixed" is usually for tri-state controls like checkbox or treeitem.');
  }

  // 4) Relationship integrity (simple string checks; DOM presence validated elsewhere)
  const idListRegex = /^[A-Za-z][\w\-:.]*(?:\s+[A-Za-z][\w\-:.]*)*$/;
  ['aria-labelledby', 'aria-describedby', 'aria-controls', 'aria-owns', 'aria-activedescendant']
    .forEach((attr) => {
      const v = props[attr as keyof AriaProps];
      if (typeof v === 'string' && v.trim() && !idListRegex.test(v.trim())) {
        warnings.push(`${attr} should be a space-separated list of valid IDs.`);
      }
    });

  // 5) Suggested companions
  SUGGESTED_COMPANIONS.forEach((fn) => {
    const msg = fn(props);
    if (msg) warnings.push(msg);
  });

  return warnings;
};

// ---------------------------------------------------------------------------
// Role constants
// ---------------------------------------------------------------------------

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
