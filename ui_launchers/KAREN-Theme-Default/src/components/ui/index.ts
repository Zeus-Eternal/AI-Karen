// Consolidated UI exports with explicit conflict management
// This file gathers frequently used UI components while avoiding duplicate re-exports
// that break TypeScript isolated module compilation.

export * as AccessibilityUI from './accessibility';
export * from './accessibility-testing';
export * from './accordion';
export * from './alert-dialog';
export * from './alert';
export * from './animated-number';
export * from './animation';
export * from './animation-fallbacks';
export {
  AriaEnhancedButton,
  ToggleButton,
  MenuButton,
  type AriaEnhancedButtonProps,
  type ToggleButtonProps,
  type MenuButtonProps,
  buttonVariants as ariaEnhancedButtonVariants,
} from './aria-enhanced-button';
export {
  Form as AriaEnhancedFormProvider,
  useAriaFormField,
  AriaEnhancedFormField,
  AriaEnhancedFormItem,
  AriaEnhancedFormLabel,
  AriaEnhancedFormControl,
  AriaEnhancedFormDescription,
  AriaEnhancedFormMessage,
  AriaFormField,
  AriaFormItem,
  AriaFormLabel,
  AriaFormControl,
  AriaFormDescription,
  AriaFormMessage,
  AriaFormHelp,
  AriaFormFieldset,
  AriaFormSection,
  type FormFieldContextValue as AriaFormFieldContextValue,
} from './aria-enhanced-form';
export { AriaEnhancedInput } from './aria-enhanced-input';
export * from './aria-live-region';
export * from './aria-navigation';
export * from './avatar';
export * from './badge';
export * from './button';
export * from './calendar';
export * from './card';
export * from './carousel';
export * from './chart';
export * from './checkbox';
export * from './clipboard-test';
export * from './collapsible';
export * as CompoundUI from './compound';
export * from './confirmation-dialog';
export * from './contextual-help';
export * from './degraded-mode-banner';
export * from './dialog';
export * from './dropdown-menu';
export * from './enhanced';
export {
  ErrorBoundary as UIErrorBoundary,
  type ErrorBoundaryProps as UIErrorBoundaryProps,
  type ErrorBoundaryState as UIErrorBoundaryState,
} from './error-boundary';
export {
  ErrorBoundary as DisplayErrorBoundary,
  type ErrorBoundaryProps as DisplayErrorBoundaryProps,
  type ErrorBoundaryState as DisplayErrorBoundaryState,
} from './error-display';
export * from './focus-indicators';
export * from './focus-trap';
export * from './form-field';
export * from './form';
export * from './glass-card';
export * from './haptic-feedback';
export * from './health-status-badge';
export * from './help-tooltip';
export * from './input';
export * from './karen-toast';
export * from './karen-toaster';
export * from './label';
export * from './layout';
export * from './lazy-loading';
export * as LoadingStates from './loading-states';
export * from './loading';
export * from './menubar';
export * from './metric-card';
export * from './micro-interactions';
export * from './page-transitions';
export * from './panel-content';
export * from './panel-header';
export * from './panel-transitions';
export * from './performance';
export {
  type TextProps as PolymorphicTextProps,
  type ButtonProps as PolymorphicButtonProps,
  type ContainerProps as PolymorphicContainerProps,
  type ContainerVariant as PolymorphicContainerVariant,
  type ContainerSize as PolymorphicContainerSize,
  type ContainerDisplay as PolymorphicContainerDisplay,
  type ContainerBreakpoints as PolymorphicContainerBreakpoints,
  type FlexContainerProps as PolymorphicFlexContainerProps,
  type GridContainerProps as PolymorphicGridContainerProps,
  type AspectRatioContainerProps as PolymorphicAspectRatioContainerProps,
  type ScrollContainerProps as PolymorphicScrollContainerProps,
} from './polymorphic';
export * from './popover';
export * from './progress-indicator';
export * from './progress';
export * from './progressive-loader';
export * from './radio-group';
export * from './resizable';
export * from './responsive-card-grid';
export * from './retry-components';
export * from './right-panel';
export * from './screen-reader';
export * from './scroll-area';
export * from './select';
export * from './separator';
export * from './sheet';
export * from './sidebar';
export * from './skeleton';
export * from './skip-links';
export * from './slider';
export * from './sparkline';
export * from './status-indicator';
export * from './suggested-actions';
export * from './switch';
export * from './table';
export * from './tabs';
export * from './text-selection-provider';
export * from './textarea';
export * from './theme-toggle';
export * from './toast';
export * from './toaster';
export * from './tooltip';
export * from './touch-interactions';
export * from './types';
export * from './with-retry';
