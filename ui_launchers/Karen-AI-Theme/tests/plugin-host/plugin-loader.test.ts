import { vi, describe, it, expect } from 'vitest';

// Mock the require object before anything else is imported
vi.hoisted(() => {
  if (typeof (globalThis as any).require === 'undefined') {
    (globalThis as any).require = {};
  }
  (globalThis as any).require.context = vi.fn(() => {
    const context = (key: string) => ({ default: () => null });
    context.keys = () => [] as string[];
    context.resolve = (key: string) => key;
    context.id = 'mock';
    return context;
  });
});

// Now import the module that calls require.context at top level
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
    }),
  };
});

const mockCatalog: LoaderPluginEntry[] = [
  { name: 'weather-query', status: 'active', capabilities: { provides_ui: true } },
  { name: 'data-connector', status: 'active', capabilities: { provides_ui: true } },
];

describe('Plugin Loader', () => {
  it('should normalize plugin ids', () => {
    expect(normalizePluginId('Weather_Query')).toBe('weather-query');
  });

  it('should resolve components', () => {
    (PLUGIN_IMPORT_MAP as any)['weather-query'] = vi.fn().mockResolvedValue({ default: () => null });
    const component = resolvePluginComponent('weather-query', mockCatalog);
    expect(component).toBeTruthy();
  });
});
