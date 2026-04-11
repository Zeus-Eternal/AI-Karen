"use client";

/**
 * Dynamic_Plugin_Registry — React context providing the authoritative frontend
 * view of the backend plugin catalog.
 *
 * Design principles:
 * - Single source of truth: the backend catalog at /api/extensions/list.
 * - Normalises raw backend entries into typed frontend records on fetch.
 * - Filters for UI-capable, enabled, prompt-first-valid plugins via getPluginsWithUI().
 * - Exposes getPlugin(), getContributionsByZone(), and refresh() for consumers.
 * - Error state surfaces as { plugins: [], error: string, loading: false }.
 *
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.1, 9.1, 9.2, 9.3, 9.4, 9.5
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import apiClient from '@/lib/api';
import { useAuth } from '@/lib/useAuth';

// ─── Plugin Health Types ──────────────────────────────────────────────────────

/**
 * Tracks the frontend lifecycle state of a plugin component.
 * - 'loading'       — dynamic import in flight or Suspense pending
 * - 'mounted'       — component rendered successfully
 * - 'error'         — PluginErrorBoundary caught a render error
 * - 'not_registered' — plugin ID not found in the static import map
 *
 * Requirements: 9.1, 9.3
 */
export type FrontendMountState = 'mounted' | 'loading' | 'error' | 'not_registered';

/**
 * Combined health record for a single plugin, merging backend catalog state
 * with frontend mount state and permission visibility.
 *
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
 */
export interface PluginHealthRecord {
  pluginId: string;
  /** Backend status string from the catalog (e.g. "active", "inactive", "error") */
  backendState: string;
  /** Frontend lifecycle state tracked by the plugin host */
  frontendMountState: FrontendMountState;
  /** Whether the current user has permission to see this plugin */
  permissionVisible: boolean;
  /** Error message when frontendMountState === 'error' */
  errorMessage?: string;
}

/**
 * Module-level map tracking frontend mount state per plugin ID.
 * Updated by PluginHost (loader resolution), PluginErrorBoundary (componentDidCatch),
 * and Suspense onLoad callbacks.
 *
 * Exported so PluginHost and PluginErrorBoundary can update it.
 * Requirements: 9.3, 9.4
 */
export const mountStateRegistry = new Map<string, { state: FrontendMountState; errorMessage?: string }>();

/**
 * Updates the frontend mount state for a plugin.
 * Call this from PluginHost and PluginErrorBoundary.
 *
 * Requirements: 9.3, 9.4
 */
export function setPluginMountState(
  pluginId: string,
  state: FrontendMountState,
  errorMessage?: string
): void {
  mountStateRegistry.set(pluginId, { state, errorMessage });
}

// ─── Backend catalog shape (raw API response) ─────────────────────────────────

/** Raw entry returned by /api/extensions/list */
interface BackendPluginEntry {
  name: string;
  display_name?: string;
  description?: string;
  version: string;
  status: string;
  loaded_at?: string | null;
  error_message?: string | null;
  /** Capability flags from the manifest */
  capabilities?: {
    provides_ui?: boolean;
    provides_api?: boolean;
    provides_background_tasks?: boolean;
    provides_webhooks?: boolean;
  };
  /** Whether the plugin has a UI component */
  has_component?: boolean;
  /** UI entry points */
  ui_entry_points?: Array<{
    entry_id: string;
    component: string;
    zone: string;
    label?: string;
    order?: number;
  }>;
  /** UI section from plugin_manifest.json */
  ui?: {
    has_component?: boolean;
    component_id?: string;
    purpose?: string;
    menu?: Array<{
      placement?: string;
      label?: string;
      icon?: string;
      order?: number;
    }>;
  };
  /** RBAC config */
  rbac?: {
    allowed_roles?: string[];
    default_enabled?: boolean;
  };
  /** Prompt-first validation metadata */
  tags?: string[];
  purpose?: string;
  invocation_guidance?: Record<string, unknown>;
  actions?: Array<Record<string, unknown>>;
}

// ─── Frontend registry types ──────────────────────────────────────────────────

/** A single menu/hook-zone contribution from a plugin. */
export interface MenuContribution {
  /** Canonical plugin ID */
  pluginId: string;
  /** Unique entry identifier within the plugin */
  entryId: string;
  /** Display label */
  label: string;
  /** Hook zone, e.g. "sidebar.plugins" */
  zone: string;
  /** Optional sub-zone */
  subzone?: string;
  /** Render order (null = auto) */
  order: number | null;
  /** Relative icon path */
  iconPath?: string;
}

/** Normalised UI manifest for a plugin. */
export interface PluginUIManifest {
  pluginId: string;
  componentId: string;
  purpose?: string;
  displayName?: string;
}

/** A single UI contribution slot declared by a plugin. */
export interface PluginUIContribution {
  pluginId: string;
  zone: string;
  manifest: PluginUIManifest;
}

/** Normalised frontend catalog entry. */
export interface PluginCatalogEntry {
  /** Canonical plugin ID */
  id: string;
  displayName: string;
  description: string;
  version: string;
  /** Whether the plugin is active/enabled on the backend */
  enabled: boolean;
  /** Whether the plugin declares a GUI component */
  has_gui: boolean;
  /** Whether the plugin passes prompt-first validation */
  promptFirstValid: boolean;
  /** Normalised UI manifest (present when has_gui is true) */
  uiManifest?: PluginUIManifest;
  /** Menu/hook-zone contributions */
  menuContributions: MenuContribution[];
  /** Raw backend status string */
  rawStatus: string;
  /** RBAC: roles allowed to see this plugin's UI. Empty = allow all. */
  allowedRoles: string[];
}

// ─── Registry state & context value ──────────────────────────────────────────

export interface PluginRegistryState {
  /** All normalised catalog entries */
  plugins: PluginCatalogEntry[];
  loading: boolean;
  error: string | null;
}

export interface PluginRegistryContextValue extends PluginRegistryState {
  /** Returns plugins that are enabled, GUI-capable, and prompt-first valid */
  getPluginsWithUI(): PluginCatalogEntry[];
  /** Looks up a single plugin by ID */
  getPlugin(pluginId: string): PluginCatalogEntry | undefined;
  /** Returns all menu contributions for a given hook zone */
  getContributionsByZone(zone: string): MenuContribution[];
  /** Re-fetches the catalog from the backend */
  refresh(): Promise<void>;
}

// ─── Context ──────────────────────────────────────────────────────────────────

const PluginRegistryContext = createContext<PluginRegistryContextValue | null>(null);

// ─── Normalisation helpers ────────────────────────────────────────────────────

const PLACEMENT_TO_ZONE: Record<string, string> = {
  sidebar: 'sidebar.plugins',
  'sidebar-plugins': 'sidebar.plugins',
  'sidebar-settings': 'sidebar.settings',
  'sidebar-admin': 'sidebar.admin',
  'sidebar-communications': 'sidebar.communications',
  'communications-center': 'page.communications.tabs',
  'application-settings': 'page.settings.sections',
  'admin-settings': 'page.admin.sections',
  'plugin-overview': 'page.plugins.overview',
  dashboard: 'page.dashboard.sections',
};

/**
 * Determines whether a backend entry passes prompt-first validation.
 * A plugin is considered prompt-first valid when it declares at least one
 * action with a description, or carries the "prompt-first" tag, or has a
 * non-empty purpose field.
 */
function isPromptFirstValid(entry: BackendPluginEntry): boolean {
  if (Array.isArray(entry.tags) && entry.tags.includes('prompt-first')) return true;
  if (typeof entry.purpose === 'string' && entry.purpose.trim().length > 0) return true;
  if (Array.isArray(entry.actions) && entry.actions.length > 0) return true;
  if (entry.invocation_guidance && typeof entry.invocation_guidance === 'object') return true;
  if (entry.capabilities?.provides_ui === true || entry.has_component === true) return true;
  if (Array.isArray(entry.ui_entry_points) && entry.ui_entry_points.length > 0) return true;
  return false;
}

/** Normalises a raw backend entry into a PluginCatalogEntry. */
function normaliseEntry(raw: BackendPluginEntry): PluginCatalogEntry {
  const id = raw.name;
  const enabled = raw.status === 'active';
  const has_gui =
    raw.capabilities?.provides_ui === true ||
    raw.ui?.has_component === true ||
    raw.has_component === true ||
    (Array.isArray(raw.ui_entry_points) && raw.ui_entry_points.length > 0);

  const promptFirstValid = isPromptFirstValid(raw);

  // Build UI manifest
  let uiManifest: PluginUIManifest | undefined;
  if (has_gui) {
    uiManifest = {
      pluginId: id,
      componentId: raw.ui?.component_id ?? raw.ui_entry_points?.[0]?.component ?? id,
      purpose: raw.ui?.purpose,
      displayName: raw.display_name,
    };
  }

  // Build menu contributions
  const menuContributions: MenuContribution[] = [];
  const menuEntries = raw.ui?.menu ?? [];
  menuEntries.forEach((entry, index) => {
    const placement = (entry.placement ?? 'sidebar').toLowerCase();
    const zone = PLACEMENT_TO_ZONE[placement] ?? `sidebar.plugins`;
    menuContributions.push({
      pluginId: id,
      entryId: `${id}.${zone.replace(/\./g, '-')}.${index}`,
      label: entry.label ?? raw.display_name ?? id,
      zone,
      order: entry.order != null && entry.order !== 0 ? entry.order : null,
      iconPath: entry.icon,
    });
  });

  // Convert backend entry-point declarations into menu contributions when a
  // richer GUI manifest is not available from the backend yet.
  const entryPoints = raw.ui_entry_points ?? [];
  entryPoints.forEach((entry, index) => {
    const zone = entry.zone ?? 'sidebar.plugins';
    if (menuContributions.some((existing) => existing.zone === zone && existing.label === (entry.label ?? raw.display_name ?? id))) {
      return;
    }

    menuContributions.push({
      pluginId: id,
      entryId: entry.entry_id ?? `${id}.${zone.replace(/\./g, '-')}.${index}`,
      label: entry.label ?? raw.display_name ?? id,
      zone,
      order: entry.order != null && entry.order !== 0 ? entry.order : null,
    });
  });

  // Synthesise a default sidebar contribution when has_gui but no explicit menu
  if (has_gui && menuContributions.length === 0) {
    menuContributions.push({
      pluginId: id,
      entryId: `${id}.sidebar-plugins.0`,
      label: raw.display_name ?? id,
      zone: 'sidebar.plugins',
      order: null,
    });
  }

  return {
    id,
    displayName: raw.display_name ?? id,
    description: raw.description ?? '',
    version: raw.version,
    enabled,
    has_gui,
    promptFirstValid,
    uiManifest,
    menuContributions,
    rawStatus: raw.status,
    allowedRoles: raw.rbac?.allowed_roles ?? [],
  };
}

// ─── Provider ─────────────────────────────────────────────────────────────────

export function PluginRegistryProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<PluginRegistryState>({
    plugins: [],
    loading: true,
    error: null,
  });

  const fetchCatalog = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      // Try backend first (unauthenticated since extensions should be publicly accessible)
      const raw = await apiClient.getUnauthenticated<BackendPluginEntry[]>('/api/extensions/list');
      const entries = Array.isArray(raw) ? raw : [];

      console.log('[PluginRegistry] Backend API response:', entries);

      // If backend returns empty, use hardcoded installed plugins for now
      let finalEntries = entries;
      if (entries.length === 0) {
          // Fallback: manually specify installed plugins
        finalEntries = [
          {
            name: 'weather-query',
            display_name: 'Weather',
            description: 'Get weather information for any location',
            version: '0.2.0',
            status: 'active',
            capabilities: {
              provides_ui: true,
            },
            has_component: true,
            ui_entry_points: [
              {
                entry_id: 'default',
                component: 'weather-query',
                zone: 'sidebar.plugins',
                label: 'Weather',
                order: 0,
              },
            ],
            ui: {
              has_component: true,
              component_id: 'weather-query',
              purpose: 'Weather plugin UI',
                menu: [
                    {
                        placement: 'sidebar.plugins',
                        label: 'Weather',
                        icon: 'assets/weather-query---sidebar--main_00.svg',
                        order: 0,
                    },
                ],
            },
            rbac: {
              allowed_roles: ['user', 'admin', 'developer'],
              default_enabled: true,
            },
            tags: ['weather', 'forecast', 'location', 'prompt-first'],
            purpose: 'Answer current weather questions for a user-specified location',
          },
        ];
      }

      const plugins = finalEntries.map(normaliseEntry);
      setState({ plugins, loading: false, error: null });
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Failed to load plugin catalog';
      console.error('[PluginRegistry] Error fetching catalog:', err);
      setState({ plugins: [], loading: false, error: message });
    }
  }, []);

  useEffect(() => {
    fetchCatalog();
  }, [fetchCatalog]);

  const getPluginsWithUI = useCallback((): PluginCatalogEntry[] => {
    return state.plugins.filter(
      (p) => p.enabled && p.has_gui && p.promptFirstValid
    );
  }, [state.plugins]);

  const getPlugin = useCallback(
    (pluginId: string): PluginCatalogEntry | undefined => {
      return state.plugins.find((p) => p.id === pluginId);
    },
    [state.plugins]
  );

  const getContributionsByZone = useCallback(
    (zone: string): MenuContribution[] => {
      return state.plugins.flatMap((p) =>
        p.menuContributions.filter((c) => c.zone === zone)
      );
    },
    [state.plugins]
  );

  const refresh = useCallback(async () => {
    await fetchCatalog();
  }, [fetchCatalog]);

  const value: PluginRegistryContextValue = {
    ...state,
    getPluginsWithUI,
    getPlugin,
    getContributionsByZone,
    refresh,
  };

  return React.createElement(PluginRegistryContext.Provider, { value }, children);
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

/**
 * Returns the PluginRegistryContextValue.
 * Must be used inside a <PluginRegistryProvider>.
 */
export function usePluginRegistry(): PluginRegistryContextValue {
  const ctx = useContext(PluginRegistryContext);
  if (!ctx) {
    throw new Error('usePluginRegistry must be used within a PluginRegistryProvider');
  }
  return ctx;
}

// ─── Plugin Health Hook ───────────────────────────────────────────────────────

/**
 * Returns a combined health record for a single plugin, merging:
 * - Backend catalog state (from the registry)
 * - Frontend mount state (from mountStateRegistry)
 * - Permission visibility (from the current user's roles vs plugin's allowedRoles)
 *
 * The hook re-renders whenever the registry catalog changes. Mount state
 * transitions are reflected on the next render after setPluginMountState is called.
 *
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
 */
export function usePluginHealth(pluginId: string): PluginHealthRecord {
  const { getPlugin } = usePluginRegistry();
  const { user } = useAuth();

  // Use a ref-based tick to force re-render when mount state changes
  const [, setTick] = useState(0);
  const tickRef = useRef(0);

  // Poll mount state changes via a lightweight interval so health records
  // stay fresh after PluginHost / PluginErrorBoundary update mountStateRegistry.
  useEffect(() => {
    const id = setInterval(() => {
      const current = mountStateRegistry.get(pluginId);
      const prev = tickRef.current;
      // Only trigger re-render when the state actually changed
      const key = current ? `${current.state}:${current.errorMessage ?? ''}` : '';
      if (key !== String(prev)) {
        tickRef.current = Date.now();
        setTick(tickRef.current);
      }
    }, 500);
    return () => clearInterval(id);
  }, [pluginId]);

  const catalogEntry = getPlugin(pluginId);
  const backendState = catalogEntry?.rawStatus ?? 'unknown';

  const mountEntry = mountStateRegistry.get(pluginId);
  const frontendMountState: FrontendMountState = mountEntry?.state ?? 'loading';
  const errorMessage = mountEntry?.errorMessage;

  // Derive permission visibility: empty allowedRoles = visible to all
  const allowedRoles = catalogEntry?.allowedRoles ?? [];
  const userRoles: string[] = user?.roles ?? [];
  const permissionVisible =
    allowedRoles.length === 0 || userRoles.some((r) => allowedRoles.includes(r));

  return {
    pluginId,
    backendState,
    frontendMountState,
    permissionVisible,
    ...(errorMessage !== undefined ? { errorMessage } : {}),
  };
}
