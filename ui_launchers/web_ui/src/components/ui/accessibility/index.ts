/**
 * Accessibility Components Index
 * Exports all accessibility-related components and utilities
 */

// ARIA utilities
export * from '../../../utils/aria';

// ARIA Live Region components
export * from '../aria-live-region';

// Enhanced components with ARIA support
export * from '../aria-enhanced-button';
export * from '../aria-enhanced-form';
export * from '../aria-enhanced-input';

// Navigation components
export * from '../aria-navigation';

// Focus management
export * from '../../../hooks/use-focus-management';
export * from '../focus-trap';
export * from '../focus-indicators';

// Keyboard navigation
export * from '../../../hooks/use-keyboard-navigation';
export * from '../../../hooks/use-enhanced-keyboard-shortcuts';
export * from '../../../hooks/use-tab-order';

// Screen reader support
export * from '../screen-reader';

// Skip links
export * from '../skip-links';

// Accessibility testing
export * from '../accessibility-testing';

// Re-export commonly used types
export type { AriaProps, AriaRole } from '../../../utils/aria';
export type { FocusManagementOptions } from '../../../hooks/use-focus-management';
export type { KeyboardNavigationOptions } from '../../../hooks/use-keyboard-navigation';
export type { SkipLink } from '../skip-links';
export type { AccessibilityTestResult, AccessibilityTestSuite } from '../accessibility-testing';
