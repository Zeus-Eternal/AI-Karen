import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { resolvePluginComponent } from '../../src/plugin_host/loader';
import { derivePluginRoutes } from '../../src/plugin_host/route-injector';
import { validateRawManifest } from '../../src/plugin_host/manifest-validator';
import type { PluginCatalogEntry } from '../../src/plugin_host/registry';
import type { LoaderPluginEntry } from '../../src/plugin_host/loader';
import React from 'react';

// Mock React.lazy
vi.mock('react', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react')>();
  return {
    ...actual,
    lazy: vi.fn((importer: any) => {
      const LazyComp = (props: any) => actual.createElement('div', null, 'Lazy Component');
      (LazyComp as any).$$typeof = Symbol.for('react.lazy');
      return LazyComp;
    }),
  };
});

const weatherManifest: PluginCatalogEntry = {
  id: 'weather-query',
  displayName: 'Weather',
  version: '1.0.0',
  enabled: true,
  has_gui: true,
  promptFirstValid: true,
  description: 'Weather plugin',
  rawStatus: 'active',
  allowedRoles: [],
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
    const routes = derivePluginRoutes([weatherManifest]);
    expect(routes.sidebarEntries).toHaveLength(1);
    expect(routes.sidebarEntries[0].pluginId).toBe('weather-query');

    // 2. Component resolution
    const component = resolvePluginComponent('weather-query', mockLoaderCatalog);
    expect(component).toBeTruthy();

    // 3. Manifest validation
    const validation = validateRawManifest(weatherManifest as any, 'weather-query');
    expect(validation.valid).toBe(true);
  });
});
