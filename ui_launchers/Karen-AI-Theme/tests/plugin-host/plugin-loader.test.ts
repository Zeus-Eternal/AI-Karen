import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { resolvePluginComponent, normalizePluginId, PLUGIN_IMPORT_MAP, type LoaderPluginEntry } from '../../src/plugin_host/loader';
import '@testing-library/jest-dom';
import React from 'react';

vi.mock('@/lib/api', () => ({
  default: { get: vi.fn() }
}));

vi.mock('@/lib/useAuth', () => ({
  useAuth: () => ({ user: { id: 'test-user', roles: ['user', 'admin'] } })
}));

vi.mock('react', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react')>();
  return {
    ...actual,
    lazy: vi.fn((importer: any) => {
      const LazyComp = (props: any) => actual.createElement('div', null, 'Lazy Component');
      (LazyComp as any).$$typeof = Symbol.for('react.lazy');
      return LazyComp;
    })
  };
});

const mockCatalog: LoaderPluginEntry[] = [
  { name: 'weather-query', status: 'active', capabilities: { provides_ui: true } },
  { name: 'data-connector', status: 'active', capabilities: { provides_ui: true } },
];

describe('Plugin Loader', () => {
  it('should normalize plugin ids correctly', () => {
    expect(normalizePluginId('Weather_Query')).toBe('weather-query');
    expect(normalizePluginId('  weather-query  ')).toBe('weather-query');
  });

  it('should resolve plugin components', () => {
    (PLUGIN_IMPORT_MAP as any)['weather-query'] = vi.fn().mockResolvedValue({ default: () => null });
    const component = resolvePluginComponent('weather-query', mockCatalog);
    expect(component).toBeTruthy();
  });

  it('should resolve aliases correctly', () => {
    const mockImporter = vi.fn().mockResolvedValue({ default: vi.fn() });
    (PLUGIN_IMPORT_MAP as any)['data-connector'] = mockImporter;
    (PLUGIN_IMPORT_MAP as any)['karen-data-connector'] = mockImporter;
    const catalog: LoaderPluginEntry[] = [
      { name: 'karen-data-connector', status: 'active', capabilities: { provides_ui: true } },
      { name: 'data-connector', status: 'active', capabilities: { provides_ui: true } },
    ];
    const component1 = resolvePluginComponent('karen-data-connector', catalog);
    const component2 = resolvePluginComponent('data-connector', catalog);
    expect(component1).toBe(component2);
  });
});
