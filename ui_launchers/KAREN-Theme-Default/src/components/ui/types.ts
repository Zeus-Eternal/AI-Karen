/**
 * UI Component Types
 * 
 * Centralized type definitions for UI components
 * maintaining consistency with React and Next.js patterns
 */

import type React from "react";
import type { SuggestedAction, ActionResult } from '@/services/actionMapper';

// Loading Component Types
export interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'spinner' | 'dots' | 'pulse' | 'skeleton';
  message?: string;
  className?: string;
  fullScreen?: boolean;
}

// Error Boundary Types
export interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  showDetails?: boolean;
  enableRecovery?: boolean;
  className?: string;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  showDetails: boolean;
  retryCount: number;
}

// Suggested Actions Types
export interface SuggestedActionsProps {
  actions: SuggestedAction[];
  onActionComplete?: (action: SuggestedAction, result: ActionResult) => void;
  onDismiss?: () => void;
  className?: string;
  variant?: 'default' | 'compact' | 'inline';
  showConfidence?: boolean;
  maxActions?: number;
}

// Touch Interaction Types
export interface TouchButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  onLongPress?: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  haptic?: boolean;
}

export interface SwipeableCardProps {
  children: React.ReactNode;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  swipeThreshold?: number;
  className?: string;
}

export interface PullToRefreshProps {
  children: React.ReactNode;
  onRefresh: () => Promise<void>;
  refreshThreshold?: number;
  className?: string;
}

export interface FloatingActionButtonProps {
  onClick: () => void;
  icon: React.ReactNode;
  label?: string;
  position?: 'bottom-right' | 'bottom-left' | 'bottom-center';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export interface TouchSliderProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  className?: string;
  trackColor?: string;
  thumbColor?: string;
}

export interface TouchMenuProps {
  trigger: React.ReactNode;
  items: Array<{
    label: string;
    icon?: React.ReactNode;
    onClick: () => void;
    destructive?: boolean;
  }>;
  className?: string;
}

// Loading States Types
export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export interface SkeletonProps {
  className?: string;
  animate?: boolean;
}

export interface PulseLoaderProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'blue' | 'green' | 'purple' | 'gray';
  className?: string;
}

export interface ShimmerProps {
  className?: string;
  children?: React.ReactNode;
}

export interface LoadingCardProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  className?: string;
}

export interface ProgressBarProps {
  progress: number;
  className?: string;
  showPercentage?: boolean;
  color?: 'blue' | 'green' | 'purple';
}

export interface FloatingDotsProps {
  className?: string;
  color?: 'blue' | 'green' | 'purple' | 'gray';
}

export interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
  className?: string;
}

// Common UI Types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface InteractiveComponentProps extends BaseComponentProps {
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
}

export interface FormComponentProps extends BaseComponentProps {
  name?: string;
  value?: any;
  onChange?: (value: any) => void;
  onBlur?: () => void;
  onFocus?: () => void;
  error?: string;
  required?: boolean;
  disabled?: boolean;
}

// Animation Types
export interface AnimationProps {
  initial?: any;
  animate?: any;
  exit?: any;
  transition?: any;
  variants?: any;
}

// Theme Types
export type ColorVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
export type SizeVariant = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type VariantType = 'default' | 'outline' | 'ghost' | 'link' | 'destructive';

// Responsive Types
export interface ResponsiveProps {
  sm?: any;
  md?: any;
  lg?: any;
  xl?: any;
}

// Accessibility Types
export interface AccessibilityProps {
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  'aria-expanded'?: boolean;
  'aria-hidden'?: boolean;
  role?: string;
  tabIndex?: number;
}

// Event Handler Types
export type ClickHandler<TElement = HTMLElement> = (
  event: React.MouseEvent<TElement>,
) => void;
export type KeyboardHandler<TElement = HTMLElement> = (
  event: React.KeyboardEvent<TElement>,
) => void;
export type FocusHandler<TElement = HTMLElement> = (
  event: React.FocusEvent<TElement>,
) => void;
export type ChangeHandler<T = any> = (value: T) => void;

// Component State Types
export interface LoadingState {
  isLoading: boolean;
  error: Error | null;
  data: any;
}

export interface AsyncState<T = any> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

// Form Types
export interface FormFieldProps extends FormComponentProps {
  label?: string;
  placeholder?: string;
  helperText?: string;
  validation?: {
    required?: boolean;
    minLength?: number;
    maxLength?: number;
    pattern?: RegExp;
    custom?: (value: any) => string | null;
  };
}

// Modal/Dialog Types
export interface ModalProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
}

// Notification Types
export interface NotificationProps {
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// Export utility types
export type ComponentVariant<T extends string> = T;
export type ComponentSize<T extends string> = T;
export type ComponentColor<T extends string> = T;