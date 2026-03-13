/**
 * Memory Management API Service
 * Handles all API communications for the memory management system
 */

import { BaseApiClient } from '@/lib/base-api-client';
import {
  Memory,
  MemoryFilters,
  MemorySortOptions,
  MemoryListResponse,
  MemoryStatistics,
  MemoryActionPayload,
  MemoryUpdateEvent,
  MemorySearchResponse,
  MemoryExportOptions,
  MemoryImportOptions,
  MemoryCleanupOptions,
  MemoryCleanupResult,
  MemorySearchResult,
} from '../types';

// Define ApiResponse interface locally since it's not exported from base-api-client
interface ApiResponse<T = unknown> {
  data: T;
  status: number;
  headers: Headers;
  ok: boolean;
}

// Create a dedicated API client for memory management
const memoryApiClient = new BaseApiClient({
  baseUrl: process.env.NEXT_PUBLIC_MEMORY_API_BASE_URL || '/api/memory',
  timeout: 30000, // 30 seconds timeout for memory operations
  defaultHeaders: {
    'X-Memory-Client': 'karen-theme-default',
  },
});

/**
 * Memory Management API Service
 */
export class MemoryApiService {
  /**
   * Fetch memories with optional filters and sorting
   */
  static async fetchMemories(
    filters?: MemoryFilters,
    sort?: MemorySortOptions,
    page: number = 1,
    pageSize: number = 20
  ): Promise<ApiResponse<MemoryListResponse>> {
    const params: Record<string, string | number | boolean> = {
      page,
      pageSize,
    };

    // Add filters to params
    if (filters) {
      if (filters.type && filters.type.length > 0) {
        params.type = filters.type.join(',');
      }
      if (filters.status && filters.status.length > 0) {
        params.status = filters.status.join(',');
      }
      if (filters.priority && filters.priority.length > 0) {
        params.priority = filters.priority.join(',');
      }
      if (filters.source && filters.source.length > 0) {
        params.source = filters.source.join(',');
      }
      if (filters.category && filters.category.length > 0) {
        params.category = filters.category.join(',');
      }
      if (filters.tags && filters.tags.length > 0) {
        params.tags = filters.tags.join(',');
      }
      if (filters.folder && filters.folder.length > 0) {
        params.folder = filters.folder.join(',');
      }
      if (filters.collection && filters.collection.length > 0) {
        params.collection = filters.collection.join(',');
      }
      if (filters.userId && filters.userId.length > 0) {
        params.userId = filters.userId.join(',');
      }
      if (filters.dateRange) {
        params.dateFrom = filters.dateRange.start.toISOString();
        params.dateTo = filters.dateRange.end.toISOString();
      }
      if (filters.search) {
        params.search = filters.search;
      }
      if (filters.contentSearch) {
        params.contentSearch = filters.contentSearch;
      }
      if (filters.metadataSearch) {
        params.metadataSearch = filters.metadataSearch;
      }
      if (filters.minConfidence !== undefined) {
        params.minConfidence = filters.minConfidence;
      }
      if (filters.maxConfidence !== undefined) {
        params.maxConfidence = filters.maxConfidence;
      }
      if (filters.minImportance !== undefined) {
        params.minImportance = filters.minImportance;
      }
      if (filters.maxImportance !== undefined) {
        params.maxImportance = filters.maxImportance;
      }
      if (filters.hasAttachments !== undefined) {
        params.hasAttachments = filters.hasAttachments;
      }
      if (filters.isEncrypted !== undefined) {
        params.isEncrypted = filters.isEncrypted;
      }
      if (filters.isExpired !== undefined) {
        params.isExpired = filters.isExpired;
      }
      if (filters.isNearExpiry !== undefined) {
        params.isNearExpiry = filters.isNearExpiry;
      }
      if (filters.minAccessCount !== undefined) {
        params.minAccessCount = filters.minAccessCount;
      }
      if (filters.maxAccessCount !== undefined) {
        params.maxAccessCount = filters.maxAccessCount;
      }
    }

    // Add sorting to params
    if (sort) {
      params.sortBy = sort.field;
      params.sortOrder = sort.direction;
    }

    return memoryApiClient.get<MemoryListResponse>('/', { params });
  }

  /**
   * Fetch a single memory by ID
   */
  static async fetchMemory(memoryId: string): Promise<ApiResponse<Memory>> {
    return memoryApiClient.get<Memory>(`/${memoryId}`);
  }

  /**
   * Create a new memory
   */
  static async createMemory(memory: Omit<Memory, 'id' | 'createdAt' | 'updatedAt' | 'hash' | 'version'>): Promise<ApiResponse<Memory>> {
    return memoryApiClient.post<Memory>('/', memory);
  }

  /**
   * Update an existing memory
   */
  static async updateMemory(memoryId: string, updates: Partial<Memory>): Promise<ApiResponse<Memory>> {
    return memoryApiClient.patch<Memory>(`/${memoryId}`, updates);
  }

  /**
   * Delete a memory
   */
  static async deleteMemory(memoryId: string): Promise<ApiResponse<void>> {
    return memoryApiClient.delete<void>(`/${memoryId}`);
  }

  /**
   * Execute an action on a memory
   */
  static async executeMemoryAction(payload: MemoryActionPayload): Promise<ApiResponse<Memory>> {
    return memoryApiClient.post<Memory>(`/${payload.memoryId}/actions`, {
      action: payload.action,
      data: payload.data,
    });
  }

  /**
   * Fetch memory statistics
   */
  static async fetchStatistics(): Promise<ApiResponse<MemoryStatistics>> {
    return memoryApiClient.get<MemoryStatistics>('/statistics');
  }

  /**
   * Search memories
   */
  static async searchMemories(
    query: string,
    filters?: MemoryFilters,
    page: number = 1,
    pageSize: number = 20
  ): Promise<ApiResponse<MemorySearchResponse>> {
    const params: Record<string, string | number | boolean> = {
      q: query,
      page,
      pageSize,
    };

    // Add filters to params
    if (filters) {
      if (filters.type && filters.type.length > 0) {
        params.type = filters.type.join(',');
      }
      if (filters.status && filters.status.length > 0) {
        params.status = filters.status.join(',');
      }
      if (filters.priority && filters.priority.length > 0) {
        params.priority = filters.priority.join(',');
      }
      if (filters.category && filters.category.length > 0) {
        params.category = filters.category.join(',');
      }
      if (filters.tags && filters.tags.length > 0) {
        params.tags = filters.tags.join(',');
      }
      if (filters.folder && filters.folder.length > 0) {
        params.folder = filters.folder.join(',');
      }
      if (filters.collection && filters.collection.length > 0) {
        params.collection = filters.collection.join(',');
      }
      if (filters.dateRange) {
        params.dateFrom = filters.dateRange.start.toISOString();
        params.dateTo = filters.dateRange.end.toISOString();
      }
      if (filters.minConfidence !== undefined) {
        params.minConfidence = filters.minConfidence;
      }
      if (filters.maxConfidence !== undefined) {
        params.maxConfidence = filters.maxConfidence;
      }
      if (filters.minImportance !== undefined) {
        params.minImportance = filters.minImportance;
      }
      if (filters.maxImportance !== undefined) {
        params.maxImportance = filters.maxImportance;
      }
    }

    return memoryApiClient.get<MemorySearchResponse>('/search', { params });
  }

  /**
   * Export memories
   */
  static async exportMemories(
    options: MemoryExportOptions,
    memoryIds?: string[]
  ): Promise<ApiResponse<Blob>> {
    const params: Record<string, string | number | boolean> = {
      format: options.format,
      includeMetadata: options.includeMetadata,
      includeContent: options.includeContent,
      compress: options.compress,
      encrypt: options.encrypt,
    };

    if (options.password) {
      params.password = options.password;
    }

    if (memoryIds && memoryIds.length > 0) {
      params.memoryIds = memoryIds.join(',');
    }

    // Add filters to params
    if (options.filters) {
      if (options.filters.type && options.filters.type.length > 0) {
        params.type = options.filters.type.join(',');
      }
      if (options.filters.status && options.filters.status.length > 0) {
        params.status = options.filters.status.join(',');
      }
      if (options.filters.priority && options.filters.priority.length > 0) {
        params.priority = options.filters.priority.join(',');
      }
      if (options.filters.dateRange) {
        params.dateFrom = options.filters.dateRange.start.toISOString();
        params.dateTo = options.filters.dateRange.end.toISOString();
      }
    }

    return memoryApiClient.get<Blob>('/export', { params });
  }

  /**
   * Import memories
   */
  static async importMemories(
    file: File,
    options: MemoryImportOptions
  ): Promise<ApiResponse<{ imported: number; errors: string[] }>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', options.format);
    formData.append('overwriteExisting', options.overwriteExisting.toString());
    formData.append('validateData', options.validateData.toString());

    if (options.assignToUser) {
      formData.append('assignToUser', options.assignToUser);
    }
    if (options.defaultType) {
      formData.append('defaultType', options.defaultType);
    }
    if (options.defaultStatus) {
      formData.append('defaultStatus', options.defaultStatus);
    }
    if (options.defaultPriority) {
      formData.append('defaultPriority', options.defaultPriority);
    }
    if (options.defaultFolder) {
      formData.append('defaultFolder', options.defaultFolder);
    }
    if (options.defaultCollection) {
      formData.append('defaultCollection', options.defaultCollection);
    }
    if (options.defaultTags) {
      formData.append('defaultTags', options.defaultTags.join(','));
    }
    if (options.defaultCategory) {
      formData.append('defaultCategory', options.defaultCategory);
    }

    return memoryApiClient.post<{ imported: number; errors: string[] }>('/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  /**
   * Cleanup memories
   */
  static async cleanupMemories(
    options: MemoryCleanupOptions
  ): Promise<ApiResponse<MemoryCleanupResult>> {
    return memoryApiClient.post<MemoryCleanupResult>('/cleanup', options);
  }

  /**
   * Bulk update memories
   */
  static async bulkUpdateMemories(
    memoryIds: string[],
    updates: Partial<Memory>
  ): Promise<ApiResponse<Memory[]>> {
    return memoryApiClient.patch<Memory[]>('/bulk', {
      memoryIds,
      updates,
    });
  }

  /**
   * Bulk delete memories
   */
  static async bulkDeleteMemories(memoryIds: string[]): Promise<ApiResponse<void>> {
    return memoryApiClient.delete<void>('/bulk', {
      params: { memoryIds: memoryIds.join(',') },
    });
  }

  /**
   * Bulk archive memories
   */
  static async bulkArchiveMemories(memoryIds: string[]): Promise<ApiResponse<Memory[]>> {
    return memoryApiClient.post<Memory[]>('/bulk/archive', { memoryIds });
  }

  /**
   * Bulk restore memories
   */
  static async bulkRestoreMemories(memoryIds: string[]): Promise<ApiResponse<Memory[]>> {
    return memoryApiClient.post<Memory[]>('/bulk/restore', { memoryIds });
  }

  /**
   * Bulk export memories
   */
  static async bulkExportMemories(
    memoryIds: string[],
    format: 'json' | 'csv' | 'xlsx' = 'json'
  ): Promise<ApiResponse<Blob>> {
    return memoryApiClient.get<Blob>('/bulk/export', {
      params: {
        memoryIds: memoryIds.join(','),
        format,
      },
    });
  }

  /**
   * Fetch memory folders
   */
  static async fetchFolders(): Promise<ApiResponse<string[]>> {
    return memoryApiClient.get<string[]>('/folders');
  }

  /**
   * Create a new folder
   */
  static async createFolder(name: string): Promise<ApiResponse<string>> {
    return memoryApiClient.post<string>('/folders', { name });
  }

  /**
   * Delete a folder
   */
  static async deleteFolder(name: string): Promise<ApiResponse<void>> {
    return memoryApiClient.delete<void>(`/folders/${encodeURIComponent(name)}`);
  }

  /**
   * Fetch memory collections
   */
  static async fetchCollections(): Promise<ApiResponse<string[]>> {
    return memoryApiClient.get<string[]>('/collections');
  }

  /**
   * Create a new collection
   */
  static async createCollection(name: string): Promise<ApiResponse<string>> {
    return memoryApiClient.post<string>('/collections', { name });
  }

  /**
   * Delete a collection
   */
  static async deleteCollection(name: string): Promise<ApiResponse<void>> {
    return memoryApiClient.delete<void>(`/collections/${encodeURIComponent(name)}`);
  }

  /**
   * Fetch memory tags
   */
  static async fetchTags(): Promise<ApiResponse<string[]>> {
    return memoryApiClient.get<string[]>('/tags');
  }

  /**
   * Fetch memory categories
   */
  static async fetchCategories(): Promise<ApiResponse<string[]>> {
    return memoryApiClient.get<string[]>('/categories');
  }

  /**
   * Create a WebSocket connection for real-time updates
   */
  static createWebSocketConnection(): WebSocket {
    const wsUrl = process.env.NEXT_PUBLIC_MEMORY_WS_URL || 
                  `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/memory/ws`;
    
    const ws = new WebSocket(wsUrl);
    
    return ws;
  }

  /**
   * Subscribe to real-time memory updates
   */
  static subscribeToMemoryUpdates(
    callback: (event: MemoryUpdateEvent) => void
  ): () => void {
    const ws = this.createWebSocketConnection();
    
    ws.onopen = () => {
      console.log('Memory updates WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const memoryEvent: MemoryUpdateEvent = JSON.parse(event.data);
        callback(memoryEvent);
      } catch (error) {
        console.error('Error parsing memory update event:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('Memory updates WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('Memory updates WebSocket disconnected');
    };
    
    // Return unsubscribe function
    return () => {
      ws.close();
    };
  }

  /**
   * Reindex memories for search
   */
  static async reindexMemories(memoryIds?: string[]): Promise<ApiResponse<{ indexed: number; errors: string[] }>> {
    if (memoryIds && memoryIds.length > 0) {
      return memoryApiClient.post<{ indexed: number; errors: string[] }>('/reindex', { memoryIds });
    }
    return memoryApiClient.post<{ indexed: number; errors: string[] }>('/reindex');
  }

  /**
   * Process memories (extract entities, topics, etc.)
   */
  static async processMemories(memoryIds?: string[]): Promise<ApiResponse<{ processed: number; errors: string[] }>> {
    if (memoryIds && memoryIds.length > 0) {
      return memoryApiClient.post<{ processed: number; errors: string[] }>('/process', { memoryIds });
    }
    return memoryApiClient.post<{ processed: number; errors: string[] }>('/process');
  }

  /**
   * Generate embeddings for memories
   */
  static async generateEmbeddings(memoryIds?: string[]): Promise<ApiResponse<{ embedded: number; errors: string[] }>> {
    if (memoryIds && memoryIds.length > 0) {
      return memoryApiClient.post<{ embedded: number; errors: string[] }>('/embeddings', { memoryIds });
    }
    return memoryApiClient.post<{ embedded: number; errors: string[] }>('/embeddings');
  }

  /**
   * Find similar memories
   */
  static async findSimilarMemories(
    memoryId: string,
    limit: number = 10
  ): Promise<ApiResponse<MemorySearchResult[]>> {
    return memoryApiClient.get<MemorySearchResult[]>(`/${memoryId}/similar`, {
      params: { limit },
    });
  }

  /**
   * Get memory access history
   */
  static async getMemoryAccessHistory(
    memoryId: string,
    limit: number = 50
  ): Promise<ApiResponse<Array<{
    timestamp: Date;
    userId: string;
    action: string;
  }>>> {
    return memoryApiClient.get<Array<{
      timestamp: Date;
      userId: string;
      action: string;
    }>>(`/${memoryId}/history`, {
      params: { limit },
    });
  }

  /**
   * Get memory relationships
   */
  static async getMemoryRelationships(
    memoryId: string
  ): Promise<ApiResponse<{
    related: Memory[];
    linked: Memory[];
    parent?: Memory;
    children: Memory[];
  }>> {
    return memoryApiClient.get<{
      related: Memory[];
      linked: Memory[];
      parent?: Memory;
      children: Memory[];
    }>(`/${memoryId}/relationships`);
  }

  /**
   * Update memory relationships
   */
  static async updateMemoryRelationships(
    memoryId: string,
    relationships: {
      relatedIds?: string[];
      linkedIds?: string[];
      parentId?: string;
      childIds?: string[];
    }
  ): Promise<ApiResponse<Memory>> {
    return memoryApiClient.patch<Memory>(`/${memoryId}/relationships`, relationships);
  }
}

// Export the default API client for advanced usage
export { memoryApiClient };

// Export convenience functions for common operations
export const memoryApi = {
  fetchMemories: MemoryApiService.fetchMemories,
  fetchMemory: MemoryApiService.fetchMemory,
  createMemory: MemoryApiService.createMemory,
  updateMemory: MemoryApiService.updateMemory,
  deleteMemory: MemoryApiService.deleteMemory,
  executeMemoryAction: MemoryApiService.executeMemoryAction,
  fetchStatistics: MemoryApiService.fetchStatistics,
  searchMemories: MemoryApiService.searchMemories,
  exportMemories: MemoryApiService.exportMemories,
  importMemories: MemoryApiService.importMemories,
  cleanupMemories: MemoryApiService.cleanupMemories,
  bulkUpdateMemories: MemoryApiService.bulkUpdateMemories,
  bulkDeleteMemories: MemoryApiService.bulkDeleteMemories,
  bulkArchiveMemories: MemoryApiService.bulkArchiveMemories,
  bulkRestoreMemories: MemoryApiService.bulkRestoreMemories,
  bulkExportMemories: MemoryApiService.bulkExportMemories,
  fetchFolders: MemoryApiService.fetchFolders,
  createFolder: MemoryApiService.createFolder,
  deleteFolder: MemoryApiService.deleteFolder,
  fetchCollections: MemoryApiService.fetchCollections,
  createCollection: MemoryApiService.createCollection,
  deleteCollection: MemoryApiService.deleteCollection,
  fetchTags: MemoryApiService.fetchTags,
  fetchCategories: MemoryApiService.fetchCategories,
  subscribeToMemoryUpdates: MemoryApiService.subscribeToMemoryUpdates,
  reindexMemories: MemoryApiService.reindexMemories,
  processMemories: MemoryApiService.processMemories,
  generateEmbeddings: MemoryApiService.generateEmbeddings,
  findSimilarMemories: MemoryApiService.findSimilarMemories,
  getMemoryAccessHistory: MemoryApiService.getMemoryAccessHistory,
  getMemoryRelationships: MemoryApiService.getMemoryRelationships,
  updateMemoryRelationships: MemoryApiService.updateMemoryRelationships,
};
