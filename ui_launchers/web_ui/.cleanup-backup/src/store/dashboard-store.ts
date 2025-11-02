/**
 * Dashboard Store
 * 
 * Manages dashboard configurations, templates, and persistence.
 * Implements requirements: 3.3, 3.5
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { subscribeWithSelector } from 'zustand/middleware';
import type { 
  DashboardConfig, 
  WidgetConfig, 
  DashboardFilter,
  DashboardLayout 
} from '@/types/dashboard';

// Dashboard Template Types
export interface DashboardTemplate {
  id: string;
  name: string;
  description: string;
  category: 'system' | 'user' | 'role-based';
  roles?: string[];
  config: Omit<DashboardConfig, 'id' | 'createdAt' | 'updatedAt'>;
  preview?: string;
  tags: string[];
  isDefault?: boolean;
}

// Time Range Types
export interface TimeRange {
  start: Date;
  end: Date;
  preset?: 'last-hour' | 'last-day' | 'last-week' | 'last-month' | 'custom';
}

// Dashboard State
export interface DashboardState {
  // Current dashboards
  dashboards: Record<string, DashboardConfig>;
  activeDashboardId: string | null;
  
  // Templates
  templates: Record<string, DashboardTemplate>;
  
  // Global filters and settings
  globalTimeRange: TimeRange;
  globalFilters: DashboardFilter[];
  
  // UI state
  isEditing: boolean;
  selectedWidgets: string[];
  
  // Export/Import state
  exportInProgress: boolean;
  importInProgress: boolean;
  
  // Persistence settings
  autoSave: boolean;
  saveInterval: number; // in milliseconds
}

// Dashboard Actions
export interface DashboardActions {
  // Dashboard management
  createDashboard: (config: Omit<DashboardConfig, 'id' | 'createdAt' | 'updatedAt'>) => string;
  updateDashboard: (id: string, updates: Partial<DashboardConfig>) => void;
  deleteDashboard: (id: string) => void;
  duplicateDashboard: (id: string, name?: string) => string;
  setActiveDashboard: (id: string) => void;
  
  // Widget management
  addWidget: (dashboardId: string, widget: Omit<WidgetConfig, 'id'>) => string;
  updateWidget: (dashboardId: string, widgetId: string, updates: Partial<WidgetConfig>) => void;
  removeWidget: (dashboardId: string, widgetId: string) => void;
  reorderWidgets: (dashboardId: string, widgetIds: string[]) => void;
  
  // Template management
  createTemplate: (template: Omit<DashboardTemplate, 'id'>) => string;
  updateTemplate: (id: string, updates: Partial<DashboardTemplate>) => void;
  deleteTemplate: (id: string) => void;
  applyTemplate: (templateId: string, dashboardId?: string) => string;
  
  // Filter management
  setGlobalTimeRange: (timeRange: TimeRange) => void;
  addGlobalFilter: (filter: Omit<DashboardFilter, 'id'>) => string;
  updateGlobalFilter: (id: string, updates: Partial<DashboardFilter>) => void;
  removeGlobalFilter: (id: string) => void;
  clearGlobalFilters: () => void;
  
  // Dashboard filters (per dashboard)
  addDashboardFilter: (dashboardId: string, filter: Omit<DashboardFilter, 'id'>) => string;
  updateDashboardFilter: (dashboardId: string, filterId: string, updates: Partial<DashboardFilter>) => void;
  removeDashboardFilter: (dashboardId: string, filterId: string) => void;
  
  // UI state management
  setEditing: (editing: boolean) => void;
  setSelectedWidgets: (widgetIds: string[]) => void;
  toggleWidgetSelection: (widgetId: string) => void;
  clearSelection: () => void;
  
  // Export/Import
  exportDashboard: (id: string) => Promise<string>;
  exportAllDashboards: () => Promise<string>;
  importDashboard: (data: string) => Promise<string>;
  
  // Persistence settings
  setAutoSave: (enabled: boolean) => void;
  setSaveInterval: (interval: number) => void;
  saveToStorage: () => void;
  loadFromStorage: () => void;
  
  // Reset
  resetDashboardStore: () => void;
}

export type DashboardStore = DashboardState & DashboardActions;

// Default templates
const defaultTemplates: DashboardTemplate[] = [
  {
    id: 'system-overview',
    name: 'System Overview',
    description: 'Comprehensive system health and performance monitoring',
    category: 'system',
    config: {
      name: 'System Overview',
      description: 'Monitor system health, performance, and key metrics',
      widgets: [
        {
          id: 'cpu-metric',
          type: 'metric',
          title: 'CPU Usage',
          size: 'small',
          position: { x: 0, y: 0, w: 1, h: 1 },
          config: { metric: 'cpu_usage', threshold: { warning: 70, critical: 90 } },
          enabled: true
        },
        {
          id: 'memory-metric',
          type: 'metric',
          title: 'Memory Usage',
          size: 'small',
          position: { x: 1, y: 0, w: 1, h: 1 },
          config: { metric: 'memory_usage', threshold: { warning: 80, critical: 95 } },
          enabled: true
        },
        {
          id: 'system-status',
          type: 'status',
          title: 'System Health',
          size: 'medium',
          position: { x: 2, y: 0, w: 2, h: 1 },
          config: { components: ['api', 'database', 'cache', 'storage'] },
          enabled: true
        },
        {
          id: 'performance-chart',
          type: 'chart',
          title: 'Performance Trends',
          size: 'large',
          position: { x: 0, y: 1, w: 4, h: 2 },
          config: { 
            metrics: ['cpu_usage', 'memory_usage', 'response_time'],
            timeRange: '24h',
            chartType: 'line'
          },
          enabled: true
        }
      ],
      layout: 'grid',
      refreshInterval: 30000,
      filters: []
    },
    tags: ['system', 'monitoring', 'performance'],
    isDefault: true
  },
  {
    id: 'ai-operations',
    name: 'AI Operations',
    description: 'Monitor AI models, providers, and inference performance',
    category: 'system',
    config: {
      name: 'AI Operations',
      description: 'Track AI model performance, provider health, and inference metrics',
      widgets: [
        {
          id: 'model-status',
          type: 'status',
          title: 'Model Status',
          size: 'medium',
          position: { x: 0, y: 0, w: 2, h: 1 },
          config: { models: ['gpt-4', 'claude-3', 'llama-2'] },
          enabled: true
        },
        {
          id: 'inference-metrics',
          type: 'metric',
          title: 'Inference Rate',
          size: 'small',
          position: { x: 2, y: 0, w: 1, h: 1 },
          config: { metric: 'inference_rate', unit: 'req/min' },
          enabled: true
        },
        {
          id: 'cost-tracking',
          type: 'metric',
          title: 'API Costs',
          size: 'small',
          position: { x: 3, y: 0, w: 1, h: 1 },
          config: { metric: 'api_costs', format: 'currency' },
          enabled: true
        },
        {
          id: 'provider-chart',
          type: 'chart',
          title: 'Provider Performance',
          size: 'large',
          position: { x: 0, y: 1, w: 4, h: 2 },
          config: { 
            metrics: ['latency', 'success_rate', 'cost_per_token'],
            groupBy: 'provider',
            chartType: 'bar'
          },
          enabled: true
        }
      ],
      layout: 'grid',
      refreshInterval: 60000,
      filters: []
    },
    tags: ['ai', 'models', 'providers', 'inference'],
    isDefault: true
  },
  {
    id: 'admin-dashboard',
    name: 'Administrator Dashboard',
    description: 'Comprehensive admin view with security and audit information',
    category: 'role-based',
    roles: ['admin', 'superuser'],
    config: {
      name: 'Administrator Dashboard',
      description: 'Security monitoring, user management, and system administration',
      widgets: [
        {
          id: 'security-status',
          type: 'status',
          title: 'Security Status',
          size: 'medium',
          position: { x: 0, y: 0, w: 2, h: 1 },
          config: { securityChecks: ['auth', 'permissions', 'audit', 'threats'] },
          enabled: true
        },
        {
          id: 'active-users',
          type: 'metric',
          title: 'Active Users',
          size: 'small',
          position: { x: 2, y: 0, w: 1, h: 1 },
          config: { metric: 'active_users' },
          enabled: true
        },
        {
          id: 'audit-logs',
          type: 'log',
          title: 'Audit Logs',
          size: 'large',
          position: { x: 0, y: 1, w: 3, h: 2 },
          config: { 
            logType: 'audit',
            filters: ['security', 'admin'],
            maxEntries: 100
          },
          enabled: true
        },
        {
          id: 'system-alerts',
          type: 'log',
          title: 'System Alerts',
          size: 'medium',
          position: { x: 3, y: 1, w: 1, h: 2 },
          config: { 
            logType: 'alerts',
            severity: ['warning', 'error', 'critical']
          },
          enabled: true
        }
      ],
      layout: 'grid',
      refreshInterval: 15000,
      filters: []
    },
    tags: ['admin', 'security', 'audit', 'management']
  }
];

// Initial state
const initialState: DashboardState = {
  dashboards: {},
  activeDashboardId: null,
  templates: defaultTemplates.reduce((acc, template) => {
    acc[template.id] = template;
    return acc;
  }, {} as Record<string, DashboardTemplate>),
  globalTimeRange: {
    start: new Date(Date.now() - 24 * 60 * 60 * 1000), // Last 24 hours
    end: new Date(),
    preset: 'last-day'
  },
  globalFilters: [],
  isEditing: false,
  selectedWidgets: [],
  exportInProgress: false,
  importInProgress: false,
  autoSave: true,
  saveInterval: 30000, // 30 seconds
};

// Utility functions
const generateId = () => `dashboard-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
const generateWidgetId = () => `widget-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
const generateFilterId = () => `filter-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

// Create the dashboard store
export const useDashboardStore = create<DashboardStore>()(
  subscribeWithSelector(
    persist(
      immer((set, get) => ({
        ...initialState,
        
        // Dashboard management
        createDashboard: (config) => {
          const id = generateId();
          const dashboard: DashboardConfig = {
            ...config,
            id,
            createdAt: new Date(),
            updatedAt: new Date()
          };
          
          set((state) => {
            state.dashboards[id] = dashboard;
            if (!state.activeDashboardId) {
              state.activeDashboardId = id;
            }
          });
          
          return id;
        },
        
        updateDashboard: (id, updates) => set((state) => {
          if (state.dashboards[id]) {
            state.dashboards[id] = {
              ...state.dashboards[id],
              ...updates,
              updatedAt: new Date()
            };
          }
        }),
        
        deleteDashboard: (id) => set((state) => {
          delete state.dashboards[id];
          if (state.activeDashboardId === id) {
            const remainingIds = Object.keys(state.dashboards);
            state.activeDashboardId = remainingIds.length > 0 ? remainingIds[0] : null;
          }
        }),
        
        duplicateDashboard: (id, name) => {
          const original = get().dashboards[id];
          if (!original) return '';
          
          const newId = generateId();
          const duplicated: DashboardConfig = {
            ...original,
            id: newId,
            name: name || `${original.name} (Copy)`,
            createdAt: new Date(),
            updatedAt: new Date(),
            widgets: original.widgets.map(widget => ({
              ...widget,
              id: generateWidgetId()
            }))
          };
          
          set((state) => {
            state.dashboards[newId] = duplicated;
          });
          
          return newId;
        },
        
        setActiveDashboard: (id) => set((state) => {
          if (state.dashboards[id]) {
            state.activeDashboardId = id;
          }
        }),
        
        // Widget management
        addWidget: (dashboardId, widget) => {
          const widgetId = generateWidgetId();
          const newWidget: WidgetConfig = {
            ...widget,
            id: widgetId
          };
          
          set((state) => {
            if (state.dashboards[dashboardId]) {
              state.dashboards[dashboardId].widgets.push(newWidget);
              state.dashboards[dashboardId].updatedAt = new Date();
            }
          });
          
          return widgetId;
        },
        
        updateWidget: (dashboardId, widgetId, updates) => set((state) => {
          const dashboard = state.dashboards[dashboardId];
          if (dashboard) {
            const widgetIndex = dashboard.widgets.findIndex(w => w.id === widgetId);
            if (widgetIndex !== -1) {
              dashboard.widgets[widgetIndex] = {
                ...dashboard.widgets[widgetIndex],
                ...updates
              };
              dashboard.updatedAt = new Date();
            }
          }
        }),
        
        removeWidget: (dashboardId, widgetId) => set((state) => {
          const dashboard = state.dashboards[dashboardId];
          if (dashboard) {
            dashboard.widgets = dashboard.widgets.filter(w => w.id !== widgetId);
            dashboard.updatedAt = new Date();
            // Remove from selection if selected
            state.selectedWidgets = state.selectedWidgets.filter(id => id !== widgetId);
          }
        }),
        
        reorderWidgets: (dashboardId, widgetIds) => set((state) => {
          const dashboard = state.dashboards[dashboardId];
          if (dashboard) {
            const widgetMap = new Map(dashboard.widgets.map(w => [w.id, w]));
            dashboard.widgets = widgetIds.map(id => widgetMap.get(id)!).filter(Boolean);
            dashboard.updatedAt = new Date();
          }
        }),
        
        // Template management
        createTemplate: (template) => {
          const id = generateId();
          const newTemplate: DashboardTemplate = {
            ...template,
            id
          };
          
          set((state) => {
            state.templates[id] = newTemplate;
          });
          
          return id;
        },
        
        updateTemplate: (id, updates) => set((state) => {
          if (state.templates[id]) {
            state.templates[id] = {
              ...state.templates[id],
              ...updates
            };
          }
        }),
        
        deleteTemplate: (id) => set((state) => {
          delete state.templates[id];
        }),
        
        applyTemplate: (templateId, dashboardId) => {
          const template = get().templates[templateId];
          if (!template) return '';
          
          const targetId = dashboardId || generateId();
          const dashboard: DashboardConfig = {
            ...template.config,
            id: targetId,
            createdAt: new Date(),
            updatedAt: new Date(),
            widgets: template.config.widgets.map(widget => ({
              ...widget,
              id: generateWidgetId()
            }))
          };
          
          set((state) => {
            state.dashboards[targetId] = dashboard;
            if (!dashboardId) {
              state.activeDashboardId = targetId;
            }
          });
          
          return targetId;
        },
        
        // Filter management
        setGlobalTimeRange: (timeRange) => set((state) => {
          state.globalTimeRange = timeRange;
        }),
        
        addGlobalFilter: (filter) => {
          const id = generateFilterId();
          const newFilter: DashboardFilter = {
            ...filter,
            id
          };
          
          set((state) => {
            state.globalFilters.push(newFilter);
          });
          
          return id;
        },
        
        updateGlobalFilter: (id, updates) => set((state) => {
          const filterIndex = state.globalFilters.findIndex(f => f.id === id);
          if (filterIndex !== -1) {
            state.globalFilters[filterIndex] = {
              ...state.globalFilters[filterIndex],
              ...updates
            };
          }
        }),
        
        removeGlobalFilter: (id) => set((state) => {
          state.globalFilters = state.globalFilters.filter(f => f.id !== id);
        }),
        
        clearGlobalFilters: () => set((state) => {
          state.globalFilters = [];
        }),
        
        // Dashboard filters
        addDashboardFilter: (dashboardId, filter) => {
          const id = generateFilterId();
          const newFilter: DashboardFilter = {
            ...filter,
            id
          };
          
          set((state) => {
            const dashboard = state.dashboards[dashboardId];
            if (dashboard) {
              dashboard.filters.push(newFilter);
              dashboard.updatedAt = new Date();
            }
          });
          
          return id;
        },
        
        updateDashboardFilter: (dashboardId, filterId, updates) => set((state) => {
          const dashboard = state.dashboards[dashboardId];
          if (dashboard) {
            const filterIndex = dashboard.filters.findIndex(f => f.id === filterId);
            if (filterIndex !== -1) {
              dashboard.filters[filterIndex] = {
                ...dashboard.filters[filterIndex],
                ...updates
              };
              dashboard.updatedAt = new Date();
            }
          }
        }),
        
        removeDashboardFilter: (dashboardId, filterId) => set((state) => {
          const dashboard = state.dashboards[dashboardId];
          if (dashboard) {
            dashboard.filters = dashboard.filters.filter(f => f.id !== filterId);
            dashboard.updatedAt = new Date();
          }
        }),
        
        // UI state management
        setEditing: (editing) => set((state) => {
          state.isEditing = editing;
          if (!editing) {
            state.selectedWidgets = [];
          }
        }),
        
        setSelectedWidgets: (widgetIds) => set((state) => {
          state.selectedWidgets = widgetIds;
        }),
        
        toggleWidgetSelection: (widgetId) => set((state) => {
          const index = state.selectedWidgets.indexOf(widgetId);
          if (index === -1) {
            state.selectedWidgets.push(widgetId);
          } else {
            state.selectedWidgets.splice(index, 1);
          }
        }),
        
        clearSelection: () => set((state) => {
          state.selectedWidgets = [];
        }),
        
        // Export/Import
        exportDashboard: async (id) => {
          const dashboard = get().dashboards[id];
          if (!dashboard) throw new Error('Dashboard not found');
          
          set((state) => {
            state.exportInProgress = true;
          });
          
          try {
            const exportData = {
              version: '1.0',
              type: 'dashboard',
              data: dashboard,
              exportedAt: new Date().toISOString(),
              exportedBy: 'user' // In real app, get from auth context
            };
            
            return JSON.stringify(exportData, null, 2);
          } finally {
            set((state) => {
              state.exportInProgress = false;
            });
          }
        },
        
        exportAllDashboards: async () => {
          const { dashboards, templates } = get();
          
          set((state) => {
            state.exportInProgress = true;
          });
          
          try {
            const exportData = {
              version: '1.0',
              type: 'dashboard-collection',
              data: {
                dashboards,
                templates: Object.values(templates).filter(t => t.category === 'user')
              },
              exportedAt: new Date().toISOString(),
              exportedBy: 'user'
            };
            
            return JSON.stringify(exportData, null, 2);
          } finally {
            set((state) => {
              state.exportInProgress = false;
            });
          }
        },
        
        importDashboard: async (data) => {
          set((state) => {
            state.importInProgress = true;
          });
          
          try {
            const importData = JSON.parse(data);
            
            if (importData.type === 'dashboard') {
              const dashboard = importData.data as DashboardConfig;
              const newId = generateId();
              const importedDashboard: DashboardConfig = {
                ...dashboard,
                id: newId,
                name: `${dashboard.name} (Imported)`,
                createdAt: new Date(),
                updatedAt: new Date(),
                widgets: dashboard.widgets.map(widget => ({
                  ...widget,
                  id: generateWidgetId()
                }))
              };
              
              set((state) => {
                state.dashboards[newId] = importedDashboard;
              });
              
              return newId;
            } else if (importData.type === 'dashboard-collection') {
              const { dashboards, templates } = importData.data;
              const importedIds: string[] = [];
              
              set((state) => {
                // Import dashboards
                Object.values(dashboards).forEach((dashboard: any) => {
                  const newId = generateId();
                  const importedDashboard: DashboardConfig = {
                    ...dashboard,
                    id: newId,
                    name: `${dashboard.name} (Imported)`,
                    createdAt: new Date(),
                    updatedAt: new Date(),
                    widgets: dashboard.widgets.map((widget: any) => ({
                      ...widget,
                      id: generateWidgetId()
                    }))
                  };
                  
                  state.dashboards[newId] = importedDashboard;
                  importedIds.push(newId);
                });
                
                // Import user templates
                templates?.forEach((template: any) => {
                  const newId = generateId();
                  state.templates[newId] = {
                    ...template,
                    id: newId,
                    category: 'user'
                  };
                });
              });
              
              return importedIds[0] || '';
            }
            
            throw new Error('Invalid import data format');
          } catch (error) {
            throw new Error(`Import failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
          } finally {
            set((state) => {
              state.importInProgress = false;
            });
          }
        },
        
        // Persistence settings
        setAutoSave: (enabled) => set((state) => {
          state.autoSave = enabled;
        }),
        
        setSaveInterval: (interval) => set((state) => {
          state.saveInterval = interval;
        }),
        
        saveToStorage: () => {
          // This is handled by the persist middleware
          // But we can trigger manual saves here if needed
        },
        
        loadFromStorage: () => {
          // This is handled by the persist middleware
          // But we can trigger manual loads here if needed
        },
        
        // Reset
        resetDashboardStore: () => set(() => ({ ...initialState })),
      })),
      {
        name: 'kari-dashboard-store',
        storage: createJSONStorage(() => localStorage),
        // Persist everything except UI state
        partialize: (state) => ({
          dashboards: state.dashboards,
          templates: Object.fromEntries(
            Object.entries(state.templates).filter(([_, template]) => template.category === 'user')
          ),
          globalTimeRange: state.globalTimeRange,
          globalFilters: state.globalFilters,
          autoSave: state.autoSave,
          saveInterval: state.saveInterval,
        }),
        version: 1,
      }
    )
  )
);

// Selectors
export const selectActiveDashboard = (state: DashboardStore) => 
  state.activeDashboardId ? state.dashboards[state.activeDashboardId] : null;

export const selectDashboardById = (id: string) => (state: DashboardStore) => 
  state.dashboards[id];

export const selectTemplatesByCategory = (category: DashboardTemplate['category']) => (state: DashboardStore) =>
  Object.values(state.templates).filter(template => template.category === category);

export const selectTemplatesForUser = (userRoles: string[]) => (state: DashboardStore) =>
  Object.values(state.templates).filter(template => 
    template.category === 'system' || 
    template.category === 'user' ||
    (template.category === 'role-based' && template.roles?.some(role => userRoles.includes(role)))
  );

export const selectGlobalFilters = (state: DashboardStore) => state.globalFilters;
export const selectGlobalTimeRange = (state: DashboardStore) => state.globalTimeRange;
export const selectIsEditing = (state: DashboardStore) => state.isEditing;
export const selectSelectedWidgets = (state: DashboardStore) => state.selectedWidgets;