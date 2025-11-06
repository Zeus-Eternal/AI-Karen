/**
 * Dashboard components exports
 */

// Main dashboards
export { default as Dashboard } from './Dashboard';
export { default as ProductionDashboard } from './ProductionDashboard';

// Dashboard infrastructure
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

// Widgets
export * from './widgets';

// Types
export type { WidgetBaseProps } from './WidgetBase';
