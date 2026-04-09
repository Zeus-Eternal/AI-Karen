"use client";

/**
 * PluginHost — renders a plugin's UI component by ID.
 *
 * Resolution: delegates to loader.ts as the single frontend loading authority.
  * Uses generated import map from plugin_repo for dynamic loading.
 * No hardcoded importer maps - everything resolved through loader service.
 *
 * Requirements: 3.1, 3.2, 3.3, 3.4, 7.1, 7.2, 7.3, 7.4, 7.5, 9.3, 9.4, 29, 30
 */

import React, { Suspense, useMemo, useEffect, useState } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import {
  resolvePluginComponentAsync,
  normalizePluginId,
  getRegisteredPluginIds
} from '../../plugin_host/loader';
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
  const [pluginComponent, setPluginComponent] = useState<React.LazyExoticComponent<React.ComponentType<Record<string, unknown>>> | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Resolve plugin component using loader as single authority
  useEffect(() => {
    const loadPlugin = async () => {
      try {
        setIsLoading(true);
        
        // Use async loader to resolve component from installed packages only
        console.log(`[PluginHost] Resolving component for ${pluginId}`);
        const component = await resolvePluginComponentAsync(pluginId);
        console.log(`[PluginHost] Resolved component for ${pluginId}:`, !!component);

        if (component) {
          setPluginComponent(component);
          setPluginMountState(pluginId, 'loading');
        } else {
          console.warn(`[PluginHost] No component found for ${pluginId}`);
          setPluginMountState(pluginId, 'not_registered');
        }
      } catch (error) {
        console.error(`Failed to resolve plugin ${pluginId}:`, error);
        setPluginMountState(pluginId, 'error');
      } finally {
        setIsLoading(false);
      }
    };

    loadPlugin();
  }, [pluginId]);

  // Check if plugin is registered in generated registry
  const isRegistered = useMemo(() => {
    return getRegisteredPluginIds().includes(normalizedId);
  }, [normalizedId]);

  // Show safe fallback when no component is found
  if (!pluginComponent && !isLoading) {
    return (
      <div className="p-8 border rounded-lg bg-destructive/5 text-center text-destructive text-sm flex flex-col items-center justify-center gap-2">
        <AlertCircle className="h-5 w-5" />
        <p>
          No UI registered for plugin{' '}
          <span className="font-mono font-bold">{normalizedId}</span>.
        </p>
        <p className="text-xs opacity-70 italic">
          {isRegistered 
            ? "Plugin is installed but UI component not found. Check plugin manifest."
            : "Install plugin UI first using the plugin overview page."
          }
        </p>
      </div>
    );
  }

  // Show loading state
  if (isLoading) {
    return (
      fallback ?? (
        <div className="flex flex-col items-center justify-center p-12 space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary opacity-50" />
          <p className="text-xs text-muted-foreground animate-pulse">
            Loading {pluginId} UI module…
          </p>
        </div>
      )
    );
  }

  // Render plugin component with error boundaries
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
          {pluginComponent && React.createElement(pluginComponent)}
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

// ─── Plugin_Error_Boundary Usage ─────────────────────────────────────────────
// The PluginErrorBoundary component is imported from plugin_host/PluginErrorBoundary.tsx
