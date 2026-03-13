/**
 * Memory Management Module
 * Exports all memory management components and utilities
 */

// Main components
export { MemoryManagement } from './MemoryManagement';

// UI components
export { MemoryCard } from './ui/MemoryCard';
export { MemoryFilters as MemoryFiltersComponent } from './ui/MemoryFilters';
export { MemoryDetails } from './ui/MemoryDetails';
export { MemoryActions } from './ui/MemoryActions';
export { MemoryStatistics as MemoryStatisticsComponent } from './ui/MemoryStatistics';
export { MemoryOrganization } from './ui/MemoryOrganization';
export { MemoryImportExport } from './ui/MemoryImportExport';
export { MemoryCleanup } from './ui/MemoryCleanup';

// Services
export { memoryApi } from './services/memoryApi';

// Store
export { useMemoryStore } from './store/memoryStore';

// Types
export type {
  Memory,
  MemoryType,
  MemoryStatus,
  MemoryPriority,
  MemorySource,
  MemoryMetadata,
  MemoryFilters as MemoryFiltersType,
  MemorySortOptions,
  MemoryListResponse,
  MemoryStatistics,
  MemoryUpdateEvent,
  MemoryAction,
  MemoryActionPayload,
  MemoryManagementState,
  MemoryManagementActions,
  MemoryManagementStore,
  MemoryManagementProps,
  MemoryCardProps,
  MemoryDetailsProps,
  MemoryFiltersComponentProps,
  MemoryActionsProps,
  MemoryStatisticsProps,
  MemoryOrganizationProps,
  MemoryImportExportProps,
  MemoryCleanupProps,
  MemorySearchResult,
  MemorySearchResponse,
  MemoryExportOptions,
  MemoryImportOptions,
  MemoryCleanupOptions,
  MemoryCleanupResult,
} from './types';