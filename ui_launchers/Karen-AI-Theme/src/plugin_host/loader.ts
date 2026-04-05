/**
 * Auto-Discovery Plugin Loader — hybrid static discovery + dynamic backend validation.
 *
 * Design principles:
 * - Uses webpack require.context to statically discover all plugin UI components
 * - Fetches backend catalog at runtime to validate plugin status and capabilities
 * - Falls back to safe fallback components when plugins are disabled or missing
 * - No manual registration needed — just drop a PluginPage.tsx in the plugin's ui/ folder
 *
 * Requirements: 3.1, 3.2, 3.3, 3.4
 */

import React from 'react';

// ─── Types ────────────────────────────────────────────────────────────────────

/** Minimal shape of a backend catalog entry needed by the loader. */
export interface LoaderPluginEntry {
  name: string;
  status: string;
  capabilities?: {
    provides_ui?: boolean;
  };
  ui_entry_points?: UIEntryPoint[];
}

/** A single UI entry point declared by a plugin. */
export interface UIEntryPoint {
  entry_id: string;
  component: string;
  zone: string;
  label?: string;
  order?: number;
}

type PluginImporter = () => Promise<{ default: React.ComponentType<Record<string, unknown>> }>;

/** Backend import map response from /api/ui-materialization/import-map */
interface BackendImportMap {
  status: string;
  data: {
    import_map: Record<string, string>;
    total_entries: number;
  };
}

/** Backend catalog response */
interface BackendCatalog {
  status: string;
  data: {
    plugins: { plugin_id: string; status: string; has_component: boolean; ui_entry_points?: UIEntryPoint[] }[];
    total: number;
  };
}

// ─── Fallback component factory ───────────────────────────────────────────────

function makeLoadFailureFallback(pluginId: string): React.ComponentType<Record<string, unknown>> {
  const Fallback: React.FC = () =>
    React.createElement(
      'div',
      {
        style: {
          padding: '1rem',
          border: '1px solid #e5e7eb',
          borderRadius: '0.375rem',
          textAlign: 'center',
          fontSize: '0.875rem',
          color: '#6b7280',
        },
      },
      `Plugin "${pluginId}" failed to load.`
    );
  Fallback.displayName = `PluginLoadFailure(${pluginId})`;
  return Fallback;
}

// ─── Static Discovery via require.context ─────────────────────────────────────

/**
 * Discover all plugin UI components at build time using webpack's require.context.
 * This scans the plugins directory for UI components matching the pattern: plugins/[name]/ui/*PluginPage.tsx
 */
// eslint-disable-next-line @typescript-eslint/no-require-imports
const pluginContext = require.context(
  '@/plugins',
  true,
  /ui\/.*PluginPage\.(tsx|jsx)$/
);

/**
 * Build a static import map from discovered plugin components.
 * Maps plugin directory names to their import functions.
 */
function buildStaticImportMap(): Record<string, PluginImporter> {
  const map: Record<string, PluginImporter> = {};

  pluginContext.keys().forEach((key: string) => {
    // Extract plugin ID from path: ./weather/ui/WeatherPluginPage.tsx -> weather
    const match = key.match(/^\.\/([^/]+)\/ui\/.*PluginPage\.(tsx|jsx)$/);
    if (match) {
      const pluginDirName = match[1];
      const normalizedId = pluginDirName.toLowerCase().replace(/_/g, '-');

      // Create importer with webpack chunk name
      const importer: PluginImporter = () =>
        pluginContext(key)
          .then((module: any) => {
            if (module && module.default) {
              return module;
            }
            // Handle ES module default export
            if (module && module.__esModule && module.default) {
              return { default: module.default };
            }
            return { default: makeLoadFailureFallback(normalizedId) };
          })
          .catch(() => ({
            default: makeLoadFailureFallback(normalizedId),
          }));

      map[normalizedId] = importer;

      // Also add alias with underscores for compatibility
      if (pluginDirName !== normalizedId) {
        map[pluginDirName] = importer;
      }
    }
  });

  return map;
}

// Build static import map at module load time
const STATIC_IMPORT_MAP = buildStaticImportMap();

/**
 * Legacy manual import map for plugins that can't be auto-discovered.
 * This serves as a fallback for backwards compatibility.
 */
const LEGACY_IMPORT_MAP: Record<string, PluginImporter> = {};

/**
 * Combined import map: static discovery + legacy fallback.
 */
export const PLUGIN_IMPORT_MAP: Record<string, PluginImporter> = {
  ...LEGACY_IMPORT_MAP,
  ...STATIC_IMPORT_MAP,
};

// ─── Backend Catalog Cache ───────────────────────────────────────────────────

let cachedCatalog: LoaderPluginEntry[] | null = null;
let catalogFetchPromise: Promise<LoaderPluginEntry[]> | null = null;
let lastCatalogFetch = 0;
const CATALOG_CACHE_TTL = 5 * 60 * 1000; // 5 minutes

/**
 * Fetch the backend plugin catalog.
 * Uses caching to avoid excessive API calls.
 */
async function fetchBackendCatalog(): Promise<LoaderPluginEntry[]> {
  const now = Date.now();

  // Return cached if still fresh
  if (cachedCatalog && now - lastCatalogFetch < CATALOG_CACHE_TTL) {
    return cachedCatalog;
  }

  // Reuse in-flight request
  if (catalogFetchPromise) {
    return catalogFetchPromise;
  }

  // Fetch from backend
  catalogFetchPromise = fetch('/api/ui-materialization/discover', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  })
    .then((res) => {
      if (!res.ok) {
        throw new Error(`Backend catalog fetch failed: ${res.status}`);
      }
      return res.json() as Promise<BackendCatalog>;
    })
    .then((response) => {
      cachedCatalog = response.data.plugins.map((p) => ({
        name: p.plugin_id,
        status: p.status,
        capabilities: {
          provides_ui: p.has_component,
        },
      }));
      lastCatalogFetch = now;
      catalogFetchPromise = null;
      return cachedCatalog!;
    })
    .catch((error) => {
      console.warn('[PluginLoader] Failed to fetch backend catalog:', error);
      catalogFetchPromise = null;
      // Return empty catalog on error (will use static discovery only)
      return [] as LoaderPluginEntry[];
    });

  return catalogFetchPromise;
}

/**
 * Invalidate the catalog cache, forcing a fresh fetch on next access.
 */
export function invalidateCatalogCache(): void {
  cachedCatalog = null;
  lastCatalogFetch = 0;
}

// ─── Loader API ───────────────────────────────────────────────────────────────

/**
 * Normalises a plugin ID for import-map lookup.
 * Converts underscores to hyphens so "data_connector" matches "data-connector".
 */
export function normalizePluginId(id: string): string {
  return id.trim().toLowerCase().replace(/_/g, '-');
}

/**
 * Returns all valid UI entry points for a plugin from the backend catalog entry.
 * Falls back to a single synthetic entry when the catalog entry declares
 * `capabilities.provides_ui: true` but has no explicit `ui_entry_points`.
 * Returns an empty array when the plugin is not GUI-capable, disabled, or
 * not present in the import map.
 */
export function resolvePluginEntries(
  pluginId: string,
  catalog: LoaderPluginEntry[]
): UIEntryPoint[] {
  const normalised = normalizePluginId(pluginId);
  const entry = catalog.find(
    (p) => normalizePluginId(p.name) === normalised
  );

  if (!entry) return [];
  if (entry.status !== 'active') return [];
  if (!entry.capabilities?.provides_ui) return [];
  if (!(normalised in PLUGIN_IMPORT_MAP)) return [];

  if (entry.ui_entry_points && entry.ui_entry_points.length > 0) {
    return entry.ui_entry_points;
  }

  return [{ entry_id: 'default', component: normalised, zone: 'sidebar.plugins' }];
}

/**
 * Resolves a plugin ID to a React.lazy-wrapped component.
 *
 * Returns `null` when the plugin is not active, not GUI-capable, or not in
 * the import map. Accepts both hyphenated and underscored plugin IDs.
 */
export function resolvePluginComponent(
  pluginId: string,
  catalog: LoaderPluginEntry[],
  entryId?: string
): React.LazyExoticComponent<React.ComponentType<Record<string, unknown>>> | null {
  const entries = resolvePluginEntries(pluginId, catalog);
  if (entries.length === 0) return null;

  if (entryId !== undefined) {
    const match = entries.find((e) => e.entry_id === entryId);
    if (!match) return null;
  }

  const normalised = normalizePluginId(pluginId);
  const importer = PLUGIN_IMPORT_MAP[normalised];
  if (!importer) return null;

  return React.lazy(importer);
}

/**
 * Async version of resolvePluginComponent that fetches the backend catalog.
 */
export async function resolvePluginComponentAsync(
  pluginId: string,
  entryId?: string
): Promise<React.LazyExoticComponent<React.ComponentType<Record<string, unknown>>> | null> {
  const catalog = await fetchBackendCatalog();
  return resolvePluginComponent(pluginId, catalog, entryId);
}

/** Returns the set of plugin IDs currently registered in the import map. */
export function getRegisteredPluginIds(): string[] {
  return Object.keys(PLUGIN_IMPORT_MAP);
}

/**
 * Returns statistics about the plugin loader.
 */
export function getLoaderStats(): {
  staticCount: number;
  legacyCount: number;
  totalCount: number;
  pluginIds: string[];
} {
  const staticCount = Object.keys(STATIC_IMPORT_MAP).length;
  const legacyCount = Object.keys(LEGACY_IMPORT_MAP).length;
  return {
    staticCount,
    legacyCount,
    totalCount: Object.keys(PLUGIN_IMPORT_MAP).length,
    pluginIds: Object.keys(PLUGIN_IMPORT_MAP),
  };
}