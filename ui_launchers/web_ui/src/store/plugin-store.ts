/**
 * Plugin Store
 * 
 * Zustand store for plugin management state and operations.
 * Based on requirements: 5.1, 5.2, 5.3, 5.4, 5.5
 */

import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { subscribeWithSelector } from 'zustand/middleware';
import {
  PluginInfo,
  PluginInstallationRequest,
  PluginInstallationProgress,
  PluginMarketplaceEntry,
  PluginFilter,
  PluginConfig,
  PluginStore,
  PluginStoreState,
  PluginStoreActions,
} from '@/types/plugins';

// Mock API service (will be replaced with actual API integration)
class PluginAPIService {
  async listPlugins(): Promise<PluginInfo[]> {
    // Mock data for development
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
            lastExecution: new Date(Date.now() - 86400000), // 1 day ago
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
          timestamp: new Date(Date.now() - 3600000), // 1 hour ago
        },
      },
    ];
  }

  async installPlugin(request: PluginInstallationRequest): Promise<string> {
    const installationId = `install-${Date.now()}`;
    // Mock installation process
    return installationId;
  }

  async uninstallPlugin(id: string): Promise<void> {
    // Mock uninstallation
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  async enablePlugin(id: string): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  async disablePlugin(id: string): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  async configurePlugin(id: string, config: PluginConfig): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, 800));
  }

  async searchMarketplace(query?: string): Promise<PluginMarketplaceEntry[]> {
    // Mock marketplace data
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

// Initial state
const initialState: PluginStoreState = {
  plugins: [],
  selectedPlugin: null,
  installations: {},
  marketplacePlugins: [],
  
  loading: {
    plugins: false,
    installation: false,
    marketplace: false,
  },
  
  errors: {
    plugins: null,
    installation: null,
    marketplace: null,
  },
  
  searchQuery: '',
  filters: {},
  sortBy: 'name',
  sortOrder: 'asc',
  
  view: 'list',
  showInstallationWizard: false,
  showMarketplace: false,
};

// Create the plugin store
export const usePluginStore = create<PluginStore>()(
  subscribeWithSelector(
    immer((set, get) => ({
      ...initialState,
      
      // Plugin operations
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
            state.errors.plugins = error instanceof Error ? error.message : 'Failed to load plugins';
          });
        }
      },
      
      selectPlugin: (plugin: PluginInfo | null) => set((state) => {
        state.selectedPlugin = plugin;
      }),
      
      installPlugin: async (request: PluginInstallationRequest) => {
        set((state) => {
          state.loading.installation = true;
          state.errors.installation = null;
        });
        
        try {
          const installationId = await pluginAPI.installPlugin(request);
          
          // Mock installation progress
          set((state) => {
            state.installations[installationId] = {
              stage: 'downloading',
              progress: 0,
              message: 'Starting installation...',
            };
          });
          
          // Simulate installation progress
          const progressStages = [
            { stage: 'downloading' as const, progress: 20, message: 'Downloading plugin...' },
            { stage: 'validating' as const, progress: 40, message: 'Validating plugin manifest...' },
            { stage: 'resolving' as const, progress: 60, message: 'Resolving dependencies...' },
            { stage: 'installing' as const, progress: 80, message: 'Installing plugin...' },
            { stage: 'configuring' as const, progress: 90, message: 'Configuring plugin...' },
            { stage: 'complete' as const, progress: 100, message: 'Installation complete!' },
          ];
          
          for (const stage of progressStages) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            set((state) => {
              if (state.installations[installationId]) {
                state.installations[installationId] = {
                  ...state.installations[installationId],
                  ...stage,
                };
              }
            });
          }
          
          // Reload plugins after installation
          await get().loadPlugins();
          
          set((state) => {
            state.loading.installation = false;
            delete state.installations[installationId];
          });
          
          return installationId;
        } catch (error) {
          set((state) => {
            state.loading.installation = false;
            state.errors.installation = error instanceof Error ? error.message : 'Installation failed';
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
            state.plugins = state.plugins.filter(p => p.id !== id);
            if (state.selectedPlugin?.id === id) {
              state.selectedPlugin = null;
            }
            delete state.loading[`uninstall-${id}`];
          });
        } catch (error) {
          set((state) => {
            delete state.loading[`uninstall-${id}`];
            state.errors[`uninstall-${id}`] = error instanceof Error ? error.message : 'Uninstallation failed';
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
            const plugin = state.plugins.find(p => p.id === id);
            if (plugin) {
              plugin.enabled = true;
              plugin.status = 'active';
            }
            if (state.selectedPlugin?.id === id) {
              state.selectedPlugin.enabled = true;
              state.selectedPlugin.status = 'active';
            }
            delete state.loading[`enable-${id}`];
          });
        } catch (error) {
          set((state) => {
            delete state.loading[`enable-${id}`];
            state.errors[`enable-${id}`] = error instanceof Error ? error.message : 'Failed to enable plugin';
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
            const plugin = state.plugins.find(p => p.id === id);
            if (plugin) {
              plugin.enabled = false;
              plugin.status = 'inactive';
            }
            if (state.selectedPlugin?.id === id) {
              state.selectedPlugin.enabled = false;
              state.selectedPlugin.status = 'inactive';
            }
            delete state.loading[`disable-${id}`];
          });
        } catch (error) {
          set((state) => {
            delete state.loading[`disable-${id}`];
            state.errors[`disable-${id}`] = error instanceof Error ? error.message : 'Failed to disable plugin';
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
            const plugin = state.plugins.find(p => p.id === id);
            if (plugin) {
              plugin.config = { ...plugin.config, ...config };
            }
            if (state.selectedPlugin?.id === id) {
              state.selectedPlugin.config = { ...state.selectedPlugin.config, ...config };
            }
            delete state.loading[`configure-${id}`];
          });
        } catch (error) {
          set((state) => {
            delete state.loading[`configure-${id}`];
            state.errors[`configure-${id}`] = error instanceof Error ? error.message : 'Failed to configure plugin';
          });
          throw error;
        }
      },
      
      // Marketplace operations
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
            state.errors.marketplace = error instanceof Error ? error.message : 'Failed to load marketplace';
          });
        }
      },
      
      // UI operations
      setSearchQuery: (query: string) => set((state) => {
        state.searchQuery = query;
      }),
      
      setFilters: (filters: Partial<PluginFilter>) => set((state) => {
        state.filters = { ...state.filters, ...filters };
      }),
      
      setSorting: (sortBy: string, sortOrder: 'asc' | 'desc') => set((state) => {
        state.sortBy = sortBy as any;
        state.sortOrder = sortOrder;
      }),
      
      setView: (view: 'list' | 'grid' | 'details') => set((state) => {
        state.view = view;
      }),
      
      setShowInstallationWizard: (show: boolean) => set((state) => {
        state.showInstallationWizard = show;
      }),
      
      setShowMarketplace: (show: boolean) => set((state) => {
        state.showMarketplace = show;
      }),
      
      // Error handling
      setError: (key: string, error: string | null) => set((state) => {
        if (error) {
          state.errors[key] = error;
        } else {
          delete state.errors[key];
        }
      }),
      
      clearErrors: () => set((state) => {
        state.errors = {
          plugins: null,
          installation: null,
          marketplace: null,
        };
      }),
    }))
  )
);

// Selectors
export const selectPlugins = (state: PluginStore) => state.plugins;
export const selectSelectedPlugin = (state: PluginStore) => state.selectedPlugin;
export const selectPluginLoading = (key: string) => (state: PluginStore) => state.loading[key] || false;
export const selectPluginError = (key: string) => (state: PluginStore) => state.errors[key] || null;
export const selectMarketplacePlugins = (state: PluginStore) => state.marketplacePlugins;
export const selectInstallationProgress = (id: string) => (state: PluginStore) => state.installations[id];

// Filtered and sorted plugins selector
export const selectFilteredPlugins = (state: PluginStore) => {
  let filtered = state.plugins;
  
  // Apply search query
  if (state.searchQuery) {
    const query = state.searchQuery.toLowerCase();
    filtered = filtered.filter(plugin =>
      plugin.name.toLowerCase().includes(query) ||
      plugin.manifest.description.toLowerCase().includes(query) ||
      plugin.manifest.keywords.some(keyword => keyword.toLowerCase().includes(query))
    );
  }
  
  // Apply filters
  if (state.filters.status?.length) {
    filtered = filtered.filter(plugin => state.filters.status!.includes(plugin.status));
  }
  
  if (state.filters.category?.length) {
    filtered = filtered.filter(plugin => state.filters.category!.includes(plugin.manifest.category));
  }
  
  if (state.filters.enabled !== undefined) {
    filtered = filtered.filter(plugin => plugin.enabled === state.filters.enabled);
  }
  
  if (state.filters.hasErrors) {
    filtered = filtered.filter(plugin => !!plugin.lastError);
  }
  
  // Apply sorting
  filtered.sort((a, b) => {
    let aValue: any, bValue: any;
    
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
        aValue = a.installedAt.getTime();
        bValue = b.installedAt.getTime();
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
  
  return filtered;
};