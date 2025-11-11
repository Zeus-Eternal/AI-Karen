/**
 * Memory Management Types
 * Comprehensive type definitions for memory analytics, search, and management
 */

// Core memory types (extending existing backend types)
export interface MemoryEntry {
  id: string;
  content: string;
  metadata: Record<string, unknown>;
  timestamp: number;
  similarity_score?: number;
  tags: string[];
  user_id?: string;
  session_id?: string;
  type?: "fact" | "preference" | "context";
  confidence?: number;
  semantic_cluster?: string;
  relationships?: string[];
  last_accessed?: string;
  relevance_score?: number;
}

export interface MemoryQuery {
  text: string;
  user_id?: string;
  session_id?: string;
  tags?: string[];
  metadata_filter?: Record<string, unknown>;
  time_range?: [Date, Date];
  top_k?: number;
  similarity_threshold?: number;
}

// Memory Analytics Types
export interface VectorStoreStats {
  totalEmbeddings: number;
  storageSize: number;
  averageLatency: number;
  searchAccuracy: number;
  memoryDecay: DecayPattern[];
  embeddingDimensions: number;
  indexType: string;
  lastUpdated: Date;
}

export interface DecayPattern {
  timeRange: string;
  retentionRate: number;
  accessFrequency: number;
  forgettingCurve: number;
}

export interface MemoryAnalytics {
  vectorStore: VectorStoreStats;
  usage: MemoryUsageStats;
  performance: MemoryPerformanceStats;
  content: MemoryContentStats;
  trends: MemoryTrendData;
}

export interface MemoryUsageStats {
  totalMemories: number;
  memoriesByType: Record<string, number>;
  memoriesByCluster: Record<string, number>;
  memoriesByAge: Array<{ range: string; count: number }>;
  storageBreakdown: {
    embeddings: number;
    metadata: number;
    content: number;
    indices: number;
  };
  growthTrend: Array<{ date: string; count: number; size: number }>;
}

export interface MemoryPerformanceStats {
  searchLatency: {
    average: number;
    p50: number;
    p95: number;
    p99: number;
  };
  indexingLatency: {
    average: number;
    p95: number;
  };
  throughput: {
    searchesPerSecond: number;
    indexingPerSecond: number;
  };
  cacheHitRate: number;
  errorRate: number;
}

export interface MemoryContentStats {
  confidenceDistribution: Array<{ range: string; count: number }>;
  tagDistribution: Array<{ tag: string; count: number; percentage: number }>;
  clusterDistribution: Array<{
    cluster: string;
    count: number;
    avgConfidence: number;
  }>;
  contentTypes: Array<{ type: string; count: number; avgSize: number }>;
  relationshipStats: {
    totalConnections: number;
    avgConnectionsPerMemory: number;
    stronglyConnectedClusters: number;
  };
}

export interface MemoryTrendData {
  accessPatterns: Array<{ date: string; count: number; uniqueUsers: number }>;
  creationPatterns: Array<{
    date: string;
    count: number;
    avgConfidence: number;
  }>;
  searchPatterns: Array<{ date: string; queries: number; avgLatency: number }>;
  retentionCurve: Array<{ age: number; retentionRate: number }>;
}

// Memory Search Types
export interface MemorySearchOptions {
  topK?: number;
  similarityThreshold?: number;
  tags?: string[];
  timeRange?: [Date, Date];
  includeMetadata?: boolean;
  contentType?: string;
  minConfidence?: number;
  clusters?: string[];
  sortBy?: "relevance" | "date" | "confidence" | "access_count";
  sortOrder?: "asc" | "desc";
}

export interface MemorySearchResult {
  memories: MemoryEntry[];
  totalFound: number;
  searchTime: number;
  facets: SearchFacets;
  suggestions: string[];
  relatedQueries: string[];
}

export interface SearchFacets {
  types: Array<{ type: string; count: number }>;
  tags: Array<{ tag: string; count: number }>;
  clusters: Array<{ cluster: string; count: number }>;
  timeRanges: Array<{ range: string; count: number }>;
  confidenceRanges: Array<{ range: string; count: number }>;
}

export interface MemorySearchHistory {
  id: string;
  query: string;
  timestamp: Date;
  resultCount: number;
  filters: MemorySearchOptions;
  userId: string;
}

export interface SavedSearch {
  id: string;
  name: string;
  query: string;
  filters: MemorySearchOptions;
  userId: string;
  createdAt: Date;
  lastUsed: Date;
  useCount: number;
}

// Memory Network Types
export interface MemoryNetworkNode {
  id: string;
  label: string;
  content: string;
  type: string;
  confidence: number;
  cluster: string;
  size: number;
  color: string;
  position?: { x: number; y: number };
  metadata: Record<string, unknown>;
  tags: string[];
}

export interface MemoryNetworkEdge {
  id: string;
  source: string;
  target: string;
  weight: number;
  type: "semantic" | "temporal" | "explicit" | "inferred";
  confidence: number;
  metadata?: Record<string, unknown>;
}

export interface MemoryNetworkData {
  nodes: MemoryNetworkNode[];
  edges: MemoryNetworkEdge[];
  clusters: MemoryCluster[];
  statistics: NetworkStatistics;
}

export interface MemoryCluster {
  id: string;
  name: string;
  nodes: string[];
  centroid: { x: number; y: number };
  color: string;
  size: number;
  density: number;
  coherence: number;
  topics: string[];
}

export interface NetworkStatistics {
  nodeCount: number;
  edgeCount: number;
  clusterCount: number;
  averageConnectivity: number;
  networkDensity: number;
  modularity: number;
  smallWorldCoefficient: number;
}

// Memory Management Types
export interface MemoryValidationResult {
  isValid: boolean;
  issues: ValidationIssue[];
  suggestions: string[];
  confidence: number;
}

export interface ValidationIssue {
  type:
    | "duplicate"
    | "inconsistency"
    | "corruption"
    | "low_quality"
    | "orphaned";
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  affectedMemories: string[];
  suggestedAction: string;
}

export interface MemoryBatchOperation {
  type: "delete" | "update" | "merge" | "tag" | "cluster";
  memoryIds: string[];
  parameters: Record<string, unknown>;
  userId: string;
  timestamp: Date;
}

export interface MemoryBatchResult {
  operationId: string;
  success: boolean;
  processedCount: number;
  failedCount: number;
  errors: Array<{ memoryId: string; error: string }>;
  warnings: string[];
  duration: number;
}

export interface MemoryBackup {
  id: string;
  name: string;
  description?: string;
  userId: string;
  createdAt: Date;
  memoryCount: number;
  size: number;
  version: string;
  metadata: Record<string, unknown>;
}

export interface MemoryRestoreOptions {
  backupId: string;
  overwriteExisting: boolean;
  preserveIds: boolean;
  filterOptions?: {
    types?: string[];
    tags?: string[];
    dateRange?: [Date, Date];
  };
}

// UI Component Props Types
export interface MemoryAnalyticsProps {
  userId: string;
  tenantId?: string;
  timeRange?: [Date, Date];
  refreshInterval?: number;
  height?: number;
  onError?: (error: Error) => void;
}

export interface MemorySearchProps {
  userId: string;
  tenantId?: string;
  initialQuery?: string;
  onMemorySelect?: (memory: MemoryEntry) => void;
  onSearchComplete?: (result: MemorySearchResult) => void;
  height?: number;
}

export interface MemoryNetworkProps {
  userId: string;
  tenantId?: string;
  onNodeSelect?: (node: MemoryNetworkNode) => void;
  onNodeDoubleClick?: (node: MemoryNetworkNode) => void;
  onClusterSelect?: (cluster: MemoryCluster) => void;
  height?: number;
  width?: number;
}

export interface MemoryEditorProps {
  memory?: MemoryEntry;
  onSave: (memory: Partial<MemoryEntry>) => Promise<void>;
  onCancel: () => void;
  onDelete?: (memoryId: string) => Promise<void>;
  isOpen: boolean;
  userId: string;
  tenantId?: string;
}

// API Response Types
export interface MemoryAnalyticsResponse {
  analytics: MemoryAnalytics;
  timestamp: Date;
  userId: string;
  tenantId?: string;
}

export interface MemorySearchResponse {
  result: MemorySearchResult;
  query: string;
  options: MemorySearchOptions;
  timestamp: Date;
}

export interface MemoryNetworkResponse {
  network: MemoryNetworkData;
  query?: string;
  filters?: Record<string, unknown>;
  timestamp: Date;
}

// Error Types
export interface MemoryError extends Error {
  type:
    | "MEMORY_NOT_FOUND"
    | "SEARCH_FAILED"
    | "ANALYTICS_ERROR"
    | "NETWORK_ERROR"
    | "VALIDATION_ERROR";
  memoryId?: string;
  userId?: string;
  details?: Record<string, unknown>;
}

// Utility Types
export type MemoryTimeRange =
  | "1h"
  | "24h"
  | "7d"
  | "30d"
  | "90d"
  | "1y"
  | "all";
export type MemoryViewMode = "grid" | "network" | "analytics" | "search";
export type MemorySortField =
  | "relevance"
  | "date"
  | "confidence"
  | "access_count"
  | "similarity";
export type MemorySortOrder = "asc" | "desc";
