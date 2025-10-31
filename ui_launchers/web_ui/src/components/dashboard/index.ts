/**
 * Dashboard components exports
 */

export { DashboardContainer } from './DashboardContainer';
export { WidgetBase } from './WidgetBase';
export { DraggableWidget } from './DraggableWidget';
export { 
  widgetRegistry,
  getWidgetComponent,
  getWidgetDefaultConfig,
  getAvailableWidgetTypes,
  getWidgetInfo,
  createWidgetConfig
} from './WidgetRegistry';

// Dashboard customization components
export { TimeRangeSelector } from './TimeRangeSelector';
export { DashboardFilters } from './DashboardFilters';
export { DashboardTemplateSelector } from './DashboardTemplateSelector';
export { DashboardExportImport } from './DashboardExportImport';

export type { WidgetBaseProps } from './WidgetBase';