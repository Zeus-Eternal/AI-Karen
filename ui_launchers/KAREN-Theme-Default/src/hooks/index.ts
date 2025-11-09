/**
 * Hooks Index - Production Grade
 *
 * Centralized export hub for all custom React hooks.
 */

export { useExtensionCache } from './extensions/useExtensionCache';

export { useExtensionControls } from './extensions/useExtensionControls';

export { useExtensionHealth } from './extensions/useExtensionHealth';
export type { ExtensionHealth } from './extensions/useExtensionHealth';

export { useExtensionMarketplace } from './extensions/useExtensionMarketplace';
export type { MarketplaceExtension } from './extensions/useExtensionMarketplace';

export { useExtensionNavigation } from './extensions/useExtensionNavigation';
export type { UseExtensionNavigation } from './extensions/useExtensionNavigation';

export { useExtensionSettings } from './extensions/useExtensionSettings';
export type { ExtensionSettings } from './extensions/useExtensionSettings';

export { useExtensions } from './extensions/useExtensions';
export type { UseExtensionsResult } from './extensions/useExtensions';

export { useAccessibilityTesting, useAccessibilityMonitor, useAccessibilityTestRunner } from './use-accessibility-testing';
export type { UseAccessibilityTestingOptions, AccessibilityTestingState } from './use-accessibility-testing';

export { useActionEvents, useActionSuggestions, useActionRegistry } from './use-action-registry';
export type { UseActionRegistryOptions, UseActionRegistryReturn } from './use-action-registry';

export { useDashboardUrlSync } from './use-dashboard-url-sync';
export type { DashboardUrlState } from './use-dashboard-url-sync';

export { useDebounce } from './use-debounce';

export { useDownloadStatus } from './use-download-status';
export type { DownloadTask, DownloadStatusHookReturn } from './use-download-status';

export { useTableKeyboardShortcuts, useEscapeKeyHandler, useKeyboardShortcutHelp, useSearchKeyboardShortcuts, useFormKeyboardShortcuts, useModalKeyboardShortcuts, useEnhancedKeyboardShortcuts } from './use-enhanced-keyboard-shortcuts';
export type { KeyboardShortcutContext, EnhancedKeyboardShortcutConfig } from './use-enhanced-keyboard-shortcuts';

export { useErrorRecovery, useFormErrorRecovery, useNetworkErrorRecovery } from './use-error-recovery';
export type { ErrorRecoveryOptions, ErrorRecoveryState } from './use-error-recovery';

export { useFeatureFlag, useFeatureFlags, useDeploymentPhase, useFeatureClasses, useConditionalComponent } from './use-feature-flags';

export { invalidateFeatureFlagCache, isFeatureEnabled, useFeatures, useAllFeatures, useFeature } from './use-feature';
export type { FeatureFlag } from './use-feature';

export { useFocusVisible, useFocusRestore, useFocusTrap, useFocusManagement } from './use-focus-management';
export type { FocusableElement, FocusManagementOptions } from './use-focus-management';

export { useFormValidation, useFieldValidation } from './use-form-validation';
export type { FieldValidationState, UseFormValidationConfig, UseFormValidationReturn, FormValidationState } from './use-form-validation';

export { useInputPreservation } from './use-input-preservation';
export type { InputPreservationHook } from './use-input-preservation';

export { useIntelligentErrorBoundary, useIntelligentApiError, useIntelligentError } from './use-intelligent-error';
export type { ErrorAnalysisRequest, UseIntelligentErrorReturn, ErrorAnalysisResponse, UseIntelligentErrorOptions } from './use-intelligent-error';

export { useKarenAlerts, useSimpleAlerts } from './use-karen-alerts';
export type { UseKarenAlertsState, UseKarenAlertsReturn } from './use-karen-alerts';

export { useKeyboardNavigation, useRovingTabIndex, useGridNavigation } from './use-keyboard-navigation';
export type { KeyMap, GridNavigationOptions, KeyboardNavigationOptions } from './use-keyboard-navigation';

export { useKeyboardShortcut, useShortcutHelp, useShortcutDisplay, useKeyboardShortcuts, useCommonShortcuts, useNavigationShortcuts } from './use-keyboard-shortcuts';
export type { KeyboardShortcut, KeyboardShortcutHandler, KeyboardShortcutConfig } from './use-keyboard-shortcuts';

export { usePersistentUIState, usePersistentForm, useSessionStorage, useLocalStorage } from './use-local-storage';

export { useMediaQueries, useCurrentBreakpoint, useDeviceCapabilities, useMediaQuery, useBreakpoint } from './use-media-query';

export { useIsMobile } from './use-mobilex';

export { useMonitoring } from './use-monitoring';
export type { MonitoringState, UseMonitoringReturn } from './use-monitoring';

export { useMultipleNonBlockingOperations, useNonBlockingOperation, useNonBlockingLoading } from './use-non-blocking-loading';
export type { NonBlockingLoadingState, NonBlockingLoadingOptions } from './use-non-blocking-loading';

export { useOptimisticForm, useOptimisticList, useOptimisticUpdates } from './use-optimistic-updates';
export type { OptimisticUpdateOptions } from './use-optimistic-updates';

export { useAnimationDuration, useReducedMotion, useAnimationVariants } from './use-reduced-motion';

export { useResponsivePanel, usePanelPerformance, usePanelBackdrop } from './use-responsive-panel';
export type { ResponsivePanelOptions, ResponsivePanelState, ResponsivePanelActions, UseResponsivePanelReturn } from './use-responsive-panel';

export { useSession } from './use-session';
export type { UseSessionReturn } from './use-session';

export { useStreamingController } from './use-streaming-controller';
export type { StreamOptions, StreamState, StreamMetrics, StreamingController } from './use-streaming-controller';

export { useTabOrderItem, useTabOrder } from './use-tab-order';
export type { TabOrderItem, TabOrderOptions } from './use-tab-order';

export { useTelemetry } from './use-telemetry';
export type { TelemetryEvent, TelemetryHook } from './use-telemetry';

export { reducer } from './use-toast';
export type { State, Toast, ToasterToast, ActionType, Action } from './use-toast';

export { useCopilotApi, useUnifiedApi, useMemoryApi } from './use-unified-api';
export type { UseUnifiedApiReturn, UseUnifiedApiOptions, CacheEntry } from './use-unified-api';

export { useAdminErrorHandler, useBulkOperationErrors, useSystemConfigErrors, useUserManagementErrors, useAuditLogErrors, default as useAdminErrorHandler } from './useAdminErrorHandler';
export type { UseAdminErrorHandlerOptions, UseAdminErrorHandlerReturn, ErrorState } from './useAdminErrorHandler';

export { useChatPerformance, default as useChatPerformance } from './useChatPerformance';
export type { ChatPerformanceMetrics } from './useChatPerformance';

export { useDeviceDetection, useTouchGestures, useResponsiveDesign, default as useDeviceDetection } from './useDeviceDetection';
export type { DeviceInfo } from './useDeviceDetection';

export { useFirstRunSetupWithRedirect, useFirstRunSetup, firstRunSetupStorage, useSetupCompletion, shouldBypassFirstRunCheck, useFirstRunSetupProvider } from './useFirstRunSetup';
export type { UseFirstRunSetupState, UseFirstRunSetupReturn } from './useFirstRunSetup';

export { useInfiniteScroll, default as useInfiniteScroll } from './useInfiniteScroll';
export type { UseInfiniteScrollOptions } from './useInfiniteScroll';

export { useModelActions, useModelSelection } from './useModelSelection';
export type { UseModelSelectionOptions, UseModelSelectionReturn } from './useModelSelection';

export { useNavigation } from './useNavigation';
export type { NavigationOptions } from './useNavigation';

export { usePerformanceMonitor, useWebVitals } from './usePerformanceMonitor';
export type { PerformanceMetrics } from './usePerformanceMonitor';

export { useProviderNotifications, default as useProviderNotifications } from './useProviderNotifications';
export type { ProviderNotification, NotificationSettings, UseProviderNotificationsOptions } from './useProviderNotifications';

export { useReasoning, default as useReasoning } from './useReasoning';
export type { UseReasoningReturn } from './useReasoning';

export { useHasPermission, useIsSuperAdmin, useHasRole, useIsAdmin, useRole } from './useRole';
export type { UseRoleReturn } from './useRole';

export { useSystemHealth } from './useSystemHealth';
export type { UseSystemHealthOptions } from './useSystemHealth';

export { highlightSelection, debugTextSelection, ensureTextSelectable, isTextSelectionSupported, getDocumentSelection, useTextSelection } from './useTextSelection';
export type { TextSelectionState, UseTextSelectionOptions } from './useTextSelection';

