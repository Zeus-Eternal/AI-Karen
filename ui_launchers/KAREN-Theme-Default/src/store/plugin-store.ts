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

// ────────────────────────────────────────────────────────────────────────────────
// Mock API service (placeholder — wire to real API client)
// ────────────────────────────────────────────────────────────────────────────────
class PluginAPIService {
  async listPlugins(): Promise<PluginInfo[]> {
    return [
      {
        id: 'weather-plugin',
        name: 'Weather Service',
        version: '1.2.0',
        status: 'active',
        enabled: true,
        autoStart: true,
        restartCount: 0,
        installedAt: new Date('2024-01-15'),
        updatedAt: new Date('2024-01-20'),
        installedBy: 'admin',
        manifest: {
          id: 'weather-plugin',
          name: 'Weather Service',
          version: '1.2.0',
          description: 'Provides current weather information for specified locations',
          author: { name: 'Kari AI Team' },
          license: 'MIT',
          keywords: ['weather', 'api', 'location'],
          category: 'integration',
          runtime: { platform: ['node'] },
          dependencies: [],
          systemRequirements: {},
          permissions: [
            {
              id: 'network-access',
              name: 'Network Access',
              description: 'Access to external weather APIs',
              category: 'network',
              level: 'read',
              required: true,
            },
          ],
          sandboxed: true,
          securityPolicy: {
            allowNetworkAccess: true,
            allowFileSystemAccess: false,
            allowSystemCalls: false,
            trustedDomains: ['api.openweathermap.org'],
          },
          configSchema: [
            {
              key: 'apiKey',
              type: 'password',
              label: 'API Key',
              description: 'OpenWeatherMap API key',
              required: true,
            },
            {
              key: 'units',
              type: 'select',
              label: 'Temperature Units',
              required: false,
              default: 'metric',
              options: [
                { label: 'Celsius', value: 'metric' },
                { label: 'Fahrenheit', value: 'imperial' },
                { label: 'Kelvin', value: 'standard' },
              ],
            },
          ],
          apiVersion: '1.0',
        },
        config: {
          apiKey: '***hidden***',
          units: 'metric',
        },
        permissions: [
          {
            id: 'network-access',
            name: 'Network Access',
            description: 'Access to external weather APIs',
            category: 'network',
            level: 'read',
            required: true,
          },
        ],
        metrics: {
          performance: {
            averageExecutionTime: 250,
            totalExecutions: 1247,
            errorRate: 0.02,
            lastExecution: new Date(),
          },
          resources: {
            memoryUsage: 15.2,
            cpuUsage: 0.5,
            diskUsage: 2.1,
            networkUsage: 0.8,
          },
          health: {
            status: 'healthy',
            uptime: 99.8,
            lastHealthCheck: new Date(),
            issues: [],
          },
        },
        dependencyStatus: {
          satisfied: true,
          missing: [],
          conflicts: [],
        },
      },
      {
        id: 'gmail-plugin',
        name: 'Gmail Integration',
        version: '2.1.0',
        status: 'inactive',
        enabled: false,
        autoStart: false,
        restartCount: 2,
        installedAt: new Date('2024-01-10'),
        updatedAt: new Date('2024-01-25'),
        installedBy: 'admin',
        manifest: {
          id: 'gmail-plugin',
          name: 'Gmail Integration',
          version: '2.1.0',
          description: 'Read and compose Gmail messages through AI chat interface',
          author: { name: 'Kari AI Team' },
          license: 'MIT',
          keywords: ['gmail', 'email', 'google'],
          category: 'integration',
          runtime: { platform: ['node'] },
          dependencies: [],
          systemRequirements: {},
          permissions: [
            {
              id: 'gmail-read',
              name: 'Gmail Read Access',
              description: 'Read Gmail messages and metadata',
              category: 'data',
              level: 'read',
              required: true,
            },
            {
              id: 'gmail-compose',
              name: 'Gmail Compose Access',
              description: 'Send emails through Gmail',
              category: 'data',
              level: 'write',
              required: false,
            },
          ],
          sandboxed: true,
          securityPolicy: {
            allowNetworkAccess: true,
            allowFileSystemAccess: false,
            allowSystemCalls: false,
            trustedDomains: ['gmail.googleapis.com'],
          },
          configSchema: [
            {
              key: 'clientId',
              type: 'string',
              label: 'Google Client ID',
              required: true,
            },
            {
              key: 'clientSecret',
              type: 'password',
              label: 'Google Client Secret',
              required: true,
            },
            {
              key: 'maxResults',
              type: 'number',
              label: 'Max Results per Query',
              required: false,
              default: 10,
              validation: { min: 1, max: 100 },
            },
          ],
          apiVersion: '1.0',
        },
        config: {
          clientId: 'your-client-id',
          clientSecret: '***hidden***',
          maxResults: 10,
        },
        permissions: [
          {
            id: 'gmail-read',
            name: 'Gmail Read Access',
            description: 'Read Gmail messages and metadata',
            category: 'data',
            level: 'read',
            required: true,
          },
        ],
        metrics: {
          performance: {
            averageExecutionTime: 1200,
            totalExecutions: 45,
            errorRate: 0.15,
            lastExecution: new Date(Date.now() - 86400000),
          },
          resources: {
            memoryUsage: 8.5,
            cpuUsage: 0.2,
            diskUsage: 1.2,
            networkUsage: 0.3,
          },
          health: {
            status: 'warning',
            uptime: 85.2,
            lastHealthCheck: new Date(),
            issues: ['Authentication token expired', 'Rate limit approaching'],
          },
        },
        dependencyStatus: {
          satisfied: true,
          missing: [],
          conflicts: [],
        },
        lastError: {
          message: 'Authentication failed: Token expired',
          timestamp: new Date(Date.now() - 3600000),
        },
      },
    ];
  }

  async installPlugin(request: PluginInstallationRequest): Promise<string> {
    void request; // placeholder usage
    const installationId = `install-${Date.now()}`;
    return installationId;
  }

  async uninstallPlugin(id: string): Promise<void> {
    void id;
    await new Promise((r) => setTimeout(r, 300));
  }

  async enablePlugin(id: string): Promise<void> {
    void id;
    await new Promise((r) => setTimeout(r, 200));
  }

  async disablePlugin(id: string): Promise<void> {
    void id;
    await new Promise((r) => setTimeout(r, 200));
  }

  async configurePlugin(id: string, config: PluginConfig): Promise<void> {
    void id;
    void config;
    await new Promise((r) => setTimeout(r, 250));
  }

  async searchMarketplace(query?: string): Promise<PluginMarketplaceEntry[]> {
    void query;
    return [
      {
        id: 'slack-integration',
        name: 'Slack Integration',
        description: 'Connect with Slack workspaces and manage messages',
        version: '1.0.0',
        author: { name: 'Community Developer', verified: false },
        category: 'integration',
        tags: ['slack', 'messaging', 'team'],
        downloads: 1250,
        rating: 4.5,
        reviewCount: 23,
        featured: false,
        verified: false,
        compatibility: {
          minVersion: '1.0.0',
          platforms: ['node'],
        },
        screenshots: [],
        pricing: { type: 'free' },
        installUrl: 'https://marketplace.kari.ai/plugins/slack-integration',
        manifest: {
          id: 'slack-integration',
          name: 'Slack Integration',
          version: '1.0.0',
          description: 'Connect with Slack workspaces and manage messages',
          author: { name: 'Community Developer' },
          license: 'MIT',
          keywords: ['slack', 'messaging'],
          category: 'integration',
          runtime: { platform: ['node'] },
          dependencies: [],
          systemRequirements: {},
          permissions: [],
          sandboxed: true,
          securityPolicy: {
            allowNetworkAccess: true,
            allowFileSystemAccess: false,
            allowSystemCalls: false,
          },
          configSchema: [],
          apiVersion: '1.0',
        },
      },
    ];
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

          await get().loadPlugins();

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
          state.sortBy = sortBy as any;
          state.sortOrder = sortOrder;
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
    let aValue: any;
    let bValue: any;

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

    if (aValue < bValue) return state.sortOrder === 'asc' ? -1 : 1;
    if (aValue > bValue) return state.sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  return sorted;
};
