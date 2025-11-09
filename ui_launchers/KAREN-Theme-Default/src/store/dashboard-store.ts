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
  DashboardLayout,
} from '@/types/dashboard';

// ────────────────────────────────────────────────────────────────────────────────
// Types
// ────────────────────────────────────────────────────────────────────────────────

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

export interface TimeRange {
  start: Date;
  end: Date;
  preset?: 'last-hour' | 'last-day' | 'last-week' | 'last-month' | 'custom';
}

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

export interface DashboardActions {
  // Dashboard management
  createDashboard: (
    config: Omit<DashboardConfig, 'id' | 'createdAt' | 'updatedAt'>
  ) => string;
  updateDashboard: (id: string, updates: Partial<DashboardConfig>) => void;
  deleteDashboard: (id: string) => void;
  duplicateDashboard: (id: string, name?: string) => string;
  setActiveDashboard: (id: string) => void;

  // Widget management
  addWidget: (dashboardId: string, widget: Omit<WidgetConfig, 'id'>) => string;
  updateWidget: (
    dashboardId: string,
    widgetId: string,
    updates: Partial<WidgetConfig>
  ) => void;
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
  addDashboardFilter: (
    dashboardId: string,
    filter: Omit<DashboardFilter, 'id'>
  ) => string;
  updateDashboardFilter: (
    dashboardId: string,
    filterId: string,
    updates: Partial<DashboardFilter>
  ) => void;
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

// ────────────────────────────────────────────────────────────────────────────────
/** Default templates */
// ────────────────────────────────────────────────────────────────────────────────

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
          enabled: true,
        },
        {
          id: 'memory-metric',
          type: 'metric',
          title: 'Memory Usage',
          size: 'small',
          position: { x: 1, y: 0, w: 1, h: 1 },
          config: { metric: 'memory_usage', threshold: { warning: 80, critical: 95 } },
          enabled: true,
        },
        {
          id: 'system-status',
          type: 'status',
          title: 'System Health',
          size: 'medium',
          position: { x: 2, y: 0, w: 2, h: 1 },
          config: { components: ['api', 'database', 'cache', 'storage'] },
          enabled: true,
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
            chartType: 'line',
          },
          enabled: true,
        },
      ],
      layout: 'grid' as DashboardLayout,
      refreshInterval: 30000,
      filters: [],
    },
    tags: ['system', 'monitoring', 'performance'],
    isDefault: true,
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
          enabled: true,
        },
        {
          id: 'inference-metrics',
          type: 'metric',
          title: 'Inference Rate',
          size: 'small',
          position: { x: 2, y: 0, w: 1, h: 1 },
          config: { metric: 'inference_rate', unit: 'req/min' },
          enabled: true,
        },
        {
          id: 'cost-tracking',
          type: 'metric',
          title: 'API Costs',
          size: 'small',
          position: { x: 3, y: 0, w: 1, h: 1 },
          config: { metric: 'api_costs', format: 'currency' },
          enabled: true,
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
            chartType: 'bar',
          },
          enabled: true,
        },
      ],
      layout: 'grid' as DashboardLayout,
      refreshInterval: 60000,
      filters: [],
    },
    tags: ['ai', 'models', 'providers', 'inference'],
    isDefault: true,
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
          enabled: true,
        },
        {
          id: 'active-users',
          type: 'metric',
          title: 'Active Users',
          size: 'small',
          position: { x: 2, y: 0, w: 1, h: 1 },
          config: { metric: 'active_users' },
          enabled: true,
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
            maxEntries: 100,
          },
          enabled: true,
        },
        {
          id: 'system-alerts',
          type: 'log',
          title: 'System Alerts',
          size: 'medium',
          position: { x: 3, y: 1, w: 1, h: 2 },
          config: {
            logType: 'alerts',
            severity: ['warning', 'error', 'critical'],
          },
          enabled: true,
        },
      ],
      layout: 'grid' as DashboardLayout,
      refreshInterval: 15000,
      filters: [],
    },
    tags: ['admin', 'security', 'audit', 'management'],
  },
];

// ────────────────────────────────────────────────────────────────────────────────
// Initial state
// ────────────────────────────────────────────────────────────────────────────────

const initialState: DashboardState = {
  dashboards: {},
  activeDashboardId: null,
  templates: defaultTemplates.reduce((acc, template) => {
    acc[template.id] = template;
    return acc;
  }, {} as Record<string, DashboardTemplate>),
  globalTimeRange: {
    start: new Date(Date.now() - 24 * 60 * 60 * 1000),
    end: new Date(),
    preset: 'last-day',
  },
  globalFilters: [],
  isEditing: false,
  selectedWidgets: [],
  exportInProgress: false,
  importInProgress: false,
  autoSave: true,
  saveInterval: 30000,
};

// ────────────────────────────────────────────────────────────────────────────────
// Utils
// ────────────────────────────────────────────────────────────────────────────────

const generateId = () =>
  `dashboard-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
const generateWidgetId = () =>
  `widget-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
const generateFilterId = () =>
  `filter-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;

// ────────────────────────────────────────────────────────────────────────────────
// Store
// ────────────────────────────────────────────────────────────────────────────────

export const useDashboardStore = create<DashboardStore>()(
  subscribeWithSelector(
    persist(
      immer<DashboardStore>((set, get) => ({
        ...initialState,

        // ───────── Dashboard management
        createDashboard: (config) => {
          const id = generateId();
          const dashboard: DashboardConfig = {
            ...config,
            id,
            createdAt: new Date(),
            updatedAt: new Date(),
          };

          set((state) => {
            state.dashboards[id] = dashboard;
            if (!state.activeDashboardId) {
              state.activeDashboardId = id;
            }
          });

          return id;
        },

        updateDashboard: (id, updates) =>
          set((state) => {
            if (state.dashboards[id]) {
              state.dashboards[id] = {
                ...state.dashboards[id],
                ...updates,
                updatedAt: new Date(),
              };
            }
          }),

        deleteDashboard: (id) =>
          set((state) => {
            delete state.dashboards[id];
            if (state.activeDashboardId === id) {
              const remainingIds = Object.keys(state.dashboards);
              state.activeDashboardId =
                remainingIds.length > 0 ? remainingIds[0] : null;
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
            widgets: original.widgets.map((widget) => ({
              ...widget,
              id: generateWidgetId(),
            })),
          };

          set((state) => {
            state.dashboards[newId] = duplicated;
          });

          return newId;
        },

        setActiveDashboard: (id) =>
          set((state) => {
            if (state.dashboards[id]) {
              state.activeDashboardId = id;
            }
          }),

        // ───────── Widget management
        addWidget: (dashboardId, widget) => {
          const widgetId = generateWidgetId();
          const newWidget: WidgetConfig = {
            ...widget,
            id: widgetId,
          };

          set((state) => {
            if (state.dashboards[dashboardId]) {
              state.dashboards[dashboardId].widgets.push(newWidget);
              state.dashboards[dashboardId].updatedAt = new Date();
            }
          });

          return widgetId;
        },

        updateWidget: (dashboardId, widgetId, updates) =>
          set((state) => {
            const dashboard = state.dashboards[dashboardId];
            if (dashboard) {
              const idx = dashboard.widgets.findIndex((w) => w.id === widgetId);
              if (idx !== -1) {
                dashboard.widgets[idx] = {
                  ...dashboard.widgets[idx],
                  ...updates,
                };
                dashboard.updatedAt = new Date();
              }
            }
          }),

        removeWidget: (dashboardId, widgetId) =>
          set((state) => {
            const dashboard = state.dashboards[dashboardId];
            if (dashboard) {
              dashboard.widgets = dashboard.widgets.filter((w) => w.id !== widgetId);
              dashboard.updatedAt = new Date();
              // Remove from selection if selected
              state.selectedWidgets = state.selectedWidgets.filter((id) => id !== widgetId);
            }
          }),

        reorderWidgets: (dashboardId, widgetIds) =>
          set((state) => {
            const dashboard = state.dashboards[dashboardId];
            if (dashboard) {
              const map = new Map(dashboard.widgets.map((w) => [w.id, w]));
              const reordered: WidgetConfig[] = [];
              widgetIds.forEach((id) => {
                const w = map.get(id);
                if (w) reordered.push(w);
              });
              // Include any widgets not present in widgetIds (fallback)
              dashboard.widgets.forEach((w) => {
                if (!widgetIds.includes(w.id)) reordered.push(w);
              });
              dashboard.widgets = reordered;
              dashboard.updatedAt = new Date();
            }
          }),

        // ───────── Template management
        createTemplate: (template) => {
          const id = generateId();
          const newTemplate: DashboardTemplate = { ...template, id };

          set((state) => {
            state.templates[id] = newTemplate;
          });

          return id;
        },

        updateTemplate: (id, updates) =>
          set((state) => {
            if (state.templates[id]) {
              state.templates[id] = {
                ...state.templates[id],
                ...updates,
              };
            }
          }),

        deleteTemplate: (id) =>
          set((state) => {
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
            widgets: template.config.widgets.map((w) => ({
              ...w,
              id: generateWidgetId(),
            })),
          };

          set((state) => {
            state.dashboards[targetId] = dashboard;
            if (!dashboardId) {
              state.activeDashboardId = targetId;
            }
          });

          return targetId;
        },

        // ───────── Global filter management
        setGlobalTimeRange: (timeRange) =>
          set((state) => {
            state.globalTimeRange = timeRange;
          }),

        addGlobalFilter: (filter) => {
          const id = generateFilterId();
          const newFilter: DashboardFilter = { ...filter, id };

          set((state) => {
            state.globalFilters.push(newFilter);
          });

          return id;
        },

        updateGlobalFilter: (id, updates) =>
          set((state) => {
            const idx = state.globalFilters.findIndex((f) => f.id === id);
            if (idx !== -1) {
              state.globalFilters[idx] = {
                ...state.globalFilters[idx],
                ...updates,
              };
            }
          }),

        removeGlobalFilter: (id) =>
          set((state) => {
            state.globalFilters = state.globalFilters.filter((f) => f.id !== id);
          }),

        clearGlobalFilters: () =>
          set((state) => {
            state.globalFilters = [];
          }),

        // ───────── Per-dashboard filters
        addDashboardFilter: (dashboardId, filter) => {
          const id = generateFilterId();
          const newFilter: DashboardFilter = { ...filter, id };

          set((state) => {
            const dashboard = state.dashboards[dashboardId];
            if (dashboard) {
              dashboard.filters.push(newFilter);
              dashboard.updatedAt = new Date();
            }
          });

          return id;
        },

        updateDashboardFilter: (dashboardId, filterId, updates) =>
          set((state) => {
            const dashboard = state.dashboards[dashboardId];
            if (dashboard) {
              const idx = dashboard.filters.findIndex((f) => f.id === filterId);
              if (idx !== -1) {
                dashboard.filters[idx] = {
                  ...dashboard.filters[idx],
                  ...updates,
                };
                dashboard.updatedAt = new Date();
              }
            }
          }),

        removeDashboardFilter: (dashboardId, filterId) =>
          set((state) => {
            const dashboard = state.dashboards[dashboardId];
            if (dashboard) {
              dashboard.filters = dashboard.filters.filter((f) => f.id !== filterId);
              dashboard.updatedAt = new Date();
            }
          }),

        // ───────── UI state management
        setEditing: (editing) =>
          set((state) => {
            state.isEditing = editing;
            if (!editing) {
              state.selectedWidgets = [];
            }
          }),

        setSelectedWidgets: (widgetIds) =>
          set((state) => {
            state.selectedWidgets = widgetIds;
          }),

        toggleWidgetSelection: (widgetId) =>
          set((state) => {
            const idx = state.selectedWidgets.indexOf(widgetId);
            if (idx === -1) {
              state.selectedWidgets.push(widgetId);
            } else {
              state.selectedWidgets.splice(idx, 1);
            }
          }),

        clearSelection: () =>
          set((state) => {
            state.selectedWidgets = [];
          }),

        // ───────── Export / Import
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
              exportedBy: 'user',
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
                templates: Object.values(templates).filter((t) => t.category === 'user'),
              },
              exportedAt: new Date().toISOString(),
              exportedBy: 'user',
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
                widgets: dashboard.widgets.map((w: WidgetConfig) => ({
                  ...w,
                  id: generateWidgetId(),
                })),
              };

              set((state) => {
                state.dashboards[newId] = importedDashboard;
              });

              return newId;
            } else if (importData.type === 'dashboard-collection') {
              const { dashboards: ds, templates: ts } = importData.data || {};
              const importedIds: string[] = [];

              set((state) => {
                // Dashboards
                Object.values(ds || {}).forEach((dashboard: any) => {
                  const newId = generateId();
                  const importedDashboard: DashboardConfig = {
                    ...dashboard,
                    id: newId,
                    name: `${dashboard.name} (Imported)`,
                    createdAt: new Date(),
                    updatedAt: new Date(),
                    widgets: (dashboard.widgets || []).map((w: any) => ({
                      ...w,
                      id: generateWidgetId(),
                    })),
                  };
                  state.dashboards[newId] = importedDashboard;
                  importedIds.push(newId);
                });

                // User templates only
                (ts || []).forEach((template: any) => {
                  const newTid = generateId();
                  state.templates[newTid] = {
                    ...template,
                    id: newTid,
                    category: 'user',
                  };
                });
              });

              return importedIds[0] || '';
            }

            throw new Error('Invalid import data format');
          } catch (error: any) {
            throw new Error(`Import failed: ${error?.message ?? 'Unknown error'}`);
          } finally {
            set((state) => {
              state.importInProgress = false;
            });
          }
        },

        // ───────── Persistence settings
        setAutoSave: (enabled) =>
          set((state) => {
            state.autoSave = enabled;
          }),

        setSaveInterval: (interval) =>
          set((state) => {
            state.saveInterval = interval;
          }),

        saveToStorage: () => {
          // Handled by persist; hook kept for API parity
        },

        loadFromStorage: () => {
          // Handled by persist; hook kept for API parity
        },

        // ───────── Reset
        resetDashboardStore: () => set(() => ({ ...initialState })),
      })),
      {
        name: 'kari-dashboard-store',
        storage: createJSONStorage(() => localStorage),
        // Persist everything except ephemeral UI flags
        partialize: (state) => ({
          dashboards: state.dashboards,
          templates: Object.fromEntries(
            Object.entries(state.templates).filter(
              ([, template]) => template.category === 'user'
            )
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

// ────────────────────────────────────────────────────────────────────────────────
// Selectors
// ────────────────────────────────────────────────────────────────────────────────

export const selectActiveDashboard = (state: DashboardStore) =>
  state.activeDashboardId ? state.dashboards[state.activeDashboardId] : null;

export const selectDashboardById =
  (id: string) =>
  (state: DashboardStore) =>
    state.dashboards[id];

export const selectTemplatesByCategory =
  (category: DashboardTemplate['category']) =>
  (state: DashboardStore) =>
    Object.values(state.templates).filter((t) => t.category === category);

export const selectTemplatesForUser =
  (userRoles: string[]) =>
  (state: DashboardStore) =>
    Object.values(state.templates).filter(
      (t) =>
        t.category === 'system' ||
        t.category === 'user' ||
        (t.category === 'role-based' &&
          t.roles?.some((role) => userRoles.includes(role)))
    );

export const selectGlobalFilters = (state: DashboardStore) => state.globalFilters;
export const selectGlobalTimeRange = (state: DashboardStore) => state.globalTimeRange;
export const selectIsEditing = (state: DashboardStore) => state.isEditing;
export const selectSelectedWidgets = (state: DashboardStore) => state.selectedWidgets;
