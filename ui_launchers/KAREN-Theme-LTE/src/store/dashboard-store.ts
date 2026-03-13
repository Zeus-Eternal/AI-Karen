/**
 * Dashboard Store
 * 
 * State management for dashboard functionality
 */

import { create } from 'zustand';
import type { Dashboard, DashboardFilter, TimeRange } from '@/types/dashboard';

// Export TimeRange type for use in other modules
export type { TimeRange };

interface DashboardState {
  // Dashboard management
  dashboards: Record<string, Dashboard>;
  activeDashboardId: string | null;
  
  // Global state
  globalTimeRange: TimeRange;
  globalFilters: DashboardFilter[];
  isEditing: boolean;
  
  // UI state
  isLoading: boolean;
  error: string | null;
}

interface DashboardActions {
  // Dashboard management
  setDashboards: (dashboards: Record<string, Dashboard>) => void;
  addDashboard: (dashboard: Dashboard) => void;
  updateDashboard: (id: string, updates: Partial<Dashboard>) => void;
  removeDashboard: (id: string) => void;
  setActiveDashboard: (id: string | null) => void;
  
  // Global state
  setGlobalTimeRange: (timeRange: TimeRange) => void;
  addGlobalFilter: (filter: Omit<DashboardFilter, 'id'>) => void;
  removeGlobalFilter: (id: string) => void;
  clearGlobalFilters: () => void;
  setEditing: (editing: boolean) => void;
  
  // UI state
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

const defaultTimeRange: TimeRange = {
  start: new Date(Date.now() - 24 * 60 * 60 * 1000), // 24 hours ago
  end: new Date(),
  preset: 'last-day'
};

export const useDashboardStore = create<DashboardState & DashboardActions>((set) => ({
  // Initial state
  dashboards: {},
  activeDashboardId: null,
  globalTimeRange: defaultTimeRange,
  globalFilters: [],
  isEditing: false,
  isLoading: false,
  error: null,

  // Dashboard management
  setDashboards: (dashboards) => set({ dashboards }),
  
  addDashboard: (dashboard) => set((state) => ({
    dashboards: { ...state.dashboards, [dashboard.id]: dashboard }
  })),
  
  updateDashboard: (id, updates) => set((state) => {
    const currentDashboard = state.dashboards[id];
    if (!currentDashboard) return state;
    
    return {
      dashboards: {
        ...state.dashboards,
        [id]: { ...currentDashboard, ...updates }
      }
    };
  }),
  
  removeDashboard: (id) => set((state) => {
    const newDashboards = { ...state.dashboards };
    delete newDashboards[id];
    return { 
      dashboards: newDashboards,
      activeDashboardId: state.activeDashboardId === id ? null : state.activeDashboardId
    };
  }),
  
  setActiveDashboard: (id) => set({ activeDashboardId: id }),

  // Global state
  setGlobalTimeRange: (timeRange) => set({ globalTimeRange: timeRange }),
  
  addGlobalFilter: (filter) => {
    const id = Math.random().toString(36).substr(2, 9);
    set((state) => ({
      globalFilters: [...state.globalFilters, { ...filter, id }]
    }));
  },
  
  removeGlobalFilter: (id) => set((state) => ({
    globalFilters: state.globalFilters.filter(f => f.id !== id)
  })),
  
  clearGlobalFilters: () => set({ globalFilters: [] }),
  
  setEditing: (editing) => set({ isEditing: editing }),

  // UI state
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error })
}));

// Selectors
export const useActiveDashboard = () => {
  const activeDashboardId = useDashboardStore(state => state.activeDashboardId);
  const dashboards = useDashboardStore(state => state.dashboards);
  
  return activeDashboardId ? dashboards[activeDashboardId] : null;
};

export const useDashboardWidgets = () => {
  const activeDashboard = useActiveDashboard();
  return activeDashboard?.widgets || [];
};

export const useDashboardFilters = () => {
  const activeDashboard = useActiveDashboard();
  return activeDashboard?.filters || [];
};