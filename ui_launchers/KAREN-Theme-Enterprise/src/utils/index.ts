/**
 * Utils Index - Production Grade
 *
 * Centralized export hub for all utility functions and helpers.
 */

export { createAccessibilityTestWrapper, runAccessibilityTestSuite, accessibilityConfigs, isValidAriaRole, registerA11yMatchers, validateAccessibilityPattern, default as AccessibilityTestSetup } from './accessibility-test-setup.js';
export type { AccessibilityConfigKey, A11yRunReport } from './accessibility-test-setup.js';

export { validateColorContrast, testKeyboardAccessibility, testScreenReaderAccessibility, validateAriaAttributes, generateAccessibilityReportSummary, accessibilityTestConfigs } from './accessibility-testing.js';
export type { AccessibilityPresetKey, KeyboardTestResult, AccessibilityViolation, AccessibilityTestOptions, AccessibilityReport, ScreenReaderTestResult } from './accessibility-testing.js';

export { reducedMotionVariants, animationCSS, useWillChange, usePerformanceAwareAnimation, performanceAnimationVariants, useAnimationPerformance, AnimationPerformanceMonitor, ANIMATION_PERFORMANCE_THRESHOLDS, animationPerformanceMonitor, default as AnimationPerformance } from './animation-performance.js';
export type { AnimationMetrics } from './animation-performance.js';

export { createModalAria, createNavigationAria, joinIds, createLoadingAria, createInteractiveAria, createFormAria, createAriaLabel, createAriaLive, generateAriaId, mergeAriaProps, validateAriaProps, createGridAria, ARIA_ROLES } from './aria.js';
export type {
  AriaLabelProps,
  AriaRole,
  AriaLiveProps,
  AriaProps,
  AriaGridProps,
  AriaStateProps,
  AriaRelationshipProps,
  AriaRelevant,
} from './aria.js';

export { BUNDLE_BUDGETS, createBundleAnalyzer, BundleAnalyzer, DEFAULT_BUNDLE_BUDGETS, summarizeBundle, bundleAnalyzer } from './bundle-analyzer.js';
export type { ModuleInfo, BudgetSeverity, BundleStats, BundleBudget, ChunkInfo, AssetInfo, BudgetViolation, BudgetViolationType, BudgetWarning, BundleAnalysisResult } from './bundle-analyzer.js';

export { sleep, formatDateTime, truncate, clamp, unique, isEmpty, pascalCase, formatRelativeTime, getDaysBetween, formatDate, formatNumber, slugify, percentage, formatBytes, debounce, snakeCase, isValidHex, throttle, deepMerge, isEmail, pick, camelCase, isURL, addDays, omit, groupBy } from './common.js';

export { errorReportingService, default as ErrorReporting } from './error-reporting.js';
export type { ErrorReport, ErrorBreadcrumb, ErrorReportingConfig, ReactErrorInfoLike } from './error-reporting.js';

export { useFeatureDetection, featureDetection, default as FeatureDetection } from './feature-detection.js';
export type { Callback, FeatureSupport } from './feature-detection.js';

export { componentMigrationMap, defaultPageConfig, getPendingMigrations, withModernPageLayout, areAllComponentsMigrated, getComponentMigrationStatus } from './page-integration.js';
export type { PageIntegrationConfig, ComponentMigrationStatus } from './page-integration.js';

export { PerformanceMonitor, PERFORMANCE_THRESHOLDS, usePerformanceMonitor, performanceMonitor, checkPerformanceBudget } from './performance-monitor.js';
export type { NavigationTimingSummary, WebVitalsMetric, CustomMetric, ResourceTimingSummary, MetricSummary, PerformanceSummary } from './performance-monitor.js';

export { polyfillLoader, usePolyfills, default as PolyfillLoader } from './polyfill-loader.js';
export type { PolyfillConfig, ScriptLoadOptions, KnownPolyfill, PolyfillLoadResult } from './polyfill-loader.js';

export { useProgressiveEnhancement, progressiveEnhancement, default as ProgressiveEnhancement } from './progressive-enhancement.js';
export type { ProgressiveEnhancementConfig, AnimationEnhancements, CSSEnhancements, EnhancementLevel, PerformanceEnhancements, LayoutEnhancements, AccessibilityEnhancements, JSEnhancements, ImageEnhancements, EnhancementSnapshot } from './progressive-enhancement.js';

export { retryMechanism, useRetryFetch, useRetry, default as RetryMechanisms } from './retry-mechanisms.js';
export type { CircuitState, CircuitBreakerState, RetryState, RetryConfig, CircuitBreakerConfig } from './retry-mechanisms.js';

export { testElementSelection, getTextSelectionInfo } from './text-selection-test.js';
export type { TextSelectionTestResult } from './text-selection-test.js';

export { treeShakingAnalyzer, TREE_SHAKING_CONFIG, OPTIMIZED_IMPORTS, TreeShakingAnalyzer, treeShakingUtils } from './tree-shaking.js';
export type { TreeShakingSuggestion, TreeShakingReport, TreeShakingIssue, OptimizedLib } from './tree-shaking.js';

