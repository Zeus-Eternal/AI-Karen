/**
 * UI Components Index
 * 
 * Centralized exports for all UI components maintaining Next.js consistency
 * and React component architecture patterns
 */

// Core UI Components (shadcn/ui based)
import { export { Button, type ButtonProps } from './button';
import { export { Input, type InputProps } from './input';
import { export { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './card';
import { export { Badge, type BadgeProps } from './badge';
import { export { Separator } from './separator';
import { export { ScrollArea } from './scroll-area';
import { export { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs';
import { export { Progress } from './progress';
import { export { Skeleton } from './skeleton';
import { export { Toaster } from './toaster';
import { export { useToast, toast } from '../../hooks/use-toast';

// Enhanced UI Components
export { 
import { } from './loading-states';

export {
  default as Loading,
  withLoading,
  useLoadingState
import { } from './loading';

export {
import { } from './error-boundary';

export {
import { } from './touch-interactions';

export {
import { } from './suggested-actions';

// Modern Layout System Components
export {
  useContainerQuery,
  useContainerSize,
  type GridContainerProps,
  type FlexContainerProps,
  type FlexItemProps,
  type ResponsiveContainerProps,
  type ContainerBreakpoints,
  type ContainerSize,
  type ResponsiveValue,
import { } from './layout';

// Component Types
export type {
import { } from './types';

// Right Panel Components
export {
  useRightPanel,
  type RightPanelProps,
  type RightPanelView,
  type RightPanelHeaderProps,
  type RightPanelContentProps,
  type RightPanelNavigationProps,
import { } from './right-panel';

// Panel Components
export {
  type PanelHeaderProps,
import { } from './panel-header';

export {
  type PanelContentProps,
  type PanelSectionProps,
import { } from './panel-content';

export {
  type PanelContentProps as PanelContentPropsBase,
import { } from './panel-content';

// Re-export commonly used types
import { export type { VariantProps } from 'class-variance-authority';
import { export type { LucideIcon } from 'lucide-react';