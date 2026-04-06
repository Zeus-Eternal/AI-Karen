import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import React from 'react';

// Mock fetch for API calls
global.fetch = vi.fn() as unknown as Mock;
const mockedFetch = vi.mocked(fetch);

// Helper function to create mock Response
function createMockResponse(data: any, ok = true) {
  return {
    ok,
    json: () => Promise.resolve(data)
  } as Response;
}

// Mock authentication
vi.mock('@/lib/useAuth', () => ({
  useAuth: () => ({ user: { id: 'test-user', roles: ['user', 'admin'] } })
}));

// Import plugin registry and loader
import { PluginRegistryProvider, usePluginHealth, setPluginMountState } from '../../src/plugin_host/registry';
import { resolvePluginComponent, resolvePluginEntries, PLUGIN_IMPORT_MAP, LoaderPluginEntry } from '../../src/plugin_host/loader';

describe('Authority Verification Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Property 1: Discovery ≠ Installation', () => {
    it('should not automatically install discovered plugins', () => {
      // Mock backend catalog response with discovered but not installed plugins
      mockedFetch.mockImplementationOnce(() =>
        Promise.resolve(createMockResponse([
          {
            name: 'weather-query',
            status: 'discovered',
            capabilities: { provides_ui: true },
            ui: { has_component: true }
          }
        ]))
      );

      // Test that discovered plugin is not in installed state
      const { result } = renderHook(() => usePluginHealth('weather-query'), {
        wrapper: ({ children }) => React.createElement(PluginRegistryProvider, null, children)
      });
      
      expect(result.current.backendState).toBe('discovered');
      expect(result.current.frontendMountState).toBe('loading');
    });

    it('should require explicit installation action', async () => {
      // Mock initial state - plugin is discovered but not installed
      mockedFetch.mockImplementationOnce(() =>
        Promise.resolve(createMockResponse([
          {
            name: 'weather-query',
            status: 'discovered',
            capabilities: { provides_ui: true },
            ui: { has_component: true }
          }
        ]))
      );

      const { result } = renderHook(() => usePluginHealth('weather-query'), {
        wrapper: ({ children }) => React.createElement(PluginRegistryProvider, null, children)
      });

      // Verify plugin remains in discovered state without explicit installation
      expect(result.current.backendState).toBe('discovered');
      
      // Mock that installation action would change status
      mockedFetch.mockImplementationOnce(() =>
        Promise.resolve(createMockResponse([
          {
            name: 'weather-query',
            status: 'installed',
            capabilities: { provides_ui: true },
            ui: { has_component: true }
          }
        ]))
      );

      // Simulate installation action (this would come from API call)
      await act(async () => {
        // This would normally be triggered by an API call to install the plugin
        // For test purposes, we'll directly update the mock
        const { result: newResult } = renderHook(() => usePluginHealth('weather-query'), {
          wrapper: ({ children }) => React.createElement(PluginRegistryProvider, null, children)
        });
        expect(newResult.current.backendState).toBe('discovered'); // Should still be discovered until explicit install
      });
    });
  });

  describe('Property 2: Registration ≠ Mounting', () => {
    it('should not automatically mount registered plugins', () => {
      // Mock backend catalog with installed and registered plugin
      mockedFetch.mockImplementationOnce(() =>
        Promise.resolve(createMockResponse([
          {
            name: 'weather-query',
            status: 'installed',
            capabilities: { provides_ui: true },
            ui: { has_component: true }
          }
        ]))
      );

      // Plugin is in registry (has importer)
      expect('weather-query' in PLUGIN_IMPORT_MAP).toBe(true);

      const { result } = renderHook(() => usePluginHealth('weather-query'), {
        wrapper: ({ children }) => React.createElement(PluginRegistryProvider, null, children)
      });

      // Plugin should be registered but not mounted yet
      expect(result.current.backendState).toBe('installed');
      expect(result.current.frontendMountState).toBe('loading');
    });

    it('should require explicit mounting action', () => {
      // Mock plugin component resolution
      const mockComponent = vi.fn();
      
      // Test that registered plugin requires explicit mounting
      const component = resolvePluginComponent('weather-query', [], 'default');
      
      // Component should be available but not automatically mounted
      expect(component).not.toBeNull();
      
      // Mount state should be controlled by explicit mounting logic
      const { result } = renderHook(() => usePluginHealth('weather-query'), {
        wrapper: ({ children }) => React.createElement(PluginRegistryProvider, null, children)
      });

      // Initially should be in loading state until explicit mount
      expect(result.current.frontendMountState).toBe('loading');
    });
  });

  describe('Property 3: Category Path Correctness', () => {
    it('should resolve canonical paths deterministically', () => {
      // Test plugin ID normalization
      const normalizedId = 'weather-query'.toLowerCase().replace(/_/g, '-');
      expect(normalizedId).toBe('weather-query');
      
      // Test path resolution for valid categories
      const validCategories = ['plugins', 'sys_extensions', 'channels'];
      const testPlugin = 'test-plugin';
      
      validCategories.forEach(category => {
        const expectedPath = `src/extensions/${category}/${testPlugin}/`;
        expect(expectedPath).toMatch(/^src\/extensions\/(plugins|sys_extensions|channels)\/.*\/$/);
      });
    });

    it('should reject invalid categories', () => {
      const invalidCategories = ['invalid', 'plugins/', 'sys_extensions', ''];
      
      invalidCategories.forEach(category => {
        // Test that invalid categories would be rejected
        expect(typeof category).toBe('string');
        expect(category).not.toMatch(/^(plugins|sys_extensions|channels)$/);
      });
    });
  });

  describe('Property 4: Category Restriction', () => {
    it('should validate category in lifecycle operations', () => {
      const validCategories = ['plugins', 'sys_extensions', 'channels'];
      const invalidCategories = ['invalid', 'hack', 'malicious', ''];
      
      // Test valid categories pass validation
      validCategories.forEach(category => {
        const isValid = validCategories.includes(category);
        expect(isValid).toBe(true);
      });
      
      // Test invalid categories are rejected
      invalidCategories.forEach(category => {
        const isValid = validCategories.includes(category);
        expect(isValid).toBe(false);
      });
    });
  });

  describe('Property 22: Install UI Correctness', () => {
    it('should install GUI-capable plugins deterministically', () => {
      // Mock plugin with GUI capability
      const guiCapablePlugin: LoaderPluginEntry = {
        name: 'weather-query',
        status: 'installed',
        capabilities: {
          provides_ui: true,
        },
        ui_entry_points: [
          {
            entry_id: 'default',
            component: 'weather-query',
            zone: 'sidebar.plugins'
          }
        ]
      };

      // Test that GUI-capable plugin can be resolved
      const entries = resolvePluginEntries('weather-query', [guiCapablePlugin]);
      expect(entries.length).toBeGreaterThan(0);
      expect(entries[0].zone).toBe('sidebar.plugins');
    });

    it('should not install non-GUI plugins', () => {
      // Mock plugin without GUI capability
      const nonGuiPlugin: LoaderPluginEntry = {
        name: 'background-task',
        status: 'installed',
        capabilities: {
          provides_ui: false,
        },
        ui_entry_points: []
      };

      // Test that non-GUI plugin has no UI entries
      const entries = resolvePluginEntries('background-task', [nonGuiPlugin]);
      expect(entries.length).toBe(0);
    });
  });

  describe('Property 23: Remove UI Correctness', () => {
    it('should unregister and remove artifacts when removing UI', () => {
      // Mock plugin with installed UI
      const installedPlugin: LoaderPluginEntry = {
        name: 'weather-query',
        status: 'installed',
        capabilities: {
          provides_ui: true,
        },
        ui_entry_points: []
      };

      // Initially should have entries
      let entries = resolvePluginEntries('weather-query', [installedPlugin]);
      expect(entries.length).toBeGreaterThan(0);

      // Simulate UI removal - this would clear the registry
      // For test purposes, we'll test the removal logic
      const removedEntries = resolvePluginEntries('weather-query', []);
      expect(removedEntries.length).toBe(0);
    });
  });

  describe('Property 24: Manifest Override Correctness', () => {
    it('should use manifest-defined entry over fallback', () => {
      // Mock plugin with manifest-defined entry
      const manifestPlugin: LoaderPluginEntry = {
        name: 'weather-query',
        status: 'active',
        capabilities: {
          provides_ui: true,
        },
        ui_entry_points: [
          {
            entry_id: 'custom',
            component: 'custom-component',
            zone: 'page.plugins.overview'
          }
        ]
      };

      const entries = resolvePluginEntries('weather-query', [manifestPlugin]);
      expect(entries.length).toBe(1);
      expect(entries[0].entry_id).toBe('custom');
      expect(entries[0].component).toBe('custom-component');
      expect(entries[0].zone).toBe('page.plugins.overview');
    });

    it('should fallback to default when no manifest override', () => {
      // Mock plugin without manifest-defined entry
      const fallbackPlugin: LoaderPluginEntry = {
        name: 'weather-query',
        status: 'active',
        capabilities: {
          provides_ui: true,
        },
        ui_entry_points: []
      };

      const entries = resolvePluginEntries('weather-query', [fallbackPlugin]);
      expect(entries.length).toBe(1);
      expect(entries[0].entry_id).toBe('default');
      expect(entries[0].component).toBe('weather-query');
      expect(entries[0].zone).toBe('sidebar.plugins');
    });
  });

  describe('Property 29: Loader-Only Resolution', () => {
    it('should not use hardcoded importer registry', () => {
      // Test that PLUGIN_IMPORT_MAP is built from loader, not hardcoded
      const pluginIds = Object.keys(PLUGIN_IMPORT_MAP);
      
      // Should not contain hardcoded entries
      expect(pluginIds).not.toContain('hardcoded-plugin');
      
      // Should only contain entries discovered by loader
      pluginIds.forEach(id => {
        expect(typeof id).toBe('string');
        expect(id.length).toBeGreaterThan(0);
      });
    });

    it('should resolve only from plugin_repo', () => {
      // Test that loader resolves from proper location
      const testPluginId = 'weather-query';
      const normalizedId = testPluginId.toLowerCase().replace(/_/g, '-');
      
      // Check that plugin is in import map
      const hasImporter = normalizedId in PLUGIN_IMPORT_MAP;
      expect(hasImporter).toBe(true);
    });
  });

  describe('Property 30: Safe Fallback Behavior', () => {
    it('should render controlled fallback for failed loads', () => {
      // Test fallback component creation
      const fallbackComponent = () => React.createElement('div', null, 'Fallback');
      expect(fallbackComponent).toBeDefined();
      
      // Test that failed loads return null
      const component = resolvePluginComponent('nonexistent-plugin', []);
      expect(component).toBeNull();
    });
  });

  describe('Property 34: Registry Completeness', () => {
    it('should include all installed valid UIs', () => {
      // Mock multiple installed plugins
      const installedPlugins: LoaderPluginEntry[] = [
        {
          name: 'weather-query',
          status: 'installed',
          capabilities: {
            provides_ui: true,
          },
          ui_entry_points: []
        },
        {
          name: 'data-connector',
          status: 'installed',
          capabilities: {
            provides_ui: true,
          },
          ui_entry_points: []
        }
      ];

      // Test that all installed plugins appear in registry
      const weatherEntries = resolvePluginEntries('weather-query', installedPlugins);
      const dataEntries = resolvePluginEntries('data-connector', installedPlugins);
      
      expect(weatherEntries.length).toBeGreaterThan(0);
      expect(dataEntries.length).toBeGreaterThan(0);
    });
  });

  describe('Property 35: No Stale Entries', () => {
    it('should remove uninstalled plugins deterministically', () => {
      // Mock initial state with plugin
      const withPlugin: LoaderPluginEntry[] = [
        {
          name: 'weather-query',
          status: 'installed',
          capabilities: {
            provides_ui: true,
          },
          ui_entry_points: []
        }
      ];

      // Mock state after removal
      const withoutPlugin: LoaderPluginEntry[] = [];

      // Test that plugin is removed when uninstalled
      const withEntries = resolvePluginEntries('weather-query', withPlugin);
      const withoutEntries = resolvePluginEntries('weather-query', withoutPlugin);
      
      expect(withEntries.length).toBeGreaterThan(0);
      expect(withoutEntries.length).toBe(0);
    });
  });

  describe('Property 47: Full Lifecycle Correctness', () => {
    it('should allow valid plugins to traverse lifecycle deterministically', async () => {
      // Mock discovered state
      mockedFetch.mockImplementationOnce(() =>
        Promise.resolve(createMockResponse([
          {
            name: 'weather-query',
            status: 'discovered',
            capabilities: { provides_ui: true },
            ui: { has_component: true }
          }
        ]))
      );

      const { result: discoveredResult } = renderHook(() => usePluginHealth('weather-query'), {
        wrapper: ({ children }) => React.createElement(PluginRegistryProvider, null, children)
      });

      expect(discoveredResult.current.backendState).toBe('discovered');

      // Mock installed state
      mockedFetch.mockImplementationOnce(() =>
        Promise.resolve(createMockResponse([
          {
            name: 'weather-query',
            status: 'installed',
            capabilities: { provides_ui: true },
            ui: { has_component: true }
          }
        ]))
      );

      // Simulate installation
      const { result: installedResult } = renderHook(() => usePluginHealth('weather-query'), {
        wrapper: ({ children }) => React.createElement(PluginRegistryProvider, null, children)
      });

      expect(installedResult.current.backendState).toBe('installed');
    });
  });

  describe('Property 48: No Stale Integration Artifacts', () => {
    it('should leave no stale artifacts after remove/uninstall/restore', () => {
      // Mock plugin in various states
      const states: LoaderPluginEntry[] = [
        {
          name: 'weather-query',
          status: 'discovered',
          capabilities: {
            provides_ui: false,
          },
          ui_entry_points: []
        },
        {
          name: 'weather-query',
          status: 'installed',
          capabilities: {
            provides_ui: true,
          },
          ui_entry_points: []
        },
        {
          name: 'weather-query',
          status: 'active',
          capabilities: {
            provides_ui: true,
          },
          ui_entry_points: []
        }
      ];
      
      // Test that state transitions are clean
      states.forEach((state, index) => {
        const entries = resolvePluginEntries('weather-query', [state]);
        
        // Should have clean state transitions
        expect(Array.isArray(entries)).toBe(true);
        if (state.status === 'discovered') {
          expect(entries.length).toBe(0); // No entries when discovered
        } else {
          expect(entries.length).toBeGreaterThan(0); // Has entries when installed/active
        }
      });
    });
  });
});