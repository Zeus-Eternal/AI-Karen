"use client";

/**
 * Slot_Manager — named-slot rendering for the frontend plugin host.
 *
 * Provides:
 * - `SlotId` union type for all valid plugin contribution slots
 * - `useSlotPlugins(slotId)` hook — filters the registry catalog by zone
 * - `<PluginSlot slotId={...} pluginProps={...} />` component — renders all
 *   plugins contributing to a slot, each wrapped in PluginErrorBoundary + Suspense
 *
 * Requirements: 4.1, 5.1, 5.2, 5.3, 5.4, 5.5
 */

import React, { Suspense, lazy, useMemo, useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { usePluginRegistry, type PluginCatalogEntry } from './registry';
import { resolvePluginComponent, normalizePluginId, getRegisteredPluginIds, PLUGIN_IMPORT_MAP } from './loader';
import { PluginErrorBoundary } from './PluginErrorBoundary';
import { type HookZone, useZoneContributions, type ContributionType, type ZoneContribution } from './hook-zones-context';

// ─── SlotId ───────────────────────────────────────────────────────────────────

/**
 * All valid slot identifiers that plugins may contribute UI into.
 * Maps to hook zones defined in hook-zones.ts.
 */
export type SlotId = HookZone;

// ─── useSlotPlugins ───────────────────────────────────────────────────────────

/**
 * Returns all enabled, GUI-capable plugins that contribute to the given slot.
 * Filters the registry catalog by `menuContributions[].zone === slotId`.
 *
 * @param slotId - The target slot identifier
 * @returns Array of matching PluginCatalogEntry records
 */
export function useSlotPlugins(slotId: SlotId): PluginCatalogEntry[] {
  const { plugins } = usePluginRegistry();

  return useMemo(
    () =>
      plugins.filter(
        (plugin) =>
          plugin.enabled &&
          plugin.has_gui &&
          plugin.menuContributions.some((c) => c.zone === slotId)
      ),
    [plugins, slotId]
  );
}

// ─── PluginSlot ───────────────────────────────────────────────────────────────

export interface PluginSlotProps {
  /** The slot to render plugins into */
  slotId: SlotId;
  /** Allowed contribution types */
  types?: ContributionType[];
  /** Extra props forwarded to each rendered plugin component */
  pluginProps?: Record<string, unknown>;
  /** Maximum plugins to render */
  maxPlugins?: number;
}

/**
 * Renders all plugins contributing to the given slot.
 *
 * Each plugin component is:
 * - Resolved via the static PLUGIN_IMPORT_MAP (React.lazy)
 * - Wrapped in a PluginErrorBoundary to isolate render failures
 * - Wrapped in Suspense with a spinner fallback
 *
 * Returns an empty fragment when no plugins contribute to the slot.
 */
export function PluginSlot({
  slotId,
  types,
  pluginProps = {},
  maxPlugins,
}: PluginSlotProps) {
  const contributors = useSlotPlugins(slotId);
  const hookContributions = useZoneContributions(slotId, {
    types: types || ['component'],
    enabledOnly: true,
  });

  // Combine registry-based and hook-based contributions
  const allContributors = useMemo(() => {
    const contributorIds = new Set(contributors.map((p) => p.id));
    
    type ContributorEntry = 
      | { type: 'registry'; plugin: PluginCatalogEntry }
      | { type: 'hook'; hookContribution: ZoneContribution };

    const combined: ContributorEntry[] = contributors.map((p) => ({ 
      type: 'registry' as const, 
      plugin: p 
    }));

    // Add hook contributions that aren't already in the registry
    for (const hc of hookContributions) {
      if (!contributorIds.has(hc.pluginId) && hc.component) {
        combined.push({
          type: 'hook' as const,
          hookContribution: hc,
        });
      }
    }

    if (maxPlugins && maxPlugins > 0) {
      return combined.slice(0, maxPlugins);
    }

    return combined;
  }, [contributors, hookContributions, maxPlugins]);

  if (allContributors.length === 0) {
    return <></>;
  }

  return (
    <>
      {allContributors.map((entry, index) => {
        if (entry.type === 'hook' && entry.hookContribution?.component) {
          const Component = entry.hookContribution.component;
          return (
            <Suspense
              key={`hook-${entry.hookContribution.id}`}
              fallback={
                <div className="flex items-center justify-center p-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary opacity-50" />
                </div>
              }
            >
              <PluginErrorBoundary pluginId={entry.hookContribution.pluginId}>
                <Component pluginId={entry.hookContribution.pluginId} {...pluginProps} />
              </PluginErrorBoundary>
            </Suspense>
          );
        }

        const plugin = entry.type === 'registry' ? entry.plugin : null;
        if (!plugin) return null;

        const normalised = normalizePluginId(plugin.id);
        const importer = PLUGIN_IMPORT_MAP[normalised];

        if (!importer) return null;

        const PluginComponent = lazy(importer);

        return (
          <Suspense
            key={plugin.id}
            fallback={
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-6 w-6 animate-spin text-primary opacity-50" />
              </div>
            }
          >
            <PluginErrorBoundary pluginId={plugin.id}>
              <PluginComponent pluginId={plugin.id} {...pluginProps} />
            </PluginErrorBoundary>
          </Suspense>
        );
      })}
    </>
  );
}
