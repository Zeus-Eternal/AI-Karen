/**
 * Memory Management Store
 * Zustand store for managing memory state and operations
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { 
  Memory, 
  MemoryFilters, 
  MemorySortOptions, 
  MemoryStatistics, 
  MemoryActionPayload,
  MemoryUpdateEvent,
  MemoryManagementStore,
  MemoryManagementState,
  MemoryManagementActions,
  MemorySearchResponse,
  MemoryExportOptions,
  MemoryImportOptions,
  MemoryCleanupOptions,
  MemoryCleanupResult,
} from '../types';
import { memoryApi } from '../services/memoryApi';

// Default filters
const defaultFilters: MemoryFilters = {
  type: [],
  status: ['active'],
  priority: [],
  source: [],
  category: [],
  tags: [],
  folder: [],
  collection: [],
};

// Default sort options
const defaultSortOptions: MemorySortOptions = {
  field: 'updatedAt',
  direction: 'desc',
};

// Initial state
const initialState: MemoryManagementState = {
  memories: [],
  selectedMemory: null,
  isLoading: false,
  error: null,
  filters: defaultFilters,
  sortOptions: defaultSortOptions,
  isRealTimeEnabled: false,
  lastUpdate: null,
  statistics: null,
  showDetails: false,
  showFilters: false,
  viewMode: 'grid',
  selectedMemories: [],
  currentPage: 1,
  pageSize: 20,
  total: 0,
  hasMore: false,
  searchQuery: '',
  searchResults: [],
  isSearching: false,
  folders: [],
  collections: [],
  tags: [],
  categories: [],
};

// Create the store
type MemoryStoreWithUnsubscribe = MemoryManagementStore & { unsubscribeFromUpdates?: () => void };

export const useMemoryStore = create<MemoryManagementStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // Memory operations
        fetchMemories: async (filters?: MemoryFilters, sort?: MemorySortOptions, page?: number, pageSize?: number) => {
          set({ isLoading: true, error: null });
          
          try {
            const currentFilters = filters || get().filters;
            const currentSort = sort || get().sortOptions;
            const currentPage = page || get().currentPage;
            const currentPageSize = pageSize || get().pageSize;
            
            const response = await memoryApi.fetchMemories(currentFilters, currentSort, currentPage, currentPageSize);
            
            set({
              memories: response.data.memories,
              total: response.data.total,
              hasMore: response.data.hasMore,
              isLoading: false,
              filters: currentFilters,
              sortOptions: currentSort,
              currentPage,
              pageSize: currentPageSize,
            });
          } catch (error) {
            console.error('Failed to fetch memories:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to fetch memories',
              isLoading: false,
            });
          }
        },

        fetchMemory: async (memoryId: string) => {
          set({ isLoading: true, error: null });
          
          try {
            const response = await memoryApi.fetchMemory(memoryId);
            const memory = response.data;
            
            // Update memory in the list if it exists
            set((state) => ({
              memories: state.memories.some(m => m.id === memory.id)
                ? state.memories.map(m => m.id === memory.id ? memory : m)
                : [...state.memories, memory],
              selectedMemory: memory,
              isLoading: false,
            }));
          } catch (error) {
            console.error('Failed to fetch memory:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to fetch memory',
              isLoading: false,
            });
          }
        },

        createMemory: async (memoryData: Omit<Memory, 'id' | 'createdAt' | 'updatedAt' | 'hash' | 'version'>) => {
          set({ isLoading: true, error: null });
          
          try {
            const response = await memoryApi.createMemory(memoryData);
            const newMemory = response.data;
            
            set((state) => ({
              memories: [newMemory, ...state.memories],
              total: state.total + 1,
              isLoading: false,
            }));
          } catch (error) {
            console.error('Failed to create memory:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to create memory',
              isLoading: false,
            });
            throw error;
          }
        },

        updateMemory: async (memoryId: string, updates: Partial<Memory>) => {
          set({ isLoading: true, error: null });
          
          try {
            const response = await memoryApi.updateMemory(memoryId, updates);
            const updatedMemory = response.data;
            
            set((state) => ({
              memories: state.memories.map(memory =>
                memory.id === memoryId ? updatedMemory : memory
              ),
              selectedMemory: state.selectedMemory?.id === memoryId ? updatedMemory : state.selectedMemory,
              isLoading: false,
            }));
          } catch (error) {
            console.error('Failed to update memory:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to update memory',
              isLoading: false,
            });
            throw error;
          }
        },

        deleteMemory: async (memoryId: string) => {
          set({ isLoading: true, error: null });
          
          try {
            await memoryApi.deleteMemory(memoryId);
            
            set((state) => ({
              memories: state.memories.filter(memory => memory.id !== memoryId),
              selectedMemory: state.selectedMemory?.id === memoryId ? null : state.selectedMemory,
              selectedMemories: state.selectedMemories.filter(id => id !== memoryId),
              total: state.total - 1,
              isLoading: false,
            }));
          } catch (error) {
            console.error('Failed to delete memory:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to delete memory',
              isLoading: false,
            });
            throw error;
          }
        },

        executeMemoryAction: async (payload: MemoryActionPayload) => {
          set({ isLoading: true, error: null });
          
          try {
            const response = await memoryApi.executeMemoryAction(payload);
            const updatedMemory = response.data;
            
            set((state) => ({
              memories: state.memories.map(memory =>
                memory.id === payload.memoryId ? updatedMemory : memory
              ),
              selectedMemory: state.selectedMemory?.id === payload.memoryId ? updatedMemory : state.selectedMemory,
              isLoading: false,
            }));
          } catch (error) {
            console.error('Failed to execute memory action:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to execute memory action',
              isLoading: false,
            });
            throw error;
          }
        },

        // Bulk operations
        bulkUpdateMemories: async (memoryIds: string[], updates: Partial<Memory>) => {
          set({ isLoading: true, error: null });
          
          try {
            const response = await memoryApi.bulkUpdateMemories(memoryIds, updates);
            const updatedMemories = response.data;
            
            set((state) => {
              const updatedMemoryMap = new Map(updatedMemories.map(m => [m.id, m]));
              return {
                memories: state.memories.map(memory =>
                  updatedMemoryMap.has(memory.id) ? updatedMemoryMap.get(memory.id)! : memory
                ),
                selectedMemory: state.selectedMemory && updatedMemoryMap.has(state.selectedMemory.id)
                  ? updatedMemoryMap.get(state.selectedMemory.id)!
                  : state.selectedMemory,
                isLoading: false,
              };
            });
          } catch (error) {
            console.error('Failed to bulk update memories:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to bulk update memories',
              isLoading: false,
            });
            throw error;
          }
        },

        bulkDeleteMemories: async (memoryIds: string[]) => {
          set({ isLoading: true, error: null });
          
          try {
            await memoryApi.bulkDeleteMemories(memoryIds);
            
            set((state) => ({
              memories: state.memories.filter(memory => !memoryIds.includes(memory.id)),
              selectedMemory: state.selectedMemory && memoryIds.includes(state.selectedMemory.id) 
                ? null 
                : state.selectedMemory,
              selectedMemories: state.selectedMemories.filter(id => !memoryIds.includes(id)),
              total: state.total - memoryIds.length,
              isLoading: false,
            }));
          } catch (error) {
            console.error('Failed to bulk delete memories:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to bulk delete memories',
              isLoading: false,
            });
            throw error;
          }
        },

        bulkArchiveMemories: async (memoryIds: string[]) => {
          set({ isLoading: true, error: null });
          
          try {
            const response = await memoryApi.bulkArchiveMemories(memoryIds);
            const archivedMemories = response.data;
            
            set((state) => {
              const archivedMemoryMap = new Map(archivedMemories.map(m => [m.id, m]));
              return {
                memories: state.memories.map(memory =>
                  archivedMemoryMap.has(memory.id) ? archivedMemoryMap.get(memory.id)! : memory
                ),
                selectedMemory: state.selectedMemory && archivedMemoryMap.has(state.selectedMemory.id)
                  ? archivedMemoryMap.get(state.selectedMemory.id)!
                  : state.selectedMemory,
                isLoading: false,
              };
            });
          } catch (error) {
            console.error('Failed to bulk archive memories:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to bulk archive memories',
              isLoading: false,
            });
            throw error;
          }
        },

        bulkRestoreMemories: async (memoryIds: string[]) => {
          set({ isLoading: true, error: null });
          
          try {
            const response = await memoryApi.bulkRestoreMemories(memoryIds);
            const restoredMemories = response.data;
            
            set((state) => {
              const restoredMemoryMap = new Map(restoredMemories.map(m => [m.id, m]));
              return {
                memories: state.memories.map(memory =>
                  restoredMemoryMap.has(memory.id) ? restoredMemoryMap.get(memory.id)! : memory
                ),
                selectedMemory: state.selectedMemory && restoredMemoryMap.has(state.selectedMemory.id)
                  ? restoredMemoryMap.get(state.selectedMemory.id)!
                  : state.selectedMemory,
                isLoading: false,
              };
            });
          } catch (error) {
            console.error('Failed to bulk restore memories:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to bulk restore memories',
              isLoading: false,
            });
            throw error;
          }
        },

        bulkExportMemories: async (memoryIds: string[], format?: 'json' | 'csv' | 'xlsx') => {
          set({ isLoading: true, error: null });
          
          try {
            const response = await memoryApi.bulkExportMemories(memoryIds, format);
            
            // Create download link
            const blob = response.data;
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `memory-export-${new Date().toISOString().split('T')[0]}.${format || 'json'}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            set({ isLoading: false });
          } catch (error) {
            console.error('Failed to bulk export memories:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to bulk export memories',
              isLoading: false,
            });
            throw error;
          }
        },

        // Search operations
        searchMemories: async (query: string, filters?: MemoryFilters) => {
          set({ isSearching: true, error: null, searchQuery: query });
          
          try {
            const response = await memoryApi.searchMemories(query, filters);
            
            set({
              searchResults: response.data.results.map(r => r.memory),
              isSearching: false,
            });
          } catch (error) {
            console.error('Failed to search memories:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to search memories',
              isSearching: false,
            });
          }
        },

        clearSearch: () => {
          set({
            searchQuery: '',
            searchResults: [],
            isSearching: false,
          });
        },

        // Filters and sorting
        setFilters: (filters: MemoryFilters) => {
          set({ filters });
          // Auto-refresh with new filters
          const { sortOptions, currentPage, pageSize } = get();
          get().fetchMemories(filters, sortOptions, currentPage, pageSize);
        },

        setSortOptions: (sortOptions: MemorySortOptions) => {
          set({ sortOptions });
          // Auto-refresh with new sort
          const { filters, currentPage, pageSize } = get();
          get().fetchMemories(filters, sortOptions, currentPage, pageSize);
        },

        clearFilters: () => {
          set({ filters: defaultFilters });
          const { sortOptions, currentPage, pageSize } = get();
          get().fetchMemories(defaultFilters, sortOptions, currentPage, pageSize);
        },

        // Real-time updates
        enableRealTimeUpdates: () => {
          const { isRealTimeEnabled } = get();
          if (isRealTimeEnabled) return;
          
          const unsubscribe = memoryApi.subscribeToMemoryUpdates((event: MemoryUpdateEvent) => {
            get().handleRealTimeUpdate(event);
          });
          
          set({ 
            isRealTimeEnabled: true,
            lastUpdate: new Date(),
          });
          
          // Store unsubscribe function for cleanup
          (get() as MemoryStoreWithUnsubscribe).unsubscribeFromUpdates = unsubscribe;
        },

        disableRealTimeUpdates: () => {
          const { isRealTimeEnabled } = get();
          if (!isRealTimeEnabled) return;
          
          const unsubscribe = (get() as MemoryStoreWithUnsubscribe).unsubscribeFromUpdates;
          if (unsubscribe) {
            unsubscribe();
          }
          
          set({ isRealTimeEnabled: false });
        },

        handleRealTimeUpdate: (event: MemoryUpdateEvent) => {
          const { type, memoryId, memory } = event;
          
          set((state) => {
            let updatedMemories = [...state.memories];
            let updatedSelectedMemory = state.selectedMemory;
            
            switch (type) {
              case 'memory_created':
                if (memory) {
                  updatedMemories = [memory, ...updatedMemories];
                }
                break;
                
              case 'memory_updated':
              case 'memory_accessed':
                if (memory) {
                  updatedMemories = updatedMemories.map(m => 
                    m.id === memoryId ? memory : m
                  );
                  if (updatedSelectedMemory?.id === memoryId) {
                    updatedSelectedMemory = memory;
                  }
                }
                break;
                
              case 'memory_deleted':
                updatedMemories = updatedMemories.filter(m => m.id !== memoryId);
                if (updatedSelectedMemory?.id === memoryId) {
                  updatedSelectedMemory = null;
                }
                break;
                
              case 'memory_archived':
                if (memory) {
                  updatedMemories = updatedMemories.map(m => 
                    m.id === memoryId ? memory : m
                  );
                  if (updatedSelectedMemory?.id === memoryId) {
                    updatedSelectedMemory = memory;
                  }
                }
                break;
                
              case 'memory_restored':
                if (memory) {
                  updatedMemories = updatedMemories.map(m => 
                    m.id === memoryId ? memory : m
                  );
                  if (updatedSelectedMemory?.id === memoryId) {
                    updatedSelectedMemory = memory;
                  }
                }
                break;
            }
            
            return {
              memories: updatedMemories,
              selectedMemory: updatedSelectedMemory,
              lastUpdate: new Date(),
            };
          });
        },

        // Statistics
        fetchStatistics: async () => {
          try {
            const response = await memoryApi.fetchStatistics();
            set({ statistics: response.data });
          } catch (error) {
            console.error('Failed to fetch statistics:', error);
          }
        },

        // Organization
        fetchFolders: async () => {
          try {
            const response = await memoryApi.fetchFolders();
            set({ folders: response.data });
          } catch (error) {
            console.error('Failed to fetch folders:', error);
          }
        },

        fetchCollections: async () => {
          try {
            const response = await memoryApi.fetchCollections();
            set({ collections: response.data });
          } catch (error) {
            console.error('Failed to fetch collections:', error);
          }
        },

        fetchTags: async () => {
          try {
            const response = await memoryApi.fetchTags();
            set({ tags: response.data });
          } catch (error) {
            console.error('Failed to fetch tags:', error);
          }
        },

        fetchCategories: async () => {
          try {
            const response = await memoryApi.fetchCategories();
            set({ categories: response.data });
          } catch (error) {
            console.error('Failed to fetch categories:', error);
          }
        },

        createFolder: async (name: string) => {
          try {
            await memoryApi.createFolder(name);
            const { folders } = get();
            set({ folders: [...folders, name] });
          } catch (error) {
            console.error('Failed to create folder:', error);
            throw error;
          }
        },

        createCollection: async (name: string) => {
          try {
            await memoryApi.createCollection(name);
            const { collections } = get();
            set({ collections: [...collections, name] });
          } catch (error) {
            console.error('Failed to create collection:', error);
            throw error;
          }
        },

        // Selection
        selectMemory: (memoryId: string) => {
          set({ selectedMemories: [memoryId] });
        },

        selectMultipleMemories: (memoryIds: string[]) => {
          set({ selectedMemories: memoryIds });
        },

        deselectMemory: (memoryId: string) => {
          set((state) => ({
            selectedMemories: state.selectedMemories.filter(id => id !== memoryId)
          }));
        },

        clearSelection: () => {
          set({ selectedMemories: [] });
        },

        selectAll: () => {
          const { memories } = get();
          set({ selectedMemories: memories.map(m => m.id) });
        },

        // UI state
        setSelectedMemory: (memory: Memory | null) => {
          set({ selectedMemory: memory });
        },

        setShowDetails: (show: boolean) => {
          set({ showDetails: show });
        },

        setShowFilters: (show: boolean) => {
          set({ showFilters: show });
        },

        setViewMode: (mode: 'list' | 'grid' | 'kanban' | 'timeline') => {
          set({ viewMode: mode });
        },

        // Pagination
        setCurrentPage: (page: number) => {
          set({ currentPage: page });
          const { filters, sortOptions, pageSize } = get();
          get().fetchMemories(filters, sortOptions, page, pageSize);
        },

        setPageSize: (pageSize: number) => {
          set({ pageSize, currentPage: 1 });
          const { filters, sortOptions } = get();
          get().fetchMemories(filters, sortOptions, 1, pageSize);
        },

        // Utility
        clearError: () => {
          set({ error: null });
        },

        reset: () => {
          // Disable real-time updates before resetting
          const { isRealTimeEnabled } = get();
          if (isRealTimeEnabled) {
            get().disableRealTimeUpdates();
          }
          
          set(initialState);
        },
      }),
      {
        name: 'memory-store',
        partialize: (state) => ({
          filters: state.filters,
          sortOptions: state.sortOptions,
          viewMode: state.viewMode,
          pageSize: state.pageSize,
          isRealTimeEnabled: state.isRealTimeEnabled,
        }),
      }
    ),
    {
      name: 'memory-store',
    }
  )
);

// Selectors for common state combinations
export const useMemories = () => useMemoryStore((state) => state.memories);
export const useSelectedMemory = () => useMemoryStore((state) => state.selectedMemory);
export const useMemoryLoading = () => useMemoryStore((state) => state.isLoading);
export const useMemoryError = () => useMemoryStore((state) => state.error);
export const useMemoryFilters = () => useMemoryStore((state) => state.filters);
export const useMemorySortOptions = () => useMemoryStore((state) => state.sortOptions);
export const useMemoryStatistics = () => useMemoryStore((state) => state.statistics);
export const useMemoryViewMode = () => useMemoryStore((state) => state.viewMode);
export const useSelectedMemories = () => useMemoryStore((state) => state.selectedMemories);
export const useRealTimeEnabled = () => useMemoryStore((state) => state.isRealTimeEnabled);
export const useSearchResults = () => useMemoryStore((state) => state.searchResults);
export const useIsSearching = () => useMemoryStore((state) => state.isSearching);
export const useSearchQuery = () => useMemoryStore((state) => state.searchQuery);
export const useFolders = () => useMemoryStore((state) => state.folders);
export const useCollections = () => useMemoryStore((state) => state.collections);
export const useTags = () => useMemoryStore((state) => state.tags);
export const useCategories = () => useMemoryStore((state) => state.categories);

// Action hooks
export const useMemoryActions = () => useMemoryStore((state) => ({
  fetchMemories: state.fetchMemories,
  fetchMemory: state.fetchMemory,
  createMemory: state.createMemory,
  updateMemory: state.updateMemory,
  deleteMemory: state.deleteMemory,
  executeMemoryAction: state.executeMemoryAction,
  bulkUpdateMemories: state.bulkUpdateMemories,
  bulkDeleteMemories: state.bulkDeleteMemories,
  bulkArchiveMemories: state.bulkArchiveMemories,
  bulkRestoreMemories: state.bulkRestoreMemories,
  bulkExportMemories: state.bulkExportMemories,
  searchMemories: state.searchMemories,
  clearSearch: state.clearSearch,
  setFilters: state.setFilters,
  setSortOptions: state.setSortOptions,
  clearFilters: state.clearFilters,
  enableRealTimeUpdates: state.enableRealTimeUpdates,
  disableRealTimeUpdates: state.disableRealTimeUpdates,
  fetchStatistics: state.fetchStatistics,
  fetchFolders: state.fetchFolders,
  fetchCollections: state.fetchCollections,
  fetchTags: state.fetchTags,
  fetchCategories: state.fetchCategories,
  createFolder: state.createFolder,
  createCollection: state.createCollection,
  selectMemory: state.selectMemory,
  selectMultipleMemories: state.selectMultipleMemories,
  deselectMemory: state.deselectMemory,
  clearSelection: state.clearSelection,
  selectAll: state.selectAll,
  setSelectedMemory: state.setSelectedMemory,
  setShowDetails: state.setShowDetails,
  setShowFilters: state.setShowFilters,
  setViewMode: state.setViewMode,
  setCurrentPage: state.setCurrentPage,
  setPageSize: state.setPageSize,
  clearError: state.clearError,
  reset: state.reset,
}));

// Utility functions
export const getMemoryById = (id: string, memories: Memory[]): Memory | undefined => {
  return memories.find((memory) => memory.id === id);
};

export const getMemoriesByType = (type: Memory['type'], memories: Memory[]): Memory[] => {
  return memories.filter((memory) => memory.type === type);
};

export const getMemoriesByStatus = (status: Memory['status'], memories: Memory[]): Memory[] => {
  return memories.filter((memory) => memory.status === status);
};

export const getMemoriesByPriority = (priority: Memory['priority'], memories: Memory[]): Memory[] => {
  return memories.filter((memory) => memory.priority === priority);
};

export const getActiveMemories = (memories: Memory[]): Memory[] => {
  return memories.filter((memory) => memory.status === 'active');
};

export const getArchivedMemories = (memories: Memory[]): Memory[] => {
  return memories.filter((memory) => memory.status === 'archived');
};

export const getExpiredMemories = (memories: Memory[]): Memory[] => {
  const now = new Date();
  return memories.filter((memory) => memory.expiresAt && memory.expiresAt < now);
};

export const getMemoriesNearExpiry = (memories: Memory[], days: number = 7): Memory[] => {
  const now = new Date();
  const threshold = new Date(now.getTime() + days * 24 * 60 * 60 * 1000);
  return memories.filter((memory) => memory.expiresAt && memory.expiresAt <= threshold && memory.expiresAt > now);
};

export const getMemoryStatistics = (memories: Memory[]) => {
  const total = memories.length;
  const byType: Record<Memory['type'], number> = {
    conversation: 0,
    case: 0,
    unified: 0,
    fact: 0,
    preference: 0,
    context: 0,
  };
  const byStatus: Record<Memory['status'], number> = {
    active: 0,
    archived: 0,
    deleted: 0,
    processing: 0,
  };
  const byPriority: Record<Memory['priority'], number> = {
    low: 0,
    medium: 0,
    high: 0,
    critical: 0,
  };
  
  let totalSize = 0;
  let totalAccessCount = 0;
  let totalConfidence = 0;
  let totalImportance = 0;
  let confidenceCount = 0;
  let importanceCount = 0;
  
  memories.forEach(memory => {
    byType[memory.type]++;
    byStatus[memory.status]++;
    byPriority[memory.priority]++;
    
    totalSize += memory.size;
    totalAccessCount += memory.metadata.accessCount || 0;
    
    if (memory.metadata.confidence !== undefined) {
      totalConfidence += memory.metadata.confidence;
      confidenceCount++;
    }
    
    if (memory.metadata.importance !== undefined) {
      totalImportance += memory.metadata.importance;
      importanceCount++;
    }
  });
  
  const averageConfidence = confidenceCount > 0 ? totalConfidence / confidenceCount : 0;
  const averageImportance = importanceCount > 0 ? totalImportance / importanceCount : 0;
  const averageSize = total > 0 ? totalSize / total : 0;
  const averageAccessCount = total > 0 ? totalAccessCount / total : 0;
  
  return {
    total,
    byType,
    byStatus,
    byPriority,
    totalSize,
    averageSize,
    averageConfidence,
    averageImportance,
    totalAccessCount,
    averageAccessCount,
  };
};
