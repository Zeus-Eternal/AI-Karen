"use client";

/**
 * PluginHost — renders a plugin's UI component by ID.
 *
 * Resolution: looks up the normalised plugin ID in the auto-discovered
 * PLUGIN_IMPORT_MAP (built at compile time by loader.ts via require.context).
 * No manual registration needed — just drop a PluginPage.tsx in the plugin's
 * ui/ folder.
 *
 * Requirements: 3.1, 3.2, 3.3, 3.4, 7.1, 7.2, 7.3, 7.4, 7.5, 9.3, 9.4
 */

import React, { Suspense, lazy, useMemo, useEffect } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import { PLUGIN_IMPORT_MAP, normalizePluginId } from '../../plugin_host/loader';
import { setPluginMountState } from '../../plugin_host/registry';
import { PluginErrorBoundary } from '../../plugin_host/PluginErrorBoundary';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface PluginHostProps {
  pluginId: string;
  fallback?: React.ReactNode;
}

// ─── PluginHost ───────────────────────────────────────────────────────────────

export function PluginHost({ pluginId, fallback }: PluginHostProps) {
  const normalizedId = useMemo(() => normalizePluginId(pluginId), [pluginId]);

  const PluginComponent = useMemo(() => {
    const importer = PLUGIN_IMPORT_MAP[normalizedId] ?? PLUGIN_IMPORT_MAP[pluginId];
    if (!importer) return null;
    return lazy(importer);
  }, [normalizedId, pluginId]);

  // Mark as not_registered when no importer is found
  useEffect(() => {
    if (!PluginComponent) {
      setPluginMountState(pluginId, 'not_registered');
    } else {
      // Mark as loading until the component mounts
      setPluginMountState(pluginId, 'loading');
    }
  }, [pluginId, PluginComponent]);

  if (!PluginComponent) {
    return (
      <div className="p-8 border rounded-lg bg-destructive/5 text-center text-destructive text-sm flex flex-col items-center justify-center gap-2">
        <AlertCircle className="h-5 w-5" />
        <p>
          No UI registered for plugin{' '}
          <span className="font-mono font-bold">{normalizedId}</span>.
        </p>
        <p className="text-xs opacity-70 italic">
          Add a PluginPage.tsx inside the plugin&apos;s ui/ folder.
        </p>
      </div>
    );
  }

  return (
    <Suspense
      fallback={
        fallback ?? (
          <div className="flex flex-col items-center justify-center p-12 space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary opacity-50" />
            <p className="text-xs text-muted-foreground animate-pulse">
              Loading {pluginId} UI module…
            </p>
          </div>
        )
      }
    >
      <PluginErrorBoundary pluginId={pluginId}>
        <PluginMountTracker pluginId={pluginId}>
          <PluginComponent />
        </PluginMountTracker>
      </PluginErrorBoundary>
    </Suspense>
  );
}

// ─── PluginMountTracker ───────────────────────────────────────────────────────

/** Marks the plugin as 'mounted' once it renders successfully. */
function PluginMountTracker({
  pluginId,
  children,
}: {
  pluginId: string;
  children: React.ReactNode;
}) {
  useEffect(() => {
    setPluginMountState(pluginId, 'mounted');
  }, [pluginId]);

  return <>{children}</>;
}

// ─── PluginErrorBoundary ──────────────────────────────────────────────────────

interface ErrorBoundaryProps {
  pluginId: string;
  children: React.ReactNode;
}

// ─── Plugin_Error_Boundary Usage ─────────────────────────────────────────────
// The PluginErrorBoundary component is imported from plugin_host/PluginErrorBoundary.tsx
