/**
 * Memory Service - Handles memory storage, retrieval, and context management
 * Integrates with Python backend memory management service
 */

import { getKarenBackend } from '@/lib/karen-backend';
import { safeError } from '@/lib/safe-console';
import type { MemoryEntry, MemoryQuery } from '@/lib/karen-backend';
import type { MemoryBatchOperation } from '@/types/memory';

export interface MemorySearchOptions {
  topK?: number;
  similarityThreshold?: number;
  tags?: string[];
  timeRange?: [Date, Date];
  includeMetadata?: boolean;
}

export interface MemoryStats {
  totalMemories: number;
  memoriesByTag: Record<string, number>;
  recentActivity: Array<{
    date: string;
    count: number;
  }>;
  averageSimilarity: number;
  topTags: Array<{
    tag: string;
    count: number;
  }>;
}

export interface MemoryContext {
  relevantMemories: MemoryEntry[];
  contextSummary: string;
  confidence: number;
  keywords: string[];
}

export class MemoryService {
  private backend = getKarenBackend();
  private cache = new Map<string, MemoryEntry[]>();
  private contextCache = new Map<string, MemoryContext>();

  /**
   * Store a new memory entry
   */
  async storeMemory(
    content: string,
    options: {
      tags?: string[];
      metadata?: Record<string, unknown>;
      userId?: string;
      sessionId?: string;
    } = {}
  ): Promise<string | null> {
    try {
      const memoryId = await this.backend.storeMemory(
        content,
        options.metadata || {},
        options.tags || [],
        options.userId,
        options.sessionId
      );

      // Clear relevant caches
      this.clearCacheForUser(options.userId);
      
      return memoryId;
    } catch (error) {
      safeError('MemoryService: Failed to store memory:', error);
      return null;
    }
  }

  /**
   * Query memories based on similarity and filters
   */
  async queryMemories(
    query: string,
    options: MemorySearchOptions & {
      userId?: string;
      sessionId?: string;
    } = {}
  ): Promise<MemoryEntry[]> {
    try {
      const cacheKey = this.generateCacheKey(query, options);
      
      // Check cache first
      if (this.cache.has(cacheKey)) {
        const cached = this.cache.get(cacheKey)!;
        // Return cached results if they're less than 5 minutes old
        const cacheAge = Date.now() - (cached[0]?.timestamp || 0);
        if (cacheAge < 300000) { // 5 minutes
          return cached;
        }
        this.cache.delete(cacheKey);
      }

      const memoryQuery: MemoryQuery = {
        text: query,
        user_id: options.userId,
        session_id: options.sessionId,
        tags: options.tags,
        top_k: options.topK || 10,
        similarity_threshold: options.similarityThreshold || 0.6,
        time_range: options.timeRange,
      };

      const memories = await this.backend.queryMemories(memoryQuery);
      
      // Cache the results
      this.cache.set(cacheKey, memories);
      
      return memories;
    } catch (error) {
      safeError('MemoryService: Failed to query memories:', error);
      return [];
    }
  }

  /**
   * Build conversation context from relevant memories
   */
  async buildContext(
    query: string,
    options: {
      userId?: string;
      sessionId?: string;
      maxMemories?: number;
      minSimilarity?: number;
    } = {}
  ): Promise<MemoryContext> {
    try {
      const cacheKey = `context_${query}_${options.userId || 'anon'}_${options.sessionId || 'none'}`;
      
      // Check context cache
      if (this.contextCache.has(cacheKey)) {
        return this.contextCache.get(cacheKey)!;
      }

      const memories = await this.queryMemories(query, {
        userId: options.userId,
        sessionId: options.sessionId,
        topK: options.maxMemories || 5,
        similarityThreshold: options.minSimilarity || 0.7,
      });

      // Build context summary
      const contextSummary = this.generateContextSummary(memories);
      const keywords = this.extractKeywords(memories);
      const confidence = this.calculateContextConfidence(memories);

      const context: MemoryContext = {
        relevantMemories: memories,
        contextSummary,
        confidence,
        keywords,
      };

      // Cache the context
      this.contextCache.set(cacheKey, context);
      
      return context;
    } catch (error) {
      safeError('MemoryService: Failed to build context:', error);
      return {
        relevantMemories: [],
        contextSummary: '',
        confidence: 0,
        keywords: [],
      };
    }
  }

  /**
   * Get memory statistics for a user
   */
  async getMemoryStats(userId?: string): Promise<MemoryStats> {
    try {
      const stats = await this.backend.getMemoryStats(userId);
      
      return {
        totalMemories: (stats.total_memories as number) || 0,
        memoriesByTag: (stats.memories_by_tag as Record<string, number>) || ({} as Record<string, number>),
        recentActivity: (stats.recent_activity as Array<{ date: string; count: number; }>) || ([] as Array<{ date: string; count: number; }>),
        averageSimilarity: (stats.average_similarity as number) || 0,
        topTags: (stats.top_tags as Array<{ tag: string; count: number; }>) || ([] as Array<{ tag: string; count: number; }>),
      };
    } catch (error) {
      safeError('MemoryService: Failed to get memory stats:', error);
      return {
        totalMemories: 0,
        memoriesByTag: {} as Record<string, number>,
        recentActivity: [] as Array<{ date: string; count: number; }>,
        averageSimilarity: 0,
        topTags: [] as Array<{ tag: string; count: number; }>,
      };
    }
  }

  /**
   * Search memories with advanced filtering
   */
  async searchMemories(
    searchTerm: string,
    filters: {
      userId?: string;
      sessionId?: string;
      tags?: string[];
      dateRange?: [Date, Date];
      contentType?: string;
      minSimilarity?: number;
      maxResults?: number;
    } = {}
  ): Promise<{
    memories: MemoryEntry[];
    totalFound: number;
    searchTime: number;
  }> {
    const startTime = Date.now();
    
    try {
      const memories = await this.queryMemories(searchTerm, {
        userId: filters.userId,
        sessionId: filters.sessionId,
        tags: filters.tags,
        timeRange: filters.dateRange,
        topK: filters.maxResults || 20,
        similarityThreshold: filters.minSimilarity || 0.5,
      });

      // Additional filtering by content type if specified
      let filteredMemories = memories;
      if (filters.contentType) {
        filteredMemories = memories.filter(mem => 
          mem.metadata?.type === filters.contentType ||
          mem.tags.includes(filters.contentType!)
        );
      }

      const searchTime = Date.now() - startTime;

      return {
        memories: filteredMemories,
        totalFound: filteredMemories.length,
        searchTime,
      };
    } catch (error) {
      safeError('MemoryService: Failed to search memories:', error);
      return {
        memories: [],
        totalFound: 0,
        searchTime: Date.now() - startTime,
      };
    }
  }

  /**
   * Get memories by tags
   */
  async getMemoriesByTags(
    tags: string[],
    options: {
      userId?: string;
      sessionId?: string;
      limit?: number;
    } = {}
  ): Promise<MemoryEntry[]> {
    try {
      return await this.queryMemories('', {
        userId: options.userId,
        sessionId: options.sessionId,
        tags,
        topK: options.limit || 50,
        similarityThreshold: 0.1, // Low threshold since we're filtering by tags
      });
    } catch (error) {
      safeError('MemoryService: Failed to get memories by tags:', error);
      return [];
    }
  }

  /**
   * Placeholder for batch operations (delete/tag/cluster updates, etc.).
   * Replace with an actual backend call when available.
   */
  async batchOperation(operation: MemoryBatchOperation): Promise<void> {
    try {
      if (process.env.NODE_ENV === 'development') {
        console.debug('MemoryService.batchOperation invoked', operation);
      }
    } catch (error) {
      safeError('MemoryService: Failed to execute batch operation:', error);
    }
  }

  /**
   * Delete a memory entry
   */
  async deleteMemory(memoryId: string, userId?: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.backend['config'].baseUrl}/api/memory/${memoryId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          ...(this.backend['config'].apiKey && { 'Authorization': `Bearer ${this.backend['config'].apiKey}` }),
        },
        body: JSON.stringify({ user_id: userId }),
      });

      if (response.ok) {
        // Clear caches
        this.clearCacheForUser(userId);
        return true;
      }
      
      return false;
    } catch (error) {
      safeError('MemoryService: Failed to delete memory:', error);
      return false;
    }
  }

  /**
   * Update memory tags
   */
  async updateMemoryTags(
    memoryId: string,
    tags: string[],
    userId?: string
  ): Promise<boolean> {
    try {
      const response = await fetch(`${this.backend['config'].baseUrl}/api/memory/${memoryId}/tags`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(this.backend['config'].apiKey && { 'Authorization': `Bearer ${this.backend['config'].apiKey}` }),
        },
        body: JSON.stringify({ 
          tags,
          user_id: userId 
        }),
      });

      if (response.ok) {
        // Clear caches
        this.clearCacheForUser(userId);
        return true;
      }
      
      return false;
    } catch (error) {
      safeError('MemoryService: Failed to update memory tags:', error);
      return false;
    }
  }

  /**
   * Clear cache for a specific user
   */
  private clearCacheForUser(userId?: string): void {
    if (!userId) {
      this.cache.clear();
      this.contextCache.clear();
      return;
    }

    // Clear entries that contain the user ID
    for (const [key] of this.cache) {
      if (key.includes(userId)) {
        this.cache.delete(key);
      }
    }
    
    for (const [key] of this.contextCache) {
      if (key.includes(userId)) {
        this.contextCache.delete(key);
      }
    }
  }

  /**
   * Generate cache key for query
   */
  private generateCacheKey(
    query: string,
    options: MemorySearchOptions & { userId?: string; sessionId?: string }
  ): string {
    const keyParts = [
      query,
      options.userId || 'anon',
      options.sessionId || 'none',
      JSON.stringify(options.tags || []),
      options.topK || 10,
      options.similarityThreshold || 0.6,
    ];
    return keyParts.join('_');
  }

  private ensureRecord(value: unknown): Record<string, unknown> {
    if (typeof value === 'object' && value !== null) {
      return value as Record<string, unknown>;
    }
    return {};
  }

  private parseDate(value: unknown): Date | undefined {
    if (value instanceof Date) {
      return value;
    }

    if (typeof value === 'string' || typeof value === 'number') {
      const date = new Date(value);
      return isNaN(date.getTime()) ? undefined : date;
    }

    return undefined;
  }

  /**
   * Generate context summary from memories
   */
  private generateContextSummary(memories: MemoryEntry[]): string {
    if (memories.length === 0) {
      return 'No relevant context found.';
    }

    const topMemories = memories.slice(0, 3);
    const summaryParts = topMemories.map(mem => 
      mem.content.length > 100 
        ? mem.content.substring(0, 100) + '...'
        : mem.content
    );

    return `Based on ${memories.length} relevant memories: ${summaryParts.join(' | ')}`;
  }

  /**
   * Extract keywords from memories
   */
  private extractKeywords(memories: MemoryEntry[]): string[] {
    const allTags = memories.flatMap(mem => mem.tags);
    const tagCounts = allTags.reduce((acc, tag) => {
      acc[tag] = (acc[tag] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(tagCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([tag]) => tag);
  }

  /**
   * Calculate context confidence based on memory similarity scores
   */
  private calculateContextConfidence(memories: MemoryEntry[]): number {
    if (memories.length === 0) return 0;

    const scores = memories
      .map(mem => mem.similarity_score || 0)
      .filter(score => score > 0);

    if (scores.length === 0) return 0;

    const avgScore = scores.reduce((sum, score) => sum + score, 0) / scores.length;
    return Math.min(avgScore * memories.length / 5, 1); // Normalize to 0-1
  }

  /**
   * Get search history for a user
   */
  async getSearchHistory(userId: string, limit: number = 20): Promise<Array<{
    id: string;
    query: string;
    timestamp: Date;
    resultCount: number;
    filters?: unknown;
    userId: string;
  }>> {
    try {
      const response = await fetch(
        `${this.backend['config'].baseUrl}/api/memory/search-history?user_id=${encodeURIComponent(userId)}&limit=${limit}`,
        {
          headers: {
            ...(this.backend['config'].apiKey && { 'Authorization': `Bearer ${this.backend['config'].apiKey}` }),
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        return (data.history || []).map((item: unknown) => {
          const record = this.ensureRecord(item);
          const timestamp = this.parseDate(record.timestamp) ?? new Date();
          return {
            ...record,
            timestamp,
          };
        });
      }

      return [];
    } catch (error) {
      safeError('MemoryService: Failed to get search history:', error);
      return [];
    }
  }

  /**
   * Get saved searches for a user
   */
  async getSavedSearches(userId: string): Promise<Array<{
    id: string;
    name: string;
    query: string;
    filters?: unknown;
    userId: string;
    createdAt: Date;
    lastUsed?: Date;
    useCount?: number;
  }>> {
    try {
      const response = await fetch(
        `${this.backend['config'].baseUrl}/api/memory/saved-searches?user_id=${encodeURIComponent(userId)}`,
        {
          headers: {
            ...(this.backend['config'].apiKey && { 'Authorization': `Bearer ${this.backend['config'].apiKey}` }),
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        return (data.searches || []).map((item: unknown) => {
          const record = this.ensureRecord(item);
          const createdAt = this.parseDate(record.createdAt) ?? new Date();
          return {
            ...record,
            createdAt,
            lastUsed: this.parseDate(record.lastUsed),
          };
        });
      }

      return [];
    } catch (error) {
      safeError('MemoryService: Failed to get saved searches:', error);
      return [];
    }
  }

  /**
   * Save a search for future use
   */
  async saveSearch(params: {
    userId: string;
    name: string;
    query: string;
    filters?: unknown;
  }): Promise<{ id: string } | null> {
    try {
      const response = await fetch(
        `${this.backend['config'].baseUrl}/api/memory/saved-searches`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(this.backend['config'].apiKey && { 'Authorization': `Bearer ${this.backend['config'].apiKey}` }),
          },
          body: JSON.stringify(params),
        }
      );

      if (response.ok) {
        return await response.json();
      }

      return null;
    } catch (error) {
      safeError('MemoryService: Failed to save search:', error);
      return null;
    }
  }

  /**
   * Delete a saved search
   */
  async deleteSavedSearch(userId: string, searchId: string): Promise<boolean> {
    try {
      const response = await fetch(
        `${this.backend['config'].baseUrl}/api/memory/saved-searches/${searchId}?user_id=${encodeURIComponent(userId)}`,
        {
          method: 'DELETE',
          headers: {
            ...(this.backend['config'].apiKey && { 'Authorization': `Bearer ${this.backend['config'].apiKey}` }),
          },
        }
      );

      return response.ok;
    } catch (error) {
      safeError('MemoryService: Failed to delete saved search:', error);
      return false;
    }
  }

  /**
   * Get memory backups for a user
   */
  async getMemoryBackups(userId: string): Promise<Array<{
    id: string;
    name: string;
    timestamp: Date;
    memoryCount: number;
    size: number;
  }>> {
    try {
      const response = await fetch(
        `${this.backend['config'].baseUrl}/api/memory/backups?user_id=${encodeURIComponent(userId)}`,
        {
          headers: {
            ...(this.backend['config'].apiKey && { 'Authorization': `Bearer ${this.backend['config'].apiKey}` }),
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        return (data.backups || []).map((item: unknown) => {
          const record = this.ensureRecord(item);
          const timestamp = this.parseDate(record.timestamp) ?? new Date();
          return {
            ...record,
            timestamp,
          };
        });
      }

      return [];
    } catch (error) {
      safeError('MemoryService: Failed to get backups:', error);
      return [];
    }
  }

  /**
   * Create a memory backup
   */
  async createBackup(userId: string, name: string): Promise<{ id: string } | null> {
    try {
      const response = await fetch(
        `${this.backend['config'].baseUrl}/api/memory/backups`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(this.backend['config'].apiKey && { 'Authorization': `Bearer ${this.backend['config'].apiKey}` }),
          },
          body: JSON.stringify({ user_id: userId, name }),
        }
      );

      if (response.ok) {
        return await response.json();
      }

      return null;
    } catch (error) {
      safeError('MemoryService: Failed to create backup:', error);
      return null;
    }
  }

  /**
   * Restore from a memory backup
   */
  async restoreBackup(userId: string, backupId: string): Promise<boolean> {
    try {
      const response = await fetch(
        `${this.backend['config'].baseUrl}/api/memory/backups/${backupId}/restore`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(this.backend['config'].apiKey && { 'Authorization': `Bearer ${this.backend['config'].apiKey}` }),
          },
          body: JSON.stringify({ user_id: userId }),
        }
      );

      if (response.ok) {
        // Clear caches after restore
        this.clearCacheForUser(userId);
        return true;
      }

      return false;
    } catch (error) {
      safeError('MemoryService: Failed to restore backup:', error);
      return false;
    }
  }

  /**
   * Clear all caches
   */
  clearCache(): void {
    this.cache.clear();
    this.contextCache.clear();
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): {
    queryCache: { size: number; keys: string[] };
    contextCache: { size: number; keys: string[] };
  } {
    return {
      queryCache: {
        size: this.cache.size,
        keys: Array.from(this.cache.keys()),
      },
      contextCache: {
        size: this.contextCache.size,
        keys: Array.from(this.contextCache.keys()),
      },
    };
  }
}

// Global instance
let memoryService: MemoryService | null = null;

export function getMemoryService(): MemoryService {
  if (!memoryService) {
    memoryService = new MemoryService();
  }
  return memoryService;
}

export function initializeMemoryService(): MemoryService {
  memoryService = new MemoryService();
  return memoryService;
}
