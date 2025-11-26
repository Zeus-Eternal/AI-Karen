/**
 * Layout Component Types
 * 
 * Centralized type definitions for all layout components to ensure consistency
 * and type safety across the application.
 */

import { ReactNode } from 'react';
import { LucideIcon } from 'lucide-react';

// Base Layout Types
export interface BaseLayoutProps {
  children: ReactNode;
  className?: string;
}

// AppShell Types
export interface AppShellProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'children'> {
  children: ReactNode;
  className?: string;
  sidebar?: ReactNode;
  header?: ReactNode;
  footer?: ReactNode;
  defaultSidebarOpen?: boolean;
  defaultSidebarCollapsed?: boolean;
  sidebarBreakpoint?: number;
  tabletBreakpoint?: number;
  persistSidebarState?: boolean;
  enableKeyboardShortcuts?: boolean;
  layout?: 'default' | 'grid';
}

export interface AppShellSidebarProps extends BaseLayoutProps {
  children: ReactNode;
}

export interface AppShellHeaderProps extends BaseLayoutProps {
  children: ReactNode;
}

export interface AppShellMainProps extends BaseLayoutProps {
  children: ReactNode;
}

export interface AppShellFooterProps extends BaseLayoutProps {
  children: ReactNode;
}

export interface AppShellContextType {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean | ((prev: boolean) => boolean)) => void;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (
    collapsed: boolean | ((prev: boolean) => boolean)
  ) => void;
  isMobile: boolean;
  isTablet: boolean;
  toggleSidebar: () => void;
  closeSidebar: () => void;
  openSidebar: () => void;
}

// ModernLayout Types
export type LayoutGap = "none" | "sm" | "md" | "lg" | "xl";
export type LayoutColumns =
  | "auto"
  | "1"
  | "2"
  | "3"
  | "4"
  | "5"
  | "6"
  | "auto-fit"
  | "auto-fill";

export type Breakpoint = "sm" | "md" | "lg" | "xl";
export type ResponsiveColumnCount = "1" | "2" | "3" | "4" | "5" | "6";

export interface LayoutGridProps extends BaseLayoutProps {
  columns?: LayoutColumns;
  gap?: LayoutGap;
  responsive?: boolean;
  responsiveColumns?: Partial<Record<Breakpoint, ResponsiveColumnCount>>;
  minItemWidth?: number;
  style?: React.CSSProperties;
}

export interface LayoutFlexProps extends BaseLayoutProps {
  direction?: "row" | "row-reverse" | "col" | "col-reverse";
  align?: "start" | "center" | "end" | "stretch" | "baseline";
  justify?: "start" | "center" | "end" | "between" | "around" | "evenly";
  wrap?: boolean | "nowrap" | "wrap" | "wrap-reverse";
  gap?: LayoutGap;
}

export interface LayoutSectionProps extends BaseLayoutProps {
  variant?: "default" | "card" | "glass";
  padding?: LayoutGap;
}

export interface LayoutHeaderProps extends BaseLayoutProps {
  title?: string;
  description?: string;
  actions?: ReactNode;
}

export interface LayoutContainerProps extends BaseLayoutProps {
  size?: "sm" | "md" | "lg" | "xl" | "full";
  centered?: boolean;
}

// Header Types
export interface HeaderProps {
  className?: string;
  sidebarCollapsed?: boolean;
}

// SidebarTypes
export interface NavItem {
  icon: LucideIcon;
  label: string;
  href: string;
  badge?: string;
  shortcut?: string;
}

export interface NavSection {
  section: string;
  items: NavItem[];
}

export interface ModernSidebarProps {
  className?: string;
}

// AuthenticatedHeader Types
export interface User {
  email?: string;
  userId?: string;
  roles?: string[] | string;
}

export interface UseAuthReturn {
  user: User | null;
  logout: () => void;
}

// DeveloperNav Types
export interface DeveloperNavProps {
  className?: string;
}

// Error Boundary Types
export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

// Hook Types
export interface UseErrorHandlerReturn {
  captureError: (error: Error) => void;
  resetError: () => void;
}

// Responsive Types
export interface ResponsiveConfig {
  mobile: number;
  tablet: number;
  desktop: number;
}

export interface ResponsiveState {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
}

// Theme Types
export interface ThemeConfig {
  mode: 'light' | 'dark' | 'system';
  primary?: string;
  secondary?: string;
  accent?: string;
}

export interface ThemeContextType {
  theme: ThemeConfig;
  setTheme: (theme: Partial<ThemeConfig>) => void;
  toggleTheme: () => void;
}

// Animation Types
export interface AnimationConfig {
  duration?: number;
  easing?: string;
  delay?: number;
}

export interface TransitionProps {
  in?: boolean;
  timeout?: number | { enter?: number; exit?: number };
  onEnter?: () => void;
  onEntering?: () => void;
  onEntered?: () => void;
  onExit?: () => void;
  onExiting?: () => void;
  onExited?: () => void;
}

// Utility Types
export type Omit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

// Event Handler Types
export type KeyboardEventHandler = (event: React.KeyboardEvent) => void;
export type MouseEventHandler = (event: React.MouseEvent) => void;
export type FocusEventHandler = (event: React.FocusEvent) => void;

// Ref Types
export type RefCallback<T> = (instance: T | null) => void;
export type RefObject<T> = React.MutableRefObject<T | null>;

// Component Props Common Patterns
export interface WithChildren {
  children: ReactNode;
}

export interface WithClassName {
  className?: string;
}

export interface WithStyle {
  style?: React.CSSProperties;
}

export interface WithTestId {
  'data-testid'?: string;
}

// Common Props Combinations
export interface StandardComponentProps extends WithChildren, WithClassName, WithStyle, WithTestId {}

// Layout Component Variants
export type LayoutVariant = 'default' | 'compact' | 'spacious' | 'minimal';
export type LayoutTheme = 'light' | 'dark' | 'auto';
export type LayoutDensity = 'comfortable' | 'compact' | 'spacious';

// Responsive Breakpoint Configuration
export interface Breakpoints {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
  '2xl': number;
}

// Spacing Scale
export type SpacingScale = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl';

// Color Scheme
export type ColorScheme = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';

// Component Size
export type ComponentSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

// Component State
export type ComponentState = 'default' | 'hover' | 'focus' | 'active' | 'disabled' | 'loading';

// Layout Direction
export type LayoutDirection = 'ltr' | 'rtl';

// Navigation Types
export interface NavigationItem {
  id: string;
  label: string;
  icon?: LucideIcon;
  href?: string;
  onClick?: () => void;
  disabled?: boolean;
  badge?: string | number;
  children?: NavigationItem[];
}

export interface NavigationSection {
  id: string;
  title?: string;
  items: NavigationItem[];
}

// Header Types
export interface HeaderAction {
  id: string;
  label: string;
  icon?: LucideIcon;
  onClick: () => void;
  disabled?: boolean;
  tooltip?: string;
}

export interface HeaderUser {
  name: string;
  email?: string;
  avatar?: string;
  initials?: string;
  role?: string;
}

// Footer Types
export interface FooterLink {
  label: string;
  href: string;
  external?: boolean;
}

export interface FooterSection {
  title: string;
  links: FooterLink[];
}

// Sidebar Types
export interface SidebarConfig {
  collapsible?: boolean;
  collapsed?: boolean;
  width?: number;
  collapsedWidth?: number;
  overlay?: boolean;
  position?: 'left' | 'right';
}

// Toast/Notification Types
export interface ToastProps {
  id: string;
  title?: string;
  description?: string;
  action?: ReactNode;
  variant?: 'default' | 'destructive' | 'success' | 'warning';
  duration?: number;
}

// Loading State Types
export interface LoadingState {
  isLoading: boolean;
  error?: Error | null;
  data?: Record<string, unknown> | Array<Record<string, unknown>> | null;
}

// Accessibility Types
export interface AriaAttributes {
  role?: string;
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  'aria-expanded'?: boolean;
  'aria-hidden'?: boolean;
  'aria-disabled'?: boolean;
  'aria-required'?: boolean;
  'aria-invalid'?: boolean;
}

// Focus Management Types
export interface FocusManager {
  focusFirst: () => void;
  focusLast: () => void;
  focusNext: () => void;
  focusPrevious: () => void;
  trapFocus: () => () => void;
}

// Keyboard Navigation Types
export interface KeyboardNavigationConfig {
  enabled?: boolean;
  loop?: boolean;
  orientation?: 'horizontal' | 'vertical' | 'both';
  activateOn?: 'click' | 'space' | 'enter' | 'both';
}

// Drag and Drop Types
export interface DraggableItem {
  id: string;
  type: string;
  data: Record<string, unknown>;
}

export interface DropZone {
  id: string;
  accepts: string[];
  onDrop: (item: DraggableItem) => void;
}

// Animation Presets
export interface AnimationPresets {
  fadeIn: AnimationConfig;
  slideIn: AnimationConfig;
  scaleIn: AnimationConfig;
  bounce: AnimationConfig;
  shake: AnimationConfig;
}

// Responsive Grid Types
export interface ResponsiveGridConfig {
  columns?: Partial<Record<Breakpoint, ResponsiveColumnCount>>;
  gap?: Partial<Record<Breakpoint, LayoutGap>>;
  minItemWidth?: number;
  maxItemWidth?: number;
}

// Flex Layout Types
export interface FlexLayoutConfig {
  direction?: Partial<Record<Breakpoint, LayoutFlexProps['direction']>>;
  align?: Partial<Record<Breakpoint, LayoutFlexProps['align']>>;
  justify?: Partial<Record<Breakpoint, LayoutFlexProps['justify']>>;
  wrap?: Partial<Record<Breakpoint, LayoutFlexProps['wrap']>>;
}

// Layout Spacing Types
export interface LayoutSpacing {
  padding?: Partial<Record<Breakpoint, SpacingScale>>;
  margin?: Partial<Record<Breakpoint, SpacingScale>>;
  gap?: Partial<Record<Breakpoint, SpacingScale>>;
}

// Component State Types
export interface ComponentStateConfig {
  default?: ComponentState;
  hover?: ComponentState;
  focus?: ComponentState;
  active?: ComponentState;
  disabled?: ComponentState;
  loading?: ComponentState;
}

// Layout Theme Types
export interface LayoutThemeConfig {
  colors?: {
    primary?: string;
    secondary?: string;
    background?: string;
    surface?: string;
    border?: string;
    text?: string;
    muted?: string;
    accent?: string;
    destructive?: string;
  };
  spacing?: LayoutSpacing;
  borderRadius?: Partial<Record<Breakpoint, SpacingScale>>;
  shadows?: {
    sm?: string;
    md?: string;
    lg?: string;
    xl?: string;
  };
  typography?: {
    fontFamily?: string;
    fontSize?: Partial<Record<Breakpoint, SpacingScale>>;
    fontWeight?: {
      normal?: number;
      medium?: number;
      semibold?: number;
      bold?: number;
    };
    lineHeight?: number;
  };
}

// Layout Config Types
export interface LayoutConfig {
  theme?: LayoutThemeConfig;
  responsive?: ResponsiveConfig;
  animations?: AnimationPresets;
  keyboard?: KeyboardNavigationConfig;
  accessibility?: {
    reduceMotion?: boolean;
    highContrast?: boolean;
    screenReader?: boolean;
  };
  breakpoints?: Breakpoints;
}

// Context Types
export interface LayoutContextType {
  config: LayoutConfig;
  updateConfig: (config: Partial<LayoutConfig>) => void;
  state: {
    isMobile: boolean;
    isTablet: boolean;
    isDesktop: boolean;
    sidebar: {
      open: boolean;
      collapsed: boolean;
    };
    theme: {
      mode: 'light' | 'dark' | 'system';
    };
  };
}

// Provider Props
export interface LayoutProviderProps {
  children: ReactNode;
  config?: Partial<LayoutConfig>;
}

// Hook Return Types
export interface UseLayoutReturn {
  config: LayoutConfig;
  updateConfig: (config: Partial<LayoutConfig>) => void;
  state: LayoutContextType['state'];
  actions: {
    toggleSidebar: () => void;
    openSidebar: () => void;
    closeSidebar: () => void;
    toggleTheme: () => void;
    setTheme: (theme: 'light' | 'dark' | 'system') => void;
  };
}

// Event Types
export interface LayoutEventMap {
  'sidebar:toggle': void;
  'sidebar:open': void;
  'sidebar:close': void;
  'sidebar:collapse': void;
  'sidebar:expand': void;
  'theme:change': { mode: 'light' | 'dark' | 'system' };
  'resize': { width: number; height: number };
  'keydown': KeyboardEvent;
  'focus': FocusEvent;
  'blur': FocusEvent;
}

// Component Ref Types
export interface LayoutComponentRefs {
  appShell?: HTMLDivElement;
  sidebar?: HTMLDivElement;
  header?: HTMLElement;
  main?: HTMLElement;
  footer?: HTMLElement;
}

// Performance Types
export interface LayoutPerformanceMetrics {
  renderTime: number;
  layoutShift: number;
  paintTime: number;
  interactionTime: number;
}

// Debug Types
export interface LayoutDebugOptions {
  enabled?: boolean;
  showGrid?: boolean;
  showSpacing?: boolean;
  showBreakpoints?: boolean;
  showPerformance?: boolean;
  showAccessibility?: boolean;
}

// Export all types for convenience
export type * from './layout-types';