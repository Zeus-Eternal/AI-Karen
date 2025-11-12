/**
 * Utils Index - Production Grade
 *
 * Centralized export hub for all utility functions and helpers.
 */

export { createAccessibilityTestWrapper, runAccessibilityTestSuite, accessibilityConfigs, isValidAriaRole, registerA11yMatchers, validateAccessibilityPattern, default as AccessibilityTestSetup } from './accessibility-test-setup';
export type { AccessibilityConfigKey, A11yRunReport } from './accessibility-test-setup';

export { validateColorContrast, testKeyboardAccessibility, testScreenReaderAccessibility, validateAriaAttributes, generateAccessibilityReportSummary, accessibilityTestConfigs } from './accessibility-testing';
export type { AccessibilityPresetKey, KeyboardTestResult, AccessibilityViolation, AccessibilityTestOptions, AccessibilityReport, ScreenReaderTestResult } from './accessibility-testing';

export { reducedMotionVariants, animationCSS, useWillChange, usePerformanceAwareAnimation, performanceAnimationVariants, useAnimationPerformance, AnimationPerformanceMonitor, ANIMATION_PERFORMANCE_THRESHOLDS, animationPerformanceMonitor, default as AnimationPerformance } from './animation-performance';
export type { AnimationMetrics } from './animation-performance';

export { createModalAria, createNavigationAria, joinIds, createLoadingAria, createInteractiveAria, createFormAria, createAriaLabel, createAriaLive, generateAriaId, mergeAriaProps, validateAriaProps, createGridAria, ARIA_ROLES } from './aria';
export type {
  AriaLabelProps,
  AriaRole,
  AriaLiveProps,
  AriaProps,
  AriaGridProps,
  AriaStateProps,
  AriaRelationshipProps,
  AriaRelevant,
} from './aria';

export { BUNDLE_BUDGETS, createBundleAnalyzer, BundleAnalyzer, DEFAULT_BUNDLE_BUDGETS, summarizeBundle, bundleAnalyzer } from './bundle-analyzer';
export type { ModuleInfo, BudgetSeverity, BundleStats, BundleBudget, ChunkInfo, AssetInfo, BudgetViolation, BudgetViolationType, BudgetWarning, BundleAnalysisResult } from './bundle-analyzer';

export { sleep, formatDateTime, truncate, clamp, unique, isEmpty, pascalCase, formatRelativeTime, getDaysBetween, formatDate, formatNumber, slugify, percentage, formatBytes, debounce, snakeCase, isValidHex, throttle, deepMerge, isEmail, pick, camelCase, isURL, addDays, omit, groupBy } from './common';

export { errorReportingService, default as ErrorReporting } from './error-reporting';
export type { ErrorReport, ErrorBreadcrumb, ErrorReportingConfig, ReactErrorInfoLike } from './error-reporting';

export { useFeatureDetection, featureDetection, default as FeatureDetection } from './feature-detection';
export type { Callback, FeatureSupport } from './feature-detection';

export { componentMigrationMap, defaultPageConfig, getPendingMigrations, withModernPageLayout, areAllComponentsMigrated, getComponentMigrationStatus } from './page-integration';
export type { PageIntegrationConfig, ComponentMigrationStatus } from './page-integration';

export { PerformanceMonitor, PERFORMANCE_THRESHOLDS, usePerformanceMonitor, performanceMonitor, checkPerformanceBudget } from './performance-monitor';
export type { NavigationTimingSummary, WebVitalsMetric, CustomMetric, ResourceTimingSummary, MetricSummary, PerformanceSummary } from './performance-monitor';

export { polyfillLoader, usePolyfills, default as PolyfillLoader } from './polyfill-loader';
export type { PolyfillConfig, ScriptLoadOptions, KnownPolyfill, PolyfillLoadResult } from './polyfill-loader';

export { useProgressiveEnhancement, progressiveEnhancement, default as ProgressiveEnhancement } from './progressive-enhancement';
export type { ProgressiveEnhancementConfig, AnimationEnhancements, CSSEnhancements, EnhancementLevel, PerformanceEnhancements, LayoutEnhancements, AccessibilityEnhancements, JSEnhancements, ImageEnhancements, EnhancementSnapshot } from './progressive-enhancement';

export { retryMechanism, useRetryFetch, useRetry, default as RetryMechanisms } from './retry-mechanisms';
export type { CircuitState, CircuitBreakerState, RetryState, RetryConfig, CircuitBreakerConfig } from './retry-mechanisms';

export { testElementSelection, getTextSelectionInfo } from './text-selection-test';
export type { TextSelectionTestResult } from './text-selection-test';

export { treeShakingAnalyzer, TREE_SHAKING_CONFIG, OPTIMIZED_IMPORTS, TreeShakingAnalyzer, treeShakingUtils } from './tree-shaking';
export type { TreeShakingSuggestion, TreeShakingReport, TreeShakingIssue, OptimizedLib } from './tree-shaking';

