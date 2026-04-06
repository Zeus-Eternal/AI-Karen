import { vi, describe, it, expect } from 'vitest';
import { resolvePluginComponent, PLUGIN_IMPORT_MAP, type LoaderPluginEntry } from '../../src/plugin_host/loader';
import { derivePluginRoutes } from '../../src/plugin_host/route-injector';
import { validateRawManifest } from '../../src/plugin_host/manifest-validator';
import React from 'react';

// Block-hoist the mock for require.context
vi.hoisted(() => {
  if (typeof (globalThis as any).require === 'undefined') {
    (globalThis as any).require = {};
  }
  (globalThis as any).require.context = vi.fn(() => ({
    keys: () => [] as string[],
    resolve: (k: string) => k,
    id: 'mock'
  }));
});

// Mock React.lazy
vi.mock('react', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react')>();
  return {
    ...actual,
    lazy: vi.fn((importer: any) => {
      const LazyComp = (props: any) => actual.createElement('div', { 'data-testid': 'lazy-comp' }, 'Lazy Component');
      (LazyComp as any).$$typeof = Symbol.for('react.lazy');
      return LazyComp;
    }),
  };
});

const rawManifest = {
  plugin_id: 'weather-query',
  component: 'WeatherPluginPage',
  slots: ['sidebar.plugins'],
  permissions: [],
  display_name: 'Weather',
  icon: 'weather-query---sidebar_00.svg',
  order: 0,
  label: 'Weather'
};

const catalogEntry: any = {
  id: 'weather-query',
  displayName: 'Weather',
  enabled: true,
  has_gui: true,
  promptFirstValid: true,
  rawStatus: 'active',
  menuContributions: [
    {
      pluginId: 'weather-query',
      entryId: 'default',
      label: 'Weather',
      zone: 'sidebar.plugins',
      order: 0,
      iconPath: 'weather-query---sidebar_00.svg'
    }
  ]
};

const mockLoaderCatalog: LoaderPluginEntry[] = [
  { name: 'weather-query', status: 'active', capabilities: { provides_ui: true } }
];

describe('Weather Plugin Integration', () => {
  it('should support weather plugin workflow', () => {
    // 1. Route derivation
    const routes = derivePluginRoutes([catalogEntry]);
    expect(routes.sidebarEntries).toHaveLength(1);
    expect(routes.sidebarEntries[0].pluginId).toBe('weather-query');

    // 2. Component resolution
    // Manually populate import map for the test
    (PLUGIN_IMPORT_MAP as any)['weather-query'] = vi.fn().mockResolvedValue({ default: () => null });
    
    const component = resolvePluginComponent('weather-query', mockLoaderCatalog);
    expect(component).toBeTruthy();

    // 3. Manifest validation
    const validation = validateRawManifest(rawManifest as any, 'weather-query');
    expect(validation.valid).toBe(true);
  });
});
