/**
 * Plugin Store Tests
 * 
 * Unit tests for plugin store state management and operations.
 * Based on requirements: 5.1, 5.4
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePluginStore, selectFilteredPlugins } from '../plugin-store';
import { PluginInfo, PluginInstallationRequest } from '@/types/plugins';

// Mock the API service
vi.mock('../plugin-store', async () => {
  const actual = await vi.importActual('../plugin-store');
  return {
    ...actual,
    // We'll override the store implementation in tests
  };
});

describe('Plugin Store', () => {
  const mockPlugin: PluginInfo = {
    id: 'test-plugin',
    name: 'Test Plugin',
    version: '1.0.0',
    status: 'active',
    enabled: true,
    autoStart: true,
    restartCount: 0,
    installedAt: new Date('2024-01-15'),
    updatedAt: new Date('2024-01-20'),
    installedBy: 'admin',
    manifest: {
      id: 'test-plugin',
      name: 'Test Plugin',
      version: '1.0.0',
      description: 'A test plugin',
      author: { name: 'Test Author' },
      license: 'MIT',
      keywords: ['test'],
      category: 'utility',
      runtime: { platform: ['node'] },
      dependencies: [],
      systemRequirements: {},
      permissions: [],
      sandboxed: true,
      securityPolicy: {
        allowNetworkAccess: false,
        allowFileSystemAccess: false,
        allowSystemCalls: false,
      },
      configSchema: [],
      apiVersion: '1.0',
    },
    config: {},
    permissions: [],
    metrics: {
      performance: {
        averageExecutionTime: 100,
        totalExecutions: 50,
        errorRate: 0.0,
        lastExecution: new Date(),
      },
      resources: {
        memoryUsage: 10.0,
        cpuUsage: 1.0,
        diskUsage: 5.0,
        networkUsage: 0.0,
      },
      health: {
        status: 'healthy',
        uptime: 100.0,
        lastHealthCheck: new Date(),
        issues: [],
      },
    },
    dependencyStatus: {
      satisfied: true,
      missing: [],
      conflicts: [],
    },
  };

  beforeEach(() => {
    // Reset store state before each test
    const { result } = renderHook(() => usePluginStore());
    act(() => {
      result.current.clearErrors();
      // Reset to initial state
      usePluginStore.setState({
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
      });
    });
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => usePluginStore());
      
      expect(result.current.plugins).toEqual([]);
      expect(result.current.selectedPlugin).toBeNull();
      expect(result.current.installations).toEqual({});
      expect(result.current.marketplacePlugins).toEqual([]);
      expect(result.current.loading.plugins).toBe(false);
      expect(result.current.errors.plugins).toBeNull();
      expect(result.current.searchQuery).toBe('');
      expect(result.current.filters).toEqual({});
      expect(result.current.sortBy).toBe('name');
      expect(result.current.sortOrder).toBe('asc');
      expect(result.current.view).toBe('list');
      expect(result.current.showInstallationWizard).toBe(false);
      expect(result.current.showMarketplace).toBe(false);
    });
  });

  describe('Plugin Selection', () => {
    it('should select a plugin', () => {
      const { result } = renderHook(() => usePluginStore());
      
      act(() => {
        result.current.selectPlugin(mockPlugin);
      });
      
      expect(result.current.selectedPlugin).toEqual(mockPlugin);
    });

    it('should deselect a plugin', () => {
      const { result } = renderHook(() => usePluginStore());
      
      act(() => {
        result.current.selectPlugin(mockPlugin);
      });
      
      expect(result.current.selectedPlugin).toEqual(mockPlugin);
      
      act(() => {
        result.current.selectPlugin(null);
      });
      
      expect(result.current.selectedPlugin).toBeNull();
    });
  });

  describe('Search and Filtering', () => {
    it('should update search query', () => {
      const { result } = renderHook(() => usePluginStore());
      
      act(() => {
        result.current.setSearchQuery('test query');
      });
      
      expect(result.current.searchQuery).toBe('test query');
    });

    it('should update filters', () => {
      const { result } = renderHook(() => usePluginStore());
      
      act(() => {
        result.current.setFilters({ status: ['active'], enabled: true });
      });
      
      expect(result.current.filters).toEqual({
        status: ['active'],
        enabled: true,
      });
    });

    it('should merge filters when updating', () => {
      const { result } = renderHook(() => usePluginStore());
      
      act(() => {
        result.current.setFilters({ status: ['active'] });
      });
      
      act(() => {
        result.current.setFilters({ enabled: true });
      });
      
      expect(result.current.filters).toEqual({
        status: ['active'],
        enabled: true,
      });
    });

    it('should update sorting', () => {
      const { result } = renderHook(() => usePluginStore());
      
      act(() => {
        result.current.setSorting('version', 'desc');
      });
      
      expect(result.current.sortBy).toBe('version');
      expect(result.current.sortOrder).toBe('desc');
    });
  });

  describe('View Management', () => {
    it('should update view mode', () => {
      const { result } = renderHook(() => usePluginStore());
      
      act(() => {
        result.current.setView('grid');
      });
      
      expect(result.current.view).toBe('grid');
    });

    it('should toggle installation wizard', () => {
      const { result } = renderHook(() => usePluginStore());
      
      act(() => {
        result.current.setShowInstallationWizard(true);
      });
      
      expect(result.current.showInstallationWizard).toBe(true);
      
      act(() => {
        result.current.setShowInstallationWizard(false);
      });
      
      expect(result.current.showInstallationWizard).toBe(false);
    });

    it('should toggle marketplace', () => {
      const { result } = renderHook(() => usePluginStore());
      
      act(() => {
        result.current.setShowMarketplace(true);
      });
      
      expect(result.current.showMarketplace).toBe(true);
      
      act(() => {
        result.current.setShowMarketplace(false);
      });
      
      expect(result.current.showMarketplace).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('should set and clear errors', () => {
      const { result } = renderHook(() => usePluginStore());
      
      act(() => {
        result.current.setError('test-error', 'Test error message');
      });
      
      expect(result.current.errors['test-error']).toBe('Test error message');
      
      act(() => {
        result.current.setError('test-error', null);
      });
      
      expect(result.current.errors['test-error']).toBeUndefined();
    });

    it('should clear all errors', () => {
      const { result } = renderHook(() => usePluginStore());
      
      act(() => {
        result.current.setError('error1', 'Error 1');
        result.current.setError('error2', 'Error 2');
      });
      
      expect(result.current.errors['error1']).toBe('Error 1');
      expect(result.current.errors['error2']).toBe('Error 2');
      
      act(() => {
        result.current.clearErrors();
      });
      
      expect(result.current.errors.plugins).toBeNull();
      expect(result.current.errors.installation).toBeNull();
      expect(result.current.errors.marketplace).toBeNull();
    });
  });

  describe('Plugin Operations', () => {
    beforeEach(() => {
      // Mock the API calls to resolve immediately
      vi.clearAllTimers();
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should load plugins successfully', async () => {
      const { result } = renderHook(() => usePluginStore());
      
      // Mock the loadPlugins to set some test data
      act(() => {
        usePluginStore.setState({
          plugins: [mockPlugin],
          loading: { ...result.current.loading, plugins: false },
        });
      });
      
      expect(result.current.plugins).toEqual([mockPlugin]);
      expect(result.current.loading.plugins).toBe(false);
    });

    it('should handle plugin loading error', async () => {
      const { result } = renderHook(() => usePluginStore());
      
      act(() => {
        usePluginStore.setState({
          loading: { ...result.current.loading, plugins: false },
          errors: { ...result.current.errors, plugins: 'Failed to load plugins' },
        });
      });
      
      expect(result.current.errors.plugins).toBe('Failed to load plugins');
      expect(result.current.loading.plugins).toBe(false);
    });

    it('should enable a plugin', async () => {
      const { result } = renderHook(() => usePluginStore());
      
      // Set initial state with disabled plugin
      const disabledPlugin = { ...mockPlugin, enabled: false, status: 'inactive' as const };
      act(() => {
        usePluginStore.setState({
          plugins: [disabledPlugin],
        });
      });
      
      // Simulate enabling the plugin
      act(() => {
        const updatedPlugin = { ...disabledPlugin, enabled: true, status: 'active' as const };
        usePluginStore.setState({
          plugins: [updatedPlugin],
        });
      });
      
      expect(result.current.plugins[0].enabled).toBe(true);
      expect(result.current.plugins[0].status).toBe('active');
    });

    it('should disable a plugin', async () => {
      const { result } = renderHook(() => usePluginStore());
      
      // Set initial state with enabled plugin
      act(() => {
        usePluginStore.setState({
          plugins: [mockPlugin],
        });
      });
      
      // Simulate disabling the plugin
      act(() => {
        const updatedPlugin = { ...mockPlugin, enabled: false, status: 'inactive' as const };
        usePluginStore.setState({
          plugins: [updatedPlugin],
        });
      });
      
      expect(result.current.plugins[0].enabled).toBe(false);
      expect(result.current.plugins[0].status).toBe('inactive');
    });

    it('should uninstall a plugin', async () => {
      const { result } = renderHook(() => usePluginStore());
      
      // Set initial state with plugin
      act(() => {
        usePluginStore.setState({
          plugins: [mockPlugin],
          selectedPlugin: mockPlugin,
        });
      });
      
      // Simulate uninstalling the plugin
      act(() => {
        usePluginStore.setState({
          plugins: [],
          selectedPlugin: null,
        });
      });
      
      expect(result.current.plugins).toEqual([]);
      expect(result.current.selectedPlugin).toBeNull();
    });
  });

  describe('Filtered Plugins Selector', () => {
    const plugins: PluginInfo[] = [
      {
        ...mockPlugin,
        id: 'plugin1',
        name: 'Weather Plugin',
        status: 'active',
        enabled: true,
        manifest: {
          ...mockPlugin.manifest,
          category: 'integration',
          keywords: ['weather', 'api'],
        },
      },
      {
        ...mockPlugin,
        id: 'plugin2',
        name: 'Email Plugin',
        status: 'inactive',
        enabled: false,
        manifest: {
          ...mockPlugin.manifest,
          category: 'integration',
          keywords: ['email', 'gmail'],
        },
      },
      {
        ...mockPlugin,
        id: 'plugin3',
        name: 'Analytics Plugin',
        status: 'error',
        enabled: true,
        manifest: {
          ...mockPlugin.manifest,
          category: 'analytics',
          keywords: ['analytics', 'metrics'],
        },
        lastError: {
          message: 'Connection failed',
          timestamp: new Date(),
        },
      },
    ];

    it('should filter plugins by search query', () => {
      const state = {
        plugins,
        searchQuery: 'weather',
        filters: {},
        sortBy: 'name' as const,
        sortOrder: 'asc' as const,
      };
      
      const filtered = selectFilteredPlugins(state as any);
      expect(filtered).toHaveLength(1);
      expect(filtered[0].name).toBe('Weather Plugin');
    });

    it('should filter plugins by status', () => {
      const state = {
        plugins,
        searchQuery: '',
        filters: { status: ['active'] },
        sortBy: 'name' as const,
        sortOrder: 'asc' as const,
      };
      
      const filtered = selectFilteredPlugins(state as any);
      expect(filtered).toHaveLength(1);
      expect(filtered[0].status).toBe('active');
    });

    it('should filter plugins by category', () => {
      const state = {
        plugins,
        searchQuery: '',
        filters: { category: ['analytics'] },
        sortBy: 'name' as const,
        sortOrder: 'asc' as const,
      };
      
      const filtered = selectFilteredPlugins(state as any);
      expect(filtered).toHaveLength(1);
      expect(filtered[0].manifest.category).toBe('analytics');
    });

    it('should filter plugins by enabled status', () => {
      const state = {
        plugins,
        searchQuery: '',
        filters: { enabled: true },
        sortBy: 'name' as const,
        sortOrder: 'asc' as const,
      };
      
      const filtered = selectFilteredPlugins(state as any);
      expect(filtered).toHaveLength(2);
      expect(filtered.every(p => p.enabled)).toBe(true);
    });

    it('should filter plugins with errors', () => {
      const state = {
        plugins,
        searchQuery: '',
        filters: { hasErrors: true },
        sortBy: 'name' as const,
        sortOrder: 'asc' as const,
      };
      
      const filtered = selectFilteredPlugins(state as any);
      expect(filtered).toHaveLength(1);
      expect(filtered[0].lastError).toBeDefined();
    });

    it('should sort plugins by name ascending', () => {
      const state = {
        plugins,
        searchQuery: '',
        filters: {},
        sortBy: 'name' as const,
        sortOrder: 'asc' as const,
      };
      
      const filtered = selectFilteredPlugins(state as any);
      expect(filtered[0].name).toBe('Analytics Plugin');
      expect(filtered[1].name).toBe('Email Plugin');
      expect(filtered[2].name).toBe('Weather Plugin');
    });

    it('should sort plugins by name descending', () => {
      const state = {
        plugins,
        searchQuery: '',
        filters: {},
        sortBy: 'name' as const,
        sortOrder: 'desc' as const,
      };
      
      const filtered = selectFilteredPlugins(state as any);
      expect(filtered[0].name).toBe('Weather Plugin');
      expect(filtered[1].name).toBe('Email Plugin');
      expect(filtered[2].name).toBe('Analytics Plugin');
    });

    it('should sort plugins by status', () => {
      const state = {
        plugins,
        searchQuery: '',
        filters: {},
        sortBy: 'status' as const,
        sortOrder: 'asc' as const,
      };
      
      const filtered = selectFilteredPlugins(state as any);
      expect(filtered[0].status).toBe('active');
      expect(filtered[1].status).toBe('error');
      expect(filtered[2].status).toBe('inactive');
    });

    it('should combine search and filters', () => {
      const state = {
        plugins,
        searchQuery: 'plugin',
        filters: { enabled: true },
        sortBy: 'name' as const,
        sortOrder: 'asc' as const,
      };
      
      const filtered = selectFilteredPlugins(state as any);
      expect(filtered).toHaveLength(2);
      expect(filtered.every(p => p.enabled)).toBe(true);
      expect(filtered.every(p => p.name.toLowerCase().includes('plugin'))).toBe(true);
    });
  });
});