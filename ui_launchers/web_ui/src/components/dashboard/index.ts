/**
 * Dashboard components exports
 */

import { export { DashboardContainer } from './DashboardContainer';
import { export { WidgetBase } from './WidgetBase';
import { export { DraggableWidget } from './DraggableWidget';
export { 
  widgetRegistry,
  getWidgetComponent,
  getWidgetDefaultConfig,
  getAvailableWidgetTypes,
  getWidgetInfo,
  createWidgetConfig
import { } from './WidgetRegistry';

// Dashboard customization components
import { export { TimeRangeSelector } from './TimeRangeSelector';
import { export { DashboardFilters } from './DashboardFilters';
import { export { DashboardTemplateSelector } from './DashboardTemplateSelector';
import { export { DashboardExportImport } from './DashboardExportImport';

import { export type { WidgetBaseProps } from './WidgetBase';