/**
 * Memory Management Types
 * TypeScript interfaces for the CoPilot Memory Management System
 */

// Memory type enumeration
export type MemoryType = 'conversation' | 'case' | 'unified' | 'fact' | 'preference' | 'context';

// Memory status enumeration
export type MemoryStatus = 'active' | 'archived' | 'deleted' | 'processing';

// Memory priority enumeration
export type MemoryPriority = 'low' | 'medium' | 'high' | 'critical';

// Memory source enumeration
export type MemorySource = 'user-input' | 'conversation' | 'document' | 'api' | 'system' | 'import';

// Memory metadata
export interface MemoryMetadata {
  source?: MemorySource;
  context?: string;
  relatedIds?: string[];
  conversationId?: string;
  caseId?: string;
  userId?: string;
  sessionId?: string;
  tenantId?: string;
  extractionMethod?: string;
  confidence?: number;
  importance?: number;
  tags?: string[];
  category?: string;
  folder?: string;
  collection?: string;
  checksum?: string;
  version?: number;
  parentMemoryId?: string;
  childMemoryIds?: string[];
  linkedMemories?: string[];
  accessCount?: number;
  lastAccessed?: Date;
  expiresAt?: Date;
  retentionPeriod?: number; // in days
  isEncrypted?: boolean;
  encryptionKey?: string;
  processingStatus?: 'pending' | 'processing' | 'completed' | 'failed';
  processingError?: string;
  indexingStatus?: 'pending' | 'indexing' | 'indexed' | 'failed';
  vectorEmbedding?: number[];
  semanticSummary?: string;
  language?: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
  emotion?: string;
  entities?: Array<{
    type: string;
    value: string;
    confidence: number;
  }>;
  topics?: Array<{
    name: string;
    confidence: number;
  }>;
}

// Main memory interface
export interface Memory {
  id: string;
  title?: string;
  content: string;
  type: MemoryType;
  status: MemoryStatus;
  priority: MemoryPriority;
  createdAt: Date;
  updatedAt: Date;
  accessedAt?: Date;
  expiresAt?: Date;
  metadata: MemoryMetadata;
  size: number; // in bytes
  hash: string;
  version: number;
  userId: string;
  tenantId?: string;
}

// Memory filter options
export interface MemoryFilters {
  type?: MemoryType[];
  status?: MemoryStatus[];
  priority?: MemoryPriority[];
  source?: MemorySource[];
  category?: string[];
  tags?: string[];
  folder?: string[];
  collection?: string[];
  userId?: string[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  search?: string;
  contentSearch?: string;
  metadataSearch?: string;
  minConfidence?: number;
  maxConfidence?: number;
  minImportance?: number;
  maxImportance?: number;
  hasAttachments?: boolean;
  isEncrypted?: boolean;
  isExpired?: boolean;
  isNearExpiry?: boolean; // within 7 days
  minAccessCount?: number;
  maxAccessCount?: number;
}

// Memory sort options
export interface MemorySortOptions {
  field: 'createdAt' | 'updatedAt' | 'accessedAt' | 'priority' | 'confidence' | 'importance' | 'size' | 'accessCount' | 'title';
  direction: 'asc' | 'desc';
}

// Memory list response
export interface MemoryListResponse {
  memories: Memory[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
  facets?: {
    types: Record<MemoryType, number>;
    statuses: Record<MemoryStatus, number>;
    priorities: Record<MemoryPriority, number>;
    sources: Record<MemorySource, number>;
    categories: Record<string, number>;
    tags: Record<string, number>;
    folders: Record<string, number>;
    collections: Record<string, number>;
  };
}

// Memory statistics
export interface MemoryStatistics {
  total: number;
  byType: Record<MemoryType, number>;
  byStatus: Record<MemoryStatus, number>;
  byPriority: Record<MemoryPriority, number>;
  bySource: Record<MemorySource, number>;
  totalSize: number; // in bytes
  averageSize: number; // in bytes
  oldestMemory?: Date;
  newestMemory?: Date;
  averageConfidence: number;
  averageImportance: number;
  totalAccessCount: number;
  averageAccessCount: number;
  expiredCount: number;
  nearExpiryCount: number;
  encryptedCount: number;
  processingCount: number;
  indexedCount: number;
  retentionStats: {
    expiredLastMonth: number;
    expiringNextMonth: number;
    averageRetentionDays: number;
  };
  usageStats: {
    memoriesCreatedToday: number;
    memoriesCreatedThisWeek: number;
    memoriesCreatedThisMonth: number;
    memoriesAccessedToday: number;
    memoriesAccessedThisWeek: number;
    memoriesAccessedThisMonth: number;
  };
  storageStats: {
    totalStorageUsed: number;
    storageByType: Record<MemoryType, number>;
    storageGrowthRate: number; // percentage per month
    projectedStorageUsage: number; // in 6 months
  };
}

// Real-time memory update event
export interface MemoryUpdateEvent {
  type: 'memory_created' | 'memory_updated' | 'memory_deleted' | 'memory_accessed' | 'memory_archived' | 'memory_restored';
  memoryId: string;
  memory?: Memory;
  timestamp: Date;
  userId?: string;
  changes?: Partial<Memory>;
}

// Memory action types
export type MemoryAction = 'view' | 'edit' | 'delete' | 'archive' | 'restore' | 'export' | 'tag' | 'move' | 'copy' | 'encrypt' | 'decrypt' | 'reindex' | 'process';

// Memory action payload
export interface MemoryActionPayload {
  memoryId: string;
  action: MemoryAction;
  data?: Record<string, unknown> | unknown;
}

// Memory management store state
export interface MemoryManagementState {
  // Memories
  memories: Memory[];
  selectedMemory: Memory | null;
  isLoading: boolean;
  error: string | null;
  
  // Filters and sorting
  filters: MemoryFilters;
  sortOptions: MemorySortOptions;
  
  // Real-time updates
  isRealTimeEnabled: boolean;
  lastUpdate: Date | null;
  
  // Statistics
  statistics: MemoryStatistics | null;
  
  // UI state
  showDetails: boolean;
  showFilters: boolean;
  viewMode: 'list' | 'grid' | 'kanban' | 'timeline';
  
  // Selection
  selectedMemories: string[];
  
  // Pagination
  currentPage: number;
  pageSize: number;
  total: number;
  hasMore: boolean;
  
  // Search
  searchQuery: string;
  searchResults: Memory[];
  isSearching: boolean;
  
  // Organization
  folders: string[];
  collections: string[];
  tags: string[];
  categories: string[];
}

// Memory management store actions
export interface MemoryManagementActions {
  // Memory operations
  fetchMemories: (filters?: MemoryFilters, sort?: MemorySortOptions, page?: number, pageSize?: number) => Promise<void>;
  fetchMemory: (memoryId: string) => Promise<void>;
  createMemory: (memory: Omit<Memory, 'id' | 'createdAt' | 'updatedAt' | 'hash' | 'version'>) => Promise<void>;
  updateMemory: (memoryId: string, updates: Partial<Memory>) => Promise<void>;
  deleteMemory: (memoryId: string) => Promise<void>;
  executeMemoryAction: (payload: MemoryActionPayload) => Promise<void>;
  
  // Bulk operations
  bulkUpdateMemories: (memoryIds: string[], updates: Partial<Memory>) => Promise<void>;
  bulkDeleteMemories: (memoryIds: string[]) => Promise<void>;
  bulkArchiveMemories: (memoryIds: string[]) => Promise<void>;
  bulkRestoreMemories: (memoryIds: string[]) => Promise<void>;
  bulkExportMemories: (memoryIds: string[], format?: 'json' | 'csv' | 'xlsx') => Promise<void>;
  
  // Search
  searchMemories: (query: string, filters?: MemoryFilters) => Promise<void>;
  clearSearch: () => void;
  
  // Filters and sorting
  setFilters: (filters: MemoryFilters) => void;
  setSortOptions: (sortOptions: MemorySortOptions) => void;
  clearFilters: () => void;
  
  // Real-time updates
  enableRealTimeUpdates: () => void;
  disableRealTimeUpdates: () => void;
  handleRealTimeUpdate: (event: MemoryUpdateEvent) => void;
  
  // Statistics
  fetchStatistics: () => Promise<void>;
  
  // Organization
  fetchFolders: () => Promise<void>;
  fetchCollections: () => Promise<void>;
  fetchTags: () => Promise<void>;
  fetchCategories: () => Promise<void>;
  createFolder: (name: string) => Promise<void>;
  createCollection: (name: string) => Promise<void>;
  
  // Selection
  selectMemory: (memoryId: string) => void;
  selectMultipleMemories: (memoryIds: string[]) => void;
  deselectMemory: (memoryId: string) => void;
  clearSelection: () => void;
  selectAll: () => void;
  
  // UI state
  setSelectedMemory: (memory: Memory | null) => void;
  setShowDetails: (show: boolean) => void;
  setShowFilters: (show: boolean) => void;
  setViewMode: (mode: 'list' | 'grid' | 'kanban' | 'timeline') => void;
  
  // Pagination
  setCurrentPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  
  // Utility
  clearError: () => void;
  reset: () => void;
}

// Memory management store (combined state and actions)
export type MemoryManagementStore = MemoryManagementState & MemoryManagementActions;

// Props for MemoryManagement component
export interface MemoryManagementProps {
  className?: string;
  onMemorySelect?: (memory: Memory) => void;
  onMemoryAction?: (payload: MemoryActionPayload) => void;
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
  enableRealTimeUpdates?: boolean;
  defaultViewMode?: 'list' | 'grid' | 'kanban' | 'timeline';
  showStatistics?: boolean;
  showOrganization?: boolean;
  showAdvancedFilters?: boolean;
  maxMemoryItems?: number;
}

// Props for MemoryCard component
export interface MemoryCardProps {
  memory: Memory;
  onSelect?: (memory: Memory) => void;
  onAction?: (payload: MemoryActionPayload) => void;
  isSelected?: boolean;
  showMetadata?: boolean;
  compact?: boolean;
  className?: string;
}

// Props for MemoryDetails component
export interface MemoryDetailsProps {
  memory: Memory;
  onClose?: () => void;
  onAction?: (payload: MemoryActionPayload) => void;
  onEdit?: (memory: Memory) => void;
  showActions?: boolean;
  className?: string;
}

// Props for MemoryFilters component
export interface MemoryFiltersComponentProps {
  filters: MemoryFilters;
  onFiltersChange: (filters: MemoryFilters) => void;
  onClear: () => void;
  folders?: string[];
  collections?: string[];
  tags?: string[];
  categories?: string[];
  className?: string;
}

// Props for MemoryActions component
export interface MemoryActionsProps {
  memory: Memory;
  onAction: (payload: MemoryActionPayload) => void;
  compact?: boolean;
  showBulkActions?: boolean;
  selectedCount?: number;
  className?: string;
}

// Props for MemoryStatistics component
export interface MemoryStatisticsProps {
  statistics: MemoryStatistics;
  className?: string;
  showCharts?: boolean;
  showDetails?: boolean;
}

// Props for MemoryOrganization component
export interface MemoryOrganizationProps {
  folders: string[];
  collections: string[];
  tags: string[];
  categories: string[];
  onFolderCreate: (name: string) => void;
  onCollectionCreate: (name: string) => void;
  onFolderSelect: (folder: string) => void;
  onCollectionSelect: (collection: string) => void;
  onTagSelect: (tag: string) => void;
  onCategorySelect: (category: string) => void;
  className?: string;
}

// Props for MemoryImportExport component
export interface MemoryImportExportProps {
  onImport: (file: File) => Promise<void>;
  onExport: (format: 'json' | 'csv' | 'xlsx', memoryIds?: string[]) => Promise<void>;
  className?: string;
}

// Props for MemoryCleanup component
export interface MemoryCleanupProps {
  onCleanup: (options: {
    expired: boolean;
    duplicates: boolean;
    lowConfidence: boolean;
    lowImportance: boolean;
    minConfidence: number;
    minImportance: number;
    olderThan: Date;
  }) => Promise<MemoryCleanupResult>;
  className?: string;
}

// Memory search result
export interface MemorySearchResult {
  memory: Memory;
  score: number;
  highlights: Array<{
    field: string;
    fragments: string[];
  }>;
}

// Memory search response
export interface MemorySearchResponse {
  results: MemorySearchResult[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
  suggestions?: string[];
  facets?: Record<string, Record<string, number>>;
}

// Memory export options
export interface MemoryExportOptions {
  format: 'json' | 'csv' | 'xlsx';
  includeMetadata: boolean;
  includeContent: boolean;
  filters?: MemoryFilters;
  memoryIds?: string[];
  compress: boolean;
  encrypt: boolean;
  password?: string;
}

// Memory import options
export interface MemoryImportOptions {
  format: 'json' | 'csv' | 'xlsx';
  overwriteExisting: boolean;
  validateData: boolean;
  assignToUser?: string;
  defaultType?: MemoryType;
  defaultStatus?: MemoryStatus;
  defaultPriority?: MemoryPriority;
  defaultFolder?: string;
  defaultCollection?: string;
  defaultTags?: string[];
  defaultCategory?: string;
}

// Memory cleanup options
export interface MemoryCleanupOptions {
  expired: boolean;
  duplicates: boolean;
  lowConfidence: boolean;
  lowImportance: boolean;
  minConfidence: number;
  minImportance: number;
  olderThan: Date;
  dryRun: boolean;
  batchSize: number;
  [key: string]: unknown; // Index signature for API compatibility
}

// Memory cleanup result
export interface MemoryCleanupResult {
  deletedCount: number;
  archivedCount: number;
  errors: string[];
  duplicatesFound: number;
  spaceFreed: number; // in bytes
  duration: number; // in milliseconds
}
