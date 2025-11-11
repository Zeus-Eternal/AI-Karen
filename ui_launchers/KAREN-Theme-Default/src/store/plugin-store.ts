/**
 * Plugin Store
 *
 * Zustand store for plugin management state and operations.
 * Based on requirements: 5.1, 5.2, 5.3, 5.4, 5.5
 */

import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { subscribeWithSelector } from 'zustand/middleware';
import type {
  PluginInfo,
  PluginInstallationRequest,
  PluginMarketplaceEntry,
  PluginFilter,
  PluginConfig,
  PluginStore, // state + actions union
  PluginStoreState,
  PluginStoreActions,
} from '@/types/plugins';
export type { PluginStore } from '@/types/plugins';
import { enhancedApiClient } from '@/lib/enhanced-api-client';

// ────────────────────────────────────────────────────────────────────────────────
// Real API service using enhanced API client
// ────────────────────────────────────────────────────────────────────────────────
class PluginAPIService {
  /**
   * List all installed plugins
   */
  async listPlugins(): Promise<PluginInfo[]> {
    try {
      const response = await enhancedApiClient.get<PluginInfo[]>('/plugins');
      return response.data;
    } catch (error) {
      console.error('[PluginAPI] Failed to list plugins:', error);
      throw new Error('Failed to load plugins. Please check your connection and try again.');
    }
  }

  /**
   * Install a plugin from the marketplace or URL
   */
  async installPlugin(request: PluginInstallationRequest): Promise<string> {
    try {
      const response = await enhancedApiClient.post<{ installationId: string }>(
        '/plugins/install',
        request
      );
      return response.data.installationId;
    } catch (error) {
      console.error('[PluginAPI] Failed to install plugin:', error);
      throw new Error('Failed to install plugin. Please check the plugin source and try again.');
    }
  }

  /**
   * Uninstall a plugin by ID
   */
  async uninstallPlugin(id: string): Promise<void> {
    try {
      await enhancedApiClient.delete(`/plugins/${id}`);
    } catch (error) {
      console.error(`[PluginAPI] Failed to uninstall plugin ${id}:`, error);
      throw new Error('Failed to uninstall plugin. Please try again.');
    }
  }

  /**
   * Enable a plugin by ID
   */
  async enablePlugin(id: string): Promise<void> {
    try {
      await enhancedApiClient.post(`/plugins/${id}/enable`);
    } catch (error) {
      console.error(`[PluginAPI] Failed to enable plugin ${id}:`, error);
      throw new Error('Failed to enable plugin. Please try again.');
    }
  }

  /**
   * Disable a plugin by ID
   */
  async disablePlugin(id: string): Promise<void> {
    try {
      await enhancedApiClient.post(`/plugins/${id}/disable`);
    } catch (error) {
      console.error(`[PluginAPI] Failed to disable plugin ${id}:`, error);
      throw new Error('Failed to disable plugin. Please try again.');
    }
  }

  /**
   * Update plugin configuration
   */
  async configurePlugin(id: string, config: PluginConfig): Promise<void> {
    try {
      await enhancedApiClient.put(`/plugins/${id}/config`, config);
    } catch (error) {
      console.error(`[PluginAPI] Failed to configure plugin ${id}:`, error);
      throw new Error('Failed to update plugin configuration. Please try again.');
    }
  }

  /**
   * Search marketplace for plugins
   */
  async searchMarketplace(query?: string): Promise<PluginMarketplaceEntry[]> {
    try {
      const endpoint = query ? `/plugins/marketplace?q=${encodeURIComponent(query)}` : '/plugins/marketplace';
      const response = await enhancedApiClient.get<PluginMarketplaceEntry[]>(endpoint);
      return response.data;
    } catch (error) {
      console.error('[PluginAPI] Failed to search marketplace:', error);
      throw new Error('Failed to load marketplace plugins. Please try again.');
    }
  }
}

const pluginAPI = new PluginAPIService();

// ────────────────────────────────────────────────────────────────────────────────
// Initial state (make dynamic maps for op-level loading/errors)
// ────────────────────────────────────────────────────────────────────────────────
const initialState: PluginStoreState = {
  plugins: [],
  selectedPlugin: null,
  installations: {}, // Record<string, PluginInstallationProgress>

  marketplacePlugins: [],

  // Use dynamic maps to support operation-scoped keys: "enable-<id>", etc.
  loading: {
    plugins: false,
    installation: false,
    marketplace: false,
  } as Record<string, boolean> & { plugins: boolean; installation: boolean; marketplace: boolean },

  errors: {
    plugins: null,
    installation: null,
    marketplace: null,
  } as Record<string, string | null> & { plugins: string | null; installation: string | null; marketplace: string | null },

  searchQuery: '',
  filters: {},
  sortBy: 'name',
  sortOrder: 'asc',

  view: 'list',
  showInstallationWizard: false,
  showMarketplace: false,
};

// ────────────────────────────────────────────────────────────────────────────────
// Debounce helper to prevent race conditions
// ────────────────────────────────────────────────────────────────────────────────
let loadPluginsTimeout: NodeJS.Timeout | null = null;
let isLoadingPlugins = false;

const debouncedLoadPlugins = async (loadPluginsFn: () => Promise<void>, delay: number = 500) => {
  // Clear any pending debounced call
  if (loadPluginsTimeout) {
    clearTimeout(loadPluginsTimeout);
    loadPluginsTimeout = null;
  }

  // If already loading, skip this call
  if (isLoadingPlugins) {
    return;
  }

  // Debounce the call
  return new Promise<void>((resolve) => {
    loadPluginsTimeout = setTimeout(async () => {
      isLoadingPlugins = true;
      try {
        await loadPluginsFn();
      } finally {
        isLoadingPlugins = false;
        loadPluginsTimeout = null;
      }
      resolve();
    }, delay);
  });
};

// ────────────────────────────────────────────────────────────────────────────────
export const usePluginStore = create<PluginStore>()(
  subscribeWithSelector(
    immer<PluginStoreState & PluginStoreActions>((set, get) => ({
      ...initialState,

      // ───────── Plugin operations
      loadPlugins: async () => {
        set((state) => {
          state.loading.plugins = true;
          state.errors.plugins = null;
        });

        try {
          const plugins = await pluginAPI.listPlugins();
          set((state) => {
            state.plugins = plugins;
            state.loading.plugins = false;
          });
        } catch (error) {
          set((state) => {
            state.loading.plugins = false;
            state.errors.plugins =
              error instanceof Error ? error.message : 'Failed to load plugins';
          });
        }
      },

      selectPlugin: (plugin) =>
        set((state) => {
          state.selectedPlugin = plugin;
        }),

      installPlugin: async (request) => {
        set((state) => {
          state.loading.installation = true;
          state.errors.installation = null;
        });

        try {
          const installationId = await pluginAPI.installPlugin(request);

          // initialize progress
          set((state) => {
            state.installations[installationId] = {
              stage: 'downloading',
              progress: 0,
              message: 'Starting installation...',
            };
          });

          const progressStages = [
            { stage: 'downloading' as const, progress: 20, message: 'Downloading plugin...' },
            { stage: 'validating' as const, progress: 40, message: 'Validating plugin manifest...' },
            { stage: 'resolving' as const, progress: 60, message: 'Resolving dependencies...' },
            { stage: 'installing' as const, progress: 80, message: 'Installing plugin...' },
            { stage: 'configuring' as const, progress: 90, message: 'Configuring plugin...' },
            { stage: 'complete' as const, progress: 100, message: 'Installation complete!' },
          ];

          for (const stage of progressStages) {
            // simulate step
            await new Promise((r) => setTimeout(r, 350));
            set((state) => {
              if (state.installations[installationId]) {
                state.installations[installationId] = {
                  ...state.installations[installationId],
                  ...stage,
                };
              }
            });
          }

          // Use debounced loadPlugins to prevent race conditions
          await debouncedLoadPlugins(() => get().loadPlugins());

          set((state) => {
            state.loading.installation = false;
            delete state.installations[installationId];
          });

          return installationId;
        } catch (error) {
          set((state) => {
            state.loading.installation = false;
            state.errors.installation =
              error instanceof Error ? error.message : 'Installation failed';
          });
          throw error;
        }
      },

      uninstallPlugin: async (id: string) => {
        set((state) => {
          state.loading[`uninstall-${id}`] = true;
        });

        try {
          await pluginAPI.uninstallPlugin(id);

          set((state) => {
            state.plugins = state.plugins.filter((p) => p.id !== id);
            if (state.selectedPlugin?.id === id) {
              state.selectedPlugin = null;
            }
            delete state.loading[`uninstall-${id}`];
          });
        } catch (error) {
          set((state) => {
            delete state.loading[`uninstall-${id}`];
            state.errors[`uninstall-${id}`] =
              error instanceof Error ? error.message : 'Uninstallation failed';
          });
          throw error;
        }
      },

      enablePlugin: async (id: string) => {
        set((state) => {
          state.loading[`enable-${id}`] = true;
        });

        try {
          await pluginAPI.enablePlugin(id);

          set((state) => {
            const plugin = state.plugins.find((p) => p.id === id);
            if (plugin) {
              plugin.enabled = true;
              plugin.status = 'active';
            }
            if (state.selectedPlugin?.id === id && state.selectedPlugin) {
              state.selectedPlugin.enabled = true;
              state.selectedPlugin.status = 'active';
            }
            delete state.loading[`enable-${id}`];
          });
        } catch (error) {
          set((state) => {
            delete state.loading[`enable-${id}`];
            state.errors[`enable-${id}`] =
              error instanceof Error ? error.message : 'Failed to enable plugin';
          });
          throw error;
        }
      },

      disablePlugin: async (id: string) => {
        set((state) => {
          state.loading[`disable-${id}`] = true;
        });

        try {
          await pluginAPI.disablePlugin(id);

          set((state) => {
            const plugin = state.plugins.find((p) => p.id === id);
            if (plugin) {
              plugin.enabled = false;
              plugin.status = 'inactive';
            }
            if (state.selectedPlugin?.id === id && state.selectedPlugin) {
              state.selectedPlugin.enabled = false;
              state.selectedPlugin.status = 'inactive';
            }
            delete state.loading[`disable-${id}`];
          });
        } catch (error) {
          set((state) => {
            delete state.loading[`disable-${id}`];
            state.errors[`disable-${id}`] =
              error instanceof Error ? error.message : 'Failed to disable plugin';
          });
          throw error;
        }
      },

      configurePlugin: async (id: string, config: PluginConfig) => {
        set((state) => {
          state.loading[`configure-${id}`] = true;
        });

        try {
          await pluginAPI.configurePlugin(id, config);

          set((state) => {
            const plugin = state.plugins.find((p) => p.id === id);
            if (plugin) {
              plugin.config = { ...plugin.config, ...config };
            }
            if (state.selectedPlugin?.id === id && state.selectedPlugin) {
              state.selectedPlugin.config = {
                ...state.selectedPlugin.config,
                ...config,
              };
            }
            delete state.loading[`configure-${id}`];
          });
        } catch (error) {
          set((state) => {
            delete state.loading[`configure-${id}`];
            state.errors[`configure-${id}`] =
              error instanceof Error ? error.message : 'Failed to configure plugin';
          });
          throw error;
        }
      },

      // ───────── Marketplace operations
      loadMarketplacePlugins: async (query?: string) => {
        set((state) => {
          state.loading.marketplace = true;
          state.errors.marketplace = null;
        });

        try {
          const plugins = await pluginAPI.searchMarketplace(query);
          set((state) => {
            state.marketplacePlugins = plugins;
            state.loading.marketplace = false;
          });
        } catch (error) {
          set((state) => {
            state.loading.marketplace = false;
            state.errors.marketplace =
              error instanceof Error ? error.message : 'Failed to load marketplace';
          });
        }
      },

      // ───────── UI operations
      setSearchQuery: (query: string) =>
        set((state) => {
          state.searchQuery = query;
        }),

      setFilters: (filters: Partial<PluginFilter>) =>
        set((state) => {
          state.filters = { ...state.filters, ...filters };
        }),

      setSorting: (sortBy: string, sortOrder: 'asc' | 'desc') =>
        set((state) => {
          // Validate sortBy against allowed values
          const validSortFields = ['name', 'status', 'version', 'installedAt', 'lastUsed', 'performance'] as const;
          type ValidSortField = typeof validSortFields[number];

          if (validSortFields.includes(sortBy as ValidSortField)) {
            state.sortBy = sortBy as ValidSortField;
            state.sortOrder = sortOrder;
          } else {
            console.warn(`[PluginStore] Invalid sortBy field: ${sortBy}. Using default: name`);
            state.sortBy = 'name';
            state.sortOrder = sortOrder;
          }
        }),

      setView: (view: 'list' | 'grid' | 'details') =>
        set((state) => {
          state.view = view;
        }),

      setShowInstallationWizard: (show: boolean) =>
        set((state) => {
          state.showInstallationWizard = show;
        }),

      setShowMarketplace: (show: boolean) =>
        set((state) => {
          state.showMarketplace = show;
        }),

      // ───────── Error handling
      setError: (key: string, error: string | null) =>
        set((state) => {
          if (error) state.errors[key] = error;
          else delete state.errors[key];
        }),

      clearErrors: () =>
        set((state) => {
          state.errors = {
            plugins: null,
            installation: null,
            marketplace: null,
          } as typeof state.errors;
        }),
    }))
  )
);

// ────────────────────────────────────────────────────────────────────────────────
// Selectors
// ────────────────────────────────────────────────────────────────────────────────
export const selectPlugins = (state: PluginStore) => state.plugins;
export const selectSelectedPlugin = (state: PluginStore) => state.selectedPlugin;
export const selectPluginLoading =
  (key: string) =>
  (state: PluginStore) =>
    (state.loading as Record<string, boolean>)[key] ?? false;
export const selectPluginError =
  (key: string) =>
  (state: PluginStore) =>
    (state.errors as Record<string, string | null>)[key] ?? null;
export const selectMarketplacePlugins = (state: PluginStore) => state.marketplacePlugins;
export const selectInstallationProgress =
  (id: string) =>
  (state: PluginStore) =>
    state.installations[id];

// Filtered & sorted (no state mutation)
export const selectFilteredPlugins = (state: PluginStore) => {
  let filtered = state.plugins;

  // Search
  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    filtered = filtered.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.manifest.description.toLowerCase().includes(q) ||
        p.manifest.keywords.some((k) => k.toLowerCase().includes(q))
    );
  }

  // Filters
  if (state.filters.status?.length) {
    filtered = filtered.filter((p) => state.filters.status!.includes(p.status));
  }
  if (state.filters.category?.length) {
    filtered = filtered.filter((p) =>
      state.filters.category!.includes(p.manifest.category)
    );
  }
  if (state.filters.enabled !== undefined) {
    filtered = filtered.filter((p) => p.enabled === state.filters.enabled);
  }
  if (state.filters.hasErrors) {
    filtered = filtered.filter((p) => !!p.lastError);
  }

  // Sort (copy to avoid mutating state)
  const sorted = [...filtered].sort((a, b) => {
    let aValue: unknown;
    let bValue: unknown;

    switch (state.sortBy) {
      case 'name':
        aValue = a.name.toLowerCase();
        bValue = b.name.toLowerCase();
        break;
      case 'status':
        aValue = a.status;
        bValue = b.status;
        break;
      case 'version':
        aValue = a.version;
        bValue = b.version;
        break;
      case 'installedAt':
        aValue = a.installedAt?.getTime() ?? 0;
        bValue = b.installedAt?.getTime() ?? 0;
        break;
      case 'performance':
        aValue = a.metrics.performance.averageExecutionTime;
        bValue = b.metrics.performance.averageExecutionTime;
        break;
      default:
        return 0;
    }

    if ((aValue as number | string) < (bValue as number | string)) return state.sortOrder === 'asc' ? -1 : 1;
    if ((aValue as number | string) > (bValue as number | string)) return state.sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  return sorted;
};
