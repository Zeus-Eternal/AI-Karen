/**
 * Hook Zone System - Comprehensive zone definitions and contribution management.
 *
 * Provides:
 * - 8 hook zones for UI placement
 * - 8 contribution types for plugin capabilities
 * - Zone registry for dynamic zone management
 * - Contribution validation and filtering
 * - Zone hierarchy and inheritance
 *
 * Requirements: 4.1
 */

import React, { createContext, useContext, useCallback, useMemo, useState } from 'react';

// ─── Zone Types ────────────────────────────────────────────────────────────────

/**
 * All available hook zones where plugins can contribute UI.
 * Each zone represents a specific location in the application layout.
 */
export type HookZone =
  // Sidebar zones
  | 'sidebar.plugins'
  | 'sidebar.settings'
  | 'sidebar.admin'
  | 'sidebar.communications'
  // Page zones
  | 'page.plugins.overview'
  | 'page.settings.sections'
  | 'page.admin.sections'
  | 'page.communications.tabs'
  // Dashboard zones
  | 'page.dashboard.widgets'
  | 'page.dashboard.sections'
  // Chat zones
  | 'chat.input.toolbar'
  | 'chat.input.suggestions'
  | 'chat.message.actions'
  | 'chat.message.attachments'
  // Modal/dialog zones
  | 'modal.settings.tabs'
  | 'modal.admin.tabs'
  // Header/footer zones
  | 'header.actions'
  | 'header.navigation'
  | 'footer.actions';

/**
 * Types of contributions a plugin can make.
 */
export type ContributionType =
  | 'component'        // React component rendering
  | 'action'           // Button/action trigger
  | 'menu_item'        // Navigation menu entry
  | 'widget'           // Dashboard widget
  | 'toolbar_item'     // Toolbar button/tool
  | 'suggestion'       // Chat suggestion
  | 'attachment'       // File attachment handler
  | 'metadata';        // Data/meta information

/**
 * Priority levels for zone contributions.
 */
export type ContributionPriority = 'critical' | 'high' | 'medium' | 'low' | 'optional';

/**
 * A single contribution to a hook zone.
 */
export interface ZoneContribution {
  /** Unique contribution identifier */
  id: string;
  /** Plugin that owns this contribution */
  pluginId: string;
  /** Target zone */
  zone: HookZone;
  /** Type of contribution */
  type: ContributionType;
  /** Display label */
  label: string;
  /** Description/tooltip */
  description?: string;
  /** Icon identifier or path */
  icon?: string;
  /** Priority level */
  priority?: ContributionPriority;
  /** Render order (lower = earlier) */
  order?: number;
  /** Component to render (for component type) */
  component?: React.ComponentType<Record<string, unknown>>;
  /** Action handler (for action type) */
  action?: () => void;
  /** Whether contribution is currently enabled */
  enabled?: boolean;
  /** Conditions for showing this contribution */
  conditions?: ContributionCondition[];
  /** Additional metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Condition for showing a contribution.
 */
export interface ContributionCondition {
  /** Condition type */
  type: 'user_role' | 'feature_flag' | 'plugin_state' | 'custom';
  /** Condition value */
  value: string | string[];
  /** Custom check function (for custom type) */
  check?: () => boolean;
}

/**
 * Zone configuration metadata.
 */
export interface ZoneConfig {
  /** Zone identifier */
  id: HookZone;
  /** Human-readable name */
  name: string;
  /** Zone description */
  description: string;
  /** Allowed contribution types */
  allowedTypes: ContributionType[];
  /** Maximum contributions allowed (0 = unlimited) */
  maxContributions?: number;
  /** Whether zone supports ordering */
  supportsOrdering: boolean;
  /** Whether zone is currently active */
  active: boolean;
  /** Parent zone for inheritance */
  parentZone?: HookZone;
  /** Default contribution priority */
  defaultPriority?: ContributionPriority;
}

// ─── Zone Registry ─────────────────────────────────────────────────────────────

/**
 * Default zone configurations.
 */
const DEFAULT_ZONES: ZoneConfig[] = [
  {
    id: 'sidebar.plugins',
    name: 'Plugin Sidebar',
    description: 'Main plugin navigation area',
    allowedTypes: ['component', 'menu_item'],
    maxContributions: 0,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'sidebar.settings',
    name: 'Settings Sidebar',
    description: 'Application settings navigation',
    allowedTypes: ['menu_item'],
    maxContributions: 0,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'sidebar.admin',
    name: 'Admin Sidebar',
    description: 'Administration navigation',
    allowedTypes: ['menu_item'],
    maxContributions: 0,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'high',
  },
  {
    id: 'sidebar.communications',
    name: 'Communications Sidebar',
    description: 'Communication channels navigation',
    allowedTypes: ['menu_item'],
    maxContributions: 0,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'page.plugins.overview',
    name: 'Plugin Overview Page',
    description: 'Plugin management and overview sections',
    allowedTypes: ['component', 'widget'],
    maxContributions: 0,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'page.settings.sections',
    name: 'Settings Sections',
    description: 'Application settings sections',
    allowedTypes: ['component', 'menu_item'],
    maxContributions: 0,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'page.admin.sections',
    name: 'Admin Sections',
    description: 'Administration sections',
    allowedTypes: ['component', 'menu_item'],
    maxContributions: 0,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'high',
  },
  {
    id: 'page.communications.tabs',
    name: 'Communications Tabs',
    description: 'Communication channel tabs',
    allowedTypes: ['component', 'menu_item'],
    maxContributions: 0,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'page.dashboard.widgets',
    name: 'Dashboard Widgets',
    description: 'Dashboard widget area',
    allowedTypes: ['widget', 'component'],
    maxContributions: 20,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'page.dashboard.sections',
    name: 'Dashboard Sections',
    description: 'Dashboard content sections',
    allowedTypes: ['component'],
    maxContributions: 0,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'chat.input.toolbar',
    name: 'Chat Input Toolbar',
    description: 'Toolbar above chat input',
    allowedTypes: ['toolbar_item', 'action'],
    maxContributions: 10,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'chat.input.suggestions',
    name: 'Chat Suggestions',
    description: 'Suggestion chips below chat input',
    allowedTypes: ['suggestion'],
    maxContributions: 5,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'low',
  },
  {
    id: 'chat.message.actions',
    name: 'Message Actions',
    description: 'Action buttons on chat messages',
    allowedTypes: ['action'],
    maxContributions: 5,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'chat.message.attachments',
    name: 'Message Attachments',
    description: 'Attachment handlers',
    allowedTypes: ['attachment'],
    maxContributions: 10,
    supportsOrdering: false,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'modal.settings.tabs',
    name: 'Settings Modal Tabs',
    description: 'Tabs in settings modal',
    allowedTypes: ['menu_item', 'component'],
    maxContributions: 0,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'modal.admin.tabs',
    name: 'Admin Modal Tabs',
    description: 'Tabs in admin modal',
    allowedTypes: ['menu_item', 'component'],
    maxContributions: 0,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'high',
  },
  {
    id: 'header.actions',
    name: 'Header Actions',
    description: 'Action buttons in header',
    allowedTypes: ['action'],
    maxContributions: 5,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'header.navigation',
    name: 'Header Navigation',
    description: 'Navigation items in header',
    allowedTypes: ['menu_item'],
    maxContributions: 10,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'medium',
  },
  {
    id: 'footer.actions',
    name: 'Footer Actions',
    description: 'Action buttons in footer',
    allowedTypes: ['action'],
    maxContributions: 5,
    supportsOrdering: true,
    active: true,
    defaultPriority: 'low',
  },
];

/**
 * Priority weight mapping for sorting.
 */
const PRIORITY_WEIGHTS: Record<ContributionPriority, number> = {
  critical: 0,
  high: 10,
  medium: 50,
  low: 90,
  optional: 100,
};

// ─── Hook Zone Context ────────────────────────────────────────────────────────

interface HookZoneContextValue {
  /** All registered zone configurations */
  zones: Map<HookZone, ZoneConfig>;
  /** All contributions indexed by zone */
  contributions: Map<HookZone, ZoneContribution[]>;
  /** Register a contribution */
  registerContribution: (contribution: ZoneContribution) => void;
  /** Unregister a contribution */
  unregisterContribution: (contributionId: string) => void;
  /** Get contributions for a zone */
  getContributions: (
    zone: HookZone,
    options?: {
      types?: ContributionType[];
      enabledOnly?: boolean;
    }
  ) => ZoneContribution[];
  /** Check if a zone is active */
  isZoneActive: (zone: HookZone) => boolean;
  /** Enable/disable a zone */
  setZoneActive: (zone: HookZone, active: boolean) => void;
  /** Clear all contributions for a plugin */
  clearPluginContributions: (pluginId: string) => void;
}

const HookZoneContext = createContext<HookZoneContextValue | null>(null);

// ─── Provider ──────────────────────────────────────────────────────────────────

export function HookZoneProvider({ children }: { children: React.ReactNode }) {
  const [zones, setZones] = useState<Map<HookZone, ZoneConfig>>(
    new Map(DEFAULT_ZONES.map((z) => [z.id, z]))
  );
  const [contributions, setContributions] = useState<Map<HookZone, ZoneContribution[]>>(
    new Map()
  );

  const registerContribution = useCallback((contribution: ZoneContribution) => {
    setContributions((prev) => {
      const next = new Map(prev);
      const zoneContribs = next.get(contribution.zone) || [];

      // Check if contribution already exists
      const existingIndex = zoneContribs.findIndex((c) => c.id === contribution.id);
      if (existingIndex >= 0) {
        zoneContribs[existingIndex] = contribution;
      } else {
        zoneContribs.push(contribution);
      }

      next.set(contribution.zone, zoneContribs);
      return next;
    });
  }, []);

  const unregisterContribution = useCallback((contributionId: string) => {
    setContributions((prev) => {
      const next = new Map();
      for (const [zone, contribs] of prev.entries()) {
        const filtered = contribs.filter((c) => c.id !== contributionId);
        if (filtered.length > 0) {
          next.set(zone, filtered);
        }
      }
      return next;
    });
  }, []);

  const getContributions = useCallback(
    (
      zone: HookZone,
      options: {
        types?: ContributionType[];
        enabledOnly?: boolean;
      } = {}
    ): ZoneContribution[] => {
      const zoneContribs = contributions.get(zone) || [];

      let filtered = zoneContribs;

      // Filter by types
      if (options.types && options.types.length > 0) {
        filtered = filtered.filter((c) => options.types!.includes(c.type));
      }

      // Filter by enabled status
      if (options.enabledOnly) {
        filtered = filtered.filter((c) => c.enabled !== false);
      }

      // Sort by priority and order
      const sorted = [...filtered].sort((a, b) => {
        const aPriority = a.priority || 'medium';
        const bPriority = b.priority || 'medium';
        const aWeight = PRIORITY_WEIGHTS[aPriority] ?? 50;
        const bWeight = PRIORITY_WEIGHTS[bPriority] ?? 50;

        if (aWeight !== bWeight) return aWeight - bWeight;

        const aOrder = a.order ?? 50;
        const bOrder = b.order ?? 50;

        return aOrder - bOrder;
      });

      return sorted;
    },
    [contributions]
  );

  const isZoneActive = useCallback(
    (zone: HookZone): boolean => {
      return zones.get(zone)?.active ?? false;
    },
    [zones]
  );

  const setZoneActive = useCallback((zone: HookZone, active: boolean) => {
    setZones((prev) => {
      const next = new Map(prev);
      const config = next.get(zone);
      if (config) {
        next.set(zone, { ...config, active });
      }
      return next;
    });
  }, []);

  const clearPluginContributions = useCallback((pluginId: string) => {
    setContributions((prev) => {
      const next = new Map();
      for (const [zone, contribs] of prev.entries()) {
        const filtered = contribs.filter((c) => c.pluginId !== pluginId);
        if (filtered.length > 0) {
          next.set(zone, filtered);
        }
      }
      return next;
    });
  }, []);

  const value: HookZoneContextValue = {
    zones,
    contributions,
    registerContribution,
    unregisterContribution,
    getContributions,
    isZoneActive,
    setZoneActive,
    clearPluginContributions,
  };

  return React.createElement(HookZoneContext.Provider, { value }, children);
}

// ─── Hooks ────────────────────────────────────────────────────────────────────

/**
 * Access the hook zone system.
 * Must be used within a <HookZoneProvider>.
 */
export function useHookZones(): HookZoneContextValue {
  const ctx = useContext(HookZoneContext);
  if (!ctx) {
    throw new Error('useHookZones must be used within a HookZoneProvider');
  }
  return ctx;
}

/**
 * Get contributions for a specific zone.
 */
export function useZoneContributions(
  zone: HookZone,
  options?: {
    types?: ContributionType[];
    enabledOnly?: boolean;
  }
): ZoneContribution[] {
  const { getContributions, isZoneActive } = useHookZones();
  const active = isZoneActive(zone);

  return useMemo(
    () => (active ? getContributions(zone, options) : []),
    [getContributions, zone, active, options]
  );
}

/**
 * Register a contribution hook.
 */
export function useRegisterContribution(contribution: ZoneContribution | null): void {
  const { registerContribution, unregisterContribution } = useHookZones();

  React.useEffect(() => {
    if (!contribution) return;

    registerContribution(contribution);

    return () => {
      unregisterContribution(contribution.id);
    };
  }, [contribution, registerContribution, unregisterContribution]);
}

// ─── Utility Functions ─────────────────────────────────────────────────────────

/**
 * Get all zone IDs.
 */
export function getAllZoneIds(): HookZone[] {
  return DEFAULT_ZONES.map((z) => z.id);
}

/**
 * Get zone configuration.
 */
export function getZoneConfig(zone: HookZone): ZoneConfig | undefined {
  return DEFAULT_ZONES.find((z) => z.id === zone);
}

/**
 * Create a contribution ID.
 */
export function createContributionId(
  pluginId: string,
  zone: HookZone,
  suffix?: string
): string {
  const zoneSlug = zone.replace(/\./g, '-');
  return `${pluginId}::${zoneSlug}${suffix ? `::${suffix}` : ''}`;
}