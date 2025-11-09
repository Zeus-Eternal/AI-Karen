"use client";

import React, { useEffect, useMemo, useState, useCallback } from "react";
import { useExtensionContext, navigationActions } from "@/extensions";
import {
  getPluginService,
  getExtensionService,
  type PluginCategory,
} from "@/services";
import type { ExtensionInfo as LegacyExtensionInfo } from "@/services/extensionService";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

/**
 * SidebarNavigation
 * - Loads plugin categories and extensions safely (with unmount guards)
 * - A11y-friendly navigation markup
 * - Graceful loading/empty/error states
 */

export default function SidebarNavigation() {
  const { state, dispatch } = useExtensionContext();

  const [pluginCategories, setPluginCategories] = useState<PluginCategory[]>([]);
  const [extensions, setExtensions] = useState<LegacyExtensionInfo[]>([]);

  const [loadingPlugins, setLoadingPlugins] = useState(true);
  const [loadingExts, setLoadingExts] = useState(true);
  const [pluginErr, setPluginErr] = useState<string | null>(null);
  const [extErr, setExtErr] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    (async () => {
      try {
        const cats = await getPluginService().getPluginsByCategory();
        if (active) setPluginCategories(cats ?? []);
      } catch (e: any) {
        if (active) setPluginErr(e?.message ?? "Failed to load plugins.");
      } finally {
        if (active) setLoadingPlugins(false);
      }
    })();

    (async () => {
      try {
        const exts = await getExtensionService().getInstalledExtensions();
        if (active) setExtensions(exts ?? []);
      } catch (e: any) {
        if (active) setExtErr(e?.message ?? "Failed to load extensions.");
      } finally {
        if (active) setLoadingExts(false);
      }
    })();

    return () => {
      active = false;
    };
  }, []);

  const handleOpenPlugin = useCallback(
    (categoryName: string, pluginName: string) => {
      const actions = navigationActions.navigateToPluginProvider(
        categoryName.toLowerCase(),
        pluginName,
      );
      // Ensure array of actions is dispatched in order
      actions.forEach((a) => dispatch(a));
    },
    [dispatch],
  );

  const handleOpenExtension = useCallback(
    (extName: string) => {
      dispatch({
        type: "PUSH_BREADCRUMB",
        item: { level: "items", id: extName, name: extName },
      });
    },
    [dispatch],
  );

  const isPluginsView = state.currentCategory === "Plugins";

  const content = useMemo(() => {
    if (isPluginsView) {
      if (loadingPlugins) {
        return (
          <div className="space-y-3" aria-busy="true" aria-live="polite">
            <div className="h-4 w-24 bg-muted rounded" />
            <div className="h-8 w-full bg-muted rounded" />
            <div className="h-8 w-5/6 bg-muted rounded" />
          </div>
        );
      }
      if (pluginErr) {
        return (
          <div className="text-sm text-destructive" role="alert">
            {pluginErr}
          </div>
        );
      }
      if (pluginCategories.length === 0) {
        return <p className="text-sm text-muted-foreground">No plugins available.</p>;
      }
      return (
        <div className="space-y-4">
          {pluginCategories.map((cat) => (
            <div key={cat.name} className="space-y-2">
              <p className="text-xs font-semibold text-muted-foreground uppercase sm:text-sm md:text-base">
                {cat.name}
              </p>
              <ul className="pl-2 space-y-1">
                {(cat.plugins ?? []).map((p) => (
                  <li key={`${cat.name}:${p.name}`}>
                    <Button
                      type="button"
                      variant="ghost"
                      className="w-full justify-start text-sm hover:underline md:text-base lg:text-lg"
                      onClick={() => handleOpenPlugin(cat.name, p.name)}
                    >
                      {p.name}
                    </Button>
                  </li>
                ))}
              </ul>
              <Separator />
            </div>
          ))}
        </div>
      );
    }

    // Extensions view
    if (loadingExts) {
      return (
        <div className="space-y-3" aria-busy="true" aria-live="polite">
          <div className="h-4 w-24 bg-muted rounded" />
          <div className="h-8 w-full bg-muted rounded" />
          <div className="h-8 w-5/6 bg-muted rounded" />
        </div>
      );
    }
    if (extErr) {
      return (
        <div className="text-sm text-destructive" role="alert">
          {extErr}
        </div>
      );
    }
    if (extensions.length === 0) {
      return <p className="text-sm text-muted-foreground">No extensions installed.</p>;
    }
    return (
      <ul className="space-y-1">
        {extensions.map((ext) => (
          <li key={ext.name}>
            <Button
              type="button"
              variant="ghost"
              className="w-full justify-start text-sm hover:underline md:text-base lg:text-lg"
              onClick={() => handleOpenExtension(ext.name)}
            >
              {ext.name}
            </Button>
          </li>
        ))}
      </ul>
    );
  }, [
    isPluginsView,
    loadingPlugins,
    pluginErr,
    pluginCategories,
    handleOpenPlugin,
    loadingExts,
    extErr,
    extensions,
    handleOpenExtension,
  ]);

  return (
    <nav
      className="space-y-4"
      role="navigation"
      aria-label={isPluginsView ? "Plugins Navigation" : "Extensions Navigation"}
    >
      {content}
    </nav>
  );
}
