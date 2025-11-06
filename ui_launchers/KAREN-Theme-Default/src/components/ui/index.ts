/**
 * UI Components Index - Production Grade
 *
 * Centralized export hub for all UI components and types.
 * Auto-generated barrel export for comprehensive type safety.
 */

// ============================================================================
// Core Shadcn/UI Components
// ============================================================================

export { Button } from './button';
export type { ButtonProps } from './button';

export type { InputProps } from './input';

export { CardTitle, CardContent, CardHeader, Card, CardFooter, CardDescription } from './card';
export type { CardContentProps, CardTitleProps, CardFooterProps, CardHeaderProps, CardProps, CardDescriptionProps } from './card';

export { Badge } from './badge';
export type { BadgeProps } from './badge';

export type { AlertProps } from './alert';











export type { CalendarProps } from './calendar';

export type { CarouselApi, CarouselProps, CarouselContextProps } from './carousel';

export type { ChartConfig, ChartContextProps } from './chart';


export type { FormItemContextValue, FormFieldContextValue } from './form';






export type { SheetContentProps } from './sheet';




export type { TextareaProps } from './textarea';

export { ToastDescription, ToastProvider, ToastAction, ToastTitle, ToastClose, Toast, ToastViewport } from './toast';
export type { ToastActionElement, ToastProps } from './toast';

export { Toaster } from './toaster';



export type { ResizablePanelProps, ResizablePanelGroupProps, ResizableHandleProps } from './resizable';


// ============================================================================
// Enhanced & Custom Components
// ============================================================================

export { ErrorBoundary } from './ErrorBoundary';
export type { State, Props } from './ErrorBoundary';
export { AccessibilityReport, AccessibilityTester, default as AccessibilityTesting } from './accessibility-testing';
export type { AccessibilityTestResult, AccessibilityTesterProps, AccessibilityReportProps, AccessibilityTestSuite } from './accessibility-testing';
export { AnimatedNumber, default as AnimatedNumber } from './animated-number';
export type { AnimatedNumberProps } from './animated-number';
export { SlideAnimation, BounceAnimation, ScaleAnimation, SpinnerAnimation, CollapseAnimation, PulseAnimation, AnimationFallback, FadeAnimation } from './animation-fallbacks';
export type { BounceProps, FadeProps, CollapseProps, SlideProps, ScaleProps, PulseProps, AnimationFallbackProps, SpinnerProps } from './animation-fallbacks';
export { MenuButton, ToggleButton } from './aria-enhanced-button';
export type { MenuButtonProps, AriaEnhancedButtonProps, ToggleButtonProps } from './aria-enhanced-button';
export type { FormItemContextValue, AriaFormSectionProps, FormFieldContextValue, AriaFormFieldsetProps } from './aria-enhanced-form';
export { PasswordInput, SearchInput } from './aria-enhanced-input';
export type { AriaEnhancedInputProps, PasswordInputProps, SearchInputProps } from './aria-enhanced-input';
export { AriaAnnouncer, AriaLiveRegion, AriaProgress, AriaStatus, default as AriaLiveRegion } from './aria-live-region';
export type { AriaStatusProps, AriaProgressProps, AriaLiveRegionProps, UseAriaAnnouncementsOptions, AriaAnnouncerProps } from './aria-live-region';
export { AriaNavItem, AriaBreadcrumbItem, AriaNavList, AriaTabPanel, AriaNavLink, AriaBreadcrumb, AriaTabList, AriaNavigation, AriaTab } from './aria-navigation';
export type { AriaNavigationProps, AriaTabProps, AriaTabListProps, AriaBreadcrumbItemProps, AriaNavListProps, AriaBreadcrumbProps, AriaNavLinkProps, AriaNavItemProps, AriaTabPanelProps } from './aria-navigation';
export { ClipboardTest, default as ClipboardTest } from './clipboard-test';
export type { ClipboardTestProps } from './clipboard-test';
export { DeactivateUserConfirmation, BulkOperationConfirmation, DeleteUserConfirmation, ConfirmationDialog, default as ConfirmationDialog } from './confirmation-dialog';
export type { ConfirmationDialogProps } from './confirmation-dialog';
export { ContextualHelp, QuickStartHelp, HelpCallout } from './contextual-help';
export type { HelpCalloutProps, ContextualHelpProps, QuickStartHelpProps } from './contextual-help';
export { default as DegradedModeBanner } from './degraded-mode-banner';
export { ErrorBoundary } from './error-boundary';
export type { ErrorBoundaryState, ErrorBoundaryProps } from './error-boundary';
export { ErrorToast, ErrorDisplay, ErrorBoundary, default as ErrorDisplay } from './error-display';
export type { ErrorDisplayProps, ErrorBoundaryState, ErrorBoundaryProps, ErrorToastProps } from './error-display';
export { FocusableArea, FocusIndicator, FocusRing, default as FocusIndicators } from './focus-indicators';
export type { FocusableAreaProps, FocusIndicatorProps, FocusRingProps } from './focus-indicators';
export { ModalFocusTrap, FocusTrapWithGuards, FocusTrap, FocusGuard, default as FocusTrap } from './focus-trap';
export type { FocusTrapWithGuardsProps, ModalFocusTrapProps, FocusTrapProps } from './focus-trap';
export { ValidatedFormField, FormField, PasswordStrength, default as FormField } from './form-field';
export type { ValidatedFormFieldProps, PasswordStrengthProps, FormFieldProps } from './form-field';
export { GlassCard, default as GlassCard } from './glass-card';
export type { GlassCardProps } from './glass-card';
export { HealthStatusBadge } from './health-status-badge';
export type { HealthStatus } from './health-status-badge';
export { HelpSection, HelpTooltip, QuickHelp } from './help-tooltip';
export type { QuickHelpProps, HelpTooltipProps, HelpSectionProps } from './help-tooltip';
export type { KarenToastProps, KarenToastActionElement } from './karen-toast';
export { KarenToaster } from './karen-toaster';
export type { LoadingProps } from './loading';
export type { PulseLoaderProps, ShimmerProps, LoadingCardProps, FloatingDotsProps, ProgressBarProps, SkeletonProps, LoadingOverlayProps, LoadingSpinnerProps } from './loading-states';
export { MetricCard, default as MetricCard } from './metric-card';
export type { MetricCardProps } from './metric-card';
export { PanelContent, PanelSection } from './panel-content';
export type { PanelContentProps, PanelSectionProps } from './panel-content';
export { PanelHeader } from './panel-header';
export type { PanelHeaderProps } from './panel-header';
export type { TransitionDirection, TransitionType } from './panel-transitions';
export { SimpleProgressBar, ProgressIndicator, default as ProgressIndicator } from './progress-indicator';
export type { BulkOperationProgress, ProgressIndicatorProps, SimpleProgressBarProps, ProgressStep } from './progress-indicator';
export { ProgressiveLoader } from './progressive-loader';
export type { ProgressiveLoaderProps } from './progressive-loader';
export { default as ResponsiveCardGrid } from './responsive-card-grid';
export type { ResponsiveCardGridProps } from './responsive-card-grid';
export type { RetryButtonProps, RetryBannerProps, RetryCardProps, InlineRetryProps, RetryWrapperProps, LoadingRetryProps } from './retry-components';
export { RightPanelNavigation, RightPanelHeader, RightPanelContent, RightPanel } from './right-panel';
export type { RightPanelProps, RightPanelHeaderProps, RightPanelView, RightPanelNavigationProps, RightPanelContentProps } from './right-panel';
export { ScreenReaderOnly, VisuallyHidden, LoadingAnnouncement, StatusMessage, LandmarkRegion, InteractionDescription, ScreenReaderAnnouncer, DescriptiveText, ScreenReaderTestHelper, HeadingStructure, default as ScreenReader } from './screen-reader';
export type { DescriptiveTextProps, StatusMessageProps, ScreenReaderAnnouncerProps, ScreenReaderOnlyProps, LoadingAnnouncementProps, LandmarkRegionProps, InteractionDescriptionProps, HeadingStructureProps } from './screen-reader';
export type { SidebarProps, SidebarMenuButtonProps, SidebarTriggerProps, SidebarContextValue, SidebarProviderProps } from './sidebar';
export { DEFAULT_SKIP_LINKS, SkipToContent, MainContent, SkipLinks, default as SkipLinks } from './skip-links';
export type { SkipToContentProps, SkipLinksProps, SkipLink, MainContentProps } from './skip-links';
export { Sparkline, default as Sparkline } from './sparkline';
export type { SparklineProps } from './sparkline';
export { StatusIndicator, default as StatusIndicator } from './status-indicator';
export type { StatusIndicatorProps } from './status-indicator';
export { SuggestedActions, default as SuggestedActions } from './suggested-actions';
export type { SuggestedActionsProps } from './suggested-actions';
export { TextSelectionProvider, default as TextSelectionProvider } from './text-selection-provider';
export type { TextSelectionProviderProps } from './text-selection-provider';
export { default as ThemeToggle } from './theme-toggle';
export type { SwipeableCardProps, TouchMenuProps, TouchSliderProps, FloatingActionButtonProps, TouchButtonProps, PullToRefreshProps } from './touch-interactions';
export type { PulseLoaderProps, ComponentSize, AsyncState, KeyboardHandler, ProgressBarProps, LoadingOverlayProps, PullToRefreshProps, ClickHandler, InteractiveComponentProps, AccessibilityProps, LoadingState, LoadingCardProps, TouchSliderProps, SizeVariant, ResponsiveProps, NotificationProps, ColorVariant, FloatingActionButtonProps, ChangeHandler, SuggestedActionsProps, LoadingSpinnerProps, FocusHandler, BaseComponentProps, LoadingProps, ComponentColor, ErrorBoundaryProps, FormFieldProps, VariantType, TouchButtonProps, AnimationProps, ComponentVariant, FormComponentProps, SkeletonProps, ErrorBoundaryState, SwipeableCardProps, ShimmerProps, FloatingDotsProps, ModalProps, TouchMenuProps } from './types';
export { RetryBoundary } from './with-retry';
export type { RetryBoundaryProps, WithRetryProps, WithRetryState, RetryBoundaryState, WithRetryOptions } from './with-retry';

// ============================================================================
// UI Subdirectory Exports
// ============================================================================

// Enhanced Components
export * from './enhanced';

// Layout System
export * from './layout';

// Animation System
export * from './animation';

// Performance Optimizations
export * from './performance';

// Lazy Loading
export * from './lazy-loading';

// Accessibility
export * from './accessibility';

// Micro Interactions
export * from './micro-interactions';

// Page Transitions
export * from './page-transitions';

// Polymorphic Components
export * from './polymorphic';

// Compound Components
export * from './compound';

// Haptic Feedback
export * from './haptic-feedback';

// Skeleton Components
export * from './skeleton';
