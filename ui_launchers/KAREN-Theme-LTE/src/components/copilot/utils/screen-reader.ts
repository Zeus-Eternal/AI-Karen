/**
 * Screen Reader Utilities for CoPilot Components
 * 
 * This file provides utilities for improving screen reader compatibility
 * in compliance with WCAG 2.1 AA guidelines.
 */

/**
 * Screen reader announcement priorities
 */
export type AnnouncementPriority = 'polite' | 'assertive';

/**
 * Screen reader region roles
 */
export const ScreenReaderRoles = {
  ALERT: 'alert',
  STATUS: 'status',
  LOG: 'log',
  MARQUEE: 'marquee',
  TIMER: 'timer',
  APPLICATION: 'application',
  ARTICLE: 'article',
  BANNER: 'banner',
  COMPLEMENTARY: 'complementary',
  CONTENTINFO: 'contentinfo',
  DEFINITION: 'definition',
  DIALOG: 'dialog',
  DIRECTORY: 'directory',
  DOCUMENT: 'document',
  FEED: 'feed',
  FIGURE: 'figure',
  FORM: 'form',
  GROUP: 'group',
  HEADING: 'heading',
  IMG: 'img',
  LIST: 'list',
  LISTITEM: 'listitem',
  MAIN: 'main',
  NAVIGATION: 'navigation',
  NOTE: 'note',
  PRESENTATION: 'presentation',
  REGION: 'region',
  ROW: 'row',
  ROWGROUP: 'rowgroup',
  ROWHEADER: 'rowheader',
  SEARCH: 'search',
  SEPARATOR: 'separator',
  TABLE: 'table',
  TEXTBOX: 'textbox',
  CELL: 'cell',
  COLUMNHEADER: 'columnheader',
  GRID: 'grid',
  GRIDCELL: 'gridcell',
  LINK: 'link',
  LISTBOX: 'listbox',
  OPTION: 'option',
  PROGRESSBAR: 'progressbar',
  RADIOGROUP: 'radiogroup',
  SCROLLBAR: 'scrollbar',
  SEARCHBOX: 'searchbox',
  SLIDER: 'slider',
  SPINBUTTON: 'spinbutton',
  SWITCH: 'switch',
  TAB: 'tab',
  TABLIST: 'tablist',
  TABPANEL: 'tabpanel',
  TOOLBAR: 'toolbar',
  TOOLTIP: 'tooltip',
  TREE: 'tree',
  TREEGRID: 'treegrid',
  TREEITEM: 'treeitem'
} as const;

/**
 * Screen reader states and properties
 */
export const ScreenReaderStates = {
  ATOMIC: 'aria-atomic',
  BUSY: 'aria-busy',
  CHECKED: 'aria-checked',
  DISABLED: 'aria-disabled',
  EXPANDED: 'aria-expanded',
  GRABBED: 'aria-grabbed',
  HIDDEN: 'aria-hidden',
  INVALID: 'aria-invalid',
  PRESSED: 'aria-pressed',
  SELECTED: 'aria-selected'
} as const;

/**
 * Screen reader properties
 */
export const ScreenReaderProperties = {
  ACTDESCENDANT: 'aria-activedescendant',
  ATOMIC: 'aria-atomic',
  AUTOCOMPLETE: 'aria-autocomplete',
  BUSY: 'aria-busy',
  CHECKED: 'aria-checked',
  CONTROLS: 'aria-controls',
  DESCRIBEDBY: 'aria-describedby',
  DISABLED: 'aria-disabled',
  DROPEFFECT: 'aria-dropeffect',
  EXPANDED: 'aria-expanded',
  FLOWTO: 'aria-flowto',
  GRABBED: 'aria-grabbed',
  HASPOPUP: 'aria-haspopup',
  HIDDEN: 'aria-hidden',
  INVALID: 'aria-invalid',
  LABEL: 'aria-label',
  LABELLEDBY: 'aria-labelledby',
  LEVEL: 'aria-level',
  LIVE: 'aria-live',
  MODAL: 'aria-modal',
  MULTILINE: 'aria-multiline',
  MULTISELECTABLE: 'aria-multiselectable',
  ORIENTATION: 'aria-orientation',
  OWNS: 'aria-owns',
  POSINSET: 'aria-posinset',
  PRESSED: 'aria-pressed',
  READONLY: 'aria-readonly',
  RELEVANT: 'aria-relevant',
  REQUIRED: 'aria-required',
  SELECTED: 'aria-selected',
  SETSIZE: 'aria-setsize',
  SORT: 'aria-sort',
  VALUEMAX: 'aria-valuemax',
  VALUEMIN: 'aria-valuemin',
  VALUENOW: 'aria-valuenow',
  VALUETEXT: 'aria-valuetext'
} as const;

/**
 * Create a screen reader announcement
 */
export const announceToScreenReader = (
  message: string,
  priority: AnnouncementPriority = 'polite',
  timeout = 1000
): void => {
  // Check if we already have an announcement element
  let announcement = document.getElementById('screen-reader-announcement');
  
  if (!announcement) {
    announcement = document.createElement('div');
    announcement.id = 'screen-reader-announcement';
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.style.position = 'absolute';
    announcement.style.left = '-10000px';
    announcement.style.width = '1px';
    announcement.style.height = '1px';
    announcement.style.overflow = 'hidden';
    document.body.appendChild(announcement);
  } else {
    // Update the priority if it's different
    announcement.setAttribute('aria-live', priority);
  }
  
  // Set the message
  announcement.textContent = message;
  
  // Clear the message after timeout
  setTimeout(() => {
    announcement.textContent = '';
  }, timeout);
};

/**
 * Create a live region for dynamic content
 */
export const createLiveRegion = (
  id: string,
  priority: AnnouncementPriority = 'polite',
  atomic = true
): HTMLElement => {
  // Check if live region already exists
  let liveRegion = document.getElementById(id);
  
  if (!liveRegion) {
    liveRegion = document.createElement('div');
    liveRegion.id = id;
    liveRegion.setAttribute('aria-live', priority);
    liveRegion.setAttribute('aria-atomic', atomic.toString());
    liveRegion.className = 'sr-only';
    liveRegion.style.position = 'absolute';
    liveRegion.style.left = '-10000px';
    liveRegion.style.width = '1px';
    liveRegion.style.height = '1px';
    liveRegion.style.overflow = 'hidden';
    document.body.appendChild(liveRegion);
  }
  
  return liveRegion;
};

/**
 * Update a live region with new content
 */
export const updateLiveRegion = (
  id: string,
  message: string,
  timeout = 1000
): void => {
  const liveRegion = document.getElementById(id);
  
  if (liveRegion) {
    liveRegion.textContent = message;
    
    // Clear the message after timeout
    setTimeout(() => {
      liveRegion.textContent = '';
    }, timeout);
  }
};

/**
 * Create a screen reader only text element
 */
export const createScreenReaderOnlyText = (
  text: string,
  id?: string
): HTMLElement => {
  const element = document.createElement('span');
  element.className = 'sr-only';
  element.textContent = text;
  
  if (id) {
    element.id = id;
  }
  
  return element;
};

/**
 * Add screen reader instructions to an element
 */
export const addScreenReaderInstructions = (
  element: HTMLElement,
  instructions: string,
  id?: string
): void => {
  const instructionsId = id || `${element.id || 'element'}-instructions`;
  
  // Check if instructions already exist
  let instructionsElement = document.getElementById(instructionsId);
  
  if (!instructionsElement) {
    instructionsElement = document.createElement('div');
    instructionsElement.id = instructionsId;
    instructionsElement.className = 'sr-only';
    instructionsElement.textContent = instructions;
    element.appendChild(instructionsElement);
  }
  
  // Add aria-describedby to the element
  element.setAttribute('aria-describedby', instructionsId);
};

/**
 * Mark an element as being processed/busy
 */
export const markElementBusy = (
  element: HTMLElement,
  isBusy = true
): void => {
  element.setAttribute('aria-busy', isBusy.toString());
  
  if (isBusy) {
    announceToScreenReader('Processing, please wait', 'polite');
  } else {
    announceToScreenReader('Processing complete', 'polite');
  }
};

/**
 * Create a descriptive label for an element
 */
export const createDescriptiveLabel = (
  element: HTMLElement,
  text: string,
  id?: string
): void => {
  const labelId = id || `${element.id || 'element'}-label`;
  
  // Check if label already exists
  let labelElement = document.getElementById(labelId);
  
  if (!labelElement) {
    labelElement = document.createElement('div');
    labelElement.id = labelId;
    labelElement.className = 'sr-only';
    labelElement.textContent = text;
    element.appendChild(labelElement);
  }
  
  // Add aria-labelledby to the element
  element.setAttribute('aria-labelledby', labelId);
};

/**
 * Create a descriptive description for an element
 */
export const createDescriptiveDescription = (
  element: HTMLElement,
  text: string,
  id?: string
): void => {
  const descriptionId = id || `${element.id || 'element'}-description`;
  
  // Check if description already exists
  let descriptionElement = document.getElementById(descriptionId);
  
  if (!descriptionElement) {
    descriptionElement = document.createElement('div');
    descriptionElement.id = descriptionId;
    descriptionElement.className = 'sr-only';
    descriptionElement.textContent = text;
    element.appendChild(descriptionElement);
  }
  
  // Add aria-describedby to the element
  element.setAttribute('aria-describedby', descriptionId);
};

/**
 * Set the current context for screen readers
 */
export const setScreenReaderContext = (
  context: string,
  priority: AnnouncementPriority = 'polite'
): void => {
  announceToScreenReader(`Current context: ${context}`, priority);
};

/**
 * Announce a state change
 */
export const announceStateChange = (
  element: HTMLElement,
  state: string,
  priority: AnnouncementPriority = 'polite'
): void => {
  const label = element.getAttribute('aria-label') || element.textContent || 'Element';
  announceToScreenReader(`${label} is now ${state}`, priority);
};

/**
 * Create a landmark region
 */
export const createLandmarkRegion = (
  element: HTMLElement,
  role: string,
  label: string
): void => {
  element.setAttribute('role', role);
  element.setAttribute('aria-label', label);
};

/**
 * Hide content from screen readers but keep it visible
 */
export const hideFromScreenReaders = (element: HTMLElement): void => {
  element.setAttribute('aria-hidden', 'true');
};

/**
 * Make content visible to screen readers only
 */
export const showOnlyToScreenReaders = (element: HTMLElement): void => {
  element.className += ' sr-only';
  element.setAttribute('aria-hidden', 'false');
};

/**
 * Create a screen reader friendly progress bar
 */
export const createAccessibleProgress = (
  container: HTMLElement,
  value: number,
  min = 0,
  max = 100,
  label = 'Progress'
): void => {
  // Create the progress element
  const progressElement = document.createElement('div');
  progressElement.setAttribute('role', 'progressbar');
  progressElement.setAttribute('aria-valuenow', value.toString());
  progressElement.setAttribute('aria-valuemin', min.toString());
  progressElement.setAttribute('aria-valuemax', max.toString());
  progressElement.setAttribute('aria-label', label);
  
  // Add it to the container
  container.appendChild(progressElement);
  
  // Announce the progress
  const percentage = Math.round(((value - min) / (max - min)) * 100);
  announceToScreenReader(`${label} is ${percentage}% complete`, 'polite');
};

/**
 * Create a screen reader friendly status message
 */
export const createAccessibleStatus = (
  container: HTMLElement,
  message: string,
  priority: AnnouncementPriority = 'polite'
): void => {
  // Create the status element
  const statusElement = document.createElement('div');
  statusElement.setAttribute('role', 'status');
  statusElement.setAttribute('aria-live', priority);
  statusElement.setAttribute('aria-atomic', 'true');
  statusElement.className = 'sr-only';
  statusElement.textContent = message;
  
  // Add it to the container
  container.appendChild(statusElement);
  
  // Announce the status
  announceToScreenReader(message, priority);
};

/**
 * Create a screen reader friendly alert
 */
export const createAccessibleAlert = (
  container: HTMLElement,
  message: string,
  priority: AnnouncementPriority = 'assertive'
): void => {
  // Create the alert element
  const alertElement = document.createElement('div');
  alertElement.setAttribute('role', 'alert');
  alertElement.setAttribute('aria-live', priority);
  alertElement.setAttribute('aria-atomic', 'true');
  alertElement.className = 'sr-only';
  alertElement.textContent = message;
  
  // Add it to the container
  container.appendChild(alertElement);
  
  // Announce the alert
  announceToScreenReader(message, priority);
};

/**
 * Create a screen reader friendly table
 */
export const createAccessibleTable = (
  container: HTMLElement,
  headers: string[],
  rows: string[][]
): void => {
  // Create the table element
  const tableElement = document.createElement('table');
  
  // Create the header row
  const headerRow = document.createElement('tr');
  headers.forEach(header => {
    const th = document.createElement('th');
    th.setAttribute('scope', 'col');
    th.textContent = header;
    headerRow.appendChild(th);
  });
  
  // Create the header section
  const thead = document.createElement('thead');
  thead.appendChild(headerRow);
  tableElement.appendChild(thead);
  
  // Create the body
  const tbody = document.createElement('tbody');
  rows.forEach(row => {
    const tr = document.createElement('tr');
    row.forEach((cell, index) => {
      const td = document.createElement('td');
      td.textContent = cell;
      
      // If this is the first cell, make it a header for the row
      if (index === 0) {
        td.setAttribute('scope', 'row');
      }
      
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  
  tableElement.appendChild(tbody);
  
  // Add the table to the container
  container.appendChild(tableElement);
  
  // Announce the table
  announceToScreenReader(`Table with ${headers.length} columns and ${rows.length} rows`, 'polite');
};

/**
 * Create a screen reader friendly list
 */
export const createAccessibleList = (
  container: HTMLElement,
  items: string[],
  ordered = false
): void => {
  // Create the list element
  const listElement = ordered ? document.createElement('ol') : document.createElement('ul');
  
  // Add the items
  items.forEach(item => {
    const li = document.createElement('li');
    li.textContent = item;
    listElement.appendChild(li);
  });
  
  // Add the list to the container
  container.appendChild(listElement);
  
  // Announce the list
  announceToScreenReader(`${ordered ? 'Ordered' : 'Unordered'} list with ${items.length} items`, 'polite');
};