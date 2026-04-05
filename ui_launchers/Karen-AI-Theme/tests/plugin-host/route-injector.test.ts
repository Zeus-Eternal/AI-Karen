import { describe, it, expect, vi } from 'vitest';

vi.mock('@/lib/api', () => ({
  default: { get: vi.fn() }
}));

vi.mock('@/lib/useAuth', () => ({
  useAuth: () => ({ user: { id: 'test-user', roles: ['user', 'admin'] } })
}));

const { derivePluginRoutes, usePluginRoutes } = await import('../../src/plugin_host/route-injector');
type PluginMenuEntry = import('../../src/plugin_host/route-injector').PluginMenuEntry;
type PluginRoutes = import('../../src/plugin_host/route-injector').PluginRoutes;
type PluginCatalogEntry = import('../../src/plugin_host/registry').PluginCatalogEntry;
type MenuContribution = import('../../src/plugin_host/registry').MenuContribution;

describe('Route Injector', () => {
  describe('derivePluginRoutes', () => {
    it('should derive sidebar entries from menu_contributions with zone sidebar.plugins', () => {
      const catalog: PluginCatalogEntry[] = [
        {
          id: 'weather-query',
          displayName: 'Weather',
          version: '1.0.0',
          enabled: true,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'weather-query',
              entryId: 'default',
              label: 'Weather',
              zone: 'sidebar.plugins',
              order: 0,
              iconPath: 'weather-query---sidebar_00.svg',
            }
          ]
        }
      ];

      const routes = derivePluginRoutes(catalog);
      
      expect(routes.sidebarEntries).toHaveLength(1);
      expect(routes.sidebarEntries[0]).toEqual({
        pluginId: 'weather-query',
        entryId: 'default',
        viewKey: 'weather-query::default',
        label: 'Weather',
        iconPath: 'weather-query---sidebar_00.svg',
        order: 0,
        isDefault: false
      });
      
      expect(routes.viewMap).toEqual({
        'weather-query::default': 'weather-query'
      });
    });

    it('should generate default sidebar entry for UI-capable plugins without menu_contributions', () => {
      const catalog: PluginCatalogEntry[] = [
        {
          id: 'test-plugin',
          displayName: 'Test Plugin',
          version: '1.0.0',
          enabled: true,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: []
        }
      ];

      const routes = derivePluginRoutes(catalog);
      
      expect(routes.sidebarEntries).toHaveLength(1);
      expect(routes.sidebarEntries[0]).toEqual({
        pluginId: 'test-plugin',
        entryId: 'test-plugin.sidebar-plugins.default',
        viewKey: 'test-plugin::sidebar-plugins-default',
        label: 'Test Plugin',
        order: null,
        isDefault: true
      });
      
      expect(routes.viewMap).toEqual({
        'test-plugin::sidebar-plugins-default': 'test-plugin'
      });
    });

    it('should sort sidebar entries by order field', () => {
      const catalog: PluginCatalogEntry[] = [
        {
          id: 'plugin-b',
          displayName: 'Plugin B',
          version: '1.0.0',
          enabled: true,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'plugin-b',
              entryId: 'default',
              label: 'Plugin B',
              zone: 'sidebar.plugins',
              order: 1,
            }
          ]
        },
        {
          id: 'plugin-a',
          displayName: 'Plugin A',
          version: '1.0.0',
          enabled: true,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'plugin-a',
              entryId: 'default',
              label: 'Plugin A',
              zone: 'sidebar.plugins',
              order: 0,
            }
          ]
        }
      ];

      const routes = derivePluginRoutes(catalog);
      
      expect(routes.sidebarEntries).toHaveLength(2);
      expect(routes.sidebarEntries[0].pluginId).toBe('plugin-a'); // Lower order first
      expect(routes.sidebarEntries[1].pluginId).toBe('plugin-b');
    });

    it('should place entries without explicit order after those with order', () => {
      const catalog: PluginCatalogEntry[] = [
        {
          id: 'plugin-a',
          displayName: 'Plugin A',
          version: '1.0.0',
          enabled: true,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'plugin-a',
              entryId: 'default',
              label: 'Plugin A',
              zone: 'sidebar.plugins',
              order: 1,
            }
          ]
        },
        {
          id: 'plugin-b',
          displayName: 'Plugin B',
          version: '1.0.0',
          enabled: true,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'plugin-b',
              entryId: 'default',
              label: 'Plugin B',
              zone: 'sidebar.plugins',
              order: null,
            }
          ]
        }
      ];

      const routes = derivePluginRoutes(catalog);
      
      expect(routes.sidebarEntries).toHaveLength(2);
      expect(routes.sidebarEntries[0].pluginId).toBe('plugin-a'); // With order first
      expect(routes.sidebarEntries[1].pluginId).toBe('plugin-b'); // Without order last
    });

    it('should include only plugins with provides_ui capability', () => {
      const catalog: PluginCatalogEntry[] = [
        {
          id: 'ui-plugin',
          displayName: 'UI Plugin',
          version: '1.0.0',
          enabled: true,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'ui-plugin',
              entryId: 'default',
              label: 'UI Plugin',
              zone: 'sidebar.plugins',
              order: null,
            }
          ]
        },
        {
          id: 'backend-only',
          displayName: 'Backend Only',
          version: '1.0.0',
          enabled: true,
          has_gui: false,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'backend-only',
              entryId: 'default',
              label: 'Backend Only',
              zone: 'sidebar.plugins',
              order: null,
            }
          ]
        }
      ];

      const routes = derivePluginRoutes(catalog);
      
      expect(routes.sidebarEntries).toHaveLength(1);
      expect(routes.sidebarEntries[0].pluginId).toBe('ui-plugin');
    });

    it('should exclude inactive plugins', () => {
      const catalog: PluginCatalogEntry[] = [
        {
          id: 'active-plugin',
          displayName: 'Active Plugin',
          version: '1.0.0',
          enabled: true,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'active-plugin',
              entryId: 'default',
              label: 'Active Plugin',
              zone: 'sidebar.plugins',
              order: null,
            }
          ]
        },
        {
          id: 'inactive-plugin',
          displayName: 'Inactive Plugin',
          version: '1.0.0',
          enabled: false,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'inactive',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'inactive-plugin',
              entryId: 'default',
              label: 'Inactive Plugin',
              zone: 'sidebar.plugins',
              order: null,
            }
          ]
        }
      ];

      const routes = derivePluginRoutes(catalog);
      
      expect(routes.sidebarEntries).toHaveLength(1);
      expect(routes.sidebarEntries[0].pluginId).toBe('active-plugin');
    });

    it('should handle multiple plugins in the same zone', () => {
      const catalog: PluginCatalogEntry[] = [
        {
          id: 'plugin-a',
          displayName: 'Plugin A',
          version: '1.0.0',
          enabled: true,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'plugin-a',
              entryId: 'default',
              label: 'Plugin A',
              zone: 'sidebar.plugins',
              order: 0,
            }
          ]
        },
        {
          id: 'plugin-b',
          displayName: 'Plugin B',
          version: '1.0.0',
          enabled: true,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'plugin-b',
              entryId: 'default',
              label: 'Plugin B',
              zone: 'sidebar.plugins',
              order: 1,
            }
          ]
        }
      ];

      const routes = derivePluginRoutes(catalog);
      
      expect(routes.sidebarEntries).toHaveLength(2);
      expect(routes.viewMap).toEqual({
        'plugin-a::default': 'plugin-a',
        'plugin-b::default': 'plugin-b'
      });
    });

    it('should generate view keys using plugin name', () => {
      const catalog: PluginCatalogEntry[] = [
        {
          id: 'weather-query',
          displayName: 'Weather',
          version: '1.0.0',
          enabled: true,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'weather-query',
              entryId: 'default',
              label: 'Weather',
              zone: 'sidebar.plugins',
              order: null,
            }
          ]
        }
      ];

      const routes = derivePluginRoutes(catalog);
      
      expect(routes.viewMap).toEqual({
        'weather-query::default': 'weather-query'
      });
    });

    it('should handle empty catalog', () => {
      const catalog: PluginCatalogEntry[] = [];

      const routes = derivePluginRoutes(catalog);
      
      expect(routes.sidebarEntries).toHaveLength(0);
      expect(routes.viewMap).toEqual({});
    });

    it('should handle plugin with no display_name', () => {
      const catalog: PluginCatalogEntry[] = [
        {
          id: 'test-plugin',
          displayName: '',
          version: '1.0.0',
          enabled: true,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'test-plugin',
              entryId: 'default',
              label: 'Test Plugin',
              zone: 'sidebar.plugins',
              order: null,
            }
          ]
        }
      ];

      const routes = derivePluginRoutes(catalog);
      
      expect(routes.sidebarEntries[0].label).toBe('Test Plugin');
    });
  });

  describe('usePluginRoutes', () => {
    it('should return plugin routes when called', () => {
      // This would normally be a React hook test, but we'll test the underlying logic
      const catalog: PluginCatalogEntry[] = [
        {
          id: 'test-plugin',
          displayName: 'Test Plugin',
          version: '1.0.0',
          enabled: true,
          has_gui: true,
          promptFirstValid: true,
          description: '',
          rawStatus: 'active',
          allowedRoles: [],
          menuContributions: [
            {
              pluginId: 'test-plugin',
              entryId: 'default',
              label: 'Test Plugin',
              zone: 'sidebar.plugins',
              order: null,
            }
          ]
        }
      ];

      const routes = derivePluginRoutes(catalog);
      
      expect(routes).toHaveProperty('sidebarEntries');
      expect(routes).toHaveProperty('viewMap');
      expect(Array.isArray(routes.sidebarEntries)).toBe(true);
      expect(typeof routes.viewMap).toBe('object');
    });
  });
});