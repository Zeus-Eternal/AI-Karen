/**
 * Accessibility Module Index - Production Grade
 *
 * Centralized export hub for accessibility utilities and types.
 */

export { createAccessibilityTestSuite, AccessibilityTestSuiteImpl, default as AccessibilityTesting } from './accessibility-testing';
export type { KeyboardAccessibilityReport, FocusManagementReport, ColorContrastReport, AccessibilityViolation, ScreenReaderReport, AccessibilityReport, AccessibilityWarning, AccessibilityTestSuite, AriaReport } from './accessibility-testing';

export { AriaManager, useAriaLiveRegion, useAriaDescription, useLoadingState } from './aria-helpers';
export type { AriaLiveRegionOptions, AriaDescriptionOptions } from './aria-helpers';

export { AccessibilityTestConfigs, runPageAccessibilityTest, AutomatedAccessibilityTester, runAccessibilityTest, accessibilityTester, default as AutomatedTesting } from './automated-testing';
export type { AccessibilityTestResult, AccessibilityTestConfig, AccessibilityRegressionResult } from './automated-testing';

export { AccessibilityDocumentationGenerator, generateAccessibilityDocs, default as DocumentationGenerator } from './documentation-generator';
export type { AriaAttribute, KeyboardSupport, ScreenReaderFeature, AccessibilityExample, AccessibilityIssue, ComponentAccessibilityInfo, AccessibilityFeature, TestingInstruction, DocumentationConfig } from './documentation-generator';

export { KeyboardUtils, KeyboardNavigationManager, useKeyboardNavigation, default as KeyboardNavigation } from './keyboard-navigation';
export type { KeyboardNavigationOptions } from './keyboard-navigation';

