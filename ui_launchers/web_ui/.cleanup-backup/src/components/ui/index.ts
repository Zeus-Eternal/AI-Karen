/**
 * UI Components Index
 * 
 * Centralized exports for all UI components maintaining Next.js consistency
 * and React component architecture patterns
 */

// Core UI Components (shadcn/ui based)
export { Button, type ButtonProps } from './button';
export { Input, type InputProps } from './input';
export { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './card';
export { Badge, type BadgeProps } from './badge';
export { Separator } from './separator';
export { ScrollArea } from './scroll-area';
export { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs';
export { Progress } from './progress';
export { Skeleton } from './skeleton';
export { Toaster } from './toaster';
export { useToast, toast } from '../../hooks/use-toast';

// Enhanced UI Components
export { 
  LoadingSpinner,
  MessageSkeleton,
  ChatLoadingSkeleton,
  PulseLoader,
  Shimmer,
  LoadingCard,
  ProgressBar,
  FloatingDots,
  LoadingOverlay
} from './loading-states';

export {
  default as Loading,
  PageLoading,
  ComponentLoading,
  ChatLoading,
  withLoading,
  SuspenseWrapper,
  useLoadingState
} from './loading';

export {
  ErrorBoundary
} from './error-boundary';

export {
  TouchButton,
  SwipeableCard,
  PullToRefresh,
  FloatingActionButton,
  TouchSlider,
  TouchMenu
} from './touch-interactions';

export {
  SuggestedActions
} from './suggested-actions';

// Modern Layout System Components
export {
  GridContainer,
  TwoColumnGrid,
  ThreeColumnGrid,
  AutoFitGrid,
  ResponsiveCardGrid,
  DashboardGrid,
  FlexContainer,
  HStack,
  VStack,
  Center,
  SpaceBetween,
  ResponsiveFlex,
  FlexItem,
  ResponsiveContainer,
  PageContainer,
  SectionContainer,
  CardContainer,
  SidebarContainer,
  ContentContainer,
  useContainerQuery,
  useContainerSize,
  type GridContainerProps,
  type FlexContainerProps,
  type FlexItemProps,
  type ResponsiveContainerProps,
  type ContainerBreakpoints,
  type ContainerSize,
  type ResponsiveValue,
} from './layout';

// Component Types
export type {
  LoadingProps,
  ErrorBoundaryProps,
  SuggestedActionsProps
} from './types';

// Right Panel Components
export {
  RightPanel,
  RightPanelHeader,
  RightPanelContent,
  RightPanelNavigation,
  useRightPanel,
  type RightPanelProps,
  type RightPanelView,
  type RightPanelHeaderProps,
  type RightPanelContentProps,
  type RightPanelNavigationProps,
} from './right-panel';

// Panel Components
export {
  PanelHeader,
  type PanelHeaderProps,
} from './panel-header';

export {
  PanelContent,
  PanelSection,
  type PanelContentProps,
  type PanelSectionProps,
} from './panel-content';

export {
  type PanelContentProps as PanelContentPropsBase,
} from './panel-content';

// Re-export commonly used types
export type { VariantProps } from 'class-variance-authority';
export type { LucideIcon } from 'lucide-react';