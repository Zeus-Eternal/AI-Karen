/**
 * Agent Selection Store
 * Zustand store for managing agent selection state and operations
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  Agent,
  AgentCapability,
  AgentFilters,
  AgentSortOptions,
  AgentRecommendation,
  AgentComparison,
  AgentSelectionContext,
  AgentConfigurationValues,
  AgentSelectionStore,
  AgentSelectionState,
  AgentSelectionActions
} from '../types';
import { agentApi } from '../services/agentApi';

// Default filters
const defaultFilters: AgentFilters = {
  status: ['available'],
  includeDeprecated: false,
  includeBeta: true,
};

// Default sort options
const defaultSortOptions: AgentSortOptions = {
  field: 'rating',
  direction: 'desc',
};

// Default selection context
const defaultSelectionContext: AgentSelectionContext = {
  userPreferences: {
    preferredCapabilities: [],
    performanceRequirements: {
      maxResponseTime: 5000, // 5 seconds
      minSuccessRate: 90, // 90%
    },
  },
  previousSelections: [],
  userHistory: {
    completedTasks: 0,
    averageRating: 0,
    preferredAgents: [],
  },
};

// Initial state
const initialState: AgentSelectionState = {
  agents: [],
  selectedAgent: null,
  comparisonAgents: [],
  recommendations: [],
  isLoading: false,
  error: null,
  filters: defaultFilters,
  sortOptions: defaultSortOptions,
  showDetails: false,
  showFilters: false,
  showComparison: false,
  showConfiguration: false,
  viewMode: 'grid',
  configurationValues: {},
  selectionContext: defaultSelectionContext,
};

// Create the store
export const useAgentSelectionStore = create<AgentSelectionStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // Agent operations
        fetchAgents: async (filters?: AgentFilters, sort?: AgentSortOptions) => {
          set({ isLoading: true, error: null });
          
          try {
            const currentFilters = filters || get().filters;
            const currentSort = sort || get().sortOptions;
            
            const response = await agentApi.fetchAgents(currentFilters, currentSort);
            
            set({
              agents: response.data.agents,
              isLoading: false,
              filters: currentFilters,
              sortOptions: currentSort,
            });
          } catch (error) {
            console.error('Failed to fetch agents:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to fetch agents',
              isLoading: false,
            });
          }
        },

        fetchAgent: async (agentId: string) => {
          set({ isLoading: true, error: null });
          
          try {
            const response = await agentApi.fetchAgent(agentId);
            const agent = response.data;
            
            // Update agent in the list if it exists
            set((state) => ({
              agents: state.agents.some(a => a.id === agent.id)
                ? state.agents.map(a => a.id === agent.id ? agent : a)
                : [...state.agents, agent],
              selectedAgent: agent,
              isLoading: false,
            }));
          } catch (error) {
            console.error('Failed to fetch agent:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to fetch agent',
              isLoading: false,
            });
          }
        },

        selectAgent: (agent: Agent) => {
          set({ selectedAgent: agent });
        },

        deselectAgent: () => {
          set({ selectedAgent: null });
        },

        // Comparison operations
        addToComparison: (agent: Agent) => {
          set((state) => {
            const isAlreadyInComparison = state.comparisonAgents.some(a => a.id === agent.id);
            if (isAlreadyInComparison) return state;
            
            return {
              comparisonAgents: [...state.comparisonAgents, agent],
            };
          });
        },

        removeFromComparison: (agentId: string) => {
          set((state) => ({
            comparisonAgents: state.comparisonAgents.filter(a => a.id !== agentId),
          }));
        },

        clearComparison: () => {
          set({ comparisonAgents: [] });
        },

        // Recommendations
        fetchRecommendations: async (context: AgentSelectionContext) => {
          set({ isLoading: true, error: null });
          
          try {
            const response = await agentApi.getRecommendations(context);
            
            set({
              recommendations: response.data,
              isLoading: false,
              selectionContext: context,
            });
          } catch (error) {
            console.error('Failed to fetch recommendations:', error);
            set({
              error: error instanceof Error ? error.message : 'Failed to fetch recommendations',
              isLoading: false,
            });
          }
        },

        // Configuration
        updateConfiguration: (configId: string, value: any) => {
          set((state) => ({
            configurationValues: {
              ...state.configurationValues,
              [configId]: value,
            },
          }));
        },

        resetConfiguration: () => {
          set({ configurationValues: {} });
        },

        // Filters and sorting
        setFilters: (filters: AgentFilters) => {
          set({ filters });
          // Auto-refresh with new filters
          const { sortOptions } = get();
          get().fetchAgents(filters, sortOptions);
        },

        setSortOptions: (sortOptions: AgentSortOptions) => {
          set({ sortOptions });
          // Auto-refresh with new sort
          const { filters } = get();
          get().fetchAgents(filters, sortOptions);
        },

        clearFilters: () => {
          set({ filters: defaultFilters });
          const { sortOptions } = get();
          get().fetchAgents(defaultFilters, sortOptions);
        },

        // UI state
        setShowDetails: (show: boolean) => {
          set({ showDetails: show });
        },

        setShowFilters: (show: boolean) => {
          set({ showFilters: show });
        },

        setShowComparison: (show: boolean) => {
          set({ showComparison: show });
        },

        setShowConfiguration: (show: boolean) => {
          set({ showConfiguration: show });
        },

        setViewMode: (mode: 'list' | 'grid' | 'compact') => {
          set({ viewMode: mode });
        },

        // Context
        setSelectionContext: (context: AgentSelectionContext) => {
          set({ selectionContext: context });
        },

        // Utility
        clearError: () => {
          set({ error: null });
        },

        reset: () => {
          set(initialState);
        },
      }),
      {
        name: 'agent-store',
        partialize: (state) => ({
          filters: state.filters,
          sortOptions: state.sortOptions,
          viewMode: state.viewMode,
          selectionContext: state.selectionContext,
        }),
      }
    ),
    {
      name: 'agent-store',
    }
  )
);

// Selectors for common state combinations
export const useAgents = () => useAgentSelectionStore((state) => state.agents);
export const useSelectedAgent = () => useAgentSelectionStore((state) => state.selectedAgent);
export const useComparisonAgents = () => useAgentSelectionStore((state) => state.comparisonAgents);
export const useRecommendations = () => useAgentSelectionStore((state) => state.recommendations);
export const useAgentLoading = () => useAgentSelectionStore((state) => state.isLoading);
export const useAgentError = () => useAgentSelectionStore((state) => state.error);
export const useAgentFilters = () => useAgentSelectionStore((state) => state.filters);
export const useAgentSortOptions = () => useAgentSelectionStore((state) => state.sortOptions);
export const useAgentViewMode = () => useAgentSelectionStore((state) => state.viewMode);
export const useConfigurationValues = () => useAgentSelectionStore((state) => state.configurationValues);
export const useSelectionContext = () => useAgentSelectionStore((state) => state.selectionContext);

// Action hooks
export const useAgentActions = () => useAgentSelectionStore((state) => ({
  fetchAgents: state.fetchAgents,
  fetchAgent: state.fetchAgent,
  selectAgent: state.selectAgent,
  deselectAgent: state.deselectAgent,
  addToComparison: state.addToComparison,
  removeFromComparison: state.removeFromComparison,
  clearComparison: state.clearComparison,
  fetchRecommendations: state.fetchRecommendations,
  updateConfiguration: state.updateConfiguration,
  resetConfiguration: state.resetConfiguration,
  setFilters: state.setFilters,
  setSortOptions: state.setSortOptions,
  clearFilters: state.clearFilters,
  setShowDetails: state.setShowDetails,
  setShowFilters: state.setShowFilters,
  setShowComparison: state.setShowComparison,
  setShowConfiguration: state.setShowConfiguration,
  setViewMode: state.setViewMode,
  setSelectionContext: state.setSelectionContext,
  clearError: state.clearError,
  reset: state.reset,
}));

// Utility functions
export const getAgentById = (id: string, agents: Agent[]): Agent | undefined => {
  return agents.find((agent) => agent.id === id);
};

export const getAgentsByStatus = (status: Agent['status'], agents: Agent[]): Agent[] => {
  return agents.filter((agent) => agent.status === status);
};

export const getAgentsByType = (type: Agent['type'], agents: Agent[]): Agent[] => {
  return agents.filter((agent) => agent.type === type);
};

export const getAgentsByCapability = (capability: AgentCapability, agents: Agent[]): Agent[] => {
  return agents.filter((agent) => agent.capabilities.includes(capability));
};

export const getAvailableAgents = (agents: Agent[]): Agent[] => {
  return agents.filter((agent) => agent.status === 'available');
};

export const getRecommendedAgents = (agents: Agent[]): Agent[] => {
  return agents.filter((agent) => agent.isRecommended);
};

export const getBetaAgents = (agents: Agent[]): Agent[] => {
  return agents.filter((agent) => agent.isBeta);
};

export const getDeprecatedAgents = (agents: Agent[]): Agent[] => {
  return agents.filter((agent) => agent.isDeprecated);
};

export const getTopRatedAgents = (agents: Agent[], limit: number = 5): Agent[] => {
  return agents
    .filter((agent) => agent.ratings.count > 0)
    .sort((a, b) => b.ratings.average - a.ratings.average)
    .slice(0, limit);
};

export const getMostUsedAgents = (agents: Agent[], limit: number = 5): Agent[] => {
  return agents
    .sort((a, b) => b.performance.totalTasks - a.performance.totalTasks)
    .slice(0, limit);
};

export const getMostReliableAgents = (agents: Agent[], limit: number = 5): Agent[] => {
  return agents
    .sort((a, b) => b.performance.successRate - a.performance.successRate)
    .slice(0, limit);
};

export const getFastestAgents = (agents: Agent[], limit: number = 5): Agent[] => {
  return agents
    .sort((a, b) => a.performance.averageResponseTime - b.performance.averageResponseTime)
    .slice(0, limit);
};

export const searchAgents = (agents: Agent[], query: string): Agent[] => {
  if (!query.trim()) return agents;
  
  const lowercaseQuery = query.toLowerCase();
  
  return agents.filter((agent) => 
    agent.name.toLowerCase().includes(lowercaseQuery) ||
    agent.description.toLowerCase().includes(lowercaseQuery) ||
    agent.specializations.some(s => s.toLowerCase().includes(lowercaseQuery)) ||
    agent.tags.some(t => t.toLowerCase().includes(lowercaseQuery)) ||
    agent.developer.name.toLowerCase().includes(lowercaseQuery)
  );
};

export const filterAgents = (agents: Agent[], filters: AgentFilters): Agent[] => {
  return agents.filter((agent) => {
    // Status filter
    if (filters.status && filters.status.length > 0) {
      if (!filters.status.includes(agent.status)) return false;
    }
    
    // Type filter
    if (filters.type && filters.type.length > 0) {
      if (!filters.type.includes(agent.type)) return false;
    }
    
    // Capabilities filter
    if (filters.capabilities && filters.capabilities.length > 0) {
      const hasAllCapabilities = filters.capabilities.every((cap: AgentCapability) =>
        agent.capabilities.includes(cap)
      );
      if (!hasAllCapabilities) return false;
    }
    
    // Specializations filter
    if (filters.specializations && filters.specializations.length > 0) {
      const hasAnySpecialization = filters.specializations.some((spec: string) =>
        agent.specializations.includes(spec)
      );
      if (!hasAnySpecialization) return false;
    }
    
    // Tags filter
    if (filters.tags && filters.tags.length > 0) {
      const hasAnyTag = filters.tags.some((tag: string) =>
        agent.tags.includes(tag)
      );
      if (!hasAnyTag) return false;
    }
    
    // Developer filter
    if (filters.developer && filters.developer.length > 0) {
      if (!filters.developer.includes(agent.developer.name)) return false;
    }
    
    // Rating filter
    if (filters.rating) {
      if (agent.ratings.average < filters.rating.min ||
          agent.ratings.average > filters.rating.max) {
        return false;
      }
    }
    
    // Pricing filter
    if (filters.pricing && filters.pricing.length > 0) {
      const isFree = !agent.pricing || agent.pricing.model === 'free';
      const isPaid = agent.pricing && agent.pricing.model !== 'free';
      
      if (filters.pricing.includes('free') && !isFree) return false;
      if (filters.pricing.includes('paid') && !isPaid) return false;
    }
    
    // Performance filter
    if (filters.performance) {
      if (filters.performance.minSuccessRate &&
          agent.performance.successRate < filters.performance.minSuccessRate) {
        return false;
      }
      
      if (filters.performance.maxResponseTime &&
          agent.performance.averageResponseTime > filters.performance.maxResponseTime) {
        return false;
      }
    }
    
    // Search filter
    if (filters.search) {
      const searchResults = searchAgents([agent], filters.search);
      if (searchResults.length === 0) return false;
    }
    
    // Deprecated filter
    if (!filters.includeDeprecated && agent.isDeprecated) return false;
    
    // Beta filter
    if (!filters.includeBeta && agent.isBeta) return false;
    
    return true;
  });
};

export const sortAgents = (agents: Agent[], sortOptions: AgentSortOptions): Agent[] => {
  const { field, direction } = sortOptions;
  
  return [...agents].sort((a, b) => {
    let aValue: string | number | Date;
    let bValue: string | number | Date;
    
    switch (field) {
      case 'name':
        aValue = a.name.toLowerCase();
        bValue = b.name.toLowerCase();
        break;
      case 'rating':
        aValue = a.ratings.average;
        bValue = b.ratings.average;
        break;
      case 'performance':
        aValue = a.performance.successRate;
        bValue = b.performance.successRate;
        break;
      case 'createdAt':
        aValue = a.createdAt.getTime();
        bValue = b.createdAt.getTime();
        break;
      case 'lastUsed':
        aValue = a.lastUsed?.getTime() || 0;
        bValue = b.lastUsed?.getTime() || 0;
        break;
      case 'popularity':
        aValue = a.performance.totalTasks;
        bValue = b.performance.totalTasks;
        break;
      default:
        return 0;
    }
    
    if (aValue < bValue) return direction === 'asc' ? -1 : 1;
    if (aValue > bValue) return direction === 'asc' ? 1 : -1;
    return 0;
  });
};