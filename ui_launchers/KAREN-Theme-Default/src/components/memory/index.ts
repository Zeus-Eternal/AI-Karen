/**
 * Memory Component Exports
 *
 * Central barrel export for memory management components including analytics,
 * editing, visualization, network graphs, and search functionality.
 */

// Memory Analytics
export { default as MemoryAnalytics } from './MemoryAnalytics';
export type { MetricCardProps } from './MemoryAnalytics';

// Memory Editor
export { default as MemoryEditor } from './MemoryEditor';
export type {
  MemoryType as EditorMemoryType,
  MemoryGridRow as EditorMemoryGridRow,
  MemoryEditorProps,
  AISuggestionType,
  AISuggestion,
} from './MemoryEditor';

// Memory Grid
export { default as MemoryGrid } from './MemoryGrid';
export type {
  MemoryType as GridMemoryType,
  MemoryGridProps,
} from './MemoryGrid';

// Memory Interface
export { default as MemoryInterface } from './MemoryInterface';
export type {
  MemoryType as InterfaceMemoryType,
  MemoryGridRow as InterfaceMemoryGridRow,
  MemoryNetworkNode as InterfaceMemoryNetworkNode,
  MemoryAnalytics as InterfaceMemoryAnalytics,
  MemoryInterfaceProps,
  ViewMode,
} from './MemoryInterface';

// Memory Management Tools
export { default as MemoryManagementTools } from './MemoryManagementTools';
export type {
  BatchOperationConfig,
  ValidationConfig,
} from './MemoryManagementTools';

// Memory Network Graph
export { default as MemoryNetworkGraph } from './MemoryNetworkGraph';
export type {
  MemoryNetworkNode as GraphMemoryNetworkNode,
  NetworkConfig,
  TooltipData,
  FilterOptions,
} from './MemoryNetworkGraph';

// Memory Network Visualization
export { default as MemoryNetworkVisualization } from './MemoryNetworkVisualization';
export type {
  MemoryNetworkNode as VisualizationMemoryNetworkNode,
  MemoryNetworkEdge,
  MemoryNetworkData,
  MemoryNetworkVisualizationProps,
  XY,
} from './MemoryNetworkVisualization';

// Memory Search
export { default as MemorySearch } from './MemorySearch';
export type {
  SearchFilters,
  SearchSuggestion,
} from './MemorySearch';
